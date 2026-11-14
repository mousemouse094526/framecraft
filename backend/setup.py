"""The setup entry point: `python -m backend.setup` (ADR 0002).

The OS wrappers (setup.sh, setup.cmd -> setup.ps1) install uv and run `uv sync`;
everything else happens here. Every step can be re-run: models that are
already `ok` are skipped and snapshot_download skips finished files.
"""

import fnmatch
import json
import os
import shutil
import socket
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from backend import disk, drum_kit, fonts
from backend.checks import (
    Probes,
    StatusResponse,
    check_model,
    named_patterns,
    now_iso,
    qwen_gpu_problem,
    real_probes,
    run_checks,
)
from backend.drum_notes import onnx_runner
from backend.models import MODELS, ONNX_MODELS, ModelSpec, qwen_for
from backend.paths import ROOT, ProjectPaths

IS_WINDOWS = sys.platform == "win32"
BACKEND_ADDRESS = ("127.0.0.1", 8000)
# The models are about 22 GB on a Mac and 35 GB on Windows, whose Qwen is bf16 (19 GB), with
# klein's 11 GB on both (toon D34, D51); the rest is headroom for partial downloads (windows-launch
# D12). A Windows card under Qwen's target skips it, and needs only the 16 GB of the others (D14).
REQUIRED_FREE_BYTES = {"darwin": 32_000_000_000, "win32": 42_000_000_000}
REQUIRED_FREE_BYTES_WITHOUT_QWEN = 27_000_000_000
STATUS_ICONS = {"ok": "✓", "warning": "!", "missing": "✗"}

Download = Callable[..., str]
OpenSession = onnx_runner.OpenSession


def run_setup(
    root: Path = ROOT,
    *,
    download: Download | None = None,
    npm_install: Callable[[Path], None] | None = None,
    fetch: Callable[[str], bytes] | None = None,
    backend_running: Callable[[], bool] | None = None,
    free_bytes: Callable[[Path], int] | None = None,
    probes: Probes | None = None,
    open_session: OpenSession | None = None,
    sys_platform: str = sys.platform,
) -> int:
    """Downloads what is missing and prints the checklist. Returns the exit code. `open_session`
    opens a downloaded ONNX file once, the smoke test before its marker (drum-notes D20)."""
    download = download or _snapshot_download
    open_session = open_session or onnx_runner.open_session
    npm_install = npm_install or _npm_install
    fetch = fetch or fonts.fetch_https
    backend_running = backend_running or _backend_running
    free_bytes = free_bytes or disk.free_bytes
    probes = probes or real_probes()
    project = ProjectPaths(root)

    # A running backend holds torch's files open, so Windows can't update them.
    if backend_running():
        print("ปิด npm run dev ก่อนรัน setup")
        return 1

    if not _take_lock(project.setup_lock):
        print("setup กำลังรันอยู่อีกหน้าต่าง")
        return 1
    step = "เช็คโมเดล"
    try:
        # Each OS downloads only its own models: the MLX one doesn't run on Windows (spoil-maker D50).
        to_download = [
            m for m in MODELS if sys_platform in m.platforms and check_model(project, m)[0] != "ok"
        ]
        skip = _qwen_skip_reason(probes, sys_platform)
        if skip:
            qwen = qwen_for(sys_platform)
            to_download = [m for m in to_download if m != qwen]
            print(f"ข้าม {qwen.label}: {skip}")
        if to_download:
            step = "เช็คที่ว่างบนดิสก์"
            free = free_bytes(root)
            # Another OS (Linux, for tests) is held to the larger, Mac figure.
            required = REQUIRED_FREE_BYTES.get(sys_platform, REQUIRED_FREE_BYTES["darwin"])
            if skip:
                required = REQUIRED_FREE_BYTES_WITHOUT_QWEN
            if free < required:
                print(f"ที่ว่างบนดิสก์ไม่พอ: มี {free / 1e9:.1f} GB ต้องการ {required // 1_000_000_000} GB")
                return 1
        for model in to_download:
            if model in ONNX_MODELS:
                continue  # after the drum kit (drum-notes D7)
            step = f"โหลด {model.repo_id}"
            _download_model(project, model, download)
        if fonts.check_kanit(project)[0] != "ok":
            step = "โหลด Kanit"
            print("กำลังโหลด font Kanit…")
            fonts.install_kanit(project, fetch)
        if drum_kit.check_drum_kit(project)[0] != "ok":
            step = "โหลดเสียงกลอง"
            print("กำลังโหลดเสียงกลอง Big Rusty Drums…")
            drum_kit.install_drum_kit(project, fetch)
        for model in to_download:
            if model not in ONNX_MODELS:
                continue
            step = f"โหลด {model.repo_id}"
            snapshot = _download_model(project, model, download, marker=False)
            _open_onnx_files(model, snapshot, open_session)
            _write_marker(project, model, snapshot)
        step = "npm install"
        print("กำลังรัน npm install…", flush=True)  # before npm writes its own output
        npm_install(root)
    except Exception as error:
        print(f"ล้มที่ขั้น {step}: {error}")
        print("รัน setup ใหม่เพื่อทำต่อจากที่ค้าง")
        return 1
    finally:
        project.setup_lock.unlink(missing_ok=True)

    result = run_checks(root, probes, sys_platform)
    _print_checklist(result)
    if not result.ready:
        missing = [i.label for i in result.items if i.status == "missing"]
        print(f"ยังขาด: {', '.join(missing)}")
        return 1
    print("ขั้นต่อไป: รัน npm run dev แล้วเปิด http://localhost:5173")
    return 0


def _qwen_skip_reason(probes: Probes, sys_platform: str) -> str | None:
    """Why Qwen isn't downloaded here: on Windows, the gpu row's fix when the card misses
    Qwen's target or nvidia-smi can't read it, so 19 GB it may not run never come down
    (windows-launch D9). The rows warn, and setup still exits 0."""
    if sys_platform != "win32":
        return None
    problem = qwen_gpu_problem(probes.gpu)
    return problem.text if problem else None


def _snapshot_download(repo_id: str, **kwargs) -> str:
    from huggingface_hub import snapshot_download

    return snapshot_download(repo_id, **kwargs)


def _npm_install(root: Path) -> None:
    """Installs the root packages (concurrently) and the web UI's packages."""
    # which() finds npm.cmd on Windows, where a bare "npm" can't be executed.
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("ไม่พบคำสั่ง npm: ติดตั้ง Node.js 22+ จาก https://nodejs.org")
    subprocess.run([npm, "install"], cwd=root, check=True)
    subprocess.run([npm, "install", "--prefix", "frontend"], cwd=root, check=True)


def _backend_running() -> bool:
    try:
        with socket.create_connection(BACKEND_ADDRESS, timeout=0.5):
            return True
    except OSError:
        return False


def _take_lock(lock: Path) -> bool:
    """Creates the lock with our PID unless a live process already holds it."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    # Two tries: the second follows removing a lock whose setup died.
    for _ in range(2):
        try:
            # O_EXCL: of two setups started together, only one creates the file.
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if _lock_holder_alive(lock):
                return False
            lock.unlink(missing_ok=True)  # left by a setup that died
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(str(os.getpid()))
        return True
    return False


def _lock_holder_alive(lock: Path) -> bool:
    try:
        holder = int(lock.read_text(encoding="utf-8").strip())
    except (ValueError, FileNotFoundError):
        return False
    return _pid_alive(holder)


def _pid_alive(pid: int) -> bool:
    if IS_WINDOWS:
        return _windows_pid_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:  # alive, but owned by another user
        return True
    return True


def _windows_pid_alive(pid: int) -> bool:
    # os.kill(pid, 0) would terminate the process on Windows, so ask the OS instead.
    import ctypes
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    still_active = 259
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def _download_model(project: ProjectPaths, model: ModelSpec, download: Download, marker: bool = True) -> Path:
    """One model's snapshot, its named files checked; its marker too unless the caller writes it
    after a check of its own. Returns the snapshot folder."""
    print(f"กำลังโหลด {model.repo_id} ({model.short_revision})…")
    snapshot = Path(
        download(model.repo_id, revision=model.revision, cache_dir=project.hub_dir, allow_patterns=list(model.allow_patterns))
    )
    _check_named_files(model, snapshot)
    if marker:
        _write_marker(project, model, snapshot)
    return snapshot


def _open_onnx_files(model: ModelSpec, snapshot: Path, open_session: OpenSession) -> None:
    """Opens each `.onnx` file of the snapshot once: a file onnxruntime can't load ends setup
    naming it, with no marker (drum-notes D20)."""
    for pattern in model.allow_patterns:
        if not pattern.endswith(".onnx"):
            continue
        try:
            open_session(snapshot / pattern)
        except Exception as error:
            raise RuntimeError(f"เปิดไฟล์โมเดล {pattern} ไม่ได้: {error}") from None


def _check_named_files(model: ModelSpec, snapshot: Path) -> None:
    """Every pattern that names a file or a folder (`text_encoder/*`) matched a file: a download
    can finish with a folder holding nothing (toon trial-klein-mac › 5.3), so its exit isn't trusted.
    The same patterns the Status check looks for in the marker (`checks.named_patterns`, D50)."""
    found = [path.relative_to(snapshot).as_posix() for path in snapshot.rglob("*") if path.is_file()]
    for pattern in named_patterns(model):
        if not any(fnmatch.fnmatch(name, pattern) for name in found):
            raise RuntimeError(f"ไม่พบไฟล์ {pattern} หลังโหลด")


def _write_marker(project: ProjectPaths, model: ModelSpec, snapshot: Path) -> None:
    """Records every file of the snapshot so the check can spot a deleted one."""
    files = [
        {"path": path.relative_to(snapshot).as_posix(), "size": path.stat().st_size}
        for path in sorted(snapshot.rglob("*"))
        if path.is_file()
    ]
    marker = {
        "repo_id": model.repo_id,
        "revision": model.revision,
        "files": files,
        "size_bytes": sum(f["size"] for f in files),
        "finished_at": now_iso(),
    }
    path = project.marker(model)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write then rename, so an interrupted setup never leaves half a marker.
    partial = path.with_suffix(".json.partial")
    partial.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    os.replace(partial, path)


def _print_checklist(result: StatusResponse) -> None:
    print(f"\nStatus check: {result.ok_count}/{result.total}")
    for item in result.items:
        print(f"{STATUS_ICONS[item.status]} {item.label}: {item.detail}")
        if item.fix:
            print(f"    แก้: {item.fix}")


def main() -> None:
    sys.exit(run_setup())


if __name__ == "__main__":
    main()
