# Progress: reels-only

**Now:** 01 done; 02 next

**Next:**

```
/warroom-build reels-only 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | หน้า reel กลอง แทนสอนกลอง | done |
| 02 | หน้าเพลงไม่มีบทเรียน และลบโค้ดสร้างบทเรียนจากเพลง | ready |

## Log

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
