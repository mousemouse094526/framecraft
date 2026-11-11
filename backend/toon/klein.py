"""The image adapter: the only module that imports diffusers (toon D34, ADR 0019).

`worker` runs in a `spawn` child process (ADR 0012). Its first request is `Encode`: it
loads klein's text encoder alone, encodes every prompt under `torch.no_grad()`, frees the
encoder, then loads the GGUF transformer and the vae — the two never sit in memory together
on a 16 GB Mac (D34) — and says `Encoded`. Each `Draw` then answers `Drawn` with a PNG's
bytes and empties the GPU cache (D49); the backend thread writes every file. torch and diffusers are imported in the child only.
A request that runs past `DUMP_AFTER` prints the child's stacks to the backend's terminal (D76).
"""

import io
import multiprocessing
import traceback
from pathlib import Path
from typing import Literal, NamedTuple

from backend import checks
from backend.spoil_maker import llm
from backend.workers import Worker, dump_stacks_after, dump_stacks_on_signal

GGUF_FILE = "flux-2-klein-4b-Q4_K_M.gguf"  # Q8_0 and Q6_K peak over 12 GB on a 16 GB Mac (D51)
STEPS = 4  # klein 4B is step-distilled (docs/library-notes/diffusers.md)
GUIDANCE = 1.0
REF_SIDE = 512  # a reference image's long side as it goes in (D49; D31 had 768)
# A request that runs this long prints the child's stacks, again each time, before the
# backend stops it at `draw_timeout` (D76): the 15 minutes leave room for one or two.
DUMP_AFTER = 600

# Seconds one picture may take before its child is stopped (spec › Image job): the Mac's
# 15 minutes, and Windows at the same multiple as `llm.TIMEOUTS` starts from.
_MAC_DRAW = 900
DRAW_TIMEOUTS = {"darwin": _MAC_DRAW, "win32": _MAC_DRAW * llm.WINDOWS_START}


def draw_timeout() -> float:
    return DRAW_TIMEOUTS.get(checks.this_platform(), DRAW_TIMEOUTS["darwin"])


# Sent to the child. `None` asks it to exit.


class Encode(NamedTuple):
    """Every prompt of the job, encoded once before any picture (D34)."""

    prompts: list[str]


class Draw(NamedTuple):
    index: int  # which of `Encode.prompts`
    ref_paths: list[Path]  # characters first, then the background (spec › คำสั่งภาพ)
    width: int
    height: int
    seed: int


# Sent back, in order: `Encoded` once the transformer is loaded, then one `Drawn` per
# `Draw`. A `WorkerError` instead of `Encoded` ends the child; one instead of a `Drawn`
# answers that `Draw` only.


class Encoded(NamedTuple):
    count: int


class Drawn(NamedTuple):
    png: bytes


class WorkerError(NamedTuple):
    code: Literal["model_failed"]
    detail: str  # "{exception type}: {message}", for the log


def start_worker(snapshot_dir: Path, gguf_dir: Path, device: str) -> Worker:
    """Starts the child with its queue of requests and its queue of replies.
    Fresh queues per child; daemonic, so the child dies with the backend."""
    context = multiprocessing.get_context("spawn")
    requests, replies = context.Queue(), context.Queue()
    process = context.Process(
        target=worker,
        args=(snapshot_dir, gguf_dir, device, requests, replies),
        daemon=True,
        name="framecraft-klein",
    )
    process.start()
    return Worker(process, requests, replies)


def worker(snapshot_dir: Path, gguf_dir: Path, device: str, requests, replies) -> None:
    """The child process: klein from the pinned snapshots, never from the Hub (ADR 0008)."""
    dump_stacks_on_signal()
    pipe, embeds = None, []
    while (request := requests.get()) is not None:
        try:
            with dump_stacks_after(DUMP_AFTER):
                if isinstance(request, Encode):
                    embeds = encode(snapshot_dir, device, request.prompts)
                    pipe = load_pipeline(snapshot_dir, gguf_dir, device)
                    reply = Encoded(len(embeds))
                else:
                    reply = Drawn(draw(pipe, embeds[request.index], request, device))
        except Exception as error:
            traceback.print_exc()  # the child shares the backend's terminal: the full error shows in [api]
            replies.put(WorkerError("model_failed", f"{type(error).__name__}: {error}"))
            if not isinstance(request, Draw):
                return
            continue  # one picture failed: the Image job counts it and asks for the next (spec › Image job)
        replies.put(reply)


def encode(snapshot_dir: Path, device: str, prompts: list[str]) -> list:
    """The text encoder on `device` straight away (`device_map`: no CPU copy first), then
    freed; the embeddings wait on the CPU (trial-klein-mac › 1)."""
    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"no model snapshot at {snapshot_dir}")
    import gc

    import torch
    from diffusers import Flux2KleinPipeline

    encoder = Flux2KleinPipeline.from_pretrained(
        str(snapshot_dir), transformer=None, vae=None, torch_dtype=torch.bfloat16, device_map=device, local_files_only=True
    )
    embeds = []
    with torch.no_grad():  # without it the graph stays and fills the GPU (trial-klein-mac › 5.1)
        for prompt in prompts:
            prompt_embeds, _ = encoder.encode_prompt(prompt, device=torch.device(device))
            embeds.append(prompt_embeds.to("cpu"))
    del encoder
    gc.collect()
    _empty_cache(torch, device)
    return embeds


def load_pipeline(snapshot_dir: Path, gguf_dir: Path, device: str):
    """The GGUF transformer with the local `transformer/config.json` — without `config=`
    diffusers looks up another repo on the Hub (docs/library-notes/diffusers.md) — and the vae."""
    import torch
    from diffusers import Flux2KleinPipeline, Flux2Transformer2DModel, GGUFQuantizationConfig

    transformer = Flux2Transformer2DModel.from_single_file(
        str(gguf_dir / GGUF_FILE),
        config=str(snapshot_dir / "transformer"),
        quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
        torch_dtype=torch.bfloat16,
        local_files_only=True,
    )
    pipe = Flux2KleinPipeline.from_pretrained(
        str(snapshot_dir),
        transformer=transformer,
        text_encoder=None,
        tokenizer=None,
        torch_dtype=torch.bfloat16,
        local_files_only=True,
    )
    return pipe.to(device)


def draw(pipe, prompt_embeds, request: Draw, device: str) -> bytes:
    import torch
    from PIL import Image

    refs = []
    for path in request.ref_paths:
        with Image.open(path) as opened:
            image = opened.convert("RGB")
        image.thumbnail((REF_SIDE, REF_SIDE), Image.Resampling.LANCZOS)
        refs.append(image)
    with torch.no_grad():
        image = pipe(
            image=refs or None,
            prompt_embeds=prompt_embeds.to(device),
            width=request.width,
            height=request.height,
            num_inference_steps=STEPS,
            guidance_scale=GUIDANCE,
            generator=torch.Generator("cpu").manual_seed(request.seed),
        ).images[0]
    _empty_cache(torch, device)  # without it the peak climbs picture by picture (D49)
    out = io.BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


def _empty_cache(torch, device: str) -> None:
    if device == "mps":
        torch.mps.empty_cache()
    elif device == "cuda":
        torch.cuda.empty_cache()
