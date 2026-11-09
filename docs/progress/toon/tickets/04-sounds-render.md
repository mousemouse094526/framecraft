# 04: คลังเสียงพื้นและ render

**What to build:** ผู้ใช้เอาไฟล์เสียงหรือลิงก์เข้าคลังเสียงพื้นกลางของ tab แล้วเปลี่ยน ปิด หรือตั้งความดังต่อช่วง และ Cards job เลือกเสียงจากคลังนี้. กด render แล้วได้ mp4 1080×1920 ตามแบบจอของ Series พร้อมซับ ป้ายชื่อตัวละคร และเสียงพื้น โดย render สร้างเสียงเล่าที่ขาดให้ก่อน. เล่น ดาวน์โหลด และลบคลิปที่ render ได้.

**Blocked by:** 03: ภาพการ์ดและเสียงเล่า

**Covers:**
- Decisions: D4, D5, D7, D14, D16, D17, D19, D22, D23, D32 (render ด้วยภาพเดิมของ `stale_ref`), D37, D38, D39, D45, spoil-maker D20, spoil-maker D21
- ADR: 0005, 0010, 0013, 0015, 0021, 0024, 0026, 0028, 0029
- Screens: คลังเสียงพื้น, render และผล, เส้นเรื่อง (การ์ด) ส่วนเสียงพื้นและความดังต่อช่วง
- Seams: 1 (Sound import, `in_use` ของเสียง, `sound: null`, Render job ระหว่าง Image job), 2, 3 (คำเตือนก่อนเอาเสียงเข้า)
- User stories: 10, 11
- Legal: 4

**Status:** ready-for-agent

## Acceptance criteria

### คลังเสียงพื้น

- `YtDlpAdapter.download` รับ options ตาม spec › Modules touched; ค่าตั้งต้นให้ผลเดิมของ Temp clip → test ของ spoil ผ่านเหมือนเดิม
- Sound import ไฟล์ wav → เสียงใน `sounds.json` เป็น m4a aac ชื่อตั้งต้นจากชื่อไฟล์
- ไฟล์ที่ ffmpeg อ่านเสียงไม่ได้ → `400` `unsupported_file`; ยาวเกิน 20 นาที → `400` `too_long`; เกิน 200 MB → ปฏิเสธที่ `check`
- ลิงก์ด้วย adapter ปลอม → โหลดลง `media/toon/.partial/` แบบ `bestaudio` ไม่มี thumbnail; ลิงก์ที่กติกาของ spoil ไม่รับ → `400` `invalid_url`
- Sound import ซ้อนกัน → `409` `busy`; Sound import ระหว่าง Toon job → `202`
- ลบเสียงที่ช่วงใช้ → `409` `in_use` พร้อม `eps`; `PATCH` ช่วง `sound: null` → ไม่มีเสียงพื้น
- Cards job กับคลังที่มีเสียง → `FakeLlm` เลือก `sound` ที่มีอยู่ ช่วงได้ `sound_id` และความดัง 30

### Render job

- Render job มี slot ของตัวเอง: Render job ซ้อนกัน → `409` `busy`; Render job ของ EP ที่เสียงครบระหว่าง Image job → `202`
- EP ถูกล็อกโดย Cards job → `409` `ep_locked`; การ์ดไม่มีภาพ → `400` `cards_not_ready` พร้อม `card_ids`
- การ์ด `no_audio` → state `voicing` ก่อน `rendering` และการ์ดมี `audio` หลังจบ; ช่อง GPU ถูกคืนหลัง `voicing`
- EP 3 การ์ด (หนึ่งการ์ดเงียบ `hold_s` 2) แบบ `frame` ด้วย ffmpeg จริง → `ffmpeg -i` อ่านได้ 1080×1920, 30 fps, h264, aac ยาวเท่าผลรวมความยาวการ์ด ±0.1 วินาที
- เฟรมกลางของแต่ละการ์ด → ตรงกลางภาพเป็นสีของภาพการ์ดนั้นตามลำดับ
- แบบ `full` → ไฟล์ ASS ใน `.render/` มีป้ายชื่อเฉพาะในการ์ดแรกของตัวละคร และไม่มีชื่อตอน
- แบบ `frame` → ASS มีชื่อตอน ป้าย `EP{n:02}` และ `channel_name`; `channel_name` ว่าง → ไม่วาด
- ช่วงติดกันที่ใช้เสียงพื้นเดียวกัน → เป็นท่อนเดียวใน filter graph; เปลี่ยนเสียง → `acrossfade` 1 วินาที
- render เสร็จ → `renders/` มี `.mp4`, `.srt`, `.json`; ยกเลิก → ไม่มี `.partial` และ `.render/`; start ใหม่ล้างทั้งสอง
- `DELETE …/renders/{name}` → สามไฟล์ของคลิปนั้นหาย
- `gpu.Kind` มี `toon_render` ใน `RUNNING_NAMES` ("render การ์ตูนเล่า"); `JOB_HOLDERS` มี Render job และ Sound import

### หน้าเว็บ

- `#/toon/sounds` เปิดหน้าคลังเสียงพื้น
- `GPU_JOB_PATHS` ใน `lib/gpu` มี `/api/toon/render/current`
- กดเอาเสียงเข้า (ไฟล์หรือลิงก์) → เห็นคำเตือนของ legal ข้อ 4 ก่อนช่องเลือกไฟล์ (e2e)
- กด render → เห็น `voicing` แล้ว `rendering` พร้อม % แล้วคลิปขึ้นในรายการ (e2e)
- `useLeaveGuard` ระหว่าง upload เสียง
- หน้าตาตรงแบบของจอคลังเสียงพื้นและ render และผล (Source ยัง `pending`: Blocked #8–9)

### เช็คมือบน Mac

- render EP แรกของ Series หลอนแบบกรอบดำ → ดูด้วยตาว่าตำแหน่งชื่อตอน ภาพ ซับ ชื่อช่อง ตรง layout-sketch; จดผลใน `progress.md`
