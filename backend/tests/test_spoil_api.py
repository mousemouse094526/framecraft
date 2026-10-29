"""The Download job API under /api/spoil, with a fake yt-dlp adapter (spoil seam 1)."""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from yt_dlp.utils import ExtractorError, GeoRestrictedError

from backend import checks, paths, spoil
from backend.app import app
from backend.models import OMNIVOICE
from backend.paths import ProjectPaths
from backend.spoil import downloads

from .fakes import (
    FakeAdapter,
    ok_deno,
    ok_ffmpeg,
    ok_yt_dlp,
    write_temp_clip,
    youtube_info,
    yt_dlp_error,
)

GB = 1_000_000_000
URL = "https://youtu.be/dQw4w9WgXcQ"
VIDEO_ID = "dQw4w9WgXcQ"
FINISHED = {"done", "failed", "cancelled"}


@pytest.fixture
def adapter(monkeypatch) -> FakeAdapter:
    fake = FakeAdapter()
    monkeypatch.setattr(spoil, "adapter", fake)
    return fake


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def client(fake_root, adapter, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(spoil, "free_bytes", lambda path: 100 * GB)
    monkeypatch.setattr(downloads, "downloads", downloads.Downloads())
    return TestClient(app, base_url="http://127.0.0.1")


def start(client, url: str = URL):
    return client.post("/api/spoil/downloads", json={"url": url})


def current(client) -> dict | None:
    return client.get("/api/spoil/downloads/current").json()


def wait_for_end(client) -> dict:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = current(client)
        if job["state"] in FINISHED:
            return job
        time.sleep(0.01)
    raise AssertionError(f"job never finished: {job}")


def files_named(folder, video_id: str = VIDEO_ID) -> list[str]:
    return sorted(p.name for p in folder.glob(f"{video_id}.*"))


# --- Links ---


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123&t=42s",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ?si=abc",
        "https://youtu.be/dQw4w9WgXcQ",
        "http://youtu.be/dQw4w9WgXcQ?si=abc",
        "  https://youtu.be/dQw4w9WgXcQ  ",
    ],
)
def test_every_accepted_link_shape_starts_a_job(client, adapter, url):
    response = start(client, url)

    assert response.status_code == 202
    assert response.json()["id"] == VIDEO_ID
    assert wait_for_end(client)["state"] == "done"
    # yt-dlp doesn't match a link with spaces around it.
    assert adapter.fetched_urls == [url.strip()]


@pytest.mark.parametrize(
    "url",
    [
        "https://vimeo.com/1",
        "https://www.youtube.com/playlist?list=x",
        "https://www.youtube.com/watch?v=short",
        "ftp://youtu.be/dQw4w9WgXcQ",
    ],
)
def test_links_outside_the_table_are_invalid_url(client, url):
    response = start(client, url)

    assert response.status_code == 400
    assert response.json() == {"code": "invalid_url", "message": "ลิงก์นี้ไม่ใช่ลิงก์คลิป YouTube"}


# --- A job that succeeds ---


def test_no_job_since_start_is_null(client):
    assert client.get("/api/spoil/downloads/current").json() is None


def test_polling_shows_checking_downloading_merging_then_done(client, adapter):
    for point in ("fetch", "progress", "merge"):
        adapter.pause_at(point)

    assert start(client).status_code == 202
    adapter.wait_until("fetch")
    checking = current(client)
    adapter.release("fetch")
    adapter.wait_until("progress")
    downloading = current(client)
    adapter.release("progress")
    adapter.wait_until("merge")
    merging = current(client)
    adapter.release("merge")
    done = wait_for_end(client)

    assert (checking["state"], checking["title"], checking["percent"]) == ("checking", None, None)
    # 400 of an estimated 1000 + 100 bytes
    assert (downloading["state"], downloading["percent"]) == ("downloading", 36)
    assert downloading["title"] == "ชื่อคลิป"
    assert (merging["state"], merging["percent"]) == ("merging", None)
    assert done == {
        "url": URL,
        "id": VIDEO_ID,
        "state": "done",
        "title": "ชื่อคลิป",
        "percent": None,
        "cancel_requested": False,
        "error": None,
        "clip_id": VIDEO_ID,
    }


def test_done_job_leaves_mp4_thumbnail_and_complete_json(client, project):
    start(client)
    wait_for_end(client)

    assert files_named(project.media_temp_dir) == [
        f"{VIDEO_ID}.json",
        f"{VIDEO_ID}.mp4",
        f"{VIDEO_ID}.webp",
    ]
    clip = json.loads((project.media_temp_dir / f"{VIDEO_ID}.json").read_text(encoding="utf-8"))
    downloaded_at = clip.pop("downloaded_at")
    assert clip == {
        "id": VIDEO_ID,
        "title": "ชื่อคลิป",
        "channel": "ชื่อช่อง",
        "source_url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "duration_s": 213,
        "width": 1920,
        "height": 1080,
        "orientation": "landscape",
        "file_bytes": 1234,
        "thumbnail": f"{VIDEO_ID}.webp",
        "yt_dlp_version": "2026.10.26",
    }
    assert downloaded_at[:2] == "20" and downloaded_at[-6] in "+-"
    assert files_named(project.partial_dir) == []


def test_a_taller_than_wide_video_is_portrait(client, adapter, project):
    adapter.info["requested_formats"][0] |= {"width": 1080, "height": 1920}

    start(client)
    wait_for_end(client)

    clip = json.loads((project.media_temp_dir / f"{VIDEO_ID}.json").read_text(encoding="utf-8"))
    assert (clip["width"], clip["height"], clip["orientation"]) == (1080, 1920, "portrait")


def test_unknown_size_gives_percent_null(client, adapter):
    adapter.info = youtube_info(requested_formats=None)
    adapter.events = [
        {"status": "downloading", "filename": "a.mp4", "downloaded_bytes": 400, "total_bytes": None},
        {"status": "finished", "filename": "a.mp4", "downloaded_bytes": 900, "total_bytes": None},
    ]
    adapter.pause_at("progress")

    start(client)
    adapter.wait_until("progress")
    downloading = current(client)
    adapter.release("progress")

    assert (downloading["state"], downloading["percent"]) == ("downloading", None)
    assert wait_for_end(client)["state"] == "done"


def test_size_from_bitrate_and_percent_never_passes_100(client, adapter):
    # 8 kbps for 1 s = 1000 bytes estimated, but 5000 come in.
    adapter.info = youtube_info(requested_formats=None, tbr=8, duration=1)
    adapter.events = [
        {"status": "downloading", "filename": "a.mp4", "downloaded_bytes": 5000, "total_bytes": None},
        {"status": "finished", "filename": "a.mp4", "downloaded_bytes": 5000, "total_bytes": None},
    ]
    adapter.pause_at("progress")

    start(client)
    adapter.wait_until("progress")
    downloading = current(client)
    adapter.release("progress")

    assert downloading["percent"] == 100
    wait_for_end(client)


def test_percent_does_not_go_back_when_a_format_restarts(client, adapter):
    adapter.events = [
        {"status": "downloading", "filename": "v.mp4", "downloaded_bytes": 400, "total_bytes": 1000},
        {"status": "downloading", "filename": "v.mp4", "downloaded_bytes": 100, "total_bytes": 1000},
        {"status": "finished", "filename": "v.mp4", "downloaded_bytes": 1000, "total_bytes": 1000},
        {"status": "finished", "filename": "a.m4a", "downloaded_bytes": 100, "total_bytes": 100},
    ]
    adapter.pause_at("merge")
    seen = []
    original = adapter.download

    def download(info, project, on_progress):
        def record(event):
            on_progress(event)
            seen.append(current(client)["percent"])

        return original(info, project, record)

    adapter.download = download
    start(client)
    adapter.wait_until("merge")
    adapter.release("merge")
    wait_for_end(client)

    assert seen[:2] == [36, 36]


# --- Refused before a job starts ---


def test_a_json_that_cant_be_written_fails_the_job_and_leaves_no_files(client, project, monkeypatch):
    def replace(source, target):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", replace)

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert files_named(project.media_temp_dir) == []


def test_link_of_a_clip_that_has_json_is_duplicate(client, project):
    project.media_temp_dir.mkdir(parents=True)
    (project.media_temp_dir / f"{VIDEO_ID}.json").write_text("{}", encoding="utf-8")

    response = start(client, f"https://www.youtube.com/watch?v={VIDEO_ID}")

    assert response.status_code == 409
    assert response.json() == {
        "code": "duplicate",
        "message": "คลิปนี้โหลดไว้แล้ว",
        "clip_id": VIDEO_ID,
    }


def test_post_while_a_job_is_unfinished_is_busy(client, adapter):
    adapter.pause_at("fetch")
    start(client)
    adapter.wait_until("fetch")

    response = start(client, "https://youtu.be/aaaaaaaaaaa")
    adapter.release("fetch")

    assert response.status_code == 409
    assert response.json() == {"code": "busy", "message": "กำลังโหลดคลิปอื่นอยู่"}
    assert wait_for_end(client)["state"] == "done"


def test_two_posts_at_once_give_one_202_and_one_busy(client, adapter):
    adapter.pause_at("fetch")
    barrier = threading.Barrier(2)
    codes: list[int] = []

    def post(url):
        barrier.wait()
        codes.append(start(client, url).status_code)

    threads = [
        threading.Thread(target=post, args=(url,))
        for url in (URL, "https://youtu.be/aaaaaaaaaaa")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
    adapter.release("fetch")

    assert sorted(codes) == [202, 409]
    wait_for_end(client)


@pytest.mark.parametrize("probe", ["probe_yt_dlp", "probe_deno", "probe_ffmpeg"])
def test_a_failing_download_probe_is_not_ready(client, adapter, monkeypatch, probe):
    def broken():
        raise FileNotFoundError(probe)

    monkeypatch.setattr(checks, probe, broken)

    response = start(client)

    assert response.status_code == 503
    assert response.json()["code"] == "not_ready"
    assert adapter.download_calls == 0
    assert current(client) is None


def test_deno_probe_that_raises_is_missing_in_status_and_blocks_downloads(client, monkeypatch):
    def broken():
        raise FileNotFoundError("deno")

    monkeypatch.setattr(checks, "probe_deno", broken)
    monkeypatch.setattr(checks, "probe_device", lambda: "mps")

    status = client.get("/api/setup/status").json()

    deno = next(i for i in status["items"] if i["id"] == "deno")
    assert deno["status"] == "missing"
    assert len(status["items"]) == 11
    assert start(client).status_code == 503


def test_a_missing_model_marker_does_not_block_downloads(client, project):
    project.marker(OMNIVOICE).unlink()

    assert start(client).status_code == 202
    assert wait_for_end(client)["state"] == "done"


# --- Cancel ---


def test_cancel_while_downloading_ends_cancelled_with_no_partial_files(client, adapter, project):
    adapter.pause_at("progress")
    start(client)
    adapter.wait_until("progress")

    response = client.delete("/api/spoil/downloads/current")
    adapter.release("progress")
    job = wait_for_end(client)

    assert response.status_code == 202
    assert response.json()["cancel_requested"] is True
    assert (job["state"], job["cancel_requested"], job["clip_id"]) == ("cancelled", True, None)
    assert files_named(project.partial_dir) == []
    assert files_named(project.media_temp_dir) == []


def test_cancel_while_checking_ends_cancelled_without_downloading(client, adapter, project):
    adapter.pause_at("fetch")
    start(client)
    adapter.wait_until("fetch")

    client.delete("/api/spoil/downloads/current")
    adapter.release("fetch")
    job = wait_for_end(client)

    assert job["state"] == "cancelled"
    assert adapter.download_calls == 0
    assert files_named(project.media_temp_dir) == []


def test_cancel_while_merging_is_refused_and_the_job_ends_done(client, adapter):
    adapter.pause_at("merge")
    start(client)
    adapter.wait_until("merge")

    response = client.delete("/api/spoil/downloads/current")
    adapter.release("merge")

    assert response.status_code == 409
    assert response.json() == {"code": "merging", "message": "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว"}
    assert wait_for_end(client)["state"] == "done"


def test_cancel_with_no_unfinished_job_is_not_found(client):
    response = client.delete("/api/spoil/downloads/current")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_cancel_after_the_job_ended_is_not_found(client):
    start(client)
    wait_for_end(client)

    assert client.delete("/api/spoil/downloads/current").status_code == 404


# --- Failures ---


def failed_error(client) -> dict:
    job = wait_for_end(client)
    assert job["state"] == "failed"
    return job["error"]


@pytest.mark.parametrize("live_status", ["is_live", "is_upcoming"])
def test_live_or_upcoming_info_fails_live(client, adapter, live_status):
    adapter.info = youtube_info(live_status=live_status)

    start(client)

    assert failed_error(client)["code"] == "live"
    assert adapter.download_calls == 0


def test_a_live_event_that_has_not_begun_fails_live(client, adapter):
    # YouTube gives no info for these; this is the message seen on 2026-10-29 (D16).
    adapter.fetch_error = yt_dlp_error(
        ExtractorError("[youtube] WUTDiO_fXdE: This live event will begin in 4 days.", expected=True)
    )

    start(client)

    assert failed_error(client) == {
        "code": "live",
        "message": "คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้",
        "yt_dlp_version": "2026.10.26",
        "fix": None,
    }


def test_too_little_disk_fails_disk_full_without_downloading(client, adapter, monkeypatch):
    # Needs 1100 bytes + 1 GiB, about 1.07 GB.
    monkeypatch.setattr(spoil, "free_bytes", lambda path: GB // 2)

    start(client)

    error = failed_error(client)
    assert error["code"] == "disk_full"
    assert error["message"] == "ที่ว่างไม่พอ: ต้องการ 1.1 GB มี 0.5 GB"
    assert adapter.download_calls == 0


@pytest.mark.parametrize(
    "message",
    [
        "[youtube] Tq92D6wQ1mg: Sign in to confirm your age. This video may be inappropriate",
        "[youtube] x: Sign in to confirm you're not a bot",
    ],
)
def test_sign_in_errors_fail_login_required(client, adapter, message):
    adapter.fetch_error = yt_dlp_error(ExtractorError(message, expected=True))

    start(client)

    assert failed_error(client)["code"] == "login_required"


def test_geo_restriction_fails_unavailable(client, adapter):
    adapter.fetch_error = yt_dlp_error(GeoRestrictedError("not available in your country"))

    start(client)

    error = failed_error(client)
    assert error["code"] == "unavailable"
    assert error["message"] == "คลิปนี้เป็น private ถูกลบ หรือจำกัดประเทศ โหลดไม่ได้"


def test_private_or_removed_video_fails_unavailable(client, adapter):
    adapter.fetch_error = yt_dlp_error(
        ExtractorError("[youtube] yYr8q0y5Jfg: Video unavailable. This video is not available", expected=True)
    )

    start(client)

    assert failed_error(client)["code"] == "unavailable"


def test_any_other_error_fails_youtube_error_with_version_and_fix(client, adapter, project):
    adapter.download_error = yt_dlp_error(RuntimeError("Unable to download webpage: HTTP Error 403"))

    start(client)

    assert failed_error(client) == {
        "code": "youtube_error",
        "message": (
            "โหลดไม่สำเร็จ (yt-dlp 2026.10.26). ถ้าเป็นทุกคลิป "
            "ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script"
        ),
        "yt_dlp_version": "2026.10.26",
        "fix": "uv lock --upgrade-package yt-dlp",
    }
    assert files_named(project.partial_dir) == []
    assert files_named(project.media_temp_dir) == []


def test_a_job_whose_cleanup_fails_still_ends_and_frees_the_slot(client, adapter, monkeypatch):
    # Windows can't delete a file another program still holds open.
    real_unlink = Path.unlink

    def unlink(path, missing_ok=False):
        if path.name.endswith(".part"):
            raise PermissionError(path)
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)
    adapter.download_error = yt_dlp_error(RuntimeError("HTTP Error 403"))

    start(client)

    assert failed_error(client)["code"] == "youtube_error"
    adapter.download_error = None
    assert start(client, "https://youtu.be/aaaaaaaaaaa").status_code == 202
    wait_for_end(client)


# --- Temp clips ---


def clip_list(client) -> list[dict]:
    response = client.get("/api/spoil/clips")
    assert response.status_code == 200
    return response.json()["clips"]


def test_a_done_job_is_in_the_list_with_every_field(client):
    start(client)
    wait_for_end(client)

    [clip] = clip_list(client)
    downloaded_at = clip.pop("downloaded_at")
    assert clip == {
        "id": VIDEO_ID,
        "title": "ชื่อคลิป",
        "channel": "ชื่อช่อง",
        "source_url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "duration_s": 213,
        "width": 1920,
        "height": 1080,
        "orientation": "landscape",
        "file_bytes": 1234,
        "thumbnail": f"{VIDEO_ID}.webp",
        "yt_dlp_version": "2026.10.26",
        "transcribed": False,
    }
    assert datetime.fromisoformat(downloaded_at).tzinfo is not None  # sortable as an instant


def test_an_empty_or_missing_media_folder_lists_nothing(client):
    assert clip_list(client) == []


def test_the_list_is_newest_first(client, project):
    write_temp_clip(project, "aaaaaaaaaaa", downloaded_at="2026-10-28T21:10:00+07:00")
    write_temp_clip(project, "bbbbbbbbbbb", downloaded_at="2026-10-29T18:52:00+07:00")
    # 12:00 UTC is 19:00 in Bangkok: newer than bbb though its text sorts first.
    write_temp_clip(project, "ccccccccccc", downloaded_at="2026-10-29T12:00:00+00:00")

    assert [c["id"] for c in clip_list(client)] == ["ccccccccccc", "bbbbbbbbbbb", "aaaaaaaaaaa"]


def test_json_without_its_mp4_or_broken_json_is_not_listed(client, project):
    write_temp_clip(project, "aaaaaaaaaaa")
    write_temp_clip(project, "bbbbbbbbbbb")
    (project.media_temp_dir / "bbbbbbbbbbb.mp4").unlink()
    write_temp_clip(project, "ccccccccccc")
    (project.media_temp_dir / "ccccccccccc.json").write_text("{not json", encoding="utf-8")
    write_temp_clip(project, "ddddddddddd")
    (project.media_temp_dir / "ddddddddddd.json").write_text('{"id": "ddddddddddd"}', encoding="utf-8")

    assert [c["id"] for c in clip_list(client)] == ["aaaaaaaaaaa"]


@pytest.mark.parametrize("downloaded_at", ["yesterday", "2026-10-29T14:05:11"])
def test_a_json_whose_time_cant_be_compared_is_skipped_not_a_500(client, project, downloaded_at):
    write_temp_clip(project, "aaaaaaaaaaa")
    write_temp_clip(project, "bbbbbbbbbbb", downloaded_at=downloaded_at)

    assert [c["id"] for c in clip_list(client)] == ["aaaaaaaaaaa"]


def test_video_answers_a_range_with_206(client, project):
    write_temp_clip(project)

    response = client.get(f"/api/spoil/clips/{VIDEO_ID}/video", headers={"Range": "bytes=0-99"})

    assert response.status_code == 206
    assert response.headers["content-type"] == "video/mp4"
    assert response.headers["content-range"] == "bytes 0-99/1024"
    assert response.content == bytes(range(100))


def test_video_without_a_range_is_the_whole_file(client, project):
    write_temp_clip(project)

    response = client.get(f"/api/spoil/clips/{VIDEO_ID}/video")

    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"
    assert len(response.content) == 1024


def test_thumbnail_is_the_file(client, project):
    write_temp_clip(project)

    response = client.get(f"/api/spoil/clips/{VIDEO_ID}/thumbnail")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert response.content == b"thumb"


NOT_FOUND = {"code": "not_found", "message": "ไม่พบคลิปนี้"}


def test_a_clip_without_a_thumbnail_file_is_404(client, project):
    write_temp_clip(project, thumbnail=False)

    response = client.get(f"/api/spoil/clips/{VIDEO_ID}/thumbnail")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


@pytest.mark.parametrize("part", ["video", "thumbnail"])
def test_files_of_an_unknown_clip_are_404(client, part):
    response = client.get(f"/api/spoil/clips/{VIDEO_ID}/{part}")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_an_mp4_whose_json_is_not_written_yet_is_404(client, project):
    project.media_temp_dir.mkdir(parents=True)
    (project.media_temp_dir / f"{VIDEO_ID}.mp4").write_bytes(b"m")

    assert client.get(f"/api/spoil/clips/{VIDEO_ID}/video").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        # httpx folds `..` before sending, so this one only proves the URL stays harmless;
        # the encoded `%2F` below is the one that reaches the clip route.
        "/api/spoil/clips/../x/video",
        "/api/spoil/clips/..%2Fx/video",
        "/api/spoil/clips/short/video",
        "/api/spoil/clips/dQw4w9WgXcQx/video",
        "/api/spoil/clips/dQw4w9WgX.c/thumbnail",
    ],
)
def test_a_path_that_is_not_an_id_is_404(client, project, path):
    write_temp_clip(project)

    assert client.get(path).status_code == 404


def test_delete_removes_the_three_files(client, project):
    write_temp_clip(project)

    response = client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    assert response.status_code == 204
    assert files_named(project.media_temp_dir) == []
    assert clip_list(client) == []


def test_delete_of_an_unknown_clip_is_404(client):
    response = client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_delete_of_a_bad_id_is_404(client):
    assert client.delete("/api/spoil/clips/not-an-id").status_code == 404


def test_delete_of_a_json_whose_mp4_is_gone_removes_the_json(client, project):
    # Otherwise the link stays `duplicate` for a clip the list never shows.
    write_temp_clip(project)
    (project.media_temp_dir / f"{VIDEO_ID}.mp4").unlink()

    assert client.delete(f"/api/spoil/clips/{VIDEO_ID}").status_code == 204
    assert files_named(project.media_temp_dir) == []


def test_delete_while_the_mp4_is_open_is_in_use_and_keeps_the_json(client, project, monkeypatch):
    write_temp_clip(project)
    real_unlink = Path.unlink

    def unlink(path: Path, missing_ok: bool = False):
        if path.suffix == ".mp4":
            raise PermissionError(32, "The process cannot access the file")
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)

    response = client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    assert response.status_code == 409
    assert response.json() == {
        "code": "in_use",
        "message": "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง",
    }
    assert files_named(project.media_temp_dir) == [f"{VIDEO_ID}.json", f"{VIDEO_ID}.mp4", f"{VIDEO_ID}.webp"]


def test_a_deleted_clip_can_be_downloaded_again(client, project):
    write_temp_clip(project)
    assert start(client).status_code == 409

    client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    assert start(client).status_code == 202
    wait_for_end(client)


# --- Start and Host ---


def test_backend_start_removes_partial_files_and_clips_without_json(fake_root, monkeypatch, project):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    project.partial_dir.mkdir(parents=True)
    (project.partial_dir / "aaaaaaaaaaa.f137.mp4.part").write_bytes(b"x")
    (project.media_temp_dir / "bbbbbbbbbbb.mp4").write_bytes(b"x")
    (project.media_temp_dir / "bbbbbbbbbbb.webp").write_bytes(b"x")
    for name in ("ccccccccccc.mp4", "ccccccccccc.webp", "ccccccccccc.json", ".DS_Store"):
        (project.media_temp_dir / name).write_bytes(b"x")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert list(project.partial_dir.iterdir()) == []
    assert sorted(p.name for p in project.media_temp_dir.iterdir() if p.is_file()) == [
        ".DS_Store",
        "ccccccccccc.json",
        "ccccccccccc.mp4",
        "ccccccccccc.webp",
    ]


def test_a_request_from_another_host_is_refused(client):
    response = client.get("/api/spoil/downloads/current", headers={"Host": "evil.example"})

    assert response.status_code == 400


@pytest.mark.parametrize("host", ["localhost:5173", "127.0.0.1:8000", "[::1]:8000"])
def test_local_hosts_are_allowed(client, host):
    response = client.get("/api/spoil/downloads/current", headers={"Host": host})

    assert response.status_code == 200
