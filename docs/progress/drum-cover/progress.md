# Progress: drum-cover

**Now:** ticket ครบ 4/4 และ feature review เสร็จ (`3cf9bfd`); เหลือ Blocked 2 — เจ้าของดูเฟรม reel Yellow ภาพใหม่ใน `docs/features/drum-cover/reel-frames/` แล้วจึง `/pr-open`

**Next:** เจ้าของตอบ Blocked 2 → อ่านออก: `/pr-open`; อ่านไม่ออก: `/warroom drum-cover` (change request)

```
/pr-open
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | reel cover จากเพลงที่แกะ: ตั้งช่วง ข้อความ เสียง ฟัง render | done |
| 02 | ภาพพื้นหลังของ reel และหน้าเพลงบอกเมื่อกลองเข้าช้า | done |
| 03 | ความดังกลองแยกจากเพลง และปิดเสียงกลองได้ | done |
| 04 | ภาพกลองของ reel ใหม่ที่อ่านออกว่าตีชิ้นไหน มือไหน ห้องไหน | done |

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01, 02 | design: หน้าเพลง — ส่วนที่เพิ่ม, หน้า reel | ไม่รอ Figma: สร้างตาม `ui-prompt.md` กับ design system เดิม (D14, แบบ drum-notes D28) | done (01, 02) |
| 2 | 04 | เจ้าของดู reel Yellow 11.5–30 ด้วยภาพใหม่ แล้วยืนยันว่าอ่านออกว่าแต่ละโน้ตตีชิ้นไหนมือไหน (D27; แทนข้อเช็คภาพเดิมของ D15) | เจ้าของ: ดู `docs/features/drum-cover/reel-frames/yellow-{0.03,2.1,5.53,6.22}s.jpg` (หรือ render reel Yellow ใหม่จากหน้า reel) แล้วตอบว่าอ่านออก/ไม่ออกตรงไหน; ดูด้วยว่าไม้ R (ชมพู) ที่ตีไฮแฮทไขว้ไม้ L ผ่าน SNARE/KICK (`yellow-2.1s.jpg`) อ่านยากไหม — ตาม sketch แต่ D25 นับไม้ไขว้เป็นต้นเหตุเดิม (feature review) | open |

## Log

### Feature review — 2026-11-16

**Built:** review สามแกน (subagent) บน `ba5135b..aff80f5` — Standards 0 breach + 2 ข้อ soft + ~10 smell, Spec 0 blocking + 6 ข้อ, Newcomer 15 จุดเดา (สรุปตรงกับ spec › Solution). แก้ใน `3cf9bfd` (auto mode, ตัวเลือก Recommended: ข้อเล็กที่ชัด):
- `drum_cover.frames.drawn_of`/`is_stroke` แทน `KIT[DRAWN_OF[…]]` และเงื่อนไขมือซ้ำใน frames/captions; ลบ `KIT_BOX` ที่ไม่ใช้; `_lit` → `_latest_hits`; `FULL_SPEED`; comment `probe`, ความเร็วเลน 4 จังหวะ, จุดจังหวะ, `Scene(…, None)`, `until > at`
- `audio`: `INT16_MAX`, `pcm`
- tests: `timing_of`/`END_S` ไป `fakes.py` (test ไม่ import test อื่น, fastapi-api testing.md); เลน test เช็คแถว HI-HAT ด้วย; `CLIP_S`; test volume ใส่ `drums` เอง; comment แถวและ `volume=16`
- frontend: `Sound` type เดียวของ `drums`/`backing`; comment `fireEvent.change` ของ range
- `vite-react-web/SKILL.md` มี `Switch`; spec › Modules touched ชี้ `backend.subtitles` (D29)

**Decided:** ไม่มี D ใหม่ — ปัด (บันทึกไว้ ไม่ทำ):
- `px_per_s` 4 จังหวะ (For the next ticket ของ 04): เป็นความเร็วเลนเท่านั้น เส้นห้องมาจาก downbeat — ไม่ต้องเปลี่ยน
- `scene.hits`/`times` คู่กัน, hex parse สามที่ (สองที่ใน video-gen), รายชื่อ field ของ cover หลายที่, `_note_head` แยกตาม piece id, string ของจังหวะ/มือ, สวิตช์ของ `toon`, test อ่าน `scene.bars`/`px_per_s`, `KIT` เทียบตัวเอง, ป้ายมือคิดสองที่ (`_latest_hits` vs `_badges`), `text.ass` ของบทเรียนเช็คด้วยมือ — smell ที่ยังไม่คุ้มรื้อ
- ไม้ไขว้ตอน R ตีไฮแฮท: ตาม sketch (D26) — ส่งให้เจ้าของดูใน Blocked 2

**Checks:** `uv run pytest` 1487 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 609 passed; `npm --prefix frontend run build` ผ่าน

### 04: ภาพกลองของ reel ใหม่ที่อ่านออกว่าตีชิ้นไหน มือไหน ห้องไหน — done 2026-11-16

**Built:**
- prefactor video-gen (ผลเดิม): `frames.background_image`, `frames.stick_tip(times, targets, rest, t)`, `frames.paste`/`shrunk`/`lighter` public; `captions.stick_letters(tips_at, total)`; helper ASS `style`, `pos`, `ass_color`, `squeeze(width, max_px)`, `at_most_two` ย้ายไป `backend/subtitles.py` — `text.ass` และ hash เฟรมของบทเรียนตัวอย่างเท่าเดิมทุกตัวอักษร (เทียบก่อน/หลังด้วยมือ); test เดิมของ video-gen ไม่แก้
- `drum_cover.frames`: ชุดกลองมุมบน 9 ชิ้นตาม sketch (พัก 30 %, ตีเติมเต็ม ขอบขาว ขยาย 1.12/1.2 แล้วหด, ghost 60 %, HH เปิดมีวงขาว), ไม้ L ขาว R ชมพู ขยับด้วย `stick_tip`, ป้ายมือ, เลนละชิ้นที่เล่น (สูง `min(84, 420/n)` กลางกรอบ, หัวโน้ตตามชนิด, ตัดที่ขอบเลน), จุดจังหวะ, `Scene.still` วาดเมื่อใช้
- `drum_cover.captions`: หัวเรื่องบีบ ≤ 760 px, บรรทัดรองบีบ ≤ 760 px, คำบรรยาย, ป้ายชิ้นตลอดคลิป, ชื่อเลนสีของชิ้น, "ห้อง n" ต่อ downbeat, เลขห้องเหนือเลน, ตัว L/R ในหัวโน้ตเลื่อนด้วย `\move` + `\clip`, ป้ายมือ, ตัว L/R บนหัวไม้
- `render` ใช้ภาพและตัวหนังสือของ reel; test เสียงตรงภาพอ่านสีเติมเต็มของ snare ที่จุดวัดสี (`#60A5FA` ± 12) แทนวงแดง
- tests: `test_drum_cover_frames.py` (7: ตารางชิ้น, สีเติม/พัก + bytes เดียวกัน, สีไม้, เลน 3 แถว + หัวโน้ตที่ x 330, หางเสียงนิ่ง, ห้อง 5 จังหวะ + ห้อง 3 จังหวะ, จังหวะก่อน downbeat), `test_drum_cover_captions.py` (7: ป้ายชิ้น, ชื่อเลน, "ห้อง 1/2", ตัว L/R ของมือเท่านั้น, หัวเรื่องและบรรทัดรองบีบ 760, ป้ายมือถึงการตีถัดไป); ลบ test ภาพเดิมสองตัวใน `test_drum_cover_timeline.py`
- วัดมือ: reel 30 วินาที (Yellow 11.5–30 ต่อซ้ำ) render 8.9 วินาที; reel Yellow 11.54–30 render 6.3 วินาที (D15 ≤ 60)
- เฟรมให้เจ้าของดู: `docs/features/drum-cover/reel-frames/yellow-0.03s.jpg` (crash + kick ต้นห้อง 1), `yellow-2.1s.jpg` (snare L + hi-hat R), `yellow-5.53s.jpg` (crash + kick ห้อง 3), `yellow-6.22s.jpg` (snare + hi-hat) — Blocked 2
- review (subagent): Standards 3 breach + smells, Spec 0 blocking + 4 ข้อ, Newcomer 14 จุดเดา — แก้: helper ASS ไป `subtitles`, ใช้ `paste`/`shrunk`/`lighter` ของ video-gen แทนสำเนา, test แยกตาม module, import ที่ไม่ใช้, `Scene.ahead_s`/`behind_s` ที่เดียว, `_dot_sprite` แทน `_badge`/`_dot`, `bar_starts`, swings ซ้ำ, `__all__`, ชื่อ `note head`/`NoteLetter`, docstring `bars_of`, comment crop/hand loop, test ใช้ค่าคงที่ของ sketch (y 1390/1474, สี) แทนค่าของโค้ด, test ป้ายมือสลับมือ, บรรทัดรอง 760 px, ป้ายมือชนป้าย HI-HAT ย้ายไปขอบขวา

**Decided:** D29

**For the next ticket:**
- `px_per_s` ใช้ห้อง 4 จังหวะที่ `scroll_bpm` (ค่ากลางของระยะจังหวะ) ไม่ว่าเพลงเป็นกี่จังหวะ (D4 เดิม) — Newcomer สังเกต; feature review ดูว่าต้องเปลี่ยนไหม
- ชื่อจังหวะ/มือเป็น string เปล่า (`"accent"`, `"L"`) ทั้ง video-gen และ reel — Standards: Primitive Obsession; ใช้ร่วมกับ `timeline.NoteKind` อยู่แล้ว ยังไม่รื้อ
- `_note_head` แยกรูปตาม piece id แทน `Drawn.shape` (ฉาบกับไฮแฮทรูปต่างกันในเลน จึงยังไม่รวม)

**Checks:** `uv run pytest` 1487 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 609 passed (รอบแรก 1 ล้มใต้โหลด ผ่านเมื่อรันซ้ำ — frontend ไม่ถูกแตะ, flaky เดิม); `npm --prefix frontend run build` ผ่าน

### 03: ความดังกลองแยกจากเพลง และปิดเสียงกลองได้ — done 2026-11-16

**Built:**
- backend: `cover.Drums` `{on, volume}` (ค่าตั้งต้น เปิด 100 สำหรับ `cover.json`/`.json` ของ render เก่า); `PUT` ตรวจ `drums` ด้วย `_sound` ตัวเดียวกับ `backing`, ปิดทั้งคู่ → `400` `drums.on`; `used(check_sound)` ปฏิเสธ cover แก้มือที่เงียบที่ฟังและ render; `audio.reel_wav`: กลอง 100 + backing ปิด = `mixer.mix` ตรง ๆ, กลองปิดไม่เรียก mixer, ผลรวมลดเฉพาะเมื่อเกิน −1 dBFS (ไม่ดันขึ้น); render `.json` มี `drums`
- frontend: การ์ดเสียงมีบรรทัด "กลอง" สวิตช์ "ปิดเสียงกลอง" + สไลเดอร์ "ความดังกลอง" ({v}%); ปิดทั้งคู่ → ข้อความที่การ์ด ปุ่ม "ฟัง"/"render reel" กดไม่ได้; แถวผลป้าย "ไม่มีเสียงกลอง"/"กลอง {v}%"; `Switch` ย้ายไป `components/ui`
- tests: API +5 (field ของ `drums`, ปิดทั้งคู่, ไฟล์เก่า + cover เงียบที่ listen/render, wav เดิมที่ 100 และ −6.0 dB ที่ 50, กลองปิด = เพลง × volume ± 1 LSB, render กลองปิด + `.json` เก่า) และ test "never clips" ใช้เพลงดังเกิน full scale; e2e +3 (สไลเดอร์ 60, ปิดเสียงกลอง, ป้ายแถวผล)
- review (subagent): Standards 1 breach + 8 smell, Spec 0 + 1 test note, Newcomer 9 จุดเดา — แก้: `Switch` ร่วม, `_sound` คืน model, ชื่อ `drum_pcm`/`ceiling`, `BACKING_VOLUME`/`FULL_VOLUME` (ทั้งสองฝั่ง), test wav 100 ไม่วนผ่าน `cover.used`, ชื่อ test สองตัว, comment สวิตช์กลับด้านและ int16 ÷ 32767

**Decided:** D28

**For the next ticket:**
- สวิตช์ของ `toon` (`CardEditor.tsx:187`, `SeriesForm.tsx:393`) ยังเขียนเอง — ใช้ `components/ui/Switch` เมื่อแตะไฟล์นั้น
- รายชื่อ field ของ cover ซ้ำหลายที่ (`fieldsOf`, `sameFields`, รายการ field ที่แสดงข้อผิดพลาดในช่อง, `cover_body`/`bodyOf` ของ test) — review: Shotgun Surgery; ยังไม่ใหญ่พอให้รื้อ
- backing เปิด: wav ต่างจากก่อน ticket นี้ ≤ 1 LSB (อ่านกลองเป็น int16 ÷ 32767, D28); D15 ยังจริงสำหรับกลองล้วน 100

**Checks:** `uv run pytest` 1475 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 609 passed; `npm --prefix frontend run build` ผ่าน

### Change request — 2026-11-16

- คำขอเจ้าของ (Telegram): ความดังกลองแยก + mute และบันทึกในผล render; ภาพกลองอ่านไม่ออก; "ทำได้โดยไม่อิงคลิปต้นฉบับ" → ตีความว่าออกแบบภาพ reel ใหม่ได้ทั้งหมด (auto mode, Recommended)
- ดูเฟรมจริงของ reel Yellow: กระเดื่องบัง snare/ทอม, ไม่มีชื่อชิ้น, ทอม 2 ใบสีเดียว, crash/ride สีเดียว, เลน 3 เลนรวมชิ้น, ไม้สีเดียวไขว้กัน
- Decided: D24 (`drums {on, volume}`, ลดเฉพาะเมื่อเกิน −1 dBFS), D25 (ภาพ reel เป็นของ `drum_cover`, video-gen ไม่เปลี่ยน; D3/D4 changed by D25), D26 (sketch `reel-picture-sketch.md`), D27 (เป้า)
- legal: ข้อ 2 และ 4 คง CONDITIONAL ไม่มีเงื่อนไขใหม่
- Breaker: 1 BLOCKER + 4 CONCERN แก้ docs ครบ — จุดวัดสีแยกจากจุดตีและป้าย (BLOCKER), ป้ายครึ่งบน/จุดตีครึ่งล่าง, หัวเรื่อง ≤ 760 px ไม่ชนตัวนับ, ที่พักไม้นอกกระเดื่อง, จังหวะ > 4 → จุดที่ 4
- ADR: 0054 (ภาพ reel เป็นของ `drum_cover`); D24 เป็นพฤติกรรมของ feature ไม่ใช่ ADR
- Gate: Approve (auto mode, Recommended)


### 02: ภาพพื้นหลังของ reel และหน้าเพลงบอกเมื่อกลองเข้าช้า — done 2026-11-15

**Built:**
- `backend.pictures` (ใช้ร่วม: `checked_size`, `receive(body, partial, expected, place)`); `video_gen.backgrounds` เรียกมัน (test เดิม 86 ผ่านโดยไม่แก้)
- `drum_cover.backgrounds`: `check`/`PUT ?size=`/`DELETE`/`GET background.jpg`, `song_busy` "กำลัง render reel ของเพลงนี้อยู่" ระหว่าง render (และของ drum-notes ระหว่าง Pick job), `.tmp` ไม่ขึ้นต้นด้วย song id; render ใช้ภาพที่ copy ไว้ เบลอ ทำมืด
- frontend: `BackgroundPicker` + `useBackground` ย้ายไป `components/ui` และ `lib` (รับ `path`, `imageUrl`, `apply`); การ์ดพื้นหลังบนหน้า reel; หน้าเพลงมี Alert "ไม่พบการตีกลองในช่วง…" และ "ห้อง 1–{k} ไม่มีการตี การตีแรกอยู่ที่ {t} วินาที" + ปุ่ม "เริ่มช่วงที่การตีแรก" (`PUT /range` แล้ว `POST /pick`), `lateStart` ในกรณีขอบ D19
- tests: API +4 (ครอป 1080×1920, 415/413, render ภาพเบลอและ `song_busy` ระหว่าง render, ภาพหายแล้วใช้สี), e2e +4 (Alert ไม่มีการตี, ห้องว่าง + ปุ่ม, การตีก่อน downbeat ไม่ขึ้น, เลือก/ลบ/ปฏิเสธภาพ), lib +3 (`lateStart`)

- review (subagent): 7 ข้อ แก้ 6 — ภาพหายแล้ว `GET` ยังบอก `image` (บันทึกไม่ได้), เขียน `cover.json` ก่อนวางไฟล์, test 415 ผ่าน `PUT` จริง, status ของ 415, e2e ปุ่มใกล้ท้ายเพลง, e2e การตีกลางห้อง; ยึด D9 (ต้นห้องแรกที่มีการตี) แทนเวลาการตี และคำของ `BackgroundPicker` ร่วม — บันทึกใน D23

**Decided:** D23

**Checks:** `uv run pytest` 1470 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 606 passed; `npm --prefix frontend run build` ผ่าน

### 01: reel cover จากเพลงที่แกะ — done 2026-11-15

**Built:**
- backend `drum_cover`: `cover` (`cover.json` ใต้ `songs.lock`, ค่าตั้งต้นจากต้นห้องแรกที่มีการตี, ช่วงตั้งต้น ≥ 2 วิ, ดึงเข้าช่วงเมื่อแกะใหม่ `adjusted`, `has_audio`, `hits`), `timeline` (การตีตามเวลาจริงผ่าน `video_gen.timeline.assemble`, มือจาก `groove.trimmed`/`with_hands` บนห้องของ downbeats ทั้งหมด, เลขจังหวะนับถอยจากจำนวนจังหวะของห้องแรก, Lesson ชั่วคราวท่อนเดียว), `audio.reel_wav` (กลองของ mixer; backing ถอด m4a เป็น f32le ผสม numpy แล้ว peak −1 dBFS; `ffmpeg_failed` 500 เมื่อไฟล์เสีย), `render` (slot ของตัวเอง, copy เข้า `media/songs/.render/`, คำสั่ง ffmpeg เดิมของ video-gen, json มี `start_s`/`end_s`/`picked_at`/`backing`, ลงทะเบียน `songs.song_jobs`), routes `/api/songs/{id}/cover…` + `/api/covers/render`, `JOB_HOLDERS`, `paths.songs_render_dir`
- prefactor: `video_gen.timeline.assemble` (`build` ให้ผลเดิม; test เดิมผ่านโดยไม่แก้)
- frontend `features/drum-cover`: `CoverPage` (ช่วง + แถบห้องในช่วง, ข้อความ + ตัวนับ, เสียง กลองล้วน/+ เพลงต้นฉบับ, บันทึก/ฟัง/render reel, ผล render พร้อมป้าย "มีเพลงต้นฉบับ"/"แกะใหม่แล้ว", ลบพร้อมยืนยัน, ถามก่อนออก), `useCover`, `useCoverRender`; `App` เลือกหน้าด้วย `coverViewOf`; หน้าเพลงมีส่วน "Reel cover" เหนือ "สร้างบทเรียน" (`ReelCover` + `useReelRenders`), ปุ่มสร้างบทเรียนเป็นปุ่มรอง
- tests: `test_drum_cover_timeline.py` (17), `test_drum_cover_api.py` (19, ffmpeg จริง: mp4 1080×1920 h264+aac, เสียงตรงภาพ ≤ 1 เฟรม, wav เดิมทุก byte, backing ไม่ clip, busy/song_busy/cancel/restart), `CoverPage.test.tsx` (14 ผ่าน `App`); `written_song` ย้ายไป `fakes.py` + `song_m4a`
- วัดมือ: reel 30 วินาที render 12.7 วินาที (D15 ≤ 60)
- review (subagent): 11 ข้อ แก้ครบ — volume ที่ซ่อนแล้วผิด, ช่องว่าง = 0, save ซ้อน/ทับสิ่งที่พิมพ์, listen 500 เปล่า, `__init__.py`, `field` ของช่วงที่ไม่ใช่ตัวเลข/NaN, แถบห้องทั้งเพลง, เลขจังหวะห้องแรก 3/4, เทียบ draft ตามลำดับ key, alias ชื่อซ้ำ, error ค้างหลังแก้; เพิ่ม test `..`

**Decided:** D22

**For the next ticket:**
- ร่างของ 02 อยู่ใน tree แล้ว (ยังไม่ commit): `backend/pictures.py`, `frontend/src/lib/useBackground.ts`, `frontend/src/components/ui/BackgroundPicker.tsx` — ต่อสาย `video_gen.backgrounds` และ `LessonEditor` เข้าแล้วลบของเดิม
- vitest `DraftProgress.test.tsx` (spoil-maker) ล้มครั้งหนึ่งตอนรันทั้งชุดใต้โหลด ผ่านเมื่อรันซ้ำ 3 ครั้ง — flaky ไม่ใช่ของ ticket นี้

**Checks:** `uv run pytest` 1466 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 598 passed; `npm --prefix frontend run build` ผ่าน

### Planning — 2026-11-15

- Phase 1–2.5 (session ก่อน): `spec`, `decisions` D1–D16, `flow`, `legal` (commit `6742a45`)
- Red team (5 subagent `opus`): 3 BLOCKER + 22 CONCERN → แก้ docs 14, ตัดสินใหม่ D17–D21, ปัด 3 (Skeptic: ตัดภาพพื้นหลัง — brief ของเจ้าของขอ; ตัด D9 — user story 7 ของเจ้าของ; ตัดตัวนับ/BAR — D3 เลือกแล้ว เจ้าของตัดสินบน Yellow ตาม D15)
  - BLOCKER Skeptic (แก้ video-gen หลายไฟล์) → D17: ตัด prefactor `captions` และ `_command`, เหลือ `assemble` + ย้ายของรับภาพ ที่ผลเดิมไม่เปลี่ยน
  - BLOCKER Builder (`amix` index ผิด, `-map` ทำภาพหาย) + Breaker (clip, wav header จาก pipe) → D17: ผสม backing ใน numpy ทางเดียว
- ADR sweep (The Successor): 0050 แทน 0045 (backing ใน reel), 0051 ต่อ 0041 (Timeline จากเวลาจริง), 0052 (cover เป็นของ Song), 0053 ต่อ 0046 (ไม่หารายได้); 0028 เพิ่ม route ภาพของ cover; ปัด D (ทิศ import — อยู่ใน 0052) และ E (stack video-gen — D17 ลด coupling)
- Gate: Approve (auto mode, Recommended); Open Questions 2 ข้อ non-blocking (legal 1–2, D16)
- `ui-prompt.md` เขียนแล้ว เป็นสเปกจอแทน Figma (D14)
