"""How many tokens a text is to Qwen, gated on its Status check row: an EP's lines
(spoil-maker D46) and a Story block (story-kb D14) count the same way.

`spoil_maker.count_tokens` is looked up at call time, so tests swap it for a fake.
"""

from backend import gate_rows, spoil_maker
from backend.errors import ApiError, require_rows
from backend.models import QWEN
from backend.paths import ProjectPaths


def count(project: ProjectPaths, text: str) -> int:
    """Raises `ApiError` 503 `not_ready` without Qwen's tokenizer (spoil-maker D60)."""
    require_rows(gate_rows.qwen_model(project))
    try:
        return spoil_maker.count_tokens(project.snapshot_dir(QWEN, QWEN.revision), text)
    except OSError:
        # A marker without its snapshot, or with files transformers can't read: the install is broken the same way.
        raise ApiError(503, "not_ready", f"ยังติดตั้งไม่ครบ: {QWEN.label}", rows=[QWEN.check_id]) from None
