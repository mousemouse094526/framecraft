"""The Status check rows a job's gate checks, as id → (label, check), named once so
every gate reads the checklist the same way (ADR 0009, spoil-maker spec › Status check).
Each check looks its probe up when it runs, so a test's fake probe is the one it calls."""

from backend import checks
from backend.errors import Row
from backend.models import QWEN
from backend.paths import ProjectPaths

FFMPEG: dict[str, Row] = {"ffmpeg": ("ffmpeg", lambda: checks.check_ffmpeg(checks.probe_ffmpeg))}
# `device` is a warning on `cpu`, which doesn't pass a gate (ADR 0006).
DEVICE: dict[str, Row] = {"device": ("Device", lambda: checks.check_device(checks.probe_device))}
PYTHAINLP: dict[str, Row] = {
    "pythainlp": ("pythainlp", lambda: checks.check_pinned(checks.probe_pythainlp, checks.PYTHAINLP_VERSION))
}


def qwen_model(project: ProjectPaths) -> dict[str, Row]:
    """Qwen's files, which its tokenizer reads too. Off a Mac never ok (spoil-maker D50)."""
    return {QWEN.check_id: (QWEN.label, lambda: checks.check_model_on_platform(project, QWEN, checks.this_platform()))}


def qwen_jobs(project: ProjectPaths) -> dict[str, Row]:
    """What a Describe job and a Draft job need: both run Qwen in mlx-vlm."""
    mlx_vlm: dict[str, Row] = {
        "mlx_vlm": ("mlx-vlm", lambda: checks.check_mlx_vlm(checks.probe_mlx_vlm, checks.this_platform()))
    }
    return FFMPEG | DEVICE | qwen_model(project) | mlx_vlm
