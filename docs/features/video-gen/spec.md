# Spec: video-gen

tab "สอนกลอง" ให้ผู้ใช้กรอกโน้ตกลอง แล้วแอปทำคลิปสอนกลองแนวตั้ง 1080×1920 ที่ชุดกลอง เลนโน้ต และตัวนับจังหวะขยับตรงกับเสียงกลองที่แอปผสมเอง.

**Status:** ready-to-build

## Problem

ผู้ใช้อยากทำคลิปสอนกลองแบบเพจ Your Turn (ไดอะแกรมชุดกลองที่ไม้ตีตามจังหวะ, โน้ตเลื่อน, ตัวนับ, ป้ายท่อน) แต่ framecraft ทำได้แค่คลิปสปอยกับการ์ตูนเล่า; ทำมือในโปรแกรมตัดต่อต้องวางทุกการตีให้ตรงเสียงทีละจุด.

## Solution

- สร้าง ทำซ้ำ และลบบทเรียนกลองในรายการ (D10)
- กรอก Groove 1–4 ห้องบนตาราง 16 ช่องต่อห้อง พร้อมไม้ R/L และลักษณะตีของแต่ละโน้ต (D2, D5, D20)
- แบ่งเป็นท่อนสอน 1–6 ท่อน ตั้งป้าย คำอธิบาย ชิ้นที่เน้น รอบ และความเร็วต่อท่อน (D4)
- ฟังเสียงกลองของทั้งคลิปก่อน render (D8)
- render เป็น mp4 พร้อม `.srt` เก็บทุกครั้ง เล่น โหลด ลบได้ (D10, D14)
- ใช้พื้นหลังสีเข้มของแอป หรือภาพของตัวเอง (D6)

## User Stories

**ผู้ทำคลิป**
1. As a ผู้ทำคลิป, I want กรอกโน้ตกลองของท่อนเพลงบนตาราง, so that ไม่ต้องวางการตีให้ตรงเสียงเองทีละจุด (D2, D5, D20)
2. As a ผู้ทำคลิป, I want ฟังจังหวะที่กรอกก่อน render, so that รู้ว่ากรอกผิดก่อนเสียเวลา render (D8)
3. As a ผู้ทำคลิป, I want แบ่งคลิปเป็นท่อนสอนที่เน้นทีละชิ้นกลองและช้าลงได้, so that ผู้ชมฝึกทีละส่วนได้ (D4)
4. As a ผู้ทำคลิป, I want render เป็น mp4 แนวตั้งที่ภาพกับเสียงตรงกัน, so that โพสต์ลง reels ได้ทันที (D14)
5. As a ผู้ทำคลิป, I want เก็บบทเรียนกลองหลายเพลงและผล render ทุกครั้ง, so that แก้แล้ว render ใหม่ได้โดยไม่เสียงานเก่า (D10)
6. As a ผู้ทำคลิป, I want ใช้ภาพของตัวเองเป็นพื้นหลัง, so that คลิปแต่ละเพลงหน้าตาไม่ซ้ำกัน (D6)

## Design

แบบหน้าจอทำใน Figma หลัง plan (setup-status D9). ทุกหน้าใต้ `#/drums` อ่าน `GET /render` ตอนเปิดและติดตามงานที่รันอยู่ (D22).

| Screen | User stories | Must show | Source |
|---|---|---|---|
| รายการบทเรียนกลอง (`#/drums`) | 5 | บทเรียนเรียงตาม `updated_at` ใหม่สุดก่อน: หัวเรื่อง, ความยาวคลิป, จำนวนผล render, เวลาแก้ล่าสุด; แถวที่กำลัง render มีป้ายพร้อม % (D22); ปุ่มสร้างใหม่ (ถามหัวเรื่อง), ทำซ้ำ, ลบ (ถามยืนยัน บอกจำนวนผล render ที่จะหาย) (D10); ว่าง: ข้อความชวนสร้างบทเรียนแรก; error ของลบ: `lesson_busy` "กำลัง render บทเรียนนี้อยู่", `in_use` | pending |
| หน้าแก้บทเรียนกลอง (`#/drums/{id}`) | 1, 2, 3, 6 | ข้อมูล: หัวเรื่อง, บรรทัดรอง, คำบรรยาย, BPM 40–240 (D4); พื้นหลัง: สีของแอปหรือเลือก PNG/JPG, ลบภาพ, ข้อความข้างปุ่ม "ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม" (D6, D23); ตาราง Groove: แถว = ชิ้นกลอง 10 ชิ้นเรียงตามเลนโน้ต, คอลัมน์ = 16 ช่องต่อห้อง หัวคอลัมน์ 1 e & a, เพิ่มและลดห้อง 1–4 (ลดห้องลบโน้ตที่เลยห้องสุดท้ายหลังถาม) (D5, D22); กดช่องว่าง = เพิ่มโน้ตปกติด้วยมือที่ว่างในช่องนั้น (R ก่อน), ช่องที่สองมือไม่ว่างกดไม่ได้ (D20); กดโน้ต = เลือก, กล่องของโน้ตที่เลือกตั้งไม้ R/L และลักษณะตี และลบได้, ตัวเลือกที่ทำให้มือชนกันกดไม่ได้ (D20); ชิ้นของเท้าไม่มีตัวเลือกไม้และ flam (D20); รายการท่อนสอน: ป้าย (คำบอก "ว่าง = แสดงหัวเรื่อง"), คำอธิบาย, ชิ้นที่เน้น (เลือกหลายอัน), รอบ 1–8, ความเร็ว 50–100% ทีละ 5, เพิ่ม ลบ เลื่อนขึ้นลง (D4, D22); ความยาวคลิปรวมกับเพดาน 90 วินาที เกินแล้วบอกว่าเกินกี่วินาที บันทึกได้ แต่ฟังจังหวะและ render กดไม่ได้ (D16, D21); ปุ่มบันทึก ถามก่อนออกเมื่อยังไม่บันทึก (story-kb D11); "ฟังจังหวะ": บันทึกก่อน แล้วปุ่มเป็น "กำลังผสมเสียง…" กดไม่ได้จนเล่น, error ใต้ปุ่ม, `not_ready` แสดง `fix` ของแถว (D8, D22, setup-status D26); render: บันทึกก่อนแล้วเริ่มงาน แถบ % และยกเลิก, `failed` หรือ `cancelled` แสดงข้อความกับปุ่มลองอีกครั้ง, เสร็จแล้วพาไปหน้าผล (D14, D22); error: `invalid_request` ที่ช่อง (`field`), `too_long`, `not_ready`, `busy` บอกบทเรียนที่ render อยู่ | pending |
| ผล render ของบทเรียน (`#/drums/{id}/renders`) | 4, 5 | ผล render ใหม่สุดก่อน: เวลาสร้าง, ความยาว, player 9:16, โหลด mp4 และ `.srt`, ลบ (ถามยืนยัน; `in_use` เมื่อไฟล์ยังเปิดอยู่) (D10); มาจาก render ที่เพิ่งจบ = เลือกผลล่าสุด; บทเรียนนี้กำลัง render = แถบ % ด้านบน; ว่าง: ข้อความว่ายังไม่เคย render | pending |

Pending screens: one design prompt in [ui-prompt.md](ui-prompt.md).

## Expected Outcome

ผู้ใช้กรอกโน้ตของ fill หรือ groove หนึ่งท่อน แล้วได้คลิปสอนกลองแนวตั้งที่พร้อมโพสต์ โดยไม่เปิดโปรแกรมตัดต่อ.

- **กรอกเสร็จแล้วฟัง:** กด "ฟังจังหวะ" ได้ยินนับเข้า 1 ห้อง แล้วกลองทุกท่อนตามความเร็วของแต่ละท่อน ภายใน 5 วินาทีสำหรับคลิป 90 วินาที
- **render:** แถบ % เดินจนจบ แล้วเห็นคลิปที่ไม้ตีชิ้นกลองตรงกับเสียงทุกครั้ง ป้ายของท่อนขึ้นแทนหัวเรื่องตลอดท่อนและชิ้นที่ไม่เน้นหรี่

**How success is judged:**
- ทำคลิปที่หน้าตาเทียบได้กับคลิปอ้างอิง (Smells Like Teen Spirit intro fill, 19 วินาที, path ใน [kit-sketch.md](kit-sketch.md)) จากโน้ตที่กรอกในแอป เจ้าของดูแล้วรับ
- ในคลิปที่ render: เฟรมแรกที่วงแหวนการตีของโน้ตขึ้น กับจุดเริ่มเสียงของโน้ตนั้นใน mp4 ห่างไม่เกิน 1 เฟรม (D14; test ใน Seams 1)
- คลิป 30 วินาที render จบใน ≤ 60 วินาทีบน Mac Apple Silicon (D14)
- render บทเรียนเดิมสองครั้งได้ `audio.wav` เหมือนกันทุก byte (D13)

## Implementation

### Modules touched

- **`backend/video_gen`** (package ใหม่)
  - `lessons`: อ่าน เขียน ตรวจค่า บทเรียนกลอง ใต้ lock เดียว (D10, D16, D20)
  - `kit`: ตารางชิ้นกลอง (เลน, สี, folder ของ sample) และตำแหน่งตาม [kit-sketch.md](kit-sketch.md) (D11, D17)
  - `timeline`: แปลงบทเรียนเป็นตารางเวลา — การตีทุกครั้ง (เวลา, ชิ้น, มือ, ชั้นความแรง, round-robin), ต้นจังหวะ, ช่วงของท่อนสอน, `length_s`; ที่เดียวที่ทั้งเสียงและภาพอ่านเวลา (D2, D15, D21)
  - `mixer`: ผสม sample ตามตารางเวลาเป็น wav 44.1 kHz stereo (D2, D8, D19)
  - `frames`: `Scene` (ชั้นนิ่งที่วาดครั้งเดียวต่อ render) และ `frame_at(scene, t)` วาดชั้นที่ขยับ (D3, D17, D18)
  - `captions`: ไฟล์ ASS ของหัวเรื่อง ป้าย ตัวนับ คำบรรยาย ตัว L/R และเลขจังหวะ, และ `.srt` ผ่าน `backend.subtitles` (D3, D22)
  - `render`: Render job (D14)
- **`backend.ffmpeg`**: `run_piped(command, cwd, cancel, frames, on_frame)` ใหม่ และ `h264_args(platform)` ที่ย้ายการเลือก encoder ออกจาก `backend.spoil.trim` ให้ trim ใช้ด้วย (D22, spoil D36)
- **`backend.drum_kit`** (module ใหม่ ข้าง `backend.fonts`): ตารางไฟล์ sample พร้อม sha256, `install`, `check` ของแถว `drum_kit` (D11, D19)
- **`backend.setup`**: โหลด sample ที่ขาดหลัง Kanit (D11)
- **`backend.checks`**: แถว `drum_kit` ต่อจาก `font_kanit` (D11, ADR-0009)
- **`backend.gate_rows`**: `drums(project)` = `drum_kit`, `font_kanit`, `ffmpeg`, `pythainlp` (D11, D22)
- **`backend.paths`**: `drums_dir` (`media/drums/`), `drum_samples_dir` (`models/drums/`) (D10, D11)
- **`backend.routes`**: router ใหม่ `video_gen` prefix `/drums` (D9)
- **`pyproject.toml`**: pin `pillow` และ `soundfile` เป็น dependency ตรงตามรุ่นใน `uv.lock` (D3)
- **`frontend/src/features/video-gen`**: 3 หน้าใต้ `#/drums` (D9); `App` และ `useHash` รู้จัก tab `drums` ต่อท้าย `toon`

### Data

ไฟล์ใน `media/drums/` (D10):

| Path | Holds |
|---|---|
| `lessons/{lesson_id}/lesson.json` | บทเรียนกลอง (schema ด้านล่าง) เขียนแบบ `write_atomic` |
| `lessons/{lesson_id}/background.jpg` | ภาพพื้นหลังที่ครอป 1080×1920 แล้ว (ยังไม่เบลอ) หรือไม่มี |
| `lessons/{lesson_id}/renders/` | ผล render ตาม `backend.renders` |
| `.render/` | work folder ของ Render job ที่กำลังรัน ล้างตอน start |

`lesson_id` เป็น 12 ตัวอักษร `[a-z0-9]` สุ่ม; ทุก route เช็ค `fullmatch` ก่อนสร้าง path ไม่ตรง = `404` `not_found` (D22). Schema ของ `lesson.json`:

```json
{
  "version": 1,
  "id": "k3v9x0a1b2c4",
  "title": "SMELLS LIKE TEEN SPIRIT",
  "subtitle": "Nirvana · how to play the intro fill",
  "caption": "Wait for the snare roll",
  "bpm": 116,
  "background": "image",
  "groove": {
    "bars": 2,
    "notes": [{ "piece": "snare", "step": 0, "hand": "R", "hit": "flam" }]
  },
  "chapters": [
    { "label": "KICK", "text": "On 1e, 1a, 2e, 2a", "focus": ["kick"], "repeats": 2, "speed": 75 }
  ],
  "updated_at": "2026-11-13T10:30:00+07:00"
}
```

| Field | Rule |
|---|---|
| `title` | 1–40 ตัวอักษร (นับ code point แบบ story-kb D12) |
| `subtitle`, `caption` | 0–60 ตัวอักษร; ว่าง = ไม่แสดง |
| `bpm` | จำนวนเต็ม 40–240 |
| `background` | `"color"` หรือ `"image"`; `"image"` ต้องมี `background.jpg` |
| `groove.bars` | 1–4 |
| `groove.notes` | 0 ตัวขึ้นไป; 0 = นับเข้าแล้วเงียบ (D22) |
| `groove.notes[].piece` | id ใน `kit` (ตาราง Drum kit) |
| `groove.notes[].step` | 0 ถึง `bars × 16 − 1`; คู่ (`piece`, `step`) ไม่ซ้ำ |
| `groove.notes[].hand` | `"R"`, `"L"` สำหรับชิ้นของมือ; `null` สำหรับ `kick`, `hihat_pedal` |
| `groove.notes[].hit` | `normal`, `accent`, `ghost`, `flam`; `flam` เฉพาะชิ้นของมือ |
| ช่องเดียวกัน (`step`) | มือเดียวตีได้ชิ้นเดียว; โน้ตมือไม่เกินสองตัว; ไม่มี `hihat_open` คู่ `hihat_closed`; `flam` ต้องเป็นโน้ตมือตัวเดียวของช่อง (D20) |
| `chapters` | 1–6 ท่อน |
| `chapters[].label` | 0–16 ตัวอักษร; ว่างในท่อนแรก = แสดงหัวเรื่อง (D12) |
| `chapters[].text` | 0–60 ตัวอักษร |
| `chapters[].focus` | id ใน `kit` ไม่ซ้ำ; ว่าง = ทุกชิ้นสว่าง (D13) |
| `chapters[].repeats` | 1–8 |
| `chapters[].speed` | 50–100 ทีละ 5 |

ค่าไม่ผ่าน = `400` `invalid_request` พร้อม `field` (เช่น `groove.notes[3]`).

`length_s` = นับเข้า `4 × 60 / (bpm × speed₁/100)` + ผลรวมทุกท่อนของ `repeats × bars × 4 × 60 / (bpm × speed/100)` + หางเสียง 1.5 วินาที (D21). `length_s` > 90 บันทึกได้ แต่ฟังจังหวะและ render ตอบ `422` `too_long` (D16).

บทเรียนใหม่ (D22, D23):
- Groove ร็อกพื้นฐาน 1 ห้อง: `hihat_closed` ทุก 8th ไม้ R, `snare` จังหวะ 2 กับ 4 ไม้ L, `kick` จังหวะ 1 กับ 3
- BPM 100, พื้นหลัง `color`
- ท่อนที่ 1: ป้ายว่าง (แสดงหัวเรื่อง) รอบ 2 ความเร็ว 100
- ท่อนที่ 2: ป้าย `ลองเล่นเอง` รอบ 2 ความเร็ว 100

### Drum kit

10 ชิ้นกลอง sample จาก Big Rusty Drums ไมค์ใกล้ (D11). สีตามคลิปอ้างอิง (D12). ตำแหน่งบนไดอะแกรม จุดกระทบ และหัวโน้ตใน [kit-sketch.md](kit-sketch.md) (D17).

| `piece` | เลนโน้ต | สี | sample (ใต้ repo) | มือ/เท้า |
|---|---|---|---|---|
| `hihat_closed` | ฉาบ | เหลือง `#E8C547` | `hihat_14/cl` | มือ |
| `hihat_open` | ฉาบ | เหลือง `#E8C547` | `hihat_14/open` | มือ |
| `crash` | ฉาบ | ส้ม `#E8894A` | `crash_17/cr` | มือ |
| `ride` | ฉาบ | ส้ม `#E8894A` | `ride_22/rd` | มือ |
| `snare` | กลาง | ฟ้า `#4A7FE8` | `snare_14/center` | มือ |
| `tom_high` | กลาง | เขียวน้ำเงิน `#2E8C82` | `tom_14/center` | มือ |
| `tom_mid` | กลาง | เขียวน้ำเงิน `#2E8C82` | `tom_15/center` | มือ |
| `tom_floor` | กลาง | ม่วง `#6B4FC2` | `tom_18/center` | มือ |
| `kick` | ล่าง | แดง `#E84A6B` | `kick_24/kick` | เท้าขวา `RF` |
| `hihat_pedal` | ล่าง | เหลือง `#E8C547` | `hihat_14/chik` | เท้าซ้าย `LF` |

- Setup script โหลดเฉพาะชั้นเบาสุด กลาง แรงสุด ของแต่ละชิ้น ทุก round-robin ไมค์ `cl` (snare ไมค์ `top`, kick ไมค์ `kick`: ไม่มี `cl`) ลง `models/drums/` ตาม path ใต้ `Samples/` ของ repo (D19, D26)
- ตาราง (`piece`, ชั้น `soft`/`mid`/`hard`, round-robin, path, sha256) อยู่ใน `backend.drum_kit`; ticket แรกสร้างจาก `.sfz` ของ repo ที่ commit ที่ pin (D19)
- ไม่มีไฟล์ใด = แถว `drum_kit` เป็น `missing` พร้อม `fix` คำสั่ง Setup script (setup-status D26)
- `chik` เป็นไฮแฮทเท้า และทอม 14/15/18 เป็นสูง กลาง ต่ำ — ตรวจแล้วใน D30 (Open Question 1)

### Timeline and audio

1. ท่อนสอนเรียงกัน; ท่อนหนึ่งเล่น Groove `repeats` รอบที่ BPM `bpm × speed / 100`
2. นับเข้า 1 ห้องที่ความเร็วของท่อนแรก: `hihat_closed` ชั้น `soft` ทุกจังหวะ ตัวนับขึ้น 1–4 (D13)
3. เวลาของโน้ต = ต้นห้อง + `step × (60 / BPM ของท่อน) / 4`
4. ชั้นความแรง: `accent` = `hard`, `normal` = `mid`, `ghost` = `soft`; `flam` = โน้ตนำ `soft` มืออีกข้าง 0.03 วินาทีก่อน + โน้ตหลัก `mid` (D13)
5. round-robin วนตามลำดับการตีของชิ้นและชั้นนั้นตั้งแต่ต้นคลิป (render ซ้ำได้ wav เดิม) (D13)
6. `mixer` อ่าน FLAC ด้วย `soundfile` ครั้งเดียวต่อไฟล์ต่องาน, ผสมที่ 44.1 kHz ด้วย numpy float32, ไฮแฮทเปิดถูกตัดด้วยไฮแฮทปิดหรือเท้าตัวถัดไป (fade 10 ms), ปรับทั้งคลิปให้ peak −1 dBFS แล้วเขียน wav 16-bit ยาว `length_s` (D19, D21)
7. เวลาที่ใช้ทั้งเสียงและภาพปัดเป็น sample ที่ 44.1 kHz ครั้งเดียวใน `timeline`

### Layout

ทุกค่าที่ 1080×1920 (D12). วาดด้วย Pillow (กราฟิก) หรือ ASS (ตัวหนังสือ) (D3).

| ชั้น | ตำแหน่ง | วาดด้วย | เนื้อหา |
|---|---|---|---|
| พื้นหลัง | ทั้งจอ | Pillow, ครั้งเดียว | `color`: กรมท่า `#0E1A2B` ไล่ลง `#07090D`; `image`: ภาพ blur รัศมี 24 แล้วทับดำ 55% |
| หัวเรื่อง | กล่องขาวมุมซ้ายบน x 54, y 240 สูง 84 | ASS | `title` ตัวดำ Kanit Bold 64 บรรทัดเดียว กว้างเกิน 860 px ย่อด้วย `\fscx`; บรรทัดรอง `subtitle` ขาว 34 ที่ y 340 ไม่เกิน 2 บรรทัด (D22) |
| ป้ายท่อนสอน | ที่เดียวกับหัวเรื่อง | ASS | `label` บนกล่องสีของชิ้นที่เน้นชิ้นแรก (ไม่มีชิ้นที่เน้น = กล่องขาวตัวดำ) แทนหัวเรื่องตลอดท่อน; `text` แทนบรรทัดรอง (D12) |
| ตัวนับจังหวะ | ขวาบน x 1000 (ชิดขวา), y 282 | ASS | เลข 1–4 ขาว 72 เปลี่ยนต้นจังหวะ (D13) |
| ไดอะแกรมชุดกลอง | y 390–1170 | Pillow, ครั้งเดียวต่อชุดชิ้นที่เน้น | ตาม [kit-sketch.md](kit-sketch.md); ชิ้นไม่เน้น 35% (D13, D17, D18) |
| ไม้กลองและวงแหวน | บนไดอะแกรม | Pillow, ทุกเฟรม | การขยับตาม [kit-sketch.md](kit-sketch.md) › ไม้กลอง (D13) |
| วง L และ R | x 816 และ 900, y 1149 | Pillow + ASS | วงที่มือกำลังตีสว่าง อีกวงจาง |
| เลนโน้ต | y 1245–1575, กว้าง 54–1026 | Pillow + ASS | เส้นเลนและช่องวาดครั้งเดียว; หัวโน้ตตาม kit-sketch วาดทุกเฟรม; เลขจังหวะ 2 3 4 และ `BAR` ด้านบน (ASS); playhead เส้นขาวนิ่งที่ x 250; หน้าต่างกว้าง 1.5 ห้องของความเร็วท่อนปัจจุบัน (D13) |
| คำบรรยาย | ซ้ายล่าง x 54, y 1656 | ASS | `caption` ขาว 40 ไม่เกิน 2 บรรทัด ตลอดคลิป (D22) |

- ของที่ขยับ (ไม้ วงแหวน หัวโน้ต playhead วง L/R) วาดเป็นชิ้นเล็กที่ 2 เท่าแล้วย่อแปะบนชั้นนิ่ง (D18)
- ตัดบรรทัดด้วย `subtitles.cut_lines` (ตัดคำไทยด้วย pythainlp); วัดความกว้างหัวเรื่องด้วย `ImageFont.getlength` ของ Kanit Bold (D22)
- ช่วงหางเสียง 1.5 วินาที ภาพค้างที่ท่อนสุดท้าย ไม้อยู่จุดพัก (D21)

### Render job

หนึ่งงานต่อครั้ง `JobSlot` ของตัวเอง ไม่จองช่อง GPU (D14). thread ใน backend (ADR-0010).

1. ตรวจ body (`lesson_id`) → `400` `invalid_request`
2. `gate_rows.drums` ไม่ ok → `503` `not_ready`
3. มี Render job ของ tab นี้รันอยู่ → `409` `busy` (มี `lesson_id` ของงานนั้น)
4. อ่านบทเรียนครั้งเดียว: ไม่พบ → `404` `not_found`; `length_s` > 90 → `422` `too_long` (D16)
5. `disk.require_free` ด้วย `length_s × 2 MB` → `507` `disk_full`
6. copy `lesson.json` และ `background.jpg` เข้า `.render/` ใต้ lock ของบทเรียน (แก้ระหว่าง render ไม่มีผลกับงานนี้, ทางเดียวกับ ADR-0024) แล้วตอบ `202` และทำต่อใน thread (D33)
7. `timeline` → `mixer` เขียน `audio.wav`; `captions` เขียน `text.ass`; สร้าง `Scene` (ชั้นนิ่ง) (D18)
8. `ffmpeg.run_piped`: rawvideo `rgb24` 1080×1920 30 fps จาก stdin + `audio.wav`, filter `ass` (Kanit ผ่าน `fontsdir`), `h264_args`, aac 48 kHz, เขียน `{name}.mp4.partial`; ส่ง `frame_at` ของเฟรม 0 ถึง `ceil(length_s × 30) − 1`; `percent` = เฟรมที่ส่ง / เฟรมทั้งหมด (D21, D22)
9. `renders.Render.finish` เขียน `.srt` (ป้ายและคำบรรยายตามเวลา) กับ `.json` (`lesson_id`, `title`, `length_s`, `created_at`)

| State | ความหมาย |
|---|---|
| `rendering` | กำลังวาดและ encode, `percent` 0–100 |
| `done` | มีผลใน `renders/`; `result` = ชื่อ render |
| `failed` | `error` = `ffmpeg_failed` (มีบรรทัดท้ายของ stderr ใน `message`) หรือ `internal` |
| `cancelled` | ผู้ใช้ยกเลิก; kill ffmpeg ลบ `.partial` |

`run_piped` (D22):
- thread หนึ่งอ่าน stderr เก็บบรรทัดท้าย; thread ของงานเขียนเฟรมและเช็ค `cancel` ก่อนทุกเฟรม
- เขียน stdin พัง (`BrokenPipeError`, บน Windows `OSError`) ตอน `cancel` ตั้งอยู่ → `Cancelled`; ไม่ได้ยกเลิก → รอ process จบแล้ว `FfmpegFailed` พร้อมบรรทัดท้ายของ stderr
- ffmpeg จบด้วย code ไม่ใช่ 0 → `FfmpegFailed`

restart ระหว่างรัน: start ล้าง `.render/` และ `.partial` ทั้งหมด (`renders.remove_partials`).

### API

ทุก route อยู่ใต้ `/api/drums`. `POST`/`PUT` ต้องเป็น JSON (ADR-0013) ยกเว้น route ภาพที่รับ `application/octet-stream` (ADR-0028). error เป็น `{code, message}` (spoil-maker D63). `{id}` ไม่ตรงรูปแบบ = `404` `not_found` (D22).

| Method | Path | ทำอะไร | Error |
|---|---|---|---|
| `GET` | `/lessons` | รายการ: `id`, `title`, `length_s`, `renders`, `updated_at`; ข้าม `lesson.json` ที่อ่านไม่ได้ (log) | — |
| `POST` | `/lessons` | `{title}` → `201` บทเรียนใหม่ค่าตั้งต้น | `400` `invalid_request` |
| `POST` | `/lessons/{id}/copy` | `201` สำเนา หัวเรื่อง + " (สำเนา)" ตัดที่ 40 ไม่ copy ผล render | `404` `not_found` |
| `GET` | `/lessons/{id}` | บทเรียนเต็ม + `length_s` | `404` `not_found` |
| `PUT` | `/lessons/{id}` | ทับทั้งบทเรียน (ยกเว้น `id`, `version`, `updated_at`); ยาวเกินบันทึกได้ (D16) | `400` `invalid_request` (มี `field`), `404` |
| `DELETE` | `/lessons/{id}` | `204` ลบผล render ทีละอัน แล้ว `background.jpg` แล้ว `lesson.json` สุดท้าย แล้ว folder; ลบได้แม้ `lesson.json` อ่านไม่ได้ (D22) | `409` `lesson_busy`, `409` `in_use` (ไฟล์ที่ลบแล้วไม่กลับ), `404` |
| `PUT` | `/lessons/{id}/background` | body ดิบ PNG/JPG ≤ 20 MB → `exif_transpose` แล้วครอป 1080×1920 (`ImageOps.fit`) เก็บ jpg, ตั้ง `background` = `image` | `413` `file_too_large`, `415` `unsupported_image`, `409` `lesson_busy` |
| `DELETE` | `/lessons/{id}/background` | ลบภาพ ตั้ง `background` = `color` | `409` `lesson_busy` |
| `POST` | `/lessons/{id}/listen` | `{}` → `audio/wav` ยาว `length_s` `Cache-Control: no-store` (D8, D21) | `503` `not_ready` (`drum_kit`), `422` `too_long`, `404` |
| `POST` | `/render` | `{lesson_id}` → `202` งาน | ตาม Render job |
| `GET` | `/render` | งานล่าสุด: `state`, `lesson_id`, `percent`, `result`, `error`, `message` หรือ `null` | — |
| `POST` | `/render/cancel` | `{}` → งาน | `409` `not_running` |
| `GET` | `/lessons/{id}/renders` | ผลเรียงใหม่สุดก่อน (`renders.listed`) | `404` |
| `GET` | `/lessons/{id}/renders/{name}.mp4` และ `.srt` | ไฟล์ | `404` `not_found` |
| `DELETE` | `/lessons/{id}/renders/{name}` | `204` | `409` `in_use`, `404` |

`lesson_busy` = Render job ที่ยังไม่จบเป็นของบทเรียนนี้. `PUT /lessons/{id}` ระหว่าง render ของบทเรียนเดียวกันทำได้ (งานใช้สำเนา ข้อ 6).

### Status check and Setup

- แถว `drum_kit` (label "Drum samples") ok เมื่อ marker ใน `paths.markers_dir` ตรงตารางไฟล์และทุกไฟล์มีอยู่; ค่าแสดง `Big Rusty Drums · f07ce00` (D11, D22)
- Setup script เขียน marker หลังโหลดครบและ sha256 ตรงทุกไฟล์ (แบบ Kanit, ADR-0004); การเช็คของ Status check ไม่เขียนอะไร
- Setup script โหลดไฟล์ที่ขาดหรือ hash ไม่ตรง ลอง 3 ครั้งต่อไฟล์; พังหนึ่งไฟล์ = Setup จบด้วย error ที่บอกชื่อไฟล์ ไม่เขียน marker

### Frontend

- `frontend/src/features/video-gen` มี `DrumsPage` ที่เลือกหน้าตาม hash: `#/drums`, `#/drums/{id}`, `#/drums/{id}/renders`; hash อื่นใต้ `#/drums` = รายการ
- ทุกหน้าอ่าน `GET /render` ตอนเปิด; poll ทุก 1 วินาทีระหว่าง `rendering` (`usePollWhile`); พาไปหน้าผลเฉพาะหน้าที่กดเริ่มงาน (D22)
- ตัวกันออกเมื่อยังไม่บันทึกใช้แบบเดียวกับหน้าแก้ Story (story-kb D11, D16)
- "ฟังจังหวะ" เล่น wav ด้วย `<audio>` จาก blob URL; กดใหม่ระหว่างเล่นหยุดของเดิมก่อน
- ตารางคำนวณมือที่ว่างของแต่ละช่องจากโน้ตในช่องนั้นด้วยกฎเดียวกับ `PUT` (D20)

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| Pillow | 12.3.0 | `ImageDraw` วาด `ellipse`, `polygon`, `line(width=)`, `rounded_rectangle` บน RGBA; `Image.alpha_composite`, `paste` ด้วย mask; `resize(LANCZOS)`; `tobytes()` เป็น RGB ดิบ | [ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html), [Image](https://pillow.readthedocs.io/en/stable/reference/Image.html) |
| Pillow | 12.3.0 | `ImageFilter.GaussianBlur`; `ImageOps.fit`, `ImageOps.exif_transpose`; `Image.open(formats=["PNG", "JPEG"])` | [ImageFilter](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html), [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html) |
| Pillow | 12.3.0 | `ImageFont.truetype(...).getlength(text)` วัดความกว้างหัวเรื่องเป็น px | [ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html) |
| ffmpeg | 7.1 (imageio-ffmpeg 0.7.0) | demuxer `rawvideo` อ่าน `-f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i -` จาก stdin | [rawvideo demuxer](https://ffmpeg.org/ffmpeg-formats.html#rawvideo) |
| ffmpeg | 7.1 | filter `ass` กับ `fontsdir` วาด Kanit พร้อม Thai shaping | [ass filter](https://ffmpeg.org/ffmpeg-filters.html#ass) |
| soundfile | ตาม `uv.lock` | `soundfile.read` อ่าน FLAC 16-bit เป็น numpy float; `soundfile.write` เขียน wav `PCM_16` | [soundfile](https://python-soundfile.readthedocs.io/en/latest/) |
| numpy | ตาม `uv.lock` | รวมเสียงด้วยการบวก array แบบ float32 | [numpy.add](https://numpy.org/doc/stable/reference/generated/numpy.add.html) |
| Python | 3.12 | `subprocess.Popen(stdin=PIPE)`; เขียน pipe ที่ปลายปิดแล้วได้ `BrokenPipeError` | [subprocess](https://docs.python.org/3.12/library/subprocess.html), [BrokenPipeError](https://docs.python.org/3.12/library/exceptions.html#BrokenPipeError) |

## Seams

สาม seam ตาม D15: ทางนี้ไม่มีโมเดล ทดสอบด้วย ffmpeg จริงได้ทั้งทาง และความตรงของเสียงกับภาพตัดสินที่ `timeline` จุดเดียว.

1. **API ของ tab สอนกลอง** `/api/drums/*` ผ่าน `TestClient` ด้วย ffmpeg จริงและ sample ปลอม (`fakes.write_drum_kit`)
   - `POST /lessons` แล้ว `GET /lessons` → มีบทเรียนใหม่ สองท่อน ป้ายท่อนสอง `ลองเล่นเอง`
   - `PUT` ที่ยาวเกิน 90 วินาที → `200`, `length_s` > 90; `POST /listen` และ `POST /render` → `422` `too_long`
   - `PUT` แต่ละกฎของ D20 และโน้ตเลยห้อง → `400` `invalid_request` พร้อม `field`, ไฟล์ไม่เปลี่ยน
   - id `..`, `%2E%2E`, ตัวใหญ่ → `404` และไม่มีไฟล์ใดหาย
   - `POST /render` แล้ว poll จน `done` → `renders/` มี mp4, srt, json; `ffmpeg -i` บอก 1080×1920, 30 fps, h264, aac, ความยาวตรง `length_s` ± 0.1 วินาที
   - **เสียงตรงภาพ:** บทเรียน snare ตัวเดียวกับ sample ปลอมที่เริ่มด้วยเสียงคลิกชัด → หา sample แรกของเสียงจาก mp4 และเฟรมแรกที่จุดกระทบของ snare เป็นสีแดง (ดึงเฟรมแบบ `backend/tests/test_toon_render_api.py`) → ห่างไม่เกิน 1 เฟรม
   - ไม่มี sample → `503` `not_ready` มี `rows: ["drum_kit"]`
   - render ซ้อน → `409` `busy`; ลบบทเรียนระหว่าง render → `409` `lesson_busy`; ยกเลิกกลางการส่งเฟรม → `cancelled` ไม่มี `.partial` เหลือ
   - ตัวเลือกของ filter `ass` ผิด (ffmpeg จบตอนเริ่ม; `fontsdir` ที่ไม่มีอยู่ไม่ทำให้ ffmpeg จบ, D34) → `failed` `ffmpeg_failed` มีบรรทัดของ stderr
   - `PUT /background` PNG → `background.jpg` 1080×1920, `background` = `image`; ไฟล์ข้อความ → `415`; เกิน 20 MB → `413`
   - `POST /copy` → id ใหม่ ไม่มีผล render; `DELETE` → folder หาย; `lesson.json` เสีย → ไม่อยู่ในรายการ แต่ `DELETE` ได้
   - `POST /listen` → wav ยาว `length_s`
2. **ตารางเวลาและเฟรม** `timeline.build(lesson)`, `frames.frame_at(scene, t)`
   - BPM 120 ท่อนแรกความเร็ว 50 → นับเข้ายาว 4.0 วินาที โน้ต step 2 ของห้องแรกอยู่ที่ 4.5 วินาที (step 4 ที่ 5.0, D27)
   - `flam` → สองการตี ห่าง 0.03 วินาที มือสลับ `soft` ก่อน
   - เฟรมที่เวลาของโน้ต snare → พิกเซลที่จุดกระทบของ snare เป็นสีแดง; เฟรมก่อนหน้า 1 เฟรม (1/30 วินาที) ไม่แดง
   - ท่อนที่ `focus` = `["kick"]` → พิกเซลกลาง snare มืดกว่าในท่อนที่ไม่มี focus
   - เวลาเดียวกันเรียกสองครั้ง → bytes เดียวกัน; สองครั้งของ `mixer` → wav เดียวกัน
3. **หน้าเว็บ tab สอนกลอง** (e2e) ผ่าน `App` กับ fetch ปลอม (story-kb D18)
   - กด tab "สอนกลอง" → `#/drums` รายการ; ว่าง → ข้อความชวนสร้าง
   - กดช่องว่างที่ R ใช้อยู่ → โน้ตใหม่เป็น L; ช่องที่สองมือไม่ว่างกดไม่ได้
   - เปลี่ยนเป็น flam แล้วบันทึก → `PUT` ส่ง `hit: "flam"`
   - เพิ่ม เลื่อน ลบท่อนสอน แล้วบันทึก → `PUT` ส่ง `chapters` ตามลำดับใหม่
   - "ฟังจังหวะ" → `PUT` แล้ว `POST /listen` ปุ่มเป็น "กำลังผสมเสียง…" แล้วเล่น blob
   - ออกจากหน้าแก้ก่อนบันทึก → ถามยืนยัน
   - render → แถบ % → `done` พาไป `#/drums/{id}/renders`; เปิด `#/drums` ระหว่างงาน → แถวมีป้าย render
   - ทำซ้ำ และลบพร้อมยืนยันในรายการ → `POST /copy`, `DELETE`

## Testing decisions

- **Copy:** `backend/tests/test_toon_render_api.py` — render ด้วย ffmpeg จริง ตรวจด้วย `ffmpeg -i` และดึงเฟรมจาก mp4 (toon D42)
- **Copy:** `backend/tests/test_toon_sounds_api.py` — body ดิบของไฟล์และ error ขนาดไฟล์
- **Copy:** `backend/tests/test_setup.py` — การโหลดไฟล์ pin ด้วย `fetch` ปลอม (แบบ Kanit)
- **Copy:** `frontend/src/features/toon/components/ToonPage.test.tsx` — หน้าเว็บผ่าน `App` กับ fetch ปลอม (story-kb D18)
- `fakes.write_drum_kit(root)` แบบ `fakes.write_kanit`: เขียน FLAC สั้น 0.1 วินาทีด้วย `soundfile` ทุกไฟล์ในตาราง (ทุกชิ้น ทุกชั้น ทุก round-robin) และ marker ที่ Setup script เขียน; ไม่โหลดจากเน็ต
- sample ปลอมเริ่มด้วยเสียงคลิก (sample แรกเต็มแรง) เพื่อหาจุดเริ่มเสียงใน test เสียงตรงภาพ
- เป้าความเร็ว (D14) และเวลาต่อเฟรม (D18) วัดมือบน Mac ใน ticket render ไม่อยู่ใน CI

## Out of Scope

- เครื่องดนตรีอื่นนอกจากกลอง (D1)
- นำเข้า MIDI และถอดโน้ตจากเสียงจริง (D2)
- อัตราจังหวะอื่นนอกจาก 4/4 และโน้ตสามพยางค์ (D5)
- backing track และคลังเสียงพื้น (D7)
- ตัวอย่างภาพสดก่อน render (D8)
- ตัวเลือกตำแหน่ง สี ขนาดบนจอ (D12)
- ช่องใส่โลโก้หรือลายน้ำ (D23)
- Windows: ใช้ทางเดียวกับทุก feature (setup-status D25); encoder `libx264` ตาม spoil D36

## Open Questions

1. ~~`hihat_14/chik` เป็นไฮแฮทเท้าจริงไหม และทอม 14/15/18 นิ้วเหมาะกับสูง กลาง ต่ำไหม~~ — ปิดแล้วใน D30: ตารางคงเดิม (ตรวจจาก keymap ของ repo และ f0 ของไฟล์ ยังไม่ได้ฟังด้วยหู)
2. legal ข้อ 2 UNVERIFIED: โน้ตกลองไม่กี่ห้องของเพลงที่มีลิขสิทธิ์เป็น "สาระสำคัญ" ของงานดนตรีหรือไม่ และ s.32(6) ครอบคลิปสอนของเพจส่วนตัวหรือไม่ — non-blocking: รับความเสี่ยงแล้วใน D25
3. legal ข้อ 3 UNVERIFIED: ปกอัลบั้มที่เบลอหนักเข้าข้อยกเว้นหรือไม่ (แอปเตือนห้ามใช้อยู่แล้ว D23) — non-blocking: รับความเสี่ยงแล้วใน D25
4. legal ข้อ 4 UNVERIFIED: "Your Turn" จดเครื่องหมายการค้าในไทยหรือไม่ (ป้ายตั้งต้นไม่ใช้คำนี้แล้ว D23) — non-blocking: รับความเสี่ยงแล้วใน D25

## Sources

- [Big Rusty Drums repository](https://github.com/sfzinstruments/karoryfer.big-rusty-drums/tree/f07ce00df34a46b6b08375be56fe116cf15782bc) — folder ของ sample, ชั้นความแรง, `.sfz` (accessed 2026-11-13)
- [Big Rusty Drums LICENSE](https://github.com/sfzinstruments/karoryfer.big-rusty-drums/blob/f07ce00df34a46b6b08375be56fe116cf15782bc/LICENSE) — CC0 1.0 (accessed 2026-11-13)
- [Pillow ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html) — รูปทรงที่วาดได้ (accessed 2026-11-13)
- [Pillow Image](https://pillow.readthedocs.io/en/stable/reference/Image.html) — `resize`, `tobytes`, `alpha_composite`, `open(formats=)` (accessed 2026-11-13)
- [Pillow ImageFilter](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html) — `GaussianBlur` (accessed 2026-11-13)
- [Pillow ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html) — `fit`, `exif_transpose` (accessed 2026-11-13)
- [Pillow ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html) — `getlength` (accessed 2026-11-13)
- [FFmpeg formats: rawvideo](https://ffmpeg.org/ffmpeg-formats.html#rawvideo) — รับเฟรมดิบจาก stdin (accessed 2026-11-13)
- [FFmpeg filters: ass](https://ffmpeg.org/ffmpeg-filters.html#ass) — วาด ASS ด้วย `fontsdir` (accessed 2026-11-13)
- [python-soundfile](https://python-soundfile.readthedocs.io/en/latest/) — อ่าน FLAC เขียน wav (accessed 2026-11-13)
- [numpy.add](https://numpy.org/doc/stable/reference/generated/numpy.add.html) — รวม array (accessed 2026-11-13)
- [Python subprocess](https://docs.python.org/3.12/library/subprocess.html) — `Popen(stdin=PIPE)` (accessed 2026-11-13)
- [Python BrokenPipeError](https://docs.python.org/3.12/library/exceptions.html#BrokenPipeError) — เขียน pipe ที่ปิดแล้ว (accessed 2026-11-13)
