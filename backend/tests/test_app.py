import re
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from backend import checks, paths
from backend.app import app
from backend.paths import ProjectPaths

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
    assert body["ok_count"] == 20
    assert body["total"] == 20
    assert len(body["items"]) == 20


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


def test_start_up_removes_what_every_job_left_unfinished(fake_root, monkeypatch):
    """`JOB_HOLDERS` runs each job's start-up clean (spoil-maker spec › Ops)."""
    monkeypatch.setattr(paths, "ROOT", fake_root)
    project = ProjectPaths(fake_root)
    leftovers = [
        project.renders_dir / "x.partial",
        project.new_shots_dir("a") / "0.jpg",
        project.pending_voice_dir / "preview.wav",
        project.episodes_dir / "a.json.0123abcd.tmp",  # an EP cut half-written under its own `.tmp` name
        project.episodes_file("dQw4w9WgXcQ"),  # a clip that isn't there
    ]
    for path in leftovers:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"half")

    with TestClient(app, base_url="http://127.0.0.1"):
        pass

    assert [path for path in leftovers if path.exists()] == []
    assert not project.new_shots_dir("a").exists()
    assert not project.pending_voice_dir.exists()


def test_the_backend_s_own_info_lines_reach_the_terminal_with_the_time():
    """A job's `started` / `ended … after N s` in `[api]` (toon D76): uvicorn's loggers only, before."""
    script = (
        "import logging; from backend import app; app.log_to_terminal(); "
        "logging.getLogger('backend.jobs').info('toon job ref c_1 ended done after 412 s')"
    )

    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)

    assert re.fullmatch(r"\d\d:\d\d:\d\d INFO backend.jobs: toon job ref c_1 ended done after 412 s\n", result.stderr)
