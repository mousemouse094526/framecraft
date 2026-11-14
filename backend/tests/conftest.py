import sys
from pathlib import Path

import pytest

from backend import checks
from backend.models import MODELS

from .fakes import ok_diffusers, ok_gguf, ok_mlx_vlm, ok_pythainlp, write_drum_kit, write_kanit, write_marker, write_snapshot


@pytest.fixture
def fake_root(tmp_path, monkeypatch) -> Path:
    """A project root with every model, Kanit and the drum samples downloaded, running from its .venv on
    a Mac with mlx-vlm, pythainlp, diffusers and gguf installed, whatever OS runs the tests (ADR 0016)."""
    monkeypatch.setattr(checks, "this_platform", lambda: "darwin")
    monkeypatch.setattr(checks, "probe_mlx_vlm", ok_mlx_vlm)
    monkeypatch.setattr(checks, "probe_pythainlp", ok_pythainlp)
    monkeypatch.setattr(checks, "probe_diffusers", ok_diffusers)
    monkeypatch.setattr(checks, "probe_gguf", ok_gguf)
    root = tmp_path / "framecraft"
    (root / ".venv").mkdir(parents=True)
    monkeypatch.setattr(sys, "prefix", str(root / ".venv"))
    for model in MODELS:
        write_snapshot(root, model)
        write_marker(root, model)
    write_kanit(root)
    write_drum_kit(root)
    return root
