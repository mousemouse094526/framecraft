"""The Spoil draft, its edits, the token count and the Draft job, under /api/spoil-maker,
and what a draft changes under /api/spoil, with a fake LLM worker and a fake token
counter (spoil-maker seam 1)."""

import json
import re
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil, spoil_maker
from backend.app import app
from backend.models import QWEN
from backend.paths import ProjectPaths
from backend.spoil import transcribe
from backend.spoil_maker import describe, draft, voices

from .fakes import (
    FakeLlm,
    FakeWorker,
    cuda_device,
    make_test_clip,
    ok_ffmpeg,
    write_temp_clip,
    write_transcript,
)

EP1 = "dQw4w9WgXcQ"
EP2 = "aaaaaaaaaaa"
VOICE = "v_0000abcd"
OTHER_VOICE = "v_0000ef01"
FINISHED = {"done", "failed", "cancelled"}
JOBS = "/api/spoil-maker/draft-jobs"
CURRENT = "/api/spoil-maker/draft-jobs/current"
DRAFT = "/api/spoil-maker/draft"

# A line every 10 s; with a Shot every 5 s, line n is Shots 2n and 2n + 1.
LINES = [{"start_s": 10.0 * n, "end_s": 10.0 * n + 4, "text": f"Line {n}."} for n in range(20)]
SHOT_COUNT = 40
# 15 letters a second and 60 s: 900 letters; each script sentence below is 30 (spoken, no spaces).
THIRTY = "ก" * 30
PASSING = 30  # sentences of THIRTY: 900 letters, the target


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def llm(monkeypatch) -> FakeLlm:
    fake = FakeLlm()
    fake.scripts = []  # replies to script prompts, in order; the last one repeats
    fake.picks = lambda request: '{"shots": [0, 1]}'
    fake.respond = lambda request: _respond(fake, request)
    monkeypatch.setattr(spoil_maker, "start_worker", fake)
    return fake


def is_pick(request) -> bool:
    """Picking Shots and writing the script differ in their generation settings (spec › ค่าการสร้างข้อความ)."""
    return request.max_tokens == draft.PICK_MAX_TOKENS


def _respond(fake: FakeLlm, request) -> str:
    if is_pick(request):
        return fake.picks(request)
    scripts = [r for r in fake.requests if not is_pick(r)]
    reply = fake.scripts[min(len(scripts) - 1, len(fake.scripts) - 1)]
    return reply(request) if callable(reply) else reply


@pytest.fixture
def counted(monkeypatch) -> list[str]:
    """The fake token counter: a token per character, and every text it counted."""
    texts: list[str] = []

    def count(snapshot_dir: Path, text: str) -> int:
        texts.append(text)
        return len(text)

    monkeypatch.setattr(spoil_maker, "count_tokens", count)
    return texts


@pytest.fixture
def whisper(monkeypatch) -> FakeWorker:
    fake = FakeWorker()
    monkeypatch.setattr(spoil, "start_worker", fake)
    return fake


@pytest.fixture
def client(fake_root, llm, counted, whisper, monkeypatch):
    """Everything the gates check passes, with fresh job slots and a free GPU slot."""
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    monkeypatch.setattr(draft, "draft_jobs", draft.DraftJobs())
    monkeypatch.setattr(describe, "describes", describe.Describes())
    monkeypatch.setattr(transcribe, "transcriptions", transcribe.Transcriptions())
    return TestClient(app, base_url="http://127.0.0.1")


def ready_clip(project: ProjectPaths, video_id: str = EP1, described: bool = True, lines=LINES) -> None:
    """A Temp clip that is transcribed and, unless told not, described."""
    write_temp_clip(project, video_id)
    write_transcript(project, video_id, lines=lines)
    if described:
        write_shots(project, video_id)


def write_shots(project: ProjectPaths, video_id: str, count: int = SHOT_COUNT) -> None:
    folder = project.clip_shots_dir(video_id)
    folder.mkdir(parents=True, exist_ok=True)
    found = [{"n": n, "start": 5.0 * n, "end": 5.0 * n + 5, "description": f"Shot {n}."} for n in range(count)]
    (folder / "shots.json").write_text(json.dumps({"clip_id": video_id, "shots": found}), encoding="utf-8")


def write_voice(project: ProjectPaths, voice_id: str = VOICE, chars_per_s: float = 15.0) -> None:
    project.voices_dir.mkdir(parents=True, exist_ok=True)
    stored = {
        "name": "เสียง",
        "kind": "design",
        "speed": 1.0,
        "chars_per_s": chars_per_s,
        "created_at": "2026-11-02T10:00:00+07:00",
        "instruct": "female, young adult, moderate pitch",
    }
    (project.voices_dir / f"{voice_id}.json").write_text(json.dumps(stored), encoding="utf-8")
    (project.voices_dir / f"{voice_id}.wav").write_bytes(b"wav")
    (project.voices_dir / f"{voice_id}.pt").write_bytes(b"pt")


def script(*sentences, top_text: str = "") -> str:
    """A script reply: each sentence `(text, refs)`."""
    body = {"top_text": top_text, "sentences": [{"text": text, "refs": refs} for text, refs in sentences]}
    return json.dumps(body, ensure_ascii=False)


def passing_script(refs=("1-0",)) -> str:
    return script(*[(THIRTY, list(refs))] * PASSING)


def order(**overrides) -> dict:
    return {
        "kind": "draft",
        "clip_ids": [EP1],
        "style": "drama",
        "layout": "B",
        "target_s": 60,
        "voice_id": VOICE,
        "replace": False,
    } | overrides


def start(client, **overrides):
    return client.post(JOBS, json=order(**overrides))


def wait_for(client, condition, path: str = CURRENT) -> dict:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        job = client.get(path).json()
        if condition(job):
            return job
        time.sleep(0.01)
    raise AssertionError(f"job never got there: {job}")


def wait_for_end(client, path: str = CURRENT) -> dict:
    return wait_for(client, lambda job: job is not None and job["state"] in FINISHED, path)


def write_draft(project: ProjectPaths, clip_ids=(EP1,), sentences=None, voice_id: str = VOICE, **fields) -> dict:
    """A `draft.json` as a finished Draft job leaves it; returns its content."""
    content = {
        "version": 1,
        "clip_ids": list(clip_ids),
        "style": "drama",
        "layout": "B",
        "target_s": 60,
        "voice_id": voice_id,
        "original_volume": 20,
        "top_text": "",
        "sentences": sentences
        if sentences is not None
        else [
            sentence("s_00000001", "ประโยคแรก", refs=[{"clip_id": clip_ids[0], "line": 1}]),
            sentence("s_00000002", "ประโยคสอง", refs=[{"clip_id": clip_ids[0], "line": 2}]),
        ],
    } | fields
    project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
    project.draft_file.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    return content


def sentence(sid: str, text: str, refs=(), shots=None, audio=None) -> dict:
    clip_id = refs[0]["clip_id"] if refs else EP1
    return {
        "id": sid,
        "text": text,
        "refs": list(refs),
        "shots": shots if shots is not None else [{"clip_id": clip_id, "n": 2}, {"clip_id": clip_id, "n": 3}],
        "audio": audio,
    }


def voiced(text: str, seconds: float = 2.0, voice_id: str = VOICE) -> dict:
    return {"tts_text": text, "voice_id": voice_id, "duration_s": seconds}


def a_draft(client) -> dict:
    return client.get(DRAFT).json()


@pytest.fixture
def ready(project) -> None:
    """EP1 and EP2 transcribed and described, and a Saved voice of 15 letters a second."""
    ready_clip(project, EP1)
    ready_clip(project, EP2)
    write_voice(project)


# --- Starting a Draft job: the checks, in spec order ---


def test_a_clip_transcribed_but_not_described_is_clip_not_ready(client, project, ready):
    ready_clip(project, "bbbbbbbbbbb", described=False)

    response = start(client, clip_ids=[EP1, "bbbbbbbbbbb"])

    assert response.status_code == 400
    assert response.json()["code"] == "clip_not_ready"
    assert response.json()["clip_ids"] == ["bbbbbbbbbbb"]


def test_the_same_clip_twice_is_clip_not_ready(client, ready):
    response = start(client, clip_ids=[EP1, EP1])

    assert (response.status_code, response.json()["code"], response.json()["clip_ids"]) == (400, "clip_not_ready", [EP1])


@pytest.mark.parametrize("target_s", [29, 181, 60.5])
def test_a_target_outside_30_to_180_whole_seconds_is_invalid_target(client, ready, target_s):
    response = start(client, target_s=target_s)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_target")


@pytest.mark.parametrize("field, value", [("style", "x"), ("layout", "D")])
def test_an_unknown_style_or_layout_is_invalid_request(client, ready, field, value):
    response = start(client, **{field: value})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_an_unknown_voice_is_voice_not_found(client, ready):
    response = start(client, voice_id="v_ffffffff")

    assert (response.status_code, response.json()["code"]) == (400, "voice_not_found")


def test_transcripts_over_32000_tokens_are_too_long(client, ready, monkeypatch):
    monkeypatch.setattr(spoil_maker, "count_tokens", lambda snapshot, text: 16_001 if "[1-" in text else 16_000)

    response = start(client, clip_ids=[EP1, EP2])
    counted = client.get(f"/api/spoil-maker/tokens?clip_ids={EP1},{EP2}")

    assert response.status_code == 400
    assert response.json() == {
        "code": "transcript_too_long",
        "message": "Transcript รวม 32,001 token เกิน 32,000",
        "tokens": 32_001,
    }
    assert counted.status_code == 200
    assert counted.json() == {"per_clip": {EP1: 16_001, EP2: 16_000}, "total": 32_001, "limit": 32_000}


def test_tokens_count_each_transcript_as_the_llm_gets_it_numbered_by_order(client, project, ready, counted):
    client.get(f"/api/spoil-maker/tokens?clip_ids={EP2},{EP1}")

    assert counted[0].startswith("[1-0 00:00:00] Line 0.\n[1-1 00:00:10] Line 1.\n")
    assert counted[1].startswith("[2-0 00:00:00] Line 0.\n")


def test_tokens_with_qwens_snapshot_gone_are_not_ready(client, project, ready, monkeypatch):
    def gone(snapshot_dir, text):
        raise FileNotFoundError(snapshot_dir)

    monkeypatch.setattr(spoil_maker, "count_tokens", gone)

    response = client.get(f"/api/spoil-maker/tokens?clip_ids={EP1}")

    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", ["model_qwen"])


def test_tokens_of_a_clip_not_transcribed_are_clip_not_ready(client, project, ready):
    write_temp_clip(project, "bbbbbbbbbbb")

    response = client.get(f"/api/spoil-maker/tokens?clip_ids={EP1},bbbbbbbbbbb")

    assert (response.status_code, response.json()["code"]) == (400, "clip_not_ready")
    assert response.json()["clip_ids"] == ["bbbbbbbbbbb"]


def test_an_edited_line_is_what_the_counter_and_the_llm_get(client, project, ready, llm, counted):
    client.patch(f"/api/spoil/clips/{EP1}/transcript/lines/0", json={"text": "บรรทัดที่แก้"})
    llm.scripts = [passing_script()]

    start(client)
    wait_for_end(client)

    assert "[1-0 00:00:00] บรรทัดที่แก้\n" in counted[-1]
    assert "[1-0 00:00:00] บรรทัดที่แก้\n" in llm.requests[0].prompt
    assert "Line 0." not in llm.requests[0].prompt


def test_a_draft_already_there_without_replace_is_draft_exists(client, project, ready, llm):
    write_draft(project)
    llm.scripts = [passing_script()]

    refused = start(client)
    accepted = start(client, replace=True)

    assert (refused.status_code, refused.json()["code"]) == (409, "draft_exists")
    assert accepted.status_code == 202
    assert wait_for_end(client)["state"] == "done"


def test_a_missing_qwen_marker_is_not_ready(client, project, ready):
    project.marker(QWEN).unlink()

    response = start(client)

    assert response.status_code == 503
    assert response.json()["code"] == "not_ready"
    assert "model_qwen" in response.json()["rows"]


def test_a_draft_while_a_describe_job_runs_is_gpu_busy(client, ready):
    gpu.slot.take("describe", [EP2])

    response = start(client)

    assert response.status_code == 409
    assert response.json() == {"code": "gpu_busy", "message": "รอให้งานบรรยายฉากเสร็จก่อน", "running": "describe"}


def test_an_unknown_kind_is_invalid_request(client, ready):
    response = client.post(JOBS, json={"kind": "x"})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


# --- A Draft job from start to end ---


def test_a_two_episode_script_cites_each_episode_and_picks_shots_in_the_window(client, project, ready, llm):
    llm.scripts = [script(*[(THIRTY, ["1-0"])] * 15, *[(THIRTY, ["2-1"])] * 15)]

    response = start(client, clip_ids=[EP1, EP2])

    assert response.status_code == 202
    assert response.json()["kind"] == "draft"
    assert response.json()["state"] == "writing"
    assert wait_for_end(client)["state"] == "done"
    found = a_draft(client)
    assert found["clip_ids"] == [EP1, EP2]
    assert found["sentences"][0]["refs"] == [{"clip_id": EP1, "line": 0}]
    assert found["sentences"][-1]["refs"] == [{"clip_id": EP2, "line": 1}]
    last = found["sentences"][-1]
    assert last["window"] == {"clip_id": EP2, "start": 0.0, "end": 44.0}
    for slot in last["shots"]:
        assert slot["clip_id"] == EP2
        shot_start = 5.0 * slot["n"]
        assert last["window"]["start"] <= shot_start < last["window"]["end"]


def test_a_sentence_citing_two_episodes_takes_its_window_from_the_first(client, project, ready, llm):
    llm.scripts = [script(*[(THIRTY, ["1-0", "2-1"])] * PASSING)]

    start(client, clip_ids=[EP1, EP2])
    wait_for_end(client)

    first = a_draft(client)["sentences"][0]
    assert first["refs"] == [{"clip_id": EP1, "line": 0}, {"clip_id": EP2, "line": 1}]
    assert first["window"] == {"clip_id": EP1, "start": 0.0, "end": 34.0}
    assert {slot["clip_id"] for slot in first["shots"]} == {EP1}
    pick = next(r for r in llm.requests if is_pick(r))
    assert "Line 1." not in pick.prompt  # EP 2's line isn't sent


def test_the_draft_has_the_order_the_remembered_volume_and_becomes_the_last_voice(client, project, ready, llm):
    llm.scripts = [passing_script()]

    start(client, layout="A", style="fast", target_s=60)
    wait_for_end(client)

    found = a_draft(client)
    assert (found["style"], found["layout"], found["target_s"], found["voice_id"]) == ("fast", "A", 60, VOICE)
    assert found["original_volume"] == 20
    assert client.get("/api/spoil-maker/settings").json()["last_voice_id"] == VOICE


def test_the_llm_gets_the_target_letters_and_sentences_and_the_generation_settings(client, project, ready, llm):
    llm.scripts = [passing_script()]

    start(client, layout="C", style="chrono", target_s=60)
    wait_for_end(client)

    # 60 s × 15 letters a second, and 60 / 4 sentences (spec › Draft job step 2).
    request = llm.requests[0]
    assert request.image is None
    assert (request.max_tokens, request.temperature) == (2 * 900 + 1000, 0.3)
    assert "900" in request.prompt
    assert "15" in request.prompt
    assert "[1-0 00:00:00] Line 0." in request.prompt
    # The rules come again after a long Transcript, where the model reads last.
    assert request.prompt.rindex("900") > request.prompt.index("[1-19 ")
    pick = next(r for r in llm.requests if is_pick(r))
    assert (pick.temperature, pick.image) == (0.0, None)


def test_writing_then_matching_reports_done_and_total_sentences(client, project, ready, llm):
    llm.scripts = [script(*[(THIRTY, ["1-0"])] * 29, (THIRTY, []))]
    llm.pause_at(2)  # the second pick

    start(client)
    llm.wait_until(2)
    job = wait_for(client, lambda job: job["state"] == "matching")

    assert (job["done"], job["total"]) == (1, 29)
    llm.release(2)
    assert wait_for_end(client)["state"] == "done"


def test_three_broken_replies_fail_as_draft_failed_and_keep_the_old_draft(client, project, ready, llm):
    old = write_draft(project)
    llm.scripts = ["not json", '{"sentences": "x"}', "```json\n{oops\n```"]

    start(client, replace=True)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"] == {"code": "draft_failed", "message": "AI ร่างบทไม่สำเร็จ 3 ครั้ง"}
    assert json.loads(project.draft_file.read_text(encoding="utf-8")) == old
    assert gpu.slot.holds_draft() is False


def test_a_script_missing_only_its_last_brace_is_read(client, project, ready, llm):
    llm.scripts = [passing_script()[:-1]]  # a real reply ended at the sentences' "]" (D61)

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert len([r for r in llm.requests if not is_pick(r)]) == 1


def test_two_broken_replies_then_a_good_one_is_done_after_three_asks(client, project, ready, llm):
    llm.scripts = ["not json", "nope", "```json\n" + passing_script() + "\n```"]

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert len([r for r in llm.requests if not is_pick(r)]) == 3


def test_asking_again_says_what_was_wrong_with_the_last_reply(client, project, ready, llm):
    # Real replies ran long or looped until max_tokens cut the JSON (D61).
    llm.scripts = [script(*[(THIRTY, ["1-0"])] * 60), "{cut", passing_script()]

    start(client)
    wait_for_end(client)

    first, second, third = [r.prompt for r in llm.requests if not is_pick(r)]
    assert "each sentence at most 72 Thai letters" in first  # 900 letters in 15 sentences, with room
    assert "Your last script" not in first
    assert "1800 letters in 60 sentences" in second
    assert "not complete JSON" in third


def test_a_reply_slower_than_the_timeout_counts_as_a_failed_try(client, project, ready, llm, monkeypatch):
    monkeypatch.setattr(draft, "WRITE_TIMEOUT_SECONDS", 0.2)
    llm.scripts = [FakeLlm.HANG, passing_script()]

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert llm.processes[0].terminated is True  # the stuck child is ended, a new one starts
    assert len(llm.processes) == 2


def test_a_script_far_from_the_target_is_asked_again_and_the_last_readable_is_kept(client, project, ready, llm):
    short = script(("สั้น", ["1-0"]))
    llm.scripts = [short, short, script(("สั้นที่สุด", ["1-0"]))]

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert [s["text"] for s in a_draft(client)["sentences"]] == ["สั้นที่สุด"]


def test_han_and_lines_that_do_not_exist_are_cleaned_out(client, project, ready, llm):
    llm.scripts = [script(("ไป現場กัน", ["9-999"]), *[(THIRTY, ["1-0"])] * (PASSING - 1))]

    start(client)
    wait_for_end(client)

    first = a_draft(client)["sentences"][0]
    assert first["text"] == "ไปกัน"
    assert first["refs"] == []
    assert first["shots"] == [None, None]
    assert first["status"] == "no_shot"


def test_a_sentence_empty_after_cleaning_is_dropped(client, project, ready, llm):
    llm.scripts = [script(("現場", ["1-0"]), *[(THIRTY, ["1-0"])] * PASSING)]

    start(client)
    wait_for_end(client)

    assert len(a_draft(client)["sentences"]) == PASSING


def test_shots_picked_outside_the_window_fall_back_to_the_two_nearest_the_first_line(client, project, ready, llm):
    llm.scripts = [passing_script(refs=("1-10",))]  # line 10 starts at 100 s: Shot 20
    llm.picks = lambda request: '{"shots": [0, 39]}'

    start(client)
    wait_for_end(client)

    assert a_draft(client)["sentences"][0]["shots"] == [{"clip_id": EP1, "n": 19}, {"clip_id": EP1, "n": 20}]


def test_a_sentence_keeps_only_its_first_three_cited_lines(client, project, ready, llm):
    # A real reply listed a run of 60 ids for one sentence (spec › Draft job step 2: 1 to 3).
    llm.scripts = [passing_script(refs=("1-5", "1-6", "1-7", "1-8", "1-9"))]

    start(client)
    wait_for_end(client)

    assert [ref["line"] for ref in a_draft(client)["sentences"][0]["refs"]] == [5, 6, 7]


def test_a_wide_window_asks_about_only_the_shots_nearest_the_first_line(client, project, ready, llm, monkeypatch):
    monkeypatch.setattr(draft, "PICK_MAX_SHOTS", 6)
    llm.scripts = [passing_script(refs=("1-19", "1-10"))]  # window 70–224 s: Shots 14–39
    llm.picks = lambda request: '{"shots": [15, 36]}'  # 15 is in the window but wasn't asked about

    start(client)
    wait_for_end(client)

    asked = [r.prompt for r in llm.requests if is_pick(r)][0]
    listed = [int(line.split(" ")[0]) for line in asked.splitlines() if re.match(r"\d+ \[", line)]
    assert listed == [34, 35, 36, 37, 38, 39]  # the six nearest line 19 (190 s), in clip order
    assert a_draft(client)["sentences"][0]["shots"] == [{"clip_id": EP1, "n": 37}, {"clip_id": EP1, "n": 38}]


def test_a_window_with_one_shot_uses_it_twice_without_asking(client, project, ready, llm):
    write_shots(project, EP1, count=1)  # 0–5 s; line 0's window holds only it
    llm.scripts = [passing_script()]

    start(client)
    wait_for_end(client)

    assert a_draft(client)["sentences"][0]["shots"] == [{"clip_id": EP1, "n": 0}, {"clip_id": EP1, "n": 0}]
    assert not any(is_pick(r) for r in llm.requests)


def test_a_new_draft_removes_the_old_drafts_voice(client, project, ready, llm):
    write_draft(project)
    project.draft_audio_dir.mkdir(parents=True)
    (project.draft_audio_dir / "s_00000001.wav").write_bytes(b"wav")
    llm.scripts = [passing_script()]

    start(client, replace=True)
    wait_for_end(client)

    assert not (project.draft_audio_dir / "s_00000001.wav").exists()


def test_cancelling_while_writing_ends_cancelled_and_keeps_the_old_draft(client, project, ready, llm):
    old = write_draft(project)
    llm.scripts = [passing_script()]
    llm.pause_at(0)

    start(client, replace=True)
    llm.wait_until(0)
    cancelled = client.delete(CURRENT)

    assert cancelled.status_code == 202
    assert cancelled.json()["cancel_requested"] is True
    assert wait_for_end(client)["state"] == "cancelled"
    assert json.loads(project.draft_file.read_text(encoding="utf-8")) == old
    assert llm.processes[0].terminated is True


def test_a_picking_timeout_fails_as_model_failed(client, project, ready, llm, monkeypatch):
    monkeypatch.setattr(draft, "PICK_TIMEOUT_SECONDS", 0.2)
    llm.scripts = [passing_script()]
    llm.picks = lambda request: FakeLlm.HANG

    start(client)
    job = wait_for_end(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "model_failed")


def test_an_llm_process_that_dies_fails_as_crashed_and_frees_the_gpu(client, project, ready, llm):
    llm.crash_at = 0

    start(client)
    job = wait_for_end(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "crashed")
    assert client.post("/api/spoil-maker/describes", json={"clip_id": EP2}).status_code != 409


def test_cancel_without_a_running_job_is_404(client):
    response = client.delete(CURRENT)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_current_is_null_before_any_job(client):
    assert client.get(CURRENT).json() is None


# --- Picking new Shots for one sentence ---


def test_pick_writes_only_that_sentences_shots(client, project, ready, llm):
    write_draft(project)
    llm.picks = lambda request: '{"shots": [4, 5]}'

    response = client.post(JOBS, json={"kind": "pick", "sentence_id": "s_00000001"})

    assert response.status_code == 202
    assert (response.json()["kind"], response.json()["state"]) == ("pick", "matching")
    assert wait_for_end(client)["state"] == "done"
    sentences = a_draft(client)["sentences"]
    assert sentences[0]["shots"] == [{"clip_id": EP1, "n": 4}, {"clip_id": EP1, "n": 5}]
    assert sentences[1]["shots"] == [{"clip_id": EP1, "n": 2}, {"clip_id": EP1, "n": 3}]
    assert "Sentence: ประโยคแรก" in llm.requests[0].prompt


def test_editing_during_pick_is_draft_locked_and_the_draft_reads_locked(client, project, ready, llm):
    write_draft(project)
    llm.pause_at(0)

    client.post(JOBS, json={"kind": "pick", "sentence_id": "s_00000001"})
    llm.wait_until(0)
    refused = client.patch(f"{DRAFT}/sentences/s_00000002", json={"text": "ใหม่"})

    assert (refused.status_code, refused.json()["code"]) == (409, "draft_locked")
    assert a_draft(client)["locked"] is True
    llm.release(0)
    wait_for_end(client)
    assert a_draft(client)["locked"] is False


def test_pick_of_an_unknown_sentence_is_404(client, project, ready):
    write_draft(project)

    response = client.post(JOBS, json={"kind": "pick", "sentence_id": "s_ffffffff"})

    assert (response.status_code, response.json()["code"]) == (404, "not_found")


def test_pick_without_a_draft_is_no_draft(client, ready):
    response = client.post(JOBS, json={"kind": "pick", "sentence_id": "s_00000001"})

    assert (response.status_code, response.json()["code"]) == (404, "no_draft")


# --- Reading the draft ---


def test_no_draft_reads_null(client):
    assert client.get(DRAFT).json() is None


def test_a_new_app_on_the_same_root_reads_the_same_draft(client, project, ready, llm):
    llm.scripts = [passing_script()]
    start(client)
    wait_for_end(client)
    before = a_draft(client)

    with TestClient(app, base_url="http://127.0.0.1") as restarted:
        after = restarted.get(DRAFT).json()

    assert after == before


@pytest.mark.parametrize("content", ["{not json", '{"version": 2}'])
def test_a_draft_file_that_cannot_be_read_is_no_draft(client, project, ready, content):
    project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
    project.draft_file.write_text(content, encoding="utf-8")

    assert client.get(DRAFT).json() is None


def test_a_draft_naming_a_clip_that_is_gone_is_no_draft(client, project, ready):
    write_draft(project, clip_ids=(EP1, "bbbbbbbbbbb"))

    assert client.get(DRAFT).json() is None


def test_each_sentence_shows_the_lines_it_cites_and_its_window(client, project, ready):
    write_draft(project)

    first = a_draft(client)["sentences"][0]

    assert first["ref_lines"] == [{"clip_id": EP1, "line": 1, "start": 10.0, "end": 14.0, "text": "Line 1."}]
    assert first["window"] == {"clip_id": EP1, "start": 0.0, "end": 44.0}
    assert first["status"] == "no_audio"


def test_the_estimate_adds_ready_seconds_and_letters_over_the_voices_speed(client, project, ready):
    write_draft(
        project,
        sentences=[
            sentence("s_00000001", "พร้อม", refs=[{"clip_id": EP1, "line": 1}], audio=voiced("พร้อม", 2.0)),
            sentence("s_00000002", THIRTY, refs=[{"clip_id": EP1, "line": 2}]),
        ],
    )

    found = a_draft(client)

    assert [s["estimated_s"] for s in found["sentences"]] == [2.0, 2.0]
    assert found["estimated_total_s"] == 4.0


# --- Changing the draft ---


def test_new_text_makes_a_voiced_sentence_stale_and_the_old_text_ready_again(client, project, ready):
    write_draft(project, sentences=[sentence("s_00000001", "เดิม", refs=[{"clip_id": EP1, "line": 1}], audio=voiced("เดิม"))])

    changed = client.patch(f"{DRAFT}/sentences/s_00000001", json={"text": "ใหม่"})
    back = client.patch(f"{DRAFT}/sentences/s_00000001", json={"text": "เดิม"})

    assert changed.status_code == 200
    assert changed.json()["sentences"][0]["status"] == "stale_audio"
    assert back.json()["sentences"][0]["status"] == "ready"


def test_text_with_numbers_compares_as_spoken(client, project, ready):
    spoken = "ปี หนึ่งพันเก้าร้อยหกสิบแปด"
    write_draft(project, sentences=[sentence("s_00000001", "ปี 1968", refs=[{"clip_id": EP1, "line": 1}], audio=voiced(spoken))])

    assert a_draft(client)["sentences"][0]["status"] == "ready"


def test_another_voice_makes_every_voiced_sentence_stale(client, project, ready):
    write_voice(project, OTHER_VOICE)
    write_draft(
        project,
        sentences=[
            sentence("s_00000001", "หนึ่ง", refs=[{"clip_id": EP1, "line": 1}], audio=voiced("หนึ่ง")),
            sentence("s_00000002", "สอง", refs=[{"clip_id": EP1, "line": 2}]),
        ],
    )

    response = client.patch(DRAFT, json={"voice_id": OTHER_VOICE})

    assert response.status_code == 200
    assert [s["status"] for s in response.json()["sentences"]] == ["stale_audio", "no_audio"]


def test_changing_to_a_voice_that_does_not_exist_is_voice_not_found(client, project, ready):
    write_draft(project)

    response = client.patch(DRAFT, json={"voice_id": "v_ffffffff"})

    assert (response.status_code, response.json()["code"]) == (400, "voice_not_found")


def test_top_text_and_layout_change(client, project, ready):
    write_draft(project)

    response = client.patch(DRAFT, json={"top_text": "  คดี\nหลอน ", "layout": "C"})

    assert (response.json()["top_text"], response.json()["layout"]) == ("คดี หลอน", "C")


@pytest.mark.parametrize(
    "body",
    [{"layout": "D"}, {"top_text": 3}, {"top_text": "ก" * 41}, {"original_volume": 33}, {"original_volume": 105}],
)
def test_bad_draft_fields_are_invalid_request(client, project, ready, body):
    write_draft(project)

    response = client.patch(DRAFT, json=body)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_forty_letters_with_marks_above_fit_the_top_text(client, project, ready):
    write_draft(project)

    response = client.patch(DRAFT, json={"top_text": "กิ" * 40})

    assert response.status_code == 200


def test_the_volume_is_remembered_and_a_new_draft_takes_it(client, project, ready, llm):
    write_draft(project)
    llm.scripts = [passing_script()]

    client.patch(DRAFT, json={"original_volume": 35})
    remembered = client.get("/api/spoil-maker/settings").json()["original_volume"]
    start(client, replace=True)
    wait_for_end(client)

    assert remembered == 35
    assert a_draft(client)["original_volume"] == 35


def test_settings_start_at_their_defaults(client):
    assert client.get("/api/spoil-maker/settings").json() == {
        "watermarks": [],
        "original_volume": 20,
        "last_voice_id": None,
    }


def test_a_sentence_inserted_after_the_first_is_second_with_no_shot(client, project, ready):
    write_draft(project)

    response = client.post(f"{DRAFT}/sentences", json={"after_id": "s_00000001", "text": "แทรก"})

    assert response.status_code == 201
    sentences = response.json()["sentences"]
    assert [s["text"] for s in sentences] == ["ประโยคแรก", "แทรก", "ประโยคสอง"]
    assert (sentences[1]["status"], sentences[1]["refs"], sentences[1]["window"]) == ("no_shot", [], None)
    picked = client.post(JOBS, json={"kind": "pick", "sentence_id": sentences[1]["id"]})
    assert (picked.status_code, picked.json()["code"]) == (400, "no_refs")


def test_a_sentence_inserted_after_null_is_first(client, project, ready):
    write_draft(project)

    response = client.post(f"{DRAFT}/sentences", json={"after_id": None, "text": "แรกสุด"})

    assert response.json()["sentences"][0]["text"] == "แรกสุด"


@pytest.mark.parametrize("body", [{"after_id": None, "text": "  "}, {"after_id": "s_ffffffff", "text": "x"}])
def test_an_empty_insert_or_an_unknown_after_id_is_invalid_request(client, project, ready, body):
    write_draft(project)

    response = client.post(f"{DRAFT}/sentences", json=body)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_shots_can_be_set_from_any_shot_of_a_draft_clip(client, project, ready):
    write_draft(project)

    response = client.patch(
        f"{DRAFT}/sentences/s_00000001", json={"shots": [{"clip_id": EP1, "n": 39}, {"clip_id": EP1, "n": 0}]}
    )

    assert response.status_code == 200
    assert response.json()["sentences"][0]["shots"] == [{"clip_id": EP1, "n": 39}, {"clip_id": EP1, "n": 0}]


@pytest.mark.parametrize(
    "shots",
    [
        [{"clip_id": EP1, "n": 40}, {"clip_id": EP1, "n": 0}],
        [{"clip_id": EP2, "n": 0}, {"clip_id": EP1, "n": 0}],
        [{"clip_id": EP1, "n": 0}],
        "x",
    ],
)
def test_a_shot_that_is_not_one_of_the_drafts_is_invalid_shot(client, project, ready, shots):
    write_draft(project)

    response = client.patch(f"{DRAFT}/sentences/s_00000001", json={"shots": shots})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_shot")


def test_empty_text_is_invalid_request(client, project, ready):
    write_draft(project)

    response = client.patch(f"{DRAFT}/sentences/s_00000001", json={"text": " \n "})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_deleting_a_sentence_deletes_its_voice(client, project, ready):
    write_draft(project)
    project.draft_audio_dir.mkdir(parents=True)
    (project.draft_audio_dir / "s_00000001.wav").write_bytes(b"wav")

    response = client.delete(f"{DRAFT}/sentences/s_00000001")

    assert response.status_code == 200
    assert [s["id"] for s in response.json()["sentences"]] == ["s_00000002"]
    assert not (project.draft_audio_dir / "s_00000001.wav").exists()


@pytest.mark.parametrize("sid", ["s_ffffffff", "x", "s_0000000G"])
def test_an_unknown_or_malformed_sentence_is_404(client, project, ready, sid):
    write_draft(project)

    assert client.patch(f"{DRAFT}/sentences/{sid}", json={"text": "x"}).status_code == 404
    assert client.delete(f"{DRAFT}/sentences/{sid}").status_code == 404


def test_changes_without_a_draft_are_no_draft(client, ready):
    response = client.patch(DRAFT, json={"layout": "A"})

    assert (response.status_code, response.json()["code"]) == (404, "no_draft")


def test_a_patch_that_is_not_json_is_415(client, project, ready):
    write_draft(project)

    response = client.patch(DRAFT, content=b'{"layout": "A"}', headers={"Content-Type": "text/plain"})

    assert response.status_code == 415


# --- Saved voices the draft uses ---


def test_deleting_the_drafts_voice_is_voice_in_use(client, project, ready):
    write_draft(project)

    response = client.delete(f"/api/spoil-maker/voices/{VOICE}")
    listed = client.get("/api/spoil-maker/voices").json()

    assert response.status_code == 409
    assert response.json() == {"code": "voice_in_use", "message": "เสียงนี้ใช้อยู่ใน Spoil draft"}
    assert (project.voices_dir / f"{VOICE}.json").is_file()
    assert listed[0]["in_use"] is True


# --- Clips in the Spoil draft (D49) ---


@pytest.fixture(scope="session")
def three_colours(tmp_path_factory) -> Path:
    return make_test_clip(tmp_path_factory.mktemp("clips") / "three.mp4")


def test_describing_a_clip_in_the_draft_needs_confirm_then_done_removes_the_draft(
    client, project, ready, llm, three_colours
):
    shutil.copyfile(three_colours, project.media_temp_dir / f"{EP1}.mp4")
    write_draft(project)
    llm.respond = lambda request: "A frame."

    refused = client.post("/api/spoil-maker/describes", json={"clip_id": EP1})
    accepted = client.post("/api/spoil-maker/describes", json={"clip_id": EP1, "confirm_draft_loss": True})

    assert refused.status_code == 409
    assert refused.json() == {"code": "in_draft", "message": "คลิปนี้อยู่ใน Spoil draft: ทำต่อจะลบ Spoil draft"}
    assert accepted.status_code == 202
    assert wait_for_end(client, "/api/spoil-maker/describes/current")["state"] == "done"
    assert client.get(DRAFT).json() is None


def test_a_cancelled_describe_keeps_the_draft(client, project, ready, llm, three_colours):
    shutil.copyfile(three_colours, project.media_temp_dir / f"{EP1}.mp4")
    write_draft(project)
    llm.respond = lambda request: "A frame."
    llm.pause_at(0)

    client.post("/api/spoil-maker/describes", json={"clip_id": EP1, "confirm_draft_loss": True})
    llm.wait_until(0)
    client.delete("/api/spoil-maker/describes/current")

    assert wait_for_end(client, "/api/spoil-maker/describes/current")["state"] == "cancelled"
    assert client.get(DRAFT).json() is not None


def test_transcribing_a_clip_in_the_draft_needs_confirm_then_done_removes_the_draft(client, project, ready):
    write_draft(project)

    refused = client.post("/api/spoil/transcriptions", json={"clip_id": EP1})
    accepted = client.post("/api/spoil/transcriptions", json={"clip_id": EP1, "confirm_draft_loss": True})

    assert (refused.status_code, refused.json()["code"]) == (409, "in_draft")
    assert accepted.status_code == 202
    assert wait_for_end(client, "/api/spoil/transcriptions/current")["state"] == "done"
    assert client.get(DRAFT).json() is None


def test_deleting_a_clip_in_the_draft_removes_its_shots_and_the_draft(client, project, ready):
    write_draft(project)
    project.draft_audio_dir.mkdir(parents=True)
    (project.draft_audio_dir / "s_00000001.wav").write_bytes(b"wav")

    response = client.delete(f"/api/spoil/clips/{EP1}")

    assert response.status_code == 204
    assert not project.clip_shots_dir(EP1).exists()
    assert client.get(DRAFT).json() is None
    assert not project.draft_file.exists()
    assert not project.draft_audio_dir.exists()


def test_a_clip_delete_that_fails_in_use_keeps_the_draft(client, project, ready, monkeypatch):
    write_draft(project)
    mp4 = project.media_temp_dir / f"{EP1}.mp4"
    real_unlink = Path.unlink

    def unlink(path, missing_ok=False):
        if path == mp4:
            raise PermissionError(32, "The process cannot access the file")
        return real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)

    response = client.delete(f"/api/spoil/clips/{EP1}")

    assert (response.status_code, response.json()["code"]) == (409, "in_use")
    assert client.get(DRAFT).json() is not None


def test_deleting_a_clip_a_draft_job_reads_is_clip_busy(client, project, ready, llm):
    llm.scripts = [passing_script()]
    llm.pause_at(0)

    start(client)
    llm.wait_until(0)
    response = client.delete(f"/api/spoil/clips/{EP1}")

    assert (response.status_code, response.json()["code"]) == (409, "clip_busy")
    llm.release(0)
    wait_for_end(client)


def test_the_clip_list_shows_which_clips_are_in_the_draft(client, project, ready):
    write_draft(project)

    listed = {clip["id"]: clip["in_draft"] for clip in client.get("/api/spoil/clips").json()["clips"]}

    assert listed == {EP1: True, EP2: False}


def test_editing_a_line_of_a_clip_a_draft_job_reads_is_clip_busy(client, project, ready, llm):
    llm.scripts = [passing_script()]
    llm.pause_at(0)

    start(client)
    llm.wait_until(0)
    response = client.patch(f"/api/spoil/clips/{EP1}/transcript/lines/0", json={"text": "ใหม่"})

    assert response.status_code == 409
    assert response.json() == {"code": "clip_busy", "message": "คลิปนี้กำลังถูกใช้ในงานอื่น"}
    llm.release(0)
    wait_for_end(client)


def test_editing_a_line_of_a_clip_in_the_draft_with_no_job_is_ok(client, project, ready):
    write_draft(project)

    response = client.patch(f"/api/spoil/clips/{EP1}/transcript/lines/0", json={"text": "ใหม่"})

    assert response.status_code == 200


def test_start_up_removes_a_half_written_draft(fake_root, project, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    project.spoil_maker_dir.mkdir(parents=True)
    (project.spoil_maker_dir / "draft.json.tmp").write_text("{", encoding="utf-8")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert not (project.spoil_maker_dir / "draft.json.tmp").exists()
