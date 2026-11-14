"""Kanit Bold, the one font every text on a render is drawn in (spoil-maker D21, D45):
pinned to a google/fonts commit and checked by sha256, like a model (ADR 0004).

Setup fetches it, the Status check checks it, the Render job points libass at its folder.
"""

import hashlib
import json
from collections.abc import Callable

from backend import files
from backend.paths import ProjectPaths

CHECK_ID = "font_kanit"
LABEL = "Kanit font"
COMMIT = "130fcfb0ff422fec96b335616b2ca99f91914792"
BASE_URL = f"https://raw.githubusercontent.com/google/fonts/{COMMIT}/ofl/kanit/"
KANIT_SHA256 = {
    "Kanit-Bold.ttf": "5dec5b080dab13de9d2295437c0ff3ec05c9e75587dfc31358c005eb4efa5e70",
    "OFL.txt": "eb998cc5a685b240cdb46a0b5747e70334c8c57bbd7b1f6b044d75719358df67",
}
FETCH_TIMEOUT_SECONDS = 60


def check_kanit(project: ProjectPaths) -> tuple[str, str]:
    """Both files there and the marker naming the pinned sha256 of each (spoil-maker spec › Status check)."""
    try:
        marker = json.loads(project.kanit_marker.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "missing", "ไม่พบ marker ใน models/.setup"
    except ValueError as error:
        return "missing", f"marker เสีย: {error}"
    if not isinstance(marker, dict) or marker.get("files") != KANIT_SHA256:
        return "missing", "sha256 ใน marker ไม่ตรง"
    for name in KANIT_SHA256:
        if not (project.kanit_dir / name).is_file():
            return "missing", f"ไฟล์หาย: {name}"
    return "ok", f"Kanit Bold · {COMMIT[:7]}"


def install_kanit(project: ProjectPaths, fetch: Callable[[str], bytes]) -> None:
    """Fetches both files, checks each sha256, then writes the marker last. A file that
    doesn't match is removed and raises `ValueError`, so setup fails (spec › Modules touched)."""
    project.kanit_dir.mkdir(parents=True, exist_ok=True)
    project.kanit_marker.unlink(missing_ok=True)
    for name, expected in KANIT_SHA256.items():
        content = fetch(BASE_URL + name)
        path = project.kanit_dir / name
        if hashlib.sha256(content).hexdigest() != expected:
            path.unlink(missing_ok=True)
            raise ValueError(f"sha256 ของ {name} ไม่ตรง")
        path.write_bytes(content)
    files.write_marker(project.kanit_marker, KANIT_SHA256)


def fetch_https(url: str) -> bytes:
    from urllib.request import urlopen

    with urlopen(url, timeout=FETCH_TIMEOUT_SECONDS) as response:
        return response.read()
