# Flow: windows-launch

2 diagrams, read in this order:
1. งาน Qwen ผ่าน gate บน Windows ได้เมื่อไหร่
2. งาน Qwen คุยกับ worker ของ Windows ยังไง

All diagrams use the same names as [spec.md](spec.md).

## 1. gate ของงาน Qwen บน Windows

```mermaid
flowchart LR
    press["กดบรรยายฉาก<br/>หรือร่างบท"] --> device{"แถว device<br/>sm อยู่ใน arch list"}
    device -->|ไม่ผ่าน| refuse["503 not_ready<br/>rows บอกแถว"]
    device -->|ผ่าน| gpu{"แถว gpu<br/>sm ≥ 8.0, VRAM ≥ 7.5 GiB"}
    gpu -->|warning| refuse
    gpu -->|ผ่าน| model{"model_qwen<br/>Qwen/Qwen3.5-9B ครบ"}
    model -->|ไม่ครบ| refuse
    model -->|ครบ| runner{"bitsandbytes<br/>ติดตั้งแล้ว"}
    runner -->|ไม่มี| refuse
    runner -->|มี| start["จองช่อง GPU<br/>แล้วเริ่มงาน"]
```

**แถวไหนที่ทำให้ Windows เริ่มงาน Qwen ไม่ได้**
- อ่านจากซ้ายไปขวา; ทุกทางที่ไม่ผ่านไปที่ `503` `not_ready` ตัวเดียวกัน ซึ่ง `rows` บอกแถวที่ไม่ผ่านทั้งหมด ไม่ใช่แค่แถวแรก (spoil-maker D56).
- แถว `ffmpeg` เช็คก่อนตามเดิม ไม่ได้วาด.
- แถว `device` กันงานถอดเสียงและสร้างเสียงด้วย ไม่ใช่แค่งาน Qwen (D8).
- `gpu` ที่เป็น `warning` ยังกันงาน แต่ Setup script จบปกติ (D9).
- บน Mac ไม่มีแถว `gpu` และแถวตัวรันเป็น `mlx_vlm` แทน `bitsandbytes` (D6, D8).

## 2. งาน Qwen กับ worker ของ Windows

```mermaid
sequenceDiagram
    participant Job as Describe job หรือ Draft job
    participant Llm as spoil_maker.llm
    participant Child as process ลูก (Windows worker)
    Job->>Llm: start_worker(snapshot ของ Qwen/Qwen3.5-9B)
    Llm->>Child: spawn worker ของ OS นี้
    Child->>Child: โหลด nf4 ไม่ย่อ visual, lm_head
    Child-->>Job: Ready
    Job->>Child: Generate(prompt, ภาพ, max_tokens, temperature)
    Child-->>Job: Generated(text)
    Job->>Child: None (จบงาน)
```

**ทางเดินของหนึ่งคำขอจากงานถึงโมเดลบน Windows**
- ข้อความ `Generate`, `Ready`, `Generated`, `WorkerError` เหมือน worker ของ Mac ทุกตัว; ต่างกันแค่ worker ที่ `start_worker` เลือกตาม OS (D3).
- การโหลดไม่มี timeout; trial จดเวลาถึง `Ready` (D12).
- แต่ละ `Generate` รอได้ตามค่าต่อ OS ใน spec › ค่าต่อ OS แล้ว terminate process ลูก (D7, D12).
- exception ใน process ลูกส่ง `WorkerError` `model_failed` แล้วออก; process ตายไม่ส่งผล = `crashed` ตามเดิม (spoil D28).
- งานถือช่อง GPU ช่องเดียวตลอด ตาม ADR-0015.
