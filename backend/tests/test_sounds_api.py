"""The sound library under /api/sounds: a file's Sound import with real ffmpeg, a link's with a
fake yt-dlp adapter, `in_use`, `sound: null`, the Cards job picking a sound, and the move from
`media/toon/sounds/` at start (sound-library seam 1, toon seam 1 › Sound import)."""

import ast
import json
import os
import re
import threading
from pathlib import Path

import anyio
import deno
import pytest

from backend import checks, ffmpeg, files, sounds, spoil
from backend.spoil.adapter import DownloadOptions, YtDlpAdapter, select_formats

from .fakes import (
    FINISHED,
    SOUNDS,
    TOON_VOICE,
    FakeAdapter,
    Upload,
    Writer,
    cards_of,
    import_file,
    import_tone,
    new_ep,
    new_series,
    ok_deno,
    ok_yt_dlp,
    play,
    restart,
    poll_until,
    run,
    start,
    tone,
    toon_api,
    with_series,
    write_library,
    youtube_info,
)

IMPORT = "/api/sounds/import/current"


project, llm, klein, tts, client = toon_api(lambda: Writer().respond, uses=("adapter",))


@pytest.fixture
def adapter(monkeypatch, tmp_path_factory) -> FakeAdapter:
    """yt-dlp, and the Status check rows a link needs, ready."""
    fake = LinkAdapter(tone(tmp_path_factory.mktemp("link") / "tone.webm", 2))
    monkeypatch.setattr(spoil, "adapter", fake)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    return fake


class LinkAdapter(FakeAdapter):
    """yt-dlp for a link's sound: the options it was asked with, and the audio file it
    leaves where they say."""

    def __init__(self, audio: Path):
        super().__init__(info=youtube_info(title="ฝนตกในป่า", duration=2))
        self.audio = audio
        self.options: list[DownloadOptions] = []

    def fetch_info(self, url: str, options: DownloadOptions = DownloadOptions()) -> dict:
        self.options.append(options)
        return super().fetch_info(url)

    def download(self, info, project, clip_id, on_progress, options: DownloadOptions = DownloadOptions()) -> Path:
        self.options.append(options)
        self.clip_ids.append(clip_id)
        folder = options.folder(project)
        for event in self.events:
            on_progress(event)
        self._checkpoint("progress")
        target = folder / options.name.format(id=clip_id).replace("%(ext)s", "webm")
        target.write_bytes(self.audio.read_bytes())
        self.landed = sorted(path.name for path in folder.iterdir())
        return target


def download(client, url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ") -> dict:
    response = client.post(f"{SOUNDS}/downloads", json={"url": url})
    assert response.status_code == 202, response.json()
    return poll_until(client, IMPORT, lambda job: job["state"] in FINISHED)


# --- what the library imports ---


def test_the_library_imports_none_of_the_tabs_that_use_it():
    tree = ast.parse(Path(sounds.__file__).read_text(encoding="utf-8"))
    imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imported |= {f"backend.{alias.name}" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module == "backend" for alias in node.names}
    imported |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    users = ("backend.toon", "backend.spoil_maker")  # spoil's yt-dlp adapter is the app's one way to load a link
    assert [name for name in sorted(imported) if name.startswith(users)] == []


# --- the adapter's options ---


@pytest.fixture
def no_deno(monkeypatch):
    """`_params` names Deno's binary; the machine running the tests may have none."""
    monkeypatch.setattr(deno, "find_deno_bin", lambda: "deno")


def test_the_adapter_s_default_options_are_a_temp_clip_s_as_before(project, no_deno):
    params = YtDlpAdapter()._params(project, "dQw4w9WgXcQ", DownloadOptions())
    assert params["format"] is select_formats
    assert params["merge_output_format"] == "mp4"
    assert params["writethumbnail"] is True
    assert params["paths"] == {"home": str(project.media_temp_dir), "temp": str(project.partial_dir)}
    assert params["outtmpl"] == "dQw4w9WgXcQ.%(ext)s"


def test_a_sound_link_s_options_take_the_best_audio_into_the_library_s_partial_with_no_thumbnail_or_merge(project, no_deno):
    params = YtDlpAdapter()._params(project, "m_01234567", sounds.LINK_OPTIONS)
    assert params["format"] == "bestaudio"
    assert "merge_output_format" not in params
    assert params["writethumbnail"] is False
    assert params["paths"] == {"home": str(project.sounds_partial_dir), "temp": str(project.sounds_partial_dir)}
    assert params["outtmpl"] == "m_01234567.%(ext)s"


# --- a file ---


def test_a_wav_file_comes_in_as_aac_in_m4a_named_after_the_file(client, project, tmp_path):
    sound = import_tone(client, tmp_path, "ฝนตกในป่า.wav", seconds=1.5)
    assert sound["name"] == "ฝนตกในป่า"
    assert sound["source"] == "file"
    assert sound["duration_s"] == pytest.approx(1.5, abs=0.1)
    m4a = project.sounds_dir / f"{sound['id']}.m4a"
    info = ffmpeg.input_info(m4a)
    assert "Audio: aac" in info and "48000 Hz" in info and "stereo" in info
    assert [s.id for s in sounds.read_sounds(project)] == [sound["id"]]
    assert client.get(SOUNDS).json() == [sound]
    assert client.get(f"{SOUNDS}/{sound['id']}/file").content == m4a.read_bytes()
    assert not list(project.sounds_partial_dir.iterdir())


def test_a_file_ffmpeg_reads_no_sound_in_is_unsupported_file(client, project):
    response = import_file(client, "notes.mp3", "ไม่ใช่เสียง".encode() * 100)
    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_file"
    assert client.get(SOUNDS).json() == []


def test_a_file_over_twenty_minutes_is_too_long(client, tmp_path):
    long = tone(tmp_path / "long.wav", sounds.MAX_SECONDS + 1, rate=8_000)
    response = import_file(client, "long.wav", long.read_bytes())
    assert response.status_code == 400
    assert response.json()["code"] == "too_long"


def test_a_file_over_200_mb_is_refused_at_the_check(client):
    response = client.post(f"{SOUNDS}/imports/check", json={"name": "big.wav", "size": sounds.UPLOAD_MAX_BYTES + 1})
    assert response.status_code == 400
    assert response.json()["code"] == "file_too_large"
    assert client.post(f"{SOUNDS}/imports/check", json={"name": "ok.wav", "size": 1000}).json() == {"size": 1000}


def test_a_sound_is_renamed_within_1_to_60_letters(client, tmp_path):
    sound = import_tone(client, tmp_path)
    assert client.patch(f"{SOUNDS}/{sound['id']}", json={"name": " ลมพัด "}).json()["name"] == "ลมพัด"
    assert client.patch(f"{SOUNDS}/{sound['id']}", json={"name": ""}).json()["code"] == "invalid_request"


# --- a link ---


def test_a_link_loads_its_best_audio_into_the_library_s_partial_with_no_thumbnail_and_comes_in_named_after_the_clip(
    client, adapter, project
):
    job = download(client)
    assert job["state"] == "done", job
    assert all(options == sounds.LINK_OPTIONS for options in adapter.options)
    assert adapter.landed == [f"{adapter.clip_ids[0]}.webm"]
    [sound] = client.get(SOUNDS).json()
    assert sound == {"id": job["sound_id"], "name": "ฝนตกในป่า", "duration_s": pytest.approx(2, abs=0.1), "source": "link"}
    assert (project.sounds_dir / f"{sound['id']}.m4a").is_file()
    assert not list(project.sounds_partial_dir.iterdir())


def test_a_link_whose_clip_title_is_only_spaces_comes_in_named_after_its_id(client, adapter):
    adapter.info["title"] = "   "
    job = download(client)
    assert job["state"] == "done", job
    [sound] = client.get(SOUNDS).json()
    assert sound["name"] == job["sound_id"]


def test_a_link_spoil_s_rules_refuse_is_invalid_url(client):
    for url in ("ftp://example.com/a.mp3", "http://127.0.0.1/a.mp3", "not a link"):
        response = client.post(f"{SOUNDS}/downloads", json={"url": url})
        assert response.status_code == 400
        assert response.json()["code"] == "invalid_url"


def test_a_link_over_twenty_minutes_by_its_info_fails_too_long_before_loading(client, adapter):
    adapter.info["duration"] = sounds.MAX_SECONDS + 1
    job = download(client)
    assert job["state"] == "failed"
    assert job["error"]["code"] == "too_long"
    assert adapter.clip_ids == []


def test_a_sound_import_is_busy_while_another_runs_but_not_while_a_toon_job_runs(client, llm, adapter):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.pause_at(0)
    assert start(client, "plot", ep_id).status_code == 202
    llm.wait_until(0)
    adapter.pause_at("progress")
    assert client.post(f"{SOUNDS}/downloads", json={"url": "https://youtu.be/dQw4w9WgXcQ"}).status_code == 202
    adapter.wait_until("progress")
    again = client.post(f"{SOUNDS}/downloads", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
    assert (again.status_code, again.json()["code"]) == (409, "busy")
    assert import_file(client, "a.wav", b"x" * 10).json()["code"] == "busy"
    adapter.release("progress")
    llm.release(0)
    assert poll_until(client, IMPORT, lambda job: job["state"] in FINISHED)["state"] == "done"


# --- in use ---


def with_sound_on_cards(client, llm, tmp_path) -> tuple[dict, dict, Writer]:
    """A Series whose EP is split with one sound in the library: the Cards job picks it."""
    sound = import_tone(client, tmp_path)
    series_id, _, _ = with_series(client, llm)
    writer = llm.respond.__self__
    cards = writer.cards
    writer.cards = lambda act: {"segments": [{**cards(act)["segments"][0], "sound": sound["id"]}]}
    ep_id = new_ep(client, series_id)["id"]
    assert run(client, "plot", ep_id)["state"] == "done"
    assert run(client, "cards", ep_id)["state"] == "done"
    return sound, client.get(f"/api/toon/eps/{ep_id}").json(), writer


def test_the_cards_job_picks_a_sound_of_the_library_at_volume_30(client, llm, tmp_path):
    sound, ep, _ = with_sound_on_cards(client, llm, tmp_path)
    segments = [segment for act in ep["acts"] for segment in act["segments"]]
    assert {segment["sound"]["sound_id"] for segment in segments} == {sound["id"]}
    assert {segment["sound"]["volume"] for segment in segments} == {30}
    assert f"- {sound['id']}: {sound['name']}" in llm.requests[-1].prompt


def test_a_sound_a_segment_plays_is_in_use_naming_the_ep_until_its_sound_is_null(client, llm, tmp_path, project):
    sound, ep, _ = with_sound_on_cards(client, llm, tmp_path)
    refused = client.delete(f"{SOUNDS}/{sound['id']}")
    assert refused.status_code == 409
    assert refused.json()["code"] == "in_use"
    assert refused.json()["message"] == "ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้"
    assert refused.json()["users"] == [{"tab": "toon", "label": f"รุ่นพี่เล่าว่า… · EP 1 {ep['title']}"}]
    for segment in (s for act in ep["acts"] for s in act["segments"]):
        changed = client.patch(f"/api/toon/eps/{ep['id']}/segments/{segment['id']}", json={"sound": None})
        assert changed.status_code == 200
    after = client.get(f"/api/toon/eps/{ep['id']}").json()
    assert {s["sound"] is None for act in after["acts"] for s in act["segments"]} == {True}
    assert client.delete(f"{SOUNDS}/{sound['id']}").status_code == 204
    assert not (project.sounds_dir / f"{sound['id']}.m4a").exists()
    assert len(cards_of(after)) == len(cards_of(ep))


def write_ep_playing(project, series_id: str, ep_id: str, n: int, title: str, sound_id: str) -> None:
    """An EP whose one segment plays the sound, as a Cards job leaves it."""
    segment = {"id": "g_00000001", "background_id": "b_00000001", "sound": {"sound_id": sound_id, "volume": 30}, "cards": []}
    ep = {
        "version": 1, "id": ep_id, "n": n, "idea": "ไอเดีย", "title": title, "voice_id": TOON_VOICE, "stage": "cards",
        "acts": [{"id": "a_00000001", "name": "เปิด", "segments": [segment]}],
    }  # fmt: skip
    folder = project.series_dir(series_id) / "eps" / ep_id
    folder.mkdir(parents=True)
    (folder / "ep.json").write_text(json.dumps(ep), encoding="utf-8")


def test_eps_using_a_sound_are_listed_by_series_name_then_ep_number(client, project, tmp_path):
    sound = import_tone(client, tmp_path)
    for name, eps in (("ผีบ้านไม้", ((2, "e_00000002", "คืนฝนตก"), (1, "e_00000001", ""))), ("กองถ่ายผี", ((1, "e_00000003", "ไฟดับ"),))):
        series_id = new_series(client, name=name)["id"]
        for n, ep_id, title in eps:
            write_ep_playing(project, series_id, ep_id, n, title, sound["id"])
    refused = client.delete(f"{SOUNDS}/{sound['id']}").json()
    assert refused["users"] == [
        {"tab": "toon", "label": "กองถ่ายผี · EP 1 ไฟดับ"},
        {"tab": "toon", "label": "ผีบ้านไม้ · EP 1"},
        {"tab": "toon", "label": "ผีบ้านไม้ · EP 2 คืนฝนตก"},
    ]


def test_the_old_toon_sound_routes_are_gone(client, tmp_path):
    sound = import_tone(client, tmp_path)
    old = "/api/toon/sounds"
    for method, path in (
        ("GET", old),
        ("PATCH", f"{old}/{sound['id']}"),
        ("DELETE", f"{old}/{sound['id']}"),
        ("GET", f"{old}/{sound['id']}/file"),
        ("POST", f"{old}/imports/check"),
        ("POST", f"{old}/downloads"),
        ("GET", f"{old}/import/current"),
    ):
        response = client.request(method, path, json={} if method in ("PATCH", "POST") else None)
        assert (method, path, response.status_code) == (method, path, 404)
    assert client.get(SOUNDS).json() == [sound]


def test_a_start_removes_a_conversion_cut_short(client, project):
    project.sounds_dir.mkdir(parents=True)
    (project.sounds_dir / "m_01234567.m4a.partial").write_bytes(b"half")
    with client:  # the app's start-up runs each job holder's clean
        pass
    assert not (project.sounds_dir / "m_01234567.m4a.partial").exists()


class PausedConvert:
    """ffmpeg converting a sound, until the job's `cancel` is set: ffmpeg running long."""

    def __init__(self):
        self.reached = threading.Event()
        self.cancelled = False

    def __call__(self, command: list[str], cwd: Path, cancel: threading.Event, on_progress=None) -> None:
        Path(command[-1]).write_bytes(b"half")  # as far as ffmpeg got
        self.reached.set()
        self.cancelled = cancel.wait(5)
        raise ffmpeg.Cancelled() if self.cancelled else AssertionError("the import never cancelled ffmpeg")


def test_a_page_that_goes_away_while_ffmpeg_converts_its_file_stops_ffmpeg_and_adds_no_sound(
    client, project, tmp_path, monkeypatch
):
    paused = PausedConvert()
    monkeypatch.setattr(sounds, "sound_imports", sounds.SoundImports(convert=paused))
    data = tone(tmp_path / "in.wav", 1).read_bytes()
    upload = Upload(data, then="leave")

    async def main():
        async with anyio.create_task_group() as group:
            group.start_soon(play, upload, "ฝนตก.wav", len(data), f"{SOUNDS}/imports")
            assert await anyio.to_thread.run_sync(paused.reached.wait, 5)
            upload.leave()

    anyio.run(main)

    assert paused.cancelled
    assert client.get(SOUNDS).json() == []
    assert list(project.sounds_partial_dir.iterdir()) == []
    assert [path for path in project.sounds_dir.iterdir() if path != project.sounds_partial_dir] == []
    monkeypatch.setattr(sounds, "sound_imports", sounds.SoundImports())
    assert import_file(client, "ฝนตก.wav", data).status_code == 201


def test_a_page_that_goes_away_as_ffmpeg_ends_adds_no_sound(client, project, tmp_path, monkeypatch):
    # The page is asked about once a second at most here, so only the last question before
    # the sound comes in can see it gone.
    monkeypatch.setattr(sounds, "GONE_POLL_SECONDS", 1)
    data = tone(tmp_path / "in.wav", 1).read_bytes()
    upload = Upload(data, then="leave")

    def convert_then_leave(command, cwd, cancel, on_progress=None):
        ffmpeg.run(command, cwd, cancel, on_progress)
        anyio.from_thread.run_sync(upload.leave)

    monkeypatch.setattr(sounds, "sound_imports", sounds.SoundImports(convert=convert_then_leave))

    anyio.run(play, upload, "ฝนตก.wav", len(data), f"{SOUNDS}/imports")

    assert client.get(SOUNDS).json() == []
    assert list(project.sounds_partial_dir.iterdir()) == []
    assert [path for path in project.sounds_dir.iterdir() if path != project.sounds_partial_dir] == []


# --- a library that matches its m4a files (D70) ---


def bad_copies(project) -> list[Path]:
    return sorted(project.sounds_dir.glob("sounds.json.bad-*"))


def test_an_unreadable_library_is_kept_aside_at_start_and_its_sounds_come_back_named_by_id(client, project, tmp_path):
    rain, wind = import_tone(client, tmp_path, "ฝน.wav"), import_tone(client, tmp_path, "ลม.wav")
    write_library(project, "{not json")
    restart(client)
    listed = client.get(SOUNDS).json()
    assert sorted((s["id"], s["name"], s["source"]) for s in listed) == sorted(
        (s["id"], s["id"], "file") for s in (rain, wind)
    )
    assert [s["duration_s"] for s in listed] == [pytest.approx(1.5, abs=0.1)] * 2
    [kept] = bad_copies(project)
    assert re.fullmatch(r"sounds\.json\.bad-\d{8}-\d{6}-[0-9a-f]{4}", kept.name)
    assert kept.read_text(encoding="utf-8") == "{not json"


def test_a_library_of_another_version_is_kept_aside_and_recovered_the_same_way(client, project, tmp_path):
    rain = import_tone(client, tmp_path, "ฝน.wav")
    write_library(project, {"version": 2, "sounds": [rain]})
    restart(client)
    assert [(s["id"], s["name"]) for s in client.get(SOUNDS).json()] == [(rain["id"], rain["id"])]
    assert len(bad_copies(project)) == 1


def test_a_bad_entry_is_dropped_and_its_m4a_comes_back_named_by_id_but_an_m4a_off_the_id_pattern_stays_out(
    client, project, tmp_path
):
    rain, wind = import_tone(client, tmp_path, "ฝน.wav"), import_tone(client, tmp_path, "ลม.wav")
    (project.sounds_dir / "x_1.m4a").write_bytes((project.sounds_dir / f"{rain['id']}.m4a").read_bytes())
    write_library(
        project,
        {
            "version": 1,
            "sounds": [
                rain,
                wind | {"source": "tape"},
                {"id": "x_1", "name": "ชื่อผิดรูป", "duration_s": 1, "source": "file"},
                rain | {"name": "ซ้ำ"},
            ],
        },
    )
    restart(client)
    assert [(s["id"], s["name"]) for s in client.get(SOUNDS).json()] == [
        (rain["id"], "ฝน"),
        (wind["id"], wind["id"]),
    ]
    assert bad_copies(project) == []


def test_an_entry_with_no_m4a_is_gone_after_a_start(client, project, tmp_path):
    rain, wind = import_tone(client, tmp_path, "ฝน.wav"), import_tone(client, tmp_path, "ลม.wav")
    (project.sounds_dir / f"{wind['id']}.m4a").unlink()
    restart(client)
    assert client.get(SOUNDS).json() == [rain]


def test_an_m4a_ffmpeg_cannot_read_comes_back_with_no_length(client, project):
    project.sounds_dir.mkdir(parents=True)
    (project.sounds_dir / "m_0000000a.m4a").write_bytes(b"not a sound")
    restart(client)
    assert client.get(SOUNDS).json() == [{"id": "m_0000000a", "name": "m_0000000a", "duration_s": 0, "source": "file"}]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="a named pipe needs a POSIX system")
def test_an_m4a_ffmpeg_is_still_reading_after_its_time_comes_back_with_no_length(client, project, monkeypatch):
    # A named pipe nobody writes to: ffmpeg waits on it for as long as it is let.
    monkeypatch.setattr(sounds, "PROBE_SECONDS", 0.5)
    project.sounds_dir.mkdir(parents=True)
    os.mkfifo(project.sounds_dir / "m_0000000a.m4a")
    restart(client)
    assert client.get(SOUNDS).json()[0]["duration_s"] == 0


def test_a_library_that_matches_its_files_is_not_written_at_start(client, project, tmp_path):
    import_tone(client, tmp_path)
    before = project.sounds_file.stat()
    restart(client)
    after = project.sounds_file.stat()
    assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns)


def test_a_segment_on_a_recovered_sound_still_plays_it(client, llm, project, tmp_path):
    sound, ep, _ = with_sound_on_cards(client, llm, tmp_path)
    write_library(project, "{not json")
    restart(client)
    assert [s["id"] for s in client.get(SOUNDS).json()] == [sound["id"]]
    assert client.delete(f"{SOUNDS}/{sound['id']}").json()["code"] == "in_use"


def test_with_no_library_one_import_is_one_sound(client, project, tmp_path):
    sound = import_tone(client, tmp_path)
    assert client.get(SOUNDS).json() == [sound]
    assert [s["id"] for s in json.loads(project.sounds_file.read_text(encoding="utf-8"))["sounds"]] == [sound["id"]]


def test_a_library_broken_while_the_app_runs_keeps_every_sound_through_the_next_import(client, project, tmp_path):
    rain, wind = import_tone(client, tmp_path, "ฝน.wav"), import_tone(client, tmp_path, "ลม.wav")
    write_library(project, "{not json")
    fire = import_tone(client, tmp_path, "ไฟ.wav")
    listed = {s["id"]: s for s in client.get(SOUNDS).json()}
    assert sorted(listed) == sorted([rain["id"], wind["id"], fire["id"]])
    assert [listed[s["id"]]["name"] for s in (rain, wind, fire)] == [rain["id"], wind["id"], "ไฟ"]
    assert (listed[rain["id"]]["duration_s"], listed[wind["id"]]["duration_s"]) == (0, 0)  # until the next start
    assert len(bad_copies(project)) == 1
    restart(client)
    timed = {s["id"]: s["duration_s"] for s in client.get(SOUNDS).json()}
    assert [timed[rain["id"]], timed[wind["id"]]] == [pytest.approx(1.5, abs=0.1)] * 2


def test_a_recovered_library_that_cannot_be_written_is_still_read(client, project, tmp_path, monkeypatch):
    rain = import_tone(client, tmp_path)
    write_library(project, "{not json")

    def refuse(*args, **kwargs):
        raise OSError("read-only")

    monkeypatch.setattr(files, "write_atomic", refuse)
    response = client.get(SOUNDS)
    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == [rain["id"]]


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="a read-only folder needs a POSIX user")
def test_a_library_that_cannot_be_kept_aside_is_recovered_but_never_written_over(client, project, tmp_path):
    rain = import_tone(client, tmp_path)
    write_library(project, "{not json")
    project.sounds_dir.chmod(0o555)
    try:
        assert [s["id"] for s in client.get(SOUNDS).json()] == [rain["id"]]
        with pytest.raises(OSError):  # the test client raises what the app would answer 500 with
            client.patch(f"{SOUNDS}/{rain['id']}", json={"name": "ฝน"})
    finally:
        project.sounds_dir.chmod(0o755)
    assert project.sounds_file.read_text(encoding="utf-8") == "{not json"


def test_a_sound_whose_m4a_came_in_before_a_crash_is_in_the_library_after_a_start(client, project, tmp_path):
    rain = import_tone(client, tmp_path, "ฝน.wav")
    m4a = project.sounds_dir / "m_0000000b.m4a"
    m4a.write_bytes((project.sounds_dir / f"{rain['id']}.m4a").read_bytes())  # placed, `sounds.json` not written
    restart(client)
    assert [(s["id"], s["name"]) for s in client.get(SOUNDS).json()] == [(rain["id"], "ฝน"), ("m_0000000b", "m_0000000b")]


def test_a_sound_deleted_before_a_crash_does_not_come_back(client, project, tmp_path, monkeypatch):
    rain = import_tone(client, tmp_path)

    def crash(*args, **kwargs):
        raise RuntimeError("the app stopped here")

    with monkeypatch.context() as patched:
        patched.setattr(sounds, "write_sounds", crash)
        with pytest.raises(RuntimeError):
            client.delete(f"{SOUNDS}/{rain['id']}")
    restart(client)
    assert client.get(SOUNDS).json() == []


# --- `.partial/` of the library (D11) ---


def test_a_file_s_upload_and_conversion_go_through_the_library_s_partial_folder(client, project, tmp_path, monkeypatch):
    paused = PausedConvert()
    monkeypatch.setattr(sounds, "sound_imports", sounds.SoundImports(convert=paused))
    data = tone(tmp_path / "in.wav", 1).read_bytes()
    upload = Upload(data, then="leave")

    async def main():
        async with anyio.create_task_group() as group:
            group.start_soon(play, upload, "ฝนตก.wav", len(data), f"{SOUNDS}/imports")
            assert await anyio.to_thread.run_sync(paused.reached.wait, 5)
            assert sorted(path.suffix for path in project.sounds_partial_dir.iterdir()) == [".partial", ".upload"]
            upload.leave()

    anyio.run(main)


def test_a_start_empties_the_library_s_partial_folder(client, project):
    (project.sounds_partial_dir / "left").mkdir(parents=True)
    (project.sounds_partial_dir / "left" / "m_01234567.webm").write_bytes(b"half")
    (project.sounds_partial_dir / "m_01234567.m4a.partial").write_bytes(b"half")
    restart(client)
    assert not project.sounds_partial_dir.exists()


# --- the move from `media/toon/sounds/` (D6, D10) ---

LEGACY = "/api/sounds/legacy"


def to_legacy_folder(project) -> None:
    """The library as an older app kept it, in `media/toon/sounds/`."""
    project.legacy_sounds_dir.parent.mkdir(parents=True, exist_ok=True)
    project.sounds_dir.rename(project.legacy_sounds_dir)


def test_an_old_library_moves_to_media_sounds_at_start_with_its_ids(client, project, tmp_path, caplog):
    rain, wind = import_tone(client, tmp_path, "ฝน.wav"), import_tone(client, tmp_path, "ลม.wav")
    to_legacy_folder(project)
    with caplog.at_level("INFO", logger="backend"):
        restart(client)
    assert client.get(SOUNDS).json() == [rain, wind]
    assert not project.legacy_sounds_dir.exists()
    assert "moved sound library to media/sounds" in caplog.text
    assert client.get(LEGACY).json() == {"left_behind": None}


def test_an_old_library_beside_a_new_one_is_merged_keeping_the_new_one_s_copy_of_a_shared_id(client, project, tmp_path):
    rain, wind = import_tone(client, tmp_path, "ฝน.wav"), import_tone(client, tmp_path, "ลม.wav")
    to_legacy_folder(project)
    project.sounds_dir.mkdir()
    (project.sounds_dir / f"{rain['id']}.m4a").write_bytes((project.legacy_sounds_dir / f"{rain['id']}.m4a").read_bytes())
    write_library(project, {"version": 1, "sounds": [rain | {"name": "ฝนใหม่"}]})
    restart(client)
    assert client.get(SOUNDS).json() == [rain | {"name": "ฝนใหม่"}, wind]
    assert not project.legacy_sounds_dir.exists()


def test_an_old_library_moves_whole_onto_a_new_folder_that_holds_only_partial(client, project, tmp_path):
    rain = import_tone(client, tmp_path, "ฝน.wav")
    to_legacy_folder(project)
    (project.sounds_partial_dir / "m_01234567.upload").parent.mkdir(parents=True)
    (project.sounds_partial_dir / "m_01234567.upload").write_bytes(b"half")
    restart(client)
    assert client.get(SOUNDS).json() == [rain]
    assert not project.legacy_sounds_dir.exists()


def test_a_move_that_fails_half_way_is_finished_by_a_later_start(client, project, tmp_path, monkeypatch):
    rain, wind, fire = (import_tone(client, tmp_path, f"{name}.wav") for name in ("ฝน", "ลม", "ไฟ"))
    to_legacy_folder(project)
    project.sounds_dir.mkdir()
    (project.legacy_sounds_dir / f"{fire['id']}.m4a").rename(project.sounds_dir / f"{fire['id']}.m4a")
    write_library(project, {"version": 1, "sounds": [fire]})
    first, second = sorted((rain, wind), key=lambda sound: sound["id"])  # the order the move takes them
    replace = os.replace

    def fail_on_the_second(source, target):
        if Path(source).name == f"{second['id']}.m4a":
            raise OSError("no space left on device")
        replace(source, target)

    with monkeypatch.context() as patched:
        patched.setattr(os, "replace", fail_on_the_second)
        restart(client)
    assert client.get(SOUNDS).json() == [fire, first]
    assert client.get(LEGACY).json() == {"left_behind": "media/toon/sounds"}
    new = import_tone(client, tmp_path, "น้ำ.wav")
    restart(client)
    listed = client.get(SOUNDS).json()
    assert sorted(listed, key=lambda sound: sound["id"]) == sorted([fire, rain, wind, new], key=lambda sound: sound["id"])
    assert client.get(LEGACY).json() == {"left_behind": None}
    assert not project.legacy_sounds_dir.exists()


def test_an_ep_on_a_sound_of_the_old_library_still_plays_it_after_the_move(client, project, tmp_path):
    rain = import_tone(client, tmp_path, "ฝน.wav")
    series_id = new_series(client)["id"]
    write_ep_playing(project, series_id, "e_00000001", 1, "คืนฝนตก", rain["id"])
    to_legacy_folder(project)
    restart(client)
    changed = client.patch("/api/toon/eps/e_00000001/segments/g_00000001", json={"sound": {"sound_id": rain["id"], "volume": 40}})
    assert changed.status_code == 200, changed.json()
    refused = client.delete(f"{SOUNDS}/{rain['id']}")
    assert refused.status_code == 409
    assert refused.json()["users"] == [{"tab": "toon", "label": "รุ่นพี่เล่าว่า… · EP 1 คืนฝนตก"}]


def test_an_old_m4a_the_new_library_lists_without_its_file_moves_under_the_new_entry(client, project, tmp_path):
    rain = import_tone(client, tmp_path, "ฝน.wav")
    to_legacy_folder(project)
    project.sounds_dir.mkdir()
    write_library(project, {"version": 1, "sounds": [rain | {"name": "ฝนใหม่"}]})  # its m4a lost
    restart(client)
    assert client.get(SOUNDS).json() == [rain | {"name": "ฝนใหม่"}]
    assert not project.legacy_sounds_dir.exists()


def test_an_old_m4a_not_named_by_a_sound_id_stays_where_it_is_and_is_not_left_behind(client, project, tmp_path):
    rain = import_tone(client, tmp_path, "ฝน.wav")
    to_legacy_folder(project)
    (project.legacy_sounds_dir / "เพลงของฉัน.m4a").write_bytes(b"the user's own file")
    project.sounds_dir.mkdir()
    write_library(project, {"version": 1, "sounds": []})
    restart(client)
    assert client.get(SOUNDS).json() == [rain]
    assert (project.legacy_sounds_dir / "เพลงของฉัน.m4a").read_bytes() == b"the user's own file"
    assert client.get(LEGACY).json() == {"left_behind": None}
