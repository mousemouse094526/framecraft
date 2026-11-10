"""The Image job, swapping a card's image back, and the Voice job under /api/toon, with fake
Qwen, klein and OmniVoice children (toon seam 1 › Image job, `failed_cards`, ภาพก่อนหน้า,
start ใหม่, `stale_ref`, Voice job, `stale_audio`)."""

import json

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil_maker, toon
from backend.app import app
from backend.errors import ApiError
from backend.models import KLEIN, OMNIVOICE
from backend.paths import ProjectPaths
from backend.toon import images, jobs, series
from backend.toon.klein import Draw, Encode

from .fakes import FakeKlein, FakeLlm, FakeTts, cuda_device, ok_ffmpeg, poll_until
from .test_toon_eps_api import Writer, cards_of, new_ep, run
from .test_toon_ref_api import png, upload
from .test_toon_series_api import create, write_voice

SERIES = "/api/toon/series"
EPS = "/api/toon/eps"
JOBS = "/api/toon/jobs"
CURRENT = "/api/toon/jobs/current"
FINISHED = {"done", "failed", "cancelled"}
SCENE = "character 1 sits by a campfire, wide shot, orange light from below."


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


class Translator(Writer):
    """Qwen as the Plot and Cards jobs ask it, and as the Image job asks for a card's scene."""

    def __init__(self):
        super().__init__()
        self.scene = lambda request: json.dumps({"scene": SCENE})

    def respond(self, request) -> str:
        if '"scene"' in request.prompt:
            return self.scene(request)
        return super().respond(request)


@pytest.fixture
def llm(monkeypatch) -> FakeLlm:
    fake = FakeLlm()
    fake.respond = Translator().respond
    monkeypatch.setattr(spoil_maker, "start_worker", fake)
    return fake


@pytest.fixture
def klein(monkeypatch) -> FakeKlein:
    fake = FakeKlein()
    monkeypatch.setattr(toon, "start_klein_worker", fake)
    return fake


@pytest.fixture
def tts(monkeypatch) -> FakeTts:
    fake = FakeTts()
    monkeypatch.setattr(spoil_maker, "start_tts_worker", fake)
    return fake


@pytest.fixture
def client(fake_root, llm, klein, tts, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    monkeypatch.setattr(jobs, "toon_jobs", jobs.ToonJobs())
    write_voice(ProjectPaths(fake_root))
    return TestClient(app, base_url="http://127.0.0.1")


def add(client, series_id: str, kind: str, name: str, with_ref: bool = True) -> str:
    """A character or background of the Series, with an uploaded reference image."""
    item_id = client.post(f"{SERIES}/{series_id}/{kind}", json={"name": name}).json()[kind][-1]["id"]
    if with_ref:
        assert upload(client, series_id, kind, item_id, png(64, 64)).status_code == 200
    return item_id


def with_cards(client, llm, layout: str = "frame") -> tuple[str, str, str, dict]:
    """A Series whose character and background have reference images, and an EP of four
    acts, each one segment on that background: the act's first card shows the character,
    its second is silent with no one in it."""
    series_id = create(client, layout=layout)["id"]
    character = add(client, series_id, "characters", "พีค")
    background = add(client, series_id, "backgrounds", "กองไฟ")
    writer = llm.respond.__self__
    writer.plot = {
        "title": "เสียงเรียกจากป่า",
        "acts": [{"summary": f"สรุปองก์ {n}"} for n in range(1, 5)],
        "characters": [{"id": character}],
        "backgrounds": [{"id": background}],
    }
    writer.cards = lambda act: {
        "segments": [
            {
                "background": background,
                "sound": None,
                "cards": [
                    {"text": f"พีคนั่งหน้ากองไฟใน{act}", "characters": [character], "description": "พีคนั่งหน้ากองไฟ มุมกว้าง"},
                    {"text": "", "characters": [], "description": ""},
                ],
            }
        ]
    }
    ep_id = new_ep(client, series_id)["id"]
    assert run(client, "plot", ep_id)["state"] == "done"
    assert run(client, "cards", ep_id)["state"] == "done"
    return series_id, character, background, client.get(f"{EPS}/{ep_id}").json()


def start_image(client, ep_id: str, **body):
    return client.post(JOBS, json={"kind": "image", "ep_id": ep_id} | body)


def wait_for_end(client) -> dict:
    return poll_until(client, CURRENT, lambda job: job["state"] in FINISHED)


def draw(client, ep_id: str, **body) -> dict:
    response = start_image(client, ep_id, **body)
    assert response.status_code == 202, response.json()
    return wait_for_end(client)


def get_ep(client, ep_id: str) -> dict:
    return client.get(f"{EPS}/{ep_id}").json()


def draws(klein: FakeKlein) -> list[Draw]:
    return [request for request in klein.requests if isinstance(request, Draw)]


# --- Image job ---


def test_drawing_what_is_missing_draws_each_no_image_card_in_order_and_skips_one_with_no_ref(client, llm, klein):
    series_id, _, _, ep = with_cards(client, llm)
    newcomer = add(client, series_id, "characters", "ลุงยาม", with_ref=False)
    cards = cards_of(ep)
    client.patch(f"{EPS}/{ep['id']}/cards/{cards[2]['id']}", json={"character_ids": [newcomer]})

    job = draw(client, ep["id"], scope="missing")

    assert (job["state"], job["done"], job["total"], job["skipped"]) == ("done", 7, 7, 1)
    assert job["missing_refs"] == [{"kind": "characters", "id": newcomer, "name": "ลุงยาม", "cards": 1}]
    after = cards_of(get_ep(client, ep["id"]))
    assert [card["image_status"] for card in after] == ["ready", "ready", "no_ref", "ready", "ready", "ready", "ready", "ready"]
    assert [card["has_image"] for card in after] == [True, True, False, True, True, True, True, True]
    encoded = next(request for request in klein.requests if isinstance(request, Encode))
    assert len(encoded.prompts) == 7
    assert [d.index for d in draws(klein)] == list(range(7))


def test_drawing_what_is_missing_when_every_card_has_no_ref_is_nothing_to_draw_and_one_such_card_is_no_ref(client, llm):
    series_id, _, background, ep = with_cards(client, llm)
    other = add(client, series_id, "backgrounds", "ห้องน้ำ", with_ref=False)
    for act in ep["acts"]:
        client.patch(f"{EPS}/{ep['id']}/segments/{act['segments'][0]['id']}", json={"background_id": other})

    every = start_image(client, ep["id"], scope="missing")
    one = start_image(client, ep["id"], card_id=cards_of(ep)[0]["id"])

    assert (every.status_code, every.json()["code"]) == (400, "nothing_to_draw")
    assert every.json()["missing_refs"] == [{"kind": "backgrounds", "id": other, "name": "ห้องน้ำ", "cards": 8}]
    assert (one.status_code, one.json()["code"]) == (400, "no_ref")


def test_deleting_a_series_during_its_image_job_is_series_busy(client, llm, klein):
    series_id, _, _, ep = with_cards(client, llm)
    klein.pause_at(1)
    start_image(client, ep["id"], scope="missing")
    klein.wait_until(1)

    response = client.request("DELETE", f"/api/toon/series/{series_id}", json={"confirm_eps": 1})

    assert (response.status_code, response.json()["code"]) == (409, "series_busy")
    klein.release(1)


def test_a_cancel_midway_keeps_the_pictures_done_and_drops_the_one_being_drawn(client, llm, klein):
    _, _, _, ep = with_cards(client, llm)
    klein.pause_at(2)  # request 0 is `Encode`: the second card's picture
    start_image(client, ep["id"], scope="missing")
    klein.wait_until(2)

    assert client.delete(CURRENT).status_code == 202
    job = wait_for_end(client)

    assert (job["state"], job["done"]) == ("cancelled", 1)
    statuses = [card["image_status"] for card in cards_of(get_ep(client, ep["id"]))]
    assert statuses[:2] == ["ready", "no_image"]


def test_a_card_klein_fails_on_is_in_failed_cards_and_the_job_goes_on_to_done(client, llm, klein):
    _, _, _, ep = with_cards(client, llm)
    klein.fail_at = 2

    job = draw(client, ep["id"], scope="missing")

    cards = cards_of(get_ep(client, ep["id"]))
    assert (job["state"], job["done"], job["failed_cards"]) == ("done", 8, [cards[1]["id"]])
    assert [card["image_status"] for card in cards[:3]] == ["ready", "no_image", "ready"]


def test_drawing_a_card_again_keeps_the_old_picture_as_previous_drops_the_one_before_and_swaps_back(client, llm, project):
    series_id, _, _, ep = with_cards(client, llm)
    card_id = cards_of(ep)[0]["id"]
    pictures = []
    for _ in range(3):
        assert draw(client, ep["id"], card_id=card_id)["state"] == "done"
        pictures.append(client.get(f"{EPS}/{ep['id']}/cards/{card_id}/image").content)
    folder = project.ep_dir(series_id, ep["id"]) / "images"

    assert cards_of(get_ep(client, ep["id"]))[0]["has_previous_image"]
    assert client.get(f"{EPS}/{ep['id']}/cards/{card_id}/previous-image").content == pictures[1]
    assert sorted(path.read_bytes() for path in folder.iterdir()) == sorted(pictures[1:])  # the first is gone
    swapped = client.post(f"{EPS}/{ep['id']}/cards/{card_id}/swap-image", json={})
    assert swapped.status_code == 200
    assert client.get(f"{EPS}/{ep['id']}/cards/{card_id}/image").content == pictures[1]
    assert client.get(f"{EPS}/{ep['id']}/cards/{card_id}/previous-image").content == pictures[2]


def test_swapping_a_card_with_no_previous_picture_is_not_found(client, llm):
    _, _, _, ep = with_cards(client, llm)
    card_id = cards_of(ep)[0]["id"]
    draw(client, ep["id"], card_id=card_id)

    response = client.post(f"{EPS}/{ep['id']}/cards/{card_id}/swap-image", json={})

    assert (response.status_code, response.json()["code"]) == (404, "not_found")


def test_a_backend_start_removes_pictures_no_ep_names_and_the_image_job_s_copies(client, llm, project):
    series_id, _, _, ep = with_cards(client, llm)
    card_id = cards_of(ep)[0]["id"]
    draw(client, ep["id"], card_id=card_id)
    folder = project.ep_dir(series_id, ep["id"]) / "images"
    kept = next(folder.iterdir())
    (folder / f"{card_id}-123.png").write_bytes(b"left by a job that never wrote ep.json")
    project.image_job_dir.mkdir(parents=True)
    (project.image_job_dir / "c_00000000-1.png").write_bytes(b"copy")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert list(folder.iterdir()) == [kept]
    assert not project.image_job_dir.exists()


def test_after_a_restart_drawing_what_is_missing_draws_only_the_cards_with_no_image(client, llm, klein):
    _, _, _, ep = with_cards(client, llm)
    cards = cards_of(ep)
    draw(client, ep["id"], card_id=cards[0]["id"])
    draw(client, ep["id"], card_id=cards[1]["id"])

    with TestClient(app, base_url="http://127.0.0.1") as restarted:
        assert restarted.post(JOBS, json={"kind": "image", "ep_id": ep["id"], "scope": "missing"}).status_code == 202
        job = wait_for_end(restarted)

    assert (job["total"], job["scope"], job["card_ids"]) == (6, "missing", [card["id"] for card in cards[2:]])


def test_a_changed_reference_or_character_makes_a_card_stale_ref_which_only_the_stale_ref_scope_draws(client, llm, klein):
    series_id, character, _, ep = with_cards(client, llm)
    assert draw(client, ep["id"], scope="missing")["state"] == "done"
    other = add(client, series_id, "characters", "ลุงยาม")
    cards = cards_of(ep)
    upload(client, series_id, "characters", character, png(32, 32))  # the character's face changes
    client.patch(f"{EPS}/{ep['id']}/cards/{cards[1]['id']}", json={"character_ids": [other]})

    statuses = [card["image_status"] for card in cards_of(get_ep(client, ep["id"]))]
    nothing = start_image(client, ep["id"], scope="missing")
    job = draw(client, ep["id"], scope="stale_ref")

    assert statuses == ["stale_ref", "stale_ref", "stale_ref", "ready", "stale_ref", "ready", "stale_ref", "ready"]
    assert (nothing.status_code, nothing.json()["code"]) == (400, "nothing_to_draw")
    assert job["card_ids"] == [cards[i]["id"] for i in (0, 1, 2, 4, 6)]
    assert {card["image_status"] for card in cards_of(get_ep(client, ep["id"]))} == {"ready"}


def test_a_card_deleted_while_its_picture_is_drawn_gets_none_and_leaves_no_file(client, llm, klein, project):
    series_id, _, _, ep = with_cards(client, llm)
    card_id = cards_of(ep)[0]["id"]
    klein.pause_at(1)
    start_image(client, ep["id"], card_id=card_id)
    klein.wait_until(1)

    assert client.delete(f"{EPS}/{ep['id']}/cards/{card_id}").status_code == 200
    klein.release(1)

    assert wait_for_end(client)["state"] == "done"
    assert not list((project.ep_dir(series_id, ep["id"]) / "images").glob(f"{card_id}-*"))


def test_a_card_s_prompt_binds_its_character_and_background_to_their_reference_images_in_order(client, llm, klein, project):
    series_id, character, background, ep = with_cards(client, llm)
    cards = cards_of(ep)

    draw(client, ep["id"], card_id=cards[0]["id"])

    [prompt] = next(r for r in klein.requests if isinstance(r, Encode)).prompts
    assert prompt.startswith(
        f"{SCENE} character 1 is the character in reference image 1. In the setting of the background in reference image 2. "
    )
    assert prompt.endswith("deep shadows. No text, no letters, no signs.")
    assert [path.name for path in draws(klein)[0].ref_paths] == [f"{character}-1.png", f"{background}-1.png"]
    asked = [r.prompt for r in llm.requests if '"scene"' in r.prompt][-1]
    assert "พีค is character 1" in asked and "พีคนั่งหน้ากองไฟ มุมกว้าง" in asked
    assert SCENE not in json.dumps(get_ep(client, ep["id"]))  # the prompt stays out of the page (D36)


def test_an_empty_scene_from_qwen_or_an_empty_description_takes_the_spec_s_fallback(client, llm, klein):
    _, _, _, ep = with_cards(client, llm)
    llm.respond.__self__.scene = lambda request: '{"scene": ""}'
    cards = cards_of(ep)

    draw(client, ep["id"], card_id=cards[0]["id"])
    draw(client, ep["id"], card_id=cards[1]["id"])

    prompts = [r.prompts[0] for r in klein.requests if isinstance(r, Encode)]
    assert prompts[0].startswith("character 1 in a medium shot. พีคนั่งหน้ากองไฟ มุมกว้าง character 1 is the character")
    assert prompts[1].startswith("A medium shot. In the setting of the background in reference image 1.")


@pytest.mark.parametrize(("layout", "size"), [("frame", (1024, 576)), ("full", (576, 1024))])
def test_a_card_is_drawn_at_its_series_background_size(client, llm, klein, layout, size):
    _, _, _, ep = with_cards(client, llm, layout=layout)

    draw(client, ep["id"], card_id=cards_of(ep)[0]["id"])

    assert (draws(klein)[0].width, draws(klein)[0].height) == size


def test_an_image_job_on_a_full_disk_is_disk_full_and_frees_the_gpu(client, llm, monkeypatch):
    _, _, _, ep = with_cards(client, llm)
    monkeypatch.setattr(series.disk, "free_bytes", lambda path: 0)

    response = start_image(client, ep["id"], scope="missing")

    assert (response.status_code, response.json()["code"]) == (507, "disk_full")
    assert gpu.slot.take("describe") is None


def test_an_image_job_without_klein_s_marker_is_not_ready_naming_the_row(client, llm, project):
    _, _, _, ep = with_cards(client, llm)
    project.marker(KLEIN).unlink()

    response = start_image(client, ep["id"], scope="missing")

    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", ["model_klein"])


def test_an_image_job_during_a_describe_job_is_gpu_busy(client, llm):
    _, _, _, ep = with_cards(client, llm)
    gpu.slot.take("describe")

    response = start_image(client, ep["id"], scope="missing")

    assert (response.status_code, response.json()["code"]) == (409, "gpu_busy")


# --- Voice job ---


def start_voice(client, ep_id: str, card_id: str):
    return client.post(JOBS, json={"kind": "voice", "ep_id": ep_id, "card_id": card_id})


def voice(client, ep_id: str, card_id: str) -> dict:
    response = start_voice(client, ep_id, card_id)
    assert response.status_code == 202, response.json()
    return wait_for_end(client)


def test_a_voice_job_speaks_a_card_in_the_ep_s_voice_and_its_wav_is_served(client, llm, tts):
    _, _, _, ep = with_cards(client, llm)
    card = cards_of(ep)[0]
    tts.seconds = 1.5

    job = voice(client, ep["id"], card["id"])

    after = cards_of(get_ep(client, ep["id"]))[0]
    assert (job["state"], job["done"], job["total"], job["card_ids"]) == ("done", 1, 1, [card["id"]])
    assert (after["audio_status"], after["duration_s"]) == ("ready", 1.8)  # the narration, then 0.3 s
    [speak] = tts.requests
    assert (speak.text, speak.prompt, speak.speed) == (card["text"], b"pt", 1.0)
    audio = client.get(f"{EPS}/{ep['id']}/cards/{card['id']}/audio")
    assert (audio.status_code, audio.content[:4]) == (200, b"RIFF")


def test_a_voice_job_on_a_silent_card_is_refused_and_a_card_with_no_audio_has_none_to_serve(client, llm):
    _, _, _, ep = with_cards(client, llm)
    silent = cards_of(ep)[1]

    response = start_voice(client, ep["id"], silent["id"])
    audio = client.get(f"{EPS}/{ep['id']}/cards/{cards_of(ep)[0]['id']}/audio")

    assert (response.status_code, response.json()["code"]) == (400, "silent_card")
    assert audio.status_code == 404


def test_a_new_voice_for_the_ep_or_a_changed_text_makes_a_card_s_audio_stale(client, llm, project):
    _, _, _, ep = with_cards(client, llm)
    first, _, third, *_ = cards_of(ep)
    voice(client, ep["id"], first["id"])
    voice(client, ep["id"], third["id"])
    write_voice(project, "v_00000002")

    client.patch(f"{EPS}/{ep['id']}/cards/{third['id']}", json={"text": "คืนนั้นฝนตก"})
    after_text = cards_of(get_ep(client, ep["id"]))
    client.patch(f"{EPS}/{ep['id']}", json={"voice_id": "v_00000002"})
    after_voice = cards_of(get_ep(client, ep["id"]))

    assert (after_text[0]["audio_status"], after_text[2]["audio_status"]) == ("ready", "stale_audio")
    assert after_voice[0]["audio_status"] == "stale_audio"


def test_a_voice_job_without_omnivoice_s_marker_is_not_ready_naming_the_row(client, llm, project):
    _, _, _, ep = with_cards(client, llm)
    project.marker(OMNIVOICE).unlink()

    response = start_voice(client, ep["id"], cards_of(ep)[0]["id"])

    assert (response.status_code, response.json()["code"], response.json()["rows"]) == (503, "not_ready", ["model_omnivoice"])


def test_a_voice_job_during_a_describe_job_is_gpu_busy_and_one_running_names_itself(client, llm, tts):
    _, _, _, ep = with_cards(client, llm)
    card_id = cards_of(ep)[0]["id"]
    gpu.slot.take("describe")
    refused = start_voice(client, ep["id"], card_id)
    gpu.slot.release("describe")
    tts.pause_at(0)
    start_voice(client, ep["id"], card_id)
    tts.wait_until(0)

    with pytest.raises(ApiError) as other:
        gpu.slot.take("describe")
    running = other.value.extra["running"]
    tts.release(0)
    wait_for_end(client)

    assert (refused.status_code, refused.json()["code"]) == (409, "gpu_busy")
    assert (running, gpu.RUNNING_NAMES[running]) == ("toon_voice", "สร้างเสียงเล่า")


def test_an_image_job_whose_reference_can_t_be_copied_frees_the_gpu(client, llm, project, monkeypatch):
    _, _, _, ep = with_cards(client, llm)
    monkeypatch.setattr(images.shutil, "copyfile", lambda *args: (_ for _ in ()).throw(OSError("disk error")))

    with pytest.raises(OSError):
        start_image(client, ep["id"], scope="missing")

    assert gpu.slot.take("describe") is None
