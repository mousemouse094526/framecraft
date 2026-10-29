"""The Windows wrappers (setup.cmd, setup.ps1) can't run on a Mac; running them
is checked by hand on Windows. These pin the two things the spec fixes in their
text."""

from backend.paths import ROOT

SETUP_CMD = ROOT / "setup.cmd"
SETUP_PS1 = ROOT / "setup.ps1"


def test_setup_ps1_is_ascii_only():
    # Windows PowerShell 5.1 reads a UTF-8 file without a BOM as the ANSI code page.
    non_ascii = [
        (number, line)
        for number, line in enumerate(SETUP_PS1.read_bytes().splitlines(), start=1)
        if any(byte > 0x7F for byte in line)
    ]
    assert non_ascii == []


def test_setup_cmd_switches_to_utf8_then_runs_setup_ps1_bypassing_the_policy():
    lines = [line.strip() for line in SETUP_CMD.read_text(encoding="ascii").splitlines()]

    utf8 = lines.index("chcp 65001 >nul")
    run = lines.index(
        'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"'
    )
    assert utf8 < run
