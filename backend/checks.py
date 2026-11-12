"""The Status check: the Checklist items shared by setup and the API.

Never imports `omnivoice` or `transformers` and never uses the network.
Packages are checked through their installed metadata only.
"""

import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Literal, NamedTuple, get_args

from pydantic import BaseModel

from backend import fonts, paths
from backend.models import KLEIN, KLEIN_GGUF, OMNIVOICE, WHISPER, ModelSpec, qwen_for
from backend.paths import ProjectPaths

ItemStatus = Literal["ok", "missing", "warning"]
# "command" is copied and run as-is (the UI shows a copy chip); "hint" is a sentence.
FixKind = Literal["command", "hint"]

VERSION_TIMEOUT_SECONDS = 5
MLX_VLM_VERSION = "0.7.11"  # the pin in pyproject.toml (spoil-maker spec › Dependencies)
PYTHAINLP_VERSION = "5.4.0"  # the pin in pyproject.toml (spoil-maker spec › Dependencies)
DIFFUSERS_VERSION = "0.42.1"  # the pin in pyproject.toml (toon spec › Dependencies)
GGUF_VERSION = "0.19.0"  # the pin in pyproject.toml (toon D47)


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
# Only Mac and Windows are supported (ADR 0006), so "not here" means Windows.
UNSUPPORTED_HERE = "ยังไม่รองรับบน Windows"

# Qwen's target on Windows: bfloat16 in hardware (RTX 30xx, sm_80) and 8 GB, which a card
# reports as a little under 8 GiB (windows-launch D9, D10).
QWEN_MIN_CAPABILITY = (8, 0)
QWEN_MIN_MEMORY_BYTES = 15 * 2**29  # 7.5 GiB
QWEN_GPU_FIX = Fix("Qwen ต้องใช้การ์ด NVIDIA RTX 30xx ขึ้นไปที่มี VRAM อย่างน้อย 8 GB", "hint")
# A card nvidia-smi can't read isn't said to be too old (windows-launch D12).
GPU_UNREADABLE_FIX = Fix("อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA", "hint")
NVIDIA_SMI_QUERY = [
    "nvidia-smi",
    "--query-gpu=name,memory.total,compute_cap",
    "--format=csv,noheader,nounits",
    "-i",
    "0",  # card 0, the one the workers load (`cuda:0`, windows-launch D8)
]


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


class GpuInfo(NamedTuple):
    name: str  # nvidia-smi name of GPU 0
    memory_bytes: int  # nvidia-smi memory.total (MiB × 2**20)
    capability: tuple[int, int]  # nvidia-smi compute_cap, e.g. "8.6" → (8, 6)
    arch_list: tuple[str, ...]  # torch.cuda.get_arch_list(), e.g. ("sm_75", "sm_80", ...)

    @property
    def sm(self) -> str:
        return f"sm_{self.capability[0]}{self.capability[1]}"


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


def probe_gpu(
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    arch_list: Callable[[], tuple[str, ...]] | None = None,
) -> GpuInfo:
    """Card 0 as nvidia-smi reads it, and what torch was built for; raises when nvidia-smi
    fails. Never asks torch about the device: that makes a CUDA context in the backend
    process, which holds VRAM next to the worker's (windows-launch D12). Windows only.
    Tests pass `run` and `arch_list`."""
    result = run(NVIDIA_SMI_QUERY, capture_output=True, text=True, timeout=VERSION_TIMEOUT_SECONDS)
    if result.returncode != 0:
        raise RuntimeError(f"nvidia-smi exited with {result.returncode}: {result.stderr.strip()}")
    # "NVIDIA GeForce RTX 3060, 12288, 8.6": split from the right, a name may hold a comma.
    name, mib, capability = (field.strip() for field in result.stdout.strip().rsplit(",", 2))
    major, minor = capability.split(".")
    return GpuInfo(name, int(mib) * 2**20, (int(major), int(minor)), (arch_list or torch_arch_list)())


def torch_arch_list() -> tuple[str, ...]:
    """The `sm_XY` targets this torch was built for; reads build flags, not the device."""
    import torch  # takes seconds, so not imported until a check needs it

    return tuple(torch.cuda.get_arch_list())


def probe_bitsandbytes() -> str:
    """The installed bitsandbytes version, from its metadata only. Raises when it isn't installed."""
    try:
        return metadata.version("bitsandbytes")
    except metadata.PackageNotFoundError:
        raise RuntimeError("ยังไม่ได้ติดตั้ง") from None


def probe_diffusers() -> str:
    """The installed diffusers version, from its metadata only: importing it pulls in torch."""
    return _installed_version("diffusers")


def probe_gguf() -> str:
    """The installed gguf version, from its metadata only (docs/library-notes/gguf.md)."""
    return _installed_version("gguf")


def _installed_version(name: str) -> str:
    """Raises when the package isn't installed."""
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        raise RuntimeError("ยังไม่ได้ติดตั้ง") from None


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


# A check returns (status, detail) or raises; a raise makes the item `missing`. A third
# value is the fix to show instead of the row's own, when the reason decides it.
CheckResult = tuple[ItemStatus, str] | tuple[ItemStatus, str, Fix]
Check = Callable[[], CheckResult]


@dataclass(frozen=True)
class Probes:
    """The parts of the Status check that ask the machine; tests pass fakes."""

    device: Callable[[], str]
    ffmpeg: Callable[[], FfmpegInfo]
    deno: Callable[[], str]
    yt_dlp: Callable[[], str]
    mlx_vlm: Callable[[], str]
    pythainlp: Callable[[], str]
    gpu: Callable[[], GpuInfo]  # Windows only
    bitsandbytes: Callable[[], str]  # Windows only
    diffusers: Callable[[], str]
    gguf: Callable[[], str]


def real_probes() -> Probes:
    # Looked up at call time, so tests can swap the module's probes.
    return Probes(
        device=probe_device,
        ffmpeg=probe_ffmpeg,
        deno=probe_deno,
        yt_dlp=probe_yt_dlp,
        mlx_vlm=probe_mlx_vlm,
        pythainlp=probe_pythainlp,
        gpu=probe_gpu,
        bitsandbytes=probe_bitsandbytes,
        diffusers=probe_diffusers,
        gguf=probe_gguf,
    )


def read_once(probe: Callable[[], GpuInfo]) -> Callable[[], GpuInfo]:
    """`probe`, run at most once: every row of one check reads the same card, and
    nvidia-smi runs once. What the first call raised is raised again on every later call
    (hence a list, not `functools.cache`, which keeps only return values)."""
    reading: list[GpuInfo | Exception] = []

    def read() -> GpuInfo:
        if not reading:
            try:
                reading.append(probe())
            except Exception as error:
                reading.append(error)
        if isinstance(reading[0], Exception):
            raise reading[0]
        return reading[0]

    return read


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
    gpu = read_once(probes.gpu)
    qwen = qwen_for(sys_platform)
    qwen_rows = [
        _item(row_id, label, check, fixes.setup, _license(qwen) if row_id == qwen.check_id else None)
        for row_id, (label, check) in qwen_checks(project, probes, sys_platform, gpu).items()
    ]

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
        _item("device", "Device", device_check(probes.device, sys_platform, gpu), fixes.device),
        # spoil-maker's rows follow the older ones (spoil-maker spec › Status check).
        *qwen_rows,
        _item("pythainlp", "pythainlp", lambda: check_pinned(probes.pythainlp, PYTHAINLP_VERSION), fixes.setup),
        _item(fonts.CHECK_ID, fonts.LABEL, lambda: fonts.check_kanit(project), fixes.setup),
        # The การ์ตูนเล่า tab's rows follow Kanit (toon spec › Status check).
        _model_item(project, KLEIN, fixes.setup, sys_platform),
        _model_item(project, KLEIN_GGUF, fixes.setup, sys_platform),
        *(_item(row_id, label, check, fixes.setup) for row_id, (label, check) in klein_packages(probes).items()),
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


def qwen_checks(
    project: ProjectPaths, probes: Probes, sys_platform: str, gpu: Callable[[], GpuInfo]
) -> dict[str, tuple[str, Check]]:
    """Qwen's rows on this OS, id → (label, check), in checklist order: on a Mac its MLX
    model and mlx-vlm; on Windows the gpu row, its model and bitsandbytes, which warn with
    the gpu row's fix on a card under Qwen's target (windows-launch D6, D8, D9). The Status
    check and the gate of a Qwen job both read them. `gpu` is called only on Windows."""
    qwen = qwen_for(sys_platform)

    def model() -> CheckResult:
        return check_model(project, qwen)

    if sys_platform != "win32":
        return {
            qwen.check_id: (qwen.label, model),
            "mlx_vlm": ("mlx-vlm", lambda: check_pinned(probes.mlx_vlm, MLX_VLM_VERSION)),
        }
    return {
        "gpu": ("GPU", lambda: check_gpu(gpu)),
        qwen.check_id: (qwen.label, on_qwen_gpu(gpu, model)),
        "bitsandbytes": ("bitsandbytes", on_qwen_gpu(gpu, lambda: check_version(probes.bitsandbytes))),
    }


def klein_packages(probes: Probes) -> dict[str, tuple[str, Check]]:
    """The two packages klein's child imports, id → (label, check): the Status check and
    klein's gate both read them (toon spec › Status check)."""
    return {
        "diffusers": ("diffusers", lambda: check_pinned(probes.diffusers, DIFFUSERS_VERSION)),
        "gguf": ("gguf", lambda: check_pinned(probes.gguf, GGUF_VERSION)),
    }


def device_check(device: Callable[[], str], sys_platform: str, gpu: Callable[[], GpuInfo]) -> Check:
    """The `device` row's check on this OS; on Windows it reads the card too (windows-launch D8)."""
    return lambda: check_device(device, gpu if sys_platform == "win32" else None)


def named_patterns(model: ModelSpec) -> list[str]:
    """The patterns of `allow_patterns` that name a file or a folder (`text_encoder/*`),
    not a kind of file (`*.json`): each must match a downloaded file (toon D50)."""
    return [pattern for pattern in model.allow_patterns if "*" not in pattern.split("/")[0]]


def check_model(project: ProjectPaths, model: ModelSpec) -> tuple[ItemStatus, str]:
    """Whether a model's marker, revision, and files all match, and every file or folder
    `allow_patterns` names is among its files. Used by setup too."""
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
    names = [file["path"] for file in files]
    for pattern in named_patterns(model):
        if not any(fnmatch.fnmatch(name, pattern) for name in names):
            # Another file of the same revision was downloaded (toon D49).
            return "missing", f"ไม่มีไฟล์ {pattern} ใน marker"
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
        status, detail, *own_fix = check()
        fix = own_fix[0] if own_fix else fix
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


def _license(model: ModelSpec) -> License:
    return License(name=model.license, url=model.license_url, author=model.author, model_url=model.model_url)


def _model_item(project: ProjectPaths, model: ModelSpec, fix: Fix, sys_platform: str) -> ChecklistItem:
    return _item(
        model.check_id,
        model.label,
        lambda: check_model_on_platform(project, model, sys_platform),
        fix,
        _license(model),
    )


def check_model_on_platform(project: ProjectPaths, model: ModelSpec, sys_platform: str) -> tuple[ItemStatus, str]:
    """`check_model`, on an OS the model runs on; never `ok` on another (spoil-maker D50)."""
    if sys_platform not in model.platforms:
        return "missing", UNSUPPORTED_HERE
    return check_model(project, model)


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


def check_device(device_probe: Callable[[], str], gpu: Callable[[], GpuInfo] | None = None) -> CheckResult:
    """`cpu` is a warning (ADR 0006). Given `gpu` (Windows), a CUDA card this torch has
    no kernels for is missing: every GPU job would fail on it (windows-launch D8). The
    detail is the device, or on that missing card the card itself (windows-launch D15)."""
    device = device_probe()
    if device == "cpu":
        return "warning", device
    if device != "cuda" or gpu is None:
        return "ok", device
    try:
        card = gpu()
    except Exception:
        return "ok", device  # the gpu row says it can't read the card (windows-launch D12)
    if not torch_runs_on(card):
        return "missing", f"{card.name} · {card.sm}", Fix(f"การ์ด {card.name} ({card.sm}) เก่าเกินสำหรับ torch ที่ติดตั้ง", "hint")
    return "ok", device


def torch_runs_on(card: GpuInfo) -> bool:
    """CUDA kernels run on every later card of their major, so sm_86 covers an sm_89:
    the rule torch's own `_check_cubins` uses (docs/library-notes/torch.md, windows-launch D13)."""
    built = [int(re.sub(r"\D", "", arch.removeprefix("sm_"))) for arch in card.arch_list if arch.startswith("sm_")]
    return any(sm // 10 == card.capability[0] for sm in built)


def check_gpu(gpu: Callable[[], GpuInfo]) -> CheckResult:
    """Windows: ok on a card that meets Qwen's target (windows-launch D9, D10); otherwise a
    warning, which a Qwen job's gate refuses but which leaves `ready` true. A card
    `nvidia-smi` can't read is a warning with an empty detail: the fix tells the user
    what to do, and the error is dropped by design (windows-launch D12, D15)."""
    try:
        card = gpu()
    except Exception:
        return "warning", "", GPU_UNREADABLE_FIX
    detail = f"{card.name} · {card.memory_bytes / 2**30:.0f} GB · {card.sm}"
    if card.capability < QWEN_MIN_CAPABILITY or card.memory_bytes < QWEN_MIN_MEMORY_BYTES:
        return "warning", detail, QWEN_GPU_FIX
    return "ok", detail


def qwen_gpu_problem(gpu: Callable[[], GpuInfo]) -> Fix | None:
    """The gpu row's fix when Qwen can't run on this card — under its target, or
    unreadable — else None. Setup skips Qwen's download on the same answer (windows-launch D9)."""
    status, _, *fix = check_gpu(gpu)
    return fix[0] if status != "ok" else None


def on_qwen_gpu(gpu: Callable[[], GpuInfo], check: Check) -> Check:
    """`check`, on a card Qwen runs on. Otherwise `check` still runs for its detail
    alone — its status, even a raise, is dropped — and the row is a warning with the
    gpu row's fix, so a weak card never makes `ready` false (windows-launch D9, D15)."""

    def checked() -> CheckResult:
        problem = qwen_gpu_problem(gpu)
        if not problem:
            return check()
        try:
            _, detail, *_ = check()
        except Exception as error:  # bitsandbytes not installed, say
            detail = str(error) or type(error).__name__
        return "warning", detail, problem

    return checked
