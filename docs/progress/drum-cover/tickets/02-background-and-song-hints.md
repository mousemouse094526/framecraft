# 02: ภาพพื้นหลังของ reel และหน้าเพลงบอกเมื่อกลองเข้าช้า

**What to build:** ผู้ทำคลิปเลือกภาพ PNG/JPG ของตัวเองเป็นพื้นหลังของ reel (ครอป 9:16 เบลอ ทำมืดตอน render) หรือกลับเป็นสีของแอป; และหลังแกะ หน้าเพลงบอกเมื่อช่วงไม่มีการตีหรือห้องแรก ๆ ว่าง พร้อมปุ่ม "เริ่มช่วงที่การตีแรก" ที่ตั้งช่วงใหม่แล้วแกะทันที.

**Blocked by:** 01: reel cover จากเพลงที่แกะ: ตั้งช่วง ข้อความ เสียง ฟัง render

**Covers:**
- Decisions: D8, D9, D19 (ปุ่มและ Alert), D21 (`pictures`, `useBackground`, `song_busy` ของภาพ), video-gen D6, D36, D37, spoil D58
- ADR: 0028
- Screens: หน้าเพลง — ส่วนที่เพิ่ม (Alert หลังแกะ), หน้า reel (การ์ดพื้นหลัง)
- Seams: 1 (ข้อ background), 3 (ข้อ Alert หลังแกะ, ข้อเลือกภาพ)
- User stories: 6, 7
- Legal: 3

**Status:** done

## Acceptance criteria

- `PUT /background` PNG → `cover-background.jpg` 1080×1920, `background` = `image`; `DELETE` → `color`; ไฟล์ข้อความ → `415`; เกิน 20 MB → `413` ที่ `check` และ `PUT`; ระหว่าง render reel → `409` `song_busy` "กำลัง render reel ของเพลงนี้อยู่"
- render ด้วยภาพ → เฟรมไม่ใช่สีพื้นของแอป; ภาพถูกลบหลังบันทึก `image` → render ใช้สีของแอป
- test เดิมของ video-gen backgrounds และหน้าแก้บทเรียนผ่านโดยไม่แก้ assertion หลังย้ายไป `backend.pictures` และ `components/ui`
- หน้า reel เลือกภาพ → `background/check` แล้ว `PUT` body ดิบ แล้วเห็นภาพ; ลบภาพ → สีของแอป; `415` → error ข้างปุ่ม (e2e)
- หน้าเพลงหลัง `done` ที่ `hits` ว่าง → Alert "ไม่พบการตีกลองในช่วง 0.0–30.0 วินาที …" (e2e)
- ห้อง 1–5 ว่างและการตีแรกที่ 11.5 → Alert "ห้อง 1–5 ไม่มีการตี การตีแรกอยู่ที่ 11.5 วินาที"; กด "เริ่มช่วงที่การตีแรก" → `PUT /range` `{start_s: 11.5, end_s: 41.5}` แล้ว `POST /pick` (e2e)
- การตีก่อน downbeat แรก → ไม่มี Alert ห้องว่าง; ช่วงใหม่ใกล้ท้ายเพลงยาวอย่างน้อย 4 วินาที (e2e)
