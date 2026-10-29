"""The setup entry point: `python -m backend.setup` (ADR 0002).

The OS wrappers (setup.sh, setup.cmd -> setup.ps1) install uv and run `uv sync`;
everything else happens here. Every step can be re-run: models that are
already `ok` are skipped and snapshot_download skips finished files.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from backend.checks import (
    FfmpegInfo,
    StatusResponse,
    check_model,
    now_iso,
    run_checks,
)
from backend.models import MODELS, ModelSpec
from backend.paths import ROOT, ProjectPaths

IS_WINDOWS = sys.platform == "win32"
BACKEND_ADDRESS = ("127.0.0.1", 8000)
# Both models are about 5 GB; the rest is headroom for partial downloads.
REQUIRED_FREE_BYTES = 15_000_000_000
STATUS_ICONS = {"ok": "✓", "warning": "!", "missing": "✗"}

Download = Callable[..., str]


def run_setup(
    root: Path = ROOT,
    *,
    download: Download | None = None,
    npm_install: Callable[[Path], None] | None = None,
    backend_running: Callable[[], bool] | None = None,
    free_bytes: Callable[[Path], int] | None = None,
    device_probe: Callable[[], str] | None = None,
    ffmpeg_probe: Callable[[], FfmpegInfo] | None = None,
) -> int:
    """Downloads what is missing and prints the checklist. Returns the exit code."""
    download = download or _snapshot_download
    npm_install = npm_install or _npm_install
    backend_running = backend_running or _backend_running
    free_bytes = free_bytes or _free_bytes
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
        to_download = [m for m in MODELS if check_model(project, m)[0] != "ok"]
        if to_download:
            step = "เช็คที่ว่างบนดิสก์"
            free = free_bytes(root)
            if free < REQUIRED_FREE_BYTES:
                print(
                    f"ที่ว่างบนดิสก์ไม่พอ: มี {free / 1e9:.1f} GB "
                    f"ต้องการ {REQUIRED_FREE_BYTES // 1_000_000_000} GB"
                )
                return 1
        for model in to_download:
            step = f"โหลด {model.repo_id}"
            print(f"กำลังโหลด {model.repo_id} ({model.short_revision})…")
            snapshot = download(
                model.repo_id,
                revision=model.revision,
                cache_dir=project.hub_dir,
                allow_patterns=list(model.allow_patterns),
            )
            _write_marker(project, model, Path(snapshot))
        step = "npm install"
        print("กำลังรัน npm install…", flush=True)  # before npm writes its own output
        npm_install(root)
    except Exception as error:
        print(f"ล้มที่ขั้น {step}: {error}")
        print("รัน setup ใหม่เพื่อทำต่อจากที่ค้าง")
        return 1
    finally:
        project.setup_lock.unlink(missing_ok=True)

    result = run_checks(root, device_probe=device_probe, ffmpeg_probe=ffmpeg_probe)
    _print_checklist(result)
    if not result.ready:
        missing = [i.label for i in result.items if i.status == "missing"]
        print(f"ยังขาด: {', '.join(missing)}")
        return 1
    print("ขั้นต่อไป: รัน npm run dev แล้วเปิด http://localhost:5173")
    return 0


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


def _free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def _take_lock(lock: Path) -> bool:
    """Creates the lock with our PID unless a live process already holds it."""
    lock.parent.mkdir(parents=True, exist_ok=True)
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
