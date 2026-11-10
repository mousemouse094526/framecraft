"""The TTS adapter: the only module that imports omnivoice (spoil-maker D3, ADR 0019).

`worker` runs in a `spawn` child process (ADR 0012) that loads OmniVoice once, says
`Ready`, then answers each `Design` with `Designed` and each `Speak` with `Spoken`. The backend thread
owns the job and every file: the child sends audio and the clone prompt as bytes.
torch and omnivoice are imported inside the child only. A later TTS keeps these
messages and swaps `worker`.
"""

import io
import multiprocessing
import traceback
from pathlib import Path
from typing import Literal, NamedTuple

from backend.workers import Worker

LANGUAGE = "th"

# Sent to the child. `None` asks it to exit.


class Design(NamedTuple):
    """Speak `text` once in a voice drawn from `instruct`, lock that voice as a clone
    prompt, then speak `text` again in it at `speed` (spoil-maker spec › Saved voice step 2)."""

    instruct: str
    text: str
    speed: float
    num_step: int


class Speak(NamedTuple):
    """Speak `text` (numbers already words) in a Saved voice: its clone prompt as
    `VoiceClonePrompt.save` wrote it, and its speed (spoil-maker spec › Voice job)."""

    text: str
    prompt: bytes
    speed: float
    num_step: int


# Sent back, in order: `Ready` once the model is loaded, then one `Designed` per
# `Design` and one `Spoken` per `Speak`; a `WorkerError` instead ends the child.


class Ready(NamedTuple):
    pass


class Designed(NamedTuple):
    audio: bytes  # 16-bit little-endian mono PCM
    sample_rate: int
    prompt: bytes  # the clone prompt as `VoiceClonePrompt.save` writes it


class Spoken(NamedTuple):
    audio: bytes  # 16-bit little-endian mono PCM
    sample_rate: int


class WorkerError(NamedTuple):
    code: Literal["model_failed"]
    detail: str  # "{exception type}: {message}", for the log


def start_worker(snapshot_dir: Path, device: str) -> Worker:
    """Starts the child with its queue of requests and its queue of replies.

    Fresh queues per child: `terminate()` may corrupt a queue it was using.
    Daemonic, so the child dies with the backend.
    """
    context = multiprocessing.get_context("spawn")
    requests, replies = context.Queue(), context.Queue()
    process = context.Process(
        target=worker,
        args=(snapshot_dir, device, requests, replies),
        daemon=True,
        name="framecraft-tts",
    )
    process.start()
    return Worker(process, requests, replies)


def worker(snapshot_dir: Path, device: str, requests, replies) -> None:
    """The child process: load the model from the pinned snapshot, then answer requests."""
    try:
        model = load(snapshot_dir, device)
    except Exception as error:
        _send_error(replies, error)
        return
    replies.put(Ready())
    while (request := requests.get()) is not None:
        try:
            reply = design_voice(model, request) if isinstance(request, Design) else speak(model, request)
        except Exception as error:
            _send_error(replies, error)
            return
        replies.put(reply)


def load(snapshot_dir: Path, device: str):
    """omnivoice downloads when the path isn't a folder, so a missing one raises instead
    (docs/library-notes/omnivoice.md, ADR 0002)."""
    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"no model snapshot at {snapshot_dir}")
    import torch
    from omnivoice import OmniVoice

    dtype = torch.float32 if device == "cpu" else torch.float16
    return OmniVoice.from_pretrained(str(snapshot_dir), device_map=device, dtype=dtype)


def design_voice(model, request: Design) -> Designed:
    import torch

    locked = model.generate(text=request.text, language=LANGUAGE, instruct=request.instruct, num_step=request.num_step)[0]
    prompt = model.create_voice_clone_prompt(
        ref_audio=(torch.from_numpy(locked), model.sampling_rate), ref_text=request.text
    )
    sample = model.generate(
        text=request.text,
        language=LANGUAGE,
        voice_clone_prompt=prompt,
        speed=request.speed,
        num_step=request.num_step,
    )[0]
    saved = io.BytesIO()
    prompt.save(saved)  # torch.save takes a file object as well as a path
    return Designed(audio=_pcm16(sample), sample_rate=model.sampling_rate, prompt=saved.getvalue())


def speak(model, request: Speak) -> Spoken:
    from omnivoice import VoiceClonePrompt

    prompt = VoiceClonePrompt.load(io.BytesIO(request.prompt))  # torch.load takes a file object too
    audio = model.generate(
        text=request.text,
        language=LANGUAGE,
        voice_clone_prompt=prompt,
        speed=request.speed,
        num_step=request.num_step,
    )[0]
    return Spoken(audio=_pcm16(audio), sample_rate=model.sampling_rate)


def _pcm16(samples) -> bytes:
    """OmniVoice's float samples in [-1, 1] as 16-bit PCM, what `wave` writes."""
    import numpy as np

    return (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2").tobytes()


def _send_error(replies, error: Exception) -> None:
    traceback.print_exc()  # the child shares the backend's terminal: the full error shows in [api]
    replies.put(WorkerError("model_failed", f"{type(error).__name__}: {error}"))
