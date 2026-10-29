"""The Status check: the Checklist items shared by setup and the API.

Never imports `omnivoice` or `transformers` and never uses the network.
Packages are checked through their installed metadata only.
"""

import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import paths
from backend.models import MODELS, ModelSpec
from backend.paths import ProjectPaths

ItemStatus = Literal["ok", "missing", "warning"]

FFMPEG_TIMEOUT_SECONDS = 5
DENO_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class FixTexts:
    """What a Checklist item's `fix` tells the user to do, per OS.

    `setup` is the setup command; `device` is the advice when only `cpu` works.
    """

    setup: str
    device: str


def _fix_texts(sys_platform: str) -> FixTexts:
    if sys_platform == "win32":
        return FixTexts(
            setup="setup.cmd",
            device="ติดตั้ง NVIDIA driver แล้วปิดและเปิด npm run dev ใหม่",
        )
    return FixTexts(setup="./setup.sh", device="ต้องเป็น Mac Apple Silicon")


class License(BaseModel):
    name: str
    url: str
    author: str
    model_url: str


class ChecklistItem(BaseModel):
    id: str
    label: str
    status: ItemStatus
    detail: str
    fix: str | None
    license: License | None = None


class StatusResponse(BaseModel):
    checked_at: str
    ready: bool
    ok_count: int
    warning_count: int
    missing_count: int
    total: int
    items: list[ChecklistItem]


@dataclass(frozen=True)
class FfmpegInfo:
    version: str
    source: str


class DeviceProbe:
    """Finds the torch device; caches `cuda` or `mps` for the whole process.

    A GPU torch has found stays usable while the process lives, so it is safe
    to cache. `cpu` and errors are not cached, so installing a driver and
    pressing Refresh shows the new device.
    """

    def __init__(self, detect: Callable[[], str]):
        self._detect = detect
        self._found: str | None = None

    def __call__(self) -> str:
        if self._found:
            return self._found
        device = self._detect()
        if device != "cpu":
            self._found = device
        return device


def detect_torch_device() -> str:
    import torch  # takes seconds, so not imported until a check needs it

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


probe_device = DeviceProbe(detect_torch_device)


def probe_ffmpeg() -> FfmpegInfo:
    """Runs `ffmpeg -version` from imageio-ffmpeg (ADR 0005); raises if it fails."""
    import imageio_ffmpeg

    exe = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [exe, "-version"],
        capture_output=True,
        text=True,
        timeout=FFMPEG_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg -version exited with {result.returncode}")
    # First line: "ffmpeg version 7.1 Copyright (c) ..."
    version = result.stdout.split()[2]
    return FfmpegInfo(version=version, source=_ffmpeg_source(exe))


def probe_yt_dlp() -> str:
    """The installed yt-dlp version; raises when it isn't installed."""
    try:
        return metadata.version("yt-dlp")
    except metadata.PackageNotFoundError:
        raise RuntimeError("ยังไม่ได้ติดตั้ง") from None


def probe_deno() -> str:
    """Runs `deno --version` from the `deno` wheel in the venv; raises if it fails.

    Not cached: Refresh after setup must see a newly installed Deno.
    """
    import deno

    exe = deno.find_deno_bin()  # raises FileNotFoundError when the wheel is missing
    result = subprocess.run(
        [exe, "--version"],
        capture_output=True,
        text=True,
        timeout=DENO_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(f"deno --version exited with {result.returncode}")
    # First line: "deno 2.9.8 (stable, release, aarch64-apple-darwin)"
    return result.stdout.split()[1]


def _ffmpeg_source(exe: str) -> str:
    # imageio-ffmpeg has no API for this; a system ffmpeg comes back as "ffmpeg".
    import imageio_ffmpeg

    if os.environ.get("IMAGEIO_FFMPEG_EXE"):
        return "IMAGEIO_FFMPEG_EXE"
    package_dir = Path(imageio_ffmpeg.__file__).resolve().parent
    if Path(exe).resolve().is_relative_to(package_dir):
        return "imageio-ffmpeg"
    return "system"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# A check returns (status, detail) or raises; a raise makes the item `missing`.
Check = Callable[[], tuple[ItemStatus, str]]


def run_checks(
    root: Path | None = None,
    device_probe: Callable[[], str] | None = None,
    ffmpeg_probe: Callable[[], FfmpegInfo] | None = None,
    sys_platform: str | None = None,
    deno_probe: Callable[[], str] | None = None,
    yt_dlp_probe: Callable[[], str] | None = None,
) -> StatusResponse:
    """Builds every Checklist item in spec order. Defaults are the real probes
    and the OS this process runs on.

    Defaults are looked up at call time, so tests can swap `paths.ROOT` and the
    module's probes.
    """
    project = ProjectPaths(root or paths.ROOT)
    device_probe = device_probe or probe_device
    ffmpeg_probe = ffmpeg_probe or probe_ffmpeg
    deno_probe = deno_probe or probe_deno
    yt_dlp_probe = yt_dlp_probe or probe_yt_dlp
    fixes = _fix_texts(sys_platform or sys.platform)

    items = [
        _item("python", "Python venv", lambda: _check_python(project), "รัน backend ด้วย npm run dev"),
        _item("torch", "torch", lambda: _check_package("torch"), fixes.setup),
        _item("transformers", "transformers", lambda: _check_package("transformers"), fixes.setup),
        _item("omnivoice", "omnivoice", lambda: _check_package("omnivoice"), fixes.setup),
        _item("fastapi", "fastapi", lambda: _check_package("fastapi"), fixes.setup),
        _item("ffmpeg", "ffmpeg", lambda: _check_ffmpeg(ffmpeg_probe), fixes.setup),
        # The spoil download gate calls these two probes too (spoil D9).
        _item("yt_dlp", "yt-dlp", lambda: ("ok", yt_dlp_probe()), fixes.setup),
        _item("deno", "Deno", lambda: ("ok", deno_probe()), fixes.setup),
        *(_model_item(project, model, fixes.setup) for model in MODELS),
        _item("device", "Device", lambda: _check_device(device_probe), fixes.device),
    ]
    counts = {s: sum(1 for i in items if i.status == s) for s in ("ok", "warning", "missing")}
    return StatusResponse(
        checked_at=now_iso(),
        ready=counts["missing"] == 0,
        ok_count=counts["ok"],
        warning_count=counts["warning"],
        missing_count=counts["missing"],
        total=len(items),
        items=items,
    )


def check_model(project: ProjectPaths, model: ModelSpec) -> tuple[ItemStatus, str]:
    """Whether a model's marker, revision, and files all match. Used by setup too."""
    marker_path = project.marker(model)
    if not marker_path.is_file():
        return "missing", "ไม่พบ marker ใน models/.setup"
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        revision, files = marker["revision"], marker["files"]
    except (ValueError, KeyError, TypeError) as error:
        return "missing", f"marker เสีย: {error}"
    if revision != model.revision:
        return "missing", (
            f"revision ไม่ตรง: โหลดไว้ {revision[:7]} ต้องการ {model.short_revision}"
        )
    snapshot = project.snapshot_dir(model, model.revision)
    for file in files:
        path = snapshot / file["path"]
        if not path.is_file():
            return "missing", f"ไฟล์หาย: {file['path']}"
        if path.stat().st_size != file["size"]:
            return "missing", f"ขนาดไฟล์ไม่ตรง: {file['path']}"
    size_gb = marker["size_bytes"] / 1e9
    return "ok", f"{model.short_revision} · {size_gb:.1f} GB"


def _item(
    item_id: str,
    label: str,
    check: Check,
    fix: str,
    license: License | None = None,
) -> ChecklistItem:
    try:
        status, detail = check()
    except Exception as error:  # one broken check must not hide the others
        status, detail = "missing", str(error) or type(error).__name__
    return ChecklistItem(
        id=item_id,
        label=label,
        status=status,
        detail=detail,
        fix=None if status == "ok" else fix,
        license=license,
    )


def _model_item(project: ProjectPaths, model: ModelSpec, fix: str) -> ChecklistItem:
    license = License(
        name=model.license,
        url=model.license_url,
        author=model.author,
        model_url=model.model_url,
    )
    return _item(
        model.check_id,
        model.label,
        lambda: check_model(project, model),
        fix,
        license,
    )


def _check_python(project: ProjectPaths) -> tuple[ItemStatus, str]:
    # Only a warning: the packages may still work, but the backend should run
    # from the project's .venv (`npm run dev` does that).
    version = ".".join(str(n) for n in sys.version_info[:3])
    in_venv = Path(sys.prefix).resolve() == project.venv_dir.resolve()
    if sys.version_info[:2] == (3, 12) and in_venv:
        return "ok", f"Python {version} ใน .venv"
    return "warning", f"Python {version} ที่ {sys.prefix} ไม่ใช่ .venv ของ project"


def _check_package(name: str) -> tuple[ItemStatus, str]:
    try:
        return "ok", metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing", "ยังไม่ได้ติดตั้ง"


def _check_ffmpeg(ffmpeg_probe: Callable[[], FfmpegInfo]) -> tuple[ItemStatus, str]:
    # A failing probe raises; _item turns that into `missing`.
    info = ffmpeg_probe()
    return "ok", f"{info.version} ({info.source})"


def _check_device(device_probe: Callable[[], str]) -> tuple[ItemStatus, str]:
    device = device_probe()
    return ("warning" if device == "cpu" else "ok"), device
