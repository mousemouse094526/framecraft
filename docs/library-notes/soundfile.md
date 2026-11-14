# soundfile

**Kind:** library

**Version:** 0.14.0 (bundles libsndfile; the docs site shows 0.13.1, the latest page published)

**Docs:** https://python-soundfile.readthedocs.io/en/latest/

## Best practices

- `soundfile.read(file, dtype=...)` returns `(data, samplerate)`; mono is a 1-D array, more channels are `frames × channels`; `always_2d=True` forces 2-D — [read](https://python-soundfile.readthedocs.io/en/latest/#soundfile.read)
- The default `dtype` is `'float64'`: pass `dtype="float32"` to mix in float32 — [read](https://python-soundfile.readthedocs.io/en/latest/#soundfile.read)
- `soundfile.write(file, data, samplerate, subtype=None, format=None)` takes the format from the file's extension; WAV's default subtype is `PCM_16`. Data must be float64, float32, int32 or int16 and is converted to the subtype — [write](https://python-soundfile.readthedocs.io/en/latest/#soundfile.write)
- A file-like object (`io.BytesIO`) has no extension: pass `format="WAV"` (the source raises `TypeError` when it can't tell the format) — [write](https://python-soundfile.readthedocs.io/en/latest/#soundfile.write), [source](https://python-soundfile.readthedocs.io/en/latest/_modules/soundfile.html)
- FLAC reads and writes; its write subtypes are `PCM_16`, `PCM_24`, `PCM_S8` — [available_subtypes](https://python-soundfile.readthedocs.io/en/latest/#soundfile.available_subtypes)
- `soundfile.info(file)` gives `samplerate`, `channels`, `frames`, `duration`, `subtype` without reading the samples — [info](https://python-soundfile.readthedocs.io/en/latest/#soundfile.info)
- **Avoid:** relying on how float becomes `PCM_16`: the docs only say libsndfile clips (every open sets `SFC_SET_CLIPPING`) and don't state the rounding — [source](https://python-soundfile.readthedocs.io/en/latest/_modules/soundfile.html)

## Pattern

```python
data, rate = soundfile.read(path, dtype="float32")  # one sample, read once per job
soundfile.write(buffer, pcm16, rate, subtype="PCM_16", format="WAV")  # int16 made with numpy
```

## Traps

- `write` truncates an existing file — [write](https://python-soundfile.readthedocs.io/en/latest/#soundfile.write)
- Wheels carry their own libsndfile (1.2.2) and prefer it over a system one — [News](https://python-soundfile.readthedocs.io/en/latest/#news)

## Sources

- [python-soundfile](https://python-soundfile.readthedocs.io/en/latest/) — read, write, info, subtypes, news (accessed 2026-11-13)
- [soundfile source](https://python-soundfile.readthedocs.io/en/latest/_modules/soundfile.html) — format from extension, clipping (accessed 2026-11-13)
