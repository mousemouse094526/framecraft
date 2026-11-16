"""A song's reel cover under /api/songs/{id}/cover and its Render job under /api/covers/render, with
real ffmpeg, the fake samples and analyses written straight to disk (drum-cover seam 1; D2, D6, D7,
D12, D15, D17, D18, D19, D24, D27; ADR 0050, 0052)."""

import io
import json
import subprocess
import threading
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pytest
import soundfile
from fastapi.testclient import TestClient
from PIL import Image, ImageFont

from backend import ffmpeg, paths, pictures
from backend.app import app
from backend.drum_cover import cover, render
from backend.drum_cover import frames as reel_frames
from backend.drum_cover import timeline as reel_timeline
from backend.drum_notes import songs
from backend.paths import ProjectPaths
from backend.video_gen import captions, mixer
from backend.video_gen import render as drum_render

from .fakes import FINISHED, png, poll_until, restart, song_m4a, written_song

SONGS = "/api/songs"
RENDER = "/api/covers/render"
SNARE = reel_frames.KIT["snare"]
SNARE_FILL = (0x60, 0xA5, 0xFA)  # the sketch's snare, filled in full (D27)
# Bars 2.0 s long from 10.0; the picked range 10–16.
DOWNBEATS = (10.0, 12.0, 14.0, 16.0)
CLIP_S = 6.0 + 1.5  # the picked range 10–16, then the clip's tail


class FakePiped:
    """The job's `run_piped`: the real one, but frame `pause_at` waits for `released` or the
    cancel, and `audio` keeps each run's `audio.wav`."""

    def __init__(self):
        self.pause_at: int | None = None
        self.reached, self.released = threading.Event(), threading.Event()
        self.audio: list[bytes] = []

    def __call__(self, command, cwd, cancel, drawn, on_frame) -> None:
        self.audio.append((Path(cwd) / drum_render.AUDIO).read_bytes())

        def paused():
            for n, frame in enumerate(drawn):
                if n == self.pause_at:
                    self.reached.set()
                    while not (self.released.is_set() or cancel.is_set()):
                        cancel.wait(0.01)
                yield frame

        ffmpeg.run_piped(command, cwd, cancel, paused(), on_frame)


@pytest.fixture
def project(fake_root, monkeypatch) -> ProjectPaths:
    monkeypatch.setattr(paths, "ROOT", fake_root)
    return ProjectPaths(fake_root)


@pytest.fixture
def piped(monkeypatch) -> FakePiped:
    fake = FakePiped()
    title_font = lambda _project: ImageFont.load_default(captions.TITLE_SIZE)  # noqa: E731 – the fake root's Kanit is a name only
    monkeypatch.setattr(render, "render_jobs", render.CoverRenderJobs(run_piped=fake, title_font=title_font))
    return fake


@pytest.fixture
def client(project, piped) -> TestClient:
    return TestClient(app, base_url="http://127.0.0.1")


def picked(project: ProjectPaths, hits=((11.0, "snare", "normal"),), downbeats=DOWNBEATS, start_s: float = 10.0, **fields) -> str:
    return written_song(project, downbeats=downbeats, hits=list(hits), start_s=start_s, **fields)


def cover_body(client, song_id: str, **changes) -> dict:
    stored = client.get(f"{SONGS}/{song_id}/cover").json()
    keys = ("start_s", "end_s", "title", "subtitle", "caption", "background", "drums", "backing", "instrument", "kalimba")
    return {key: stored[key] for key in keys} | changes


def put_cover(client, song_id: str, **changes):
    return client.put(f"{SONGS}/{song_id}/cover", json=cover_body(client, song_id, **changes))


def start(client, song_id: str):
    return client.post(f"{SONGS}/{song_id}/cover/render", json={})


def rendered(client, song_id: str) -> dict:
    response = start(client, song_id)
    assert response.status_code == 202, response.json()
    return poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)


def renders_dir(project: ProjectPaths, song_id: str) -> Path:
    return project.song_dir(song_id) / "renders"


def ffmpeg_out(*args: str) -> bytes:
    return subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", *args], check=True, capture_output=True).stdout


def listened(client, song_id: str) -> np.ndarray:
    response = client.post(f"{SONGS}/{song_id}/cover/listen", json={})
    assert response.status_code == 200, response.json()
    return wav_of(response)


def stored_cover(project: ProjectPaths, song_id: str, **changes) -> None:
    """Writes `cover.json` by hand, as an older build or a hand edit leaves it."""
    stored = {"version": 1, "updated_at": "2026-11-15T00:00:00Z", "start_s": 10.0, "end_s": 16.0, "title": "Teen Spirit",
              "subtitle": "", "caption": "", "background": "color", "backing": {"on": False, "volume": 35}} | changes  # fmt: skip
    (project.song_dir(song_id) / cover.COVER_FILE).write_text(json.dumps(stored), encoding="utf-8")


def wav_of(response) -> np.ndarray:
    sound, rate = soundfile.read(io.BytesIO(response.content), dtype="int16")
    assert rate == 44_100
    return sound


# --- the cover ---


def test_a_picked_song_s_cover_starts_at_the_first_bar_with_a_hit_and_carries_the_clip_s_names(client, project):
    song_id = picked(project, hits=[(12.4, "snare", "normal"), (13.0, "kick", "normal")], title="Yellow (Drum Cover)", subtitle="DRUMMATE")

    body = client.get(f"{SONGS}/{song_id}/cover").json()

    assert (body["saved"], body["adjusted"], body["start_s"], body["end_s"], body["suggested_start_s"]) == (False, False, 12.0, 16.0, 12.0)
    assert (body["title"], body["subtitle"], body["caption"], body["background"]) == ("Yellow (Drum Cover)", "DRUMMATE", "", "color")
    assert body["backing"] == {"on": False, "volume": 35}
    assert (body["hits"], body["length_s"], body["has_audio"]) == (2, 4.0, False)


def test_a_song_not_picked_yet_has_no_cover_and_an_unknown_one_is_not_found(client, project):
    song = songs.new_song("notpickedyet", songs.Head("Song", "", songs.Source(kind="file", name="a.mp3", size=1)), 30, songs.default_range(30), None)
    with songs.lock:
        songs.write_new(project, song)

    response = client.get(f"{SONGS}/notpickedyet/cover")
    assert (response.status_code, response.json()["code"]) == (409, "no_analysis")
    assert client.get(f"{SONGS}/nosuchsong0/cover").status_code == 404
    assert client.get(f"{SONGS}/..%2Fetc/cover").status_code == 404


def test_a_first_hit_in_the_last_two_seconds_still_gives_a_two_second_stretch(client, project):
    song_id = picked(project, hits=[(15.5, "snare", "normal")])
    body = client.get(f"{SONGS}/{song_id}/cover").json()
    assert (body["start_s"], body["end_s"]) == (14.0, 16.0)


def test_a_put_saves_the_cover_and_a_bad_field_is_refused_by_name(client, project):
    song_id = picked(project)

    for field, change in [
        ("end_s", {"start_s": 11.0, "end_s": 12.0}),
        ("end_s", {"end_s": 16.5}),
        ("start_s", {"start_s": 9.0}),
        ("backing.volume", {"backing": {"on": False, "volume": 5}}),
        ("drums.volume", {"drums": {"on": True, "volume": 5}}),
        ("drums.volume", {"drums": {"on": True, "volume": 101}}),
        ("drums.volume", {"drums": {"on": True, "volume": 60.5}}),
        ("drums.volume", {"drums": {"on": True, "volume": True}}),
        ("drums.on", {"drums": {"on": "no", "volume": 100}}),
        ("drums.on", {"drums": None}),
        ("title", {"title": "  "}),
        ("subtitle", {"subtitle": "ก" * 61}),
        ("backing.on", {"backing": {"on": True, "volume": 35}}),  # no audio.m4a: a MIDI song's case
        ("background", {"background": "image"}),  # no picture yet
        ("start_s", {"start_s": "10"}),
        ("end_s", {"end_s": None}),
    ]:
        response = put_cover(client, song_id, **change)
        assert (response.status_code, response.json().get("field")) == (400, field), change

    response = put_cover(client, song_id, title="Yellow", caption="cover by me", start_s=10.5)
    assert response.status_code == 200, response.json()
    assert (response.json()["saved"], response.json()["title"], response.json()["start_s"]) == (True, "Yellow", 10.5)
    assert (project.song_dir(song_id) / "cover.json").is_file()


def test_drums_off_with_backing_off_is_refused_as_a_silent_reel(client, project):
    song_id = picked(project, audio=song_m4a(40.0))

    response = put_cover(client, song_id, drums={"on": False, "volume": 100})
    assert (response.status_code, response.json()["field"]) == (400, "drums.on")
    assert response.json()["message"] == "เปิดเสียงกลองหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง"
    response = put_cover(client, song_id, drums={"on": False, "volume": 60}, backing={"on": True, "volume": 35})
    assert response.status_code == 200, response.json()
    assert response.json()["drums"] == {"on": False, "volume": 60}


def test_a_cover_without_drums_reads_them_as_full_and_a_hand_edited_silent_one_is_refused(client, project):
    song_id = picked(project)
    assert client.get(f"{SONGS}/{song_id}/cover").json()["drums"] == {"on": True, "volume": 100}

    stored_cover(project, song_id)  # written before drums had a volume (D24)
    body = client.get(f"{SONGS}/{song_id}/cover").json()
    assert (body["saved"], body["drums"]) == (True, {"on": True, "volume": 100})

    stored_cover(project, song_id, drums={"on": False, "volume": 100})
    for response in (client.post(f"{SONGS}/{song_id}/cover/listen", json={}), start(client, song_id)):
        assert (response.status_code, response.json()["field"]) == (400, "drums.on")


def test_a_new_pick_that_no_longer_covers_the_stretch_pulls_it_in_and_says_so(client, project):
    song_id = picked(project)
    assert put_cover(client, song_id, start_s=12.0, end_s=16.0).status_code == 200
    with songs.lock:
        song = songs.read_under_lock(project, song_id)
    shorter = song.analysis.model_copy(update={"end_s": 15.0, "downbeats": [10.0, 12.0, 14.0], "beats": [10.0 + n / 2 for n in range(11)]})
    songs.set_analysis(project, song_id, shorter)

    body = client.get(f"{SONGS}/{song_id}/cover").json()
    assert (body["start_s"], body["end_s"], body["adjusted"], body["saved"]) == (12.0, 15.0, True, True)


# --- listen ---


def test_listen_mixes_the_drums_of_the_stretch_as_long_as_it_and_the_tail(client, project):
    song_id = picked(project)

    response = client.post(f"{SONGS}/{song_id}/cover/listen", json={})

    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    sound = wav_of(response)
    assert len(sound) / 44_100 == pytest.approx(CLIP_S, abs=0.05)
    assert np.abs(sound[: 44_100 - 100]).max() == 0  # the snare comes at 1.0 s
    assert np.abs(sound[44_100 : 44_100 + 4410]).max() > 0


def test_listen_at_full_drum_volume_is_the_mixer_s_wav_and_at_half_is_six_db_down(client, project):
    song_id = picked(project, hits=[(11.0, "snare", "normal"), (11.5, "kick", "accent"), (12.0, "hihat_closed", "normal")])
    with songs.lock:
        song = songs.read_under_lock(project, song_id)
    # The cover's defaults: the whole picked range 10–16, drums alone.
    fields = cover.CoverFields(start_s=10.0, end_s=16.0, title="Teen Spirit", subtitle="", caption="", background="color", backing=cover.Backing(on=False, volume=35), drums=cover.Drums(on=True, volume=100))
    mixed = mixer.mix(project, reel_timeline.build(song.analysis, fields))

    full = client.post(f"{SONGS}/{song_id}/cover/listen", json={})
    assert full.content == mixed  # D15: the same bytes as before drums had a volume

    assert put_cover(client, song_id, drums={"on": True, "volume": 50}).status_code == 200
    half = listened(client, song_id)
    assert len(half) / 44_100 == pytest.approx(CLIP_S, abs=0.05)
    peaks = [np.abs(sound.astype(np.int32)).max() for sound in (wav_of(full), half)]
    assert 20 * np.log10(peaks[1] / peaks[0]) == pytest.approx(-6.0, abs=0.1)  # 50 % is −6.0 dB, not brought back up


def test_drums_off_under_backing_is_the_song_alone_at_its_volume(client, project):
    song_id = picked(project, audio=song_m4a(40.0, volume=0.5))
    assert put_cover(client, song_id, drums={"on": False, "volume": 100}, backing={"on": True, "volume": 60}).status_code == 200

    sound = listened(client, song_id)

    raw = ffmpeg_out("-ss", "10.000", "-t", "6.000", "-i", str(project.song_dir(song_id) / songs.AUDIO_FILE), "-vn", "-ac", "2", "-ar", "44100", "-f", "f32le", "-")
    song = np.frombuffer(raw, dtype="<f4").reshape(-1, 2) * 0.6
    expected = np.zeros_like(sound, dtype=np.float32)
    expected[: len(song)] = song[: len(sound)]
    assert len(sound) / 44_100 == pytest.approx(CLIP_S, abs=0.05)
    assert np.abs(sound.astype(np.int32) - np.rint(expected * 32767)).max() <= 1  # no drums, and not pushed up to −1 dBFS


def test_listen_with_backing_lays_the_song_under_the_drums_and_never_clips(client, project):
    song_id = picked(project, hits=[(11.0, "snare", "accent")], audio=song_m4a(40.0, volume=16.0))  # lavfi's sine decodes near 0.09 of full scale, so 16 times over makes the sum pass −1 dBFS: D24 only ever lowers it
    assert put_cover(client, song_id, backing={"on": True, "volume": 100}).status_code == 200

    sound = wav_of(client.post(f"{SONGS}/{song_id}/cover/listen", json={}))

    assert len(sound) / 44_100 == pytest.approx(CLIP_S, abs=0.05)
    assert np.abs(sound[: 44_100 - 100]).max() > 1000  # the song plays before the first hit
    peak = np.abs(sound.astype(np.int32)).max()
    assert peak == round(32767 * 10 ** (-1 / 20))  # −1 dBFS: the sum was brought down, not clipped
    assert not np.any(np.abs(sound.astype(np.int32)) >= 32767)


def test_listen_with_a_broken_song_file_says_the_mix_failed(client, project):
    song_id = picked(project, audio=b"not an m4a")
    assert put_cover(client, song_id, backing={"on": True, "volume": 35}).status_code == 200

    response = client.post(f"{SONGS}/{song_id}/cover/listen", json={})
    assert (response.status_code, response.json()["code"]) == (500, "ffmpeg_failed")
    assert response.json()["message"].startswith("ผสมเสียงเพลงต้นฉบับไม่สำเร็จ: ")


def test_a_song_id_off_the_pattern_is_not_found_and_nothing_goes(client, project):
    song_id = picked(project)
    for response in (client.get(f"{SONGS}/..%2E/cover"), client.put(f"{SONGS}/a.b/cover", json={}), client.delete(f"{SONGS}/a.b")):
        assert response.status_code == 404
    assert (project.song_dir(song_id) / songs.SONG_FILE).is_file()


def test_listen_without_the_drum_samples_is_not_ready(client, project):
    song_id = picked(project)
    project.drum_kit_marker.unlink()

    response = client.post(f"{SONGS}/{song_id}/cover/listen", json={})
    assert (response.status_code, response.json()["rows"]) == (503, ["drum_kit"])


# --- render ---


def test_a_render_is_a_vertical_h264_aac_mp4_of_the_stretch_with_its_srt_and_json(client, project):
    song_id = picked(project)

    job = rendered(client, song_id)

    assert (job["state"], job["percent"], job["song_id"], job["title"]) == ("done", 100, song_id, "Teen Spirit")
    folder = renders_dir(project, song_id)
    mp4 = folder / f"{job['result']}.mp4"
    info = ffmpeg.input_info(mp4)
    assert "1080x1920" in info and "30 fps" in info and "Video: h264" in info and "Audio: aac" in info
    assert ffmpeg.probe(mp4).duration_s == pytest.approx(CLIP_S, abs=0.1)
    [listed] = client.get(f"{SONGS}/{song_id}/cover/renders").json()
    assert (listed["start_s"], listed["end_s"], listed["picked_at"], listed["backing"]) == (10.0, 16.0, "2026-11-14T00:00:00Z", {"on": False, "volume": 35})
    assert "Teen Spirit" in client.get(f"{SONGS}/{song_id}/cover/renders/{job['result']}.srt").text
    assert not project.songs_render_dir.exists()


def test_the_snare_s_sound_starts_within_a_frame_of_it_lighting_up(client, project):
    song_id = picked(project)  # a snare 1.0 s into the stretch
    job = rendered(client, song_id)
    mp4 = renders_dir(project, song_id) / f"{job['result']}.mp4"

    rate = 48_000
    sound = np.frombuffer(ffmpeg_out("-i", str(mp4), "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"), dtype=np.int16)
    near = np.abs(sound[int(0.9 * rate) : int(1.3 * rate)].astype(np.int32))
    sound_at = (int(0.9 * rate) + int(np.argmax(near > near.max() // 2))) / rate
    x, y = SNARE.probe  # nothing but the snare there: its label is above, the stick's head below
    pixels = ffmpeg_out("-i", str(mp4), "-vf", f"crop=2:2:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-")
    full = [n for n in range(len(pixels) // 12) if all(abs(pixels[12 * n + i] - c) <= 12 for i, c in enumerate(SNARE_FILL))]
    assert abs(full[0] / reel_frames.FPS - sound_at) <= 1 / reel_frames.FPS


def test_a_render_with_backing_has_its_picture_and_the_song_under_the_drums(client, project):
    song_id = picked(project, audio=song_m4a(40.0, volume=0.5))
    assert put_cover(client, song_id, backing={"on": True, "volume": 35}).status_code == 200

    job = rendered(client, song_id)

    mp4 = renders_dir(project, song_id) / f"{job['result']}.mp4"
    info = ffmpeg.input_info(mp4)
    assert "Video: h264" in info and "Audio: aac" in info
    assert ffmpeg.probe(mp4).duration_s == pytest.approx(CLIP_S, abs=0.1)
    sound = np.frombuffer(ffmpeg_out("-i", str(mp4), "-ac", "1", "-ar", "48000", "-t", "0.8", "-f", "s16le", "-"), dtype=np.int16)
    assert np.abs(sound).max() > 100  # before the snare: the song (backing off is silent there)
    [listed] = client.get(f"{SONGS}/{song_id}/cover/renders").json()
    assert listed["backing"] == {"on": True, "volume": 35}


def test_a_render_with_the_drums_off_is_a_whole_mp4_that_says_so_and_an_older_one_reads_as_full(client, project):
    song_id = picked(project, audio=song_m4a(40.0, volume=0.5))
    assert put_cover(client, song_id, drums={"on": False, "volume": 80}, backing={"on": True, "volume": 35}).status_code == 200

    job = rendered(client, song_id)

    mp4 = renders_dir(project, song_id) / f"{job['result']}.mp4"
    info = ffmpeg.input_info(mp4)
    assert "Video: h264" in info and "Audio: aac" in info
    assert ffmpeg.probe(mp4).duration_s == pytest.approx(CLIP_S, abs=0.1)
    stored = json.loads((renders_dir(project, song_id) / f"{job['result']}.json").read_text(encoding="utf-8"))
    assert stored["drums"] == {"on": False, "volume": 80}

    del stored["drums"]  # a render made before drums had a volume (D24)
    (renders_dir(project, song_id) / f"{job['result']}.json").write_text(json.dumps(stored), encoding="utf-8")
    [listed] = client.get(f"{SONGS}/{song_id}/cover/renders").json()
    assert listed["drums"] == {"on": True, "volume": 100}


def test_the_same_cover_rendered_twice_mixes_the_same_audio_wav(client, project, piped):
    song_id = picked(project)
    rendered(client, song_id)
    rendered(client, song_id)

    assert len(piped.audio) == 2 and piped.audio[0] == piped.audio[1]


def test_a_render_without_the_drum_samples_is_not_ready_and_an_unpicked_song_has_no_analysis(client, project):
    song_id = picked(project)
    project.drum_kit_marker.unlink()

    response = start(client, song_id)
    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", ["drum_kit"])
    assert start(client, "nosuchsong0").status_code == 404


def test_a_second_render_is_busy_the_song_can_t_be_deleted_and_a_put_reaches_only_the_next(client, project, piped):
    first, second = picked(project), picked(project, song_id="secondsong0")
    piped.pause_at = 10
    assert start(client, first).status_code == 202
    assert piped.reached.wait(10)

    busy = start(client, second)
    assert (busy.status_code, busy.json()["code"], busy.json()["song_id"]) == (409, "busy", first)
    deleted = client.delete(f"{SONGS}/{first}")
    assert (deleted.status_code, deleted.json()["code"]) == (409, "song_busy")
    assert put_cover(client, first, title="NEW TITLE").status_code == 200
    piped.released.set()
    job = poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)
    [listed] = client.get(f"{SONGS}/{first}/cover/renders").json()
    assert (job["state"], listed["title"]) == ("done", "Teen Spirit")


def test_a_cancel_while_frames_go_leaves_no_partial(client, project, piped):
    song_id = picked(project)
    piped.pause_at = 10
    assert start(client, song_id).status_code == 202
    assert piped.reached.wait(10)

    assert client.post(f"{RENDER}/cancel", json={}).status_code == 200
    job = poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=30)
    assert job["state"] == "cancelled"
    assert list(renders_dir(project, song_id).iterdir()) == []
    assert not project.songs_render_dir.exists()
    response = client.post(f"{RENDER}/cancel", json={})
    assert (response.status_code, response.json()["code"]) == (409, "not_running")


def test_a_backend_restart_removes_the_work_folder_and_every_partial(client, project):
    song_id = picked(project)
    folder = renders_dir(project, song_id)
    folder.mkdir(parents=True)
    (folder / "20261115-103000.mp4.partial").write_bytes(b"half")
    project.songs_render_dir.mkdir(parents=True)

    restart(client)
    assert list(folder.iterdir()) == []
    assert not project.songs_render_dir.exists()


# --- results and the song ---


def test_renders_are_served_and_deleted_and_go_with_their_song(client, project):
    song_id = picked(project)
    name = rendered(client, song_id)["result"]

    mp4 = client.get(f"{SONGS}/{song_id}/cover/renders/{name}.mp4")
    assert (mp4.status_code, mp4.headers["content-type"]) == (200, "video/mp4")
    assert client.delete(f"{SONGS}/{song_id}/cover/renders/..%2Fsong").status_code == 404
    assert client.delete(f"{SONGS}/{song_id}/cover/renders/{name}").status_code == 204
    assert client.get(f"{SONGS}/{song_id}/cover/renders/{name}.mp4").status_code == 404

    rendered(client, song_id)
    assert put_cover(client, song_id, title="Yellow").status_code == 200
    assert client.delete(f"{SONGS}/{song_id}").status_code == 204
    assert not project.song_dir(song_id).exists()


# --- the background picture (D8, D21) ---


def put_picture(client, song_id: str, body: bytes, size: int | None = None, content_type: str = "application/octet-stream"):
    return client.put(f"{SONGS}/{song_id}/cover/background?size={len(body) if size is None else size}", content=body, headers={"Content-Type": content_type})


def corner_of_first_frame(mp4: Path) -> tuple[int, int, int]:
    pixels = ffmpeg_out("-i", str(mp4), "-vf", "crop=2:2:0:0", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-")
    return pixels[0], pixels[1], pixels[2]


def test_a_picture_is_cropped_to_1080x1920_kept_and_removed(client, project):
    song_id = picked(project)

    assert client.post(f"{SONGS}/{song_id}/cover/background/check", json={"size": 1000}).json() == {"size": 1000}
    response = put_picture(client, song_id, png(540, 400, "#FF0000"))

    assert response.status_code == 200, response.json()
    assert (response.json()["background"], response.json()["saved"]) == ("image", True)
    with Image.open(project.song_dir(song_id) / "cover-background.jpg") as kept:
        assert kept.size == (1080, 1920)
    picture = client.get(f"{SONGS}/{song_id}/cover/background.jpg")
    assert (picture.status_code, picture.headers["content-type"]) == (200, "image/jpeg")
    removed = client.delete(f"{SONGS}/{song_id}/cover/background")
    assert removed.json()["background"] == "color"
    assert not (project.song_dir(song_id) / "cover-background.jpg").exists()
    assert client.get(f"{SONGS}/{song_id}/cover/background.jpg").status_code == 404


def test_a_picture_that_isn_t_one_or_is_too_large_is_refused(client, project):
    song_id = picked(project)

    text = put_picture(client, song_id, b"just text")
    assert (text.status_code, text.json()["code"]) == (415, "unsupported_image")
    over = pictures.MAX_BYTES + 1
    checked = client.post(f"{SONGS}/{song_id}/cover/background/check", json={"size": over})
    assert (checked.status_code, checked.json()["code"]) == (413, "file_too_large")
    assert put_picture(client, song_id, b"x", size=over).status_code == 413
    assert not project.songs_partial_dir.exists() or not any(project.songs_partial_dir.iterdir())  # no upload left behind


def test_a_render_uses_the_picture_blurred_and_the_picture_can_t_change_meanwhile(client, project, piped):
    plain, pictured = picked(project), picked(project, song_id="pictured000")
    assert put_picture(client, pictured, png(540, 960, "#FF0000")).status_code == 200
    plain_corner = corner_of_first_frame(renders_dir(project, plain) / f"{rendered(client, plain)['result']}.mp4")

    piped.pause_at = 10
    assert start(client, pictured).status_code == 202
    assert piped.reached.wait(10)
    refused = [put_picture(client, pictured, png(540, 960, "#00FF00")), client.delete(f"{SONGS}/{pictured}/cover/background")]
    piped.released.set()
    job = poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)

    for response in refused:
        assert (response.status_code, response.json()["code"], response.json()["message"]) == (409, "song_busy", "กำลัง render reel ของเพลงนี้อยู่")
    corner = corner_of_first_frame(renders_dir(project, pictured) / f"{job['result']}.mp4")
    assert corner != plain_corner and corner[0] > 80 and corner[1] < 30  # red under 55 % black


def test_a_cover_saved_as_image_whose_picture_went_renders_on_the_app_s_colours(client, project):
    song_id = picked(project)
    assert put_picture(client, song_id, png(540, 960, "#FF0000")).status_code == 200
    (project.song_dir(song_id) / "cover-background.jpg").unlink()
    assert client.get(f"{SONGS}/{song_id}/cover").json()["background"] == "color"  # so its next save isn't refused

    job = rendered(client, song_id)
    assert job["state"] == "done"
    corner = corner_of_first_frame(renders_dir(project, song_id) / f"{job['result']}.mp4")
    assert corner[0] < 40  # the navy, not the red
