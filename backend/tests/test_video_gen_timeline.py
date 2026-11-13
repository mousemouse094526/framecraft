"""A lesson's timeline and its mixed sound (video-gen seam 2 › `timeline.build`, `mixer`)."""

import io

import numpy as np
import pytest
import soundfile

from backend import drum_kit
from backend.paths import ProjectPaths
from backend.video_gen import mixer, timeline

from .fakes import drum_chapter as chapter
from .fakes import drum_lesson as lesson
from .fakes import drum_note as note

RATE = 44_100


def hits_of(played: timeline.Timeline, piece: str) -> list[timeline.Hit]:
    return [hit for hit in played.hits if hit.piece == piece]


# --- timeline.build ---


def test_a_half_speed_first_chapter_counts_in_for_four_seconds_and_its_notes_follow():
    played = timeline.build(lesson(note("snare", 2), note("tom_high", 4), bpm=120, chapters=[chapter(speed=50)]))

    assert [hit.at for hit in hits_of(played, "hihat_closed")] == [0, RATE, 2 * RATE, 3 * RATE]
    assert {hit.layer for hit in hits_of(played, "hihat_closed")} == {"soft"}
    assert played.chapters[0].start == 4 * RATE
    # a 16th is 0.25 s at 60 BPM: step 2 at 4.5 s, step 4 at 5.0 s
    assert hits_of(played, "snare")[0].at == round(4.5 * RATE)
    assert hits_of(played, "tom_high")[0].at == 5 * RATE


def test_a_flam_is_a_soft_grace_note_with_the_other_hand_30_ms_before_the_main_one():
    played = timeline.build(lesson(note("snare", 0, "R", "flam")))

    grace, main = hits_of(played, "snare")
    assert main.at - grace.at == round(0.03 * RATE)
    assert (grace.hand, grace.layer) == ("L", "soft")
    assert (main.hand, main.layer) == ("R", "mid")


def test_accent_normal_and_ghost_play_the_hard_mid_and_soft_layers():
    played = timeline.build(lesson(note("snare", 0, "R", "accent"), note("snare", 4, "R"), note("snare", 8, "R", "ghost")))

    assert [hit.layer for hit in hits_of(played, "snare")] == ["hard", "mid", "soft"]


def test_round_robins_cycle_per_piece_and_layer_from_the_clip_s_start():
    notes = [note("snare", step, "L") for step in (0, 4, 8, 12)] + [note("ride", step, "R") for step in (0, 4, 8, 12)]
    played = timeline.build(lesson(*notes, chapters=[chapter(repeats=2)]))

    assert [hit.round_robin for hit in hits_of(played, "snare")] == [1, 2, 3, 4, 1, 2, 3, 4]
    # the ride has three round-robins per layer
    assert [hit.round_robin for hit in hits_of(played, "ride")] == [1, 2, 3, 1, 2, 3, 1, 2]
    # the count-in's soft hi-hats don't touch the snare's count
    assert [hit.round_robin for hit in hits_of(played, "hihat_closed")] == [1, 2, 3, 4]


def test_length_counts_the_count_in_every_chapter_and_a_1_5_s_tail():
    played = timeline.build(lesson(bpm=100, bars=2, chapters=[chapter(repeats=2, speed=75), chapter(repeats=1)]))

    # count-in 4 × 0.8 s, then 2 × 2 bars × 3.2 s, then 2 bars × 2.4 s, then the tail
    assert played.length_s == pytest.approx(3.2 + 12.8 + 4.8 + 1.5)
    assert played.samples == round((3.2 + 12.8 + 4.8 + 1.5) * RATE)
    assert [(span.start, span.end) for span in played.chapters] == [
        (round(3.2 * RATE), round(16.0 * RATE)),
        (round(16.0 * RATE), round(20.8 * RATE)),
    ]


def test_every_bar_has_four_beats_numbered_after_the_count_in():
    played = timeline.build(lesson(bpm=120, bars=2))

    assert [beat.number for beat in played.beats] == [1, 2, 3, 4] * 3
    assert played.beats[4].at == round(2.0 * RATE)


# --- mixer ---


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


def mixed(project: ProjectPaths, played: timeline.Timeline) -> tuple[np.ndarray, soundfile._SoundFileInfo]:
    wav = mixer.mix(project, played)
    info = soundfile.info(io.BytesIO(wav))
    audio, _ = soundfile.read(io.BytesIO(wav), dtype="int16")
    return audio, info


def test_the_same_lesson_mixes_the_same_wav_byte_for_byte(project):
    played = timeline.build(lesson(note("snare", 0, "R", "flam"), note("kick", 8, None, "accent")))

    assert mixer.mix(project, played) == mixer.mix(project, played)


def test_the_mix_is_16_bit_44_1_khz_stereo_with_its_peak_at_minus_1_dbfs(project):
    played = timeline.build(lesson(note("snare", 0), note("kick", 0, None)))

    audio, info = mixed(project, played)

    assert (info.samplerate, info.channels, info.subtype, info.frames) == (RATE, 2, "PCM_16", played.samples)
    assert int(np.abs(audio).max()) == round(32767 * 10 ** (-1 / 20))
    assert np.array_equal(audio[:, 0], audio[:, 1])


def test_each_hit_starts_on_its_timeline_sample(project):
    played = timeline.build(lesson(note("snare", 3), bpm=120))

    audio, _ = mixed(project, played)

    loud = list(np.flatnonzero(np.abs(audio[:, 0]) > 1000))
    assert loud == [hit.at for hit in played.hits]


def test_an_open_hi_hat_stops_10_ms_after_the_next_closed_hi_hat(project):
    ringing = io.BytesIO()
    soundfile.write(ringing, np.full(RATE, 0.5, dtype=np.float32), RATE, subtype="PCM_16", format="FLAC")
    for sample in drum_kit.SAMPLES:
        if sample.piece == "hihat_open":
            drum_kit.sample_path(project, sample).write_bytes(ringing.getvalue())
    played = timeline.build(lesson(note("hihat_open", 0), note("hihat_closed", 4), bpm=120))
    open_at, closed_at = hits_of(played, "hihat_open")[0].at, hits_of(played, "hihat_closed")[-1].at

    audio, _ = mixed(project, played)

    fade = round(0.01 * RATE)
    assert np.all(audio[open_at + 1 : closed_at, 0] != 0)  # rings until the hi-hat closes
    assert np.abs(audio[closed_at + 1 : closed_at + fade, 0]).max() < np.abs(audio[open_at + 1, 0])
    assert np.all(audio[closed_at + fade : closed_at + 2 * fade, 0] == 0)  # then nothing
