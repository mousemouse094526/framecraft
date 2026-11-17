"""The kalimba samples `kalimba_cover.sound` plays (kalimba-cover D18, ADR 0042, ADR 0061): 14
plucks of VCSL's "Kalimba, Tanzania" (CC0 1.0), one velocity layer, pinned to a commit and checked
by sha256 like the drum samples (`backend.drum_kit`).

Each file is named in the C3 = MIDI 60 scheme, so its note is one octave above what the name says
in MIDI's C4 = 60; `pitch` is the pitch its tine really rings at, measured from the recording, as a fractional MIDI number. The mbira is not
tuned to C major: `sound` moves the nearest sample to each tine's pitch. Only the 14 that are
nearest to a tine somewhere in C4–E6 are fetched, not the set's 27.

Setup fetches them, the Status check checks them, `kalimba_cover.sound` reads them.
"""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote

from backend import files
from backend.paths import ProjectPaths

CHECK_ID = "kalimba_kit"
LABEL = "Kalimba samples"
COMMIT = "c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e"
BASE_URL = f"https://raw.githubusercontent.com/sgossner/VCSL/{COMMIT}/{quote('Idiophones/Plucked Idiophones/Kalimba, Tanzania')}/"
TRIES = 3


class Sample(NamedTuple):
    """One pluck: its file in the repo's folder, the pitch its tine rings at and its sha256."""

    path: str
    pitch: float
    sha256: str


# Measured by the strongest peak of each recording's first 0.6 s, within a semitone of its name's
# MIDI number + 12.
SAMPLES: tuple[Sample, ...] = (
    Sample("MBira3_pluck_Main_C#3_k16_50_100_rr2.wav", 60.55, "8bf3cbb5812176bd37529babb994123667fa410a837159549795e573e59b8906"),
    Sample("MBira3_pluck_Main_D#3_k7_50_100_rr2.wav", 63.50, "fa56975960f9dc2dce8b092cf80fd77a18c8273e4a880d62996576a95176a7af"),
    Sample("MBira3_pluck_Main_F3_k17_50_100_rr2.wav", 65.39, "1dd82312d3202a7cb8e28efe0cbe9e8c1bb3bc65b6a9916da709d169e2491b14"),
    Sample("MBira3_pluck_Main_G3_k6_50_100_rr2.wav", 67.16, "f66bcdf337dec1ef6a73aad8dc3e3345a91e37e27679aaa60b640b26f5be1c4c"),
    Sample("MBira3_pluck_Main_A#3_k18_50_100_rr2.wav", 70.51, "4982936107dca7fbe370c1f78e3a8c2c609e0700938ff4a391fc7ecdf7c3523d"),
    Sample("MBira3_pluck_Main_C#4_k5_50_100_rr2.wav", 73.09, "2d2be2152d784f8013ded81ff863f4d0c5775d546bc1d61723d0c04f25426e45"),
    Sample("MBira3_pluck_Main_D4_k19_50_100_rr2.wav", 73.51, "c9b6034cec0ad70c483ac0db87f48f33a5421e2cf594ed590e405a126cfd43c5"),
    Sample("MBira3_pluck_Main_D#4_k4_50_100_rr2.wav", 75.33, "f2fa1fe9513e2552ad60b610e5553d1651c11912d74a1d3e2301d4400ea544b5"),
    Sample("MBira3_pluck_Main_F4_k3_50_100_rr2.wav", 77.26, "5e232c1abdb50b917b25a6193304efea29a200a39d2add3eaa44e49de00a891d"),
    Sample("MBira3_pluck_Main_G4_k22_50_100_rr2.wav", 79.33, "59fef12af5bf667cd7b3d12454e62377ac47f6893de416fc9f6e12f30043495b"),
    Sample("MBira3_pluck_Main_A#4_k2_50_100_rr2.wav", 82.48, "8b536bc1941c6a674c59cb3d6f4a3c0c1581b22df0948fa140165aaa0b8abf49"),
    Sample("MBira3_pluck_Main_B4_k23_50_100_rr2.wav", 82.57, "ae7d7acce2ea9a222f8105542ba940bb546876c3cbaa23fec790cbc9c7731fc1"),
    Sample("MBira3_pluck_Main_C#5_k24_50_100_rr2.wav", 85.38, "81cad929b42f5177bbe5d09da860725d2cf5304d2d0fe32443523ef09e508ef3"),
    Sample("MBira3_pluck_Main_E5_k25_50_100_rr2.wav", 87.78, "becb36f0ad9f00ffab16f70bed644e40eada202dc839eee29bc7012953ab5bb9"),
)


def sample_path(project: ProjectPaths, sample: Sample) -> Path:
    return project.kalimba_samples_dir / sample.path


def nearest(pitch: int) -> Sample:
    """The sample whose tine rings closest to `pitch`; a tie takes the higher, moved down."""
    return min(SAMPLES, key=lambda sample: (abs(sample.pitch - pitch), -sample.pitch))


def check_kalimba_kit(project: ProjectPaths) -> tuple[str, str]:
    """Every file there and the marker naming the pinned sha256 of each. Writes nothing."""
    try:
        marker = json.loads(project.kalimba_kit_marker.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "missing", "ไม่พบ marker ใน models/.setup"
    except ValueError as error:
        return "missing", f"marker เสีย: {error}"
    if not isinstance(marker, dict) or marker.get("files") != _pinned():
        return "missing", "sha256 ใน marker ไม่ตรง"
    for sample in SAMPLES:
        if not sample_path(project, sample).is_file():
            return "missing", f"ไฟล์หาย: {sample.path}"
    return "ok", f"VCSL Kalimba, Tanzania · {COMMIT[:7]}"


def install_kalimba_kit(project: ProjectPaths, fetch: Callable[[str], bytes]) -> None:
    """Fetches every file that is missing or doesn't match its sha256, up to TRIES times each,
    then writes the marker last. A file that fails every try raises `RuntimeError` naming it,
    and no marker is written (the drum kit's rule, `drum_kit.install_drum_kit`)."""
    project.kalimba_kit_marker.unlink(missing_ok=True)
    project.kalimba_samples_dir.mkdir(parents=True, exist_ok=True)
    for sample in SAMPLES:
        path = sample_path(project, sample)
        if path.is_file() and _sha256(path.read_bytes()) == sample.sha256:
            continue
        _fetch_checked(sample, path, fetch)
    files.write_marker(project.kalimba_kit_marker, _pinned())


def _fetch_checked(sample: Sample, path: Path, fetch: Callable[[str], bytes]) -> None:
    problem = ""
    for _ in range(TRIES):
        try:
            content = fetch(BASE_URL + quote(sample.path))
        except OSError as error:
            problem = str(error)
            continue
        if _sha256(content) == sample.sha256:
            path.write_bytes(content)
            return
        problem = "sha256 ไม่ตรง"
    path.unlink(missing_ok=True)
    raise RuntimeError(f"โหลด {sample.path} ไม่สำเร็จ {TRIES} ครั้ง ({problem})")


def _pinned() -> dict[str, str]:
    return {sample.path: sample.sha256 for sample in SAMPLES}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
