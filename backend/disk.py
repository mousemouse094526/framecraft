"""Disk space, shared by setup and the spoil download."""

import shutil
from pathlib import Path


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free
