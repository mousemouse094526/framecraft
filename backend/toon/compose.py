"""What a การ์ตูนเล่า render draws and plays (toon spec › Render job, D4, D17, D19, D22, D23, D37):
the timeline of the cards, the ffmpeg command of each card's piece and of the whole clip, and
the ASS file libass draws.

Each card becomes a 1080×1920 30 fps piece: its picture scaled with lanczos, moved with
`zoompan`, flickered with `eq`, and placed for the Series' layout. A piece other than the last
runs `FADE_S` longer, and `xfade` lays that over the start of the next card, so the clip is as
long as its cards. The background sounds play in runs of segments that share one, each looped
from its start; a run other than the last runs its fade longer for `acrossfade` the same way.

Every command runs with `cwd` at the render's work folder and names files there bare, so no
path goes through ffmpeg's filter escaping (docs/library-notes/ffmpeg.md).
"""

import random
from typing import NamedTuple

from backend.ffmpeg import exe
from backend.paths import ProjectPaths
from backend import subtitles
from backend.sounds import AUDIO_BITRATE, AUDIO_RATE
from backend.subtitles import BLACK, WHITE, Timed
from backend.toon.store import Layout, Motion

FPS = 30
WIDTH, HEIGHT = 1080, 1920
FADE_S = 0.3  # between cards (D4)
SOUND_FADE_S = 1.0  # between background sounds (D17)

# Each layout's picture on the screen (D22, D37): its size, and its top on the black (`frame`).
PICTURE_SIZES: dict[Layout, tuple[int, int]] = {"frame": (1080, 608), "full": (1080, 1920)}
FRAME_TOP = 656
# `zoompan` rounds its crop to whole pixels: it works at twice the size, so a slow zoom doesn't shake.
ZOOM_WORK = 2
ZOOM_TO = 1.10
PAN_SHARE = 0.08  # of the width, at `ZOOM_TO` (spec › Render job)
# The flicker (D4): two waves whose sum stays in -0.06–0 and turns about six times a second.
FLICKER_DEPTH = 0.06
FLICKER_HZ = (2.9, 4.3)


class Placed(NamedTuple):
    """A card on the timeline: its picture and narration (bare names in the work folder),
    where it starts and how many frames it lasts."""

    card_id: str
    picture: str
    narration: str | None  # None: a silent card
    narration_s: float
    start_frame: int
    frames: int
    motion: Motion
    flicker: bool


class SoundRun(NamedTuple):
    """Segments in a row that play one background sound, or none (`sound` None)."""

    sound: str | None  # the m4a's bare name
    volume: int
    seconds: float


def frames_of(seconds: float) -> int:
    return round(seconds * FPS)


# --- pieces ---


def piece_command(placed: Placed, layout: Layout, frames: int, out: str) -> list[str]:
    """One card's picture for `frames` frames, lossless enough for the join."""
    width, height = PICTURE_SIZES[layout]
    graph = f"[0:v]scale={width * ZOOM_WORK}:{height * ZOOM_WORK}:flags=lanczos,{_motion(placed.motion, frames, width, height)}"
    if placed.flicker:
        graph += f",{_flicker(placed.card_id)}"
    if layout == "frame":
        graph += f",pad={WIDTH}:{HEIGHT}:0:{FRAME_TOP}:black"
    graph += ",format=yuv420p,setsar=1[v]"
    return [
        exe(), "-nostdin", "-hide_banner", "-y", "-loop", "1", "-framerate", str(FPS), "-i", placed.picture,
        "-filter_complex", graph, "-map", "[v]", "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", out,
    ]  # fmt: skip


def _motion(motion: Motion, frames: int, width: int, height: int) -> str:
    """`zoompan` one output frame per input frame (`d=1`), `on` counting them (D4)."""
    last = max(frames - 1, 1)
    centre_x, centre_y = "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
    zoom, x = "1", centre_x
    if motion == "zoom_in":
        zoom = f"1+{ZOOM_TO - 1:.2f}*on/{last}"
    elif motion == "zoom_out":
        zoom = f"{ZOOM_TO:.2f}-{ZOOM_TO - 1:.2f}*on/{last}"
    elif motion in ("pan_left", "pan_right"):
        zoom = f"{ZOOM_TO:.2f}"
        sign = "-" if motion == "pan_left" else "+"
        x = f"{centre_x}{sign}iw*{PAN_SHARE:.2f}*(on/{last}-0.5)"
    return f"zoompan=z='{zoom}':x='{x}':y='{centre_y}':d=1:s={width}x{height}:fps={FPS}"


def _flicker(card_id: str) -> str:
    """The whole picture darkens by 0–0.06, smoothly; the waves' phases come from the card's id."""
    seeded = random.Random(card_id)
    one, two = (seeded.uniform(0, 6.283) for _ in range(2))
    half = FLICKER_DEPTH / 2
    quarter = FLICKER_DEPTH / 4
    a, b = FLICKER_HZ
    return (
        f"eq=eval=frame:brightness='-{half:.3f}+{quarter:.3f}*sin(2*PI*{a}*t+{one:.3f})"
        f"+{quarter:.3f}*sin(2*PI*{b}*t+{two:.3f})'"
    )


# --- the whole clip ---


def final_command(
    pieces: list[str],
    placed: list[Placed],
    narration: str,
    runs: list[SoundRun],
    ass: str,
    fonts_dir: str,
    total_frames: int,
    out: str,
) -> list[str]:
    """The pieces faded into each other, the text drawn, the narration over the background
    sounds (`normalize=0`, so neither is turned down), encoded for phones."""
    inputs: list[str] = []
    for piece in pieces:
        inputs += ["-i", piece]
    graph: list[str] = []
    video = "[0:v]"
    for index in range(1, len(pieces)):
        offset = placed[index].start_frame / FPS
        graph.append(f"{video}[{index}:v]xfade=transition=fade:duration={FADE_S}:offset={offset:.3f}[x{index}]")
        video = f"[x{index}]"
    graph.append(f"{video}ass=filename={ass}:fontsdir={fonts_dir}[v]")
    inputs += ["-i", narration]
    voice_input = len(pieces)
    graph.append(f"[{voice_input}:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo[voice]")
    background = _background(runs, inputs, graph)
    graph.append(f"[voice]{background}amix=inputs=2:duration=first:normalize=0[a]")
    seconds = total_frames / FPS
    return [
        exe(), "-nostdin", "-hide_banner", "-y", "-progress", "pipe:1", "-nostats", *inputs,
        "-filter_complex", ";".join(graph), "-map", "[v]", "-map", "[a]", "-t", f"{seconds:.3f}",
        "-r", str(FPS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-ar", str(AUDIO_RATE),
        "-movflags", "+faststart", "-f", "mp4", out,
    ]  # fmt: skip


def _background(runs: list[SoundRun], inputs: list[str], graph: list[str]) -> str:
    """Each run looped or silent, cut to its length plus the fade into the next, at its
    volume; runs in a row joined with `acrossfade` (D17). Adds the inputs and filters it needs;
    returns the label of the whole."""
    labels: list[str] = []
    for index, run in enumerate(runs):
        fade = _fade_after(runs, index)
        seconds = run.seconds + fade
        if run.sound is None:
            source = f"anullsrc=r={AUDIO_RATE}:cl=stereo,atrim=duration={seconds:.3f}"
        else:
            # The input loops, not `aloop`: that holds the whole sound in memory, up to 20 minutes (D56).
            inputs += ["-stream_loop", "-1", "-i", run.sound]
            number = inputs.count("-i") - 1
            source = (
                f"[{number}:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo,"
                f"atrim=duration={seconds:.3f},volume={run.volume / 100:.2f}"
            )
        graph.append(f"{source},asetpts=PTS-STARTPTS[s{index}]")
        labels.append(f"[s{index}]")
    joined = labels[0]
    for index in range(1, len(labels)):
        fade = _fade_after(runs, index - 1)
        graph.append(f"{joined}{labels[index]}acrossfade=d={fade:.3f}:c1=tri:c2=tri[j{index}]")
        joined = f"[j{index}]"
    return joined


def _fade_after(runs: list[SoundRun], index: int) -> float:
    """1 s between two runs, shorter when either is shorter than that; none after the last."""
    if index >= len(runs) - 1:
        return 0.0
    return min(SOUND_FADE_S, runs[index].seconds, runs[index + 1].seconds)


# --- the text (D19, D22, D23) ---

RED = "&H002E26D7"  # #D7262E
GREY = "&H00A0A0A0"
NAME_BOX = "&H60000000"  # black, a little see-through


class Look(NamedTuple):
    size: int
    fill: str
    outline: str
    border: int
    boxed: bool = False  # ASS BorderStyle 3: an opaque box in the outline colour


TITLE = Look(76, WHITE, BLACK, 0)
EP_TAG = Look(48, WHITE, RED, 10, boxed=True)
CHANNEL = Look(40, GREY, BLACK, 0)
SUB = {"frame": Look(72, WHITE, BLACK, 4), "full": Look(84, WHITE, BLACK, 8)}
NAME_TAG = Look(44, WHITE, NAME_BOX, 10, boxed=True)

TITLE_PER_LINE = 20
TITLE_LINES = 2
TITLE_AT = "\\an8\\pos(540,250)"
EP_TAG_AT = "\\an8\\pos(540,{y})"
CHANNEL_AT = "\\an2\\pos(540,1840)"
SUB_AT = {"frame": "\\an8\\pos(540,1320)", "full": "\\an5\\pos(540,1152)"}  # under the picture; 60% of the height
NAME_TAG_AT = {"frame": (1, 40, FRAME_TOP + 608 - 30), "full": (7, 40, 120)}  # anchor, x, y of the first line
NAME_TAG_STEP = 70  # the second tag of a card, a line below (or above, from the bottom)


class Narrated(NamedTuple):
    """A card's text on the timeline, while its narration plays."""

    text: str
    start: float
    end: float


class Tagged(NamedTuple):
    """The name tags of a card (D23): its characters' first card in the EP."""

    tags: list[str]
    start: float
    end: float


def ass_file(
    project: ProjectPaths,
    layout: Layout,
    title: str,
    n: int,
    channel_name: str,
    narrated: list[Narrated],
    tagged: list[Tagged],
    total: float,
) -> str:
    """`frame`: the title (≤ 2 lines, cut with "…") and `EP{n:02}` on top, the channel name at the
    bottom, the whole clip; `full`: none of them. Subtitles in short chunks (spoil-maker D20)."""
    styles = [_style("Sub", SUB[layout]), _style("Tag", NAME_TAG)]
    events: list[str] = []
    if layout == "frame":
        styles += [_style("Title", TITLE), _style("Ep", EP_TAG), _style("Channel", CHANNEL)]
        lines = _title_lines(project, title)
        if lines:
            events.append(subtitles.event("Title", 0.0, total, TITLE_AT, lines))
        ep_y = 250 + TITLE.size * max(len(lines), 1) + 40
        events.append(subtitles.event("Ep", 0.0, total, EP_TAG_AT.format(y=ep_y), [f"EP{n:02}"]))
        if channel_name.strip():
            events.append(subtitles.event("Channel", 0.0, total, CHANNEL_AT, [channel_name]))
    for card in narrated:
        pieces = [[chunk] for chunk in subtitles.chunks(project, card.text)]
        timed = Timed(card.text, card.start, card.end)
        for (start, end), piece in zip(subtitles.split_time(timed, pieces), pieces, strict=True):
            events.append(subtitles.event("Sub", start, end, SUB_AT[layout], piece))
    anchor, x, y = NAME_TAG_AT[layout]
    step = -NAME_TAG_STEP if anchor == 1 else NAME_TAG_STEP
    for card in tagged:
        for index, tag in enumerate(card.tags):
            at = f"\\an{anchor}\\pos({x},{y + step * index})"
            events.append(subtitles.event("Tag", card.start, card.end, at, [tag]))
    return subtitles.HEADER.format(styles="\n".join(styles)) + "\n".join(events) + "\n"


def _title_lines(project: ProjectPaths, title: str) -> list[str]:
    if not title.strip():
        return []
    lines = subtitles.cut_lines(project, title, TITLE_PER_LINE)
    if len(lines) > TITLE_LINES:
        lines = [*lines[: TITLE_LINES - 1], lines[TITLE_LINES - 1].rstrip() + "…"]
    return lines


def _style(name: str, look: Look) -> str:
    border_style = 3 if look.boxed else 1
    return (
        f"Style: {name},{subtitles.FONT},{look.size},{look.fill},{look.fill},{look.outline},{look.outline},-1,0,0,0,"
        f"100,100,0,0,{border_style},{look.border},0,8,0,0,0,1"
    )
