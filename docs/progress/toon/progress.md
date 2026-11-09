# Progress: toon

**Now:** 01 หยุดกลางทาง: klein บน torch 2.8.0 กรณีหนักสุดใช้ memory เกินเกณฑ์ ~12 GB (Blocked #10); ต้องเลือกทางแก้ใน `/warroom toon`

**Next:**

```
/warroom toon
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้ง klein, Series และภาพอ้างอิง | in-progress |
| 02 | EP, พล็อต และเส้นเรื่อง | ready |
| 03 | ภาพการ์ดและเสียงเล่า | ready |
| 04 | คลังเสียงพื้นและ render | ready |

## Log

### 01: ติดตั้ง klein, Series และภาพอ้างอิง — stopped 2026-11-09

**Done:** (โค้ดอยู่บน `wip/toon-01`, test backend 897 ผ่าน)
- ติดตั้งและ Status check: `KLEIN` และ `KLEIN_GGUF` ใน `MODELS` (GGUF pin `a09d5bb51ac4000ccd9643d10e9db3ed14200508`), setup ตรวจทุก folder ใน `allow_patterns` หลังโหลด, ที่ว่างที่ต้องการ 33/43/28 GB, แถว `model_klein` `model_klein_gguf` `diffusers` `gguf` ต่อจาก `font_kanit`, `NOTICE.md`
- Series ตัวละคร ฉากหลัง: สร้าง แก้ ลบ (`confirm_needed`, `series_busy`), `voice_in_use` ของ Series, ข้าม `series.json` ที่อ่านไม่ได้; test ใน `backend/tests/test_toon_series_api.py`
- เริ่มแล้วแต่ยังไม่มี test: Ref job (`backend/toon/jobs.py`), worker ของ klein (`backend/toon/klein.py`), pick และ upload ภาพอ้างอิง

**Left:** กลุ่ม Ref job และเอาไฟล์เข้า (test ทั้งกลุ่ม), กลุ่มหน้าเว็บ (รอแบบ: Blocked #1–4)

**ลองจริง (Open Question 1):** Mac M1 16 GB, torch 2.8.0, diffusers 0.42.1, gguf 0.19.0, GGUF Q8_0, 4 steps

| ขั้น | เวลา | peak MPS | peak ทั้งระบบ | swap |
|---|---|---|---|---|
| โหลด text encoder | 9.7 วิ | — | — | — |
| encode 4 prompt | 9.3 วิ/prompt | 9.77 GB | 15.58 GB | — |
| โหลด transformer GGUF + vae | 11.2 วิ | — | — | — |
| ภาพ 576×1024, 3 ภาพอ้างอิง (รอบ 1) | 178 วิ | **13.09 GB** | 16.41 GB | 5.37 → 9.27 GB |
| ภาพ 576×1024, 3 ภาพอ้างอิง (รอบ 2) | 231 วิ | **13.98 GB** | 16.34 GB | → 10.96 GB |

- peak MPS ของ klein อย่างเดียวเกิน ~12 GB ของ D34 ทั้งสองรอบ และเครื่อง swap จริง; ตัวเลขทั้งระบบรวมแอปอื่นที่เปิดอยู่ (swap 5.4 GB ก่อนเริ่ม และ pytest รันช่วงรอบ 2) แต่ MPS เป็นของ klein เอง
- เทียบผลลองเดิม (torch 2.15, 1024×576, 1 ภาพอ้างอิง): 11.2 GB; กรณี 3 ภาพอ้างอิงกับภาพแนวตั้งไม่เคยวัดมาก่อน
- ภาพไทยตรงเข้า klein (ข้อมูลให้ D36): รอบนี้ยังไม่ได้ผล ไปลองต่อพร้อมทางแก้ใน `/warroom toon`
- สคริปต์ลองอยู่นอก repo; ขั้นตอนเหมือน `backend/toon/klein.py` (encode แยก, `device_map`, `no_grad`, `config=` ของ transformer ในเครื่อง)

**Decided:**
- D47 — gguf pin 0.19.0 แทน 0.10.0 ที่อ่าน GGUF ไม่ได้บน numpy 2
- D48 — ค่าเล็กของ Series และ Ref job (ความยาว style/tone, `file_too_large`, `item_id`, ค่าสำรองของคำแปล, `backend/uploads.py`)

**For the next ticket:**
- `backend/uploads.py` คือการรับ body ดิบที่ spoil import และ upload ภาพอ้างอิงใช้ร่วมกัน; Sound import ของ ticket 04 ใช้ตัวนี้
- `gate_rows.klein(project)` เป็นฟังก์ชัน (ต้องใช้ project) ไม่ใช่ค่าคงที่ `gate_rows.KLEIN` ตามที่ spec เขียน

**Checks:** `uv run pytest` 897 passed บน `wip/toon-01`; frontend ไม่ได้แตะ

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: รายการ Series (หน้าแรกของ tab) | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 2 | 01 | design: ตั้งค่า Series | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 3 | 01 | design: ตัวละครและฉากหลัง | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 4 | 01 | design: เลือกภาพอ้างอิง | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 5 | 02 | design: รายการ EP ใน Series | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 6 | 02 | design: พล็อต | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 7 | 02 | design: เส้นเรื่อง (การ์ด) | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 8 | 04 | design: คลังเสียงพื้น | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 9 | 04 | design: render และผล | `/warroom toon` พร้อมลิงก์แบบจาก [ui-prompt.md](../../features/toon/ui-prompt.md) | open |
| 10 | 01 | klein บน torch 2.8.0 กรณีหนักสุด (GGUF Q8_0, 3 ภาพอ้างอิง, 576×1024) peak MPS 13.1–14.0 GB เกิน ~12 GB ของ D34 และ swap; ต้องเลือก: ภาพอ้างอิงเล็กลง, GGUF ที่เล็กกว่า (Q6_K/Q4_K_M), ภาพอ้างอิงสูงสุดน้อยลง, torch รุ่นใหม่ หรือยอมรับ | `/warroom toon` | open |
