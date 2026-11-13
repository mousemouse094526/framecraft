# numpy

**Kind:** library

**Version:** 2.5.4

**Docs:** https://numpy.org/doc/2.5/

## Best practices

- `np.frombuffer(data, dtype=np.float32)` views raw bytes (ffmpeg `-f f32le` output) as an array without copying — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)

- `np.add.at(target, indices, values)` adds without buffering, so repeated indices all add; `target[a:b] += values` on a slice is the plain way when ranges are contiguous — [numpy.add](https://numpy.org/doc/2.5/reference/generated/numpy.add.html)
- `np.rint` rounds half to even, element-wise; `np.clip` then `astype(np.int16)` turns float audio into 16-bit PCM the same way every run — [numpy.rint](https://numpy.org/doc/2.5/reference/generated/numpy.rint.html), [numpy.clip](https://numpy.org/doc/2.5/reference/generated/numpy.clip.html)

## Pattern

```python
audio = np.frombuffer(result.stdout, dtype=np.float32)  # 16 kHz mono from ffmpeg
```

## Traps

- The array is read-only because it shares the `bytes` buffer — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)
- The buffer length must be a multiple of the item size (4 for float32), or it raises `ValueError` — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)

## Sources

- [numpy.add](https://numpy.org/doc/2.5/reference/generated/numpy.add.html) — adding arrays (accessed 2026-11-13)
- [numpy.rint](https://numpy.org/doc/2.5/reference/generated/numpy.rint.html), [numpy.clip](https://numpy.org/doc/2.5/reference/generated/numpy.clip.html) — rounding to PCM (accessed 2026-11-13)
- [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html) — dtype, read-only view (accessed 2026-10-29)
