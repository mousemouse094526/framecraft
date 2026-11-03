"""Times as people read them: shared by the Transcript files, the prompts that cite lines and
Shots, and the `.srt` of a Transcript and of a render."""

from collections.abc import Iterable


def hms(seconds: float) -> str:
    """`hh:mm:ss` of whole seconds, as the Transcript's `.txt` writes a line's start (spoil D22)."""
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}"


def srt(cues: Iterable[tuple[float, float, str]]) -> str:
    """Standard SRT from `(start, end, text)` in seconds: numbered from 1,
    `hh:mm:ss,mmm --> hh:mm:ss,mmm`, a blank line between cues."""
    return "\n".join(
        f"{number}\n{_srt_time(start)} --> {_srt_time(end)}\n{text}\n"
        for number, (start, end, text) in enumerate(cues, start=1)
    )


def _srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    return f"{hms(millis // 1000)},{millis % 1000:03d}"
