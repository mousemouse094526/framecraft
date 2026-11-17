"""A song's reel cover played on the kalimba, under /api/songs/{id}/cover and /api/covers/render
(kalimba-cover seam 1; D1, D2, D4, D8, D9, D12, D14): the instrument and the kalimba's sound in
`cover.json`, the arrangement's counts, ฟัง through `kalimba_cover.sound`, and its Render job with
real ffmpeg, with analyses written straight to disk."""

import io
import json
import subprocess

import imageio_ffmpeg
import numpy as np
import pytest
import soundfile

from backend import ffmpeg, fonts, kalimba_kit
from backend.drum_cover import cover
from backend.drum_notes import songs
from backend.kalimba_cover import frames
from backend.paths import ProjectPaths

from .fakes import COVER_KEYS, FINISHED, cover_api, poll_until, song_m4a, write_kanit, written_song

SONGS = "/api/songs"
RENDER = "/api/covers/render"
DOWNBEATS = (10.0, 12.0, 14.0, 16.0)  # the picked range 10–16, bars 2.0 s long
CLIP_S = 6.0 + 1.5
# A melody of the stretch: C5 B4 A4 F4 every half second from 11.0, then an F#4 bent to F4; no key holds more than four.
MELODY = [(11.0, 72, "normal"), (11.5, 71, "normal"), (12.0, 69, "accent"), (12.5, 65, "normal"), (13.0, 66, "normal")]
KALIMBA = {"on": True, "volume": 100}
project, piped, client = cover_api()


def picked(project: ProjectPaths, hits=((11.0, "snare", "normal"),), notes=MELODY, **fields) -> str:
    return written_song(project, downbeats=DOWNBEATS, hits=list(hits), start_s=10.0, notes=notes, **fields)


def got(client, song_id: str) -> dict:
    return client.get(f"{SONGS}/{song_id}/cover").json()


def put_cover(client, song_id: str, **changes):
    stored = got(client, song_id)
    return client.put(f"{SONGS}/{song_id}/cover", json={key: stored[key] for key in COVER_KEYS} | changes)


def listen(client, song_id: str):
    return client.post(f"{SONGS}/{song_id}/cover/listen", json={})


def start(client, song_id: str):
    return client.post(f"{SONGS}/{song_id}/cover/render", json={})


def rendered(client, song_id: str) -> dict:
    response = start(client, song_id)
    assert response.status_code == 202, response.json()
    return poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)


def mp4_of(project: ProjectPaths, song_id: str, job: dict):
    return project.song_dir(song_id) / "renders" / f"{job['result']}.mp4"


def ffmpeg_out(*args: str) -> bytes:
    return subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", *args], check=True, capture_output=True).stdout


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


def test_listen_on_the_kalimba_without_its_samples_is_refused_naming_their_row(client, project):
    song_id = picked(project)
    assert put_cover(client, song_id, instrument="kalimba").status_code == 200
    project.kalimba_kit_marker.unlink()

    response = listen(client, song_id)
    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", [kalimba_kit.CHECK_ID])


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


def kalimba_song(project: ProjectPaths, notes=MELODY, **fields) -> str:
    """A song whose cover is saved as the kalimba's, drums off."""
    song_id = picked(project, notes=notes, **fields)
    stored = {"version": 1, "updated_at": "2026-11-16T00:00:00Z", "start_s": 10.0, "end_s": 16.0, "title": "Yellow",
              "subtitle": "", "caption": "", "background": "color", "backing": {"on": False, "volume": 35},
              "drums": {"on": False, "volume": 100}, "instrument": "kalimba", "kalimba": {"on": True, "volume": 80}}  # fmt: skip
    (project.song_dir(song_id) / cover.COVER_FILE).write_text(json.dumps(stored), encoding="utf-8")
    return song_id


def test_a_kalimba_render_is_a_vertical_h264_aac_mp4_of_the_stretch_that_says_it_is_the_kalimba_s(client, project):
    song_id = kalimba_song(project)

    job = rendered(client, song_id)

    assert (job["state"], job["title"]) == ("done", "Yellow")
    mp4 = mp4_of(project, song_id, job)
    info = ffmpeg.input_info(mp4)
    assert "1080x1920" in info and "30 fps" in info and "Video: h264" in info and "Audio: aac" in info
    assert ffmpeg.probe(mp4).duration_s == pytest.approx(CLIP_S, abs=0.1)
    [listed] = client.get(f"{SONGS}/{song_id}/cover/renders").json()
    assert (listed["instrument"], listed["kalimba"], listed["drums"]) == ("kalimba", {"on": True, "volume": 80}, {"on": False, "volume": 100})

    stored = mp4.with_suffix(".json")
    written = json.loads(stored.read_text(encoding="utf-8"))
    assert (written["instrument"], written["kalimba"]) == ("kalimba", {"on": True, "volume": 80})
    del written["instrument"], written["kalimba"]  # a render made before the kalimba (D9)
    stored.write_text(json.dumps(written), encoding="utf-8")
    [listed] = client.get(f"{SONGS}/{song_id}/cover/renders").json()
    assert (listed["instrument"], listed["kalimba"]) == ("drums", KALIMBA)


def test_a_c4_s_sound_starts_within_a_frame_of_its_tine_lighting_up(client, project):
    song_id = kalimba_song(project, notes=[(11.0, 60, "normal")])  # one C4 1.0 s into the stretch
    job = rendered(client, song_id)
    mp4 = mp4_of(project, song_id, job)

    rate = 48_000
    sound = np.frombuffer(ffmpeg_out("-i", str(mp4), "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"), dtype=np.int16)
    near = np.abs(sound[int(0.9 * rate) : int(1.3 * rate)].astype(np.int32))
    # The sound starts where it first reaches half its peak: the struck tine's click, past any codec smear before it.
    sound_at = (int(0.9 * rate) + int(np.argmax(near > near.max() // 2))) / rate
    tine = frames.TINES[8]
    x, y = tine.probe
    pixels = ffmpeg_out("-i", str(mp4), "-vf", f"crop=2:2:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-")
    red = (0xF8, 0x71, 0x71)  # a 1's colour, filled in full
    # One frame of the 2×2 crop is 12 bytes (4 pixels × RGB); the frames whose 4 pixels are all the 1's red.
    full = [n for n in range(len(pixels) // 12) if all(abs(pixels[12 * n + i] - c) <= 12 for i, c in enumerate(red))]
    assert full and abs(full[0] / frames.FPS - sound_at) <= 1 / frames.FPS


def test_the_same_kalimba_cover_rendered_twice_mixes_the_same_audio_wav(client, project, piped):
    song_id = kalimba_song(project)
    rendered(client, song_id)
    rendered(client, song_id)

    assert len(piped.audio) == 2 and piped.audio[0] == piped.audio[1]


def test_a_render_is_refused_for_no_notes_then_missing_rows_then_another_render_running(client, project, piped, fake_root):
    without_notes = kalimba_song(project, notes=[(10.5, 36, "normal")], song_id="nonotesong0")  # the bass alone, dropped
    drums, kalimba = picked(project, song_id="drumsong000"), kalimba_song(project)
    (project.kanit_dir / "OFL.txt").unlink()

    response = start(client, without_notes)
    assert (response.status_code, response.json()["code"]) == (409, "no_notes")

    write_kanit(fake_root)
    piped.pause_at = 10
    assert start(client, drums).status_code == 202
    assert piped.reached.wait(10)
    (project.kanit_dir / "OFL.txt").unlink()
    response = start(client, kalimba)
    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", [fonts.CHECK_ID])

    write_kanit(fake_root)
    response = start(client, kalimba)
    assert (response.status_code, response.json()["code"], response.json()["song_id"]) == (409, "busy", drums)
    piped.released.set()
    assert poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"


def test_a_kalimba_render_needs_the_kalimba_samples_but_no_drum_samples(client, project):
    song_id = kalimba_song(project)
    project.drum_kit_marker.unlink()

    assert rendered(client, song_id)["state"] == "done"
    project.kalimba_kit_marker.unlink()
    response = start(client, song_id)
    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", [kalimba_kit.CHECK_ID])
