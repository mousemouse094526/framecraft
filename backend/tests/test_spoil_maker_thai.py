"""Numbers as Thai words, the letter count, and word cutting (spoil-maker spec › ตัวเลขเป็นคำ)."""

import os
import subprocess
import sys

import pytest

from backend.paths import ProjectPaths
from backend.spoil_maker import thai


def test_the_spec_sentence_reads_every_number_as_words():
    text = "ปี 1968 เวลา 10:30 ราว 50% หรือ 3.25 เท่า ๑๑ คน 114,000 บาท 007"

    assert thai.spoken(text) == (
        "ปี หนึ่งพันเก้าร้อยหกสิบแปด เวลา สิบนาฬิกาสามสิบนาที ราว ห้าสิบเปอร์เซ็นต์ หรือ สามจุดสองห้า"
        " เท่า สิบเอ็ด คน หนึ่งแสนหนึ่งหมื่นสี่พัน บาท ศูนย์ศูนย์เจ็ด"
    )


@pytest.mark.parametrize(
    ("number", "words"),
    [
        ("0", "ศูนย์"),
        ("1", "หนึ่ง"),
        ("10", "สิบ"),
        ("11", "สิบเอ็ด"),
        ("20", "ยี่สิบ"),
        ("21", "ยี่สิบเอ็ด"),
        ("101", "หนึ่งร้อยเอ็ด"),
        ("110", "หนึ่งร้อยสิบ"),
        ("1000000", "หนึ่งล้าน"),
        ("1000001", "หนึ่งล้านเอ็ด"),
        ("21000000", "ยี่สิบเอ็ดล้าน"),
        ("1000000000000", "หนึ่งล้านล้าน"),
    ],
)
def test_whole_numbers_follow_thai_reading(number, words):
    assert thai.spoken(number) == words


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("10:00", "สิบนาฬิกา"),
        ("9:05", "เก้านาฬิกาห้านาที"),
        ("10:30 น. ตรง", "สิบนาฬิกาสามสิบนาที ตรง"),
        ("10.30 น.", "สิบนาฬิกาสามสิบนาที"),
        ("18:00น.", "สิบแปดนาฬิกา"),
        ("1/2", "หนึ่ง/สอง"),
        ("3.5%", "สามจุดห้าเปอร์เซ็นต์"),
        ("0.75", "ศูนย์จุดเจ็ดห้า"),
        ("๑๙๖๘", "หนึ่งพันเก้าร้อยหกสิบแปด"),
        ("ไม่มีตัวเลข", "ไม่มีตัวเลข"),
    ],
)
def test_times_fractions_percents_and_decimals(text, words):
    assert thai.spoken(text) == words


def test_letters_leave_out_spaces_and_punctuation():
    assert thai.letters("ก ข, ค.") == 3
    # Marks above and below a consonant count, the way the TTS trial counted them.
    assert thai.letters("ที่") == 3


def test_words_keep_pythainlp_data_inside_the_project(tmp_path):
    # pythainlp makes its data folder once, at its first use in a process: a fresh one.
    root, home = tmp_path / "framecraft", tmp_path / "home"
    home.mkdir()
    code = (
        "import sys; from pathlib import Path; from backend.paths import ProjectPaths; from backend.spoil_maker import thai;"
        "print(thai.words(ProjectPaths(Path(sys.argv[1])), 'ชายคนหนึ่งตื่นขึ้นมา'))"
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHAINLP_")} | {"HOME": str(home)}
    result = subprocess.run([sys.executable, "-c", code, str(root)], capture_output=True, text=True, env=env, check=True)

    assert result.stdout.strip() == "['ชาย', 'คน', 'หนึ่ง', 'ตื่นขึ้น', 'มา']"
    assert ProjectPaths(root).pythainlp_dir.is_dir()
    assert not (home / "pythainlp-data").exists()


def test_words_keep_the_spaces_after_them(tmp_path):
    project = ProjectPaths(tmp_path / "framecraft")

    assert thai.words(project, "หนัง Night of  the ศพ") == ["หนัง ", "Night ", "of  ", "the ", "ศพ"]


def test_importing_the_module_does_not_import_pythainlp():
    code = "import sys, backend.spoil_maker.thai; print('pythainlp' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)

    assert result.stdout.strip() == "False"
