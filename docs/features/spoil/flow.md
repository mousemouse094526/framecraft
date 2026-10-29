# Flow: spoil

2 diagrams, read in this order:
1. ผู้ใช้วางลิงก์จนได้ Temp clip: หน้าเว็บ, API, Download job และ yt-dlp คุยกันยังไง
2. state ของ Download job และสิ่งที่เกิดกับไฟล์ในแต่ละทาง

All diagrams use the same names as [spec.md](spec.md).

## 1. วางลิงก์จนได้ Temp clip

```mermaid
sequenceDiagram
    actor U as ผู้ใช้
    participant W as tab สปอย
    participant A as Spoil API
    participant J as Download job (thread)
    participant Y as yt-dlp adapter

    U->>W: วางลิงก์ กด "โหลด"
    W->>A: POST /api/spoil/downloads
    A->>A: เช็ค not_ready, invalid_url, duplicate, busy
    alt ไม่ผ่านข้อใดข้อหนึ่ง
        A-->>W: 503 / 400 / 409 พร้อม code
        W-->>U: ข้อความตาม code
    else ผ่าน
        A->>J: เริ่มงาน state checking
        A-->>W: 202 Download job
        J->>Y: extract_info(download=False)
        Y-->>J: metadata
        J->>J: เช็ค live และดิสก์
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
