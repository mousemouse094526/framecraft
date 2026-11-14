"""The Status check rows a job's gate checks, as id → (label, check), named once so
every gate reads the checklist the same way (ADR 0009, spoil-maker spec › Status check).
Each check looks its probe and the OS up when it runs, so a test's fakes are the ones it calls."""

from backend import checks, drum_kit, fonts
from backend.errors import Row
from backend.models import ADTOF, BASIC_PITCH, BEAT_THIS, KLEIN, KLEIN_GGUF, OMNIVOICE, ModelSpec
from backend.paths import ProjectPaths

FFMPEG: dict[str, Row] = {"ffmpeg": ("ffmpeg", lambda: checks.check_ffmpeg(checks.probe_ffmpeg))}
# `device` is a warning on `cpu`, which doesn't pass a gate (ADR 0006); on Windows it is
# missing on a card torch has no kernels for, so it gates every GPU job (windows-launch D8).
DEVICE: dict[str, Row] = {
    "device": (
        "Device",
        lambda: checks.device_check(checks.probe_device, checks.this_platform(), checks.probe_gpu)(),
    )
}
# A link's download: yt-dlp and the JS runtime it solves YouTube's challenge with.
LINK_TOOLS: dict[str, Row] = {
    "yt_dlp": ("yt-dlp", lambda: checks.check_version(checks.probe_yt_dlp)),
    "deno": ("Deno", lambda: checks.check_version(checks.probe_deno)),
}
PYTHAINLP: dict[str, Row] = {
    "pythainlp": ("pythainlp", lambda: checks.check_pinned(checks.probe_pythainlp, checks.PYTHAINLP_VERSION))
}


def _qwen_rows(project: ProjectPaths) -> dict[str, Row]:
    """Qwen's rows on the OS this runs on, reading the card once (`checks.qwen_checks`)."""
    probes = checks.real_probes()
    sys_platform = checks.this_platform()
    gpu = checks.read_once(probes.gpu)
    return {"device": ("Device", checks.device_check(probes.device, sys_platform, gpu))} | dict(
        checks.qwen_checks(project, probes, sys_platform, gpu)
    )


def qwen_model(project: ProjectPaths) -> dict[str, Row]:
    """Qwen's files on this OS, which its tokenizer reads too. On Windows the gpu row
    first: setup never downloads them on a card under Qwen's target (windows-launch D9),
    so the refusal names the card, not the files."""
    rows = _qwen_rows(project)
    return {row_id: rows[row_id] for row_id in ("gpu", "model_qwen") if row_id in rows}


def qwen_jobs(project: ProjectPaths) -> dict[str, Row]:
    """What a Describe job and a Draft job need: ffmpeg, the device, and Qwen's rows on
    this OS — gpu, its model and bitsandbytes on Windows; its model and mlx-vlm on a Mac."""
    return FFMPEG | _qwen_rows(project)


def klein(project: ProjectPaths) -> dict[str, Row]:
    """klein's two snapshots and the two packages its child imports (toon spec › Status check)."""
    return {
        KLEIN.check_id: (KLEIN.label, lambda: checks.check_model(project, KLEIN)),
        KLEIN_GGUF.check_id: (KLEIN_GGUF.label, lambda: checks.check_model(project, KLEIN_GGUF)),
    } | checks.klein_packages(checks.real_probes())


def voice(project: ProjectPaths) -> dict[str, Row]:
    """What a Voice job needs: the device, OmniVoice and pythainlp (spoil-maker spec › Status check)."""
    omnivoice: dict[str, Row] = {OMNIVOICE.check_id: (OMNIVOICE.label, lambda: checks.check_model(project, OMNIVOICE))}
    return DEVICE | omnivoice | PYTHAINLP


def _kanit(project: ProjectPaths) -> dict[str, Row]:
    """The font every ASS file's text is set in."""
    return {fonts.CHECK_ID: (fonts.LABEL, lambda: fonts.check_kanit(project))}


def render(project: ProjectPaths, voices_first: bool) -> dict[str, Row]:
    """What every Render job's ffmpeg needs: ffmpeg, Kanit and pythainlp (each spec › Status
    check); a job that voices first adds the Voice job's rows."""
    return FFMPEG | _kanit(project) | PYTHAINLP | (voice(project) if voices_first else {})


# The แกะเพลง tab's imports (drum-notes D7): a link needs yt-dlp and Deno too, a file ffmpeg alone.
SONGS_LINK: dict[str, Row] = FFMPEG | LINK_TOOLS
SONGS_FILE: dict[str, Row] = FFMPEG
ONNXRUNTIME: dict[str, Row] = {"onnxruntime": ("onnxruntime", lambda: checks.onnxruntime_check(checks.real_probes()))}


def _model_row(project: ProjectPaths, model: ModelSpec) -> dict[str, Row]:
    return {model.check_id: (model.label, lambda: checks.check_model(project, model))}


def _pick_rows(project: ProjectPaths, hits_model: ModelSpec) -> dict[str, Row]:
    """What a Pick job needs: the model that hears the hits, Beat This!, onnxruntime and ffmpeg (drum-notes D7, ADR 0043: no `device`)."""
    return _model_row(project, hits_model) | _model_row(project, BEAT_THIS) | ONNXRUNTIME | FFMPEG


def pick_drums(project: ProjectPaths) -> dict[str, Row]:
    """Drums mode: ADTOF hears the hits."""
    return _pick_rows(project, ADTOF)


def pick_melody(project: ProjectPaths) -> dict[str, Row]:
    """Melody mode: Basic Pitch hears the hits (D14)."""
    return _pick_rows(project, BASIC_PITCH)


# The Pick job's gate by `range.mode` (spec › Pick job step 2).
PICK_GATES = {"drums": pick_drums, "melody": pick_melody}


def drum_kit_row(project: ProjectPaths) -> dict[str, Row]:
    """The drum samples, all ฟังจังหวะ needs (video-gen spec › API)."""
    return {drum_kit.CHECK_ID: (drum_kit.LABEL, lambda: drum_kit.check_drum_kit(project))}


def drums(project: ProjectPaths) -> dict[str, Row]:
    """What a drum lesson's Render job needs: the samples, Kanit, ffmpeg and pythainlp (video-gen D11, D22)."""
    return drum_kit_row(project) | _kanit(project) | FFMPEG | PYTHAINLP
