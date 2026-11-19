# Progress: nav-ia

**Now:** 01 done; 02 next

**Next:**

```
/warroom-build nav-ia 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เมนูและที่อยู่ใหม่ พร้อม redirect | done |
| 02 | สปอยเป็นพื้นที่ทำงานเดียว | ready |
| 03 | เพลงกับ reel cover และ reel กลองกับผล render เป็นหน้าเดียว | ready |
| 04 | EP การ์ตูนเล่าเป็นหน้าเดียว | ready |

## Log

### 01: เมนูและที่อยู่ใหม่ พร้อม redirect — done 2026-11-19

**Built:**
- เมนู: สปอยมีคลิปทั้งหมด (`#/spoil/clips`), หมวดดนตรีมี reel cover (`#/covers`), คลังเหลือ คลังความรู้ · คลังเสียง · เสียงพากย์ (`#/voices`)
- hash เก่า `#/clips`, `#/spoil/voices`, `#/songs…` พาไปหน้าใหม่ (`MOVED` แบบ pattern, `movedTo`); ล่าสุดกุญแจ `songs` อ่านเป็น `covers`
- ป้ายบนจอที่ชี้ "tab สปอย" หรือ "แกะเพลง" เปลี่ยนตาม (ฟอร์มชุด, รายการ reel กลอง, หัวรายการเพลง)

**Decided:**
- ไม่มี D ใหม่; หน้า reel ยังอยู่ที่ `#/covers/{id}/cover` ชั่วคราวจนกว่า 03 รวมหน้า

**For the next ticket:**
- ขั้นของสปอยยังเป็นรายการเมนูที่มี `step` จนกว่า 02 จะเอาออก; `REVIEW_HASH`/`RENDERS_HASH` ยังใช้อยู่
- `CLIPS_HASH` อยู่ใน `lib/clips`; `backOf` ของคลังเสียงรับ `#/spoil` แล้ว

**Checks:** typecheck · `npm test` 661 passed · build · `uv run pytest` 1547 passed — all green

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
