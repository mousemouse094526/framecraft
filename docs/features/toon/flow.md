# Flow: toon

4 diagrams, read in this order:
1. ทางของผู้ใช้ตั้งแต่สร้าง Series จนได้ mp4
2. ขั้นของ EP กับการแตกใหม่
3. Image job: Qwen แปล แล้ว klein สร้างทีละภาพ
4. Render job: จากการ์ดเป็น mp4

All diagrams use the same names as [spec.md](spec.md).

## 1. ทางของผู้ใช้

```mermaid
flowchart LR
    series[สร้าง Series] --> refs[ภาพอ้างอิง<br/>สร้าง 3 แบบ เลือก หรือเอาไฟล์เข้า]
    series --> ep[EP ใหม่<br/>พิมพ์ไอเดีย]
    ep --> plot[Plot job<br/>แก้พล็อต]
    plot --> cards[Cards job<br/>แก้การ์ด]
    cards --> images[Image job<br/>ภาพที่ขาดทั้งหมด]
    refs --> images
    cards --> voice[Voice job<br/>ทีละการ์ด]
    sounds[คลังเสียงพื้น] --> cards
    images --> render[Render job]
    voice --> render
    render --> mp4[mp4 1080×1920]
```

**ผู้ใช้ต้องทำอะไรก่อนได้คลิป**
- ภาพอ้างอิงทำก่อนหรือหลังพล็อตก็ได้; ของใหม่จากพล็อตเข้า Series ตอน Cards job ครั้งแรก ยังไม่มีภาพ (D13)
- การ์ดที่ใช้ของที่ไม่มีภาพอ้างอิงถูกข้ามใน Image job และนับใน `skipped` (D33)
- Voice job ข้ามได้: Render job สร้างเสียงที่ขาดให้ (D38)
- AI เลือกเสียงพื้นจากชื่อในคลังตอน Cards job; render ผสมเสียงต่อช่วง (D5, D17)
- ทุกงานที่โหลดโมเดลจองช่อง GPU ช่องเดียวของ backend (ADR-0015); Render job มี slot ของตัวเอง (D45)

## 2. ขั้นของ EP

```mermaid
stateDiagram-v2
    direction LR
    [*] --> plot: สร้าง EP
    plot --> plot: Plot job
    plot --> cards: Cards job ครั้งแรก
    cards --> changed: แก้ summary หรือเพิ่มองก์
    changed --> confirm: จะเสียการ์ด edited ภาพ เสียง
    changed --> cards: Cards job
    confirm --> cards: confirm_edited
```

**เมื่อไหร่ AI เขียนทับการ์ด**
- `changed` = มีองก์ที่ `summary` ≠ `cards_from` หรือ `cards_from` `null` (องก์ที่เพิ่มหลังยืนยัน); Cards job แตกเฉพาะองก์เหล่านั้น (D15)
- `confirm`: Cards job ได้ `409` `cards_will_be_lost` พร้อมจำนวนต่อองก์ จนกว่าส่ง `confirm_loss: true` (D43)
- องก์ที่แตกใหม่เสียภาพและเสียงของการ์ดเดิม; องก์อื่นไม่เปลี่ยน (D15)
- Plot job ใช้ได้เฉพาะ `stage` `plot`; หลังนั้นผู้ใช้แก้พล็อตเอง (`409` `plot_confirmed`)

## 3. Image job

```mermaid
sequenceDiagram
    participant W as หน้าเว็บ
    participant B as backend thread
    participant Q as Qwen (process ลูก)
    participant K as klein (process ลูก)
    W->>B: POST /api/toon/jobs kind image
    B->>B: copy ภาพอ้างอิงลง .image-job/
    B->>Q: คำบรรยายภาพทุกการ์ดในงาน
    Q-->>B: ประโยคอังกฤษต่อการ์ด
    B->>K: Encode(คำสั่งภาพทั้งหมด)
    K-->>B: Encoded
    B->>K: Draw(การ์ดละครั้ง)
    K-->>B: Drawn(png)
    B->>B: เขียน image, ย้ายเดิมเป็น previous_image
    W->>B: GET /api/toon/jobs/current (poll)
```

**ทำไม memory พอบนเครื่อง 16 GB**
- Qwen จบ process ก่อน klein เริ่ม; ในขั้น klein ปล่อย text encoder ก่อนโหลด transformer GGUF (D34, D36)
- คำบรรยายภาพที่ใช้คือของ ณ ตอนเริ่มงาน (D36)
- ยกเลิก: หยุดหลังภาพที่กำลังสร้าง ภาพที่เสร็จแล้วอยู่ (D33)
- การ์ดที่ถูกลบหรือแตกใหม่ระหว่างงาน: ภาพที่ได้ถูกทิ้ง; `Draw` ล้มหนึ่งการ์ด: นับใน `failed_cards` แล้วไปต่อ

## 4. Render job

```mermaid
flowchart LR
    check[เช็ค stage การ์ดมีภาพ<br/>ล็อก busy ดิสก์ แถว] --> voicing[voicing<br/>เสียงที่ขาด]
    voicing --> pictures[ภาพต่อการ์ด<br/>lanczos zoompan ไฟกะพริบ]
    pictures --> xfade[xfade 0.3 วิ]
    voicing --> narration[เสียงเล่า<br/>+ เว้น 0.3 + ค้าง]
    sounds[เสียงพื้นต่อช่วง<br/>aloop acrossfade] --> mix[amix]
    narration --> mix
    xfade --> ass[ASS ซับ ป้าย ชื่อตอน]
    ass --> mp4[mp4 + srt + json]
    mix --> mp4
```

**จากการ์ดเป็นคลิป**
- `voicing` จองช่อง GPU เฉพาะเมื่อมีการ์ด `no_audio` หรือ `stale_audio`; ไม่มีก็ข้าม (D38)
- การ์ดไม่มีภาพ → `400` `cards_not_ready` ก่อนเริ่ม; `stale_ref` render ได้ด้วยภาพเดิม (D32)
- ช่วงที่ติดกันใช้เสียงพื้นเดียวกันเล่นต่อไม่เริ่มใหม่ (D17)
- ป้ายชื่อขึ้นตลอดการ์ดแรกที่ตัวละครออกเมื่อ `name_tags` เปิด (D19, D23)
- `rendering` อ่าน EP ครั้งเดียวและ copy ไฟล์ลง `.render/`; json ของผล render เขียนหลังสุด; ยกเลิกหรือ restart ลบ `.partial` และ `.render/` (spec › Render job)
