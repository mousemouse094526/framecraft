import pytest
from fastapi.testclient import TestClient

from backend import checks, paths
from backend.app import app

from .fakes import ok_deno, ok_ffmpeg, ok_yt_dlp


@pytest.fixture
def client(fake_root, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", fake_root)
    monkeypatch.setattr(checks, "probe_device", lambda: "mps")
    monkeypatch.setattr(checks, "probe_ffmpeg", ok_ffmpeg)
    monkeypatch.setattr(checks, "probe_deno", ok_deno)
    monkeypatch.setattr(checks, "probe_yt_dlp", ok_yt_dlp)
    return TestClient(app, base_url="http://127.0.0.1")


def test_status_api_returns_the_checklist_as_json(client):
    response = client.get("/api/setup/status")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["ok_count"] == 15
    assert body["total"] == 15
    assert len(body["items"]) == 15


def test_status_api_rows_have_fix_null_when_ok_and_license_only_on_models(client):
    body = client.get("/api/setup/status").json()

    device = next(i for i in body["items"] if i["id"] == "device")
    assert device == {
        "id": "device",
        "label": "Device",
        "status": "ok",
        "detail": "mps",
        "fix": None,
        "fix_kind": None,
        "license": None,
    }
    whisper = next(i for i in body["items"] if i["id"] == "model_whisper")
    assert whisper["license"] == {
        "name": "MIT",
        "url": "https://opensource.org/license/mit",
        "author": "OpenAI",
        "model_url": "https://huggingface.co/openai/whisper-large-v3-turbo",
    }


@pytest.mark.parametrize(
    ("method", "path", "body", "status", "code"),
    [
        ("GET", "/api/no-such-thing", None, 404, "not_found"),
        ("DELETE", "/api/setup/status", None, 405, "method_not_allowed"),
        ("POST", "/api/spoil-maker/voices", [], 400, "invalid_request"),
    ],
)
def test_every_refusal_has_the_one_flat_shape(client, method, path, body, status, code):
    response = client.request(method, path, json=body)

    assert response.status_code == status
    assert response.json()["code"] == code
    assert isinstance(response.json()["message"], str)
