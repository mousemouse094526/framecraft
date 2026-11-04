"""A Temp clip cut into EPs, and a Spoil draft of one EP, under /api/spoil-maker (spoil-maker
seam 1 › EP). The 3-second test clip is too short to cut: these use a fake Shot file of a
3,600-second clip with a Shot every 7 seconds."""

import json

import pytest

from backend.paths import ProjectPaths

from .fakes import write_temp_clip, write_transcript
from .test_spoil_maker_draft_api import (  # noqa: F401 (fixtures)
    DRAFT,
    JOBS,
    THIRTY,
    VOICE,
    a_draft,
    client,
    counted,
    is_pick,
    llm,
    project,
    script,
    sentence,
    start,
    transcribing,
    tts,
    voicing,
    wait_for_end,
    whisper,
    write_draft,
    write_voice,
)

FILM = "fffffffffff"
OTHER = "ggggggggggg"
SETTINGS = "/api/spoil-maker/settings"
# A line a minute, 5 s in: line k starts at 60k + 5.
FILM_LINES = [{"start_s": 60.0 * k + 5, "end_s": 60.0 * k + 9, "text": f"Line {k}."} for k in range(60)]
PASSING = 30  # sentences of THIRTY: 900 letters, the target


def episodes_path(clip_id: str = FILM) -> str:
    return f"/api/spoil-maker/clips/{clip_id}/episodes"


def write_film(project: ProjectPaths, clip_id: str = FILM, length: float = 3600, lines=FILM_LINES) -> None:
    """A transcribed, described clip `length` seconds long, a Shot every 7 s."""
    write_temp_clip(project, clip_id)
    write_transcript(project, clip_id, lines=lines)
    folder = project.clip_shots_dir(clip_id)
    folder.mkdir(parents=True, exist_ok=True)
    count = int(-(-length // 7))
    found = [
        {"n": n, "start": 7.0 * n, "end": min(7.0 * n + 7, length), "description": f"Shot {n}."} for n in range(count)
    ]
    (folder / "shots.json").write_text(json.dumps({"clip_id": clip_id, "shots": found}), encoding="utf-8")


def cuts_of(response) -> list[float]:
    return [ep["start_s"] for ep in response.json()["episodes"][1:]]


@pytest.fixture
def film(project) -> None:
    write_film(project)
    write_voice(project)


# --- Cutting ---


def test_a_clip_without_a_cut_is_cut_by_ep_minutes_at_the_nearest_shot(client, project, film):
    response = client.get(episodes_path())

    assert response.status_code == 200
    body = response.json()
    assert (body["clip_id"], body["minutes"], body["custom"], body["limit"]) == (FILM, 30, False, 32_000)
    # 1,800 is between the Shots at 1,799 and 1,806: 1,799 is nearer.
    assert [(ep["n"], ep["start_s"], ep["end_s"]) for ep in body["episodes"]] == [(1, 0.0, 1799.0), (2, 1799.0, 3600.0)]
    assert [ep["thumb_shot"] for ep in body["episodes"]] == [0, 257]
    assert [ep["lines"] for ep in body["episodes"]] == [30, 30]
    assert [(ep["renders"], ep["in_draft"]) for ep in body["episodes"]] == [(0, False), (0, False)]
    assert project.episodes_file(FILM).is_file()


def test_putting_minutes_cuts_again_and_remembers_them(client, film):
    response = client.put(episodes_path(), json={"minutes": 25})

    assert response.status_code == 200
    assert cuts_of(response) == [1498.0, 3003.0]
    assert response.json()["episodes"][-1]["end_s"] - response.json()["episodes"][-1]["start_s"] == 597.0
    assert response.json()["custom"] is False
    assert client.get(SETTINGS).json()["ep_minutes"] == 25


def test_a_last_piece_under_a_minute_joins_the_ep_before(client, project):
    write_film(project, length=1830)

    response = client.get(episodes_path())

    assert [(ep["start_s"], ep["end_s"]) for ep in response.json()["episodes"]] == [(0.0, 1830.0)]


def test_users_cuts_move_to_the_nearest_shot_start(client, film):
    response = client.put(episodes_path(), json={"minutes": 30, "cuts": [1000]})

    assert response.status_code == 200
    assert cuts_of(response) == [1001.0]
    assert response.json()["custom"] is True
    assert client.get(episodes_path()).json()["custom"] is True


def test_a_cut_halfway_between_two_shots_goes_to_the_earlier(client, film):
    # 66.5 is halfway between the Shots at 63 and 70 (an EP under a minute is refused, so not 7 and 14).
    response = client.put(episodes_path(), json={"minutes": 30, "cuts": [66.5]})

    assert cuts_of(response) == [63.0]


@pytest.mark.parametrize(
    "body",
    [
        {"minutes": 30, "cuts": [1000, 1030]},  # EP 2 would be 28 s
        {"minutes": 7},
        {"minutes": 65},
        {"minutes": True},
        # Python's json reads NaN, so a cut must be checked finite; the test client won't send it.
        '{"minutes": 30, "cuts": [NaN]}',
        {"minutes": 30, "cuts": [True]},
        {"minutes": 30, "cuts": ["10"]},
        {"minutes": 30, "cuts": [2000, 1000]},
        {"minutes": 30, "cuts": [float(n) for n in range(100, 6200, 100)]},  # 61 cuts in 60 minutes
        {"cuts": [1000]},
    ],
)
def test_cuts_breaking_the_rules_are_invalid_episodes(client, film, body):
    if isinstance(body, str):
        response = client.put(episodes_path(), content=body, headers={"Content-Type": "application/json"})
    else:
        response = client.put(episodes_path(), json=body)

    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_episodes",
        "message": "ตัด EP แบบนี้ไม่ได้: ทุก EP ต้องยาวอย่างน้อย 1 นาทีและเรียงตามเวลา",
    }


def test_a_short_clip_is_one_ep_whatever_the_minutes(client, project):
    write_film(project, length=40, lines=[{"start_s": 1.0, "end_s": 2.0, "text": "Hi."}])

    listed = client.get(episodes_path())
    put = client.put(episodes_path(), json={"minutes": 30})

    assert [(ep["start_s"], ep["end_s"]) for ep in listed.json()["episodes"]] == [(0.0, 40.0)]
    assert put.status_code == 200


def test_a_clips_cut_keeps_its_first_minutes_when_another_clip_changes_them(client, project, film):
    write_film(project, OTHER)
    client.get(episodes_path())

    client.put(episodes_path(OTHER), json={"minutes": 25})

    assert cuts_of(client.get(episodes_path())) == [1799.0]


@pytest.mark.parametrize(
    "content",
    ["{not json", '{"minutes": 30, "cuts": [1800.0], "custom": true}'],  # 1,800 is no Shot's start
)
def test_a_broken_cut_file_is_cut_again_by_ep_minutes(client, project, film, content):
    project.episodes_dir.mkdir(parents=True)
    project.episodes_file(FILM).write_text(content, encoding="utf-8")

    response = client.get(episodes_path())

    assert response.status_code == 200
    assert (cuts_of(response), response.json()["custom"]) == ([1799.0], False)


def test_putting_a_cut_while_a_transcribe_job_reads_the_clip_is_clip_busy(client, film, whisper):
    with transcribing(client, whisper, FILM):
        response = client.put(episodes_path(), json={"minutes": 25})

    assert (response.status_code, response.json()["code"]) == (409, "clip_busy")


def test_putting_a_cut_while_a_voice_job_reads_the_clip_is_allowed(client, project, film, tts):
    """A Voice job reads the draft's own copy of its EP, not the clip's cut (D71)."""
    write_voice(project)
    write_draft(project, clip_id=FILM, sentences=[sentence("s_00000001", "ประโยค", refs=[{"clip_id": FILM, "line": 1}])])

    with voicing(client, tts, "s_00000001"):
        response = client.put(episodes_path(), json={"minutes": 25})

    assert response.status_code == 200


def test_a_cut_that_is_not_json_is_415(client, film):
    response = client.put(episodes_path(), content=b'{"minutes": 25}', headers={"Content-Type": "text/plain"})

    assert (response.status_code, response.json()["code"]) == (415, "unsupported_media_type")


def test_episodes_of_a_clip_not_described_are_clip_not_ready(client, project):
    write_temp_clip(project, FILM)
    write_transcript(project, FILM)

    response = client.get(episodes_path())

    assert (response.status_code, response.json()["code"]) == (400, "clip_not_ready")


def test_episodes_of_an_unknown_clip_are_not_found(client):
    assert client.get(episodes_path()).status_code == 404


def test_deleting_the_clip_removes_its_cut(client, project, film):
    client.get(episodes_path())

    response = client.delete(f"/api/spoil/clips/{FILM}")

    assert response.status_code == 204
    assert not project.episodes_file(FILM).exists()


# --- A draft of one EP ---


def ep2(**overrides) -> dict:
    return {"n": 2, "start_s": 1799.0, "end_s": 3600.0} | overrides


def draft_ep2(client, llm, refs=("30",)):
    llm.scripts = [script(*[(THIRTY, list(refs))] * PASSING)]
    response = start(client, clip_id=FILM, ep=ep2())
    assert response.status_code == 202, response.json()
    return wait_for_end(client)


def test_drafting_ep_2_sends_only_its_lines_and_picks_shots_inside_it(client, film, llm):
    job = draft_ep2(client, llm)

    assert job["state"] == "done"
    prompt = llm.requests[0].prompt
    # Line 29 starts at 1,745, before the cut at 1,799; line 30 at 1,805.
    assert "[30 00:30:05] Line 30.\n" in prompt
    assert "Line 29." not in prompt
    found = a_draft(client)
    assert found["clip_id"] == FILM
    assert found["ep"] == ep2()
    assert found["clip_title"] == "ชื่อคลิป"
    first = found["sentences"][0]
    assert first["refs"] == [{"clip_id": FILM, "line": 30}]
    for slot in first["shots"]:
        assert first["window"]["start"] <= 7.0 * slot["n"] < first["window"]["end"]


def test_a_window_near_the_cut_starts_at_the_cut(client, film, llm):
    draft_ep2(client, llm)

    # Line 30 is 1,805–1,809: 30 s before is 1,775, inside EP 1.
    assert a_draft(client)["sentences"][0]["window"] == {"clip_id": FILM, "start": 1799.0, "end": 1839.0}


def test_a_ref_to_a_line_of_another_ep_is_dropped(client, film, llm):
    draft_ep2(client, llm, refs=("29", "31"))

    assert a_draft(client)["sentences"][0]["refs"] == [{"clip_id": FILM, "line": 31}]


def test_an_ep_number_the_cut_has_not_is_invalid_episodes(client, film):
    response = start(client, clip_id=FILM, ep={"n": 3, "start_s": 3600.0, "end_s": 3600.0})

    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_episodes",
        "message": "ตัด EP แบบนี้ไม่ได้: ทุก EP ต้องยาวอย่างน้อย 1 นาทีและเรียงตามเวลา",
    }


def test_ep_minutes_edited_out_of_range_cut_by_30(client, project, film):
    project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
    project.settings_file.write_text('{"ep_minutes": 0}', encoding="utf-8")

    response = client.get(episodes_path())

    assert (response.status_code, cuts_of(response)) == (200, [1799.0])


def test_an_ep_whose_range_moved_is_episodes_changed(client, film):
    response = start(client, clip_id=FILM, ep=ep2(start_s=1806.0))

    assert response.status_code == 409
    assert response.json() == {"code": "episodes_changed", "message": "การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง"}


def test_an_ep_without_lines_is_ep_empty(client, project):
    write_film(project, lines=FILM_LINES[:10])
    write_voice(project)

    response = start(client, clip_id=FILM, ep=ep2())

    assert response.json() == {"code": "ep_empty", "message": "EP นี้ไม่มีบทพูด"}
    assert response.status_code == 400
    assert [ep["lines"] for ep in client.get(episodes_path()).json()["episodes"]] == [10, 0]


def test_the_ep_of_the_draft_is_marked_in_draft(client, project, film):
    write_draft(project, clip_id=FILM, ep=ep2(), sentences=[sentence("s_00000001", "ประโยค", refs=[{"clip_id": FILM, "line": 30}])])

    found = client.get(episodes_path()).json()["episodes"]

    assert [ep["in_draft"] for ep in found] == [False, True]


def test_shots_outside_the_drafts_ep_are_invalid_shot(client, project, film):
    write_draft(project, clip_id=FILM, ep=ep2(), sentences=[sentence("s_00000001", "ประโยค", refs=[{"clip_id": FILM, "line": 30}])])

    response = client.patch(
        f"{DRAFT}/sentences/s_00000001", json={"shots": [{"clip_id": FILM, "n": 10}, {"clip_id": FILM, "n": 300}]}
    )

    assert (response.status_code, response.json()["code"]) == (400, "invalid_shot")


def test_a_draft_of_the_old_version_is_no_draft(client, project, film):
    content = write_draft(project, clip_id=FILM, ep=ep2())
    old = {key: value for key, value in content.items() if key not in ("clip_id", "ep")}
    project.draft_file.write_text(json.dumps(old | {"version": 1, "clip_ids": [FILM]}), encoding="utf-8")

    assert client.get(DRAFT).json() is None
