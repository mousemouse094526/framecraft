import sys

from backend.checks import DeviceProbe, run_checks
from backend.models import OMNIVOICE
from backend.paths import ProjectPaths

from .fakes import (
    broken_deno,
    broken_ffmpeg,
    fake_probes,
    item,
    write_marker,
)


def checks_with_fakes(root, sys_platform=None, **probe_overrides):
    """run_checks with every probe faked as passing on a CUDA machine, unless overridden."""
    return run_checks(root, fake_probes(**probe_overrides), sys_platform)


def test_complete_root_with_cuda_is_ready_with_eleven_ok(fake_root):
    result = checks_with_fakes(fake_root)

    assert result.ready is True
    assert result.ok_count == 11
    assert result.total == 11


def test_cpu_only_device_is_a_warning_but_still_ready(fake_root):
    result = checks_with_fakes(fake_root, device=lambda: "cpu")

    assert result.ok_count == 10
    assert result.warning_count == 1
    assert item(result, "device").status == "warning"
    assert result.ready is True


def test_missing_omnivoice_marker_makes_it_missing_and_not_ready(fake_root):
    ProjectPaths(fake_root).marker(OMNIVOICE).unlink()

    result = checks_with_fakes(fake_root)

    assert item(result, "model_omnivoice").status == "missing"
    assert result.ready is False


def test_marker_with_a_deleted_file_makes_model_missing(fake_root):
    snapshot = ProjectPaths(fake_root).snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
    (snapshot / "model.safetensors").unlink()

    result = checks_with_fakes(fake_root)

    assert item(result, "model_omnivoice").status == "missing"
    assert "model.safetensors" in item(result, "model_omnivoice").detail


def test_marker_with_a_wrong_file_size_makes_model_missing(fake_root):
    snapshot = ProjectPaths(fake_root).snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
    (snapshot / "config.json").write_bytes(b"short")

    result = checks_with_fakes(fake_root)

    assert item(result, "model_omnivoice").status == "missing"


def test_marker_with_another_revision_makes_model_missing(fake_root):
    write_marker(fake_root, OMNIVOICE, revision="0" * 40)

    result = checks_with_fakes(fake_root)

    assert item(result, "model_omnivoice").status == "missing"


def test_ffmpeg_probe_that_raises_makes_only_ffmpeg_missing(fake_root):
    result = checks_with_fakes(fake_root, ffmpeg=broken_ffmpeg)

    assert item(result, "ffmpeg").status == "missing"
    assert item(result, "ffmpeg").detail == "ffmpeg -version exited with 1"
    assert len(result.items) == 11


def test_yt_dlp_and_deno_rows_follow_ffmpeg_with_their_versions(fake_root):
    result = checks_with_fakes(fake_root)

    ids = [i.id for i in result.items]
    assert ids[ids.index("ffmpeg") + 1 : ids.index("ffmpeg") + 3] == ["yt_dlp", "deno"]
    assert item(result, "yt_dlp").status == "ok"
    assert item(result, "yt_dlp").detail == "2026.10.26"
    assert item(result, "deno").status == "ok"
    assert item(result, "deno").detail == "2.9.8"


def test_missing_yt_dlp_makes_only_yt_dlp_missing(fake_root):
    def not_installed():
        raise RuntimeError("ยังไม่ได้ติดตั้ง")

    result = checks_with_fakes(fake_root, yt_dlp=not_installed)

    assert (item(result, "yt_dlp").status, item(result, "yt_dlp").detail) == ("missing", "ยังไม่ได้ติดตั้ง")
    assert result.missing_count == 1


def test_deno_probe_that_raises_makes_only_deno_missing(fake_root):
    result = checks_with_fakes(fake_root, deno=broken_deno)

    assert item(result, "deno").status == "missing"
    assert item(result, "deno").fix == "./setup.sh"
    assert len(result.items) == 11
    assert result.missing_count == 1


def test_cpu_device_is_not_cached_but_cuda_is(fake_root):
    answers = iter(["cpu", "cuda", "cpu"])
    probe = DeviceProbe(detect=lambda: next(answers))

    first = checks_with_fakes(fake_root, device=probe)
    second = checks_with_fakes(fake_root, device=probe)
    third = checks_with_fakes(fake_root, device=probe)

    assert item(first, "device").detail == "cpu"
    assert item(second, "device").detail == "cuda"
    assert item(third, "device").detail == "cuda"


def test_only_model_rows_carry_a_license(fake_root):
    result = checks_with_fakes(fake_root)

    omnivoice = item(result, "model_omnivoice").license
    assert omnivoice.name == "CC BY-NC 4.0"
    assert omnivoice.url == "https://creativecommons.org/licenses/by-nc/4.0/"
    assert omnivoice.author == "k2-fsa"
    assert omnivoice.model_url == "https://huggingface.co/k2-fsa/OmniVoice"
    assert item(result, "model_whisper").license.name == "MIT"
    others = [i for i in result.items if not i.id.startswith("model_")]
    assert all(i.license is None for i in others)


def test_items_come_in_the_spec_order(fake_root):
    result = checks_with_fakes(fake_root)

    assert [i.id for i in result.items] == [
        "python",
        "torch",
        "transformers",
        "omnivoice",
        "fastapi",
        "ffmpeg",
        "yt_dlp",
        "deno",
        "model_omnivoice",
        "model_whisper",
        "device",
    ]


def test_corrupt_marker_makes_model_missing(fake_root):
    ProjectPaths(fake_root).marker(OMNIVOICE).write_text("{not json", encoding="utf-8")

    result = checks_with_fakes(fake_root)

    assert item(result, "model_omnivoice").status == "missing"
    assert item(result, "model_omnivoice").detail.startswith("marker เสีย")


def test_rows_on_windows_tell_the_user_to_run_setup_cmd(fake_root):
    # `fix` is only set on rows that aren't ok, so break a model, ffmpeg, deno and the GPU.
    ProjectPaths(fake_root).marker(OMNIVOICE).unlink()

    result = checks_with_fakes(
        fake_root,
        device=lambda: "cpu",
        ffmpeg=broken_ffmpeg,
        deno=broken_deno,
        sys_platform="win32",
    )

    assert item(result, "model_omnivoice").fix == "setup.cmd"
    assert item(result, "model_omnivoice").fix_kind == "command"
    assert item(result, "ffmpeg").fix == "setup.cmd"
    assert item(result, "deno").fix == "setup.cmd"
    assert item(result, "device").fix == "ติดตั้ง NVIDIA driver แล้วปิดและเปิด npm run dev ใหม่"
    assert item(result, "device").fix_kind == "hint"


def test_rows_on_mac_tell_the_user_to_run_setup_sh(fake_root):
    ProjectPaths(fake_root).marker(OMNIVOICE).unlink()

    result = checks_with_fakes(
        fake_root,
        device=lambda: "cpu",
        ffmpeg=broken_ffmpeg,
        deno=broken_deno,
        sys_platform="darwin",
    )

    assert item(result, "model_omnivoice").fix == "./setup.sh"
    assert item(result, "ffmpeg").fix == "./setup.sh"
    assert item(result, "deno").fix == "./setup.sh"
    assert item(result, "device").fix == "ต้องเป็น Mac Apple Silicon"


def test_ok_rows_have_no_fix_kind(fake_root):
    result = checks_with_fakes(fake_root)

    assert {(i.fix, i.fix_kind) for i in result.items} == {(None, None)}


def test_python_outside_the_venv_is_a_warning_that_says_so(fake_root, monkeypatch):
    monkeypatch.setattr(sys, "prefix", "/usr/local")

    result = checks_with_fakes(fake_root)

    python = item(result, "python")
    assert python.status == "warning"
    assert "ไม่ใช่ .venv ของ project" in python.detail
    assert (python.fix, python.fix_kind) == ("รัน backend ด้วย npm run dev", "hint")


def test_wrong_python_inside_the_venv_says_the_version_not_the_venv(fake_root, monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 13, 1, "final", 0))

    result = checks_with_fakes(fake_root)

    python = item(result, "python")
    assert python.status == "warning"
    assert python.detail == "Python 3.13.1 ใน .venv ต้องเป็น 3.12"
    assert python.fix_kind == "hint"
