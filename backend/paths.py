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

    def clip_json(self, clip_id: str) -> Path:
        """A Temp clip's `{id}.json`, written last: no json, no clip (spoil D14)."""
        return self.media_temp_dir / f"{clip_id}.json"

    @property
    def shots_dir(self) -> Path:
        """Shots of every described Temp clip, one folder each (spoil-maker D51)."""
        return self.media_temp_dir / "shots"

    def clip_shots_dir(self, clip_id: str) -> Path:
        """A described clip's `shots.json` and `{n}.jpg` thumbnails."""
        return self.shots_dir / clip_id

    def new_shots_dir(self, clip_id: str) -> Path:
        """Where a Describe job writes until it is `done`, so the old shots stay till then (D51)."""
        return self.shots_dir / f".new-{clip_id}"

    @property
    def episodes_dir(self) -> Path:
        """Each described Temp clip's EP cuts, `{id}.json` (spoil-maker spec › EP, ADR 0018)."""
        return self.media_temp_dir / "episodes"

    def episodes_file(self, clip_id: str) -> Path:
        return self.episodes_dir / f"{clip_id}.json"

    @property
    def pythainlp_dir(self) -> Path:
        """pythainlp's data folder, instead of `~/pythainlp-data` (spoil-maker spec › Library assumptions)."""
        return self.models_dir / "pythainlp"

    @property
    def spoil_maker_dir(self) -> Path:
        """Everything the สปอย tab keeps that isn't a Temp clip's (spoil-maker spec › Ops)."""
        return self.root / "media" / "spoil-maker"

    @property
    def voices_dir(self) -> Path:
        """Saved voices: `{voice_id}.json`, `.pt` and `.wav` each (spoil-maker spec › Saved voice)."""
        return self.spoil_maker_dir / "voices"

    @property
    def pending_voice_dir(self) -> Path:
        """The one preview not saved yet; emptied on every start."""
        return self.voices_dir / ".pending"

    @property
    def draft_file(self) -> Path:
        """The one Spoil draft (spoil-maker spec › Spoil draft, D28)."""
        return self.spoil_maker_dir / "draft.json"

    @property
    def draft_audio_dir(self) -> Path:
        """The Spoil draft's voice, one `{sentence_id}.wav` per sentence."""
        return self.spoil_maker_dir / "draft-audio"

    @property
    def renders_dir(self) -> Path:
        """Every finished render: `{name}.mp4`, `.srt` and `.json` (spoil-maker D42)."""
        return self.spoil_maker_dir / "renders"

    @property
    def render_work_dir(self) -> Path:
        """The running render's pieces, voice and ASS file; removed when it ends."""
        return self.spoil_maker_dir / ".render"

    @property
    def settings_file(self) -> Path:
        """What the สปอย tab remembers between drafts (spoil-maker spec › ค่าที่จำไว้)."""
        return self.spoil_maker_dir / "settings.json"

    @property
    def stories_dir(self) -> Path:
        """The คลังความรู้ tab's Stories, `{story_id}.json` each (story-kb spec › Data, D12)."""
        return self.root / "media" / "stories"

    @property
    def clip_stories_file(self) -> Path:
        """The Story each Temp clip remembers, `{clip_id: story_id}` (story-kb D3, D15)."""
        return self.stories_dir / "clip-stories.json"

    @property
    def kanit_dir(self) -> Path:
        """Kanit Bold and its license, the font of every render (spoil-maker D21)."""
        return self.models_dir / "fonts" / "kanit"

    @property
    def kanit_marker(self) -> Path:
        """Written by setup once both Kanit files match their sha256."""
        return self.markers_dir / "font_kanit"

    @property
    def toon_dir(self) -> Path:
        """Everything the การ์ตูนเล่า tab keeps (toon spec › ข้อมูล, ADR 0003)."""
        return self.root / "media" / "toon"

    @property
    def toon_series_dir(self) -> Path:
        return self.toon_dir / "series"

    def series_dir(self, series_id: str) -> Path:
        """A Series' `series.json`, its reference images and its EPs."""
        return self.toon_series_dir / series_id

    def refs_dir(self, series_id: str) -> Path:
        """The current reference image of each character and background, `{id}-{rev}.png`."""
        return self.series_dir(series_id) / "refs"

    def pending_refs_dir(self, series_id: str) -> Path:
        """The three pictures of a Ref job not picked yet, `{id}-{1..3}.png`; emptied on every start."""
        return self.refs_dir(series_id) / ".pending"

    def ep_dir(self, series_id: str, ep_id: str) -> Path:
        """An EP's `ep.json`, its card images and narration, and its renders."""
        return self.series_dir(series_id) / "eps" / ep_id

    def card_images_dir(self, series_id: str, ep_id: str) -> Path:
        """Each card's image and previous image, `{card_id}-{seed}.png`."""
        return self.ep_dir(series_id, ep_id) / "images"

    def card_audio_dir(self, series_id: str, ep_id: str) -> Path:
        """Each card's narration, `{card_id}.wav`."""
        return self.ep_dir(series_id, ep_id) / "audio"

    @property
    def toon_sounds_file(self) -> Path:
        """The background sound library of the whole tab (toon D16)."""
        return self.toon_dir / "sounds" / "sounds.json"

    @property
    def toon_partial_dir(self) -> Path:
        """Uploads not received in full yet; emptied on every start."""
        return self.toon_dir / ".partial"

    @property
    def image_job_dir(self) -> Path:
        """The reference images an Image job draws with, copied as it starts; emptied on every start."""
        return self.toon_dir / ".image-job"

    def marker(self, model: ModelSpec) -> Path:
        return self.markers_dir / f"{model.cache_name}.json"

    def snapshot_dir(self, model: ModelSpec, revision: str) -> Path:
        """The folder snapshot_download fills for one revision of a model."""
        return self.hub_dir / f"models--{model.cache_name}" / "snapshots" / revision


def project() -> ProjectPaths:
    """The project at `ROOT`, read per call: tests point `ROOT` at a fake root."""
    return ProjectPaths(ROOT)
