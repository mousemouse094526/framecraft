"""The Status check rows a job's gate checks, as id → (label, check), named once so
every gate reads the checklist the same way (ADR 0009, spoil-maker spec › Status check).
Each check looks its probe and the OS up when it runs, so a test's fakes are the ones it calls."""

from backend import checks
from backend.errors import Row
from backend.paths import ProjectPaths

FFMPEG: dict[str, Row] = {"ffmpeg": ("ffmpeg", lambda: checks.check_ffmpeg(checks.probe_ffmpeg))}
# `device` is a warning on `cpu`, which doesn't pass a gate (ADR 0006); on Windows it is
# missing on a card torch has no kernels for, so it gates every GPU job (windows-launch D8).
DEVICE: dict[str, Row] = {
    "device": (
        "Device",
        lambda: checks.device_check(checks.probe_device, checks.this_platform(), checks.probe_gpu)(),
    )
}
PYTHAINLP: dict[str, Row] = {
    "pythainlp": ("pythainlp", lambda: checks.check_pinned(checks.probe_pythainlp, checks.PYTHAINLP_VERSION))
}


def _qwen_rows(project: ProjectPaths) -> dict[str, Row]:
    """Qwen's rows on the OS this runs on, reading the card once (`checks.qwen_checks`)."""
    probes = checks.real_probes()
    sys_platform = checks.this_platform()
    gpu = checks.read_once(probes.gpu)
    return {"device": ("Device", checks.device_check(probes.device, sys_platform, gpu))} | dict(
        checks.qwen_checks(project, probes, sys_platform, gpu)
    )


def qwen_model(project: ProjectPaths) -> dict[str, Row]:
    """Qwen's files on this OS, which its tokenizer reads too. On Windows the gpu row
    first: setup never downloads them on a card under Qwen's target (windows-launch D9),
    so the refusal names the card, not the files."""
    rows = _qwen_rows(project)
    return {row_id: rows[row_id] for row_id in ("gpu", "model_qwen") if row_id in rows}


def qwen_jobs(project: ProjectPaths) -> dict[str, Row]:
    """What a Describe job and a Draft job need: ffmpeg, the device, and Qwen's rows on
    this OS — gpu, its model and bitsandbytes on Windows; its model and mlx-vlm on a Mac."""
    return FFMPEG | _qwen_rows(project)
