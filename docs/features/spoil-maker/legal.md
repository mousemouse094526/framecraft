# Legal check: spoil-maker

**Jurisdiction:** Thailand — checked 2026-10-31

- การโหลดต้นฉบับและถอดบทพูดตรวจไว้แล้วใน [spoil legal.md](../spoil/legal.md) ข้อ 1, 2, 4; ไฟล์นี้ตรวจเฉพาะสิ่งที่ spoil-maker เพิ่ม
- ผลงานใช้แบบไม่หารายได้ (ADR-0007, D3)
- ผู้ใช้เป็นคนเผยแพร่คลิปเอง แอปจบที่ไฟล์ (D10)

## 1. เผยแพร่คลิปสปอยที่มีภาพและเสียงช่วงสั้นจากต้นฉบับ (D9, D15, D31)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ใช้ต้นฉบับเพียงบางตอนตามสมควร ไม่ใช่ทั้งเรื่องหรือฉากยาวต่อเนื่อง [1][2]
- คลิปเป็นการเล่า ติชม วิจารณ์ หรือแนะนำงาน ด้วยคำบรรยายของผู้ใช้เอง [1][2]
- ไม่ขัดการแสวงหาประโยชน์ตามปกติของเจ้าของ และไม่กระทบสิทธิของเจ้าของเกินสมควร [1]
- มีการรับรู้ความเป็นเจ้าของลิขสิทธิ์: ระบุชื่อเรื่องต้นฉบับในคลิปหรือคำอธิบาย [1][2]

UNVERIFIED — from model knowledge, verify before relying: ยังไม่พบคำพิพากษาไทยที่ชี้ว่าคลิปสปอยที่เล่าเรื่องทั้งเรื่องเข้าข้อยกเว้นมาตรา 32 และ 33.

## 2. เผยแพร่เสียงบรรยายจาก OmniVoice โดยไม่มีเครดิตโมเดล (D41)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ไม่ใช้เพื่อประโยชน์ทางการค้า [3]
- ให้เครดิตผู้สร้างโมเดล ชื่อ license และลิงก์ license เมื่อแชร์ [3]

ผู้ใช้รับความเสี่ยงของข้อเครดิตไว้ใน D41 และใส่เครดิตเป็นลายน้ำเองได้.

## 3. clone เสียงจากไฟล์เสียงของคนอื่น แล้วเผยแพร่คลิปที่ใช้เสียงนั้น (D33, D34)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ใช้ไฟล์เสียงของผู้ใช้เอง หรือได้รับความยินยอมจากเจ้าของเสียงก่อนเผยแพร่ [4]
- หน้า clone บอกผู้ใช้ข้อนี้ก่อนเลือกไฟล์ [4]

การ clone เพื่อใช้ส่วนตัวในเครื่องได้รับยกเว้นตามมาตรา 4 [4]. UNVERIFIED — from model knowledge, verify before relying: ยังไม่พบแนวทางของ PDPC ที่ชี้ว่าเสียงที่ใช้ clone เป็นข้อมูลชีวภาพตามมาตรา 26.

ไม่เกิดในรอบนี้: clone ย้ายไปรอบหน้า (D48). ตรวจข้อนี้ใหม่เมื่อเพิ่ม clone.

## 4. ใช้ Qwen3.5 9B, mlx-vlm, pythainlp และ font Kanit ในงานที่เผยแพร่ (D13, D14, D20, D21)

**Verdict: ALLOWED** [5][6][7][8]

## Summary
| # | Item | Verdict | Required to be allowed |
|---|------|---------|------------------------|
| 1 | เผยแพร่คลิปที่มีภาพและเสียงช่วงสั้นจากต้นฉบับ | CONDITIONAL (UNVERIFIED ว่าคลิปสปอยเข้าข้อยกเว้น) | ใช้บางตอนตามสมควร · เป็นการเล่าหรือวิจารณ์ด้วยคำของผู้ใช้ · ไม่ขัดการแสวงหาประโยชน์ของเจ้าของ · ระบุชื่อเรื่องต้นฉบับ |
| 2 | เผยแพร่เสียง OmniVoice โดยไม่มีเครดิต | CONDITIONAL | ไม่หารายได้ · ให้เครดิตโมเดลและ license (ผู้ใช้รับความเสี่ยงใน D41) |
| 3 | clone เสียงของคนอื่นแล้วเผยแพร่ (ไม่เกิดในรอบนี้, D48) | CONDITIONAL (UNVERIFIED ว่าเสียงเป็นข้อมูลชีวภาพ) | เสียงของตัวเองหรือได้รับยินยอม · หน้า clone แจ้งข้อนี้ |
| 4 | ใช้ Qwen3.5, mlx-vlm, pythainlp, Kanit | ALLOWED | — |

## References
1. พระราชบัญญัติลิขสิทธิ์ พ.ศ. 2537 มาตรา 32, 33 — https://th.wikisource.org/wiki/พระราชบัญญัติลิขสิทธิ์_พ.ศ._2537 (accessed 2026-10-31)
2. ว่าด้วย ข้อยกเว้นการละเมิดลิขสิทธิ์ (สรุปมาตรา 32–33) — https://www.gotoknow.org/posts/88607 (accessed 2026-10-31)
3. Creative Commons Attribution-NonCommercial 4.0 — https://creativecommons.org/licenses/by-nc/4.0/ (accessed 2026-10-31)
4. สรุปสาระสำคัญ พ.ร.บ.คุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 มาตรา 4, 19, 26 — https://legalaffairs.stou.ac.th/wp-content/uploads/2019/12/สรุปสาระสำคัญกฎหมาย-พรบ-คุ้มครองข้อมูลส่วนบุคคล-2562.pdf (accessed 2026-10-31)
5. mlx-community/Qwen3.5-9B-MLX-4bit › License: Apache-2.0 — https://huggingface.co/mlx-community/Qwen3.5-9B-MLX-4bit (accessed 2026-10-31)
6. mlx-vlm › License: MIT — https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11 (accessed 2026-10-31)
7. PyThaiNLP › License: Apache-2.0 — https://github.com/PyThaiNLP/pythainlp/tree/v5.4.0 (accessed 2026-10-31)
8. Kanit › SIL Open Font License 1.1 — https://github.com/google/fonts/tree/130fcfb0ff422fec96b335616b2ca99f91914792/ofl/kanit (accessed 2026-10-31)

*บันทึกด้าน compliance สำหรับวิศวกรรม ไม่ใช่คำแนะนำทางกฎหมาย*
