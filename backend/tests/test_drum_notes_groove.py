"""The sticking a reel cover plays (drum-notes D13, D20; drum-cover D4): the trim to two hands and
the hand of each note, on hits placed by hand on 16 steps a bar."""

from backend.drum_notes import groove
from backend.drum_notes.groove import Placed
from backend.video_gen import kit


def handed(*hits: tuple[str, int]) -> list:
    """The notes `with_hands` gives after `trimmed`: hits in step then kit order, as `drum_cover.timeline` passes them."""
    placed = sorted((Placed(piece, step, "normal") for piece, step in hits), key=lambda p: (p.step, kit.PIECES.index(kit.BY_ID[p.piece])))
    return groove.with_hands(groove.trimmed(placed))


def test_a_third_hand_note_in_a_step_is_dropped_by_the_keep_order_and_an_open_hihat_beside_a_closed_one_goes():
    notes = handed(("hihat_closed", 0), ("snare", 0), ("crash", 0), ("hihat_open", 0), ("hihat_open", 4), ("hihat_closed", 4), ("kick", 4))

    # Step 0: the open hi-hat goes, then of snare, crash and closed hi-hat the keep order cuts the hi-hat.
    assert sorted((n.piece, n.step) for n in notes) == [("crash", 0), ("hihat_closed", 4), ("kick", 4), ("snare", 0)]


def test_eight_sixteenth_hihats_alternate_hands_from_the_right():
    notes = handed(*(("hihat_closed", step) for step in range(8)))

    assert [note.hand for note in notes] == ["R", "L", "R", "L", "R", "L", "R", "L"]


def test_a_rock_groove_keeps_the_hihat_in_the_right_hand_and_the_snare_in_the_left():
    notes = handed(*(("hihat_closed", step) for step in range(0, 16, 2)), ("snare", 4), ("snare", 12), ("kick", 0), ("kick", 8))

    hands = {(note.piece, note.step): note.hand for note in notes}
    assert all(hands[("hihat_closed", step)] == "R" for step in range(0, 16, 2))
    assert (hands[("snare", 4)], hands[("snare", 12)]) == ("L", "L")
    assert (hands[("kick", 0)], hands[("kick", 8)]) == (None, None)


def test_a_crash_after_a_rest_of_four_steps_is_right_and_a_snare_an_8th_after_a_right_cymbal_is_left():
    notes = handed(("hihat_closed", 0), ("snare", 2), ("crash", 6), ("snare", 12))

    assert [(note.piece, note.step, note.hand) for note in notes] == [
        ("hihat_closed", 0, "R"),
        ("snare", 2, "L"),  # two steps after a right cymbal
        ("crash", 6, "R"),  # four steps after the last hand note: a cymbal, right
        ("snare", 12, "R"),  # six steps after: no cymbal within two
    ]


def test_a_snare_a_16th_after_the_right_hand_hihat_is_the_left_hand_s():
    notes = handed(("hihat_closed", 4), ("snare", 5))

    assert {(n.piece, n.step): n.hand for n in notes}[("snare", 5)] == "L"
