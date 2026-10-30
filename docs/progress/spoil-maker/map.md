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

## Open

1. **LLM ในเครื่องตัวไหนเขียนบทและจับคู่ภาพ** — ฟรีและรันบน M2 16 GB ได้ (D2): ลองโมเดลขนาด 7–8B กับภาษาไทย แล้วสรุปตัวเลือก; ติดตั้งผ่าน Setup script หรือใช้ Ollama ที่มีอยู่ (ADR-0003, ADR-0008) · kind: research
2. **AI เห็นอะไรของต้นฉบับ** — แค่ Transcript หรือดูภาพด้วย (คลิปที่ภาพเล่าเรื่องแต่ไม่มีบทพูดจะจับคู่ได้ไหม) · kind: interview · blocked by: LLM ในเครื่องตัวไหนเขียนบทและจับคู่ภาพ
3. **รายละเอียดของ layout แต่ละแบบ** — ตำแหน่งภาพ, hook หรือชื่อตอนที่ผู้ใช้พิมพ์เอง, ซับทีละคำหรือทีละประโยค, font ไทย, สี · kind: sketch
4. **ตรวจแก้ก่อน render** — เห็นรายการประโยคกับภาพที่ AI จับคู่ แล้วเปลี่ยนภาพ, แก้ประโยค หรือสร้างเสียงใหม่ทีละประโยค · kind: sketch
5. **OmniVoice clone และเสียงตัวอย่าง** — ไฟล์เสียงยาวเท่าไรถึง clone ได้, มีเสียงตัวอย่างอะไรให้เลือก, อ่านไทยได้ดีไหม (ลองจริงบนเครื่อง) · kind: research

## Fog

- วิธีจับคู่ประโยคกับภาพในทางเทคนิค (ตัดเป็น shot, ค้นด้วย Transcript, ค้นด้วยภาพ) — ชัดเมื่อตอบ "AI ตัวไหน" กับ "AI เห็นอะไร"
- เวลาและ memory บน Mac เมื่อต้นฉบับเป็นหนังยาว 1.5 ชั่วโมง
- ลิขสิทธิ์ของการนำภาพต้นฉบับไปเผยแพร่ — legal check หลังเขียน spec

## Out of scope

- อัปโหลดขึ้น YouTube หรือ TikTok ให้อัตโนมัติ — ผลของ map นี้จบที่ไฟล์ mp4
- โหลดต้นฉบับจากเว็บอื่นนอกจาก YouTube — การโหลดเป็นงานของ spoil
- เช็คบนเครื่อง Windows — ทำใน `windows-check` ตาม ADR-0014
