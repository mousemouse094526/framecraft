"""Writing files so a crash never leaves half of one: shared by every feature that keeps JSON."""

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


def remove_unfinished(folder: Path) -> None:
    """Removes every `.tmp` under `folder` that `write_atomic` left: start-up runs it,
    since nothing is half way through a write then."""
    if folder.is_dir():
        for leftover in folder.rglob("*.tmp"):
            leftover.unlink(missing_ok=True)
