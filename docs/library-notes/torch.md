# torch

**Kind:** library

**Version:** 2.8.0 (`+cu128` on Windows, setup-status D5)

**Docs:** https://docs.pytorch.org/docs/2.8/

## Best practices

- Pick the device with `torch.cuda.is_available()` then `torch.backends.mps.is_available()` — [MPS backend](https://docs.pytorch.org/docs/2.8/notes/mps.html)
- Pass a dtype object (`torch.float16`, `torch.float32`), not a string, where an API takes `dtype` — [Tensor attributes](https://docs.pytorch.org/docs/2.8/tensor_attributes.html)
- Importing torch takes seconds; import it inside the function that needs it — project rule (`backend.checks`)

## Pattern

```python
import torch  # inside the child process only

dtype = torch.float16 if device == "cuda" else torch.float32
```

## Traps

- A Metal or CUDA crash kills the whole process; it is not a Python exception (ADR 0012)
- `float16` on `mps` is not safe for Whisper large-v3-turbo — see [transformers.md](transformers.md)

## Sources

- [MPS backend](https://docs.pytorch.org/docs/2.8/notes/mps.html) — device checks (accessed 2026-10-29)
- [Tensor attributes](https://docs.pytorch.org/docs/2.8/tensor_attributes.html) — dtypes (accessed 2026-10-29)
