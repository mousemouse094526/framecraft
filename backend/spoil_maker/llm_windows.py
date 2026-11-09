"""Qwen on Windows: transformers runs `Qwen/Qwen3.5-9B` in 4 bits on the NVIDIA card
(windows-launch D3, D10). The only module that imports transformers' VLM classes and
`BitsAndBytesConfig` (which loads bitsandbytes), inside the child process only (ADR 0012);
`llm` starts it and owns the messages it answers.
"""

import sys
from collections import Counter
from pathlib import Path

from backend.spoil_maker.llm import Generate, serve_requests

DEVICE = "cuda:0"
# Left unquantized (windows-launch D12). A name matches a module's full name from its
# start, so "visual" alone would miss Qwen3.5's `model.visual.*` (docs/library-notes/transformers.md, D16).
SKIP_MODULES = ["model.visual", "lm_head"]


def worker(snapshot_dir: Path, requests, replies) -> None:
    """The Windows child process: transformers' model from the pinned snapshot."""
    serve_requests(load, generate, snapshot_dir, requests, replies)


def load(snapshot_dir: Path):
    """A path that isn't a folder would be read as a Hub repo id, so a missing snapshot
    raises here, naming the path, before transformers is imported (ADR 0008)."""
    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"no model snapshot at {snapshot_dir}")
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

    # bfloat16 only: Qwen's target cards (sm_80 and up) all have it (windows-launch D10).
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        llm_int8_skip_modules=SKIP_MODULES,
    )
    processor = AutoProcessor.from_pretrained(snapshot_dir, local_files_only=True)
    model = AutoModelForImageTextToText.from_pretrained(
        snapshot_dir,
        local_files_only=True,
        device_map=DEVICE,
        dtype=torch.bfloat16,
        quantization_config=quantization,
    )
    _log_load_report(model, torch)
    return model, processor


def _log_load_report(model, torch) -> None:
    """Prints to the `[api]` terminal what the Windows trial (windows-launch ticket 03)
    records: the plain `Linear` layers left unquantized, counted by their first two name
    parts (`model.visual`, `lm_head`; anything else means the skip list missed), and the
    card's peak memory. `torch` is passed in: it is imported only inside the child."""
    kept = Counter(
        ".".join(name.split(".")[:2]) for name, module in model.named_modules() if type(module) is torch.nn.Linear
    )
    listed = ", ".join(f"{prefix} ({count})" for prefix, count in kept.items()) or "none"
    print(f"[qwen] not quantized: {listed}", file=sys.stderr, flush=True)
    print(f"[qwen] VRAM after load: {torch.cuda.max_memory_allocated(DEVICE) / 2**30:.1f} GiB", file=sys.stderr, flush=True)


def generate(model, processor, request: Generate) -> str:
    """Thinking off for every step (spoil-maker D51); temperature 0 is greedy."""
    content = [{"type": "image", "path": str(request.image)}] if request.image else []
    content.append({"type": "text", "text": request.prompt})
    inputs = processor.apply_chat_template(
        [{"role": "user", "content": content}],
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        enable_thinking=False,
    ).to(model.device)
    sampling = {"do_sample": True, "temperature": request.temperature} if request.temperature > 0 else {"do_sample": False}
    output = model.generate(**inputs, max_new_tokens=request.max_tokens, **sampling)
    new_tokens = output[:, inputs["input_ids"].shape[1] :]
    return processor.batch_decode(new_tokens, skip_special_tokens=True)[0]
