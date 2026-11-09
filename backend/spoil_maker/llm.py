"""The LLM adapter: the only module that imports mlx-vlm (spoil-maker D14).

`worker` runs in a `spawn` child process (ADR 0012) that loads Qwen once, says
`Ready`, then answers each `Generate` it is sent with `Generated`. The backend
thread owns the job, the timeouts and every file. mlx-vlm is imported inside the
child only, never when the backend imports this module. On Windows the child runs
`llm_windows.worker` instead, with the same messages (windows-launch D3).
"""

import multiprocessing
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Literal, NamedTuple

from backend import checks

# Sent to the child: one prompt, with one image or none. `None` asks it to exit.


class Generate(NamedTuple):
    prompt: str
    image: Path | None
    max_tokens: int
    temperature: float


# Sent back, in order: `Ready` once the model is loaded, then one `Generated` per
# `Generate`; a `WorkerError` instead ends the child.


class Ready(NamedTuple):
    pass


class Generated(NamedTuple):
    text: str


class WorkerError(NamedTuple):
    code: Literal["model_failed"]
    detail: str  # "{exception type}: {message}", for the log


class Timeouts(NamedTuple):
    """Seconds one answer of each step may take before its child is stopped
    (spec › ค่าการสร้างข้อความ, windows-launch D7, D12). Loading has none."""

    describe: float  # one Shot
    write: float  # one try at the script
    polish: float  # one try at polishing
    pick: float  # one sentence's Shots


# Windows starts at the Mac's × 5; the trial on a Windows card (windows-launch ticket 03)
# measures each step and replaces these with max(this, longest × 3 in whole minutes) (D7).
TIMEOUTS = {
    "darwin": Timeouts(describe=60, write=600, polish=300, pick=60),
    "win32": Timeouts(describe=300, write=3000, polish=1500, pick=300),
}


def timeouts() -> Timeouts:
    """This OS's timeouts, read when a job starts; any OS but Windows gets the Mac's."""
    return TIMEOUTS.get(checks.this_platform(), TIMEOUTS["darwin"])


def worker_for(sys_platform: str) -> Callable:
    """The child of this OS: transformers on Windows, mlx-vlm elsewhere (windows-launch D3)."""
    if sys_platform == "win32":
        # Here, not at the top: llm_windows imports this module, so a top-level import is circular.
        from backend.spoil_maker import llm_windows

        return llm_windows.worker
    return worker


def start_worker(snapshot_dir: Path):
    """Starts this OS's child; returns it with the queue of requests and the queue of replies.

    Fresh queues per child: `terminate()` may corrupt a queue it was using.
    Daemonic, so the child dies with the backend.
    """
    context = multiprocessing.get_context("spawn")
    requests, replies = context.Queue(), context.Queue()
    process = context.Process(
        target=worker_for(checks.this_platform()),
        args=(snapshot_dir, requests, replies),
        daemon=True,
        name="framecraft-llm",
    )
    process.start()
    return process, requests, replies


def worker(snapshot_dir: Path, requests, replies) -> None:
    """The Mac child process: mlx-vlm's model from the pinned snapshot."""
    serve_requests(load, generate, snapshot_dir, requests, replies)


def serve_requests(load: Callable, generate: Callable, snapshot_dir: Path, requests, replies) -> None:
    """A child's whole life, whatever runs the model: `load` it from the pinned snapshot,
    say `Ready`, then `generate` an answer to each request until `None`; any error is a
    `WorkerError` that ends it."""
    try:
        model, processor = load(snapshot_dir)
    except Exception as error:
        _send_error(replies, error)
        return
    replies.put(Ready())
    while (request := requests.get()) is not None:
        try:
            text = generate(model, processor, request)
        except Exception as error:
            _send_error(replies, error)
            return
        replies.put(Generated(text))


def load(snapshot_dir: Path):
    """mlx-vlm downloads when the path isn't a folder, so a missing one raises instead
    (docs/library-notes/mlx-vlm.md, ADR 0002)."""
    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"no model snapshot at {snapshot_dir}")
    from mlx_vlm import load as load_model

    return load_model(str(snapshot_dir))


def generate(model, processor, request: Generate) -> str:
    """Thinking off for every step (spoil-maker D51); `num_images` matches the images sent."""
    from mlx_vlm import generate as generate_text
    from mlx_vlm.prompt_utils import apply_chat_template

    images = [str(request.image)] if request.image else None
    prompt = apply_chat_template(
        processor, model.config, request.prompt, num_images=len(images or []), enable_thinking=False
    )
    result = generate_text(
        model, processor, prompt, image=images, max_tokens=request.max_tokens, temperature=request.temperature
    )
    return result.text


def _send_error(replies, error: Exception) -> None:
    traceback.print_exc()  # the child shares the backend's terminal: the full error shows in [api]
    replies.put(WorkerError("model_failed", f"{type(error).__name__}: {error}"))
