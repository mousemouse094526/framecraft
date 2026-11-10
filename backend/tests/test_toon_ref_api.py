"""The Ref job, picking a reference picture and uploading one, under /api/toon, with fake Qwen
and klein children (toon seam 1 › Ref job, ref/pick, upload, `not_ready` of klein)."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend import gpu
from backend.app import app
from backend.models import KLEIN
from backend.paths import ProjectPaths
from backend.toon import series
from backend.toon.klein import Draw, Encode

from .fakes import poll_until, toon_api
from .test_toon_series_api import create

SERIES = "/api/toon/series"
JOBS = "/api/toon/jobs"
CURRENT = "/api/toon/jobs/current"
FINISHED = {"done", "failed", "cancelled"}


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


def scene(request) -> str:
    return '{"scene": "A boy with short black hair in a navy shirt."}'


llm, klein, tts, client = toon_api(lambda: scene)


def add_item(client, series_id: str, kind: str = "characters", **body) -> dict:
    response = client.post(f"{SERIES}/{series_id}/{kind}", json={"name": "พี่ต้น", "description": "ผมสั้น เสื้อกรมท่า"} | body)
    assert response.status_code == 201, response.json()
    return response.json()[kind][-1]


def start_ref(client, series_id: str, item_id: str, kind: str = "characters"):
    return client.post(JOBS, json={"kind": "ref", "series_id": series_id, "item_kind": kind, "item_id": item_id})


def wait_for_end(client) -> dict:
    return poll_until(client, CURRENT, lambda job: job["state"] in FINISHED)


def gpu_is_free() -> bool:
    try:
        gpu.slot.take("describe")
    except Exception:
        return False
    gpu.slot.release("describe")
    return True


def waiting_picture(client, series_id: str, item_id: str, n: int) -> bytes:
    """Picture `n` of a character's waiting set, as the page gets it."""
    response = client.get(f"{SERIES}/{series_id}/characters/{item_id}/ref/pending/{n}")
    assert response.status_code == 200, response.json()
    return response.content


def with_pending(client) -> tuple[str, str]:
    """A Series with one character whose Ref job is done: three pictures wait."""
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    assert start_ref(client, series_id, item_id).status_code == 202
    assert wait_for_end(client)["state"] == "done"
    return series_id, item_id


def png(width: int, height: int) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), "gray").save(out, "PNG")
    return out.getvalue()


def upload(client, series_id: str, kind: str, item_id: str, body: bytes):
    return client.post(
        f"{SERIES}/{series_id}/{kind}/{item_id}/ref/upload?size={len(body)}",
        content=body,
        headers={"Content-Type": "application/octet-stream"},
    )


# --- Ref job ---


def test_a_ref_job_translates_then_draws_three_pictures_that_wait_to_be_picked(client, llm, klein, project):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    llm.pause_at(0)
    klein.pause_at(1)

    started = start_ref(client, series_id, item_id)
    assert (started.status_code, started.json()["state"], started.json()["item_id"]) == (202, "translating", item_id)
    llm.wait_until(0)
    assert client.get(CURRENT).json()["state"] == "translating"
    llm.release(0)
    klein.wait_until(1)
    drawing = client.get(CURRENT).json()
    assert (drawing["state"], drawing["done"], drawing["total"]) == ("drawing", 0, 3)
    assert not llm.processes[0].is_alive()  # Qwen's child ended before klein loaded (D36)
    klein.release(1)

    job = wait_for_end(client)
    assert (job["state"], job["done"], job["total"]) == ("done", 3, 3)
    character = client.get(f"{SERIES}/{series_id}").json()["characters"][0]
    assert (character["pending"], character["ref_rev"]) == (3, 0)


def test_a_character_s_prompt_holds_qwen_s_scene_and_the_series_style_and_three_seeds(client, klein):
    series_id, _ = with_pending(client)

    encode, *draws = klein.requests
    assert isinstance(encode, Encode) and len(encode.prompts) == 1
    assert encode.prompts[0].startswith("Full body, front view, standing, plain light gray background. A boy with short")
    assert "dark night scene" in encode.prompts[0]
    assert [type(draw) for draw in draws] == [Draw, Draw, Draw]
    assert {(draw.width, draw.height, tuple(draw.ref_paths)) for draw in draws} == {(576, 1024, ())}
    assert len({draw.seed for draw in draws}) == 3


def test_a_background_is_drawn_at_the_series_card_size(client, klein):
    series_id = create(client, layout="full")["id"]
    item_id = add_item(client, series_id, "backgrounds", name="ห้องน้ำโรงเรียน")["id"]

    assert start_ref(client, series_id, item_id, "backgrounds").status_code == 202
    assert wait_for_end(client)["state"] == "done"
    assert (klein.requests[1].width, klein.requests[1].height) == (576, 1024)


def test_qwen_s_unreadable_answer_puts_the_description_in_as_written(client, llm, klein):
    llm.respond = lambda request: "not json"

    with_pending(client)

    assert "ผมสั้น เสื้อกรมท่า" in klein.requests[0].prompts[0]


def test_a_second_ref_job_meanwhile_is_busy(client, klein):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    klein.pause_at(1)
    start_ref(client, series_id, item_id)
    klein.wait_until(1)

    response = start_ref(client, series_id, item_id)

    assert (response.status_code, response.json()["code"]) == (409, "busy")
    klein.release(1)
    wait_for_end(client)


def test_a_ref_job_during_a_describe_job_is_gpu_busy_naming_it(client):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    gpu.slot.take("describe")

    response = start_ref(client, series_id, item_id)

    assert (response.status_code, response.json()["code"], response.json()["running"]) == (409, "gpu_busy", "describe")


def test_a_ref_job_without_klein_s_marker_is_not_ready_naming_the_row(client, project):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    project.marker(KLEIN).unlink()

    response = start_ref(client, series_id, item_id)

    assert (response.status_code, response.json()["code"]) == (503, "not_ready")
    assert response.json()["rows"] == ["model_klein"]


def test_deleting_a_series_during_its_ref_job_is_series_busy(client, klein, project):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    klein.pause_at(1)
    start_ref(client, series_id, item_id)
    klein.wait_until(1)

    response = client.request("DELETE", f"{SERIES}/{series_id}", json={"confirm_eps": 0})

    assert (response.status_code, response.json()["code"]) == (409, "series_busy")
    klein.release(1)
    wait_for_end(client)
    assert project.series_dir(series_id).is_dir()


def test_a_ref_job_on_a_full_disk_after_gpu_busy_is_checked_is_disk_full_and_frees_the_gpu(client, monkeypatch):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    monkeypatch.setattr(series.disk, "free_bytes", lambda path: 0)

    response = start_ref(client, series_id, item_id)

    assert (response.status_code, response.json()["code"]) == (507, "disk_full")
    assert gpu_is_free()


def test_a_ref_job_on_a_full_disk_while_the_gpu_is_taken_is_gpu_busy(client, monkeypatch):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    monkeypatch.setattr(series.disk, "free_bytes", lambda path: 0)
    gpu.slot.take("describe")

    response = start_ref(client, series_id, item_id)

    assert (response.status_code, response.json()["code"]) == (409, "gpu_busy")


ITEM_ROUTES = [
    ("patch", "", {"json": {"name": "พี่ต้น"}}),
    ("delete", "", {}),
    ("get", "/ref", {}),
    ("get", "/ref/pending/1", {}),
    ("post", "/ref/pick", {"json": {"n": 1}}),
    ("post", "/ref/upload/check", {"json": {"size": 10}}),
    ("post", "/ref/upload?size=10", {"content": b"x" * 10, "headers": {"Content-Type": "application/octet-stream"}}),
]


@pytest.mark.parametrize(("method", "tail", "send"), ITEM_ROUTES)
def test_every_route_of_one_item_is_not_found_for_a_series_or_an_item_that_isn_t_there(client, method, tail, send):
    series_id = create(client)["id"]
    no_series = client.request(method, f"{SERIES}/s_00000000/characters/c_00000000{tail}", **send)
    no_item = client.request(method, f"{SERIES}/{series_id}/characters/c_00000000{tail}", **send)
    assert (no_series.status_code, no_series.json()) == (404, {"code": "not_found", "message": "ไม่พบ Series นี้"})
    assert (no_item.status_code, no_item.json()) == (404, {"code": "not_found", "message": "ไม่พบตัวละครหรือฉากหลังนี้"})


def test_a_ref_job_for_an_item_that_isn_t_there_is_not_found(client):
    series_id = create(client)["id"]

    response = start_ref(client, series_id, "c_00000000")

    assert (response.status_code, response.json()["code"]) == (404, "not_found")


@pytest.mark.parametrize("ending", ["done", "failed", "cancelled"])
def test_every_ending_of_a_ref_job_frees_the_gpu(client, klein, ending):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    if ending == "failed":
        klein.fail_at = 2  # request 0 is `Encode`: the second picture fails
    if ending == "cancelled":
        klein.pause_at(1)
    start_ref(client, series_id, item_id)
    if ending == "cancelled":
        klein.wait_until(1)
        assert client.delete(CURRENT).status_code == 202

    job = wait_for_end(client)

    assert job["state"] == ending
    assert gpu_is_free()


def test_a_failed_ref_job_leaves_nothing_waiting(client, klein):
    klein.fail_at = 3  # the third picture: two are drawn already
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    start_ref(client, series_id, item_id)

    job = wait_for_end(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "model_failed")
    assert client.get(f"{SERIES}/{series_id}").json()["characters"][0]["pending"] == 0


def test_a_new_ref_job_of_the_same_item_replaces_the_waiting_set(client, klein, project):
    series_id, item_id = with_pending(client)
    start_ref(client, series_id, item_id)
    wait_for_end(client)

    waiting = [waiting_picture(client, series_id, item_id, n) for n in (1, 2, 3)]

    second_job = [f"png {draw.seed}".encode() for draw in klein.requests[5:]]
    assert waiting == second_job
    assert len(list(project.pending_refs_dir(series_id).glob("*.png"))) == 3


# --- ref/pick ---


def test_picking_makes_the_picture_the_reference_and_clears_the_set(client, project):
    series_id, item_id = with_pending(client)
    second = waiting_picture(client, series_id, item_id, 2)

    response = client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/pick", json={"n": 2})

    assert response.status_code == 200
    character = response.json()["characters"][0]
    assert (character["ref_rev"], character["pending"]) == (1, 0)
    assert client.get(f"{SERIES}/{series_id}/characters/{item_id}/ref").content == second
    assert list(project.pending_refs_dir(series_id).glob(f"{item_id}-*")) == []


def test_picking_again_drops_the_old_reference(client, project):
    series_id, item_id = with_pending(client)
    client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/pick", json={"n": 1})
    start_ref(client, series_id, item_id)
    wait_for_end(client)

    response = client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/pick", json={"n": 3})

    assert response.json()["characters"][0]["ref_rev"] == 2
    assert sorted(path.name for path in project.refs_dir(series_id).glob("*.png")) == [f"{item_id}-2.png"]


def test_picking_with_nothing_waiting_is_no_pending(client):
    series_id, item_id = with_pending(client)
    client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/pick", json={"n": 2})

    response = client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/pick", json={"n": 2})

    assert (response.status_code, response.json()["code"]) == (404, "no_pending")


@pytest.mark.parametrize("n", [4, 0, 1.5, True, "2"])
def test_picking_outside_one_to_three_is_invalid_request(client, n):
    series_id, item_id = with_pending(client)

    response = client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/pick", json={"n": n})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_a_waiting_picture_is_served_by_its_number(client, klein):
    series_id, item_id = with_pending(client)

    response = client.get(f"{SERIES}/{series_id}/characters/{item_id}/ref/pending/3")

    draws = [request for request in klein.requests if isinstance(request, Draw)]
    assert response.content == f"png {draws[2].seed}".encode()


def test_a_backend_start_clears_every_waiting_set(client, project):
    series_id, item_id = with_pending(client)

    with TestClient(app, base_url="http://127.0.0.1") as restarted:
        character = restarted.get(f"{SERIES}/{series_id}").json()["characters"][0]

    assert character["pending"] == 0
    assert not project.pending_refs_dir(series_id).exists()


# --- upload ---


def test_uploading_a_text_file_is_unsupported_file(client):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]

    response = upload(client, series_id, "characters", item_id, b"just some text\n")

    assert (response.status_code, response.json()["code"]) == (400, "unsupported_file")
    assert client.get(f"{SERIES}/{series_id}").json()["characters"][0]["ref_rev"] == 0


def test_a_square_background_in_a_frame_series_becomes_a_card(client):
    series_id = create(client, layout="frame")["id"]
    item_id = add_item(client, series_id, "backgrounds", name="ห้องเรียน")["id"]

    response = upload(client, series_id, "backgrounds", item_id, png(800, 800))

    assert response.json()["backgrounds"][0]["ref_rev"] == 1
    picture = client.get(f"{SERIES}/{series_id}/backgrounds/{item_id}/ref").content
    assert Image.open(io.BytesIO(picture)).size == (1024, 576)


def test_a_big_character_keeps_its_shape_with_the_long_side_at_1536(client):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]

    upload(client, series_id, "characters", item_id, png(1500, 3000))

    picture = client.get(f"{SERIES}/{series_id}/characters/{item_id}/ref").content
    assert Image.open(io.BytesIO(picture)).size == (768, 1536)


def test_an_upload_replaces_a_waiting_set(client, project):
    series_id, item_id = with_pending(client)

    response = upload(client, series_id, "characters", item_id, png(576, 1024))

    assert (response.json()["characters"][0]["ref_rev"], response.json()["characters"][0]["pending"]) == (1, 0)


def test_the_upload_check_refuses_a_file_over_20_mb(client):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]

    response = client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/upload/check", json={"size": 20 * 2**20 + 1})

    assert (response.status_code, response.json()["code"]) == (400, "file_too_large")


def test_a_multipart_upload_is_refused(client):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]

    response = client.post(f"{SERIES}/{series_id}/characters/{item_id}/ref/upload?size=3", files={"file": ("a.png", b"png")})

    assert response.status_code == 415


def test_a_ref_job_whose_klein_dies_while_loading_fails_crashed_and_frees_the_gpu(client, llm, klein):
    series_id = create(client)["id"]
    item_id = add_item(client, series_id)["id"]
    klein.crash_on_load = True

    assert start_ref(client, series_id, item_id).status_code == 202
    job = wait_for_end(client)

    assert (job["state"], job["error"]["code"]) == ("failed", "crashed")
    assert gpu_is_free()


def test_a_backend_shutdown_stops_a_running_ref_job_s_child(client, klein):
    """The Toon job is in `JOB_HOLDERS`: the lifespan's end stops its child."""
    with TestClient(app, base_url="http://127.0.0.1") as running:
        series_id = create(running)["id"]
        item_id = add_item(running, series_id)["id"]
        klein.pause_at(1)
        start_ref(running, series_id, item_id)
        klein.wait_until(1)

    assert klein.processes[0].terminated
