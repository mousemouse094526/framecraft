"""A song's melody notes laid on a 17-tine C-major kalimba (kalimba-cover seam 2; spec › การจัดโน้ตลงคาลิมบา,
D4, D14): the spec's examples, by hand-written notes."""

from backend.drum_notes.songs import Note
from backend.kalimba_cover import arrange


def notes(*timed: tuple[float, int]) -> list[Note]:
    return [Note(t=t, pitch=pitch, level="normal") for t, pitch in timed]


def pitches(arranged: arrange.Arranged) -> list[int]:
    return [note.pitch for note in arranged.notes]


def test_the_tines_go_from_d6_on_the_left_to_e6_on_the_right_with_c4_in_the_middle():
    assert arrange.TINES == (86, 83, 79, 76, 72, 69, 65, 62, 60, 64, 67, 71, 74, 77, 81, 84, 88)
    assert arrange.TINES.index(60) == 8


def test_three_notes_below_the_kalimba_move_the_least_key_and_fold_up_an_octave():
    arranged = arrange.arranged(notes((10.0, 56), (10.5, 58), (11.0, 60)), 10.0, 12.0)

    # k −1, −3 and +4 all put the three in the scale: −1 moves least.
    assert (arranged.transpose, pitches(arranged), arranged.dropped, arranged.bent) == (-1, [67, 69, 71], 0, 0)


def test_a_chord_keeps_its_top_note():
    arranged = arrange.arranged(notes((10.0, 60), (10.0, 64), (10.01, 67), (10.02, 72)), 10.0, 12.0)

    assert (pitches(arranged), arranged.dropped, arranged.transpose) == ([72], 3, 0)


def test_c3_is_not_bass_but_under_c4_it_is_a_chord_s_lower_note_and_dropped():
    arranged = arrange.arranged(notes((10.0, 48), (10.0, 60)), 10.0, 12.0)

    assert (pitches(arranged), arranged.dropped) == ([60], 1)


def test_the_bass_under_a_melody_is_dropped_before_the_key_is_chosen():
    melody = [(10.0 + n * 0.5, pitch) for n, pitch in enumerate((76, 74, 72) * 2)]
    bass = [(10.0 + n * 0.5, 36) for n in range(6)]
    arranged = arrange.arranged(notes(*melody, *bass), 10.0, 13.0)

    assert (pitches(arranged), arranged.dropped, arranged.transpose) == ([76, 74, 72] * 2, 6, 0)


def test_one_tine_twice_within_80_ms_keeps_the_first():
    arranged = arrange.arranged(notes((10.0, 60), (10.05, 60), (10.2, 60)), 10.0, 12.0)

    assert ([note.t for note in arranged.notes], arranged.dropped) == ([10.0, 10.2], 1)


def test_a_lone_sharp_ties_between_down_and_up_and_goes_up():
    arranged = arrange.arranged(notes((10.0, 61)), 10.0, 12.0)

    assert (arranged.transpose, pitches(arranged), arranged.bent) == (1, [62], 0)


def test_a_note_off_the_scale_after_the_move_goes_down_a_semitone_and_is_counted():
    # C, F, F#, G: k 0 holds three as k −5, −3, −1, +2, +4 and +5 do, and moves least; the F# bends down to F.
    arranged = arrange.arranged(notes((10.0, 60), (10.5, 65), (11.0, 66), (11.5, 67)), 10.0, 12.0)

    assert (arranged.transpose, pitches(arranged), arranged.bent) == (0, [60, 65, 65, 67], 1)


def test_notes_above_e6_fold_down_and_notes_out_of_the_stretch_are_not_counted():
    arranged = arrange.arranged(notes((9.0, 60), (10.0, 91), (10.5, 100), (12.0, 60)), 10.0, 12.0)

    assert (pitches(arranged), arranged.dropped) == ([79, 88], 0)


def test_no_notes_is_no_move():
    arranged = arrange.arranged([], 10.0, 12.0)

    assert arranged == arrange.Arranged(notes=[], transpose=0, dropped=0, bent=0)
