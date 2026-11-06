"""The Spoil draft, its edits, the token count and the Draft job, under /api/spoil-maker,
and what a draft changes under /api/spoil, with a fake LLM worker and a fake token
counter (spoil-maker seam 1)."""

import json
import re
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil, spoil_maker, stories
from backend.app import app
from backend.models import QWEN_MAC, QWEN_WINDOWS
from backend.paths import ProjectPaths
from backend.spoil import transcribe
from backend.spoil_maker import describe, draft, voices

from .fakes import (
    os_timeouts,
    slow_first,
    poll_until,
    FakeLlm,
    FakeTts,
    FakeWorker,
    cuda_device,
    card,
    make_test_clip,
    on_windows,
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
# The Shots end at 200 s, shorter than any EP length: the clip is one EP.
WHOLE = {"n": 1, "start_s": 0.0, "end_s": 200.0}


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def llm(monkeypatch) -> FakeLlm:
    fake = FakeLlm()
    fake.scripts = []  # replies to script prompts, in order; the last one repeats
    fake.picks = lambda request: '{"shots": [0, 1]}'
    fake.polishes = unchanged  # replies to polish prompts
    fake.respond = lambda request: _respond(fake, request)
    monkeypatch.setattr(spoil_maker, "start_worker", fake)
    return fake


def is_pick(request) -> bool:
    """Picking Shots and writing the script differ in their generation settings (spec › ค่าการสร้างข้อความ)."""
    return request.max_tokens == draft.PICK_MAX_TOKENS


def is_polish(request) -> bool:
    return request.prompt.startswith("Polish")


def is_script(request) -> bool:
    return not is_pick(request) and not is_polish(request)


# A sentence of a polish prompt: `[i] text`, or `[i] (fixed) text`.
POLISH_ITEM = re.compile(r"^\[(\d+)\] (\(fixed\) )?(.*)$", re.MULTILINE)


def asked_to_polish(request) -> dict[int, str]:
    """The sentences a polish prompt asks to rewrite, by `i`."""
    return {int(i): text for i, fixed, text in POLISH_ITEM.findall(request.prompt) if not fixed}


def fixed_in(request) -> dict[int, str]:
    return {int(i): text for i, fixed, text in POLISH_ITEM.findall(request.prompt) if fixed}


def polished(texts: dict[int, str]) -> str:
    return json.dumps({"sentences": [{"i": i, "text": text} for i, text in texts.items()]}, ensure_ascii=False)


def unchanged(request) -> str:
    """Every sentence asked for, as it was."""
    return polished(asked_to_polish(request))


def _respond(fake: FakeLlm, request) -> str:
    if is_pick(request):
        return fake.picks(request)
    if is_polish(request):
        return fake.polishes(request)
    scripts = [r for r in fake.requests if is_script(r)]
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
def counted_in(monkeypatch) -> list[Path]:
    """The fake token counter, keeping the snapshot each count read its tokenizer from."""
    snapshots: list[Path] = []

    def count(snapshot_dir: Path, text: str) -> int:
        snapshots.append(snapshot_dir)
        return len(text)

    monkeypatch.setattr(spoil_maker, "count_tokens", count)
    return snapshots


@pytest.fixture
def whisper(monkeypatch) -> FakeWorker:
    fake = FakeWorker()
    monkeypatch.setattr(spoil, "start_worker", fake)
    return fake


@pytest.fixture
def tts(monkeypatch) -> FakeTts:
    fake = FakeTts()
    monkeypatch.setattr(spoil_maker, "start_tts_worker", fake)
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
    monkeypatch.setattr(voices, "voice_jobs", voices.VoiceJobs())
    return TestClient(app, base_url="http://127.0.0.1")


@contextmanager
def transcribing(client, whisper: FakeWorker, clip_id: str) -> Iterator[None]:
    """A Transcribe job of the clip started through the API, paused before its first segment:
    it holds the GPU slot and reads the clip until the block ends, then finishes."""
    whisper.pause_at(0)
    response = client.post("/api/spoil/transcriptions", json={"clip_id": clip_id})
    assert response.status_code == 202, response.json()
    whisper.wait_until(0)
    try:
        yield
    finally:
        whisper.release(0)
        poll_until(client, "/api/spoil/transcriptions/current", lambda job: job["state"] not in transcribe.UNFINISHED)


@contextmanager
def voicing(client, tts: FakeTts, sentence_id: str) -> Iterator[None]:
    """A Voice job of one draft sentence started through the API, paused before it speaks:
    it holds the GPU slot and locks the draft until the block ends, then finishes."""
    tts.pause_at(0)
    response = client.post("/api/spoil-maker/voice-jobs", json={"kind": "sentences", "sentence_ids": [sentence_id]})
    assert response.status_code == 202, response.json()
    tts.wait_until(0)
    try:
        yield
    finally:
        tts.release(0)
        poll_until(client, "/api/spoil-maker/voice-jobs/current", lambda job: job["state"] not in voices.UNFINISHED)


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


def passing_script(refs=("0",)) -> str:
    return script(*[(THIRTY, list(refs))] * PASSING)


def order(**overrides) -> dict:
    return {
        "kind": "draft",
        "clip_id": EP1,
        "ep": WHOLE,
        "style": "drama",
        "layout": "B",
        "target_s": 60,
        "voice_id": VOICE,
        "replace": False,
    } | overrides


def start(client, **overrides):
    return client.post(JOBS, json=order(**overrides))


def wait_for(client, condition, path: str = CURRENT) -> dict:
    return poll_until(client, path, condition)


def wait_for_end(client, path: str = CURRENT) -> dict:
    return wait_for(client, lambda job: job is not None and job["state"] in FINISHED, path)


def write_draft(project: ProjectPaths, clip_id=EP1, sentences=None, voice_id: str = VOICE, ep=WHOLE, **fields) -> dict:
    """A `draft.json` as a finished Draft job leaves it; returns its content."""
    content = {
        "version": 2,
        "clip_id": clip_id,
        "ep": ep,
        "style": "drama",
        "layout": "B",
        "target_s": 60,
        "voice_id": voice_id,
        "original_volume": 20,
        "top_text": "",
        "sentences": sentences
        if sentences is not None
        else [
            sentence("s_00000001", "ประโยคแรก", refs=[{"clip_id": clip_id, "line": 1}]),
            sentence("s_00000002", "ประโยคสอง", refs=[{"clip_id": clip_id, "line": 2}]),
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

    response = start(client, clip_id="bbbbbbbbbbb")

    assert response.status_code == 400
    assert response.json()["code"] == "clip_not_ready"
    assert response.json()["clip_ids"] == ["bbbbbbbbbbb"]


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


def test_an_ep_over_32000_tokens_is_too_long(client, ready, monkeypatch):
    monkeypatch.setattr(spoil_maker, "count_tokens", lambda snapshot, text: 32_001)

    response = start(client)
    listed = client.get(f"/api/spoil-maker/clips/{EP1}/episodes")

    assert response.status_code == 400
    assert response.json() == {
        "code": "transcript_too_long",
        "message": "Transcript ของ EP นี้ 32,001 token เกิน 32,000",
        "tokens": 32_001,
    }
    assert [ep["tokens"] for ep in listed.json()["episodes"]] == [32_001]
    assert listed.json()["limit"] == 32_000


def test_tokens_count_the_eps_lines_as_the_llm_gets_them(client, project, ready, counted):
    client.get(f"/api/spoil-maker/clips/{EP1}/episodes")

    assert counted[0].startswith("[0 00:00:00] Line 0.\n[1 00:00:10] Line 1.\n")


def test_with_qwens_snapshot_gone_tokens_are_null_and_a_draft_is_not_ready(client, project, ready, monkeypatch):
    def gone(snapshot_dir, text):
        raise FileNotFoundError(snapshot_dir)

    monkeypatch.setattr(spoil_maker, "count_tokens", gone)

    listed = client.get(f"/api/spoil-maker/clips/{EP1}/episodes")
    response = start(client)

    assert listed.status_code == 200
    assert [ep["tokens"] for ep in listed.json()["episodes"]] == [None]
    assert listed.json()["tokens_not_ready"] == response.json()["message"]
    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", ["model_qwen"])


def test_on_windows_a_card_under_qwen_s_target_refuses_a_draft_naming_the_gpu_row(client, ready, llm, monkeypatch):
    on_windows(monkeypatch, card("NVIDIA GeForce RTX 2070", 8, (7, 5)))

    response = start(client)

    # The token count's gate refuses first: the card's model was never downloaded (D9).
    assert (response.status_code, response.json()["code"]) == (503, "not_ready")
    assert response.json()["rows"] == ["gpu", "model_qwen"]
    assert llm.processes == []


def test_on_windows_without_qwen_s_own_files_the_token_count_is_not_ready(client, project, ready, monkeypatch):
    on_windows(monkeypatch)
    project.marker(QWEN_WINDOWS).unlink()

    listed = client.get(f"/api/spoil-maker/clips/{EP1}/episodes").json()
    response = start(client)

    assert [ep["tokens"] for ep in listed["episodes"]] == [None]
    assert listed["tokens_not_ready"] == "ยังติดตั้งไม่ครบ: Qwen3.5 9B model"
    assert (response.status_code, response.json()["rows"]) == (503, ["model_qwen"])


def test_on_windows_tokens_are_counted_with_qwen_s_own_tokenizer(client, project, ready, counted_in, monkeypatch):
    on_windows(monkeypatch)

    listed = client.get(f"/api/spoil-maker/clips/{EP1}/episodes").json()

    assert listed["episodes"][0]["tokens"] is not None
    assert set(counted_in) == {project.snapshot_dir(QWEN_WINDOWS, QWEN_WINDOWS.revision)}


def slow_step(llm: FakeLlm, step: str) -> None:
    """Makes the first answer of one step (`write`, `polish` or `pick`) slow."""
    llm.scripts = [slow_first(passing_script()) if step == "write" else passing_script()]
    if step == "polish":
        llm.polishes = slow_first(unchanged)
    if step == "pick":
        llm.picks = slow_first('{"shots": [0, 1]}')


@pytest.mark.parametrize("step", ["write", "polish", "pick"])
def test_on_windows_a_step_slower_than_the_mac_s_timeout_finishes_in_one_try(step, client, ready, llm, monkeypatch):
    on_windows(monkeypatch)
    os_timeouts(monkeypatch, darwin=0.2, win32=1)
    slow_step(llm, step)

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert len(llm.processes) == 1  # no try timed out


@pytest.mark.parametrize("step", ["write", "polish"])
def test_on_the_mac_the_same_slow_write_or_polish_is_a_timed_out_try(step, client, ready, llm, monkeypatch):
    os_timeouts(monkeypatch, darwin=0.2, win32=1)
    slow_step(llm, step)

    start(client)

    assert wait_for_end(client)["state"] == "done"  # the next try answers at once (windows-launch D16)
    assert llm.processes[0].terminated is True
    assert len(llm.processes) == 2


def test_on_the_mac_the_same_slow_pick_fails_naming_the_mac_s_seconds(client, ready, llm, monkeypatch):
    os_timeouts(monkeypatch, darwin=0.2, win32=1)
    slow_step(llm, "pick")

    start(client)
    job = wait_for_end(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "model_failed")
    assert "เลือกภาพเกิน 0.2 วินาที" in job["error"]["message"]


def test_on_windows_a_ready_card_drafts_with_qwen_s_own_repo(client, project, ready, llm, monkeypatch):
    on_windows(monkeypatch)
    llm.scripts = [passing_script()]

    assert start(client).status_code == 202
    wait_for_end(client)

    assert llm.processes[0].snapshot_dir == project.snapshot_dir(QWEN_WINDOWS, QWEN_WINDOWS.revision)


def test_episodes_of_a_clip_not_transcribed_are_clip_not_ready(client, project, ready):
    write_temp_clip(project, "bbbbbbbbbbb")
    write_shots(project, "bbbbbbbbbbb")

    response = client.get("/api/spoil-maker/clips/bbbbbbbbbbb/episodes")

    assert (response.status_code, response.json()["code"]) == (400, "clip_not_ready")


def test_an_edited_line_is_what_the_counter_and_the_llm_get(client, project, ready, llm, counted):
    client.patch(f"/api/spoil/clips/{EP1}/transcript/lines/0", json={"text": "บรรทัดที่แก้"})
    llm.scripts = [passing_script()]

    start(client)
    wait_for_end(client)

    assert "[0 00:00:00] บรรทัดที่แก้\n" in counted[-1]
    assert "[0 00:00:00] บรรทัดที่แก้\n" in llm.requests[0].prompt
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
    project.marker(QWEN_MAC).unlink()

    response = start(client)

    assert response.status_code == 503
    assert response.json()["code"] == "not_ready"
    assert "model_qwen" in response.json()["rows"]


def test_a_draft_while_a_transcribe_job_runs_is_gpu_busy(client, ready, whisper):
    with transcribing(client, whisper, EP2):
        response = start(client)

    assert response.status_code == 409
    assert (response.json()["code"], response.json()["running"]) == ("gpu_busy", "transcribe")


def test_an_unknown_kind_is_invalid_request(client, ready):
    response = client.post(JOBS, json={"kind": "x"})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


# --- A Draft job from start to end ---


def test_the_draft_has_the_order_the_remembered_volume_and_becomes_the_last_voice(client, project, ready, llm):
    llm.scripts = [passing_script()]

    start(client, layout="A", style="fast", target_s=60)
    wait_for_end(client)

    found = a_draft(client)
    assert (found["style"], found["layout"], found["target_s"], found["voice_id"]) == ("fast", "A", 60, VOICE)
    assert found["original_volume"] == 20
    assert client.get("/api/spoil-maker/settings").json()["last_voice_id"] == VOICE


def test_a_draft_job_carries_its_order_while_writing_and_after_it_fails(client, project, ready, llm):
    llm.scripts = ["not json"] * 3
    llm.pause_at(0)
    title = next(clip["title"] for clip in client.get("/api/spoil/clips").json()["clips"] if clip["id"] == EP1)

    started = start(client, style="fast", layout="A", target_s=90)
    llm.wait_until(0)
    writing = client.get(CURRENT).json()
    llm.release(0)
    failed = wait_for_end(client)

    expected = {
        "clip_id": EP1,
        "clip_title": title,
        "ep": WHOLE,
        "style": "fast",
        "layout": "A",
        "target_s": 90,
        "voice_id": VOICE,
        "story_id": None,
        "story_title": None,
    }
    assert started.json()["order"] == expected
    assert writing["order"] == expected
    assert (failed["state"], failed["order"]) == ("failed", expected)


def test_a_voice_deleted_while_a_draft_starts_is_voice_not_found_and_frees_the_gpu(client, project, ready, monkeypatch):
    # The token count runs between the first voice check and the draft's lock (D87).
    def count_and_delete(snapshot_dir: Path, text: str) -> int:
        client.delete(f"/api/spoil-maker/voices/{VOICE}")
        return len(text)

    monkeypatch.setattr(spoil_maker, "count_tokens", count_and_delete)

    response = start(client)

    assert (response.status_code, response.json()["code"]) == (400, "voice_not_found")
    assert not (project.voices_dir / f"{VOICE}.json").exists()
    assert gpu.slot.holds_draft() is False
    assert client.get(CURRENT).json() is None


def test_a_clip_gone_while_a_draft_starts_does_not_hold_the_gpu(client, project, ready, monkeypatch):
    def count_and_delete(snapshot_dir: Path, text: str) -> int:
        project.clip_json(EP1).unlink()
        return len(text)

    monkeypatch.setattr(spoil_maker, "count_tokens", count_and_delete)

    response = start(client)

    assert response.status_code == 404
    assert gpu.slot.holds_draft() is False


def test_a_cancelled_draft_job_keeps_its_order(client, project, ready, llm):
    llm.scripts = [passing_script()]
    llm.pause_at(0)

    start(client)
    llm.wait_until(0)
    client.delete(CURRENT)
    llm.release(0)
    job = wait_for_end(client)

    assert (job["state"], job["order"]["clip_id"], job["order"]["ep"]) == ("cancelled", EP1, WHOLE)


def test_a_pick_or_polish_job_has_no_order(client, project, ready, llm):
    write_draft(project)

    picked = client.post(JOBS, json={"kind": "pick", "sentence_id": "s_00000001"})
    wait_for_end(client)
    polished = client.post(JOBS, json={"kind": "polish"})
    wait_for_end(client)

    assert picked.json()["order"] is None
    assert polished.json()["order"] is None
    assert client.get(CURRENT).json()["order"] is None


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
    assert "[0 00:00:00] Line 0." in request.prompt
    # The rules come again after a long Transcript, where the model reads last.
    assert request.prompt.rindex("900") > request.prompt.index("[19 ")
    pick = next(r for r in llm.requests if is_pick(r))
    assert (pick.temperature, pick.image) == (0.0, None)


def test_writing_then_polishing_then_matching_reports_done_and_total_sentences(client, project, ready, llm):
    llm.scripts = [script(*[(THIRTY, ["0"])] * 29, (THIRTY, []))]
    llm.pause_at(1)  # the polish
    llm.pause_at(3)  # the second pick

    start(client)
    llm.wait_until(1)
    polishing = wait_for(client, lambda job: job["state"] == "polishing")
    llm.release(1)
    llm.wait_until(3)
    matching = wait_for(client, lambda job: job["state"] == "matching")

    assert (polishing["done"], polishing["total"], polishing["percent"]) == (None, None, None)
    assert (matching["done"], matching["total"]) == (1, 29)
    llm.release(3)
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
    assert len([r for r in llm.requests if is_script(r)]) == 1


def test_two_broken_replies_then_a_good_one_is_done_after_three_asks(client, project, ready, llm):
    llm.scripts = ["not json", "nope", "```json\n" + passing_script() + "\n```"]

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert len([r for r in llm.requests if is_script(r)]) == 3


def test_asking_again_says_what_was_wrong_with_the_last_reply(client, project, ready, llm):
    # Real replies ran long or looped until max_tokens cut the JSON (D61).
    llm.scripts = [script(*[(THIRTY, ["0"])] * 60), "{cut", passing_script()]

    start(client)
    wait_for_end(client)

    first, second, third = [r.prompt for r in llm.requests if is_script(r)]
    assert "each sentence at most 72 Thai letters" in first  # 900 letters in 15 sentences, with room
    assert "Your last script" not in first
    assert "1800 letters in 60 sentences" in second
    assert "not complete JSON" in third


def test_a_reply_slower_than_the_timeout_counts_as_a_failed_try(client, project, ready, llm, monkeypatch):
    os_timeouts(monkeypatch, darwin=0.2, win32=1)
    llm.scripts = [FakeLlm.HANG, passing_script()]

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert llm.processes[0].terminated is True  # the stuck child is ended, a new one starts
    assert len(llm.processes) == 2


def test_a_script_far_from_the_target_is_asked_again_and_the_last_readable_is_kept(client, project, ready, llm):
    short = script(("สั้น", ["0"]))
    llm.scripts = [short, short, script(("สั้นที่สุด", ["0"]))]

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert [s["text"] for s in a_draft(client)["sentences"]] == ["สั้นที่สุด"]


def test_chinese_characters_and_lines_that_do_not_exist_are_cleaned_out(client, project, ready, llm):
    # Refs are "{episode}-{line}": EP 9 line 999 is in no Transcript.
    llm.scripts = [script(("ไป現場กัน", ["9-999"]), *[(THIRTY, ["0"])] * (PASSING - 1))]

    start(client)
    wait_for_end(client)

    first = a_draft(client)["sentences"][0]
    assert first["text"] == "ไปกัน"
    assert first["refs"] == []
    assert first["shots"] == [None, None]
    assert first["status"] == "no_shot"


def test_a_sentence_empty_after_cleaning_is_dropped(client, project, ready, llm):
    llm.scripts = [script(("現場", ["0"]), *[(THIRTY, ["0"])] * PASSING)]

    start(client)
    wait_for_end(client)

    assert len(a_draft(client)["sentences"]) == PASSING


def test_shots_picked_outside_the_window_fall_back_to_the_two_nearest_the_first_line(client, project, ready, llm):
    llm.scripts = [passing_script(refs=("10",))]  # line 10 starts at 100 s: Shot 20
    llm.picks = lambda request: '{"shots": [0, 39]}'

    start(client)
    wait_for_end(client)

    assert a_draft(client)["sentences"][0]["shots"] == [{"clip_id": EP1, "n": 19}, {"clip_id": EP1, "n": 20}]


def test_a_sentence_keeps_only_its_first_three_cited_lines(client, project, ready, llm):
    # A real reply listed a run of 60 ids for one sentence (spec › Draft job step 2: 1 to 3).
    llm.scripts = [passing_script(refs=("5", "6", "7", "8", "9"))]

    start(client)
    wait_for_end(client)

    assert [ref["line"] for ref in a_draft(client)["sentences"][0]["refs"]] == [5, 6, 7]


def test_a_wide_window_asks_about_only_the_shots_nearest_the_first_line(client, project, ready, llm, monkeypatch):
    monkeypatch.setattr(draft, "PICK_MAX_SHOTS", 6)
    llm.scripts = [passing_script(refs=("19", "10"))]  # window 70–224 s: Shots 14–39
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

    start(client, ep={"n": 1, "start_s": 0.0, "end_s": 5.0})
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
    os_timeouts(monkeypatch, darwin=0.2, win32=1)
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


# --- Polishing: after the script is written (kind "draft") ---


def test_the_script_prompt_asks_for_one_story(client, project, ready, llm):
    llm.scripts = [passing_script()]

    start(client)
    wait_for_end(client)

    assert "carries on from the one before" in next(r for r in llm.requests if is_script(r)).prompt


def test_a_draft_is_polished_after_writing_and_before_picking(client, project, ready, llm):
    rest = [(THIRTY, ["0"])] * (PASSING - 2)
    llm.scripts = [script((THIRTY, ["1"]), (THIRTY, ["2", "3"]), *rest, top_text="หัวเรื่อง")]
    llm.polishes = lambda request: polished({i: "ข" * 30 for i in asked_to_polish(request)} | {0: "ค" * 30})

    start(client, layout="A")
    wait_for_end(client)

    kinds = ["pick" if is_pick(r) else "polish" if is_polish(r) else "script" for r in llm.requests]
    assert kinds == ["script", "polish"] + ["pick"] * PASSING
    polish = llm.requests[1]
    assert asked_to_polish(polish) == {i: THIRTY for i in range(PASSING)}
    assert fixed_in(polish) == {}
    assert "[1 00:00:10] Line 1." in polish.prompt
    assert "[3 00:00:30] Line 3." in polish.prompt
    assert "หัวเรื่อง" in polish.prompt
    # The pick reads the sentence as polished.
    assert f"Sentence: {'ค' * 30}" in llm.requests[2].prompt
    found = a_draft(client)
    assert [s["text"] for s in found["sentences"][:2]] == ["ค" * 30, "ข" * 30]
    assert len(found["sentences"]) == PASSING
    assert [[r["line"] for r in s["refs"]] for s in found["sentences"][:2]] == [[1], [2, 3]]
    assert {s["edited"] for s in found["sentences"]} == {False}
    assert found["top_text"] == "หัวเรื่อง"


def test_polishing_uses_its_generation_settings(client, project, ready, llm):
    llm.scripts = [passing_script()]

    start(client)
    wait_for_end(client)

    polish = next(r for r in llm.requests if is_polish(r))
    # The script is 900 letters: twice that, plus room for the JSON (spec › ค่าการสร้างข้อความ).
    assert (polish.max_tokens, polish.temperature, polish.image) == (2 * 900 + 1000, 0.3, None)


def test_a_draft_polish_that_answers_under_half_twice_keeps_the_written_text(client, project, ready, llm, caplog):
    llm.scripts = [passing_script()]
    llm.polishes = lambda request: polished({0: "ใหม่"})  # 1 of 30

    start(client)
    job = wait_for_end(client)

    assert job["state"] == "done"
    assert len([r for r in llm.requests if is_polish(r)]) == 2
    assert a_draft(client)["sentences"][0]["text"] == THIRTY
    assert THIRTY not in caplog.text


def test_a_polish_longer_than_the_target_allows_twice_keeps_the_written_text(client, project, ready, llm):
    llm.scripts = [passing_script()]
    # 40 letters a sentence: 1,200 letters, over 900 + 25%, though each is within ±50%.
    llm.polishes = lambda request: polished({i: "ข" * 40 for i in asked_to_polish(request)})

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert len([r for r in llm.requests if is_polish(r)]) == 2
    assert {s["text"] for s in a_draft(client)["sentences"]} == {THIRTY}


def test_a_polish_slower_than_the_timeout_counts_as_a_failed_try(client, project, ready, llm, monkeypatch):
    os_timeouts(monkeypatch, darwin=0.2, win32=1)
    llm.scripts = [passing_script()]
    replies = iter([FakeLlm.HANG])
    llm.polishes = lambda request: next(replies, None) or polished({i: "ข" * 30 for i in asked_to_polish(request)})

    start(client)

    assert wait_for_end(client)["state"] == "done"
    assert llm.processes[0].terminated is True  # the stuck child is ended, a new one starts
    assert len(llm.processes) == 2
    assert a_draft(client)["sentences"][0]["text"] == "ข" * 30


# --- Polishing again (kind "polish") ---


def polish(client, **body):
    return client.post(JOBS, json={"kind": "polish", **body})


# Ten letters each, so a polished sentence of 5 to 15 passes on its own (±50%).
ONE, EDITED, THREE = "ก" * 10, "ข" * 10, "ค" * 10


def three_sentences(project, second_edited: bool = True, voiced_first: bool = False) -> None:
    """Sentence 2 edited by the user; sentence 1 voiced, if asked."""
    sentences = [
        sentence("s_00000001", ONE, refs=[{"clip_id": EP1, "line": 1}], audio=voiced(ONE) if voiced_first else None),
        sentence("s_00000002", EDITED, refs=[{"clip_id": EP1, "line": 2}]) | {"edited": second_edited},
        sentence("s_00000003", THREE, refs=[{"clip_id": EP1, "line": 3}]),
    ]
    write_draft(project, sentences=sentences)


def test_polish_keeps_the_edited_sentence_and_rewrites_the_others(client, project, ready, llm):
    three_sentences(project, voiced_first=True)
    before = a_draft(client)
    llm.polishes = lambda request: polished({0: "ง" * 12, 1: "จ" * 10, 2: "ฉ" * 12})

    response = polish(client)

    assert response.status_code == 202
    assert (response.json()["kind"], response.json()["state"]) == ("polish", "polishing")
    job = wait_for_end(client)
    assert (job["state"], job["done"], job["total"]) == ("done", 2, 2)
    request = llm.requests[0]
    assert fixed_in(request) == {1: EDITED}
    assert asked_to_polish(request) == {0: ONE, 2: THREE}
    after = a_draft(client)
    assert [s["text"] for s in after["sentences"]] == ["ง" * 12, EDITED, "ฉ" * 12]
    assert [s["edited"] for s in after["sentences"]] == [False, True, False]
    assert after["sentences"][0]["status"] == "stale_audio"
    assert [s["shots"] for s in after["sentences"]] == [s["shots"] for s in before["sentences"]]
    assert [s["refs"] for s in after["sentences"]] == [s["refs"] for s in before["sentences"]]
    assert [s["id"] for s in after["sentences"]] == [s["id"] for s in before["sentences"]]


def test_polish_with_include_edited_rewrites_every_sentence_and_clears_edited(client, project, ready, llm):
    three_sentences(project)
    llm.polishes = lambda request: polished({0: ONE, 1: "จ" * 10, 2: THREE})

    polish(client, include_edited=True)
    job = wait_for_end(client)

    assert (job["done"], job["total"]) == (1, 3)
    assert fixed_in(llm.requests[0]) == {}
    second = a_draft(client)["sentences"][1]
    assert (second["text"], second["edited"]) == ("จ" * 10, False)


def test_a_finished_polish_counts_the_sentences_whose_text_changed(client, project, ready, llm):
    three_sentences(project, second_edited=False)
    llm.polishes = lambda request: polished({0: "ง" * 10, 1: "จ" * 10, 2: "ฉ" * 10})

    polish(client)

    assert wait_for_end(client)["done"] == 3


def test_answers_for_an_unknown_a_repeated_or_a_fixed_i_are_dropped(client, project, ready, llm):
    three_sentences(project)
    llm.polishes = lambda request: json.dumps(
        {
            "sentences": [
                {"i": 0, "text": "ง" * 10},
                {"i": 1, "text": "จ" * 10},  # fixed
                {"i": 2, "text": "ฉ" * 10},
                {"i": 2, "text": "ช" * 10},
                {"i": 7, "text": "เจ็ด"},
                {"i": True, "text": "จริง"},
            ]
        },
        ensure_ascii=False,
    )

    polish(client)
    wait_for_end(client)

    assert [s["text"] for s in a_draft(client)["sentences"]] == ["ง" * 10, EDITED, THREE]


@pytest.mark.parametrize("reply", ["   ", "ง" * 20])
def test_a_sentence_polished_empty_or_far_longer_keeps_its_text(client, project, ready, llm, reply):
    three_sentences(project, second_edited=False)
    llm.polishes = lambda request: polished({0: reply, 1: "จ" * 10, 2: "ฉ" * 10})

    polish(client)
    wait_for_end(client)

    assert [s["text"] for s in a_draft(client)["sentences"]] == [ONE, "จ" * 10, "ฉ" * 10]


def test_polish_that_fails_twice_is_polish_failed_and_keeps_the_draft(client, project, ready, llm):
    three_sentences(project, second_edited=False)
    before = project.draft_file.read_text(encoding="utf-8")
    llm.polishes = lambda request: polished({0: "ง" * 10})  # 1 of 3

    polish(client)
    job = wait_for_end(client)

    assert job["state"] == "failed"
    assert job["error"] == {"code": "polish_failed", "message": "AI เรียบเรียงไม่สำเร็จ บทเดิมไม่เปลี่ยน"}
    assert len(llm.requests) == 2
    assert project.draft_file.read_text(encoding="utf-8") == before


def test_polish_that_grows_the_script_over_15_percent_fails(client, project, ready, llm):
    three_sentences(project, second_edited=False)
    # 30 letters become 36: 20% more, though each sentence passes on its own.
    llm.polishes = lambda request: polished({0: "ง" * 12, 1: "จ" * 12, 2: "ฉ" * 12})

    polish(client)

    assert wait_for_end(client)["error"]["code"] == "polish_failed"


def test_polish_when_every_sentence_is_edited_is_nothing_to_polish_unless_included(client, project, ready, llm):
    write_draft(project, sentences=[sentence("s_00000001", "หนึ่ง", refs=[{"clip_id": EP1, "line": 1}]) | {"edited": True}])

    refused = polish(client)
    included = polish(client, include_edited=True)

    assert (refused.status_code, refused.json()["code"]) == (400, "nothing_to_polish")
    assert included.status_code == 202
    wait_for_end(client)


def test_polish_of_an_empty_draft_is_nothing_to_polish(client, project, ready):
    write_draft(project, sentences=[])

    response = polish(client)

    assert (response.status_code, response.json()["code"]) == (400, "nothing_to_polish")


@pytest.mark.parametrize("value", ["yes", None, 1])
def test_include_edited_that_is_not_a_boolean_is_invalid_request(client, project, ready, value):
    three_sentences(project)

    response = polish(client, include_edited=value)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_polish_without_a_draft_is_no_draft_before_any_other_check(client, ready):
    response = polish(client, include_edited="yes")  # would be invalid_request with a draft

    assert (response.status_code, response.json()["code"]) == (404, "no_draft")


def test_polish_without_qwen_is_not_ready(client, project, ready):
    three_sentences(project)
    project.marker(QWEN_MAC).unlink()

    response = polish(client)

    assert (response.status_code, response.json()["code"]) == (503, "not_ready")


def test_polish_while_the_draft_is_voiced_is_draft_locked(client, project, ready, tts):
    three_sentences(project)

    with voicing(client, tts, "s_00000001"):
        response = polish(client)

    assert (response.status_code, response.json()["code"]) == (409, "draft_locked")


def test_polish_while_another_gpu_job_runs_is_gpu_busy(client, project, ready, whisper):
    three_sentences(project)

    with transcribing(client, whisper, EP2):
        response = polish(client)

    assert (response.status_code, response.json()["code"]) == (409, "gpu_busy")


def test_cancelling_a_polish_keeps_the_draft_and_edits_meanwhile_are_draft_locked(client, project, ready, llm):
    three_sentences(project)
    before = project.draft_file.read_text(encoding="utf-8")
    llm.pause_at(0)

    polish(client)
    llm.wait_until(0)
    refused = client.patch(f"{DRAFT}/sentences/s_00000001", json={"text": "ใหม่"})
    line = client.patch(f"/api/spoil/clips/{EP1}/transcript/lines/1", json={"text": "แก้"})
    client.delete(CURRENT)

    assert (refused.status_code, refused.json()["code"]) == (409, "draft_locked")
    assert (line.status_code, line.json()["code"]) == (409, "clip_busy")
    assert wait_for_end(client)["state"] == "cancelled"
    assert project.draft_file.read_text(encoding="utf-8") == before


def test_include_edited_in_another_kind_is_ignored(client, project, ready, llm):
    """Only `polish` reads it, so a stray one never refuses a `pick` (spec › เรียบเรียงใหม่)."""
    write_draft(project)

    response = client.post(JOBS, json={"kind": "pick", "sentence_id": "s_00000001", "include_edited": "yes"})

    assert response.status_code == 202
    wait_for_end(client)


# --- `edited` ---


def test_new_text_makes_a_sentence_edited_and_the_same_text_or_shots_do_not(client, project, ready):
    write_draft(project)

    same = client.patch(f"{DRAFT}/sentences/s_00000001", json={"text": "  ประโยคแรก "})
    shots = client.patch(f"{DRAFT}/sentences/s_00000001", json={"shots": [{"clip_id": EP1, "n": 4}, None]})
    changed = client.patch(f"{DRAFT}/sentences/s_00000002", json={"text": "ประโยคสองใหม่"})
    back = client.patch(f"{DRAFT}/sentences/s_00000002", json={"text": "ประโยคสอง"})

    assert same.json()["sentences"][0]["edited"] is False
    assert shots.json()["sentences"][0]["edited"] is False
    assert changed.json()["sentences"][1]["edited"] is True
    assert back.json()["sentences"][1]["edited"] is True  # typed back, still the user's


def test_an_inserted_sentence_is_edited(client, project, ready):
    write_draft(project)

    response = client.post(f"{DRAFT}/sentences", json={"after_id": None, "text": "ใหม่"})

    assert response.json()["sentences"][0]["edited"] is True


def test_a_draft_without_edited_reads_false(client, project, ready):
    write_draft(project)  # `sentence()` writes no `edited`

    assert [s["edited"] for s in a_draft(client)["sentences"]] == [False, False]


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
    write_draft(project, clip_id="bbbbbbbbbbb")

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
        "ep_minutes": 30,
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
    assert response.json() == {"code": "voice_in_use", "message": "เสียงนี้ใช้อยู่ใน Spoil draft หรืองานร่างบท"}
    assert (project.voices_dir / f"{VOICE}.json").is_file()
    assert listed[0]["in_use"] is True


def test_the_voice_of_an_unfinished_draft_job_is_voice_in_use_until_it_ends(client, project, ready, llm):
    llm.scripts = ["not json"] * 3
    llm.pause_at(0)

    start(client)
    llm.wait_until(0)
    while_writing = client.delete(f"/api/spoil-maker/voices/{VOICE}")
    listed = client.get("/api/spoil-maker/voices").json()
    llm.release(0)
    wait_for_end(client)
    after_failing = client.delete(f"/api/spoil-maker/voices/{VOICE}")

    assert (while_writing.status_code, while_writing.json()["code"]) == (409, "voice_in_use")
    assert listed[0]["in_use"] is True
    assert after_failing.status_code == 204


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


def test_describing_a_clip_in_the_draft_without_qwen_is_not_ready_before_in_draft(client, project, ready, three_colours):
    """The gate comes before `in_draft` (D60): no confirm is asked for a job that can't run."""
    shutil.copyfile(three_colours, project.media_temp_dir / f"{EP1}.mp4")
    write_draft(project)
    project.marker(QWEN_MAC).unlink()

    response = client.post("/api/spoil-maker/describes", json={"clip_id": EP1})

    assert (response.status_code, response.json()["code"]) == (503, "not_ready")


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


# --- The Story of the clip (story-kb seam 1) ---

GOLDEN = Path(__file__).parent / "golden"
STORIES = "/api/stories"
CLIP_STORIES = "/api/story-clips"
CONAN = {
    "title": "ยอดนักสืบจิ๋วโคนัน",
    "article": "คุโด้ ชินอิจิ ถูกบังคับกินยา\nจนตัวหดเป็นเด็ก",
    "characters": [{"name": "โคนัน", "description": "ชินอิจิในร่างเด็ก"}, {"name": "รัน", "description": ""}],
}
CONAN_BLOCK = (
    "ข้อมูลพื้นหลังของเรื่อง (ใช้เข้าใจเรื่องและสะกดชื่อเท่านั้น ห้ามเล่าเหตุการณ์จากส่วนนี้ "
    "เหตุการณ์ต้องมาจากบรรทัดของ Transcript):\n"
    "ชื่อเรื่อง: ยอดนักสืบจิ๋วโคนัน\n"
    "บทความ:\n"
    "คุโด้ ชินอิจิ ถูกบังคับกินยา\nจนตัวหดเป็นเด็ก\n"
    "ตัวละคร (เขียนชื่อตามนี้ แม้ Transcript สะกดต่าง):\n"
    "- โคนัน: ชินอิจิในร่างเด็ก\n"
    "- รัน"
)
NAMES_RULE = "เขียนชื่อตัวละครตาม Story: โคนัน, รัน\n"
TOP = "หัวเรื่อง"


def new_story(client, **changes) -> str:
    response = client.post(STORIES, json=CONAN | changes)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


def remembered(client) -> dict[str, str]:
    return client.get(CLIP_STORIES).json()


def short_then_passing() -> list[str]:
    """A first script too short, so the job asks again (step 3), then one that passes."""
    return [script((THIRTY, ["1"]), top_text=TOP), script(*[(THIRTY, ["0"])] * PASSING, top_text=TOP)]


def prompts(llm, kind) -> list[str]:
    return [request.prompt for request in llm.requests if kind(request)]


@pytest.mark.parametrize("asked", [{"story_id": None}, {}], ids=["null", "left out"])
def test_without_a_story_the_prompts_are_the_ones_from_before_story_kb(client, project, ready, llm, asked):
    llm.scripts = short_then_passing()

    assert start(client, layout="A", **asked).status_code == 202
    assert wait_for_end(client)["state"] == "done"

    # Kept from the prompts of spoil-maker before story-kb, letter for letter (spec › Testing decisions).
    first, again = prompts(llm, is_script)
    assert first == (GOLDEN / "script_prompt_no_story.txt").read_text(encoding="utf-8")
    assert again == (GOLDEN / "script_prompt_asked_again_no_story.txt").read_text(encoding="utf-8")
    assert prompts(llm, is_polish) == [(GOLDEN / "polish_prompt_no_story.txt").read_text(encoding="utf-8")]


def test_the_story_block_comes_once_before_the_transcript_and_the_names_close_the_rules(client, project, ready, llm):
    story_id = new_story(client)
    llm.scripts = short_then_passing()

    start(client, layout="A", story_id=story_id)
    assert wait_for_end(client)["state"] == "done"

    before = (GOLDEN / "script_prompt_no_story.txt").read_text(encoding="utf-8")
    again_before = (GOLDEN / "script_prompt_asked_again_no_story.txt").read_text(encoding="utf-8")
    transcript_head = "Transcript, one line each"
    retry_head = "Your last script was"
    first, again = prompts(llm, is_script)
    # The first rules, the block, then the Transcript; the rules again end with the names.
    expected = before.replace(transcript_head, f"{CONAN_BLOCK}\n\n{transcript_head}", 1) + NAMES_RULE
    assert first == expected
    assert first.count(CONAN_BLOCK) == 1
    assert again == again_before.replace(transcript_head, f"{CONAN_BLOCK}\n\n{transcript_head}", 1).replace(
        retry_head, NAMES_RULE + retry_head
    )


def test_the_polish_prompt_of_a_draft_has_the_block_after_top_text(client, project, ready, llm):
    story_id = new_story(client)
    llm.scripts = [script(*[(THIRTY, ["0"])] * PASSING, top_text=TOP)]

    start(client, layout="A", story_id=story_id)
    assert wait_for_end(client)["state"] == "done"

    before = (GOLDEN / "polish_prompt_no_story.txt").read_text(encoding="utf-8")
    script_head = "The script, one sentence each"
    (polish,) = prompts(llm, is_polish)
    assert polish == before.replace(script_head, f"{CONAN_BLOCK}\n{script_head}", 1)
    assert polish.index(f'"{TOP}"') < polish.index(CONAN_BLOCK)


def test_no_article_no_characters_and_no_description_leave_their_lines_out(client, project, ready, llm):
    bare = new_story(client, article="", characters=[])
    llm.scripts = [passing_script()]

    start(client, story_id=bare)
    wait_for_end(client)

    (prompt,) = prompts(llm, is_script)
    assert "ชื่อเรื่อง: ยอดนักสืบจิ๋วโคนัน\n\nTranscript, one line each" in prompt
    assert "บทความ:" not in prompt
    assert "ตัวละคร" not in prompt
    assert "เขียนชื่อตัวละครตาม Story" not in prompt

    named = new_story(client, characters=[{"name": "โคนัน"}])
    llm.requests.clear()
    start(client, story_id=named, replace=True)
    wait_for_end(client)

    (prompt,) = prompts(llm, is_script)
    assert "\n- โคนัน\n\nTranscript, one line each" in prompt
    assert prompt.endswith("เขียนชื่อตัวละครตาม Story: โคนัน\n")


def test_the_pick_prompts_have_no_story_block(client, project, ready, llm):
    llm.scripts = [passing_script()]

    start(client, story_id=new_story(client))
    wait_for_end(client)

    picks = prompts(llm, is_pick)
    assert len(picks) == PASSING
    assert not any("ชื่อเรื่อง" in prompt or "โคนัน" in prompt for prompt in picks)


def test_a_draft_with_a_story_remembers_it_for_the_clip_and_carries_it_in_its_order(client, project, ready, llm):
    story_id = new_story(client)
    llm.scripts = [passing_script()]

    response = start(client, story_id=story_id)
    job = wait_for_end(client)

    assert response.status_code == 202
    assert remembered(client) == {EP1: story_id}
    assert (response.json()["order"]["story_id"], response.json()["order"]["story_title"]) == (story_id, CONAN["title"])
    assert (job["order"]["story_id"], job["order"]["story_title"]) == (story_id, CONAN["title"])
    assert client.get(f"{STORIES}/{story_id}").json()["clips"] == 1


@pytest.mark.parametrize("asked", [{"story_id": None}, {}], ids=["null", "left out"])
def test_a_draft_without_a_story_makes_the_clip_forget_its_story(client, project, ready, llm, asked):
    story_id = new_story(client)
    llm.scripts = [passing_script()]
    start(client, story_id=story_id)
    wait_for_end(client)
    start(client, story_id=story_id, clip_id=EP2, replace=True)
    wait_for_end(client)

    response = start(client, replace=True, **asked)
    job = wait_for_end(client)

    assert response.status_code == 202
    assert remembered(client) == {EP2: story_id}
    assert (job["order"]["story_id"], job["order"]["story_title"]) == (None, None)


@pytest.mark.parametrize("story_id", ["st_00000000", "not-an-id", 7], ids=["no file", "bad id", "not text"])
def test_a_story_that_is_not_there_is_story_not_found_and_the_clip_keeps_its_story(client, project, ready, llm, story_id):
    kept = new_story(client)
    llm.scripts = [passing_script()]
    start(client, story_id=kept)
    wait_for_end(client)

    response = start(client, story_id=story_id, replace=True)

    assert response.status_code == 400
    assert response.json() == {"code": "story_not_found", "message": "ไม่พบเรื่องนี้ในคลังความรู้แล้ว"}
    assert remembered(client) == {EP1: kept}


def test_a_story_file_that_cannot_be_read_is_story_not_found(client, project, ready, caplog):
    story_id = new_story(client)
    (project.stories_dir / f"{story_id}.json").write_text("{", encoding="utf-8")

    response = start(client, story_id=story_id)

    assert (response.status_code, response.json()["code"]) == (400, "story_not_found")
    assert story_id in caplog.text
    assert remembered(client) == {}


def test_the_story_counts_with_the_ep_against_32000_tokens(client, project, ready, llm, monkeypatch):
    story_id = new_story(client)
    llm.scripts = [passing_script()]

    def count(snapshot_dir: Path, text: str) -> int:
        return 2_001 if text.startswith(stories.BLOCK_HEAD) else 30_000

    monkeypatch.setattr(spoil_maker, "count_tokens", count)

    refused = start(client, story_id=story_id)
    accepted = start(client, story_id=None)

    assert refused.status_code == 400
    assert refused.json() == {
        "code": "transcript_too_long",
        "message": "EP กับเรื่องรวม 32,001 token เกิน 32,000 (เรื่อง 2,001)",
        "tokens": 32_001,
        "story_tokens": 2_001,
    }
    assert remembered(client) == {}
    assert accepted.status_code == 202
    wait_for_end(client)


def test_the_story_block_is_counted_as_the_llm_gets_it(client, project, ready, llm, counted):
    llm.scripts = [passing_script()]

    start(client, story_id=new_story(client))
    wait_for_end(client)

    assert CONAN_BLOCK in counted


def test_a_story_without_qwens_tokenizer_is_not_ready(client, project, ready, monkeypatch):
    story_id = new_story(client)

    def gone(snapshot_dir, text):
        if text.startswith(stories.BLOCK_HEAD):
            raise FileNotFoundError(snapshot_dir)
        return len(text)

    monkeypatch.setattr(spoil_maker, "count_tokens", gone)

    response = start(client, story_id=story_id)

    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", ["model_qwen"])


def test_a_draft_refused_as_draft_exists_or_gpu_busy_leaves_the_clips_story_as_it_was(client, project, ready, llm, whisper):
    kept, other = new_story(client), new_story(client, title="เรื่องสอง")
    llm.scripts = [passing_script()]
    start(client, story_id=kept)
    wait_for_end(client)

    exists = start(client, story_id=other)
    with transcribing(client, whisper, EP2):
        busy = start(client, story_id=other, replace=True)

    assert (exists.status_code, exists.json()["code"]) == (409, "draft_exists")
    assert (busy.status_code, busy.json()["code"]) == (409, "gpu_busy")
    assert remembered(client) == {EP1: kept}


def test_a_story_deleted_while_a_draft_starts_is_story_not_found_and_frees_the_gpu(client, project, ready, llm, monkeypatch):
    story_id = new_story(client)
    llm.scripts = [passing_script()]

    # The token count runs between the Story check and the draft's lock.
    def count_and_delete(snapshot_dir: Path, text: str) -> int:
        client.delete(f"{STORIES}/{story_id}")
        return len(text)

    monkeypatch.setattr(spoil_maker, "count_tokens", count_and_delete)

    response = start(client, story_id=story_id)

    assert (response.status_code, response.json()["code"]) == (400, "story_not_found")
    assert remembered(client) == {}
    assert client.get(CURRENT).json() is None
    # The GPU went back: the next draft starts.
    assert start(client).status_code == 202
    wait_for_end(client)


def test_a_story_changed_during_a_draft_job_leaves_the_job_with_the_story_as_it_started(client, project, ready, llm):
    story_id = new_story(client)
    llm.scripts = [passing_script()]
    llm.pause_at(1)  # the polish

    start(client, story_id=story_id)
    llm.wait_until(1)
    changed = client.put(f"{STORIES}/{story_id}", json=CONAN | {"title": "ชื่อใหม่"})
    llm.release(1)
    job = wait_for_end(client)

    assert changed.status_code == 200
    (polish,) = prompts(llm, is_polish)
    assert "ชื่อเรื่อง: ยอดนักสืบจิ๋วโคนัน" in polish
    assert "ชื่อใหม่" not in polish
    assert job["order"]["story_title"] == CONAN["title"]


# --- Polishing again with the clip's Story (story-kb D5, ADR 0024) ---

NEW_CONAN = CONAN | {
    "article": "ชินอิจิกลายเป็นเด็ก",
    "characters": [{"name": "เอโดงาวะ โคนัน", "description": "ชื่อใหม่"}, {"name": "รัน", "description": ""}],
}
NEW_CONAN_BLOCK = CONAN_BLOCK.replace(
    "คุโด้ ชินอิจิ ถูกบังคับกินยา\nจนตัวหดเป็นเด็ก", "ชินอิจิกลายเป็นเด็ก"
).replace("- โคนัน: ชินอิจิในร่างเด็ก", "- เอโดงาวะ โคนัน: ชื่อใหม่")


def drafted_with(client, project, llm, story_id: str | None) -> None:
    """A draft whose clip remembers `story_id` (through a real Draft job), then three known sentences."""
    llm.scripts = [passing_script()]
    start(client, story_id=story_id)
    assert wait_for_end(client)["state"] == "done"
    three_sentences(project)
    llm.requests.clear()


def test_polish_after_the_story_is_changed_asks_with_its_new_values(client, project, ready, llm):
    story_id = new_story(client)
    drafted_with(client, project, llm, story_id)
    assert client.put(f"{STORIES}/{story_id}", json=NEW_CONAN).status_code == 200

    polish(client)
    assert wait_for_end(client)["state"] == "done"

    no_story_prompt = (GOLDEN / "polish_again_prompt_no_story.txt").read_text(encoding="utf-8")
    script_head = "The script, one sentence each"
    (prompt,) = prompts(llm, is_polish)
    assert prompt == no_story_prompt.replace(script_head, f"{NEW_CONAN_BLOCK}\n{script_head}", 1)


@pytest.mark.parametrize("gone", ["never remembered", "story deleted", "file unreadable"])
def test_polish_without_the_clips_story_is_the_prompt_from_before_story_kb(client, project, ready, llm, gone):
    story_id = new_story(client)
    drafted_with(client, project, llm, None if gone == "never remembered" else story_id)
    if gone == "story deleted":
        assert client.delete(f"{STORIES}/{story_id}").status_code == 204
    if gone == "file unreadable":
        (project.stories_dir / f"{story_id}.json").write_text("{", encoding="utf-8")

    response = polish(client)
    assert wait_for_end(client)["state"] == "done"

    assert response.json()["order"] is None
    # Captured from the code before story-kb (d5557214), letter for letter (spec › Testing
    # decisions, story-kb D19).
    assert prompts(llm, is_polish) == [(GOLDEN / "polish_again_prompt_no_story.txt").read_text(encoding="utf-8")]


def test_pick_of_a_clip_that_remembers_a_story_has_no_story_block(client, project, ready, llm):
    """`kind: "pick"` after a draft with a Story: unlike `polish`, its prompt leaves the Story out (D4)."""
    drafted_with(client, project, llm, new_story(client))

    response = client.post(JOBS, json={"kind": "pick", "sentence_id": "s_00000001"})

    assert (response.status_code, wait_for_end(client)["state"]) == (202, "done")
    (prompt,) = prompts(llm, is_pick)
    assert "ชื่อเรื่อง" not in prompt and "โคนัน" not in prompt
