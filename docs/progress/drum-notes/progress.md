# Progress: drum-notes

**Now:** ทุก ticket done (01–04); รอ feature review + เจ้าของฟังเทียบ (ตาราง intro ของ 03, kalimba ของ 04) + แบบ Figma สองหน้า (Blocked 1–2)

**Next:**

```
/warroom-build drum-notes --review-feature
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เอาเพลงเข้า: ลิงก์ ไฟล์เสียง ไฟล์ MIDI และโมเดล | done |
| 02 | แกะโน้ตกลองจากช่วงที่เลือก | done |
| 03 | เลือกห้อง ฟัง แล้วสร้างบทเรียนกลอง | done |
| 04 | โหมดทำนอง | done |

## Log

### 04: โหมดทำนอง — done 2026-11-14

**Built:**
- อ่าน `basic_pitch_nmp.onnx` ที่ pin จริง (sha256 ตรงกับไฟล์ของเจ้าของใน `~/.hermes/cache/scratch/fbreel/models/`): input `serving_default_input_2:0` `[N, 43844, 1]`, output `:2` onset / `:1` note `[N, 172, 88]`, `:0` contour `[N, 172, 264]` — พิสูจน์ด้วยโน้ตสังเคราะห์ 3 ตัว (onset ขึ้นเฉพาะเฟรม 25–26, 68–69, 111–112 ตรงที่คาด 26, 69, 112) → `docs/library-notes/basic-pitch.md` (+ แถว README) ปิด Open Question 1 ของ spec
- backend: `onnx_runner.run_basic_pitch` (ขอ output ตามชื่อ); `score` ส่วน Basic Pitch — `basic_pitch_windows` (pad 3,840, หน้าต่าง 43,844 ทุก 36,164 ตามโค้ดต้นฉบับ `get_audio_input`), `window_samples`, `melody_hits` (ตัด 15 เฟรมต่อด้าน, onset ≥ 0.5 ของโน้ตใด, เวลาจากต้นหน้าต่างของตัวเอง, เฟรมติดกันรวมเป็นการตีเดียว, เกินท้ายช่วงทิ้ง → `snare` `normal`) และ `preview(hits, bars, bpm, mode)` ขั้น 5 `base_groove` (kick ช่อง 0, 8 + `hihat_closed` ช่องคู่); `pick`: gate ตาม `range.mode` (`gate_rows.pick_melody` = Basic Pitch, Beat This!, onnxruntime, ffmpeg), โหมดทำนองถอด 22.05 kHz อย่างเดียว รัน Basic Pitch ทีละหน้าต่าง (`percent` ต่อหน้าต่าง + chunk ผ่าน `pick.Steps`, เช็คยกเลิกก่อนทุกหน้าต่าง) แล้ว Beat This! เหมือนเดิม, `analysis.mode` = โหมดของ range, ตัด `MELODY_NOT_YET`; `lesson._scored` ส่ง `analysis.mode`
- test seam 2 (`test_drum_notes_score.py` +6): แผนหน้าต่าง, pad ศูนย์, เวลาเฟรม/ตัดขอบ/เกินช่วง, รวมเฟรมติดกันข้ามหน้าต่าง (ห่าง 68 sample) และ 2 เฟรมห่างเป็นสอง, preview ทำนอง (kick 0/8/16/24, ไฮแฮท R ทุกช่องคู่, snare L, ผ่าน `lessons.from_song`), โหมดกลองไม่เติม; seam 1 (`test_drum_notes_pick_api.py`): แกะทำนอง 6 s = 4 หน้าต่าง + 1 chunk `percent` 0 → 80 → done, feed `(1, 43844, 1)` ×4, hits snare ทุก 0.5 s, แถวรายการ `{mode: melody, bars: 2}`; gate ทำนองไม่ต้องมี marker ADTOF แต่ต้องมี Basic Pitch (`503` rows `["model_basic_pitch"]`); `test_drum_notes_lesson_api.py`: `written_song(mode="melody")` → preview snare 4/8/20/24 L + base, สร้างบทเรียนได้ Groove สามชิ้นและ `timeline.build` มีทั้งสาม, `/listen` 200 wav; fake: `FakeOnnxRunner(onset=…)` + `melody_onsets`, checkpoint `window n`
- frontend: ปุ่ม "ทำนอง" กดได้ คำอธิบายแสดงเมื่อเลือกทำนอง; หัว "ผลแกะ" บอก "โหมดกลอง"/"โหมดทำนอง"; ใต้ตารางของเพลงโหมดทำนอง "สแนร์คือจังหวะทำนอง · กระเดื่องจังหวะ 1 และ 3 กับไฮแฮทปิดทุกครึ่งจังหวะ แอปเติมให้" (`MELODY_BASE`); e2e ใหม่ 1 (เลือกทำนอง → `PUT /range` `mode: melody` → ผลบอกโหมด → ตารางมี kick ช่อง 1, 3 ไฮแฮท R snare L) + ปรับ 2
- รันจริง (Mac, โมเดลจาก revision ที่ pin, `ffmpeg` + `score` ตรง ไม่ผ่าน HTTP) บน "Yiruma - River Flows in You - Kalimba Cover" (`DdYi7i6t2R8`, 162 s): ช่วง 0–30 s → decode 0.1 s, Basic Pitch 19 หน้าต่าง 0.2 s, Beat This! 2 chunk 1.8 s; onset 82 ตัว; ท่อน intro เล่นอิสระ Beat This! ให้ห้อง 1–3 จังหวะจน 20 s แล้วเป็น 4/4 ห้อง 24–28 (~1.85 s ≈ BPM 131); เลือกห้อง 24–25 → snare ที่ช่อง 0, 4, 8, 12, 14 | 16, 20, 26, 28, 30 (ทุกจังหวะ + บางครึ่งจังหวะ = arpeggio มือซ้ายของเพลง) มือ L ทุกตัว ไฮแฮท R kick 1, 3 ไม่มี dropped; ช่วง 20–50 s → onset 110 แต่ Beat This! ให้ 2 จังหวะต่อห้อง (half-time) ทั้ง 16 ห้อง จึงเลือกไม่ได้ — เหมือนที่ 02 บันทึก ขึ้นกับช่วงที่เลือก

**Decided:**
- D26 — ทางเลือกเล็ก: I/O จริงของไฟล์, หน้าต่างตามโค้ดต้นฉบับ เวลาเฟรมจากต้นหน้าต่าง (ตารางเดียวเลื่อน 8.5 ms ต่อหน้าต่าง), onset เฟรมติดกันเป็นการตีเดียว, ถอด 22.05 kHz อย่างเดียว, `pick.Steps`, ขั้น 5 ใน `score.preview(mode)`, ข้อความและหัว "ผลแกะ" บนหน้าเพลง, fake `onset`, vitest คงเดิมตาม D25; เปลี่ยน D24 (ไม่มี `400` field `mode`) และแก้ spec › Pick job (ลำดับขั้น, `preparing` อัตราเดียวในโหมดทำนอง)
- AC ของ ticket เขียน "pad ครึ่งหน้าต่างที่ต้น" — ของจริงคือครึ่งของ overlap (3,840 sample = 15 เฟรม) ตาม `get_audio_input` ไม่ใช่ครึ่งของหน้าต่าง 43,844; ทำตามโค้ดต้นฉบับ (D26)

**ตัดสินโดยเจ้าของ (ยังค้าง):** เจ้าของเปิด `#/songs` วางลิงก์ kalimba หรือ piano (เช่น `https://www.youtube.com/watch?v=DdYi7i6t2R8`) เลือก "ทำนอง" แกะช่วงที่จังหวะคงที่ (เพลงนี้ 0–30 s แล้วเลือกห้อง 24–25) กด "ฟัง" เทียบว่า snare ตรงจังหวะทำนองที่ได้ยิน; ยังค้างจาก 03 ด้วย (ตาราง intro ของ reel/SLTS)

**For the next ticket:**
- Beat This! บนเพลงทำนองเบา (kalimba 20–50 s) ให้ 2 จังหวะต่อห้องทั้งช่วง → ไม่มีห้อง 4/4 ให้เลือก; ช่วง 0–30 s ของเพลงเดียวกันได้ 4/4 — ถ้าเจ้าของเจอบ่อย ค่อยคิดเรื่องรวมห้อง 2 จังหวะเป็นคู่ (เปลี่ยน spec ต้อง `/warroom drum-notes`; บันทึกแล้วใน 02)
- Basic Pitch ถูกฝึกกับเสียง piano-like: เพลงที่มีกลองหรือเสียงรบกวนให้ onset ของมันเอง → โหมดทำนองจะได้ snare เกิน (เลือกช่วงที่เป็นทำนองล้วน)
- ยังค้างจาก 03: `crash` + ไฮแฮทช่องเดียว (D13), `setup.py` `OpenSession` alias ซ้ำ, `threading.Timer(0.3)` ใน test `run_capture`, `Placed.piece: str`
- แบบ Figma สองหน้า (Blocked 1–2) แล้วปรับหน้าเว็บตามแบบ

**Checks:** `uv run pytest` 1379 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 545 passed; `npm --prefix frontend run build` ผ่าน. Review สามแกนจาก `8012bbb`: Standards 0 ผิดกติกา + 1 ก้ำกึ่ง (แก้: `MELODY_BASE` ใช้ชื่อชิ้นไทยตามตาราง) + smell 7 (แก้ทั้งหมด: `_pick` ซ้ำ `update` → `_start_picking`; `pick_drums`/`pick_melody` ซ้ำ → `_pick_rows` + `PICK_GATES` แทน ternary; `_step_done` คำนวณบน `Steps` → `Steps.done_one`; `BEAT_THIS_RATE` → `MODELS_RATE = score.BASIC_PITCH_RATE` และ fake ใช้ค่าเดียวกัน; fake ใช้ `onnx_runner.BASIC_PITCH_INPUT`, 88 → `BASIC_PITCH_NOTES` ที่เดียว; `FoundSection` รับ `mode` แทน `analysis`; `preview(mode)` บังคับส่ง); Spec 0 ผิด + 3 ขาดบางส่วน (`/listen` ของทำนองพิสูจน์แค่ 200 wav — สามชิ้นพิสูจน์บนบทเรียนที่สร้างและ `timeline.build` ทางเดียวกัน ยอมรับ; ข้อความรายการเพลงไม่มี test ของทำนอง — โค้ดไม่เปลี่ยน; วัดมือ → รันจริงใน Log นี้ เจ้าของฟังเทียบค้าง) + 4 นอกที่ขอแต่บันทึกใน D26 (รวม onset เฟรมติดกัน, หัว "ผลแกะ" บอกโหมดกลองด้วย, บรรทัด `MELODY_BASE`, ถอดอัตราเดียว → แก้ spec › Pick job) + 3 เอกสารคลาด (แก้: AC "pad ครึ่งหน้าต่าง" บันทึกใน Decided; D24 Status → changed by D26 + แถว index; spec › Pick job เรียงขั้นตามโค้ด) + 1 test (แก้: ตัด assert ค่าคงที่กับค่าคงที่); Newcomer สรุปตรง What to build + เดา 7 จุด (แก้ทั้งหมด: ชื่ออัตรา, comment `Steps` บนช่องเดียว, docstring `melody_onsets` บอกว่าช้าไม่เกินหนึ่งเฟรม, fake นับหน้าต่าง "ตามลำดับครั้งเดียว", `mode` จาก parent, comment fixture `midiAnalysis`, comment `ONSET_MERGE_SAMPLES` "ต่ำกว่า")

### 03: เลือกห้อง ฟัง แล้วสร้างบทเรียนกลอง — done 2026-11-14

**Built:**
- backend `drum_notes.lesson` (`preview`/`listen`/`create`; `checked_choice` ตรวจ body, `chosen_bars` = Score ขั้น 2) + `score.preview` (ขั้น 3–8: quantize `floor(x + 0.5)`, ตัดเกินสองมือตาม `KEEP_ORDER`, มือ L/R ตาม `RIGHT_ORDER`/`_hand`, BPM ตั้งต้น `240 / median` ปัดครึ่งขึ้น จำกัด 40–240) คืน `Scored`; สาม route `POST /songs/{id}/preview|/listen|/lessons` (`Preview`/`Created` response); `video_gen.lessons.from_song`/`create_from`/`unsaved` (กฎของ `PUT` เดียวกัน, `lesson.json` ไม่มีช่องใหม่); `songs.add_lesson`; `/listen` ส่ง `audio/wav` `Cache-Control: no-store` ไม่มีไฟล์ใหม่
- test seam 2 (`test_drum_notes_score.py`): ทุก AC ของ Score รวม round trip ±20 ms และ activation สุ่ม 100 ชุดผ่านกฎ D20; seam 1 (`test_drum_notes_lesson_api.py` 14 test ด้วยเพลง MIDI และเพลงที่เขียน analysis ตรง): ห้อง 3 จังหวะเลือกไม่ได้, บรรทัดรองตัด 60, ลบบทเรียนแล้วเพลงไม่ error, ลบเพลงบทเรียนอยู่
- frontend: `kit.ts`/`lesson.ts`/`useListen` (+ `useListen.test.ts`) ใน `src/lib/`; `GrooveGrid` ใน `components/ui/` รับ `editing` (ไม่ส่ง = อ่านอย่างเดียว); หน้าเพลง: `FoundSection` → `LessonPick` (`useLessonPreview`: ห้องแรกจากแถบ, จำนวนห้อง 1–4 ไม่เกินห้อง 4/4 ที่เหลือ, BPM, `POST /preview` debounce 300 ms, ตาราง + รายการ "ตัดโน้ตที่มือตีไม่ได้", ฟัง, สร้าง → `#/drums/{id}`), "บทเรียนจากเพลงนี้"; e2e 10 test ใน `SongsPage.test.tsx`
- รันจริง (Mac, โมเดลจาก revision ที่ pin, `ffmpeg` + `score` ตรง ไม่ผ่าน HTTP): `reel.mp4` 0–19 s → 118 การตี 15 ห้อง ห้อง 1–2 4/4 BPM ตั้งต้น 111 ไม่มี dropped; Smells Like Teen Spirit (`hTWKbfoikeg`) 0–30 s → 162 การตี 15 ห้อง ห้อง 1–3 เงียบ ห้อง 4–12 4/4 (ห้อง 13–15 ท่อนเบา 2 จังหวะ) เลือกห้อง 4–5 BPM ตั้งต้น 115 ไม่มี dropped. ตารางสองห้องแรกของ intro ทั้งสองคลิป **ตรงกัน**: ห้อง fill = `tom_mid` R + `snare` L ทุกจังหวะ, `kick` ที่ e และ a ของจังหวะ 1–3 และที่ & ของ 4, `hihat_closed` R ที่ e ของจังหวะ 1–3; ห้อง groove เริ่ม `crash` + `hihat_closed` + `kick` ที่ 1 แล้ว SLTS ต่อด้วย snare ที่ 2, 4 (+ e ของ 2–3) ไฮแฮท 8th. ตำแหน่ง kick/snare ตรงกับ spike ของ 01–02 (kick 7 snare 4 tom 4 ในห้อง fill)

**Decided:**
- D25 เพิ่มจาก review: BPM ปัดครึ่งขึ้น; `lesson.Choice`; `score` คืน NamedTuple, response model ใน `lesson`; `notePlace`/`hitName`/`BAR_COUNTS` ใน `lib/lesson.ts`; `useListen.test.ts`

**ตัดสินโดยเจ้าของ (ยังค้าง):** ตารางด้านบนคือสิ่งที่แอปให้ — เจ้าของเปิด `#/songs` เอา `reel.mp4` หรือลิงก์ SLTS เข้า แกะ 0–30 s เลือกห้อง 4–5 (SLTS) หรือ 1–2 (reel) กด "ฟัง" เทียบกับเพลง แล้วบันทึกสิ่งที่ต้องแก้มือ. ที่เห็นจากตาราง: (1) `crash` กับ `hihat_closed` ช่องเดียวกันทำให้ crash ได้มือ L (RIGHT_ORDER ให้ไฮแฮท R) — มือกลองจริงตี crash R แทนไฮแฮท ถ้าเจ้าของเห็นด้วย เป็นกติกาใหม่ "crash + ไฮแฮทช่องเดียว → ตัดไฮแฮท" (เปลี่ยน D13 → `/warroom drum-notes`); (2) `hihat_closed` ที่ e ของ fill น่าจะเป็น false positive ของ snare (ADTOF class 3) → ลบมือในหน้าแก้; (3) kick ที่ 16th ของ fill ของจริงอาจเป็น kick-kick-snare บน 8th — ต้องฟัง

**For the next ticket:**
- โหมดทำนอง (04): `pick._pickable` ปฏิเสธ `mode` `melody` ที่ `MELODY_NOT_YET`; gate `pick_melody` ยังไม่มีใน `gate_rows`; ปุ่ม "ทำนอง" `disabled`; Basic Pitch I/O ดู Log ของ 01
- `lesson._lesson_fields` คือทางที่ `listen`/`create` ใช้ร่วม; โหมดทำนองที่ให้โน้ตเสียง (ไม่ใช่ Groove) ต้องมีทางของตัวเอง ไม่ควรยัดใน `score.preview`
- `written_song(project, subtitle, downbeats)` ใน `test_drum_notes_lesson_api.py` เขียนเพลงที่มี analysis ตรง (`songs.new_song` + `write_new`) — ใช้ซ้ำได้สำหรับ test ที่ MIDI ให้ไม่ได้ (ห้องไม่ใช่ 4/4, บรรทัดรอง)
- `score.default_bpm` กับ `quantize` ปัดครึ่งขึ้นทั้งคู่ (D25); `round()` ของ Python ห้ามใช้กับเลขที่ผู้ใช้เห็น
- Beat This! บนท่อนเบา (SLTS 24–30 s) ยังให้ห้อง 2 จังหวะ → เลือกไม่ได้ (บันทึกใน 02 แล้ว)
- `setup.py` มี `OpenSession` alias ซ้ำกับ `onnx_runner.OpenSession`; test `run_capture` ใช้ `threading.Timer(0.3)` (02)
- `Placed.piece`/`Dropped.piece` เป็น `str` (id ของ `video_gen.kit`) — ถ้า kit ได้ `PieceId` Literal ฝั่ง backend ค่อยใช้
- แบบ Figma สองหน้า (Blocked 1–2) แล้วปรับหน้าเว็บตามแบบ

**Checks:** `uv run pytest` 1370 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 544 passed; `npm --prefix frontend run build` ผ่าน. Review สามแกนจาก `ee62d3b`: Standards 3 ผิดกติกา (แก้: `setTimeout` จริงใน test → `vi.useFakeTimers`; `useListen` ใน `lib/` ไม่มี test → `useListen.test.ts` 5 test; `score` ถือ pydantic response model → ย้าย `Preview`/`DroppedNote` ไป `lesson`, `score` คืน NamedTuple) + smell 10 (แก้ 9: ข้อความตำแหน่งโน้ตซ้ำ → `notePlace`; `HITS.find` ซ้ำ → `hitName`; `trimmed`/`with_hands` วนซ้ำ → `_by_step`; `listen`/`create` ซ้ำ → `_lesson_fields`; `<p>` ว่างซ้ำ → `EmptyNote`; `preview.preview` → spread `ready`; `Found`/`Picked` → `FoundSection`/`LessonPick`; `_hand` คืน `Hand` Literal; `BAR_COUNTS` จาก `BARS_MAX`; import ใน test body → module level; ไม่แก้: `Placed.piece: str` — บันทึก For the next ticket); Spec 0 ผิด + 3 ขาด (แก้: test ห้อง 3 จังหวะจริง, test บรรทัดรองตัด 60, อ่าน `lesson.json` จากไฟล์) + 2 คลาด (แก้: `dropped` ให้ `hihat_open` ที่คู่ไปก่อนตาม D25 จริง; BPM ปัดครึ่งขึ้น); Newcomer สรุปตรง What to build + เดา 13 จุด (แก้ 12: `_new_fields("x")` → ชื่อจริง; เหตุผล `KEEP_ORDER`/`RIGHT_ORDER`; `ALTERNATE_STEP`/`CYMBAL_WITHIN` อธิบายเป็นช่อง 16th; เช็ค step นอกช่วงที่ไม่มีทางถึง → ตัด; `notes[-2]` → ตัวแปร; `Pick` → `Choice`; comment เลข GM และ `timeline.TAIL_S`; `asked`/`withBpm` แทน `pick`/`pickShown` และ comment deps; comment `open()` เสิร์ฟ `RENDER_PATH`; comment หัวตาราง `slice(-1)`; comment key `picked_at`; ไม่แก้: `(800, 5)`/`0.08` มี comment อยู่แล้ว)

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
