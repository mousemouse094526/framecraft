# numpy

**Kind:** library

**Version:** 2.5.4

**Docs:** https://numpy.org/doc/2.5/

## Best practices

- `np.frombuffer(data, dtype=np.float32)` views raw bytes (ffmpeg `-f f32le` output) as an array without copying — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)

- `np.add.at(target, indices, values)` adds without buffering, so repeated indices all add; `target[a:b] += values` on a slice is the plain way when ranges are contiguous — [numpy.add](https://numpy.org/doc/2.5/reference/generated/numpy.add.html)
- `np.random.default_rng(seed)` gives a PCG64 `Generator`; `standard_normal(size, dtype=np.float32)` takes `float32` or `float64`, `uniform(low, high, size)` is `float64` only — [Generator](https://numpy.org/doc/2.5/reference/random/generator.html)
- `np.fft.rfft(a)` is `n//2 + 1` complex bins of a real signal; `np.fft.rfftfreq(n, d=1/rate)` their centre frequencies in Hz — [numpy.fft.rfft](https://numpy.org/doc/2.5/reference/generated/numpy.fft.rfft.html), [numpy.fft.rfftfreq](https://numpy.org/doc/2.5/reference/generated/numpy.fft.rfftfreq.html)
- `np.rint` rounds half to even, element-wise; `np.clip` then `astype(np.int16)` turns float audio into 16-bit PCM the same way every run — [numpy.rint](https://numpy.org/doc/2.5/reference/generated/numpy.rint.html), [numpy.clip](https://numpy.org/doc/2.5/reference/generated/numpy.clip.html)

## Pattern

```python
audio = np.frombuffer(result.stdout, dtype=np.float32)  # 16 kHz mono from ffmpeg
```

## Traps

- The array is read-only because it shares the `bytes` buffer — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)
- The buffer length must be a multiple of the item size (4 for float32), or it raises `ValueError` — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)
- A seeded `Generator` repeats its stream only for the same calls with the same arguments on the same numpy build: "Generator does not provide a version compatibility guarantee", and a feature release (X.Y) may change it — draw the same `size` in one call, and expect a numpy upgrade to change seeded noise — [Compatibility policy](https://numpy.org/doc/2.5/reference/random/compatibility.html)

## Sources

- [Random Generator](https://numpy.org/doc/2.5/reference/random/generator.html), [Compatibility policy](https://numpy.org/doc/2.5/reference/random/compatibility.html) — seeded streams (accessed 2026-11-16)
- [numpy.fft.rfft](https://numpy.org/doc/2.5/reference/generated/numpy.fft.rfft.html), [numpy.fft.rfftfreq](https://numpy.org/doc/2.5/reference/generated/numpy.fft.rfftfreq.html) — a tone's main frequency (accessed 2026-11-16)
- [numpy.add](https://numpy.org/doc/2.5/reference/generated/numpy.add.html) — adding arrays (accessed 2026-11-13)
- [numpy.rint](https://numpy.org/doc/2.5/reference/generated/numpy.rint.html), [numpy.clip](https://numpy.org/doc/2.5/reference/generated/numpy.clip.html) — rounding to PCM (accessed 2026-11-13)
- [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html) — dtype, read-only view (accessed 2026-10-29)
