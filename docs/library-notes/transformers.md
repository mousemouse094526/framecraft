# transformers

**Kind:** library

**Version:** 5.21.0 (torch 2.8.0, bitsandbytes 0.50.2 on Windows)

**Docs:** https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines

## Best practices

- `pipeline("automatic-speech-recognition", model=<local folder>, device=..., dtype=...)` loads from a folder with no network call; set `device` explicitly, the docs disagree on what `None` picks — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- Pass a 1-D `np.float32` array at the model's sampling rate (16 kHz for Whisper); the pipeline doesn't check the rate, a wrong one silently degrades results — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- A `str` or `bytes` input goes through `ffmpeg_read`, which needs `ffmpeg` on PATH; an array skips it — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- Whisper with `return_timestamps=True` returns `{"text", "chunks": [{"timestamp": (start, end), "text"}]}` in seconds — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- An array longer than 30 s without `chunk_length_s` goes to Whisper's own sequential long-form `generate` — `pipelines/automatic_speech_recognition.py` `preprocess`, v5.21.0
- **Avoid:** `chunk_length_s` with Whisper; the pipeline warns it is "very experimental" for seq2seq models — `automatic_speech_recognition.py:306`, v5.21.0

- Qwen3.5 VLM: `AutoModelForImageTextToText` maps `qwen3_5` to `Qwen3_5ForConditionalGeneration`; load it and `AutoProcessor` with `local_files_only=True` so a missing file raises instead of downloading — `models/auto/modeling_auto.py:1211`, v5.21.0
- 4-bit: `quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16, llm_int8_skip_modules=[...])`; a given `llm_int8_skip_modules` replaces the default skip list, so name `lm_head` yourself — [bitsandbytes quantization](https://huggingface.co/docs/transformers/v5.21.0/en/quantization/bitsandbytes), `quantizers/base.py` `get_modules_to_not_convert`, v5.21.0
- `processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt", enable_thinking=False)`: an image is a content block `{"type": "image", "path": ...}`; a kwarg the jinja template reads (`enable_thinking`) goes to the template, others to the processor — `processing_utils.py` `apply_chat_template`, v5.21.0
- `generate` returns prompt + new tokens; slice off `input_ids.shape[1]` and `processor.batch_decode(..., skip_special_tokens=True)` — [Generation](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/text_generation)

## Pattern

```python
asr = pipeline("automatic-speech-recognition", model=str(snapshot), device="mps", dtype=torch.float32)
out = asr(audio, return_timestamps=True, return_language=True, batch_size=1)
lines = [(c["timestamp"][0], c["timestamp"][1], c["text"]) for c in out["chunks"]]
language = out["chunks"][0]["language"] if out["chunks"] else None
```

## Traps

- `llm_int8_skip_modules` entries match a module's full name from its start or as a suffix (`quantizers_utils.should_convert_module`): `"visual"` does **not** skip `model.visual.blocks.0.attn.qkv` in Qwen3.5, `"model.visual"` does; `"lm_head"` matches `lm_head` — checked with the installed function, 2026-11-06

Checked against the installed code and real runs on an M-series Mac, not in the docs:

- `return_language=True` puts the language **name** (`"english"`, `"thai"`) in every `chunks[i]["language"]`, not an ISO code and not at the top level; map it with `models.whisper.tokenization_whisper.TO_LANGUAGE_CODE`. It reads the first batch item only, so keep `batch_size` 1
- Whisper large-v3-turbo with `float16` on `mps` returns garbage (`"The!!! I! THE!"`); `float32` is correct
- The last chunk's end can be `None` ("Whisper did not predict an ending timestamp"), and an end can run past the array's length (298.5 → 328.5 on a 300 s array); clamp to the length
- Over music with no speech, long-form emits one invented line per 30 s window (`"THE END"`, `"Thank you for listening."`, timestamp `(0.0, 29.98)`); `no_speech_threshold` with `logprob_threshold` doesn't remove them
- Temperature fallback (`temperature` as a tuple) crashes in 5.21.0: `'EncoderDecoderCache' object has no attribute 'layers'`; `logprob_threshold` without `temperature=0.0` raises `TypeError` in `_retrieve_avg_logprobs`

## Sources

- `.venv/lib/python3.12/site-packages/transformers/quantizers/quantizers_utils.py`, `quantizers/base.py`, `processing_utils.py`, `models/qwen3_5/modeling_qwen3_5.py` v5.21.0 — skip-module matching, chat template kwargs, `model.visual` (read 2026-11-06)
- [bitsandbytes quantization v5.21.0](https://huggingface.co/docs/transformers/v5.21.0/en/quantization/bitsandbytes) — `BitsAndBytesConfig` nf4 (accessed 2026-11-06)

- [Pipelines v5.21.0](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines) — ASR inputs, outputs, `return_timestamps` (accessed 2026-10-29)
- `.venv/lib/python3.12/site-packages/transformers/pipelines/automatic_speech_recognition.py` v5.21.0 — `preprocess`, `_forward`, `return_language` (read 2026-10-29)
