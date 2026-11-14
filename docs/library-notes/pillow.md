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
- `ImageDraw` draws without anti-aliasing: draw at 2× and shrink with `resize(size, Image.Resampling.LANCZOS)` for smooth edges; `line(xy, fill, width)`, `ellipse(xy, fill, outline, width)`, `arc(xy, start, end, fill, width)`, `rectangle`; on an RGBA image a fill with alpha replaces the pixels, it doesn't blend — draw a see-through shape on its own layer and `alpha_composite` it — [ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
- `Image.alpha_composite(im1, im2)` / `im.alpha_composite(im, dest)` blend RGBA over RGBA; `im.paste(sprite, box, sprite)` blends an RGBA sprite onto an RGB image through its own alpha as the mask — [Image](https://pillow.readthedocs.io/en/stable/reference/Image.html)
- `im.tobytes()` of an RGB image is raw `rgb24`, row after row: what ffmpeg's `rawvideo` reads — [Image.tobytes](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.tobytes)
- `ImageFilter.GaussianBlur(radius)`; `Image.blend(a, b, alpha)`; `Image.linear_gradient("L")` is a 256×256 black-to-white ramp top to bottom, a mask for `Image.composite` — [ImageFilter](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html), [Image](https://pillow.readthedocs.io/en/stable/reference/Image.html)
- `ImageFont.truetype(path, size).getlength(text)` is the text's advance in px; `ImageFont.load_default(size)` (FreeType builds) is a scalable font shipped inside Pillow, no file needed — [ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html)
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
- [ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html), [ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html), [ImageFilter](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html) — shapes, `getlength`, `load_default(size)`, `GaussianBlur` (accessed 2026-11-13)
