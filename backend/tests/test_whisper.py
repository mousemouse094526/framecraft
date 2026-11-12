"""The pure parts of the Whisper adapter; the model itself is checked by hand (spoil seam 3)."""

import subprocess
import sys
from pathlib import Path

import pytest

from backend.spoil import whisper


@pytest.mark.parametrize(
    ("duration_s", "segments"),
    [
        (20, [(0, 20)]),
        (300, [(0, 300)]),
        (329, [(0, 329)]),  # a last piece under 30 s joins the one before
        (330, [(0, 300), (300, 30)]),
        (610, [(0, 300), (300, 310)]),
        (5743, [(start, 300) for start in range(0, 5700, 300)] + [(5700, 43)]),
        (None, [(0, None)]),
        (0, [(0, None)]),
    ],
)
def test_plan_segments(duration_s, segments):
    assert whisper.plan_segments(duration_s) == segments


def test_lines_move_by_the_segment_start():
    chunks = [{"timestamp": (1.0, 2.5), "text": " Hi."}, {"timestamp": (10.0, 12.0), "text": " There."}]

    assert whisper.to_lines(chunks, 600, 300) == [(601.0, 602.5, " Hi."), (610.0, 612.0, " There.")]


def test_a_missing_end_is_the_segment_end():
    chunks = [{"timestamp": (290.26, None), "text": " Jesus."}]

    assert whisper.to_lines(chunks, 300, 300) == [(590.26, 600.0, " Jesus.")]


def test_an_end_past_the_segment_is_clamped():
    # Seen on a real 300 s array: (298.48, 328.46).
    chunks = [{"timestamp": (298.48, 328.46), "text": " Thank you."}]

    assert whisper.to_lines(chunks, 0, 300) == [(298.48, 300.0, " Thank you.")]


def test_a_segment_of_unknown_length_keeps_whisper_times():
    chunks = [{"timestamp": (1.0, None), "text": " Hi."}, {"timestamp": (2.0, 3.0), "text": " There."}]

    assert whisper.to_lines(chunks, 0, None) == [(1.0, 1.0, " Hi."), (2.0, 3.0, " There.")]


def test_importing_the_adapter_loads_neither_torch_nor_transformers():
    # The backend imports it on every start; torch takes seconds (spec › Transcribe).
    code = "import sys, backend.spoil.whisper; sys.exit(bool({'torch', 'transformers'} & set(sys.modules)))"
    root = Path(__file__).resolve().parents[2]

    assert subprocess.run([sys.executable, "-c", code], cwd=root).returncode == 0
