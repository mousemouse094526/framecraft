"""ffmpeg for a render (spoil-maker spec › Render job step 3, D9, D22, D31, D40, D45):
each half-sentence Shot becomes a 1080×1920 30 fps piece with the original sound
turned down, then the pieces are joined, the voice mixed in, the ASS text drawn and
the whole encoded for phones.

Every command runs with `cwd` at the render's work folder and names files there
bare, so no path goes through ffmpeg's filter escaping (docs/library-notes/ffmpeg.md).
"""

from pathlib import Path

from pydantic import BaseModel

from backend.ffmpeg import Media, exe

FPS = 30
WIDTH, HEIGHT = 1080, 1920
AUDIO_RATE = 48_000
# Seeking this close to a clip's end may find no frame; a Shot past it shows the last
# frame held (spec › Render job step 3.2).
END_MARGIN_SECONDS = 0.5

# The picture of each layout (D22): `{tail}` makes every piece the same format and
# holds its last frame when the source runs out. A's background blurs at a quarter of
# the size (sigma 30 / 4) and scales back up: the same look, several times faster (D63).
LAYOUT_GRAPHS = {
    "A": (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,gblur=sigma=7.5,scale=1080:1920[blur];"
        "[fg]scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350[top];"
        "[blur][top]overlay=0:285,{tail}[v]"
    ),
    "B": "[0:v]scale=1080:608:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:656+(608-ih)/2:black,{tail}[v]",
    "C": "[0:v]scale=1080:608:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:420+(608-ih)/2:black,{tail}[v]",
}


class Piece(BaseModel):
    """Half a sentence on the timeline: one Shot played from its start (D31)."""

    clip_id: str
    start: float
    seconds: float


def piece_command(piece: Piece, mp4: Path, media: Media, layout: str, volume: int, out: str) -> list[str]:
    """The piece framed for `layout`, with the original sound at `volume` percent (0:
    silence, D40). Lossless-enough x264 and PCM, so the join and the final encode lose
    nothing that shows."""
    start = min(piece.start, max(0.0, media.duration_s - END_MARGIN_SECONDS))
    seconds = piece.seconds
    tail = f"fps={FPS},format=yuv420p,setsar=1,tpad=stop_mode=clone:stop_duration={seconds:.3f}"
    graph = LAYOUT_GRAPHS[layout].format(tail=tail)
    inputs = ["-ss", f"{start:.3f}", "-i", str(mp4)]
    if volume > 0 and media.has_audio:
        graph += f";[0:a]volume={volume / 100:.2f},aresample={AUDIO_RATE},aformat=channel_layouts=stereo,apad[a]"
        audio = "[a]"
    else:
        inputs += ["-f", "lavfi", "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo"]
        audio = "1:a"
    return [
        exe(), "-nostdin", "-hide_banner", "-y", *inputs,
        "-filter_complex", graph, "-map", "[v]", "-map", audio, "-t", f"{seconds:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le", "-ar", str(AUDIO_RATE), "-ac", "2", out,
    ]  # fmt: skip


def final_command(pieces_list: str, narration: str, captions: str, fonts_dir: str, seconds: float, out: str) -> list[str]:
    """Joins the pieces, mixes the voice over their sound (`normalize=0`, so neither is
    turned down) and draws the text (spec › Render job step 3.4)."""
    graph = (
        f"[0:v]ass=filename={captions}:fontsdir={fonts_dir}[v];"
        f"[1:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo[voice];"
        f"[0:a][voice]amix=inputs=2:duration=first:normalize=0[a]"
    )
    return [
        exe(), "-nostdin", "-hide_banner", "-y", "-progress", "pipe:1", "-nostats",
        "-f", "concat", "-safe", "0", "-i", pieces_list, "-i", narration,
        "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{seconds:.3f}",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(AUDIO_RATE),
        "-movflags", "+faststart", "-f", "mp4", out,
    ]  # fmt: skip
