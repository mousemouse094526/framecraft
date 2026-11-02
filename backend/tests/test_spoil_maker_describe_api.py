"""The Describe job and the GPU slot, under /api/spoil-maker and /api/spoil, with a
fake LLM worker and real ffmpeg on clips made with `lavfi` (spoil-maker seam 1)."""

import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil, spoil_maker
from backend.app import app
from backend.models import QWEN
from backend.paths import ProjectPaths
from backend.spoil import downloads, transcribe
from backend.spoil_maker import describe

from .fakes import (
    FakeAdapter,
    FakeLlm,
    FakeWorker,
    cuda_device,
    jpeg_width,
    make_test_clip,
    ok_deno,
    ok_ffmpeg,
    ok_yt_dlp,
    write_temp_clip,
)

VIDEO_ID = "dQw4w9WgXcQ"
OTHER_ID = "aaaaaaaaaaa"
FINISHED = {"done", "failed", "cancelled"}
DESCRIBES = "/api/spoil-maker/describes"
CURRENT = "/api/spoil-maker/describes/current"


@pytest.fixture(scope="session")
def three_colours(tmp_path_factory) -> Path:
    """3 s: red, white at 1 s, blue at 2 s (spec › Seams 1)."""
    return make_test_clip(tmp_path_factory.mktemp("clips") / "three.mp4")


@pytest.fixture(scope="session")
def thirty_seconds(tmp_path_factory) -> Path:
    """30 s of one colour: the fake cut finder's Shots go up to 30 s, and each Shot's
    middle frame is still read from the real file."""
    return make_test_clip(tmp_path_factory.mktemp("clips") / "thirty.mp4", ("gray",), seconds_each=30)


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def llm(monkeypatch) -> FakeLlm:
    fake = FakeLlm()
    monkeypatch.setattr(spoil_maker, "start_worker", fake)
    return fake


@pytest.fixture
def whisper(monkeypatch) -> FakeWorker:
    fake = FakeWorker()
    monkeypatch.setattr(spoil, "start_worker", fake)
    return fake


@pytest.fixture
def client(fake_root, llm, whisper, monkeypatch):
    """Everything the gates check passes, with fresh job slots and a free GPU slot."""
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    monkeypatch.setattr(describe, "describes", describe.Describes())
    monkeypatch.setattr(transcribe, "transcriptions", transcribe.Transcriptions())
    monkeypatch.setattr(downloads, "downloads", downloads.Downloads())
    return TestClient(app, base_url="http://127.0.0.1")


def add_clip(project: ProjectPaths, source: Path, video_id: str = VIDEO_ID, duration_s: int = 3) -> None:
    write_temp_clip(project, video_id, duration_s=duration_s)
    shutil.copyfile(source, project.media_temp_dir / f"{video_id}.mp4")


def start(client, clip_id: str = VIDEO_ID):
    return client.post(DESCRIBES, json={"clip_id": clip_id})


def wait_for(client, condition, path: str = CURRENT) -> dict:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        job = client.get(path).json()
        if condition(job):
            return job
        time.sleep(0.01)
    raise AssertionError(f"job never got there: {job}")


def wait_for_end(client, path: str = CURRENT) -> dict:
    return wait_for(client, lambda job: job["state"] in FINISHED, path)


def shots_of(client, clip_id: str = VIDEO_ID) -> list[dict]:
    return client.get(f"/api/spoil-maker/clips/{clip_id}/shots").json()["shots"]


def listed(client, clip_id: str = VIDEO_ID) -> dict:
    return next(clip for clip in client.get("/api/spoil/clips").json()["clips"] if clip["id"] == clip_id)


def fake_cuts(cuts: list[float], duration: float):
    """Stands in for the scene filter: these cut times, this length."""

    def find_cuts(mp4, on_progress, cancel):
        on_progress(duration)
        return cuts, duration

    return find_cuts


# --- A job from start to end ---


def test_a_job_finds_three_shots_describes_each_and_lists_the_clip_as_described(client, project, llm, three_colours):
    add_clip(project, three_colours)
    assert listed(client)["described"] is False

    response = start(client)

    assert response.status_code == 202
    body = response.json()
    assert (body["kind"], body["state"], body["clip_id"]) == ("describe", "cutting", VIDEO_ID)
    assert body["error"] is None
    assert wait_for_end(client)["state"] == "done"
    shots = shots_of(client)
    assert [shot["n"] for shot in shots] == [0, 1, 2]
    for shot, start_s in zip(shots, (0, 1, 2)):
        assert shot["start"] == pytest.approx(start_s, abs=0.1)
    assert shots[-1]["end"] == pytest.approx(3, abs=0.1)
    assert [shot["description"] for shot in shots] == ["A frame at 0.jpg.", "A frame at 1.jpg.", "A frame at 2.jpg."]
    for n in range(3):
        image = client.get(f"/api/spoil-maker/clips/{VIDEO_ID}/shots/{n}.jpg")
        assert image.status_code == 200
        assert image.headers["content-type"] == "image/jpeg"
        assert jpeg_width(project.clip_shots_dir(VIDEO_ID) / f"{n}.jpg") == 320
    assert listed(client)["described"] is True


def test_the_llm_gets_a_448_frame_the_pinned_snapshot_and_the_generation_settings(client, project, llm, three_colours):
    add_clip(project, three_colours)
    widths = []
    llm.respond = lambda request: (widths.append(jpeg_width(request.image)), "A frame.")[1]

    start(client)
    wait_for_end(client)

    assert llm.processes[0].snapshot_dir == project.snapshot_dir(QWEN, QWEN.revision)
    assert widths == [448, 448, 448]
    request = llm.requests[0]
    assert (request.max_tokens, request.temperature) == (80, 0.0)
    assert "30 words" in request.prompt
    # The 448 frames were only for the LLM.
    assert sorted(path.name for path in project.clip_shots_dir(VIDEO_ID).iterdir()) == [
        "0.jpg",
        "1.jpg",
        "2.jpg",
        "shots.json",
    ]


def test_a_25_second_range_becomes_three_equal_shots(client, project, monkeypatch, thirty_seconds):
    add_clip(project, thirty_seconds, duration_s=30)
    monkeypatch.setattr(spoil_maker, "find_cuts", fake_cuts([25.0], 30.0))

    start(client)
    assert wait_for_end(client)["state"] == "done"

    spans = [(shot["start"], shot["end"]) for shot in shots_of(client)]
    # Times are kept to the millisecond.
    assert spans[:3] == [
        pytest.approx((0, 25 / 3), abs=0.001),
        pytest.approx((25 / 3, 50 / 3), abs=0.001),
        pytest.approx((50 / 3, 25), abs=0.001),
    ]
    assert spans[3] == pytest.approx((25, 30))


def test_a_half_second_range_joins_the_shot_before_it(client, project, monkeypatch, thirty_seconds):
    add_clip(project, thirty_seconds, duration_s=30)
    monkeypatch.setattr(spoil_maker, "find_cuts", fake_cuts([5.0, 5.5], 10.0))

    start(client)
    assert wait_for_end(client)["state"] == "done"

    spans = [(shot["start"], shot["end"]) for shot in shots_of(client)]
    assert spans == [pytest.approx((0, 5.5)), pytest.approx((5.5, 10))]


def test_a_short_first_range_joins_the_shot_after_it(client, project, monkeypatch, thirty_seconds):
    add_clip(project, thirty_seconds, duration_s=30)
    monkeypatch.setattr(spoil_maker, "find_cuts", fake_cuts([0.4, 6.0], 10.0))

    start(client)
    assert wait_for_end(client)["state"] == "done"

    spans = [(shot["start"], shot["end"]) for shot in shots_of(client)]
    assert spans == [pytest.approx((0, 6)), pytest.approx((6, 10))]


def test_cutting_reports_how_far_into_the_clip_ffmpeg_has_read(client, project, monkeypatch, thirty_seconds):
    add_clip(project, thirty_seconds, duration_s=30)
    halfway = __import__("threading").Event()

    def slow_cuts(mp4, on_progress, cancel):
        on_progress(15.0)
        halfway.set()
        cancel.wait(5)
        return [], 30.0

    monkeypatch.setattr(spoil_maker, "find_cuts", slow_cuts)
    start(client)
    assert halfway.wait(5)

    job = wait_for(client, lambda job: job["percent"] == 50)
    assert job["state"] == "cutting"
    client.delete(CURRENT)
    wait_for_end(client)


def test_describing_reports_done_and_total_shots(client, project, llm, three_colours):
    add_clip(project, three_colours)
    llm.pause_at(1)

    start(client)
    llm.wait_until(1)

    job = wait_for(client, lambda job: job["done"] == 1)
    assert (job["state"], job["done"], job["total"], job["percent"]) == ("describing", 1, 3, None)
    llm.release(1)
    assert wait_for_end(client)["state"] == "done"


def test_shot_thumbnails_never_replace_the_clips_own_thumbnail(client, project, llm, three_colours):
    add_clip(project, three_colours)

    start(client)
    wait_for_end(client)

    assert client.get(f"/api/spoil/clips/{VIDEO_ID}/thumbnail").content == b"thumb"


# --- Cancel, failure, and doing it again ---


def test_cancelling_a_redo_keeps_the_old_shots_and_leaves_no_new_folder(client, project, llm, three_colours):
    add_clip(project, three_colours)
    start(client)
    wait_for_end(client)
    old = shots_of(client)
    old_thumbnail = (project.clip_shots_dir(VIDEO_ID) / "0.jpg").read_bytes()
    llm.respond = lambda request: "Something else."
    llm.pause_at(1)

    start(client)
    llm.wait_until(1)
    cancelling = client.delete(CURRENT)

    assert cancelling.status_code == 202
    assert cancelling.json()["cancel_requested"] is True
    assert wait_for_end(client)["state"] == "cancelled"
    assert shots_of(client) == old
    assert (project.clip_shots_dir(VIDEO_ID) / "0.jpg").read_bytes() == old_thumbnail
    assert not project.new_shots_dir(VIDEO_ID).exists()
    assert llm.processes[-1].terminated is True


def test_cancelling_while_cutting_ends_cancelled(client, project, monkeypatch, three_colours):
    add_clip(project, three_colours)
    reached = __import__("threading").Event()

    def slow_cuts(mp4, on_progress, cancel):
        reached.set()
        cancel.wait(5)
        return [], 3.0

    monkeypatch.setattr(spoil_maker, "find_cuts", slow_cuts)

    start(client)
    assert reached.wait(5)
    client.delete(CURRENT)

    assert wait_for_end(client)["state"] == "cancelled"
    assert not project.new_shots_dir(VIDEO_ID).exists()
    assert client.get(f"/api/spoil-maker/clips/{VIDEO_ID}/shots").json()["code"] == "not_described"


def test_cancel_without_a_running_job_is_404(client):
    response = client.delete(CURRENT)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_an_llm_slower_than_the_timeout_fails_as_model_failed(client, project, llm, monkeypatch, three_colours):
    add_clip(project, three_colours)
    monkeypatch.setattr(describe, "DESCRIBE_TIMEOUT_SECONDS", 0.2)
    llm.hang_at = 0

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"]["code"] == "model_failed"
    assert llm.processes[0].terminated is True
    assert not project.new_shots_dir(VIDEO_ID).exists()


def test_an_llm_process_that_dies_fails_as_crashed(client, project, llm, three_colours):
    add_clip(project, three_colours)
    llm.crash_at = 1

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"]["code"] == "crashed"


def test_a_clip_ffmpeg_cannot_read_fails_as_ffmpeg_failed(client, project):
    write_temp_clip(project, VIDEO_ID)  # its mp4 is 1 KiB of noise

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"]["code"] == "ffmpeg_failed"


# --- The GPU slot ---


def test_describe_while_a_transcription_runs_is_gpu_busy(client, project, whisper, three_colours):
    add_clip(project, three_colours)
    whisper.pause_at(0)
    client.post("/api/spoil/transcriptions", json={"clip_id": VIDEO_ID})
    whisper.wait_until(0)

    response = start(client)

    assert response.status_code == 409
    assert response.json() == {"code": "gpu_busy", "message": "รอให้งานถอดบทพูดเสร็จก่อน", "running": "transcribe"}
    whisper.release(0)


def test_transcribe_while_describing_is_gpu_busy_but_a_download_starts(client, project, llm, monkeypatch, three_colours):
    add_clip(project, three_colours)
    monkeypatch.setattr(spoil, "adapter", FakeAdapter())
    llm.pause_at(0)
    start(client)
    llm.wait_until(0)

    transcribing = client.post("/api/spoil/transcriptions", json={"clip_id": VIDEO_ID})
    downloading = client.post("/api/spoil/downloads", json={"url": "https://youtu.be/xvFZjo5PgG0"})

    assert transcribing.status_code == 409
    assert transcribing.json() == {"code": "gpu_busy", "message": "รอให้งานบรรยายฉากเสร็จก่อน", "running": "describe"}
    assert downloading.status_code == 202
    llm.release(0)
    wait_for_end(client)


def test_a_second_describe_while_one_runs_is_busy(client, project, llm, three_colours):
    add_clip(project, three_colours)
    llm.pause_at(0)
    start(client)
    llm.wait_until(0)

    response = start(client)

    assert response.status_code == 409
    assert response.json()["code"] == "busy"
    llm.release(0)
    wait_for_end(client)


def test_deleting_the_clip_being_described_is_clip_busy(client, project, llm, three_colours):
    add_clip(project, three_colours)
    llm.pause_at(0)
    start(client)
    llm.wait_until(0)

    response = client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    assert response.status_code == 409
    assert response.json() == {"code": "clip_busy", "message": "คลิปนี้กำลังถูกใช้ในงานอื่น"}
    assert (project.media_temp_dir / f"{VIDEO_ID}.mp4").is_file()
    llm.release(0)
    wait_for_end(client)


@pytest.mark.parametrize("ending", ["done", "failed", "cancelled"])
def test_every_ending_frees_the_gpu_for_the_next_job(client, project, llm, monkeypatch, three_colours, ending):
    add_clip(project, three_colours)
    if ending == "failed":
        llm.crash_at = 0
    if ending == "cancelled":
        llm.pause_at(0)

    start(client)
    if ending == "cancelled":
        llm.wait_until(0)
        client.delete(CURRENT)
    assert wait_for_end(client)["state"] == ending

    response = client.post("/api/spoil/transcriptions", json={"clip_id": VIDEO_ID})
    assert response.status_code == 202
    wait_for_end(client, "/api/spoil/transcriptions/current")


@pytest.mark.parametrize("ending", ["done", "cancelled"])
def test_every_transcription_ending_frees_the_gpu_for_a_describe(client, project, whisper, three_colours, ending):
    add_clip(project, three_colours)
    if ending == "cancelled":
        whisper.pause_at(0)
    client.post("/api/spoil/transcriptions", json={"clip_id": VIDEO_ID})
    if ending == "cancelled":
        whisper.wait_until(0)
        client.delete("/api/spoil/transcriptions/current")
    assert wait_for_end(client, "/api/spoil/transcriptions/current")["state"] == ending

    assert start(client).status_code == 202
    wait_for_end(client)


# --- Clip delete and start-up ---


def test_deleting_a_described_clip_deletes_its_shots(client, project, llm, three_colours):
    add_clip(project, three_colours)
    start(client)
    wait_for_end(client)

    assert client.delete(f"/api/spoil/clips/{VIDEO_ID}").status_code == 204

    assert not project.clip_shots_dir(VIDEO_ID).exists()


def test_start_up_removes_unfinished_shot_folders_and_shots_of_clips_it_cleans(fake_root, project, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    write_temp_clip(project, VIDEO_ID)
    write_temp_clip(project, OTHER_ID)
    (project.media_temp_dir / f"{OTHER_ID}.json").unlink()  # an unfinished download
    for folder in (project.new_shots_dir("a"), project.clip_shots_dir(VIDEO_ID), project.clip_shots_dir(OTHER_ID)):
        folder.mkdir(parents=True)
        (folder / "0.jpg").write_bytes(b"jpg")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert not project.new_shots_dir("a").exists()
    assert not project.clip_shots_dir(OTHER_ID).exists()
    assert (project.clip_shots_dir(VIDEO_ID) / "0.jpg").is_file()


# --- Refusals ---


def test_a_missing_qwen_marker_is_not_ready_naming_it(client, project, three_colours):
    add_clip(project, three_colours)
    project.marker(QWEN).unlink()

    response = start(client)

    assert response.status_code == 503
    assert response.json()["code"] == "not_ready"
    assert response.json()["rows"] == ["model_qwen"]
    assert response.json()["message"] == "ยังติดตั้งไม่ครบ: Qwen3.5 9B model"


def test_describing_an_unknown_clip_is_404(client):
    response = start(client, OTHER_ID)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_shots_of_a_clip_never_described_are_not_described(client, project):
    write_temp_clip(project)

    response = client.get(f"/api/spoil-maker/clips/{VIDEO_ID}/shots")

    assert response.status_code == 404
    assert response.json()["code"] == "not_described"


@pytest.mark.parametrize(
    "path",
    [
        "/api/spoil-maker/clips/..%2Fx/shots",
        f"/api/spoil-maker/clips/{OTHER_ID}/shots",
        f"/api/spoil-maker/clips/{VIDEO_ID}/shots/3.jpg",
        f"/api/spoil-maker/clips/{VIDEO_ID}/shots/x.jpg",
        f"/api/spoil-maker/clips/{VIDEO_ID}/shots/..%2F0.jpg",
    ],
)
def test_a_path_that_is_not_a_clip_or_shot_is_404_not_found(client, project, llm, three_colours, path):
    add_clip(project, three_colours)
    start(client)
    wait_for_end(client)

    response = client.get(path)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_a_post_that_is_not_json_is_415(client, project):
    write_temp_clip(project)

    response = client.post(DESCRIBES, content='{"clip_id": "dQw4w9WgXcQ"}', headers={"Content-Type": "text/plain"})

    assert response.status_code == 415


def test_another_host_is_400(client):
    response = client.get(CURRENT, headers={"Host": "evil.example"})

    assert response.status_code == 400


def test_current_is_null_before_any_job(client):
    assert client.get(CURRENT).json() is None
