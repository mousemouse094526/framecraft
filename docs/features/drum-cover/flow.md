# Flow: drum-cover

3 diagrams, read in this order:
1. ทางเดินจากเพลงที่แกะไปเป็น reel: อะไรของเดิม อะไรของใหม่
2. Render job ของ reel ตั้งแต่กดจนได้ไฟล์ และเสียง backing เข้าตรงไหน
3. หน้าเพลงหลังแกะ: เมื่อไรบอกว่าช่วงไม่มีกลอง

All diagrams use the same names as [spec.md](spec.md).

## 1. จากเพลงที่แกะไปเป็น reel

```mermaid
flowchart LR
  subgraph notes["drum-notes (ของเดิม)"]
    direction LR
    Song["Song<br/>song.json + audio.m4a"] -->|Pick job| Analysis["analysis<br/>hits, beats, downbeats"]
  end
  subgraph cover["drum-cover (ใหม่)"]
    direction LR
    Cover["cover.json<br/>ช่วง ข้อความ พื้นหลัง backing"]
    Build["drum_cover.timeline.build"]
    Timeline["Timeline<br/>ของ video-gen"]
    Cover -->|ช่วงและข้อความ| Build
    Build -->|การตีจริง + มือ D5| Timeline
  end
  subgraph gen["video-gen (ของเดิม)"]
    direction LR
    Mixer["mixer"] -->|audio.wav| FF["ffmpeg"]
    Frames["frame_at + captions"] -->|rgb24 + text.ass| FF
  end
  Analysis -->|hits ในช่วง| Build
  Timeline --> Mixer
  Timeline --> Frames
  FF -->|mp4| Renders["renders/ ใต้เพลง"]
```

**reel ใช้ของเดิมสองข้าง: `analysis` จาก drum-notes เข้า และ mixer/frames ของ video-gen ออก; ของใหม่คือ `cover.json` กับตัวแปลงเป็น `Timeline`**
- บทเรียนกลอง (`drum_notes.lesson` → `video_gen.lessons`) ยังอยู่เป็นทางออกที่สองของ `analysis` ไม่อยู่ในภาพ (D1, D11)
- `Timeline` ตัวเดียวขับทั้งเสียงและภาพ reel จึงตรงกันเท่าคลิปสอน (D4, ADR-0041)
- Lesson ชั่วคราวหนึ่งท่อนถือหัวเรื่อง บรรทัดรอง คำบรรยาย พื้นหลัง ให้ `frames` และ `captions` อ่าน (D4)
- `cover.json` และ `renders/` อยู่ใน folder ของเพลงและหายตามเพลง (D2)

## 2. Render job ของ reel

```mermaid
sequenceDiagram
  participant Web as หน้า reel
  participant API as /api/songs/{id}/cover
  participant Job as Render job thread
  participant FF as ffmpeg
  Web->>API: POST /render {}
  API->>API: เพลง, analysis, gate drums, busy, cover ที่ดึงเข้าช่วง, ดิสก์
  API->>API: copy song.json + cover.json + ภาพ เข้า .render/
  API-->>Web: 202 rendering
  API->>Job: เริ่มงาน
  Job->>Job: timeline.build, mixer → audio.wav, captions → text.ass, Scene
  Job->>FF: run_piped (rawvideo stdin + audio.wav + audio.m4a เมื่อ backing เปิด)
  loop ทุกเฟรม
    Job->>FF: frame_at(t) เป็น rgb24
  end
  FF-->>Job: จบ (exit 0)
  Job->>Job: renders.Render.finish (srt, json มี backing)
  Web->>API: GET /api/covers/render ทุก 1 วินาที
  API-->>Web: done + result
```

**ระหว่างกด render จนได้ไฟล์ เกิดอะไรตามลำดับ และ backing เข้าทาง ffmpeg ไม่ใช่ทาง `Timeline`**
- การตรวจทั้งหมดเกิดก่อน `202`; ลำดับและ error code อยู่ใน spec › Render job (D12)
- backing ปิด: ffmpeg มีเสียงแค่ `audio.wav`; เปิด: `audio.m4a` ช่วง `[start_s, end_s)` ผ่าน `volume` แล้ว `amix` ใต้กลอง (D7)
- งานใช้สำเนาใน `media/songs/.render/`; `PUT /cover` ระหว่างงานถึงงานถัดไป (D12)
- ลบเพลงระหว่างงาน → `409` `song_busy`; `audio.m4a` จึงอ่านที่เดิมได้ (D2, D12)
- state `rendering` → `done` | `failed` | `cancelled` เหมือน Render job ของ video-gen (D12)

## 3. หน้าเพลงหลังแกะ

```mermaid
flowchart TB
  Done["Pick job done"] --> Any{"มีการตี<br/>ในช่วงไหม"}
  Any -->|ไม่มี| NoneAlert["Alert: ไม่พบการตีกลอง<br/>ในช่วง start–end"]
  Any -->|มี| First{"ห้องที่พบ<br/>ตัวแรกว่างไหม"}
  First -->|ว่าง k ห้อง| Gap["Alert: ห้อง 1–k ไม่มีการตี<br/>การตีแรกที่ t"]
  Gap -->|กด เริ่มช่วงที่การตีแรก| Repick["PUT /range ช่วงใหม่<br/>แล้ว POST /pick"]
  First -->|ไม่ว่าง| Reel["ส่วน Reel cover<br/>ปุ่ม ทำ reel cover"]
  Gap --> Reel
  Repick --> Done
```

**หลังแกะ หน้าเพลงตอบสามแบบ: ไม่มีกลองเลย, กลองเข้าช้า, หรือพร้อมทำ reel; กลองเข้าช้าก็ยังทำ reel ได้ (ค่าตั้งต้นของ reel เริ่มที่การตีแรกอยู่แล้ว)**
- ทุกค่าคำนวณบนหน้าเว็บจาก `bars[].hits` และ `analysis.hits` ไม่มี API ใหม่ (D9)
- ช่วงใหม่ = ต้นห้องแรกที่มีการตี (ปัดลง 0.1) ถึง + ความยาวเดิม จำกัดที่ `duration_s` (D9)
- ลูป `Repick → Done` คือ Pick job รอบใหม่ ซึ่งแสดงแถบ % ตามเดิมของ drum-notes
- ส่วน "สร้างบทเรียน" ยังอยู่ใต้ส่วน Reel cover ไม่อยู่ในภาพ (D11)
