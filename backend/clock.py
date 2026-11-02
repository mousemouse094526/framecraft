"""Times as people read them: shared by the Transcript files and the prompts that cite lines and Shots."""


def hms(seconds: float) -> str:
    """`hh:mm:ss` of whole seconds, as the Transcript's `.txt` writes a line's start (spoil D22)."""
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}"
