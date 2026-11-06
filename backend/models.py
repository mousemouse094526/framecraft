"""Every model the project uses, pinned to a commit (ADR 0004).

To update a model: change its `revision` to a newer commit hash on the Hub
and run the setup script again.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    check_id: str  # the model's Checklist item id, e.g. "model_omnivoice"
    label: str
    repo_id: str
    revision: str
    allow_patterns: tuple[str, ...]
    license: str
    license_url: str
    author: str
    # The `sys.platform` values the model runs on; setup skips it elsewhere (spoil-maker D50).
    platforms: tuple[str, ...] = ("darwin", "win32")

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

QWEN_MAC = ModelSpec(
    check_id="model_qwen",
    label="Qwen3.5 9B model",
    repo_id="mlx-community/Qwen3.5-9B-MLX-4bit",
    revision="938d8919941c6e7efd3c7150eff7fe9d12afa631",
    # Tokenizer and chat template included: `AutoTokenizer` counts tokens from them (spoil-maker D46).
    allow_patterns=("*.json", "*.safetensors", "*.txt", "*.jinja"),
    license="Apache-2.0",
    license_url="https://www.apache.org/licenses/LICENSE-2.0",
    author="Qwen",
    platforms=("darwin",),  # an MLX model: Apple Silicon only (spoil-maker D50)
)

# bf16 weights that transformers shrinks to 4-bit with bitsandbytes as it loads them (windows-launch D3).
QWEN_WINDOWS = ModelSpec(
    check_id="model_qwen",
    label="Qwen3.5 9B model",
    repo_id="Qwen/Qwen3.5-9B",
    revision="c202236235762e1c871ad0ccb60c8ee5ba337b9a",
    allow_patterns=QWEN_MAC.allow_patterns,
    license="Apache-2.0",
    license_url="https://www.apache.org/licenses/LICENSE-2.0",
    author="Qwen",
    platforms=("win32",),
)


def qwen_for(sys_platform: str) -> ModelSpec:
    """Qwen as the OS runs it; one Checklist item, `model_qwen`, either way (windows-launch D6).
    Callers pass `checks.this_platform()` when they use it, so tests can swap the OS."""
    return QWEN_WINDOWS if sys_platform == "win32" else QWEN_MAC


# Setup downloads in this order and the checklist lists them in it too.
MODELS = (OMNIVOICE, WHISPER, QWEN_MAC, QWEN_WINDOWS)
