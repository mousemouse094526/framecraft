# ffmpeg (filters and libass)

**Kind:** runtime

**Version:** 7.1, the binary imageio-ffmpeg 0.7.0 bundles (`--enable-libass --enable-libharfbuzz --enable-libfreetype --enable-libx264`); see [imageio-ffmpeg.md](imageio-ffmpeg.md) for finding it

**Docs:** https://ffmpeg.org/ffmpeg-filters.html — options below were read from the installed binary with `ffmpeg -h filter={name}`

## Best practices

- `ass=filename=…:fontsdir=…` draws an ASS file with libass; `fontsdir` adds a folder of fonts to look in; `shaping` defaults to `auto` (complex shaping through harfbuzz when present, which Thai marks need) — [ass filter](https://ffmpeg.org/ffmpeg-filters.html#ass)
- `tpad=stop_mode=clone:stop_duration={s}` repeats the last frame for `s` seconds after the input ends (default `add` pads with `color`, black) — [tpad](https://ffmpeg.org/ffmpeg-filters.html#tpad)
- `apad=whole_dur={s}` pads audio with silence up to at least `s` seconds; pair it with `-t` or `atrim` to cut to an exact length — [apad](https://ffmpeg.org/ffmpeg-filters.html#apad)
- `amix=inputs=N:duration=first:normalize=0`: `normalize` defaults to true and scales every input by 1/N; off keeps each input's own volume; `duration` defaults to `longest` — [amix](https://ffmpeg.org/ffmpeg-filters.html#amix)
- `concat=n=N:v=1:a=1` joins segments; every segment must have the same video size, pixel format, frame rate time base and audio layout and rate, so normalise (`scale`, `setsar=1`, `fps`, `format`, `aresample`) before it — [concat](https://ffmpeg.org/ffmpeg-filters.html#concat)
- `gblur=sigma=…` (default 0.5, up to 1024); `steps` 1–6 trades speed for quality — [gblur](https://ffmpeg.org/ffmpeg-filters.html#gblur)
- `scale=W:H:force_original_aspect_ratio=decrease|increase` fits inside or covers a box keeping the aspect ratio; follow with `pad` (fit) or `crop` (cover) to land on exactly W×H — [scale](https://ffmpeg.org/ffmpeg-filters.html#scale-1)
- `-progress pipe:1` prints `key=value` blocks; `out_time_us` (or `out_time_ms`, also in microseconds) is how far the output is, `progress=end` closes the run — [ffmpeg -progress](https://ffmpeg.org/ffmpeg.html#Advanced-options)
- `-movflags +faststart` moves the `moov` atom to the front so a player can start before the whole file arrives — [mov muxer](https://ffmpeg.org/ffmpeg-formats.html#mov_002c-mp4_002c-ismv)

## Pattern

```python
graph = (
    f"[0:v]scale=1080:608:force_original_aspect_ratio=decrease,pad=1080:608:(ow-iw)/2:(oh-ih)/2,setsar=1,"
    f"tpad=stop_mode=clone:stop_duration={seconds}[v]"
)
command = [ffmpeg, "-nostdin", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(mp4),
           "-filter_complex", graph, "-map", "[v]", "-t", f"{seconds:.3f}", str(out)]
```

## Traps

- A filter argument is cut at `:` and the graph at `,`, `;`, `[`, `]`: a path with any of them needs escaping at two levels. Run ffmpeg with `cwd` at the file's folder and pass a bare name instead — [filtergraph escaping](https://ffmpeg.org/ffmpeg-filters.html#Notes-on-filtergraph-escaping)
- On Windows a drive letter is a `:`: the bare-name-and-`cwd` way avoids it too
- `-ss` before `-i` seeks the input (fast, to the keyframe, then decodes to the exact time); a `-t` after the input limits the output's length
- Clips that end before `-t` simply end early: pad with `tpad` / `apad` when a length must hold
- There is no ffprobe in imageio-ffmpeg (ADR 0005): read `Duration:` and `Stream … 1080x1920` from `ffmpeg -i` stderr

## ASS files (libass)

- `[Script Info]` `PlayResX`/`PlayResY` set the coordinate space; at the video's own size (1080×1920) pixel values in tags are pixels — [ASS tags](https://aegisub.org/docs/latest/ass_tags/)
- `\an1`–`\an9` pick the anchor (numpad layout), `\pos(x,y)` places that anchor; `\fs` font size, `\bord` outline, `\1c`/`\3c` fill and outline colour as `&HBBGGRR&`, `\1a`/`\3a` alpha `&HAA&` where `00` is opaque — [ASS tags](https://aegisub.org/docs/latest/ass_tags/)
- In Dialogue text `{…}` is an override block and `\N` a hard line break; text from users must have `{`, `}` and `\` escaped before it goes in (spoil-maker D51)
- Times are `H:MM:SS.cc` (centiseconds)

## Sources

- `ffmpeg -h filter=ass|tpad|amix|concat|gblur|apad` of the bundled 7.1 binary (read 2026-11-03)
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) — filtergraph escaping, `ass`, `scale` (accessed 2026-11-03)
- [ASS override tags](https://aegisub.org/docs/latest/ass_tags/) — `\an`, `\pos`, `\fs`, `\bord`, colours (accessed 2026-11-03)
