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

from backend import checks, gpu, paths, spoil
from backend.app import app
from backend.models import OMNIVOICE
from backend.paths import ProjectPaths
from backend.spoil import downloads, links
from backend.spoil.adapter import error_code, select_formats

from .fakes import (
    FakeAdapter,
    FakeMp4Check,
    ok_deno,
    ok_ffmpeg,
    ok_yt_dlp,
    site_info,
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
def mp4_check() -> FakeMp4Check:
    return FakeMp4Check()


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def client(fake_root, adapter, mp4_check, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(spoil, "free_bytes", lambda path: 100 * GB)
    monkeypatch.setattr(downloads, "downloads", downloads.Downloads(check_mp4=mp4_check))
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
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
        "https://www.youtube.com/playlist?list=x",
        "https://www.youtube.com/watch?v=short",
        "https://youtu.be/",
        "ftp://youtu.be/dQw4w9WgXcQ",
        "ftp://x.com/a",
        "https:///a",
        "not a link",
        "http://localhost:8000/a",
        "http://LOCALHOST./a",
        "http://app.localhost/a",
        "http://127.0.0.1/a",
        "http://127.1/a",
        "http://2130706433/a",
        "http://192.168.1.5/a",
        "http://10.0.0.1/a",
        "http://[::1]/a",
        "http://169.254.169.254/",
        "http://0.0.0.0/a",
        "http://0x7f000001/a",
        "http://0x7f.0.0.1/a",
    ],
)
def test_links_that_are_not_a_youtube_clip_or_a_public_site_are_invalid_url(client, adapter, url):
    response = start(client, url)

    assert response.status_code == 400
    assert response.json() == {"code": "invalid_url", "message": "ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป"}
    assert adapter.fetched_urls == []


@pytest.mark.parametrize("url", ["https://vimeo.com/1", "https://www.facebook.com/watch/?v=123", "http://93.184.216.34/v"])
def test_a_link_of_another_site_starts_a_job_whose_id_comes_later(client, adapter, url):
    adapter.info = site_info()

    response = start(client, url)

    assert response.status_code == 202
    assert response.json()["id"] is None
    assert wait_for_end(client)["clip_id"] == "facebook-123"
    assert adapter.fetched_urls == [url]


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
        "site": "Youtube",
        "trimmed": [],
        "trimmed_at": None,
    }
    assert downloaded_at[:2] == "20" and downloaded_at[-6] in "+-"
    assert files_named(project.partial_dir) == []


def test_the_size_comes_from_checking_the_file_and_taller_than_wide_is_portrait(client, mp4_check, project):
    # A phone video stored 1920×1080 with a quarter turn shows 1080×1920 (D55).
    mp4_check.width, mp4_check.height = 1080, 1920

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

    def download(info, project, clip_id, on_progress):
        def record(event):
            on_progress(event)
            seen.append(current(client)["percent"])

        return original(info, project, clip_id, record)

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
    assert response.json() == {"code": "busy", "message": "กำลังโหลดหรือเอาไฟล์อื่นเข้าอยู่"}
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
    assert len(status["items"]) == 20
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
        "clip_id": None,
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
        # Seen from Vimeo on 2026-11-07 (D56).
        "[vimeo] 1: The web client only works when logged-in. Use --cookies, --cookies-from-browser",
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


def test_any_other_error_fails_download_error_with_version_and_fix(client, adapter, project):
    adapter.download_error = yt_dlp_error(RuntimeError("Unable to download webpage: HTTP Error 403"))

    start(client)

    assert failed_error(client) == {
        "code": "download_error",
        "message": (
            "โหลดไม่สำเร็จ (yt-dlp 2026.10.26). ถ้าเป็นทุกคลิป "
            "ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script"
        ),
        "yt_dlp_version": "2026.10.26",
        "fix": "uv lock --upgrade-package yt-dlp",
        "clip_id": None,
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

    assert failed_error(client)["code"] == "download_error"
    adapter.download_error = None
    assert start(client, "https://youtu.be/aaaaaaaaaaa").status_code == 202
    wait_for_end(client)


# --- Other sites (D47, D51, D52, D54, D55) ---


FACEBOOK_URL = "https://www.facebook.com/watch/?v=123"


def test_another_sites_clip_is_named_by_site_and_id(client, adapter, project):
    adapter.info = site_info()

    start(client, FACEBOOK_URL)
    job = wait_for_end(client)

    assert (job["state"], job["id"], job["clip_id"]) == ("done", "facebook-123", "facebook-123")
    assert adapter.clip_ids == ["facebook-123"]
    clip = json.loads((project.media_temp_dir / "facebook-123.json").read_text(encoding="utf-8"))
    downloaded_at = clip.pop("downloaded_at")
    assert clip == {
        "id": "facebook-123",
        "title": "คลิปจากเว็บอื่น",
        "channel": "เพจ",
        "site": "Facebook",
        "source_url": "https://www.facebook.com/watch/?v=123",
        "duration_s": 30,
        "width": 1920,
        "height": 1080,
        "orientation": "landscape",
        "file_bytes": 1234,
        "thumbnail": "facebook-123.webp",
        "yt_dlp_version": "2026.10.26",
        "trimmed": [],
        "trimmed_at": None,
    }
    assert downloaded_at[:2] == "20"


def test_the_same_link_of_another_site_again_fails_duplicate_without_downloading(client, adapter, project):
    adapter.info = site_info()
    start(client, FACEBOOK_URL)
    wait_for_end(client)

    assert start(client, FACEBOOK_URL).status_code == 202
    error = failed_error(client)

    assert (error["code"], error["message"], error["clip_id"]) == ("duplicate", "คลิปนี้โหลดไว้แล้ว", "facebook-123")
    assert adapter.download_calls == 1
    assert files_named(project.media_temp_dir, "facebook-123") == [
        "facebook-123.json",
        "facebook-123.mp4",
        "facebook-123.webp",
    ]


def test_a_youtube_clip_found_through_another_link_is_duplicate_too(client, adapter, project):
    write_temp_clip(project)

    start(client, "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ")

    assert failed_error(client)["clip_id"] == VIDEO_ID
    assert adapter.download_calls == 0


@pytest.mark.parametrize(
    "message",
    [
        "Unsupported URL: https://example.com/a",
        # What yt-dlp says once the generic extractor is off; seen on 2026-11-07 (D56).
        "No suitable extractor found for URL https://example.com/a",
    ],
)
def test_a_site_yt_dlp_has_no_extractor_for_fails_unsupported(client, adapter, message):
    adapter.fetch_error = yt_dlp_error(RuntimeError(message))

    start(client, "https://example.com/a")

    assert failed_error(client) == {
        "code": "unsupported",
        "message": 'เว็บนี้โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด "เลือกไฟล์ในเครื่อง"',
        "yt_dlp_version": "2026.10.26",
        "fix": None,
        "clip_id": None,
    }


def test_login_required_points_to_the_file_picker(client, adapter):
    adapter.fetch_error = yt_dlp_error(ExtractorError("[youtube] x: Sign in to confirm you're not a bot", expected=True))

    start(client)

    assert failed_error(client)["message"] == (
        'เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด "เลือกไฟล์ในเครื่อง"'
    )


def test_a_playlist_fails_playlist_without_downloading(client, adapter, project):
    adapter.info = {"_type": "playlist", "id": "PL1", "extractor_key": "TikTokUser", "title": "user"}

    start(client, "https://www.tiktok.com/@someone")

    assert failed_error(client)["code"] == "playlist"
    assert failed_error(client)["message"] == "ลิงก์นี้เป็น playlist วางลิงก์ของคลิปเดียว"
    assert adapter.download_calls == 0
    assert list(project.media_temp_dir.glob("*")) == []


def test_no_h264_format_to_pick_fails_unsupported_format_before_downloading(client, adapter):
    # The format selector yields nothing, so `extract_info` raises (D54).
    adapter.fetch_error = yt_dlp_error(
        ExtractorError("[TikTok] 7: Requested format is not available. Use --list-formats", expected=True)
    )

    start(client, "https://www.tiktok.com/@a/video/7")

    error = failed_error(client)
    assert (error["code"], error["message"]) == (
        "unsupported_format",
        'เว็บนี้ไม่มีไฟล์ H.264 ไม่เกิน 1080p ให้โหลด โหลดเองแล้วแปลง จากนั้นกด "เลือกไฟล์ในเครื่อง"',
    )
    assert adapter.download_calls == 0


def test_a_merged_file_that_breaks_the_rule_fails_unsupported_format_and_is_removed(client, adapter, mp4_check, project):
    adapter.info = site_info()
    mp4_check.reason = "ภาพเป็น hevc"

    start(client, FACEBOOK_URL)

    assert failed_error(client)["code"] == "unsupported_format"
    assert mp4_check.checked == [project.media_temp_dir / "facebook-123.mp4"]
    assert files_named(project.media_temp_dir, "facebook-123") == []


@pytest.mark.parametrize(
    ("key", "raw_id", "expected"),
    [
        ("Youtube", "dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("Facebook", "123", "facebook-123"),
        ("TikTok", "7123456789", "tiktok-7123456789"),
        ("BiliBili", "bvabc", "bilibili-bvabc"),
        ("Twitter", "a.b", "twitter-a_b-fb5b9332"),
    ],
)
def test_clip_ids_by_site(key, raw_id, expected):
    assert links.clip_id(key, raw_id) == expected


def test_ids_that_would_look_alike_stay_apart():
    assert links.clip_id("Twitter", "a.b") != links.clip_id("Twitter", "a_b")


def test_ids_that_differ_only_in_case_stay_apart_on_a_disk_that_ignores_case():
    # Mac and Windows disks take `x-BVabc.json` and `x-bvabc.json` for one file.
    upper, lower = links.clip_id("BiliBili", "BVabc"), links.clip_id("BiliBili", "bvabc")

    assert upper.lower() != lower.lower()
    assert upper == upper.lower()
    assert upper.startswith("bilibili-bvabc-")


def test_a_long_id_is_cut_to_64_with_a_hash_and_still_a_clip_id():
    long_id = links.clip_id("Facebook", "x" * 80)

    assert len(long_id) == 64
    assert links.CLIP_ID.fullmatch(long_id)
    assert long_id != links.clip_id("Facebook", "x" * 81)


def test_a_long_id_from_the_site_gives_a_64_character_clip(client, adapter, project):
    adapter.info = site_info(video_id="x" * 80)

    start(client, FACEBOOK_URL)
    job = wait_for_end(client)

    assert job["state"] == "done"
    assert len(job["clip_id"]) == 64
    assert links.CLIP_ID.fullmatch(job["clip_id"])
    assert clip_list(client)[0]["id"] == job["clip_id"]


def test_a_downloaded_file_that_is_not_mp4_fails_unsupported_format_and_is_removed(client, adapter, project):
    # A format that named no extension is saved under its own, not merged into mp4 (D56).
    adapter.info = site_info()
    original = adapter.download

    def download(info, project, clip_id, on_progress):
        mp4 = original(info, project, clip_id, on_progress)
        return mp4.rename(mp4.with_suffix(".unknown_video"))

    adapter.download = download

    start(client, FACEBOOK_URL)

    assert failed_error(client)["code"] == "unsupported_format"
    assert files_named(project.media_temp_dir, "facebook-123") == []


AVC_1080x1920 = {"format_id": "v1", "vcodec": "avc1.640028", "acodec": "none", "width": 1080, "height": 1920, "tbr": 2000, "protocol": "https"}
AVC_720 = {"format_id": "v0", "vcodec": "avc1.4d401f", "acodec": "none", "width": 720, "height": 1280, "tbr": 900, "protocol": "https"}
AAC = {"format_id": "a1", "vcodec": "none", "acodec": "mp4a.40.2", "tbr": 128, "protocol": "https"}
HEVC = {"format_id": "h1", "vcodec": "hvc1.1.6.L120.90", "acodec": "mp4a.40.2", "width": 1080, "height": 1920, "tbr": 1500, "protocol": "https"}
AVC_1440 = {"format_id": "v2", "vcodec": "avc1.640032", "acodec": "none", "width": 1440, "height": 2560, "tbr": 6000, "protocol": "https"}
COMBINED_480 = {"format_id": "c1", "vcodec": "h264", "acodec": "aac", "width": 480, "height": 854, "tbr": 800, "protocol": "https"}


def pick(*formats: dict) -> list[dict]:
    return list(select_formats({"formats": list(formats)}))


@pytest.mark.parametrize("formats", [(HEVC,), (AVC_1440, AAC), (AVC_1080x1920,), (HEVC | {"format_id": "h2"}, AVC_1440)])
def test_the_format_selector_yields_nothing_without_h264_at_most_1080_and_aac(formats):
    assert pick(*formats) == []


def test_the_format_selector_picks_the_largest_h264_with_aac():
    [picked] = pick(AVC_720, AVC_1440, HEVC, AAC, AVC_1080x1920, COMBINED_480)

    assert picked["format_id"] == "v1+a1"
    assert picked["requested_formats"] == [AVC_1080x1920, AAC]
    assert (picked["ext"], picked["width"], picked["height"]) == ("mp4", 1080, 1920)


def test_the_format_selector_takes_a_combined_format_when_it_is_the_largest():
    [picked] = pick(COMBINED_480, AVC_720 | {"width": 360, "height": 640}, AAC)

    assert picked == COMBINED_480


FB_HD = {"format_id": "hd", "vcodec": None, "acodec": None, "width": None, "height": None, "protocol": "https"}
FB_SD = {"format_id": "sd", "vcodec": None, "acodec": None, "width": None, "height": None, "protocol": "https"}
VP9 = {"format_id": "v9", "vcodec": "vp09.00.40.08", "acodec": "none", "width": 1080, "height": 1080, "tbr": 1872, "protocol": "https"}


def test_the_format_selector_falls_back_to_a_format_that_names_no_codec_and_leaves_it_to_the_file_check():
    # Facebook's progressive `hd`/`sd` say nothing; its DASH is VP9 (seen 2026-11-07, D56).
    [picked] = pick(FB_SD, FB_HD, VP9, AAC)

    assert picked["format_id"] == "hd"


def test_the_format_selector_prefers_a_known_h264_to_one_that_names_no_codec():
    [picked] = pick(FB_HD, COMBINED_480)

    assert picked == COMBINED_480


def test_the_format_selector_skips_a_10_bit_picture():
    assert pick(AVC_720 | {"pix_fmt": "yuv420p10le"}, AAC) == []


@pytest.mark.parametrize(
    ("formats", "code"),
    [((HEVC,), "unsupported_format"), ((AVC_1440, AAC), "unsupported_format"), ((AVC_1080x1920, AAC), None)],
)
def test_yt_dlp_itself_reports_a_selector_that_yields_nothing_as_unsupported_format(formats, code):
    # The real YoutubeDL runs the selector on a made-up info dict; no network (D54).
    import yt_dlp

    info = {"id": "7", "title": "t", "extractor": "TikTok", "extractor_key": "TikTok", "webpage_url": "https://x/7",
            "formats": [dict(f, url=f"https://x/{f['format_id']}", ext="mp4") for f in formats]}  # fmt: skip
    with yt_dlp.YoutubeDL({"format": select_formats, "quiet": True, "no_warnings": True}) as ydl:
        try:
            picked = ydl.process_ie_result(info, download=False)
        except yt_dlp.utils.YoutubeDLError as error:  # `extract_info` wraps it in DownloadError
            assert error_code(error) == code
        else:
            assert code is None
            assert picked["format_id"] == "v1+a1"


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
        "site": "Youtube",
        "trimmed": [],
        "trimmed_at": None,
        "transcribed": False,
        "described": False,
        "in_draft": False,
    }
    assert datetime.fromisoformat(downloaded_at).tzinfo is not None  # sortable as an instant


def test_a_json_from_before_other_sites_lists_as_youtube(client, project):
    write_temp_clip(project)  # has no `site`

    assert clip_list(client)[0]["site"] == "Youtube"


def test_a_clip_of_another_site_plays_and_deletes_like_a_youtube_one(client, project):
    write_temp_clip(project, "facebook-123")

    video = client.get("/api/spoil/clips/facebook-123/video", headers={"Range": "bytes=0-99"})
    assert video.status_code == 206
    assert client.get("/api/spoil/clips/facebook-123").json()["id"] == "facebook-123"
    assert client.delete("/api/spoil/clips/facebook-123").status_code == 204
    assert files_named(project.media_temp_dir, "facebook-123") == []


def test_a_clip_without_channel_source_or_yt_dlp_version_lists(client, project):
    clip = write_temp_clip(project, "local-0123456789ab")
    clip |= {"channel": None, "source_url": None, "yt_dlp_version": None, "site": "local"}
    (project.media_temp_dir / "local-0123456789ab.json").write_text(json.dumps(clip), encoding="utf-8")

    [listed] = clip_list(client)

    assert (listed["source_url"], listed["yt_dlp_version"], listed["site"]) == (None, None, "local")


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


@pytest.mark.parametrize(
    ("head", "media_type"),
    [(b"\xff\xd8\xff\xe0", "image/jpeg"), (b"\x89PNG\r\n\x1a\n", "image/png"), (b"RIFF\0\0\0\0WEBPVP8 ", "image/webp")],
)
def test_a_thumbnail_whose_extension_names_no_type_is_served_as_the_image_it_is(client, project, head, media_type):
    # TikTok's thumbnail comes as `{id}.image` (seen 2026-11-07, D56).
    write_temp_clip(project, "tiktok-7", thumbnail=False)
    (project.media_temp_dir / "tiktok-7.image").write_bytes(head + b"rest")

    response = client.get("/api/spoil/clips/tiktok-7/thumbnail")

    assert response.headers["content-type"] == media_type


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
    # Only names the app makes are its leftovers; a user's own file stays (D55).
    for name in ("facebook-1.mp4", "facebook-1.jpg", "local-0123456789ab.mp4", "bilibili-bvabc-1a2b3c4d.mp4"):
        (project.media_temp_dir / name).write_bytes(b"x")
    kept = (
        ".DS_Store", "notes.txt", "my_video.mp4", "ccccccccccc.mp4", "ccccccccccc.webp", "ccccccccccc.json",
        "tiktok-7.mp4", "tiktok-7.json",
        # A `-` alone doesn't make a name the app's: "my" is no site yt-dlp knows.
        "my-video.mp4", "my-video.jpg", "local-notes-1.txt",
    )  # fmt: skip
    for name in kept:
        (project.media_temp_dir / name).write_bytes(b"x")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert list(project.partial_dir.iterdir()) == []
    assert sorted(p.name for p in project.media_temp_dir.iterdir() if p.is_file()) == sorted(kept)


def test_a_request_from_another_host_is_refused(client):
    response = client.get("/api/spoil/downloads/current", headers={"Host": "evil.example"})

    assert response.status_code == 400


@pytest.mark.parametrize("host", ["localhost:5173", "127.0.0.1:8000", "[::1]:8000"])
def test_local_hosts_are_allowed(client, host):
    response = client.get("/api/spoil/downloads/current", headers={"Host": host})

    assert response.status_code == 200
