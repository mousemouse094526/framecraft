# Notice

framecraft downloads and runs the models below on your own machine. They are
not part of this repository; `./setup.sh` (Mac) or `setup.cmd` (Windows)
fetches them into `models/`.

Use framecraft for personal or experimental work only. The OmniVoice model is
licensed for non-commercial use (CC BY-NC 4.0), and the ADTOF drum model for
non-commercial use with attribution (CC BY-NC-SA 4.0), so videos, audio and drum
notes made with them must not be used for commercial purposes. Crediting the model in what you
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

## ADTOF Frame_RNN (ONNX)

The แกะเพลง tab picks drum hits out of a song with the Frame_RNN model of ADTOF, as
converted to ONNX. The model is a format conversion, with no weights modified, of the
checkpoint released by the authors of:

> M. Zehren, M. Alunno, P. Bientinesi. "High-Quality and Reproducible Automatic Drum
> Transcription from Crowdsourced Data." Signals 2023, 4(4), 768–787.
> M. Zehren, M. Alunno, P. Bientinesi. "ADTOF: A large dataset of non-synthetic music
> for automatic drum transcription." ISMIR 2021.

- **Creator:** Mickaël Zehren, Marco Alunno, Paolo Bientinesi (ADTOF); ONNX conversion by thebluescreen
- **License:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — non-commercial use only, credit the authors, share any adaptation alike
- **Model:** <https://huggingface.co/thebluescreen/adtof-drums-onnx> (original: <https://github.com/MZehren/ADTOF>)

## Beat This! (ONNX)

Beats and downbeats of a song, from the `final0` checkpoint of Beat This! (Foscarin, Schlüter,
Widmer, "Beat this! Accurate beat tracking without DBN postprocessing", ISMIR 2024), converted
to ONNX with no weights modified.

- **Creator:** Institute of Computational Perception, JKU Linz (CPJKU); ONNX conversion by thebluescreen
- **License:** [MIT](https://opensource.org/license/mit)
- **Model:** <https://huggingface.co/thebluescreen/beat-this-onnx> (original: <https://github.com/CPJKU/beat_this>)

## Basic Pitch (ONNX)

Note onsets of a melody, for the แกะเพลง tab's melody mode: Spotify's Basic Pitch model as an
ONNX file.

- **Creator:** Spotify
- **License:** [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)
- **Model:** <https://huggingface.co/Andremi/audioweb-models> (`analysis/basic_pitch_nmp.onnx`; the hosting repository's own files are MIT; original: <https://github.com/spotify/basic-pitch>)

## onnxruntime

The three models above run on the CPU with [onnxruntime](https://onnxruntime.ai/) (MIT).

## ffmpeg

The ffmpeg binary comes from the [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
package and is used locally only. See <https://ffmpeg.org/legal.html> before
redistributing it.
