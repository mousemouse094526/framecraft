"""The image adapter: the only module that imports diffusers (toon D34, ADR 0019).

A job runs two `spawn` child processes (ADR 0012), one after the other. `encoder_worker` loads
klein's text encoder alone, answers its one `Encode` with every prompt's embeddings as bytes, and
exits: the encoder's memory is the Mac's again before `drawer_worker` starts (D74 › 1; freed in the
same process, it wasn't). `drawer_worker`'s first request is `Load`, with those bytes: it loads the GGUF
transformer and the vae and says `Loaded`. Each `Draw` then answers `Drawn` with a PNG's bytes and
empties the GPU cache (D49); the backend thread writes every file. torch and diffusers are imported
in the children only, so the embeddings pass through the backend as `torch.save` bytes.
A request that runs past `DUMP_AFTER` prints the child's stacks to the backend's terminal (D76).
"""

import io
import multiprocessing
import traceback
from pathlib import Path
from typing import Literal, NamedTuple

from backend import checks
from backend.spoil_maker import llm
from backend.workers import Worker, dump_stacks_after, dump_stacks_on_signal, error_detail

GGUF_FILE = "flux-2-klein-4b-Q4_K_M.gguf"  # Q8_0 and Q6_K peak over 12 GB on a 16 GB Mac (D51)
STEPS = 4  # klein 4B is step-distilled (docs/library-notes/diffusers.md)
GUIDANCE = 1.0
REF_SIDE = 512  # a reference image's long side as it goes in (D49; D31 had 768)
# A request that runs this long prints the child's stacks, again each time, before the
# backend stops it at `draw_timeout` (D76): once on the Mac's 15 minutes, more on Windows.
DUMP_AFTER = 600

# Seconds one picture may take before its child is stopped (spec › Image job): the Mac's
# 15 minutes, and Windows at the same multiple as `llm.TIMEOUTS` starts from.
_MAC_DRAW = 900
DRAW_TIMEOUTS = {"darwin": _MAC_DRAW, "win32": _MAC_DRAW * llm.WINDOWS_START}


def draw_timeout() -> float:
    return DRAW_TIMEOUTS.get(checks.this_platform(), DRAW_TIMEOUTS["darwin"])


# Sent to the child. `None` asks it to exit.


class Encode(NamedTuple):
    """Every prompt of the job, encoded once before any picture (D34), by the encoder's child."""

    prompts: list[str]


class Load(NamedTuple):
    """The drawing child's first request: `Encoded.embeds`, which its `Draw`s name by index."""

    embeds: list[bytes]


class Draw(NamedTuple):
    index: int  # which of `Encode.prompts`
    ref_paths: list[Path]  # characters first, then the background (spec › คำสั่งภาพ)
    width: int
    height: int
    seed: int


# Sent back: the encoder's child says `Encoded` and exits. The drawing child says `Loaded` once
# the transformer is loaded, then one `Drawn` per `Draw`. A `WorkerError` instead of `Encoded`
# or `Loaded` ends the child; one instead of a `Drawn` answers that `Draw` only.


class Encoded(NamedTuple):
    embeds: list[bytes]  # `embeds_bytes` of each prompt's embeddings, in the order of `Encode.prompts`


class Loaded(NamedTuple):
    """The transformer and the vae are loaded."""


class Drawn(NamedTuple):
    png: bytes


class WorkerError(NamedTuple):
    code: Literal["model_failed"]
    detail: str  # "{exception type}: {message}", for the log


def start_encoder(snapshot_dir: Path, device: str) -> Worker:
    """Starts the encoder's child, as `start_drawer` does."""
    return _start(encoder_worker, (snapshot_dir, device), "framecraft-klein-encoder")


def start_drawer(snapshot_dir: Path, gguf_dir: Path, device: str) -> Worker:
    """Starts the drawing child with its queue of requests and its queue of replies.
    Fresh queues per child; daemonic, so the child dies with the backend."""
    return _start(drawer_worker, (snapshot_dir, gguf_dir, device), "framecraft-klein")


def _start(target, args: tuple, name: str) -> Worker:
    context = multiprocessing.get_context("spawn")
    requests, replies = context.Queue(), context.Queue()
    process = context.Process(target=target, args=(*args, requests, replies), daemon=True, name=name)
    process.start()
    return Worker(process, requests, replies)


def encoder_worker(snapshot_dir: Path, device: str, requests, replies) -> None:
    """The encoder's child: one `Encode`, answered, then it exits without waiting to be asked."""
    dump_stacks_on_signal()
    if (request := requests.get()) is None:
        return
    try:
        with dump_stacks_after(DUMP_AFTER):
            reply = Encoded(encode(snapshot_dir, device, request.prompts))
    except Exception as error:
        reply = _worker_error(error)
    replies.put(reply)


def drawer_worker(snapshot_dir: Path, gguf_dir: Path, device: str, requests, replies) -> None:
    """The drawing child: klein from the pinned snapshots, never from the Hub (ADR 0008)."""
    dump_stacks_on_signal()
    pipe, prompt_embeds = None, []
    while (request := requests.get()) is not None:
        try:
            with dump_stacks_after(DUMP_AFTER):
                if isinstance(request, Load):
                    prompt_embeds = [embeds_from(data) for data in request.embeds]
                    pipe = load_pipeline(snapshot_dir, gguf_dir, device)
                    reply = Loaded()
                else:
                    reply = Drawn(draw(pipe, prompt_embeds[request.index], request, device))
        except Exception as error:
            replies.put(_worker_error(error))
            if not isinstance(request, Draw):
                return
            continue  # one picture failed: the Image job counts it and asks for the next (spec › Image job)
        replies.put(reply)


def _worker_error(error: Exception) -> WorkerError:
    traceback.print_exc()  # the child shares the backend's terminal: the full error shows in [api]
    return WorkerError("model_failed", error_detail(error))


def embeds_bytes(embeds) -> bytes:
    """One prompt's embeddings as they cross the backend, dtype kept: the same seed draws the same picture."""
    import torch

    out = io.BytesIO()
    torch.save(embeds, out)
    return out.getvalue()


def embeds_from(data: bytes):
    import torch

    return torch.load(io.BytesIO(data), weights_only=True)


def encode(snapshot_dir: Path, device: str, prompts: list[str]) -> list[bytes]:
    """The text encoder on `device` straight away (`device_map`: no CPU copy first); each
    prompt's embeddings come back to the CPU, as `embeds_bytes` (trial-klein-mac › 1)."""
    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"no model snapshot at {snapshot_dir}")
    import torch
    from diffusers import Flux2KleinPipeline

    encoder = Flux2KleinPipeline.from_pretrained(
        str(snapshot_dir), transformer=None, vae=None, torch_dtype=torch.bfloat16, device_map=device, local_files_only=True
    )
    embeds = []
    with torch.no_grad():  # without it the graph stays and fills the GPU (trial-klein-mac › 5.1)
        for prompt in prompts:
            prompt_embeds, _ = encoder.encode_prompt(prompt, device=torch.device(device))
            embeds.append(embeds_bytes(prompt_embeds.to("cpu")))
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
