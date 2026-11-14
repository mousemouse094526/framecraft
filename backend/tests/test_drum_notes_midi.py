"""A MIDI file's drum track as a Song's analysis (drum-notes seam 2 › MIDI, D10, D20): files are
built with `struct` in the tests, never a `.mid` in git (spec › Testing decisions)."""

import struct

import pytest

from backend.drum_notes import midi
from backend.errors import ApiError

from .fakes import BEAT, ROCK, meta, midi_file, notes_track, tempo_meta, time_signature, track


def refused(data: bytes) -> ApiError:
    with pytest.raises(ApiError) as caught:
        midi.read(data)
    return caught.value


# --- a drum track ---


def test_channel_10_notes_at_100_bpm_are_hits_of_the_gm_pieces_in_bars_of_2_4_s():
    found = midi.read(midi_file(ROCK, bpm=100, name=b"Rock beat"))

    assert found.title == "Rock beat"
    assert [(hit.piece, hit.t) for hit in found.analysis.hits] == [
        ("kick", 0.0), ("hihat_closed", 0.0), ("hihat_closed", 0.6), ("snare", 1.2), ("hihat_closed", 1.2), ("hihat_closed", 1.8)
    ]  # fmt: skip
    assert {hit.level for hit in found.analysis.hits} == {"accent"}  # velocity 110
    # the last hit at 1.8 s, then one bar: 4.2 s; beats every 0.6 s up to it, downbeats every 2.4 s
    assert found.duration_s == pytest.approx(4.2)
    assert found.analysis.beats == [0.0, 0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2]
    assert found.analysis.downbeats == [0.0, 2.4]
    assert (found.analysis.mode, found.analysis.start_s, found.analysis.end_s) == ("drums", 0.0, 4.2)


def test_velocity_sets_the_level_and_notes_off_the_gm_map_are_dropped():
    found = midi.read(midi_file([(0, 36, 40), (BEAT, 38, 80), (2 * BEAT, 49, 127), (3 * BEAT, 60, 100)]))

    assert [(hit.piece, hit.level) for hit in found.analysis.hits] == [("kick", "ghost"), ("snare", "normal"), ("crash", "accent")]


GM_MAP = {
    35: "kick", 36: "kick", 38: "snare", 40: "snare", 42: "hihat_closed", 44: "hihat_pedal", 46: "hihat_open",
    49: "crash", 55: "crash", 57: "crash", 51: "ride", 53: "ride", 59: "ride",
    48: "tom_high", 50: "tom_high", 45: "tom_mid", 47: "tom_mid", 41: "tom_floor", 43: "tom_floor",
}  # fmt: skip


def test_the_whole_gm_map_covers_the_ten_pieces():
    """The map of D10, note by note; 37 (side stick) and 60 (hi bongo) are dropped."""
    notes = [*sorted(GM_MAP), 37, 60]
    found = midi.read(midi_file([(index * BEAT, note, 100) for index, note in enumerate(notes)]))

    assert [hit.piece for hit in found.analysis.hits] == [GM_MAP[note] for note in sorted(GM_MAP)]


def test_a_format_0_file_with_running_status_and_no_track_name_reads_the_same_with_no_title():
    events = b"\x00" + tempo_meta(100) + b"\x00" + time_signature() + notes_track(ROCK, running_status=True)
    data = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) + track(events)

    found = midi.read(data)

    assert found.title is None
    assert [hit.t for hit in found.analysis.hits] == [0.0, 0.0, 0.6, 1.2, 1.2, 1.8]


def test_a_file_with_no_tempo_is_120_bpm():
    data = b"MThd" + struct.pack(">IHHH", 6, 1, 1, 480) + track(notes_track([(0, 36, 100), (BEAT, 38, 100)]))

    found = midi.read(data)

    assert [hit.t for hit in found.analysis.hits] == [0.0, 0.5]
    assert found.analysis.downbeats == [0.0, 2.0]


# --- refused files (D20) ---


@pytest.mark.parametrize(
    "data",
    [
        midi_file(ROCK, signature=(3, 2)),  # 3/4
        midi_file(ROCK, channel=0),  # no channel 10
        midi_file(ROCK, bpm=1000),
        midi_file(ROCK, bpm=10),
        midi_file(ROCK, division=10),
        midi_file(ROCK, smpte=True),
        b"MThd" + struct.pack(">IHHH", 6, 2, 1, 480) + track(notes_track(ROCK)),  # format 2
        midi_file([(index * 12, 36, 100) for index in range(20_001)]),  # 20,001 hits
        b"RIFF not a midi file",
        midi_file(ROCK)[:-10],  # cut short
    ],
    ids=["3/4", "no drum track", "1000 BPM", "10 BPM", "division 10", "SMPTE", "format 2", "20,001 hits", "junk", "truncated"],
)
def test_a_file_that_is_not_a_4_4_drum_track_is_unsupported_file(data):
    error = refused(data)

    assert (error.status, error.code, error.message) == (415, "unsupported_file", "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง")


def test_twenty_thousand_hits_are_still_read():
    found = midi.read(midi_file([(index * 12, 36, 100) for index in range(20_000)]))

    assert len(found.analysis.hits) == 20_000


def test_a_track_ending_after_ten_minutes_is_too_long():
    error = refused(midi_file([(0, 36, 100), (BEAT * 4 * 250, 36, 100)], bpm=100))  # bar 250 starts at 600 s

    assert (error.status, error.code, error.message) == (422, "too_long", "เพลงยาวเกิน 10 นาที")


def test_a_track_ending_right_at_ten_minutes_is_not():
    found = midi.read(midi_file([(0, 36, 100), (BEAT * 4 * 249, 36, 100)], bpm=100))  # 597.6 s + one bar

    assert found.duration_s == pytest.approx(600.0)
