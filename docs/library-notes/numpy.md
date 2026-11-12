# numpy

**Kind:** library

**Version:** 2.5.4

**Docs:** https://numpy.org/doc/2.5/

## Best practices

- `np.frombuffer(data, dtype=np.float32)` views raw bytes (ffmpeg `-f f32le` output) as an array without copying — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)

## Pattern

```python
audio = np.frombuffer(result.stdout, dtype=np.float32)  # 16 kHz mono from ffmpeg
```

## Traps

- The array is read-only because it shares the `bytes` buffer — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)
- The buffer length must be a multiple of the item size (4 for float32), or it raises `ValueError` — [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html)

## Sources

- [numpy.frombuffer](https://numpy.org/doc/2.5/reference/generated/numpy.frombuffer.html) — dtype, read-only view (accessed 2026-10-29)
