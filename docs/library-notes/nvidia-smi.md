# nvidia-smi

**Kind:** runtime

**Version:** ships with the NVIDIA driver (R510 or newer has the `compute_cap` query field)

**Docs:** https://docs.nvidia.com/deploy/nvidia-smi/index.html

## Best practices

- `--query-gpu=` takes a comma-separated list of properties; `nvidia-smi --help-query-gpu` lists them (`name`, `memory.total`, `compute_cap`) — [nvidia-smi › Selective query options](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
- `--format=csv` is mandatory with `--query-gpu`; add `noheader` to skip the column line and `nounits` to drop units (`memory.total` is then a bare MiB number) — [nvidia-smi › Selective query options](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
- `-i 0` limits the output to the GPU at 0-based index 0 — [nvidia-smi › Selective query options](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
- nvidia-smi reads the card through NVML, so the calling process gets no CUDA context and holds no VRAM — [nvidia-smi › Description](https://docs.nvidia.com/deploy/nvidia-smi/index.html)

## Pattern

```python
result = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap", "--format=csv,noheader,nounits", "-i", "0"],
    capture_output=True, text=True, timeout=5, check=True,
)
name, mib, cap = (field.strip() for field in result.stdout.strip().rsplit(",", 2))
# "NVIDIA GeForce RTX 3060, 12288, 8.6"
```

## Traps

- A driver older than the `compute_cap` field prints an error for the whole query and exits non-zero — treat it like a missing driver
- No NVIDIA driver → `nvidia-smi` isn't on PATH: `FileNotFoundError`, not a non-zero exit
- `name` is free text; split from the right so a comma in it can't shift the numbers

## Sources

- [nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html) — query options, `--format`, `-i` (accessed 2026-11-06)
