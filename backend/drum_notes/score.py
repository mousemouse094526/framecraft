"""The numbers behind the models (drum-notes spec › Score, D6, D9, D14, D20): the plan of
Beat This! chunks and their stitching, ADTOF peak picking into hits, the plan of Basic Pitch windows
and their onsets into snare hits (melody mode), and beats and downbeats from logits. Pure functions
on arrays and seconds: the Pick job calls them with what the models gave, tests with synthetic
arrays (D17). The bars found (Score step 1) are `songs.bars_of`, read off an analysis; a lesson's
Groove from the bars picked (steps 3–8) is `drum_notes.groove`.
numpy is imported inside each function (fastapi-api › Never break).
"""

from typing import TYPE_CHECKING, NamedTuple

from backend.drum_notes.songs import Hit

if TYPE_CHECKING:
    import numpy as np

# --- Beat This! (model card: 50 frames/s, hop 441 at 22,050 Hz, chunks of 1,500 frames overlapping 6) ---

BEAT_THIS_FPS = 50
BEAT_THIS_HOP = 441
BEAT_THIS_WINDOW = 1024
CHUNK_FRAMES = 1500
OVERLAP_FRAMES = 6  # cut from each side of a chunk; the model pads the range's own ends by as many
KEPT_FRAMES = CHUNK_FRAMES - 2 * OVERLAP_FRAMES
BEAT_WINDOW_FRAMES = 3  # a beat is the top of its 7-frame window (±3)

# --- ADTOF (model card: 100 frames/s at 44,100 Hz, five classes in this order) ---

ADTOF_FPS = 100
ADTOF_CLASSES = 5
# The app's piece for each class (D9): kick, snare, toms, hi-hat, cymbals.
ADTOF_PIECES = ("kick", "snare", "tom_mid", "hihat_closed", "crash")
THRESHOLDS = (0.22, 0.24, 0.32, 0.22, 0.30)
# Peak-picking windows in frames, from the card's seconds: pre_avg 0.1, post_avg 0.01, pre_max 0.02, post_max 0.01, combine 0.02.
PRE_AVG, POST_AVG, PRE_MAX, POST_MAX, COMBINE = 10, 1, 2, 1, 2

# --- Basic Pitch (docs/library-notes/basic-pitch.md: windows of 43,844 samples at 22,050 Hz, 172 frames
# of 256 samples each, 30 overlapping frames between windows) ---

BASIC_PITCH_RATE = 22_050
BASIC_PITCH_WINDOW = 43_844
BASIC_PITCH_FRAMES = 172
BASIC_PITCH_NOTES = 88  # the piano's keys: one onset column each
BASIC_PITCH_FRAME_HOP = 256  # samples from one frame to the next inside a window
BASIC_PITCH_OVERLAP = 30  # frames two windows share: 15 cut from each side of every window
BASIC_PITCH_CUT = BASIC_PITCH_OVERLAP // 2
BASIC_PITCH_PAD = BASIC_PITCH_CUT * BASIC_PITCH_FRAME_HOP  # zeros before the range, so the first kept frame is its first sample
BASIC_PITCH_HOP = BASIC_PITCH_WINDOW - BASIC_PITCH_OVERLAP * BASIC_PITCH_FRAME_HOP  # samples from one window to the next
ONSET_THRESHOLD = 0.5  # Basic Pitch's default
# Onsets under this far apart are one hit (two frames apart are two): adjacent frames of a window are 256
# samples apart, and the last kept frame of a window and the first of the next 68 (36,164 is 68 over a multiple of 256).
ONSET_MERGE_SAMPLES = 2 * BASIC_PITCH_FRAME_HOP


class Chunk(NamedTuple):
    """One run of Beat This!: `frames` frames of the range from `first_frame`, and the frames the
    model pads before and after them (6 at the range's own ends, 0 elsewhere). Its output is
    `pad_before + frames + pad_after` frames long; `stitch` keeps the middle ones."""

    first_frame: int
    frames: int
    pad_before: int
    pad_after: int


def beat_this_frames(samples: int) -> int:
    """How many frames the model makes of `samples` at 22,050 Hz: `N = (frames − 1) × 441 + 1024`."""
    return max(1, (samples - BEAT_THIS_WINDOW) // BEAT_THIS_HOP + 1)


def beat_this_frames_to_samples(frames: int) -> int:
    return (frames - 1) * BEAT_THIS_HOP + BEAT_THIS_WINDOW


def beat_this_chunks(frames: int) -> list[Chunk]:
    """The chunks of a range of `frames`: each covers 1,500 output frames, of which the 6 at each
    side are cut; the last is shifted so its kept frames end at the range's end (D20)."""
    starts = [-OVERLAP_FRAMES]
    while starts[-1] + CHUNK_FRAMES - OVERLAP_FRAMES < frames:  # its kept frames end before the range does
        starts.append(starts[-1] + KEPT_FRAMES)
    starts[-1] = max(-OVERLAP_FRAMES, frames + OVERLAP_FRAMES - CHUNK_FRAMES)
    chunks = []
    for start in starts:
        end = min(start + CHUNK_FRAMES, frames + OVERLAP_FRAMES)
        first, last = max(start, 0), min(end, frames)
        chunks.append(Chunk(first, last - first, first - start, end - last))
    return chunks


def chunk_samples(pcm: "np.ndarray", chunk: Chunk) -> "np.ndarray":
    """The waveform of one chunk, zero-padded to the samples its frames need when the range's
    end falls short of the last window."""
    import numpy as np

    start = chunk.first_frame * BEAT_THIS_HOP
    needed = beat_this_frames_to_samples(chunk.frames)
    piece = pcm[start : start + needed]
    if len(piece) < needed:
        piece = np.concatenate([piece, np.zeros(needed - len(piece), np.float32)])
    return piece


def stitch(frames: int, outputs: list[tuple[Chunk, "np.ndarray"]]) -> "np.ndarray":
    """One array of `frames` logits from each chunk's output (`[1, T]` or `[T]`): 6 frames cut
    from each side, chunks in order, the first to cover a frame keeps it (D20)."""
    import numpy as np

    stitched = np.zeros(frames, np.float32)
    covered = np.zeros(frames, bool)
    for chunk, logits in outputs:
        # The output covers `pad_before + frames + pad_after` frames from `first_frame - pad_before`.
        logits = np.asarray(logits, np.float32).reshape(-1)
        kept = logits[OVERLAP_FRAMES : len(logits) - OVERLAP_FRAMES]
        first = chunk.first_frame - chunk.pad_before + OVERLAP_FRAMES
        at = np.arange(first, first + len(kept))
        new = ~covered[at]
        stitched[at[new]] = kept[new]
        covered[at] = True
    return stitched


# --- hits ---


def drum_hits(activations: "np.ndarray", start_s: float) -> list[Hit]:
    """The hits of `[frames, 5]` sigmoid activations at 100 frames/s, peak-picked per class with the
    card's thresholds and windows (D6), as the app's pieces at `normal` (D9), in time order, in
    seconds of the song (`start_s` added)."""
    import numpy as np

    activations = np.asarray(activations, np.float32).reshape(-1, ADTOF_CLASSES)
    hits = []
    for class_index, piece in enumerate(ADTOF_PIECES):
        for frame in _peaks(activations[:, class_index], THRESHOLDS[class_index]):
            hits.append(Hit(t=round(start_s + frame / ADTOF_FPS, 3), piece=piece, level="normal"))
    hits.sort(key=lambda hit: (hit.t, ADTOF_PIECES.index(hit.piece)))
    return hits


def _peaks(activation: "np.ndarray", threshold: float) -> list[int]:
    """madmom's peak picking as the card describes it: a frame at least `threshold` over the mean
    of its `pre_avg`/`post_avg` window, the top of its `pre_max`/`post_max` window; peaks within
    `combine` frames of the one kept before are dropped."""
    import numpy as np

    moving_average = _window(activation, PRE_AVG, POST_AVG, np.nanmean)
    moving_max = _window(activation, PRE_MAX, POST_MAX, np.nanmax)
    candidates = np.nonzero((activation >= moving_average + threshold) & (activation >= moving_max))[0]
    peaks: list[int] = []
    for frame in candidates:
        if not peaks or frame - peaks[-1] > COMBINE:
            peaks.append(int(frame))
    return peaks


def _window(values: "np.ndarray", before: int, after: int, reduce) -> "np.ndarray":
    """`reduce` (a `nan`-skipping numpy reduction) over `[n − before, n + after]` for every frame, the
    window clipped at the ends: the array is padded with `nan` and read through `sliding_window_view`
    (docs/library-notes/numpy.md), one call for all frames."""
    import numpy as np

    padded = np.concatenate([np.full(before, np.nan, np.float32), values, np.full(after, np.nan, np.float32)])
    windows = np.lib.stride_tricks.sliding_window_view(padded, before + after + 1)
    return reduce(windows, axis=1).astype(np.float32)


# --- Basic Pitch windows and melody hits (D14) ---


class Window(NamedTuple):
    """One run of Basic Pitch: the 43,844 samples from `first_sample` of the range (negative for the
    first window: the zeros padded before it). Its output is 172 frames, of which `melody_hits`
    keeps the middle 142."""

    first_sample: int


def basic_pitch_windows(samples: int) -> list[Window]:
    """The windows of a range of `samples`, as Basic Pitch's `get_audio_input` cuts them: the range
    padded with 3,840 zeros before, then a window every 36,164 samples while one starts inside it,
    the last zero-padded past the range's end."""
    return [Window(start - BASIC_PITCH_PAD) for start in range(0, samples + BASIC_PITCH_PAD, BASIC_PITCH_HOP)]


def window_samples(pcm: "np.ndarray", window: Window) -> "np.ndarray":
    """The waveform of one window, zero-padded where it reaches before the range or past its end."""
    import numpy as np

    first, last = window.first_sample, window.first_sample + BASIC_PITCH_WINDOW
    piece = pcm[max(first, 0) : max(last, 0)]
    return np.concatenate([np.zeros(max(-first, 0), np.float32), piece, np.zeros(max(last - max(first, 0) - len(piece), 0), np.float32)])


def melody_hits(outputs: list[tuple[Window, "np.ndarray"]], samples: int, start_s: float) -> list[Hit]:
    """The snare hits of melody mode (D14) from each window's `[172, 88]` onset output (`BASIC_PITCH_FRAMES` × `BASIC_PITCH_NOTES`): a frame is an
    onset when any note's onset is at least 0.5; the 15 frames at each side of a window are cut and
    frames past the range's end dropped; an onset under `ONSET_MERGE_SAMPLES` after the one before is
    the same hit, at its first frame. All `snare` at `normal`, in time order, in seconds of the song."""
    import numpy as np

    onset_samples: list[int] = []
    for window, onset in outputs:
        onset = np.asarray(onset, np.float32).reshape(BASIC_PITCH_FRAMES, BASIC_PITCH_NOTES)
        for frame in np.nonzero(onset.max(axis=1) >= ONSET_THRESHOLD)[0]:
            if BASIC_PITCH_CUT <= frame < BASIC_PITCH_FRAMES - BASIC_PITCH_CUT:
                onset_samples.append(window.first_sample + int(frame) * BASIC_PITCH_FRAME_HOP)
    hits: list[int] = []
    last = None  # the onset before, merged or not: a run of adjacent frames is one hit
    for sample in sorted(set(onset_samples)):
        if 0 <= sample < samples and (last is None or sample - last >= ONSET_MERGE_SAMPLES):
            hits.append(sample)
        last = sample
    return [Hit(t=round(start_s + sample / BASIC_PITCH_RATE, 3), piece="snare", level="normal") for sample in hits]


# --- beats and downbeats ---


def beats_and_downbeats(beat: "np.ndarray", downbeat: "np.ndarray", start_s: float) -> tuple[list[float], list[float]]:
    """Beats: the frames whose `beat` logit is over 0 and the top of their 7-frame window, adjacent
    ones as one; downbeats the same on `downbeat`, each moved to its nearest beat (D6). Seconds of
    the song, ascending, unique."""
    beat_frames = _logit_peaks(beat)
    downbeat_frames = _logit_peaks(downbeat)
    beats = [round(start_s + frame / BEAT_THIS_FPS, 3) for frame in beat_frames]
    downbeats: list[float] = []
    for frame in downbeat_frames:
        if not beats:
            break
        nearest = min(beats, key=lambda t: abs(t - (start_s + frame / BEAT_THIS_FPS)))
        if nearest not in downbeats:
            downbeats.append(nearest)
    return beats, sorted(downbeats)


def _logit_peaks(logits: "np.ndarray") -> list[int]:
    import numpy as np

    logits = np.asarray(logits, np.float32).reshape(-1)
    moving_max = _window(logits, BEAT_WINDOW_FRAMES, BEAT_WINDOW_FRAMES, np.nanmax)
    candidates = np.nonzero((logits > 0) & (logits >= moving_max))[0]
    peaks: list[int] = []
    last = None
    for frame in candidates:
        if last is None or frame - last > 1:
            peaks.append(int(frame))
        last = frame  # a run of equal frames beside a peak is the same beat: its first frame
    return peaks
