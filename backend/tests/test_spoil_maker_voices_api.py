"""Saved voices and the Voice job `design_preview`, under /api/spoil-maker, with a fake
OmniVoice worker (spoil-maker seam 1 › เสียงและตัวเลข)."""

import wave

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil_maker
from backend.app import app
from backend.models import OMNIVOICE, QWEN_MAC
from backend.paths import ProjectPaths
from backend.spoil_maker import voices

from .fakes import CODE_ERROR, GPU_ERROR, FakeTts, cuda_device, card, on_windows, poll_until

FINISHED = {"done", "failed", "cancelled"}
JOBS = "/api/spoil-maker/voice-jobs"
CURRENT = "/api/spoil-maker/voice-jobs/current"
VOICES = "/api/spoil-maker/voices"
DESIGN = {"kind": "design_preview", "gender": "female", "age": "young adult", "pitch": "low pitch", "speed": 1.1}


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
    """Every row the Voice job checks passes, with a fresh job slot and a free GPU slot."""
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    monkeypatch.setattr(voices, "voice_jobs", voices.VoiceJobs())
    return TestClient(app, base_url="http://127.0.0.1")


def wait_for(client, condition) -> dict:
    return poll_until(client, CURRENT, condition)


def wait_for_end(client) -> dict:
    return wait_for(client, lambda job: job["state"] in FINISHED)


def design(client, **changes) -> dict:
    """A `design_preview` that ran to its end."""
    response = client.post(JOBS, json={**DESIGN, **changes})
    assert response.status_code == 202, response.json()
    return wait_for_end(client)


def save(client, name: str = "พี่สาวเล่าหนัง") -> dict:
    design(client)
    response = client.post(VOICES, json={"name": name})
    assert response.status_code == 201, response.json()
    return response.json()


def wav_seconds(data: bytes) -> float:
    import io

    with wave.open(io.BytesIO(data)) as audio:
        return audio.getnframes() / audio.getframerate()


# --- design_preview ---


def test_a_design_preview_speaks_the_sample_sentence_with_the_chosen_voice(client, tts):
    response = client.post(JOBS, json=DESIGN)

    assert response.status_code == 202
    body = response.json()
    assert (body["kind"], body["state"], body["error"]) == ("design_preview", "voicing", None)
    assert wait_for_end(client)["state"] == "done"
    (request,) = tts.requests
    assert request.instruct == "female, young adult, low pitch"
    assert request.text == voices.SAMPLE_SENTENCE
    assert (request.speed, request.num_step) == (1.1, 16)


def test_the_preview_is_a_wav_of_what_the_tts_spoke(client, tts):
    tts.seconds = 1.5
    design(client)

    response = client.get(f"{JOBS}/preview.wav")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert wav_seconds(response.content) == 1.5


def test_no_preview_wav_before_a_design_ran(client):
    assert client.get(f"{JOBS}/preview.wav").status_code == 404
    assert client.head(f"{JOBS}/preview.wav").status_code == 404


def test_head_says_a_preview_is_there_without_sending_it(client):
    design(client)

    response = client.head(f"{JOBS}/preview.wav")

    assert (response.status_code, response.content) == (200, b"")


@pytest.mark.parametrize(
    "changes",
    [{"speed": 1.3}, {"speed": 0.75}, {"speed": 0.83}, {"age": "baby"}, {"gender": "other"}, {"pitch": "low"}],
)
def test_a_value_outside_the_lists_is_invalid_voice(client, tts, changes):
    response = client.post(JOBS, json={**DESIGN, **changes})

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_voice"
    assert tts.requests == []


def test_sentences_with_ids_that_no_draft_has_are_invalid_request(client):
    response = client.post(JOBS, json={"kind": "sentences", "sentence_ids": ["s_0000abcd"]})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_an_unknown_kind_is_invalid_request(client):
    response = client.post(JOBS, json={"kind": "clone"})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_a_second_design_while_one_runs_is_busy(client, tts):
    tts.pause_at(0)
    client.post(JOBS, json=DESIGN)
    tts.wait_until(0)

    response = client.post(JOBS, json=DESIGN)

    assert (response.status_code, response.json()["code"]) == (409, "busy")
    tts.release(0)
    wait_for_end(client)


def test_a_design_during_a_describe_job_is_gpu_busy_naming_it(client, tts):
    gpu.slot.take("describe", ["dQw4w9WgXcQ"])

    response = client.post(JOBS, json=DESIGN)

    assert response.status_code == 409
    assert (response.json()["code"], response.json()["running"]) == ("gpu_busy", "describe")
    assert tts.requests == []


def test_a_design_holds_the_gpu_until_it_ends(client, tts):
    tts.pause_at(0)
    client.post(JOBS, json=DESIGN)
    tts.wait_until(0)

    with pytest.raises(Exception) as refused:
        gpu.slot.take("describe")
    assert refused.value.extra["running"] == "voice"
    tts.release(0)
    wait_for_end(client)
    gpu.slot.take("describe")  # free again


def test_a_design_does_not_need_qwen(client, project):
    project.marker(QWEN_MAC).unlink()

    assert client.post(JOBS, json=DESIGN).status_code == 202
    assert wait_for_end(client)["state"] == "done"


def test_on_windows_a_card_torch_has_no_kernels_for_refuses_a_design(client, tts, monkeypatch):
    on_windows(monkeypatch, card("NVIDIA GeForce GTX 1050 Ti", 4, (6, 1)))

    response = client.post(JOBS, json=DESIGN)

    assert response.status_code == 503
    assert (response.json()["code"], response.json()["rows"]) == ("not_ready", ["device"])


def test_without_the_omnivoice_marker_a_design_is_not_ready(client, project, tts):
    project.marker(OMNIVOICE).unlink()

    response = client.post(JOBS, json=DESIGN)

    assert response.status_code == 503
    assert (response.json()["code"], response.json()["rows"]) == ("not_ready", ["model_omnivoice"])
    assert tts.requests == []


def test_the_worker_loads_omnivoice_from_its_snapshot_on_the_found_device(client, project, tts):
    design(client)

    (process,) = tts.processes
    assert process.snapshot_dir == project.snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
    assert process.args == ("cuda",)


def test_cancelling_keeps_the_previous_preview(client, tts):
    tts.seconds = 1.0
    design(client)
    tts.pause_at(0)  # counts the requests of each process
    client.post(JOBS, json=DESIGN)
    tts.wait_until(0)

    response = client.delete(CURRENT)

    assert response.status_code == 202
    assert response.json()["cancel_requested"] is True
    assert wait_for_end(client)["state"] == "cancelled"
    assert tts.processes[1].terminated is True
    assert wav_seconds(client.get(f"{JOBS}/preview.wav").content) == 1.0


def test_cancelling_with_no_job_running_is_not_found(client):
    assert client.delete(CURRENT).status_code == 404


def test_the_current_job_is_null_before_any(client):
    assert client.get(CURRENT).json() is None


@pytest.mark.parametrize(
    ("failure", "message"),
    [(CODE_ERROR, f"สร้างเสียงไม่สำเร็จ: {CODE_ERROR}"), (GPU_ERROR, f"สร้างเสียงไม่สำเร็จ: {GPU_ERROR}. {gpu.ADVICE}")],
)
def test_a_worker_error_fails_the_job_as_model_failed_and_only_one_of_the_gpu_ends_with_the_advice(client, tts, failure, message):
    """toon D84: an error of the code says what it is, without pointing at other apps on the GPU."""
    tts.fail_at, tts.fail_with = 0, failure

    job = design(client)

    assert (job["state"], job["error"]) == ("failed", {"code": "model_failed", "message": message})
    assert client.get(f"{JOBS}/preview.wav").status_code == 404


def test_a_worker_that_dies_fails_the_job_as_crashed(client, tts):
    tts.crash_at = 0

    job = design(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "crashed")


# --- Saved voices ---


def test_saving_the_preview_makes_a_voice_with_its_measured_speaking_speed(client, tts, project):
    tts.seconds = 2.0
    design(client, speed=0.9)

    response = client.post(VOICES, json={"name": "  พี่สาวเล่าหนัง "})

    assert response.status_code == 201
    voice = response.json()
    # The sample sentence has 76 letters once spaces and punctuation are left out.
    assert voice["chars_per_s"] == 38.0
    assert (voice["name"], voice["speed"], voice["in_use"]) == ("พี่สาวเล่าหนัง", 0.9, False)
    assert voice["id"].startswith("v_") and len(voice["id"]) == 10
    assert client.get(VOICES).json() == [voice]
    for suffix in (".json", ".pt", ".wav"):
        assert (project.voices_dir / f"{voice['id']}{suffix}").is_file()
    assert (project.voices_dir / f"{voice['id']}.pt").read_bytes() == b"prompt 0"


def test_the_saved_voice_keeps_its_instruct_and_kind(client, project):
    voice = save(client)

    import json

    stored = json.loads((project.voices_dir / f"{voice['id']}.json").read_text(encoding="utf-8"))
    assert (stored["kind"], stored["instruct"]) == ("design", "female, young adult, low pitch")


def test_the_sample_of_a_saved_voice_is_its_preview(client, tts):
    tts.seconds = 1.25
    voice = save(client)

    response = client.get(f"{VOICES}/{voice['id']}/sample.wav")

    assert response.status_code == 200
    assert wav_seconds(response.content) == 1.25


def test_saving_takes_the_preview_away(client):
    save(client)

    assert client.get(f"{JOBS}/preview.wav").status_code == 404
    response = client.post(VOICES, json={"name": "อีกเสียง"})
    assert (response.status_code, response.json()["code"]) == (409, "no_preview")


def test_saving_with_no_preview_is_no_preview(client):
    response = client.post(VOICES, json={"name": "เสียงแรก"})

    assert (response.status_code, response.json()["code"]) == (409, "no_preview")


def test_a_second_design_replaces_the_first_preview(client, tts):
    tts.seconds = 1.0
    design(client)
    tts.seconds = 4.0
    design(client)

    voice = client.post(VOICES, json={"name": "ล่าสุด"}).json()

    assert voice["chars_per_s"] == 19.0  # 76 letters in 4 s
    assert (ProjectPaths(paths.ROOT).voices_dir / f"{voice['id']}.pt").read_bytes() == b"prompt 1"


@pytest.mark.parametrize("name", ["ก" * 41, "   ", ""])
def test_saving_with_a_bad_name_is_invalid_voice(client, name):
    design(client)

    response = client.post(VOICES, json={"name": name})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_voice")


def test_voices_are_listed_newest_first(client):
    first = save(client, "แรก")
    second = save(client, "สอง")

    assert [v["id"] for v in client.get(VOICES).json()] == [second["id"], first["id"]]


def test_no_voices_is_an_empty_list(client):
    assert client.get(VOICES).json() == []


def test_renaming_a_voice(client):
    voice = save(client)

    response = client.patch(f"{VOICES}/{voice['id']}", json={"name": "ผู้ชายเสียงต่ำ"})

    assert response.status_code == 200
    assert response.json() == {**voice, "name": "ผู้ชายเสียงต่ำ"}
    assert client.get(VOICES).json()[0]["name"] == "ผู้ชายเสียงต่ำ"


@pytest.mark.parametrize("name", ["ก" * 41, "   "])
def test_renaming_to_a_bad_name_is_invalid_voice(client, name):
    voice = save(client)

    response = client.patch(f"{VOICES}/{voice['id']}", json={"name": name})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_voice")
    assert client.get(VOICES).json()[0]["name"] == "พี่สาวเล่าหนัง"


def test_a_forty_letter_name_is_fine(client):
    voice = save(client)

    assert client.patch(f"{VOICES}/{voice['id']}", json={"name": "ก" * 40}).status_code == 200


@pytest.mark.parametrize("voice_id", ["v_0000abcd", "v_XYZ", "..%2Fx"])
def test_renaming_an_unknown_voice_is_not_found(client, voice_id):
    response = client.patch(f"{VOICES}/{voice_id}", json={"name": "ชื่อ"})

    assert (response.status_code, response.json()["code"]) == (404, "not_found")


def test_deleting_a_voice_removes_its_three_files(client, project):
    voice = save(client)

    response = client.delete(f"{VOICES}/{voice['id']}")

    assert response.status_code == 204
    assert list(project.voices_dir.glob(f"{voice['id']}*")) == []
    assert client.get(f"{VOICES}/{voice['id']}/sample.wav").status_code == 404
    assert client.get(VOICES).json() == []


def test_deleting_an_unknown_voice_is_not_found(client):
    assert client.delete(f"{VOICES}/v_0000abcd").status_code == 404


def test_a_sample_of_an_unknown_voice_is_not_found(client):
    response = client.get(f"{VOICES}/v_0000abcd/sample.wav")

    assert (response.status_code, response.json()["code"]) == (404, "not_found")


# --- Start and safety ---


def test_starting_the_app_drops_a_preview_that_was_never_saved(client, project):
    design(client)
    assert client.get(f"{JOBS}/preview.wav").status_code == 200
    (project.voices_dir / "v_0000abcd.json.tmp").write_text("{", encoding="utf-8")

    with TestClient(app, base_url="http://127.0.0.1") as restarted:
        assert restarted.get(f"{JOBS}/preview.wav").status_code == 404
    assert not project.pending_voice_dir.exists()
    assert not (project.voices_dir / "v_0000abcd.json.tmp").exists()


def test_starting_the_app_keeps_saved_voices(client):
    voice = save(client)

    with TestClient(app, base_url="http://127.0.0.1") as restarted:
        assert restarted.get(VOICES).json() == [voice]


@pytest.mark.parametrize("path", [VOICES, CURRENT, f"{JOBS}/preview.wav"])
def test_another_host_is_refused(client, path):
    response = client.get(path, headers={"Host": "evil.example"})

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("method", "path"),
    [("post", JOBS), ("post", VOICES), ("patch", f"{VOICES}/v_0000abcd")],
)
def test_posts_and_patches_must_be_json(client, method, path):
    response = client.request(method, path, content='{"name": "x"}', headers={"Content-Type": "text/plain"})

    assert response.status_code == 415
