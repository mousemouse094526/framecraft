# gguf

**Kind:** library

**Version:** 0.19.0

**Docs:** https://pypi.org/project/gguf/0.19.0/

## Best practices

- Never imported by the project: diffusers' GGUF loader reads the file through it; only installed and version-checked — [diffusers GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf)
- Its version is read from installed metadata (`importlib.metadata.version("gguf")`), as for every pinned package — [importlib.metadata](https://docs.python.org/3.12/library/importlib.metadata.html)

## Traps

- diffusers asks for `gguf>=0.10.0` only when the GGUF loader runs; without it `from_single_file` fails late, inside the child — [diffusers GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf)
- gguf before about 0.17 calls `ndarray.newbyteorder`, which numpy 2 removed: `AttributeError: 'memmap' object has no attribute 'newbyteorder'` on load (toon D47) — [numpy 2.0 migration guide](https://numpy.org/devdocs/numpy_2_0_migration_guide.html)

## Sources

- [gguf 0.19.0 on PyPI](https://pypi.org/project/gguf/0.19.0/) — the package (accessed 2026-11-09)
- [diffusers GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf) — why it is needed (accessed 2026-11-09)
- [numpy 2.0 migration guide](https://numpy.org/devdocs/numpy_2_0_migration_guide.html) — `newbyteorder` removed (accessed 2026-11-09)
