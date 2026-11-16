"""A song's reel cover played on the kalimba, under /api/songs/{id}/cover (kalimba-cover seam 1; D1, D2,
D4, D9, D12, D14): the instrument and the kalimba's sound in `cover.json`, the arrangement's counts,
and ฟัง through `kalimba_cover.sound`, with analyses written straight to disk."""

import io
import json

import numpy as np
import pytest
import soundfile
from fastapi.testclient import TestClient

from backend import paths
from backend.app import app
from backend.drum_cover import cover
from backend.drum_notes import songs
from backend.paths import ProjectPaths

from .fakes import song_m4a, written_song

SONGS = "/api/songs"
DOWNBEATS = (10.0, 12.0, 14.0, 16.0)  # the picked range 10–16, bars 2.0 s long
CLIP_S = 6.0 + 1.5
# A melody of the stretch: C5 B4 A4 F4 every half second from 11.0, then an F#4 bent to F4; no key holds more than four.
MELODY = [(11.0, 72, "normal"), (11.5, 71, "normal"), (12.0, 69, "accent"), (12.5, 65, "normal"), (13.0, 66, "normal")]
KALIMBA = {"on": True, "volume": 100}
COVER_KEYS = ("start_s", "end_s", "title", "subtitle", "caption", "background", "drums", "backing", "instrument", "kalimba")


@pytest.fixture
def project(fake_root, monkeypatch) -> ProjectPaths:
    monkeypatch.setattr(paths, "ROOT", fake_root)
    return ProjectPaths(fake_root)


@pytest.fixture
def client(project) -> TestClient:
    return TestClient(app, base_url="http://127.0.0.1")


def picked(project: ProjectPaths, hits=((11.0, "snare", "normal"),), notes=MELODY, **fields) -> str:
    return written_song(project, downbeats=DOWNBEATS, hits=list(hits), start_s=10.0, notes=notes, **fields)


def got(client, song_id: str) -> dict:
    return client.get(f"{SONGS}/{song_id}/cover").json()


def put_cover(client, song_id: str, **changes):
    stored = got(client, song_id)
    return client.put(f"{SONGS}/{song_id}/cover", json={key: stored[key] for key in COVER_KEYS} | changes)


def listen(client, song_id: str):
    return client.post(f"{SONGS}/{song_id}/cover/listen", json={})


def wav_of(response) -> np.ndarray:
    sound, rate = soundfile.read(io.BytesIO(response.content), dtype="int16")
    assert rate == 44_100
    return sound


# --- the cover ---


def test_a_song_with_hits_opens_on_the_drums_and_counts_the_kalimba_s_notes_of_the_stretch(client, project):
    body = got(client, picked(project))

    assert (body["instrument"], body["kalimba"]) == ("drums", KALIMBA)
    assert (body["notes"], body["notes_picked"], body["transpose"], body["dropped"], body["bent"]) == (5, True, 0, 0, 1)


def test_a_stretch_with_notes_but_no_hit_opens_on_the_kalimba(client, project):
    body = got(client, picked(project, hits=()))

    assert (body["instrument"], body["hits"], body["notes"]) == ("kalimba", 0, 5)


def test_a_song_picked_before_notes_were_kept_opens_on_the_drums_and_says_so(client, project):
    body = got(client, picked(project, hits=(), notes=None))

    assert (body["instrument"], body["notes_picked"], body["notes"], body["transpose"]) == ("drums", False, 0, 0)


def test_a_cover_written_before_the_kalimba_reads_as_the_drums_and_a_full_kalimba(client, project):
    song_id = picked(project, hits=())
    stored = {"version": 1, "updated_at": "2026-11-15T00:00:00Z", "start_s": 10.0, "end_s": 16.0, "title": "Yellow",
              "subtitle": "", "caption": "", "background": "color", "backing": {"on": False, "volume": 35}}  # fmt: skip
    (project.song_dir(song_id) / cover.COVER_FILE).write_text(json.dumps(stored), encoding="utf-8")

    body = got(client, song_id)
    assert (body["saved"], body["instrument"], body["kalimba"], body["drums"]) == (True, "drums", KALIMBA, {"on": True, "volume": 100})


def test_a_put_needs_the_instrument_and_the_kalimba_and_refuses_a_bad_one_by_name(client, project):
    song_id = picked(project)

    for field, change in [
        ("instrument", {"instrument": "piano"}),
        ("kalimba.on", {"kalimba": None}),
        ("kalimba.volume", {"kalimba": {"on": True, "volume": 5}}),
        ("kalimba.on", {"instrument": "kalimba", "kalimba": {"on": False, "volume": 100}}),
    ]:
        response = put_cover(client, song_id, **change)
        assert (response.status_code, response.json().get("field")) == (400, field), change
    response = put_cover(client, song_id, instrument="kalimba", kalimba={"on": False, "volume": 100})
    assert response.json()["message"] == "เปิดเสียงคาลิมบาหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง"

    response = put_cover(client, song_id, instrument="kalimba", drums={"on": False, "volume": 100}, kalimba={"on": True, "volume": 60})
    assert response.status_code == 200, response.json()
    assert (response.json()["instrument"], response.json()["kalimba"]) == ("kalimba", {"on": True, "volume": 60})
    assert got(client, song_id)["instrument"] == "kalimba"


def test_without_the_body_s_instrument_key_the_put_is_refused(client, project):
    song_id = picked(project)
    stored = got(client, song_id)
    body = {key: stored[key] for key in COVER_KEYS if key != "instrument"}

    response = client.put(f"{SONGS}/{song_id}/cover", json=body)
    assert (response.status_code, response.json()["field"]) == (400, "instrument")


# --- listen ---


def test_listen_on_the_kalimba_is_the_stretch_and_the_tail_the_same_bytes_every_time(client, project):
    song_id = picked(project)
    assert put_cover(client, song_id, instrument="kalimba").status_code == 200

    first, second = listen(client, song_id), listen(client, song_id)

    assert first.status_code == 200 and first.headers["cache-control"] == "no-store"
    assert first.content == second.content
    sound = wav_of(first)
    assert len(sound) / 44_100 == pytest.approx(CLIP_S, abs=0.05)
    assert np.abs(sound[: 44_100 - 100]).max() == 0  # the first note comes at 1.0 s
    assert np.abs(sound[44_100 : 44_100 + 4410]).max() > 1000


def test_the_kalimba_at_half_volume_is_six_db_down(client, project):
    song_id = picked(project)
    assert put_cover(client, song_id, instrument="kalimba").status_code == 200
    full = wav_of(listen(client, song_id))

    assert put_cover(client, song_id, kalimba={"on": True, "volume": 50}).status_code == 200
    half = wav_of(listen(client, song_id))

    peaks = [np.abs(sound.astype(np.int32)).max() for sound in (full, half)]
    assert 20 * np.log10(peaks[1] / peaks[0]) == pytest.approx(-6.0, abs=0.1)


def test_the_kalimba_needs_no_drum_samples_and_off_under_backing_plays_the_song_alone(client, project):
    song_id = picked(project, audio=song_m4a(40.0))
    project.drum_kit_marker.unlink()
    assert put_cover(client, song_id, instrument="kalimba").status_code == 200

    assert listen(client, song_id).status_code == 200

    assert put_cover(client, song_id, kalimba={"on": False, "volume": 100}, backing={"on": True, "volume": 60}).status_code == 200
    sound = wav_of(listen(client, song_id))
    assert np.abs(sound[: 44_100 - 100]).max() > 1000  # the song, before the first note


def test_a_kalimba_stretch_with_no_notes_is_refused(client, project):
    song_id = picked(project, notes=[(10.5, 36, "normal")])  # the bass alone, dropped (D14)
    assert put_cover(client, song_id, instrument="kalimba").status_code == 200

    response = listen(client, song_id)
    assert (response.status_code, response.json()["code"]) == (409, "no_notes")
    assert response.json()["message"] == "ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง"


def test_a_kalimba_song_picked_before_notes_were_kept_says_to_pick_it_again_or_import_it_again(client, project):
    song_id = picked(project, notes=None)
    assert put_cover(client, song_id, instrument="kalimba").status_code == 200

    response = listen(client, song_id)
    assert (response.status_code, response.json()["code"]) == (409, "no_notes")
    assert response.json()["message"] == "เพลงนี้แกะก่อนมีคาลิมบา แกะใหม่ที่หน้าเพลงเพื่อได้โน้ตทำนอง"

    stored = project.song_dir(song_id) / songs.SONG_FILE
    text = json.loads(stored.read_text(encoding="utf-8"))
    text["source"] = {"kind": "midi", "name": "song.mid", "size": 1}
    stored.write_text(json.dumps(text), encoding="utf-8")
    assert listen(client, song_id).json()["message"] == "เพลงนี้นำเข้าก่อนมีคาลิมบา นำเข้าไฟล์ MIDI เดิมอีกครั้ง"


# --- render ---


def test_a_kalimba_reel_isn_t_rendered_yet(client, project):
    song_id = picked(project)
    assert put_cover(client, song_id, instrument="kalimba", drums={"on": False, "volume": 100}).status_code == 200

    response = client.post(f"{SONGS}/{song_id}/cover/render", json={})
    assert (response.status_code, response.json()["code"]) == (409, "not_ready")
    assert response.json()["message"] == "render reel คาลิมบายังไม่พร้อม"
