# omnivoice

**Kind:** library

**Version:** 0.2.1 (model `k2-fsa/OmniVoice` `c5fdb5c`, torch 2.8.0)

**Docs:** https://github.com/k2-fsa/OmniVoice

## Best practices

- Load once with `OmniVoice.from_pretrained(path, device_map=…, dtype=…)` and reuse the model for every sentence — [README](https://github.com/k2-fsa/OmniVoice)
- Voice design: `generate(text=…, instruct="female, young adult, low pitch")`. Each item is one of the listed values, comma + space separated; an unknown item raises `ValueError` with a suggestion — [models/omnivoice.py `_resolve_instruct`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- Voice design and auto pick a new voice on every call; to keep one voice, make a clone prompt from one generated sentence: `create_voice_clone_prompt(ref_audio=(waveform, sample_rate), ref_text=text)`, then `generate(text, voice_clone_prompt=prompt)` — [README](https://github.com/k2-fsa/OmniVoice)
- `VoiceClonePrompt.save(path)` / `VoiceClonePrompt.load(path)` store the prompt as a plain dict (`torch.load(weights_only=True)` safe, CPU tensors, `format_version` 1) — [models/omnivoice.py `VoiceClonePrompt`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- `generate` takes `speed` (> 1 faster) and generation-config keywords such as `num_step` (default 32); `duration` overrides `speed` — [models/omnivoice.py `generate`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- `generate` returns a list of 1-D float `np.ndarray`, one per text, at `model.sampling_rate` (24 000 Hz) — [models/omnivoice.py `generate`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- Pass `language="th"` (or `"Thai"`): an unknown language falls back to language-agnostic mode with only a warning — [models/omnivoice.py `_resolve_language`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- Reference audio of 3–10 s works best — [README](https://github.com/k2-fsa/OmniVoice)
- **Avoid:** `normalize_text=True` for Thai: it needs `num2words`, which isn't installed — [models/omnivoice.py `generate`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)

## Pattern

```python
def design(snapshot_dir: Path, instruct: str, text: str, speed: float):
    import torch
    from omnivoice import OmniVoice

    model = OmniVoice.from_pretrained(str(snapshot_dir), device_map="mps", dtype=torch.float16)
    locked = model.generate(text=text, language="th", instruct=instruct, num_step=16)[0]
    prompt = model.create_voice_clone_prompt(ref_audio=(torch.from_numpy(locked), model.sampling_rate), ref_text=text)
    sample = model.generate(text=text, language="th", voice_clone_prompt=prompt, speed=speed, num_step=16)[0]
    return prompt, sample
```

Follows [README](https://github.com/k2-fsa/OmniVoice).

## Traps

- `from_pretrained` calls `snapshot_download` when the path isn't a folder, and loads `eustlb/higgs-audio-v2-tokenizer` from the Hub when the snapshot has no `audio_tokenizer/`: a missing snapshot becomes a network call. Check the folder first — [models/omnivoice.py `_resolve_model_path`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- The audio tokenizer runs on CPU when the model is on MPS (it has more than 65 536 output channels) — [models/omnivoice.py `from_pretrained`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- `create_voice_clone_prompt` without `ref_text` loads an ASR model on the fly; always pass the text — [models/omnivoice.py `create_voice_clone_prompt`](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/models/omnivoice.py)
- Importing `omnivoice` imports torch, torchaudio and transformers: seconds, so only inside the child process — [omnivoice/__init__.py](https://github.com/k2-fsa/OmniVoice/blob/main/omnivoice/__init__.py)
- Numbers are read wrong in Thai; write them as words first — [tts-trial.md › รอบ 2](../features/spoil-maker/tts-trial.md)

## Sources

- [k2-fsa/OmniVoice README](https://github.com/k2-fsa/OmniVoice) — modes, `instruct`, clone prompt, 3–10 s reference (accessed 2026-11-02)
- [omnivoice 0.2.1 source](https://github.com/k2-fsa/OmniVoice/tree/main/omnivoice) — `generate`, `create_voice_clone_prompt`, `VoiceClonePrompt`, `_resolve_instruct`, `_resolve_language`, `from_pretrained`; read from the installed package (accessed 2026-11-02)
