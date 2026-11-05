# Flow: story-kb

2 diagrams, read in this order:
1. ผู้ใช้สร้าง Story แล้วใช้กับคลิปตอนกดร่างบท
2. Draft job แต่ละ `kind` ใช้ Story อย่างไร

All diagrams use the same names as [spec.md](spec.md).

## 1. สร้าง Story แล้วใช้ตอนกดร่าง

```mermaid
sequenceDiagram
    actor U as ผู้ใช้
    participant W as หน้าเว็บ
    participant S as /api/stories
    participant D as /api/spoil-maker/draft-jobs

    U->>W: คลังความรู้ › เพิ่มเรื่อง
    U->>W: ใส่ชื่อเรื่อง บทความ ตัวละคร แล้วกดบันทึก
    W->>W: เช็คกฎของค่า
    alt ไม่ผ่าน
        W-->>U: error ใต้ช่อง ไม่ส่ง request
    else ผ่าน
        W->>S: POST /api/stories
        S-->>W: 201 Story
        W-->>U: บันทึกแล้ว และ hash เป็น #/stories/{id}
    end
    U->>W: สปอย › ขั้น 1 เลือกคลิป
    W->>S: GET /api/stories กับ GET /api/story-clips
    S-->>W: รายการ Story และ Story ที่คลิปจำ
    W-->>U: ช่อง Story ตั้งที่ค่าที่คลิปจำ หรือ ไม่ใช้
    U->>W: เลือก Story แล้วกดร่างบท
    W->>D: POST kind draft พร้อม story_id
    alt 400 story_not_found หรือ transcript_too_long
        D-->>W: error
        W-->>U: Alert และช่อง Story หรือตัวนับตามจริง
    else 202
        D->>D: จำ story_id ให้คลิป แล้วอ่าน Story
        D-->>W: job พร้อม order.story_title
        W-->>U: ขั้น 2 การ์ดความคืบหน้า
    end
```

**ผู้ใช้ทำอะไร และคลิปจำ Story เมื่อไหร่**
- เปลี่ยนช่อง Story ไม่ส่ง request; จำตอนกดร่างเท่านั้น (D15)
- token ของ EP กับ Story รวมกันไม่เกิน 32,000 (D14)
- ลบคลิปลบ Story ที่คลิปจำ; ตัดช่วงหรือถอดใหม่ไม่ลบ (D7)
- ลบ Story ลบทุก key ที่ชี้มัน (D10)

## 2. Draft job ใช้ Story

```mermaid
flowchart TD
    req["POST /draft-jobs"] --> kind{"kind"}
    kind -- "draft" --> checks["เช็คคำขอ รวม story_id และ token รวม"]
    kind -- "polish" --> pchecks["เช็คของเรียบเรียงใหม่"]
    kind -- "pick" --> pgpu["จองช่อง GPU"]
    checks -- "ไม่ผ่าน" --> refuse["4xx ตามตาราง"]
    pchecks -- "ไม่ผ่าน" --> refuse
    checks -- "ผ่าน" --> remember["จำ story_id ให้คลิป"]
    remember --> read["อ่าน Story"]
    pchecks -- "ผ่าน" --> pread["อ่าน Story ที่คลิปจำ"]
    read --> dgpu["จองช่อง GPU"]
    pread --> ppgpu["จองช่อง GPU"]
    dgpu --> write["เขียนบท มีบล็อก Story"]
    write --> polish["เรียบเรียง มีบล็อก Story"]
    polish --> match["เลือก Shot ไม่มี Story"]
    match --> done["done"]
    ppgpu --> polish2["เรียบเรียง มีบล็อก Story"]
    polish2 --> done
    pgpu --> match2["เลือก Shot ไม่มี Story"]
    match2 --> done
```

**งานไหนใช้ Story และอ่านเมื่อไหร่**
- อ่านครั้งเดียวตอนรับคำขอ; แก้หรือลบ Story ระหว่างงานไม่กระทบงานนั้น (D5, D10)
- ไม่มี Story หรือไฟล์เสีย → ไม่มีบล็อก คำสั่งเหมือนเดิม (spec › คำสั่ง LLM)
- บล็อก Story บอกว่าเหตุการณ์ต้องมาจาก Transcript เท่านั้น (D8)
- ตำแหน่งบล็อกในแต่ละคำสั่ง (D16)
