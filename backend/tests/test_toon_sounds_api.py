"""The background sound library under /api/toon/sounds: a file's Sound import with real ffmpeg,
a link's with a fake yt-dlp adapter, `in_use`, `sound: null`, and the Cards job picking a sound
(toon seam 1 › Sound import, `in_use` ของเสียง, `sound: null`)."""

import threading
from pathlib import Path

import anyio
import deno
import pytest

from backend import checks, ffmpeg, spoil
from backend.spoil.adapter import DownloadOptions, YtDlpAdapter, select_formats
from backend.toon import sounds, store

from .fakes import (
    FINISHED,
    TOON_SOUNDS,
    FakeAdapter,
    Upload,
    Writer,
    cards_of,
    import_file,
    import_tone,
    new_ep,
    ok_deno,
    ok_yt_dlp,
    play,
    poll_until,
    run,
    start,
    tone,
    toon_api,
    with_series,
    youtube_info,
)

IMPORT = "/api/toon/sounds/import/current"


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
    response = client.post(f"{TOON_SOUNDS}/downloads", json={"url": url})
    assert response.status_code == 202, response.json()
    return poll_until(client, IMPORT, lambda job: job["state"] in FINISHED)


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


def test_a_sound_link_s_options_take_the_best_audio_into_toon_partial_with_no_thumbnail_or_merge(project, no_deno):
    params = YtDlpAdapter()._params(project, "m_01234567", sounds.LINK_OPTIONS)
    assert params["format"] == "bestaudio"
    assert "merge_output_format" not in params
    assert params["writethumbnail"] is False
    assert params["paths"] == {"home": str(project.toon_partial_dir), "temp": str(project.toon_partial_dir)}
    assert params["outtmpl"] == "m_01234567.%(ext)s"


# --- a file ---


def test_a_wav_file_comes_in_as_aac_in_m4a_named_after_the_file(client, project, tmp_path):
    sound = import_tone(client, tmp_path, "ฝนตกในป่า.wav", seconds=1.5)
    assert sound["name"] == "ฝนตกในป่า"
    assert sound["source"] == "file"
    assert sound["duration_s"] == pytest.approx(1.5, abs=0.1)
    m4a = project.toon_sounds_dir / f"{sound['id']}.m4a"
    info = ffmpeg.input_info(m4a)
    assert "Audio: aac" in info and "48000 Hz" in info and "stereo" in info
    assert [s.id for s in store.read_sounds(project)] == [sound["id"]]
    assert client.get(TOON_SOUNDS).json() == [sound]
    assert client.get(f"{TOON_SOUNDS}/{sound['id']}/file").content == m4a.read_bytes()
    assert not list(project.toon_partial_dir.iterdir())


def test_a_file_ffmpeg_reads_no_sound_in_is_unsupported_file(client, project):
    response = import_file(client, "notes.mp3", "ไม่ใช่เสียง".encode() * 100)
    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_file"
    assert client.get(TOON_SOUNDS).json() == []


def test_a_file_over_twenty_minutes_is_too_long(client, tmp_path):
    long = tone(tmp_path / "long.wav", sounds.MAX_SECONDS + 1, rate=8_000)
    response = import_file(client, "long.wav", long.read_bytes())
    assert response.status_code == 400
    assert response.json()["code"] == "too_long"


def test_a_file_over_200_mb_is_refused_at_the_check(client):
    response = client.post(f"{TOON_SOUNDS}/imports/check", json={"name": "big.wav", "size": sounds.UPLOAD_MAX_BYTES + 1})
    assert response.status_code == 400
    assert response.json()["code"] == "file_too_large"
    assert client.post(f"{TOON_SOUNDS}/imports/check", json={"name": "ok.wav", "size": 1000}).json() == {"size": 1000}


def test_a_sound_is_renamed_within_1_to_60_letters(client, tmp_path):
    sound = import_tone(client, tmp_path)
    assert client.patch(f"{TOON_SOUNDS}/{sound['id']}", json={"name": " ลมพัด "}).json()["name"] == "ลมพัด"
    assert client.patch(f"{TOON_SOUNDS}/{sound['id']}", json={"name": ""}).json()["code"] == "invalid_request"


# --- a link ---


def test_a_link_loads_its_best_audio_into_toon_partial_with_no_thumbnail_and_comes_in_named_after_the_clip(
    client, adapter, project
):
    job = download(client)
    assert job["state"] == "done", job
    assert all(options == sounds.LINK_OPTIONS for options in adapter.options)
    assert adapter.landed == [f"{adapter.clip_ids[0]}.webm"]
    [sound] = client.get(TOON_SOUNDS).json()
    assert sound == {"id": job["sound_id"], "name": "ฝนตกในป่า", "duration_s": pytest.approx(2, abs=0.1), "source": "link"}
    assert (project.toon_sounds_dir / f"{sound['id']}.m4a").is_file()
    assert not list(project.toon_partial_dir.iterdir())


def test_a_link_spoil_s_rules_refuse_is_invalid_url(client):
    for url in ("ftp://example.com/a.mp3", "http://127.0.0.1/a.mp3", "not a link"):
        response = client.post(f"{TOON_SOUNDS}/downloads", json={"url": url})
        assert response.status_code == 400
        assert response.json()["code"] == "invalid_url"


def test_a_link_over_twenty_minutes_by_its_info_fails_too_long_before_loading(client, adapter):
    adapter.info["duration"] = sounds.MAX_SECONDS + 1
    job = download(client)
    assert job["state"] == "failed"
    assert job["error"]["code"] == "too_long"
    assert adapter.clip_ids == []


def test_a_second_sound_import_while_one_runs_is_busy_but_one_during_a_toon_job_starts(client, llm, adapter):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.pause_at(0)
    assert start(client, "plot", ep_id).status_code == 202
    llm.wait_until(0)
    adapter.pause_at("progress")
    assert client.post(f"{TOON_SOUNDS}/downloads", json={"url": "https://youtu.be/dQw4w9WgXcQ"}).status_code == 202
    adapter.wait_until("progress")
    again = client.post(f"{TOON_SOUNDS}/downloads", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
    assert (again.status_code, again.json()["code"]) == (409, "busy")
    assert import_file(client, "a.wav", b"x" * 10).json()["code"] == "busy"
    adapter.release("progress")
    llm.release(0)
    assert poll_until(client, IMPORT, lambda job: job["state"] in FINISHED)["state"] == "done"


# --- in use ---


def with_sound_on_cards(client, llm, tmp_path) -> tuple[str, dict, dict]:
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
    refused = client.delete(f"{TOON_SOUNDS}/{sound['id']}")
    assert refused.status_code == 409
    assert refused.json()["code"] == "in_use"
    assert refused.json()["eps"] == [{"series_name": "รุ่นพี่เล่าว่า…", "n": 1, "title": ep["title"]}]
    for segment in (s for act in ep["acts"] for s in act["segments"]):
        changed = client.patch(f"/api/toon/eps/{ep['id']}/segments/{segment['id']}", json={"sound": None})
        assert changed.status_code == 200
    after = client.get(f"/api/toon/eps/{ep['id']}").json()
    assert {s["sound"] is None for act in after["acts"] for s in act["segments"]} == {True}
    assert client.delete(f"{TOON_SOUNDS}/{sound['id']}").status_code == 204
    assert not (project.toon_sounds_dir / f"{sound['id']}.m4a").exists()
    assert len(cards_of(after)) == len(cards_of(ep))


def test_a_start_removes_a_conversion_cut_short(client, project):
    project.toon_sounds_dir.mkdir(parents=True)
    (project.toon_sounds_dir / "m_01234567.m4a.partial").write_bytes(b"half")
    with client:  # the app's start-up runs each job holder's clean
        pass
    assert not (project.toon_sounds_dir / "m_01234567.m4a.partial").exists()


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
            group.start_soon(play, upload, "ฝนตก.wav", len(data), f"{TOON_SOUNDS}/imports")
            assert await anyio.to_thread.run_sync(paused.reached.wait, 5)
            upload.leave()

    anyio.run(main)

    assert paused.cancelled
    assert client.get(TOON_SOUNDS).json() == []
    assert list(project.toon_partial_dir.iterdir()) == []
    assert list(project.toon_sounds_dir.iterdir()) == []
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

    anyio.run(play, upload, "ฝนตก.wav", len(data), f"{TOON_SOUNDS}/imports")

    assert client.get(TOON_SOUNDS).json() == []
    assert list(project.toon_partial_dir.iterdir()) == []
    assert list(project.toon_sounds_dir.iterdir()) == []
