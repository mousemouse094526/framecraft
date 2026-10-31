# Flow: spoil-maker

5 diagrams, read in this order:
1. เส้นทางของผู้ใช้ตั้งแต่ Temp clip ถึงผล render
2. Draft job: ใครเรียกใครระหว่างร่างบท
3. สถานะของประโยคใน Spoil draft
4. Render job: ขั้นจากกด render ถึงไฟล์
5. state ของงาน GPU ทุกชนิด

All diagrams use the same names as [spec.md](spec.md). Diagram 1 is the map; 2–4 zoom into its steps; 5 is the lifecycle every job in 1 shares.

## 1. เส้นทางของผู้ใช้

```mermaid
flowchart LR
    clip["Temp clip<br/>ถอดแล้ว"] -->|กดดูภาพ| describe["Describe job"]
    describe -->|shots.json| ready["คลิปพร้อม"]
    voice["Saved voice"] -->|เลือกเสียง| setup["ตั้งค่า<br/>EP สไตล์ ความยาว"]
    ready -->|เลือกและเรียง| setup
    setup -->|กดร่างบท| draftjob["Draft job"]
    draftjob -->|draft.json| review["หน้าตรวจแก้"]
    review -->|สร้างเสียง| voicejob["Voice job"]
    voicejob -->|เสียงต่อประโยค| render["Render job"]
    review -->|กด render| render
    render -->|mp4 + .srt| renders["รายการผล render"]
```

**ผู้ใช้ทำคลิปสปอยหนึ่งคลิปผ่านขั้นไหนบ้าง**
- Describe job ทำครั้งเดียวต่อคลิป ใช้ราว 45 นาทีต่อหนัง 96 นาที (D16, D18)
- Saved voice สร้างก่อนครั้งเดียว ใช้ซ้ำทุกคลิป (D32)
- สร้างเสียงก่อนก็ได้ ข้ามไปกด render ก็ได้: render สร้างเสียงที่ขาดให้ (D30)
- กดร่างบทตอนมี Spoil draft อยู่ต้องยืนยันทับ (D28)
- ทุกงานในภาพนี้ใช้ช่อง GPU เดียวกัน: ดู diagram 5 (D45)
- ถอดใหม่หรือดูภาพใหม่ของคลิปใน Spoil draft ลบ Spoil draft หลังยืนยัน (D49)

## 2. Draft job

```mermaid
sequenceDiagram
    participant UI as หน้าเว็บ
    participant API as backend
    participant W as process ลูก (Qwen)
    UI->>API: POST /draft-jobs
    API->>API: เช็คคลิป token ช่อง GPU
    API-->>UI: 202 writing
    API->>W: Transcript ทุก EP
    W-->>API: JSON บท (สูงสุด 3 ครั้ง)
    API->>API: ตัดอักษรจีน ตรวจ refs
    loop ทุกประโยคที่มี refs
        API->>W: Shot ในช่วง ±30 วินาที
        W-->>API: 2 Shot
    end
    API->>API: เขียน draft.json คืนช่อง GPU
    UI->>API: GET /draft-jobs/current (poll)
    API-->>UI: done
```

**ร่างบทกับเลือก Shot ต่อกันในงานเดียวอย่างไร**
- JSON พังหรือความยาวนอก ±25% สั่งใหม่ได้รวม 3 ครั้ง; ไม่มีผลที่อ่านได้เลย = `draft_failed` (D18)
- token รวมเกิน 32,000 ไม่เริ่มงาน: `400` `transcript_too_long` (D46)
- ประโยคที่ไม่มี refs ข้ามขั้นเลือก Shot ได้ `[null, null]` (D18, D26)
- ยกเลิกหรือ crash ก่อนเขียน draft.json: Spoil draft เดิมไม่เปลี่ยน
- `kind: "pick"` ทำเฉพาะ loop กับประโยคเดียว (D25)

## 3. สถานะของประโยค

```mermaid
stateDiagram-v2
    direction LR
    [*] --> no_shot: แทรก หรือไม่มี refs
    [*] --> no_audio: ร่างได้ 2 Shot
    no_shot --> no_audio: เลือก Shot ครบ
    no_audio --> ready: สร้างเสียง
    ready --> stale_audio: แก้ข้อความ<br/>หรือเปลี่ยนเสียง
    stale_audio --> ready: สร้างเสียงใหม่
```

**ประโยคหนึ่งพร้อม render เมื่อไร**
- สถานะคำนวณตอนอ่านจาก `shots`, `audio` และข้อความปัจจุบัน ไม่เก็บในไฟล์ (D30)
- `no_shot` render ไม่ได้; `no_audio` กับ `stale_audio` render สร้างเสียงให้ก่อน (D30)
- แก้ข้อความกลับเป็นข้อความเดิม: `stale_audio` กลับเป็น `ready` เอง เพราะเทียบข้อความหลังแปลงตัวเลข (D36)
- ล้าง Shot ช่องใดช่องหนึ่งให้ว่างจากสถานะไหนก็ได้ กลับเป็น `no_shot` (ไม่ได้วาดเส้น)

## 4. Render job

```mermaid
flowchart LR
    start["POST /renders"] -->|ไม่มี no_shot<br/>ดิสก์พอ| gpu["จองช่อง GPU"]
    gpu --> voicing["voicing<br/>สร้างเสียงที่ขาด"]
    voicing --> free["คืนช่อง GPU"]
    free --> cut["ตัดแต่ละช่วง<br/>ตาม layout"]
    cut --> join["ต่อช่วง ผสมเสียง<br/>วาด ASS"]
    join --> write["rename .partial<br/>เป็น mp4 .srt .json"]
```

**จากกด render ถึงไฟล์ในรายการผล render**
- ไม่มีประโยคที่ขาดเสียง ข้ามการจองช่อง GPU และ `voicing` ไปตัดช่วงเลย (D30)
- ช่วง ffmpeg ไม่ถือช่อง GPU: งาน GPU อื่นเริ่มได้ระหว่างนั้น (D51)
- เสียงประโยคยาว N แบ่ง Shot ละ N/2 เล่นจากต้น Shot; เลยท้ายต้นฉบับค้างเฟรมสุดท้าย (D31, D45)
- ที่ว่างน้อยกว่า 1 GiB หรือมีประโยค `no_shot`: `POST /renders` ตอบ error ทันที ไม่มีงานเกิดขึ้น (`507` `disk_full`, `400` `missing_shots`)
- ยกเลิกระหว่างตัดหรือต่อ: ฆ่า ffmpeg ลบ `.partial` และ `.render/`
- ผล render ใหม่ไม่ทับของเก่า (D42)

## 5. state ของงาน GPU

```mermaid
stateDiagram-v2
    direction LR
    [*] --> running: จองช่อง GPU ได้
    running --> done: เขียนผลเสร็จ
    running --> cancelled: ผู้ใช้ยกเลิก
    running --> failed: error หรือ process ลูกตาย
    done --> [*]
    cancelled --> [*]
    failed --> [*]
```

**งาน GPU ทุกชนิดเริ่มและจบอย่างไร**
- `running` แทน state ย่อยของแต่ละงาน: `cutting`, `describing`, `writing`, `matching`, `voicing`, `rendering`
- จองไม่ได้ไม่มี state: ได้ `409` `gpu_busy` ทันที พร้อม `running` (D45)
- ทุกทางออกคืนช่อง GPU (D45); Render job คืนก่อนนั้นเมื่อจบ `voicing` (D51)
- คำขอที่ไม่ผ่านการเช็ค (`400`, `404`, `409`, `503`, `507`) ไม่สร้างงาน
- งานทั้งหมดอยู่ใน memory หายเมื่อ backend restart (ADR-0010)
- Download job ของ spoil ไม่ใช้ช่องนี้ (spoil D24)
