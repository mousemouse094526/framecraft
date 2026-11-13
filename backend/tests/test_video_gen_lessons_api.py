"""Drum lessons and ฟังจังหวะ under /api/drums (video-gen seam 1 › new lesson, too long,
D20 rules, id in the path, copy and delete, a broken `lesson.json`, the background picture,
listen, `not_ready`)."""

import io
import json
import logging

import numpy as np
import pytest
import soundfile
from fastapi.testclient import TestClient
from PIL import Image

from backend import paths
from backend.app import app
from backend.paths import ProjectPaths
from backend.video_gen import backgrounds, lessons

from .fakes import png, put_background, restart

LESSONS = "/api/drums/lessons"


@pytest.fixture
def project(fake_root, monkeypatch) -> ProjectPaths:
    monkeypatch.setattr(paths, "ROOT", fake_root)
    return ProjectPaths(fake_root)


@pytest.fixture
def client(project) -> TestClient:
    return TestClient(app, base_url="http://127.0.0.1")


def new_lesson(client, title: str = "SMELLS LIKE TEEN SPIRIT") -> dict:
    response = client.post(LESSONS, json={"title": title})
    assert response.status_code == 201
    return response.json()


def body_of(lesson: dict, **changes) -> dict:
    """What the page sends back with `PUT`: the lesson without what the server sets."""
    body = {k: v for k, v in lesson.items() if k not in ("id", "version", "updated_at", "length_s")}
    return body | changes


def put(client, lesson: dict, **changes):
    return client.put(f"{LESSONS}/{lesson['id']}", json=body_of(lesson, **changes))


def lesson_file(project: ProjectPaths, lesson_id: str):
    return project.lessons_dir / lesson_id / "lesson.json"


def note(piece: str, step: int, hand: str | None = "R", hit: str = "normal") -> dict:
    return {"piece": piece, "step": step, "hand": hand, "hit": hit}


def groove(*notes: dict, bars: int = 1) -> dict:
    return {"bars": bars, "notes": list(notes)}


def chapter(**changes) -> dict:
    return {"label": "", "text": "", "focus": [], "repeats": 1, "speed": 100} | changes


# --- A new lesson and the list ---


def test_a_new_lesson_has_the_default_rock_groove_and_two_chapters(client):
    lesson = new_lesson(client)

    assert len(lesson["id"]) == 12
    assert (lesson["title"], lesson["bpm"], lesson["background"]) == ("SMELLS LIKE TEEN SPIRIT", 100, "color")
    assert lesson["groove"]["bars"] == 1
    notes = {(n["piece"], n["step"], n["hand"], n["hit"]) for n in lesson["groove"]["notes"]}
    assert notes == {("hihat_closed", step, "R", "normal") for step in range(0, 16, 2)} | {
        ("snare", 4, "L", "normal"),
        ("snare", 12, "L", "normal"),
        ("kick", 0, None, "normal"),
        ("kick", 8, None, "normal"),
    }
    assert [(c["label"], c["repeats"], c["speed"]) for c in lesson["chapters"]] == [
        ("", 2, 100),
        ("ลองเล่นเอง", 2, 100),
    ]
    # count-in 2.4 + two chapters of 2 bars at 100 BPM (4.8 each) + 1.5 tail
    assert lesson["length_s"] == pytest.approx(13.5)


def test_the_list_has_the_new_lesson_with_its_length_and_no_renders(client):
    lesson = new_lesson(client)

    rows = client.get(LESSONS).json()

    assert rows == [
        {
            "id": lesson["id"],
            "title": "SMELLS LIKE TEEN SPIRIT",
            "length_s": pytest.approx(13.5),
            "renders": 0,
            "updated_at": lesson["updated_at"],
        }
    ]


def test_the_list_puts_the_latest_change_first(client, monkeypatch):
    # `updated_at` counts whole seconds: three writes in one second tied, and the list fell back
    # to the random ids, so this failed now and then. A clock that steps one each call keeps them apart.
    times = iter(f"2026-11-13T10:00:{second:02d}+07:00" for second in range(60))
    monkeypatch.setattr(lessons, "now_iso", lambda: next(times))
    first = new_lesson(client, "หนึ่ง")
    second = new_lesson(client, "สอง")
    assert put(client, first, title="หนึ่ง แก้แล้ว").status_code == 200

    assert [row["id"] for row in client.get(LESSONS).json()] == [first["id"], second["id"]]


def test_a_title_left_empty_or_too_long_is_refused(client):
    for title in ("", "  ", "ก" * 41):
        response = client.post(LESSONS, json={"title": title})
        assert (response.status_code, response.json()["code"], response.json()["field"]) == (
            400,
            "invalid_request",
            "title",
        )
    assert client.get(LESSONS).json() == []


def test_a_title_of_forty_thai_letters_is_kept(client):
    assert new_lesson(client, "ก" * 40)["title"] == "ก" * 40


def test_get_answers_the_whole_lesson(client):
    lesson = new_lesson(client)

    assert client.get(f"{LESSONS}/{lesson['id']}").json() == lesson


# --- PUT ---


def test_put_replaces_the_lesson_and_answers_it_with_its_length(client, project):
    lesson = new_lesson(client)
    changes = {
        "title": "FILL",
        "subtitle": "Nirvana · how to play the intro fill",
        "caption": "Wait for the snare roll",
        "bpm": 120,
        "groove": groove(note("snare", 0, "R", "flam"), note("kick", 0, None, "accent"), bars=2),
        "chapters": [chapter(label="KICK", text="On 1e", focus=["kick"], repeats=2, speed=75)],
    }

    response = put(client, lesson, **changes)

    assert response.status_code == 200
    saved = response.json()
    assert {key: saved[key] for key in changes} == changes
    # count-in 4 × 60 / 90 + 2 × 2 bars × 4 × 60 / 90 + 1.5
    assert saved["length_s"] == pytest.approx(8 / 3 + 32 / 3 + 1.5)
    stored = json.loads(lesson_file(project, lesson["id"]).read_text(encoding="utf-8"))
    assert (stored["version"], stored["id"], stored["bpm"]) == (1, lesson["id"], 120)
    assert "length_s" not in stored


def test_a_lesson_over_ninety_seconds_is_saved_but_not_listened_to(client):
    lesson = new_lesson(client)

    response = put(client, lesson, bpm=40, chapters=[chapter(repeats=8, speed=50)] * 2)

    assert response.status_code == 200
    assert response.json()["length_s"] > 90
    refused = client.post(f"{LESSONS}/{lesson['id']}/listen", json={})
    assert (refused.status_code, refused.json()["code"]) == (422, "too_long")


@pytest.mark.parametrize(
    "notes, field",
    [
        # one hand on two pieces
        ([note("snare", 4, "L"), note("tom_high", 4, "L")], "groove.notes[1]"),
        # three hand notes
        ([note("snare", 4, "L"), note("crash", 4, "R"), note("ride", 4, "R")], "groove.notes[2]"),
        # open and closed hi-hat together
        ([note("hihat_closed", 4, "R"), note("hihat_open", 4, "L")], "groove.notes[1]"),
        # a flam on a foot
        ([note("kick", 4, None, "flam")], "groove.notes[0]"),
        # a flam beside the other hand's note
        ([note("snare", 4, "L", "flam"), note("crash", 4, "R")], "groove.notes[1]"),
        # past the last bar
        ([note("snare", 16, "L")], "groove.notes[0]"),
        # the same piece twice in one step
        ([note("snare", 4, "L"), note("snare", 4, "R")], "groove.notes[1]"),
        # a hand on a foot, no hand on a hand piece
        ([note("kick", 4, "R")], "groove.notes[0]"),
        ([note("snare", 4, None)], "groove.notes[0]"),
        ([note("cowbell", 4, "R")], "groove.notes[0]"),
    ],
)
def test_a_groove_no_drummer_can_play_is_refused_and_nothing_changes(client, project, notes, field):
    lesson = new_lesson(client)
    before = lesson_file(project, lesson["id"]).read_bytes()

    response = put(client, lesson, groove=groove(*notes))

    assert (response.status_code, response.json()["code"], response.json()["field"]) == (
        400,
        "invalid_request",
        field,
    )
    assert lesson_file(project, lesson["id"]).read_bytes() == before


def test_two_hands_on_two_pieces_and_both_feet_share_a_step(client):
    lesson = new_lesson(client)
    notes = [note("snare", 4, "L"), note("crash", 4, "R"), note("kick", 4, None), note("hihat_pedal", 4, None)]

    assert put(client, lesson, groove=groove(*notes)).status_code == 200


@pytest.mark.parametrize(
    "changes, field",
    [
        ({"bpm": 39}, "bpm"),
        ({"bpm": 241}, "bpm"),
        ({"bpm": 100.5}, "bpm"),
        ({"bpm": True}, "bpm"),
        ({"title": "ก" * 41}, "title"),
        ({"subtitle": "ก" * 61}, "subtitle"),
        ({"caption": "ก" * 61}, "caption"),
        ({"background": "video"}, "background"),
        ({"background": "image"}, "background"),  # no background.jpg yet
        ({"groove": groove(bars=5)}, "groove.bars"),
        ({"groove": {"bars": 1, "notes": "x"}}, "groove.notes"),
        ({"chapters": []}, "chapters"),
        ({"chapters": [chapter()] * 7}, "chapters"),
        ({"chapters": [chapter(speed=72)]}, "chapters[0].speed"),
        ({"chapters": [chapter(speed=45)]}, "chapters[0].speed"),
        ({"chapters": [chapter(), chapter(repeats=9)]}, "chapters[1].repeats"),
        ({"chapters": [chapter(label="ก" * 17)]}, "chapters[0].label"),
        ({"chapters": [chapter(text="ก" * 61)]}, "chapters[0].text"),
        ({"chapters": [chapter(focus=["kick", "kick"])]}, "chapters[0].focus"),
        ({"chapters": [chapter(focus=["cowbell"])]}, "chapters[0].focus"),
    ],
)
def test_a_value_outside_the_rules_is_refused_with_its_field(client, project, changes, field):
    lesson = new_lesson(client)
    before = lesson_file(project, lesson["id"]).read_bytes()

    response = put(client, lesson, **changes)

    assert (response.status_code, response.json()["code"], response.json()["field"]) == (
        400,
        "invalid_request",
        field,
    )
    assert lesson_file(project, lesson["id"]).read_bytes() == before


def test_a_groove_with_no_notes_is_saved(client):
    lesson = new_lesson(client)

    assert put(client, lesson, groove=groove()).status_code == 200


# --- The id in the path ---


@pytest.mark.parametrize("bad_id", ["..", "%2E%2E", "K3V9X0A1B2C4", "k3v9x0a1b2c", "k3v9x0a1b2c4d"])
def test_an_id_that_is_not_a_lesson_s_is_not_found_and_nothing_goes(client, project, bad_id):
    lesson = new_lesson(client)
    before = sorted(project.drums_dir.rglob("*"))

    for method, path in (
        ("GET", f"{LESSONS}/{bad_id}"),
        ("PUT", f"{LESSONS}/{bad_id}"),
        ("DELETE", f"{LESSONS}/{bad_id}"),
        ("POST", f"{LESSONS}/{bad_id}/copy"),
        ("POST", f"{LESSONS}/{bad_id}/listen"),
    ):
        response = client.request(method, path, json=body_of(lesson) if method == "PUT" else {})
        assert (response.status_code, response.json()["code"]) == (404, "not_found"), (method, path)
    assert sorted(project.drums_dir.rglob("*")) == before


def test_an_unknown_id_of_the_right_shape_is_not_found(client):
    assert client.get(f"{LESSONS}/k3v9x0a1b2c4").status_code == 404


# --- Copy and delete ---


def test_a_copy_gets_a_new_id_and_its_title_ends_with_copy_cut_at_forty(client, project):
    lesson = new_lesson(client, "ก" * 38)
    renders = project.lessons_dir / lesson["id"] / "renders"
    renders.mkdir()
    for suffix in (".mp4", ".srt", ".json"):
        (renders / f"20261113-103000{suffix}").write_text("x", encoding="utf-8")

    response = client.post(f"{LESSONS}/{lesson['id']}/copy", json={})

    assert response.status_code == 201
    copy = response.json()
    assert copy["id"] != lesson["id"]
    assert copy["title"] == "ก" * 38 + " ("
    assert copy["groove"] == lesson["groove"]
    rows = {row["id"]: row["renders"] for row in client.get(LESSONS).json()}
    assert rows == {lesson["id"]: 1, copy["id"]: 0}


def test_a_short_title_gets_the_whole_copy_suffix(client):
    lesson = new_lesson(client, "FILL")

    assert client.post(f"{LESSONS}/{lesson['id']}/copy", json={}).json()["title"] == "FILL (สำเนา)"


def test_delete_removes_the_lesson_s_folder(client, project):
    lesson = new_lesson(client)
    renders = project.lessons_dir / lesson["id"] / "renders"
    renders.mkdir()
    for suffix in (".mp4", ".srt", ".json"):
        (renders / f"20261113-103000{suffix}").write_text("x", encoding="utf-8")

    response = client.delete(f"{LESSONS}/{lesson['id']}")

    assert response.status_code == 204
    assert not (project.lessons_dir / lesson["id"]).exists()
    assert client.get(LESSONS).json() == []


def test_a_render_held_open_stops_the_delete_with_in_use_and_the_lesson_stays(client, project, monkeypatch):
    lesson = new_lesson(client)
    renders = project.lessons_dir / lesson["id"] / "renders"
    renders.mkdir()
    for suffix in (".mp4", ".srt", ".json"):
        (renders / f"20261113-103000{suffix}").write_text("x", encoding="utf-8")
    held = renders / "20261113-103000.mp4"
    unlink = type(held).unlink

    def windows_unlink(path, missing_ok=False):
        if path == held:
            raise PermissionError("in use")
        unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(type(held), "unlink", windows_unlink)

    response = client.delete(f"{LESSONS}/{lesson['id']}")

    assert (response.status_code, response.json()["code"]) == (409, "in_use")
    assert lesson_file(project, lesson["id"]).is_file()


def test_a_lesson_json_that_cant_be_read_is_left_out_of_the_list_but_can_be_deleted(client, project, caplog):
    broken = new_lesson(client, "เสีย")
    kept = new_lesson(client, "ดี")
    lesson_file(project, broken["id"]).write_text("{not json", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        rows = client.get(LESSONS).json()

    assert [row["id"] for row in rows] == [kept["id"]]
    assert broken["id"] in caplog.text
    assert client.delete(f"{LESSONS}/{broken['id']}").status_code == 204
    assert not (project.lessons_dir / broken["id"]).exists()


def test_a_body_that_is_not_json_is_refused(client):
    response = client.post(LESSONS, content=b"title=x", headers={"content-type": "application/x-www-form-urlencoded"})

    assert response.status_code == 415


# --- The background picture ---


def check_picture(client, lesson_id: str, size: int):
    return client.post(f"{LESSONS}/{lesson_id}/background/check", json={"size": size})


def turned_jpeg(image: Image.Image) -> bytes:
    """`image` as a JPEG whose EXIF says "turn 90° clockwise to show", as a phone writes a portrait photo."""
    exif = Image.Exif()
    exif[0x0112] = 6  # Orientation
    out = io.BytesIO()
    image.save(out, "JPEG", exif=exif)
    return out.getvalue()


def background_of(project: ProjectPaths, lesson_id: str):
    return project.lessons_dir / lesson_id / lessons.BACKGROUND


def test_a_png_becomes_a_1080x1920_jpg_and_the_lesson_s_background_an_image(client, project):
    lesson = new_lesson(client)

    response = put_background(client, lesson["id"], png(800, 600))

    assert response.status_code == 200
    assert response.json()["background"] == "image"
    assert response.json()["updated_at"] >= lesson["updated_at"]
    with Image.open(background_of(project, lesson["id"])) as stored:
        assert (stored.format, stored.size) == ("JPEG", (1080, 1920))
    assert json.loads(lesson_file(project, lesson["id"]).read_text(encoding="utf-8"))["background"] == "image"
    served = client.get(f"{LESSONS}/{lesson['id']}/background.jpg")
    assert (served.status_code, served.headers["content-type"]) == (200, "image/jpeg")
    assert list((project.drums_partial_dir).iterdir()) == []


def test_a_photo_is_turned_the_way_its_exif_says_before_the_crop(client, project):
    lesson = new_lesson(client)
    # Stored 2000×1000 with a white band along its top, shown 1000×2000 with the band down the
    # right edge. Cropped unturned, the band would run across the top instead.
    stored = Image.new("RGB", (2000, 1000), "gray")
    stored.paste("white", (0, 0, 2000, 120))

    assert put_background(client, lesson["id"], turned_jpeg(stored)).status_code == 200

    with Image.open(background_of(project, lesson["id"])) as picture:
        right, left = picture.getpixel((1070, 960)), picture.getpixel((10, 960))
    assert sum(right) > 600 and sum(left) < 600


def test_a_text_file_is_unsupported_image_and_nothing_changes(client, project):
    lesson = new_lesson(client)

    response = put_background(client, lesson["id"], b"just some text\n")

    assert (response.status_code, response.json()["code"]) == (415, "unsupported_image")
    assert not background_of(project, lesson["id"]).exists()
    assert client.get(f"{LESSONS}/{lesson['id']}").json()["background"] == "color"
    assert list((project.drums_partial_dir).iterdir()) == []


def test_a_picture_over_20_mb_is_file_too_large_at_the_check_and_at_the_put(client):
    lesson = new_lesson(client)
    over = backgrounds.MAX_BYTES + 1

    checked = check_picture(client, lesson["id"], over)
    # A one-byte body that says it is over: the size is refused before any body is read.
    sent = put_background(client, lesson["id"], b"x", size=over)

    assert (checked.status_code, checked.json()["code"]) == (413, "file_too_large")
    assert (sent.status_code, sent.json()["code"]) == (413, "file_too_large")
    assert check_picture(client, lesson["id"], 1000).json() == {"size": 1000}


def test_a_body_that_is_not_octet_stream_is_refused_as_adr_0028_says(client):
    lesson = new_lesson(client)

    multipart = client.put(f"{LESSONS}/{lesson['id']}/background?size=3", files={"file": ("a.png", b"png")})
    as_json = put_background(client, lesson["id"], b'{"a": 1}', content_type="application/json")

    assert (multipart.status_code, multipart.json()["code"]) == (415, "unsupported_media_type")
    assert (as_json.status_code, as_json.json()["code"]) == (415, "unsupported_media_type")


def test_a_body_longer_than_its_size_is_size_mismatch(client, project):
    lesson = new_lesson(client)
    body = png(64, 64)

    response = put_background(client, lesson["id"], body, size=len(body) - 1)

    assert (response.status_code, response.json()["code"]) == (400, "size_mismatch")
    assert not background_of(project, lesson["id"]).exists()


def test_deleting_the_picture_goes_back_to_the_app_s_colours(client, project):
    lesson = new_lesson(client)
    put_background(client, lesson["id"], png(64, 64))

    response = client.delete(f"{LESSONS}/{lesson['id']}/background")

    assert response.status_code == 200
    assert response.json()["background"] == "color"
    assert not background_of(project, lesson["id"]).exists()
    assert client.get(f"{LESSONS}/{lesson['id']}/background.jpg").status_code == 404
    assert client.delete(f"{LESSONS}/{lesson['id']}/background").status_code == 200  # nothing left to remove


def test_a_put_of_image_after_the_picture_went_is_invalid_with_its_field(client):
    lesson = new_lesson(client)
    put_background(client, lesson["id"], png(64, 64))
    client.delete(f"{LESSONS}/{lesson['id']}/background")

    response = put(client, lesson, background="image")

    assert (response.status_code, response.json()["code"], response.json()["field"]) == (400, "invalid_request", "background")


def test_a_put_keeps_the_picture_while_it_says_image(client, project):
    lesson = put_background(client, new_lesson(client)["id"], png(64, 64)).json()

    response = put(client, lesson, title="NEW", background="image")

    assert response.status_code == 200
    assert background_of(project, lesson["id"]).is_file()


def test_a_copy_of_a_lesson_with_a_picture_has_the_picture_too(client, project):
    lesson = new_lesson(client)
    put_background(client, lesson["id"], png(64, 64))

    copy = client.post(f"{LESSONS}/{lesson['id']}/copy", json={}).json()

    assert copy["background"] == "image"
    assert background_of(project, copy["id"]).read_bytes() == background_of(project, lesson["id"]).read_bytes()


@pytest.mark.parametrize(
    "send",
    [
        lambda client, lesson_id: put_background(client, lesson_id, png(64, 64)),
        lambda client, lesson_id: check_picture(client, lesson_id, 1000),
        lambda client, lesson_id: client.delete(f"{LESSONS}/{lesson_id}/background"),
        lambda client, lesson_id: client.get(f"{LESSONS}/{lesson_id}/background.jpg"),
    ],
    ids=["put", "check", "delete", "get"],
)
def test_every_picture_route_of_a_lesson_that_isn_t_there_is_not_found(client, send):
    assert send(client, "abcdefabcdef").status_code == 404
    assert send(client, "..").status_code == 404


def test_a_start_removes_an_upload_never_received_in_full(client, project):
    lesson = new_lesson(client)
    leftover = project.drums_partial_dir / f"{lesson['id']}.0a1b2c3d.tmp"
    leftover.parent.mkdir(parents=True)
    leftover.write_bytes(b"half a picture")

    restart(client)

    assert not leftover.exists()


# --- ฟังจังหวะ ---


def listen(client, lesson: dict):
    return client.post(f"{LESSONS}/{lesson['id']}/listen", json={})


def test_listen_answers_a_wav_as_long_as_the_lesson_and_never_cached(client):
    lesson = new_lesson(client)

    response = listen(client, lesson)

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["cache-control"] == "no-store"
    info = soundfile.info(io.BytesIO(response.content))
    assert (info.samplerate, info.channels, info.subtype) == (44100, 2, "PCM_16")
    assert info.frames == round(13.5 * 44100)


def test_listen_starts_with_the_count_in_on_the_beat(client):
    lesson = new_lesson(client)
    put(client, lesson, bpm=120, groove=groove(), chapters=[chapter(speed=50)])

    audio, rate = soundfile.read(io.BytesIO(listen(client, lesson).content), dtype="float32")

    loud = np.flatnonzero(np.abs(audio[:, 0]) > 0.5)
    # four soft hi-hats at 60 BPM, then the empty groove is silent
    assert list(loud) == [0, 44100, 88200, 132300]


def test_listen_without_the_drum_samples_is_not_ready(client, project):
    lesson = new_lesson(client)
    project.drum_kit_marker.unlink()

    response = listen(client, lesson)

    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (
        503,
        "not_ready",
        ["drum_kit"],
    )
