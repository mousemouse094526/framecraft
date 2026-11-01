# mlx-vlm

**Kind:** library

**Version:** 0.7.11 (mlx 0.32.4), Apple Silicon only

**Docs:** https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11

## Best practices

- Load once, then reuse the pair for every prompt: `model, processor = load(path)` and `config = load_config(path)` (or `model.config`) — [README v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11)
- Build every prompt with `apply_chat_template(processor, config, prompt, num_images=n)`; `num_images` must match the images passed to `generate`, or the image tokens are missing — [README v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11)
- `generate(model, processor, prompt, image=[path], max_tokens=…, temperature=…)` returns a `GenerationResult`; the text is `.text`, and `.prompt_tokens`, `.generation_tokens`, `.peak_memory` (GB) come with it — [generate/common.py v0.7.11](https://github.com/Blaizzy/mlx-vlm/blob/v0.7.11/mlx_vlm/generate/common.py)
- `max_tokens` defaults to 100 and `temperature` to the checkpoint's default; pass both explicitly — [generate/dispatch.py v0.7.11](https://github.com/Blaizzy/mlx-vlm/blob/v0.7.11/mlx_vlm/generate/dispatch.py)
- A long prompt that runs out of GPU memory goes through with a smaller `prefill_step_size` (a `generate` keyword) — [generate/types.py v0.7.11](https://github.com/Blaizzy/mlx-vlm/blob/v0.7.11/mlx_vlm/generate/types.py)

## Pattern

```python
def describe(snapshot_dir: Path, frames: list[Path]) -> list[str]:
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template

    model, processor = load(str(snapshot_dir))
    prompt = apply_chat_template(processor, model.config, PROMPT, num_images=1, enable_thinking=False)
    return [
        generate(model, processor, prompt, image=[str(frame)], max_tokens=80, temperature=0.0).text
        for frame in frames
    ]
```

Follows [README v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11).

## Traps

- `load()` downloads from the Hub when the path doesn't exist on disk: a missing snapshot folder becomes a network call. Check the folder first — [utils.py `get_model_path` v0.7.11](https://github.com/Blaizzy/mlx-vlm/blob/v0.7.11/mlx_vlm/utils.py)
- `apply_chat_template` sets `enable_thinking=False` by itself when the template knows the keyword; passing it explicitly keeps the intent visible and survives a changed default — [prompt_utils.py v0.7.11](https://github.com/Blaizzy/mlx-vlm/blob/v0.7.11/mlx_vlm/prompt_utils.py)
- Importing `mlx_vlm` imports `mlx`, `transformers` and `PIL`: it takes seconds and must stay inside the child process — [utils.py v0.7.11](https://github.com/Blaizzy/mlx-vlm/blob/v0.7.11/mlx_vlm/utils.py)
- `generate` has no timeout; a stuck generation is stopped only by ending the process — [generate/dispatch.py v0.7.11](https://github.com/Blaizzy/mlx-vlm/blob/v0.7.11/mlx_vlm/generate/dispatch.py)

## Sources

- [mlx-vlm README v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11) — `load`, `apply_chat_template`, `generate` with images (accessed 2026-11-02)
- [mlx_vlm source v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11/mlx_vlm) — `get_model_path`, `GenerateKwargs`, `GenerationResult`, thinking default; read from the installed package (accessed 2026-11-02)
