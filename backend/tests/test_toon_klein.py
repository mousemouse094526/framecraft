"""The klein adapter's surface, the pure helpers of the Ref job and how the status check finds
klein's files. The real `worker` needs the model and a GPU, so it is checked by hand on a Mac;
its two children run here with the model stubbed."""

import queue
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from backend.checks import named_patterns
from backend.models import KLEIN, KLEIN_GGUF, QWEN_MAC
from backend.toon import klein, prompts


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


def test_the_encoder_s_child_answers_its_one_encode_with_the_embeddings_and_ends_without_being_asked(monkeypatch):
    """Step 1 of D74: the child ends, and the text encoder's memory with it, before the drawing child starts."""
    monkeypatch.setattr(klein, "encode", lambda snapshot_dir, device, prompts: [f"embeds of {p}".encode() for p in prompts])
    requests, replies = queue.Queue(), queue.Queue()
    requests.put(klein.Encode(["a", "b"]))

    klein.encoder_worker(Path("snapshot"), "cpu", requests, replies)

    assert replies.get_nowait() == klein.Encoded([b"embeds of a", b"embeds of b"])
    assert requests.empty()


def test_the_encoder_s_child_asked_to_end_before_any_encode_ends_without_a_word():
    requests, replies = queue.Queue(), queue.Queue()
    requests.put(None)

    klein.encoder_worker(Path("snapshot"), "cpu", requests, replies)

    assert replies.empty()


def test_the_drawing_child_loads_with_the_encoder_s_embeddings_and_draws_the_one_each_draw_names(monkeypatch):
    drawn = []
    monkeypatch.setattr(klein, "load_pipeline", lambda *args: "pipe")
    monkeypatch.setattr(klein, "embeds_from", lambda data: data.decode())
    monkeypatch.setattr(klein, "draw", lambda pipe, embeds, request, device: drawn.append((pipe, embeds)) or b"png")
    requests, replies = queue.Queue(), queue.Queue()
    for request in (klein.Load([b"first", b"second"]), klein.Draw(1, [], 8, 8, 0), None):
        requests.put(request)

    klein.drawer_worker(Path("snapshot"), Path("gguf"), "cpu", requests, replies)

    assert [replies.get_nowait(), replies.get_nowait()] == [klein.Loaded(), klein.Drawn(b"png")]
    assert drawn == [("pipe", "second")]


def test_embeddings_go_through_bytes_unchanged_so_a_seed_draws_the_same_picture():
    import torch

    embeds = torch.randn(1, 4, 6).to(torch.bfloat16)

    back = klein.embeds_from(klein.embeds_bytes(embeds))

    assert back.dtype == torch.bfloat16 and torch.equal(back, embeds)


@pytest.mark.parametrize("child", ["encoder", "drawer"])
def test_every_klein_request_runs_under_the_stack_dumper_of_dump_after(monkeypatch, child):
    """D76: a request that hangs prints where it waits, in the `[api]` terminal."""
    running = []

    @contextmanager
    def dumper(seconds):
        running.append(seconds)
        yield
        running.append("cancelled")

    monkeypatch.setattr(klein, "dump_stacks_after", dumper)
    monkeypatch.setattr(klein, "encode", lambda *args: running.append("encode") or [b"embeds"])
    monkeypatch.setattr(klein, "embeds_from", lambda data: data)
    monkeypatch.setattr(klein, "load_pipeline", lambda *args: running.append("load") or "pipe")
    requests, replies = queue.Queue(), queue.Queue()
    if child == "encoder":
        requests.put(klein.Encode(["a prompt"]))
        klein.encoder_worker(Path("snapshot"), "cpu", requests, replies)
    else:
        requests.put(klein.Load([b"embeds"]))
        requests.put(None)
        klein.drawer_worker(Path("snapshot"), Path("gguf"), "cpu", requests, replies)

    assert running == [klein.DUMP_AFTER, "encode" if child == "encoder" else "load", "cancelled"]
