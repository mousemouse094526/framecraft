# diffusers

**Kind:** library

**Version:** 0.42.1

**Docs:** https://huggingface.co/docs/diffusers/v0.42.1/en/index

## Best practices

- `Flux2KleinPipeline(image=[...], prompt_embeds=..., width, height, num_inference_steps=4, guidance_scale=1.0)`: a list of PIL images is the reference set; klein 4B is step-distilled (`is_distilled`), so `guidance_scale` above 1 is ignored and no negative embeds are made — [Flux2 pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/api/pipelines/flux2)
- `width` and `height` must be multiples of 16 (`vae_scale_factor * 2`), else the pipeline resizes with a warning — [pipeline_flux2_klein.py v0.42.1](https://github.com/huggingface/diffusers/blob/v0.42.1/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py)
- A reference image over 1024×1024 pixels is shrunk to that area by the pipeline; one under 64 px a side or more than 8:1 raises `ValueError` (`check_image_input`) — same file and `flux2/image_processor.py`
- `encode_prompt(prompt, device)` returns `(prompt_embeds, text_ids)` and is callable on its own; pass `prompt_embeds` instead of `prompt` to the call, never both (`check_inputs` raises) — same file
- A component passed as `None` to `from_pretrained` (`transformer=None`, `text_encoder=None, tokenizer=None`) is not loaded: one pipeline encodes, another denoises — [Loading pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/using-diffusers/loading)
- GGUF: `Flux2Transformer2DModel.from_single_file(path, config=..., quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16), torch_dtype=torch.bfloat16)`; needs the `gguf` package — [GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf)
- `local_files_only=True` on every `from_pretrained` and `from_single_file`, so nothing reaches the Hub at runtime — [Loading pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/using-diffusers/loading)
- **Avoid:** `from_pretrained` to CPU then `.to("mps")` for the text encoder: two copies at once; load it with `device_map` — [Loading big models](https://huggingface.co/docs/diffusers/v0.42.1/en/tutorials/inference_with_big_models)

## Pattern

```python
# inside the klein child only
with torch.no_grad():
    embeds, _ = encoder.encode_prompt(prompt, device=torch.device("mps"))
image = pipe(image=refs or None, prompt_embeds=embeds, width=576, height=1024,
             num_inference_steps=4, guidance_scale=1.0, generator=torch.Generator("cpu").manual_seed(seed)).images[0]
```

Follows [Flux2 pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/api/pipelines/flux2).

## Traps

- `from_single_file` on the unsloth GGUF without `config=` looks up `black-forest-labs/FLUX.2-dev` from the file's metadata and fails with `OSError`; pass the local `transformer/` folder — [trial-klein-mac › 3](../features/toon/trial-klein-mac-2026-11-09.md)
- `encode_prompt` outside `torch.no_grad()` keeps the graph: 12.6 GB and `MPS backend out of memory` after a few prompts — [trial-klein-mac › 5](../features/toon/trial-klein-mac-2026-11-09.md)
- `diffusers` does not pull in `gguf`; install it beside — [GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf)

## Sources

- [Flux2 pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/api/pipelines/flux2) — `Flux2KleinPipeline`, references, steps (accessed 2026-11-09)
- [pipeline_flux2_klein.py v0.42.1](https://github.com/huggingface/diffusers/blob/v0.42.1/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py) — `encode_prompt`, `check_inputs`, image checks; read in the installed package (accessed 2026-11-09)
- [GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf) — `from_single_file` with `GGUFQuantizationConfig` (accessed 2026-11-09)
- [Loading pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/using-diffusers/loading) — components as `None`, `local_files_only` (accessed 2026-11-09)
- [Loading big models](https://huggingface.co/docs/diffusers/v0.42.1/en/tutorials/inference_with_big_models) — `device_map` (accessed 2026-11-09)
