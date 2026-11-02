"""The Status check: the Checklist items shared by setup and the API.

Never imports `omnivoice` or `transformers` and never uses the network.
Packages are checked through their installed metadata only.
"""

import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel

from backend import paths
from backend.models import OMNIVOICE, QWEN, WHISPER, ModelSpec
from backend.paths import ProjectPaths

ItemStatus = Literal["ok", "missing", "warning"]
# "command" is copied and run as-is (the UI shows a copy chip); "hint" is a sentence.
FixKind = Literal["command", "hint"]

VERSION_TIMEOUT_SECONDS = 5
MLX_VLM_VERSION = "0.7.11"  # the pin in pyproject.toml (spoil-maker spec › Dependencies)
PYTHAINLP_VERSION = "5.4.0"  # the pin in pyproject.toml (spoil-maker spec › Dependencies)


@dataclass(frozen=True)
class Fix:
    text: str
    kind: FixKind


@dataclass(frozen=True)
class FixTexts:
    """What a Checklist item's `fix` tells the user to do, per OS.

    `setup` is the setup command; `device` is the advice when only `cpu` works.
    """

    setup: Fix
    device: Fix


RUN_BACKEND_FIX = Fix("รัน backend ด้วย npm run dev", "hint")
MAC_ONLY_FIX = Fix("ใช้ได้บน Mac เท่านั้น", "hint")
# Only Mac and Windows are supported (ADR 0006), so "not here" means Windows.
UNSUPPORTED_HERE = "ยังไม่รองรับบน Windows"


def _fix_texts(sys_platform: str) -> FixTexts:
    if sys_platform == "win32":
        return FixTexts(
            setup=Fix("setup.cmd", "command"),
            device=Fix("ติดตั้ง NVIDIA driver แล้วปิดและเปิด npm run dev ใหม่", "hint"),
        )
    return FixTexts(
        setup=Fix("./setup.sh", "command"),
        device=Fix("ต้องเป็น Mac Apple Silicon", "hint"),
    )


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
    fix_kind: FixKind | None
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


def _version_output(name: str, exe: str, flag: str) -> str:
    """Runs `{exe} {flag}` and returns its stdout; raises naming `name` if it fails."""
    result = subprocess.run(
        [exe, flag],
        capture_output=True,
        text=True,
        timeout=VERSION_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{name} {flag} exited with {result.returncode}")
    return result.stdout


def probe_ffmpeg() -> FfmpegInfo:
    """Runs `ffmpeg -version` from imageio-ffmpeg (ADR 0005); raises if it fails."""
    import imageio_ffmpeg

    exe = imageio_ffmpeg.get_ffmpeg_exe()
    # First line: "ffmpeg version 7.1 Copyright (c) ..."
    version = _version_output("ffmpeg", exe, "-version").split()[2]
    return FfmpegInfo(version=version, source=_ffmpeg_source(exe))


def probe_yt_dlp() -> str:
    """The installed yt-dlp version; raises when it isn't installed."""
    try:
        return metadata.version("yt-dlp")
    except metadata.PackageNotFoundError:
        raise RuntimeError("ยังไม่ได้ติดตั้ง") from None


def probe_mlx_vlm() -> str:
    """The installed mlx-vlm version, from its metadata only: importing mlx_vlm loads
    transformers, which the Status check never does. Raises when it isn't installed."""
    try:
        version = metadata.version("mlx-vlm")
    except metadata.PackageNotFoundError:
        raise RuntimeError("ยังไม่ได้ติดตั้ง") from None
    if importlib.util.find_spec("mlx_vlm") is None:
        raise RuntimeError("ยังไม่ได้ติดตั้ง")
    return version


def probe_pythainlp() -> str:
    """The installed pythainlp version, from its metadata only: importing pythainlp may
    create its data folder (docs/library-notes/pythainlp.md). Raises when it isn't installed;
    metadata alone can outlive a package whose files are gone, hence `find_spec` too."""
    try:
        version = metadata.version("pythainlp")
    except metadata.PackageNotFoundError:
        raise RuntimeError("ยังไม่ได้ติดตั้ง") from None
    if importlib.util.find_spec("pythainlp") is None:
        raise RuntimeError("ยังไม่ได้ติดตั้ง")
    return version


def this_platform() -> str:
    """The OS this process runs on, as `sys.platform`; tests swap it."""
    return sys.platform


def probe_deno() -> str:
    """Runs `deno --version` from the `deno` wheel in the venv; raises if it fails.

    Not cached: Refresh after setup must see a newly installed Deno.
    """
    import deno

    exe = deno.find_deno_bin()  # raises FileNotFoundError when the wheel is missing
    # First line: "deno 2.9.8 (stable, release, aarch64-apple-darwin)"
    return _version_output("deno", exe, "--version").split()[1]


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


@dataclass(frozen=True)
class Probes:
    """The parts of the Status check that ask the machine; tests pass fakes."""

    device: Callable[[], str]
    ffmpeg: Callable[[], FfmpegInfo]
    deno: Callable[[], str]
    yt_dlp: Callable[[], str]
    mlx_vlm: Callable[[], str]
    pythainlp: Callable[[], str]


def real_probes() -> Probes:
    # Looked up at call time, so tests can swap the module's probes.
    return Probes(
        device=probe_device,
        ffmpeg=probe_ffmpeg,
        deno=probe_deno,
        yt_dlp=probe_yt_dlp,
        mlx_vlm=probe_mlx_vlm,
        pythainlp=probe_pythainlp,
    )


def run_checks(
    root: Path | None = None,
    probes: Probes | None = None,
    sys_platform: str | None = None,
) -> StatusResponse:
    """Builds every Checklist item in spec order. Defaults are `paths.ROOT`
    (looked up at call time, so tests can swap it), the real probes, and the OS
    this process runs on.
    """
    project = ProjectPaths(root or paths.ROOT)
    probes = probes or real_probes()
    sys_platform = sys_platform or this_platform()
    fixes = _fix_texts(sys_platform)
    # The LLM runs on Apple Silicon only; Windows is the windows-launch feature (spoil-maker D50, ADR 0016).
    llm_fix = fixes.setup if sys_platform in QWEN.platforms else MAC_ONLY_FIX

    items = [
        _item("python", "Python venv", lambda: _check_python(project), RUN_BACKEND_FIX),
        _item("torch", "torch", lambda: check_package("torch"), fixes.setup),
        _item("transformers", "transformers", lambda: check_package("transformers"), fixes.setup),
        _item("omnivoice", "omnivoice", lambda: check_package("omnivoice"), fixes.setup),
        _item("fastapi", "fastapi", lambda: check_package("fastapi"), fixes.setup),
        _item("ffmpeg", "ffmpeg", lambda: check_ffmpeg(probes.ffmpeg), fixes.setup),
        # The spoil download gate calls these two probes too (spoil D9).
        _item("yt_dlp", "yt-dlp", lambda: check_version(probes.yt_dlp), fixes.setup),
        _item("deno", "Deno", lambda: check_version(probes.deno), fixes.setup),
        _model_item(project, OMNIVOICE, fixes.setup, sys_platform),
        _model_item(project, WHISPER, fixes.setup, sys_platform),
        _item("device", "Device", lambda: check_device(probes.device), fixes.device),
        # spoil-maker's rows follow the older ones (spoil-maker spec › Status check).
        _model_item(project, QWEN, llm_fix, sys_platform),
        _item("mlx_vlm", "mlx-vlm", lambda: check_mlx_vlm(probes.mlx_vlm, sys_platform), llm_fix),
        _item("pythainlp", "pythainlp", lambda: check_pinned(probes.pythainlp, PYTHAINLP_VERSION), fixes.setup),
    ]
    counts = {s: sum(1 for i in items if i.status == s) for s in get_args(ItemStatus)}
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
    fix: Fix,
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
        fix=None if status == "ok" else fix.text,
        fix_kind=None if status == "ok" else fix.kind,
        license=license,
    )


def _model_item(project: ProjectPaths, model: ModelSpec, fix: Fix, sys_platform: str) -> ChecklistItem:
    license = License(
        name=model.license,
        url=model.license_url,
        author=model.author,
        model_url=model.model_url,
    )
    return _item(
        model.check_id,
        model.label,
        lambda: check_model_on_platform(project, model, sys_platform),
        fix,
        license,
    )


def check_model_on_platform(project: ProjectPaths, model: ModelSpec, sys_platform: str) -> tuple[ItemStatus, str]:
    """`check_model`, on an OS the model runs on; never `ok` on another (spoil-maker D50)."""
    if sys_platform not in model.platforms:
        return "missing", UNSUPPORTED_HERE
    return check_model(project, model)


def check_mlx_vlm(probe: Callable[[], str], sys_platform: str) -> tuple[ItemStatus, str]:
    """Installed at the pinned version. MLX runs where Qwen runs (D50); a failing probe
    raises, and _item turns that into `missing`."""
    if sys_platform not in QWEN.platforms:
        return "missing", UNSUPPORTED_HERE
    return check_pinned(probe, MLX_VLM_VERSION)


def check_pinned(probe: Callable[[], str], pinned: str) -> tuple[ItemStatus, str]:
    """Installed at the pinned version; a failing probe raises, and _item turns that into `missing`."""
    version = probe()
    if version != pinned:
        return "missing", f"version ไม่ตรง: ติดตั้งไว้ {version} ต้องการ {pinned}"
    return "ok", version


def _check_python(project: ProjectPaths) -> tuple[ItemStatus, str]:
    # Only a warning: the packages may still work, but the backend should run
    # from the project's .venv (`npm run dev` does that).
    version = ".".join(str(n) for n in sys.version_info[:3])
    if Path(sys.prefix).resolve() != project.venv_dir.resolve():
        return "warning", f"Python {version} ที่ {sys.prefix} ไม่ใช่ .venv ของ project"
    if sys.version_info[:2] != (3, 12):
        return "warning", f"Python {version} ใน .venv ต้องเป็น 3.12"
    return "ok", f"Python {version} ใน .venv"


def check_package(name: str) -> tuple[ItemStatus, str]:
    try:
        return "ok", metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing", "ยังไม่ได้ติดตั้ง"


def check_ffmpeg(ffmpeg_probe: Callable[[], FfmpegInfo]) -> tuple[ItemStatus, str]:
    # A failing probe raises; _item turns that into `missing`.
    info = ffmpeg_probe()
    return "ok", f"{info.version} ({info.source})"


def check_version(probe: Callable[[], str]) -> tuple[ItemStatus, str]:
    # A probe that returns a version is ok; one that raises makes the item missing.
    return "ok", probe()


def check_device(device_probe: Callable[[], str]) -> tuple[ItemStatus, str]:
    device = device_probe()
    return ("warning" if device == "cpu" else "ok"), device
