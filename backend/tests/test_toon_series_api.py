"""Series, characters and backgrounds under /api/toon (toon seam 1 › Series)."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from backend import gpu, paths
from backend.app import app
from backend.paths import ProjectPaths
from backend.toon import jobs

VOICE = "v_8f2c01ab"
SERIES = "/api/toon/series"


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def client(fake_root, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(gpu, "slot", gpu.GpuSlot())
    monkeypatch.setattr(jobs, "toon_jobs", jobs.ToonJobs())
    write_voice(ProjectPaths(fake_root))
    return TestClient(app, base_url="http://127.0.0.1")


def write_voice(project: ProjectPaths, voice_id: str = VOICE) -> None:
    project.voices_dir.mkdir(parents=True, exist_ok=True)
    stored = {"name": "เสียง", "kind": "design", "speed": 1.0, "chars_per_s": 15.0, "created_at": "2026-11-02T10:00:00+07:00"}
    (project.voices_dir / f"{voice_id}.json").write_text(json.dumps(stored), encoding="utf-8")
    (project.voices_dir / f"{voice_id}.wav").write_bytes(b"wav")
    (project.voices_dir / f"{voice_id}.pt").write_bytes(b"pt")


def create(client, **changes) -> dict:
    body = {"name": "รุ่นพี่เล่าว่า…", "channel_name": "รุ่นพี่เล่าว่า", "layout": "frame", "genre": "horror", "voice_id": VOICE}
    response = client.post(SERIES, json=body | changes)
    assert response.status_code == 201, response.json()
    return response.json()


def write_ep(project: ProjectPaths, series_id: str, ep_id: str, n: int, title: str) -> None:
    folder = project.series_dir(series_id) / "eps" / ep_id
    folder.mkdir(parents=True)
    (folder / "ep.json").write_text(json.dumps({"version": 1, "id": ep_id, "n": n, "title": title}), encoding="utf-8")


def test_a_horror_series_starts_with_the_horror_acts_style_and_tone(client):
    series = create(client)

    assert series["acts"] == ["เปิด", "ปม", "หักมุม", "จบหลอน"]
    assert series["style"].startswith("flat 2D cartoon illustration") and "dark night scene" in series["style"]
    assert series["tone"] == 'เล่าเป็น "ฉัน" น้ำเสียงเรียบ ช้า ชวนขนลุก ประโยคสั้น'
    assert (series["max_ep"], series["name_tags"], series["characters"]) == (0, True, [])


def test_a_comedy_series_starts_with_the_comedy_defaults(client):
    series = create(client, genre="comedy", layout="full")

    assert series["acts"] == ["ตั้งเรื่อง", "ปั่น", "พลิก", "ตบมุก"]
    assert series["style"].endswith("bright cheerful colors, soft daylight")
    assert series["tone"] == "เล่ากวนๆ จังหวะเร็ว มีมุกตบท้าย ประโยคสั้น"


def test_a_new_series_takes_the_style_tone_and_acts_it_is_sent_in_place_of_its_genre_defaults(client):
    series = create(client, style="ink wash", tone="", acts=["ต้น", "จบ"])

    assert (series["style"], series["tone"], series["acts"]) == ("ink wash", "", ["ต้น", "จบ"])


def test_a_new_series_with_no_acts_is_invalid_request(client):
    response = client.post(SERIES, json={"name": "ช่อง", "layout": "frame", "genre": "horror", "voice_id": VOICE, "acts": []})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_a_series_with_a_voice_that_isn_t_saved_is_voice_not_found(client):
    response = client.post(SERIES, json={"name": "ช่อง", "layout": "frame", "genre": "horror", "voice_id": "v_00000000"})

    assert (response.status_code, response.json()["code"]) == (400, "voice_not_found")


def test_patching_layout_or_genre_changes_neither(client):
    series = create(client)

    response = client.patch(f"{SERIES}/{series['id']}", json={"layout": "full", "genre": "comedy", "name": "ช่องใหม่"})

    assert response.status_code == 200
    assert (response.json()["layout"], response.json()["genre"], response.json()["name"]) == ("frame", "horror", "ช่องใหม่")


@pytest.mark.parametrize("acts", [[f"องก์ {n}" for n in range(9)], ["ก" * 21], []])
def test_acts_outside_1_to_8_names_of_1_to_20_letters_are_refused(client, acts):
    series = create(client)

    response = client.patch(f"{SERIES}/{series['id']}", json={"acts": acts})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")


def test_new_acts_are_kept(client):
    series = create(client)

    response = client.patch(f"{SERIES}/{series['id']}", json={"acts": ["หนึ่ง", "สอง"]})

    assert response.json()["acts"] == ["หนึ่ง", "สอง"]


def test_the_list_counts_each_series_eps(client, project):
    series = create(client)
    write_ep(project, series["id"], "e_00000001", 1, "เสียงเรียกจากป่า")

    listed = client.get(SERIES).json()

    assert [(s["id"], s["ep_count"], s["layout"]) for s in listed] == [(series["id"], 1, "frame")]


def test_deleting_a_series_without_confirm_eps_is_confirm_needed_with_its_eps(client, project):
    series = create(client)
    write_ep(project, series["id"], "e_00000002", 2, "ตอนสอง")
    write_ep(project, series["id"], "e_00000001", 1, "ตอนหนึ่ง")

    response = client.request("DELETE", f"{SERIES}/{series['id']}", json={"confirm_eps": 1})

    assert (response.status_code, response.json()["code"]) == (409, "confirm_needed")
    assert response.json()["eps"] == [{"n": 1, "title": "ตอนหนึ่ง"}, {"n": 2, "title": "ตอนสอง"}]


def test_a_confirmed_delete_removes_the_series_folder_and_keeps_the_saved_voice(client, project):
    series = create(client)
    write_ep(project, series["id"], "e_00000001", 1, "ตอนหนึ่ง")

    response = client.request("DELETE", f"{SERIES}/{series['id']}", json={"confirm_eps": 1})

    assert response.status_code == 204
    assert not project.series_dir(series["id"]).exists()
    assert (project.voices_dir / f"{VOICE}.json").is_file()
    assert client.get(f"{SERIES}/{series['id']}").status_code == 404


def test_a_saved_voice_a_series_uses_can_t_be_deleted(client):
    create(client)

    response = client.delete(f"/api/spoil-maker/voices/{VOICE}")

    assert (response.status_code, response.json()["code"]) == (409, "voice_in_use")


def test_a_series_json_of_another_version_or_unreadable_is_skipped_and_logged(client, project, caplog):
    kept = create(client)
    newer = project.series_dir("s_0000000a")
    newer.mkdir(parents=True)
    (newer / "series.json").write_text(json.dumps({"version": 2, "id": "s_0000000a"}), encoding="utf-8")
    broken = project.series_dir("s_0000000b")
    broken.mkdir(parents=True)
    (broken / "series.json").write_text("{not json", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="backend.toon.store"):
        listed = client.get(SERIES).json()

    assert [s["id"] for s in listed] == [kept["id"]]
    assert sum("skipped" in record.message for record in caplog.records) == 2


def test_characters_and_backgrounds_start_without_a_reference_image(client):
    series = create(client)

    client.post(f"{SERIES}/{series['id']}/characters", json={"name": "พีค", "tag": "สายแฟ", "description": "เสื้อฮาวาย"})
    after = client.post(f"{SERIES}/{series['id']}/backgrounds", json={"name": "กองไฟในป่า"}).json()

    assert [(c["name"], c["tag"], c["ref_rev"], c["pending"]) for c in after["characters"]] == [("พีค", "สายแฟ", 0, 0)]
    assert [(b["name"], b["ref_rev"]) for b in after["backgrounds"]] == [("กองไฟในป่า", 0)]
    assert after["characters"][0]["id"].startswith("c_") and after["backgrounds"][0]["id"].startswith("b_")


def test_a_character_name_over_30_letters_is_refused(client):
    series = create(client)

    response = client.post(f"{SERIES}/{series['id']}/characters", json={"name": "ก" * 31})

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")
