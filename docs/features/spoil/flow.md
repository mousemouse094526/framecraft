# Flow: spoil

6 diagrams, read in this order:
1. ผู้ใช้วางลิงก์จนได้ Temp clip: หน้าเว็บ, API, Download job และ yt-dlp คุยกันยังไง
2. state ของ Download job และสิ่งที่เกิดกับไฟล์ในแต่ละทาง
3. ผู้ใช้เลือกคลิปแล้วกดถอดจนเห็น Transcript
4. state ของ Transcribe job และสิ่งที่เกิดกับ Transcript ในแต่ละทาง
5. state ของ Trim job และสิ่งที่เกิดกับ mp4 และข้อมูลจากคลิปในแต่ละทาง — ตัดก่อนถอด แล้ว diagram 3 อ่านไฟล์ที่ตัดแล้ว
6. ผู้ใช้เลือกไฟล์ mp4 ในเครื่องจนได้ Temp clip (File import) — ทางที่สองของ diagram 1

All diagrams use the same names as [spec.md](spec.md).

## 1. วางลิงก์จนได้ Temp clip

```mermaid
sequenceDiagram
    actor U as ผู้ใช้
    participant W as tab คลิป
    participant A as Spoil API
    participant J as Download job (thread)
    participant Y as yt-dlp adapter

    U->>W: วางลิงก์ กด "โหลด"
    W->>A: POST /api/spoil/downloads
    A->>A: เช็ค not_ready, invalid_url, duplicate (YouTube), busy
    alt ไม่ผ่านข้อใดข้อหนึ่ง
        A-->>W: 503 / 400 / 409 พร้อม code
        W-->>U: ข้อความตาม code
    else ผ่าน
        A->>J: เริ่มงาน state checking
        A-->>W: 202 Download job
        J->>Y: extract_info(download=False)
        Y-->>J: metadata
        J->>J: เช็ค playlist, duplicate (เว็บอื่น), live และดิสก์
        J->>Y: โหลดและ merge เป็น mp4
        loop ทุก 1 วินาทีจนงานจบ
            W->>A: GET /api/spoil/downloads/current
            A-->>W: state และ percent
        end
        Y-->>J: ไฟล์ใน media/temp/
        J->>J: เขียน {id}.json แล้ว state done
        W->>A: GET /api/spoil/clips
        A-->>W: รายการใหม่
        W-->>U: "โหลดเสร็จ" และ highlight แถวใหม่
    end
```

**ใครทำอะไร ตั้งแต่กดโหลดจนเห็นแถวใหม่**
- ทุกเช็คใน POST ไม่ใช้ network; probe แค่ `yt_dlp`, `deno`, `ffmpeg` (D9, D14)
- มีงานได้ทีละงาน เช็คภายใต้ lock เดียว งานที่สองได้ `409` `busy` (D6, D15)
- ยกเลิก = `DELETE /api/spoil/downloads/current`; ผลต่อแต่ละ state อยู่ใน diagram 2 (D15)
- restart backend ระหว่างงาน → งานหาย; start ใหม่ล้าง `.partial/` และ `{id}.*` ที่ไม่มี json (D14, D15)

## 2. state ของ Download job

```mermaid
stateDiagram-v2
    [*] --> checking: POST /downloads ผ่าน
    checking --> failed: live หรือ disk_full หรือ unavailable หรือ youtube_error
    checking --> downloading: metadata ผ่าน
    downloading --> merging: format สุดท้าย finished
    merging --> done: เขียน json ของคลิปแล้ว
    downloading --> failed: error จาก yt-dlp
    merging --> failed: error จาก ffmpeg
    checking --> cancelled: flag ยกเลิก เช็คหลัง fetch_info
    downloading --> cancelled: hook raise DownloadCancelled
    done --> [*]
    failed --> [*]
    cancelled --> [*]
```

**งานจบได้สามทาง และแต่ละทางเหลือไฟล์อะไร**
- `done`: `{id}.mp4`, `{id}.json` และ thumbnail อยู่ใน `media/temp/` (D14)
- `failed` และ `cancelled`: ลบไฟล์ของ id นี้ใน `.partial/` และ `{id}.mp4` ที่ยังไม่มี json คู่ (D14)
- งานที่จบแล้วยังตอบใน `GET /downloads/current` จนมีงานใหม่ (D6)
- `merging` ยกเลิกไม่ได้: `DELETE /downloads/current` ได้ `409` `merging` (D15)
- งานนับว่าจบเมื่อ thread ออก ไม่ใช่ตอนได้ `DELETE` (D15)

## 3. เลือกคลิปแล้วถอดจนเห็น Transcript

```mermaid
sequenceDiagram
    actor U as ผู้ใช้
    participant W as กล่องถอดบทพูด
    participant A as Spoil API
    participant T as Transcribe job (thread)
    participant H as Whisper worker (process ลูก)

    U->>W: กดแถวคลิป แล้วกด "ถอดบทพูด"
    W->>A: POST /api/spoil/transcriptions
    A->>A: เช็ค not_ready, not_found, busy
    alt ไม่ผ่านข้อใดข้อหนึ่ง
        A-->>W: 503 / 404 / 409 พร้อม code
        W-->>U: ข้อความตาม code
    else ผ่าน
        A->>T: เริ่มงาน state preparing
        A-->>W: 202 Transcribe job
        T->>H: start process ลูก (spawn)
        H->>H: load โมเดล
        loop ทุกช่วง 300 วินาทีของเสียง
            H->>H: read_audio ช่วงนี้ แล้ว transcribe
            H-->>T: segment พร้อมบรรทัดผ่าน queue
        end
        H-->>T: done แล้ว exit
        loop ทุก 1 วินาทีจนงานจบ
            W->>A: GET /api/spoil/transcriptions/current
            A-->>W: state และ percent
        end
        T->>T: เขียน {id}.transcript.json แล้ว state done
        W->>A: GET /clips และ GET /clips/{id}/transcript
        A-->>W: transcribed true และบรรทัด
        W-->>U: Transcript, Copy, .txt, .srt
    end
```

**ใครทำอะไร ตั้งแต่กดถอดจนเห็น Transcript**
- gate ใช้แถว `torch`, `transformers`, `ffmpeg`, `model_whisper` และ `device` ไม่ใช่ `cpu` (D27)
- Download job ไม่ทำให้ได้ `busy`; งานถอดสองงานทำให้ได้ (D24)
- ถอดใน process ลูก: crash ไม่ล้ม backend และงานโหลด, memory คืนเมื่อ process ออก (D28)
- เสียงดึงทีละช่วงเข้า memory ไม่ลงดิสก์; backend เขียน Transcript คนเดียว (D28, D29)
- ยกเลิก = `DELETE /api/spoil/transcriptions/current` แล้ว backend terminate process ลูกทันที (D28)

## 4. state ของ Transcribe job

```mermaid
stateDiagram-v2
    [*] --> preparing: POST /transcriptions ผ่าน
    preparing --> failed: no_audio หรือ model_failed หรือ crashed
    preparing --> cancelled: flag ยกเลิก terminate process ลูก
    preparing --> transcribing: ได้ segment แรก
    transcribing --> cancelled: flag ยกเลิก terminate process ลูก
    transcribing --> failed: model_failed หรือ crashed หรือ internal
    transcribing --> done: เขียน Transcript แล้ว
    done --> [*]
    failed --> [*]
    cancelled --> [*]
```

**งานจบได้สามทาง และ Transcript เป็นอย่างไร**
- `done`: `{id}.transcript.json` ใหม่ทับของเดิม แถวแสดง "ถอดแล้ว" (D23)
- `failed` และ `cancelled`: Transcript เดิม (ถ้ามี) ไม่ถูกแตะ; ทุกทาง process ลูกไม่เหลือ (D28, D29)
- ระหว่างงานยังไม่จบ ลบคลิปนั้นได้ `409` `transcribing` (D27)
- restart backend ระหว่างงาน → งานหาย Transcript เดิมยังอยู่ (ADR-0010)
- หลัง `done` แก้ข้อความทีละบรรทัดได้ด้วย `PATCH /clips/{id}/transcript/lines/{n}`: เวลาและจำนวนบรรทัดไม่เปลี่ยน บรรทัดได้ `edited: true`; ระหว่าง Transcribe job ของคลิปนั้น `409` `transcribing`; ถอดใหม่จน `done` ทับที่แก้ไว้ (spoil-maker D54)

## 5. state ของ Trim job

```mermaid
stateDiagram-v2
    [*] --> trimming: POST /trims ผ่าน
    trimming --> cancelled: flag ยกเลิก kill ffmpeg
    trimming --> failed: disk_full หรือ ffmpeg_failed
    trimming --> replacing: ffmpeg exit 0
    replacing --> failed: in_use หรือ internal
    replacing --> done: แทน mp4 ลบข้อมูลจากคลิป เขียน json
    done --> [*]
    failed --> [*]
    cancelled --> [*]
```

Trim job จาก `POST /trims` จนจบ: ยกเลิกได้เฉพาะตอน `trimming`; ตั้งแต่ `replacing` ไฟล์ถูกแทนจริง (D41).

**งานจบได้สามทาง และ mp4 กับข้อมูลจากคลิปเป็นอย่างไร**
- `done`: `{id}.mp4` เป็นไฟล์ใหม่; Transcript, Shot, การตัด EP และ Spoil draft ของคลิปหาย; json มี `duration_s` ใหม่และ `trimmed` (D36, D37)
- `cancelled` และ `failed`: mp4 และข้อมูลเดิมไม่ถูกแตะ; ไฟล์ใน `.partial/` ถูกลบ (D41)
- ระหว่างงานยังไม่จบ ถอด แก้บรรทัด และลบคลิปนั้นได้ `409` `trimming`; งาน spoil-maker ของคลิปนั้นได้ `409` `clip_busy` (D41)
- restart backend ระหว่าง `replacing` → marker `{id}.trimming.json` ทำให้ start ครั้งหน้าทำต่อหรือย้อนจนครบ (D41)

## 6. เลือกไฟล์ในเครื่องจนได้ Temp clip

```mermaid
sequenceDiagram
    actor U as ผู้ใช้
    participant W as tab คลิป
    participant A as Spoil API
    participant F as ffmpeg

    U->>W: เลือกหรือลากไฟล์ .mp4
    W->>A: POST /api/spoil/imports/check {name, size}
    A->>A: เช็ค not_ready, not_mp4, duplicate, busy, disk_full
    alt ไม่ผ่าน
        A-->>W: 400 / 409 / 503 พร้อม code
        W-->>U: ข้อความตาม code, ไม่ส่งไฟล์
    else ผ่าน
        A-->>W: 200 {clip_id}
        W->>A: POST /api/spoil/imports (body ไฟล์ดิบ)
        A->>A: เช็คข้อเดิมซ้ำ แล้วเขียน .partial/ ทีละก้อน
        W-->>U: % จาก upload progress
        opt ผู้ใช้กดยกเลิก
            W->>A: abort การเชื่อมต่อ
            A->>A: ลบไฟล์ใน .partial/
        end
        A->>F: ffmpeg -i (อ่าน codec, ขนาดภาพ, ความยาว)
        F-->>A: stderr
        alt ไม่ใช่ h264/aac ≤ 1080
            A->>A: ลบไฟล์ใน .partial/
            A-->>W: 400 unsupported_file บอกข้อที่ไม่ตรง
            W-->>U: ให้แปลงไฟล์เอง
        else ตรง
            A->>F: ดึงเฟรมที่ 10% เป็น thumbnail
            A->>A: ย้าย mp4 เข้า media/temp/ แล้วเขียน {id}.json สุดท้าย
            A-->>W: 201 Temp clip
            W-->>U: แถวใหม่ "ไฟล์ในเครื่อง" ถูก highlight
        end
    end
```
