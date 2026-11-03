"""Thai text for the voice: numbers read as words, the letter count speaking speed
is measured in, and word cutting (spoil-maker D20, D35, D36, D44).

`spoken` changes only what OmniVoice reads; scripts, subtitles and `.srt` keep the
digits (D36). pythainlp is imported inside `words` only, after its data folder is
pointed into the project (ADR 0003).
"""

import os
import re
import unicodedata

from backend.paths import ProjectPaths

DIGITS = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
PLACES = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"]  # within one group of six digits

THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
GROUPED = re.compile(r"(?<=\d),(?=\d{3})")
# `10:30`, or `10.30` only when `น.` follows; the `น.` itself is dropped, since นาฬิกา already says it.
TIME = re.compile(r"(\d{1,2})(?::(\d{2})(?:\s*น\.)?|\.(\d{2})\s*น\.)")
PERCENT = re.compile(r"(?<=\d)%")
DECIMAL = re.compile(r"(\d+)\.(\d+)")
NUMBER = re.compile(r"\d+")


def spoken(text: str) -> str:
    """`text` with every number as Thai words, in the spec's order (spec › ตัวเลขเป็นคำ)."""
    text = text.translate(THAI_DIGITS)
    text = GROUPED.sub("", text)
    text = TIME.sub(_time, text)
    text = PERCENT.sub("เปอร์เซ็นต์", text)
    text = DECIMAL.sub(lambda m: f"{_number(m.group(1))}จุด{_digit_by_digit(m.group(2))}", text)
    return NUMBER.sub(lambda m: _number(m.group()), text)


def letters(text: str) -> int:
    """Characters that are neither space nor punctuation, the way the TTS trial counted
    speaking speed (D35): marks above and below a consonant count too."""
    return sum(1 for c in text if not c.isspace() and not unicodedata.category(c).startswith("P"))


def width(text: str) -> int:
    """Letters that take space."""
    return sum(1 for c in text if _takes_space(c))


def cut_width(text: str, limit: int) -> str:
    """`text` cut after `limit` letters that take space."""
    taken = 0
    for index, c in enumerate(text):
        if _takes_space(c):
            taken += 1
            if taken > limit:
                return text[:index].rstrip()
    return text


def words(project: ProjectPaths, text: str) -> list[str]:
    """Thai words by pythainlp's `newmm` dictionary, each with the spaces after it, so
    joined back they are `text` without its leading spaces; nothing written outside the
    project and nothing downloaded (docs/library-notes/pythainlp.md). The Render job
    cuts subtitles and lines with it (D20)."""
    os.environ["PYTHAINLP_DATA"] = str(project.pythainlp_dir)
    os.environ["PYTHAINLP_OFFLINE"] = "1"
    from pythainlp.tokenize import word_tokenize

    found: list[str] = []
    for token in word_tokenize(text, engine="newmm", keep_whitespace=True):
        if token.isspace():
            if found:
                found[-1] += token
        elif token:
            found.append(token)
    return found


def _time(match: re.Match) -> str:
    hours, minutes = int(match.group(1)), int(match.group(2) or match.group(3))
    said = f"{_whole(hours)}นาฬิกา"
    return said if minutes == 0 else f"{said}{_whole(minutes)}นาที"


def _number(digits: str) -> str:
    """A run of digits: `007` digit by digit, anything else as a whole number."""
    if len(digits) > 1 and digits.startswith("0"):
        return _digit_by_digit(digits)
    return _whole(int(digits))


def _digit_by_digit(digits: str) -> str:
    return "".join(DIGITS[int(d)] for d in digits)


def _whole(n: int) -> str:
    """Groups of six digits joined by ล้าน, so 10^12 reads หนึ่งล้านล้าน."""
    if n == 0:
        return DIGITS[0]
    groups = []
    while n:
        n, group = divmod(n, 1_000_000)
        groups.append(group)
    said = ""
    for index in range(len(groups) - 1, -1, -1):
        # The lowest group's 1 reads เอ็ด when any group above it isn't zero (1000001).
        said += _group(groups[index], has_higher=index == 0 and any(groups[1:]))
        if index > 0:
            said += "ล้าน"
    return said


def _group(n: int, has_higher: bool) -> str:
    said = ""
    for place in range(5, -1, -1):
        digit = n // 10**place % 10
        if digit == 0:
            continue
        if place == 1:
            said += {1: "", 2: "ยี่"}.get(digit, DIGITS[digit]) + "สิบ"
        elif place == 0 and digit == 1 and (n > 9 or has_higher):
            said += "เอ็ด"
        else:
            said += DIGITS[digit] + PLACES[place]
    return said


def _takes_space(c: str) -> bool:
    """Thai vowels above and below and tone marks sit on a letter (Unicode Mn, Me)."""
    return unicodedata.category(c) not in ("Mn", "Me")
