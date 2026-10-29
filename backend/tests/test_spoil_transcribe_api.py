"""The Transcribe job API under /api/spoil, with a fake Whisper worker (spoil seam 1)."""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import checks, paths, spoil
from backend.app import app
from backend.models import WHISPER
from backend.paths import ProjectPaths
from backend.spoil import clips, jobs, transcribe
from backend.spoil.whisper import Done, WorkerError

from .fakes import (
    FakeAdapter,
    FakeWorker,
    cuda_device,
    ok_deno,
    ok_ffmpeg,
    ok_yt_dlp,
    segment,
    write_temp_clip,
    write_transcript,
)

VIDEO_ID = "dQw4w9WgXcQ"
FINISHED = {"done", "failed", "cancelled"}


@pytest.fixture
def worker(monkeypatch) -> FakeWorker:
    fake = FakeWorker()
    monkeypatch.setattr(spoil, "start_worker", fake)
    return fake


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def ready(fake_root, worker, monkeypatch) -> None:
    """Everything the gate checks passes, with a fresh job slot."""
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(transcribe, "transcriptions", transcribe.Transcriptions())


@pytest.fixture
def client(ready):
    return TestClient(app, base_url="http://127.0.0.1")


def start(client, clip_id: str = VIDEO_ID):
    return client.post("/api/spoil/transcriptions", json={"clip_id": clip_id})


def current(client) -> dict | None:
    return client.get("/api/spoil/transcriptions/current").json()


def wait_for(client, condition, path: str = "/api/spoil/transcriptions/current") -> dict:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = client.get(path).json()
        if condition(job):
            return job
        time.sleep(0.01)
    raise AssertionError(f"job never got there: {job}")


def wait_for_end(client, path: str = "/api/spoil/transcriptions/current") -> dict:
    return wait_for(client, lambda job: job["state"] in FINISHED, path)


def transcript_path(project: ProjectPaths):
    return clips.transcript_path(project, VIDEO_ID)


# A 600 s clip: the second segment's line comes back in clip time, past 300 s.
TWO_SEGMENTS = [
    segment(0, 2, [(1.0, 2.5, " Where are you going?")]),
    segment(1, 2, [(301.0, 302.5, " Home.")]),
    Done(),
]


# --- A job from start to end ---


def test_a_job_runs_until_done_and_writes_every_segments_lines(client, project, worker):
    write_temp_clip(project, duration_s=600)
    worker.messages = TWO_SEGMENTS

    response = start(client)

    assert response.status_code == 202
    assert response.json() == {
        "clip_id": VIDEO_ID,
        "state": "preparing",
        "percent": None,
        "cancel_requested": False,
        "error": None,
    }
    assert wait_for_end(client)["state"] == "done"
    transcript = client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript").json()
    assert transcript["lines"] == [
        {"start_s": 1.0, "end_s": 2.5, "text": "Where are you going?"},
        {"start_s": 301.0, "end_s": 302.5, "text": "Home."},
    ]
    assert transcript["clip_id"] == VIDEO_ID
    assert transcript["language"] == "en"
    assert transcript["duration_s"] == 600
    assert transcript["model"] == "openai/whisper-large-v3-turbo"
    assert transcript["revision"] == "41f01f3"
    assert datetime.fromisoformat(transcript["transcribed_at"]).tzinfo is not None
    assert json.loads(transcript_path(project).read_text(encoding="utf-8")) == transcript


def test_the_worker_gets_the_clip_the_pinned_snapshot_and_the_device(client, project, worker):
    write_temp_clip(project)

    start(client)
    wait_for_end(client)

    mp4, duration_s, snapshot_dir, device = worker.calls[0]
    assert mp4 == project.media_temp_dir / f"{VIDEO_ID}.mp4"
    assert duration_s == 213
    assert snapshot_dir == project.snapshot_dir(WHISPER, WHISPER.revision)
    assert device == "cuda"


def test_percent_counts_finished_segments(client, project, worker):
    write_temp_clip(project)
    worker.messages = [segment(0, 3), segment(1, 3), segment(2, 3), Done()]
    worker.pause_at(0)
    worker.pause_at(2)

    start(client)
    worker.wait_until(0)
    assert current(client)["state"] == "preparing"
    worker.release(0)
    worker.wait_until(2)
    job = wait_for(client, lambda job: job["percent"] == 66)
    assert job["state"] == "transcribing"
    worker.release(2)
    assert wait_for_end(client)["percent"] is None


def test_the_clip_list_shows_transcribed(client, project, worker):
    write_temp_clip(project, "aaaaaaaaaaa")
    write_temp_clip(project)

    start(client)
    wait_for_end(client)

    clips = client.get("/api/spoil/clips").json()["clips"]
    assert {c["id"]: c["transcribed"] for c in clips} == {VIDEO_ID: True, "aaaaaaaaaaa": False}


def test_empty_lines_are_dropped_and_no_lines_is_still_done(client, project, worker):
    write_temp_clip(project)
    worker.messages = [segment(0, 2, []), segment(1, 2, [(300.0, 301.0, "   ")]), Done()]

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript").json()["lines"] == []


def test_lines_are_sorted_by_start(client, project, worker):
    write_temp_clip(project)
    worker.messages = [segment(0, 1, [(5.0, 6.0, "second"), (1.0, 2.0, "first")]), Done()]

    start(client)
    wait_for_end(client)

    lines = client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript").json()["lines"]
    assert [line["text"] for line in lines] == ["first", "second"]


@pytest.mark.parametrize(
    ("languages", "expected"),
    [
        ([None, None], None),
        (["th", "en", "en"], "en"),
        (["th", None, "en"], "th"),  # a tie goes to the earlier segment
        ([None, "en"], "en"),
    ],
)
def test_language_is_what_most_segments_detected(client, project, worker, languages, expected):
    write_temp_clip(project)
    total = len(languages)
    worker.messages = [segment(i, total, language=lang) for i, lang in enumerate(languages)] + [Done()]

    start(client)
    wait_for_end(client)

    assert client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript").json()["language"] == expected


def test_a_new_transcript_replaces_the_old_one(client, project, worker):
    write_temp_clip(project)
    write_transcript(project)

    start(client)
    wait_for_end(client)

    lines = client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript").json()["lines"]
    assert lines == [{"start_s": 1.0, "end_s": 2.5, "text": "Hello."}]


# --- Transcript files ---


def test_txt_and_srt_of_a_two_line_transcript(client, project):
    write_temp_clip(project)
    write_transcript(
        project,
        lines=[
            {"start_s": 12.4, "end_s": 15.0, "text": "Where are you going?"},
            {"start_s": 3725.25, "end_s": 3727.9, "text": "กลับบ้าน"},
        ],
    )

    txt = client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript.txt")
    srt = client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript.srt")

    assert txt.status_code == 200
    assert txt.headers["content-type"] == "text/plain; charset=utf-8"
    assert txt.headers["content-disposition"] == f'attachment; filename="{VIDEO_ID}.txt"'
    assert txt.content == "[00:00:12] Where are you going?\n[01:02:05] กลับบ้าน\n".encode()
    assert srt.status_code == 200
    assert srt.headers["content-type"] == "application/x-subrip"
    assert srt.headers["content-disposition"] == f'attachment; filename="{VIDEO_ID}.srt"'
    assert srt.content == (
        "1\n00:00:12,400 --> 00:00:15,000\nWhere are you going?\n\n"
        "2\n01:02:05,250 --> 01:02:07,900\nกลับบ้าน\n"
    ).encode()


def test_an_empty_transcript_gives_empty_files(client, project):
    write_temp_clip(project)
    write_transcript(project, lines=[])

    assert client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript.txt").content == b""
    assert client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript.srt").content == b""


NOT_FOUND = {"code": "not_found", "message": "ไม่พบคลิปนี้"}


@pytest.mark.parametrize("part", ["transcript", "transcript.txt", "transcript.srt"])
def test_a_clip_without_a_transcript_is_404(client, project, part):
    write_temp_clip(project)

    response = client.get(f"/api/spoil/clips/{VIDEO_ID}/{part}")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "คลิปนี้ยังไม่ได้ถอดบทพูด"}


@pytest.mark.parametrize("path", ["/api/spoil/clips/..%2Fx/transcript", "/api/spoil/clips/short/transcript.srt"])
def test_a_transcript_path_that_is_not_an_id_is_404(client, project, path):
    write_temp_clip(project)
    write_transcript(project)

    assert client.get(path).status_code == 404


# --- Refusals ---


def test_an_unknown_clip_is_404(client, project):
    write_temp_clip(project)
    (project.media_temp_dir / "aaaaaaaaaaa.mp4").write_bytes(b"m")  # mp4 without json

    for clip_id in ("bbbbbbbbbbb", "aaaaaaaaaaa", "../x"):
        response = start(client, clip_id)
        assert response.status_code == 404
        assert response.json() == NOT_FOUND


def test_a_clip_whose_mp4_is_gone_is_404(client, project):
    write_temp_clip(project)
    (project.media_temp_dir / f"{VIDEO_ID}.mp4").unlink()

    assert start(client).status_code == 404


def test_post_while_a_transcribe_job_is_unfinished_is_busy(client, project, worker):
    write_temp_clip(project)
    write_temp_clip(project, "aaaaaaaaaaa")
    worker.pause_at(0)
    start(client)
    worker.wait_until(0)

    response = start(client, "aaaaaaaaaaa")

    assert response.status_code == 409
    assert response.json() == {"code": "busy", "message": "กำลังถอดคลิปอื่นอยู่"}
    worker.release(0)
    wait_for_end(client)


def test_post_while_a_download_is_unfinished_is_accepted(client, project, worker, monkeypatch):
    adapter = FakeAdapter()
    monkeypatch.setattr(spoil, "adapter", adapter)
    monkeypatch.setattr(spoil, "free_bytes", lambda path: 10**12)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    monkeypatch.setattr(jobs, "downloads", jobs.Downloads())
    write_temp_clip(project, "aaaaaaaaaaa")
    adapter.pause_at("progress")
    client.post("/api/spoil/downloads", json={"url": f"https://youtu.be/{VIDEO_ID}"})
    adapter.wait_until("progress")

    response = start(client, "aaaaaaaaaaa")

    assert response.status_code == 202
    assert wait_for_end(client)["state"] == "done"
    adapter.release("progress")
    assert wait_for_end(client, "/api/spoil/downloads/current")["state"] == "done"


def test_a_missing_whisper_marker_is_not_ready(client, project):
    write_temp_clip(project)
    project.marker(WHISPER).unlink()

    response = start(client)

    assert response.status_code == 503
    assert response.json() == {"code": "not_ready", "message": "ยังติดตั้งไม่ครบ: Whisper model"}


def test_a_cpu_device_is_not_ready(client, project, monkeypatch):
    write_temp_clip(project)
    monkeypatch.setattr(checks, "probe_device", lambda: "cpu")

    response = start(client)

    assert response.status_code == 503
    assert response.json() == {"code": "not_ready", "message": "ยังติดตั้งไม่ครบ: Device"}


def test_a_broken_ffmpeg_is_not_ready(client, project, monkeypatch):
    write_temp_clip(project)

    def broken():
        raise RuntimeError("ffmpeg -version exited with 1")

    monkeypatch.setattr(checks, "probe_ffmpeg", broken)

    assert start(client).json()["message"] == "ยังติดตั้งไม่ครบ: ffmpeg"


def test_the_gate_comes_before_the_clip_check(client, monkeypatch):
    monkeypatch.setattr(checks, "probe_device", lambda: "cpu")

    assert start(client, "bbbbbbbbbbb").status_code == 503


@pytest.mark.parametrize("path", ["/api/spoil/transcriptions", "/api/spoil/downloads"])
def test_a_post_that_is_not_json_is_415(client, path):
    response = client.post(path, content=b'{"clip_id": "x"}', headers={"Content-Type": "text/plain"})

    assert response.status_code == 415
    assert response.json() == {"code": "unsupported_media_type", "message": "ต้องส่งเป็น JSON"}


def test_a_post_without_a_content_type_is_415(client):
    response = client.post("/api/spoil/transcriptions", content=b'{"clip_id": "x"}')

    assert response.status_code == 415


def test_json_with_a_charset_is_accepted(client, project):
    write_temp_clip(project)

    response = client.post(
        "/api/spoil/transcriptions",
        content=json.dumps({"clip_id": VIDEO_ID}).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

    assert response.status_code == 202
    wait_for_end(client)


# --- Cancel, errors and crashes ---


def test_current_is_null_before_any_job(client):
    assert current(client) is None


def test_cancel_without_an_unfinished_job_is_404(client):
    response = client.delete("/api/spoil/transcriptions/current")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "ไม่มีงานถอดที่ยังไม่จบ"}


def test_cancel_during_the_first_segment_terminates_the_worker_and_keeps_the_old_transcript(
    client, project, worker
):
    write_temp_clip(project)
    old = write_transcript(project)
    worker.messages = TWO_SEGMENTS
    worker.pause_at(0)
    start(client)
    worker.wait_until(0)

    response = client.delete("/api/spoil/transcriptions/current")

    assert response.status_code == 202
    assert response.json()["cancel_requested"] is True
    job = wait_for_end(client)
    assert job["state"] == "cancelled"
    assert job["cancel_requested"] is True
    assert worker.processes[0].terminated
    assert not worker.processes[0].is_alive()
    assert json.loads(transcript_path(project).read_text(encoding="utf-8")) == old


@pytest.mark.parametrize(
    ("code", "detail", "message"),
    [
        ("no_audio", "ffmpeg exited with 1", "คลิปนี้ไม่มีเสียง หรืออ่านเสียงไม่ได้"),
        (
            "model_failed",
            "RuntimeError: MPS backend out of memory",
            "ถอดไม่สำเร็จ: RuntimeError: MPS backend out of memory. ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง",
        ),
    ],
)
def test_a_worker_error_fails_the_job(client, project, worker, code, detail, message):
    write_temp_clip(project)
    old = write_transcript(project)
    worker.messages = [WorkerError(code, detail)]
    worker.exitcode = 1

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"] == {"code": code, "message": message}
    assert json.loads(transcript_path(project).read_text(encoding="utf-8")) == old


def test_a_worker_that_exits_without_done_is_crashed_and_frees_the_slot(client, project, worker):
    write_temp_clip(project)
    worker.messages = [segment(0, 2)]
    worker.exitcode = -11

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"] == {
        "code": "crashed",
        "message": "ตัวถอดหยุดทำงานกลางทาง (exit -11). ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง",
    }
    assert not transcript_path(project).exists()
    worker.messages = [segment(0, 1), Done()]
    assert start(client).status_code == 202
    assert wait_for_end(client)["state"] == "done"


def test_a_transcript_that_cant_be_written_is_internal_and_frees_the_slot(client, project, worker, monkeypatch):
    write_temp_clip(project)
    old = write_transcript(project)
    real_replace = os.replace

    def replace(source, target):
        if str(target).endswith(".transcript.json"):
            raise OSError(28, "No space left on device")
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", replace)

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"] == {"code": "internal", "message": "ถอดไม่สำเร็จ: [Errno 28] No space left on device"}
    assert json.loads(transcript_path(project).read_text(encoding="utf-8")) == old
    monkeypatch.setattr(os, "replace", real_replace)
    assert start(client).status_code == 202
    assert wait_for_end(client)["state"] == "done"


def test_an_unknown_message_is_internal_and_the_worker_is_stopped(client, project, worker):
    write_temp_clip(project)
    worker.messages = [("surprise",), segment(0, 1)]
    worker.pause_at(1)  # keeps the fake alive, so only the job can stop it

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"]["code"] == "internal"
    assert worker.processes[0].terminated


# --- Delete and start ---


def test_delete_of_the_clip_being_transcribed_is_refused(client, project, worker):
    write_temp_clip(project)
    worker.pause_at(0)
    start(client)
    worker.wait_until(0)

    response = client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    assert response.status_code == 409
    assert response.json() == {"code": "transcribing", "message": "กำลังถอดคลิปนี้อยู่ ยกเลิกก่อนแล้วลบ"}
    assert (project.media_temp_dir / f"{VIDEO_ID}.json").is_file()
    worker.release(0)
    wait_for_end(client)
    assert client.delete(f"/api/spoil/clips/{VIDEO_ID}").status_code == 204
    assert sorted(p.name for p in project.media_temp_dir.glob(f"{VIDEO_ID}.*")) == []


def test_another_clip_can_be_deleted_while_transcribing(client, project, worker):
    write_temp_clip(project)
    write_temp_clip(project, "aaaaaaaaaaa")
    worker.pause_at(0)
    start(client)
    worker.wait_until(0)

    assert client.delete("/api/spoil/clips/aaaaaaaaaaa").status_code == 204
    worker.release(0)
    wait_for_end(client)


def test_the_transcript_file_is_not_a_clip_row(client, project):
    write_temp_clip(project)
    write_transcript(project)

    clips = client.get("/api/spoil/clips").json()["clips"]

    assert [c["id"] for c in clips] == [VIDEO_ID]


def test_backend_start_removes_tmp_files(fake_root, monkeypatch, project):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    write_temp_clip(project)
    write_transcript(project)
    leftovers = [f"{VIDEO_ID}.transcript.json.tmp", f"{VIDEO_ID}.json.tmp"]
    for name in leftovers:
        (project.media_temp_dir / name).write_text("{", encoding="utf-8")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert sorted(p.name for p in project.media_temp_dir.glob(f"{VIDEO_ID}.*")) == [
        f"{VIDEO_ID}.json",
        f"{VIDEO_ID}.mp4",
        f"{VIDEO_ID}.transcript.json",
        f"{VIDEO_ID}.webp",
    ]


def test_backend_start_removes_a_transcript_without_its_clip(fake_root, monkeypatch, project):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    project.media_temp_dir.mkdir(parents=True)
    write_transcript(project)

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert not transcript_path(project).exists()


def test_shutdown_terminates_the_worker(ready, worker, project):
    write_temp_clip(project)
    worker.pause_at(0)

    with TestClient(app, base_url="http://127.0.0.1") as client:
        start(client)
        worker.wait_until(0)

    worker.processes[0].join(5)
    assert worker.processes[0].terminated


def test_a_broken_transcript_file_is_404_not_a_500(client, project):
    write_temp_clip(project)
    transcript_path(project).write_text("{not json", encoding="utf-8")

    response = client.get(f"/api/spoil/clips/{VIDEO_ID}/transcript")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "อ่าน Transcript ไม่ได้ ถอดใหม่อีกครั้ง"}


def test_a_transcript_that_cant_be_removed_doesnt_stop_the_delete(client, project, monkeypatch):
    write_temp_clip(project)
    write_transcript(project)
    real_unlink = Path.unlink

    def unlink(path: Path, missing_ok: bool = False):
        if path.name.endswith(".transcript.json"):
            raise PermissionError(32, "The process cannot access the file")
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)

    assert client.delete(f"/api/spoil/clips/{VIDEO_ID}").status_code == 204
    # Left for the clean-up at the next start, which removes a transcript without its json.
    assert sorted(p.name for p in project.media_temp_dir.glob(f"{VIDEO_ID}.*")) == [f"{VIDEO_ID}.transcript.json"]
