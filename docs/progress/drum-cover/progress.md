# Progress: drum-cover

**Now:** ticket 01–02 done; [PR #16](https://github.com/mousemouse094526/framecraft/pull/16) merge เข้า `develop` แล้ว (`fb354f2`) — เหลือเจ้าของเช็ค reel Yellow (D15). คำขอเปลี่ยน (ความดังกลอง + ความชัดของ UI กลอง) เปิดเป็น change request ผ่าน `/warroom drum-cover`

**Next:**

```
/warroom next
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | reel cover จากเพลงที่แกะ: ตั้งช่วง ข้อความ เสียง ฟัง render | done |
| 02 | ภาพพื้นหลังของ reel และหน้าเพลงบอกเมื่อกลองเข้าช้า | done |

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01, 02 | design: หน้าเพลง — ส่วนที่เพิ่ม, หน้า reel | ไม่รอ Figma: สร้างตาม `ui-prompt.md` กับ design system เดิม (D14, แบบ drum-notes D28) | done (01, 02) |

## Log

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
