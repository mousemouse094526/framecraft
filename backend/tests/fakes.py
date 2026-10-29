"""Fake project roots and probes shared by the backend tests."""

import json
import threading
from pathlib import Path

from backend.checks import FfmpegInfo
from backend.models import MODELS, ModelSpec
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.spoil.whisper import Done, Segment

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


def ok_ffmpeg() -> FfmpegInfo:
    return FfmpegInfo(version="7.1", source="imageio-ffmpeg")


def broken_ffmpeg() -> FfmpegInfo:
    raise RuntimeError("ffmpeg -version exited with 1")


def ok_yt_dlp() -> str:
    return "2026.10.26"


def ok_deno() -> str:
    return "2.9.8"


def broken_deno() -> str:
    raise FileNotFoundError("deno")


def cuda_device() -> str:
    return "cuda"


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
