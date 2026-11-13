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


# FLUX.2 klein 4B's text encoder, vae and configs; its bf16 transformer is left out, the
# GGUF below replaces it (toon D34). `transformer/config.json` is the `config=` the GGUF loads with.
KLEIN = ModelSpec(
    check_id="model_klein",
    label="FLUX.2 klein 4B model",
    repo_id="black-forest-labs/FLUX.2-klein-4B",
    revision="e7b7dc27f91deacad38e78976d1f2b499d76a294",
    allow_patterns=(
        "model_index.json",
        "text_encoder/*",
        "tokenizer/*",
        "vae/*",
        "scheduler/*",
        "transformer/config.json",
    ),
    license="Apache-2.0",
    license_url="https://www.apache.org/licenses/LICENSE-2.0",
    author="Black Forest Labs",
)

KLEIN_GGUF = ModelSpec(
    check_id="model_klein_gguf",
    label="FLUX.2 klein 4B GGUF",
    repo_id="unsloth/FLUX.2-klein-4B-GGUF",
    revision="a09d5bb51ac4000ccd9643d10e9db3ed14200508",
    allow_patterns=("flux-2-klein-4b-Q4_K_M.gguf",),
    license="Apache-2.0",
    license_url="https://www.apache.org/licenses/LICENSE-2.0",
    author="Unsloth",
)

# The แกะเพลง tab's ONNX models, run on the CPU by onnxruntime (drum-notes D7, ADR 0041): setup
# downloads them after the drum kit and opens each file once before its marker (D20). ADTOF's
# author line credits the model's authors and its converter, as its NOTICE.md asks (legal 3).
ADTOF = ModelSpec(
    check_id="model_adtof",
    label="ADTOF drum model",
    repo_id="thebluescreen/adtof-drums-onnx",
    revision="d0e809bb1c1b6fe8a4a00c576852117a0636ab5a",
    allow_patterns=("adtof_frame_rnn.onnx",),
    license="CC BY-NC-SA 4.0",
    license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
    author="Zehren, Alunno, Bientinesi · ONNX by thebluescreen",
)

BEAT_THIS = ModelSpec(
    check_id="model_beat_this",
    label="Beat This! model",
    repo_id="thebluescreen/beat-this-onnx",
    revision="92842057ebb781a31fcf0d638f04a098fb887313",
    allow_patterns=("beat_this.onnx",),
    license="MIT",
    license_url="https://opensource.org/license/mit",
    author="Foscarin, Schlüter, Widmer (CPJKU) · ONNX by thebluescreen",
)

# One file of a repo that holds other models too (a demucs ONNX among them): the pattern names it (D7).
BASIC_PITCH = ModelSpec(
    check_id="model_basic_pitch",
    label="Basic Pitch model",
    repo_id="Andremi/audioweb-models",
    revision="953d0a9e46fd364860c9413ee4c7a9aa4fbcae4b",
    allow_patterns=("analysis/basic_pitch_nmp.onnx",),
    license="Apache-2.0",
    license_url="https://www.apache.org/licenses/LICENSE-2.0",
    author="Spotify",
)

ONNX_MODELS = (ADTOF, BEAT_THIS, BASIC_PITCH)

# Setup downloads in this order and the checklist lists them in it too, except the ONNX models:
# setup downloads those after the drum kit, and the checklist shows their rows right after the
# drum kit's, before klein's (D7; `checks.run_checks`).
MODELS = (OMNIVOICE, WHISPER, QWEN_MAC, QWEN_WINDOWS, KLEIN, KLEIN_GGUF, *ONNX_MODELS)
