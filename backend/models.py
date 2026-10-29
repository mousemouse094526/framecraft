"""Every model the project uses, pinned to a commit (ADR 0004).

To update a model: change its `revision` to a newer commit hash on the Hub
and run the setup script again.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    check_id: str
    label: str
    repo_id: str
    revision: str
    allow_patterns: tuple[str, ...]
    license: str
    license_url: str
    author: str

    @property
    def model_url(self) -> str:
        return f"https://huggingface.co/{self.repo_id}"

    @property
    def short_revision(self) -> str:
        return self.revision[:7]

    @property
    def cache_name(self) -> str:
        """`owner--name`, the way the Hugging Face cache names a repo."""
        return self.repo_id.replace("/", "--")


OMNIVOICE = ModelSpec(
    check_id="model_omnivoice",
    label="OmniVoice model",
    repo_id="k2-fsa/OmniVoice",
    revision="c5fdb5ccb189668d56333f77ba2629f4cd7535f4",
    allow_patterns=("*.json", "*.safetensors", "*.jinja"),
    license="CC BY-NC 4.0",
    license_url="https://creativecommons.org/licenses/by-nc/4.0/",
    author="k2-fsa",
)

WHISPER = ModelSpec(
    check_id="model_whisper",
    label="Whisper model",
    repo_id="openai/whisper-large-v3-turbo",
    revision="41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
    allow_patterns=("*.json", "*.safetensors", "*.txt"),
    license="MIT",
    license_url="https://opensource.org/license/mit",
    author="OpenAI",
)

# Setup downloads in this order and the checklist lists them in it too.
MODELS = (OMNIVOICE, WHISPER)
