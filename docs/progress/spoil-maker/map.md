# Map: spoil-maker

## Destination

spec ที่ `ready-to-build` สำหรับ spoil-maker รอบแรก: จาก Temp clip ที่ถอดแล้ว (หนึ่งคลิปหรือหลาย EP) ได้คลิปสปอย mp4 แนวตั้งที่มีเสียงบรรยาย และแต่ละประโยคมีภาพจากต้นฉบับที่ตรงกับสิ่งที่พูด.

## Notes

- ผลวิเคราะห์คลิปตัวอย่าง 3 คลิปของผู้ใช้อยู่ใน [reference-shorts.md](../../features/spoil-maker/reference-shorts.md): จังหวะตัด, layout, เสียงบรรยาย
- ของที่มีแล้วจาก spoil: Temp clip ใน `media/temp/` และ Transcript ที่มีเวลาของแต่ละบรรทัด (spoil D21–D24)
- OmniVoice (TTS) ติดตั้งผ่าน Setup script แล้ว แต่ license CC BY-NC: ผลงานใช้ได้แค่ไม่หารายได้ (ADR-0007)
- งานยาวเป็น daemon thread และหน้าเว็บ poll (ADR-0010); งานที่ใช้ GPU รันใน process ลูก (ADR-0012)
- โมเดลใหม่ต้องลงทะเบียนและ pin ใน `backend.models` และโหลดผ่าน Setup script เท่านั้น (ADR-0004, ADR-0008)
- ของที่ต้องติดตั้งเพิ่มต้องมีแถวใน Status check (ADR-0009)
- feature จบได้เมื่อผ่านบน Mac; เช็ค Windows เป็น ticket ใน `windows-check` (ADR-0014)
- เวลาและ memory บน Mac M2: ร่างบทราว 5 นาที ราว 10 GB, Describe job ราว 45 นาทีต่อหนัง 96 นาที (D18), เสียงราว 9 วินาทีต่อประโยค 3.5 GB (D37, [tts-trial.md](../../features/spoil-maker/tts-trial.md)). เวลา render ยังไม่ได้วัด: ไม่ใช่การตัดสินใจ วัดตอน build
- ลิขสิทธิ์ของการนำภาพต้นฉบับไปเผยแพร่: legal check (Phase 2.5) หลังเขียน spec

## Decided

- **feature ใหม่หรือต่อใน spoil** — feature ใหม่ชื่อ `spoil-maker` ใน tab สปอย → [D1](../../features/spoil-maker/decisions.md)
- **ใช้ของเสียเงินได้ไหม** — ไม่ได้ ทุกอย่างต้องฟรี → [D2](../../features/spoil-maker/decisions.md)
- **ใช้เพื่อหารายได้ไหม** — ยังไม่คิดเรื่อง license ใช้ OmniVoice ไปก่อน แล้วค่อยหาตัวแทน → [D3](../../features/spoil-maker/decisions.md)
- **ใครเขียนบทสปอย** — AI ในเครื่องร่างจาก Transcript แล้วผู้ใช้แก้ก่อนสร้างเสียง → [D4](../../features/spoil-maker/decisions.md)
- **ต้นฉบับกี่ EP ต่อหนึ่งคลิปสปอย** — เลือก Temp clip ที่ถอดแล้วได้หลาย EP เรียงลำดับเอง ได้คลิปเดียว → [D5](../../features/spoil-maker/decisions.md)
- **เสียงบรรยายมาจากไหน** — OmniVoice เลือกเสียงตัวอย่างหรือ clone จากไฟล์เสียงสั้นของผู้ใช้ → [D6](../../features/spoil-maker/decisions.md)
- **ความยาวและสไตล์** — preset 3 แบบตามคลิปตัวอย่าง แล้วใส่ความยาวเป้าหมายเอง → [D7](../../features/spoil-maker/decisions.md)
- **Layout ของรอบแรก** — 3 แบบตามคลิปตัวอย่าง เลือกแยกจากสไตล์ → [D8](../../features/spoil-maker/decisions.md)
- **เสียงต้นฉบับ** — ลดเบาไว้ใต้เสียงบรรยาย ตั้งระดับได้ ไม่มีเพลงพื้นหลัง → [D9](../../features/spoil-maker/decisions.md)
- **ผลลัพธ์** — mp4 1080×1920 กับ `.srt` ของบทบรรยาย → [D10](../../features/spoil-maker/decisions.md)
- **ภาษาของบทบรรยาย** — ไทยอย่างเดียว ต้นฉบับภาษาอะไรก็ได้ → [D11](../../features/spoil-maker/decisions.md)
- **LLM รันผ่านอะไร** — library ใน `.venv` โมเดล pin ลง `models/` ตาม ADR ไม่ใช้ Ollama → [D12](../../features/spoil-maker/decisions.md)
- **LLM ในเครื่องตัวไหนเขียนบทและจับคู่ภาพ** — Qwen3.5 9B 4-bit ดูภาพได้ ลองแล้วใน [llm-trial.md](../../features/spoil-maker/llm-trial.md) → [D13](../../features/spoil-maker/decisions.md)
- **library ของ LLM** — mlx-vlm บน Mac หลัง interface; Windows ตัดสินใน `windows-check` → [D14](../../features/spoil-maker/decisions.md)
- **AI เห็นอะไรของต้นฉบับ** — Transcript กับ Shot description ของทุก Shot → [D15](../../features/spoil-maker/decisions.md)
- **บรรยายภาพเมื่อไร** — ปุ่มแยกต่อคลิป (Describe job) เห็น % ยกเลิกได้ → [D16](../../features/spoil-maker/decisions.md)
- **ตัด Shot และเลือกเฟรม** — scene filter 0.3, แบ่ง Shot ยาวเกิน 10 วินาที, รวม Shot สั้นกว่า 1 วินาที, เฟรมกลาง; ราว 840 Shot ต่อหนัง 96 นาที → [D17](../../features/spoil-maker/decisions.md)
- **LLM ร่างบทอย่างไรเมื่อมี Shot description ราว 840 รายการ** — สองขั้น: บทจาก Transcript แล้วเลือก Shot ต่อประโยคจากช่วง ±30 วินาที ลองแล้วใน [llm-trial.md](../../features/spoil-maker/llm-trial.md) › รอบ 2 → [D18](../../features/spoil-maker/decisions.md)
- **รายละเอียดของ layout แต่ละแบบ** — ตาม [layout-sketch.md](../../features/spoil-maker/layout-sketch.md): hook และชื่อตอนให้ AI ร่างแล้วผู้ใช้แก้, ซับ A ทีละท่อนสั้น, font Kanit, สีและตำแหน่งตายตัว, watermark ข้อความเดียวที่จำไว้, ตัดตรง → [D19](../../features/spoil-maker/decisions.md)–[D24](../../features/spoil-maker/decisions.md)
- **ตรวจแก้ก่อน render** — ตาม [review-sketch.md](../../features/spoil-maker/review-sketch.md): ร่างบทกับเลือก Shot ในงานเดียว, ตัวเลือก Shot ±30 วินาทีขยายทั้งคลิปได้, แก้ ลบ แทรกประโยค, Spoil draft เดียวเก็บเป็นไฟล์, ลบคลิปที่ใช้อยู่ลบ draft ด้วย, สร้างเสียงทั้งหมดหรือทีละประโยค, เสียงแบ่งครึ่งให้ 2 Shot → [D25](../../features/spoil-maker/decisions.md)–[D31](../../features/spoil-maker/decisions.md)
- **OmniVoice clone และเสียงตัวอย่าง** (research) — อ่านไทยได้ดี (CER 3–7%), clone ไฟล์ 3–10 วินาทีได้แต่บางไฟล์เสีย, ไม่มีเสียงสำเร็จรูป, 9–20 วินาทีต่อประโยค, 3.5 GB → [tts-trial.md](../../features/spoil-maker/tts-trial.md)
- **เสียงตัวอย่างมาจากไหน** — Saved voice ที่ผู้ใช้ออกแบบเอง (เพศ วัย ระดับเสียง → สุ่ม → ฟัง → บันทึก) เก็บเป็น clone prompt → [D32](../../features/spoil-maker/decisions.md)
- **clone ไม่ได้ทำอย่างไร** — สร้างประโยคตัวอย่างให้ฟังก่อนบันทึก ไม่มีตรวจอัตโนมัติ → [D33](../../features/spoil-maker/decisions.md)
- **ไฟล์สำหรับ clone** — 3–10 วินาทีแรก, Whisper ถอดข้อความ ผู้ใช้แก้ได้ → [D34](../../features/spoil-maker/decisions.md)
- **ความเร็วพูด** — speed 0.8–1.2 ต่อ Saved voice, ความเร็วที่วัดได้ใช้ประมาณความยาวบท ([tts-trial.md](../../features/spoil-maker/tts-trial.md) › รอบ 2) → [D35](../../features/spoil-maker/decisions.md)
- **ตัวเลขในบท** — แปลงเป็นคำไทยเฉพาะข้อความที่ส่งให้ OmniVoice ซับยังเป็นตัวเลข → [D36](../../features/spoil-maker/decisions.md)

## Open

ไม่มี: map จบแล้ว. spec ผ่าน gate เป็น `ready-to-build` เมื่อ 2026-10-31 ([spec.md](../../features/spoil-maker/spec.md), D38–D52); ขั้นต่อไปคือตัด ticket.

## Fog

ไม่มี.

## Out of scope

- อัปโหลดขึ้น YouTube หรือ TikTok ให้อัตโนมัติ — ผลของ map นี้จบที่ไฟล์ mp4
- โหลดต้นฉบับจากเว็บอื่นนอกจาก YouTube — การโหลดเป็นงานของ spoil
- ภาพเลื่อน ซ้อน เอียง และ transition — รอบแรกตัดตรง (D24)
- เช็คบนเครื่อง Windows — ทำใน `windows-check` ตาม ADR-0014 รวม backend ของ LLM บน Windows (D14)
