"""The Render job of the การ์ตูนเล่า tab under /api/toon/render and its results, with a fake
OmniVoice child and real ffmpeg on solid-colour card pictures and short narration the test
makes (toon seam 1 › Render job ระหว่าง Image job, seam 2 › render จริง)."""

import io
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import pytest
from PIL import Image

from backend import app as app_module
from backend import ffmpeg, gpu
from backend.paths import ProjectPaths
from backend.toon import render, sounds
from backend.toon.store import CardImage

from .fakes import FakeFfmpeg, poll_until, toon_api
from .test_toon_eps_api import Writer, cards_of, edit_stored, gpu_refusal, new_ep, run, start
from .test_toon_images_api import add
from .test_toon_series_api import create
from .test_toon_sounds_api import import_tone

EPS = "/api/toon/eps"
RENDER = "/api/toon/render"
CURRENT = "/api/toon/render/current"
FINISHED = {"done", "failed", "cancelled"}
COLOURS = [(220, 30, 30), (30, 200, 40), (40, 60, 220)]


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


llm, klein, tts, client = toon_api(lambda: Writer().respond, tts_seconds=1.0, uses=("renderer",))


@pytest.fixture
def renderer(monkeypatch) -> FakeFfmpeg:
    """Real ffmpeg behind a stand-in that can pause a run (`fastapi-api` › testing)."""
    fake = FakeFfmpeg(progress=(), then=ffmpeg.run)
    monkeypatch.setattr(render, "render_jobs", render.RenderJobs(run_ffmpeg=fake))
    return fake


def three_cards(client, llm, project, layout: str = "frame", channel_name: str = "รุ่นพี่เล่าว่า", sounds=(None, None)):
    """A one-act Series with a character and a background, and an EP of three cards over two
    segments: the character speaks, a silent card holds 2 s, the character speaks again. Each
    card's picture is a solid colour of `COLOURS`; no card has narration yet."""
    series_id = create(client, layout=layout, channel_name=channel_name, acts=["เปิด"])["id"]
    character = add(client, series_id, "characters", "พีค")
    client.patch(f"/api/toon/series/{series_id}/characters/{character}", json={"tag": "สายแฟ"})
    background = add(client, series_id, "backgrounds", "กองไฟ")
    writer = llm.respond.__self__
    writer.plot = {
        "title": "เสียงเรียกจากป่า",
        "acts": [{"summary": "รุ่นพี่ตั้งแคมป์"}],
        "characters": [{"id": character}],
        "backgrounds": [{"id": background}],
    }

    def card(text: str, characters: list[str]) -> dict:
        return {"text": text, "characters": characters, "description": "", "motion": "zoom_in"}

    writer.cards = lambda act: {
        "segments": [
            {"background": background, "sound": sounds[0], "cards": [card("คืนนั้นเราตั้งแคมป์", [character]), card("", [])]},
            {"background": background, "sound": sounds[1], "cards": [card("พีคได้ยินเสียงเรียก", [character])]},
        ]
    }
    ep_id = new_ep(client, series_id)["id"]
    assert run(client, "plot", ep_id)["state"] == "done"
    assert run(client, "cards", ep_id)["state"] == "done"
    size = (1024, 576) if layout == "frame" else (576, 1024)
    refs = {character: 1, background: 1}
    folder = project.card_images_dir(series_id, ep_id)
    folder.mkdir(parents=True, exist_ok=True)

    def paint(ep):
        for (_, stored), colour in zip(((s, c) for a in ep.acts for s in a.segments for c in s.cards), COLOURS, strict=True):
            out = io.BytesIO()
            Image.new("RGB", size, colour).save(out, "PNG")
            (folder / f"{stored.id}-1.png").write_bytes(out.getvalue())
            used = {background: 1} | {i: 1 for i in stored.character_ids}
            stored.image = CardImage(file=f"{stored.id}-1.png", refs={k: refs[k] for k in used})

    edit_stored(project, series_id, ep_id, paint)
    return series_id, client.get(f"{EPS}/{ep_id}").json()


def start_render(client, ep_id: str):
    return client.post(RENDER, json={"ep_id": ep_id})


def rendered(client, ep_id: str) -> dict:
    response = start_render(client, ep_id)
    assert response.status_code == 202, response.json()
    return poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)


def colour_at(mp4, seconds: float) -> tuple[int, int, int]:
    """The pixel at the centre of the picture's area, the frame at `seconds`."""
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-ss", f"{seconds:.3f}", "-i", str(mp4),
        "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-",
    ]  # fmt: skip
    frame = Image.open(io.BytesIO(subprocess.run(command, check=True, capture_output=True).stdout)).convert("RGB")
    return frame.getpixel((540, 960))


def near(found, wanted, slack: int = 40) -> bool:
    return all(abs(a - b) <= slack for a, b in zip(found, wanted, strict=True))


# --- render จริง (seam 2) ---


def test_a_frame_render_of_three_cards_is_1080x1920_30fps_h264_aac_as_long_as_its_cards_in_their_colours(
    client, llm, project, tts
):
    series_id, ep = three_cards(client, llm, project)
    job = rendered(client, ep["id"])
    assert job["state"] == "done", job
    ep = client.get(f"{EPS}/{ep['id']}").json()
    lengths = [card["duration_s"] for card in cards_of(ep)]
    assert lengths == [1.3, 2.0, 1.3]  # 1 s of narration + 0.3 s gap; the silent card holds 2 s
    mp4 = project.ep_renders_dir(series_id, ep["id"]) / f"{job['name']}.mp4"
    info = ffmpeg.input_info(mp4)
    assert re.search(r"Video: h264.*1080x1920.*30 fps", info), info
    assert "Audio: aac" in info
    assert ffmpeg.probe(mp4).duration_s == pytest.approx(sum(lengths), abs=0.1)
    starts = [0.0, 1.3, 3.3]
    for at, length, colour in zip(starts, lengths, COLOURS, strict=True):
        assert near(colour_at(mp4, at + length / 2), colour), (at, colour_at(mp4, at + length / 2))
    names = sorted(path.name for path in mp4.parent.iterdir())
    assert names == [f"{job['name']}{suffix}" for suffix in (".json", ".mp4", ".srt")]
    assert "คืนนั้นเราตั้งแคมป์" in (mp4.parent / f"{job['name']}.srt").read_text(encoding="utf-8")


def test_a_full_render_s_ass_tags_a_character_on_its_first_card_only_and_has_no_title(client, llm, project, renderer):
    _, ep = three_cards(client, llm, project, layout="full")
    renderer.pause_at(0)
    assert start_render(client, ep["id"]).status_code == 202
    renderer.wait_until(0)
    ass = (project.toon_render_dir / render.CAPTIONS).read_text(encoding="utf-8")
    renderer.release(0)
    tags = [line for line in ass.splitlines() if line.startswith("Dialogue") and ",Tag," in line]
    assert len(tags) == 1
    assert tags[0].startswith("Dialogue: 0,0:00:00.00,0:00:01.30,Tag,")
    assert tags[0].endswith("พีค / สายแฟ")
    assert "\\an7" in tags[0]
    assert ",Title," not in ass and ",Ep," not in ass and ",Channel," not in ass
    assert "เสียงเรียกจากป่า" not in ass
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"


@pytest.mark.parametrize("channel_name", ["รุ่นพี่เล่าว่า", ""])
def test_a_frame_render_s_ass_has_the_title_its_ep_tag_and_the_channel_name_unless_empty(
    client, llm, project, renderer, channel_name
):
    _, ep = three_cards(client, llm, project, channel_name=channel_name)
    renderer.pause_at(0)
    assert start_render(client, ep["id"]).status_code == 202
    renderer.wait_until(0)
    ass = (project.toon_render_dir / render.CAPTIONS).read_text(encoding="utf-8")
    renderer.release(0)
    assert re.search(r",Title,.*เสียงเรียกจากป่า$", ass, re.MULTILINE)
    assert re.search(r",Ep,.*EP01$", ass, re.MULTILINE)
    assert bool(re.search(r",Channel,.*รุ่นพี่เล่าว่า$", ass, re.MULTILINE)) == bool(channel_name)
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"


def test_a_title_longer_than_two_lines_is_cut_with_an_ellipsis(client, llm, project, renderer):
    _, ep = three_cards(client, llm, project)
    long = "เสียงเรียกจากป่าลึก คืนฝนตกหนัก ไฟดับทั้งแคมป์ ไม่มีใครกล้า"  # ≤ 60 letters, > 2 lines
    assert client.patch(f"{EPS}/{ep['id']}", json={"title": long}).status_code == 200
    renderer.pause_at(0)
    assert start_render(client, ep["id"]).status_code == 202
    renderer.wait_until(0)
    ass = (project.toon_render_dir / render.CAPTIONS).read_text(encoding="utf-8")
    renderer.release(0)
    [title] = [line for line in ass.splitlines() if ",Title," in line]
    assert title.count("\\N") == 1
    assert title.endswith("…")
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"


def test_segments_in_a_row_on_one_sound_are_one_run_and_a_new_sound_crossfades_for_a_second(
    client, llm, project, renderer, tmp_path
):
    rain = import_tone(client, tmp_path, "ฝน.wav", seconds=1.0)["id"]
    _, same = three_cards(client, llm, project, sounds=(rain, rain))
    assert rendered(client, same["id"])["state"] == "done"
    final = renderer.commands[-1]
    assert final.count(f"{rain}.m4a") == 1
    assert "acrossfade" not in final[final.index("-filter_complex") + 1]
    wind = import_tone(client, tmp_path, "ลม.wav", seconds=1.0)["id"]
    _, changing = three_cards(client, llm, project, sounds=(rain, wind))
    job = rendered(client, changing["id"])
    assert job["state"] == "done", job
    graph = renderer.commands[-1][renderer.commands[-1].index("-filter_complex") + 1]
    assert "acrossfade=d=1.000" in graph
    assert f"{wind}.m4a" in renderer.commands[-1]


# --- the job (seam 1) ---


def test_cards_with_no_narration_are_voiced_first_then_rendered_with_the_gpu_free(client, llm, project, tts, renderer):
    _, ep = three_cards(client, llm, project)
    tts.pause_at(0)
    renderer.pause_at(0)
    job = start_render(client, ep["id"]).json()
    assert (job["state"], job["done"], job["total"]) == ("voicing", 0, 2)
    tts.wait_until(0)
    assert gpu_refusal().code == "gpu_busy"
    tts.release(0)
    renderer.wait_until(0)
    assert client.get(CURRENT).json()["state"] == "rendering"
    assert gpu_refusal() is None
    renderer.release(0)
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"
    statuses = [card["audio_status"] for card in cards_of(client.get(f"{EPS}/{ep['id']}").json())]
    assert statuses == ["ready", "silent", "ready"]
    assert tts.processes[0].asked_to_end  # OmniVoice is told to exit, not only stopped


def test_a_cancel_while_voicing_stops_omnivoice_and_keeps_the_narration_already_spoken(client, llm, project, tts):
    _, ep = three_cards(client, llm, project)
    tts.pause_at(1)
    assert start_render(client, ep["id"]).status_code == 202
    tts.wait_until(1)
    assert poll_until(client, CURRENT, lambda job: job["done"] == 1)["total"] == 2
    client.delete(CURRENT)
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED)["state"] == "cancelled"
    assert tts.processes[0].terminated
    statuses = [card["audio_status"] for card in cards_of(client.get(f"{EPS}/{ep['id']}").json())]
    assert statuses == ["ready", "silent", "no_audio"]


def test_a_render_of_an_ep_with_its_narration_starts_during_an_image_job_and_a_second_is_busy(
    client, llm, project, klein, renderer
):
    _, ep = three_cards(client, llm, project)
    assert rendered(client, ep["id"])["state"] == "done"  # voices every card
    klein.pause_at(1)
    assert client.post("/api/toon/jobs", json={"kind": "image", "ep_id": ep["id"], "card_id": cards_of(ep)[0]["id"]}).status_code == 202
    klein.wait_until(1)
    first_run = len(renderer.commands)  # this render's first ffmpeg run: the first render's came before
    renderer.pause_at(first_run)
    job = start_render(client, ep["id"])
    assert job.status_code == 202, job.json()
    assert job.json()["state"] == "rendering"
    again = start_render(client, ep["id"])
    assert (again.status_code, again.json()["code"]) == (409, "busy")
    renderer.release(first_run)
    klein.release(1)
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"


def test_a_render_of_an_ep_a_cards_job_works_on_is_ep_locked(client, llm, project):
    _, ep = three_cards(client, llm, project)
    client.patch(f"{EPS}/{ep['id']}/acts/{ep['acts'][0]['id']}", json={"summary": "เรื่องใหม่"})
    llm.pause_at(0)  # the Cards job's own child, from its first request
    assert start(client, "cards", ep["id"], confirm_loss=True).status_code == 202
    llm.wait_until(0)
    response = start_render(client, ep["id"])
    assert (response.status_code, response.json()["code"]) == (409, "ep_locked")
    llm.release(0)


def test_a_cards_job_on_an_ep_a_render_works_on_is_ep_busy(client, llm, project, renderer):
    _, ep = three_cards(client, llm, project)
    assert rendered(client, ep["id"])["state"] == "done"  # voices every card: the next render needs no GPU
    client.patch(f"{EPS}/{ep['id']}/acts/{ep['acts'][0]['id']}", json={"summary": "เรื่องใหม่"})
    first_run = len(renderer.commands)
    renderer.pause_at(first_run)
    assert start_render(client, ep["id"]).status_code == 202
    renderer.wait_until(first_run)
    response = start(client, "cards", ep["id"], confirm_loss=True)
    assert (response.status_code, response.json()["code"]) == (409, "ep_busy")
    renderer.release(first_run)
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"


def test_a_plot_job_on_an_ep_a_render_works_on_is_ep_busy(client, llm, project, renderer):
    _, ep = three_cards(client, llm, project)
    assert rendered(client, ep["id"])["state"] == "done"  # voices every card: the next render needs no GPU
    first_run = len(renderer.commands)
    renderer.pause_at(first_run)
    assert start_render(client, ep["id"]).status_code == 202
    renderer.wait_until(first_run)
    response = start(client, "plot", ep["id"])
    assert (response.status_code, response.json()["code"]) == (409, "ep_busy")  # before `plot_confirmed`
    renderer.release(first_run)
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)["state"] == "done"


def test_a_render_with_a_card_with_no_picture_is_cards_not_ready_naming_it(client, llm, project):
    series_id, ep = three_cards(client, llm, project)
    second = cards_of(ep)[1]["id"]

    def unpaint(stored):
        next(c for a in stored.acts for s in a.segments for c in s.cards if c.id == second).image = None

    edit_stored(project, series_id, ep["id"], unpaint)
    response = start_render(client, ep["id"])
    assert response.status_code == 400
    assert (response.json()["code"], response.json()["card_ids"]) == ("cards_not_ready", [second])


def test_a_cancel_during_the_final_encode_leaves_no_partial_and_no_work_folder_and_a_start_clears_both(
    client, llm, project, renderer
):
    series_id, ep = three_cards(client, llm, project)
    renderer.pause_at(3)  # three pieces, then the whole clip
    assert start_render(client, ep["id"]).status_code == 202
    renderer.wait_until(3)
    folder = project.ep_renders_dir(series_id, ep["id"])
    partial = folder / renderer.commands[3][-1].split("/")[-1]
    partial.write_bytes(b"half")  # as far as ffmpeg got
    assert client.delete(CURRENT).status_code == 202
    assert poll_until(client, CURRENT, lambda job: job["state"] in FINISHED)["state"] == "cancelled"
    assert not project.toon_render_dir.exists()
    assert list(folder.iterdir()) == []
    project.toon_render_dir.mkdir(parents=True)
    partial.write_bytes(b"half")
    with client:  # the app's start-up runs each job holder's clean
        pass
    assert not project.toon_render_dir.exists()
    assert list(folder.iterdir()) == []


def test_a_render_is_listed_served_and_deleted_with_its_three_files(client, llm, project):
    series_id, ep = three_cards(client, llm, project)
    job = rendered(client, ep["id"])
    [listed] = client.get(f"{EPS}/{ep['id']}/renders").json()
    assert (listed["name"], listed["title"], listed["n"]) == (job["name"], "เสียงเรียกจากป่า", 1)
    assert listed["duration_s"] == pytest.approx(4.6, abs=0.1)
    mp4 = client.get(f"{EPS}/{ep['id']}/renders/{job['name']}")
    assert mp4.status_code == 200 and mp4.headers["content-type"] == "video/mp4"
    [row] = client.get(f"/api/toon/series/{series_id}/eps").json()
    assert row["rendered_at"] == listed["created_at"]
    assert client.delete(f"{EPS}/{ep['id']}/renders/{job['name']}").status_code == 204
    assert not list(project.ep_renders_dir(series_id, ep["id"]).iterdir())
    assert client.get(f"{EPS}/{ep['id']}/renders/{job['name']}").status_code == 404


def test_a_render_a_player_holds_open_is_in_use_and_keeps_its_files(client, llm, project, monkeypatch):
    # Windows can't delete a file another program still holds open.
    series_id, ep = three_cards(client, llm, project)
    job = rendered(client, ep["id"])
    real_unlink = Path.unlink

    def unlink(path, missing_ok=False):
        if path.suffix == ".mp4":
            raise PermissionError(32, "The process cannot access the file")
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)
    response = client.delete(f"{EPS}/{ep['id']}/renders/{job['name']}")

    assert response.status_code == 409
    assert response.json() == {"code": "in_use", "message": "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง"}
    assert [row["name"] for row in client.get(f"{EPS}/{ep['id']}/renders").json()] == [job["name"]]


def test_a_series_a_render_works_on_can_t_be_deleted(client, llm, project, renderer):
    series_id, ep = three_cards(client, llm, project)
    renderer.pause_at(0)
    assert start_render(client, ep["id"]).status_code == 202
    renderer.wait_until(0)
    response = client.request("DELETE", f"/api/toon/series/{series_id}", json={"confirm_eps": 1})
    assert (response.status_code, response.json()["code"]) == (409, "series_busy")
    renderer.release(0)
    poll_until(client, CURRENT, lambda job: job["state"] in FINISHED, timeout_s=60)


def test_the_render_and_sound_import_slots_are_job_holders_and_the_render_has_its_running_name():
    assert gpu.RUNNING_NAMES["toon_render"] == "render การ์ตูนเล่า"
    holders = [entry.current() for entry in app_module.JOB_HOLDERS]
    assert render.render_jobs in holders
    assert sounds.sound_imports in holders
