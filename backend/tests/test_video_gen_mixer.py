"""The mixed sound of a lesson's timeline (video-gen seam 2 › `mixer`)."""

import io

import numpy as np
import pytest
import soundfile

from backend import drum_kit
from backend.paths import ProjectPaths
from backend.video_gen import mixer, timeline

from .fakes import drum_lesson as lesson
from .fakes import drum_note as note

RATE = 44_100


def hits_of(timing: timeline.Timeline, piece: str) -> list[timeline.Hit]:
    return [hit for hit in timing.hits if hit.piece == piece]


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


def mixed(project: ProjectPaths, timing: timeline.Timeline) -> tuple[np.ndarray, soundfile._SoundFileInfo]:
    wav = mixer.mix(project, timing)
    info = soundfile.info(io.BytesIO(wav))
    audio, _ = soundfile.read(io.BytesIO(wav), dtype="int16")
    return audio, info


def test_the_same_lesson_mixes_the_same_wav_byte_for_byte(project):
    timing = timeline.build(lesson(note("snare", 0, "R", "flam"), note("kick", 8, None, "accent")))

    assert mixer.mix(project, timing) == mixer.mix(project, timing)


def test_the_mix_is_16_bit_44_1_khz_stereo_with_its_peak_at_minus_1_dbfs(project):
    timing = timeline.build(lesson(note("snare", 0), note("kick", 0, None)))

    audio, info = mixed(project, timing)

    assert (info.samplerate, info.channels, info.subtype, info.frames) == (RATE, 2, "PCM_16", timing.samples)
    assert int(np.abs(audio).max()) == round(32767 * 10 ** (-1 / 20))
    assert np.array_equal(audio[:, 0], audio[:, 1])


def test_each_hit_starts_on_its_timeline_sample(project):
    timing = timeline.build(lesson(note("snare", 3), bpm=120))

    audio, _ = mixed(project, timing)

    loud = list(np.flatnonzero(np.abs(audio[:, 0]) > 1000))
    assert loud == [hit.at for hit in timing.hits]


@pytest.mark.parametrize("closer", ["hihat_closed", "hihat_pedal"])
def test_an_open_hi_hat_stops_10_ms_after_the_next_closed_hi_hat_or_foot(project, closer):
    ringing = io.BytesIO()
    soundfile.write(ringing, np.full(RATE, 0.5, dtype=np.float32), RATE, subtype="PCM_16", format="FLAC")
    for sample in drum_kit.SAMPLES:
        if sample.piece == "hihat_open":
            drum_kit.sample_path(project, sample).write_bytes(ringing.getvalue())
    hand = None if closer == "hihat_pedal" else "R"
    timing = timeline.build(lesson(note("hihat_open", 0), note(closer, 4, hand), bpm=120))
    open_at, closed_at = hits_of(timing, "hihat_open")[0].at, hits_of(timing, closer)[-1].at

    audio, _ = mixed(project, timing)

    fade = round(0.01 * RATE)
    assert np.all(audio[open_at + 1 : closed_at, 0] != 0)  # rings until the hi-hat closes
    assert np.abs(audio[closed_at + 1 : closed_at + fade, 0]).max() < np.abs(audio[open_at + 1, 0])
    assert np.all(audio[closed_at + fade : closed_at + 2 * fade, 0] == 0)  # then nothing
