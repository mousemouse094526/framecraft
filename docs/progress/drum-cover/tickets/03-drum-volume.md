# 03: ความดังกลองแยกจากเพลง และปิดเสียงกลองได้

**What to build:** ผู้ทำคลิปเลื่อน "ความดังกลอง" (10–100) หรือกด "ปิดเสียงกลอง" ในการ์ดเสียงของหน้า reel แยกจาก "ความดังเพลง" แล้ว "ฟัง" หรือ "render reel" ได้ยินตามที่ตั้ง; ผล render บันทึกค่ากลองไว้และแถวผลบอกด้วยป้าย.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D24, D27 (ข้อเสียง)
- ADR: 0050
- Screens: หน้า reel (การ์ดเสียง, ป้ายแถวผล render)
- Seams: 1 (ข้อ `drums`, `/listen` volume, render `drums`), 3 (ข้อความดังกลอง)
- User stories: 8
- Legal: 2

**Status:** done

## Acceptance criteria

### API และเสียง

- `cover.json` เก่าที่ไม่มี `drums` → `GET /cover` ตอบ `drums` `{on: true, volume: 100}`; ไม่มี `cover.json` → ค่าตั้งต้นเดียวกัน
- `PUT /cover` `drums.volume` 5, 101 หรือไม่ใช่จำนวนเต็ม → `400` field `drums.volume`; `drums.on` `false` กับ backing ปิด → `400` field `drums.on` "เปิดเสียงกลองหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง"
- `/listen` กลองล้วน volume 100 → bytes เดียวกับ `mixer.mix` ของ timeline เดียวกัน (D15)
- `/listen` กลองล้วน volume 50 → peak ต่ำกว่า volume 100 6.0 dB ± 0.1 และยาว `length_s` ± 0.05
- `/listen` กลองปิด + backing → เท่ากับเพลงของช่วง × `backing.volume/100` ± 1 LSB (ไม่ดันขึ้น); กลอง + backing ดังเต็ม → peak −1 dBFS ไม่มี sample ค้างที่ ±32767
- render กลองปิด + backing → mp4 h264 + aac ยาว `length_s` ± 0.1, `.json` มี `drums.on` `false`; `GET …/renders` ของ `.json` เก่าที่ไม่มี `drums` → `{on: true, volume: 100}`
- render cover เดิมสองครั้ง (กลองล้วน volume 100) → `audio.wav` เหมือนกันทุก byte; test เสียงตรงภาพเดิมยังผ่าน

### หน้า reel

- เลื่อน "ความดังกลอง" เป็น 60 แล้ว "บันทึก" → `PUT` ส่ง `drums: {on: true, volume: 60}` (e2e)
- กด "ปิดเสียงกลอง" ตอนกลองล้วน → สไลเดอร์ซ่อน ข้อความ "เปิดเสียงกลองหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง" ปุ่ม "ฟัง"/"render reel" กดไม่ได้; เปิด backing แล้ว → กดได้ (e2e)
- แถวผล render `drums.on` `false` → ป้าย "ไม่มีเสียงกลอง"; `volume` 60 → "กลอง 60%"; 100 → ไม่มีป้ายกลอง (e2e)
