# Progress: reels-only

**Now:** PR [#21](https://github.com/mousemouse094526/framecraft/pull/21) รอ review และ merge

**Next:**

```
/warroom next
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | หน้า reel กลอง แทนสอนกลอง | done |
| 02 | หน้าเพลงไม่มีบทเรียน และลบโค้ดสร้างบทเรียนจากเพลง | done |

## Log

### Feature review — 2026-11-18

**Fixed:**
- Alert ของ reel แบบเก่าตามจำนวนรอบที่เลือกอยู่ ไม่ค้างที่ค่าตอนเปิด
- test: `PUT` แบบเก่าสามครั้งติดกันเก็บสำเนาแรกไว้, select มี 1–8, test helper ใช้ `lessons.BACKUP_FILE`
- ชื่อ: `MergedRepeats`, `oldShape` แทน `legacy`; comment บอกว่าทำไม backend ยังรับหลายท่อน; docstring `trimmed` บอกว่าโน้ตที่ตัดยังดังใน reel cover
- `CONTEXT.md` Reel cover ไม่มีคำว่าท่อนสอน

**Not changed:**
- กฎรูปร่าง reel อยู่สองฝั่ง (`isReelShape` คู่ `_is_reel_shape`) แบบ `lengthOf`: มี comment "keep the two alike"
- ชื่อ lesson ในโค้ด: ADR-0066 (Open Questions 1)

**Checks:** `uv run pytest` 1543 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 648 passed; `npm --prefix frontend run build` ผ่าน

### 02: หน้าเพลงไม่มีบทเรียน และลบโค้ดสร้างบทเรียนจากเพลง — done 2026-11-18

**Built:**
- หน้าเพลงเหลือหัวเพลง ช่วงแกะ แกะโน้ต คำเตือนการตีแรก และการ์ด Reel cover (ขึ้นแม้ไม่มีห้อง 4/4); รายการเพลงไม่นับบทเรียน dialog ลบไม่พูดถึงบทเรียน
- route `preview` `listen` `lessons` ของเพลง, `drum_notes.lesson`, `from_song` `create_from`, `Song.lessons`, hook preview/titles ลบ; `song.json` เก่าที่มี `lessons` อ่าน เขียน ลบได้
- ไม่มีคำว่าบทเรียนหรือสอนใน string บนจอทั้งแอป

**Decided:**
- D14 — `groove` เหลือกฎมือ, test กฎมือเรียกตรง, `GrooveGrid` ต้องมี `editing`, `MELODY_HINT`

**For the next ticket:**
- ห้ามรัน `npx prettier --write`: repo ไม่มี config และไฟล์เขียนบรรทัดยาว; prettier ค่าตั้งต้นพับทุกบรรทัดที่ 80 (เกิดใน ticket นี้ แก้กลับแล้ว)
- `groove` อยู่ใน `drum_notes` แต่มีแค่ `drum_cover` ใช้ — ย้ายได้เป็นงานแยก

**Checks:** `uv run pytest` 1542 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 648 passed; `npm --prefix frontend run build` ผ่าน

### 01: หน้า reel กลอง แทนสอนกลอง — done 2026-11-18

**Built:**
- เมนูและหน้า `#/drums` เป็น "reel กลอง": รายการ reel, หน้าแก้มี Groove กับจำนวนรอบ 1–8 ไม่มีท่อนสอน; คำบนจอไม่มีบทเรียนหรือสอน
- reel เก่าหลายท่อนเปิดได้ รวมรอบ (ไม่เกิน 8) บอกว่าบันทึกแล้วอะไรหาย; `PUT` ครั้งแรกเก็บ `lesson.before-reels-only.json`
- reel ใหม่เริ่มท่อนเดียว 4 รอบ (ความยาวเท่าเดิม 13.5 วินาที); ข้อความ error ของ backend เป็นคำของ reel

**Decided:**
- D13 — ชื่อของกฎรูปร่าง reel, ลบไฟล์ซ้ำของ video-gen, test รอ `hashchange`

**For the next ticket:**
- `test_drum_notes_lesson_api.py` แก้ assertion ค่าตั้งต้นไว้ชั่วคราวให้เขียว ticket 02 ลบทั้งไฟล์
- `lib/lesson.ts` บรรทัด "1–4: the bar counts …" เป็น comment ลอยที่หน้าเพลงใช้ ลบตอนลบ `BAR_COUNTS`
- `groove.preview` กับ test ของมันทดสอบกฎมือที่ `drum_cover.timeline` ใช้ (`trimmed`, `with_hands`): ถ้าลบ `preview` ต้องย้าย test ไปเรียก `trimmed`/`with_hands` ตรง
- `SongsPage.test.tsx` fixture ยังมีสองท่อนกับ "ลองเล่นเอง"

**Checks:** `uv run pytest` 1558 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 659 passed (test ที่ไม่แตะของ spoil/spoil-maker ล้ม 1 ใน 3 รอบ ดู Blocked 1); `npm --prefix frontend run build` ผ่าน

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | test frontend ที่ไม่เกี่ยวกับงานนี้ล้มสุ่ม ~1 ใน 3 รอบของทั้งชุด (ครั้งละตัว: `SpoilMakerPage` polish, `ClipsPage` drop, …) มีตั้งแต่ก่อนเริ่ม feature บน `bf5383c`; รันซ้ำผ่าน | `/kiki-debug frontend suite flaky one test per run` | open |
