"""EPs, the Plot job, the Cards job and the storyline's edits under /api/toon, with a fake Qwen
child (toon seam 1 › Plot job, Cards job, แตกใหม่, เลข EP, `ep_locked`, `in_use`)."""

import json
import threading

import pytest
from fastapi.testclient import TestClient

from backend import checks, gpu, paths, spoil_maker
from backend.app import app
from backend.errors import ApiError
from backend.paths import ProjectPaths
from backend.spoil_maker import thai
from backend.toon import jobs, store
from backend.toon.store import Audio, CardImage

from .fakes import FakeLlm, cuda_device, ok_ffmpeg, poll_until
from .test_toon_series_api import VOICE, create, write_voice

SERIES = "/api/toon/series"
JOBS = "/api/toon/jobs"
CURRENT = "/api/toon/jobs/current"
FINISHED = {"done", "failed", "cancelled"}


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def llm(monkeypatch) -> FakeLlm:
    fake = FakeLlm()
    fake.respond = Writer().respond
    monkeypatch.setattr(spoil_maker, "start_worker", fake)
    return fake


@pytest.fixture
def client(fake_root, llm, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_device", cuda_device)
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    monkeypatch.setattr(jobs, "toon_jobs", jobs.ToonJobs())
    write_voice(ProjectPaths(fake_root))
    return TestClient(app, base_url="http://127.0.0.1")


class Writer:
    """Answers a plot prompt and each act's cards prompt the way Qwen is asked to. `cards`
    makes one act's answer from the act's name in the prompt."""

    def __init__(self):
        self.plot: dict | None = None  # set by `with_series`
        self.cards = lambda act: {
            "segments": [
                {
                    "background": self.plot["backgrounds"][0].get("id", "b_unknown"),
                    "sound": None,
                    "cards": [
                        {"text": f"การ์ดแรกของ{act}", "characters": [], "description": "มุมกว้าง", "motion": "zoom_in"},
                        {"text": "", "characters": [], "description": "", "motion": "still"},
                    ],
                }
            ]
        }

    def respond(self, request) -> str:
        if "เขียนพล็อต" in request.prompt:
            return json.dumps(self.plot, ensure_ascii=False)
        act = request.prompt.split("องก์นี้ (")[1].split(")")[0]
        return "```json\n" + json.dumps(self.cards(act), ensure_ascii=False) + "\n```"


def with_series(client, llm) -> tuple[str, str, str]:
    """A horror Series with one character and one background; the plot Qwen writes uses
    the character and proposes a new character and a new background."""
    series_id = create(client)["id"]
    character = client.post(f"{SERIES}/{series_id}/characters", json={"name": "พีค", "tag": "สายแฟ"}).json()["characters"][0]["id"]
    background = client.post(f"{SERIES}/{series_id}/backgrounds", json={"name": "กองไฟ"}).json()["backgrounds"][0]["id"]
    llm.respond.__self__.plot = {
        "title": "เสียงเรียกจากป่า",
        "acts": [{"summary": f"สรุปองก์ {n}"} for n in range(1, 5)],
        "characters": [{"id": character}, {"id": "c_00000000"}, {"name": "ลุงยาม", "tag": "", "description": "ชายแก่"}],
        "backgrounds": [{"name": "ห้องน้ำชั้นสาม", "description": "ห้องน้ำมืด"}],
    }
    return series_id, character, background


def new_ep(client, series_id: str, idea: str = "รุ่นพี่ไปแคมป์แล้วได้ยินเสียงเรียกชื่อ") -> dict:
    response = client.post(f"{SERIES}/{series_id}/eps", json={"idea": idea})
    assert response.status_code == 201, response.json()
    return response.json()


def start(client, kind: str, ep_id: str, **body):
    return client.post(JOBS, json={"kind": kind, "ep_id": ep_id} | body)


def wait_for_end(client) -> dict:
    return poll_until(client, CURRENT, lambda job: job["state"] in FINISHED)


def run(client, kind: str, ep_id: str, **body) -> dict:
    response = start(client, kind, ep_id, **body)
    assert response.status_code == 202, response.json()
    return wait_for_end(client)


def with_cards(client, llm) -> tuple[str, dict]:
    """A Series and an EP whose plot is written and split into cards."""
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    assert run(client, "plot", ep_id)["state"] == "done"
    assert run(client, "cards", ep_id)["state"] == "done"
    return series_id, client.get(f"/api/toon/eps/{ep_id}").json()


def cards_of(ep: dict) -> list[dict]:
    return [card for act in ep["acts"] for segment in act["segments"] for card in segment["cards"]]


def edit_stored(project: ProjectPaths, series_id: str, ep_id: str, change) -> None:
    """Changes `ep.json` as a job would, for a state the API can't reach yet (images, audio)."""
    ep = store.read_ep(project, series_id, ep_id)
    change(ep)
    store.write_ep(project, series_id, ep)


def gpu_refusal() -> ApiError | None:
    """What another job is told when it asks for the GPU slot now."""
    try:
        gpu.slot.take("describe")
    except ApiError as refused:
        return refused
    gpu.slot.release("describe")
    return None


def gpu_holder() -> str | None:
    refused = gpu_refusal()
    return refused.extra["running"] if refused else None


# --- EP and Plot job ---


def test_the_first_ep_is_1_and_a_new_one_after_a_delete_is_past_the_highest_ever(client, llm):
    series_id, _, _ = with_series(client, llm)

    first = new_ep(client, series_id)
    second = new_ep(client, series_id)
    assert client.delete(f"/api/toon/eps/{second['id']}").status_code == 204
    third = new_ep(client, series_id)

    assert (first["n"], first["stage"], first["voice_id"], third["n"]) == (1, "plot", VOICE, 3)
    assert [act["name"] for act in first["acts"]] == ["เปิด", "ปม", "หักมุม", "จบหลอน"]
    assert [ep["n"] for ep in client.get(f"{SERIES}/{series_id}/eps").json()] == [3, 1]


@pytest.mark.parametrize("n", [1, 0, 1000, True])
def test_an_ep_number_taken_in_the_series_or_out_of_1_999_is_invalid_ep_number(client, llm, n):
    series_id, _, _ = with_series(client, llm)
    new_ep(client, series_id)
    second = new_ep(client, series_id)

    response = client.patch(f"/api/toon/eps/{second['id']}", json={"n": n})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_ep_number")


def test_an_ep_number_past_the_highest_raises_the_series_highest(client, llm):
    series_id, _, _ = with_series(client, llm)
    ep = new_ep(client, series_id)

    assert client.patch(f"/api/toon/eps/{ep['id']}", json={"n": 9}).json()["n"] == 9
    assert new_ep(client, series_id)["n"] == 10


def test_a_plot_job_writes_the_title_and_every_summary_and_keeps_new_items_in_the_plot(client, llm):
    series_id, character, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.pause_at(0)

    started = start(client, "plot", ep_id)
    assert (started.status_code, started.json()["state"], started.json()["ep_id"]) == (202, "writing", ep_id)
    llm.wait_until(0)
    refused = gpu_refusal()
    assert (refused.extra["running"], refused.message) == ("toon_write", "รอให้งานร่างการ์ตูนเล่าเสร็จก่อน")
    llm.release(0)
    assert wait_for_end(client)["state"] == "done"

    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    assert (ep["title"], [act["summary"] for act in ep["acts"]]) == ("เสียงเรียกจากป่า", [f"สรุปองก์ {n}" for n in range(1, 5)])
    # The id the Series lacks is dropped; the new ones wait in the plot (D13).
    assert ep["plot"]["characters"] == [
        {"id": character, "new": False, "name": "", "tag": "", "description": ""},
        {"id": None, "new": True, "name": "ลุงยาม", "tag": "", "description": "ชายแก่"},
    ]
    assert ep["plot"]["backgrounds"][0] == {"id": None, "new": True, "name": "ห้องน้ำชั้นสาม", "tag": "", "description": "ห้องน้ำมืด"}
    series = client.get(f"{SERIES}/{series_id}").json()
    assert ([c["name"] for c in series["characters"]], [b["name"] for b in series["backgrounds"]]) == (["พีค"], ["กองไฟ"])
    assert gpu_holder() is None


def test_a_plot_job_whose_answer_is_broken_three_times_fails_write_failed(client, llm):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.respond = lambda request: '{"title": "ครึ่ง'

    job = run(client, "plot", ep_id)

    assert (job["state"], job["error"]["code"], len(llm.requests)) == ("failed", "write_failed", 3)
    assert client.get(f"/api/toon/eps/{ep_id}").json()["title"] == ""
    assert gpu_holder() is None


def test_a_plot_job_on_a_confirmed_plot_is_plot_confirmed(client, llm):
    _, ep = with_cards(client, llm)

    response = start(client, "plot", ep["id"])

    assert (response.status_code, response.json()["code"]) == (409, "plot_confirmed")


def test_a_new_character_added_to_a_confirmed_plot_is_invalid_request(client, llm):
    _, ep = with_cards(client, llm)
    plot = {kind: [{"id": item["id"]} for item in ep["plot"][kind]] for kind in ("characters", "backgrounds")}
    plot["characters"].append({"name": "ป้าแม่บ้าน"})

    response = client.patch(f"/api/toon/eps/{ep['id']}", json={"plot": plot})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_a_plot_left_with_no_background_is_invalid_request(client, llm):
    series_id, character, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]

    response = client.patch(f"/api/toon/eps/{ep_id}", json={"plot": {"characters": [{"id": character}], "backgrounds": []}})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_a_new_item_of_the_plot_switches_to_one_of_the_series(client, llm):
    series_id, _, background = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    plot = client.get(f"/api/toon/eps/{ep_id}").json()["plot"]

    plot["backgrounds"] = [{"id": background}]
    ep = client.patch(f"/api/toon/eps/{ep_id}", json={"plot": plot}).json()

    assert [(b["id"], b["new"]) for b in ep["plot"]["backgrounds"]] == [(background, False)]


# --- Cards job ---


def test_the_first_cards_job_adds_the_new_items_to_the_series_and_their_cards_have_no_ref(client, llm):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)

    job = run(client, "cards", ep_id)

    assert (job["state"], job["done"], job["total"]) == ("done", 4, 4)
    series = client.get(f"{SERIES}/{series_id}").json()
    new_background = next(b for b in series["backgrounds"] if b["name"] == "ห้องน้ำชั้นสาม")
    assert new_background["ref_rev"] == 0
    assert any(c["name"] == "ลุงยาม" and c["ref_rev"] == 0 for c in series["characters"])
    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    assert ep["stage"] == "cards"
    assert [b["id"] for b in ep["plot"]["backgrounds"]] == [new_background["id"]]
    assert all(act["cards_from"] == act["summary"] for act in ep["acts"])
    assert {card["image_status"] for card in cards_of(ep)} == {"no_ref"}
    assert [(c["edited"], c["hold_s"]) for c in cards_of(ep)[:2]] == [(False, 0), (False, 2)]  # D21: silent holds 2 s


def test_a_card_answer_is_kept_to_two_characters_a_known_motion_and_a_sound_in_the_library(client, llm, project):
    series_id, character, _ = with_series(client, llm)
    project.toon_sounds_file.parent.mkdir(parents=True)
    sounds = {"version": 1, "sounds": [{"id": "m_00000001", "name": "ฝนตกในป่า", "duration_s": 60, "source": "file"}]}
    project.toon_sounds_file.write_text(json.dumps(sounds), encoding="utf-8")
    llm.respond.__self__.plot["characters"] = [{"id": character}, {"name": "มายด์"}, {"name": "ลุงยาม"}]
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    plot = client.get(f"/api/toon/eps/{ep_id}").json()["plot"]
    llm.respond.__self__.plot = plot | {"backgrounds": [{"id": "b_x"}]}
    llm.respond.__self__.cards = lambda act: {
        "segments": [
            {
                "background": "b_not_in_plot",
                "sound": "m_00000009",
                "cards": [{"text": "สามคน", "characters": [character, character, "c_x", "c_y"], "motion": "spin"}],
            },
            {"background": "b_x", "sound": "m_00000001", "cards": [{"text": "สองคน", "characters": []}]},
        ]
    }

    run(client, "cards", ep_id)

    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    first, second = ep["acts"][0]["segments"]
    series = client.get(f"{SERIES}/{series_id}").json()
    assert first["background_id"] == ep["plot"]["backgrounds"][0]["id"]  # not in the plot: the plot's first
    assert (first["sound"], second["sound"]) == (None, {"sound_id": "m_00000001", "volume": 30})
    assert (first["cards"][0]["character_ids"], first["cards"][0]["motion"]) == ([character], "still")
    assert "m_00000001: ฝนตกในป่า" in llm.requests[-1].prompt
    assert len(series["characters"]) == 3


def test_a_card_answer_naming_three_characters_of_the_plot_keeps_the_first_two(client, llm):
    series_id, character, _ = with_series(client, llm)
    llm.respond.__self__.plot["characters"] = [{"id": character}, {"name": "มายด์"}, {"name": "ลุงยาม"}]
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    writer = llm.respond.__self__
    original = writer.respond

    def respond(request):
        if "เขียนพล็อต" in request.prompt:
            return original(request)
        ids = [line.split(":")[0].removeprefix("- ") for line in request.prompt.split("ตัวละคร:\n")[1].split("\nฉากหลัง:")[0].splitlines()]
        return json.dumps({"segments": [{"background": "", "cards": [{"text": "สามคน", "characters": ids}]}]})

    llm.respond = respond
    run(client, "cards", ep_id)

    card = cards_of(client.get(f"/api/toon/eps/{ep_id}").json())[0]
    assert len(card["character_ids"]) == 2 and card["character_ids"][0] == character


def test_a_changed_summary_splits_only_that_act_and_the_others_keep_their_cards(client, llm, project):
    series_id, ep = with_cards(client, llm)
    before = [[card["id"] for card in cards_of({"acts": [act]})] for act in ep["acts"]]

    def draw(stored):
        card = stored.acts[0].segments[0].cards[0]
        card.image = CardImage(file=f"{card.id}-1.png", refs={})

    edit_stored(project, series_id, ep["id"], draw)
    second = ep["acts"][1]["id"]
    client.patch(f"/api/toon/eps/{ep['id']}/acts/{second}", json={"summary": "สรุปใหม่"})

    job = run(client, "cards", ep["id"])

    after = client.get(f"/api/toon/eps/{ep['id']}").json()
    ids = [[card["id"] for card in cards_of({"acts": [act]})] for act in after["acts"]]
    assert (job["total"], ids[0], ids[2], ids[3]) == (1, before[0], before[2], before[3])
    assert set(ids[1]).isdisjoint(before[1])
    assert after["acts"][0]["segments"][0]["cards"][0]["image_status"] != "no_image"
    assert "องก์นี้ (ปม): สรุปใหม่" in llm.requests[-1].prompt


def test_re_splitting_an_act_with_edited_cards_or_images_without_confirm_loss_is_cards_will_be_lost(client, llm, project):
    series_id, ep = with_cards(client, llm)
    act = ep["acts"][0]
    first, second = cards_of({"acts": [act]})
    client.patch(f"/api/toon/eps/{ep['id']}/cards/{first['id']}", json={"text": "แก้เอง"})

    def draw(stored):
        card = stored.acts[0].segments[0].cards[1]
        card.image = CardImage(file=f"{card.id}-1.png", refs={})
        card.audio = Audio(tts_text="x", voice_id=VOICE, duration_s=1)

    edit_stored(project, series_id, ep["id"], draw)
    client.patch(f"/api/toon/eps/{ep['id']}/acts/{act['id']}", json={"summary": "สรุปใหม่"})

    refused = start(client, "cards", ep["id"])
    assert (refused.status_code, refused.json()["code"]) == (409, "cards_will_be_lost")
    assert refused.json()["acts"] == [{"id": act["id"], "name": "เปิด", "edited": 1, "images": 1, "audio": 1}]
    assert run(client, "cards", ep["id"], confirm_loss=True)["state"] == "done"


def test_with_no_changed_act_a_cards_job_is_nothing_to_split_and_an_added_act_counts_as_changed(client, llm):
    _, ep = with_cards(client, llm)

    refused = start(client, "cards", ep["id"])
    assert (refused.status_code, refused.json()["code"]) == (400, "nothing_to_split")

    added = client.post(f"/api/toon/eps/{ep['id']}/acts", json={"name": "ส่งท้าย", "summary": "ปิดเรื่อง"}).json()
    assert added["acts"][-1]["cards_from"] is None
    job = run(client, "cards", ep["id"])
    assert (job["state"], job["total"]) == ("done", 1)


@pytest.mark.parametrize("ending", ["cancel", "crash"])
def test_a_cards_job_cancelled_or_crashed_midway_leaves_ep_json_and_the_series_as_they_were(client, llm, project, ending):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    folder = project.ep_dir(series_id, ep_id)
    before = (folder / "ep.json").read_text(encoding="utf-8"), (project.series_dir(series_id) / "series.json").read_text(encoding="utf-8")
    if ending == "cancel":
        llm.pause_at(2)
    else:
        llm.crash_at = 2

    start(client, "cards", ep_id)
    if ending == "cancel":
        llm.wait_until(2)
        client.delete(CURRENT)
    job = wait_for_end(client)

    assert job["state"] == ("cancelled" if ending == "cancel" else "failed")
    after = (folder / "ep.json").read_text(encoding="utf-8"), (project.series_dir(series_id) / "series.json").read_text(encoding="utf-8")
    assert after == before
    assert gpu_holder() is None


def test_a_cards_job_while_another_job_holds_the_gpu_is_gpu_busy(client, llm):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    gpu.slot.take("describe")

    response = start(client, "cards", ep_id)

    assert (response.status_code, response.json()["code"], response.json()["running"]) == (409, "gpu_busy", "describe")


# --- editing the storyline ---


def test_a_changed_text_makes_a_card_edited_and_a_silent_card_with_no_hold_is_invalid_card(client, llm):
    _, ep = with_cards(client, llm)
    first, silent = cards_of(ep)[:2]

    changed = client.patch(f"/api/toon/eps/{ep['id']}/cards/{first['id']}", json={"text": "ข้อความใหม่"})
    refused = client.patch(f"/api/toon/eps/{ep['id']}/cards/{silent['id']}", json={"hold_s": 0})

    assert cards_of(changed.json())[0]["edited"] is True
    assert (refused.status_code, refused.json()["code"]) == (400, "invalid_card")


def test_a_flag_motion_or_hold_change_leaves_a_card_not_edited(client, llm):
    _, ep = with_cards(client, llm)
    first = cards_of(ep)[0]

    changed = client.patch(f"/api/toon/eps/{ep['id']}/cards/{first['id']}", json={"motion": "pan_left", "flicker": True, "hold_s": 1.5})

    card = cards_of(changed.json())[0]
    assert (card["motion"], card["flicker"], card["hold_s"], card["edited"]) == ("pan_left", True, 1.5, False)


def test_deleting_the_last_card_of_a_segment_removes_the_segment(client, llm):
    _, ep = with_cards(client, llm)
    segment = ep["acts"][0]["segments"][0]

    for card in segment["cards"]:
        after = client.delete(f"/api/toon/eps/{ep['id']}/cards/{card['id']}").json()

    assert after["acts"][0]["segments"] == []


def test_a_segment_added_without_a_background_is_invalid_request_and_with_one_holds_a_silent_card(client, llm):
    series_id, ep = with_cards(client, llm)
    act = ep["acts"][0]
    background = ep["plot"]["backgrounds"][0]["id"]

    refused = client.post(f"/api/toon/eps/{ep['id']}/segments", json={"act_id": act["id"]})
    added = client.post(f"/api/toon/eps/{ep['id']}/segments", json={"act_id": act["id"], "background_id": background, "after": None})

    assert (refused.status_code, refused.json()["code"]) == (400, "invalid_request")
    first = added.json()["acts"][0]["segments"][0]
    assert [(c["text"], c["hold_s"], c["edited"]) for c in first["cards"]] == [("", 2, True)]


def test_a_card_added_after_another_lands_after_it_and_is_edited(client, llm):
    _, ep = with_cards(client, llm)
    segment = ep["acts"][0]["segments"][0]

    added = client.post(
        f"/api/toon/eps/{ep['id']}/cards", json={"segment_id": segment["id"], "after": segment["cards"][0]["id"], "text": "แทรก"}
    ).json()

    cards = added["acts"][0]["segments"][0]["cards"]
    assert [(c["text"], c["edited"]) for c in cards][1] == ("แทรก", True)
    assert len(cards) == 3


def test_get_ep_gives_each_card_its_states_and_length_and_the_total(client, llm, project):
    series_id, ep = with_cards(client, llm)
    first = cards_of(ep)[0]

    def heard(stored):
        card = stored.acts[0].segments[0].cards[0]
        card.audio = Audio(tts_text=thai.spoken(card.text), voice_id=VOICE, duration_s=3.1)
        card.hold_s = 0.5

    edit_stored(project, series_id, ep["id"], heard)
    ep = client.get(f"/api/toon/eps/{ep['id']}").json()
    cards = cards_of(ep)

    assert (cards[0]["audio_status"], cards[0]["duration_s"]) == ("ready", 3.9)  # 3.1 + 0.3 + 0.5
    assert (cards[1]["audio_status"], cards[1]["duration_s"]) == ("silent", 2)
    guessed = cards[2]
    letters = thai.letters(thai.spoken(guessed["text"]))
    assert (guessed["audio_status"], guessed["duration_s"]) == ("no_audio", round(letters / 15 + 0.3, 1))
    assert ep["duration_s"] == round(sum(card["duration_s"] for card in cards), 1)
    assert first["image_status"] == "no_ref"


def test_a_card_drawn_before_its_reference_changed_is_stale_ref_and_a_new_voice_makes_its_audio_stale(client, llm, project):
    series_id, ep = with_cards(client, llm)
    background = ep["plot"]["backgrounds"][0]["id"]

    def drawn(stored):
        series_now = store.read_series(project, series_id)
        next(b for b in series_now.backgrounds if b.id == background).ref_rev = 2
        store.write_series(project, series_now)
        card = stored.acts[0].segments[0].cards[0]
        card.image = CardImage(file=f"{card.id}-1.png", refs={background: 1})
        card.audio = Audio(tts_text=thai.spoken(card.text), voice_id=VOICE, duration_s=1)

    edit_stored(project, series_id, ep["id"], drawn)
    write_voice(project, "v_00000002")
    ep = client.patch(f"/api/toon/eps/{ep['id']}", json={"voice_id": "v_00000002"}).json()

    card = cards_of(ep)[0]
    assert (card["image_status"], card["audio_status"]) == ("stale_ref", "stale_audio")


def test_editing_a_card_during_its_ep_s_cards_job_is_ep_locked_and_deleting_the_ep_is_ep_busy(client, llm):
    _, ep = with_cards(client, llm)
    act, card = ep["acts"][0], cards_of(ep)[0]
    client.patch(f"/api/toon/eps/{ep['id']}/acts/{act['id']}", json={"summary": "สรุปใหม่"})
    llm.pause_at(0)
    start(client, "cards", ep["id"])
    llm.wait_until(0)

    edited = client.patch(f"/api/toon/eps/{ep['id']}/cards/{card['id']}", json={"text": "แก้"})
    deleted = client.delete(f"/api/toon/eps/{ep['id']}")
    locked = client.get(f"/api/toon/eps/{ep['id']}").json()["locked"]

    assert (edited.status_code, edited.json()["code"]) == (409, "ep_locked")
    assert (deleted.status_code, deleted.json()["code"]) == (409, "ep_busy")
    assert locked is True
    llm.release(0)
    wait_for_end(client)
    assert client.get(f"/api/toon/eps/{ep['id']}").json()["locked"] is False


def test_deleting_a_character_a_card_or_plot_uses_is_in_use_with_the_eps(client, llm):
    series_id, character, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    client.patch(f"/api/toon/eps/{ep_id}", json={"title": "ตอนแรก"})

    response = client.delete(f"{SERIES}/{series_id}/characters/{character}")

    assert (response.status_code, response.json()["code"], response.json()["eps"]) == (409, "in_use", [{"n": 1, "title": "ตอนแรก"}])


def test_deleting_a_character_only_a_card_uses_is_in_use(client, llm, project):
    series_id, ep = with_cards(client, llm)
    character = next(item["id"] for item in ep["plot"]["characters"] if item["name"] == "" and item["id"])

    def card_only(stored):
        stored.plot.characters = [item for item in stored.plot.characters if item.id != character]
        stored.acts[0].segments[0].cards[0].character_ids = [character]

    edit_stored(project, series_id, ep["id"], card_only)

    response = client.delete(f"{SERIES}/{series_id}/characters/{character}")

    assert (response.status_code, response.json()["code"], [e["n"] for e in response.json()["eps"]]) == (409, "in_use", [1])


def test_deleting_a_background_only_a_segment_uses_is_in_use(client, llm, project):
    series_id, ep = with_cards(client, llm)
    background = client.get(f"{SERIES}/{series_id}").json()["backgrounds"][0]["id"]

    def segment_only(stored):
        stored.plot.backgrounds = [item for item in stored.plot.backgrounds if item.id != background]
        for act in stored.acts:
            for segment in act.segments:
                segment.background_id = background

    edit_stored(project, series_id, ep["id"], segment_only)

    response = client.delete(f"{SERIES}/{series_id}/backgrounds/{background}")

    assert (response.status_code, response.json()["code"], [e["n"] for e in response.json()["eps"]]) == (409, "in_use", [1])


def test_deleting_the_saved_voice_an_ep_narrates_with_is_voice_in_use(client, llm, project):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    write_voice(project, "v_00000002")
    client.patch(f"{SERIES}/{series_id}", json={"voice_id": "v_00000002"})
    client.patch(f"/api/toon/eps/{ep_id}", json={"voice_id": VOICE})
    client.patch(f"{SERIES}/{series_id}", json={"voice_id": "v_00000002"})

    response = client.delete(f"/api/spoil-maker/voices/{VOICE}")

    assert (response.status_code, response.json()["code"]) == (409, "voice_in_use")


def test_changing_an_ep_s_voice_waits_for_the_draft_s_lock(client, llm, project):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    write_voice(project, "v_00000002")
    answers = []

    with gpu.slot.draft_lock:
        thread = threading.Thread(
            target=lambda: answers.append(client.patch(f"/api/toon/eps/{ep_id}", json={"voice_id": "v_00000002"}))
        )
        thread.start()
        thread.join(0.3)
        assert answers == []
        assert store.lock.acquire(blocking=False)  # held at the draft's lock, the store's still free
        store.lock.release()
    thread.join(5)

    assert answers[0].json()["voice_id"] == "v_00000002"
