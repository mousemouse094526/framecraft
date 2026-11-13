# 01: คลังเสียงกลางที่ tab คลังเสียง

**What to build:** ผู้ใช้เปิด tab "คลังเสียง" (`#/sounds`) จากแถบนำทาง แล้วเอาไฟล์หรือลิงก์เข้า ฟัง เปลี่ยนชื่อ ลบเสียง ได้แบบเดิมของการ์ตูนเล่า พร้อมปุ่ม info. เสียงที่เคยเอาเข้าคลังเสียงพื้นย้ายมาที่ `media/sounds/` เองตอน start และช่วงของ EP ยังเล่นเสียงเดิม. ลบเสียงที่ EP ใช้อยู่ไม่ได้ และบอกว่า EP ไหนใช้.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D4, D6, D7, D9, D10, D11, toon D39, toon D56, toon D70, toon D71
- ADR: 0003, 0009, 0028, 0029, 0033, 0037, 0038, 0039
- Screens: หน้าคลังเสียง
- Seams: 1 (ทุกข้อยกเว้นข้อที่ใช้ Spoil draft และ Render job ของสปอย), 3 (ลำดับ tab, `#/toon/sounds`, ปุ่ม info, `in_use`, Alert legacy)
- User stories: 1, 3, 5, 6
- Legal: 1 (คำเตือนสิทธิ์ของเสียงบนหน้าคลังเสียง)

**Status:** ready-for-agent

## Acceptance criteria

### ของที่ย้ายก่อน

- หน้าคลังเสียงและ toon ใช้ `CommitField`, `NoticeLine`, `lib/edit`, `lib/notice`, `lib/upload`, `useReadyState` และ icon จากที่ของแอป → test ของ toon ผ่านโดยไม่เปลี่ยนสิ่งที่เช็ค (D11)
- `features/sound-library` ไม่ import `features/toon` และ `backend.sounds` ไม่ import feature ใด (D7, D11)

### คลังเสียงผ่าน HTTP

- test เดิมของคลังเสียงพื้นย้ายมาที่ `/api/sounds` → ผ่านทุกข้อโดยไม่เปลี่ยนสิ่งที่เช็ค ยกเว้น `in_use` ที่เป็น `users`
- upload, โหลดลิงก์ และไฟล์แปลงของ Sound import → อยู่ใต้ `media/sounds/.partial/`; start ใหม่ล้าง folder นั้นทั้งหมด (D11)
- `/api/toon/sounds` ทุกเส้น → `404`
- EP ที่ช่วงชี้ `m_…` เดิม → `PATCH` ช่วงด้วย id นั้นผ่าน; ลบเสียงนั้น → `409` `in_use` `users[0].tab` `toon` label `{ชื่อ Series} · EP {n} {ชื่อตอน}`
- Cards job เลือกเสียงที่ถูกลบระหว่างงาน → ขั้นเขียนผลเช็ค `sounds.exists` ใต้ `toon.store.lock` และไม่เขียน `sound_id` ที่ไม่มี (D11)
- `in_use` หลายรายการของ toon → เรียงตาม Series แล้วเลข EP

### ย้ายจากที่เดิม

- มี `media/toon/sounds/` สองเสียงแล้ว start → `GET /api/sounds` ได้สองเสียง id เดิม; `media/toon/sounds/` ไม่มีแล้ว; log `moved sound library to media/sounds`
- มี `media/sounds/` หนึ่งเสียง และ `media/toon/sounds/` สองเสียง (หนึ่ง id ซ้ำ) แล้ว start → ได้สองเสียง; `media/toon/sounds/` ไม่มีแล้ว
- มี `media/sounds/` ที่มีแค่ `.partial/` → ย้ายทั้ง folder ได้
- ย้ายไฟล์ที่สองล้มด้วย `OSError` → start ได้; `GET /api/sounds/legacy` `left_behind` ไม่ใช่ `null`; import หนึ่งเสียงแล้ว start ใหม่ → เสียงครบ `left_behind` `null` (D10)
- EP ที่ render หลังย้าย → เล่นเสียงพื้นเดิมจาก `media/sounds/`

### หน้าเว็บ

- แถบนำทางเรียง ติดตั้ง · คลิป · คลังความรู้ · คลังเสียง · สปอย · การ์ตูนเล่า; กด "คลังเสียง" → `#/sounds` เห็นรายการเสียง (e2e)
- เปิด `#/toon/sounds` ทั้งตอนโหลดหน้าและตอนเปลี่ยน hash → hash เป็น `#/sounds` (e2e)
- กดปุ่ม info → เห็นสามข้อตาม spec › Frontend; กดซ้ำ `Esc` หรือคลิกนอก → ปิด (e2e)
- ลบเสียงได้ `409` `in_use` สอง `users` → เห็นสองบรรทัด "การ์ตูนเล่า · …" และ "สปอย · …" (e2e)
- `GET /api/sounds/legacy` ไม่ใช่ `null` → Alert warning ตาม spec › Design (e2e)
- `#/sounds?back=#/toon/…` → ลิงก์ "← กลับ" ไปที่นั้น; `back` ค่าอื่น → ไม่มีลิงก์; ไม่มีลิงก์ "← การ์ตูนเล่า" (e2e)
- ปุ่ม "คลังเสียง" ในรายการ Series และ toolbar เส้นเรื่อง → เปิด `#/sounds?back={hash ที่อยู่}`; ข้อความยืนยันลบ Series พูดว่า "คลังเสียง"
- คำเตือนสิทธิ์ของเสียง → แสดงตลอดเหนือช่องไฟล์และลิงก์ ข้อความเดิม (e2e)
- คลังว่าง → "ยังไม่มีเสียงในคลัง"
- หน้าตาตรงแบบของจอหน้าคลังเสียง (Blocked #2)

### Ops

- README ภาษาไทย → ชื่อ "คลังเสียง", path `media/sounds/`, และขั้นย้อนไปแอปรุ่นก่อน (spec › Ops)
