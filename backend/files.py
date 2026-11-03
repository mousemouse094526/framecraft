"""Writing files so a crash never leaves half of one: shared by every feature that keeps JSON."""

import os
from pathlib import Path


def write_atomic(target: Path, text: str) -> None:
    """Writes through `{target}.tmp` then renames it, removing the `.tmp` if the
    rename fails; a crash in between leaves a `.tmp` that start-up removes."""
    temporary = target.with_name(target.name + ".tmp")
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
