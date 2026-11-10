"""Disk space, shared by setup, the spoil download, the spoil-maker render and the toon jobs."""

import shutil
from pathlib import Path

from backend.errors import ApiError

MIN_FREE_BYTES = 2**30  # a job that writes media needs 1 GiB free after its bytes land


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def require_free(root: Path, incoming: int = 0) -> None:
    """Raises `ApiError` 507 `disk_full` unless 1 GiB stays free after `incoming` bytes land."""
    if free_bytes(root) < MIN_FREE_BYTES + incoming:
        raise ApiError(507, "disk_full", "ที่ว่างดิสก์ไม่ถึง 1 GiB")
