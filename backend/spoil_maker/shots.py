"""A described Temp clip's Shots on disk: `media/temp/shots/{id}/shots.json` and a
`{n}.jpg` thumbnail per Shot (spoil-maker spec › Describe job, D17, D51).

Knows no job: `backend.spoil.clips` reads `is_described` from here.
"""

import logging
import math
import shutil

from pydantic import BaseModel, ValidationError

from backend.paths import ProjectPaths

log = logging.getLogger(__name__)

SPLIT_SECONDS = 10  # a longer range is cut into equal pieces no longer than this (D17)
MIN_SECONDS = 1  # a shorter Shot joins its neighbour (D17)
SHOTS_FILE = "shots.json"


class Shot(BaseModel):
    n: int
    start: float
    end: float
    description: str


class ShotsFile(BaseModel):
    clip_id: str
    shots: list[Shot]


def plan_shots(cuts: list[float], duration: float) -> list[tuple[float, float]]:
    """`(start, end)` of every Shot, in order (spec › Describe job step 4):

    1. the range between two cuts is a Shot;
    2. one longer than 10 s becomes `ceil(length / 10)` equal pieces;
    3. one shorter than 1 s joins the Shot before it, the first joins the one after.
    """
    edges = [0.0] + sorted(cut for cut in cuts if 0 < cut < duration) + [duration]
    pieces: list[list[float]] = []
    for start, end in zip(edges, edges[1:]):
        count = max(1, math.ceil((end - start) / SPLIT_SECONDS))
        step = (end - start) / count
        pieces += [[start + step * index, start + step * (index + 1)] for index in range(count)]
    merged: list[list[float]] = []
    for start, end in pieces:
        if merged and end - start < MIN_SECONDS:
            merged[-1][1] = end
        else:
            merged.append([start, end])
    if len(merged) > 1 and merged[0][1] - merged[0][0] < MIN_SECONDS:
        first = merged.pop(0)
        merged[0][0] = first[0]
    return [(start, end) for start, end in merged]


def read_shots(project: ProjectPaths, video_id: str) -> ShotsFile | None:
    """The clip's Shots, or None when it isn't described: no file, a file that
    can't be read, or one for another clip (spec › Describe job)."""
    path = project.clip_shots_dir(video_id) / SHOTS_FILE
    if not path.is_file():
        return None
    try:
        shots = ShotsFile.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        log.warning("skipping unreadable %s", path)
        return None
    return shots if shots.clip_id == video_id else None


def is_described(project: ProjectPaths, video_id: str) -> bool:
    return read_shots(project, video_id) is not None


def clean_on_start(project: ProjectPaths, known_ids: set[str]) -> None:
    """Jobs don't survive a restart: unfinished `.new-{id}/` folders go, and so do
    the Shots of a clip that is gone (spec › Ops)."""
    if not project.shots_dir.is_dir():
        return
    for folder in project.shots_dir.iterdir():
        if folder.is_dir() and (folder.name.startswith(".new-") or folder.name not in known_ids):
            shutil.rmtree(folder, ignore_errors=True)
