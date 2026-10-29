import json
import os
import shutil

import pytest

from backend.checks import run_checks
from backend.models import MODELS, OMNIVOICE
from backend.paths import ProjectPaths
from backend.setup import run_setup

from .fakes import cuda_device, item, ok_deno, ok_ffmpeg, ok_yt_dlp, write_snapshot

GB = 1_000_000_000


@pytest.fixture
def empty_root(fake_root):
    """A project root with a .venv but no models downloaded yet."""
    shutil.rmtree(ProjectPaths(fake_root).models_dir)
    return fake_root


class FakeNpmInstall:
    """Stands in for the two `npm install` runs."""

    def __init__(self, fail=False):
        self.fail = fail
        self.roots = []

    def __call__(self, root):
        self.roots.append(root)
        if self.fail:
            raise RuntimeError("npm ERR! network")


class FakeDownload:
    """Stands in for huggingface_hub.snapshot_download."""

    def __init__(self, root, fail=False):
        self.root = root
        self.fail = fail
        self.calls = []

    def __call__(self, repo_id, *, revision, cache_dir, allow_patterns):
        self.calls.append(repo_id)
        if self.fail:
            raise OSError("connection reset")
        model = next(m for m in MODELS if m.repo_id == repo_id)
        assert cache_dir == ProjectPaths(self.root).hub_dir
        return str(write_snapshot(self.root, model, revision))


def run_with_fakes(root, download, **overrides):
    options = {
        "download": download,
        "npm_install": FakeNpmInstall(),
        "backend_running": lambda: False,
        "free_bytes": lambda path: 100 * GB,
        "device_probe": cuda_device,
        "ffmpeg_probe": ok_ffmpeg,
        "deno_probe": ok_deno,
        "yt_dlp_probe": ok_yt_dlp,
    }
    return run_setup(root, **(options | overrides))


def test_successful_download_writes_markers_and_exits_0(empty_root, capsys):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download)

    assert exit_code == 0
    marker = json.loads(ProjectPaths(empty_root).marker(OMNIVOICE).read_text(encoding="utf-8"))
    assert marker["revision"] == OMNIVOICE.revision
    assert marker["size_bytes"] == 4216
    result = run_checks(empty_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)
    assert item(result, "model_omnivoice").status == "ok"
    assert item(result, "model_whisper").status == "ok"
    assert "ขั้นต่อไป: รัน npm run dev แล้วเปิด http://localhost:5173" in capsys.readouterr().out


def test_failed_download_leaves_no_marker_removes_lock_and_exits_1(empty_root, capsys):
    download = FakeDownload(empty_root, fail=True)

    exit_code = run_with_fakes(empty_root, download)

    project = ProjectPaths(empty_root)
    assert exit_code == 1
    assert not project.marker(OMNIVOICE).exists()
    assert not project.setup_lock.exists()
    assert "connection reset" in capsys.readouterr().out


def test_lock_held_by_a_running_process_exits_1_without_downloading(empty_root, capsys):
    lock = ProjectPaths(empty_root).setup_lock
    lock.parent.mkdir(parents=True)
    lock.write_text(str(os.getpid()), encoding="utf-8")
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download)

    assert exit_code == 1
    assert download.calls == []
    assert "setup กำลังรันอยู่อีกหน้าต่าง" in capsys.readouterr().out


def test_stale_lock_from_a_dead_process_is_taken_over(empty_root):
    lock = ProjectPaths(empty_root).setup_lock
    lock.parent.mkdir(parents=True)
    lock.write_text("999999999", encoding="utf-8")

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root))

    assert exit_code == 0
    assert not lock.exists()


def test_low_disk_space_with_models_to_download_exits_1(empty_root, capsys):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download, free_bytes=lambda path: 9 * GB)

    assert exit_code == 1
    assert download.calls == []
    out = capsys.readouterr().out
    assert "9.0 GB" in out
    assert "15 GB" in out


def test_running_backend_stops_setup_before_anything(empty_root, capsys):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download, backend_running=lambda: True)

    assert exit_code == 1
    assert download.calls == []
    assert "ปิด npm run dev ก่อนรัน setup" in capsys.readouterr().out


def test_second_run_skips_models_that_are_ok_even_with_low_disk(fake_root):
    download = FakeDownload(fake_root)

    exit_code = run_with_fakes(fake_root, download, free_bytes=lambda path: 1 * GB)

    assert exit_code == 0
    assert download.calls == []


def test_missing_items_after_download_exit_1(empty_root, capsys):
    def broken_ffmpeg():
        raise RuntimeError("no ffmpeg")

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), ffmpeg_probe=broken_ffmpeg)

    assert exit_code == 1
    assert "ffmpeg" in capsys.readouterr().out


def test_corrupt_marker_is_downloaded_again(fake_root):
    ProjectPaths(fake_root).marker(OMNIVOICE).write_text("", encoding="utf-8")
    download = FakeDownload(fake_root)

    exit_code = run_with_fakes(fake_root, download)

    assert exit_code == 0
    assert download.calls == ["k2-fsa/OmniVoice"]


def test_npm_install_runs_again_on_every_setup_run(fake_root):
    npm_install = FakeNpmInstall()

    first = run_with_fakes(fake_root, FakeDownload(fake_root), npm_install=npm_install)
    second = run_with_fakes(fake_root, FakeDownload(fake_root), npm_install=npm_install)

    assert (first, second) == (0, 0)
    assert npm_install.roots == [fake_root, fake_root]


def test_npm_install_runs_after_the_models_are_downloaded(empty_root):
    markers_at_install = []

    def npm_install(root):
        markers_at_install.extend(p.name for p in ProjectPaths(root).markers_dir.glob("*.json"))

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), npm_install=npm_install)

    assert exit_code == 0
    assert len(markers_at_install) == len(MODELS)


def test_failed_npm_install_removes_lock_and_exits_1(fake_root, capsys):
    exit_code = run_with_fakes(
        fake_root, FakeDownload(fake_root), npm_install=FakeNpmInstall(fail=True)
    )

    assert exit_code == 1
    assert not ProjectPaths(fake_root).setup_lock.exists()
    assert "ล้มที่ขั้น npm install: npm ERR! network" in capsys.readouterr().out
