# 04: เสียงคาลิมบาจาก sample จริง VCSL แทนเสียงสังเคราะห์

**What to build:** reel คาลิมบาและปุ่ม "ฟัง" เล่นเสียงคาลิมบาจริงจาก VCSL "Kalimba, Tanzania" (CC0) ที่ Setup โหลด แทนเสียงสังเคราะห์: ทุกคีย์ตรง C major, เสียงซ่าแบบ mbira กับคีย์อื่นที่ดังตามถูกกรองออก; Status check มีแถว "Kalimba samples"; timeline และภาพเหมือนเดิม. change request จากคำตอบของเจ้าของใน Blocked 2–3.

**Blocked by:** 03: render reel คาลิมบา — โน้ตตกลงบนคีย์ที่สว่างตรงเสียง

**Covers:**
- Decisions: D18 (แทน D5), D6, D12, video-gen D11
- ADR: 0002, 0041, 0042, 0061 (แทน 0059), 0060
- Seams: 1 (ฟังและ render ไม่มี sample → `503`, เสียงตรงภาพ), 2 (`sound`, `kalimba_kit`)
- Legal: 3

**Status:** done

## Acceptance criteria

### Setup และ Status check

- Setup โหลด 14 ไฟล์ของ VCSL ที่ commit `c1ea7bc` ต่อจาก sample กลอง (`#` ใน URL เป็น `%23`) ตรวจ sha256 แล้วเขียน marker; ไฟล์ที่ไม่ตรงสามครั้ง → setup จบ `1` บอกชื่อไฟล์ ไม่มี marker
- Status check แถว `kalimba_kit` "Kalimba samples" ต่อจาก `drum_kit` บอก "VCSL Kalimba, Tanzania · c1ea7bc"; ไฟล์หาย → `missing` fix `./setup.sh` แถวเดียว

### เสียง

- `sound.note(project, 60, "normal")` ความถี่หลัก 261.6 ± 1.5 Hz; คีย์ 62, 81, 88 ตรงเสียงของตัวเอง; sample ที่ใช้คือตัวที่ pitch ที่วัดได้ใกล้สุด
- sine อ็อกเทฟต่ำกว่าและ 12 kHz ใน sample → เหลือ < 1% ของความถี่หลัก; เสียงเริ่มใน 2 ms; ยาว ≤ 4 วิ; accent ดังกว่า ghost
- `mix` สองครั้ง → bytes เดียวกัน peak −1 dBFS; คีย์เดียวกันเล่นซ้ำตัดเสียงก่อน; ไม่มีโน้ต → เงียบ

### API

- `POST /listen` และ `POST /render` คาลิมบาไม่มี sample คาลิมบา → `503` `not_ready` `rows` `["kalimba_kit"]`; ไม่มี sample กลองยังได้
- เสียงตรงภาพของ C4 ≤ 1 เฟรม ผ่านเหมือนเดิม

### เจ้าของ (D12)

- import MIDI ทำนองแล้ว render ได้ทำนองถูก (Blocked 5; เจ้าของ 2026-11-17 ให้ทดสอบเอง) — ด้วยโค้ดจริงและ sample จริง: Twinkle Twinkle 14 โน้ต ทุกโน้ตตรง pitch

เจ้าของฟังเสียง sample ใหม่ตอน review PR (ไม่กันการ merge ตามที่เจ้าของสั่งเปิด PR); ปรับเสียงซ่าที่ `sound.BUZZ_FROM/TO`
