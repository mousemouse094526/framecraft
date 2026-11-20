# Progress: audio-player

**Now:** 01 และ 02 done; feature review ผ่าน; PR เข้า develop

**Next:**

```
/pr-open
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | play/pause ทุกจุด เล่นได้ทีละเสียง | done |
| 02 | เวลาบนปุ่ม และ media อื่นเล่นทีละตัว | done |

## Log

### feature review (หลัง 02) — done 2026-11-20

**Built:**
- wav ที่ผสมเสร็จหลังแก้ฟอร์มไม่เล่น; เสียงอื่นที่เริ่มระหว่างผสมไม่ถูกตัด; กดซ้ำระหว่างผสมไม่ส่งซ้ำ
- `ended`/`error` ของไฟล์เก่าไม่ล้างเสียงใหม่
- ระหว่างผสม โฟกัสคีย์บอร์ดอยู่ที่ปุ่มเดิม (`aria-disabled`)

**Decided:**
- D15 — ข้อแก้ห้าข้อจาก feature review

**For the next ticket:**
- Nothing

**Checks:** `npm --prefix frontend run typecheck` ok · `npm --prefix frontend test` 701 passed · `npm --prefix frontend run build` ok

### 02: เวลาบนปุ่ม และ media อื่นเล่นทีละตัว — done 2026-11-20

**Built:**
- ปุ่มเล่นแสดง `0:03 / 0:12` ขณะเล่นและหยุดชั่วคราว; ยังไม่รู้ความยาวแสดง `0:03`
- วิดีโอหรือเสียงเพลงที่ไม่ `muted` เริ่มเล่น = เสียงของปุ่มและ media อื่นหยุดชั่วคราว; ปุ่มเริ่ม = media อื่นหยุด
- ปุ่มไอคอนของคลังเสียงและเสียงพื้นกว้างตามเวลา (สูง 44px ต่ำกว่า 640px คงเดิม)

**Decided:**
- ไม่มี D ใหม่; `clockOf` ใน `lib/format` (ปัดลงทั้งวินาที) ตาม D13

**For the next ticket:**
- Nothing

**Checks:** `npm --prefix frontend run typecheck` ok · `npm --prefix frontend test` 700 passed · `npm --prefix frontend run build` ok · `uv run pytest` 1547 passed (ticket 01, backend ไม่เปลี่ยน)

### 01: play/pause ทุกจุด เล่นได้ทีละเสียง — done 2026-11-20

**Built:**
- แปดจุดฟังเสียงเป็น `PlayButton` ไอคอน play/pause: กดเสียงใหม่ = เสียงเดิมหยุด; กดปุ่มเดิม = หยุดชั่วคราว/เล่นต่อ
- ฟังจังหวะและฟัง reel ผสมครั้งเดียว แล้ว pause/เล่นต่อ; แก้ฟอร์มระหว่างฟัง = เสียงหยุด กดต่อผสมใหม่
- `lib/audio.ts` (`playAudio`) ถูกลบ; `lib/player` เป็นที่เดียวที่สร้าง `Audio`

**Decided:**
- D14 — ปุ่มผสมเสียงไม่มีกุญแจ: wav ใช้ได้จนฟอร์มมี `unsaved` (กุญแจของ D13 แข่งกับการบันทึก)

**For the next ticket:**
- `PlayButton` รับ `status` อย่างเดียว; เวลาต้องส่ง `position`/`duration` จาก `useSound` และ `useListen` (มีให้แล้ว)
- `SoundButton` = `PlayButton` + `useSound` สำหรับไฟล์จาก API
- capture listener `play` ยังไม่มี: เพิ่มใน `lib/player`

**Checks:** `uv run pytest` 1547 passed · `npm --prefix frontend run typecheck` ok · `npm --prefix frontend test` 696 passed · `npm --prefix frontend run build` ok

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
