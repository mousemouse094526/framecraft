"""Songs under /api/songs: a link's Song import with a fake yt-dlp adapter and real ffmpeg, a file's
as a raw body, a MIDI file, the list, one song, its audio, delete, and start-up (drum-notes seam 1
› Song import, Song และรายการ; D3, D4, D10, D18, D20)."""

import json
import threading
from pathlib import Path

import anyio
import pytest
from fastapi.testclient import TestClient

from backend import audio_imports, checks, disk, ffmpeg, paths, spoil
from backend.app import app
from backend.drum_notes import imports, songs
from backend.paths import ProjectPaths

from .fakes import (
    FINISHED,
    OCTET,
    ROCK,
    SONGS,
    AudioLinkAdapter,
    Upload,
    import_song_tone,
    midi_file,
    ok_deno,
    ok_ffmpeg,
    ok_yt_dlp,
    play,
    poll_until,
    put_song_file,
    restart,
    site_info,
    song_refusal,
    tone,
    yt_dlp_error,
    youtube_info,
)

IMPORT = f"{SONGS}/import"
YOUTUBE = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def project(fake_root, monkeypatch) -> ProjectPaths:
    monkeypatch.setattr(paths, "ROOT", fake_root)
    return ProjectPaths(fake_root)


@pytest.fixture
def adapter(monkeypatch, tmp_path_factory) -> AudioLinkAdapter:
    """yt-dlp, and the Status check rows a link needs, ready: a 6 s clip titled and channelled."""
    fake = AudioLinkAdapter(tone(tmp_path_factory.mktemp("link") / "tone.webm", 6), info=youtube_info(title="Smells Like Teen Spirit", channel="Nirvana", duration=6))
    monkeypatch.setattr(spoil, "adapter", fake)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    return fake


@pytest.fixture
def client(project, adapter, monkeypatch) -> TestClient:
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(imports, "song_imports", imports.SongImports())
    return TestClient(app, base_url="http://127.0.0.1")


def link(client, url: str = YOUTUBE):
    return client.post(f"{SONGS}/link", json={"url": url})


def import_link(client, url: str = YOUTUBE) -> dict:
    response = link(client, url)
    assert response.status_code == 202, response.json()
    return poll_until(client, IMPORT, lambda job: job["state"] in FINISHED)


def song_file(project: ProjectPaths, song_id: str) -> Path:
    return project.song_dir(song_id) / "song.json"


def partial_files(project: ProjectPaths) -> list[str]:
    return sorted(p.name for p in project.songs_partial_dir.iterdir()) if project.songs_partial_dir.is_dir() else []


# --- a link ---


def test_a_youtube_link_comes_in_as_aac_in_m4a_with_the_clip_s_title_and_channel(client, adapter, project):
    job = import_link(client)

    assert (job["state"], job["song_id"], job["percent"], job["title"]) == ("done", "dQw4w9WgXcQ", 100, "Smells Like Teen Spirit")
    assert {options.format for options in adapter.options} == {"bestaudio"}
    assert {options.folder(project) for options in adapter.options} == {project.songs_partial_dir}
    assert adapter.landed == ["dQw4w9WgXcQ.webm"]  # into media/songs/.partial/
    m4a = project.song_dir("dQw4w9WgXcQ") / "audio.m4a"
    info = ffmpeg.input_info(m4a)
    assert "Audio: aac" in info and "48000 Hz" in info
    assert ffmpeg.probe(m4a).duration_s == pytest.approx(6, abs=0.1)
    song = json.loads(song_file(project, "dQw4w9WgXcQ").read_text(encoding="utf-8"))
    assert (song["version"], song["title"], song["subtitle"]) == (1, "Smells Like Teen Spirit", "Nirvana")
    assert song["source"] == {"kind": "link", "url": YOUTUBE, "name": None, "size": None}
    assert song["duration_s"] == pytest.approx(6, abs=0.1)
    assert song["range"] == {"start_s": 0.0, "end_s": pytest.approx(6, abs=0.1), "mode": "drums"}
    assert (song["analysis"], song["lessons"]) == (None, [])
    assert partial_files(project) == []
    [row] = client.get(SONGS).json()
    assert (row["id"], row["source_kind"], row["analysis"], row["lessons"]) == ("dQw4w9WgXcQ", "link", None, 0)


def test_a_long_song_s_range_starts_as_its_first_30_seconds(client, adapter, tmp_path):
    adapter.audio = tone(tmp_path / "long.webm", 40, rate=8_000)
    adapter.info["duration"] = 40

    import_link(client)

    assert client.get(f"{SONGS}/dQw4w9WgXcQ").json()["range"] == {"start_s": 0.0, "end_s": 30.0, "mode": "drums"}


def test_the_job_goes_through_checking_downloading_with_a_percent_then_converting(client, adapter):
    adapter.pause_at("progress")
    assert link(client).status_code == 202
    assert client.get(IMPORT).json()["state"] in ("checking", "downloading")
    adapter.wait_until("progress")
    assert (client.get(IMPORT).json()["state"], client.get(IMPORT).json()["percent"]) == ("downloading", 40)
    adapter.release("progress")

    assert poll_until(client, IMPORT, lambda job: job["state"] in FINISHED)["state"] == "done"


def test_the_same_youtube_link_again_answers_the_song_s_id_and_starts_no_job(client, adapter):
    import_link(client)
    before = client.get(IMPORT).json()

    response = link(client)

    assert (response.status_code, response.json()) == (200, {"song_id": "dQw4w9WgXcQ"})
    assert client.get(IMPORT).json() == before
    assert adapter.download_calls == 1


def test_another_site_s_link_of_a_song_already_in_ends_done_with_its_id_without_loading(client, adapter, project):
    adapter.info = site_info(title="เพลงจากเว็บอื่น", duration=6)
    first = import_link(client, "https://www.facebook.com/watch/?v=123")
    assert first["state"] == "done"
    stored = song_file(project, first["song_id"]).read_bytes()

    again = import_link(client, "https://www.facebook.com/watch/?v=123&ref=share")

    assert (again["state"], again["song_id"], again["percent"]) == ("done", first["song_id"], 100)
    assert first["song_id"] == "facebook-123"
    assert adapter.download_calls == 1
    assert song_file(project, first["song_id"]).read_bytes() == stored


def test_a_link_the_site_says_is_over_ten_minutes_fails_too_long_before_loading(client, adapter):
    adapter.info["duration"] = 700

    job = import_link(client)

    assert (job["state"], job["error"]) == ("failed", {"code": "too_long", "message": "เพลงยาวเกิน 10 นาที"})
    assert adapter.download_calls == 0


def test_a_link_whose_file_turns_out_over_ten_minutes_fails_too_long_with_no_folder(client, adapter, project, tmp_path):
    adapter.info["duration"] = None
    adapter.audio = tone(tmp_path / "long.webm", 700, rate=8_000)

    job = import_link(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "too_long")
    assert not project.song_dir("dQw4w9WgXcQ").exists()
    assert partial_files(project) == []


def test_a_link_whose_file_is_two_seconds_fails_too_short(client, adapter, tmp_path):
    adapter.info["duration"] = None
    adapter.audio = tone(tmp_path / "short.webm", 2)

    job = import_link(client)

    assert (job["state"], job["error"]) == ("failed", {"code": "too_short", "message": "เพลงสั้นกว่า 4 วินาที"})


def test_the_conversion_is_cut_at_600_seconds(client, adapter, monkeypatch):
    commands: list[list[str]] = []

    def recording(command, cwd, cancel, on_progress=None):
        commands.append(command)
        ffmpeg.run(command, cwd, cancel, on_progress)

    monkeypatch.setattr(imports, "song_imports", imports.SongImports(convert=recording))

    assert import_link(client)["state"] == "done"

    [command] = commands
    assert command[command.index("-t") + 1] == "600"


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (yt_dlp_error(Exception("Unsupported URL: https://example.com/x")), "unsupported"),
        (yt_dlp_error(Exception("Sign in to confirm you're not a bot")), "login_required"),
        (yt_dlp_error(Exception("Video unavailable")), "unavailable"),
        (yt_dlp_error(Exception("This live event will begin in 3 hours")), "live"),
        (yt_dlp_error(Exception("HTTP Error 500")), "download_error"),
    ],
)
def test_yt_dlp_s_errors_end_the_job_failed_with_the_adapter_s_code(client, adapter, error, code):
    adapter.fetch_error = error

    job = import_link(client)

    assert (job["state"], job["error"]["code"]) == ("failed", code)
    assert job["error"]["message"]


def test_a_playlist_link_fails_playlist(client, adapter):
    adapter.info["_type"] = "playlist"

    job = import_link(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "playlist")


def test_a_live_stream_fails_live(client, adapter):
    adapter.info["live_status"] = "is_live"

    assert import_link(client)["error"]["code"] == "live"


@pytest.mark.parametrize("url", ["http://127.0.0.1/a.mp3", "http://192.168.1.5/song", "ftp://example.com/a.mp3", "not a link"])
def test_a_private_host_or_no_link_is_invalid_request(client, url):
    assert song_refusal(link(client, url)) == (400, "invalid_request")


def test_without_yt_dlp_a_link_is_not_ready_naming_the_rows(client, monkeypatch):
    from .fakes import broken_deno

    monkeypatch.setattr(checks, "probe_deno", broken_deno)

    response = link(client)

    assert song_refusal(response) == (503, "not_ready")
    assert response.json()["rows"] == ["deno"]


def test_while_a_link_runs_another_link_and_a_file_check_are_busy_and_a_cancel_ends_it_cancelled(client, adapter, project):
    adapter.pause_at("progress")
    assert link(client).status_code == 202
    adapter.wait_until("progress")

    assert song_refusal(link(client, "https://youtu.be/aaaaaaaaaaa")) == (409, "busy")
    assert song_refusal(client.post(f"{SONGS}/check", json={"name": "a.mp3", "size": 10})) == (409, "busy")
    cancelled = client.post(f"{IMPORT}/cancel", json={})
    assert (cancelled.status_code, cancelled.json()["cancel_requested"]) == (200, True)
    adapter.release("progress")

    assert poll_until(client, IMPORT, lambda job: job["state"] in FINISHED)["state"] == "cancelled"
    assert partial_files(project) == []
    assert not project.song_dir("dQw4w9WgXcQ").exists()
    assert client.get(SONGS).json() == []


def test_a_cancel_with_no_job_running_is_not_running(client):
    assert song_refusal(client.post(f"{IMPORT}/cancel", json={})) == (409, "not_running")
    assert client.get(IMPORT).json() is None


# --- a file ---


def test_the_check_answers_the_size_or_refuses_the_file_before_its_body_is_sent(client, tmp_path):
    assert client.post(f"{SONGS}/check", json={"name": "song.mp3", "size": 1000}).json() == {"size": 1000}
    assert song_refusal(client.post(f"{SONGS}/check", json={"name": "big.mp3", "size": imports.UPLOAD_MAX_BYTES + 1})) == (413, "file_too_large")
    assert client.post(f"{SONGS}/check", json={"name": "ok.mid", "size": imports.MIDI_MAX_BYTES}).json() == {"size": imports.MIDI_MAX_BYTES}
    assert song_refusal(client.post(f"{SONGS}/check", json={"name": "big.mid", "size": imports.MIDI_MAX_BYTES + 1})) == (413, "file_too_large")
    assert song_refusal(client.post(f"{SONGS}/check", json={"name": "", "size": 10})) == (400, "invalid_request")
    assert song_refusal(client.post(f"{SONGS}/check", json={"name": "a.mp3", "size": True})) == (400, "invalid_request")


def test_the_check_of_a_file_already_in_answers_its_id(client, tmp_path):
    song = import_song_tone(client, tmp_path, "song.mp3")

    response = client.post(f"{SONGS}/check", json={"name": "song.mp3", "size": song["source"]["size"]})

    assert (response.status_code, response.json()) == (200, {"song_id": song["id"]})


def test_a_full_disk_is_507_at_the_check_and_the_put(client, monkeypatch, tmp_path):
    monkeypatch.setattr(disk, "free_bytes", lambda path: 2**20)

    assert song_refusal(client.post(f"{SONGS}/check", json={"name": "a.mp3", "size": 1000})) == (507, "disk_full")
    assert song_refusal(put_song_file(client, "a.mp3", tone(tmp_path / "a.mp3", 6).read_bytes())) == (507, "disk_full")


def test_an_mp3_comes_in_as_a_song_with_its_audio_named_after_the_file(client, project, tmp_path):
    song = import_song_tone(client, tmp_path, "My Song (demo).mp3")

    assert (song["title"], song["subtitle"], song["source"]["kind"], song["source"]["name"]) == ("My Song (demo)", "", "file", "My Song (demo).mp3")
    assert song["id"].startswith("local-")
    assert song["duration_s"] == pytest.approx(6, abs=0.1)
    assert song["range"]["end_s"] == pytest.approx(6, abs=0.1)
    assert "Audio: aac" in ffmpeg.input_info(project.song_dir(song["id"]) / "audio.m4a")
    assert client.get(f"{SONGS}/{song['id']}").json() == song
    assert partial_files(project) == []


def test_a_two_second_wav_is_too_short_and_a_text_file_has_no_sound(client, project, tmp_path):
    short = put_song_file(client, "short.wav", tone(tmp_path / "short.wav", 2).read_bytes())
    assert song_refusal(short) == (422, "too_short")

    text = put_song_file(client, "notes.mp3", "ไม่ใช่เสียง".encode() * 100)
    assert song_refusal(text) == (415, "unsupported_file")
    assert text.json()["message"] == "ไฟล์นี้ไม่มีเสียงที่อ่านได้"
    assert client.get(SONGS).json() == []
    assert sorted(p.name for p in project.songs_dir.iterdir()) == [".partial"]
    assert partial_files(project) == []


def test_a_body_of_another_size_than_said_is_size_mismatch(client, tmp_path):
    data = tone(tmp_path / "a.mp3", 6).read_bytes()

    assert song_refusal(put_song_file(client, "a.mp3", data, size=len(data) - 1)) == (400, "size_mismatch")
    assert song_refusal(put_song_file(client, "a.mp3", data, size=len(data) + 1)) == (400, "size_mismatch")


def test_a_body_that_stops_coming_is_stalled(client, project, monkeypatch, tmp_path):
    monkeypatch.setattr(imports, "song_imports", imports.SongImports(stall_seconds=0.2))
    data = tone(tmp_path / "a.mp3", 6).read_bytes()

    status, body = anyio.run(play, Upload(data[:1000], then="stall"), "a.mp3", len(data), SONGS, "PUT")

    assert (status, body["code"]) == (408, "stalled")
    assert partial_files(project) == []
    assert put_song_file(client, "a.mp3", data).status_code == 201


def test_a_put_that_is_not_octet_stream_is_415(client):
    assert song_refusal(put_song_file(client, "a.mp3", b"x", headers={"Content-Type": "application/json"})) == (415, "unsupported_media_type")
    assert song_refusal(put_song_file(client, "a.mp3", b"x", headers={"Content-Type": "multipart/form-data"})) == (415, "unsupported_media_type")


class PausedConvert:
    """ffmpeg converting a song, until the job's `cancel` is set: ffmpeg running long."""

    def __init__(self):
        self.reached = threading.Event()
        self.cancelled = False

    def __call__(self, command: list[str], cwd: Path, cancel: threading.Event, on_progress=None) -> None:
        Path(command[-1]).write_bytes(b"half")  # as far as ffmpeg got
        self.reached.set()
        self.cancelled = cancel.wait(5)
        raise ffmpeg.Cancelled() if self.cancelled else AssertionError("the import never cancelled ffmpeg")


def test_a_page_that_goes_away_while_ffmpeg_converts_stops_ffmpeg_and_makes_no_song(client, project, tmp_path, monkeypatch):
    paused = PausedConvert()
    monkeypatch.setattr(imports, "song_imports", imports.SongImports(convert=paused))
    data = tone(tmp_path / "in.mp3", 6).read_bytes()
    upload = Upload(data, then="leave")

    async def main():
        async with anyio.create_task_group() as group:
            group.start_soon(play, upload, "in.mp3", len(data), SONGS, "PUT")
            assert await anyio.to_thread.run_sync(paused.reached.wait, 5)
            upload.leave()

    anyio.run(main)

    assert paused.cancelled
    assert client.get(SONGS).json() == []
    assert partial_files(project) == []
    assert [p.name for p in project.songs_dir.iterdir()] == [".partial"]
    monkeypatch.setattr(imports, "song_imports", imports.SongImports())
    assert put_song_file(client, "in.mp3", data).status_code == 201


# --- a MIDI file ---


def test_a_mid_file_comes_in_with_its_analysis_and_no_audio(client, project):
    response = put_song_file(client, "rock.mid", midi_file(ROCK, bpm=100))

    assert response.status_code == 201, response.json()
    song = response.json()
    assert (song["source"]["kind"], song["range"], song["title"]) == ("midi", None, "rock")
    assert song["duration_s"] == pytest.approx(4.2)
    assert song["analysis"]["downbeats"] == [0.0, 2.4]
    assert song["analysis"]["beats"] == [0.0, 0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2]
    assert [(hit["piece"], hit["level"]) for hit in song["analysis"]["hits"]][:2] == [("kick", "accent"), ("hihat_closed", "accent")]
    assert {hit["piece"] for hit in song["analysis"]["hits"]} == {"kick", "snare", "hihat_closed"}
    assert sorted(p.name for p in project.song_dir(song["id"]).iterdir()) == ["song.json"]
    assert song_refusal(client.get(f"{SONGS}/{song['id']}/audio.m4a")) == (404, "not_found")
    [row] = client.get(SONGS).json()
    assert (row["source_kind"], row["analysis"]) == ("midi", {"mode": "drums", "bars": 1})


def test_a_mid_file_that_is_not_a_4_4_drum_track_is_unsupported_file_and_a_long_one_too_long(client):
    response = put_song_file(client, "waltz.mid", midi_file(ROCK, signature=(3, 2)))
    assert song_refusal(response) == (415, "unsupported_file")
    assert response.json()["message"] == "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง"
    assert song_refusal(put_song_file(client, "piano.mid", midi_file(ROCK, channel=0))) == (415, "unsupported_file")
    assert song_refusal(put_song_file(client, "long.mid", midi_file([(0, 36, 100), (480 * 4 * 250, 36, 100)]))) == (422, "too_long")
    assert client.get(SONGS).json() == []


# --- the list, one song, delete ---


def test_the_list_puts_the_latest_change_first_and_leaves_an_unreadable_song_out_with_a_log_line(client, project, tmp_path, caplog, monkeypatch):
    clock = iter(["2026-11-14T10:00:00+07:00", "2026-11-14T10:00:01+07:00", "2026-11-14T10:00:02+07:00"])
    monkeypatch.setattr(songs, "now_iso", lambda: next(clock))
    first = import_song_tone(client, tmp_path, "first.mp3")
    second = import_song_tone(client, tmp_path, "second.mp3")
    broken = import_song_tone(client, tmp_path, "broken.mp3")
    song_file(project, broken["id"]).write_text("{not json", encoding="utf-8")

    with caplog.at_level("WARNING"):
        rows = client.get(SONGS).json()

    assert [row["id"] for row in rows] == [second["id"], first["id"]]
    assert "hits" not in json.dumps(rows)
    assert f"song {broken['id']} can't be read" in caplog.text
    assert client.delete(f"{SONGS}/{broken['id']}").status_code == 204


@pytest.mark.parametrize("song_id", ["..", "%2E%2E", "a" * 65, "with.dot"])
def test_an_id_off_the_pattern_is_not_found_and_touches_no_file(client, project, tmp_path, song_id):
    import_song_tone(client, tmp_path)
    before = sorted(project.root.rglob("*"))

    assert song_refusal(client.get(f"{SONGS}/{song_id}")) == (404, "not_found")
    assert song_refusal(client.delete(f"{SONGS}/{song_id}")) == (404, "not_found")
    assert song_refusal(client.get(f"{SONGS}/{song_id}/audio.m4a")) == (404, "not_found")
    assert sorted(project.root.rglob("*")) == before


def test_the_audio_answers_a_range_with_206_so_the_player_can_seek(client, tmp_path):
    song = import_song_tone(client, tmp_path)

    whole = client.get(f"{SONGS}/{song['id']}/audio.m4a")
    part = client.get(f"{SONGS}/{song['id']}/audio.m4a", headers={"Range": "bytes=0-99"})

    assert (whole.status_code, whole.headers["content-type"]) == (200, "audio/mp4")
    assert (part.status_code, len(part.content)) == (206, 100)
    assert part.content == whole.content[:100]


def test_delete_removes_the_folder_and_a_second_delete_is_not_found(client, project, tmp_path):
    song = import_song_tone(client, tmp_path)

    assert client.delete(f"{SONGS}/{song['id']}").status_code == 204
    assert not project.song_dir(song["id"]).exists()
    assert song_refusal(client.delete(f"{SONGS}/{song['id']}")) == (404, "not_found")
    assert client.get(SONGS).json() == []


def test_a_start_empties_partial_and_removes_a_folder_with_no_song_json(client, project, tmp_path):
    kept = import_song_tone(client, tmp_path)
    project.songs_partial_dir.mkdir(parents=True, exist_ok=True)
    (project.songs_partial_dir / "dQw4w9WgXcQ.webm").write_bytes(b"half")
    (project.songs_dir / "local-000000000000").mkdir()
    (project.songs_dir / "local-000000000000" / "audio.m4a").write_bytes(b"orphan")
    (project.song_dir(kept["id"]) / "song.json.tmp").write_text("{", encoding="utf-8")

    restart(client)

    assert partial_files(project) == []
    assert not (project.songs_dir / "local-000000000000").exists()
    assert not (project.song_dir(kept["id"]) / "song.json.tmp").exists()
    assert [row["id"] for row in client.get(SONGS).json()] == [kept["id"]]
