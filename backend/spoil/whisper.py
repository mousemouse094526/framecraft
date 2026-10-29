"""The Whisper adapter: the only module that imports `torch` and `transformers` to transcribe.

`worker` runs in a `spawn` child process (ADR 0012) and sends what it finds
through a queue; the backend thread in `transcribe` owns the job and the file.
torch and transformers are imported inside the child only, never when the
backend imports this module. Steps are in docs/features/spoil/spec.md › Transcribe.
"""

import multiprocessing
import subprocess
import traceback
from pathlib import Path
from typing import Literal, NamedTuple

SEGMENT_SECONDS = 300
MIN_LAST_SECONDS = 30  # a shorter last piece joins the one before: Whisper invents words from a few seconds (D29)
SAMPLE_RATE = 16_000

Line = tuple[float, float, str]  # start and end in clip seconds, text as Whisper wrote it


# What the child sends through the queue, in order: `Segment`s, then `Done` or a `WorkerError`.


class Segment(NamedTuple):
    """One finished 300 s piece of the clip; `index` counts from 0 up to `total`.

    Not Whisper's own "segment", which is closer to one of `lines`.
    """

    index: int
    total: int
    lines: list[Line]
    language: str | None  # an ISO code such as "en", or None when Whisper found none


class WorkerError(NamedTuple):
    code: Literal["no_audio", "model_failed"]
    detail: str  # "{exception type}: {message}", for the job's message and the log


class Done(NamedTuple):
    pass


def start_worker(mp4: Path, duration_s: int | None, snapshot_dir: Path, device: str):
    """Starts the child process; returns it with the queue it reports to.

    A fresh queue per child: `terminate()` may corrupt a queue it was using.
    Daemonic, so the child dies with the backend.
    """
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(
        target=worker,
        args=(mp4, duration_s, snapshot_dir, device, queue),
        daemon=True,
        name="framecraft-whisper",
    )
    process.start()
    return process, queue


def worker(mp4: Path, duration_s: int | None, snapshot_dir: Path, device: str, queue) -> None:
    """The child process: load the model, then send a `Segment` per 300 s piece and `Done`."""
    try:
        asr = load(snapshot_dir, device)
    except Exception as error:
        _send_error(queue, "model_failed", error)
        return
    segments = plan_segments(duration_s)
    for index, (start_s, length_s) in enumerate(segments):
        try:
            audio = read_audio(mp4, start_s, length_s)
        except Exception as error:
            # The first segment can't be read: the clip has no sound. Later ones are a failure.
            _send_error(queue, "no_audio" if index == 0 else "model_failed", error)
            return
        try:
            lines, language = transcribe(asr, audio, start_s, length_s)
        except Exception as error:
            _send_error(queue, "model_failed", error)
            return
        queue.put(Segment(index, len(segments), lines, language))
    queue.put(Done())


def plan_segments(duration_s: int | None) -> list[tuple[int, int | None]]:
    """`(start, length)` pairs of 300 s; an unknown length is one segment read to the end."""
    if not duration_s:
        return [(0, None)]
    starts = list(range(0, duration_s, SEGMENT_SECONDS))
    if len(starts) > 1 and duration_s - starts[-1] < MIN_LAST_SECONDS:
        starts.pop()
    ends = starts[1:] + [duration_s]
    return [(start, end - start) for start, end in zip(starts, ends)]


def read_audio(mp4: Path, start_s: int, length_s: int | None):
    """One segment's sound as 16 kHz mono float32, through a pipe (D27, D29).

    Raises when ffmpeg fails or the segment has no sound.
    """
    import imageio_ffmpeg
    import numpy as np

    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-ss", str(start_s)]
    if length_s is not None:
        command += ["-t", str(length_s)]
    command += ["-i", str(mp4), "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"]
    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0:
        message = result.stderr.decode(errors="replace").strip().splitlines()
        raise RuntimeError(f"ffmpeg exited with {result.returncode}: {message[-1] if message else ''}")
    if not result.stdout:
        raise RuntimeError("ffmpeg returned no audio")
    return np.frombuffer(result.stdout, dtype=np.float32)


def load(snapshot_dir: Path, device: str):
    """The ASR pipeline from the pinned snapshot folder, with no network (ADR 0004).

    `float16` on `mps` gives garbage for large-v3-turbo, so Metal runs `float32` (D30).
    """
    import torch
    from transformers import pipeline

    dtype = torch.float16 if device == "cuda" else torch.float32
    return pipeline("automatic-speech-recognition", model=str(snapshot_dir), device=device, dtype=dtype)


def transcribe(asr, audio, start_s: int, length_s: int | None) -> tuple[list[Line], str | None]:
    """One segment's lines in clip time and the language Whisper detected (`en`, `th`, or None).

    The whole array goes in without `chunk_length_s`, so Whisper runs its own
    long-form decoding; `batch_size` 1 because the language comes from the
    first batch item only (D29, docs/library-notes/transformers.md).
    """
    from transformers.models.whisper.tokenization_whisper import TO_LANGUAGE_CODE

    output = asr(audio, return_timestamps=True, return_language=True, batch_size=1)
    chunks = output.get("chunks") or []
    name = chunks[0].get("language") if chunks else None  # a name such as "english"
    return to_lines(chunks, start_s, length_s), TO_LANGUAGE_CODE.get(name, name)


def to_lines(chunks: list[dict], start_s: int, length_s: int | None) -> list[Line]:
    """Moves Whisper's times (inside the segment) to clip time.

    A missing end is the segment's end, and an end past it is clamped: both
    happen on real 300 s arrays (docs/library-notes/transformers.md).
    """
    lines = []
    for chunk in chunks:
        begin, end = chunk["timestamp"]
        if length_s is not None:
            begin = min(begin, length_s)
            end = length_s if end is None else min(end, length_s)
        elif end is None:
            end = begin
        lines.append((round(start_s + begin, 2), round(start_s + max(begin, end), 2), chunk["text"]))
    return lines


def _send_error(queue, code: str, error: Exception) -> None:
    traceback.print_exc()  # the child shares the backend's terminal: the full error shows in [api]
    queue.put(WorkerError(code, f"{type(error).__name__}: {error}"))
