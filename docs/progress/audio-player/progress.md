# Progress: audio-player

**Now:** 01 done; 02 next

**Next:**

```
/warroom-build audio-player 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | play/pause ทุกจุด เล่นได้ทีละเสียง | done |
| 02 | เวลาบนปุ่ม และ media อื่นเล่นทีละตัว | ready |

## Log

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
