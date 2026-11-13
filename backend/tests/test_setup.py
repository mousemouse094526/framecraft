import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from backend import drum_kit, fonts
from backend.checks import run_checks
from backend.models import ADTOF, BASIC_PITCH, BEAT_THIS, KLEIN, KLEIN_GGUF, MODELS, OMNIVOICE, ONNX_MODELS, QWEN_MAC, QWEN_WINDOWS
from backend.paths import ProjectPaths
from backend.setup import run_setup

from .fakes import MODEL_FILES, broken_gpu, card, fake_probes, item, write_snapshot

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


KANIT_BYTES = {"Kanit-Bold.ttf": b"ttf bytes", "OFL.txt": b"license text"}


@pytest.fixture(autouse=True)
def fake_kanit(monkeypatch):
    """The pinned sha256 of the fake files, so setup can check them without the network.
    Autouse fixtures run first, so `fake_root` writes its marker with these too."""
    monkeypatch.setattr(fonts, "KANIT_SHA256", {n: hashlib.sha256(b).hexdigest() for n, b in KANIT_BYTES.items()})


DRUM_BYTES = {"snare_14/center/top/sn_center_vl1_rr1.flac": b"soft snare", "kick_24/kick/kick/k_kick_vl14_rr4.flac": b"kick"}


@pytest.fixture(autouse=True)
def fake_drum_kit(monkeypatch):
    """Two pinned drum samples standing in for the table, like `fake_kanit`."""
    monkeypatch.setattr(
        drum_kit,
        "SAMPLES",
        tuple(
            drum_kit.Sample("snare", "soft", 1, path, hashlib.sha256(content).hexdigest())
            for path, content in DRUM_BYTES.items()
        ),
    )


class FakeFetch:
    """Stands in for fetching a Kanit file or a drum sample over HTTPS; `wrong` serves other bytes
    for that file, `fail` raises for it, each up to `times` times (every time by default)."""

    def __init__(self, wrong: str | None = None, fail: str | None = None, times: int = 99):
        self.wrong, self.fail, self.times = wrong, fail, times
        self.urls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.urls.append(url)
        name = url.rsplit("/", 1)[1]
        if name in (self.wrong, self.fail) and self.urls.count(url) <= self.times:
            if name == self.fail:
                raise TimeoutError("timed out")
            return b"something else"
        return KANIT_BYTES.get(name) or next(b for p, b in DRUM_BYTES.items() if p.endswith(name))


class FakeDownload:
    """Stands in for huggingface_hub.snapshot_download."""

    def __init__(self, root, fail=False, leave_empty: str | None = None):
        self.root = root
        self.fail = fail
        self.leave_empty = leave_empty  # a folder the download "finishes" without (trial-klein-mac › 5.3)
        self.calls = []
        self.patterns: dict[str, list[str]] = {}

    def __call__(self, repo_id, *, revision, cache_dir, allow_patterns):
        self.calls.append(repo_id)
        self.patterns[repo_id] = allow_patterns
        if self.fail:
            raise OSError("connection reset")
        model = next(m for m in MODELS if m.repo_id == repo_id)
        assert cache_dir == ProjectPaths(self.root).hub_dir
        snapshot = write_snapshot(self.root, model, revision)
        if self.leave_empty:
            shutil.rmtree(snapshot / self.leave_empty, ignore_errors=True)
        return str(snapshot)


class FakeOpenSession:
    """Stands in for `onnx_runner.open_session`, the smoke test of a downloaded ONNX file (D20):
    records the files opened and raises for `broken`."""

    def __init__(self, broken: str | None = None):
        self.broken = broken
        self.opened: list[Path] = []

    def __call__(self, model_file: Path):
        self.opened.append(model_file)
        if model_file.name == self.broken:
            raise RuntimeError("[ONNXRuntimeError] : 7 : INVALID_PROTOBUF : Protobuf parsing failed.")
        return object()


ONNX_REPOS = [model.repo_id for model in ONNX_MODELS]


def run_with_fakes(root, download, probes=None, **overrides):
    options = {
        "download": download,
        "npm_install": FakeNpmInstall(),
        "fetch": FakeFetch(),
        "open_session": FakeOpenSession(),
        "backend_running": lambda: False,
        "free_bytes": lambda path: 100 * GB,
        "probes": probes or fake_probes(),
        "sys_platform": "darwin",  # the machine running the tests never decides (rules › testing)
    }
    return run_setup(root, **(options | overrides))


def test_successful_download_writes_markers_and_exits_0(empty_root, capsys):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download)

    assert exit_code == 0
    marker = json.loads(ProjectPaths(empty_root).marker(OMNIVOICE).read_text(encoding="utf-8"))
    assert marker["revision"] == OMNIVOICE.revision
    assert marker["size_bytes"] == sum(MODEL_FILES.values())
    result = run_checks(empty_root, fake_probes())
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


@pytest.mark.parametrize(("sys_platform", "required"), [("darwin", "32 GB"), ("win32", "42 GB")])
def test_low_disk_space_with_models_to_download_exits_1(empty_root, capsys, sys_platform, required):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download, free_bytes=lambda path: 9 * GB, sys_platform=sys_platform)

    assert exit_code == 1
    assert download.calls == []
    out = capsys.readouterr().out
    assert "9.0 GB" in out
    assert f"ต้องการ {required}" in out


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

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), fake_probes(ffmpeg=broken_ffmpeg))

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
    assert len(markers_at_install) == len([m for m in MODELS if "darwin" in m.platforms])


def test_failed_npm_install_removes_lock_and_exits_1(fake_root, capsys):
    exit_code = run_with_fakes(
        fake_root, FakeDownload(fake_root), npm_install=FakeNpmInstall(fail=True)
    )

    assert exit_code == 1
    assert not ProjectPaths(fake_root).setup_lock.exists()
    assert "ล้มที่ขั้น npm install: npm ERR! network" in capsys.readouterr().out


def test_mac_setup_downloads_qwen_too(empty_root):
    download = FakeDownload(empty_root)

    run_with_fakes(empty_root, download, sys_platform="darwin")

    assert download.calls == [
        "k2-fsa/OmniVoice",
        "openai/whisper-large-v3-turbo",
        "mlx-community/Qwen3.5-9B-MLX-4bit",
        "black-forest-labs/FLUX.2-klein-4B",
        "unsloth/FLUX.2-klein-4B-GGUF",
        *ONNX_REPOS,
    ]
    assert ProjectPaths(empty_root).marker(QWEN_MAC).is_file()


def test_windows_setup_downloads_qwen_s_own_repo_on_a_card_that_meets_its_target(empty_root):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download, sys_platform="win32")

    assert exit_code == 0
    assert download.calls == [
        "k2-fsa/OmniVoice",
        "openai/whisper-large-v3-turbo",
        "Qwen/Qwen3.5-9B",
        "black-forest-labs/FLUX.2-klein-4B",
        "unsloth/FLUX.2-klein-4B-GGUF",
        *ONNX_REPOS,
    ]
    assert ProjectPaths(empty_root).marker(QWEN_WINDOWS).is_file()
    assert not ProjectPaths(empty_root).marker(QWEN_MAC).exists()


@pytest.mark.parametrize(
    ("card", "says"),
    [
        (card("NVIDIA GeForce RTX 2060", 6, (7, 5)), "Qwen ต้องใช้การ์ด NVIDIA RTX 30xx ขึ้นไปที่มี VRAM อย่างน้อย 8 GB"),
        (broken_gpu, "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA"),
    ],
)
def test_windows_setup_skips_qwen_on_a_card_under_its_target_and_still_exits_0(empty_root, capsys, card, says):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download, probes=fake_probes(gpu=card), sys_platform="win32")

    assert exit_code == 0
    assert "Qwen/Qwen3.5-9B" not in download.calls
    out = capsys.readouterr().out
    assert f"ข้าม Qwen3.5 9B model: {says}" in out


def test_windows_setup_wants_42_gb_free_to_download_qwen(empty_root, capsys):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download, free_bytes=lambda path: 40 * GB, sys_platform="win32")

    assert exit_code == 1
    assert download.calls == []
    assert "ที่ว่างบนดิสก์ไม่พอ: มี 40.0 GB ต้องการ 42 GB" in capsys.readouterr().out


def test_windows_setup_that_skips_qwen_wants_only_27_gb_free(empty_root):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(
        empty_root,
        download,
        probes=fake_probes(gpu=card("NVIDIA GeForce RTX 2060", 6, (7, 5))),
        free_bytes=lambda path: 27 * GB,
        sys_platform="win32",
    )

    assert exit_code == 0
    assert download.calls == [
        "k2-fsa/OmniVoice",
        "openai/whisper-large-v3-turbo",
        "black-forest-labs/FLUX.2-klein-4B",
        "unsloth/FLUX.2-klein-4B-GGUF",
        *ONNX_REPOS,
    ]


def test_mac_setup_never_reads_the_card(empty_root):
    def must_not_run():
        raise AssertionError("the gpu probe ran on a Mac")

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), probes=fake_probes(gpu=must_not_run))

    assert exit_code == 0


def test_setup_fetches_kanit_at_the_pinned_commit_and_writes_its_marker(empty_root):
    fetch = FakeFetch()

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), fetch=fetch)

    assert exit_code == 0
    base = "https://raw.githubusercontent.com/google/fonts/130fcfb0ff422fec96b335616b2ca99f91914792/ofl/kanit/"
    assert fetch.urls[:2] == [base + "Kanit-Bold.ttf", base + "OFL.txt"]
    project = ProjectPaths(empty_root)
    assert (project.kanit_dir / "Kanit-Bold.ttf").read_bytes() == b"ttf bytes"
    marker = json.loads(project.kanit_marker.read_text(encoding="utf-8"))
    assert marker["files"] == fonts.KANIT_SHA256
    assert item(run_checks(empty_root, fake_probes()), "font_kanit").status == "ok"


def test_a_kanit_file_with_another_sha256_is_removed_and_setup_fails(empty_root, capsys):
    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), fetch=FakeFetch(wrong="OFL.txt"))

    project = ProjectPaths(empty_root)
    assert exit_code == 1
    assert not (project.kanit_dir / "OFL.txt").exists()
    assert not project.kanit_marker.exists()
    assert "ล้มที่ขั้น โหลด Kanit: sha256 ของ OFL.txt ไม่ตรง" in capsys.readouterr().out


def test_kanit_already_there_is_not_fetched_again(fake_root):
    fetch = FakeFetch()

    exit_code = run_with_fakes(fake_root, FakeDownload(fake_root), fetch=fetch)

    assert exit_code == 0
    assert fetch.urls == []


DRUMS_URL = "https://raw.githubusercontent.com/sfzinstruments/karoryfer.big-rusty-drums/f07ce00df34a46b6b08375be56fe116cf15782bc/Samples/"


def test_setup_fetches_the_drum_samples_after_kanit_and_writes_their_marker(empty_root):
    fetch = FakeFetch()

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), fetch=fetch)

    assert exit_code == 0
    assert fetch.urls[2:] == [DRUMS_URL + path for path in DRUM_BYTES]
    project = ProjectPaths(empty_root)
    assert (project.drum_samples_dir / "kick_24/kick/kick/k_kick_vl14_rr4.flac").read_bytes() == b"kick"
    marker = json.loads(project.drum_kit_marker.read_text(encoding="utf-8"))
    assert marker["files"] == {s.path: s.sha256 for s in drum_kit.SAMPLES}
    assert item(run_checks(empty_root, fake_probes()), "drum_kit").status == "ok"


def test_a_drum_sample_that_fails_twice_is_tried_a_third_time(empty_root):
    fetch = FakeFetch(fail="sn_center_vl1_rr1.flac", times=2)

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), fetch=fetch)

    assert exit_code == 0
    assert fetch.urls.count(DRUMS_URL + "snare_14/center/top/sn_center_vl1_rr1.flac") == 3


def test_a_drum_sample_that_fails_three_times_ends_setup_naming_it_without_a_marker(empty_root, capsys):
    fetch = FakeFetch(wrong="k_kick_vl14_rr4.flac")

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), fetch=fetch)

    project = ProjectPaths(empty_root)
    assert exit_code == 1
    assert fetch.urls.count(DRUMS_URL + "kick_24/kick/kick/k_kick_vl14_rr4.flac") == 3
    assert not project.drum_kit_marker.exists()
    assert not (project.drum_samples_dir / "kick_24/kick/kick/k_kick_vl14_rr4.flac").exists()
    assert "kick_24/kick/kick/k_kick_vl14_rr4.flac" in capsys.readouterr().out


def test_only_drum_samples_missing_or_changed_are_fetched_again(empty_root):
    run_with_fakes(empty_root, FakeDownload(empty_root))
    project = ProjectPaths(empty_root)
    (project.drum_samples_dir / "kick_24/kick/kick/k_kick_vl14_rr4.flac").write_bytes(b"changed")
    project.drum_kit_marker.unlink()
    fetch = FakeFetch()

    exit_code = run_with_fakes(empty_root, FakeDownload(empty_root), fetch=fetch)

    assert exit_code == 0
    assert fetch.urls == [DRUMS_URL + "kick_24/kick/kick/k_kick_vl14_rr4.flac"]


def test_setup_downloads_klein_without_its_bf16_transformer_and_writes_both_markers(empty_root):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download)

    assert exit_code == 0
    assert download.patterns["black-forest-labs/FLUX.2-klein-4B"] == [
        "model_index.json",
        "text_encoder/*",
        "tokenizer/*",
        "vae/*",
        "scheduler/*",
        "transformer/config.json",
    ]
    assert download.patterns["unsloth/FLUX.2-klein-4B-GGUF"] == ["flux-2-klein-4b-Q4_K_M.gguf"]
    result = run_checks(empty_root, fake_probes())
    assert item(result, "model_klein").status == item(result, "model_klein_gguf").status == "ok"


def test_a_klein_folder_left_empty_by_the_download_fails_setup_without_a_marker(empty_root, capsys):
    download = FakeDownload(empty_root, leave_empty="text_encoder")

    exit_code = run_with_fakes(empty_root, download)

    assert exit_code == 1
    assert not ProjectPaths(empty_root).marker(KLEIN).exists()
    out = capsys.readouterr().out
    assert "ล้มที่ขั้น โหลด black-forest-labs/FLUX.2-klein-4B" in out
    assert "text_encoder/*" in out
    assert "unsloth/FLUX.2-klein-4B-GGUF" not in download.calls


def test_a_rerun_after_an_empty_klein_folder_downloads_klein_again(empty_root):
    run_with_fakes(empty_root, FakeDownload(empty_root, leave_empty="vae"))
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download)

    assert exit_code == 0
    assert download.calls == ["black-forest-labs/FLUX.2-klein-4B", "unsloth/FLUX.2-klein-4B-GGUF", *ONNX_REPOS]
    assert ProjectPaths(empty_root).marker(KLEIN_GGUF).is_file()


# --- the แกะเพลง tab's ONNX models (drum-notes D7, D20) ---


def test_setup_downloads_the_onnx_models_after_the_drum_kit_opens_each_file_once_and_writes_their_markers(empty_root):
    download, fetch, open_session = FakeDownload(empty_root), FakeFetch(), FakeOpenSession()
    project = ProjectPaths(empty_root)

    exit_code = run_with_fakes(empty_root, download, fetch=fetch, open_session=open_session)

    assert exit_code == 0
    assert download.calls[-3:] == ONNX_REPOS
    assert fetch.urls  # the drum kit came first: setup fetched it before the ONNX models' turn
    assert download.patterns["Andremi/audioweb-models"] == ["analysis/basic_pitch_nmp.onnx"]
    assert open_session.opened == [
        project.snapshot_dir(ADTOF, ADTOF.revision) / "adtof_frame_rnn.onnx",
        project.snapshot_dir(BEAT_THIS, BEAT_THIS.revision) / "beat_this.onnx",
        project.snapshot_dir(BASIC_PITCH, BASIC_PITCH.revision) / "analysis/basic_pitch_nmp.onnx",
    ]
    result = run_checks(empty_root, fake_probes())
    assert [item(result, m.check_id).status for m in ONNX_MODELS] == ["ok"] * 3


def test_an_onnx_file_no_session_opens_ends_setup_naming_it_without_a_marker(empty_root, capsys):
    download = FakeDownload(empty_root)

    exit_code = run_with_fakes(empty_root, download, open_session=FakeOpenSession(broken="beat_this.onnx"))

    project = ProjectPaths(empty_root)
    assert exit_code == 1
    assert project.marker(ADTOF).is_file()
    assert not project.marker(BEAT_THIS).exists()
    assert "Andremi/audioweb-models" not in download.calls
    out = capsys.readouterr().out
    assert "ล้มที่ขั้น โหลด thebluescreen/beat-this-onnx" in out
    assert "beat_this.onnx" in out


def test_onnx_models_already_ok_are_neither_downloaded_nor_opened_again(fake_root):
    download, open_session = FakeDownload(fake_root), FakeOpenSession()

    exit_code = run_with_fakes(fake_root, download, open_session=open_session)

    assert exit_code == 0
    assert download.calls == []
    assert open_session.opened == []
