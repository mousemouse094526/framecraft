"""The range and the Pick job under /api/songs (drum-notes seam 1 › ช่วงแกะ, Pick job; D5, D6, D8,
D17, D18, D20; ADR 0043): real ffmpeg decodes the stretch, `FakeOnnxRunner` stands in for the
models, and the job is watched through the API without timers."""

import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import checks, ffmpeg, gpu, paths
from backend.app import app
from backend.drum_notes import imports, pick, songs
from backend.jobs import Cancelled
from backend.models import ADTOF, BASIC_PITCH
from backend.paths import ProjectPaths

from .fakes import FINISHED, ROCK, SONGS, FakeOnnxRunner, import_song_tone, midi_file, ok_ffmpeg, poll_until, put_song_file, restart, song_refusal

PICK = f"{SONGS}/pick"


@pytest.fixture
def project(fake_root, monkeypatch) -> ProjectPaths:
    monkeypatch.setattr(paths, "ROOT", fake_root)
    return ProjectPaths(fake_root)


@pytest.fixture
def runner() -> FakeOnnxRunner:
    return FakeOnnxRunner()


@pytest.fixture
def client(project, runner, monkeypatch) -> TestClient:
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(imports, "song_imports", imports.SongImports())
    monkeypatch.setattr(pick, "pick_jobs", pick.PickJobs(open_session=runner))
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    return TestClient(app, base_url="http://127.0.0.1")


def set_range(client, song_id: str, start_s: float, end_s: float, mode: str = "drums"):
    return client.put(f"{SONGS}/{song_id}/range", json={"start_s": start_s, "end_s": end_s, "mode": mode})


def start_pick(client, song_id: str):
    return client.post(f"{SONGS}/{song_id}/pick", json={})


def pick_until_ended(client, song_id: str) -> dict:
    response = start_pick(client, song_id)
    assert response.status_code == 202, response.json()
    return poll_until(client, PICK, lambda job: job["state"] in FINISHED)


def song_json(project: ProjectPaths, song_id: str) -> dict:
    return songs.Song.model_validate_json((project.song_dir(song_id) / "song.json").read_bytes()).model_dump()


# --- the range ---


def test_a_fresh_song_s_default_range_ends_at_its_rounded_length_so_it_can_be_picked_at_once(client, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=6.24)  # a length that rounds down to one decimal

    assert song["range"]["end_s"] == song["duration_s"]
    assert start_pick(client, song["id"]).status_code == 202
    assert poll_until(client, PICK, lambda job: job["state"] in FINISHED)["state"] == "done"



def test_the_range_is_saved_and_answered_with_the_song(client, project, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)

    response = set_range(client, song["id"], 2, 10)

    assert response.status_code == 200, response.json()
    assert response.json()["range"] == {"start_s": 2.0, "end_s": 10.0, "mode": "drums"}
    assert response.json()["bars"] == []
    assert client.get(f"{SONGS}/{song['id']}").json()["range"] == {"start_s": 2.0, "end_s": 10.0, "mode": "drums"}
    assert song_json(project, song["id"])["updated_at"] >= song["updated_at"]


@pytest.mark.parametrize(
    ("start_s", "end_s", "field"),
    [(0, 2, "end_s"), (0, 100, "end_s"), (5, 20, "end_s"), (-1, 5, "start_s")],
)
def test_a_range_of_two_or_a_hundred_seconds_past_the_end_or_before_the_start_is_invalid_naming_the_field(client, tmp_path, start_s, end_s, field):
    song = import_song_tone(client, tmp_path, seconds=12)

    response = set_range(client, song["id"], start_s, end_s)

    assert song_refusal(response) == (400, "invalid_request")
    assert response.json()["field"] == field
    assert client.get(f"{SONGS}/{song['id']}").json()["range"] == {"start_s": 0.0, "end_s": 12.0, "mode": "drums"}


def test_a_range_of_a_wrong_shape_and_of_a_midi_song_and_of_no_song_are_refused(client, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)
    midi = put_song_file(client, "rock.mid", midi_file(ROCK, bpm=100)).json()

    assert song_refusal(client.put(f"{SONGS}/{song['id']}/range", json={"start_s": "0", "end_s": 10, "mode": "drums"})) == (400, "invalid_request")
    assert song_refusal(client.put(f"{SONGS}/{song['id']}/range", json={"start_s": 0, "end_s": 10, "mode": "piano"})) == (400, "invalid_request")
    assert song_refusal(set_range(client, midi["id"], 0, 2.4)) == (409, "not_applicable")
    assert song_refusal(set_range(client, "nosuchsong00", 0, 5)) == (404, "not_found")


# --- the Pick job ---


def test_a_pick_goes_preparing_then_picking_with_a_percent_then_done_and_writes_the_analysis(client, project, runner, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)
    assert set_range(client, song["id"], 2, 8).status_code == 200
    runner.pause_at("adtof")
    runner.pause_at("chunk 0")

    started = start_pick(client, song["id"])
    assert (started.status_code, started.json()["state"], started.json()["percent"]) == (202, "preparing", 0)
    runner.wait_until("adtof")
    job = client.get(PICK).json()
    assert (job["state"], job["percent"], job["song_id"]) == ("picking", 0, song["id"])  # ffmpeg done, ADTOF running
    runner.release("adtof")
    runner.wait_until("chunk 0")
    job = client.get(PICK).json()
    assert (job["state"], job["percent"]) == ("picking", 50)  # ADTOF done, one chunk to go
    runner.release("chunk 0")
    job = poll_until(client, PICK, lambda job: job["state"] in FINISHED)

    assert (job["state"], job["percent"], job["error"]) == ("done", 100, None)
    analysis = song_json(project, song["id"])["analysis"]
    assert (analysis["mode"], analysis["start_s"], analysis["end_s"]) == ("drums", 2.0, 8.0)
    assert analysis["beats"] == pytest.approx([2.0 + 0.5 * n for n in range(12)])
    assert analysis["downbeats"] == pytest.approx([2.0, 4.0, 6.0])
    assert set(analysis["downbeats"]) <= set(analysis["beats"])
    assert [(hit["t"], hit["piece"], hit["level"]) for hit in analysis["hits"]] == [
        (2.0, "kick", "normal"), (2.5, "snare", "normal"), (3.0, "kick", "normal"), (3.5, "snare", "normal"),
        (4.0, "kick", "normal"), (4.5, "snare", "normal"), (5.0, "kick", "normal"), (5.5, "snare", "normal"),
        (6.0, "kick", "normal"), (6.5, "snare", "normal"), (7.0, "kick", "normal"), (7.5, "snare", "normal"),
    ]  # fmt: skip
    assert analysis["picked_at"] >= song["created_at"]
    assert runner.opened == ["adtof_frame_rnn.onnx", "beat_this.onnx"]
    [row] = client.get(SONGS).json()
    assert row["analysis"] == {"mode": "drums", "bars": 2}


def test_the_song_answers_the_bars_found_marking_one_without_four_beats(client, runner, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)

    def beat(frames, pad_before):
        logits = FakeOnnxRunner().beat(frames, pad_before)
        logits[pad_before + 125] = -5.0  # the beat at 2.5 s of the range is gone: the second bar has three
        return logits

    runner.beat = beat
    assert pick_until_ended(client, song["id"])["state"] == "done"

    bars = client.get(f"{SONGS}/{song['id']}").json()["bars"]

    assert [(bar["n"], bar["start_s"], bar["end_s"], bar["beats"], bar["hits"], bar["four_four"]) for bar in bars] == [
        (1, 0.0, 2.0, 4, 4, True),
        (2, 2.0, 4.0, 3, 4, False),
        (3, 4.0, 6.0, 4, 4, True),
        (4, 6.0, 8.0, 4, 4, True),
        (5, 8.0, 10.0, 4, 4, True),
    ]


def test_adtof_gets_the_whole_stretch_at_44_1_khz_once_and_beat_this_each_chunk_at_22_05_khz_with_pad_frames_the_percent_rising_per_chunk(client, runner, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=40)
    assert set_range(client, song["id"], 1, 36).status_code == 200  # 35 s: 1,750 frames, two chunks
    runner.pause_at("chunk 0")
    runner.pause_at("chunk 1")

    assert start_pick(client, song["id"]).status_code == 202
    runner.wait_until("chunk 0")
    assert client.get(PICK).json()["percent"] == 33  # ADTOF, of three steps
    runner.release("chunk 0")
    runner.wait_until("chunk 1")
    assert client.get(PICK).json()["percent"] == 66
    runner.release("chunk 1")
    assert poll_until(client, PICK, lambda job: job["state"] in FINISHED)["state"] == "done"

    adtof, first, second = runner.runs
    assert adtof == ("adtof_frame_rnn.onnx", {"waveform": (1, 35 * 44_100)})
    assert first == ("beat_this.onnx", {"waveform": (1, (1494 - 1) * 441 + 1024), "pad_frames": (2,)})
    assert second == ("beat_this.onnx", {"waveform": (1, (1494 - 1) * 441 + 1024), "pad_frames": (2,)})
    assert runner.pad_frames == [[6, 0], [0, 6]]


def test_a_pick_takes_no_gpu_slot_so_a_model_job_can_start_meanwhile(client, runner, tmp_path):
    song = import_song_tone(client, tmp_path)
    runner.pause_at("adtof")
    assert start_pick(client, song["id"]).status_code == 202
    runner.wait_until("adtof")

    gpu.slot.take("transcribe")  # a Transcribe job starting beside it: not refused
    gpu.slot.release("transcribe")
    runner.release("adtof")

    assert poll_until(client, PICK, lambda job: job["state"] in FINISHED)["state"] == "done"


def test_a_second_pick_is_busy_naming_the_song_a_delete_is_song_busy_and_a_cancel_ends_it_cancelled_keeping_the_old_analysis(client, project, runner, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)
    other = import_song_tone(client, tmp_path, "other.mp3")
    assert pick_until_ended(client, song["id"])["state"] == "done"
    before = song_json(project, song["id"])
    assert set_range(client, song["id"], 4, 12).status_code == 200
    ran = runner.chunks  # the chunks of the first pick; the second's first chunk is the next
    step = f"chunk {ran}"
    runner.pause_at(step)
    assert start_pick(client, song["id"]).status_code == 202
    runner.wait_until(step)

    busy = start_pick(client, other["id"])
    assert song_refusal(busy) == (409, "busy")
    assert busy.json()["message"] == f"กำลังแกะ {song['title']} อยู่ รอให้เสร็จก่อน"
    assert busy.json()["song_id"] == song["id"]
    assert song_refusal(client.delete(f"{SONGS}/{song['id']}")) == (409, "song_busy")
    assert client.delete(f"{SONGS}/{other['id']}").status_code == 204  # another song can go
    cancelled = client.post(f"{PICK}/cancel", json={})
    assert (cancelled.status_code, cancelled.json()["cancel_requested"]) == (200, True)
    runner.release(step)

    job = poll_until(client, PICK, lambda job: job["state"] in FINISHED)
    assert job["state"] == "cancelled"
    assert song_json(project, song["id"])["analysis"] == before["analysis"]
    assert runner.chunks == ran + 1  # the released chunk ran; nothing after it
    assert client.delete(f"{SONGS}/{song['id']}").status_code == 204


def test_a_midi_song_and_a_missing_song_cant_be_picked_and_a_cancel_with_no_job_is_not_running(client):
    midi = put_song_file(client, "rock.mid", midi_file(ROCK, bpm=100)).json()

    assert song_refusal(start_pick(client, midi["id"])) == (409, "not_applicable")
    assert song_refusal(start_pick(client, "nosuchsong00")) == (404, "not_found")
    assert song_refusal(client.post(f"{PICK}/cancel", json={})) == (409, "not_running")
    assert client.get(PICK).json() is None


def test_a_melody_pick_feeds_basic_pitch_a_window_at_a_time_then_beat_this_and_writes_every_onset_as_a_snare(client, project, runner, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)
    assert set_range(client, song["id"], 2, 8, mode="melody").status_code == 200  # 6 s: 132,300 samples, four windows, one chunk
    runner.pause_at("window 0")
    runner.pause_at("chunk 0")

    assert start_pick(client, song["id"]).status_code == 202
    runner.wait_until("window 0")
    assert (client.get(PICK).json()["state"], client.get(PICK).json()["percent"]) == ("picking", 0)
    runner.release("window 0")
    runner.wait_until("chunk 0")
    assert client.get(PICK).json()["percent"] == 80  # four windows of five steps
    runner.release("chunk 0")
    job = poll_until(client, PICK, lambda job: job["state"] in FINISHED)

    assert (job["state"], job["percent"], job["error"]) == ("done", 100, None)
    assert runner.opened == ["basic_pitch_nmp.onnx", "beat_this.onnx"]
    *windows, beat_this = runner.runs
    assert windows == [("basic_pitch_nmp.onnx", {"serving_default_input_2:0": (1, 43_844, 1)})] * 4
    assert beat_this[0] == "beat_this.onnx"
    analysis = song_json(project, song["id"])["analysis"]
    assert (analysis["mode"], analysis["start_s"], analysis["end_s"]) == ("melody", 2.0, 8.0)
    assert analysis["downbeats"] == pytest.approx([2.0, 4.0, 6.0])
    assert {(hit["piece"], hit["level"]) for hit in analysis["hits"]} == {("snare", "normal")}
    assert [hit["t"] for hit in analysis["hits"]] == pytest.approx([2.0 + 0.5 * n for n in range(12)], abs=0.012)  # the fake's onsets every 0.5 s, on a 256-sample frame
    [row] = client.get(SONGS).json()
    assert row["analysis"] == {"mode": "melody", "bars": 2}


def test_a_melody_pick_needs_the_basic_pitch_row_and_not_adtof_s(client, project, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)
    assert set_range(client, song["id"], 0, 10, mode="melody").status_code == 200
    project.marker(ADTOF).unlink()
    assert start_pick(client, song["id"]).status_code == 202
    assert poll_until(client, PICK, lambda job: job["state"] in FINISHED)["state"] == "done"
    project.marker(BASIC_PITCH).unlink()

    response = start_pick(client, song["id"])

    assert song_refusal(response) == (503, "not_ready")
    assert response.json()["rows"] == ["model_basic_pitch"]


def test_without_the_adtof_marker_a_pick_is_not_ready_naming_the_row(client, project, tmp_path):
    song = import_song_tone(client, tmp_path)
    project.marker(ADTOF).unlink()

    response = start_pick(client, song["id"])

    assert song_refusal(response) == (503, "not_ready")
    assert response.json()["rows"] == ["model_adtof"]


# --- preparing: ffmpeg ---


class PausedDecode:
    """ffmpeg decoding the stretch until the job's `cancel` is set: ffmpeg running long."""

    def __init__(self):
        self.reached = threading.Event()
        self.killed = False

    def __call__(self, command: list[str], cancel: threading.Event) -> bytes:
        self.reached.set()
        self.killed = cancel.wait(5)
        raise Cancelled() if self.killed else AssertionError("the job never cancelled ffmpeg")


def test_a_cancel_while_ffmpeg_decodes_kills_it_and_ends_the_job_cancelled(client, runner, monkeypatch, tmp_path):
    paused = PausedDecode()
    monkeypatch.setattr(pick, "pick_jobs", pick.PickJobs(open_session=runner, run_ffmpeg=paused))
    song = import_song_tone(client, tmp_path)
    assert start_pick(client, song["id"]).status_code == 202
    assert paused.reached.wait(5)
    assert client.get(PICK).json()["state"] == "preparing"

    assert client.post(f"{PICK}/cancel", json={}).status_code == 200

    assert poll_until(client, PICK, lambda job: job["state"] in FINISHED)["state"] == "cancelled"
    assert paused.killed
    assert runner.opened == []


def test_ffmpeg_that_fails_ends_the_job_internal_with_its_last_line(client, runner, monkeypatch, tmp_path):
    def broken(command, cancel):
        raise ffmpeg.FfmpegFailed("ffmpeg exited with 1: Invalid data found when processing input", "Invalid data found when processing input")

    monkeypatch.setattr(pick, "pick_jobs", pick.PickJobs(open_session=runner, run_ffmpeg=broken))
    song = import_song_tone(client, tmp_path)

    job = pick_until_ended(client, song["id"])

    assert (job["state"], job["error"]) == ("failed", "internal")
    assert job["message"] == "แกะโน้ตไม่สำเร็จ: Invalid data found when processing input"


# --- picking: the models ---


def test_a_model_file_that_wont_open_fails_model_broken_with_its_row_and_the_setup_fix(client, project, runner, tmp_path):
    song = import_song_tone(client, tmp_path)
    runner.open_error = RuntimeError("[ONNXRuntimeError] : 7 : INVALID_PROTOBUF : Load model from adtof_frame_rnn.onnx failed")

    job = pick_until_ended(client, song["id"])

    assert (job["state"], job["error"], job["rows"], job["fix"]) == ("failed", "model_broken", ["model_adtof"], "./setup.sh")
    assert job["message"] == "ไฟล์โมเดลเสีย รัน Setup script ใหม่ (ADTOF drum model)"
    assert client.get(f"{SONGS}/{song['id']}").json()["analysis"] is None
    assert checks.check_model(project, ADTOF)[0] == "ok"  # the Status check still says ok: only opening the file tells


def test_a_model_that_raises_while_running_fails_model_failed_with_the_first_line(client, runner, tmp_path):
    runner.run_error = RuntimeError("Non-zero status code returned while running LSTM node\nsecond line")
    song = import_song_tone(client, tmp_path)

    job = pick_until_ended(client, song["id"])

    assert (job["state"], job["error"]) == ("failed", "model_failed")
    assert job["message"] == "โมเดลทำงานผิดพลาด: Non-zero status code returned while running LSTM node"
    assert job["rows"] is None


def test_a_stretch_with_fewer_than_two_downbeats_fails_no_beats(client, runner, tmp_path):
    runner.downbeat = lambda frames, pad_before: FakeOnnxRunner().downbeat(frames, pad_before) * 0 - 5.0
    song = import_song_tone(client, tmp_path)

    job = pick_until_ended(client, song["id"])

    assert (job["state"], job["error"], job["message"]) == ("failed", "no_beats", "หาจังหวะในช่วงนี้ไม่ได้ ลองช่วงอื่น")
    assert client.get(f"{SONGS}/{song['id']}").json()["analysis"] is None


# --- picking again, restart ---


def test_a_pick_of_another_range_replaces_the_analysis_whole_and_a_restart_loses_the_job_but_keeps_it(client, project, runner, monkeypatch, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)
    assert pick_until_ended(client, song["id"])["state"] == "done"
    first = song_json(project, song["id"])["analysis"]
    assert first["downbeats"] == pytest.approx([0.0, 2.0, 4.0, 6.0, 8.0, 10.0])
    assert set_range(client, song["id"], 5, 11).status_code == 200

    assert pick_until_ended(client, song["id"])["state"] == "done"

    second = song_json(project, song["id"])["analysis"]
    assert (second["start_s"], second["end_s"]) == (5.0, 11.0)
    assert second["downbeats"] == pytest.approx([5.0, 7.0, 9.0])
    assert all(hit["t"] >= 5.0 for hit in second["hits"])
    monkeypatch.setattr(pick, "pick_jobs", pick.PickJobs(open_session=runner))  # a new process holds no job
    restart(client)
    assert client.get(PICK).json() is None
    assert client.get(f"{SONGS}/{song['id']}").json()["analysis"]["downbeats"] == pytest.approx([5.0, 7.0, 9.0])


def test_the_decode_commands_seek_the_stretch_of_the_song_s_audio(client, runner, monkeypatch, tmp_path):
    """The rates and mono float32 show in the sample counts above; the seek is the one thing only the command shows."""
    commands: list[list[str]] = []

    def recording(command, cancel):
        commands.append(command)
        return ffmpeg.run_capture(command, cancel)

    monkeypatch.setattr(pick, "pick_jobs", pick.PickJobs(open_session=runner, run_ffmpeg=recording))
    song = import_song_tone(client, tmp_path, seconds=12)
    assert set_range(client, song["id"], 2.5, 8).status_code == 200

    assert pick_until_ended(client, song["id"])["state"] == "done"

    assert len(commands) == 2
    for command in commands:
        assert command[command.index("-ss") + 1 : command.index("-i")] == ["2.500", "-t", "5.500"]  # before `-i`: a seek, then the length
        assert Path(command[command.index("-i") + 1]).name == "audio.m4a"
