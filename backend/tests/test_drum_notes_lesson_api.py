"""A lesson from a song under /api/songs: `POST /preview`, `POST /listen` and `POST /lessons`, and
the song's `lessons` (drum-notes seam 1 › preview, listen, lessons; D11, D12, D13, D21; ADR 0047).
A MIDI song has its analysis the moment it comes in, so no model stands in here."""

import io
import json

import pytest
import soundfile
from fastapi.testclient import TestClient

from backend import checks, paths
from backend.app import app
from backend.drum_notes import songs
from backend.drum_notes.songs import Analysis, Head, Hit, Source
from backend.paths import ProjectPaths
from backend.video_gen import lessons, timeline

from .fakes import BEAT, ROCK, SONGS, import_song_tone, midi_file, ok_ffmpeg, put_song_file, song_refusal

LESSONS = "/api/drums/lessons"
# MIDI notes are `(tick, GM number, velocity)`: 36 kick, 38 snare, 42 closed hi-hat, 49 crash (`midi.GM_PIECES`).
# ROCK again a bar later, then a crash and a kick on the third bar's first beat: three bars at 100 BPM (2.4 s each).
THREE_BARS = ROCK + [(t + 4 * BEAT, n, v) for t, n, v in ROCK] + [(8 * BEAT, 49, 110), (8 * BEAT, 36, 110)]


@pytest.fixture
def project(fake_root, monkeypatch) -> ProjectPaths:
    monkeypatch.setattr(paths, "ROOT", fake_root)
    return ProjectPaths(fake_root)


@pytest.fixture
def client(project, monkeypatch) -> TestClient:
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    return TestClient(app, base_url="http://127.0.0.1")


def midi_song(client, notes=THREE_BARS, name: str = "Smells Like Teen Spirit.mid", **fields) -> dict:
    response = put_song_file(client, name, midi_file(notes, bpm=100, **fields))
    assert response.status_code == 201, response.json()
    return response.json()


def preview(client, song_id: str, **body):
    return client.post(f"{SONGS}/{song_id}/preview", json=body)


def written_song(project: ProjectPaths, subtitle: str = "", downbeats: tuple[float, ...] = (0.0, 2.0, 4.0, 6.0), mode: str = "drums") -> str:
    """A picked audio song written as the Pick job leaves it: beats every 0.5 s and, in drums mode, a
    kick on every downbeat, in melody mode two snares a beat apart from the second beat of every bar
    (D14); `downbeats` decide the bars found, so one 1.5 s apart makes a 3-beat bar (D20)."""
    beats = [t / 2 for t in range(int(downbeats[-1] * 2) + 1)]
    if mode == "melody":
        hits = [Hit(t=t + after, piece="snare", level="normal") for t in downbeats[:-1] for after in (0.5, 1.0)]
    else:
        hits = [Hit(t=t, piece="kick", level="normal") for t in downbeats[:-1]]
    analysis = Analysis(mode=mode, start_s=0.0, end_s=downbeats[-1], beats=beats, downbeats=list(downbeats), hits=hits, picked_at="2026-11-14T00:00:00Z")
    song = songs.new_song("writtensong0", Head("Teen Spirit", subtitle, Source(kind="file", name="song.mp3", size=1)), downbeats[-1] + 1, songs.default_range(downbeats[-1] + 1), analysis)
    return songs.write_new(project, song).id


def placed(groove: dict) -> list[tuple[str, int, str | None]]:
    return sorted((note["piece"], note["step"], note["hand"]) for note in groove["notes"])


# --- preview ---


def test_preview_gives_the_groove_of_the_bars_picked_with_hands_and_the_bpm_of_their_length(client):
    song = midi_song(client)
    assert [bar["four_four"] for bar in song["bars"]] == [True, True, True]

    response = preview(client, song["id"], bar=0, bars=2)

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["bpm"] == 100
    assert body["groove"]["bars"] == 2
    assert placed(body["groove"]) == [
        ("hihat_closed", 0, "R"), ("hihat_closed", 4, "R"), ("hihat_closed", 8, "R"), ("hihat_closed", 12, "R"),
        ("hihat_closed", 16, "R"), ("hihat_closed", 20, "R"), ("hihat_closed", 24, "R"), ("hihat_closed", 28, "R"),
        ("kick", 0, None), ("kick", 16, None),
        ("snare", 8, "L"), ("snare", 24, "L"),
    ]  # fmt: skip
    assert {note["hit"] for note in body["groove"]["notes"]} == {"accent"}  # velocity 110 (D22)
    assert body["dropped"] == []


def test_preview_from_the_second_bar_takes_the_given_bpm_and_lists_what_it_dropped(client):
    song = midi_song(client, THREE_BARS + [(8 * BEAT, 38, 110), (8 * BEAT, 42, 110)])  # the third bar's first step: crash, snare, hi-hat and kick

    response = preview(client, song["id"], bar=2, bars=1, bpm=95)

    assert response.status_code == 200, response.json()
    assert response.json()["bpm"] == 95
    assert placed(response.json()["groove"]) == [("crash", 0, "R"), ("kick", 0, None), ("snare", 0, "L")]
    assert response.json()["dropped"] == [{"piece": "hihat_closed", "step": 0}]


def test_a_bar_that_is_not_4_4_or_a_pick_past_the_last_bar_is_refused_at_the_bar_field(client):
    song = midi_song(client)

    past = preview(client, song["id"], bar=2, bars=2)
    assert song_refusal(past) == (400, "invalid_request")
    assert (past.json()["field"], past.json()["message"]) == ("bar", "ห้องนี้ไม่ใช่ 4/4")
    assert song_refusal(preview(client, song["id"], bar=3, bars=1)) == (400, "invalid_request")
    assert song_refusal(preview(client, song["id"], bar=-1, bars=1)) == (400, "invalid_request")


def test_a_found_bar_of_three_beats_is_not_4_4_and_cannot_be_chosen_while_its_neighbours_can(client, project):
    song_id = written_song(project, downbeats=(0.0, 2.0, 3.5, 5.5))  # the second bar is 1.5 s: three beats
    assert [bar["four_four"] for bar in client.get(f"{SONGS}/{song_id}").json()["bars"]] == [True, False, True]

    refused = preview(client, song_id, bar=1, bars=1)
    assert song_refusal(refused) == (400, "invalid_request")
    assert refused.json()["field"] == "bar"
    assert song_refusal(preview(client, song_id, bar=0, bars=2)) == (400, "invalid_request")
    assert preview(client, song_id, bar=0, bars=1).status_code == 200
    assert preview(client, song_id, bar=2, bars=1).status_code == 200


def test_a_bars_count_outside_1_to_4_and_a_bpm_outside_40_to_240_are_refused_at_their_fields(client):
    song = midi_song(client)

    assert preview(client, song["id"], bar=0, bars=0).json()["field"] == "bars"
    assert preview(client, song["id"], bar=0, bars=5).json()["field"] == "bars"
    assert preview(client, song["id"], bar=0, bars=1, bpm=30).json()["field"] == "bpm"
    assert preview(client, song["id"], bar=0, bars=1, bpm=100.5).json()["field"] == "bpm"
    assert song_refusal(preview(client, song["id"], bar="0", bars=1)) == (400, "invalid_request")


def test_a_song_not_picked_yet_has_no_analysis_and_no_song_is_not_found(client, tmp_path):
    song = import_song_tone(client, tmp_path, seconds=12)

    assert song_refusal(preview(client, song["id"], bar=0, bars=1)) == (409, "no_analysis")
    assert song_refusal(preview(client, "nosuchsong00", bar=0, bars=1)) == (404, "not_found")


def test_a_melody_song_s_preview_puts_its_onsets_on_the_snare_over_the_app_s_kick_on_1_and_3_and_8th_hihats_with_the_hihat_right(client, project):
    song_id = written_song(project, mode="melody")

    response = preview(client, song_id, bar=0, bars=2)

    assert response.status_code == 200, response.json()
    groove = response.json()["groove"]
    base = [("kick", s, None) for s in (0, 8, 16, 24)] + [("hihat_closed", s, "R") for s in range(0, 32, 2)]
    assert placed(groove) == sorted(base + [("snare", 4, "L"), ("snare", 8, "L"), ("snare", 20, "L"), ("snare", 24, "L")])
    assert (response.json()["bpm"], response.json()["dropped"]) == (120, [])


def test_a_lesson_from_a_melody_song_has_the_three_pieces_in_its_groove_and_listen_plays_all_three(client, project):
    song_id = written_song(project, mode="melody")

    created = client.post(f"{SONGS}/{song_id}/lessons", json={"bar": 1, "bars": 1, "bpm": 120})
    heard = client.post(f"{SONGS}/{song_id}/listen", json={"bar": 1, "bars": 1, "bpm": 120})

    assert created.status_code == 201, created.json()
    lesson = lessons.Lesson.model_validate_json((lessons.lesson_dir(project, created.json()["lesson_id"]) / "lesson.json").read_bytes())
    assert {note.piece for note in lesson.groove.notes} == {"kick", "snare", "hihat_closed"}
    assert {hit.piece for hit in timeline.build(lesson).hits if hit.note != "count"} == {"kick", "snare", "hihat_closed"}
    assert (heard.status_code, heard.headers["Content-Type"]) == (200, "audio/wav")


# --- listen ---


def test_listen_answers_a_wav_as_long_as_the_unsaved_lesson_without_a_file_on_disk(client, project):
    song = midi_song(client)
    files_before = sorted(p for p in project.root.rglob("*") if p.is_file())

    response = client.post(f"{SONGS}/{song['id']}/listen", json={"bar": 0, "bars": 2, "bpm": 100})

    assert response.status_code == 200, response.text[:200]
    assert response.headers["Content-Type"] == "audio/wav"
    assert response.headers["Cache-Control"] == "no-store"
    info = soundfile.info(io.BytesIO(response.content))
    # A count-in bar and two chapters of two repeats of two bars at 100 BPM (2.4 s a bar), then the tail (D21).
    assert info.frames == round((2.4 + 8 * 2.4 + timeline.TAIL_S) * 44_100)
    assert sorted(p for p in project.root.rglob("*") if p.is_file()) == files_before


def test_listen_without_the_drum_kit_is_not_ready_and_a_bad_pick_is_refused_as_preview_is(client, project):
    song = midi_song(client)
    assert song_refusal(client.post(f"{SONGS}/{song['id']}/listen", json={"bar": 3, "bars": 1, "bpm": 100})) == (400, "invalid_request")
    assert song_refusal(client.post(f"{SONGS}/{song['id']}/listen", json={"bar": 0, "bars": 1})) == (400, "invalid_request")

    project.drum_kit_marker.unlink()

    response = client.post(f"{SONGS}/{song['id']}/listen", json={"bar": 0, "bars": 1, "bpm": 100})
    assert song_refusal(response) == (503, "not_ready")
    assert response.json()["rows"] == ["drum_kit"]


# --- lessons ---


def test_creating_a_lesson_writes_it_through_video_gen_with_the_song_s_title_and_the_defaults_and_the_song_lists_it(client, project):
    song = midi_song(client, name="Smells Like Teen Spirit — Nirvana (Official Music Video) 1991 remastered.mid")

    response = client.post(f"{SONGS}/{song['id']}/lessons", json={"bar": 0, "bars": 2, "bpm": 110})

    assert response.status_code == 201, response.json()
    lesson_id, dropped = response.json()["lesson_id"], response.json()["dropped"]
    assert dropped == 0
    lesson = client.get(f"{LESSONS}/{lesson_id}").json()
    assert lesson["title"] == "Smells Like Teen Spirit — Nirvana (Offic"  # the song's title cut at 40
    assert len(lesson["title"]) == 40
    assert (lesson["subtitle"], lesson["caption"], lesson["background"], lesson["bpm"]) == ("", "", "color", 110)
    assert lesson["groove"] == preview(client, song["id"], bar=0, bars=2, bpm=110).json()["groove"]
    assert [(c["label"], c["repeats"], c["speed"]) for c in lesson["chapters"]] == [("", 2, 100), ("ลองเล่นเอง", 2, 100)]
    on_disk = json.loads((lessons.lesson_dir(project, lesson_id) / "lesson.json").read_text(encoding="utf-8"))
    assert set(on_disk) == {"version", "id", "updated_at", "title", "subtitle", "caption", "bpm", "background", "groove", "chapters"}  # no new field (ADR 0047)
    assert client.get(f"{SONGS}/{song['id']}").json()["lessons"] == [lesson_id]
    assert client.get(SONGS).json()[0]["lessons"] == 1


def test_the_song_s_subtitle_becomes_the_lesson_s_second_line_cut_at_60(client, project):
    song_id = written_song(project, subtitle="Nirvana — Official Music Video, remastered in 1991 for the channel's 30th year")

    response = client.post(f"{SONGS}/{song_id}/lessons", json={"bar": 0, "bars": 1, "bpm": 120})

    assert response.status_code == 201, response.json()
    lesson = client.get(f"{LESSONS}/{response.json()['lesson_id']}").json()
    assert (lesson["title"], lesson["subtitle"]) == ("Teen Spirit", "Nirvana — Official Music Video, remastered in 1991 for the c")
    assert len(lesson["subtitle"]) == 60


def test_a_lesson_s_dropped_notes_are_counted_and_a_deleted_lesson_leaves_the_song_s_list_without_an_error(client):
    song = midi_song(client, THREE_BARS + [(8 * BEAT, 38, 110), (8 * BEAT, 42, 110)])
    first = client.post(f"{SONGS}/{song['id']}/lessons", json={"bar": 0, "bars": 1, "bpm": 100}).json()["lesson_id"]

    response = client.post(f"{SONGS}/{song['id']}/lessons", json={"bar": 2, "bars": 1, "bpm": 100})

    assert response.status_code == 201, response.json()
    assert response.json()["dropped"] == 1
    second = response.json()["lesson_id"]
    assert client.get(f"{SONGS}/{song['id']}").json()["lessons"] == [first, second]

    assert client.delete(f"{LESSONS}/{first}").status_code == 204
    assert client.get(f"{SONGS}/{song['id']}").json()["lessons"] == [second]


def test_deleting_the_song_keeps_its_lessons_and_a_refused_pick_makes_none(client, project):
    song = midi_song(client)
    lesson_id = client.post(f"{SONGS}/{song['id']}/lessons", json={"bar": 0, "bars": 2, "bpm": 100}).json()["lesson_id"]

    assert song_refusal(client.post(f"{SONGS}/{song['id']}/lessons", json={"bar": 3, "bars": 1, "bpm": 100})) == (400, "invalid_request")
    assert song_refusal(client.post(f"{SONGS}/{song['id']}/lessons", json={"bar": 0, "bars": 1})) == (400, "invalid_request")
    assert client.delete(f"{SONGS}/{song['id']}").status_code == 204

    assert client.get(f"{LESSONS}/{lesson_id}").status_code == 200
    assert [row["id"] for row in client.get(LESSONS).json()] == [lesson_id]
