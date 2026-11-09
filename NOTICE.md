# Notice

framecraft downloads and runs the models below on your own machine. They are
not part of this repository; `./setup.sh` (Mac) or `setup.cmd` (Windows)
fetches them into `models/`.

Use framecraft for personal or experimental work only. The OmniVoice model is
licensed for non-commercial use (CC BY-NC 4.0), so videos and audio made with
it must not be used for commercial purposes. Crediting the model in what you
publish is recommended but not required: framecraft adds no credit by itself,
and you can add one yourself, for example as a watermark.

## OmniVoice

- **Creator:** k2-fsa
- **License:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) (model weights; the code is Apache 2.0)
- **Model:** <https://huggingface.co/k2-fsa/OmniVoice>

## Whisper large v3 turbo

- **Creator:** OpenAI
- **License:** [MIT](https://opensource.org/license/mit)
- **Model:** <https://huggingface.co/openai/whisper-large-v3-turbo>

## FLUX.2 klein 4B

The การ์ตูนเล่า tab draws its pictures with FLUX.2 klein 4B: the text encoder (Qwen3-4B),
vae and configs from Black Forest Labs, and the transformer as Unsloth's GGUF (Q4_K_M).
The model card forbids using it for illegal or deceptive content, sexual content
involving minors, harassment, or non-consensual intimate images.

- **Creator:** Black Forest Labs
- **License:** [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)
- **Model:** <https://huggingface.co/black-forest-labs/FLUX.2-klein-4B>

## FLUX.2 klein 4B GGUF

- **Creator:** Unsloth
- **License:** [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)
- **Model:** <https://huggingface.co/unsloth/FLUX.2-klein-4B-GGUF>

## Qwen3-4B (klein's text encoder)

Shipped inside the FLUX.2 klein 4B repository (`text_encoder/`).

- **Creator:** Qwen
- **License:** [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)
- **Model:** <https://huggingface.co/Qwen/Qwen3-4B>

## ffmpeg

The ffmpeg binary comes from the [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
package and is used locally only. See <https://ffmpeg.org/legal.html> before
redistributing it.
