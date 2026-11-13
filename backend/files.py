"""Writing files so a crash never leaves half of one: shared by every feature that keeps JSON."""

import json
import os
import uuid
from pathlib import Path


def write_atomic(target: Path, text: str, unique: bool = False) -> None:
    """Writes through `{target}.tmp` then renames it, removing the `.tmp` if the
    rename fails; a crash in between leaves a `.tmp` that start-up removes.
    `unique`: `{target}.{uuid}.tmp`, so two writers never share one."""
    suffix = f".{uuid.uuid4().hex}.tmp" if unique else ".tmp"
    temporary = target.with_name(target.name + suffix)
    temporary.write_text(text, encoding="utf-8")
    try:
        os.replace(temporary, target)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def write_marker(marker: Path, files: dict[str, str]) -> None:
    """A Setup marker naming each pinned file's sha256, through `{marker}.partial` then a
    rename, written last so a marker always means every file is there (ADR 0004)."""
    marker.parent.mkdir(parents=True, exist_ok=True)
    partial = marker.with_name(marker.name + ".partial")
    partial.write_text(json.dumps({"files": files}, indent=2), encoding="utf-8")
    os.replace(partial, marker)


def remove_unfinished(folder: Path) -> None:
    """Removes every `.tmp` under `folder` that `write_atomic` left: start-up runs it,
    since nothing is half way through a write then."""
    if folder.is_dir():
        for leftover in folder.rglob("*.tmp"):
            leftover.unlink(missing_ok=True)
