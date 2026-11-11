"""EPs, the Plot job, the Cards job and the storyline's edits under /api/toon, with a fake Qwen
child (toon seam 1 › Plot job, Cards job, แตกใหม่, เลข EP, `ep_locked`, `in_use`)."""

import json
import threading

import pytest

from backend import gpu
from backend.paths import EpAddress
from backend.spoil_maker import thai
from backend.toon import steps, store, writer
from backend.toon.kinds import KINDS
from backend.toon.series import DESCRIPTION_MAX
from backend.toon.store import Audio, CardImage

from .fakes import (
    CODE_ERROR,
    TOON_CURRENT,
    TOON_JOBS,
    TOON_SERIES,
    TOON_VOICE,
    Writer,
    cards_of,
    edit_stored_ep,
    gpu_refusal,
    new_ep,
    new_series,
    os_timeouts,
    run,
    start,
    toon_api,
    wait_for_toon_job,
    with_series,
    write_toon_voice,
)



project, llm, klein, tts, client = toon_api(lambda: Writer().respond)


def with_cards(client, llm) -> tuple[str, dict]:
    """A Series and an EP whose plot is written and split into cards."""
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    assert run(client, "plot", ep_id)["state"] == "done"
    assert run(client, "cards", ep_id)["state"] == "done"
    return series_id, client.get(f"/api/toon/eps/{ep_id}").json()


def gpu_holder() -> str | None:
    refused = gpu_refusal()
    return refused.extra["running"] if refused else None


# --- EP and Plot job ---


EP_ROUTES = [
    ("get", "", {}),
    ("patch", "", {"json": {"title": "ตอนใหม่"}}),
    ("delete", "", {}),
    ("post", "/acts", {"json": {"name": "องก์ใหม่"}}),
    ("patch", "/acts/a_00000000", {"json": {"name": "องก์ใหม่"}}),
    ("delete", "/acts/a_00000000", {}),
    ("post", "/segments", {"json": {"act_id": "a_00000000", "background_id": "b_00000000"}}),
    ("patch", "/segments/g_00000000", {"json": {"sound": None}}),
    ("delete", "/segments/g_00000000", {}),
    ("post", "/cards", {"json": {"segment_id": "g_00000000"}}),
    ("patch", "/cards/k_00000000", {"json": {"text": "ข้อความ"}}),
    ("delete", "/cards/k_00000000", {}),
    ("post", "/cards/k_00000000/swap-image", {"json": {}}),  # a POST is JSON (ADR 0013)
    ("get", "/cards/k_00000000/image", {}),
    ("get", "/cards/k_00000000/previous-image", {}),
    ("get", "/cards/k_00000000/audio", {}),
    ("get", "/renders", {}),
    ("get", "/renders/clip", {}),
    ("delete", "/renders/clip", {}),
]


@pytest.mark.parametrize(("method", "tail", "send"), EP_ROUTES)
def test_every_route_of_one_ep_is_not_found_for_an_ep_that_isn_t_there(client, method, tail, send):
    # A body valid enough to reach the EP check (a POST with none is `415`), and a Series, so
    # the id is looked for in one and found in none.
    new_series(client)
    for ep_id in ("e_00000000", "not-an-ep"):
        response = client.request(method, f"/api/toon/eps/{ep_id}{tail}", **send)
        assert (response.status_code, response.json()) == (404, {"code": "not_found", "message": "ไม่พบ EP นี้"})


def test_a_bad_body_for_an_ep_that_isn_t_there_is_refused_for_its_body_first(client):
    no_name = client.post("/api/toon/eps/e_00000000/acts", json={"name": ""})
    not_an_object = client.patch("/api/toon/eps/e_00000000", json=[1])
    assert (no_name.status_code, no_name.json()) == (400, {"code": "invalid_request", "message": "ข้อความต้องยาว 1–20 ตัวอักษร"})
    assert (not_an_object.status_code, not_an_object.json()["code"]) == (400, "invalid_request")


def test_the_first_ep_is_1_and_a_new_one_after_a_delete_is_past_the_highest_ever(client, llm):
    series_id, _, _ = with_series(client, llm)

    first = new_ep(client, series_id)
    second = new_ep(client, series_id)
    assert client.delete(f"/api/toon/eps/{second['id']}").status_code == 204
    third = new_ep(client, series_id)

    assert (first["n"], first["stage"], first["voice_id"], third["n"]) == (1, "plot", TOON_VOICE, 3)
    assert [act["name"] for act in first["acts"]] == ["เปิด", "ปม", "หักมุม", "จบหลอน"]
    assert [ep["n"] for ep in client.get(f"{TOON_SERIES}/{series_id}/eps").json()] == [3, 1]


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
    assert wait_for_toon_job(client)["state"] == "done"

    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    assert (ep["title"], [act["summary"] for act in ep["acts"]]) == ("เสียงเรียกจากป่า", [f"สรุปองก์ {n}" for n in range(1, 5)])
    # The id the Series lacks is dropped; the new ones wait in the plot (D13).
    assert ep["plot"]["characters"] == [
        {"id": character, "new": False, "name": "", "tag": "", "description": ""},
        {"id": None, "new": True, "name": "ลุงยาม", "tag": "", "description": "ชายแก่"},
    ]
    assert ep["plot"]["backgrounds"][0] == {"id": None, "new": True, "name": "ห้องน้ำชั้นสาม", "tag": "", "description": "ห้องน้ำมืด"}
    series = client.get(f"{TOON_SERIES}/{series_id}").json()
    assert ([c["name"] for c in series["characters"]], [b["name"] for b in series["backgrounds"]]) == (["พีค"], ["กองไฟ"])
    assert gpu_holder() is None


def test_a_plot_answer_whose_acts_are_plain_summaries_is_read_and_cleaned_as_one(client, llm):
    # The real Qwen wrote `"acts": ["...", ...]` to the prompt before D82 (D81); a summary is cleaned of CJK letters.
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.respond.__self__.plot["acts"] = [f"สรุป中文องก์ {n}" for n in range(1, 4)] + [{"summary": "สรุปองก์ 4"}]

    assert (run(client, "plot", ep_id)["state"], len(llm.requests)) == ("done", 1)
    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    assert [act["summary"] for act in ep["acts"]] == [f"สรุปองก์ {n}" for n in range(1, 5)]


def test_a_plot_prompt_names_each_act_as_a_key_and_an_answer_by_act_is_read_in_its_order_whatever_its_keys(client, llm):
    # The real Qwen fills one summary per key 20/20 times, where a list of acts came back 3 to 55 long (D82);
    # the summaries are from its answers to this prompt (ticket 16). The keys aren't read: the third is renamed
    # and put last, and the summaries still go to the acts in the answer's order.
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    summaries = [
        "ฉันยืนเฝ้าห้องเรียนคืนสุดท้ายก่อนตึกจะถูกทุบทิ้ง",
        "ครูเอกผู้ตายไปแล้วเดินเข้ามาที่หน้าชั้นเรียน",
        "ครูเอกหันมาสบตาฉันด้วยรอยยิ้มที่ดูคุ้นเคย",
        "ฉันสะดุ้งตื่นพบว่าตัวเองนอนหลับอยู่ที่โต๊ะ",
    ]
    llm.respond.__self__.plot["acts"] = dict(zip(["1. เปิด", "2. ปม", "4. จบหลอน", "องก์ที่สาม"], summaries, strict=True))

    assert (run(client, "plot", ep_id)["state"], len(llm.requests)) == ("done", 1)

    assert '"acts": {"1. เปิด": "สรุปองก์ เปิด 1–3 ประโยค", "2. ปม": "สรุปองก์ ปม 1–3 ประโยค",' in llm.requests[0].prompt
    assert "acts มี 4 ช่องพอดี ช่องละหนึ่งองก์" in llm.requests[0].prompt
    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    assert [act["summary"] for act in ep["acts"]] == summaries


def test_a_plot_answer_the_way_the_real_qwen_writes_it_is_read(client, llm):
    # Cut from a real Qwen answer of #35 (`bugs/2026-11-11-plot-job-write-failed-with-qwen.md`): its acts
    # are plain summaries, and the Series' items it uses carry their name, tag and description with the id.
    series_id, character, background = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    reply = (
        '{\n  "title": "คาบสุดท้ายก่อนรื้อ",\n  "acts": [\n'
        '    "คืนสุดท้ายที่ตึกโรงเรียนจะถูกทุบทำลาย ฉันนั่งเฝ้าห้องเรียนเก่าที่มืดมิดและเย็นเฉียบ",\n'
        '    "เสียงกระดุกกระดิกจากประตูทำให้ฉันสะดุ้ง",\n'
        '    "ครูเอกที่ตายไปแล้วกลับมาสอนคาบสุดท้าย",\n'
        "    \"ครูเอกชี้ไปที่กระดานแล้วบอกว่า 'ตึกจะพัง' ก่อนที่ภาพจะจางหาย\"\n  ],\n"
        f'  "characters": [\n    {{\n      "id": "{character}",\n      "name": "พีค",\n'
        '      "tag": "นักเรียน",\n      "description": "นักเรียนมัธยมที่เฝ้าห้องเรียนคืนสุดท้าย"\n    }\n  ],\n'
        f'  "backgrounds": [\n    {{\n      "id": "{background}",\n      "name": "กองไฟ",\n'
        '      "description": "ห้องเรียนที่มืดสลัว"\n    },\n'
        '    {\n      "name": "ทางเดินชั้นสอง",\n      "tag": "ทางเดิน",\n      "description": "ทางเดินยาวไฟกะพริบ"\n    }\n  ]\n}'
    )
    llm.respond = lambda request: reply

    assert (run(client, "plot", ep_id)["state"], len(llm.requests)) == ("done", 1)

    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    # Items of the Series come back by id alone: the name and description Qwen copied with it are dropped.
    assert (ep["title"], ep["acts"][1]["summary"]) == ("คาบสุดท้ายก่อนรื้อ", "เสียงกระดุกกระดิกจากประตูทำให้ฉันสะดุ้ง")
    assert [(c["id"], c["name"]) for c in ep["plot"]["characters"]] == [(character, "")]
    assert [(b["id"], b["name"]) for b in ep["plot"]["backgrounds"]] == [(background, ""), (None, "ทางเดินชั้นสอง")]


def test_a_plot_answer_drops_a_non_object_a_null_or_repeated_id_and_a_nameless_item_and_cleans_a_new_name(client, llm):
    series_id, character, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.respond.__self__.plot["characters"] = [
        "พีค",
        {"id": character},
        {"id": character},
        {"id": None, "name": "ลุงยามอีกคน"},
        {"name": "ลุง中文ยาม", "description": "ชาย" + "แก่" * 300},
        {"name": "中文"},
    ]

    assert run(client, "plot", ep_id)["state"] == "done"

    characters = client.get(f"/api/toon/eps/{ep_id}").json()["plot"]["characters"]
    # A Series' character is kept by id alone; only a new one carries its name.
    assert [(c["id"], c["name"]) for c in characters] == [(character, ""), (None, "ลุงยาม")]
    assert len(characters[1]["description"]) == DESCRIPTION_MAX


def test_a_plot_job_whose_answer_is_broken_three_times_fails_write_failed(client, llm):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.respond = lambda request: '{"title": "ครึ่ง'

    job = run(client, "plot", ep_id)

    assert (job["state"], job["error"]["code"], len(llm.requests)) == ("failed", "write_failed", 3)
    assert client.get(f"/api/toon/eps/{ep_id}").json()["title"] == ""
    assert gpu_holder() is None


def test_a_plot_answer_with_too_many_acts_is_logged_with_the_counts_and_the_start_of_the_answer(client, llm, caplog):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.respond.__self__.plot["acts"] = [f"ประโยคที่ {n} ของเรื่อง" for n in range(1, 13)]

    assert run(client, "plot", ep_id)["state"] == "failed"

    assert "plot attempt 3 is not the JSON asked for: 12 acts for the EP's 4;" in caplog.text
    assert '{"title": "เสียงเรียกจากป่า", "acts": ["ประโยคที่ 1 ของเรื่อง"' in caplog.text


def test_a_plot_answer_with_no_background_is_logged_with_what_the_plot_holds(client, llm, caplog):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.respond.__self__.plot["backgrounds"] = [{"id": "b_00000000"}]  # not in the Series: dropped

    assert run(client, "plot", ep_id)["state"] == "failed"

    assert "is not the JSON asked for: 2 characters, 0 backgrounds once unknown ids are dropped: no background" in caplog.text


def test_a_plot_answer_with_too_many_characters_is_logged_with_the_bound_it_breaks(client, llm, caplog):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.respond.__self__.plot["characters"] = [{"name": f"คนที่ {n}", "description": "ชาวบ้าน"} for n in range(1, 8)]

    assert run(client, "plot", ep_id)["state"] == "failed"

    assert "is not the JSON asked for: 7 characters (at most 6) once unknown ids are dropped;" in caplog.text


def test_an_unreadable_answer_is_logged_cut_to_its_first_letters(client, llm, caplog):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    reply = "ขอโทษครับ " + "ก" * steps.REPLY_LOG_LETTERS
    llm.respond = lambda request: reply

    assert run(client, "plot", ep_id)["state"] == "failed"

    assert f"plot attempt 1 is not the JSON asked for: no JSON object; it starts {reply[: steps.REPLY_LOG_LETTERS]!r}" in caplog.text
    assert reply[: steps.REPLY_LOG_LETTERS + 1] not in caplog.text


def test_a_cards_answer_with_no_card_three_times_fails_write_failed_and_is_logged(client, llm, caplog):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    llm.respond.__self__.cards = lambda act: {"segments": [{"background": "b_unknown", "cards": []}]}

    job = run(client, "cards", ep_id)

    # The plot, then three tries of the first act.
    assert (job["state"], job["error"]["code"], len(llm.requests)) == ("failed", "write_failed", 4)
    assert "cards of act 1 attempt 3 is not the JSON asked for: no segment with a card;" in caplog.text


def test_a_plot_job_whose_qwen_dies_while_loading_fails_crashed_and_frees_the_gpu(client, llm):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.crash_on_load = True

    job = run(client, "plot", ep_id)

    assert (job["state"], job["error"]["code"]) == ("failed", "crashed")
    assert gpu_holder() is None


def test_a_plot_job_whose_qwen_errs_in_the_code_fails_model_failed_without_the_gpu_advice(client, llm):
    """D84, for Qwen's child."""
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    llm.fail_at, llm.fail_with = 0, CODE_ERROR

    job = run(client, "plot", ep_id)

    assert (job["state"], job["error"]) == ("failed", {"code": "model_failed", "message": f"ร่างการ์ตูนเล่าไม่สำเร็จ: {CODE_ERROR}"})
    assert gpu_holder() is None


def test_a_plot_try_that_takes_too_long_stops_its_qwen_and_the_next_try_starts_another(client, llm, monkeypatch, caplog):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    os_timeouts(monkeypatch, darwin=0.2, win32=0.2)
    write, asked = llm.respond, []

    def first_hangs(request):
        asked.append(request)
        return llm.HANG if len(asked) == 1 else write(request)

    llm.respond = first_hangs

    job = run(client, "plot", ep_id)

    assert job["state"] == "done"
    first, second = llm.processes
    assert first.terminated  # stopped at the timeout
    assert not second.is_alive()  # the job's end stopped the one that answered
    assert gpu_holder() is None
    assert "not the JSON asked for" not in caplog.text  # a try that took too long logs only that


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


@pytest.mark.parametrize("item_kind", ["characters", "backgrounds"])
def test_a_plot_of_more_items_of_a_kind_than_it_may_use_is_invalid_request_from_the_page_and_asked_again_of_qwen(
    client, llm, item_kind
):
    series_id, _, background = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    too_many = [{"name": f"ใหม่ {n}"} for n in range(KINDS[item_kind].plot_max + 1)]
    plot = {"characters": [], "backgrounds": [{"id": background}]} | {item_kind: too_many}

    response = client.patch(f"/api/toon/eps/{ep_id}", json={"plot": plot})
    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")

    llm.respond.__self__.plot |= {item_kind: too_many}  # the `Writer` behind `respond` (fakes.Writer)
    job = run(client, "plot", ep_id)
    assert (job["state"], job["error"]["code"], len(llm.requests)) == ("failed", "write_failed", writer.ATTEMPTS)


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
    series = client.get(f"{TOON_SERIES}/{series_id}").json()
    new_background = next(b for b in series["backgrounds"] if b["name"] == "ห้องน้ำชั้นสาม")
    assert new_background["ref_rev"] == 0
    assert any(c["name"] == "ลุงยาม" and c["ref_rev"] == 0 for c in series["characters"])
    ep = client.get(f"/api/toon/eps/{ep_id}").json()
    assert ep["stage"] == "cards"
    assert [b["id"] for b in ep["plot"]["backgrounds"]] == [new_background["id"]]
    assert all(act["cards_from"] == act["summary"] for act in ep["acts"])
    assert {card["image_status"] for card in cards_of(ep)} == {"no_ref"}
    assert [(c["edited"], c["hold_s"]) for c in cards_of(ep)[:2]] == [(False, 0), (False, 2)]  # D21: silent holds 2 s


def test_a_cards_answer_the_way_the_real_qwen_writes_it_is_read(client, llm):
    # Cut from a real Qwen answer to the Cards prompt of e_14c37720's second act (ticket 16): pretty-printed,
    # no code fence, a null sound, and the plot's characters by id.
    series_id, character, background = with_series(client, llm)
    llm.respond.__self__.plot |= {"characters": [{"id": character}], "backgrounds": [{"id": background}]}
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    reply = (
        f'{{\n  "segments": [\n    {{\n      "background": "{background}",\n      "sound": null,\n      "cards": [\n'
        f'        {{\n          "text": "ครูเอกเดินเข้ามา",\n          "characters": [\n            "{character}"\n'
        '          ],\n          "description": "ครูเอกยืนนิ่งตรงกลางห้อง แสงสลัวจากหน้าต่างทำให้ใบหน้าดูซีดจาง",\n'
        '          "motion": "still",\n          "flicker": false\n        },\n'
        '        {\n          "text": "ฉันจับหนังสือไว้",\n          "characters": [],\n'
        '          "description": "มือฉันกำหนังสือแน่นจนเล็บจิกเข้าเนื้อ แสงในห้องเริ่มมืดลง",\n'
        '          "motion": "zoom_in",\n          "flicker": true\n        }\n      ]\n    }\n  ]\n}'
    )
    llm.respond = lambda request: reply

    assert (run(client, "cards", ep_id)["state"], len(llm.requests)) == ("done", 5)  # the plot, then one per act

    # Every act got the same answer; the second is the act it was written for.
    segment = client.get(f"/api/toon/eps/{ep_id}").json()["acts"][1]["segments"][0]
    assert (segment["background_id"], segment["sound"]) == (background, None)
    cards = [(c["text"], c["character_ids"], c["motion"], c["flicker"]) for c in segment["cards"]]
    assert cards == [("ครูเอกเดินเข้ามา", [character], "still", False), ("ฉันจับหนังสือไว้", [], "zoom_in", True)]


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
    series = client.get(f"{TOON_SERIES}/{series_id}").json()
    assert first["background_id"] == ep["plot"]["backgrounds"][0]["id"]  # not in the plot: the plot's first
    assert (first["sound"], second["sound"]) == (None, {"sound_id": "m_00000001", "volume": 30})
    assert (first["cards"][0]["character_ids"], first["cards"][0]["motion"]) == ([character], "still")
    assert "m_00000001: ฝนตกในป่า" in llm.requests[-1].prompt
    assert len(series["characters"]) == 3


def test_a_card_answer_with_a_list_for_a_sound_or_an_object_for_a_character_drops_them(client, llm):
    series_id, character, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    llm.respond.__self__.cards = lambda act: {
        "segments": [
            {
                "background": ["b_x"],
                "sound": ["m_00000001"],
                "cards": [{"text": "สองคน", "characters": [{"id": character}, character], "motion": ["still"]}],
            }
        ]
    }

    assert run(client, "cards", ep_id)["state"] == "done"

    segment = client.get(f"/api/toon/eps/{ep_id}").json()["acts"][0]["segments"][0]
    assert (segment["sound"], segment["cards"][0]["character_ids"]) == (None, [character])


def test_a_sound_deleted_from_the_library_while_qwen_splits_the_act_is_not_kept(client, llm, project):
    series_id, _, _ = with_series(client, llm)
    project.toon_sounds_file.parent.mkdir(parents=True)
    sounds = {"version": 1, "sounds": [{"id": "m_00000001", "name": "ฝนตกในป่า", "duration_s": 60, "source": "file"}]}
    project.toon_sounds_file.write_text(json.dumps(sounds), encoding="utf-8")
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)

    def cards(act):
        if project.toon_sounds_file.read_text(encoding="utf-8").count("m_00000001"):  # the first act's answer
            assert client.delete("/api/toon/sounds/m_00000001").status_code == 204  # no EP plays it yet
        return {"segments": [{"background": None, "sound": "m_00000001", "cards": [{"text": "ฝนตก", "characters": []}]}]}

    llm.respond.__self__.cards = cards
    run(client, "cards", ep_id)

    segment = client.get(f"/api/toon/eps/{ep_id}").json()["acts"][0]["segments"][0]
    assert segment["sound"] is None


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

    edit_stored_ep(project, series_id, ep["id"], draw)
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
        card.audio = Audio(tts_text="x", voice_id=TOON_VOICE, duration_s=1)

    edit_stored_ep(project, series_id, ep["id"], draw)
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
    folder = EpAddress(project, series_id, ep_id).dir
    before = (folder / "ep.json").read_text(encoding="utf-8"), (project.series_dir(series_id) / "series.json").read_text(encoding="utf-8")
    if ending == "cancel":
        llm.pause_at(2)
    else:
        llm.crash_at = 2

    start(client, "cards", ep_id)
    if ending == "cancel":
        llm.wait_until(2)
        client.delete(TOON_CURRENT)
    job = wait_for_toon_job(client)

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
        card.audio = Audio(tts_text=thai.spoken(card.text), voice_id=TOON_VOICE, duration_s=3.1)
        card.hold_s = 0.5

    edit_stored_ep(project, series_id, ep["id"], heard)
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
        card.audio = Audio(tts_text=thai.spoken(card.text), voice_id=TOON_VOICE, duration_s=1)

    edit_stored_ep(project, series_id, ep["id"], drawn)
    write_toon_voice(project, "v_00000002")
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
    wait_for_toon_job(client)
    assert client.get(f"/api/toon/eps/{ep['id']}").json()["locked"] is False


@pytest.mark.parametrize("kind", ["plot", "cards"])
def test_deleting_a_series_during_its_plot_or_cards_job_is_series_busy(client, llm, kind):
    if kind == "plot":
        series_id, _, _ = with_series(client, llm)
        ep = new_ep(client, series_id)
    else:
        series_id, ep = with_cards(client, llm)
        client.patch(f"/api/toon/eps/{ep['id']}/acts/{ep['acts'][0]['id']}", json={"summary": "สรุปใหม่"})
    llm.pause_at(0)
    assert start(client, kind, ep["id"]).status_code == 202
    llm.wait_until(0)

    response = client.request("DELETE", f"{TOON_SERIES}/{series_id}", json={"confirm_eps": 1})

    assert (response.status_code, response.json()["code"]) == (409, "series_busy")
    llm.release(0)
    wait_for_toon_job(client)


def test_deleting_a_character_a_card_or_plot_uses_is_in_use_with_the_eps(client, llm):
    series_id, character, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    run(client, "plot", ep_id)
    client.patch(f"/api/toon/eps/{ep_id}", json={"title": "ตอนแรก"})

    response = client.delete(f"{TOON_SERIES}/{series_id}/characters/{character}")

    assert (response.status_code, response.json()["code"], response.json()["eps"]) == (409, "in_use", [{"n": 1, "title": "ตอนแรก"}])


def test_deleting_a_character_only_a_card_uses_is_in_use(client, llm, project):
    series_id, ep = with_cards(client, llm)
    character = next(item["id"] for item in ep["plot"]["characters"] if item["name"] == "" and item["id"])

    def card_only(stored):
        stored.plot.characters = [item for item in stored.plot.characters if item.id != character]
        stored.acts[0].segments[0].cards[0].character_ids = [character]

    edit_stored_ep(project, series_id, ep["id"], card_only)

    response = client.delete(f"{TOON_SERIES}/{series_id}/characters/{character}")

    assert (response.status_code, response.json()["code"], [e["n"] for e in response.json()["eps"]]) == (409, "in_use", [1])


def test_deleting_a_background_only_a_segment_uses_is_in_use(client, llm, project):
    series_id, ep = with_cards(client, llm)
    background = client.get(f"{TOON_SERIES}/{series_id}").json()["backgrounds"][0]["id"]

    def segment_only(stored):
        stored.plot.backgrounds = [item for item in stored.plot.backgrounds if item.id != background]
        for act in stored.acts:
            for segment in act.segments:
                segment.background_id = background

    edit_stored_ep(project, series_id, ep["id"], segment_only)

    response = client.delete(f"{TOON_SERIES}/{series_id}/backgrounds/{background}")

    assert (response.status_code, response.json()["code"], [e["n"] for e in response.json()["eps"]]) == (409, "in_use", [1])


def test_deleting_the_saved_voice_an_ep_narrates_with_is_voice_in_use(client, llm, project):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    write_toon_voice(project, "v_00000002")
    client.patch(f"{TOON_SERIES}/{series_id}", json={"voice_id": "v_00000002"})
    client.patch(f"/api/toon/eps/{ep_id}", json={"voice_id": TOON_VOICE})
    client.patch(f"{TOON_SERIES}/{series_id}", json={"voice_id": "v_00000002"})

    response = client.delete(f"/api/spoil-maker/voices/{TOON_VOICE}")

    assert (response.status_code, response.json()["code"]) == (409, "voice_in_use")


def test_changing_an_ep_s_voice_waits_for_the_draft_s_lock(client, llm, project):
    series_id, _, _ = with_series(client, llm)
    ep_id = new_ep(client, series_id)["id"]
    write_toon_voice(project, "v_00000002")
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


@pytest.mark.parametrize("kind", ["poster", ["plot"], {"plot": True}, None])
def test_a_toon_job_of_a_kind_it_does_not_know_is_invalid_request(client, kind):
    response = client.post(TOON_JOBS, json={"kind": kind})
    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")
