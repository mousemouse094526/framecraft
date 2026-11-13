---
name: fastapi-api
description: >-
  How framecraft's Python backend code (backend/) is structured and written:
  FastAPI, uv, Python 3.12, pytest. Use whenever writing, moving, or reviewing
  code under backend/ or the setup wrappers (setup.sh, setup.ps1, setup.cmd).
---

# FastAPI backend

The local Python backend that runs every AI and media job (ADR 0001), plus the
setup entry point that installs everything (ADR 0002).

## Folder structure

```
backend/
├── app.py        ← FastAPI app; mounts every router under /api; `JOB_HOLDERS`
│                    lists every job holder once, and the lifespan runs each
│                    one's start-up clean and `stop_on_shutdown` from it
├── paths.py      ← project root, models/ and media/ paths (ADR 0003);
│                    `paths.project()` is the one routes read per request;
│                    `EpAddress` (one toon EP: project, Series, EP, and its
│                    folders) is what every function of one EP and its
│                    `/eps/{ep_id}` routes take (`episodes.address_of`
│                    makes it and never refuses; `episodes.read` gives `404`)
├── models.py     ← the model registry, pinned commits (ADR 0004)
├── checks.py     ← Status check, shared by setup and the API
├── disk.py       ← free disk space and the 1 GiB `disk_full` check: setup, spoil, both renders, toon jobs
├── fonts.py      ← Kanit Bold pinned by commit and sha256: setup fetches it, the
│                    Status check checks it, the Render job draws with it
├── drum_kit.py   ← the drum samples (Big Rusty Drums, CC0, ADR 0039) pinned the same
│                    way: `SAMPLES` (piece, layer, round-robin, path, sha256), setup's
│                    `install_drum_kit` (three tries a file), the `drum_kit` row's check
├── clock.py      ← `hh:mm:ss`, shared by Transcripts and the Draft job's prompts
├── files.py      ← write_atomic (through `.tmp`) and the start-up sweep of `.tmp`
├── body_types.py ← what a POST/PUT/PATCH body may be: JSON everywhere, a raw
│                    `application/octet-stream` file on the routes that list
│                    `require_octet_stream` (ADR 0013, ADR 0028)
├── errors.py     ← ApiError (every refusal, `{"code", "message", ...}`),
│                    JobFailed, `require_rows` (the gate of every job)
├── gate_rows.py  ← the Status check rows gates share (`FFMPEG`, `DEVICE`,
│                    `PYTHAINLP`, `LINK_TOOLS`, `qwen_jobs`, `klein`, `voice`, `render`,
│                    `drum_kit_row`, `drums`), named once (ADR 0009)
├── jobs.py       ← JobSlot (one job of a kind, ADR 0010: `running`, `update`),
│                    ModelJobSlot (a job whose model runs in a child: cancel,
│                    shutdown, `_run_job`, the one ending of every job's thread
│                    that frees the GPU) and the child process helpers every GPU
│                    job uses (ADR 0012); a child starts only through
│                    `start_child` (tracked, then its first message waited for;
│                    a child that says nothing until asked, klein's, is only
│                    `track`ed) and stops only through `stop_child` (`free_gpu` also frees
│                    the GPU mid-job); a slot's steps and its `Speaker` call
│                    `update`, `start_child`, `ask`, `stop_child`; `worker_error_message`, the
│                    message of a child's `WorkerError` (`gpu.ADVICE` unless one of
│                    `CODE_ERROR_TYPES`, toon D84)
├── workers.py    ← `Worker`, a model's child with its request and reply queues:
│                    every adapter's `start_worker` (klein's `start_encoder`,
│                    `start_drawer`) returns one, `end` asks it to exit;
│                    the stack dumpers of a child that hangs (`dump_stacks_on_signal`,
│                    `dump_stacks_after`, toon D76), `as_worker_error` (a child's error as its
│                    `WorkerError`, printed whole) and `error_detail`/`error_type_of` of its
│                    `detail` (toon D85) (standard library only, as a child imports it)
├── gpu.py        ← the one GPU slot every model job takes (ADR 0015), the
│                    Spoil draft's lock (`slot.draft_lock`, spoil-maker D51);
│                    its own lock also guards a clip's files: `clip_untouched`
│                    (delete or change, refusing a job that reads the clip)
│                    and `clip_files_lock` (a clip's EP cuts, spoil-maker D71);
│                    `begin_trim` marks the clip a Trim job cuts, which every
│                    job that reads it is refused until `end_trim` — the mark
│                    outlives the `with` (spoil D42); `trimmed_clip_swap`
│                    guards putting the new mp4 in place; `advised` ends a failed
│                    job's message with `ADVICE`
├── ffmpeg.py     ← the ffmpeg binary, running it (progress, killing on cancel),
│                    `run_piped` (frames through stdin, video-gen D22), `h264_args`
│                    (videotoolbox or libx264, spoil D36) and `ffmpeg -i` reading;
│                    spoil's trim, spoil_maker's frames and compose, video_gen's render share it
├── setup.py      ← entry point: python -m backend.setup
├── qwen_tokens.py← an EP's lines and a Story block counted to Qwen behind its
│                    Status check row (spoil-maker D46, story-kb D14)
├── stories.py    ← the คลังความรู้ tab (story-kb, ADR 0023): Stories and the
│                    Story each clip remembers in `media/stories/`, their
│                    checks, the Story block of the LLM prompts and its tokens;
│                    its own lock is the innermost (story-kb D16)
├── spoil/        ← a feature with several modules gets a package (spoil D14):
│                    links (accepted links, clip ids), adapter (the only
│                    yt-dlp import), mp4check (the h264/aac ≤ 1080 rule
│                    every Temp clip's mp4 meets, ADR 0027), clips,
│                    downloads (Download job, and the flag of a File import
│                    receiving, under the same lock), imports (File import:
│                    a local mp4 as a raw body, one request, ADR 0028),
│                    transcribe (Transcribe job, Transcript files),
│                    trim (Trim job: cut ranges out of a clip's mp4, D41),
│                    whisper (the only torch/transformers import for
│                    transcribing; its `worker` runs in a child process)
├── spoil_maker/  ← the สปอย tab (spoil-maker D56, D59): shots (Shot files),
│                    describe (Describe job), frames (ffmpeg for Shots),
│                    llm (the only mlx-vlm import; picks the child per OS), tts (the only omnivoice
│                    import), voices (Saved voices, Voice job), thai
│                    (numbers as words, letter count, the only pythainlp
│                    import), draft_file (the Spoil draft on disk; spoil
│                    imports it), draft (the draft's view and edits, the
│                    Draft job), episodes (a clip's EP cuts on disk, the
│                    EP list and its token count, D66), script (the
│                    prompts and the reading of Qwen's answers), tokens
│                    (the only transformers import of the backend process: Qwen's
│                    tokenizer), settings (what the tab remembers), render (the
│                    Render job and the render files), compose (the ffmpeg
│                    commands of a render), captions (the ASS file and the
│                    `.srt`), llm_windows (Qwen on Windows: the only
│                    transformers VLM and bitsandbytes import, windows-launch
│                    D3); llm's, llm_windows's and tts's `worker` run in a
│                    child process; `llm.TIMEOUTS` holds each OS's timeouts
├── toon/         ← the การ์ตูนเล่า tab (toon spec): store (`series.json`,
│                    `ep.json` and `sounds.json` on disk, the tab's one lock),
│                    kinds (what differs between characters and backgrounds,
│                    one row each: code that handles both reads it, never
│                    `kind == "characters"`), series (Series, characters,
│                    backgrounds, reference pictures and their uploads,
│                    `ItemRef` (one item: project, Series, kind, id; what
│                    every function of one item and its routes take),
│                    `in_use`, `new_items` of a plot, `ref_revs`; `series_jobs`, each job
│                    slot, whose running job's Series can't go), episodes
│                    (EPs, their plot (`plot_items`, the user's or Qwen's),
│                    acts, segments and cards, each card's
│                    state; `ep_jobs`, where each job slot says the EP it
│                    works on as an `EpUse`: locks it, renders it), writer
│                    (the Plot and Cards prompts and the reading of Qwen's
│                    answers through llm_reply), prompts
│                    (the picture prompts and the reading of Qwen's scene),
│                    jobs (the Toon job slot: it starts and ends every kind
│                    the same way from each kind's `WORK`, a `steps.Work`),
│                    steps (what the kinds share: Qwen's and klein's children,
│                    `open_klein` the one start of klein, `ask_klein`, `Run`, what a kind's
│                    steps call on the slot); a variable of `kinds.ItemKind`
│                    (characters or backgrounds) is `item_kind`, as `kind`
│                    names a job's (in a response too, as
│                    `missing_refs[].item_kind`); one module per kind: plot, cards, refs (Ref job), images (Image job:
│                    which cards it draws, each picture it writes, swapping
│                    back), voicing (Voice job: a card's narration), klein (the
│                    only diffusers import; two children one after the other:
│                    `encoder_worker`, then `drawer_worker`, D34, D77), sounds (the background sound library and
│                    its Sound import slot: a file in one request, which a page
│                    gone during ffmpeg never brings in, a link
│                    through spoil's adapter with `LINK_OPTIONS`), render (the
│                    Render job, its own slot, and an EP's renders), compose (a
│                    render's timeline, its ffmpeg commands and its ASS file,
│                    through `subtitles`)
├── video_gen/    ← the สอนกลอง tab (video-gen spec): kit (the ten pieces: lane, colour,
│                    foot), lessons (`lesson.json` under `media/drums/lessons/{id}/`, its
│                    checks with D20's rules, the tab's one lock; `require_id` before any
│                    path), timeline (every hit, beat and chapter span in samples at
│                    44.1 kHz: the one place a note's time is worked out, ADR 0038), mixer
│                    (the wav from the samples, ฟังจังหวะ's `listen`; numpy and soundfile
│                    imported inside); kit also holds the diagram's points (kit-sketch);
│                    lane (where the note lanes put a time), frames (`Scene` drawn once,
│                    `frame_at` per frame, Pillow imported inside), captions (the ASS file
│                    and `.srt`), render (the Render job in its own `JobSlot`, no GPU;
│                    registers itself in `lessons.lesson_jobs` for `lesson_busy`),
│                    backgrounds (a lesson's picture, D6: check, raw `PUT`, crop; D36)
├── speaking.py   ← `Speaker`, which speaks texts in a Saved voice in an
│                    OmniVoice child for the job slot that holds it (it is
│                    given the slot and calls its `track` and `reply`, never
│                    as its base), and
│                    the wav it writes: spoil_maker's Voice and Render jobs,
│                    toon's Voice and Render jobs
├── subtitles.py  ← what every render's text shares: the ASS header, a Dialogue line,
│                    Thai text cut into lines or short chunks and their times, the
│                    `.srt`; spoil_maker's captions and toon's compose lay them out
├── renders.py    ← what every render's results folder shares: a `Render` (folder and
│                    name as one value, `next_free` picks it; its `finish`,
│                    `require`, `delete`), the complete
│                    renders (`results`, `listed`), `latest_at`, the job's `percent`
│                    (`pieces_percent`, `encode_progress`), the finish (`finish`: json last), the
│                    delete (mp4 first, `409` `in_use`, json last), leftover `.partial`s;
│                    spoil_maker's, toon's and video_gen's render keep their folders and call
│                    it; the first two gate on `gate_rows.render`, video_gen's on `gate_rows.drums`
├── uploads.py    ← a raw file body to disk as it comes (ADR 0028): spoil's
│                    File import, toon's reference uploads and video_gen's
│                    backgrounds share it
├── json_values.py← int and number checks of a JSON value (JSON `true` is an
│                    int to Python): spoil_maker and toon share it
├── llm_reply.py  ← the JSON object in a Qwen reply and Thai text without CJK
│                    letters: spoil_maker's script and toon's writer share it
├── routes/       ← one router file per feature, e.g. setup_status.py, stories.py
└── tests/        ← pytest, test_{module}.py
```

No auth and no public/private split: the app binds 127.0.0.1 only.

## Flow

route (routes/{feature}.py) → module function (checks.py, spoil/) → libraries

Long jobs run as a daemon thread in the backend process; their state lives in
memory and the web page polls it (ADR 0010). A job that uses the GPU keeps that
thread, but the model runs in a `multiprocessing` `spawn` child that reports
through a queue; the thread writes the result file (ADR 0012).

## Where shared code goes

- Code one feature uses lives in that feature's module.
- A second user appears → move it to a top-level module named for its kind, in
  the same change. Never create a shared file ahead of need.
- Transcribing stayed inside `backend/spoil/` (spoil spec › Modules touched):
  it works on Temp clips only. spoil-maker, the next AI feature, is a sibling
  package `backend/spoil_maker/` (its spec › Modules touched); features stay
  top-level packages, not `backend/features/{feature}/`.

## Never break

- Nothing installs packages or downloads models at runtime; only `backend.setup`
  does. Media from a link the user typed may be fetched at runtime (ADR 0008).
- Only one module per library that talks to the outside world (the yt-dlp
  adapter, the Whisper adapter in `backend.spoil`, the mlx-vlm adapter
  `spoil_maker.llm`, the OmniVoice adapter `spoil_maker.tts`, the tokenizer
  `spoil_maker.tokens`, the diffusers adapter `toon.klein`); tests replace it with a
  fake (`spoil.adapter`, `spoil.start_worker`, `spoil_maker.start_worker`,
  `spoil_maker.start_tts_worker`, `spoil_maker.count_tokens`, `toon.klein.start_encoder`,
  `toon.klein.start_drawer`).
- torch, transformers, diffusers, mlx-vlm, omnivoice, numpy, soundfile, pythainlp and Pillow are imported
  inside the function that needs them, never at module import: the backend must
  start in under a second. Qwen's tokenizer (`spoil_maker.tokens`) is the one
  transformers use in the backend process: no model, no GPU.
- Locks are taken in one order: a job slot's, then `spoil.clips.files_lock`
  (a Temp clip's mp4 and Transcript, spoil D46), then `gpu.slot.draft_lock`,
  then the GPU slot's own (inside `GpuSlot`); never the other way round.
  `toon.store.lock` comes after `draft_lock` and before the GPU slot's own (a
  Series' `voice_id` is written under `draft_lock`, toon D25).
  `stories`' lock comes after all of them: nothing else is taken while it is held.
  `video_gen.lessons.lock` comes after the drum Render job slot's own (video-gen D33).
- pythainlp's data folder is `models/pythainlp/` (`PYTHAINLP_DATA`, set right
  before the import in `spoil_maker.thai`), never `~/pythainlp-data` (ADR 0003).
- Every job that loads a model takes `gpu.slot` before it starts and releases
  it on every ending, before its state reads as finished (ADR 0015).
- Every `POST`, `PUT` and `PATCH` must be `application/json`, else `415` (ADR 0013);
  `app.py` enforces it with an app-wide dependency, `body_types.require_json`. A route
  that takes a raw file lists `Depends(body_types.require_octet_stream)` itself, and
  `require_json` leaves it alone; `multipart/form-data` is refused everywhere (ADR 0028).
- A path no route matches answers `404` `not_found` in the same shape
  (`app.py`): `%2F` decodes before routing.
- `TrustedHostMiddleware` allows only `127.0.0.1`, `localhost`, `[::1]`
  (ADR 0011).
- Every Hugging Face call passes `cache_dir` from `backend.paths`; never rely on
  `HF_HOME` or `HF_HUB_CACHE` (ADR 0003).
- Every model comes from `backend.models` with its pinned `revision` (ADR 0004).
- ffmpeg is found with `imageio_ffmpeg.get_ffmpeg_exe()`, never PATH (ADR 0005).
- uvicorn binds 127.0.0.1 only. `npm run dev` starts it with the venv's Python
  (`scripts/dev-api.mjs`), never `uv run`: right after setup the terminal may
  not see uv on PATH (D24).
- The Status check never imports `omnivoice` or `transformers` and never uses
  the network.
- The backend process never asks torch about a CUDA device (no CUDA context next to
  a worker's VRAM): the Status check reads the card with `nvidia-smi` and only
  `torch.cuda.get_arch_list()` from torch (windows-launch D12).
- Qwen's spec comes from `models.qwen_for(checks.this_platform())` when it is used,
  never `QWEN_MAC` or `QWEN_WINDOWS` directly (ADR 0025).
- `setup.ps1` stays ASCII-only; Thai text is printed from Python.
- A Python file in `scripts/` is a tool run by hand (`.venv/bin/python scripts/….py`), never
  imported by the backend: standard library only, and the Python rules of
  `docs/library-notes/python.md` (files opened with `encoding="utf-8"`) (toon D78).

## Rules by layer

| File | Covers |
|---|---|
| [rules/routes.md](rules/routes.md) | FastAPI routers and response shapes |
| [rules/setup.md](rules/setup.md) | backend.setup and the OS wrappers |
| [rules/testing.md](rules/testing.md) | pytest, fakes, what never runs in tests |

A layer with no rules file → stop and ask before writing it.
