# torch

**Kind:** library

**Version:** 2.8.0 (`+cu128` on Windows, setup-status D5)

**Docs:** https://docs.pytorch.org/docs/2.8/

## Best practices

- Pick the device with `torch.cuda.is_available()` then `torch.backends.mps.is_available()` — [MPS backend](https://docs.pytorch.org/docs/2.8/notes/mps.html)
- Pass a dtype object (`torch.float16`, `torch.float32`), not a string, where an API takes `dtype` — [Tensor attributes](https://docs.pytorch.org/docs/2.8/tensor_attributes.html)
- `torch.cuda.get_arch_list()` lists the `sm_XY` (and `compute_XY` PTX) targets the build was compiled for; `[]` when CUDA isn't available. It reads build flags only — no device query — [torch.cuda](https://docs.pytorch.org/docs/2.8/cuda.html)
- A card is usable when the list has an `sm_` of the same major: CUDA binaries run on later minors of that major, the rule torch's own `_check_cubins` applies — [torch/cuda/__init__.py v2.8.0](https://github.com/pytorch/pytorch/blob/v2.8.0/torch/cuda/__init__.py)
- `torch.cuda.max_memory_allocated(device)` gives the peak bytes torch's allocator held on that card since start (not the driver's total) — [torch.cuda](https://docs.pytorch.org/docs/2.8/cuda.html)
- Importing torch takes seconds; import it inside the function that needs it — project rule (`backend.checks`)

## Pattern

```python
import torch  # inside the child process only

dtype = torch.float16 if device == "cuda" else torch.float32
```

## Traps

- The cu128 wheels are built for `7.0;7.5;8.0;8.6;9.0;10.0;12.0`: no `sm_89`, yet RTX 40xx runs on the `sm_8x` kernels, so never require an exact `sm_` match — [build_cuda.sh v2.8.0](https://github.com/pytorch/pytorch/blob/v2.8.0/.ci/manywheel/build_cuda.sh)
- No `sm_5x`/`sm_6x` in cu128: Maxwell and Pascal get `no kernel image is available` — [PyTorch dev-discuss](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128)

- A Metal or CUDA crash kills the whole process; it is not a Python exception (ADR 0012)
- `float16` on `mps` is not safe for Whisper large-v3-turbo — see [transformers.md](transformers.md)

## Sources

- [MPS backend](https://docs.pytorch.org/docs/2.8/notes/mps.html) — device checks (accessed 2026-10-29)
- [torch/cuda/__init__.py v2.8.0](https://github.com/pytorch/pytorch/blob/v2.8.0/torch/cuda/__init__.py) — `get_arch_list`, `_check_cubins` (accessed 2026-11-06)
- [build_cuda.sh v2.8.0](https://github.com/pytorch/pytorch/blob/v2.8.0/.ci/manywheel/build_cuda.sh) — cu128 arch list (accessed 2026-11-06)
- [Tensor attributes](https://docs.pytorch.org/docs/2.8/tensor_attributes.html) — dtypes (accessed 2026-10-29)
