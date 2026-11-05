"""Stories and the Story each clip remembers, under /api/stories and /api/story-clips
(story-kb seam 1 › CRUD, `invalid_story`, `DELETE` Story, deleting a clip, Trim job, restart)."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from backend import spoil_maker, stories
from backend.app import app
from backend.models import QWEN
from backend.paths import ProjectPaths

from .fakes import write_temp_clip
from .test_spoil_trim_api import (  # noqa: F401 (fixtures)
    OTHER_ID,
    VIDEO_ID,
    client,
    ffmpeg_run,
    media,
    project,
    start,
    tts,
    use_trims,
    wait_for_end,
)

STORIES = "/api/stories"
CLIP_STORIES = "/api/story-clips"
CONAN = {
    "title": "  ยอดนักสืบจิ๋ว\nโคนัน  ",
    "article": "  คุโด้ ชินอิจิ ถูกบังคับกินยา\nจนตัวหดเป็นเด็ก  ",
    "characters": [
        {"name": " โคนัน\n", "description": "ชินอิจิในร่างเด็ก\nไขคดีแทนลุง"},
        {"name": "รัน"},
    ],
}


# Characters of the Story block (spec › คำสั่ง LLM) of CONAN titled "เรื่องแรก แก้แล้ว", and of
# "เรื่องสอง" with CONAN's article and no characters.
TOKENS_OF_EDITED = 307
TOKENS_OF_SECOND = 203


@pytest.fixture(autouse=True)
def tokens(monkeypatch):
    """Qwen's tokenizer stand-in: one token per character of the Story block."""
    monkeypatch.setattr(spoil_maker, "count_tokens", lambda snapshot, text: len(text))


def create(client, **changes) -> dict:
    response = client.post(STORIES, json={**CONAN, **changes})
    assert response.status_code == 201, response.json()
    return response.json()


def remember(project: ProjectPaths, links: dict[str, str]) -> None:
    """What a Draft job leaves behind (D15): ticket 02 writes it through the API."""
    project.stories_dir.mkdir(parents=True, exist_ok=True)
    project.clip_stories_file.write_text(json.dumps(links), encoding="utf-8")


def refused(response, status: int, code: str) -> dict:
    assert (response.status_code, response.json()["code"]) == (status, code), response.json()
    return response.json()


# --- CRUD ---


def test_a_created_story_reads_back_trimmed_with_line_breaks_only_in_the_article(client):
    created = create(client)

    got = client.get(f"{STORIES}/{created['id']}")

    assert got.status_code == 200
    story = got.json()
    assert story == created
    assert story["id"].startswith("st_") and len(story["id"]) == 11
    assert story["title"] == "ยอดนักสืบจิ๋ว โคนัน"
    assert story["article"] == "คุโด้ ชินอิจิ ถูกบังคับกินยา\nจนตัวหดเป็นเด็ก"
    assert story["characters"] == [
        {"name": "โคนัน", "description": "ชินอิจิในร่างเด็ก ไขคดีแทนลุง"},
        {"name": "รัน", "description": ""},
    ]
    assert story["clips"] == 0
    assert story["created_at"] == story["updated_at"]


def test_article_and_characters_may_be_left_out(client):
    response = client.post(STORIES, json={"title": "หนังสั้น"})

    assert response.status_code == 201
    story = response.json()

    assert (story["article"], story["characters"]) == ("", [])


def test_the_list_is_newest_change_first_with_counts_and_tokens(client, project):
    first = create(client, title="เรื่องแรก")
    second = create(client, title="เรื่องสอง", characters=[])
    client.put(f"{STORIES}/{first['id']}", json={**CONAN, "title": "เรื่องแรก แก้แล้ว"})
    remember(project, {VIDEO_ID: first["id"], OTHER_ID: first["id"]})

    rows = client.get(STORIES).json()

    assert [row["id"] for row in rows] == [first["id"], second["id"]]
    edited = rows[0]
    assert (edited["title"], edited["characters"], edited["clips"]) == ("เรื่องแรก แก้แล้ว", 2, 2)
    stored = client.get(f"{STORIES}/{first['id']}").json()
    # The fake tokenizer counts the Story block's characters: heading, title, article, two characters.
    assert edited["tokens"] == TOKENS_OF_EDITED
    assert rows[1]["tokens"] == TOKENS_OF_SECOND
    assert edited["updated_at"] == stored["updated_at"]
    assert set(edited) == {"id", "title", "characters", "clips", "tokens", "updated_at"}


def test_tokens_are_null_without_qwens_tokenizer(client, project):
    create(client)
    project.marker(QWEN).unlink()

    assert [row["tokens"] for row in client.get(STORIES).json()] == [None]


def test_put_replaces_the_whole_story_and_moves_updated_at(client, monkeypatch):
    created = create(client)
    monkeypatch.setattr(stories, "now_iso", lambda: "2030-01-01T00:00:00+07:00")

    response = client.put(f"{STORIES}/{created['id']}", json={"title": "ชื่อใหม่"})

    assert response.status_code == 200
    story = response.json()
    assert (story["title"], story["article"], story["characters"]) == ("ชื่อใหม่", "", [])
    assert (story["created_at"], story["updated_at"]) == (created["created_at"], "2030-01-01T00:00:00+07:00")
    assert client.get(f"{STORIES}/{created['id']}").json() == story


def test_deleting_a_story_forgets_it_for_every_clip(client, project):
    kept = create(client, title="อีกเรื่อง")
    gone = create(client)
    remember(project, {VIDEO_ID: gone["id"], OTHER_ID: gone["id"], "ccccccccccc": kept["id"]})

    response = client.delete(f"{STORIES}/{gone['id']}")

    assert response.status_code == 204
    assert client.get(CLIP_STORIES).json() == {"ccccccccccc": kept["id"]}
    refused(client.get(f"{STORIES}/{gone['id']}"), 404, "not_found")


# --- Refusals ---


@pytest.mark.parametrize(
    ("changes", "field", "message"),
    [
        ({"title": " \n "}, "title", "ใส่ชื่อเรื่อง"),
        ({"title": "ก" * 101}, "title", "ชื่อเรื่องยาวเกิน 100 ตัวอักษร"),
        ({"article": "ก" * 5_001}, "article", "บทความยาวเกิน 5,000 ตัวอักษร"),
        ({"characters": [{"name": f"ตัว {i}"} for i in range(31)]}, "characters", "ตัวละครได้ไม่เกิน 30 ตัว"),
        ({"characters": [{"name": "  "}]}, "characters.0.name", "ใส่ชื่อตัวละคร"),
        ({"characters": [{"name": "ก" * 41}]}, "characters.0.name", "ชื่อตัวละครยาวเกิน 40 ตัวอักษร"),
        ({"characters": [{"name": "Conan"}, {"name": " conan "}]}, "characters.1.name", "ชื่อตัวละครซ้ำ"),
        ({"characters": [{"name": "Ran Mouri"}, {"name": "ran\nmouri"}]}, "characters.1.name", "ชื่อตัวละครซ้ำ"),
        ({"characters": [{"name": "รัน", "description": "ก" * 201}]}, "characters.0.description", "คำอธิบายยาวเกิน 200 ตัวอักษร"),
    ],
)
def test_a_value_outside_the_rules_is_invalid_story_naming_its_field(client, changes, field, message):
    body = refused(client.post(STORIES, json={**CONAN, **changes}), 400, "invalid_story")

    assert (body["field"], body["message"]) == (field, message)
    assert client.get(STORIES).json() == []


def test_a_missing_title_is_the_same_as_an_empty_one(client):
    body = refused(client.post(STORIES, json={"article": "บทความ"}), 400, "invalid_story")

    assert body["field"] == "title"


def test_5000_thai_letters_with_vowels_and_tone_marks_are_created(client):
    # "กี่" is three code points: ก, ี, ่ (spec › Data: letters are code points).
    article = "กี่" * 1_666 + "ก" * 2
    assert len(article) == 5_000

    response = client.post(STORIES, json={"title": "เรื่อง", "article": article})

    assert response.status_code == 201
    assert response.json()["article"] == article


@pytest.mark.parametrize(
    "body",
    [
        [CONAN],
        "เรื่อง",
        {"title": 1},
        {"title": "เรื่อง", "article": 5},
        {"title": "เรื่อง", "characters": {"name": "รัน"}},
        {"title": "เรื่อง", "characters": ["รัน"]},
        {"title": "เรื่อง", "characters": [{"name": 7}]},
        {"title": "เรื่อง", "characters": [{"name": "รัน", "description": ["ก"]}]},
    ],
)
def test_a_body_of_the_wrong_shape_is_invalid_request(client, body):
    refused(client.post(STORIES, json=body), 400, "invalid_request")


def test_a_body_that_isnt_json_is_415(client):
    response = client.post(STORIES, content="title=x", headers={"content-type": "application/x-www-form-urlencoded"})

    refused(response, 415, "unsupported_media_type")


@pytest.mark.parametrize(
    "story_id",
    [
        "st_0000000g",
        "st_ABCDEF12",
        "v_0000abcd",
        "st_1234567",
        "st_00000000",  # the right shape, no file
    ],
)
@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_an_id_that_isnt_a_story_is_not_found(client, method, story_id):
    kwargs = {"json": CONAN} if method == "put" else {}

    refused(getattr(client, method)(f"{STORIES}/{story_id}", **kwargs), 404, "not_found")


def test_a_bad_put_changes_nothing(client):
    created = create(client)

    refused(client.put(f"{STORIES}/{created['id']}", json={"title": ""}), 400, "invalid_story")
    assert client.get(f"{STORIES}/{created['id']}").json()["title"] == "ยอดนักสืบจิ๋ว โคนัน"


# --- The Story a clip remembers (D7) ---


def test_no_clip_remembers_a_story_at_first(client):
    assert client.get(CLIP_STORIES).json() == {}


def test_deleting_a_clip_forgets_its_story_and_keeps_the_story(client, project):
    story = create(client)
    write_temp_clip(project, OTHER_ID)
    remember(project, {VIDEO_ID: story["id"], OTHER_ID: story["id"]})

    response = client.delete(f"/api/spoil/clips/{VIDEO_ID}")

    assert response.status_code == 204
    assert client.get(CLIP_STORIES).json() == {OTHER_ID: story["id"]}
    assert client.get(f"{STORIES}/{story['id']}").json()["clips"] == 1


def test_a_trim_job_that_is_done_keeps_the_clips_story(client, project):
    """A Trim job drops what was made from the mp4; the Story a user chose isn't (D7, ADR 0022)."""
    story = create(client)
    remember(project, {VIDEO_ID: story["id"]})

    assert start(client).status_code == 202
    assert wait_for_end(client)["state"] == "done"

    assert client.get(CLIP_STORIES).json() == {VIDEO_ID: story["id"]}


def test_an_unreadable_clip_stories_file_reads_as_empty_and_is_logged(client, project, caplog):
    create(client)
    project.clip_stories_file.write_text("{not json", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="backend.stories"):
        assert client.get(CLIP_STORIES).json() == {}

    assert "clip-stories.json" in caplog.text


@pytest.mark.parametrize("content", ['["a"]', '{"abc": 5}', '{"abc": "not-a-story"}'])
def test_a_clip_stories_file_of_the_wrong_shape_reads_as_empty(client, project, content):
    project.stories_dir.mkdir(parents=True, exist_ok=True)
    project.clip_stories_file.write_text(content, encoding="utf-8")

    assert client.get(CLIP_STORIES).json() == {}


def test_an_unreadable_story_is_left_out_and_logged_by_id_only(client, project, caplog):
    kept = create(client, title="อีกเรื่อง")
    broken = create(client)
    path = project.stories_dir / f"{broken['id']}.json"
    path.write_text(path.read_text(encoding="utf-8")[:-40], encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="backend.stories"):
        rows = client.get(STORIES).json()

    assert [row["id"] for row in rows] == [kept["id"]]
    refused(client.get(f"{STORIES}/{broken['id']}"), 404, "not_found")
    assert broken["id"] in caplog.text
    assert "คุโด้" not in caplog.text and "โคนัน" not in caplog.text and "รัน" not in caplog.text


# --- Restart (spec › Ops) ---


def test_a_restart_keeps_stories_and_keys_and_drops_leftovers(client, project):
    story = create(client)
    other = create(client, title="อีกเรื่อง")
    write_temp_clip(project, OTHER_ID)
    remember(
        project,
        {
            VIDEO_ID: story["id"],  # kept: the clip and the Story are there
            OTHER_ID: other["id"],  # kept
            "gonegonegon": story["id"],  # the clip has no json
            "ccccccccccc": "st_deadbeef",  # the Story has no file
        },
    )
    write_temp_clip(project, "ccccccccccc")
    (project.stories_dir / f"{story['id']}.json.tmp").write_text("{", encoding="utf-8")
    (project.stories_dir / "clip-stories.json.tmp").write_text("{", encoding="utf-8")

    with TestClient(app, base_url="http://127.0.0.1") as restarted:
        assert restarted.get(CLIP_STORIES).json() == {VIDEO_ID: story["id"], OTHER_ID: other["id"]}
        assert [row["id"] for row in restarted.get(STORIES).json()] == [other["id"], story["id"]]

    assert list(project.stories_dir.glob("*.tmp")) == []


def test_a_restart_with_no_stories_folder_creates_nothing(client, project):
    with TestClient(app, base_url="http://127.0.0.1") as restarted:
        assert restarted.get(STORIES).json() == []

    assert not project.stories_dir.exists()
