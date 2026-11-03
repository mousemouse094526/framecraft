"""Counting Qwen tokens: the only module that imports transformers' tokenizer
(spoil-maker D46). It reads the tokenizer files in Qwen's snapshot, loads no model
and uses no GPU, so it runs in the backend process.

transformers is imported inside `count` only: it takes seconds, and the backend
must start in under a second.
"""

import threading
from pathlib import Path

_lock = threading.Lock()
_loaded: dict[Path, object] = {}  # one tokenizer per snapshot, loaded at its first count


def count(snapshot_dir: Path, text: str) -> int:
    """How many tokens `text` is to Qwen, without the special tokens a chat adds."""
    return len(_tokenizer(snapshot_dir).encode(text, add_special_tokens=False))


def _tokenizer(snapshot_dir: Path):
    """`from_pretrained` downloads when the path isn't a folder, so a missing one
    raises instead (ADR 0002); `local_files_only` keeps it off the network."""
    with _lock:
        if snapshot_dir not in _loaded:
            if not snapshot_dir.is_dir():
                raise FileNotFoundError(f"no model snapshot at {snapshot_dir}")
            from transformers import AutoTokenizer

            _loaded[snapshot_dir] = AutoTokenizer.from_pretrained(str(snapshot_dir), local_files_only=True)
        return _loaded[snapshot_dir]
