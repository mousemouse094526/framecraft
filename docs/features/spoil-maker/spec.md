# Spec: spoil-maker

ทำคลิปสปอยแนวตั้ง mp4 ที่มีเสียงบรรยายไทย จาก Temp clip ที่ถอดแล้วหนึ่งคลิป ตัดเป็น EP ตามเวลาแล้วทำทีละ EP โดยแต่ละประโยคมีภาพจากต้นฉบับที่ตรงกับสิ่งที่พูด.

**Status:** ready-to-build

## Problem

ผู้ใช้โหลดคลิปและถอดบทพูดใน tab คลิปได้แล้ว แต่ยังต้องเขียนบท อัดเสียง หาภาพที่ตรงกับแต่ละประโยค และตัดต่อเองในโปรแกรมอื่น. คลิปสปอยหนึ่งคลิปใช้เวลาหลายชั่วโมง.

## Solution

- บรรยายภาพของ Temp clip ทีละคลิปด้วยปุ่มของคลิปนั้น (Describe job) (D15, D16)
- ออกแบบเสียงบรรยาย ฟังก่อน แล้วบันทึกเป็น Saved voice ใช้ซ้ำ (D32, D35, D43, D48)
- เลือก Temp clip หนึ่งคลิป แอปตัดเป็น EP ตามความยาวที่ตั้ง (เลื่อนจุดตัดเองได้) แล้วเลือก EP เดียว (D66, D67, D69)
- เลือกสไตล์ layout ความยาว และ Saved voice แล้วกดร่างบท: AI ร่างบทไทยจากช่วงของ EP พร้อมเลือก 2 Shot ต่อประโยค (D7, D8, D18, D25)
- AI เรียบเรียงบททั้งบทให้ประโยคเล่าต่อกันเป็นเรื่องเดียว อัตโนมัติหลังร่าง และกด "เรียบเรียงใหม่" ได้ โดยเลือกว่าจะรวมประโยคที่แก้เองด้วยไหม (D72, D73, D74, D75)
- ตรวจแก้บท ข้อความค้างด้านบน และ Shot ของแต่ละประโยค; แก้ ลบ แทรกประโยคได้ (D19, D26, D27)
- สร้างและฟังเสียงทั้งหมดหรือทีละประโยค (D30)
- ใส่ลายน้ำข้อความได้หลายอัน และตั้งระดับเสียงต้นฉบับ (D40, D41)
- render เป็น mp4 1080×1920 กับ `.srt` เก็บทุกครั้งในรายการให้เล่น โหลด ลบ (D10, D42)
- แอปแบ่ง 3 tab: ติดตั้ง, คลิป (โหลด ถอด บรรยายฉาก แก้ Transcript), สปอย (เลือกคลิป → ตรวจแก้บท → ผล render) (D53)
- แก้ข้อความ Transcript ทีละบรรทัดก่อนให้ AI เขียนบท (D54)

## User Stories

**ผู้ใช้**
1. As a ผู้ใช้, I want กดปุ่มบรรยายภาพของ Temp clip และเห็น %, so that คลิปพร้อมให้ AI เลือกภาพ (D16)
2. As a ผู้ใช้, I want ออกแบบเสียงจากเพศ วัย ระดับเสียง และ speed แล้วฟังก่อนบันทึก, so that ได้เสียงเดิมทุกคลิป (D32, D35)
3. As a ผู้ใช้, I want รู้ก่อนว่าการถอดใหม่ บรรยายฉากใหม่ หรือลบคลิปจะลบ Spoil draft, so that ไม่เสียงานโดยไม่ตั้งใจ (D29, D49)
4. As a ผู้ใช้, I want เปลี่ยนชื่อและลบ Saved voice, so that รายการเสียงไม่รก (D43)
5. As a ผู้ใช้, I want เลือกคลิปเดียว ให้แอปตัดเป็น EP ตามความยาวที่ตั้ง แล้วเลือก EP ที่จะทำได้ง่าย, so that สปอยหนังยาวทีละช่วงได้ (D66, D67, D69)
14. As a ผู้ใช้, I want ตั้งสไตล์ layout ความยาว แล้วกดร่างบทครั้งเดียว, so that ได้บทพร้อมภาพโดยไม่ต้องเขียนเอง (D7, D8, D25, D39)
15. As a ผู้ใช้, I want เห็นจากตัวบอกขั้นว่าแต่ละขั้นถึงไหนแล้วและกดย้อนได้, so that รู้ว่างานกำลังรันและไม่หลง (D68)
16. As a ผู้ใช้, I want บทที่ร่างเล่าต่อกันเป็นเรื่องเดียว และกดให้ AI เรียบเรียงใหม่หลังแก้เอง โดยเลือกได้ว่าจะเก็บหรือเขียนทับที่แก้ไว้, so that ฟังแล้วไม่สะดุด (D72, D73, D74, D75)
6. As a ผู้ใช้, I want เห็นก่อนกดว่า Transcript ของ EP ยาวเกินไหม, so that ไม่ต้องรอแล้วล้ม (D46)
7. As a ผู้ใช้, I want แก้ ลบ แทรกประโยค และแก้ hook หรือชื่อตอน, so that บทถูกต้องและเป็นธรรมชาติ (D4, D19, D27)
8. As a ผู้ใช้, I want เปลี่ยน Shot ของประโยคจากตัวเลือกหรือให้ AI เลือกใหม่, so that ภาพตรงกับที่พูด (D25, D26)
9. As a ผู้ใช้, I want สร้างและฟังเสียงทีละประโยคหรือทั้งหมด และเห็นความยาวรวม, so that แก้ก่อน render (D30)
10. As a ผู้ใช้, I want ใส่ลายน้ำหลายอันและตั้งเสียงต้นฉบับ โดยแอปจำไว้, so that ไม่ต้องตั้งซ้ำทุกคลิป (D40, D41)
11. As a ผู้ใช้, I want render แล้วเล่น โหลด mp4 กับ `.srt` หรือลบผลเก่า, so that เอาไปลงได้และเทียบหลายรอบ (D10, D42)
12. As a ผู้ใช้, I want ปิดแอปแล้วเปิดใหม่ Spoil draft ยังอยู่, so that ไม่เสียงานที่แก้ (D28)
13. As a ผู้ใช้, I want แก้บทพูดที่ถอดผิดทีละประโยค, so that AI เขียนบทจากข้อความที่ถูก (D54)

## Design

แบบหน้าจอทำหลังจบ plan (D38); จอของ change request ตัด EP (D66–D68) และเรียบเรียงบท (D72, D74) อยู่ใน section `EP & เรียบเรียง`; จอที่ change request ร่างบทไปขั้น 2 (D81–D84) แตะเป็น `pending` รอแบบใหม่ ([ui-prompt.md](ui-prompt.md)) จออื่นมีแบบใน Figma แล้ว (ลิงก์ในตาราง). ทุกหน้าที่มีงานแสดง error ตามตาราง Frontend › ข้อความ error.

| Screen | User stories | Must show | Source |
|---|---|---|---|
| แถบ tab | — | 3 tab ตามลำดับ ติดตั้ง · คลิป · สปอย, tab ที่เปิดอยู่เด่นกว่า (D53) | [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) — header ของทุก frame |
| แถว Temp clip ใน tab คลิป | 1, 3 | ปุ่ม "บรรยายฉาก" ของคลิป กับบรรทัดใต้ปุ่ม "ให้ AI เขียนว่าแต่ละฉากมีภาพอะไร ใช้ตอนร่างบทสปอย" (D58); ระหว่างงาน: "กำลังแบ่งฉาก" แล้ว "กำลังบรรยายฉาก", % กับปุ่มยกเลิก; เสร็จ: "บรรยายฉากแล้ว" (D16); ปุ่มกดไม่ได้พร้อมเหตุผลเมื่อมีงาน GPU อื่น (D45); คลิปที่อยู่ใน Spoil draft: คำเตือนก่อนลบ ถอดใหม่ หรือบรรยายฉากใหม่ (D29, D49); บรรยายฉากคลิปที่บรรยายแล้ว: ยืนยันก่อนทำใหม่ | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8032-2275) — Clip row states |
| Saved voice | 2, 4 | เพศ วัย ระดับเสียง, speed 0.8–1.2, ปุ่มสุ่มและฟัง (D32, D35); บันทึกพร้อมชื่อ; รายการ: ชื่อ, ฟัง, เปลี่ยนชื่อ, ลบพร้อมยืนยัน (D43); ว่าง: "ยังไม่มีเสียง กดสุ่มเพื่อออกแบบเสียงแรก"; error: ลบเสียงที่ Spoil draft ใช้ (D43) | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8034-3220) — Saved voice |
| ตั้งค่าคลิปสปอย | 5, 6, 14 | เลือก Temp clip ได้คลิปเดียว (D66); คลิปที่เลือกไม่ได้บอกเหตุผล "ยังไม่ถอด" หรือ "ยังไม่บรรยายฉาก" พร้อมปุ่มไปทำ (D16); ไม่มีคลิปพร้อม: "ยังไม่มีคลิปที่ถอดและบรรยายฉากแล้ว" พร้อมลิงก์ไปรายการคลิป; ความยาวต่อ EP 5–60 นาที ตั้งต้น 30 (D69); รายการ EP: เลข, ช่วงเวลา, ภาพเล็ก, token, "render แล้ว {k}", EP ที่อยู่ใน Spoil draft; เลือกได้ทีละ EP (D67); เวลาจุดตัดระหว่าง EP แก้ได้ และ "ตัดใหม่ตามความยาว" (D66, D70); สไตล์ 3 แบบ, layout 3 แบบ ตั้งต้นตามสไตล์ (D7, D8); ความยาวคลิปสปอย 30–180 วินาที ตั้งต้น 60 (D39); Saved voice ตั้งต้นที่ใช้ล่าสุด; ไม่มี Saved voice: ลิงก์ไปสร้าง; token ของ EP / 32,000 และปุ่มร่างกดไม่ได้เมื่อเกิน (D46); ยืนยันก่อนทับ Spoil draft เดิม (D28); การ์ดสไตล์มีบรรทัดอธิบายใต้ชื่อ (D84); ระหว่างร่าง: ทุกช่องแสดงค่าของงานและกดไม่ได้ ไม่มีปุ่มร่าง Alert info "กำลังร่างบท {ชื่อคลิป} · EP {n}: ยกเลิกการร่างก่อนจึงเลือกใหม่ได้" พร้อมลิงก์ "ไปที่ตรวจแก้บท" (D82); current: [Figma: EP & เรียบเรียง](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833) — frames `Spoiler setup / 1 No clip chosen` ถึง `10b Drafting — picking shots`; components `Source clip row`, `Episode row`, `Cut point`; `Draft action` มี `Reason`; แบบเดิม [Spoiler setup](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8038-4681) ยังใช้กับขวามือ | `pending` |
| หน้าตรวจแก้ | 7, 8, 9, 10, 11, 16 | hook หรือชื่อตอน (D19); ความยาวประมาณ / เป้าหมาย และจำนวนประโยค (D30) พร้อมคำเตือนเมื่อนอก ±25%; แต่ละประโยค: 2 ภาพ Shot, ข้อความแก้ได้, บรรทัดที่อ้าง, สถานะ 4 แบบ (D30), ฟัง, สร้างเสียงใหม่, ให้ AI เลือก Shot ใหม่, ลบพร้อมยืนยัน, แทรกใต้ (D25, D27); ระดับเสียงต้นฉบับ (D40); ลายน้ำ: เพิ่ม ลบ เปิดปิด ข้อความ ตำแหน่ง 6 จุด ขนาด (D41, D64); คำเตือนเมื่อลายน้ำบนกลางที่เปิดอยู่ทับ hook หรือชื่อตอน (D64); ปุ่มสร้างเสียงทั้งหมดและ render; render กดไม่ได้เมื่อมีประโยค "ไม่มี Shot"; ระหว่าง Draft job `pick`, Voice job หรือ Render job: "สร้างเสียง x/y" หรือ "render %" กับปุ่มยกเลิก และช่องแก้ทุกช่องกดไม่ได้ (D51); ไม่มี Spoil draft: ลิงก์ไปหน้าตั้งค่า; ปุ่ม "เรียบเรียงใหม่" เปิดกล่องเลือกก่อนเริ่ม: ช่องติ๊ก "เรียบเรียงประโยคที่แก้เองด้วย" (ตั้งต้นไม่ติ๊ก, ซ่อนเมื่อไม่มีประโยคแก้เอง), บรรทัด "ประโยคที่เปลี่ยนต้องสร้างเสียงใหม่" เมื่อมีประโยคที่มีเสียงแล้ว, ปุ่ม "เรียบเรียง" และ "ยกเลิก" (D75), ระหว่างงาน "กำลังเรียบเรียง" กับปุ่มยกเลิก และช่องแก้ทุกช่องกดไม่ได้, ป้าย "แก้เอง" ของประโยคที่ผู้ใช้แก้หรือแทรก (D72, D74, D75); ระหว่าง Draft job `kind: "draft"`: การ์ดความคืบหน้าแทนบท — "{ชื่อคลิป} · EP {n}" สไตล์ ความยาวเป้าหมาย, 3 ขั้น "เขียนบท" → "เรียบเรียง" → "เลือกภาพ {x}/{y}" (เสร็จ / กำลังทำ / รอ), แถบความคืบหน้า, ปุ่มยกเลิก (D81); ร่างล้ม: Alert error พร้อม "ลองอีกครั้ง" และ "กลับไปแก้ตั้งค่า" เหนือบทเดิมหรือ "ยังไม่มีบท" (D83); current: [Figma: Script review](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390); ใน 3 tab: ขั้น 2 ของ tab สปอย; สวิตช์ลายน้ำและคำเตือนลายน้ำทับ (D64): frames `Script review / Watermark …` และ `Overlap …` ใน section เดียวกัน, component `Watermark row` variant `enabled`; เรียบเรียงใหม่ (D72, D74, D75): [Figma: EP & เรียบเรียง](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833) — frames `Script review / Polish …`, component `Polish dialog`, `Sentence card` property `Edited`, `Review footer` state `polishing` | `pending` |
| ตัวเลือก Shot | 8 | ภาพเล็กของ Shot ในช่วง ±30 วินาที, "ดูทั้ง EP" แสดงทุก Shot ในช่วง EP, ชี้แล้วเห็น Shot description, เล่นช่วงนั้น (D26, D70); ประโยคไม่มีบรรทัดที่อ้างเปิดที่ทั้ง EP (D26, D27) — แบบเดิมมีตัวเลือก EP: build ตัดออกและเปลี่ยนป้ายเป็น "ดูทั้ง EP" | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8050-16186) — Shot picker |
| Transcript ที่แก้ได้ใน tab คลิป | 13 | ชี้บรรทัดแล้วมีปุ่ม "แก้"; กำลังแก้: ช่องพิมพ์กับ "บันทึก" และ "ยกเลิก"; บรรทัดที่แก้แล้วมีป้าย "แก้แล้ว" (D54) | [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) — frames คลิป และ คลิป — แก้ประโยค; component `Transcript line` state hover, editing, edited |
| ตัวบอกขั้นของ tab สปอย | 5, 7, 11, 15 | 1 เลือกคลิป → 2 ตรวจแก้บท → 3 ผล render; ขั้นที่เปิดอยู่เด่น; ทุกขั้นแสดงเลขและดูกดได้ (ไม่มีเครื่องหมายถูกตามตำแหน่ง); บรรทัดสถานะใต้ชื่อ: "{ชื่อคลิป} · EP {n}" / "ยังไม่เลือก", "กำลังร่าง" / "กำลังเลือกภาพ x/y" / "สร้างเสียง x/y" / "{n} ประโยค" / "ยังไม่มีบท", "render {p}%" / "{n} คลิป" / "ยังไม่มี"; จุดหมุนข้างเลขของขั้นที่มีงานรัน (D68); มือถือแสดงชื่อเฉพาะขั้นที่เปิด แต่จุดหมุนแสดงทุกขั้น | [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) — component `Spoil steps` (variant `breakpoint`) และ `Spoil step`; สถานะต่างๆ: [Figma: EP & เรียบเรียง](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833) — frames `Step bar / …` |
| ผล render | 11 | แต่ละรายการมี "EP {n}" (D70); ระหว่าง render: "สร้างเสียง x/y" แล้ว "render %" กับปุ่มยกเลิก; รายการใหม่สุดก่อน: เวลา, ความยาว, เล่น, โหลด mp4, โหลด `.srt`, ลบพร้อมยืนยัน (D42); บรรทัด "ต้นฉบับ: {ชื่อคลิป}" พร้อมปุ่ม copy (legal 1); ว่าง: "ยังไม่มีผล render" | [Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8055-16850) — Render results; ใน 3 tab: ขั้น 3 ของ tab สปอย |

## Expected Outcome

ผู้ใช้ทำคลิปสปอยแนวตั้งที่มีเสียงบรรยายไทยและภาพตรงกับบทได้ในแอปเดียวบน Mac โดยไม่ต้องเขียนบท อัดเสียง หรือตัดต่อเอง.

- **หนังหนึ่งเรื่อง:** Temp clip 96 นาทีที่ถอดแล้ว กดบรรยายฉาก (ราว 45 นาที), ร่างบท 60 วินาที (ราว 5 นาที), แก้ 2 ประโยค, render → ได้ mp4 1080×1920 ยาว 45–75 วินาที กับ `.srt`
- **ตัด EP:** Temp clip 60 นาที ความยาวต่อ EP 30 → EP 1 กับ EP 2 จุดตัดราวนาทีที่ 30 ที่ขอบ Shot; เลือก EP 2 แล้วร่าง → บทอ้างเฉพาะบรรทัดของ EP 2 และ Shot อยู่ในช่วง EP 2 ทั้งหมด; render → ผล render มี "EP 2"
- **ปิดแอปกลางทาง:** แก้บทแล้วปิด backend, เปิดใหม่ → หน้าตรวจแก้มีบท Shot และเสียงเหมือนก่อนปิด

**How success is judged:**
- คลิป 96 นาที: Describe job จบภายใน 60 นาทีบน M2 และได้ 700–1,000 Shot
- ร่างบท 60 วินาทีจากหนัง 96 นาทีที่ผ่านในครั้งแรก จบภายใน 8 นาทีบน M2
- บทที่ร่างได้ ความยาวประมาณอยู่ใน ±25% ของเป้าหมาย
- บทที่ร่างและเรียบเรียงแล้ว: อ่าน 10 คู่ประโยคติดกัน อย่างน้อย 8 คู่ประโยคหลังเล่าต่อจากประโยคก่อน (เช็คด้วยตา, D72)
- สุ่ม 10 ประโยคจากผลร่าง: Shot ที่ AI เลือกตรงกับเนื้อหาอย่างน้อย 5 ประโยค (ผล trial ราว 5/8, D18)
- ผล render: ความยาวเท่าผลรวมความยาวเสียงทุกประโยคภายใน 0.2 วินาที
- ผล render: ข้อความไทยที่มีสระบนล่างและวรรณยุกต์ซ้อนแสดงถูกในทั้ง 3 layout (เช็คด้วยตา)
- ไม่มีงาน GPU สองงานรันพร้อมกัน (D45)

## Implementation

### Modules touched

- **`backend.models`**
  - เพิ่ม `QWEN` ต่อท้าย `MODELS` (D13):
    - `check_id` `model_qwen`, `label` `Qwen3.5 9B model`
    - `repo_id` `mlx-community/Qwen3.5-9B-MLX-4bit`, `revision` `938d8919941c6e7efd3c7150eff7fe9d12afa631`
    - `allow_patterns` `*.json`, `*.safetensors`, `*.txt`, `*.jinja` (รวม tokenizer และ chat template ที่ `AutoTokenizer` ใช้)
    - `license` `Apache-2.0`, `license_url` `https://www.apache.org/licenses/LICENSE-2.0`, `author` `Qwen`
  - เพิ่มฟิลด์ `platforms` ใน `ModelSpec` ค่าตั้งต้นทั้งสอง OS; `QWEN` เป็น `darwin` เท่านั้น (D50)
- **`backend.setup`**
  - โหลด Qwen ตาม ADR-0004 เฉพาะ Mac; บน Windows ข้าม (D50)
  - โหลด `Kanit-Bold.ttf` กับ `OFL.txt` จาก `raw.githubusercontent.com/google/fonts/130fcfb0ff422fec96b335616b2ca99f91914792/ofl/kanit/` ลง `models/fonts/kanit/` (D21, D45)
  - ตรวจ sha256: `Kanit-Bold.ttf` `5dec5b080dab13de9d2295437c0ff3ec05c9e75587dfc31358c005eb4efa5e70`, `OFL.txt` `eb998cc5a685b240cdb46a0b5747e70334c8c57bbd7b1f6b044d75719358df67`; ไม่ตรงลบไฟล์และ Setup script ล้ม
  - ตรวจผ่านแล้วเขียน `models/.setup/font_kanit` ที่มี sha256 ทั้งสอง
- **`backend.checks`**
  - เพิ่ม 4 แถว: ตาราง Status check (ADR-0009)
- **`backend.paths`**
  - path ของ Shot, Spoil draft, Saved voice, ค่าที่จำไว้, ผล render, font และ `models/pythainlp/`
- **`backend.gpu`** (ใหม่)
  - ช่อง GPU ช่องเดียวที่ทุกงาน GPU ต้องจองก่อนเริ่ม และ lock ของ Spoil draft (ช่อง GPU, Spoil draft)
- **`backend.spoil`**
  - `transcribe` จองช่อง GPU ก่อนเริ่ม; ชนได้ `409` `gpu_busy` (D45)
  - `transcribe` ของคลิปใน Spoil draft: ต้องมี `confirm_draft_loss: true` ไม่งั้น `409` `in_draft`; งาน `done` แล้วลบ Spoil draft (D49)
  - ลบ Temp clip: คลิปที่งาน spoil-maker ใช้อยู่ `409` `clip_busy` (D49); ลบสำเร็จแล้วลบ Shot ของคลิปและ Spoil draft ที่ใช้คลิปนั้น (D29, D45)
  - `GET /clips` เพิ่มฟิลด์ `described` และ `in_draft`
  - `ApiError.extra` (เดิม `SpoilError`) รับค่าที่ไม่ใช่ string (list, int) สำหรับ `sentence_ids`, `tokens`
  - ลบ Temp clip ลบ `media/temp/episodes/{id}.json` ด้วย (EP, ADR-0018)
- **`backend.spoil_maker`** (ใหม่)
  - `shots`: Describe job, ไฟล์ Shot, ภาพเล็ก
  - `llm`: interface ของ LLM กับ backend mlx-vlm และ worker ใน process ลูก (D14, ADR-0012)
  - `tts`: interface ของ TTS กับ OmniVoice และ worker ใน process ลูก (D3, ADR-0012)
  - `voices`: Saved voice และ Voice job
  - `episodes`: การตัด EP ของ Temp clip (EP, D66); Describe job `done` ลบไฟล์การตัดของคลิปนั้น
  - `draft`: Spoil draft, Draft job, การแก้บท
  - `thai`: ตัดคำ, แปลงตัวเลข, นับตัวอักษร (D20, D36, D44)
  - `render`: Render job, ไฟล์ ASS, ผล render
  - `settings`: ค่าที่จำไว้ (D45)
- **`backend.routes`**
  - เพิ่ม router `/api/spoil-maker`
- **`NOTICE.md`**
  - ประโยค "should credit the model" เปลี่ยนเป็นแนะนำให้ใส่เครดิต ไม่บังคับ (D41)
- **`frontend` › `lib/useHash`** (เดิม `useHashTab`)
  - hash ที่ขึ้นต้นด้วย `#/spoil/` เปิด tab สปอย (spoil D10)
- **`frontend` › `features/spoil`**
  - แถว Temp clip มีปุ่มบรรยายฉาก, ป้าย "บรรยายฉากแล้ว" และคำเตือนของคลิปใน Spoil draft (D29, D49)
- **`frontend` › `features/spoil-maker`** (ใหม่)
  - หน้า Saved voice, ตั้งค่า, ตรวจแก้, ตัวเลือก Shot, ผล render ใต้ tab สปอย (D1)

### Dependencies

| Package | Version | Marker | ใช้ทำอะไร |
|---|---|---|---|
| `mlx-vlm` | `==0.7.11` | `sys_platform == 'darwin'` | รัน Qwen3.5 9B บน Mac (D14) |
| `pythainlp` | `==5.4.0` | — | ตัดคำไทยสำหรับซับและการตัดบรรทัด (D20, D45) |

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| mlx-vlm | 0.7.11 | `load(path)` โหลดจาก snapshot ในเครื่อง | [README v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11) |
| mlx-vlm | 0.7.11 | `prompt_utils.apply_chat_template(..., enable_thinking=False)` ปิด thinking ของ Qwen3.5 | [README v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11) |
| mlx-vlm | 0.7.11 | `generate(model, processor, prompt, image=…, max_tokens=…, temperature=…)` รับภาพหนึ่งภาพหรือไม่มีภาพ คืน `GenerationResult` ที่ข้อความอยู่ใน `.text` | [README v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11) |
| transformers | ที่ติดตั้งอยู่ (≥ 5.3) | `AutoTokenizer.from_pretrained(snapshot_dir)` โหลด tokenizer ของ Qwen3.5 จาก snapshot เพื่อนับ token (D46) โดยไม่โหลดโมเดล | [AutoTokenizer](https://huggingface.co/docs/transformers/main/en/model_doc/auto#transformers.AutoTokenizer) |
| omnivoice | 0.2.1 | `generate(text, instruct=…)` สร้างเสียงจากคุณสมบัติ; `create_voice_clone_prompt(ref_audio, ref_text)` คืน prompt ที่ `save` เป็น `.pt` และ `load` ใช้ซ้ำ; `generate` รับ `speed` และ `num_step` | [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) |
| pythainlp | 5.4.0 | `word_tokenize(text, engine="newmm")` ใช้พจนานุกรมใน package ไม่ใช้ network | [tokenize API](https://pythainlp.org/dev-docs/api/tokenize.html), [v5.4.0](https://github.com/PyThaiNLP/pythainlp/tree/v5.4.0) |
| pythainlp | 5.4.0 | env `PYTHAINLP_DATA` (`PYTHAINLP_DATA_DIR` เลิกใช้แล้ว, D59) ย้าย folder ข้อมูลจาก `~/pythainlp-data` มาที่ `models/pythainlp/` (ADR-0003); ตั้งก่อน import | [v5.4.0](https://github.com/PyThaiNLP/pythainlp/tree/v5.4.0) |
| ffmpeg (imageio-ffmpeg 0.7.0) | 7.1 | filter `select='gt(scene,0.3)'` กับ `showinfo` ให้เวลาของจุดตัดภาพ; `ass` วาดข้อความไทยด้วย libass กับ harfbuzz; `gblur`, `tpad` (`stop_mode=clone`), `amix`; encoder `libx264` กับ `aac`; `-progress pipe:1` | [ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) |
| libass (ใน ffmpeg) | ที่มากับ ffmpeg 7.1 | ASS tag `\pos`, `\an`, `\bord`, `\3c`, `\fs` และ `fontsdir` ชี้ folder ของ Kanit | [ASS tags](https://aegisub.org/docs/latest/ass_tags/) |
| Kanit (google/fonts) | commit `130fcfb` | `Kanit-Bold.ttf` ใช้ใน libass ได้ และ license OFL ให้แจกจ่ายได้ | [ofl/kanit](https://github.com/google/fonts/tree/130fcfb0ff422fec96b335616b2ca99f91914792/ofl/kanit) |

### Status check

เพิ่ม 4 แถวต่อจากแถวเดิม (ADR-0009). ทุกแถวไม่โหลดโมเดลและไม่ใช้ network.

| id | ผ่านเมื่อ | Windows |
|---|---|---|
| `model_qwen` | Model marker ของ `QWEN` ตรง revision (ADR-0004) | `missing` "ยังไม่รองรับบน Windows" (D50) |
| `mlx_vlm` | import `mlx_vlm` ได้และ version ตรง | `missing` "ยังไม่รองรับบน Windows" (D50) |
| `pythainlp` | หา package `pythainlp` ได้และ version ตรง (ไม่ import จริง เพราะ import สร้าง folder ข้อมูล, D59) | เหมือน Mac |
| `font_kanit` | ไฟล์ทั้งสองอยู่และ marker มี sha256 ตรง | เหมือน Mac |

แต่ละงานเช็คเฉพาะแถวที่ตัวเองใช้ (ADR-0009). ไม่ผ่าน → `503` `not_ready` พร้อม `rows`:

| งาน | แถวที่ต้องผ่าน |
|---|---|
| Describe job, Draft job | `ffmpeg`, `device`, `model_qwen`, `mlx_vlm` |
| Voice job | `device`, `model_omnivoice`, `pythainlp` |
| Render job | `ffmpeg`, `font_kanit`, `pythainlp`; มีประโยคที่ขาดเสียงเพิ่มแถวของ Voice job |

### ช่อง GPU

- ทุกงานที่โหลดโมเดลจองช่อง GPU ช่องเดียวของ backend ก่อนเริ่ม: Transcribe job (spoil), Describe job, Draft job, Voice job, Render job ช่วง `voicing` (D45)
- จองไม่ได้ → `409` `gpu_busy` พร้อม `running: "transcribe" | "describe" | "draft" | "voice" | "render"`
- งานคืนช่องเมื่อจบทุกแบบ: `done`, `failed`, `cancelled`
- Render job คืนช่องเมื่อจบ `voicing` ก่อนเริ่ม `rendering` (D51)
- Download job ของ spoil ไม่จอง (spoil D24)
- งานแต่ละชนิดยังมีได้ทีละงาน: ใช้ `JobSlot` ของ `backend.spoil` (ADR-0010); ชนกับงานชนิดเดียวกันได้ `409` `busy`
- ทุกงานรันใน thread ของ backend; ส่วนที่โหลดโมเดลรันใน process ลูก `spawn` ที่ส่งผลกลับผ่าน queue และ thread ของ backend เป็นผู้เขียนไฟล์ผลคนเดียว (ADR-0012)
- `backend.gpu` บอกได้ว่าคลิปไหนและ Spoil draft ถูกงานไหนใช้อยู่ สำหรับ `clip_busy` และ `draft_locked` (D49)

### Describe job

เริ่มเมื่อผู้ใช้กด (D16). ขั้นตอน:

1. เช็คตามลำดับ (D60): คลิปมีอยู่ → ไม่ `404` `not_found`; แถว Status check → ไม่ผ่าน `503` `not_ready`; มี Describe job ยังไม่จบ → `409` `busy`
2. คลิปอยู่ใน Spoil draft และไม่มี `confirm_draft_loss: true` → `409` `in_draft` (D49); ช่อง GPU ไม่ว่าง → `409` `gpu_busy`; ผ่านแล้วจองช่อง GPU
3. state `cutting`: ffmpeg หาจุดตัดภาพด้วย scene filter 0.3 (D17) ใน thread ของ backend; `percent` จากเวลาของเฟรมล่าสุดเทียบความยาวคลิป
4. สร้างรายการ Shot จากจุดตัด (D17):
   1. ช่วงระหว่างจุดตัดสองจุดเป็นหนึ่ง Shot
   2. ช่วงยาวกว่า 10 วินาทีแบ่งเป็น `ceil(ยาว / 10)` ท่อนเท่ากัน
   3. Shot สั้นกว่า 1 วินาทีรวมเข้า Shot ก่อนหน้า; Shot แรกที่สั้นกว่า 1 วินาทีรวมเข้า Shot ถัดไป
   4. เลข Shot `n` เริ่มที่ 0 ตามเวลา
5. ดึงเฟรมกลางของแต่ละ Shot ลง folder ชั่วคราว `media/temp/shots/.new-{id}/`: JPEG กว้าง 320 คุณภาพ 80 ชื่อ `{n}.jpg` และ JPEG กว้าง 448 ให้ LLM (D45, D51, D57)
6. state `describing` (`done` / `total` Shot): process ลูกโหลด Qwen แล้วบรรยายเฟรม 448 ทีละ Shot เป็นภาษาอังกฤษไม่เกิน 30 คำ ตาม llm-trial › รอบ 2; ค่าการสร้างตาม Draft job › ค่าการสร้างข้อความ
7. เขียน `media/temp/shots/.new-{id}/shots.json`, ลบเฟรม 448, แล้วสลับใต้ lock ของ `backend.gpu`: ลบ `media/temp/shots/{id}/` เดิมถ้ามี, rename folder ใหม่เป็น `media/temp/shots/{id}/` และลบ `media/temp/episodes/{id}.json` (D51, D71)
8. คลิปอยู่ใน Spoil draft (ยืนยันแล้วในข้อ 1) → ลบ Spoil draft (D49)
9. คืนช่อง GPU

- ยกเลิกหรือ crash: ลบ `.new-{id}/`; Shot เดิมของคลิปยังอยู่ (D51)
- กดใหม่หลังยกเลิกเริ่มต้นใหม่ทั้งหมด ไม่มี resume
- คลิปที่บรรยายฉากแล้ว = `media/temp/shots/{id}/shots.json` อ่านได้และมี `clip_id` ตรง

ไฟล์ `media/temp/shots/{id}/shots.json`:

```json
{
  "clip_id": "f7jkZXvaB4g",
  "shots": [
    { "n": 0, "start": 0.0, "end": 4.2, "description": "A car drives down a rural road." }
  ]
}
```

| state | ความหมาย |
|---|---|
| `cutting` | หาจุดตัดภาพ มี `percent` |
| `describing` | บรรยายภาพ มี `done` และ `total` |
| `done` | สลับ folder แล้ว |
| `failed` | `error.code`: `crashed`, `model_failed`, `ffmpeg_failed`, `internal` |
| `cancelled` | ยกเลิกแล้ว |

### Saved voice

ไฟล์ของ Saved voice หนึ่งเสียงใน `media/spoil-maker/voices/`:

| ไฟล์ | เก็บอะไร |
|---|---|
| `{voice_id}.json` | `name`, `kind` (`design`; `clone` สงวนไว้รอบหน้า, D48), `speed`, `chars_per_s`, `created_at`, `instruct` |
| `{voice_id}.pt` | clone prompt ของ OmniVoice (D32) |
| `{voice_id}.wav` | ประโยคตัวอย่างที่ผู้ใช้ฟังก่อนบันทึก |

ออกแบบเสียง (D32):

1. ผู้ใช้เลือกเพศ (`male`, `female`), วัย (`child`, `teenager`, `young adult`, `middle-aged`, `elderly`), ระดับเสียง (`very low pitch`, `low pitch`, `moderate pitch`, `high pitch`, `very high pitch`) และ speed 0.8–1.2 ทีละ 0.05 (D35)
2. Voice job `design_preview`: OmniVoice สร้างประโยคล็อกด้วย `instruct`, สร้าง clone prompt จากประโยคนั้น, แล้วสร้างประโยคตัวอย่างด้วย prompt ที่ speed ที่เลือก และ `num_step` 16 (D37)
3. ผู้ใช้ฟัง; กดสุ่มอีกครั้ง = งานใหม่ทับผลเดิม
4. บันทึกพร้อมชื่อ → ย้าย preview ล่าสุดเป็น Saved voice

- `voice_id` คือ `v_` ตามด้วย hex 8 ตัว
- ประโยคตัวอย่างใช้ข้อความเดียวเสมอ: `ชายคนหนึ่งตื่นขึ้นมาในห้องที่ไม่รู้จัก และพบจดหมายที่เขียนด้วยลายมือของตัวเอง`
- `chars_per_s` = ตัวอักษรของข้อความหลังแปลงตัวเลข ไม่นับช่องว่างและวรรคตอน หารความยาวเสียงตัวอย่าง (D35, D36)
- preview ที่ยังไม่บันทึกอยู่ใน `media/spoil-maker/voices/.pending/` มีชุดเดียว ล้างตอน start
- ชื่อ 1–40 ตัวอักษร ไม่ว่างหลังตัดช่องว่าง; ชื่อซ้ำได้
- เปลี่ยนชื่อได้; ลบ Saved voice ที่ Spoil draft ใช้ หรือที่ `order.voice_id` ของ Draft job `kind: "draft"` ที่ยังไม่จบใช้ → `409` `voice_in_use` (D43, D87)
- speed แก้ไม่ได้หลังบันทึก (D43)

### EP

Temp clip หนึ่งคลิปตัดเป็น EP ตามเวลา; 1 EP = 1 คลิปสปอย (D66, D67). ต้องบรรยายฉากแล้ว เพราะจุดตัดอยู่ที่ขอบ Shot.

- **ความยาวคลิป** = `shots[-1].end` ของ `shots.json` (D71)
- **ไฟล์:** `media/temp/episodes/{id}.json` `{"minutes": 30, "cuts": [1799.0], "custom": false}` เขียนผ่าน `{id}.json.{uuid}.tmp` แล้ว rename; เป็นของ Temp clip (ADR-0018) (D70, D71)
- **ไฟล์แรก:** `GET` ครั้งแรกของคลิปที่ไม่มีไฟล์ ตัดตาม `ep_minutes` ของค่าที่จำไว้ (D69) แล้วเขียนไฟล์ทันที — การตัดของคลิปไม่เปลี่ยนตาม `ep_minutes` ที่คลิปอื่นตั้งภายหลัง (D71)
- **ตัดตาม `minutes`:** จุดที่ `k × minutes × 60` (k = 1, 2, …) ที่น้อยกว่าความยาวคลิป ขยับไปเวลาเริ่มของ Shot ที่ใกล้สุด (เท่ากันเลือก Shot ก่อน); จุดที่ขยับแล้วซ้ำหรือเป็น 0 ทิ้ง; EP สุดท้ายสั้นกว่า 60 วินาที → ลบจุดตัดสุดท้าย (รวมเข้า EP ก่อนหน้า) (D66, D70)
- **`cuts` ที่ผู้ใช้ส่ง:** แต่ละจุดขยับไปเวลาเริ่มของ Shot ที่ใกล้สุด (เท่ากันเลือก Shot ก่อน); หลังขยับต้องเรียงจากน้อยไปมาก ไม่ซ้ำ อยู่ใน (0, ความยาวคลิป) และเมื่อมี 2 EP ขึ้นไปทุก EP ยาว ≥ 60 วินาที → ไม่ใช่ `400` `invalid_episodes`. EP เดียวทั้งคลิปใช้ได้เสมอแม้สั้นกว่า 60 วินาที (D71)
- **รูปของ request:** `minutes` จำนวนเต็ม (ไม่ใช่ boolean) ใน {5, 10, …, 60}; `cuts` list ของตัวเลขจำกัด (ไม่ใช่ boolean, ไม่ใช่ NaN หรือ Infinity) ไม่เกิน `floor(ความยาวคลิป / 60)` จุด; นอกนั้น `400` `invalid_episodes` (D71)
- **`PUT`:** ไม่มี `cuts` → ตัดตาม `minutes`, `custom` `false`; มี `cuts` → ใช้ `cuts`, `custom` `true`; `minutes` ต่างจากในไฟล์ → เขียน `ep_minutes` ลงค่าที่จำไว้ด้วย
- **ช่วง:** EP `n` (เริ่ม 1) = [`cuts[n-2]` หรือ 0, `cuts[n-1]` หรือความยาวคลิป) — ปลายเปิด
- **บรรทัดของ EP** = บรรทัด Transcript ที่ `start_s ≤ line.start < end_s`; บรรทัดที่เริ่มหลังความยาวคลิปอยู่ใน EP สุดท้าย
- **Shot ของ EP** = Shot ที่ `shot.start < end_s` และ `shot.end > start_s`; ภาพเล็กของ EP = Shot ที่ `start == start_s`
- **lock:** ทุกการอ่าน-แก้-เขียนไฟล์นี้อยู่ใต้ lock เดียวของ `backend.gpu` พร้อมเช็คว่าคลิปยังมีและบรรยายฉากแล้ว; `PUT` ระหว่าง Describe job, Transcribe job หรือ Draft job ของคลิปนั้น → `409` `clip_busy`; ระหว่างลบคลิป รอจนลบเสร็จแล้ว `404` `not_found` (D71, D77)
- **ไฟล์เสีย:** อ่านไม่ได้ หรือไม่ผ่านกฎเดียวกับ `PUT` (รวม `cuts` ที่ไม่ใช่เวลาเริ่มของ Shot แล้ว) → log เหตุผล ถือว่าไม่มีไฟล์ และตัดใหม่ตาม `ep_minutes` (D71)
- **ลบ:** Describe job ลบไฟล์ในข้อ 7 ใต้ lock เดียวกับการสลับ folder Shot; ลบ Temp clip ลบตามลำดับ mp4 → Shot → ไฟล์การตัด → json → Spoil draft (json ไปหลังสุดของคลิป: ลบค้างกลางทาง start ครั้งหน้าลบที่เหลือ — spoil D15, D23, D80); start backend ลบไฟล์การตัดของ id ที่ไม่มี Temp clip หรือไม่มี `shots.json` (D71)

### Spoil draft

เก็บใน `media/spoil-maker/draft.json` เขียนผ่าน `.tmp` แล้ว rename ทุกครั้งที่แก้ (D28). เสียงของประโยคอยู่ใน `media/spoil-maker/draft-audio/{sentence_id}.wav`. รูปของไฟล์คือส่วนหนึ่งของการตัดสินใจ:

```json
{
  "version": 2,
  "clip_id": "abc123",
  "ep": { "n": 2, "start_s": 1795.4, "end_s": 3600.0 },
  "style": "drama",
  "layout": "B",
  "target_s": 60,
  "voice_id": "v_8f2c01ab",
  "original_volume": 20,
  "top_text": "คดีที่หลอนที่สุดในโคนัน",
  "sentences": [
    {
      "id": "s_01ab9c3d",
      "text": "ชายคนหนึ่งตื่นมาในห้องที่ไม่รู้จัก",
      "refs": [{ "clip_id": "abc123", "line": 412 }],
      "shots": [{ "clip_id": "abc123", "n": 531 }, { "clip_id": "abc123", "n": 532 }],
      "edited": false,
      "audio": { "tts_text": "ชายคนหนึ่งตื่นมาในห้องที่ไม่รู้จัก", "voice_id": "v_8f2c01ab", "duration_s": 3.4 }
    }
  ]
}
```

- `refs[].line` คือ index ของบรรทัดใน Transcript ของคลิปนั้น
- `shots` มี 2 ช่องเสมอ; ช่องว่างเป็น `null`
- `edited` เป็น `true` เมื่อ `PATCH /draft/sentences/{sid}` ทำให้ `text` (หลังทำความสะอาด) ต่างจากที่เก็บ หรือแทรกประโยคเอง; Draft job ตั้ง `false`; ไม่เปลี่ยนเมื่อแก้แค่ `shots` หรือส่งข้อความเดิม; แก้แล้วพิมพ์กลับเป็นข้อความเดิมยังเป็น `true`; ไฟล์ที่ไม่มี `edited` อ่านเป็น `false` (D74, D76)
- `audio` เป็น `null` เมื่อยังไม่มีเสียง
- `refs[].clip_id` และ `shots[].clip_id` เท่ากับ `clip_id` ของ draft เสมอ (เก็บรูปเดิมไว้ให้โค้ดเดิมใช้ได้, D70)
- `ep` คือช่วงของ EP ตอนร่าง; แก้การตัด EP ภายหลังไม่กระทบ draft (D70)
- `version` อื่นที่ไม่ใช่ 2 (รวม 1 ของแบบหลายคลิป D5) → ถือว่าไม่มี Spoil draft

สถานะของประโยค คำนวณตอนอ่าน ไม่เก็บ (D30):

| สถานะ | เมื่อ | render |
|---|---|---|
| `no_shot` | ช่อง `shots` ใดเป็น `null` | ไม่ได้ |
| `no_audio` | `audio` เป็น `null` | สร้างให้ก่อน |
| `stale_audio` | `audio.tts_text` ไม่ตรงกับข้อความที่แปลงตัวเลขแล้วตอนนี้ หรือ `audio.voice_id` ไม่ตรง `voice_id` ของ draft | สร้างให้ก่อน |
| `ready` | อื่นๆ | ได้ |

- เรียงสถานะตามตาราง: ประโยคที่ทั้งไม่มี Shot และไม่มีเสียงเป็น `no_shot`
- เปลี่ยน Saved voice ของ draft → ทุกประโยคที่มีเสียงเป็น `stale_audio`
- ความยาวประมาณรวม: ประโยค `ready` ใช้ `duration_s`; อื่นๆ ใช้ตัวอักษรหลังแปลงหาร `chars_per_s` ของ Saved voice (D30, D35)
- ลบประโยค ลบไฟล์เสียงของประโยคนั้น
- ทุกการอ่าน-แก้-เขียน `draft.json` ทั้งจาก API และจากงาน อยู่ใต้ lock เดียวของ `backend.gpu`; การเช็ค `draft_locked` และการเริ่มงานอยู่ใต้ lock เดียวกัน (D51)
- แก้ draft ระหว่าง Draft job, Voice job `sentences` หรือ Render job ช่วง `voicing` → `409` `draft_locked`
- `draft.json` อ่านไม่ได้ หรืออ้าง Temp clip ที่ไม่มีแล้ว → ถือว่าไม่มี Spoil draft และ log เหตุผล

### Draft job

เริ่มเมื่อผู้ใช้กดร่างบท (D25). ขั้นตอน:

1. เช็คคำขอตามลำดับ:
   1. `clip_id` ถอดแล้วและบรรยายฉากแล้ว → ไม่ใช่ `400` `clip_not_ready` (D16); `ep` `{n, start_s, end_s}` ตรงกับ EP `n` ของการตัดตอนนี้ (ต่างกันไม่เกิน 0.01 วินาที) → เลข `n` ไม่มี `400` `invalid_episodes`, ช่วงไม่ตรง `409` `episodes_changed` (D71); EP มีบรรทัด Transcript อย่างน้อย 1 บรรทัด → ไม่ใช่ `400` `ep_empty` (D71)
   2. `style` และ `layout` อยู่ในตาราง → ไม่ใช่ `400` `invalid_request`
   3. `target_s` จำนวนเต็ม 30–180 → ไม่ใช่ `400` `invalid_target` (D39)
   4. Saved voice มีอยู่ → ไม่ใช่ `400` `voice_not_found`
   5. token ของบรรทัดใน EP (ข้อความที่แก้แล้ว, D54) ไม่เกิน 32,000 → ไม่ใช่ `400` `transcript_too_long` พร้อม `tokens` (D46)
   6. มี Spoil draft อยู่และ `replace` ไม่เป็น `true` → `409` `draft_exists` (D28)
   7. แถว Status check แล้วจองช่อง GPU
2. state `writing` (ไม่มี %): process ลูกโหลด Qwen แล้วสั่งร่างบทจากบรรทัดของ EP (D18, D70):
   - แต่ละบรรทัดส่งเป็น `[{line} {hh:mm:ss}] {text}` (`text` ที่แก้แล้ว, D54) โดย `line` คือ index ใน Transcript ทั้งคลิป
   - คำสั่งบอกว่าทุกประโยคเล่าต่อจากประโยคก่อนเป็นเรื่องเดียว (D72), สไตล์ (ตารางสไตล์), ภาษาไทย (D11), จำนวนตัวอักษรเป้าหมาย `target_s × chars_per_s`, จำนวนประโยคเป้าหมาย `round(target_s / 4)`, ให้แต่ละประโยคอ้าง 1–3 id บรรทัด, และให้เขียน `top_text` เมื่อ layout เป็น A หรือ C (D19)
   - คำตอบเป็น JSON `{"top_text": "...", "sentences": [{"text": "...", "refs": ["412"]}]}`
3. ตรวจผล: JSON อ่านได้ และตัวอักษรรวม (หลังแปลงตัวเลข) อยู่ใน ±25% ของเป้าหมาย; ไม่ผ่านหรือเกิน timeout สั่งใหม่ได้อีก 2 ครั้ง (รวม 3, D18). ครบ 3 ครั้ง: ใช้ผลล่าสุดที่ JSON อ่านได้; ไม่มีเลย → `failed` `draft_failed`
4. ทำความสะอาด: ลบอักษรจีน ญี่ปุ่น เกาหลี (Unicode Han, Hiragana, Katakana, Hangul) ออกจากข้อความ (D18); id บรรทัดที่ไม่มีจริงหรืออยู่นอก EP ถูกตัดออกจาก `refs` และเก็บแค่ 3 ตัวแรก (D61); ประโยคที่ว่างหลังทำความสะอาดถูกตัดทิ้ง
5. state `polishing` (ไม่มี %): เรียบเรียง (ด้านล่าง) ทุกประโยค (D72)
6. state `matching` (`done` / `total` ประโยค): ต่อประโยคที่มี `refs` (D18):
   1. ช่วง = [เวลาเริ่มต่ำสุดของ refs − 30, เวลาจบสูงสุด + 30] ตัดให้อยู่ในช่วงของ EP (D70)
   2. ส่ง Shot ของคลิปที่ทับช่วงนั้นพร้อม Shot description ให้ LLM เลือก 2 Shot — ไม่เกิน 40 Shot ที่ใกล้เวลาเริ่มของ ref แรกที่สุด (D61); คำตอบเป็น JSON `{"shots": [31, 32]}`
   3. เลขที่ไม่อยู่ใน Shot ที่ส่งไป หรือ JSON พัง → ใช้ 2 Shot ในนั้นที่ใกล้เวลาเริ่มของ ref แรกที่สุด
   4. ช่วงมี Shot เดียว → ใช้ Shot นั้นทั้งสองช่อง
   5. ประโยคที่ไม่มี `refs` → `shots` เป็น `[null, null]`
7. เขียน Spoil draft ใหม่ทับของเดิม ลบ `draft-audio/` เดิม (D28); ทุกประโยค `edited` `false`; `original_volume` มาจากค่าที่จำไว้ (D40); `last_voice_id` ใน settings เป็น `voice_id` นี้
8. คืนช่อง GPU

ให้ AI เลือก Shot ใหม่ของหนึ่งประโยค (D25): Draft job `kind: "pick"` ทำเฉพาะข้อ 6 (state `matching`) กับประโยคนั้นจากข้อความปัจจุบัน แล้วเขียนเฉพาะ `shots` ของประโยคนั้น. ประโยคที่ไม่มี `refs` → `400` `no_refs` (D27).

เรียบเรียง (D72, D73, D74, D76):
- **คำสั่ง:** สไตล์, ภาษาไทย, `top_text` (ไม่แก้ ให้เรื่องเปิดต่อจากมัน), บททั้งบทเป็นรายการ `[{i}] {text}` ตามลำดับ (`i` เริ่ม 0) แต่ละประโยคตามด้วยบรรทัด Transcript ที่อ้าง (`text` ที่แก้แล้ว) เป็นบริบท; ประโยค fixed ทำเครื่องหมาย "fixed" — fixed = `edited` เมื่อ `include_edited` ไม่เป็น `true` (D74, D75)
- ให้เขียนใหม่เฉพาะประโยคที่ไม่ fixed ให้เล่าต่อจากประโยคก่อนและเข้ากับประโยคถัดไป ด้วยคำเชื่อมเท่าที่จำเป็น; ห้ามเพิ่มเรื่องที่ไม่อยู่ในบรรทัดที่อ้าง; ประโยคที่ไม่มีบรรทัดที่อ้างคงความหมายเดิม แก้แค่รอยต่อ; ห้ามรวม แยก หรือสลับประโยค; ความยาวแต่ละประโยคใกล้เดิม
- **คำตอบ:** JSON `{"sentences": [{"i": 0, "text": "..."}]}` เฉพาะ `i` ที่ไม่ fixed; จับคู่ด้วย `i` — `i` ที่ไม่รู้จัก ซ้ำ หรือ fixed และ `text` ที่ไม่ใช่ string ถูกทิ้ง (ประโยคนั้นใช้ข้อความเดิม)
- **ตรวจผลต่อประโยค:** ทำความสะอาดแบบข้อ 4; ว่างหลังทำความสะอาด หรือ `thai.letters(thai.spoken(text))` ต่างจากของเดิมเกิน ±50% → ใช้ข้อความเดิมของประโยคนั้น
- **ตรวจผลทั้งบท** (ไม่ผ่าน = หนึ่งครั้งที่ไม่ผ่าน): JSON อ่านไม่ได้; ได้ `i` ที่ใช้ได้ไม่ถึงครึ่งของที่ขอ; ตัวอักษรรวมหลังเรียบเรียงนอก ±25% ของเป้าหมาย (`kind: "draft"`) หรือมากกว่ารวมก่อนเรียบเรียงเกิน 15% (`kind: "polish"`)
- **สั่งใหม่:** รวม 2 ครั้ง; timeout นับเป็นหนึ่งครั้งที่ไม่ผ่าน: process ลูกถูก terminate แล้วเริ่มใหม่ (แบบร่างบท) — กรณีแย่สุดเพิ่มราว 10 นาทีกับโหลดโมเดลใหม่
- **ไม่ผ่านทั้ง 2 ครั้ง:** `kind: "draft"` ใช้ข้อความเดิมทั้งบท งานไปต่อ (log เฉพาะ code และจำนวน ไม่มีข้อความบท); `kind: "polish"` → `failed` `polish_failed` และ draft ไม่เปลี่ยน
- `refs`, `shots`, `id`, `audio`, `top_text` ไม่เปลี่ยน; `edited` ไม่เปลี่ยน ยกเว้นประโยคที่ `include_edited` ทำให้ถูกเรียบเรียง → `false` (D75); ข้อความที่เปลี่ยนทำให้ประโยคที่มีเสียงเป็น `stale_audio` เอง (Spoil draft › สถานะ)
- job `done` ของ `kind: "polish"` มี `done` = จำนวนประโยคที่ข้อความเปลี่ยน, `total` = จำนวนที่ขอ (D76)

เรียบเรียงใหม่ (D72, D74, D75, D76): Draft job `kind: "polish"` `include_edited` (boolean ไม่มี = `false`) ทำเฉพาะขั้นเรียบเรียงกับ Spoil draft ปัจจุบัน แล้วเขียน `text` (และ `edited`) ของประโยคที่เปลี่ยน. เช็คตามลำดับใต้ lock ของ draft: ไม่มี Spoil draft `404` `no_draft`; `include_edited` ไม่ใช่ boolean `400` `invalid_request`; ไม่มีประโยคให้เรียบเรียง (draft ว่าง หรือทุกประโยค fixed) `400` `nothing_to_polish`; แถว Status check; `draft_locked`, `gpu_busy`; จองช่อง GPU ด้วย `locks_draft` และคลิปของ draft (คลิปเป็น `clip_busy` ระหว่างงาน เหมือน Draft job). `include_edited` ใน `kind` อื่นถูกเมิน. ยกเลิก crash หรือ timeout → draft ไม่เปลี่ยน.

- ยกเลิกหรือ crash ระหว่างร่าง: Spoil draft เดิมยังอยู่ไม่เปลี่ยน
- `failed` `error.code`: `draft_failed`, `polish_failed` (`kind: "polish"`), `crashed`, `model_failed`, `internal`
- `top_text` ว่างใน layout A หรือ C ไม่วาดอะไร (D19); เปลี่ยน layout หลังร่างไม่สั่ง LLM ใหม่

ค่าการสร้างข้อความ (D51):

| ขั้น | thinking | `temperature` | `max_tokens` | timeout ต่อครั้ง |
|---|---|---|---|---|
| ร่างบท | ปิด | 0.3 (D61) | `2 × ตัวอักษรเป้าหมาย + 1,000` | 10 นาที |
| เรียบเรียง | ปิด | 0.3 | `2 × ตัวอักษรของบท + 1,000` | 5 นาที |
| เลือก Shot | ปิด | 0 | 64 | 60 วินาที |
| บรรยายภาพ (Describe job) | ปิด | 0 | 80 | 60 วินาที |

- เลือก Shot หรือบรรยายภาพเกิน timeout: process ลูกถูก terminate, งาน `failed` `model_failed`
- ร่างบทเกิน timeout นับเป็นหนึ่งครั้งที่ไม่ผ่านของข้อ 3: process ลูกถูก terminate แล้วเริ่มใหม่

สไตล์ (D7, D8):

| `style` | ชื่อบนจอ | วิธีเล่าในคำสั่ง | layout ตั้งต้น |
|---|---|---|---|
| `fast` | ปั่นตัดเร็ว | ประโยคสั้น ตลก เร็ว เล่าเหตุการณ์เด่น | A |
| `drama` | เล่าละครหักมุม | hook, เรื่อง, หักมุม, แรงจูงใจ, คำถามชวนคอมเมนต์ท้ายคลิป | B |
| `chrono` | เล่าตามลำดับ | เล่าทีละฉากตามเวลา มีบทพูดตัวละครแทรกได้ | C |

### Voice job

งานสร้างเสียงทุกแบบใช้ slot เดียวกัน (ADR-0010) และ process ลูก (ADR-0012):

| `kind` | body | ทำอะไร | ผล |
|---|---|---|---|
| `design_preview` | `{gender, age, pitch, speed}` | ข้อ 2 ของออกแบบเสียง | preview ใน `.pending/` |
| `sentences` | `{sentence_ids}` | สร้างเสียงของประโยคที่ให้มา | `draft-audio/{id}.wav` และ `audio` ของประโยค |

- ค่าที่ไม่อยู่ในรายการของออกแบบเสียง หรือ speed นอก 0.8–1.2 → `400` `invalid_voice`
- `sentences` แปลงตัวเลขก่อนส่ง (ตัวเลขเป็นคำ) แล้วใช้ clone prompt, speed ของ Saved voice และ `num_step` 16 (D35, D36, D37)
- process ลูกส่งเสียงของแต่ละประโยคกลับผ่าน queue; thread ของ backend เขียน wav และ `audio` ของประโยคนั้นทันที: ยกเลิกกลางทางเก็บประโยคที่เสร็จแล้วไว้
- ปุ่ม "สร้างเสียงทั้งหมด" ส่งทุกประโยคที่ไม่ใช่ `ready`; ปุ่มของประโยคส่ง id เดียวและสร้างใหม่แม้ `ready` (D30)
- id ที่ไม่มีใน draft → `400` `invalid_request`
- `failed` `error.code`: `crashed`, `model_failed`, `internal`

### ตัวเลขเป็นคำ

`backend.spoil_maker.thai` แปลงข้อความก่อนส่ง OmniVoice เท่านั้น (D36). ลำดับ:

1. เลขไทย `๐–๙` เป็น `0–9` (D44)
2. ตัดจุลภาคระหว่างหลัก: `114,000` → `114000` (D44)
3. `{h}:{mm}` → `{h}นาฬิกา{mm}นาที`; `mm` เป็น `00` → `{h}นาฬิกา` (D44); `น.` ที่ตามหลังเวลาถูกตัด และ `{h}.{mm} น.` เป็นเวลาเช่นกัน: `10.30 น.` → `สิบนาฬิกาสามสิบนาที` (D63)
4. `{n}%` → `{n}เปอร์เซ็นต์` (D44)
5. `{a}.{b}` → `{a}จุด` แล้วอ่าน `b` ทีละหลัก: `3.25` → `สามจุดสองห้า` (D44)
6. กลุ่มตัวเลขที่เหลือแต่ละกลุ่มอ่านเป็นจำนวนเต็ม: `1968` → `หนึ่งพันเก้าร้อยหกสิบแปด`, `1/2` → `หนึ่ง/สอง` (D36, D44)

- จำนวนเต็มอ่านตามหลักไทย: `เอ็ด` ที่หลักหน่วยเมื่อมีหลักสิบขึ้นไป (`21` → `ยี่สิบเอ็ด`, `101` → `หนึ่งร้อยเอ็ด`), `ยี่สิบ`, `สิบ` แทน `หนึ่งสิบ`, หลักล้านซ้ำ (`1000000000000` → `หนึ่งล้านล้าน`)
- เลขที่ขึ้นต้นด้วย `0` ยาวกว่าหนึ่งหลัก (`007`) อ่านทีละหลัก
- บท ซับ และ `.srt` ไม่ผ่านตัวแปลง (D36)

### Render job

เริ่มเมื่อผู้ใช้กด render. ขั้นตอน:

1. เช็คคำขอตามลำดับ: มี Spoil draft → ไม่มี `404` `no_draft`; ไม่มีประโยค `no_shot` → มี `400` `missing_shots` พร้อม `sentence_ids`; ที่ว่างดิสก์ ≥ 1 GiB → ไม่ถึง `507` `disk_full`; แถว Status check
2. มีประโยค `no_audio` หรือ `stale_audio` → จองช่อง GPU แล้ว state `voicing` (`done` / `total` ประโยค): สร้างเสียงแบบ Voice job `sentences` (D30) แล้วคืนช่อง GPU; ไม่มีเลยข้ามขั้นนี้
3. state `rendering` (`percent` จาก `-progress` ของ ffmpeg):
   1. timeline: ประโยคเรียงต่อกันไม่มีช่วงเงียบเพิ่ม; ประโยคยาว `N` = `audio.duration_s`; Shot แรกเล่นจากต้น Shot `N/2` วินาที, Shot ที่สอง `N/2` วินาที (D31)
   2. Shot ที่เวลาเลยท้ายต้นฉบับ: ค้างเฟรมสุดท้ายจนครบ (D45)
   3. ตัดแต่ละช่วงเป็นไฟล์กลางใน `media/spoil-maker/.render/` ขนาด 1080×1920 30 fps ตาม layout (ข้อความบนวิดีโอ) พร้อมเสียงต้นฉบับคูณ `original_volume / 100`; 0 = ไม่มีเสียงต้นฉบับ (D9, D40)
   4. ต่อไฟล์กลางทั้งหมด, ผสมเสียงบรรยายที่ต่อกันแล้วด้วย `amix` (`normalize=0`), วาดข้อความจากไฟล์ ASS แล้ว encode `libx264` `crf 20` `yuv420p`, `aac` 192 kbps 48 kHz, `+faststart`
4. เขียน `media/spoil-maker/renders/{YYYYMMDD-HHMMSS}.mp4`, `.srt` และ `.json` ผ่าน `.partial` แล้ว rename (D42); ลบ `.render/`

- `.srt`: หนึ่ง cue ต่อประโยค ข้อความตามที่เขียน เวลาตาม timeline (D10, D36)
- `{name}.json`: `created_at`, `duration_s` (อ่านจาก ffmpeg ตอนเขียน), `sources` รายการชื่อ Temp clip หนึ่งชื่อ (legal 1), `clip_id`, `ep`, `start_s`, `end_s` ของ draft (D70); ไฟล์เก่าที่ไม่มี `ep` แสดงโดยไม่มี "EP {n}"
- render ใช้ค่าของ draft ณ ตอนเริ่ม `rendering`; แก้ draft ระหว่าง `rendering` ได้และไม่มีผลกับไฟล์นี้
- ยกเลิกระหว่าง `voicing`: เสียงที่เสร็จแล้วอยู่ใน Spoil draft; ระหว่าง `rendering`: ฆ่า ffmpeg ลบ `.partial` และ `.render/`
- `failed` `error.code`: `ffmpeg_failed` (พร้อมท้าย stderr 20 บรรทัดใน log), `crashed`, `model_failed`, `internal`
- ผล render ไม่ผูกกับ Spoil draft: ร่างใหม่หรือลบคลิปไม่ลบผล render (D42)
- รายการผล render อ่านจาก folder: ชุดที่มีครบ mp4, `.srt`, `.json` และไม่มี `.partial`

### ข้อความบนวิดีโอ

ทุกข้อความวาดด้วย libass จากไฟล์ ASS หนึ่งไฟล์ต่อ render, font `Kanit Bold` จาก `models/fonts/kanit/` (D21). ค่าตายตัวต่อ layout (D22):

| layout | ภาพต้นฉบับ | ข้อความค้างด้านบน | ซับ |
|---|---|---|---|
| A | พื้น: ต้นฉบับขยายเต็ม 1080×1920 ครอปกลาง เบลอเท่า `gblur` sigma 30 (ทำที่ 270×480 sigma 7.5 แล้วขยาย, D63); บน: ต้นฉบับสูง 1350 ครอปกลางกว้าง 1080 ที่ y 285 | hook: 76 px ขาว `#FFFFFF` ขอบดำ `#000000` 6 px กึ่งกลาง บนสุดที่ y 70 | ท่อนสั้น: 92 px ขาว ขอบดำ 8 px กึ่งกลางที่ y 1300 (D20) |
| B | พื้นดำ `#000000`; ต้นฉบับ 1080×608 ที่ y 656 | — (D19) | ประโยค: 56 px ขาว ไม่มีขอบ กึ่งกลาง บนสุดที่ y 1300 สูงสุด 2 บรรทัด |
| C | พื้นดำ; ต้นฉบับ 1080×608 ที่ y 420 | ชื่อตอน: 80 px เหลือง `#FFD400` ขอบแดง `#D7262E` 6 px กึ่งกลาง บนสุดที่ y 160 | — |

- ต้นฉบับที่ไม่ใช่ 16:9 ขยายให้พอดีกรอบโดยคงสัดส่วน และเติมพื้นตาม layout
- ก่อนเขียน ASS ทุกข้อความ (บท, `top_text`, ลายน้ำ): แทนขึ้นบรรทัดใหม่ด้วยช่องว่าง, escape `\`, `{`, `}` (D51)
- ตัดบรรทัดที่ขอบคำของ `newmm` เมื่อตัวอักษรที่กินที่ (ไม่นับสระบนล่างและวรรณยุกต์) เกินต่อบรรทัด: hook 18, ชื่อตอน 20, ซับ A 15, ซับ B 28
- ช่อง `top_text` รับไม่เกิน 40 ตัวอักษรที่กินที่; วาดทุกบรรทัดที่ตัดได้
- ซับ A: ตัดประโยคด้วย `newmm` ไม่นับช่องว่าง, รวมคำเป็นท่อนละ 2–4 คำ ปิดท่อนเมื่อครบ 4 คำ หรือคำถัดไปทำให้เกิน 15 ตัวอักษรที่กินที่; คำเดียวที่ยาวเกินเป็นหนึ่งท่อน; เวลาของประโยคแบ่งให้ท่อนตามสัดส่วนตัวอักษรที่กินที่ (D20)
- ซับ B ที่เกิน 2 บรรทัด: แบ่งเป็นชุดละ 2 บรรทัด เวลาแบ่งตามสัดส่วนตัวอักษรแบบเดียวกับซับ A
- ลายน้ำ (D41, D51): ขาว ขอบดำ 3 px ทึบ 80% ทุก layout; เล็ก 36 px, กลาง 52 px; x 60, 540 หรือ 1020 และ y บน 60 หรือล่าง 1860 ยึดมุมตามตำแหน่ง (`\an7`, `\an8`, `\an9`, `\an1`, `\an2`, `\an3`); แสดงตลอดคลิป

### ค่าที่จำไว้

`media/spoil-maker/settings.json` (D45):

| ฟิลด์ | ค่า | ค่าตั้งต้น |
|---|---|---|
| `watermarks` | รายการ `{text, position, size, enabled}`; `enabled` boolean ไม่มีอ่านเป็น `true`, ปิดแล้วจำไว้แต่ render ไม่วาด และยังนับในสูงสุด (D64); `position` หนึ่งใน `top_left`, `top_center`, `top_right`, `bottom_left`, `bottom_center`, `bottom_right`; `size` `small` หรือ `medium`; `text` 1–40 ตัวอักษร; สูงสุด 6 อัน | `[]` (D41) |
| `original_volume` | 0–100 ทีละ 5 | 20 (D40) |
| `last_voice_id` | id ของ Saved voice ที่ใช้ร่างล่าสุด | `null` |
| `ep_minutes` | 5–60 ทีละ 5 (D69) | 30 |

- ลายน้ำเป็นของทุกคลิป ไม่เก็บใน Spoil draft: แก้ลายน้ำแล้ว render ครั้งถัดไปใช้ค่าใหม่
- ลายน้ำ `top_center` ที่เปิดอยู่ทับ hook (A) หรือชื่อตอน (C) ที่ไม่ว่างได้: แอปไม่กัน แต่หน้าตรวจแก้เตือน (D41, D64)
- `PATCH /draft` ที่แก้ `original_volume` เขียนลง settings ด้วย (D40)
- ค่าไม่ตรงตาราง → `400` `invalid_settings`
- ทุกการอ่าน-แก้-เขียน `settings.json` (`PATCH /settings`, `PATCH /draft`, Draft job, `PUT` การตัด EP) อยู่ใต้ lock เดียวและเขียนผ่าน `.tmp` แล้ว rename (D71)

### API

ทุก route อยู่ใต้ `/api/spoil-maker`. POST, PUT และ PATCH ต้องเป็น JSON (ADR-0013); ทุก request ผ่าน `TrustedHostMiddleware` (ADR-0011). Error เป็นรูปแบนเดียวกับ `ApiError` ของ spoil: `{"code", "message", ...extra}`; ที่ framework ตอบเองก็เช่นกัน — path ไม่มี route `404` `not_found`, method ผิด `405` `method_not_allowed`, body ไม่ใช่ object `400` `invalid_request` (D56, D63).

| Method | Path | ทำอะไร | ตอบ |
|---|---|---|---|
| `GET` | `/clips/{id}/shots` | `{clip_id, shots}` ของคลิป | `200`; ไม่ได้บรรยายฉาก `404` `not_described` |
| `GET` | `/clips/{id}/shots/{n}.jpg` | ภาพเล็กของ Shot | `200` `image/jpeg`; `404` `not_found` |
| `POST` | `/describes` | `{clip_id, confirm_draft_loss?}` เริ่ม Describe job | `202` job; `409` `busy`, `gpu_busy`, `in_draft`, `clip_busy`; `503` `not_ready`; `404` `not_found` |
| `GET` | `/describes/current` | งานล่าสุดหรือ `null` | `200` |
| `DELETE` | `/describes/current` | ยกเลิก | `202` job; ไม่มีงานค้าง `404` `not_found` |
| `GET` | `/clips/{id}/episodes` | การตัด EP ของคลิป (EP) | `200` `{clip_id, minutes, custom, episodes: [{n, start_s, end_s, thumb_shot, lines, tokens, renders, in_draft}], limit: 32000, tokens_not_ready}` โดย `thumb_shot` = ภาพเล็กของ EP, `lines` จำนวนบรรทัดใน EP, `tokens` ของบรรทัดใน EP (D46, D54) หรือ `null` เมื่อไม่มี tokenizer ของ Qwen (D60, D71) แล้ว `tokens_not_ready` เป็นข้อความ `not_ready` (ไม่งั้น `null`, D80), `renders` = จำนวนผล render ที่ `clip_id` ตรงและ `start_s` `end_s` ต่างไม่เกิน 0.01 วินาที, `in_draft` = Spoil draft ใช้คลิปนี้และช่วงตรงแบบเดียวกัน (D71); ยังไม่ถอดหรือบรรยายฉาก `400` `clip_not_ready` |
| `PUT` | `/clips/{id}/episodes` | `{minutes, cuts?}` ตั้งการตัด; ไม่มี `cuts` = ตัดตาม `minutes` (D66, D69) | `200` แบบ `GET`; `400` `invalid_episodes`, `clip_not_ready`; `409` `clip_busy` (EP › lock) |
| `GET` | `/voices` | `[{id, name, speed, chars_per_s, created_at, in_use}]` ใหม่สุดก่อน | `200` |
| `POST` | `/voices` | `{name}` บันทึก preview ล่าสุด | `201` voice; ไม่มี preview `409` `no_preview`; `400` `invalid_voice` |
| `PATCH` | `/voices/{id}` | `{name}` | `200` voice; `400` `invalid_voice`; `404` `not_found` |
| `DELETE` | `/voices/{id}` | ลบ | `204`; `409` `voice_in_use`; `404` `not_found` |
| `GET` | `/voices/{id}/sample.wav` | ประโยคตัวอย่าง | `200`; `404` `not_found` |
| `POST` | `/voice-jobs` | `{kind, ...}` ตาม Voice job | `202` job; `400` `invalid_voice`, `invalid_request`; `409` `busy`, `gpu_busy`, `draft_locked`; `503` `not_ready` |
| `GET` | `/voice-jobs/current` | งานล่าสุดหรือ `null` | `200` |
| `DELETE` | `/voice-jobs/current` | ยกเลิก | `202` job; `404` `not_found` |
| `GET` | `/voice-jobs/preview.wav` | preview ที่ยังไม่บันทึก | `200`; `404` `not_found` |
| `GET` | `/draft` | Spoil draft หรือ `null` (ด้านล่าง) | `200` |
| `PATCH` | `/draft` | `{top_text?, layout?, voice_id?, original_volume?}` | `200` draft; `400` `invalid_request`, `voice_not_found`; `409` `draft_locked`; `404` `no_draft` |
| `POST` | `/draft/sentences` | `{after_id: string \| null, text}` แทรกใต้ `after_id` หรือบนสุดเมื่อ `null` ไม่มี `refs` และ Shot (D27) | `201` draft; `400` `invalid_request`; `409` `draft_locked`; `404` `no_draft` |
| `PATCH` | `/draft/sentences/{sid}` | `{text?, shots?}` | `200` draft; `400` `invalid_shot`, `invalid_request`; `409` `draft_locked`; `404` `not_found` |
| `DELETE` | `/draft/sentences/{sid}` | ลบประโยค | `200` draft; `409` `draft_locked`; `404` `not_found` |
| `GET` | `/draft/sentences/{sid}/audio.wav` | เสียงของประโยค | `200` (`Cache-Control: no-store`, D63); `404` `not_found` |
| `POST` | `/draft-jobs` | `{kind: "draft", clip_id, ep: {n, start_s, end_s}, style, layout, target_s, voice_id, replace}` หรือ `{kind: "pick", sentence_id}` หรือ `{kind: "polish", include_edited?}` (D72, D75) | `202` job; `400` ตาม Draft job ข้อ 1, `no_refs`, `nothing_to_polish`; `404` `no_draft` (`polish`); `409` `draft_exists`, `episodes_changed`, `busy`, `gpu_busy`, `draft_locked`; `503` `not_ready` |
| `GET` | `/draft-jobs/current` | งานล่าสุดหรือ `null` | `200` |
| `DELETE` | `/draft-jobs/current` | ยกเลิก | `202` job; `404` `not_found` |
| `GET` | `/settings` | ค่าที่จำไว้ | `200` |
| `PATCH` | `/settings` | `{watermarks?, original_volume?}`; ลายน้ำแต่ละอัน `{text, position, size, enabled?}` (ไม่มี `enabled` = `true`, D64) | `200`; `400` `invalid_settings` |
| `POST` | `/renders` | `{}` เริ่ม Render job | `202` job; `400` `missing_shots`; `404` `no_draft`; `507` `disk_full`; `409` `busy`, `gpu_busy`; `503` `not_ready` |
| `GET` | `/renders/current` | งานล่าสุดหรือ `null` | `200` |
| `DELETE` | `/renders/current` | ยกเลิก | `202` job; `404` `not_found` |
| `GET` | `/renders` | `[{name, created_at, duration_s, size_bytes, sources, clip_id, ep}]` ใหม่สุดก่อน; ไฟล์เก่า `clip_id` และ `ep` เป็น `null` | `200` |
| `GET` | `/renders/{name}.mp4` | mp4 รองรับ `Range` | `200`, `206`; `404` `not_found` |
| `GET` | `/renders/{name}.srt` | `.srt` มี `Content-Disposition` | `200`; `404` `not_found` |
| `DELETE` | `/renders/{name}` | ลบ mp4, `.srt`, `.json` | `204`; `409` `in_use`; `404` `not_found` |

- `{name}` ต้องตรง `^\d{8}-\d{6}$`; `{id}` ตรงกฎ id ของ Temp clip ใน spoil; `{sid}` ตรง `^s_[0-9a-f]{8}$`; อื่นๆ `404` `not_found`
- `PATCH /draft/sentences/{sid}` ที่ `shots` ไม่ใช่ list ยาว 2 หรืออ้างคลิปอื่นนอกจาก `clip_id` หรือ `n` ที่ไม่มี หรือ Shot ที่ไม่ทับช่วงของ EP (D70) → `400` `invalid_shot`
- `PATCH /draft/sentences/{sid}` ที่แก้ `text` ไม่ลบไฟล์เสียง: สถานะเป็น `stale_audio` (D30); `text` ว่างหลังตัดช่องว่าง → `400` `invalid_request`
- spoil เปลี่ยน: `PATCH /api/spoil/clips/{id}/transcript/lines/{n}` body `{"text"}` แก้ข้อความบรรทัดที่ `n` (นับจาก 0) แล้วตั้ง `edited: true` เขียนแบบ `.tmp` แล้ว rename ใต้ lock ของงานถอด → `200` บรรทัดนั้น; `text` ว่างหลังตัดช่องว่าง `400` `invalid_request`; ไม่มีคลิป Transcript หรือบรรทัด `404` `not_found`; Transcribe job ของคลิปนั้นยังไม่จบ `409` `transcribing`; Draft job ที่ใช้คลิปนั้นยังไม่จบ `409` `clip_busy` (D54); `POST /api/spoil/transcriptions` ของคลิปที่มีบรรทัด `edited` ไม่มี `confirm_edit_loss: true` → `409` `has_edits` (D54); `GET /api/spoil/clips` เพิ่ม `described` และ `in_draft`; `POST /api/spoil/transcriptions` รับ `confirm_draft_loss?` และตอบ `409` `in_draft`, `clip_busy`, `gpu_busy`; `DELETE /api/spoil/clips/{id}` ตอบ `409` `clip_busy`

job object (ทุกชนิดมีฟิลด์เดียวกัน ฟิลด์ที่ไม่ใช้เป็น `null`):

```json
{
  "kind": "render",
  "state": "voicing",
  "clip_id": null,
  "percent": null,
  "done": 1,
  "total": 3,
  "error": null,
  "cancel_requested": false,
  "started_at": "2026-10-31T10:00:00+07:00",
  "order": null
}
```

- `done` และ `total` นับ Shot (`describing`) หรือประโยค (`matching`, `voicing`, Voice job `sentences`)
- `error` เป็น `{code, message}` เมื่อ `failed`
- `order` (D82): Draft job `kind: "draft"` เป็น `{clip_id, clip_title, ep: {n, start_s, end_s}, style, layout, target_s, voice_id}` ตามคำขอที่ผ่านข้อ 1 ของ Draft job (`clip_title` อ่านจาก Temp clip ตอนเริ่ม) ทั้งใน `202` และ `GET /draft-jobs/current` จนมีงานใหม่; งานอื่นเป็น `null`
- `kind` ของ Describe job เป็น `describe`; ของ Draft job เป็น `draft`, `pick` หรือ `polish` (state `writing`, `polishing`, `matching`); ของ Voice job เป็น `design_preview` หรือ `sentences`; ของ Render job เป็น `render`

`GET /draft` คืน `draft.json` พร้อมฟิลด์ที่คำนวณ:

| ฟิลด์ | อยู่ที่ | ค่า |
|---|---|---|
| `status` | แต่ละประโยค | `no_shot`, `no_audio`, `stale_audio`, `ready` |
| `estimated_s` | แต่ละประโยค | ความยาวจริงหรือประมาณ (Spoil draft) |
| `ref_lines` | แต่ละประโยค | `[{clip_id, line, start, end, text}]` ของ refs |
| `window` | แต่ละประโยค | `{clip_id, start, end}` ช่วง ±30 วินาทีที่ตัดให้อยู่ใน EP หรือ `null` (D70) |
| `clip_title` | draft | ชื่อ Temp clip ของ `clip_id` สำหรับตัวบอกขั้น (D68) |
| `estimated_total_s` | draft | ผลรวม `estimated_s` |
| `locked` | draft | `true` ระหว่างงานที่ทำให้ `draft_locked` |

### Frontend

- 3 tab: ติดตั้ง `#/setup`, คลิป `#/clips`, สปอย `#/spoil` (D53); tab สปอยมีขั้น `#/spoil` (เลือกคลิป), `#/spoil/review`, `#/spoil/renders` และหน้า `#/spoil/voices`; `useHash` (`tabOf`) จับ `#/spoil/` เป็น tab สปอย
- poll งานด้วย `usePollWhile` ของ spoil ทุก 1 วินาทีระหว่างงานค้าง
- เปิดหน้าตอนมีงานค้าง (`*/current` ไม่จบ) → แสดงความคืบหน้าของงานนั้น
- ตัวบอกขั้น (D68, D71): `SpoilMakerPage` เก็บ state ของ `GET /draft`, `GET /renders` และ `/draft-jobs/current`, `/voice-jobs/current` (`kind` `sentences`), `/renders/current` ร่วมกับทุกขั้น; poll ทุก 1 วินาทีขณะมีงานที่ state ไม่ใช่ `done`, `failed`, `cancelled`; หน้าใดเริ่มหรือยกเลิกงานแจ้ง `SpoilMakerPage` ให้อ่านใหม่และเริ่ม poll; งานเปลี่ยนจากรันเป็นจบ → อ่าน `/draft` และ `/renders` ใหม่
  - จุดหมุนเฉพาะงานที่ยังไม่จบ; `percent` เป็น `null` แสดง "render…"; Render job ช่วง `voicing` แสดง "render: สร้างเสียง x/y" ที่ขั้น 3; งาน `kind: "pick"` ไม่ทำให้ขั้น 2 เป็น "กำลังร่าง" แต่มีจุดหมุน; state `polishing` ของ `kind: "draft"` แสดง "กำลังเรียบเรียง" ที่ขั้น 2; `kind: "polish"` แสดง "กำลังเรียบเรียง" พร้อมจุดหมุนที่ขั้น 2 และเมื่อ `failed` แสดง "เรียบเรียงไม่สำเร็จ" (ไม่ใช่ "ร่างบทไม่สำเร็จ") (D76)
  - งานล่าสุด `failed`: ขั้นของงานนั้นแสดง "ร่างบทไม่สำเร็จ", "สร้างเสียงไม่สำเร็จ" หรือ "render ไม่สำเร็จ" จนเริ่มงานใหม่
- ขั้น 1: กดร่างรอ `PUT` การตัดที่ค้างอยู่ให้จบก่อนส่ง `POST /draft-jobs`; `409` `episodes_changed` → อ่านรายการ EP ใหม่และบอก "การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง"; เปลี่ยนความยาวต่อ EP ตอน `custom: true` → ยืนยันก่อนเพราะจุดตัดที่เลื่อนเองจะหาย; `tokens: null` → ปุ่มร่างกดไม่ได้พร้อม `tokens_not_ready`; ก่อนอ่านรายการ EP ตัวนับ token เป็น "— / —" (D80); EP ที่ `lines` 0 เลือกได้แต่ปุ่มร่างกดไม่ได้พร้อม "EP นี้ไม่มีบทพูด" (D71)
- ร่างบท (D81–D87): `POST /draft-jobs` `kind: "draft"` ตอบ `202` → เก็บ job ลง state ร่วมของ `SpoilMakerPage` ก่อน แล้วเปิด `#/spoil/review`; `409` `busy` → "มีงานร่างบทอยู่แล้ว" และอ่าน state ร่วมใหม่
  - ระหว่างงานยังไม่จบ ขั้น 2 แสดงการ์ดความคืบหน้าจาก current: `writing` = ขั้นเขียนบทกำลังทำ, `polishing` = เขียนบทเสร็จ เรียบเรียงกำลังทำ, `matching` = สองขั้นแรกเสร็จ "เลือกภาพ {done}/{total}"; แถบไม่มี % จนถึง `matching` แล้วเป็น `done`/`total` (`total` 0 → เต็ม)
  - ยกเลิก (D85): ส่ง `DELETE /draft-jobs/current`; ระหว่าง `cancel_requested: true` การ์ดแสดง "กำลังยกเลิก" ปุ่มกดไม่ได้; `404` → อ่าน current ใหม่; `cancelled` → เปิด `#/spoil`; จบ `done` → บทใหม่พร้อม Alert info "ยกเลิกไม่ทัน บทร่างเสร็จแล้ว"
  - ตัวบอกขั้นระหว่างงานยังไม่จบ: ขั้น 1 เป็น "{order.clip_title} · EP {order.ep.n}"
  - poll ล้มระหว่างการ์ดแสดง → ขั้น 2 แสดง offline แล้ว poll ใหม่เมื่อกลับมา; current เป็น `null` หรือไม่ใช่ `kind: "draft"` ขณะการ์ดแสดง (backend restart, ADR-0010) → "งานหยุดกลางทาง" กับ "กลับไปแก้ตั้งค่า"; `order` และ "ลองอีกครั้ง" ไม่รอด restart
  - ขั้น 1 ระหว่างงานยังไม่จบ: ค่าทุกช่องมาจาก `order` กดไม่ได้ ไม่มีปุ่มร่าง มี Alert info พร้อมลิงก์ `#/spoil/review`; คลิปของ `order` ที่ไม่อยู่ใน `GET /api/spoil/clips` แล้ว → แสดง `clip_title` ไม่มีรายการ EP; Saved voice ที่ไม่มีแล้ว → "เสียงถูกลบแล้ว"
  - `done` ขณะเปิดขั้น 2 → อ่าน `GET /draft` ใหม่แล้วแสดงบท; ขณะเปิดขั้นอื่น → ไม่ย้ายหน้า
  - `failed` → ขั้น 2 แสดง Alert error ตามตาราง error พร้อม "ลองอีกครั้ง" และ "กลับไปแก้ตั้งค่า" (`#/spoil`) เหนือบทเดิม (แก้ได้) หรือ "ยังไม่มีบท"; Alert หายเมื่อเริ่ม Draft job ใหม่เท่านั้น
  - "ลองอีกครั้ง" (D86, D87): `GET /draft` ไม่ใช่ `null` → คำยืนยันร่างทับแบบ D28 ก่อนทุกครั้ง แล้วส่ง `order` เดิมพร้อม `replace: true`; ไม่มี draft → ส่งเลย; ปุ่มกดไม่ได้ระหว่างรอคำตอบ; ถูกปฏิเสธ → ข้อความใน Alert เดิม, `episodes_changed`, `clip_not_ready`, `voice_not_found`, `ep_empty`, `transcript_too_long` มี "กลับไปแก้ตั้งค่า"; `gpu_busy`, `draft_locked`, `busy` อ่าน current ใหม่
  - ค่าของขั้น 1 (D87): ใช้ `order` เมื่อ Draft job ล่าสุดเป็น `kind: "draft"` และยังไม่จบ, `failed` หรือ `cancelled` จนเริ่ม Draft job ใหม่ชนิดใดก็ได้ (EP ที่ไม่อยู่ในการตัดตอนนี้แล้ว → EP แรก); นอกนั้นใช้ Spoil draft แล้วค่าตั้งต้น
- ขั้น 1 จำคลิปที่เลือกตาม `clip_id` ของ Spoil draft เมื่อมี (เว้นตอนใช้ `order` ด้านบน); เลื่อนจุดตัดบันทึกเมื่อ blur (`PUT /clips/{id}/episodes`)
- ระหว่าง `locked: true` ทุกช่องแก้ของหน้าตรวจแก้กดไม่ได้ (D51)
- ปุ่ม "เรียบเรียงใหม่" (D72, D75): เปิดกล่องเลือกก่อนส่ง — ช่องติ๊ก "เรียบเรียงประโยคที่แก้เองด้วย" (ตั้งต้นไม่ติ๊ก, แสดงเมื่อมีประโยค `edited`), "ประโยคที่เปลี่ยนต้องสร้างเสียงใหม่" เมื่อมีประโยคที่มีเสียง; ทุกประโยค `edited` และไม่ติ๊ก → ปุ่ม "เรียบเรียง" กดไม่ได้พร้อม "ทุกประโยคแก้เองแล้ว: ติ๊กเพื่อเรียบเรียงทับ"; ติ๊กแล้วเห็น "ข้อความที่แก้เอง {n} ประโยคจะถูกเขียนทับ ย้อนกลับไม่ได้"; กด "เรียบเรียง" รอการบันทึกประโยคที่ค้างให้จบ แล้วอ่าน `/draft` ใหม่ก่อนส่ง; ระหว่างงาน "กำลังเรียบเรียง" กับปุ่มยกเลิก; จบแล้วบอก "เรียบเรียง {done} ประโยค" หรือ "ไม่มีประโยคที่เปลี่ยน" เมื่อ 0; ประโยค `edited` มีป้าย "แก้เอง" (D74, D76)
- ตัวเลือก Shot เล่นช่วงด้วย `/api/spoil/clips/{id}/video` เดิมโดยตั้ง `currentTime` เป็น `start` แล้วหยุดที่ `end`
- ฟังเสียงของประโยคจาก `audio.wav` พร้อม query `?v={duration_s}` กัน cache ของ browser หลังสร้างใหม่; เสียงใหม่ที่ยาวเท่าเดิมได้ URL เดิม จึงตอบ `no-store` ด้วย (D63)
- ช่องข้อความของประโยคบันทึกเมื่อ blur หรือหยุดพิมพ์ 800 ms; ส่งทีละ request ต่อประโยค

ข้อความ error (ภาษาที่แอปแสดง):

| code | ข้อความ | ทางต่อ |
|---|---|---|
| `not_ready` | "ยังติดตั้งไม่ครบ: {rows}" | ลิงก์ไป Setup status (บอกให้รัน Setup script ใหม่) |
| `gpu_busy` | "รอให้งาน{running}เสร็จก่อน" โดย `running` เป็น "ถอดบทพูด", "บรรยายฉาก", "ร่างบท", "สร้างเสียง", "render" | — |
| `clip_busy` | "คลิปนี้กำลังถูกใช้ในงานอื่น" | — |
| `in_draft` | "คลิปนี้อยู่ใน Spoil draft: ทำต่อจะลบ Spoil draft" | ยืนยัน → ส่งซ้ำพร้อม `confirm_draft_loss: true` |
| `transcript_too_long` | "Transcript ของ EP นี้ {tokens} token เกิน 32,000" | ลดความยาวต่อ EP หรือเลื่อนจุดตัด |
| `invalid_episodes` | "ตัด EP แบบนี้ไม่ได้: ทุก EP ต้องยาวอย่างน้อย 1 นาทีและเรียงตามเวลา" | แก้เวลาจุดตัด |
| `episodes_changed` | "การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง" | อ่านรายการ EP ใหม่ |
| `ep_empty` | "EP นี้ไม่มีบทพูด" | เลือก EP อื่นหรือเลื่อนจุดตัด |
| `draft_failed` | "AI ร่างบทไม่สำเร็จ 3 ครั้ง" | กดร่างใหม่ |
| `nothing_to_polish` | "ทุกประโยคแก้เองแล้ว ไม่มีอะไรให้เรียบเรียง" | ติ๊ก "เรียบเรียงประโยคที่แก้เองด้วย" |
| `polish_failed` | "AI เรียบเรียงไม่สำเร็จ บทเดิมไม่เปลี่ยน" | กดเรียบเรียงใหม่ |
| `disk_full` | "ที่ว่างดิสก์ไม่ถึง 1 GiB" | ลบผล render เก่า |
| `has_edits` | "ถอดใหม่จะลบบทพูดที่แก้ไว้" | ยืนยัน → ส่งซ้ำพร้อม `confirm_edit_loss: true` (D54) |
| `ffmpeg_failed` | "render ไม่สำเร็จ" | กด render ใหม่ |
| `crashed`, `model_failed` | "งานหยุดกลางทาง" | กดใหม่ |
| `voice_in_use` | "เสียงนี้ใช้อยู่ใน Spoil draft หรืองานร่างบท" | — |
| `busy` (Draft job `kind: "draft"`) | "มีงานร่างบทอยู่แล้ว" | อ่าน state ร่วมใหม่ ขั้น 1 ล็อก (D87) |
| อื่นๆ | `message` จาก backend | — |

### Ops

- start backend: ลบ `media/temp/shots/.new-*/`, `media/temp/episodes/*.tmp`, ไฟล์การตัดของ id ที่ไม่มี Temp clip หรือ `shots.json` (D71), `media/spoil-maker/**/*.tmp`, `renders/*.partial`, `.render/`, `voices/.pending/`
- Temp clip ที่ startup ของ spoil ล้าง (mp4 ไม่มี json) ลบ `media/temp/shots/{id}/` ด้วย
- Describe job ของหนัง 96 นาทีใช้ราว 45 นาที (D18): ไม่มี resume
- ทุกงานหายเมื่อ backend restart (ADR-0010); ไฟล์ที่เขียนเสร็จแล้วอยู่
- log ของทุกงาน: เริ่ม, จบ, เวลา, error code; ไม่ log ข้อความบทหรือ Transcript
- ดิสก์: ภาพเล็กราว 15 MB ต่อหนัง 96 นาที; ผล render ราว 30–60 MB ต่อนาที ไม่ลบเอง (D42)
- ปิด feature: ไม่มีสวิตช์; ไม่ใช้ = ไม่กดปุ่ม. ไฟล์ทั้งหมดอยู่ใน `media/temp/shots/` และ `media/spoil-maker/` ลบ folder ได้โดยไม่กระทบ spoil

## Seams

สาม seam: API กับ worker ปลอมของโมเดลแต่ ffmpeg จริง, หน้าเว็บกับ fetch ปลอม, และโมเดลจริงบน Mac (D47, D51).

1. **Spoil-maker API** `/api/spoil-maker/*`, `/api/spoil/*` ด้วย `TestClient`, root ปลอมใน `tmp_path`, worker ปลอมของ LLM และ OmniVoice ที่จดข้อความที่ได้รับ, ffmpeg จริงกับคลิป 3 วินาทีที่ test สร้างด้วย `lavfi` (สีเปลี่ยนที่ 1 และ 2 วินาที, เสียง sine)
   - Describe:
     - `POST /describes` คลิปทดสอบ → poll จน `done`, `GET /clips/{id}/shots` มี 3 Shot ที่ `start` 0, 1, 2 (±0.1) และภาพเล็กกว้าง 320 ทุก Shot; `GET /api/spoil/clips` มี `described: true`
     - ตัวหาจุดตัดปลอมให้ช่วง 25 วินาที → 3 Shot ยาวเท่ากัน; ช่วง 0.5 วินาทีกลางคลิป → รวมเข้า Shot ก่อนหน้า
     - คลิปบรรยายฉากแล้ว บรรยายฉากใหม่แล้วยกเลิกระหว่าง `describing` → `cancelled`, Shot เดิมและภาพเล็กเดิมยังอยู่, ไม่มี `.new-{id}/`
     - `GET /api/spoil/clips/{id}/thumbnail` หลังบรรยายฉาก → ยังเป็น thumbnail เดิมของคลิป
   - ช่อง GPU และคลิป:
     - `POST /describes` ระหว่าง Transcribe job ยังไม่จบ → `409` `gpu_busy` `running: "transcribe"`; `POST /api/spoil/transcriptions` ระหว่าง Describe job → `409` `gpu_busy`
     - `POST /api/spoil/downloads` ระหว่าง Describe job → `202`
     - `DELETE /api/spoil/clips/{id}` ระหว่าง Describe job ของคลิปนั้น → `409` `clip_busy`; ระหว่าง Render job ช่วง `voicing` ของ draft ที่ใช้คลิปนั้น → `409` `clip_busy`
     - คลิปใน Spoil draft: `POST /describes` ไม่มี `confirm_draft_loss` → `409` `in_draft`; มี → `202` แล้วหลัง `done` `GET /draft` เป็น `null`; ยกเลิกแทน → `GET /draft` ยังอยู่
     - `POST /api/spoil/transcriptions` ของคลิปใน Spoil draft ไม่มี `confirm_draft_loss` → `409` `in_draft`
     - `PATCH /api/spoil/clips/{id}/transcript/lines/0` ระหว่าง Draft job ที่ใช้คลิปนั้น → `409` `clip_busy`; คลิปใน Spoil draft ที่ไม่มีงาน → `200` (D54)
     - render ที่ไม่มีประโยคขาดเสียง ระหว่าง `rendering` → `POST /describes` ของคลิปอื่น `202`
   - Draft:
     - คลิปถอดแล้วแต่ไม่ได้บรรยายฉาก → `400` `clip_not_ready` พร้อม id นั้น
     - `target_s` 29, 181, 60.5 → `400` `invalid_target`; `style` `x` → `400` `invalid_request`
     - token ปลอมของ EP 32,001 → `400` `transcript_too_long`; `GET /clips/{id}/episodes` คืน `tokens` 32,001 ใน EP นั้น
     - `POST /draft-jobs` `kind: "draft"` → `202` และ `GET /draft-jobs/current` มี `order` ตรงกับคำขอพร้อม `clip_title` ของคลิป ทั้งระหว่าง `writing` และหลัง `failed`; `kind: "pick"` และ `"polish"` มี `order` `null` (D82)
   - EP (คลิปทดสอบ 3 วินาทีไม่พอ: ใช้ไฟล์ Shot ปลอมของคลิปยาว 3,600 วินาทีที่ Shot เริ่มทุก 7 วินาที):
     - ไม่มีไฟล์การตัด `ep_minutes` 30 → 2 EP จุดตัดที่ 1,799 (Shot ใกล้ 1,800 สุด)
     - `PUT` `minutes` 25 → 3 EP จุดตัด 1,498 และ 3,003; EP สุดท้ายยาว 597 วินาที; `GET /settings` มี `ep_minutes` 25
     - คลิปยาว 1,830 วินาที `minutes` 30 → 1 EP (เศษ 30 วินาทีรวมเข้า EP 1)
     - `PUT` `cuts` `[1000]` → จุดตัด 1,001; `cuts` `[1000, 1030]` → `400` `invalid_episodes`; `minutes` 7 หรือ 65 → `400` `invalid_episodes`
     - บรรยายฉากใหม่ `done` → ไฟล์การตัดหาย; ลบคลิป → ไฟล์การตัดหาย
     - `POST /draft-jobs` `ep` 3 ของคลิปที่มี 2 EP → `400` `invalid_episodes`; `ep` 2 ที่ `start_s` ไม่ตรงการตัดตอนนี้ → `409` `episodes_changed`; EP ไม่มีบรรทัด → `400` `ep_empty`
     - `GET` คลิป A แล้ว `PUT` คลิป B `minutes` 25 → `GET` คลิป A ยังเป็นการตัดเดิม (ไฟล์เขียนตอน `GET` แรก)
     - คลิปยาว 40 วินาที → 1 EP; `PUT` `{minutes: 30}` → `200`
     - `cuts` `[NaN]`, `[true]`, `["10"]` หรือ `minutes` `true` → `400` `invalid_episodes`; จุดตัดกึ่งกลางระหว่าง Shot 7 กับ 14 วินาที → 7
     - ไฟล์การตัดที่เป็น JSON พัง หรือ `cuts` ไม่ตรงเวลาเริ่มของ Shot → `GET` `200` ตัดตาม `ep_minutes`
     - `PUT` ระหว่าง Describe job ของคลิปนั้น → `409` `clip_busy`
     - ไม่มี tokenizer → `GET` `200` ที่ `tokens` `null`
     - `PATCH` บรรทัด 0 ของคลิปเป็นข้อความใหม่ → ตัวนับ token ปลอมและ LLM ปลอมได้ข้อความใหม่ในบรรทัดนั้น ไม่ใช่ข้อความเดิม (D54)
     - ร่าง EP 2 → LLM ปลอมได้เฉพาะบรรทัดที่เริ่มในช่วง EP 2 เป็น `[{line} {hh:mm:ss}]`; คืน ref ของบรรทัดใน EP 2 → `done`, `GET /draft` มี `ep.n` 2 และ Shot อยู่ใน `window`
     - ref บรรทัดแรกของ EP 2 → `window` เริ่มที่จุดตัด ไม่ใช่ 30 วินาทีก่อน; ref บรรทัดใน EP 1 → ถูกตัดออกจาก `refs`
     - `PATCH /draft/sentences/{sid}` `shots` ที่อยู่ใน EP 1 → `400` `invalid_shot`
     - `draft.json` `version` 1 → `GET /draft` เป็น `null`
     - LLM ปลอมคืน JSON พัง 3 ครั้ง → `failed` `draft_failed` และ Spoil draft เดิมไม่เปลี่ยน
     - LLM ปลอมคืน JSON พัง 2 ครั้งแล้วถูก → `done` และ LLM ถูกเรียก 3 ครั้ง
     - LLM ปลอมค้างเกิน timeout (ลด timeout ใน test) → นับเป็นครั้งที่ไม่ผ่าน
     - LLM ปลอมคืนข้อความที่มี `現場` และ ref `99999` → ข้อความไม่มีอักษรจีน, `refs` ว่าง, `shots` `[null, null]`, สถานะ `no_shot`
     - LLM ปลอมขั้นสองคืน Shot นอกช่วง → ใช้ 2 Shot ที่ใกล้เวลาของ ref ที่สุด
     - มี Spoil draft แล้วไม่มี `replace` → `409` `draft_exists`; `replace: true` → `202`
   - เรียบเรียง (D72–D74):
     - ร่างบท → LLM ปลอมได้คำสั่งร่าง แล้วคำสั่งเรียบเรียงที่มีทุกประโยคและบรรทัดที่อ้าง ก่อนคำสั่งเลือก Shot; job ผ่าน state `polishing`; `GET /draft` มีข้อความที่เรียบเรียงแล้ว `refs` และจำนวนประโยคเท่าเดิม ทุกประโยค `edited` `false`
     - LLM ปลอมขั้นเรียบเรียงคืน `i` ที่ใช้ได้ไม่ถึงครึ่ง 2 ครั้ง → `kind: "draft"` ใช้ข้อความเดิมและงาน `done`; `kind: "polish"` → `failed` `polish_failed` และ draft ไม่เปลี่ยน
     - LLM ปลอมคืน `i` ซ้ำ ไม่รู้จัก หรือ fixed → ถูกทิ้ง ประโยคอื่นได้ข้อความใหม่ตาม `i`
     - LLM ปลอมคืนข้อความยาวขึ้นทุกประโยคจนรวมเกิน +25% ของเป้าหมาย 2 ครั้ง → ใช้ข้อความเดิม
     - `kind: "polish"` เปลี่ยน 3 ประโยค → job `done` มี `done` 3
     - `PATCH` `text` เดิมซ้ำ → `edited` ไม่เปลี่ยน; draft ที่ไม่มีฟิลด์ `edited` → อ่านเป็น `false`
     - LLM ปลอมคืนข้อความว่าง หรือยาวกว่าเดิม 2 เท่าในประโยคหนึ่ง → ประโยคนั้นใช้ข้อความเดิม
     - `PATCH` `text` ของประโยค 2 → `edited` `true`; `POST /draft/sentences` → `edited` `true`; `PATCH` แค่ `shots` → `edited` ไม่เปลี่ยน
     - `kind: "polish"` → คำสั่งทำเครื่องหมาย fixed ที่ประโยค 2; ข้อความประโยค 2 ไม่เปลี่ยนแม้ LLM ปลอมคืนข้อความอื่น; ประโยคอื่นที่มีเสียงและข้อความเปลี่ยน → `stale_audio`; `shots` ทุกประโยคเท่าเดิม
     - `kind: "polish"` `include_edited: true` → คำสั่งไม่มี fixed; ประโยค 2 ได้ข้อความใหม่และ `edited` `false` (D75); `include_edited: "yes"` → `400` `invalid_request`
     - ทุกประโยค `edited` → `kind: "polish"` `400` `nothing_to_polish`; พร้อม `include_edited: true` → `202`; ไม่มี draft → `404` `no_draft`
     - ยกเลิก `polish` ระหว่าง `polishing` → draft ไม่เปลี่ยน; `PATCH` ระหว่างนั้น → `409` `draft_locked`
     - สร้าง app ใหม่บน root เดิม → `GET /draft` เหมือนเดิม
   - แก้ draft:
     - แก้ `text` ของประโยคที่มีเสียง → `stale_audio`; แก้กลับเป็นข้อความเดิม → `ready`
     - `PATCH /draft` เปลี่ยน `voice_id` → ทุกประโยคที่มีเสียงเป็น `stale_audio`
     - `POST /draft/sentences` `after_id` ของประโยคแรก → ประโยคใหม่อยู่ลำดับสอง สถานะ `no_shot`; `kind: "pick"` กับประโยคนั้น → `400` `no_refs`
     - `PATCH /draft/sentences/{sid}` `shots` ที่ `n` ไม่มี → `400` `invalid_shot`
     - `PATCH` ระหว่าง Voice job `sentences` → `409` `draft_locked`; `GET /draft` มี `locked: true`
     - `PATCH /draft` `original_volume` 35 → `GET /settings` มี 35; ร่างใหม่ → draft ใหม่มี 35
     - `estimated_total_s` ของ draft ที่มีประโยค `ready` 2.0 วินาที และประโยคยังไม่มีเสียง 30 ตัวอักษรกับ `chars_per_s` 15 → 4.0
   - เสียงและตัวเลข:
     - Voice job `sentences` ของประโยค `ปี 1968 เวลา 10:30 ราว 50% หรือ 3.25 เท่า ๑๑ คน 114,000 บาท 007` → TTS ปลอมได้ `ปี หนึ่งพันเก้าร้อยหกสิบแปด เวลา สิบนาฬิกาสามสิบนาที ราว ห้าสิบเปอร์เซ็นต์ หรือ สามจุดสองห้า เท่า สิบเอ็ด คน หนึ่งแสนหนึ่งหมื่นสี่พัน บาท ศูนย์ศูนย์เจ็ด`; `.srt` หลัง render ยังเป็นตัวเลข
     - TTS ปลอมคืน wav 2 วินาที → `audio.duration_s` 2.0; ยกเลิกหลังประโยคแรก → ประโยคแรก `ready` ประโยคสอง `no_audio`
     - `design_preview` แล้ว `POST /voices` → `201`, `GET /voices` มีเสียงนั้นพร้อม `chars_per_s` = ตัวอักษรของประโยคตัวอย่างหลังแปลง / ความยาว wav ปลอม
     - `design_preview` speed 1.3 หรือ `age` `baby` → `400` `invalid_voice`; `PATCH /voices/{id}` ชื่อ 41 ตัวอักษรหรือช่องว่างล้วน → `400` `invalid_voice`; ชื่อ `ผู้ชายเสียงต่ำ` → `200` และ `GET /voices` เห็นชื่อใหม่
     - `DELETE /voices/{id}` ที่ Spoil draft ใช้ → `409` `voice_in_use`; ที่ `order.voice_id` ของ Draft job `writing` ใช้ → `409` `voice_in_use`, หลังงาน `failed` → `204` (D87)
   - Render:
     - มีประโยค `no_shot` → `400` `missing_shots`; ที่ว่างปลอม 0.5 GiB → `507` `disk_full`
     - draft 2 ประโยค (เสียงปลอม 2.0 และ 1.5 วินาที) layout A, B, C → mp4 1080×1920 ยาว 3.5 ±0.2 วินาที มีเสียง, `.srt` 2 cue ที่ `00:00:00,000 --> 00:00:02,000` และ `00:00:02,000 --> 00:00:03,500`
     - ประโยค layout A ยาว 3.0 วินาที → ไฟล์ ASS มีซับท่อนละ 2–4 คำ ไม่เกิน 15 ตัวอักษรที่กินที่ และเวลารวม 3.0
     - ลายน้ำเปิด 1 อันและปิด 1 อัน → ไฟล์ ASS มีข้อความของอันที่เปิดเท่านั้น; `PATCH /settings` ลายน้ำ `enabled: false` → `GET /settings` ยังมีข้อความ ตำแหน่ง ขนาดเดิม; `enabled` ไม่ใช่ boolean → `400` `invalid_settings` (D64)
     - ประโยคและลายน้ำที่มี `{\b1}` และขึ้นบรรทัดใหม่ → ไฟล์ ASS มี `\{\\b1\}` และไม่มีขึ้นบรรทัดใหม่ในข้อความ
     - Shot ท้ายคลิปที่เสียงยาวกว่าที่เหลือ → ยาวครบ ไม่ error
     - ประโยคขาดเสียง → state ผ่าน `voicing` แล้ว `rendering`; TTS ปลอมถูกเรียกเฉพาะประโยคนั้น
     - ยกเลิกระหว่าง `rendering` → `cancelled`, ไม่มี `.partial` และ `.render/`
     - render สองครั้ง → `GET /renders` มี 2 รายการ พร้อม `sources` เป็นชื่อคลิป และ `ep` ของ draft; `GET /clips/{id}/episodes` มี `renders` 2 ใน EP นั้น; `.json` เก่าที่ไม่มี `ep` → รายการมี `ep` `null`; `DELETE /renders/{name}` → `204` และไฟล์ทั้งสามหาย; `/renders/../x.mp4` → `404`
   - ลบคลิปและ start:
     - `DELETE /api/spoil/clips/{id}` ของคลิปใน Spoil draft → `204`, `media/temp/shots/{id}/` หาย, `GET /draft` เป็น `null`, ผล render ยังอยู่
     - ลบ mp4 ไม่ได้ → `409` `in_use` และ Spoil draft ยังอยู่
     - start app ขณะมี `media/temp/episodes/a.json.tmp`, `draft.json.tmp`, `renders/x.partial`, `voices/.pending/`, `media/temp/shots/.new-a/` → หายทั้งหมด
   - Status check และความปลอดภัย:
     - marker ของ Qwen หาย → `POST /describes` และ `POST /draft-jobs` → `503` `not_ready` มี `model_qwen`; `POST /voice-jobs` → `202`; คลิปใน Spoil draft ไม่มี `confirm_draft_loss` → ยังเป็น `503` `not_ready` ไม่ใช่ `in_draft` (D60)
     - `GET /api/setup/status` มีแถว `model_qwen`, `mlx_vlm`, `pythainlp`, `font_kanit`; `run_checks` กับ `sys_platform` `win32` → `model_qwen` และ `mlx_vlm` `missing`
     - ทุก POST, PUT และ PATCH ที่ `Content-Type: text/plain` → `415`; `Host: evil.example` → `400`
2. **ทุกหน้าใต้ tab สปอย** `frontend` ด้วย Vitest และ fetch ปลอม (project ไม่มีเครื่องมือ e2e)
   - `#/spoil` เปิด tab สปอยที่ขั้น 1 เลือกคลิป (D53)
   - ตัวบอกขั้น (D68): ทุกขั้นเป็นลิงก์ที่มีเลข ไม่มีภาพเครื่องหมายถูก; มี draft ของ EP 2 6 ประโยคและผล render 3 รายการ → เห็น "{ชื่อคลิป} · EP 2", "6 ประโยค", "3 คลิป"; ไม่มีเลย → "ยังไม่เลือก", "ยังไม่มีบท", "ยังไม่มี"
   - render current `rendering` 45 ขณะเปิดขั้น 1 → ขั้น 3 เห็น "render 45%" และจุดหมุน; `done` → `GET /renders` ถูกเรียกใหม่และเห็นจำนวนคลิปใหม่ ไม่มีจุดหมุน; `failed` → "render ไม่สำเร็จ"; เปิดหน้าตอนไม่มีงานแล้วกด render ในขั้น 2 → ขั้น 3 เริ่มแสดง %; Voice job `sentences` 2/5 → ขั้น 2 เห็น "สร้างเสียง 2/5"
   - `prefers-reduced-motion` → จุดหมุนไม่หมุน แต่บรรทัดสถานะยังอยู่
   - แถวคลิปที่ถอดแล้ว กดบรรยายฉาก, current คืน `describing` 40/100 แล้ว `done` → เห็น 40% แล้ว "บรรยายฉากแล้ว"
   - `409` `gpu_busy` `running: "draft"` → เห็น "รอให้งานร่างบทเสร็จก่อน"
   - ลบ ถอดใหม่ หรือบรรยายฉากใหม่ของคลิปที่ `in_draft: true` → เห็นคำเตือนก่อนส่ง; ยืนยันบรรยายฉาก → ส่ง `confirm_draft_loss: true`
   - หน้าตั้งค่า: เลือกคลิปได้ทีละคลิป; เลือกคลิป → เห็นรายการ EP จาก `GET /clips/{id}/episodes` พร้อมช่วงเวลาและ "render แล้ว {k}"; เลือก EP ได้ทีละ EP
   - EP ที่ `tokens` 40,000 → ปุ่มร่างกดไม่ได้ และเห็น 40,000 / 32,000
   - เปลี่ยนความยาวต่อ EP เป็น 25 → ส่ง `PUT` `{minutes: 25}`; ตอน `custom: true` → เห็นคำยืนยันก่อนส่ง; `409` `episodes_changed` ตอนกดร่าง → เห็นข้อความและรายการ EP อ่านใหม่; แก้เวลาจุดตัดแล้ว blur → ส่ง `PUT` พร้อม `cuts`; `400` `invalid_episodes` → เห็นข้อความของ code นั้น
   - กดร่าง → `POST /draft-jobs` มี `clip_id` และ `ep` ที่เลือก แล้ว hash เป็น `#/spoil/review` (D81)
   - ขั้น 2 กับ current `writing`, `polishing`, `matching` 4/12 → เห็นการ์ดที่หัว "{clip_title} · EP 2" และขั้นที่กำลังทำตามลำดับ, "เลือกภาพ 4/12"; `done` → `GET /draft` ถูกเรียกใหม่และเห็นประโยค (D81)
   - ขั้น 1 กับ current `writing` ที่มี `order` → เห็นคลิป EP สไตล์ ความยาว เสียงของ `order` ทุกช่องกดไม่ได้ ไม่มีปุ่มร่าง และ Alert ที่มีลิงก์ไปขั้น 2 (D82)
   - ขั้น 2 current `failed` `draft_failed` → เห็น "AI ร่างบทไม่สำเร็จ 3 ครั้ง"; กด "ลองอีกครั้ง" → `POST /draft-jobs` ด้วย `order` เดิม; กดยกเลิกระหว่าง `writing` → "กำลังยกเลิก" จน current `cancelled` แล้ว hash เป็น `#/spoil` และค่าของ `order` ยังเลือกอยู่; current จบ `done` หลังกดยกเลิก → เห็นบทและ "ยกเลิกไม่ทัน บทร่างเสร็จแล้ว" (D83, D85)
   - มี Spoil draft และ current `failed` → "ลองอีกครั้ง" แสดงคำยืนยันร่างทับก่อนส่ง; `POST` ตอบ `409` `episodes_changed` → ข้อความใน Alert พร้อม "กลับไปแก้ตั้งค่า"; กด "กลับไปแก้ตั้งค่า" → ขั้น 1 มีค่าของ `order` (D86, D87)
   - ขั้น 2 การ์ดแสดงอยู่แล้ว current กลายเป็น `null` → เห็น "งานหยุดกลางทาง" (D87)
   - `POST /draft-jobs` ตอบ `409` `busy` → เห็น "มีงานร่างบทอยู่แล้ว" และขั้น 1 ล็อก (D87)
   - การ์ดสไตล์ทั้ง 3 มีบรรทัดอธิบายที่ผูกกับ radio ด้วย `aria-describedby` (D84)
   - มี Spoil draft ของ EP 2 → เปิดขั้น 1 แล้วคลิปนั้นถูกเลือก และ EP 2 มีป้ายว่าอยู่ใน Spoil draft
   - คลิปที่ยังไม่บรรยายฉากเลือกไม่ได้และเห็น "ยังไม่บรรยายฉาก"; ไม่มีคลิปพร้อมเลย → เห็นข้อความว่างพร้อมลิงก์
   - เลือกสไตล์ `drama` → layout เป็น B; เปลี่ยน layout เป็น A ได้
   - ไม่มี Saved voice → เห็นลิงก์ไปหน้า Saved voice และปุ่มร่างกดไม่ได้
   - มี Spoil draft แล้วกดร่าง → เห็นคำยืนยันก่อนส่ง `replace: true`
   - หน้าตรวจแก้: ประโยค `no_shot` เห็น "เลือก" แทนภาพ และปุ่ม render กดไม่ได้
   - แก้ข้อความแล้ว blur → ส่ง `PATCH` และสถานะเป็น "ต้องสร้างเสียงใหม่"
   - `GET /draft` มี `locked: true` และ current ของ Voice job `sentences` 1/3 → เห็น "สร้างเสียง 1/3" ปุ่มยกเลิก และช่องข้อความกดไม่ได้
   - กดลบประโยค → เห็นคำยืนยันก่อนส่ง `DELETE`
   - กด "เรียบเรียงใหม่" → เห็นกล่องเลือก; ไม่ติ๊กแล้วกด "เรียบเรียง" → ส่ง `{kind: "polish", include_edited: false}`; ติ๊ก → `include_edited: true`; มีประโยคที่มีเสียง → เห็น "ประโยคที่เปลี่ยนต้องสร้างเสียงใหม่"; current `polishing` → เห็น "กำลังเรียบเรียง" ปุ่มยกเลิก และช่องข้อความกดไม่ได้; ประโยค `edited: true` เห็นป้าย "แก้เอง"; ทุกประโยค `edited` และไม่ติ๊ก → ปุ่ม "เรียบเรียง" กดไม่ได้
   - กดภาพ Shot → ตัวเลือกแสดงภาพของ Shot ใน `window`; กด "ดูทั้ง EP" → แสดงทุก Shot ในช่วง EP; ประโยคที่แทรกเปิดที่ทั้ง EP
   - เพิ่มลายน้ำ 2 อันแล้ว reload → ยังอยู่ (จาก `GET /settings`); กดสวิตช์ลายน้ำแล้ว reload → สวิตช์ยังอยู่ที่ค่าที่ตั้ง
   - ลายน้ำ `top_center` ที่เปิดอยู่กับ layout A ที่มี hook หรือ C ที่มีชื่อตอน → เห็นคำเตือน ปุ่ม render ยังกดได้; ปิด ย้าย ลบ hook จนว่าง หรือ layout B → ไม่เตือน (D64)
   - render current คืน `voicing` 1/3 แล้ว `rendering` 50 แล้ว `done` → เห็น "สร้างเสียง 1/3", "render 50%" แล้วรายการใหม่ที่มีลิงก์ mp4 และ `.srt` และ "ต้นฉบับ: {ชื่อคลิป}" พร้อมปุ่ม copy
   - render current `failed` `ffmpeg_failed` → เห็น "render ไม่สำเร็จ"
   - หน้า Saved voice: กดสุ่ม current `done` → มีปุ่มฟังและช่องชื่อ; บันทึก → อยู่ในรายการ; เปลี่ยนชื่อ → ส่ง `PATCH`; ลบเสียงที่ใช้อยู่ได้ `409` `voice_in_use` → เห็นข้อความ
3. **โมเดลจริงบน Mac M2** Qwen, OmniVoice และผล render (เช็คมือ ไม่อยู่ใน test ที่รันทุกครั้ง)
   - Describe job หนัง 96 นาที → จบภายใน 60 นาที, 700–1,000 Shot, สุ่ม 10 Shot ตรงภาพ ≥ 8
   - ร่างบท 60 วินาที style `drama` จาก EP 30 นาที → ครั้งแรกผ่านรวมเรียบเรียงภายใน 8 นาที, อ่าน 10 คู่ประโยคติดกันเล่าต่อกัน ≥ 8 คู่ (D72), ความยาวประมาณใน ±25%, Shot ตรงเนื้อหา ≥ 5 จาก 10 ประโยคที่สุ่ม
   - EP 60 นาทีของหนัง token ใต้ 32,000 → ร่างจบโดย memory ของ process ลูกไม่เกิน 13 GB
   - ยกเลิกระหว่าง `writing` → process ลูกหายภายใน 5 วินาที
   - ออกแบบเสียงหญิง young adult แล้วบันทึก → 5 ประโยคด้วยเสียงนั้นฟังเป็นเสียงเดียวกัน
   - ประโยคที่มี `1968` และ `10:30` → อ่านถูก
   - render คลิป 60 วินาทีทั้ง 3 layout → ข้อความไทยที่มีสระบนล่างและวรรณยุกต์ไม่ซ้อนผิด, ภาพตรงตาราง layout, ลายน้ำ 6 ตำแหน่งอยู่ถูกมุม, เสียงต้นฉบับ 20% ได้ยินแต่ไม่กลบ, จดเวลา render ไว้ใน progress
   - เปิด mp4 บน iPhone และอัปโหลดขึ้น YouTube Shorts แบบ private → เล่นได้แนวตั้ง
   - import `pythainlp` แล้วตัดคำ → ไม่มี `~/pythainlp-data` ถูกสร้าง

## Testing decisions

- **Copy:** `backend/tests/test_spoil_transcribe_api.py` — โครงงาน GPU ที่มี worker ปลอมใน thread, poll จนจบ, ยกเลิกด้วยสัญญาณ; ใช้กับ Describe job, Draft job, Voice job, Render job
- **Copy:** `backend/tests/fakes.py` — เพิ่ม `start_worker` ปลอมของ LLM และ TTS แบบเดียวกับของ Whisper; TTS ปลอมเขียน wav เงียบตามความยาวที่ test กำหนดและจดข้อความที่ได้รับ
- **Copy:** `backend/tests/test_spoil_api.py` — root ปลอมและการลบคลิป; เพิ่มกรณีคลิปใน Spoil draft
- **Copy:** `backend/tests/test_checks.py` — 4 แถวใหม่ และจำนวนแถวรวม
- **Copy:** `frontend/src/features/spoil/components/ClipsPage.test.tsx` (เดิม `SpoilPage.test.tsx`) — fake backend ตาม route; เพิ่ม route ของ `/api/spoil-maker`
- คลิปทดสอบสร้างใน fixture ด้วย ffmpeg `lavfi` (`color` สามสีต่อกันกับ `sine`) ไม่เก็บไฟล์สื่อใน git; เป็น test แรกของ project ที่รัน ffmpeg จริง
- test ของ render อ่านความยาวและขนาดผลลัพธ์จาก `ffmpeg -i` เพราะไม่มี ffprobe (ADR-0005)
- การตัด Shot จากจุดตัดปลอมผ่าน API โดยแทนตัวหาจุดตัด (ไม่แทน ffmpeg ส่วนอื่น)

## Out of Scope

- clone เสียงจากไฟล์ของผู้ใช้ (D48)
- Windows: backend ของ LLM, โมเดลอีก format และการเช็คบนเครื่องจริง อยู่ใน feature `windows-launch` (D50)
- อัปโหลดขึ้น YouTube หรือ TikTok อัตโนมัติ — ผลจบที่ไฟล์ (D10)
- ภาพเลื่อน ซ้อน เอียง และ transition (D24)
- เพลงพื้นหลัง (D9)
- เลือกสี font หรือลากตำแหน่งข้อความ (D21, D22, D41)
- เครดิตโมเดลที่ใส่ให้อัตโนมัติ (D41)
- หลาย Spoil draft และหน้ารายการงาน (D28, D67)
- รวมหลาย Temp clip เป็นคลิปสปอยเดียว (D66)
- ร่างหลาย EP รวดเดียว หรือให้ EP หลังรู้เรื่องของ EP ก่อน (D67)
- ลากสลับลำดับประโยค (D27)
- ให้ AI รวม แยก หรือสลับประโยคตอนเรียบเรียง (D73)
- ย้อนการเรียบเรียง (D76)
- บทภาษาอื่นนอกจากไทย (D11)
- สรุปหรือตัด Transcript ที่ยาวเกิน 32,000 token (D46)
- แก้ speed ของ Saved voice (D43)
- resume Describe job ที่ยกเลิกหรือ crash (D16)

## Open Questions

1. เวลา render คลิป 60 วินาทีบน M2 ยังไม่ได้วัด — non-blocking: ไม่มีการตัดสินใจที่ขึ้นกับตัวเลขนี้ จดตอน build (Seam 3)

## Sources

- [mlx-vlm v0.7.11](https://github.com/Blaizzy/mlx-vlm/tree/v0.7.11) — `load`, `apply_chat_template`, `generate` กับภาพ (accessed 2026-10-31)
- [transformers AutoTokenizer](https://huggingface.co/docs/transformers/main/en/model_doc/auto#transformers.AutoTokenizer) — นับ token จาก snapshot (accessed 2026-10-31)
- [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) — `instruct`, `create_voice_clone_prompt`, `speed`, `num_step` (accessed 2026-10-31)
- [PyThaiNLP tokenize API](https://pythainlp.org/dev-docs/api/tokenize.html) — `word_tokenize` engine `newmm` (accessed 2026-10-31)
- [PyThaiNLP v5.4.0](https://github.com/PyThaiNLP/pythainlp/tree/v5.4.0) — version ที่ pin และ `PYTHAINLP_DATA` (accessed 2026-10-31)
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) — `select` scene, `showinfo`, `ass`, `gblur`, `tpad`, `amix` (accessed 2026-10-31)
- [ASS override tags](https://aegisub.org/docs/latest/ass_tags/) — `\pos`, `\an`, `\bord`, `\3c`, `\fs` (accessed 2026-10-31)
- [google/fonts ofl/kanit @ 130fcfb](https://github.com/google/fonts/tree/130fcfb0ff422fec96b335616b2ca99f91914792/ofl/kanit) — ไฟล์ Kanit Bold และ OFL (accessed 2026-10-31)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) — license ของ Qwen3.5 (accessed 2026-10-31)
