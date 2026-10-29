import sys
from pathlib import Path

import pytest

from backend.models import MODELS

from .fakes import write_marker, write_snapshot


@pytest.fixture
def fake_root(tmp_path, monkeypatch) -> Path:
    """A project root with every model downloaded, running from its .venv."""
    root = tmp_path / "framecraft"
    (root / ".venv").mkdir(parents=True)
    monkeypatch.setattr(sys, "prefix", str(root / ".venv"))
    for model in MODELS:
        write_snapshot(root, model)
        write_marker(root, model)
    return root
