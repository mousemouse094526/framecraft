"""scripts/dev-api.mjs starts the backend for `npm run dev` from the venv's own
Python, so it works in a terminal that can't see uv yet. These run it with
Node in a copy of the project that has no real venv."""

import shutil
import subprocess
import sys

import pytest

from backend.paths import ROOT

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="the fake venv Python is a shell script"
)


def _project_copy(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy(ROOT / "scripts" / "dev-api.mjs", scripts)
    return tmp_path


def _run(project):
    return subprocess.run(
        ["node", str(project / "scripts" / "dev-api.mjs")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )


def test_without_a_venv_it_says_to_run_setup_and_exits_1(tmp_path):
    result = _run(_project_copy(tmp_path))

    assert result.returncode == 1
    assert "ยังไม่ได้ติดตั้ง: รัน ./setup.sh ก่อน" in result.stderr


def test_runs_uvicorn_with_the_venv_python_and_passes_its_exit_code(tmp_path):
    project = _project_copy(tmp_path)
    python = project / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text('#!/bin/sh\necho "$@"\nexit 3\n')
    python.chmod(0o755)

    result = _run(project)

    assert result.stdout.strip() == "-m uvicorn backend.app:app --host 127.0.0.1 --port 8000"
    assert result.returncode == 3
