# Pillow

**Kind:** library

**Version:** 12.3.0 (pinned in `pyproject.toml`, video-gen D3)

**Docs:** https://pillow.readthedocs.io/en/stable/

## Best practices

- `Image.open` is lazy: it reads the header only; call `image.load()` (or `verify()` on a separate open) to find a broken file before using it — [Image.open](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open)
- Check `image.format` (`"PNG"`, `"JPEG"`) after opening rather than trusting a file name; restrict with `formats=["PNG", "JPEG"]` — [Image.open](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open)
- An image over `Image.MAX_IMAGE_PIXELS` (about 89 M) warns, over twice that raises `DecompressionBombError` — [Image.open](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open)
- `ImageOps.fit(image, size, Image.Resampling.LANCZOS)` crops the centre to the size's aspect then resizes; `image.thumbnail(size)` shrinks in place keeping the aspect, never enlarges — [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html), [Image.thumbnail](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.thumbnail)
- `ImageOps.exif_transpose` turns a phone photo the way its EXIF says, before any crop — [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html)
- Import Pillow inside the function that needs it: the backend must start in under a second — project rule (`fastapi-api`)

## Pattern

```python
from PIL import Image, ImageOps  # inside the function

with Image.open(io.BytesIO(body), formats=["PNG", "JPEG"]) as image:
    image.load()
    image = ImageOps.exif_transpose(image).convert("RGB")
```

Follows [Image.open](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open).

## Traps

- `Image.open` raises `PIL.UnidentifiedImageError` (a subclass of `OSError`) for a file it can't read, and a truncated file raises `OSError` only at `load()` — [Image.open](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open)

## Sources

- [Image module](https://pillow.readthedocs.io/en/stable/reference/Image.html) — `open`, `thumbnail`, limits (accessed 2026-11-09)
- [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html) — `fit`, `exif_transpose` (accessed 2026-11-09)
