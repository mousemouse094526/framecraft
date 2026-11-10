# Spec: toon

tab "การ์ตูนเล่า" ให้ผู้ใช้ตั้ง Series กับ EP แล้วได้คลิปแนวตั้ง 1080×1920 ที่เล่าเรื่องด้วยภาพการ์ตูนที่ AI วาด เสียงเล่า ซับ และเสียงพื้น (D1, D2).

**Status:** ready-to-build

## Problem

ผู้ใช้อยากทำคลิปเล่าเรื่องแบบช่อง "รุ่นพี่เล่าว่า…" (การ์ตูน 2D แบน โทนมืด ซับทีละวลี เสียงเล่าเรียบช้า) และแบบคลิปตลกเต็มจอ. ตอนนี้ต้องวาดภาพทีละภาพ อัดเสียง ทำซับ และตัดต่อเองนอกแอป; ตัวละครหน้าไม่เหมือนเดิมข้าม EP. แอปมีแค่ tab สปอยที่ทำคลิปจาก Temp clip ไม่ใช่จากภาพวาด.

## Solution

- ตั้ง Series ที่เก็บชื่อช่อง แบบจอ สไตล์ภาพ น้ำเสียงเล่า โครงองก์ เสียงเล่าหลัก ตัวละคร และฉากหลัง (D3, D7, D8, D10, D28, D41).
- สร้างภาพอ้างอิงของตัวละครและฉากหลังด้วย AI (3 แบบให้เลือก) หรือเอาไฟล์เข้า (D31, D32).
- พิมพ์ไอเดีย EP ให้ AI ร่างพล็อต แก้พล็อต แล้วให้ AI แตกเป็นองก์ → ช่วง → การ์ด (D9, D12, D13, D24).
- แก้การ์ดทีละใบ และแตกใหม่เฉพาะองก์ที่พล็อตเปลี่ยน (D15, D20, D21).
- สร้างภาพการ์ดทีละการ์ด หรือสร้างภาพที่ขาดทั้งหมดเป็นงานเดียวที่ทิ้งไว้ข้ามคืนได้ (D33).
- สร้างและฟังเสียงเล่าทีละการ์ด (D21).
- เก็บคลังเสียงพื้นกลางของ tab ที่ AI เลือกให้แต่ละช่วง (D5, D16, D17).
- render mp4 ตามแบบจอของ Series (D4, D18, D19, D22, D23, D38).

## User Stories

**ผู้ใช้**
1. As a ผู้ใช้, I want สร้าง Series พร้อมแบบหลอนหรือตลกที่ตั้งโครงองก์ สไตล์ภาพ และน้ำเสียงเล่าให้, so that EP ทุกตอนในช่องเดียวกันได้หน้าตาและจังหวะเดียวกัน (D3, D10, D11, D28, D41)
2. As a ผู้ใช้, I want เพิ่มตัวละครและฉากหลังแล้วสร้างภาพอ้างอิง 3 แบบให้เลือก หรือเอาไฟล์ของฉันเข้า, so that ตัวละครหน้าเหมือนเดิมทุกการ์ด (D29, D31)
3. As a ผู้ใช้, I want เปลี่ยนภาพอ้างอิงได้แม้มีการ์ดใช้อยู่ และเห็นว่าการ์ดไหนยังใช้หน้าเก่า, so that แก้หน้าตัวละครได้โดยภาพที่สร้างแล้วไม่หาย (D32)
4. As a ผู้ใช้, I want พิมพ์ไอเดียสั้นๆ แล้วได้พล็อตต่อองก์ ชื่อตอน และรายชื่อตัวละครกับฉากหลังที่ต้องใช้, so that แก้ทิศเรื่องก่อนเสียเวลากับการ์ด (D12, D13, D24)
5. As a ผู้ใช้, I want ยืนยันพล็อตแล้วได้ช่วงและการ์ดพร้อมข้อความเล่า คำบรรยายภาพ การขยับ และเสียงพื้นที่ AI เลือก, so that มีเส้นเรื่องครบให้แก้ (D5, D9, D21)
6. As a ผู้ใช้, I want แก้ เพิ่ม ลบ การ์ด ช่วง และองก์ใน EP, so that เรื่องเป็นอย่างที่ฉันต้องการ (D10, D21)
7. As a ผู้ใช้, I want แก้พล็อตแล้วให้ AI แตกใหม่เฉพาะองก์ที่เปลี่ยน และถามก่อนทับการ์ดที่ฉันแก้เอง, so that งานที่แก้ไว้ไม่หาย (D15)
8. As a ผู้ใช้, I want กด "สร้างภาพที่ขาดทั้งหมด" แล้วทิ้งไว้ หยุดได้ และสลับกลับภาพก่อนหน้าได้, so that ทั้ง EP ได้ภาพโดยไม่ต้องเฝ้า (D27, D33)
9. As a ผู้ใช้, I want สร้างและฟังเสียงเล่าทีละการ์ด และเห็นความยาวรวมเทียบเป้า 60–120 วินาที, so that จังหวะเรื่องพอดี (D14, D21)
10. As a ผู้ใช้, I want เอาไฟล์เสียงหรือลิงก์เข้าคลังเสียงพื้น แล้วเปลี่ยน ปิด หรือตั้งความดังต่อช่วง, so that แต่ละช่วงมีบรรยากาศ (D5, D16, D17, D39)
11. As a ผู้ใช้, I want กด render แล้วได้ mp4 ตามแบบจอของ Series พร้อมซับและป้ายชื่อตัวละคร, so that เอาไปลงช่องได้ทันที (D7, D19, D22, D23, D38)
12. As a ผู้ใช้, I want ลบ EP หรือ Series หลังยืนยัน โดยของที่ยังใช้อยู่ลบไม่ได้, so that ไม่มีการ์ดพังและไม่ลบพลาด (D25, D26)

## Design

ออกแบบใน Figma หลัง plan (setup-status D9); ทุกจอมีแบบแล้ว (ลิงก์คือ section ของจอนั้น).

| Screen | User stories | Must show | Source |
|---|---|---|---|
| รายการ Series (หน้าแรกของ tab) | 1, 12 | รายการ Series: ชื่อ ชื่อช่อง แบบจอ จำนวน EP; ปุ่มสร้าง Series; ว่าง: คำชวนสร้าง Series แรก; ลบ Series ยืนยันพร้อมจำนวน EP (D26) | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8121-65674) |
| ตั้งค่า Series | 1 | ชื่อ (1–60), ชื่อช่อง (0–60), แบบจอ กรอบดำ/เต็มจอ แก้ไม่ได้หลังสร้าง (D7), แบบหลอน/ตลก ตอนสร้างเท่านั้น (D10, D11), สไตล์ภาพ อังกฤษ (D28), น้ำเสียงเล่า (D41), โครงองก์ เพิ่ม ลบ เปลี่ยนชื่อ พร้อมคำบอกว่ามีผลกับ EP ใหม่เท่านั้น (D11), เสียงเล่าหลักจาก Saved voice (D8), สวิตช์ป้ายชื่อตัวละคร (D19); ไม่มี Saved voice: ลิงก์ไปหน้า Saved voice ของ tab สปอย | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8122-66685) |
| ตัวละครและฉากหลัง | 2, 3, 12 | สองรายการ: ภาพอ้างอิงหรือป้าย "ยังไม่มีภาพ" (D13), ชื่อ, คำสั้น (ตัวละคร, D23), คำอธิบาย; ปุ่มสร้าง 3 แบบและเอาไฟล์เข้า; ป้าย "3 แบบรอเลือก" ที่เปิดหน้าเลือกภาพอีกครั้ง; คำเตือนก่อนเลือกไฟล์ (legal ข้อ 2); ลบไม่ได้เมื่อมีการ์ดใช้: บอก EP ที่ใช้ (D25) | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8123-68692) |
| เลือกภาพอ้างอิง | 2 | ความคืบหน้าของงาน 3 แบบ (ราว 4.5 นาทีบน M1, D31), ภาพ 3 แบบให้เลือกหนึ่ง, ยกเลิก, คำบอกว่าภาพที่ยังไม่เลือกหายเมื่อปิดแอป; error: `gpu_busy` บอกงานที่รันอยู่ | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8124-70163) |
| รายการ EP ใน Series | 4, 12 | EP: เลข, ชื่อตอน, ขั้น (พล็อต / การ์ด), จำนวนการ์ดที่มีภาพ, render ล่าสุด; ปุ่ม EP ใหม่ (ช่องไอเดีย 1–500 ตัวอักษร); ลบ EP ยืนยัน (D26) | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8126-71235) |
| พล็อต | 4, 7 | ชื่อตอน (D24), สรุปต่อองก์ แก้ได้, ตัวละครและฉากหลัง: ป้าย "ใหม่" หรือ "ใน Series" พร้อมตัวเลือกสลับเป็นของเดิม (D13); ปุ่มยืนยันพล็อต / แตกใหม่ (D15) พร้อมรายชื่อองก์ที่จะแตกใหม่ และคำยืนยันที่บอกต่อองก์ว่าจะเสียการ์ดแก้เอง ภาพ และเสียงกี่รายการ (D43); กำลังร่าง: สถานะงาน | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8127-72204) |
| เส้นเรื่อง (การ์ด) | 5, 6, 8, 9, 10 | องก์ → ช่วง (ฉากหลัง, เสียงพื้น + ความดัง) → การ์ดตาม card-sketch (D21): ข้อความเล่า, ตัวละคร 0–2 (D30), คำบรรยายภาพ (D20), การขยับ, ไฟกะพริบ, ค้างเพิ่ม, ปุ่มเสียง สร้าง/ฟัง, ภาพการ์ดพร้อมสร้างใหม่และสลับภาพก่อนหน้า (D33); ป้าย "แก้เอง" (D15), "ภาพอ้างอิงเปลี่ยน" (D32), "ยังไม่มีภาพอ้างอิง" (D13); ความยาวรวมเทียบ 60–120 วินาที (D14); ปุ่ม "สร้างภาพที่ขาดทั้งหมด" พร้อมจำนวนที่ข้ามและความคืบหน้า หยุดได้ (D33); ปุ่ม "สร้างภาพใหม่การ์ดที่ภาพอ้างอิงเปลี่ยน" (D44); รายการตัวละครและฉากหลังที่ต้องสร้างภาพอ้างอิงก่อน พร้อมลิงก์ไปสร้าง (D13); ระหว่างงานที่ล็อก EP: ช่องแก้ปิด | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8128-76737) |
| คลังเสียงพื้น | 10 | รายการเสียง: ชื่อแก้ได้, ความยาว, ปุ่มฟัง, ลบ (ใช้อยู่ลบไม่ได้); คำเตือนเรื่องสิทธิ์ของเสียง (legal ข้อ 4); เอาไฟล์เข้าพร้อม % upload; วางลิงก์พร้อม % โหลด; error ของไฟล์และลิงก์ | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8129-80163) |
| render และผล | 11 | ปุ่ม render, สถานะ `voicing` / `rendering` พร้อม %, การ์ดที่ยังไม่มีภาพ (`cards_not_ready`), รายการคลิปที่ render แล้ว: เล่น ดาวน์โหลด ลบ | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8130-81152) |

## Expected Outcome

ผู้ใช้ทำคลิปการ์ตูนเล่าหนึ่ง EP ได้ในแอปตั้งแต่ไอเดียจนได้ mp4 โดยตัวละครหน้าเหมือนเดิมทุกการ์ดและทุก EP.

- **EP แรกของ Series หลอน:** พิมพ์ไอเดีย → แก้พล็อต → ได้ราว 20–30 การ์ด → สร้างภาพอ้างอิงของตัวละครและฉากหลังใหม่ (ราว 4.5 นาทีต่อตัว แล้วเลือกหนึ่งใน 3) → สร้างภาพที่ขาดทั้งหมดข้ามคืน → render → ได้ mp4 1080×1920 แบบกรอบดำ ชื่อตอนกับป้าย EP บนสุด ซับใต้ภาพ ชื่อช่องล่างสุด.
- **EP ใน Series ตลกแบบเต็มจอ:** ภาพ 9:16 เต็มจอ ซับขาวขอบดำที่ราว 60% ป้าย "พีค / สายแฟ" มุมบนซ้ายตลอดการ์ดแรกที่พีคออก.
- **EP ที่สอง:** ตัวละครและฉากหลังจาก EP แรกอยู่ใน Series แล้ว AI ใช้ของเดิม ภาพการ์ดหน้าเหมือนเดิม.

**How success is judged:**
- คลิปที่ render ยาวเท่าผลรวมความยาวการ์ด (±0.1 วินาที) และ `ffmpeg -i` อ่านได้ h264 1080×1920 30 fps กับ aac (ไม่มี ffprobe, ADR-0005).
- ทุกการ์ดในคลิปเป็นภาพการ์ดปัจจุบันของการ์ดนั้นตามลำดับ.
- ปิด backend ระหว่าง "สร้างภาพที่ขาดทั้งหมด" แล้วเปิดใหม่: ภาพที่เสร็จก่อนปิดยังอยู่ กดใหม่สร้างเฉพาะที่เหลือ.
- งานภาพบน M1 16 GB: peak `torch.mps.driver_allocated_memory()` ของ process ลูก klein ไม่เกิน 12 GB ที่กรณีหนักสุด (576×1024, 3 ภาพอ้างอิง, 5 ภาพติดกันใน process เดียว, seed และคำสั่งตายตัว, ปิดแอปอื่น) และภาพที่ 3–5 ไม่สูงกว่าภาพที่ 2 (D49).
- ลองด้วยมือ: ตัวละครหนึ่งตัวใน ~5 การ์ดของ EP แรกและ EP ที่สอง ดูด้วยตาว่าหน้าเหมือนภาพอ้างอิง จดผลใน `progress.md` (แบบ trial-klein-mac).

## Implementation

### Modules touched

- **`backend.models`**
  - `backend.checks.check_model` ได้ `missing` เมื่อ pattern ใดใน `allow_patterns` ไม่ตรงไฟล์ใดใน marker (D49: เปลี่ยนไฟล์ใน revision เดิมต้องโหลดใหม่)
  - เพิ่ม `KLEIN` และ `KLEIN_GGUF` ใน `MODELS` (D34, ADR-0004):
    - `KLEIN`: `check_id` `model_klein`, `label` `FLUX.2 klein 4B model`, `repo_id` `black-forest-labs/FLUX.2-klein-4B`, `revision` `e7b7dc27f91deacad38e78976d1f2b499d76a294`, `allow_patterns` `model_index.json`, `text_encoder/*`, `tokenizer/*`, `vae/*`, `scheduler/*`, `transformer/config.json` (ไม่โหลด `transformer/*.safetensors`), `license` `Apache-2.0`, `license_url` `https://www.apache.org/licenses/LICENSE-2.0`, `author` `Black Forest Labs`
    - `KLEIN_GGUF`: `check_id` `model_klein_gguf`, `label` `FLUX.2 klein 4B GGUF`, `repo_id` `unsloth/FLUX.2-klein-4B-GGUF`, `revision` pin ตอน build ticket 01 (D34 › Details), `allow_patterns` `flux-2-klein-4b-Q4_K_M.gguf` (D51: Q8_0 และ Q6_K เกิน 12 GB; ใช้ทั้งสอง OS), `license` `Apache-2.0`, `license_url` `https://www.apache.org/licenses/LICENSE-2.0`, `author` `Unsloth`
    - ทั้งคู่ `platforms` ทั้งสอง OS (D35); spec เดียวต่อแถวบนทุก OS จึงไม่ต้องใช้ตัวเลือกต่อ OS แบบ `qwen_for` (ADR-0025)
    - `from_single_file` ได้ `config=` เป็น path ของ snapshot ในเครื่องเสมอ ไม่ให้ diffusers ไปหา Hub ตอนรัน (ADR-0008, trial › ข้อ 3)
- **`backend.setup`**
  - โหลดทั้งสอง spec ตาม ADR-0004 ต่อท้ายลำดับเดิม (หลัง Qwen ก่อน Kanit ตามลำดับ `MODELS`); หลังโหลดตรวจว่าทุก folder ใน `allow_patterns` มีไฟล์จริง ไม่เชื่อ exit code (trial › ข้อ 5.3)
  - `REQUIRED_FREE_BYTES` เพิ่ม 12 GB: Mac 32 GB, Windows 42 GB; `REQUIRED_FREE_BYTES_WITHOUT_QWEN` 27 GB (D51)
  - klein โหลดไม่สำเร็จเป็นเหมือนโมเดลอื่น: Setup script ล้มและรันซ้ำแล้วโหลดต่อ (ADR-0002)
- **`backend.checks`, `backend.gate_rows`**
  - แถวใหม่: Status check ด้านล่าง; `gate_rows.klein(project)` รวมสี่แถวของ klein (ฟังก์ชัน: แถว model ต้องรู้ project); แถว `diffusers` และ `gguf` เขียนที่เดียวใน `checks.klein_packages` ที่ Status check อ่านด้วย (D59); แถว `yt_dlp`, `deno` ของลิงก์เป็น `gate_rows.LINK_TOOLS` ที่ Sound import ของลิงก์และ download ของสปอยใช้ร่วม (D66)
- **`backend.renders`** (ใหม่, D59)
  - ส่วนกลางของผล render ที่ `spoil_maker.render` และ `toon.render` ใช้ร่วม: ชื่อว่าง ผลที่ครบ (`results`, `listed`) `latest_at` การจบ render (`finish`: srt และ json แล้วเอา `.partial` ออก json ท้าย) การลบ (mp4 ก่อน json ท้าย, `409` `in_use`) `.partial` ที่ค้าง; แถว gate ของ render เป็น `gate_rows.render(project, voices_first)` ที่เพิ่มแถวของ Voice job (`gate_rows.voice`) เมื่อต้องพูดก่อน (D60); `toon.episodes` อ่าน `latest_at` จากตัวนี้ จึงไม่ import `toon.render`; render หนึ่งชิ้นเป็น `Render(folder, name)` (`next_free` ให้ตัวนี้; `finish`, `require`, `delete` เป็น method) และ `percent` ของการตัดชิ้นและการต่อชิ้นเป็น `pieces_percent`, `encode_progress` (D62)
- **`backend.jobs`, `backend.workers`**
  - `ModelJobSlot.start_child` (track แล้วรอข้อความแรก), `ask`, `stop_child`, `free_gpu` เป็นทางเดียวที่ Qwen, klein และตัวพูดเริ่มและหยุด; `Worker.end` ขอให้ child ออกเอง (D62)
- **`backend.gpu`**
  - `Kind` เพิ่ม `toon_write` ("ร่างการ์ตูนเล่า"), `toon_image` ("สร้างภาพ"), `toon_voice` ("สร้างเสียงเล่า"), `toon_render` ("render การ์ตูนเล่า") ใน `RUNNING_NAMES`
- **`backend.app`**
  - `JOB_HOLDERS` เพิ่ม Toon job กับ Sound import; include router `/api/toon`
- **`backend.paths`**
  - path ของ `media/toon/` (ข้อมูล ด้านล่าง)
  - `EpAddress`: EP หนึ่งตอน (project, Series, EP) เป็นค่าเดียวที่ฟังก์ชันของ EP ตอนเดียวและ route `/eps/{ep_id}` รับ พร้อม folder ของ EP (D67)
- **`backend.spoil_maker.voices`**
  - ลบ Saved voice: นับ Series และ EP ของการ์ตูนเล่าที่ใช้ `voice_id` เป็น `voice_in_use` ด้วย (D25) ผ่าน callback ใน `voice_users` ที่ `backend.toon` ลงทะเบียน
  - ทุกการเขียน `voice_id` ของ Series หรือ EP ถือ `gpu.slot.draft_lock` ก่อน `toon.store.lock` ให้การลบ Saved voice กับการเปลี่ยนเสียงไม่ชนกัน
  - ย้ายลูปสร้างเสียงทีละข้อความของ `SentenceVoicer` เป็นตัวพูดกลาง `speaking.Speaker` ที่รับ (ข้อความ, clone prompt, speed) แล้วคืน wav ทีละอัน; job slot ถือตัวพูดไว้ ไม่สืบทอด (D58); spoil-maker, Voice job และ Render job ของ toon ใช้ตัวเดียวกัน
- **`backend.spoil.adapter`**
  - `YtDlpAdapter.download` รับ options (รูปแบบ, folder ปลายทาง, แม่แบบชื่อไฟล์, เขียน thumbnail ไหม); ค่าตั้งต้นคือของ Temp clip เดิม; คลังเสียงพื้นใช้ `bestaudio`, `media/toon/.partial/`, ไม่มี thumbnail, ไม่ merge mp4; extractor และกติกาลิงก์เดิม (ADR-0029)
- **`backend.toon`** (ใหม่)
  - `store`: อ่านเขียน `series.json`, `ep.json`, `sounds.json` ผ่าน `.tmp` แล้ว rename ใต้ lock ของ toon; `reconcile_sounds` ให้ `sounds.json` ตรงกับไฟล์ m4a (D70, D71)
  - `series`: Series ตัวละคร ฉากหลัง ภาพอ้างอิง การลบ, ของใหม่ในพล็อตเป็นตัวละครและฉากหลังของ Series (`new_items`), `ref_rev` ของทุกตัว (`ref_revs`, D62); `ItemRef` ตัวละครหรือฉากหลังหนึ่งตัวเป็นค่าเดียวที่ฟังก์ชันของตัวเดียวและ route รับ (D64); `series_jobs`: job slot ทุกตัวของ tab ที่ Series ของงานที่ยังไม่จบลบไม่ได้ (D61)
  - `kinds`: ตารางค่าที่ต่างกันระหว่างตัวละครกับฉากหลัง (D58) รวมจำนวนสูงสุดในพล็อต `plot_max` (D71); ชนิด `ItemKind` ไม่ชน `JobKind` ของ Toon job (D61)
  - `episodes`: EP พล็อต (`plot_items` อ่านตัวละครและฉากหลังของพล็อตทั้งจากผู้ใช้และจาก Qwen, D62) การ์ด การแก้ สถานะการ์ด; `ep_jobs`: แต่ละ slot บอก EP ที่ทำงานอยู่เป็น `EpUse` (`how`: ทำงานอยู่, ล็อก, render: Plot job อ่าน `rendering`, D61)
  - `writer`: คำสั่งและการอ่านคำตอบของ Plot job และ Cards job (ใช้ worker ของ `spoil_maker.llm`)
  - `prompts`: คำสั่งภาพ, คำสั่งแปลคำบรรยาย และการอ่านคำตอบ
  - `klein`: worker ของ klein ใน process ลูก `spawn` (ADR-0012)
  - `plot`, `cards`: Plot job และ Cards job (ขั้นของงาน คำสั่งจาก `writer`)
  - `refs`: Ref job
  - `images`: แผน ขั้น ไฟล์ และการเขียนภาพของ Image job
  - `voicing`: Voice job: แผน ขั้น และการเขียนเสียงเล่าของการ์ด (ผ่าน `speaking.Speaker`)
  - `sounds`: คลังเสียงพื้น, Sound import slot (ไฟล์ที่หน้าเว็บหายระหว่างแปลงไม่เข้าคลัง)
  - `render`: Render slot (D45), Render job; `compose`: timeline, ASS, filter graph
  - `jobs`: Toon job slot (ทุกงานยกเว้น render และ Sound import) ที่เริ่มและจบทุก kind แบบเดียวกันจาก `WORK` ของ module ของ kind นั้น; `steps`: ส่วนที่ kind ใช้ร่วม (child ของ Qwen และ klein, `open_klein` ที่เดียวที่เปิด klein, `draw`, D58, D61, D62)
- **`backend.routes`**
  - router ใหม่ `toon` prefix `/toon`
- **`NOTICE.md`**
  - เพิ่ม klein, GGUF, Qwen3-4B text encoder (Apache-2.0)
- **`frontend` › `lib/useHash`**
  - tab ที่ห้า `toon` `#/toon` ต่อจากสปอย; hash `#/toon/…` เปิด tab นี้
- **`frontend` › `lib/gpu`**
  - `GPU_JOB_PATHS` เพิ่ม `/api/toon/jobs/current` และ `/api/toon/render/current`
- **`frontend` › `features/toon`** (ใหม่)
  - หน้าตาม Design; ใช้ `lib/api`, `lib/job`, `lib/usePollWhile`, `lib/refusal` เดิม; หน้าที่ตาม Toon job poll ผ่าน `hooks/useToonJobPoll`; hook แก้ state ตอนพร้อมผ่าน `hooks/useReadyState` และทุกคำขอที่เปลี่ยนของ (แก้ไข, ลบ, เริ่มงาน) อ่านคำตอบผ่าน `lib/edit.sendEdit` ที่คืน `Notice` (D65, D72); ตัวละครหรือฉากหลังหนึ่งตัวเป็น `lib/series.ItemRef`, ค่าที่ต่างกันต่อชนิดอยู่ใน `lib/kinds.ITEM_KINDS`, ไฟล์ที่เช็คแล้วส่งผ่าน `lib/upload.sendChecked` (D68); ปุ่ม "ฟัง" ใช้ `lib/audio` (ย้ายจาก spoil-maker, D59)

### Dependencies

ติดตั้งผ่าน Setup script เท่านั้น (ADR-0002).

| Package | Version | Marker | ใช้ทำอะไร |
|---|---|---|---|
| `diffusers` | `==0.42.1` | — | `Flux2KleinPipeline`, `from_single_file` GGUF (D34) |
| `gguf` | `==0.19.0` | — | อ่านไฟล์ GGUF (diffusers ไม่ดึงมาให้, trial › ข้อ 3); pin ตรงตัวในช่วง `>=0.10.0` ของ D34 เพื่อให้แถว Status check เทียบได้; 0.10.0 ใช้กับ numpy 2 ไม่ได้ (D47) |
| `Pillow` | ตามที่ diffusers ดึงมา | — | อ่านและย่อภาพอ้างอิงที่เอาเข้า |

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| diffusers | 0.42.1 | `Flux2KleinPipeline(image=[...])` รับภาพอ้างอิงเป็น list, 4 steps `guidance_scale=1.0` | [Flux2 pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/api/pipelines/flux2) |
| diffusers | 0.42.1 | `Flux2Transformer2DModel.from_single_file(path, config=…, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16))` | [GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf) |
| diffusers | 0.42.1 | `encode_prompt` แยกจากการ denoise; pipeline ที่โหลดด้วย `text_encoder=None` รับ `prompt_embeds` (และ `negative_prompt_embeds` ที่ encode จาก `""` ในขั้นเดียวกัน) โดยไม่เรียก text encoder — หน้า docs ไม่ได้เขียนไว้ อิงโค้ดที่ tag กับผลลอง (trial › ข้อ 1) | [pipeline_flux2_klein.py v0.42.1](https://github.com/huggingface/diffusers/blob/v0.42.1/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py) |
| torch | 2.8.0 (pin ของ project) | MPS รัน pipeline ข้างบนได้; trial วัดบน 2.15.0 — Open Question 1 | [MPS backend](https://docs.pytorch.org/docs/2.8/notes/mps.html) |
| omnivoice, Qwen, pythainlp, Kanit, libass | ตาม spoil-maker | เหมือน [spoil-maker spec](../spoil-maker/spec.md) › Library assumptions | ตาม spoil-maker |
| ffmpeg (imageio-ffmpeg 0.7.0) | 7.1 | `scale=…:flags=lanczos`, `zoompan`, `eq=brightness` แบบ expression ตามเวลา, `xfade`, `acrossfade`, `amix`, `ass` | [ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) |
| yt-dlp | ตาม pin | format `bestaudio` โหลดเสียงอย่างเดียว | [yt-dlp format selection](https://github.com/yt-dlp/yt-dlp#format-selection) |

### Status check

เพิ่ม 4 แถวต่อจาก `font_kanit` (ADR-0009). ไม่โหลดโมเดล ไม่ใช้ network. แถวโมเดลสร้างจาก `ModelSpec` ละแถวแบบเดิม จึงแสดง license ของ repo นั้น; license ของ Qwen3-4B text encoder อยู่ใน `NOTICE.md`.

| id | ผ่านเมื่อ | Windows |
|---|---|---|
| `model_klein` | Model marker ของ `KLEIN` ตรง revision (ADR-0004) | เหมือน Mac (D35) |
| `model_klein_gguf` | Model marker ของ `KLEIN_GGUF` ตรง revision | เหมือน Mac (D35) |
| `diffusers` | หา package ได้และ version ตรง pin (`check_pinned`) | เหมือน Mac |
| `gguf` | หา package ได้และ version ตรง pin | เหมือน Mac |

ไม่ผ่าน → `503` `not_ready` พร้อม `rows`:

| งาน | แถวที่ต้องผ่าน |
|---|---|
| Plot job, Cards job | `gate_rows.qwen_jobs` |
| Ref job, Image job | `gate_rows.qwen_jobs` + `model_klein`, `model_klein_gguf`, `diffusers`, `gguf` |
| Voice job | `device`, `model_omnivoice`, `pythainlp` |
| Render job | `ffmpeg`, `font_kanit`, `pythainlp`; มีการ์ดต้องสร้างเสียงเพิ่มแถวของ Voice job (D38) |
| Sound import | `ffmpeg`; ลิงก์เพิ่ม `yt_dlp`, `deno` |

### ข้อมูล

ทุกอย่างอยู่ใน `media/toon/` (ADR-0003). ไฟล์ json เขียนผ่าน `{name}.{uuid}.tmp` แล้ว rename; ทุกการอ่าน-แก้-เขียนอยู่ใต้ `toon.store.lock` (RLock เดียวของ tab). id เป็น prefix + hex 8 ตัว: `s_` Series, `c_` ตัวละคร, `b_` ฉากหลัง, `e_` EP, `a_` องก์, `g_` ช่วง, `k_` การ์ด, `m_` เสียงพื้น.

```text
media/toon/
  series/{series_id}/
    series.json
    refs/{c_or_b_id}-{rev}.png        ภาพอ้างอิงปัจจุบัน (rev เพิ่มทุกครั้งที่เปลี่ยน)
    refs/.pending/{c_or_b_id}-{1..3}.png  ภาพ 3 แบบที่ยังไม่เลือก
    eps/{ep_id}/
      ep.json
      images/{card_id}-{seed}.png     ภาพการ์ดปัจจุบันและภาพก่อนหน้า
      audio/{card_id}.wav
      renders/{YYYYMMDD-HHMMSS}.mp4|.srt|.json
  sounds/sounds.json
  sounds/{sound_id}.m4a
  .render/                            folder ทำงานของ Render job
  .partial/                           ไฟล์ upload ที่ยังรับไม่ครบ
```

`series.json` — รูปของไฟล์คือส่วนหนึ่งของการตัดสินใจ:

```json
{
  "version": 1,
  "id": "s_1a2b3c4d",
  "name": "รุ่นพี่เล่าว่า…",
  "channel_name": "รุ่นพี่เล่าว่า",
  "layout": "frame",
  "genre": "horror",
  "style": "flat 2D cartoon, round heads, dot eyes, dark scene lit only by light sources",
  "tone": "เล่าเป็น \"ฉัน\" น้ำเสียงเรียบ ช้า ชวนขนลุก",
  "acts": ["เปิด", "ปม", "หักมุม", "จบหลอน"],
  "voice_id": "v_8f2c01ab",
  "name_tags": true,
  "max_ep": 8,
  "characters": [
    { "id": "c_01", "name": "พีค", "tag": "สายแฟ", "description": "ผู้ชายผมสั้น เสื้อฮาวาย", "ref_rev": 2 }
  ],
  "backgrounds": [
    { "id": "b_01", "name": "กองไฟในป่า", "description": "ลานโล่งกลางป่ามืด มีกองไฟ", "ref_rev": 0 }
  ]
}
```

- `layout` `frame` (กรอบดำ) หรือ `full` (เต็มจอ), แก้ไม่ได้หลังสร้าง (D7)
- `genre` `horror` หรือ `comedy` ตั้งค่าตั้งต้นของ `acts`, `style`, `tone` ตอนสร้างเท่านั้น (D10, D11, D28, D41)
- `ref_rev` `0` = ยังไม่มีภาพอ้างอิง (D13)
- `max_ep` คือเลข EP สูงสุดที่เคยมี (D40)

`ep.json`:

```json
{
  "version": 1,
  "id": "e_5e6f7a8b",
  "n": 9,
  "idea": "รุ่นพี่ไปแคมป์แล้วได้ยินเสียงเรียกชื่อ",
  "title": "เสียงเรียกจากป่า",
  "voice_id": "v_8f2c01ab",
  "stage": "cards",
  "plot": {
    "characters": [{ "id": "c_01", "new": false }],
    "backgrounds": [{ "id": "b_01", "new": false }]
  },
  "acts": [
    {
      "id": "a_01",
      "name": "เปิด",
      "summary": "รุ่นพี่กับเพื่อนตั้งแคมป์",
      "cards_from": "รุ่นพี่กับเพื่อนตั้งแคมป์",
      "segments": [
        {
          "id": "g_01",
          "background_id": "b_01",
          "sound": { "sound_id": "m_01", "volume": 30 },
          "cards": [
            {
              "id": "k_01",
              "text": "คืนนั้นเราตั้งแคมป์กันสามคน",
              "character_ids": ["c_01"],
              "description": "พีคนั่งหน้ากองไฟ มุมกว้าง แสงส้มจากล่าง",
              "motion": "zoom_in",
              "flicker": true,
              "hold_s": 0,
              "edited": false,
              "audio": { "tts_text": "คืนนั้นเราตั้งแคมป์กันสามคน", "voice_id": "v_8f2c01ab", "duration_s": 3.1 },
              "image": { "file": "k_01-918273.png", "refs": { "c_01": 2, "b_01": 1 }, "prompt": "…" },
              "previous_image": null
            }
          ]
        }
      ]
    }
  ]
}
```

- `stage` `plot` (ยังไม่ยืนยันพล็อต ไม่มีช่วง) หรือ `cards`
- `cards_from` คือ `summary` ตอนที่องก์นี้ถูกแตกครั้งล่าสุด; `summary` ≠ `cards_from` = องก์ที่พล็อตเปลี่ยน (D15); องก์ที่เพิ่มหลังยืนยันมี `cards_from` `null`
- `motion` `still`, `zoom_in`, `zoom_out`, `pan_left`, `pan_right` (D4)
- `hold_s` 0–5 ทีละ 0.5; การ์ดเงียบ (`text` ว่าง) ต้อง `hold_s` ≥ 0.5 ไม่งั้น `400` `invalid_card` (D14, D21)
- `image.refs` คือ `ref_rev` ของตัวละครและฉากหลังตอนสร้างภาพ; `image.prompt` คือคำสั่งภาพ เก็บไว้ดู bug ไม่ส่งให้หน้าเว็บ (D36)
- `edited` ตามกติกาของ spoil-maker D74: `true` เมื่อ `PATCH` เปลี่ยน `text` หรือ `description`, หรือการ์ดที่ผู้ใช้แทรกเอง; Cards job ตั้ง `false`
- `version` อื่น หรือไฟล์อ่านไม่ได้ → log เหตุผลแล้วข้าม EP นั้นในรายการ

`sounds.json`: `{"version": 1, "sounds": [{"id": "m_01", "name": "ฝนตกในป่า", "duration_s": 62.4, "source": "file"}]}`; `source` `file` หรือ `link`.

- ตรวจคลังตอน start (`sounds.clean_on_start` เรียก `store.reconcile_sounds`, ภายใต้ `store.lock`, D70, D71):
  - ทั้งไฟล์อ่านไม่ได้ (JSON เสีย, ไม่มี list `sounds`, `version` ≠ 1) → rename เป็น `sounds.json.bad-{YYYYMMDD-HHMMSS}-{4 hex}` (UTC, ไม่ลบเอง) เริ่มจากไม่มีรายการ
  - เก็บรายการที่ผ่าน schema, `id` fullmatch `SOUND_ID`, ไม่ซ้ำ และมี `{id}.m4a`; ที่เหลือทิ้งพร้อม log
  - `{id}.m4a` ที่ไม่มีรายการ → เพิ่มเรียงตาม id: `name` = id, `duration_s` จาก `ffmpeg.probe` timeout 10 วินาที (ล้ม → `0`), `source` `file`; เขียนเมื่อมีอะไรเปลี่ยน
- ระหว่างทำงาน `read_sounds` ถือ `store.lock` เอง; ไฟล์อ่านไม่ได้ → ตรวจแบบเดียวกันไม่ probe (`duration_s` `0`); เขียนล้ม → log คืนรายการในหน่วยความจำ (D70)

### สถานะการ์ด

คำนวณตอนอ่าน ไม่เก็บ. การ์ดหนึ่งใบมีสถานะภาพและสถานะเสียงแยกกัน.

| สถานะภาพ | เมื่อ |
|---|---|
| `no_ref` | ตัวละครในการ์ดหรือฉากหลังของช่วงมี `ref_rev` 0 (D13) |
| `no_image` | `image` เป็น `null` |
| `stale_ref` | ชุด key ของ `image.refs` ≠ `character_ids` ของการ์ด + `background_id` ของช่วง, หรือค่าใดไม่ตรง `ref_rev` ตอนนี้, หรืออ้าง id ที่ไม่มีแล้ว (D32) |
| `ready` | อื่นๆ |

| สถานะเสียง | เมื่อ |
|---|---|
| `silent` | `text` ว่าง |
| `no_audio` | `audio` เป็น `null` |
| `stale_audio` | `audio.tts_text` ≠ `thai.spoken(text)` หรือ `audio.voice_id` ≠ `voice_id` ของ EP |
| `ready` | อื่นๆ |

- ความยาวการ์ด (D14, D21): เสียง `ready` = `duration_s + 0.3 + hold_s`; `silent` = `hold_s`; อื่นๆ = `thai.letters(thai.spoken(text)) / chars_per_s + 0.3 + hold_s`
- `GET` EP ส่งสถานะทั้งสอง ความยาวต่อการ์ด และความยาวรวม

### Series ตัวละคร ฉากหลัง

- สร้าง Series: `name` 1–60 ตัวอักษร, `channel_name` 0–60, `layout`, `genre`, `voice_id` ที่มีอยู่ (ไม่มี → `400` `voice_not_found`); ค่าตั้งต้นตามตาราง; `style`, `tone`, `acts` ที่ส่งมา (กติกาเดียวกับ `PATCH`) แทนค่าตั้งต้น (D52)
- `PATCH` Series แก้ได้ทุกช่องยกเว้น `layout`, `genre`, `max_ep`; `acts` 1–8 ชื่อ ชื่อละ 1–20 ตัวอักษร มีผลกับ EP ใหม่เท่านั้น (D11)
- ตัวละคร: `name` 1–30, `tag` 0–20 (D23), `description` 0–300; ฉากหลัง: `name` 1–30, `description` 0–300
- ลบตัวละครหรือฉากหลังที่การ์ด หรือ `plot` ของ EP ใด อ้างอยู่ → `409` `in_use` พร้อม `eps` (เลขและชื่อตอน, D25)
- ลบ Series → ต้องมี `confirm_eps` เท่ากับจำนวน EP ไม่งั้น `409` `confirm_needed` พร้อม `eps`; ลบ folder Series ทั้งหมด (D26); ระหว่าง Toon job หรือ Render job ของ Series นั้น → `409` `series_busy`
- ลบ EP ระหว่าง Toon job หรือ Render job ของ EP นั้น → `409` `ep_busy`
- `GET /series/{sid}` ส่ง `pending` (จำนวนภาพที่รอเลือก 0 หรือ 3) ต่อตัวละครและฉากหลัง

| ค่าตั้งต้น | `horror` | `comedy` |
|---|---|---|
| `acts` | เปิด / ปม / หักมุม / จบหลอน (D10) | ตั้งเรื่อง / ปั่น / พลิก / ตบมุก (D11) |
| `style` | `flat 2D cartoon illustration, simple round heads, dot eyes, thick clean outlines, dark night scene, only light sources are bright and saturated, deep shadows` (D28) | `flat 2D cartoon illustration, simple round heads, dot eyes, thick clean outlines, bright cheerful colors, soft daylight` (D28) |
| `tone` | เล่าเป็น "ฉัน" น้ำเสียงเรียบ ช้า ชวนขนลุก ประโยคสั้น (D41) | เล่ากวนๆ จังหวะเร็ว มีมุกตบท้าย ประโยคสั้น (D41) |

### Toon job

ทุกงานของ tab ยกเว้น render ใช้ slot เดียว `toon.jobs` (subclass ของ `ModelJobSlot`, ADR-0010): ชนกับ Toon job ที่ยังไม่จบ → `409` `busy`. `gpu_kind`, `child_name`, `worker_error` ตั้งต่องานตอนเริ่ม; `child_name` กับ `worker_error` เปลี่ยนตามขั้นในงานที่มีสองขั้น (Qwen แล้ว klein) แต่ `gpu_kind` คงเดิมทั้งงาน (Image job และ Ref job เป็น `toon_image` ทั้งสองขั้น, D60); `_finish` คืนช่อง GPU ตาม kind ของงานนั้น. Render job มี slot ของตัวเอง (D45) route `/api/toon/render` แยก. state, `percent`, `done`, `total`, `error`, `cancel_requested` ตามรูปของ Voice job เดิม พร้อม `kind`, `series_id`, `ep_id`, `skipped`. route `POST /api/toon/jobs` (202), `GET /api/toon/jobs/current`, `DELETE /api/toon/jobs/current`.

| `kind` | ช่อง GPU | ล็อก EP | ทำอะไร |
|---|---|---|---|
| `plot` | `toon_write` | ใช่ | ร่างพล็อต |
| `cards` | `toon_write` | ใช่ | แตกพล็อตเป็นช่วงและการ์ด |
| `ref` | `toon_image` | ไม่ | ภาพอ้างอิง 3 แบบ |
| `image` | `toon_image` | ไม่ | ภาพการ์ดหนึ่งใบ หรือทุกใบที่ขาด |
| `voice` | `toon_voice` | ไม่ | เสียงเล่าหนึ่งการ์ด |

- แก้ EP ที่ถูกล็อก → `409` `ep_locked`
- ทุกงานคืนช่อง GPU เมื่อจบทุกแบบ (ADR-0015); restart แล้วงานหาย ผลที่เขียนไปแล้วอยู่ (ADR-0010)
- `failed` `error.code`: `crashed`, `model_failed`, `write_failed`, `internal` (ffmpeg อยู่ใน Render job)
- Toon job กับ Render job ใช้ EP เดียวกันพร้อมกันได้ เฉพาะเมื่อไม่มีฝ่ายใดล็อก EP: Plot job หรือ Cards job บน EP ที่ Render job ยังไม่จบ → `409` `ep_busy` (D57)
- ทุกงานรันใน thread ของ backend; โมเดลรันใน process ลูก `spawn`; thread ของ backend เขียนไฟล์ผลคนเดียว (ADR-0012)
- ดิสก์ว่างน้อยกว่า 1 GiB → `507` `disk_full` ก่อนเริ่ม `ref`, `image`, `render`

### Plot job

1. เช็ค: EP มีอยู่ (`404` `not_found`); `idea` 1–500 ตัวอักษร (`400` `invalid_request`); Saved voice ของ EP มีอยู่ (`400` `voice_not_found`); EP `stage` `cards` ต้องผ่าน Cards job แทน (`409` `plot_confirmed`); แถว Status check; `busy`, `gpu_busy`
2. state `writing`: Qwen ร่างพล็อตจาก `idea`, ชื่อองก์ของ EP, `tone` ของ Series, ตัวละครและฉากหลังใน Series (`id`, ชื่อ, คำอธิบาย), ความยาวเป้า 90 วินาที × `chars_per_s`
3. คำตอบ JSON: `{"title": "...", "acts": [{"summary": "..."}], "characters": [{"id": "c_01"} | {"name": "...", "tag": "...", "description": "..."}], "backgrounds": [{"id": "b_01"} | {"name": "...", "description": "..."}]}`
4. ตรวจผล: JSON อ่านได้, `acts` ยาวเท่าองก์ของ EP, ตัวละครไม่เกิน 6, ฉากหลัง 1–6; `id` ที่ไม่มีใน Series ถูกทิ้ง; ไม่ผ่านสั่งใหม่รวม 3 ครั้งแบบ Draft job ของ spoil-maker (ค่าการสร้าง: `temperature` 0.3, thinking ปิด, timeout `llm.timeouts().write`); ครบ 3 ครั้ง → `failed` `write_failed`
5. ทำความสะอาดข้อความแบบ spoil-maker Draft job ข้อ 4; เขียน `title`, `summary` ทุกองก์, `plot` (ของใหม่เก็บใน `plot` ด้วย `name`, `tag`, `description` และ `new: true` ยังไม่เข้า Series)

ผู้ใช้แก้ `title`, `summary`, และสลับของใหม่ใน `plot` ไปเป็น `id` ของเดิมได้ (D13); `plot` ต้องเหลือฉากหลังอย่างน้อยหนึ่งไม่งั้น `400` `invalid_request`.

### Cards job

ยืนยันพล็อตครั้งแรก หรือแตกใหม่หลังแก้พล็อต (D12, D15).

1. เช็คเหมือน Plot job ข้อ 1 (ยกเว้น `plot_confirmed`); มีองก์ให้แตก: ครั้งแรกทุกองก์, ครั้งต่อไปองก์ที่ `summary` ≠ `cards_from` (ไม่มี → `400` `nothing_to_split`); องก์ที่จะแตกมีการ์ด `edited` หรือการ์ดที่มี `image` หรือ `audio` และไม่มี `confirm_loss: true` → `409` `cards_will_be_lost` พร้อม `acts` (`id`, จำนวน `edited`, `images`, `audio` ต่อองก์) (D15, D43)
2. ครั้งแรก: ของ `new: true` ใน `plot` เข้า Series ตอนนี้ ได้ `id` และ `ref_rev` 0 (D13)
3. state `writing` (`done` / `total` องก์): ต่อองก์ Qwen ได้ `summary` ขององก์นั้น สรุปขององก์ก่อนและหลังเป็นบริบท, `tone`, ตัวละครและฉากหลังของ `plot`, ชื่อเสียงในคลังเสียงพื้น, ความยาวเป้าขององก์ = เป้า 90 วินาที หารจำนวนองก์
4. คำตอบ JSON: `{"segments": [{"background": "b_01", "sound": "m_01" | null, "cards": [{"text": "...", "characters": ["c_01"], "description": "...", "motion": "zoom_in", "flicker": false}]}]}`
5. ตรวจผล: `background` ต้องอยู่ใน `plot` ไม่งั้นใช้ฉากหลังแรกของ `plot`; `characters` ที่ไม่อยู่ใน `plot` ถูกทิ้ง เก็บแค่ 2 ตัวแรก (D30); `motion` นอกรายการ → `still`; `sound` ที่ไม่มีในคลัง → `null`; ความดังตั้งต้น 30; การ์ดเงียบได้ `hold_s` 2 (D21); องก์ที่ไม่ได้การ์ดเลยหลังสั่งรวม 3 ครั้ง → `failed` `write_failed` และ EP ไม่เปลี่ยน
6. เขียนทุกองก์ที่แตกในครั้งเดียว: ช่วงและการ์ดเดิมขององก์นั้นถูกแทน ลบไฟล์ภาพและเสียงของการ์ดเดิม (D15); `cards_from` = `summary`; `stage` `cards`

ยกเลิกหรือ crash: EP ไม่เปลี่ยน.

### คำสั่งภาพ

แม่แบบตายตัวของแอป (D36). `{scene}` มาจาก Qwen; `{style}` คือ `style` ของ Series. ในคำสั่งภาพตัวละครชื่อ `character 1` และ `character 2` ตามลำดับใน `character_ids` (ไม่ใช้ชื่อไทย). ภาพอ้างอิงเรียงตัวละครก่อนแล้วฉากหลัง: ฉากหลังเป็นภาพที่ `k` = จำนวนตัวละคร + 1.

| ภาพ | คำสั่งภาพ |
|---|---|
| ภาพการ์ด 0 ตัวละคร | `{scene} In the setting of the background in reference image 1. {style}. No text, no letters, no signs.` |
| ภาพการ์ด 1 ตัวละคร | `{scene} character 1 is the character in reference image 1. In the setting of the background in reference image 2. {style}. No text, no letters, no signs.` |
| ภาพการ์ด 2 ตัวละคร | `{scene} character 1 is the character in reference image 1. character 2 is the character in reference image 2. In the setting of the background in reference image 3. {style}. No text, no letters, no signs.` |
| ตัวละคร (ไม่มีภาพอ้างอิง) | `Full body, front view, standing, plain light gray background. {scene} {style}. No text, no letters.` |
| ฉากหลัง (ไม่มีภาพอ้างอิง) | `{scene} Empty location, no people. {style}. No text, no letters, no signs.` |

- Qwen แปลคำบรรยายภาพ (หรือคำอธิบาย) ทีละรายการ: คำสั่งบอกให้ใช้ `character 1`, `character 2` เป็นประธาน และบอกท่าทาง สีหน้า มุมกล้องและระยะ แสง (trial › ข้อ 4); คำตอบ JSON `{"scene": "..."}`; `temperature` 0, `max_tokens` 200, timeout `llm.timeouts().pick`
- JSON พัง, `scene` ว่าง หรือ timeout ต่อรายการ → `{scene}` = `character 1 in a medium shot.` (0 ตัวละคร: `A medium shot.`) ต่อด้วยคำบรรยายเดิม; timeout ทำให้ process ลูกเริ่มใหม่แบบ Draft job
- คำบรรยายภาพว่าง → ใช้ค่าในข้อก่อนโดยไม่ถาม Qwen
- ภาพอ้างอิงย่อด้านยาว ≤ 512 px ตอนส่งเข้า klein (D49, เดิม 768 ของ D31); ไฟล์ที่เก็บคงขนาดเดิม ย่อเฉพาะตอนส่ง
- `torch.mps.empty_cache()` หลังทุกภาพ (`cuda`: `torch.cuda.empty_cache()`) (D49)
- ขนาด: ภาพการ์ดและฉากหลัง 1024×576 (`frame`) หรือ 576×1024 (`full`) (D31, D37); ตัวละคร 576×1024 เสมอ
- seed สุ่มต่อภาพ เก็บในชื่อไฟล์

### Ref job

1. เช็ค: ตัวละครหรือฉากหลังมีอยู่; แถว Status check; `busy`, `gpu_busy`; `disk_full`
2. state `translating`: Qwen แปลคำอธิบาย (ว่าง → ใช้ชื่อ)
3. state `drawing` (`done` / `total` 3): process ลูกของ klein encode คำสั่ง → ปล่อย text encoder → โหลด transformer → สร้าง 3 ภาพด้วย seed ต่างกัน ลง `refs/.pending/`
4. งาน `done`: ผู้ใช้เลือกด้วย `POST …/ref/pick {"n": 1}` → ย้ายเป็น `refs/{id}-{rev+1}.png`, `ref_rev` +1, ลบภาพอ้างอิงเดิมและ `.pending` ของ id นั้น (D31, D32)

- `.pending` มีชุดเดียวต่อ id; Ref job ใหม่ของ id เดียวกันทับชุดเดิม; start backend ล้าง `.pending` ทั้งหมด
- `ref/pick` ไม่มีชุดรอเลือก → `404` `no_pending`; `n` ไม่ใช่จำนวนเต็ม 1–3 → `400` `invalid_request`

เอาไฟล์เข้า (D31, ADR-0028): `POST …/ref/upload?size=` body ดิบ `application/octet-stream` ไม่เกิน 20 MB; Pillow เปิดได้และเป็น PNG หรือ JPEG ไม่งั้น `400` `unsupported_file`; ฉากหลัง crop กลางให้ได้สัดส่วนของแบบจอแล้วย่อเป็นขนาดในคำสั่งภาพ; ตัวละครย่อด้านยาว ≤ 1536; เก็บเป็น PNG แล้วเหมือนข้อ 4. route นี้เพิ่มในรายการข้อยกเว้นของ ADR-0013 ตาม ADR-0028.

### Image job

`{"kind": "image", "ep_id": "...", "card_id": "..."}` สร้างหนึ่งการ์ด (ทุกสถานะยกเว้น `no_ref`, ซึ่งได้ `400` `no_ref`). ไม่มี `card_id` ต้องมี `scope`: `missing` = สร้างภาพที่ขาดทั้งหมด การ์ด `no_image` ตามลำดับ (D33); `stale_ref` = สร้างใหม่ทุกการ์ด `stale_ref` ตามลำดับ (D44). การ์ด `no_ref` นับใน `skipped` (D33). ไม่มีการ์ดให้สร้าง → `400` `nothing_to_draw`. ทั้ง `nothing_to_draw` และ job มี `missing_refs`: ตัวละครและฉากหลังที่ทำให้การ์ดถูกข้าม (`item_kind`, `id`, ชื่อ, จำนวนการ์ด).

1. ตอนเริ่ม copy ภาพอ้างอิงที่งานใช้ลง `media/toon/.image-job/` เพื่อให้เปลี่ยนหรือลบภาพอ้างอิงระหว่างงานได้; เก็บ `ref_rev` ที่ copy ไว้ลง `image.refs`
2. state `translating` (`done` / `total`): Qwen แปลคำบรรยายภาพของทุกการ์ดในงาน ณ ตอนเริ่ม แล้ว process ลูกของ Qwen จบ (D36)
3. state `drawing` (`done` / `total`): process ลูกของ klein: โหลด text encoder ด้วย `device_map` → encode ทุกคำสั่งใต้ `torch.no_grad()` → ปล่อย text encoder → โหลด transformer GGUF กับ vae → สร้างทีละการ์ด ล้าง cache หลังทุกภาพ (D34, D49)
4. ได้ภาพหนึ่งใบ thread ของ backend เขียนตามลำดับ (D33): เขียน PNG ใหม่ → ใต้ lock เขียน `ep.json` ที่ `image` เดิมเป็น `previous_image` และภาพใหม่เป็น `image` → ลบไฟล์ของ `previous_image` เดิม; การ์ดที่ถูกลบหรือองก์ที่แตกใหม่ระหว่างงาน → ทิ้งภาพนั้น
5. `Draw` ของการ์ดหนึ่งล้มด้วย `WorkerError` → การ์ดนั้นนับใน `failed_cards` แล้วไปการ์ดถัดไป; process ลูก crash หรือ timeout → งาน `failed`
6. ยกเลิก: หยุดหลังภาพที่กำลังสร้าง (ทิ้งภาพนั้น) ภาพที่เสร็จแล้วอยู่ (D33)

- start backend ลบ `.image-job/` และไฟล์ใน `images/` ที่ `ep.json` ไม่อ้าง
- สลับภาพก่อนหน้า: `POST …/cards/{card_id}/swap-image` สลับ `image` กับ `previous_image`
- เปลี่ยนตัวละครของการ์ด หรือฉากหลังของช่วง ไม่ลบภาพ: การ์ดเป็น `stale_ref` ผ่าน `image.refs` เพราะ id ไม่ตรง

klein worker (`toon.klein`): request `Encode(prompts)` → reply `Encoded(count)`; `Draw(index, ref_paths, width, height, seed)` → `Drawn(png: bytes)`; `None` ให้จบ; error → `WorkerError`. timeout ต่อภาพ 15 นาทีบน Mac, Windows ตาม `llm.timeouts` คูณเดียวกัน; เกิน → `model_failed`.

### Voice job

ต่อหนึ่งการ์ดที่ไม่ใช่ `silent` (D21): OmniVoice สร้างจาก `thai.spoken(text)` ด้วย clone prompt และ speed ของ Saved voice ของ EP, `NUM_STEP` 16 แบบ `SentenceVoicer` ของ spoil-maker; เขียน `audio/{card_id}.wav` และ `audio`. ฟังเสียง: `GET …/cards/{card_id}/audio`.

### คลังเสียงพื้น

- **Sound import** (D39): slot ของตัวเองแยกจาก Toon job (ffmpeg อย่างเดียว ไม่ใช้ GPU) มีได้ทีละงาน `409` `busy`
  - ไฟล์: `POST /api/toon/sounds/imports?name=&size=` body ดิบ (ADR-0028) ไม่เกิน 200 MB; หน้าเว็บหายระหว่าง ffmpeg แปลง → ffmpeg หยุด ไม่มีเสียงใหม่ใน `sounds.json` และไม่มีไฟล์ค้างใน `.partial/` (D59)
  - ลิงก์: `POST /api/toon/sounds/downloads {"url": "..."}` ทำตามขั้นของ Download job ของ spoil (อ่าน info → เช็คความยาวจาก info ก่อนโหลด → โหลดพร้อม % → `stalled`) ใน `toon.sounds` ด้วย adapter options ของ Modules touched ลง `media/toon/.partial/`; ใช้ error code ของลิงก์เดิม (`invalid_url`, `login_required`, `download_error`, `disk_full`) กติกาลิงก์ของ spoil (ADR-0029)
  - ffmpeg แปลงเป็น m4a aac 192k 48 kHz stereo ไม่มีภาพ; ffmpeg อ่านเสียงไม่ได้ → `400` `unsupported_file`; ยาวเกิน 20 นาที → `400` `too_long`
  - ชื่อตั้งต้น = ชื่อไฟล์ไม่มีนามสกุล หรือชื่อคลิปของลิงก์ ตัดเหลือ 60 ตัวอักษร (ชื่อคลิปว่าง → id ของเสียง, D69); แก้ชื่อได้ 1–60; ชื่อซ้ำได้
  - จบ import ถือ `store.lock` ตั้งแต่อ่าน `sounds.json` ถึง `os.replace` ของ m4a และเขียน; id เดียวกันแทนรายการเดิม ไม่เพิ่มซ้ำ (D70)
- ลบเสียงที่ช่วงของ EP ใดใช้ → `409` `in_use` พร้อม `eps` (แนวเดียวกับ D25)
- ลบเสียง: ลบ `{id}.m4a` ก่อน แล้วเขียน `sounds.json` (D70)
- AI เลือกเสียงจากชื่อตอน Cards job (D5); ผู้ใช้เปลี่ยน ปิด (`sound: null`) หรือตั้ง `volume` 0–100 ต่อช่วง

### Render job

Render slot ของตัวเอง (D45): `POST /api/toon/render {"ep_id": "..."}` (202), `GET` และ `DELETE` `/api/toon/render/current`; ชน Render job ที่ยังไม่จบ → `409` `busy`.

1. เช็ค: EP `stage` `cards` มีการ์ดอย่างน้อย 1 ใบ (ไม่งั้น `400` `cards_not_ready`); EP ถูกล็อกโดย Plot job หรือ Cards job → `409` `ep_locked`; ทุกการ์ดมี `image` (สถานะ `no_image` หรือ `no_ref` → `400` `cards_not_ready` พร้อม `card_ids`); `disk_full`; แถว Status check; `busy`; มีการ์ดเสียง `no_audio` หรือ `stale_audio` → จองช่อง GPU `toon_render` (`gpu_busy`)
2. state `voicing` (`done` / `total`): สร้างเสียงของการ์ดเหล่านั้นแบบ Voice job (D38) แล้วคืนช่อง GPU
3. state `rendering` (`percent`): อ่าน `ep.json` ครั้งเดียวและ copy ภาพกับเสียงที่ใช้ลง `.render/`; แก้ EP ระหว่างนี้ไม่มีผลกับคลิปนี้ (แบบ ADR-0024); ffmpeg ใน thread ของ backend ตามด้านล่าง ลง `renders/{stamp}.mp4.partial` แล้ว rename; เขียน `.srt` และ `.json` (`title`, `n`, `duration_s`, `created_at`) json ไปหลังสุด

ภาพ (D4, D22, D37):
- ต่อการ์ด: ขยายภาพการ์ดด้วย lanczos เป็น 1080×608 (`frame`) หรือ 1080×1920 (`full`); การขยับด้วย `zoompan` ตลอดการ์ด: `zoom_in` 1.00→1.10, `zoom_out` 1.10→1.00, `pan_left`/`pan_right` เลื่อน 8% ของความกว้างที่ซูม 1.10, `still` นิ่ง
- ไฟกะพริบ (D4): `eq=brightness` ทั้งภาพ ค่า −0.06–0 เปลี่ยนแบบสุ่มเรียบราว 6 ครั้งต่อวินาที seed ตาม `card_id`
- ระหว่างการ์ด `xfade` แบบ `fade` 0.3 วินาทีทับต้นการ์ดถัดไป; ความยาวรวมไม่เปลี่ยน
- `frame`: ภาพวางที่ y 656 บนพื้นดำ 1080×1920; `full`: ภาพเต็มจอ

ข้อความ (ASS, Kanit, libass; D19, D22, D23):
- ซับทีละท่อนตามกติกาของ spoil-maker D20 (`captions` chunk และแบ่งเวลาตามความกว้างตัวอักษร) ภายในช่วงเสียงของการ์ด; ไม่มีสีเน้นคำ
- `frame`: ชื่อตอน (ตัดบรรทัดสูงสุด 2 บรรทัด ยาวกว่านั้นตัดท้ายด้วย "…") และป้าย `EP{n:02}` พื้นแดงบนสุด, ซับใต้ภาพ, `channel_name` ตัวเทาล่างสุด ค้างตลอด; ว่างไม่วาด
- `full`: ซับตัวขาวขอบดำหนาที่ 60% ของความสูง; ไม่มีชื่อตอน ป้าย EP ชื่อช่อง
- ป้ายชื่อเมื่อ `name_tags` เปิด: "ชื่อ / คำสั้น" หรือชื่ออย่างเดียว ตลอดการ์ดแรกที่ตัวละครอยู่ใน `character_ids` ใน EP; มุมล่างซ้ายของภาพ (`frame`) หรือมุมบนซ้าย (`full`); สองตัวในการ์ดเดียวซ้อนสองบรรทัด
- ตำแหน่งและขนาดตัวหนังสือจริงตามแบบหน้าจอ (D22); ก่อนมีแบบใช้ค่าของ spoil-maker layout A

เสียง (D17):
- เสียงเล่า: wav ของแต่ละการ์ดต่อกัน ตามด้วยเงียบ 0.3 + `hold_s` วินาที; การ์ดเงียบเป็นเงียบ `hold_s`
- เสียงพื้น: ช่วงที่ติดกันและ `sound_id` เดียวกันรวมเป็นหนึ่งท่อน ความดังของช่วงแรกในท่อน; ท่อนที่สั้นกว่าวนจากต้นไฟล์ (`-stream_loop`, D56); เปลี่ยนเสียงผสม `acrossfade` 1 วินาที; ช่วง `sound: null` เงียบ
- ผสม `amix` `normalize=0`; output aac 192k, h264 crf 20 `yuv420p` 30 fps `+faststart`

- ยกเลิก: ลบ `.partial` และ `.render/`; restart ล้าง `.render/` กับ `*.partial`
- ลบคลิปที่ render: `DELETE …/renders/{name}` ลบ mp4 ก่อน json ท้าย; player เปิด mp4 อยู่ → `409` `in_use` (เหมือน spoil-maker spec › `DELETE /renders/{name}`)

### API

ทุก route ใต้ `/api/toon`; POST/PUT/PATCH เป็น JSON (ADR-0013) ยกเว้นสอง route upload.

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/series` | รายการ Series พร้อมจำนวน EP |
| POST | `/series` | สร้าง Series |
| GET, PATCH | `/series/{sid}` | อ่านหรือแก้ Series (รวมตัวละครและฉากหลัง) |
| DELETE | `/series/{sid}` | ลบ Series `{"confirm_eps": n}` |
| POST | `/series/{sid}/characters`, `/series/{sid}/backgrounds` | เพิ่ม |
| PATCH, DELETE | `/series/{sid}/{characters\|backgrounds}/{id}` | แก้หรือลบ |
| GET | `/series/{sid}/{characters\|backgrounds}/{id}/ref` | ภาพอ้างอิงปัจจุบัน |
| GET | `/series/{sid}/{characters\|backgrounds}/{id}/ref/pending/{n}` | ภาพที่ยังไม่เลือก |
| POST | `/series/{sid}/{characters\|backgrounds}/{id}/ref/pick` | เลือกภาพ 1–3 |
| POST | `/series/{sid}/{characters\|backgrounds}/{id}/ref/upload/check` | เช็คก่อน upload (ADR-0028) |
| POST | `/series/{sid}/{characters\|backgrounds}/{id}/ref/upload?size=` | เอาไฟล์เข้า (body ดิบ) |
| GET, POST | `/series/{sid}/eps` | รายการ EP, สร้าง EP `{"idea": "..."}` (ได้เลข `max_ep + 1`, D40) |
| GET, PATCH, DELETE | `/eps/{eid}` | อ่าน แก้ (`title`, `n`, `voice_id`, พล็อต) หรือลบ EP |
| POST, PATCH, DELETE | `/eps/{eid}/acts`, `/eps/{eid}/acts/{aid}` | เพิ่ม แก้ (สรุป, ชื่อองก์ D54) หรือลบองก์ (D10) |
| POST, PATCH, DELETE | `/eps/{eid}/segments…`, `/eps/{eid}/cards…` | เพิ่ม แก้ ลบ ช่วงและการ์ด (`after` บอกตำแหน่ง) |
| POST | `/eps/{eid}/cards/{kid}/swap-image` | สลับภาพก่อนหน้า |
| GET | `/eps/{eid}/cards/{kid}/image`, `/previous-image`, `/audio` | ไฟล์ |
| GET, DELETE | `/eps/{eid}/renders`, `/eps/{eid}/renders/{name}` | รายการ ไฟล์ ลบ (`409` `in_use` ระหว่าง player เปิด mp4) |
| POST, GET, DELETE | `/jobs`, `/jobs/current` | Toon job |
| POST, GET, DELETE | `/render`, `/render/current` | Render job (D45) |
| GET, PATCH, DELETE | `/sounds`, `/sounds/{mid}` | คลังเสียงพื้น |
| GET | `/sounds/{mid}/file` | ฟังเสียง |
| POST | `/sounds/imports/check`, `/sounds/imports?name=&size=`, `/sounds/downloads` | Sound import |
| GET, DELETE | `/sounds/import/current` | Sound import ปัจจุบัน |

- `PATCH` EP `n` จำนวนเต็ม 1–999 ไม่ซ้ำใน Series ไม่งั้น `400` `invalid_ep_number`; `n` > `max_ep` ยก `max_ep` ตาม (D40)
- `PATCH` EP `voice_id` เปลี่ยนแล้วการ์ดที่มีเสียงเป็น `stale_audio` (D8)
- ช่วงต้องมีการ์ดอย่างน้อย 1 ใบ: ลบการ์ดใบสุดท้ายลบช่วงด้วย; องก์ว่างได้
- ช่วงต้องมี `background_id` ที่มีใน Series: เพิ่มช่วงโดยไม่ส่ง → `400` `invalid_request`
- องก์ที่เพิ่มหลังยืนยันพล็อตมี `cards_from` `null` จึงนับเป็นองก์ที่พล็อตเปลี่ยน (D15)
- error ทุกตัวใช้รูป `ApiError`

### Frontend

- tab ที่ห้า "การ์ตูนเล่า" `#/toon`; `#/toon/series/{sid}`, `#/toon/eps/{eid}`, `#/toon/sounds`
- poll `/api/toon/jobs/current`, `/api/toon/render/current` และ `/api/toon/sounds/import/current` ด้วย `usePollWhile` ระหว่างงาน
- `gpu_busy` แสดงชื่องานจาก `RUNNING_NAMES`; `not_ready` ลิงก์ไป tab ติดตั้ง แบบ spoil-maker
- ระหว่าง Image job ของ EP ที่เปิดอยู่ หน้าเส้นเรื่องอ่านภาพใหม่ทุกครั้งที่ `done` เพิ่ม
- `useLeaveGuard` ระหว่าง upload
- คำเตือนตาม [legal.md](legal.md) แสดงก่อนเลือกไฟล์ทุกครั้ง ไม่ต้องกดยอมรับ:
  - เอาไฟล์ภาพอ้างอิงตัวละครเข้า: "ใช้ภาพหรือตัวละครที่คุณวาดเองหรือได้รับอนุญาต และอย่าใช้ภาพคนจริงในเรื่องที่ทำให้เขาเสียชื่อเสียง" (legal ข้อ 2)
  - เอาเสียงเข้าคลัง (ไฟล์และลิงก์): "ใช้เสียงของคุณเอง หรือเสียงที่ license ให้ใช้ในวิดีโอที่เผยแพร่ได้ และใส่เครดิตตามที่ license กำหนด" (legal ข้อ 4)

### Ops

- Setup script โหลดเพิ่มราว 11 GB (GGUF Q4_K_M 2.6 GB + text encoder และ vae ~8 GB, D34, D51); เครื่องที่โหลด Q8_0 ไว้แล้วเห็นแถว `model_klein_gguf` `missing` และ setup โหลดใหม่ (D50)
- `NOTICE.md` และหน้า Setup status แสดง license ของ klein ทั้งสอง repo และ Qwen3-4B text encoder (setup-status D11, legal ข้อ 1)

## Seams

สาม seam (D42): API พิสูจน์ทุกกติกาด้วย worker ปลอม, render พิสูจน์ไฟล์ด้วย ffmpeg จริง, หน้าเว็บพิสูจน์เฉพาะกติกาที่เห็นได้บนจอ.

1. **API การ์ตูนเล่า** `/api/toon/*` กับ `FakeLlm`, `FakeTts`, klein ปลอม
   - สร้าง Series `horror` → `acts`, `style`, `tone` ตามตารางค่าตั้งต้น
   - ลบ Series ไม่มี `confirm_eps` → `409` `confirm_needed` พร้อม `eps`; ระหว่าง Image job ของ Series → `409` `series_busy`; ยืนยันแล้ว folder หาย Saved voice และเสียงพื้นอยู่
   - Ref job → `pending` 3; `ref/pick {"n": 2}` → `ref_rev` +1 และ `.pending` หาย; pick ซ้ำ → `404` `no_pending`; upload ไฟล์ข้อความ → `400` `unsupported_file`; upload PNG ฉากหลัง 800×800 → ภาพอ้างอิง 1024×576
   - Plot job → EP มี `title`, `summary` ทุกองก์; ของใหม่อยู่ใน `plot` ไม่อยู่ใน Series
   - Cards job ครั้งแรก → ของใหม่เข้า Series `ref_rev` 0; การ์ดที่ใช้มันเป็น `no_ref`
   - แก้ `summary` หนึ่งองก์ → Cards job แตกเฉพาะองก์นั้น การ์ดองก์อื่น id และภาพเดิม; องก์นั้นมีการ์ดที่มีภาพและไม่ยืนยัน → `409` `cards_will_be_lost` พร้อมจำนวน
   - Image job `scope: missing` → การ์ด `no_image` ได้ภาพ, `no_ref` นับ `skipped` และอยู่ใน `missing_refs`; ทุกการ์ด `no_ref` → `400` `nothing_to_draw` พร้อม `missing_refs`; ยกเลิกกลางงาน → ภาพที่เสร็จอยู่
   - klein ปลอมล้มหนึ่งการ์ด → การ์ดนั้นอยู่ใน `failed_cards` งานไปต่อจน `done`
   - สร้างภาพใหม่ → `previous_image` เป็นภาพเดิม; สร้างอีกครั้ง → ไฟล์ภาพก่อนหน้าเดิมหายจากดิสก์; ไฟล์ PNG ที่ไม่มี `ep.json` อ้างหายหลัง start ใหม่
   - เปลี่ยนภาพอ้างอิงตัวละคร หรือเปลี่ยนตัวละครของการ์ด → การ์ดเป็น `stale_ref`; `scope: missing` ไม่สร้างมัน; `scope: stale_ref` สร้างใหม่
   - เริ่ม Image job ใหม่หลัง app ใหม่ (`paths.ROOT` เดิม) → สร้างเฉพาะการ์ดที่ยังไม่มีภาพ
   - Voice job → การ์ดมี `audio`; `PATCH` EP `voice_id` → การ์ดนั้น `stale_audio`
   - Sound import ไฟล์ wav → เสียงใน `sounds.json` เป็น m4a; ลบเสียงที่ช่วงใช้ → `409` `in_use`; `PATCH` ช่วง `sound: null` → ไม่มีเสียงพื้น
   - `sounds.json` เป็นข้อความเสียขณะมีเสียงสองตัว แล้ว start ใหม่ → `GET /sounds` ได้สองตัว ชื่อเป็น id, มี `sounds.json.bad-*`; ช่วงที่ใช้เสียงเดิมยังชี้ถูก (D70)
   - ไม่มี `sounds.json` → import หนึ่งไฟล์ → หนึ่งเสียง ไม่มี id ซ้ำ; เขียนข้อความเสียทับระหว่างทำงาน แล้ว import → สองเสียง (D70)
   - รายการหนึ่งตัว `source` ผิด → start ใหม่ รายการอื่นชื่อเดิม; รายการที่ไม่มี m4a หาย; m4a ที่ ffmpeg อ่านไม่ได้ → `duration_s` `0` (D70)
   - ลบตัวละครที่การ์ดใช้ → `409` `in_use` พร้อม `eps`; ลบ Saved voice ที่ Series ใช้ → `409` `voice_in_use`
   - ลบ EP แล้วสร้าง EP ใหม่ → เลขเท่ากับเลขสูงสุดที่เคยมี + 1
   - แก้การ์ดระหว่าง Cards job → `409` `ep_locked`; Toon job ระหว่าง Describe job → `409` `gpu_busy`; Render job ของ EP ที่เสียงครบระหว่าง Image job → `202`
   - แถว `model_klein` `missing` → Image job `503` `not_ready` พร้อม `rows`
2. **render จริง** `POST /api/toon/render` กับ ffmpeg จริง ภาพสีเรียบต่างสีต่อการ์ด และเสียงสั้นที่ test สร้าง
   - EP 3 การ์ด (หนึ่งการ์ดเงียบ `hold_s` 2) แบบ `frame` → `ffmpeg -i`: 1080×1920, 30 fps, h264, aac, ยาวเท่าผลรวมความยาวการ์ด ±0.1 วินาที
   - เฟรมที่กลางของแต่ละการ์ด (ดึงด้วย ffmpeg) ตรงกลางภาพเป็นสีของภาพการ์ดนั้นตามลำดับ
   - แบบ `full` → ไฟล์ ASS ใน `.render/` มีป้ายชื่อในการ์ดแรกของตัวละครเท่านั้น และไม่มีชื่อตอน
   - การ์ด `no_audio` → state `voicing` ก่อน `rendering` และการ์ดมี `audio` หลังจบ
   - การ์ดไม่มีภาพ → `400` `cards_not_ready` พร้อม `card_ids`
3. **หน้าเว็บ** (e2e) `App` กับ fetch ปลอม (`testing/testBackend.ts`)
   - กดเอาไฟล์ภาพตัวละครเข้า หรือเอาเสียงเข้า → เห็นคำเตือนของ legal ก่อนช่องเลือกไฟล์
   - ระหว่าง Cards job ของ EP ที่เปิดอยู่ → ช่องแก้การ์ดถูกปิด
   - เส้นเรื่องที่ความยาวรวม 130 วินาที → เห็นคำบอกว่าเกินเป้า 60–120
   - ระหว่าง Image job `done` เพิ่มจาก 1 เป็น 2 → ภาพของการ์ดที่สองขึ้นโดยไม่ reload
   - Cards job ได้ `409` `cards_will_be_lost` → เห็นจำนวนภาพที่จะหายต่อองก์ ก่อนกดยืนยัน

## Testing decisions

- **Copy:** `backend/tests/test_spoil_maker_voices_api.py` — งาน GPU ใน process ลูกปลอม, ช่อง GPU, ยกเลิก, crash
- **Copy:** `backend/tests/test_spoil_maker_render_api.py` — Render job ที่สร้างเสียงก่อน, `FakeFfmpeg`, และการอ่านไฟล์ด้วย `ffmpeg -i` (ราวบรรทัด 329); seam 2 ใช้ ffmpeg จริงแบบ test ที่มี `ok_ffmpeg` ใน `backend/tests/fakes.py`
- **Copy:** `backend/tests/test_spoil_import_api.py` — upload body ดิบ, `check`, `stalled`
- **Copy:** `frontend/src/features/story-kb/components/StoryEditor.test.tsx` — seam 3 แบบ story-kb D18: `App` จริงกับ `testing/testBackend.ts`
- **Copy:** `frontend/src/features/spoil-maker/components/SavedVoicePage.test.tsx` — หน้าที่ poll งาน (seam 3 ข้อภาพขึ้นระหว่างงาน)
- klein ปลอมเป็น subclass ของ `FakeModel` ใน `backend/tests/fakes.py` ที่คืน PNG ขนาดตามคำขอ
- klein จริงไม่อยู่ใน test; ticket 01 ลองด้วยมือบน Mac ตาม Open Question 1 และจดผลใน `progress.md`

## Out of Scope

- AI สร้างเสียงที่ขาดในคลังเสียงพื้น — รอบสอง (D5)
- โมเดลทำภาพเคลื่อนไหว (D4)
- ฝึก LoRA ต่อตัวละคร (D6)
- ดูตัวอย่างทั้ง EP หรือ render ร่าง (D18)
- กล่องข้อความบนภาพนอกจากป้ายชื่อ (D19)
- สีเน้นคำในซับ (D22)
- แก้ภาพการ์ดเฉพาะจุด (D27)
- หลายภาพให้เลือกต่อการ์ด (D33)
- เสียงเล่าต่อตัวละคร (D8)
- เช็ค klein บนเครื่อง Windows จริงและ VRAM ขั้นต่ำ — ticket ของ windows-check (D35)
- clone เสียงจากไฟล์ (spoil-maker D48)

## Open Questions

1. legal ข้อ 5 เป็น UNVERIFIED: ยังไม่ได้เช็คในราชกิจจานุเบกษาว่าร่าง พ.ร.บ. ว่าด้วยปัญญาประดิษฐ์ ยังไม่ผ่าน — non-blocking: ผู้ใช้ยอมรับความเสี่ยงใน D46.

## Sources

- [FLUX.2-klein-4B model card](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B) — repo, license, ภาพอ้างอิงหลายภาพ (accessed 2026-11-09)
- [unsloth/FLUX.2-klein-4B-GGUF](https://huggingface.co/unsloth/FLUX.2-klein-4B-GGUF) — ไฟล์ Q8_0, Q6_K, Q4_K_M และ license (accessed 2026-11-09)
- [diffusers Flux2 pipelines](https://huggingface.co/docs/diffusers/v0.42.1/en/api/pipelines/flux2) — `Flux2KleinPipeline`, `encode_prompt` (accessed 2026-11-09)
- [diffusers GGUF](https://huggingface.co/docs/diffusers/v0.42.1/en/quantization/gguf) — `from_single_file` กับ `GGUFQuantizationConfig` (accessed 2026-11-09)
- [PyTorch MPS backend](https://docs.pytorch.org/docs/2.8/notes/mps.html) — MPS ใน torch 2.8 (accessed 2026-11-09)
- [ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) — `zoompan`, `eq`, `xfade`, `acrossfade`, `amix`, `ass` (accessed 2026-11-09)
- [yt-dlp format selection](https://github.com/yt-dlp/yt-dlp#format-selection) — `bestaudio` (accessed 2026-11-09)
