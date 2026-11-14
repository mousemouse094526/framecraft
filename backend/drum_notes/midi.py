"""A Standard MIDI File's drum track as a Song's `analysis` (drum-notes D10, D20): the app's own
parser, as Drumduino's `importers.ts`, since what it needs is a hundred lines.

Format 0 and 1 with a ticks-per-quarter division; the first tempo and the first time signature of
the file set every time; notes of channel 10 (0-based 9) on the GM percussion map are the hits.
Anything else (SMPTE, no drum track, not 4/4, a tempo or division out of range, too many hits) is
`415` `unsupported_file`; a file longer than a Song may be is `422` `too_long`.
"""

import struct
from dataclasses import dataclass, field
from typing import NamedTuple

from backend.checks import now_iso
from backend.drum_notes.songs import MAX_HITS, MAX_SECONDS, TOO_LONG, Analysis, Hit, Level
from backend.errors import ApiError

DRUM_CHANNEL = 9  # channel 10, counted from 1
BPM_RANGE = (20, 400)
DIVISION_RANGE = (24, 960)
DEFAULT_TEMPO_US = 500_000  # 120 BPM, the file format's default
BEATS_PER_BAR = 4
# Velocity to a hit's level (D9): soft hits ghost, hard ones accent.
GHOST_MAX_VELOCITY = 50
ACCENT_MIN_VELOCITY = 100

NOT_DRUMS_4_4 = "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง"

# GM percussion: note → the app's piece (D10); notes off the map are dropped.
GM_PIECES = {
    35: "kick", 36: "kick",
    38: "snare", 40: "snare",
    42: "hihat_closed",
    44: "hihat_pedal",
    46: "hihat_open",
    49: "crash", 55: "crash", 57: "crash",
    51: "ride", 53: "ride", 59: "ride",
    48: "tom_high", 50: "tom_high",
    45: "tom_mid", 47: "tom_mid",
    41: "tom_floor", 43: "tom_floor",
}  # fmt: skip


class NoteOn(NamedTuple):
    """A note-on of the drum channel, in the file's ticks."""

    tick: int
    note: int
    velocity: int


@dataclass
class Parsed:
    """What the file gave: its first track name, the note-ons in ticks, the tempo and time signature."""

    division: int
    tempo_us: int | None = None
    numerator: int | None = None
    denominator: int | None = None
    track_name: str | None = None
    notes: list[NoteOn] = field(default_factory=list)


@dataclass(frozen=True)
class DrumTrack:
    """A MIDI file read into a Song's terms: its title (None: no track name), its length and analysis."""

    title: str | None
    duration_s: float
    analysis: Analysis


def unsupported() -> ApiError:
    return ApiError(415, "unsupported_file", NOT_DRUMS_4_4)


def read(data: bytes) -> DrumTrack:
    """The file's drum track as an analysis of the whole file: beats on every quarter and downbeats
    on every bar up to one bar after the last hit (D10). Raises `ApiError` 415 or 422."""
    parsed = _parse(data)
    tempo_us = parsed.tempo_us or DEFAULT_TEMPO_US
    bpm = 60_000_000 / tempo_us
    if not BPM_RANGE[0] <= bpm <= BPM_RANGE[1]:
        raise unsupported()
    if (parsed.numerator, parsed.denominator) not in ((None, None), (4, 4)):
        raise unsupported()
    hits = []
    for played in parsed.notes:
        piece = GM_PIECES.get(played.note)
        if piece is not None:
            hits.append(Hit(t=round(played.tick * tempo_us / parsed.division / 1_000_000, 4), piece=piece, level=_level(played.velocity)))
    if not hits:
        raise unsupported()
    if len(hits) > MAX_HITS:
        raise unsupported()
    hits.sort(key=lambda hit: hit.t)
    beat_s = tempo_us / 1_000_000
    bar_s = beat_s * BEATS_PER_BAR
    duration_s = hits[-1].t + bar_s  # the last hit, then one bar (spec › Data)
    if duration_s > MAX_SECONDS:
        raise ApiError(422, "too_long", TOO_LONG)
    # Every quarter up to the end: the bar after the last hit always closes, so each hit is in a bar.
    beats = [round(n * beat_s, 4) for n in range(int(duration_s / beat_s + 1e-9) + 1)]
    downbeats = beats[::BEATS_PER_BAR]
    analysis = Analysis(
        mode="drums", start_s=0.0, end_s=round(duration_s, 4), beats=beats, downbeats=downbeats, hits=hits, picked_at=now_iso()
    )
    return DrumTrack(title=parsed.track_name, duration_s=duration_s, analysis=analysis)


def _level(velocity: int) -> Level:
    if velocity <= GHOST_MAX_VELOCITY:
        return "ghost"
    return "accent" if velocity >= ACCENT_MIN_VELOCITY else "normal"


# --- the bytes ---


def _parse(data: bytes) -> Parsed:
    """The header and every track, in file order; the first tempo, time signature and track name win."""
    if len(data) < 14 or data[:4] != b"MThd":
        raise unsupported()
    header_length, fmt, track_count, division = struct.unpack(">IHHH", data[4:14])
    if fmt not in (0, 1) or division & 0x8000 or not DIVISION_RANGE[0] <= division <= DIVISION_RANGE[1]:
        raise unsupported()  # format 2, SMPTE time, or a division out of range
    parsed = Parsed(division=division)
    at = 8 + header_length
    for _ in range(track_count):
        if data[at : at + 4] != b"MTrk" or len(data) < at + 8:
            raise unsupported()
        (length,) = struct.unpack(">I", data[at + 4 : at + 8])
        track = data[at + 8 : at + 8 + length]
        if len(track) != length:
            raise unsupported()
        _read_track(track, parsed)
        at += 8 + length
    return parsed


def _read_track(track: bytes, parsed: Parsed) -> None:
    at, tick, status = 0, 0, 0
    while at < len(track):
        delta, at = _variable_length(track, at)
        tick += delta
        if at >= len(track):
            raise unsupported()
        byte = track[at]
        if byte == 0xFF:  # meta event
            if at + 2 > len(track):
                raise unsupported()
            kind = track[at + 1]
            length, at = _variable_length(track, at + 2)
            body = track[at : at + length]
            at += length
            if kind == 0x51 and length == 3 and parsed.tempo_us is None:
                parsed.tempo_us = int.from_bytes(body, "big")
            elif kind == 0x58 and length >= 2 and parsed.numerator is None:
                parsed.numerator, parsed.denominator = body[0], 2 ** body[1]
            elif kind == 0x03 and parsed.track_name is None and body.strip():
                parsed.track_name = body.decode("utf-8", errors="replace").strip()
            continue
        if byte in (0xF0, 0xF7):  # sysex: skipped
            length, at = _variable_length(track, at + 1)
            at += length
            continue
        if byte & 0x80:
            status = byte
            at += 1
        elif not status:
            raise unsupported()  # a data byte with no running status
        kind, channel = status & 0xF0, status & 0x0F
        if kind in (0xC0, 0xD0):  # program change, channel pressure: one data byte
            at += 1
            continue
        if at + 2 > len(track):
            raise unsupported()
        first, second = track[at], track[at + 1]
        at += 2
        if kind == 0x90 and second > 0 and channel == DRUM_CHANNEL:
            parsed.notes.append(NoteOn(tick, first, second))


def _variable_length(data: bytes, at: int) -> tuple[int, int]:
    """A variable-length quantity at `at`: its value and the index after it."""
    value = 0
    for _ in range(4):
        if at >= len(data):
            raise unsupported()
        byte = data[at]
        at += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, at
    raise unsupported()
