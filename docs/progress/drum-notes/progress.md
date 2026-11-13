# Progress: drum-notes

**Now:** 01 done (spike ผ่าน เพลงเข้าได้สามทาง โมเดลสามตัวใน Setup); 02 next

**Next:**

```
/warroom-build drum-notes 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เอาเพลงเข้า: ลิงก์ ไฟล์เสียง ไฟล์ MIDI และโมเดล | done |
| 02 | แกะโน้ตกลองจากช่วงที่เลือก | ready |
| 03 | เลือกห้อง ฟัง แล้วสร้างบทเรียนกลอง | ready |
| 04 | โหมดทำนอง | ready |

## Log

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
