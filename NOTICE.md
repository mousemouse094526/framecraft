# Notice

framecraft downloads and runs the models below on your own machine. They are
not part of this repository; `./setup.sh` (Mac) or `setup.cmd` (Windows)
fetches them into `models/`.

Use framecraft for personal or experimental work only. The OmniVoice model is
licensed for non-commercial use (CC BY-NC 4.0), so videos and audio made with
it must not be used for commercial purposes, and anything you publish should
credit the model.

## OmniVoice

- **Creator:** k2-fsa
- **License:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) (model weights; the code is Apache 2.0)
- **Model:** <https://huggingface.co/k2-fsa/OmniVoice>

## Whisper large v3 turbo

- **Creator:** OpenAI
- **License:** [MIT](https://opensource.org/license/mit)
- **Model:** <https://huggingface.co/openai/whisper-large-v3-turbo>

## ffmpeg

The ffmpeg binary comes from the [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
package and is used locally only. See <https://ffmpeg.org/legal.html> before
redistributing it.
