"""Fake project roots and probes shared by the backend tests."""

import json
from pathlib import Path

from backend.checks import FfmpegInfo
from backend.models import MODELS, ModelSpec
from backend.paths import ProjectPaths

MODEL_FILES = {"config.json": 120, "model.safetensors": 4096}


def write_snapshot(root: Path, model: ModelSpec, revision: str | None = None) -> Path:
    """Create the files snapshot_download would leave for one model."""
    snapshot = ProjectPaths(root).snapshot_dir(model, revision or model.revision)
    for name, size in MODEL_FILES.items():
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * size)
    return snapshot


def write_marker(root: Path, model: ModelSpec, revision: str | None = None) -> Path:
    marker = ProjectPaths(root).marker(model)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps(
            {
                "repo_id": model.repo_id,
                "revision": revision or model.revision,
                "files": [{"path": n, "size": s} for n, s in MODEL_FILES.items()],
                "size_bytes": sum(MODEL_FILES.values()),
                "finished_at": "2026-10-29T10:00:00+07:00",
            }
        ),
        encoding="utf-8",
    )
    return marker


def ok_ffmpeg() -> FfmpegInfo:
    return FfmpegInfo(version="7.1", source="imageio-ffmpeg")


def broken_ffmpeg() -> FfmpegInfo:
    raise RuntimeError("ffmpeg -version exited with 1")


def cuda_device() -> str:
    return "cuda"


def item(result, item_id: str):
    return next(i for i in result.items if i.id == item_id)
