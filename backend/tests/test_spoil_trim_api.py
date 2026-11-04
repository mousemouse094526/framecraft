"""The Trim job API under /api/spoil, with a fake ffmpeg run and probe (spoil seam 1 › Trim)."""

import json
import os
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil
from backend.app import app
from backend.errors import ApiError
from backend.ffmpeg import Media
from backend.paths import ProjectPaths
from backend.spoil import clips, downloads, transcribe, trim
from backend.spoil.clips import Range

from .fakes import (
    FakeAdapter,
    FakeFfmpeg,
    FakeWorker,
    cuda_device,
    ok_deno,
    ok_ffmpeg,
    ok_yt_dlp,
    poll_until,
    write_temp_clip,
    write_transcript,
)

VIDEO_ID = "dQw4w9WgXcQ"
OTHER_ID = "aaaaaaaaaaa"
FINISHED = {"done", "failed", "cancelled"}
CURRENT = "/api/spoil/trims/current"
# A 100-second clip cut at 0–10 and 90–100 keeps 80 seconds.
TWO_CUTS = [{"start_s": 0, "end_s": 10}, {"start_s": 90, "end_s": 100}]


class FakeProbe:
    """`probe` by file: the clip's mp4 is `source`, the Trim job's output is `output`."""

    def __init__(self):
        self.source = Media(duration_s=100.0, has_audio=True)
        self.output = Media(duration_s=80.0, has_audio=True)

    def __call__(self, path: Path) -> Media:
        return self.output if path.name.endswith(".trim.mp4") else self.source


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def ffmpeg_run() -> FakeFfmpeg:
    return FakeFfmpeg()


@pytest.fixture
def media() -> FakeProbe:
    return FakeProbe()


@pytest.fixture
def use_trims(ffmpeg_run, media, monkeypatch):
    """Puts a Trim job holder with fakes in the app; a test passes the ones it changes."""

    def use(**fakes) -> None:
        defaults = {"run_ffmpeg": ffmpeg_run, "probe": media, "free_bytes": lambda path: 10**12, "sleep": lambda s: None}
        monkeypatch.setattr(trim, "trims", trim.Trims(**(defaults | fakes)))

    use()
    return use


@pytest.fixture
def client(fake_root, project, use_trims, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(transcribe, "transcriptions", transcribe.Transcriptions())
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    write_temp_clip(project, duration_s=100)
    return TestClient(app, base_url="http://127.0.0.1")


def start(client, ranges=TWO_CUTS, clip_id: str = VIDEO_ID, **body):
    return client.post("/api/spoil/trims", json={"clip_id": clip_id, "ranges": ranges, **body})


def wait_for_end(client) -> dict:
    return poll_until(client, CURRENT, lambda job: job is not None and job["state"] in FINISHED)


def stored(project: ProjectPaths, clip_id: str = VIDEO_ID) -> dict:
    return json.loads(clips.json_path(project, clip_id).read_text(encoding="utf-8"))


def write_derived(project: ProjectPaths, clip_id: str = VIDEO_ID) -> None:
    """Shots, an EP cut and a Spoil draft made from the clip (spoil-maker ADR 0018)."""
    folder = project.clip_shots_dir(clip_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "shots.json").write_text(json.dumps({"clip_id": clip_id, "shots": []}), encoding="utf-8")
    project.episodes_dir.mkdir(parents=True, exist_ok=True)
    project.episodes_file(clip_id).write_text("{}", encoding="utf-8")
    project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
    draft_json = {
        "version": 2, "clip_id": clip_id, "ep": {"n": 1, "start_s": 0.0, "end_s": 100.0}, "style": "drama",
        "layout": "B", "target_s": 60, "voice_id": "v_0000abcd", "original_volume": 20, "top_text": "", "sentences": [],
    }  # fmt: skip
    project.draft_file.write_text(json.dumps(draft_json), encoding="utf-8")


# --- The pure parts ---


def test_the_command_trims_each_kept_span_and_joins_them():
    spans = trim.kept_spans(trim.merged([Range(start_s=0, end_s=10), Range(start_s=90, end_s=100)], 100), 100)
    argv = trim.command(Path("in.mp4"), Path("out.mp4"), spans, True, trim.video_bps(12_500_000, 100), platform="darwin")

    graph = argv[argv.index("-filter_complex") + 1]
    assert graph == "[0:v]trim=10:90,setpts=PTS-STARTPTS[v0];[0:a]atrim=10:90,asetpts=PTS-STARTPTS[a0];[v0][a0]concat=n=1:v=1:a=1[v][a]"
    assert argv[argv.index("-c:v") + 1] == "h264_videotoolbox"
    # 12.5 MB over 100 s is 1 Mbps; less 192 kbps of sound, but never under 1 Mbps (D41).
    assert argv[argv.index("-b:v") + 1] == "1000000"
    assert argv[argv.index("-b:a") + 1] == "192000"
    assert "+faststart" in argv and argv[-1] == "out.mp4"


def test_the_command_on_windows_is_libx264_and_a_clip_without_sound_has_no_atrim():
    argv = trim.command(Path("in.mp4"), Path("out.mp4"), [Range(start_s=10, end_s=90)], False, 4_000_000, platform="win32")

    graph = argv[argv.index("-filter_complex") + 1]
    assert argv[argv.index("-c:v") + 1 : argv.index("-c:v") + 4] == ["libx264", "-preset", "veryfast"]
    assert "atrim" not in graph and graph.endswith("concat=n=1:v=1:a=0[v]")
    assert "-c:a" not in argv
    assert trim.video_bps(50_000_000, 100) == 4_000_000 - 192_000


def test_overlapping_or_touching_ranges_join():
    joined = trim.merged([Range(start_s=20, end_s=40), Range(start_s=10, end_s=30), Range(start_s=40, end_s=50)], 100)

    assert joined == [Range(start_s=10, end_s=50)]


# --- Starting: the checks, in spec order ---


@pytest.mark.parametrize(
    "ranges",
    [
        [{"start_s": 0, "end_s": 95}],  # leaves 5 seconds
        [{"start_s": 10, "end_s": 120}],  # past the clip's end
        [{"start_s": 10, "end_s": 10.4}],  # shorter than 0.5 s
        [{"start_s": 30, "end_s": 20}],
    ],
)
def test_ranges_against_the_real_length_that_fail_are_invalid_ranges(client, ranges):
    response = start(client, ranges)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_ranges")
    assert client.get(CURRENT).json() is None


@pytest.mark.parametrize(
    "ranges",
    [[{"start_s": True, "end_s": 20}], [{"start_s": "1", "end_s": 20}], [{"start_s": 1}], [], [{"start_s": n, "end_s": n + 1} for n in range(0, 42, 2)], "0-10"],
)
def test_ranges_of_the_wrong_shape_are_invalid_request(client, ranges):
    response = start(client, ranges)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_an_unknown_clip_is_404_and_a_post_that_is_not_json_is_415(client):
    assert start(client, clip_id=OTHER_ID).status_code == 404
    response = client.post("/api/spoil/trims", content=b"{}", headers={"Content-Type": "text/plain"})
    assert response.status_code == 415


def test_without_ffmpeg_is_not_ready(client, monkeypatch):
    monkeypatch.setattr(checks, "probe_ffmpeg", lambda: (_ for _ in ()).throw(FileNotFoundError("no ffmpeg")))

    response = start(client)

    assert (response.status_code, response.json()["code"]) == (503, "not_ready")


def test_a_clip_whose_json_has_no_length_is_checked_against_the_probed_length(client, project):
    clip = stored(project) | {"duration_s": None}
    clips.json_path(project, VIDEO_ID).write_text(json.dumps(clip), encoding="utf-8")

    assert start(client).status_code == 202
    assert wait_for_end(client)["state"] == "done"


def test_a_transcribed_clip_needs_confirm_and_then_loses_its_transcript(client, project, ffmpeg_run):
    write_transcript(project)

    refused = start(client)
    confirmed = start(client, confirm_derived_loss=True)
    job = wait_for_end(client)

    assert (refused.status_code, refused.json()["code"]) == (409, "has_derived")
    assert refused.json()["derived"] == ["transcript"]
    assert confirmed.status_code == 202
    assert job["state"] == "done"
    assert len(ffmpeg_run.commands) == 1
    listed = client.get("/api/spoil/clips").json()["clips"][0]
    assert listed["transcribed"] is False


def test_a_described_cut_and_drafted_clip_loses_all_of_it(client, project):
    write_derived(project)

    refused = start(client)
    start(client, confirm_derived_loss=True)
    wait_for_end(client)

    assert refused.json()["derived"] == ["shots", "episodes", "draft"]
    assert not project.clip_shots_dir(VIDEO_ID).exists()
    assert not project.episodes_file(VIDEO_ID).exists()
    assert client.get("/api/spoil-maker/draft").json() is None


# --- A Trim job from start to end ---


def test_a_done_job_replaces_the_mp4_and_writes_the_new_json(client, project, ffmpeg_run):
    started = start(client)
    job = wait_for_end(client)

    clip = stored(project)
    assert started.json() == {
        "clip_id": VIDEO_ID, "state": "trimming", "percent": 0, "kept_s": 80.0, "cancel_requested": False, "error": None,
    }  # fmt: skip
    assert (job["state"], job["percent"]) == ("done", None)
    assert clips.video_path(project, VIDEO_ID).read_bytes() == b"new mp4"
    assert (clip["duration_s"], clip["file_bytes"]) == (80, len(b"new mp4"))
    assert clip["trimmed"] == [{"start_s": 0.0, "end_s": 10.0}, {"start_s": 90.0, "end_s": 100.0}]
    assert clip["trimmed_at"] is not None
    assert list(project.partial_dir.iterdir()) == []
    assert not trim.marker_path(project, VIDEO_ID).exists()


def test_trimming_reports_percent_of_the_kept_length(client, ffmpeg_run):
    ffmpeg_run.pause, ffmpeg_run.progress = True, (40.0,)

    start(client)
    ffmpeg_run.reached.wait(5)
    job = client.get(CURRENT).json()
    ffmpeg_run.release()
    wait_for_end(client)

    assert (job["state"], job["percent"]) == ("trimming", 50)


def test_cancelling_while_trimming_kills_ffmpeg_and_keeps_the_clip(client, project, ffmpeg_run):
    write_transcript(project)
    ffmpeg_run.pause = True
    start(client, confirm_derived_loss=True)
    ffmpeg_run.reached.wait(5)

    cancelled = client.delete(CURRENT)
    job = wait_for_end(client)

    assert cancelled.status_code == 202
    assert job["state"] == "cancelled" and ffmpeg_run.killed
    assert clips.transcript_path(project, VIDEO_ID).is_file()
    assert clips.video_path(project, VIDEO_ID).read_bytes() != b"new mp4"
    assert client.delete(CURRENT).status_code == 404


def test_ffmpeg_failing_keeps_the_clip_and_the_next_post_starts(client, project, ffmpeg_run):
    ffmpeg_run.fail = True

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"]["code"] == "ffmpeg_failed"
    assert job["error"]["message"].startswith("ตัดคลิปไม่สำเร็จ: ")
    assert clips.read_clip(project, VIDEO_ID).trimmed == []
    ffmpeg_run.fail = False
    assert start(client).status_code == 202
    wait_for_end(client)


@pytest.mark.parametrize("output", [Media(duration_s=75.0, has_audio=True), Media(duration_s=80.0, has_audio=False)])
def test_an_output_shorter_than_kept_or_without_sound_fails_and_touches_nothing(client, project, media, output):
    write_transcript(project)
    media.output = output

    start(client, confirm_derived_loss=True)
    job = wait_for_end(client)

    assert job["error"] == {"code": "ffmpeg_failed", "message": "ตัดคลิปไม่สำเร็จ: ไฟล์ที่ตัดได้ไม่ครบ"}
    assert clips.transcript_path(project, VIDEO_ID).is_file()
    assert clips.read_clip(project, VIDEO_ID).trimmed == []


def test_not_enough_disk_fails_before_ffmpeg(client, ffmpeg_run, use_trims):
    use_trims(free_bytes=lambda path: 0)

    start(client)
    job = wait_for_end(client)

    assert job["error"]["code"] == "disk_full"
    assert ffmpeg_run.commands == []


def test_an_mp4_windows_keeps_open_fails_in_use_and_deletes_nothing(client, project, use_trims):
    write_transcript(project)

    def held(source, destination):
        raise PermissionError("in use")

    use_trims(replace_mp4=held)

    start(client, confirm_derived_loss=True)
    job = wait_for_end(client)

    assert job["error"]["code"] == "in_use"
    assert clips.transcript_path(project, VIDEO_ID).is_file()
    assert not trim.marker_path(project, VIDEO_ID).exists()
    assert list(project.partial_dir.iterdir()) == []


def test_an_mp4_held_twice_then_free_is_replaced(client, project, use_trims):
    tries = []

    def held_twice(source, destination):
        tries.append(1)
        if len(tries) <= 2:
            raise PermissionError("in use")
        os.replace(source, destination)

    use_trims(replace_mp4=held_twice)

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert len(tries) == 3


class SlowReplace:
    """`os.replace` that waits for `release()` once it is reached: the job stays `replacing`."""

    def __init__(self):
        self.reached, self._go = threading.Event(), threading.Event()

    def __call__(self, source, destination):
        self.reached.set()
        self._go.wait(5)
        os.replace(source, destination)

    def release(self):
        self._go.set()


@pytest.fixture
def replacing(client, use_trims) -> SlowReplace:
    """A Trim job of VIDEO_ID held in `replacing`."""
    slow = SlowReplace()
    use_trims(replace_mp4=slow)
    start(client)
    slow.reached.wait(5)
    return slow


def test_cancelling_while_replacing_is_refused_and_the_job_ends_done(client, replacing):
    refused = client.delete(CURRENT)
    replacing.release()

    assert (refused.status_code, refused.json()["code"]) == (409, "replacing")
    assert wait_for_end(client)["state"] == "done"


# --- The clip while a Trim job cuts it, and the other way round ---


@pytest.fixture
def trimming(client, ffmpeg_run):
    ffmpeg_run.pause = True
    start(client)
    ffmpeg_run.reached.wait(5)
    yield
    ffmpeg_run.release()
    wait_for_end(client)


def test_while_trimming_the_clip_cant_be_transcribed_edited_or_deleted(client, project, trimming, monkeypatch):
    monkeypatch.setattr(spoil, "start_worker", FakeWorker())
    write_transcript(project)

    transcribing = client.post("/api/spoil/transcriptions", json={"clip_id": VIDEO_ID})
    edited = client.patch(f"/api/spoil/clips/{VIDEO_ID}/transcript/lines/0", json={"text": "x"})
    deleted = client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    for response in (transcribing, edited, deleted):
        assert (response.status_code, response.json()["code"]) == (409, "trimming")


def test_while_trimming_no_clip_can_be_cut_again(client, project, trimming):
    write_temp_clip(project, OTHER_ID, duration_s=100)

    same, other = start(client), start(client, clip_id=OTHER_ID)

    assert (same.status_code, same.json()["code"]) == (409, "busy")
    assert (other.status_code, other.json()["code"]) == (409, "busy")


def test_while_trimming_a_download_starts(client, trimming, monkeypatch):
    monkeypatch.setattr(spoil, "adapter", FakeAdapter())
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    monkeypatch.setattr(spoil, "free_bytes", lambda path: 10**12)
    monkeypatch.setattr(downloads, "downloads", downloads.Downloads())

    response = client.post("/api/spoil/downloads", json={"url": f"https://youtu.be/{OTHER_ID}"})

    assert response.status_code == 202
    poll_until(client, "/api/spoil/downloads/current", lambda job: job["state"] in FINISHED)


def test_while_trimming_the_clips_ep_cuts_cant_change(client, project, trimming):
    response = client.put(f"/api/spoil-maker/clips/{VIDEO_ID}/episodes", json={"minutes": 30})

    assert (response.status_code, response.json()["code"]) == (409, "clip_busy")


@pytest.mark.parametrize("kind", ["describe", "draft", "voice", "render"])
def test_while_trimming_a_gpu_job_of_the_clip_is_clip_busy(client, trimming, kind):
    # Every GPU job starts through `take` with the clips it reads (spoil-maker D49).
    with pytest.raises(ApiError) as refused:
        gpu.slot.take(kind, [VIDEO_ID])

    assert refused.value.code == "clip_busy"
    gpu.slot.take(kind, [OTHER_ID])  # another clip is free
    gpu.slot.release(kind)


def test_a_clip_being_transcribed_or_read_by_a_gpu_job_cant_be_cut(client, project, monkeypatch):
    worker = FakeWorker()
    worker.pause_at(0)
    monkeypatch.setattr(spoil, "start_worker", worker)
    client.post("/api/spoil/transcriptions", json={"clip_id": VIDEO_ID})
    worker.wait_until(0)

    transcribing = start(client)
    worker.release(0)
    poll_until(client, "/api/spoil/transcriptions/current", lambda job: job["state"] in FINISHED)
    gpu.slot.take("describe", [VIDEO_ID])
    busy = start(client, confirm_derived_loss=True)
    gpu.slot.release("describe")

    assert (transcribing.status_code, transcribing.json()["code"]) == (409, "transcribing")
    assert (busy.status_code, busy.json()["code"]) == (409, "clip_busy")


def test_a_draft_pick_starting_while_replacing_does_not_deadlock(client, replacing):
    outcome = []
    taker = threading.Thread(target=lambda: outcome.append(_start_a_draft_pick()))
    taker.start()
    taker.join(0.1)  # now waiting for the slot's lock, which the replace holds
    replacing.release()
    taker.join(5)

    assert not taker.is_alive()
    assert outcome == ["clip_busy"]  # the clip is marked until the job ends
    assert wait_for_end(client)["state"] == "done"


def _start_a_draft_pick() -> str:
    """What a Draft job's start holds, in its order: the draft's lock, then the slot (D51)."""
    try:
        with gpu.slot.draft_lock:
            gpu.slot.take("draft", [VIDEO_ID], locks_draft=True)
        gpu.slot.release("draft")
        return "taken"
    except ApiError as error:
        return error.code


def test_a_shutdown_while_replacing_waits_for_the_replace(client, project, replacing):
    stopper = threading.Thread(target=trim.trims.stop_on_shutdown)
    stopper.start()
    stopper.join(0.2)
    waited = stopper.is_alive()
    replacing.release()
    stopper.join(5)

    assert waited
    assert wait_for_end(client)["state"] == "done"
    assert clips.video_path(project, VIDEO_ID).read_bytes() == b"new mp4"


# --- Restarting ---


def test_a_restart_before_the_mp4_is_replaced_drops_the_marker(fake_root, project, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    write_temp_clip(project, duration_s=100)
    write_transcript(project)
    old = stored(project)
    trim.marker_path(project, VIDEO_ID).write_text(json.dumps(old | {"duration_s": 80}), encoding="utf-8")
    project.partial_dir.mkdir(parents=True, exist_ok=True)
    trim.trimmed_partial(project, VIDEO_ID).write_bytes(b"half")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert not trim.marker_path(project, VIDEO_ID).exists()
    assert stored(project) == old
    assert clips.transcript_path(project, VIDEO_ID).is_file()


def test_a_restart_after_the_mp4_is_replaced_finishes_the_job(fake_root, project, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    write_temp_clip(project, duration_s=100)
    write_transcript(project)
    new = stored(project) | {"duration_s": 80, "trimmed": [{"start_s": 0.0, "end_s": 20.0}]}
    trim.marker_path(project, VIDEO_ID).write_text(json.dumps(new), encoding="utf-8")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert stored(project)["duration_s"] == 80
    assert not clips.transcript_path(project, VIDEO_ID).exists()
    assert not trim.marker_path(project, VIDEO_ID).exists()


def test_an_old_json_reads_as_never_trimmed_and_a_marker_is_not_a_clip(client, project):
    trim.marker_path(project, VIDEO_ID).write_text(json.dumps(stored(project)), encoding="utf-8")

    listed = client.get("/api/spoil/clips").json()["clips"]

    assert [clip["id"] for clip in listed] == [VIDEO_ID]
    assert (listed[0]["trimmed"], listed[0]["trimmed_at"]) == ([], None)
