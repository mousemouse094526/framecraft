"""Fake project roots and probes shared by the backend tests."""

import dataclasses
import json
import threading
import time
from collections.abc import Callable
from pathlib import Path

from backend.checks import FfmpegInfo, GpuInfo, Probes
from backend.models import MODELS, ModelSpec
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.spoil.whisper import Done, Segment



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
    """Create the files snapshot_download would leave for one model."""
    snapshot = ProjectPaths(root).snapshot_dir(model, revision or model.revision)
    for name, size in MODEL_FILES.items():
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * size)
    return snapshot


def write_marker(root: Path, model: ModelSpec, revision: str | None = None) -> Path:
    marker = ProjectPaths(root).marker(model)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps(
            {
                "repo_id": model.repo_id,
                "revision": revision or model.revision,
                "files": [{"path": n, "size": s} for n, s in MODEL_FILES.items()],
                "size_bytes": sum(MODEL_FILES.values()),
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


def os_timeouts(monkeypatch, darwin: float, win32: float) -> None:
    """Swaps `llm.TIMEOUTS` so every step of the Mac and of Windows has the given seconds."""
    from backend.spoil_maker import llm

    monkeypatch.setattr(llm, "TIMEOUTS", {"darwin": llm.Timeouts(*[darwin] * 4), "win32": llm.Timeouts(*[win32] * 4)})


# A fake answer this slow outlasts a Mac timeout of 0.2 s and fits a Windows one of 1 s.
SLOW_ANSWER_SECONDS = 0.5


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

    def download(self, info: dict, project: ProjectPaths, on_progress) -> Path:
        self.download_calls += 1
        video_id = info["id"]
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

    Each start runs a thread that says `ready()`, then one `answer(request, index)`
    per request, `index` counting that process's requests from 0. It can pause
    before answering request `index` until the test calls
    `release` (or the process is terminated) with `pause_at`, never answer it
    (`hang_at`, for timeouts), or exit at it without a word (`crash_at`). An
    `answer` of `HANG` never comes either, whichever process asked.
    """

    HANG = object()

    def __init__(self):
        self.requests = []
        self.processes: list["FakeModelProcess"] = []
        self.crash_at: int | None = None
        self.hang_at: int | None = None
        self._paused: dict[int, threading.Event] = {}
        self._reached: dict[int, threading.Event] = {}

    def ready(self):
        raise NotImplementedError

    def answer(self, request, index: int):
        raise NotImplementedError

    def pause_at(self, index: int) -> None:
        self._paused[index] = threading.Event()
        self._reached[index] = threading.Event()

    def wait_until(self, index: int) -> None:
        assert self._reached[index].wait(5), f"the model never reached request {index}"

    def release(self, index: int) -> None:
        self._paused[index].set()

    def __call__(self, snapshot_dir: Path, *args):
        import queue

        requests: queue.Queue = queue.Queue()
        replies: queue.Queue = queue.Queue()
        process = FakeModelProcess(self, snapshot_dir, args, requests, replies)
        self.processes.append(process)
        process.start()
        return process, requests, replies


class FakeLlm(FakeModel):
    """The mlx-vlm child: `respond(request)` makes each `Generated` text, or is `HANG`."""

    def __init__(self):
        super().__init__()
        self.respond = lambda request: f"A frame at {request.image.name}."

    def ready(self):
        from backend.spoil_maker.llm import Ready

        return Ready()

    def answer(self, request, index: int):
        from backend.spoil_maker.llm import Generated

        text = self.respond(request)
        return text if text is self.HANG else Generated(text)


class FakeTts(FakeModel):
    """The OmniVoice child: every request is spoken as `seconds` of silence at 24 kHz;
    a `Design` also gets the clone prompt `b"prompt {n}"`, `n` counting every request
    it got from 0. `fail_at` answers that request of a process with a `WorkerError` instead."""

    SAMPLE_RATE = 24_000

    def __init__(self):
        super().__init__()
        self.seconds = 2.0
        self.fail_at: int | None = None

    def ready(self):
        from backend.spoil_maker.tts import Ready

        return Ready()

    def answer(self, request, index: int):
        from backend.spoil_maker.tts import Designed, Speak, Spoken, WorkerError

        if index == self.fail_at:
            return WorkerError("model_failed", "RuntimeError: MPS out of memory")
        audio = b"\0\0" * round(self.SAMPLE_RATE * self.seconds)
        if isinstance(request, Speak):
            return Spoken(audio=audio, sample_rate=self.SAMPLE_RATE)
        prompt = f"prompt {len(self.requests) - 1}".encode()
        return Designed(audio=audio, sample_rate=self.SAMPLE_RATE, prompt=prompt)


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
        self._replies.put(model.ready())
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
            answer = model.HANG if index == model.hang_at else model.answer(request, index)
            if answer is model.HANG:
                self._killed.wait()
            if self._killed.is_set():
                break
            self._replies.put(answer)
            index += 1
        self.exitcode = -15 if self._killed.is_set() else 0


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
