"""File import under /api/spoil/imports: a local mp4 sent as a raw body becomes a Temp
clip (spoil seam 1, spec › File import, D49–D52, D55, ADR 0028).

ffmpeg is real: the uploads are made with `lavfi`. `TestClient` sends a body in one go,
so a body that pauses, stalls or is dropped mid-way is played through the app as ASGI,
in the same event loop as the requests made meanwhile (docs/library-notes/fastapi.md).
"""

import hashlib
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import NamedTuple

import anyio
import httpx
import imageio_ffmpeg
import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil
from backend.app import app
from backend.paths import ProjectPaths
from backend.spoil import downloads, imports, mp4check

from .fakes import FakeAdapter, FakeMp4Check, Gate, Upload, broken_ffmpeg, ok_deno, ok_ffmpeg, ok_yt_dlp, play

GB = 1_000_000_000
OCTET = {"Content-Type": "application/octet-stream"}
URL = "https://youtu.be/dQw4w9WgXcQ"
ADVICE = "แปลงเป็น mp4 (H.264, AAC) ไม่เกิน 1080p ด้วยโปรแกรมอื่นแล้วลองอีกครั้ง"


def make_upload(path: Path, size: str = "640x360", video: str = "libx264", audio: str | None = "aac") -> Path:
    """A 2-second clip of a test pattern with a tone, made by ffmpeg's `lavfi`."""
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-y"]
    command += ["-f", "lavfi", "-i", f"testsrc=s={size}:r=10:d=2"]
    if audio:
        command += ["-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:a", audio]
    command += ["-c:v", video, "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(command, check=True)
    return path


class Uploads(NamedTuple):
    good: Path
    silent: Path
    hevc: Path
    too_big: Path
    opus: Path
    mkv: Path
    junk: Path


@pytest.fixture(scope="session")
def uploads(tmp_path_factory) -> Uploads:
    folder = tmp_path_factory.mktemp("uploads")
    junk = folder / "junk.mp4"
    junk.write_bytes(b"not a video at all" * 100)
    return Uploads(
        good=make_upload(folder / "good.mp4"),
        silent=make_upload(folder / "silent.mp4", audio=None),
        hevc=make_upload(folder / "hevc.mp4", video="libx265"),
        too_big=make_upload(folder / "big.mp4", size="1920x1440"),
        opus=make_upload(folder / "opus.mp4", audio="libopus"),
        mkv=make_upload(folder / "clip.mkv"),
        junk=junk,
    )


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def adapter(monkeypatch) -> FakeAdapter:
    fake = FakeAdapter()
    monkeypatch.setattr(spoil, "adapter", fake)
    return fake


@pytest.fixture
def client(fake_root, adapter, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(spoil, "free_bytes", lambda path: 100 * GB)
    monkeypatch.setattr(downloads, "downloads", downloads.Downloads(check_mp4=FakeMp4Check()))
    monkeypatch.setattr(imports, "imports", imports.Imports())
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    return TestClient(app, base_url="http://127.0.0.1")


def local_id(name: str, size: int) -> str:
    """The id spec › id ของ Temp clip gives a local file, written out apart from the code."""
    return "local-" + hashlib.sha1(f"{name}|{size}".encode()).hexdigest()[:12]


def send(client, data: bytes, name: str | None = "a.mp4", size: int | str | None = None, headers=OCTET):
    params = {"name": name, "size": len(data) if size is None else size}
    params = {key: value for key, value in params.items() if value is not None}
    return client.post("/api/spoil/imports", params=params, content=data, headers=headers)


def ask(client, name: object = "new.mp4", size: object = 1000):
    return client.post("/api/spoil/imports/check", json={"name": name, "size": size})


def refusal(response) -> tuple[int, str]:
    return response.status_code, response.json()["code"]


def partial_files(project: ProjectPaths) -> list[str]:
    return sorted(p.name for p in project.partial_dir.glob("*")) if project.partial_dir.is_dir() else []


def temp_files(project: ProjectPaths) -> list[str]:
    """The files in media/temp/, not `.partial/`."""
    return sorted(p.name for p in project.media_temp_dir.glob("*") if p.is_file()) if project.media_temp_dir.is_dir() else []


def assert_free(client) -> None:
    """Another file may come in now: the "receiving a file" flag is down."""
    assert ask(client, "next.mp4").status_code == 200


# --- An mp4 from start to end ---


def test_a_playable_mp4_becomes_a_temp_clip_byte_for_byte(client, project, uploads):
    data = uploads.good.read_bytes()
    clip_id = local_id("My Clip.MP4", len(data))

    response = send(client, data, name="My Clip.MP4")

    assert response.status_code == 201
    clip = response.json()
    assert clip.pop("downloaded_at")
    assert clip == {
        "id": clip_id,
        "title": "My Clip",
        "channel": None,
        "site": "local",
        "source_url": None,
        "duration_s": 2,
        "width": 640,
        "height": 360,
        "orientation": "landscape",
        "file_bytes": len(data),
        "thumbnail": f"{clip_id}.jpg",
        "yt_dlp_version": None,
        "trimmed": [],
        "trimmed_at": None,
    }
    assert (project.media_temp_dir / f"{clip_id}.mp4").read_bytes() == data
    assert (project.media_temp_dir / f"{clip_id}.jpg").read_bytes()[:3] == b"\xff\xd8\xff"
    stored = json.loads((project.media_temp_dir / f"{clip_id}.json").read_text(encoding="utf-8"))
    assert stored["site"] == "local"
    assert partial_files(project) == []


def test_an_imported_clip_is_listed_played_and_deleted_like_a_downloaded_one(client, project, uploads):
    clip_id = send(client, uploads.good.read_bytes()).json()["id"]

    listed = client.get("/api/spoil/clips").json()["clips"]
    assert [row["id"] for row in listed] == [clip_id]
    assert listed[0]["transcribed"] is False
    assert client.get(f"/api/spoil/clips/{clip_id}/video", headers={"Range": "bytes=0-99"}).status_code == 206
    assert client.get(f"/api/spoil/clips/{clip_id}/thumbnail").headers["content-type"] == "image/jpeg"
    assert client.delete(f"/api/spoil/clips/{clip_id}").status_code == 204
    assert temp_files(project) == []


def test_a_clip_with_no_sound_comes_in(client, uploads):
    response = send(client, uploads.silent.read_bytes())

    assert response.status_code == 201


def test_a_thumbnail_ffmpeg_could_not_make_is_null(client, project, uploads, monkeypatch):
    # ffmpeg 7.1 seeking past the end exits 0 with no frame written (checked by hand). Told the clip is far longer than it is, ffmpeg seeks past its end and writes no frame.
    monkeypatch.setattr(imports, "imports", imports.Imports(check_mp4=lambda path: mp4check.Mp4Info(5000.0, 640, 360)))

    response = send(client, uploads.good.read_bytes())

    assert response.status_code == 201
    assert response.json()["thumbnail"] is None
    assert [name for name in temp_files(project) if name.endswith(".jpg")] == []


# --- Files that are refused ---


@pytest.mark.parametrize(
    ("upload", "reason"),
    [
        ("hevc", "ภาพเป็น hevc"),
        ("too_big", "ภาพ 1920×1440 ด้านสั้นเกิน 1080"),
        ("opus", "เสียงเป็น opus"),
        ("mkv", "ไฟล์ไม่ใช่ mp4"),
        ("junk", "อ่านไฟล์ไม่ได้"),
    ],
)
def test_a_file_that_breaks_the_rule_is_unsupported_file_and_leaves_nothing(client, project, uploads, upload, reason):
    response = send(client, getattr(uploads, upload).read_bytes())

    assert response.status_code == 400
    assert response.json() == {"code": "unsupported_file", "message": f"{reason}. {ADVICE}"}
    assert partial_files(project) == []
    assert temp_files(project) == []
    assert_free(client)


@pytest.mark.parametrize("name", ["a.mkv", "a.mp4.mov", "mp4"])
def test_a_name_not_ending_in_mp4_is_not_mp4_and_the_body_is_not_written(client, project, uploads, name):
    response = send(client, uploads.good.read_bytes(), name=name)

    assert response.status_code == 400
    assert response.json() == {"code": "not_mp4", "message": "รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน"}
    assert partial_files(project) == []
    assert temp_files(project) == []


@pytest.mark.parametrize("size", [None, "", "abc", "0", "-5", "1.5", "1e3"])
def test_a_missing_or_bad_size_is_invalid_request(client, size):
    params = {"name": "a.mp4"} if size is None else {"name": "a.mp4", "size": size}

    response = client.post("/api/spoil/imports", params=params, content=b"x", headers=OCTET)

    assert refusal(response) == (400, "invalid_request")


@pytest.mark.parametrize("name", [None, "", ".mp4"])
def test_a_missing_or_empty_name_is_invalid_request(client, name):
    assert refusal(send(client, b"x", name=name)) == (400, "invalid_request")


def test_more_bytes_than_size_is_size_mismatch(client, project, uploads):
    data = uploads.good.read_bytes()

    response = send(client, data, size=len(data) - 1)

    assert response.status_code == 400
    assert response.json() == {"code": "size_mismatch", "message": "ได้ไฟล์ไม่ครบหรือเกินขนาดที่บอก ลองอีกครั้ง"}
    assert partial_files(project) == []
    assert_free(client)


def test_fewer_bytes_than_size_is_size_mismatch(client, project, uploads):
    data = uploads.good.read_bytes()

    response = send(client, data, size=len(data) + 1)

    assert refusal(response) == (400, "size_mismatch")
    assert partial_files(project) == []
    assert temp_files(project) == []


def test_without_ffmpeg_both_routes_are_not_ready_before_any_other_check(client, monkeypatch):
    monkeypatch.setattr(checks, "probe_ffmpeg", broken_ffmpeg)

    for response in (send(client, b"x", name="a.mkv"), ask(client, "a.mkv")):
        assert response.status_code == 503
        assert response.json() == {"code": "not_ready", "message": "ยังติดตั้งไม่ครบ: ffmpeg", "rows": ["ffmpeg"]}


def test_too_little_disk_is_disk_full_on_both_routes(client, project, monkeypatch):
    monkeypatch.setattr(spoil, "free_bytes", lambda path: 2**30 + 999)

    for response in (send(client, b"x" * 1000), ask(client, "a.mp4", 1000)):
        assert response.status_code == 409
        assert response.json() == {"code": "disk_full", "message": "ที่ว่างไม่พอ: ต้องการ 1.1 GB มี 1.1 GB"}
    assert partial_files(project) == []
    monkeypatch.setattr(spoil, "free_bytes", lambda path: 100 * GB)
    assert_free(client)


def test_an_error_nobody_expected_still_frees_the_flag_and_leaves_nothing(client, project, uploads, monkeypatch):
    def broken(path):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(imports, "imports", imports.Imports(check_mp4=broken))
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)

    assert send(client, uploads.good.read_bytes()).status_code == 500
    assert partial_files(project) == []
    assert temp_files(project) == []
    assert_free(client)


# --- Duplicates and the check ---


def test_the_same_name_and_size_again_is_duplicate_on_both_routes(client, project, uploads):
    data = uploads.good.read_bytes()
    clip_id = send(client, data).json()["id"]

    for response in (send(client, data), ask(client, "a.mp4", len(data))):
        assert response.status_code == 409
        assert response.json() == {"code": "duplicate", "message": "ไฟล์นี้เอาเข้าไว้แล้ว", "clip_id": clip_id}
    assert partial_files(project) == []


def test_the_check_of_a_new_file_gives_the_id_the_import_then_makes(client, uploads):
    data = uploads.good.read_bytes()

    checked = ask(client, "b.mp4", len(data))

    assert checked.status_code == 200
    assert checked.json() == {"clip_id": local_id("b.mp4", len(data))}
    assert send(client, data, name="b.mp4").json()["id"] == checked.json()["clip_id"]


@pytest.mark.parametrize(
    "body",
    [
        {"name": "a.mp4"},
        {"size": 10},
        {"name": 5, "size": 10},
        {"name": "a.mp4", "size": "10"},
        {"name": "a.mp4", "size": 1.5},
        {"name": "a.mp4", "size": True},
        {"name": "a.mp4", "size": 0},
        ["a.mp4", 10],
    ],
)
def test_a_check_with_a_bad_name_or_size_is_invalid_request(client, body):
    response = client.post("/api/spoil/imports/check", json=body)

    assert refusal(response) == (400, "invalid_request")


def test_the_check_of_a_name_not_ending_in_mp4_is_not_mp4(client):
    assert refusal(ask(client, "a.mov")) == (400, "not_mp4")


# --- One at a time with the Download job ---


def test_while_a_download_runs_an_import_is_busy_but_a_duplicate_is_still_duplicate(client, adapter, uploads):
    data = uploads.good.read_bytes()
    clip_id = send(client, data).json()["id"]
    adapter.pause_at("fetch")
    assert client.post("/api/spoil/downloads", json={"url": URL}).status_code == 202
    adapter.wait_until("fetch")

    busy = send(client, data, name="other.mp4")
    asked = ask(client, "other.mp4")
    again = send(client, data)

    adapter.release("fetch")
    assert busy.status_code == 409
    assert busy.json() == {"code": "busy", "message": "กำลังโหลดหรือเอาไฟล์อื่นเข้าอยู่"}
    assert refusal(asked) == (409, "busy")
    assert (again.status_code, again.json()["clip_id"]) == (409, clip_id)


def api() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1")


def test_while_a_file_comes_in_downloads_and_other_imports_are_busy(client, project, uploads):
    data = uploads.good.read_bytes()
    gate = Gate(data[1000:])
    upload = Upload(data[:1000], gate)
    answers: dict = {}

    async def main():
        async with api() as http, anyio.create_task_group() as group:

            async def run_import():
                answers["import"] = await play(upload, "a.mp4", len(data))

            group.start_soon(run_import)
            await gate.reached.wait()
            answers["partial"] = partial_files(project)
            started = time.monotonic()
            answers["poll"] = await http.get("/api/spoil/downloads/current")
            answers["poll_seconds"] = time.monotonic() - started
            answers["download"] = await http.post("/api/spoil/downloads", json={"url": URL})
            answers["other"] = await http.post(
                "/api/spoil/imports", params={"name": "b.mp4", "size": 3}, content=b"abc", headers=OCTET
            )
            answers["check"] = await http.post("/api/spoil/imports/check", json={"name": "b.mp4", "size": 3})
            gate.open()

    anyio.run(main)

    assert answers["partial"] == [f"{local_id('a.mp4', len(data))}.import.mp4"]
    assert (answers["poll"].status_code, answers["poll_seconds"] < 1) == (200, True)
    assert refusal(answers["download"]) == (409, "busy")
    assert refusal(answers["other"]) == (409, "busy")
    assert refusal(answers["check"]) == (409, "busy")
    assert answers["import"][0] == 201
    assert client.post("/api/spoil/downloads", json={"url": URL}).status_code == 202


class PausedCheck:
    """The real mp4 check, held until the test releases it: ffmpeg running long."""

    def __init__(self):
        self.reached = threading.Event()
        self.released = threading.Event()

    def __call__(self, path: Path) -> mp4check.Mp4Info:
        self.reached.set()
        assert self.released.wait(5), "the test never released the check"
        return mp4check.check(path)


def test_polling_the_download_job_answers_while_ffmpeg_checks_the_file(client, uploads, monkeypatch):
    paused = PausedCheck()
    monkeypatch.setattr(imports, "imports", imports.Imports(check_mp4=paused))
    data = uploads.good.read_bytes()
    answers: dict = {}

    async def main():
        async with api() as http, anyio.create_task_group() as group:

            async def run_import():
                answers["import"] = await play(Upload(data), "a.mp4", len(data))

            group.start_soon(run_import)
            assert await anyio.to_thread.run_sync(paused.reached.wait, 5)
            started = time.monotonic()
            answers["poll"] = await http.get("/api/spoil/downloads/current")
            answers["seconds"] = time.monotonic() - started
            paused.released.set()

    anyio.run(main)

    assert answers["poll"].status_code == 200
    assert answers["seconds"] < 1
    assert answers["import"][0] == 201


def test_a_body_that_stops_coming_is_stalled_and_frees_the_flag(client, project, uploads, monkeypatch):
    # The 60-second limit shortened: the body never comes, so the wait is the limit itself.
    monkeypatch.setattr(imports, "imports", imports.Imports(stall_seconds=0.2))
    data = uploads.good.read_bytes()

    status, body = anyio.run(play, Upload(data[:1000], then="stall"), "a.mp4", len(data))

    assert status == 408
    assert body == {"code": "stalled", "message": "ไม่ได้รับข้อมูลไฟล์นาน 60 วินาที ลองอีกครั้ง"}
    assert partial_files(project) == []
    assert temp_files(project) == []
    assert send(client, data).status_code == 201


def test_a_client_that_goes_away_mid_way_leaves_nothing_and_frees_the_flag(client, project, uploads):
    data = uploads.good.read_bytes()

    status, body = anyio.run(play, Upload(data[:1000], then="disconnect"), "a.mp4", len(data))

    assert (status, body) == (400, None)  # nobody reads it; not a 500
    assert partial_files(project) == []
    assert temp_files(project) == []
    assert send(client, data).status_code == 201


# --- Raw bodies on this route only (ADR 0013, ADR 0028) ---


@pytest.mark.parametrize(
    "headers",
    [{"Content-Type": "application/json"}, {"Content-Type": "multipart/form-data; boundary=x"}, {}],
)
def test_an_import_that_is_not_octet_stream_is_415(client, project, headers):
    response = send(client, b"x" * 10, headers=headers)

    assert response.status_code == 415
    assert response.json() == {"code": "unsupported_media_type", "message": "ต้องส่งเป็นไฟล์ (application/octet-stream)"}
    assert partial_files(project) == []


@pytest.mark.parametrize(
    "path",
    [
        "/api/spoil/imports/check",
        "/api/spoil/downloads",
        "/api/spoil/transcriptions",
        "/api/spoil/trims",
        "/api/spoil-maker/describes",
    ],
)
@pytest.mark.parametrize("content_type", ["application/octet-stream", "multipart/form-data; boundary=x"])
def test_every_other_post_that_is_octet_stream_or_multipart_is_415(client, path, content_type):
    response = client.post(path, content=b"{}", headers={"Content-Type": content_type})

    assert response.status_code == 415
    assert response.json() == {"code": "unsupported_media_type", "message": "ต้องส่งเป็น JSON"}
