"""The check every Temp clip's mp4 passes, whether downloaded or imported: h264 `yuv420p`,
aac, short side ≤ 1080 (spoil spec › File import step 4, D54, D55).

Most cases read `ffmpeg -i` output captured from ffmpeg 7.1; one runs the real binary.
"""

import pytest

from backend.spoil import mp4check
from backend.spoil.mp4check import Mp4Info, NotPlayable

from .fakes import make_test_clip

HEADER = """Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'a.mp4':
  Metadata:
    major_brand     : isom
  Duration: 00:01:02.50, start: 0.000000, bitrate: 129 kb/s
"""
H264 = (
    "  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(progressive), "
    "1920x1080 [SAR 1:1 DAR 16:9], 50 kb/s, 10 fps, 10 tbr, 10240 tbn (default)\n"
    "      Metadata:\n"
    "        handler_name    : VideoHandler\n"
)
AAC = (
    "  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, mono, fltp, 69 kb/s (default)\n"
    "      Metadata:\n"
    "        handler_name    : SoundHandler\n"
)
COVER = (
    "  Stream #0:0[0x0]: Video: mjpeg (Baseline), yuvj420p(pc, bt470bg/unknown/unknown), "
    "3000x3000 [SAR 1:1 DAR 1:1], 90k tbr, 90k tbn (attached pic)\n"
)
END = "At least one output file must be specified\n"


def stderr(*streams: str, header: str = HEADER) -> str:
    return header + "".join(streams) + END


def test_h264_yuv420p_with_aac_passes_with_its_size_and_length():
    assert mp4check.read_streams(stderr(H264, AAC)) == Mp4Info(duration_s=62.5, width=1920, height=1080)


def test_no_sound_passes():
    assert mp4check.read_streams(stderr(H264)).width == 1920


def test_another_container_with_the_same_streams_is_not_mp4():
    matroska = HEADER.replace("mov,mp4,m4a,3gp,3g2,mj2", "matroska,webm")

    with pytest.raises(NotPlayable) as raised:
        mp4check.read_streams(stderr(H264, AAC, header=matroska))

    assert raised.value.reason == "ไฟล์ไม่ใช่ mp4"


def test_a_cover_image_before_the_video_is_skipped():
    assert mp4check.read_streams(stderr(COVER, H264, AAC)).width == 1920


@pytest.mark.parametrize("angle", ["90.00", "-90.00", "270.00"])
def test_a_quarter_turn_swaps_width_and_height(angle):
    rotated = H264 + f"      Side data:\n        displaymatrix: rotation of {angle} degrees\n"

    found = mp4check.read_streams(stderr(rotated, AAC))

    assert (found.width, found.height) == (1080, 1920)


def test_an_old_rotate_tag_swaps_width_and_height():
    rotated = H264 + "        rotate          : 90\n"

    assert mp4check.read_streams(stderr(rotated)).width == 1080


def test_a_half_turn_keeps_width_and_height():
    rotated = H264 + "      Side data:\n        displaymatrix: rotation of -180.00 degrees\n"

    assert mp4check.read_streams(stderr(rotated)).width == 1920


def test_rotation_of_the_audio_stream_does_not_count():
    # Side data under the audio stream belongs to it, not to the picture.
    audio = AAC + "      Side data:\n        displaymatrix: rotation of 90.00 degrees\n"

    assert mp4check.read_streams(stderr(H264, audio)).width == 1920


@pytest.mark.parametrize(
    ("streams", "reason"),
    [
        ((H264.replace("h264 (High) (avc1 / 0x31637661)", "hevc (Main) (hvc1 / 0x31637668)"), AAC), "ภาพเป็น hevc"),
        ((H264.replace("1920x1080", "1920x1440"), AAC), "ภาพ 1920×1440 ด้านสั้นเกิน 1080"),
        ((H264.replace("1920x1080", "2160x3840"), AAC), "ภาพ 2160×3840 ด้านสั้นเกิน 1080"),
        ((H264, AAC.replace("aac (LC) (mp4a / 0x6134706D)", "opus (Opus / 0x7375704F)")), "เสียงเป็น opus"),
        ((H264.replace("yuv420p(progressive)", "yuv422p10le(progressive)"), AAC), "ภาพเป็น h264 แบบ yuv422p10le"),
        ((AAC,), "อ่านไฟล์ไม่ได้"),
        ((COVER, AAC), "อ่านไฟล์ไม่ได้"),
    ],
)
def test_a_file_outside_the_rule_says_which_part(streams, reason):
    with pytest.raises(NotPlayable) as raised:
        mp4check.read_streams(stderr(*streams))

    assert raised.value.reason == reason


def test_a_second_audio_track_that_is_not_aac_fails():
    second = AAC.replace("#0:1", "#0:2").replace("aac (LC) (mp4a / 0x6134706D)", "ac3")

    with pytest.raises(NotPlayable) as raised:
        mp4check.read_streams(stderr(H264, AAC, second))

    assert raised.value.reason == "เสียงเป็น ac3"


def test_a_file_without_a_length_cant_be_read():
    no_length = HEADER.replace("00:01:02.50", "N/A")

    with pytest.raises(NotPlayable) as raised:
        mp4check.read_streams(stderr(H264, AAC, header=no_length))

    assert raised.value.reason == "อ่านไฟล์ไม่ได้"


def test_junk_named_mp4_cant_be_read():
    junk = (
        "[mov,mp4,m4a,3gp,3g2,mj2 @ 0x11d619be0] moov atom not found\n"
        "Error opening input file junk.mp4.\n"
    )

    with pytest.raises(NotPlayable) as raised:
        mp4check.read_streams(junk)

    assert raised.value.reason == "อ่านไฟล์ไม่ได้"


def test_the_real_ffmpeg_reads_a_lavfi_clip(tmp_path):
    clip = make_test_clip(tmp_path / "a.mp4", colors=("red", "white"))

    found = mp4check.check(clip)

    assert (found.width, found.height) == (320, 180)
    assert found.duration_s == pytest.approx(2, abs=0.1)
