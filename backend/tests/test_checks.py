import dataclasses
import subprocess
import sys

import pytest

from backend import checks
from backend.checks import DeviceProbe, run_checks
from backend.models import KLEIN, KLEIN_GGUF, OMNIVOICE, QWEN_MAC, QWEN_WINDOWS
from backend.paths import ProjectPaths

from .fakes import (
    broken_deno,
    broken_ffmpeg,
    broken_gpu,
    fake_probes,
    card,
    item,
    write_marker,
)


def checks_with_fakes(root, sys_platform=None, **probe_overrides):
    """run_checks with every probe faked as passing on a CUDA machine, unless overridden."""
    return run_checks(root, fake_probes(**probe_overrides), sys_platform)


def test_a_complete_root_on_a_mac_is_ready_with_nineteen_ok(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="darwin")

    assert result.ready is True
    assert result.ok_count == 19
    assert result.total == 19


def test_cpu_only_device_is_a_warning_but_still_ready(fake_root):
    result = checks_with_fakes(fake_root, device=lambda: "cpu")

    assert result.ok_count == 18
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
    assert len(result.items) == 19


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
    assert len(result.items) == 19
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
        "model_qwen",
        "mlx_vlm",
        "pythainlp",
        "font_kanit",
        "model_klein",
        "model_klein_gguf",
        "diffusers",
        "gguf",
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


def test_qwen_and_mlx_vlm_rows_are_ok_on_a_mac(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="darwin")

    assert item(result, "model_qwen").status == "ok"
    assert item(result, "model_qwen").license.name == "Apache-2.0"
    assert item(result, "mlx_vlm").status == "ok"
    assert item(result, "mlx_vlm").detail == "0.7.11"


QWEN_TARGET = "Qwen ต้องใช้การ์ด NVIDIA RTX 30xx ขึ้นไปที่มี VRAM อย่างน้อย 8 GB"
GPU_ROWS = ("gpu", "model_qwen", "bitsandbytes")


def ids(result) -> list[str]:
    return [i.id for i in result.items]


def test_an_rtx_3060_with_everything_installed_is_ok_on_windows(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card(gib=12, capability=(8, 6)))

    for row in ("device", *GPU_ROWS):
        assert item(result, row).status == "ok"
    assert "mlx_vlm" not in ids(result)
    assert result.ok_count == result.total == 20


def test_windows_rows_sit_where_mlx_vlm_was_with_gpu_right_after_device(fake_root):
    mac = ids(checks_with_fakes(fake_root, sys_platform="darwin"))
    windows = ids(checks_with_fakes(fake_root, sys_platform="win32"))

    expected = mac.copy()
    expected[expected.index("mlx_vlm")] = "bitsandbytes"
    expected.insert(expected.index("device") + 1, "gpu")
    assert windows == expected


def test_the_gpu_row_shows_the_card_its_memory_and_its_capability(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card(gib=12, capability=(8, 6)))

    row = item(result, "gpu")
    assert (row.label, row.detail) == ("GPU", "NVIDIA GeForce RTX 3060 · 12 GB · sm_86")


def test_an_rtx_40xx_is_ok_though_torch_has_no_sm_89_kernels(fake_root):
    # sm_8x kernels run on every 8.x card, the rule torch's own check uses (windows-launch D13).
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card("NVIDIA GeForce RTX 4070", 12, (8, 9)))

    assert item(result, "device").status == "ok"
    assert item(result, "gpu").status == "ok"


def test_an_rtx_20xx_warns_on_every_qwen_row_but_stays_ready(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card("NVIDIA GeForce RTX 2070", 8, (7, 5)))

    for row in GPU_ROWS:
        assert (item(result, row).status, item(result, row).fix, item(result, row).fix_kind) == (
            "warning",
            QWEN_TARGET,
            "hint",
        )
    assert item(result, "device").status == "ok"
    assert result.ready is True


def test_qwen_rows_under_the_target_still_show_their_own_value(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card("NVIDIA GeForce RTX 2070", 8, (7, 5)))

    assert item(result, "model_qwen").detail.startswith(f"{QWEN_WINDOWS.revision[:7]} · ")
    assert item(result, "bitsandbytes").detail == "0.50.2"


def test_qwen_not_downloaded_under_the_target_warns_with_the_missing_detail(fake_root):
    ProjectPaths(fake_root).marker(QWEN_WINDOWS).unlink()

    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card("NVIDIA GeForce RTX 2070", 8, (7, 5)))

    row = item(result, "model_qwen")
    assert (row.status, row.detail, row.fix) == ("warning", "ไม่พบ marker ใน models/.setup", QWEN_TARGET)


def test_bitsandbytes_not_installed_under_the_target_warns_and_stays_ready(fake_root):
    def not_installed() -> str:
        raise RuntimeError("ยังไม่ได้ติดตั้ง")

    result = checks_with_fakes(
        fake_root, sys_platform="win32", gpu=card("NVIDIA GeForce RTX 2070", 8, (7, 5)), bitsandbytes=not_installed
    )

    row = item(result, "bitsandbytes")
    assert (row.status, row.detail, row.fix) == ("warning", "ยังไม่ได้ติดตั้ง", QWEN_TARGET)
    assert result.ready is True


def test_a_6_gb_card_warns_on_the_gpu_row(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card(gib=6, capability=(8, 6)))

    assert item(result, "gpu").status == "warning"
    assert item(result, "gpu").fix == QWEN_TARGET


def test_an_8_gb_card_reporting_just_under_8_gib_is_ok(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card(gib=7.6, capability=(8, 6)))

    assert (item(result, "gpu").status, item(result, "gpu").detail) == ("ok", "NVIDIA GeForce RTX 3060 · 8 GB · sm_86")


def test_a_pascal_card_makes_device_missing_with_the_reason(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=card("NVIDIA GeForce GTX 1050 Ti", 4, (6, 1)))

    device = item(result, "device")
    assert (device.status, device.detail, device.fix, device.fix_kind) == (
        "missing",
        "NVIDIA GeForce GTX 1050 Ti · sm_61",
        "การ์ด NVIDIA GeForce GTX 1050 Ti (sm_61) เก่าเกินสำหรับ torch ที่ติดตั้ง",
        "hint",
    )
    assert result.ready is False


def test_an_unreadable_card_warns_about_the_driver_not_the_card(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32", gpu=broken_gpu)

    row = item(result, "gpu")
    assert (row.status, row.detail, row.fix, row.fix_kind) == (
        "warning",
        "",
        "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA",
        "hint",
    )
    assert item(result, "model_qwen").fix == "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA"
    assert item(result, "device").status == "ok"


def test_with_only_the_mlx_model_on_disk_qwen_is_missing_on_windows(fake_root):
    ProjectPaths(fake_root).marker(QWEN_WINDOWS).unlink()

    result = checks_with_fakes(fake_root, sys_platform="win32")

    row = item(result, "model_qwen")
    assert (row.status, row.fix, row.fix_kind) == ("missing", "setup.cmd", "command")
    assert row.license.model_url == "https://huggingface.co/Qwen/Qwen3.5-9B"


def test_the_qwen_row_on_windows_shows_the_windows_revision(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32")

    assert item(result, "model_qwen").detail.startswith("c202236 · ")


def test_bitsandbytes_not_installed_is_missing_with_the_setup_command(fake_root):
    def not_installed() -> str:
        raise RuntimeError("ยังไม่ได้ติดตั้ง")

    result = checks_with_fakes(fake_root, sys_platform="win32", bitsandbytes=not_installed)

    row = item(result, "bitsandbytes")
    assert (row.status, row.fix) == ("missing", "setup.cmd")


def test_a_mac_has_no_gpu_or_bitsandbytes_row_and_never_reads_the_card(fake_root):
    def must_not_run():
        raise AssertionError("the gpu probe ran on a Mac")

    result = checks_with_fakes(fake_root, sys_platform="darwin", gpu=must_not_run, bitsandbytes=must_not_run)

    assert {"gpu", "bitsandbytes"} & set(ids(result)) == set()
    assert result.ok_count == result.total == 19


def test_the_qwen_row_on_a_mac_still_checks_the_mlx_model(fake_root):
    ProjectPaths(fake_root).marker(QWEN_WINDOWS).unlink()

    result = checks_with_fakes(fake_root, sys_platform="darwin")

    assert item(result, "model_qwen").status == "ok"
    assert item(result, "model_qwen").detail.startswith("938d891 · ")


def test_the_card_is_read_once_per_status_check(fake_root):
    calls = []
    read = card()

    def counting():
        calls.append(1)
        return read()

    checks_with_fakes(fake_root, sys_platform="win32", gpu=counting)

    assert len(calls) == 1


# The probe itself, through its `run` seam: the only proof it reads the card with
# nvidia-smi, never torch, so the backend makes no CUDA context (windows-launch D12).
def test_the_gpu_probe_asks_nvidia_smi_for_card_0_and_torch_for_its_arch_list():
    runs = []

    def fake_run(argv, **kwargs):
        runs.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, stdout="NVIDIA GeForce RTX 3060, 12288, 8.6\n", stderr="")

    info = checks.probe_gpu(fake_run, lambda: ("sm_80", "sm_86"))

    assert info == checks.GpuInfo("NVIDIA GeForce RTX 3060", 12288 * 2**20, (8, 6), ("sm_80", "sm_86"))
    argv, kwargs = runs[0]
    assert argv == [
        "nvidia-smi",
        "--query-gpu=name,memory.total,compute_cap",
        "--format=csv,noheader,nounits",
        "-i",
        "0",
    ]
    assert kwargs["timeout"] == 5


def test_a_failing_nvidia_smi_makes_the_gpu_probe_raise():
    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 9, stdout="", stderr="Field \"compute_cap\" is not a valid field")

    with pytest.raises(RuntimeError):
        checks.probe_gpu(fake_run, lambda: ())


def test_missing_qwen_marker_makes_only_qwen_missing(fake_root):
    ProjectPaths(fake_root).marker(QWEN_MAC).unlink()

    result = checks_with_fakes(fake_root, sys_platform="darwin")

    assert item(result, "model_qwen").status == "missing"
    assert result.missing_count == 1


def test_another_mlx_vlm_version_makes_mlx_vlm_missing(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="darwin", mlx_vlm=lambda: "0.8.0")

    assert item(result, "mlx_vlm").status == "missing"
    assert item(result, "mlx_vlm").detail == "version ไม่ตรง: ติดตั้งไว้ 0.8.0 ต้องการ 0.7.11"


def test_pythainlp_row_is_ok_at_the_pinned_version_on_windows_too(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32")

    assert (item(result, "pythainlp").status, item(result, "pythainlp").detail) == ("ok", "5.4.0")


def test_another_pythainlp_version_makes_pythainlp_missing(fake_root):
    result = checks_with_fakes(fake_root, pythainlp=lambda: "5.3.0")

    assert item(result, "pythainlp").status == "missing"
    assert item(result, "pythainlp").detail == "version ไม่ตรง: ติดตั้งไว้ 5.3.0 ต้องการ 5.4.0"
    assert item(result, "pythainlp").fix == "./setup.sh"


def test_kanit_row_is_ok_when_both_files_and_their_marker_are_there(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32")

    assert (item(result, "font_kanit").status, item(result, "font_kanit").label) == ("ok", "Kanit font")


def test_a_missing_kanit_file_makes_only_kanit_missing(fake_root):
    (ProjectPaths(fake_root).kanit_dir / "OFL.txt").unlink()

    result = checks_with_fakes(fake_root)

    assert item(result, "font_kanit").status == "missing"
    assert item(result, "font_kanit").detail == "ไฟล์หาย: OFL.txt"
    assert result.missing_count == 1


def test_a_kanit_marker_with_another_sha256_makes_kanit_missing(fake_root):
    marker = ProjectPaths(fake_root).kanit_marker
    marker.write_text(marker.read_text(encoding="utf-8").replace("5dec", "0000"), encoding="utf-8")

    result = checks_with_fakes(fake_root)

    assert item(result, "font_kanit").status == "missing"
    assert item(result, "font_kanit").fix == "./setup.sh"


def test_klein_rows_are_ok_on_windows_too_and_carry_each_repo_s_license(fake_root):
    result = checks_with_fakes(fake_root, sys_platform="win32")

    klein, gguf = item(result, "model_klein"), item(result, "model_klein_gguf")
    assert (klein.status, klein.label, klein.license.author) == ("ok", "FLUX.2 klein 4B model", "Black Forest Labs")
    assert (gguf.status, gguf.label, gguf.license.author) == ("ok", "FLUX.2 klein 4B GGUF", "Unsloth")
    assert klein.license.name == gguf.license.name == "Apache-2.0"
    assert gguf.license.model_url == "https://huggingface.co/unsloth/FLUX.2-klein-4B-GGUF"


@pytest.mark.parametrize("model", [KLEIN, KLEIN_GGUF])
def test_a_missing_klein_marker_makes_only_its_row_missing(fake_root, model):
    ProjectPaths(fake_root).marker(model).unlink()

    result = checks_with_fakes(fake_root)

    assert item(result, model.check_id).status == "missing"
    assert result.missing_count == 1


def test_diffusers_and_gguf_rows_show_their_pinned_versions(fake_root):
    result = checks_with_fakes(fake_root)

    assert (item(result, "diffusers").status, item(result, "diffusers").detail) == ("ok", "0.42.1")
    assert (item(result, "gguf").status, item(result, "gguf").detail) == ("ok", "0.19.0")


def test_another_diffusers_version_makes_diffusers_missing(fake_root):
    result = checks_with_fakes(fake_root, diffusers=lambda: "0.43.0")

    assert item(result, "diffusers").status == "missing"
    assert item(result, "diffusers").detail == "version ไม่ตรง: ติดตั้งไว้ 0.43.0 ต้องการ 0.42.1"
    assert result.missing_count == 1


def test_gguf_not_installed_makes_gguf_missing_with_the_setup_command(fake_root):
    def not_installed() -> str:
        raise RuntimeError("ยังไม่ได้ติดตั้ง")

    result = checks_with_fakes(fake_root, gguf=not_installed)

    assert (item(result, "gguf").status, item(result, "gguf").detail) == ("missing", "ยังไม่ได้ติดตั้ง")
    assert item(result, "gguf").fix == "./setup.sh"


def test_a_gguf_marker_of_the_q8_0_file_makes_the_gguf_row_missing(fake_root):
    """D51 moved to Q4_K_M in the same pinned revision: a machine that downloaded Q8_0
    downloads again."""
    q8 = dataclasses.replace(KLEIN_GGUF, allow_patterns=("flux-2-klein-4b-Q8_0.gguf",))
    write_marker(fake_root, q8)

    result = checks_with_fakes(fake_root)

    row = item(result, "model_klein_gguf")
    assert (row.status, row.detail) == ("missing", "ไม่มีไฟล์ flux-2-klein-4b-Q4_K_M.gguf ใน marker")
    assert result.missing_count == 1
