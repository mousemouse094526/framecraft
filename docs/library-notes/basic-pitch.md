# Basic Pitch (ONNX)

**Kind:** model

**Version:** `analysis/basic_pitch_nmp.onnx` from `Andremi/audioweb-models` revision `953d0a9e`, sha256 `2c3c1d14…` (230 kB, Apache-2.0; the `nmp` model of spotify/basic-pitch, exported from TensorFlow)

**Docs:** https://github.com/spotify/basic-pitch

## Best practices

- Feed float32 mono at 22,050 Hz in windows of exactly 43,844 samples (`AUDIO_N_SAMPLES` = 2 s × 22,050 − 256), shaped `[N, 43844, 1]`; the model gives 172 frames per window (`ANNOT_N_FRAMES`), a frame every 256 samples (`FFT_HOP`) — [constants.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/constants.py)
- Windows overlap by 30 frames (`DEFAULT_OVERLAPPING_FRAMES`): the audio is padded with 15 × 256 = 3,840 zeros before, a window starts every 43,844 − 7,680 = 36,164 samples while one starts inside the padded audio, the last is zero-padded to a full window, and 15 frames are cut from each side of every window's output — [inference.py › `get_audio_input`, `unwrap_output`](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/inference.py)
- An onset is a frame whose `onset` output is at least 0.5 (`onset_threshold` default) — [README](https://github.com/spotify/basic-pitch)
- **Avoid:** treating the concatenated kept frames as one grid of 256 samples: a window's hop (36,164) is 68 samples over a multiple of 256, so the grid slips 188 samples (8.5 ms) per window — 0.47 s over 90 s. Compute each frame's time from its own window: `first_sample + frame × 256`, with `first_sample = w × 36164 − 3840` (Basic Pitch's `model_frame_to_time` corrects this per window too)

## I/O of this file (read with `get_inputs()`/`get_outputs()` on 2026-11-14)

| Name | Shape | Is |
|---|---|---|
| `serving_default_input_2:0` | `[N, 43844, 1]` float32 | the input window |
| `StatefulPartitionedCall:0` | `[N, 172, 264]` float32 | contour (3 bins a semitone) |
| `StatefulPartitionedCall:1` | `[N, 172, 88]` float32 | note (sustained while a note sounds) |
| `StatefulPartitionedCall:2` | `[N, 172, 88]` float32 | onset (a spike at a note's start) |

Which 88-bin output is which was checked by running the file on three synthetic plucked notes at 0.3, 0.8 and 1.3 s: `:2` rose over 0.5 only at frames 25–26, 68–69 and 111–112 (expected 26, 69, 112), `:1` stayed over 0.5 for the notes' decay. The file keeps TensorFlow's names; `get_outputs()` lists them as `:2`, `:1`, `:0`, so ask `run` for the name, never trust the list's order.

## Pattern

```python
[onset] = session.run([BASIC_PITCH_ONSET], {BASIC_PITCH_INPUT: window[None, :, None].astype(np.float32)})
frames = np.nonzero(onset.reshape(172, 88).max(axis=1) >= 0.5)[0]
```

`drum_notes.onnx_runner.run_basic_pitch` and `drum_notes.score.basic_pitch_windows`/`window_samples`/`melody_hits` follow `get_audio_input` and `unwrap_output` (drum-notes D14, D26).

## Traps

- Nothing in the model card names the inputs or the hop; the ONNX file in the pinned repo is the source of truth (drum-notes spec Open Question 1, closed in ticket 04)
- An onset usually spans two adjacent frames (11.6 ms): count a run of adjacent onset frames as one note, or one note becomes two hits
- The model was trained on piano-like sources: percussive or noisy audio gives onsets of its own, which melody mode would hear as snares

## Sources

- [spotify/basic-pitch constants.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/constants.py) — `AUDIO_N_SAMPLES`, `FFT_HOP`, `ANNOT_N_FRAMES`, `ANNOTATIONS_FPS` (accessed 2026-11-14)
- [spotify/basic-pitch inference.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/inference.py) — `DEFAULT_OVERLAPPING_FRAMES`, `get_audio_input`, `unwrap_output` (accessed 2026-11-14)
- [spotify/basic-pitch README](https://github.com/spotify/basic-pitch) — 22,050 Hz, `onset_threshold` 0.5, Apache-2.0 (accessed 2026-11-14)
- [Andremi/audioweb-models](https://huggingface.co/Andremi/audioweb-models) — the pinned file (accessed 2026-11-14)
