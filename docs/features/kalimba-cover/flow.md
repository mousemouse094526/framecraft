# Flow: kalimba-cover

2 diagrams, read in this order:
1. โน้ตทำนองเข้า Song ได้สองทาง: Pick job และไฟล์ MIDI
2. ฟังและ render reel เลือกทางตาม `instrument`

All diagrams use the same names as [spec.md](spec.md).

## 1. โน้ตทำนองเข้า Song

```mermaid
flowchart TD
    A[ผู้ใช้กด แกะ ที่หน้าเพลง] --> B[Pick job ถอดเสียงช่วงแกะ 22.05 kHz]
    B --> C{range.mode}
    C -->|drums| D[ADTOF: hits ของกลอง]
    C -->|melody| E[ข้ามไปใช้ผล Basic Pitch]
    D --> F[Basic Pitch ทีละหน้าต่าง]
    E --> F
    F --> G[score.melody_notes: notes พร้อม pitch หรือ null เมื่อ Basic Pitch พังในโหมดกลอง]
    F --> H{melody?}
    H -->|ใช่| I[score.melody_hits: hits เป็น snare]
    H -->|ไม่| J[hits จาก ADTOF]
    G --> K[Beat This!: beats และ downbeats]
    I --> K
    J --> K
    K --> L[analysis ใหม่ใน song.json มี hits และ notes]

    M[ผู้ใช้เลือกไฟล์ .mid] --> N[midi.read]
    N --> O{มี hits หรือ notes?}
    O -->|ไม่มีทั้งคู่ หรือไม่ใช่ 4/4| P[415 unsupported_file]
    O -->|มี| Q[analysis ของทั้งไฟล์: ช่อง 10 เป็น hits ช่องอื่นเป็น notes]
```

**analysis หนึ่งชุดมีทั้งการตีกลองและโน้ตทำนองได้อย่างไร**
- Basic Pitch รันครั้งเดียวต่อ Pick job ทั้งสองโหมด; พังในโหมดกลองไม่ทำให้งานพัง (D2, D14)
- ไฟล์ MIDI เดิมของเพลงที่ `notes` `null` นำเข้าซ้ำ → เติม `notes` ตอบเพลงเดิม (D14)
- `percent` ของ Pick job นับหน้าต่าง Basic Pitch ทุกโหมด (D2)
- `song.json` ที่แกะก่อน feature นี้ไม่มี `notes`: อ่านเป็น `null` ไม่ใช่ `[]` (D2)
- MIDI ยังต้องเป็น 4/4 tempo แรก ความยาว = ตัวสุดท้าย + 1 ห้อง (D3)

## 2. ฟังและ render reel ตามเครื่องดนตรี

```mermaid
flowchart TD
    A[ผู้ใช้กด ฟัง หรือ render reel] --> B[บันทึก cover ถ้ายังไม่บันทึก]
    B --> C[อ่าน cover.json ใต้ songs.lock แล้วดึงเข้าช่วง]
    C --> D{instrument}
    D -->|drums| E[drum_cover.timeline.build]
    E --> F[mixer.mix ถ้า drums.on]
    D -->|kalimba| G{notes_picked และ notes มากกว่า 0?}
    G -->|ไม่| H[409 no_notes]
    G -->|ใช่| I[kalimba_cover.timeline.build: arrange แล้วปัดเป็น sample]
    I --> J[sound.mix ถ้า kalimba.on]
    F --> K[reel_wav: ความดัง backing peak -1 dBFS]
    J --> K
    K --> L{ฟัง?}
    L -->|ใช่| M[ตอบ audio/wav]
    L -->|render| N[frames และ captions ของเครื่องดนตรีที่เลือก]
    N --> O[ffmpeg _command เดิม: mp4 .partial]
    O --> P[renders/ มี mp4 srt json พร้อม instrument]
```

**เสียงกับภาพของแต่ละเครื่องดนตรีอ่านจากไหน**
- ทุกเวลาของคาลิมบามาจาก `KalimbaTimeline`; ของกลองมาจาก `Timeline` เดิม (D6, ADR-0041)
- ลำดับ error ของ render: `404`/`no_analysis` → อ่าน cover (`400`) → `no_notes` → gate ตาม `instrument` (`503`) → `busy` → `507` (spec › Render job, D14)
- Render job slot เดียวสำหรับทั้งสองแบบ: งานซ้อน `409` `busy` (D8)
- ห้ามเงียบตรวจที่ `PUT` และอีกครั้งที่ `listen`/`render` สำหรับไฟล์ที่แก้มือ (D9, drum-cover D24)
