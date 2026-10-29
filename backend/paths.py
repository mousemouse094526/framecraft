"""Where the project, its models, and its media live on disk (ADR 0003)."""

from dataclasses import dataclass
from pathlib import Path

from backend.models import ModelSpec

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def venv_dir(self) -> Path:
        return self.root / ".venv"

    @property
    def models_dir(self) -> Path:
        return self.root / "models"

    @property
    def hub_dir(self) -> Path:
        """The cache_dir passed to every Hugging Face call."""
        return self.models_dir / "hub"

    @property
    def markers_dir(self) -> Path:
        return self.models_dir / ".setup"

    @property
    def setup_lock(self) -> Path:
        return self.markers_dir / "setup.lock"

    @property
    def media_temp_dir(self) -> Path:
        """Where Temp clips live until the user deletes them (spoil D3)."""
        return self.root / "media" / "temp"

    @property
    def partial_dir(self) -> Path:
        """Where yt-dlp writes while downloading; emptied on every start (spoil D14)."""
        return self.media_temp_dir / ".partial"

    def marker(self, model: ModelSpec) -> Path:
        return self.markers_dir / f"{model.cache_name}.json"

    def snapshot_dir(self, model: ModelSpec, revision: str) -> Path:
        """The folder snapshot_download fills for one revision of a model."""
        return self.hub_dir / f"models--{model.cache_name}" / "snapshots" / revision
