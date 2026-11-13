# Progress: drum-notes

**Now:** 02 done (แกะโน้ตกลองจากช่วงที่เลือก: Pick job + หน้าเพลง); 03 next

**Next:**

```
/warroom-build drum-notes 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เอาเพลงเข้า: ลิงก์ ไฟล์เสียง ไฟล์ MIDI และโมเดล | done |
| 02 | แกะโน้ตกลองจากช่วงที่เลือก | done |
| 03 | เลือกห้อง ฟัง แล้วสร้างบทเรียนกลอง | ready |
| 04 | โหมดทำนอง | ready |

## Log

### 02: แกะโน้ตกลองจากช่วงที่เลือก — done 2026-11-14

**Built:**
- หน้าเพลง: ส่วน "ช่วงแกะ" มีช่องเริ่มและจบ (วินาที) ปุ่ม "ใช้เวลาที่เล่นอยู่" ทั้งสองช่อง บรรทัด "ยาว n s (ไม่เกิน 90 วินาที)" โหมด "กลอง" | "ทำนอง" (ทำนองกดไม่ได้จน 04) ปุ่ม "แกะโน้ต" → `PUT /range` แล้ว `POST /pick` → แถบ % ("กำลังเตรียมเสียง…" → "กำลังแกะโน้ต… n%") กับยกเลิก → "BPM ที่พบ" และแถบห้องจาก `bars` ของ server (ห้องที่ไม่ใช่ 4/4 จาง tooltip "ห้องนี้ไม่ใช่ 4/4" กดไม่ได้); ช่วงผิดเตือนที่ช่องก่อนถาม backend; Alert ของ `no_beats`, `model_failed`, `model_broken` (+ FixCommand), `busy`, `not_ready` (+ fix); รายการเพลงแสดง "กำลังแกะ n%" ระหว่างงานและโหลดใหม่เมื่อจบ
- backend `drum_notes.pick` (`PickJobs(open_session=…, run_ffmpeg=…)`, `JobSlot` ธรรมดา ไม่จอง GPU): `preparing` ถอดช่วงด้วย `ffmpeg.run_capture` (ใหม่) เป็น float32 mono 44.1 kHz และ 22.05 kHz → `picking` ADTOF ทั้งช่วงครั้งเดียว แล้ว Beat This! ทีละ chunk 1,500 เฟรม (`percent` ต่อ chunk, เช็คยกเลิกก่อนทุกโมเดลและ chunk และหลัง chunk สุดท้าย) → `score` → `songs.set_analysis` ทับทั้งก้อน; error `no_beats`/`model_broken` (rows + fix)/`model_failed`/`internal`; `409` `busy` (song_id), `song_busy` ตอนลบ (`songs.song_jobs` hook), `not_applicable` ของ MIDI, `not_running`
- `drum_notes.score` (เลขล้วน): `beat_this_chunks`/`chunk_samples`/`stitch`, peak picking ตาม model card (`drum_hits` → ชิ้นตาม D9 `normal`), `beats_and_downbeats` (หน้าต่าง 7 เฟรม logit > 0 ติดกันรวม downbeat ย้ายไปจังหวะใกล้สุด), `songs.bars_of` → `SongView.bars` ใน `GET /songs/{id}`; `onnx_runner.run_adtof`/`run_beat_this`; `gate_rows.pick_drums`; `checks.setup_fix`; `PUT /songs/{id}/range` (`songs.checked_range`, `400` มี `field`, MIDI `409`)
- วัดมือ D19 (Mac Apple Silicon, โมเดลจริงจาก revision ที่ pin): ช่วง 90 วินาทีของ Smells Like Teen Spirit (`hTWKbfoikeg` bestaudio) → `done` ใน 4.5 วินาที (preparing 0.2 s, ADTOF 0.8 s, Beat This! 4 chunk ≈ 0.8–0.95 s ต่อ chunk → ยกเลิกมีผลภายใน 1 วินาที); พบ 51 ห้อง BPM ~117 การตี 594; `reel.mp4` (19 s) → 0.8 วินาที 14 ห้อง BPM ~117 ห้อง 1 kick 7 snare 4 tom 4 (intro fill) ห้อง 12–14 kick 4–7 snare 4 hihat 4–5 crash 1 ตรงกับ spike; intro ของเพลงเต็ม 0–30 s → ห้อง 4 (7.58–9.70 s) kick 7 snare 4 tom 4 = fill เดียวกัน ห้อง 5–7 kick 6–7 snare 4 hihat 4–5 crash 1–2 (groove); ท่อน pre-chorus เบา (24–40 s) Beat This! ให้ downbeat ทุก 1.04 s = ห้อง 2 จังหวะ ถูกทำเครื่องหมาย "ไม่ใช่ 4/4" (เจ้าของยังควรฟังเทียบและตัดสินเต็มใน 03)

**Decided:**
- D24 — ทางเลือกเล็ก: `SongView.bars` คำนวณตอนอ่าน, ขอบโมเดลที่ `open_session` (fake ระดับ session), แผน chunk (ขยับ 1,488 ตัวสุดท้ายเลื่อนให้จบที่ท้าย เช็คยกเลิกหลัง chunk สุดท้าย), จังหวะติดกันรวม, `percent` ต่อ chunk, โหมดทำนอง `400` field `mode` จน 04, ข้อความ error ทั้งชุด, หน้าเพลงเช็คกฎช่วงก่อน, `songs.song_jobs`, `Labeled` ย้ายไป `components/ui/`

**For the next ticket:**
- `songs.bars_of(analysis)` คือห้องที่พบ (ขั้น 1 ของ Score) ที่ `POST /preview` ควรใช้; `bpmOf` ฝั่งหน้าเว็บยังคำนวณ "BPM ที่พบ" เอง — ticket 03 ให้ BPM มาจาก `/preview` แล้วตัด
- fake: `FakeOnnxRunner(activations=, beat=, downbeat=)` รับ callable ต่อ chunk (`frames, pad_before`) โดยนับเฟรมจากต้นช่วง จึงถูกต้องเฉพาะ chunk แรก (test ของ chunk ที่สองดูแค่รูปร่าง input); `import_song_tone`/`put_song_file`/`song_refusal` อยู่ใน `fakes.py`
- Beat This! บนท่อนเบา (half-time) ให้ downbeat ทุก 2 จังหวะ → ห้องเหล่านั้นเลือกไม่ได้; ถ้าเจ้าของเจอบ่อย ค่อยคิดเรื่องรวมห้อง 2 จังหวะเป็นคู่ (เปลี่ยน spec ต้อง `/warroom`)
- โหมดทำนอง (04): `pick._pickable` ปฏิเสธ `mode` `melody` ที่บรรทัด `MELODY_NOT_YET`; gate `pick_melody` (Basic Pitch, Beat This!, onnxruntime, ffmpeg ตาม D7) ยังต้องเพิ่มใน `gate_rows`; ปุ่ม "ทำนอง" บนหน้าเพลง `disabled` ที่ `option === "melody"`
- `setup.py` มี `OpenSession` alias ของตัวเอง ซ้ำกับ `onnx_runner.OpenSession`
- test `run_capture` ยกเลิกใช้ `threading.Timer(0.3)` ตั้ง cancel ระหว่าง ffmpeg `-re` รัน 30 วินาที (unit test ไม่ใช่งาน): ถ้ากะพริบ ให้เปลี่ยนเป็นตั้ง cancel หลังอ่าน byte แรก
- แบบ Figma สองหน้า (Blocked 1–2) แล้วปรับหน้าเว็บตามแบบ

**Checks:** `uv run pytest` 1349 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 529 passed; `npm --prefix frontend run build` ผ่าน. Review สามแกนจาก `09ab458`: Standards 3 ผิดกติกา (แก้: โครง folder ใน SKILL `fastapi-api` เพิ่ม pick/score/`run_capture`/`pick_drums`/`setup_fix`; test state `in ("preparing", "picking")` → หยุดที่ `adtof` แล้ว assert แน่ชัด; `lib/songs.ts` ได้ `songs.test.ts`) + smell 7 (แก้: `FoundBar` สองชนิด → `songs.bars_of` ตัวเดียว ไม่มี import ซ้อน; `ffmpeg` สามตัวแชร์ `_watch_stderr`/`_ended`; ตัด `pick_melody` ที่ไม่มีผู้เรียก; รายการเพลงใช้ `usePick` แทน poll ซ้ำ; `own` → `picking`; type ของ `_run_model`/`_decode`; test สามกรณีแยกเป็นสาม `it`; ไม่แก้: `threading.Timer` ใน test `run_capture` — unit test ไม่ใช่งาน บันทึกไว้ For the next ticket); Spec 0 ผิด + 2 ขาด (Checks ยังว่างตอนรีวิว → เติม; เจ้าของยังไม่ได้ฟังเทียบ → บันทึกใน Log และ board) + 3 นอกขอบ (ตัด `pick_melody`; `started_at`/`cancel_requested` และชื่อ `open_session` บันทึกใน D24 แล้วแก้ spec › API/Testing decisions และ Status ของ D20) + 2 สังเกต (แก้: เฟรมติดกันหลายเฟรมรวมเป็นจังหวะเดียวทั้งชุด; ไม่แก้: `_window` ตัดขอบแทน pad ศูนย์ของ madmom — spec บอก "ทำเองด้วย numpy") + 2 test (แก้: test คำสั่ง ffmpeg เหลือแค่ `-ss`/`-t` ที่ตัวเลข sample พิสูจน์ไม่ได้; percent สังเกตที่ 33 → 66 บนช่วงสอง chunk); Newcomer สรุปตรง What to build + เดา 9 จุด (แก้ 7: ตั้งงานใต้ `songs.lock` ปิดช่องลบระหว่างอ่านกับเริ่ม; `_pickable` อธิบายว่าทำไมเช็ค range ซ้ำและ `range is None`; guard `if frames` ตาย; `_window` เป็น `sliding_window_view` ครั้งเดียว; ชื่อ test chunk ที่สาม; docstring body `{}` ของ route pick; `pick_melody` ตัด; ไม่แก้: `findStatusWith` = กติกา testing)

### 01: เอาเพลงเข้า: ลิงก์ ไฟล์เสียง ไฟล์ MIDI และโมเดล — done 2026-11-14

**Built:**
- tab "แกะเพลง" (`#/songs`): วางลิงก์ YouTube หรือเว็บอื่นแล้วกด "เอาเพลงเข้า" → งานโหลด (checking → downloading % → converting) แล้วเพลงอยู่ในรายการ; เลือกหรือวางไฟล์เสียง (ทุกชนิดที่ ffmpeg อ่าน ≤ 200 MB) → `check` แล้ว `PUT` body ดิบ แถบ % → "กำลังแปลงเสียง…" → หน้าเพลง; ไฟล์ `.mid` (≤ 5 MB) → หน้าเพลงที่เห็น "BPM ที่พบ" และแถบห้องที่พบทันที ไม่มี player; ลิงก์หรือไฟล์ที่ซ้ำ → "เพลงนี้มีอยู่แล้ว" แล้วพาไปเพลงเดิม; ลบพร้อมยืนยันว่าบทเรียนไม่หาย
- backend `drum_notes`: `songs` (`media/songs/{id}/song.json` + `audio.m4a`, id ตาม `spoil.links`, ล้าง `.partial/` และ folder ไร้ `song.json` ตอน start), `imports` (slot ของลิงก์ + ไฟล์ใน request เดียว, error ตาม `adapter.error_code`, `-t 600`, `too_short`/`too_long` จากไฟล์จริง), `midi` (parser SMF format 0/1 ช่อง 10 GM map), `onnx_runner.open_session`; router `/api/songs` 9 route
- `backend.audio_imports` ใช้ร่วม: `toon.sounds` ย้ายงานลิงก์ `bestaudio`, รับไฟล์ดิบพร้อมเช็คหน้าเว็บหาย, probe/convert m4a, ล้าง `.partial/` ไปที่นั่น (test toon เดิม 32 ตัวผ่าน แก้แค่จุด patch `GONE_POLL_SECONDS`)
- โมเดล ONNX สามตัวใน `MODELS` (`model_adtof`, `model_beat_this`, `model_basic_pitch`) + แถว `onnxruntime` 1.32.0 ต่อจาก `drum_kit` (24 แถว); Setup script โหลดหลัง drum kit และเปิด `InferenceSession` ของแต่ละไฟล์ก่อนเขียน marker (ล้ม = error ชื่อไฟล์ ไม่มี marker); `pyproject.toml` `onnxruntime==1.32.0`; `NOTICE.md` และหน้าสถานะมีเครดิต ADTOF (Zehren, Alunno, Bientinesi; ONNX by thebluescreen), Beat This!, Basic Pitch, onnxruntime
- spike (เครื่อง Mac): ADTOF บน `reel.mp4` → kick 49, snare 31 ตรง `adtof_test.py` ของเจ้าของ (0.16 s); Beat This! บน reel → จังหวะ 115 BPM, ห้อง 1–2 และ 14–16 ครบ 4 จังหวะ (กลางคลิปเป็นช่วงสอนที่เงียบ จึงแตกเป็นห้องสั้น); บน Smells Like Teen Spirit (bestaudio YouTube `hTWKbfoikeg`) ช่วง 0–30 s → downbeat ทุก 2.04–2.18 s ครบ 4 จังหวะ 12 ห้องแรก กลองเข้าห้อง 4 ที่ 7.6 s (intro fill: kick 8) แล้ว groove kick 5–7 snare 4 ต่อห้อง; 30 s ใน 2.4 s (2 chunk) — ผ่าน ไม่ต้องใช้แผนสอง; เจ้าของยังควรฟังเทียบเองหนึ่งครั้ง
- วัดมือ D19: mp3 5 นาที (7.2 MB) `PUT` → `201` ใน 4.3 วินาที (รับ + แปลง) บน Mac

**Decided:**
- D22 — ไฟล์ MIDI ที่ไม่รับทุกเหตุตอบข้อความเดียว "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง"; velocity ≤ 50 ghost, ≥ 100 accent; ความยาว = โน้ตสุดท้าย + 1 ห้อง
- D23 — ทางเลือกเล็ก: `GET /songs` ส่ง `source_kind` และ `analysis` `{mode, bars}`; cancel ว่าง `409` `not_running`; `PUT` ไฟล์ซ้ำตอบ Song เดิม; `audio_imports.Limits`/`place`; `setupFixes.ts` ย้ายไป `src/lib/`; ไม่ย้าย helper `edit`/`notice`/`upload` ของ toon; แถว `onnxruntime` มี license (MIT, Microsoft) ตาม ticket; MIDI ไม่มี time signature = 4/4

**For the next ticket:**
- Basic Pitch ONNX (Open Question 1): input `serving_default_input_2:0` `[N, 43844, 1]` float32; output `StatefulPartitionedCall:0` `[N, 172, 264]` (contour), `:1` `[N, 172, 88]`, `:2` `[N, 172, 88]` — ลำดับตาม dict ของ TF (`contour`, `note`, `onset`) น่าจะเป็น `:1` = note, `:2` = onset; ticket 04 ตรวจด้วย onset จริง
- Beat This! ONNX: input `waveform` `[1, samples]` และ `pad_frames` `[2]` int64; output `beat`, `downbeat` `[1, frames]`; ADTOF: input `waveform`, output `activations` `[1, frames, 5]`; สูตร chunk ที่ใช้ใน spike (`starts = range(-6, frames-6, 1488)`, chunk สุดท้ายเลื่อนให้จบที่ท้าย, ตัด 6 ต่อด้าน, keep first) อยู่ใน scratchpad ของ session นี้ — ticket 02 เขียนใหม่ใน `score.stitch` ตาม D20
- `songs.checked_analysis` รับผล Pick job ได้เลย; `songs.lock`, `songs.exists`, `songs.write_new` (ไม่เขียนทับ) และ `KnownSong` คือทางที่ imports ใช้; `song_busy` (Pick job ของเพลง) ยังไม่มี: ticket 02 เพิ่ม hook แบบ `lessons.lesson_jobs`
- หน้าเพลง: `FoundBars` กดห้องแล้ว seek player แล้ว (D20) แต่เพลงเสียงยังไม่มี `analysis` จน ticket 02; `barsOf`/`bpmOf` ใน `lib/songs.ts` ทำ Score ขั้น 1 และ 3 ซ้ำกับ `drum_notes.score` ที่จะมา — ticket 03 ควรให้ BPM มาจาก `POST /preview` แล้วเหลือ `barsOf` ไว้วาดแถบอย่างเดียว
- `songs.Song.title` ไม่มีกฎ 1–60 ตอนอ่าน (ทุกชื่อตอนนี้มาจาก server ตัดที่ 60 แล้ว); ticket 03 ที่สร้างบทเรียนใช้กฎของ `video_gen.lessons` อยู่แล้ว
- `tabOf`/`App` เติม arm ต่อ tab ซ้ำแบบเดิมทุก feature (Repeated Switches ตาม Standards) — ถ้าจะแก้ให้ `TABS` ตัดสินเอง เป็นงานข้าม feature
- toon `edit`/`notice`/`upload` helper กับ `useReadyState` ยังอยู่ใน toon แม้มีผู้ใช้ที่สองในแนวเดียวกัน (video-gen และ drum-notes ใช้ `sendJson` ตรง) — งาน refactor ข้าม feature ถ้าเจ้าของต้องการ
- แบบ Figma สองหน้า (Blocked 1–2) แล้วปรับหน้าเว็บตามแบบ

**Checks:** `uv run pytest` 1313 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 513 passed; `npm --prefix frontend run build` ผ่าน. Review สามแกนจาก `15372af`: Standards 4 ผิดกติกา (route มี logic เลือก 200/202 → module คืน `(status, body)`; `test_model_imports` ไม่กัน onnxruntime; ลำดับ lock ของ `songs.lock` ไม่อยู่ใน SKILL; test import test อื่น → ตัวสร้าง MIDI ย้ายไป `fakes.py`) + smell 9 (แก้: `TOO_LONG` ซ้ำ → `songs.py`, `_file_title`/`_receiving`/`still_wanted` ซ้ำ → `audio_imports.ImportSlot`/`file_title`/`still_wanted`, `compose.AUDIO_*` อ่านจาก `audio_imports`, `songs.song_dir` → `checked_dir`, `NoteOn` NamedTuple, `knownIdOf`, dead `if False`, test เดินขึ้นจากข้อความ; ไม่แก้: `tabOf`/`App` repeated switches — แบบเดิมทุก tab); Spec 0 ผิด + 5 ขาด (แก้: license ของแถว `onnxruntime`, MIT ของ repo ที่ host Basic Pitch ใน NOTICE, e2e วางไฟล์ลงกล่อง, e2e กดห้องแล้ว seek, D22 บอกค่าตั้งต้น 4/4; ไม่แก้: กฎ title 1–60 ตอนอ่าน — ชื่อมาจาก server) + 3 test (แก้: GM map เป็นคู่ตัวอักษร, assert `LINK_OPTIONS` → format/folder ที่สังเกตได้); Newcomer สรุปตรง What to build + เดา 10 จุด (แก้ 9: ชื่อ test ลิงก์, dead branch, `BYTES_PER_SECOND`/`song_id`/`models.py` comment, `partial_of`, JobEntry comment, guard meta ขาดท้าย, ล้าง arrival; ไม่แก้: ป้าย "(e2e)" ใน Vitest = กติกา testing)

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: รายการเพลง — ทำแบบจาก [ui-prompt.md](../../features/drum-notes/ui-prompt.md) | `/warroom drum-notes` พร้อมลิงก์แบบ | open |
| 2 | 02 | design: หน้าเพลง — ทำแบบจาก [ui-prompt.md](../../features/drum-notes/ui-prompt.md) | `/warroom drum-notes` พร้อมลิงก์แบบ | open |
