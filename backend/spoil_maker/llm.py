"""The LLM adapter: the only module that imports mlx-vlm (spoil-maker D14).

`worker` runs in a `spawn` child process (ADR 0012) that loads Qwen once, says
`Ready`, then answers each `Generate` it is sent with `Generated`. The backend
thread owns the job, the timeouts and every file. mlx-vlm is imported inside the
child only, never when the backend imports this module. Another backend (Windows,
feature windows-launch) keeps these messages and swaps `worker`.
"""

import multiprocessing
import traceback
from pathlib import Path
from typing import Literal, NamedTuple

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


def start_worker(snapshot_dir: Path):
    """Starts the child; returns it with the queue of requests and the queue of replies.

    Fresh queues per child: `terminate()` may corrupt a queue it was using.
    Daemonic, so the child dies with the backend.
    """
    context = multiprocessing.get_context("spawn")
    requests, replies = context.Queue(), context.Queue()
    process = context.Process(
        target=worker,
        args=(snapshot_dir, requests, replies),
        daemon=True,
        name="framecraft-llm",
    )
    process.start()
    return process, requests, replies


def worker(snapshot_dir: Path, requests, replies) -> None:
    """The child process: load the model from the pinned snapshot, then answer requests."""
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
