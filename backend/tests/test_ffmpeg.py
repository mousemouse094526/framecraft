"""`ffmpeg.run_piped`, frames through stdin (video-gen D22), with real ffmpeg on tiny raw frames.
`h264_args` is checked through spoil's trim command (`test_spoil_trim_api.py`)."""

import threading

import pytest

from backend import ffmpeg
from backend.ffmpeg import FfmpegFailed
from backend.jobs import Cancelled

SIZE = 16
FRAME = bytes(SIZE * SIZE * 3)


def command(out, *extra: str) -> list[str]:
    return [
        ffmpeg.exe(), "-hide_banner", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{SIZE}x{SIZE}", "-r", "30", "-i", "-",
        *extra, "-f", "mp4", str(out),
    ]  # fmt: skip


def test_every_frame_goes_through_stdin_and_each_is_counted(tmp_path):
    sent: list[int] = []
    ffmpeg.run_piped(command(tmp_path / "out.mp4"), tmp_path, threading.Event(), [FRAME] * 30, sent.append)

    assert sent == list(range(1, 31))
    assert ffmpeg.probe(tmp_path / "out.mp4").duration_s == pytest.approx(1.0, abs=0.05)


def test_a_cancel_between_frames_kills_ffmpeg_and_raises_cancelled(tmp_path):
    cancel = threading.Event()

    def frames():
        for n in range(1000):
            if n == 5:
                cancel.set()
            yield FRAME

    sent: list[int] = []
    with pytest.raises(Cancelled):
        ffmpeg.run_piped(command(tmp_path / "out.mp4"), tmp_path, cancel, frames(), sent.append)
    assert sent[-1] == 5


def test_ffmpeg_that_stops_at_its_start_fails_with_the_last_line_of_stderr(tmp_path):
    bad = command(tmp_path / "out.mp4", "-vf", "ass=text.ass:nope=1")

    with pytest.raises(FfmpegFailed) as failed:
        ffmpeg.run_piped(bad, tmp_path, threading.Event(), [FRAME] * 300, lambda _: None)
    assert failed.value.last_line == "Error opening output files: Option not found"


def test_a_frame_that_cant_be_drawn_stops_ffmpeg_and_raises_its_error(tmp_path):
    def frames():
        yield FRAME
        raise ValueError("no picture")

    with pytest.raises(ValueError, match="no picture"):
        ffmpeg.run_piped(command(tmp_path / "out.mp4"), tmp_path, threading.Event(), frames(), lambda _: None)


# --- run_capture (drum-notes D20) ---


def test_run_capture_returns_the_raw_pcm_ffmpeg_writes_to_stdout():
    command = [ffmpeg.exe(), "-nostdin", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=8000:duration=0.5", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"]

    pcm = ffmpeg.run_capture(command, threading.Event())

    assert len(pcm) == 4000 * 4  # 0.5 s of float32 mono at 8 kHz


def test_run_capture_kills_ffmpeg_on_cancel_and_raises_cancelled():
    cancel = threading.Event()
    command = [ffmpeg.exe(), "-nostdin", "-v", "error", "-re", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=8000:duration=30", "-f", "f32le", "-"]
    threading.Timer(0.3, cancel.set).start()

    with pytest.raises(Cancelled):
        ffmpeg.run_capture(command, cancel)


def test_run_capture_of_a_file_that_is_not_there_fails_with_the_last_line_of_stderr(tmp_path):
    command = [ffmpeg.exe(), "-nostdin", "-v", "error", "-i", str(tmp_path / "missing.m4a"), "-f", "f32le", "-"]

    with pytest.raises(FfmpegFailed) as caught:
        ffmpeg.run_capture(command, threading.Event())

    assert caught.value.last_line == "Error opening input files: No such file or directory"
