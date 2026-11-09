"""The klein adapter's surface and the pure helpers of the Ref job (toon seam 1); the real
`worker` is checked by hand with the model (trial in progress.md)."""

import subprocess
import sys
from pathlib import Path

import pytest

from backend.checks import named_patterns
from backend.models import KLEIN, KLEIN_GGUF, QWEN_MAC
from backend.toon import prompts


def test_importing_the_adapter_loads_neither_torch_nor_diffusers():
    # The backend imports it on every start; torch takes seconds.
    code = "import sys, backend.toon.jobs; sys.exit(bool({'torch', 'diffusers'} & set(sys.modules)))"
    root = Path(__file__).resolve().parents[2]

    assert subprocess.run([sys.executable, "-c", code], cwd=root).returncode == 0


@pytest.mark.parametrize(
    ("reply", "scene"),
    [
        ('{"scene": "A boy  in a\\nnavy shirt."}', "A boy in a navy shirt."),
        ('```json\n{"scene": "An empty corridor."}\n```', "An empty corridor."),
        ('{"scene": "  "}', None),
        ('{"scene": 3}', None),
        ("no json here", None),
        ('["scene"]', None),
    ],
)
def test_parse_scene_reads_the_scene_of_qwen_s_json(reply, scene):
    assert prompts.parse_scene(reply) == scene


def test_named_patterns_are_files_and_folders_not_kinds_of_file():
    assert named_patterns(KLEIN) == [
        "model_index.json",
        "text_encoder/*",
        "tokenizer/*",
        "vae/*",
        "scheduler/*",
        "transformer/config.json",
    ]
    assert named_patterns(KLEIN_GGUF) == ["flux-2-klein-4b-Q4_K_M.gguf"]
    assert named_patterns(QWEN_MAC) == []
