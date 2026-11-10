"""The klein adapter's surface, the pure helpers of the Ref job and how the status check finds
klein's files. The real `worker` needs the model and a GPU, so it is checked by hand on a Mac."""

import subprocess
import sys
from pathlib import Path

import pytest

from backend.checks import named_patterns
from backend.models import KLEIN, KLEIN_GGUF, QWEN_MAC
from backend.toon import prompts


def test_importing_the_toon_jobs_and_their_klein_adapter_loads_neither_torch_nor_diffusers():
    # The backend imports them on every start; torch takes seconds.
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


def test_status_check_compares_the_named_files_and_folders_of_a_model_and_skips_file_types():
    # D50: a pattern like `*.safetensors` names no file, so setup can't check it is there.
    assert named_patterns(KLEIN) == [
        "model_index.json",
        "text_encoder/*",
        "tokenizer/*",
        "vae/*",
        "scheduler/*",
        "transformer/config.json",
    ]
    assert named_patterns(KLEIN_GGUF) == ["flux-2-klein-4b-Q4_K_M.gguf"]
    # The Qwen an Image job translates with lists only kinds of file (`*.json`, …): no file to look for.
    assert named_patterns(QWEN_MAC) == []
