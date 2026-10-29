# transformers

**Kind:** library

**Version:** 5.21.0 (torch 2.8.0)

**Docs:** https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines

## Best practices

- `pipeline("automatic-speech-recognition", model=<local folder>, device=..., dtype=...)` loads from a folder with no network call; set `device` explicitly, the docs disagree on what `None` picks — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- Pass a 1-D `np.float32` array at the model's sampling rate (16 kHz for Whisper); the pipeline doesn't check the rate, a wrong one silently degrades results — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- A `str` or `bytes` input goes through `ffmpeg_read`, which needs `ffmpeg` on PATH; an array skips it — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- Whisper with `return_timestamps=True` returns `{"text", "chunks": [{"timestamp": (start, end), "text"}]}` in seconds — [Pipelines](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines)
- An array longer than 30 s without `chunk_length_s` goes to Whisper's own sequential long-form `generate` — `pipelines/automatic_speech_recognition.py` `preprocess`, v5.21.0
- **Avoid:** `chunk_length_s` with Whisper; the pipeline warns it is "very experimental" for seq2seq models — `automatic_speech_recognition.py:306`, v5.21.0

## Pattern

```python
asr = pipeline("automatic-speech-recognition", model=str(snapshot), device="mps", dtype=torch.float32)
out = asr(audio, return_timestamps=True, return_language=True, batch_size=1)
lines = [(c["timestamp"][0], c["timestamp"][1], c["text"]) for c in out["chunks"]]
language = out["chunks"][0]["language"] if out["chunks"] else None
```

## Traps

Checked against the installed code and real runs on an M-series Mac, not in the docs:

- `return_language=True` puts the language **name** (`"english"`, `"thai"`) in every `chunks[i]["language"]`, not an ISO code and not at the top level; map it with `models.whisper.tokenization_whisper.TO_LANGUAGE_CODE`. It reads the first batch item only, so keep `batch_size` 1
- Whisper large-v3-turbo with `float16` on `mps` returns garbage (`"The!!! I! THE!"`); `float32` is correct
- The last chunk's end can be `None` ("Whisper did not predict an ending timestamp"), and an end can run past the array's length (298.5 → 328.5 on a 300 s array); clamp to the length
- Over music with no speech, long-form emits one invented line per 30 s window (`"THE END"`, `"Thank you for listening."`, timestamp `(0.0, 29.98)`); `no_speech_threshold` with `logprob_threshold` doesn't remove them
- Temperature fallback (`temperature` as a tuple) crashes in 5.21.0: `'EncoderDecoderCache' object has no attribute 'layers'`; `logprob_threshold` without `temperature=0.0` raises `TypeError` in `_retrieve_avg_logprobs`

## Sources

- [Pipelines v5.21.0](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines) — ASR inputs, outputs, `return_timestamps` (accessed 2026-10-29)
- `.venv/lib/python3.12/site-packages/transformers/pipelines/automatic_speech_recognition.py` v5.21.0 — `preprocess`, `_forward`, `return_language` (read 2026-10-29)
