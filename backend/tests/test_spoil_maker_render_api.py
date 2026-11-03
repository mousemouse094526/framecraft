"""The Spoil draft's voice (Voice job `sentences`), what the tab remembers (`/settings`)
and the Render job with its results, under /api/spoil-maker: a fake OmniVoice worker
and real ffmpeg on a 3-second test clip (spoil-maker seam 1 › เสียงและตัวเลข, › Render)."""

import io
import json
import shutil
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil_maker
from backend.app import app
from backend.paths import ProjectPaths
from backend.spoil_maker import render as render_module
from backend.spoil_maker import thai, voices

from .fakes import FakeTts, cuda_device, make_test_clip, ok_ffmpeg
from .test_spoil_maker_draft_api import (
    EP1,
    VOICE,
    ready_clip,
    sentence,
    voiced,
    wait_for,
    wait_for_end,
    write_draft,
    write_voice,
)

VOICE_JOBS = "/api/spoil-maker/voice-jobs"
VOICE_CURRENT = "/api/spoil-maker/voice-jobs/current"
DRAFT = "/api/spoil-maker/draft"
NUMBERS = "ปี 1968 เวลา 10:30 ราว 50% หรือ 3.25 เท่า ๑๑ คน 114,000 บาท 007"
NUMBERS_SPOKEN = (
    "ปี หนึ่งพันเก้าร้อยหกสิบแปด เวลา สิบนาฬิกาสามสิบนาที ราว ห้าสิบเปอร์เซ็นต์ หรือ สามจุดสองห้า เท่า"
    " สิบเอ็ด คน หนึ่งแสนหนึ่งหมื่นสี่พัน บาท ศูนย์ศูนย์เจ็ด"
)


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def tts(monkeypatch) -> FakeTts:
    fake = FakeTts()
    monkeypatch.setattr(spoil_maker, "start_tts_worker", fake)
    return fake


@pytest.fixture
def client(fake_root, tts, monkeypatch):
    """Every row a Voice job and a Render job check passes, with fresh job slots and a free GPU slot."""
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    monkeypatch.setattr(voices, "voice_jobs", voices.VoiceJobs())
    monkeypatch.setattr(render_module, "render_jobs", render_module.RenderJobs())
    return TestClient(app, base_url="http://127.0.0.1")


@pytest.fixture
def ready(project) -> None:
    """EP1 transcribed and described, and the draft's Saved voice."""
    ready_clip(project, EP1)
    write_voice(project)


def speak(client, *sentence_ids: str) -> dict:
    response = client.post(VOICE_JOBS, json={"kind": "sentences", "sentence_ids": list(sentence_ids)})
    assert response.status_code == 202, response.json()
    return response.json()


def wav_seconds(data: bytes) -> float:
    with wave.open(io.BytesIO(data)) as audio:
        return audio.getnframes() / audio.getframerate()


def statuses(client) -> list[str]:
    return [s["status"] for s in client.get(DRAFT).json()["sentences"]]


# --- Voice job `sentences` ---


def test_numbers_are_spoken_as_words_with_the_drafts_voice(client, project, ready, tts):
    write_draft(project, sentences=[sentence("s_00000001", NUMBERS, refs=[{"clip_id": EP1, "line": 1}])])

    job = speak(client, "s_00000001")

    assert (job["kind"], job["state"], job["done"], job["total"]) == ("sentences", "voicing", 0, 1)
    assert wait_for_end(client, VOICE_CURRENT)["state"] == "done"
    (request,) = tts.requests
    assert request.text == NUMBERS_SPOKEN
    assert (request.speed, request.num_step) == (1.0, 16)
    assert request.prompt == (project.voices_dir / f"{VOICE}.pt").read_bytes()
    assert client.get(DRAFT).json()["sentences"][0]["text"] == NUMBERS


def test_a_voiced_sentence_has_its_wav_its_length_and_reads_ready(client, project, ready, tts):
    write_draft(project)

    speak(client, "s_00000001")
    wait_for_end(client, VOICE_CURRENT)

    first = client.get(DRAFT).json()["sentences"][0]
    assert first["audio"] == {"tts_text": "ประโยคแรก", "voice_id": VOICE, "duration_s": 2.0}
    assert first["status"] == "ready"
    audio = client.get(f"{DRAFT}/sentences/s_00000001/audio.wav")
    assert (audio.status_code, audio.headers["content-type"]) == (200, "audio/wav")
    assert wav_seconds(audio.content) == 2.0


def test_a_sentence_wav_is_never_cached_so_a_new_voice_of_the_same_length_plays(client, project, ready, tts):
    write_draft(project)
    speak(client, "s_00000001")
    wait_for_end(client, VOICE_CURRENT)

    audio = client.get(f"{DRAFT}/sentences/s_00000001/audio.wav")

    assert audio.headers["cache-control"] == "no-store"


def test_cancelling_after_the_first_sentence_keeps_its_voice(client, project, ready, tts):
    write_draft(project)
    tts.pause_at(1)

    speak(client, "s_00000001", "s_00000002")
    tts.wait_until(1)
    assert wait_for(client, lambda job: job["done"] == 1, VOICE_CURRENT)["total"] == 2
    client.delete(VOICE_CURRENT)

    assert wait_for_end(client, VOICE_CURRENT)["state"] == "cancelled"
    assert statuses(client) == ["ready", "no_audio"]


def test_editing_while_sentences_are_voiced_is_draft_locked(client, project, ready, tts):
    write_draft(project)
    tts.pause_at(0)

    speak(client, "s_00000001")
    tts.wait_until(0)
    response = client.patch(f"{DRAFT}/sentences/s_00000002", json={"text": "ใหม่"})
    locked = client.get(DRAFT).json()["locked"]
    tts.release(0)

    assert (response.status_code, response.json()["code"]) == (409, "draft_locked")
    assert locked is True
    wait_for_end(client, VOICE_CURRENT)
    assert client.get(DRAFT).json()["locked"] is False


@pytest.mark.parametrize("ids", [["s_ffffffff"], [], "s_00000001", ["s_00000001", "s_00000001"]])
def test_ids_the_draft_does_not_have_are_invalid_request(client, project, ready, tts, ids):
    write_draft(project)

    response = client.post(VOICE_JOBS, json={"kind": "sentences", "sentence_ids": ids})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")
    assert tts.requests == []


def test_deleting_a_clip_of_the_draft_while_its_sentences_are_voiced_is_clip_busy(client, project, ready, tts):
    write_draft(project)
    tts.pause_at(0)

    speak(client, "s_00000001")
    tts.wait_until(0)
    response = client.delete(f"/api/spoil/clips/{EP1}")
    tts.release(0)

    assert (response.status_code, response.json()["code"]) == (409, "clip_busy")
    wait_for_end(client, VOICE_CURRENT)


def test_a_sentence_voiced_again_replaces_its_wav(client, project, ready, tts):
    write_draft(project)
    speak(client, "s_00000001")
    wait_for_end(client, VOICE_CURRENT)
    tts.seconds = 1.5

    speak(client, "s_00000001")
    wait_for_end(client, VOICE_CURRENT)

    assert client.get(DRAFT).json()["sentences"][0]["audio"]["duration_s"] == 1.5


def test_the_audio_of_a_sentence_without_voice_is_not_found(client, project, ready):
    write_draft(project)

    assert client.get(f"{DRAFT}/sentences/s_00000001/audio.wav").status_code == 404
    assert client.get(f"{DRAFT}/sentences/x/audio.wav").status_code == 404


# --- What the tab remembers ---

SETTINGS = "/api/spoil-maker/settings"
MARK = {"text": "@spoilerTH", "position": "bottom_right", "size": "small", "enabled": True}


def test_watermarks_are_remembered(client):
    marks = [MARK, {"text": "ห้ามนำไปใช้ต่อ", "position": "top_left", "size": "medium", "enabled": True}]

    response = client.patch(SETTINGS, json={"watermarks": marks})

    assert response.status_code == 200
    assert response.json()["watermarks"] == marks
    assert client.get(SETTINGS).json() == {"watermarks": marks, "original_volume": 20, "last_voice_id": None}


def test_a_switched_off_watermark_keeps_its_text_position_and_size(client):
    off = MARK | {"enabled": False}

    response = client.patch(SETTINGS, json={"watermarks": [off]})

    assert response.status_code == 200
    assert client.get(SETTINGS).json()["watermarks"] == [off]


def test_a_watermark_without_enabled_reads_on(client, project):
    """A `settings.json` written before D64, and a `PATCH` that leaves it out."""
    project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
    old = {k: v for k, v in MARK.items() if k != "enabled"}
    project.settings_file.write_text(json.dumps({"watermarks": [old]}), encoding="utf-8")

    assert client.get(SETTINGS).json()["watermarks"] == [MARK]
    assert client.patch(SETTINGS, json={"watermarks": [old]}).json()["watermarks"] == [MARK]


def test_the_volume_alone_keeps_the_watermarks(client):
    client.patch(SETTINGS, json={"watermarks": [MARK]})

    response = client.patch(SETTINGS, json={"original_volume": 35})

    assert (response.json()["watermarks"], response.json()["original_volume"]) == ([MARK], 35)


@pytest.mark.parametrize(
    "body",
    [
        {"watermarks": [MARK] * 7},
        {"watermarks": [MARK | {"position": "middle"}]},
        {"watermarks": [MARK | {"size": "large"}]},
        {"watermarks": [MARK | {"text": "  "}]},
        {"watermarks": [MARK | {"text": "ก" * 41}]},
        {"watermarks": [{"text": "x", "position": "top_left"}]},
        {"watermarks": "x"},
        {"watermarks": [MARK | {"enabled": "no"}]},
        {"watermarks": [MARK | {"enabled": 0}]},
        {"watermarks": [MARK | {"enabled": False}] * 2 + [MARK] * 5},  # 7: switched-off ones count
        {"original_volume": 33},
        {"original_volume": 105},
        {"last_voice_id": VOICE},
    ],
)
def test_values_outside_the_table_are_invalid_settings(client, body):
    response = client.patch(SETTINGS, json=body)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_settings")
    assert client.get(SETTINGS).json()["watermarks"] == []


def test_a_watermark_is_one_line(client):
    response = client.patch(SETTINGS, json={"watermarks": [MARK | {"text": " ช่อง\nสปอย "}]})

    assert response.json()["watermarks"][0]["text"] == "ช่อง สปอย"


# --- The Render job ---

RENDERS = "/api/spoil-maker/renders"
RENDER_CURRENT = "/api/spoil-maker/renders/current"
EP2 = "aaaaaaaaaaa"
# The test clip: red, white, blue a second each, so Shot n is [n, n + 1].
THREE_SHOTS = [{"n": n, "start": float(n), "end": n + 1.0, "description": f"Shot {n}."} for n in range(3)]


@pytest.fixture(scope="session")
def three_colours(tmp_path_factory) -> Path:
    return make_test_clip(tmp_path_factory.mktemp("clips") / "three.mp4")


@pytest.fixture
def renderable(project, ready, three_colours) -> None:
    """EP1 is the real 3-second clip with its three Shots."""
    shutil.copyfile(three_colours, project.media_temp_dir / f"{EP1}.mp4")
    (project.clip_shots_dir(EP1) / "shots.json").write_text(
        json.dumps({"clip_id": EP1, "shots": THREE_SHOTS}), encoding="utf-8"
    )


def shots(first: int, second: int) -> list[dict]:
    return [{"clip_id": EP1, "n": first}, {"clip_id": EP1, "n": second}]


def write_wav(project: ProjectPaths, sentence_id: str, seconds: float) -> None:
    project.draft_audio_dir.mkdir(parents=True, exist_ok=True)
    with wave.open(str(project.draft_audio_dir / f"{sentence_id}.wav"), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(FakeTts.SAMPLE_RATE)
        audio.writeframes(b"\0\0" * round(FakeTts.SAMPLE_RATE * seconds))


def voiced_sentence(project: ProjectPaths, sid: str, text: str, seconds: float, shot_pair=(0, 1)) -> dict:
    write_wav(project, sid, seconds)
    audio = voiced(thai.spoken(text), seconds)
    return sentence(sid, text, refs=[{"clip_id": EP1, "line": 1}], shots=shots(*shot_pair), audio=audio)


def two_sentence_draft(project: ProjectPaths, **fields) -> None:
    write_draft(
        project,
        sentences=[
            voiced_sentence(project, "s_00000001", "ชายคนหนึ่งตื่นมา", 2.0, (0, 1)),
            voiced_sentence(project, "s_00000002", "ปี 1968 เขาหนี", 1.5, (1, 2)),
        ],
        **fields,
    )


def render(client) -> dict:
    response = client.post(RENDERS, json={})
    assert response.status_code == 202, response.json()
    return wait_for_end(client, RENDER_CURRENT)


def media(path: Path) -> dict:
    """Length, picture size and whether there is sound, from `ffmpeg -i` (no ffprobe, ADR 0005)."""
    import re
    import subprocess

    import imageio_ffmpeg

    result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    hours, minutes, seconds = re.search(r"Duration: (\d+):(\d\d):(\d\d\.\d+)", result.stderr).groups()
    size = re.search(r"Video: .*?(\d{3,4})x(\d{3,4})", result.stderr).groups()
    return {
        "duration": int(hours) * 3600 + int(minutes) * 60 + float(seconds),
        "size": tuple(int(n) for n in size),
        "audio": "Audio:" in result.stderr,
    }


def only_render(project: ProjectPaths) -> str:
    (mp4,) = project.renders_dir.glob("*.mp4")
    return mp4.stem


@pytest.mark.parametrize("layout", ["A", "B", "C"])
def test_a_render_is_a_vertical_mp4_as_long_as_the_voice_with_an_srt(client, project, renderable, layout):
    two_sentence_draft(project, layout=layout, top_text="คดีหลอน")

    job = render(client)

    assert job["state"] == "done", job
    name = only_render(project)
    found = media(project.renders_dir / f"{name}.mp4")
    assert found["size"] == (1080, 1920)
    assert found["duration"] == pytest.approx(3.5, abs=0.2)
    assert found["audio"] is True
    assert (project.renders_dir / f"{name}.srt").read_text(encoding="utf-8") == (
        "1\n00:00:00,000 --> 00:00:02,000\nชายคนหนึ่งตื่นมา\n\n"
        "2\n00:00:02,000 --> 00:00:03,500\nปี 1968 เขาหนี\n"
    )
    assert not project.render_work_dir.exists()


def test_a_render_job_reports_rendering_with_a_percent(client, project, renderable):
    two_sentence_draft(project)

    response = client.post(RENDERS, json={})

    assert response.status_code == 202
    assert (response.json()["kind"], response.json()["state"], response.json()["percent"]) == ("render", "rendering", 0)
    assert wait_for_end(client, RENDER_CURRENT)["percent"] == 100


def test_a_shot_near_the_clips_end_holds_its_last_frame(client, project, renderable):
    # Shot 2 starts 1 s before the clip ends; each Shot plays 2 s of a 4-second sentence.
    write_draft(project, sentences=[voiced_sentence(project, "s_00000001", "ยาว", 4.0, (2, 2))])

    job = render(client)

    assert job["state"] == "done", job
    assert media(project.renders_dir / f"{only_render(project)}.mp4")["duration"] == pytest.approx(4.0, abs=0.2)


def test_a_sentence_without_voice_is_voiced_first_and_only_it(client, project, renderable, tts):
    tts.seconds = 1.0
    write_draft(
        project,
        sentences=[
            voiced_sentence(project, "s_00000001", "มีเสียงแล้ว", 2.0),
            sentence("s_00000002", "ยังไม่มีเสียง", refs=[{"clip_id": EP1, "line": 1}], shots=shots(1, 2)),
        ],
    )
    tts.pause_at(0)

    started = client.post(RENDERS, json={}).json()
    tts.wait_until(0)
    voicing = client.get(RENDER_CURRENT).json()
    tts.release(0)
    job = wait_for(client, lambda job: job["state"] in {"rendering", "done", "failed"}, RENDER_CURRENT)

    assert (started["state"], voicing["done"], voicing["total"]) == ("voicing", 0, 1)
    assert job["state"] != "failed", job
    assert [request.text for request in tts.requests] == ["ยังไม่มีเสียง"]
    assert wait_for_end(client, RENDER_CURRENT)["state"] == "done"
    assert media(project.renders_dir / f"{only_render(project)}.mp4")["duration"] == pytest.approx(3.0, abs=0.2)


def test_deleting_a_clip_of_the_draft_while_a_render_voices_is_clip_busy(client, project, renderable, tts):
    write_draft(project, sentences=[sentence("s_00000001", "ยังไม่มีเสียง", refs=[{"clip_id": EP1, "line": 1}], shots=shots(0, 1))])
    tts.pause_at(0)

    client.post(RENDERS, json={})
    tts.wait_until(0)
    response = client.delete(f"/api/spoil/clips/{EP1}")
    tts.release(0)

    assert (response.status_code, response.json()["code"]) == (409, "clip_busy")
    wait_for_end(client, RENDER_CURRENT)


@pytest.fixture
def paused_ffmpeg(monkeypatch):
    """A Render job holder whose runner holds the first ffmpeg run until the test sets
    `release` (or cancels), as `fastapi-api` › testing pauses a job that runs ffmpeg."""
    import threading

    from backend.spoil_maker import compose

    reached, release = threading.Event(), threading.Event()

    def run(command, cwd, cancel, on_progress=None):
        reached.set()
        while not (release.is_set() or cancel.is_set()):
            cancel.wait(0.01)
        return compose.run(command, cwd, cancel, on_progress)

    monkeypatch.setattr(render_module, "render_jobs", render_module.RenderJobs(run_ffmpeg=run))
    return reached, release


def test_a_describe_starts_while_a_render_with_every_voice_runs_ffmpeg(
    client, project, renderable, paused_ffmpeg, monkeypatch, three_colours
):
    """spec › Seams 1: no sentence lacks its voice, so the render never takes the GPU."""
    from backend.spoil_maker import describe

    from .fakes import FakeLlm

    reached, release = paused_ffmpeg
    monkeypatch.setattr(describe, "describes", describe.Describes())
    monkeypatch.setattr(spoil_maker, "start_worker", FakeLlm())
    ready_clip(project, EP2)
    shutil.copyfile(three_colours, project.media_temp_dir / f"{EP2}.mp4")
    two_sentence_draft(project)

    assert client.post(RENDERS, json={}).json()["state"] == "rendering"
    assert reached.wait(5)
    response = client.post("/api/spoil-maker/describes", json={"clip_id": EP2})
    release.set()

    assert response.status_code == 202, response.json()
    assert wait_for_end(client, RENDER_CURRENT)["state"] == "done"
    wait_for_end(client, "/api/spoil-maker/describes/current")  # no job outlives the test


def test_a_render_draws_only_the_switched_on_watermarks(client, project, renderable, paused_ffmpeg):
    reached, release = paused_ffmpeg
    client.patch(SETTINGS, json={"watermarks": [MARK | {"text": "@เปิด"}, MARK | {"text": "@ปิด", "enabled": False}]})
    two_sentence_draft(project)

    client.post(RENDERS, json={})
    assert reached.wait(5)  # the ASS file is written, ffmpeg not yet run
    ass = (project.render_work_dir / render_module.CAPTIONS).read_text(encoding="utf-8")
    release.set()

    assert "@เปิด" in ass
    assert "@ปิด" not in ass
    assert wait_for_end(client, RENDER_CURRENT)["state"] == "done"


def test_a_render_frees_the_gpu_once_its_sentences_are_voiced(
    client, project, renderable, paused_ffmpeg, monkeypatch, three_colours
):
    from backend.spoil_maker import describe

    from .fakes import FakeLlm

    reached, release = paused_ffmpeg
    monkeypatch.setattr(describe, "describes", describe.Describes())
    monkeypatch.setattr(spoil_maker, "start_worker", FakeLlm())
    ready_clip(project, EP2)
    shutil.copyfile(three_colours, project.media_temp_dir / f"{EP2}.mp4")
    write_draft(project, sentences=[sentence("s_00000001", "ยังไม่มีเสียง", refs=[{"clip_id": EP1, "line": 1}], shots=shots(0, 1))])

    assert client.post(RENDERS, json={}).json()["state"] == "voicing"
    assert reached.wait(5)  # voiced, now in ffmpeg
    response = client.post("/api/spoil-maker/describes", json={"clip_id": EP2})
    release.set()

    assert response.status_code == 202, response.json()
    assert wait_for_end(client, RENDER_CURRENT)["state"] == "done"
    wait_for_end(client, "/api/spoil-maker/describes/current")


def test_cancelling_while_rendering_leaves_no_partial_files(client, project, renderable, paused_ffmpeg):
    reached, _ = paused_ffmpeg
    two_sentence_draft(project)

    client.post(RENDERS, json={})
    assert reached.wait(5)
    client.delete(RENDER_CURRENT)

    assert wait_for_end(client, RENDER_CURRENT)["state"] == "cancelled"
    assert not project.render_work_dir.exists()
    assert not any(project.renders_dir.glob("*.partial"))
    assert client.get(RENDERS).json() == []


def test_a_sentence_without_a_shot_is_missing_shots(client, project, renderable):
    write_draft(project, sentences=[sentence("s_00000001", "ไม่มีภาพ", shots=[None, None])])

    response = client.post(RENDERS, json={})

    assert response.status_code == 400
    assert (response.json()["code"], response.json()["sentence_ids"]) == ("missing_shots", ["s_00000001"])


def test_under_one_gib_free_is_disk_full(client, project, renderable, monkeypatch):
    from backend import disk

    two_sentence_draft(project)
    monkeypatch.setattr(disk, "free_bytes", lambda path: 512 * 1024**2)

    response = client.post(RENDERS, json={})

    assert (response.status_code, response.json()["code"]) == (507, "disk_full")


def test_no_draft_is_no_draft(client):
    response = client.post(RENDERS, json={})

    assert (response.status_code, response.json()["code"]) == (404, "no_draft")


def test_without_kanit_a_render_is_not_ready(client, project, renderable):
    two_sentence_draft(project)
    project.kanit_marker.unlink()

    response = client.post(RENDERS, json={})

    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", ["font_kanit"])


def test_two_renders_are_listed_newest_first_with_their_source_titles(client, project, renderable):
    two_sentence_draft(project)
    render(client)
    render(client)

    listed = client.get(RENDERS).json()

    assert len(listed) == 2
    assert listed[0]["name"] > listed[1]["name"]
    assert listed[0]["sources"] == ["ชื่อคลิป"]
    assert listed[0]["duration_s"] == pytest.approx(3.5, abs=0.2)
    assert listed[0]["size_bytes"] == (project.renders_dir / f"{listed[0]['name']}.mp4").stat().st_size


def test_a_render_is_served_and_deleted(client, project, renderable):
    two_sentence_draft(project)
    render(client)
    name = only_render(project)

    video = client.get(f"{RENDERS}/{name}.mp4", headers={"Range": "bytes=0-99"})
    srt = client.get(f"{RENDERS}/{name}.srt")
    deleted = client.delete(f"{RENDERS}/{name}")

    assert (video.status_code, len(video.content)) == (206, 100)
    assert srt.status_code == 200
    assert srt.headers["content-disposition"].startswith("attachment")
    assert deleted.status_code == 204
    assert list(project.renders_dir.glob(f"{name}.*")) == []
    assert client.get(RENDERS).json() == []


@pytest.mark.parametrize("path", ["/renders/../x.mp4", "/renders/..%2Fx.mp4", "/renders/2026-1103.mp4", "/renders/20261103-100000.mp4"])
def test_a_render_that_is_not_there_is_not_found(client, path):
    assert client.get(f"/api/spoil-maker{path}").status_code == 404


def test_deleting_a_render_that_is_not_there_is_not_found(client):
    assert client.delete(f"{RENDERS}/20261103-100000").status_code == 404


def test_a_render_outlives_its_clip(client, project, renderable):
    two_sentence_draft(project)
    render(client)

    assert client.delete(f"/api/spoil/clips/{EP1}").status_code == 204
    assert len(client.get(RENDERS).json()) == 1


def test_start_up_removes_unfinished_renders(fake_root, project, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    project.renders_dir.mkdir(parents=True)
    (project.renders_dir / "x.partial").write_bytes(b"half")
    project.render_work_dir.mkdir(parents=True)
    (project.render_work_dir / "0.mkv").write_bytes(b"half")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert not (project.renders_dir / "x.partial").exists()
    assert not project.render_work_dir.exists()


def test_the_srt_keeps_numbers_as_written(client, project, renderable, tts):
    write_draft(project, sentences=[sentence("s_00000001", NUMBERS, refs=[{"clip_id": EP1, "line": 1}], shots=shots(0, 1))])

    job = render(client)

    assert job["state"] == "done", job
    assert tts.requests[0].text == NUMBERS_SPOKEN
    assert NUMBERS in (project.renders_dir / f"{only_render(project)}.srt").read_text(encoding="utf-8")
