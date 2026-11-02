import sys
from pathlib import Path

import pytest

from backend import checks
from backend.models import MODELS

from .fakes import ok_mlx_vlm, ok_pythainlp, write_marker, write_snapshot


@pytest.fixture
def fake_root(tmp_path, monkeypatch) -> Path:
    """A project root with every model downloaded, running from its .venv on a Mac
    with mlx-vlm and pythainlp installed, whatever OS runs the tests (ADR 0016)."""
    monkeypatch.setattr(checks, "this_platform", lambda: "darwin")
    monkeypatch.setattr(checks, "probe_mlx_vlm", ok_mlx_vlm)
    monkeypatch.setattr(checks, "probe_pythainlp", ok_pythainlp)
    root = tmp_path / "framecraft"
    (root / ".venv").mkdir(parents=True)
    monkeypatch.setattr(sys, "prefix", str(root / ".venv"))
    for model in MODELS:
        write_snapshot(root, model)
        write_marker(root, model)
    return root
