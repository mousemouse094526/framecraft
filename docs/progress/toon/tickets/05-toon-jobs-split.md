# 05: แยกงานของ toon ออกเป็นส่วน

**What to build:** ผู้ใช้ทำทุกอย่างใน tab การ์ตูนเล่าได้เหมือนเดิมทุกอย่าง (Plot, Cards, Ref, Image, Voice และ Render job) แต่โค้ดงานของ tab อ่านและแก้ได้ทีละ kind. slot ของ toon ใช้ OmniVoice ผ่านตัวพูดที่ถือไว้ ไม่ใช่สืบทอด `speaking.Speaker`, และแต่ละ kind ของ Toon job อยู่ module ของตัวเอง เลือกด้วยตารางต่อ kind แทนกิ่ง `kind == "characters"` ที่กระจายอยู่.

**Blocked by:** 04: คลังเสียงพื้นและ render

**Covers:**
- Decisions: D45
- ADR: 0010, 0012, 0015
- Blocked: #13, #14 (feature review)

**Status:** done

## Acceptance criteria

### ตัวพูด OmniVoice

- `ToonJobs` และ `RenderJobs` ไม่สืบทอด `speaking.Speaker`; ทั้งสองถือตัวพูดที่ใช้ `_track` และ `_reply` ของ slot ตัวเอง → test ของ Voice job และ Render job ที่ `voicing` ผ่านเหมือนเดิม
- ยกเลิกระหว่างพูด → child ของ OmniVoice ถูกปิด และเสียงที่พูดจบแล้วยังอยู่ (เหมือนเดิม)
- `SentenceVoicer` ของ spoil-maker ใช้ตัวพูดแบบเดียวกัน หรือคงไว้ตามที่ build ตัดสิน; test ของ spoil-maker ผ่านเหมือนเดิม

### งานต่อ kind

- งานของแต่ละ kind (Plot, Cards, Ref, Image, Voice) อยู่ module ของตัวเองใต้ package `toon`; child ของ klein, `delete_series`, `image_rows` ไม่อยู่ใน module ของ slot
- ค่าที่ต่างกันระหว่างตัวละครกับฉากหลัง (ชื่อไฟล์ ชื่อ field ข้อความ) มาจากตารางต่อ kind ที่เดียว → ไม่เหลือกิ่ง `kind == "characters"` ใน `toon/`
- `gpu_kind`, `child_name`, `worker_error` ตั้งต่องานและเปลี่ยนตามขั้น (Qwen แล้ว klein) เหมือน spec › Toon job → test ของ Toon job ผ่านเหมือนเดิม
- route, รูป JSON และรหัส error ของ `/api/toon/*` ไม่เปลี่ยน → test ของ `test_toon_*_api` ทุกไฟล์ผ่านโดยไม่ต้องแก้ assert
- `uv run pytest` และ CI ทั้งหมดเขียว
