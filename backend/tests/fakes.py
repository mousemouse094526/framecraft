"""Fake project roots, probes and models shared by the backend tests, and the fixtures
of the toon API tests (`toon_api`) and the calls they share."""

import dataclasses
import functools
import io
import json
import queue
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path

import anyio
import httpx
import imageio_ffmpeg
import numpy as np
import pytest
import soundfile
from fastapi.testclient import TestClient
from PIL import Image

from backend import checks, gpu, paths, sounds, spoil_maker
from backend.app import app
from backend.checks import FfmpegInfo, GpuInfo, Probes, named_patterns
from backend.errors import ApiError
from backend.models import MODELS, ModelSpec
from backend.paths import EpAddress, ProjectPaths
from backend.workers import Worker
from backend.spoil import clips
from backend.spoil.mp4check import Mp4Info, NotPlayable
from backend.spoil.whisper import Done, Segment
from backend.toon import jobs, store



def poll_until(client, path: str, condition: Callable[[dict], bool], timeout_s: float = 10) -> dict:
    """GETs `path` until its JSON meets `condition`; how a test waits for a job (rules › testing)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        job = client.get(path).json()
        if condition(job):
            return job
        time.sleep(0.01)
    raise AssertionError(f"job never got there: {job}")


MODEL_FILES = {"config.json": 120, "model.safetensors": 4096}


def write_snapshot(root: Path, model: ModelSpec, revision: str | None = None) -> Path:
    """Create the files snapshot_download would leave for one model: `MODEL_FILES`, and
    one file for each of its patterns that names a folder or a file (`text_encoder/*`)."""
    snapshot = ProjectPaths(root).snapshot_dir(model, revision or model.revision)
    for name, size in snapshot_files(model).items():
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * size)
    return snapshot


def snapshot_files(model: ModelSpec) -> dict[str, int]:
    """Path → size of the files `write_snapshot` leaves and `write_marker` lists."""
    named = {pattern.replace("*", "model.safetensors"): 64 for pattern in named_patterns(model)}
    return MODEL_FILES | named


def write_marker(root: Path, model: ModelSpec, revision: str | None = None) -> Path:
    marker = ProjectPaths(root).marker(model)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps(
            {
                "repo_id": model.repo_id,
                "revision": revision or model.revision,
                "files": [{"path": n, "size": s} for n, s in snapshot_files(model).items()],
                "size_bytes": sum(snapshot_files(model).values()),
                "finished_at": "2026-10-29T10:00:00+07:00",
            }
        ),
        encoding="utf-8",
    )
    return marker


def write_kanit(root: Path) -> None:
    """Kanit's two files and the marker setup writes once their sha256 match the pins."""
    from backend import fonts

    project = ProjectPaths(root)
    project.kanit_dir.mkdir(parents=True, exist_ok=True)
    for name in fonts.KANIT_SHA256:
        (project.kanit_dir / name).write_bytes(b"font file")
    project.kanit_marker.parent.mkdir(parents=True, exist_ok=True)
    project.kanit_marker.write_text(json.dumps({"files": dict(fonts.KANIT_SHA256)}), encoding="utf-8")


@functools.cache
def fake_sample() -> bytes:
    """A 0.1 s mono FLAC at 44.1 kHz whose first sample is at full scale, then silence: where a
    hit starts is the first loud sample (video-gen spec › Testing decisions). Made once."""
    audio = np.zeros(4410, dtype=np.float32)
    audio[0] = 1.0
    buffer = io.BytesIO()
    soundfile.write(buffer, audio, 44100, subtype="PCM_16", format="FLAC")
    return buffer.getvalue()


def write_drum_kit(root: Path) -> None:
    """Every drum sample as `fake_sample` and the marker setup writes once their sha256 match
    the pins; nothing is fetched."""
    from backend import drum_kit

    project = ProjectPaths(root)
    for sample in drum_kit.SAMPLES:
        path = drum_kit.sample_path(project, sample)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(fake_sample())
    project.drum_kit_marker.parent.mkdir(parents=True, exist_ok=True)
    pinned = {sample.path: sample.sha256 for sample in drum_kit.SAMPLES}
    project.drum_kit_marker.write_text(json.dumps({"files": pinned}), encoding="utf-8")


def drum_lesson(*notes, bpm: int = 120, bars: int = 1, chapters=None, **fields):
    """A drum lesson as `lesson.json` holds it (video-gen spec › Data): one plain chapter unless given."""
    from backend.video_gen.lessons import Groove, Lesson

    return Lesson(
        version=1,
        id="k3v9x0a1b2c4",
        title="FILL",
        subtitle="",
        caption="",
        bpm=bpm,
        background="color",
        groove=Groove(bars=bars, notes=list(notes)),
        chapters=chapters or [drum_chapter()],
        updated_at="2026-11-13T10:30:00+07:00",
    ).model_copy(update=fields)


def drum_chapter(repeats: int = 1, speed: int = 100, **fields):
    from backend.video_gen.lessons import Chapter

    return Chapter(**({"label": "", "text": "", "focus": [], "repeats": repeats, "speed": speed} | fields))


def drum_note(piece: str, step: int, hand: str | None = "R", hit: str = "normal"):
    from backend.video_gen.lessons import Note

    return Note(piece=piece, step=step, hand=hand, hit=hit)


def ok_ffmpeg() -> FfmpegInfo:
    return FfmpegInfo(version="7.1", source="imageio-ffmpeg")


def broken_ffmpeg() -> FfmpegInfo:
    raise RuntimeError("ffmpeg -version exited with 1")


def ok_yt_dlp() -> str:
    return "2026.10.26"


def ok_mlx_vlm() -> str:
    return "0.7.11"


def ok_pythainlp() -> str:
    return "5.4.0"


def ok_deno() -> str:
    return "2.9.8"


def broken_deno() -> str:
    raise FileNotFoundError("deno")


def cuda_device() -> str:
    return "cuda"


# What torch 2.8.0+cu128 was built for (docs/library-notes/torch.md): no sm_89, no Pascal.
CU128_ARCHS = ("sm_70", "sm_75", "sm_80", "sm_86", "sm_90", "sm_100", "sm_120")


def card(name: str = "NVIDIA GeForce RTX 3060", gib: float = 12, capability: tuple[int, int] = (8, 6)):
    """A `gpu` probe that reads one card, as nvidia-smi and torch's arch list would report it."""
    info = GpuInfo(name=name, memory_bytes=int(gib * 2**30), capability=capability, arch_list=CU128_ARCHS)
    return lambda: info


def broken_gpu() -> GpuInfo:
    raise FileNotFoundError("nvidia-smi")


def ok_bitsandbytes() -> str:
    return "0.50.2"


def ok_diffusers() -> str:
    return "0.42.1"


def ok_gguf() -> str:
    return "0.19.0"


def fake_probes(**overrides) -> Probes:
    """Every probe passing on a CUDA machine, unless overridden by field name."""
    probes = Probes(
        device=cuda_device,
        ffmpeg=ok_ffmpeg,
        deno=ok_deno,
        yt_dlp=ok_yt_dlp,
        mlx_vlm=ok_mlx_vlm,
        pythainlp=ok_pythainlp,
        gpu=card(),
        bitsandbytes=ok_bitsandbytes,
        diffusers=ok_diffusers,
        gguf=ok_gguf,
    )
    return dataclasses.replace(probes, **overrides)


def on_windows(monkeypatch, gpu_probe=None) -> None:
    """Makes the API's checks see a Windows machine with an RTX 3060 and bitsandbytes,
    unless `gpu_probe` says otherwise; `fake_root` has every model of both OSes."""
    from backend import checks

    monkeypatch.setattr(checks, "this_platform", lambda: "win32")
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(checks, "probe_gpu", gpu_probe or card())
    monkeypatch.setattr(checks, "probe_bitsandbytes", ok_bitsandbytes)


def klein_timeouts(monkeypatch, seconds: float) -> None:
    """Swaps `klein.DRAW_TIMEOUTS` so a picture of the Mac and of Windows may take `seconds`."""
    from backend.toon import klein

    monkeypatch.setattr(klein, "DRAW_TIMEOUTS", {"darwin": seconds, "win32": seconds})


def os_timeouts(monkeypatch, darwin: float, win32: float) -> None:
    """Swaps `llm.TIMEOUTS` so every step of the Mac and of Windows has the given seconds."""
    from backend.spoil_maker import llm

    monkeypatch.setattr(llm, "TIMEOUTS", {"darwin": llm.Timeouts(*[darwin] * 4), "win32": llm.Timeouts(*[win32] * 4)})


# A fake answer this slow outlasts a Mac timeout of 0.2 s and fits a Windows one of 1 s.
SLOW_ANSWER_SECONDS = 0.5
# A child's errors as a `WorkerError.detail`. One of the GPU, its message ending with `gpu.ADVICE`;
# one of the code (the kind of `TypeError` of toon's Blocked #33), whose message has none (toon D84).
GPU_ERROR = "RuntimeError: MPS out of memory"
CODE_ERROR = "TypeError: Load.__new__() missing 1 required positional argument: 'embeds'"


def slow_first(reply):
    """`reply` (a text, or a function of the request) that takes `SLOW_ANSWER_SECONDS`
    the first time only, so a retry after a timeout answers at once."""
    asked = []

    def respond(request):
        if not asked:
            time.sleep(SLOW_ANSWER_SECONDS)
        asked.append(request)
        return reply(request) if callable(reply) else reply

    return respond


def item(result, item_id: str):
    return next(i for i in result.items if i.id == item_id)


def youtube_info(video_id: str = "dQw4w9WgXcQ", **overrides) -> dict:
    """An info dict shaped like yt-dlp's for a 1080p video with separate audio."""
    return {
        "id": video_id,
        "extractor_key": "Youtube",
        "title": "ชื่อคลิป",
        "channel": "ชื่อช่อง",
        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
        "duration": 213,
        "live_status": "not_live",
        "requested_formats": [
            {"format_id": "137", "width": 1920, "height": 1080, "vcodec": "avc1", "filesize": 1000},
            {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "filesize": 100},
        ],
    } | overrides


def site_info(extractor_key: str = "Facebook", video_id: str = "123", **overrides) -> dict:
    """An info dict of another site's video, one combined h264/aac format picked."""
    return {
        "id": video_id,
        "extractor_key": extractor_key,
        "title": "คลิปจากเว็บอื่น",
        "uploader": "เพจ",
        "webpage_url": f"https://www.facebook.com/watch/?v={video_id}",
        "duration": 30,
        "width": 720,
        "height": 1280,
        "vcodec": "avc1.64001F",
        "acodec": "mp4a.40.2",
        "filesize": 1000,
    } | overrides


def progress_events(video_id: str = "dQw4w9WgXcQ") -> list[dict]:
    """The progress hook calls yt-dlp makes for `youtube_info`: video, then audio."""
    video = f"{video_id}.f137.mp4"
    audio = f"{video_id}.f140.m4a"
    return [
        {"status": "downloading", "filename": video, "downloaded_bytes": 400, "total_bytes": 1000},
        {"status": "downloading", "filename": video, "downloaded_bytes": 1000, "total_bytes": 1000},
        {"status": "finished", "filename": video, "downloaded_bytes": 1000, "total_bytes": 1000},
        {"status": "downloading", "filename": audio, "downloaded_bytes": 50, "total_bytes": 100},
        {"status": "finished", "filename": audio, "downloaded_bytes": 100, "total_bytes": 100},
    ]


def yt_dlp_error(cause: Exception):
    """A `DownloadError` wrapping `cause`, the way YoutubeDL raises site errors."""
    from yt_dlp.utils import DownloadError

    return DownloadError(f"ERROR: {cause}", exc_info=(type(cause), cause, None))


class FakeAdapter:
    """Stands in for the yt-dlp adapter in `backend.spoil`.

    Plays `events` through the progress hook like yt-dlp, writes the files a
    finished download leaves, and can pause at "fetch", "progress" (after the
    first event) or "merge" until the test calls `release`.
    """

    def __init__(self, info=None, events=None, fetch_error=None, download_error=None):
        self.info = info or youtube_info()
        self.events = progress_events(self.info["id"]) if events is None else events
        self.fetch_error = fetch_error
        self.download_error = download_error
        self.download_calls = 0
        self.clip_ids: list[str] = []
        self.fetched_urls: list[str] = []
        self._paused: dict[str, threading.Event] = {}
        self._reached: dict[str, threading.Event] = {}

    def pause_at(self, point: str) -> None:
        self._paused[point] = threading.Event()
        self._reached[point] = threading.Event()

    def wait_until(self, point: str) -> None:
        assert self._reached[point].wait(5), f"adapter never reached {point}"

    def release(self, point: str) -> None:
        self._paused[point].set()

    def fetch_info(self, url: str) -> dict:
        self.fetched_urls.append(url)
        self._checkpoint("fetch")
        if self.fetch_error:
            raise self.fetch_error
        return self.info

    def download(self, info: dict, project: ProjectPaths, clip_id: str, on_progress) -> Path:
        self.download_calls += 1
        self.clip_ids.append(clip_id)
        video_id = clip_id  # the files are named by `outtmpl`, which is the clip id
        project.partial_dir.mkdir(parents=True, exist_ok=True)
        (project.partial_dir / f"{video_id}.f137.mp4.part").write_bytes(b"x" * 400)
        (project.partial_dir / f"{video_id}.webp").write_bytes(b"thumb")
        for index, event in enumerate(self.events):
            on_progress(event)
            if index == 0:
                self._checkpoint("progress")
        if self.download_error:
            raise self.download_error
        self._checkpoint("merge")
        for leftover in project.partial_dir.glob(f"{video_id}.*"):
            leftover.unlink()
        (project.media_temp_dir / f"{video_id}.webp").write_bytes(b"thumb")
        mp4 = project.media_temp_dir / f"{video_id}.mp4"
        mp4.write_bytes(b"m" * 1234)
        return mp4

    def _checkpoint(self, point: str) -> None:
        if point in self._paused:
            self._reached[point].set()
            assert self._paused[point].wait(5), f"test never released {point}"


class FakeMp4Check:
    """Stands in for the Download job's `check_mp4` (ffmpeg on the merged file): a
    playable 1920×1080 file, unless the test sets the size, or a `reason` to refuse it."""

    def __init__(self):
        self.width, self.height = 1920, 1080
        self.reason: str | None = None
        self.checked: list[Path] = []

    def __call__(self, path: Path) -> Mp4Info:
        self.checked.append(path)
        if self.reason:
            raise NotPlayable(self.reason)
        return Mp4Info(duration_s=213.0, width=self.width, height=self.height)


def write_temp_clip(
    project: ProjectPaths,
    video_id: str = "dQw4w9WgXcQ",
    downloaded_at: str = "2026-10-29T14:05:11+07:00",
    thumbnail: bool = True,
    duration_s: int = 213,
) -> dict:
    """The three files a finished download leaves in media/temp/; returns the json."""
    project.media_temp_dir.mkdir(parents=True, exist_ok=True)
    (project.media_temp_dir / f"{video_id}.mp4").write_bytes(bytes(range(256)) * 4)
    if thumbnail:
        (project.media_temp_dir / f"{video_id}.webp").write_bytes(b"thumb")
    clip = {
        "id": video_id,
        "title": "ชื่อคลิป",
        "channel": "ชื่อช่อง",
        "source_url": f"https://www.youtube.com/watch?v={video_id}",
        "duration_s": duration_s,
        "width": 1920,
        "height": 1080,
        "orientation": "landscape",
        "file_bytes": 1024,
        "thumbnail": f"{video_id}.webp" if thumbnail else None,
        "downloaded_at": downloaded_at,
        "yt_dlp_version": "2026.10.26",
    }
    (project.media_temp_dir / f"{video_id}.json").write_text(json.dumps(clip), encoding="utf-8")
    return clip


def segment(index: int, total: int, lines=((1.0, 2.5, " Hello."),), language: str | None = "en") -> Segment:
    """One `Segment` as the Whisper worker sends it: its lines already moved to
    clip time (`whisper.to_lines` does that in the child)."""
    return Segment(index, total, list(lines), language)


class FakeWorker:
    """Stands in for `backend.spoil.start_worker`.

    Each start runs a thread that puts `messages` into a queue the way the
    child process does, then "exits" with `exitcode`. It can pause before the
    message at an index until the test calls `release`; `terminate` stops it
    there, like a killed process.
    """

    def __init__(self, messages=None, exitcode: int = 0):
        self.messages = [segment(0, 1), Done()] if messages is None else messages
        self.exitcode = exitcode
        self.calls: list[tuple] = []
        self.processes: list["FakeProcess"] = []
        self._paused: dict[int, threading.Event] = {}
        self._reached: dict[int, threading.Event] = {}

    def pause_at(self, index: int) -> None:
        self._paused[index] = threading.Event()
        self._reached[index] = threading.Event()

    def wait_until(self, index: int) -> None:
        assert self._reached[index].wait(5), f"worker never reached message {index}"

    def release(self, index: int) -> None:
        self._paused[index].set()

    def checkpoint(self, index: int, killed: threading.Event) -> None:
        """Waits at a paused message until the test releases it or the process is killed."""
        if index not in self._paused:
            return
        self._reached[index].set()
        while not (self._paused[index].is_set() or killed.is_set()):
            killed.wait(0.01)

    def __call__(self, mp4: Path, duration_s, snapshot_dir: Path, device: str):
        import queue

        self.calls.append((mp4, duration_s, snapshot_dir, device))
        messages: queue.Queue = queue.Queue()
        process = FakeProcess(self, messages)
        self.processes.append(process)
        process.start()
        return process, messages


class FakeProcess:
    """The `multiprocessing.Process` surface the Transcribe job uses."""

    def __init__(self, worker: FakeWorker, messages):
        self._worker = worker
        self._messages = messages
        self._killed = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.terminated = False
        self.exitcode: int | None = None

    def start(self) -> None:
        self._thread.start()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def terminate(self) -> None:
        self.terminated = True
        self._killed.set()

    def join(self, timeout: float | None = None) -> None:
        self._thread.join(timeout)

    def kill(self) -> None:
        self.terminate()

    def _run(self) -> None:
        for index, message in enumerate(self._worker.messages):
            self._worker.checkpoint(index, self._killed)
            if self._killed.is_set():
                break
            self._messages.put(message)
        self.exitcode = -15 if self._killed.is_set() else self._worker.exitcode


def write_transcript(project: ProjectPaths, video_id: str = "dQw4w9WgXcQ", lines=None) -> dict:
    """A `{id}.transcript.json` as a finished Transcribe job leaves it; returns its content."""
    transcript = {
        "clip_id": video_id,
        "language": "en",
        "duration_s": 213,
        "model": "openai/whisper-large-v3-turbo",
        "revision": "41f01f3",
        "transcribed_at": "2026-10-30T10:12:00+07:00",
        "lines": lines if lines is not None else [{"start_s": 12.4, "end_s": 15.0, "text": "Old line."}],
    }
    clips.transcript_path(project, video_id).write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")
    return transcript


def make_test_clip(path: Path, colors: tuple[str, ...] = ("red", "white", "blue"), seconds_each: float = 1) -> Path:
    """An mp4 of solid colours, `seconds_each` apiece, with a sine tone, made with ffmpeg's
    `lavfi` so no media file sits in git (spoil-maker seam 1).

    The scene filter compares brightness more than hue: red to green (about the same
    luma) is no cut, so the default colours differ in brightness."""
    import subprocess

    import imageio_ffmpeg

    inputs = []
    for color in colors:
        inputs += ["-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=10:d={seconds_each}"]
    total = seconds_each * len(colors)
    inputs += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={total}"]
    joined = "".join(f"[{index}:v]" for index in range(len(colors)))
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-y", *inputs,
        "-filter_complex", f"{joined}concat=n={len(colors)}:v=1:a=0[v]",
        "-map", "[v]", "-map", f"{len(colors)}:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path),
    ]  # fmt: skip
    subprocess.run(command, check=True)
    return path


class FakeModel:
    """Stands in for a model's child process that answers requests from a queue
    (`spoil_maker.start_worker`, `spoil_maker.start_tts_worker`).

    Each start runs a thread that says `ready()` (unless it is None), then one `answer(request, index)`
    per request, `index` counting that process's requests from 0. It can pause
    before answering request `index` until the test calls
    `release` (or the process is terminated) with `pause_at`, never answer it
    (`hang_at`, for timeouts), or exit at it without a word (`crash_at`). An
    `answer` of `HANG` never comes either, whichever process asked. `crash_on_load`
    exits before `ready()`, as a model that can't load. `fail_at` answers that request of a
    process — of every process the model starts — with the model's `WorkerError` whose
    detail is `fail_with` instead (`GPU_ERROR` unless a test sets `CODE_ERROR`).
    """

    HANG = object()

    def __init__(self):
        self.requests = []
        self.processes: list["FakeModelProcess"] = []
        self.crash_at: int | None = None
        self.hang_at: int | None = None
        self.crash_on_load = False
        self.fail_at: int | None = None
        self.fail_with = GPU_ERROR
        self._paused: dict[int, threading.Event] = {}
        self._reached: dict[int, threading.Event] = {}

    def ready(self):
        raise NotImplementedError

    def answer(self, request, index: int):
        raise NotImplementedError

    def failure(self):
        """The model's `WorkerError` with `fail_with`, the answer to request `fail_at`."""
        raise NotImplementedError

    def pause_at(self, index: int) -> None:
        self._paused[index] = threading.Event()
        self._reached[index] = threading.Event()

    def wait_until(self, index: int) -> None:
        assert self._reached[index].wait(5), f"the model never reached request {index}"

    def release(self, index: int) -> None:
        self._paused[index].set()

    def __call__(self, snapshot_dir: Path, *args):
        requests = _EndNoted()
        replies: queue.Queue = queue.Queue()
        process = FakeModelProcess(self, snapshot_dir, args, requests, replies)
        self.processes.append(process)
        process.start()
        return Worker(process, requests, replies)


class _EndNoted(queue.Queue):
    """A request queue that notes the `None` asking its child to exit, read or not."""

    def __init__(self):
        super().__init__()
        self.asked_to_end = False

    def put(self, item, block=True, timeout=None):
        if item is None:
            self.asked_to_end = True
        super().put(item, block, timeout)


class FakeLlm(FakeModel):
    """The mlx-vlm child: `respond(request)` makes each `Generated` text, or is `HANG`."""

    def __init__(self):
        super().__init__()
        self.respond = lambda request: f"A frame at {request.image.name}."

    def ready(self):
        from backend.spoil_maker.llm import Ready

        return Ready()

    def failure(self):
        from backend.spoil_maker.llm import WorkerError

        return WorkerError("model_failed", self.fail_with)

    def answer(self, request, index: int):
        from backend.spoil_maker.llm import Generated

        text = self.respond(request)
        return text if text is self.HANG else Generated(text)


class FakeTts(FakeModel):
    """The OmniVoice child: every request is spoken as `seconds` of silence at 24 kHz;
    a `Design` also gets the clone prompt `b"prompt {n}"`, `n` counting every request
    it got from 0."""

    SAMPLE_RATE = 24_000

    def __init__(self):
        super().__init__()
        self.seconds = 2.0

    def ready(self):
        from backend.spoil_maker.tts import Ready

        return Ready()

    def failure(self):
        from backend.spoil_maker.tts import WorkerError

        return WorkerError("model_failed", self.fail_with)

    def answer(self, request, index: int):
        from backend.spoil_maker.tts import Designed, Speak, Spoken

        audio = b"\0\0" * round(self.SAMPLE_RATE * self.seconds)
        if isinstance(request, Speak):
            return Spoken(audio=audio, sample_rate=self.SAMPLE_RATE)
        prompt = f"prompt {len(self.requests) - 1}".encode()
        return Designed(audio=audio, sample_rate=self.SAMPLE_RATE, prompt=prompt)


class FakeKlein(FakeModel):
    """Both klein children: the encoder's (`toon.klein.start_encoder`), which answers `Encode`
    with `embeds_of` each prompt, and the drawing one (`toon.klein.start_drawer`), which answers
    `Load` with `Loaded` and each `Draw` with the bytes `b"png {seed}"`. Neither says a word
    first; `processes` holds both, in the order they started, and `alive_at_start` which of the
    earlier ones still ran as each started. `silent_on` never answers a request of that type
    (`Encode`, `Load`)."""

    def __init__(self):
        super().__init__()
        self.silent_on: type | None = None
        self.alive_at_start: list[list[bool]] = []

    @staticmethod
    def embeds_of(prompt: str) -> bytes:
        return f"embeds of {prompt}".encode()

    def draws(self) -> list:
        """The `Draw`s of every drawing child, in order."""
        from backend.toon.klein import Draw

        return [request for request in self.requests if isinstance(request, Draw)]

    def __call__(self, snapshot_dir: Path, *args):
        self.alive_at_start.append([process.is_alive() for process in self.processes])
        return super().__call__(snapshot_dir, *args)

    def ready(self):
        return None

    def failure(self):
        from backend.toon.klein import WorkerError

        return WorkerError("model_failed", self.fail_with)

    def answer(self, request, index: int):
        from backend.toon.klein import Drawn, Encode, Encoded, Load, Loaded

        if self.silent_on is not None and isinstance(request, self.silent_on):
            return self.HANG
        if isinstance(request, Encode):
            return Encoded([self.embeds_of(prompt) for prompt in request.prompts])
        if isinstance(request, Load):
            return Loaded()
        return Drawn(f"png {request.seed}".encode())


class FakeModelProcess(FakeProcess):
    """The `multiprocessing.Process` surface, answering requests from a thread."""

    def __init__(self, model: FakeModel, snapshot_dir: Path, args: tuple, requests, replies):
        self._model, self.snapshot_dir, self.args = model, snapshot_dir, args
        self._requests, self._replies = requests, replies
        self._killed = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.terminated = False
        self.exitcode: int | None = None

    def _run(self) -> None:
        from queue import Empty

        model = self._model
        if model.crash_on_load:
            self.exitcode = -11
            return
        if (ready := model.ready()) is not None:
            self._replies.put(ready)
        index = 0
        while not self._killed.is_set():
            try:
                request = self._requests.get(timeout=0.01)
            except Empty:
                continue
            if request is None:
                break
            model.requests.append(request)
            if index == model.crash_at:
                self.exitcode = -11
                return
            if index in model._paused:
                model._reached[index].set()
                while not (model._paused[index].is_set() or self._killed.is_set()):
                    self._killed.wait(0.01)
            if index == model.hang_at:
                answer = model.HANG
            elif index == model.fail_at:
                answer = model.failure()
            else:
                answer = model.answer(request, index)
            if answer is model.HANG:
                self._killed.wait()
            if self._killed.is_set():
                break
            self._replies.put(answer)
            index += 1
        self.exitcode = -15 if self._killed.is_set() else 0

    @property
    def asked_to_end(self) -> bool:
        return self._requests.asked_to_end


def jpeg_width(path: Path) -> int:
    """The width in a JPEG's start-of-frame header, so tests need no image library."""
    data = path.read_bytes()
    index = 2  # after the SOI marker
    while index < len(data):
        marker, length = data[index + 1], int.from_bytes(data[index + 2 : index + 4], "big")
        if marker in (0xC0, 0xC1, 0xC2):  # SOF0–SOF2: height then width follow the precision byte
            return int.from_bytes(data[index + 7 : index + 9], "big")
        index += 2 + length
    raise ValueError(f"no frame header in {path}")


class FakeFfmpeg:
    """A job's `run_ffmpeg` (`Trims`, `RenderJobs`; spoil spec › Testing decisions). Run
    `n` (from 0) reports `progress` seconds, then holds at a point paused with `pause_at(n)`
    until the test calls `release(n)` or the job cancels (`Cancelled`, `killed`); `fail`
    raises `FfmpegFailed`. It then writes `output` to the command's last argument, or hands
    the command to `then` (the real `ffmpeg.run`, for a render that must make its file)."""

    def __init__(self, progress: tuple[float, ...] = (37.0,), output: bytes = b"new mp4", then=None):
        self.commands: list[list[str]] = []
        self.progress, self.output, self.then = progress, output, then
        self.fail, self.killed = False, False
        self._paused: dict[int, threading.Event] = {}
        self._reached: dict[int, threading.Event] = {}

    def pause_at(self, index: int) -> None:
        self._paused[index] = threading.Event()
        self._reached[index] = threading.Event()

    def wait_until(self, index: int) -> None:
        assert self._reached[index].wait(5), f"ffmpeg never reached run {index}"

    def release(self, index: int) -> None:
        self._paused[index].set()

    def __call__(self, command, cwd, cancel, on_progress=None) -> None:
        from backend.ffmpeg import FfmpegFailed
        from backend.jobs import Cancelled

        index = len(self.commands)
        self.commands.append(command)
        for seconds in self.progress:
            if on_progress:
                on_progress(seconds)
        if index in self._paused:
            self._reached[index].set()
            while not (self._paused[index].is_set() or cancel.is_set()):
                cancel.wait(0.01)
        if cancel.is_set():
            self.killed = True
            raise Cancelled()
        if self.fail:
            raise FfmpegFailed("ffmpeg exited with 1: Invalid data found when processing input", "Invalid data found when processing input")
        if self.then is not None:
            self.then(command, cwd, cancel, on_progress)
        else:
            Path(command[-1]).write_bytes(self.output)


# --- An upload played through the app as ASGI (docs/library-notes/fastapi.md) ---


class Upload:
    """Plays an upload's ASGI `receive` messages: `chunks`, each sent at once or (a
    `Gate`) once the test opens it, then the end of the body, a disconnect, or nothing.
    `then="leave"` ends the body, then disconnects once the test calls `leave`: the page
    going away after its file was sent."""

    def __init__(self, *chunks, then: str = "end"):
        self.chunks = list(chunks)
        self.then = then
        self.ended = False
        self.left = anyio.Event()

    def leave(self) -> None:
        self.left.set()

    async def receive(self) -> dict:
        if self.chunks:
            chunk = self.chunks.pop(0)
            if isinstance(chunk, Gate):
                chunk = await chunk.wait()
            return {"type": "http.request", "body": chunk, "more_body": True}
        if self.then == "disconnect":
            return {"type": "http.disconnect"}
        if self.then == "leave" and self.ended:
            # As uvicorn: a disconnect already seen comes back without waiting, so
            # Starlette's `is_disconnected` (a receive in a cancelled scope) sees it.
            if not self.left.is_set():
                await self.left.wait()
            return {"type": "http.disconnect"}
        self.ended = True
        if self.then == "stall":
            await anyio.sleep_forever()
        return {"type": "http.request", "body": b"", "more_body": False}


class Gate:
    """A chunk that waits until the test calls `open`; `reached` is set once the app asks for it."""

    def __init__(self, chunk: bytes):
        self.chunk = chunk
        self.reached = anyio.Event()
        self.opened = anyio.Event()

    async def wait(self) -> bytes:
        self.reached.set()
        await self.opened.wait()
        return self.chunk

    def open(self) -> None:
        self.opened.set()


async def play(upload: Upload, name: str, size: int, path: str = "/api/spoil/imports") -> tuple[int | None, dict | None]:
    """POST `path` through the app as ASGI; returns the status and the JSON body."""
    query = httpx.QueryParams({"name": name, "size": size})
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": str(query).encode(),
        "root_path": "",
        "headers": [(b"host", b"127.0.0.1"), (b"content-type", b"application/octet-stream")],
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8000),
    }
    sent: list[dict] = []

    async def collect(message: dict) -> None:
        sent.append(message)

    from backend.app import app  # here: the app imports every route, which a probe's fake never needs

    await app(scope, upload.receive, collect)
    status = next((m["status"] for m in sent if m["type"] == "http.response.start"), None)
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(body) if body else None


# --- toon API tests ---

TOON_VOICE = "v_8f2c01ab"
TOON_SERIES = "/api/toon/series"
TOON_JOBS = "/api/toon/jobs"
TOON_CURRENT = "/api/toon/jobs/current"
SOUNDS = "/api/sounds"
FINISHED = {"done", "failed", "cancelled"}


def write_toon_voice(project: ProjectPaths, voice_id: str = TOON_VOICE) -> None:
    """A Saved voice a Series can be made with."""
    project.voices_dir.mkdir(parents=True, exist_ok=True)
    stored = {"name": "เสียง", "kind": "design", "speed": 1.0, "chars_per_s": 15.0, "created_at": "2026-11-02T10:00:00+07:00"}
    (project.voices_dir / f"{voice_id}.json").write_text(json.dumps(stored), encoding="utf-8")
    (project.voices_dir / f"{voice_id}.wav").write_bytes(b"wav")
    (project.voices_dir / f"{voice_id}.pt").write_bytes(b"pt")


def toon_api(
    answers: Callable[[], Callable[[object], str]] | None = None, *, tts_seconds: float = 2.0, uses: tuple[str, ...] = ()
) -> tuple[Callable, Callable, Callable, Callable, Callable]:
    """The `project`, `llm`, `klein`, `tts` and `client` fixtures of a toon API test file. The
    file keeps them under those names, as pytest finds a fixture by its module-level name:
    `project, llm, klein, tts, client = toon_api(...)`. `answers()` makes a fresh `FakeLlm.respond` for
    each test (None: FakeLlm's own); `uses` names fixtures of the file itself that `client`
    sets up first (`renderer`, a stand-in ffmpeg; `adapter`, yt-dlp)."""
    @pytest.fixture(name="project")
    def project_fixture(fake_root) -> ProjectPaths:
        return ProjectPaths(fake_root)

    @pytest.fixture(name="llm")
    def llm_fixture(monkeypatch) -> FakeLlm:
        fake = FakeLlm()
        if answers is not None:
            fake.respond = answers()
        monkeypatch.setattr(spoil_maker, "start_worker", fake)
        return fake

    @pytest.fixture(name="klein")
    def klein_fixture(monkeypatch) -> FakeKlein:
        fake = FakeKlein()
        monkeypatch.setattr("backend.toon.klein.start_encoder", fake)
        monkeypatch.setattr("backend.toon.klein.start_drawer", fake)
        return fake

    @pytest.fixture(name="tts")
    def tts_fixture(monkeypatch) -> FakeTts:
        fake = FakeTts()
        fake.seconds = tts_seconds
        monkeypatch.setattr(spoil_maker, "start_tts_worker", fake)
        return fake

    @pytest.fixture(name="client")
    def client_fixture(fake_root, llm, klein, tts, monkeypatch, request) -> TestClient:
        for name in uses:
            request.getfixturevalue(name)
        monkeypatch.setattr(paths, "ROOT", fake_root)
        monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
        monkeypatch.setattr(checks, "probe_device", cuda_device)
        monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
        monkeypatch.setattr(jobs, "toon_jobs", jobs.ToonJobs())
        monkeypatch.setattr(sounds, "sound_imports", sounds.SoundImports())
        write_toon_voice(ProjectPaths(fake_root))
        return TestClient(app, base_url="http://127.0.0.1")

    return project_fixture, llm_fixture, klein_fixture, tts_fixture, client_fixture


# --- what the toon API test files share: no test file imports another ---


def new_series(client, **changes) -> dict:
    body = {"name": "รุ่นพี่เล่าว่า…", "channel_name": "รุ่นพี่เล่าว่า", "layout": "frame", "genre": "horror", "voice_id": TOON_VOICE}
    response = client.post(TOON_SERIES, json=body | changes)
    assert response.status_code == 201, response.json()
    return response.json()


class Writer:
    """Answers a plot prompt and each act's cards prompt the way Qwen is asked to. `cards`
    makes one act's answer from the act's name in the prompt."""

    def __init__(self):
        self.plot: dict | None = None  # set by `with_series`
        self.cards = lambda act: {
            "segments": [
                {
                    "background": self.plot["backgrounds"][0].get("id", "b_unknown"),
                    "sound": None,
                    "cards": [
                        {"text": f"การ์ดแรกของ{act}", "characters": [], "description": "มุมกว้าง", "motion": "zoom_in"},
                        {"text": "", "characters": [], "description": "", "motion": "still"},
                    ],
                }
            ]
        }

    def respond(self, request) -> str:
        if "เขียนพล็อต" in request.prompt:
            return json.dumps(self.plot, ensure_ascii=False)
        act = request.prompt.split("องก์นี้ (")[1].split(")")[0]
        return "```json\n" + json.dumps(self.cards(act), ensure_ascii=False) + "\n```"


def with_series(client, llm) -> tuple[str, str, str]:
    """A horror Series with one character and one background; the plot Qwen writes uses
    the character and proposes a new character and a new background."""
    series_id = new_series(client)["id"]
    character = client.post(f"{TOON_SERIES}/{series_id}/characters", json={"name": "พีค", "tag": "สายแฟ"}).json()["characters"][0]["id"]
    background = client.post(f"{TOON_SERIES}/{series_id}/backgrounds", json={"name": "กองไฟ"}).json()["backgrounds"][0]["id"]
    llm.respond.__self__.plot = {
        "title": "เสียงเรียกจากป่า",
        # One key per act, the way the real Qwen answers the prompt (toon D82).
        "acts": {f"{n}. {name}": f"สรุปองก์ {n}" for n, name in enumerate(["เปิด", "ปม", "หักมุม", "จบหลอน"], start=1)},
        "characters": [{"id": character}, {"id": "c_00000000"}, {"name": "ลุงยาม", "tag": "", "description": "ชายแก่"}],
        "backgrounds": [{"name": "ห้องน้ำชั้นสาม", "description": "ห้องน้ำมืด"}],
    }
    return series_id, character, background


def new_ep(client, series_id: str, idea: str = "รุ่นพี่ไปแคมป์แล้วได้ยินเสียงเรียกชื่อ") -> dict:
    response = client.post(f"{TOON_SERIES}/{series_id}/eps", json={"idea": idea})
    assert response.status_code == 201, response.json()
    return response.json()


def start(client, kind: str, ep_id: str, **body):
    return client.post(TOON_JOBS, json={"kind": kind, "ep_id": ep_id} | body)


def wait_for_toon_job(client) -> dict:
    return poll_until(client, TOON_CURRENT, lambda job: job["state"] in FINISHED)


def run(client, kind: str, ep_id: str, **body) -> dict:
    response = start(client, kind, ep_id, **body)
    assert response.status_code == 202, response.json()
    return wait_for_toon_job(client)


def cards_of(ep: dict) -> list[dict]:
    return [card for act in ep["acts"] for segment in act["segments"] for card in segment["cards"]]


def edit_stored_ep(project: ProjectPaths, series_id: str, ep_id: str, change) -> None:
    """Changes `ep.json` as a job would, for a state the API can't reach yet (images, audio)."""
    ep_address = EpAddress(project, series_id, ep_id)
    ep = store.read_ep(ep_address)
    change(ep)
    store.write_ep(ep_address, ep)


def gpu_refusal() -> ApiError | None:
    """What another job is told when it asks for the GPU slot now."""
    try:
        gpu.slot.take("describe")
    except ApiError as refused:
        return refused
    gpu.slot.release("describe")
    return None


def png(width: int, height: int, color: str = "gray") -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), color).save(out, "PNG")
    return out.getvalue()


def upload(client, series_id: str, kind: str, item_id: str, body: bytes):
    return client.post(
        f"{TOON_SERIES}/{series_id}/{kind}/{item_id}/ref/upload?size={len(body)}",
        content=body,
        headers={"Content-Type": "application/octet-stream"},
    )


def put_background(client, lesson_id: str, body: bytes, size: int | None = None, content_type: str = "application/octet-stream"):
    """`PUT` a drum lesson's background picture as the page does: the raw body with its `size`."""
    return client.put(
        f"/api/drums/lessons/{lesson_id}/background?size={len(body) if size is None else size}",
        content=body,
        headers={"Content-Type": content_type},
    )


def item_with_ref(client, series_id: str, kind: str, name: str, with_ref: bool = True) -> str:
    """A character or background of the Series, with an uploaded reference image."""
    item_id = client.post(f"{TOON_SERIES}/{series_id}/{kind}", json={"name": name}).json()[kind][-1]["id"]
    if with_ref:
        assert upload(client, series_id, kind, item_id, png(64, 64)).status_code == 200
    return item_id


def tone(path: Path, seconds: float, rate: int = 44_100) -> Path:
    """A sine tone made with ffmpeg's `lavfi`, in the format the path's suffix names."""
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=330:sample_rate={rate}:duration={seconds}", str(path),
    ]  # fmt: skip
    subprocess.run(command, check=True)
    return path


def restart(client) -> None:
    """The app's start-up, as a new run of it on the same `paths.ROOT` does: `client` is a
    fixture's, not inside a `with` yet, so this `with` runs the lifespan."""
    with client:
        pass


def write_library(project: ProjectPaths, body: object) -> None:
    """`sounds.json` as `body` says: a text as it is (a broken one), anything else as JSON."""
    project.sounds_dir.mkdir(parents=True, exist_ok=True)
    project.sounds_file.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")


def write_sound(project: ProjectPaths, name: str = "ฝนตก", seconds: float = 1.0, sound_id: str = "m_0000abcd") -> dict:
    """One sound in the library as an import leaves it: its tone as m4a and its entry."""
    project.sounds_dir.mkdir(parents=True, exist_ok=True)
    tone(project.sounds_dir / f"{sound_id}.m4a", seconds)
    sound = {"id": sound_id, "name": name, "duration_s": seconds, "source": "file"}
    listed = json.loads(project.sounds_file.read_text(encoding="utf-8"))["sounds"] if project.sounds_file.is_file() else []
    write_library(project, {"version": 1, "sounds": [*listed, sound]})
    return sound


def write_spoil_draft(project: ProjectPaths, n: int = 2, sound: dict | None = None) -> None:
    """A Spoil draft of EP `n` of the Temp clip "ชื่อคลิป", with no sentence."""
    clip = write_temp_clip(project)
    draft = {
        "version": 2, "clip_id": clip["id"], "ep": {"n": n, "start_s": 0.0, "end_s": 100.0}, "style": "drama",
        "layout": "B", "target_s": 60, "voice_id": "v_0000abcd", "original_volume": 20, "top_text": "",
        "sentences": [], "sound": sound,
    }  # fmt: skip
    project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
    project.draft_file.write_text(json.dumps(draft), encoding="utf-8")


def import_file(client, name: str, body: bytes):
    return client.post(
        f"{SOUNDS}/imports?name={name}&size={len(body)}", content=body, headers={"Content-Type": "application/octet-stream"}
    )


def import_tone(client, tmp_path, name: str = "ฝนตก.wav", seconds: float = 1.5) -> dict:
    response = import_file(client, name, tone(tmp_path / "in.wav", seconds).read_bytes())
    assert response.status_code == 201, response.json()
    return response.json()
