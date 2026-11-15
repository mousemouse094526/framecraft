# Spec: drum-cover

เอาเพลงที่แกะโน้ตแล้วใน tab แกะเพลง มาทำ reel cover แนวตั้งหนึ่งคลิป: ชุดกลองที่ไม้ตีตรงกับการตีที่พบ โน้ตเลื่อนผ่าน playhead และเสียงกลองที่แอปผสม โดยไม่มีบทเรียน BPM หรือท่อนสอน.

**Status:** draft

## Problem

เจ้าของวางลิงก์เพลง แกะโน้ต แล้วได้ "บทเรียนกลอง" ที่มี BPM ท่อนสอน และป้าย KICK-FLAMS ซึ่งไม่ใช่สิ่งที่ต้องการ: "ผมไม่ได้ทำการสอน แค่จะเอาคลิปที่แกะมา cover เป็น reels ลงช่อง แบบต้นฉบับ". และเมื่อแกะช่วง 0–30 วินาทีของเพลงที่กลองเข้าที่ 11.5 วินาที หน้าเพลงแสดงห้องว่างห้าห้องโดยไม่บอกอะไร จนคิดว่าแอปพัง.

## Solution

- จากหน้าเพลงที่แกะแล้ว กด "ทำ reel cover" แล้วตั้งค่า reel ของเพลงนั้นหนึ่งชุด: ช่วง ข้อความบนจอ พื้นหลัง เสียง (D1, D2, D6)
- reel เล่นการตีที่พบตามเวลาจริง ไม่ quantize ไม่มี BPM ท่อนสอน ป้าย หรือนับเข้า; ภาพใช้ชุดกลอง เลนโน้ต ตัวนับ และคำบรรยายของ video-gen (D3, D4)
- ฟังเสียงของ reel ก่อน render แล้ว render เป็น mp4 1080×1920 เก็บผลทุกครั้ง เล่น โหลด ลบได้ (D7, D12)
- เสียงกลองล้วนเป็นค่าตั้งต้น; เปิดเสียงเพลงต้นฉบับเป็น backing ได้เองพร้อมคำเตือน (D7)
- พื้นหลังสีของแอป หรือภาพของผู้ใช้ (D8)
- หลังแกะ หน้าเพลงบอกเมื่อช่วงไม่มีการตีหรือห้องแรก ๆ ว่าง และเริ่มช่วงใหม่ที่การตีแรกได้ปุ่มเดียว (D9)

## User Stories

**ผู้ทำคลิป**
1. As a ผู้ทำคลิป, I want กดจากเพลงที่แกะแล้วไปตั้งค่า reel cover, so that ได้คลิป cover ของท่อนนั้นโดยไม่ต้องกรอกบทเรียน (D1, D11)
2. As a ผู้ทำคลิป, I want reel ที่ไม้ตีและโน้ตตรงกับการตีที่แกะได้ตามเวลาจริง, so that คลิปฟังและดูเหมือนต้นฉบับ ไม่ใช่คลิปสอน (D3, D4, D5)
3. As a ผู้ทำคลิป, I want ตั้งช่วงของ reel หัวเรื่อง บรรทัดรอง และคำบรรยาย แล้วฟังก่อน render, so that รู้ว่าได้คลิปแบบไหนก่อนเสียเวลา render (D6, D12)
4. As a ผู้ทำคลิป, I want render เป็น mp4 แนวตั้งแล้วเก็บผลทุกครั้ง, so that โพสต์ลง reels ได้และกลับมา render ใหม่ได้ (D2, D12)
5. As a ผู้ทำคลิป, I want เลือกใส่เสียงเพลงต้นฉบับใต้กลองได้เอง, so that reel ฟังเหมือน cover จริงเมื่อฉันรับความเสี่ยงเรื่อง claim เอง (D7)
6. As a ผู้ทำคลิป, I want ใช้ภาพของตัวเองเป็นพื้นหลัง, so that reel แต่ละเพลงหน้าตาไม่ซ้ำกัน (D8)
7. As a ผู้ทำคลิป, I want รู้ทันทีว่าช่วงที่แกะไม่มีกลองหรือกลองเข้าตรงไหน และเลื่อนช่วงไปที่กลองเริ่มได้ปุ่มเดียว, so that ไม่เห็นหน้าว่างแล้วคิดว่าแอปพัง (D9)

## Design

แบบหน้าจอทำจาก [ui-prompt.md](ui-prompt.md) กับ design system เดิม ไม่รอ Figma (D14). หน้า reel อ่าน `GET /covers/render` ตอนเปิดและ poll ระหว่างงานรัน (D12).

| Screen | User stories | Must show | Source |
|---|---|---|---|
| หน้าเพลง — ส่วนที่เพิ่ม (`#/songs/{id}`) | 1, 7 | เหนือส่วน "ผลแกะ" หลัง Pick job `done`: `hits` ว่าง → Alert เตือน "ไม่พบการตีกลองในช่วง {start}–{end} วินาที ลองเลื่อนช่วงไปที่กลองเริ่มเล่น"; ห้องที่พบตัวแรกว่าง → Alert "ห้อง 1–{k} ไม่มีการตี การตีแรกอยู่ที่ {t} วินาที" กับปุ่ม "เริ่มช่วงที่การตีแรก" ที่ตั้งช่วงใหม่แล้วบันทึกและแกะทันที (D9); เหนือส่วน "สร้างบทเรียน" เมื่อมี `analysis`: ส่วน "Reel cover" บรรทัด "ช่วงแกะ {start}–{end} วินาที · {n} การตี · render แล้ว {m} ครั้ง" และปุ่มหลัก "ทำ reel cover" → `#/songs/{id}/cover`; ปุ่ม "สร้างบทเรียนกลอง" เป็นปุ่มรอง (D11); ของเดิมอื่นตาม drum-notes spec › Design | pending |
| หน้า reel (`#/songs/{id}/cover`) | 2, 3, 4, 5, 6 | ลิงก์กลับ "← {ชื่อเพลง}" และหัว "Reel cover"; ยังไม่แกะ (`no_analysis`) → ข้อความ "แกะโน้ตก่อน แล้วกลับมาทำ reel" กับลิงก์กลับ; การ์ด "ช่วงของ reel": ช่องเริ่มและจบ (วินาที) ภายในช่วงแกะ `{analysis.start_s}–{analysis.end_s}`, บรรทัด "ยาว {n} วินาที (2–90)", ปุ่ม "เริ่มที่การตีแรก" (ตั้งเริ่ม = `suggested_start_s`), แถบห้องที่พบในช่วงพร้อมจำนวนการตี (อ่านอย่างเดียว) (D6); การ์ด "ข้อความบนจอ": "หัวเรื่อง" (1–40), "บรรทัดรอง" (0–60), "คำบรรยายล่าง" (0–60) ค่าตั้งต้นชื่อเพลง บรรทัดรองของเพลง และว่าง (D12); การ์ด "พื้นหลัง": "สีเข้มของแอป" / "ภาพของฉัน" เลือก PNG/JPG ≤ 20 MB ภาพย่อ 9:16 "เปลี่ยนภาพ" "ลบภาพ" คำเตือน "ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม" (D8); การ์ด "เสียง": "กลองล้วน" (ตั้งต้น) / "กลอง + เพลงต้นฉบับ" กับ "ความดังเพลง" 10–100 (ตั้งต้น 35) และคำเตือน "เพลงต้นฉบับมีลิขสิทธิ์ แพลตฟอร์มอาจ claim ปิดเสียง หรือบล็อกคลิป เปิดเมื่อคุณมีสิทธิ์ใช้เสียงนี้" (D7); แถบท้าย: "บันทึก" (จุด "ยังไม่บันทึก" เมื่อแก้แล้ว ถามก่อนออก story-kb D11), "ฟัง" (บันทึกก่อน → "กำลังผสมเสียง…" → เล่น), ปุ่มหลัก "render reel" (บันทึกก่อนแล้วเริ่มงาน แถบ % กับ "ยกเลิก"; `failed`/`cancelled` ข้อความกับ "ลองอีกครั้ง"); การ์ด "ผล render": ใหม่สุดก่อน เวลาสร้าง ความยาว ป้าย "มีเพลงต้นฉบับ" เมื่อ `backing.on`, player 9:16 ของอันที่เลือก (อันใหม่สุดหลัง render จบ), "โหลด mp4" "โหลด .srt" "ลบ" (ถามยืนยัน; `in_use`); ว่าง: "ยังไม่เคย render reel นี้" (D12); error: `invalid_request` ที่ช่อง (`field`), `not_ready` แสดง `fix` ของแถว (setup-status D26), `busy` บอกเพลงที่ render อยู่, `song_busy`, `not_found` → กลับรายการเพลง | pending |

Pending screens: one design prompt in [ui-prompt.md](ui-prompt.md).

## Expected Outcome

ผู้ใช้วางลิงก์เพลง เลือกช่วง แกะ แล้วได้ reel cover หนึ่งคลิปที่พร้อมโพสต์ โดยไม่ผ่านบทเรียน.

- **หน้าเพลงหลังแกะ:** เห็นว่ากลองเข้าที่วินาทีไหน กดปุ่มเดียวแล้วช่วงใหม่ถูกแกะ; เห็นปุ่ม "ทำ reel cover" เป็นปุ่มหลัก
- **หน้า reel:** กด "ฟัง" ได้ยินกลองของช่วงนั้นตามเวลาจริง; กด "render reel" แถบ % เดินจนจบแล้วเห็นคลิปที่ไม้ตีตรงเสียงทุกครั้ง หัวเรื่องเป็นชื่อเพลง ไม่มี BPM ไม่มีป้ายสอน
- **backing:** เปิด "กลอง + เพลงต้นฉบับ" แล้วฟังหรือ render ได้ยินเพลงเบาใต้กลอง ตรงจังหวะกัน

**How success is judged:**
- เจ้าของทำ reel จาก Yellow (DRUMMATE `Ssz69tFTS7Y`) ช่วง 11.5–30 วินาที (7 ห้อง 88 การตี) แล้วรับว่าเป็นแบบที่ต้องการ (D15)
- หน้าเพลงหลังแกะ Yellow ช่วง 0–30 บอกห้อง 1–5 ว่างและการตีแรกที่ 11.5 วินาที (D9, D15)
- ในคลิปที่ render: เฟรมแรกที่วงแหวนของโน้ตขึ้น กับจุดเริ่มเสียงของโน้ตนั้น ห่างไม่เกิน 1 เฟรม (D15; Seams 1)
- reel 30 วินาที render จบใน ≤ 60 วินาทีบน Mac Apple Silicon (D15)
- render cover เดิมสองครั้ง (backing ปิด) ได้ `audio.wav` เหมือนกันทุก byte (D15)

## Implementation

### Modules touched

- **`backend/drum_cover`** (package ใหม่)
  - `cover`: อ่าน เขียน ตรวจค่า `cover.json` ใต้ `songs.lock`; ค่าตั้งต้นและการดึงเข้าช่วง; `suggested_start_s` (D2, D6, D12)
  - `timeline`: `build(song, cover) -> Timeline` — การตีในช่วงที่เวลาจริง มือตาม D5 จังหวะและเลขนับ ช่วงเดียว ความยาว; Lesson ชั่วคราวสำหรับภาพและตัวหนังสือ (D3, D4, D5)
  - `audio`: เสียงของ reel — `mixer.mix` แล้วถ้า backing เปิดผสม `audio.m4a` ด้วย ffmpeg (ฟังผ่าน `ffmpeg.run_capture`; render เป็น input ของคำสั่ง) (D7)
  - `render`: Render job ของ reel slot ของตัวเอง, ผลใต้ `renders/` ผ่าน `backend.renders`, ลงทะเบียน `songs.song_jobs` (D2, D12)
  - `backgrounds`: ภาพพื้นหลังของ cover ผ่าน `backend.pictures` (D8)
- **`backend.pictures`** (module ใหม่ ใช้ร่วม, prefactor จาก `video_gen.backgrounds`, D8): รับ body ดิบเป็น `.tmp`, อ่านด้วย Pillow, หมุนตาม EXIF, ครอป 1080×1920, เขียน jpg แล้วส่งให้ callback ของผู้เรียกวาง; `video_gen.backgrounds` เรียกมันแทนโค้ดเดิม (test เดิมของ video-gen ยังผ่าน)
- **`backend.video_gen.timeline`**: `assemble(sounds, beats, spans, length_s) -> Timeline` public ที่ `build` ใช้เองด้วย (D4)
- **`backend.video_gen.captions`**: ช่วงที่ยาว 0 ไม่สร้าง event (D4)
- **`backend.video_gen.render`**: คำสั่ง ffmpeg (`_command`) รับ input เสียงเพิ่มและ `filter_complex` ได้ เป็นฟังก์ชันที่ `drum_cover.render` เรียก (D7)
- **`backend.paths`**: `songs_render_dir` (`media/songs/.render/`), `song_renders_dir(song_id)` (D12)
- **`backend.routes`**: router ใหม่ `drum_cover` ไม่มี prefix (D12)
- **`backend.app`**: `JOB_HOLDERS` เพิ่ม Render job ของ reel พร้อม `clean_on_start` (D12)
- **`.claude/skills/fastapi-api`**: แถว `drum_cover/` และ `pictures.py` ในโครงสร้าง; ลำดับ lock: `songs.lock` หลัง slot ของ Render job ของ reel
- **`frontend/src/features/drum-cover`**: `CoverPage` (`#/songs/{id}/cover`) กับ hook และ lib ของมัน (D11, D12)
- **`frontend/src/App.tsx`**: เลือก `CoverPage` เมื่อ `coverViewOf(hash)` ก่อน `SongsPage` (D11)
- **`frontend/src/features/drum-notes`**: หน้าเพลงเพิ่มส่วน "Reel cover" และ Alert ของช่วงที่ไม่มีกลอง (D9, D11)
- **`frontend/src/components/ui`**: `BackgroundPicker` ย้ายมาจาก video-gen รับ path ของ route (D8)

### Data

ไฟล์ที่ feature นี้เพิ่มใน folder ของ Song (D2):

| Path | Holds |
|---|---|
| `media/songs/{song_id}/cover.json` | การตั้งค่า reel (schema ด้านล่าง) เขียนแบบ `write_atomic` ใต้ `songs.lock` |
| `media/songs/{song_id}/cover-background.jpg` | ภาพพื้นหลังที่ครอป 1080×1920 แล้ว หรือไม่มี |
| `media/songs/{song_id}/renders/` | ผล render ตาม `backend.renders` |
| `media/songs/.render/` | work folder ของ Render job ที่กำลังรัน ล้างตอน start |

Schema ของ `cover.json`:

```json
{
  "version": 1,
  "start_s": 11.5,
  "end_s": 30.0,
  "title": "Yellow",
  "subtitle": "Coldplay · drum cover",
  "caption": "",
  "background": "color",
  "backing": { "on": false, "volume": 35 },
  "updated_at": "2026-11-15T10:30:00+07:00"
}
```

| Field | Rule |
|---|---|
| `start_s`, `end_s` | `analysis.start_s ≤ start_s`, `end_s ≤ analysis.end_s`, `2 ≤ end_s − start_s ≤ 90` ปัดสามตำแหน่ง (D6) |
| `title` | 1–40 ตัวอักษร (นับ code point แบบ story-kb D12) |
| `subtitle`, `caption` | 0–60 ตัวอักษร; ว่าง = ไม่แสดง |
| `background` | `color` หรือ `image`; `image` ต้องมี `cover-background.jpg` (D8) |
| `backing.on` | `true`/`false` (D7) |
| `backing.volume` | จำนวนเต็ม 10–100 (D7) |

ค่าไม่ผ่าน = `400` `invalid_request` พร้อม `field`. ไม่มี `cover.json` → `GET` คืนค่าตั้งต้น (`saved: false`): `title` = ชื่อเพลงตัดที่ 40, `subtitle` = บรรทัดรองของเพลงตัดที่ 60, `caption` ว่าง, `background` `color`, `backing` ปิด 35, `start_s` = `suggested_start_s`, `end_s` = `min(analysis.end_s, start_s + 90)`. ค่าที่เก็บเกินช่วงหลังแกะใหม่ถูกดึงเข้าช่วงตอนอ่าน (D6).

`suggested_start_s` (D6, D9) = ต้นห้องที่พบตัวแรกที่มี `hits` > 0; การตีแรกอยู่ก่อน downbeat แรก → เวลาการตีแรก; ไม่มีการตี → `analysis.start_s`.

### Timeline ของ reel

`drum_cover.timeline.build(song, cover)` เลขล้วน (D3, D4, D5):

1. การตี = `analysis.hits` ที่ `start_s ≤ t < end_s`; เวลาในคลิป = `t − start_s`; ชั้นความแรงและชนิดหัวโน้ตตาม `level` (`accent` → `hard`/`accent`, `normal` → `mid`/`normal`, `ghost` → `soft`/`ghost`)
2. ห้องสำหรับเลือกมือ = ช่วงระหว่าง `downbeats` ติดกัน; ก่อน downbeat แรกใช้ความยาวห้องแรกถอยหลัง หลังตัวสุดท้ายใช้ความยาวห้องสุดท้ายต่อไป; `downbeats` น้อยกว่า 2 → ห้องยาว 2.0 วินาทีจาก `start_s`
3. ช่อง = `floor((t − ต้นห้อง) / (ความยาวห้อง / 16) + 0.5) + 16 × ลำดับห้อง`; ชิ้นเดียวซ้ำช่องเดียว: ตัวแรกเข้ากติกามือ ตัวถัดไป `hand` = `null`
4. `groove.trimmed` แล้ว `groove.with_hands` (drum-notes D13) บนโน้ตที่เหลือ → มือของแต่ละ (ชิ้น, ช่อง); โน้ตที่ `trimmed` ตัด → `hand` = `null` แต่ยังเล่นและมีหัวโน้ต; เท้า (`kick`, `hihat_pedal`) ไม่มีมือ
5. จังหวะ = `analysis.beats` ที่ `start_s ≤ t < end_s`; เลข = ลำดับหลัง downbeat ก่อนหน้า + 1; จังหวะก่อน downbeat แรกในช่วงนับถอยหลังจาก downbeat นั้น ต่ำสุด 1
6. ช่วงเดียว `Span(0, end_s − start_s)`; `length_s` = `end_s − start_s + 1.5`; `timeline.assemble` ปัดเป็น sample และวน round-robin
7. Lesson ชั่วคราว (`lessons.unsaved`): `title`, `subtitle`, `caption`, `background` ของ cover; `bpm` = `round(60 / มัธยฐานช่วงห่างของจังหวะในช่วง)` จำกัด 40–240 (จังหวะน้อยกว่า 2 → 120) ใช้แค่ความเร็วเลื่อนเลน; `groove` ว่าง 1 ห้อง; `chapters` = ท่อนเดียว ป้ายว่าง ไม่เน้นชิ้นใด `repeats` 1 `speed` 100

ตัวอย่างที่ test ใช้ (Seams 2): `analysis` ห้องยาว 2.0 วินาที downbeat ที่ 10.0, 12.0, 14.0; cover `start_s` 10.0 `end_s` 14.0 → `length_s` 5.5; การตี snare ที่ 11.0 อยู่ที่ sample `44100`; ไฮแฮท 8 ตัวติดกันทุก 0.125 วินาที → มือ R L R L …; snare + crash + ไฮแฮทที่ 12.0 → ไฮแฮท `hand` `null` ยังอยู่ใน `hits`; จังหวะที่ 10.0 เลข 1, 10.5 เลข 2.

### เสียง

`drum_cover.audio` (D7):

1. wav กลอง = `mixer.mix(project, timing)` (video-gen spec › Timeline and audio)
2. `backing.on` = `false` → wav นี้คือเสียงของ reel
3. `backing.on` = `true` → ffmpeg: input 1 = wav กลอง, input 2 = `-ss start_s -t (end_s − start_s) -i audio.m4a`; `filter_complex` `[1:a]volume={volume/100}[b];[0:a][b]amix=inputs=2:duration=first:normalize=0[a]`; ฟัง: `-f wav -` ผ่าน `ffmpeg.run_capture` (wav กลองเขียนชั่วคราวใน `media/songs/.partial/`); render: input ทั้งสองอยู่ในคำสั่ง `run_piped` และ `-map` เสียงจาก `[a]`
4. เพลงจาก MIDI ไม่มี `audio.m4a` → `backing.on` = `true` ตอบ `400` `invalid_request` field `backing.on` "เพลงจาก MIDI ไม่มีเสียงต้นฉบับ"

### Render job

หนึ่งงานต่อครั้ง `JobSlot` ของตัวเอง ไม่จองช่อง GPU (D12). thread ใน backend (ADR-0010). `POST /songs/{id}/cover/render` `{}`:

1. `{id}` ไม่ตรงรูปแบบหรือไม่มี → `404` `not_found`; ไม่มี `analysis` → `409` `no_analysis`
2. `gate_rows.drums` ไม่ ok → `503` `not_ready`
3. มี Render job ของ reel รันอยู่ → `409` `busy` (มี `song_id` และ `title` ของงานนั้น)
4. อ่าน `cover.json` (หรือค่าตั้งต้น) และดึงเข้าช่วง; `backing.on` กับเพลง MIDI → `400` ตามข้อ 4 ของเสียง
5. `disk.require_free` ด้วย `length_s × 2 MB` → `507` `disk_full`
6. copy `song.json`, `cover.json` (ค่าที่ใช้จริง) และ `cover-background.jpg` เข้า `media/songs/.render/` ใต้ `songs.lock` แล้วตอบ `202` และทำต่อใน thread (video-gen D33)
7. `drum_cover.timeline.build` → `mixer` เขียน `audio.wav`; `captions.ass_file` เขียน `text.ass` จาก Lesson ชั่วคราว; `frames.Scene`
8. `ffmpeg.run_piped`: rawvideo `rgb24` 1080×1920 30 fps จาก stdin + `audio.wav` (+ `audio.m4a` เมื่อ backing เปิด) filter `ass` และ `filter_complex` ของเสียง, `h264_args`, aac 48 kHz, เขียน `{name}.mp4.partial`; `percent` = เฟรมที่ส่ง / ทั้งหมด
9. `renders.Render.finish` เขียน `.srt` (cue เดียว: หัวเรื่อง บรรทัดรอง คำบรรยาย) กับ `.json` (`song_id`, `title`, `length_s`, `start_s`, `end_s`, `picked_at`, `backing`, `created_at`)

| State | ความหมาย |
|---|---|
| `rendering` | กำลังวาดและ encode, `percent` 0–100 |
| `done` | มีผลใน `renders/`; `result` = ชื่อ render |
| `failed` | `error` = `ffmpeg_failed` (บรรทัดท้ายของ stderr ใน `message`) หรือ `internal` |
| `cancelled` | ผู้ใช้ยกเลิก; kill ffmpeg ลบ `.partial` |

restart ระหว่างรัน: start ล้าง `media/songs/.render/` และ `.partial` ใน `renders/` ทุกเพลง. ลบเพลงระหว่าง render → `409` `song_busy` (drum-notes D18 ผ่าน `songs.song_jobs`).

### API

ทุก route ของ cover อยู่ใต้ `/api/songs/{id}/cover`; งาน render อยู่ที่ `/api/covers/render` (D12). `POST`/`PUT` เป็น JSON (ADR-0013) ยกเว้น `PUT …/background` ที่รับ `application/octet-stream` (ADR-0028). error เป็น `{code, message}` (spoil-maker D63). `{id}` ไม่ตรงรูปแบบหรือไม่มีเพลง = `404` `not_found`; ยังไม่มี `analysis` = `409` `no_analysis` ทุก route ของ cover.

| Method | Path | ทำอะไร | Error |
|---|---|---|---|
| `GET` | `/songs/{id}/cover` | cover ที่เก็บ (ดึงเข้าช่วงแล้ว) หรือค่าตั้งต้น + `saved`, `length_s`, `suggested_start_s` | `404`, `409` `no_analysis` |
| `PUT` | `/songs/{id}/cover` | ทับทั้งก้อน → cover | `400` `invalid_request` (มี `field`), `404`, `409` |
| `POST` | `/songs/{id}/cover/background/check` | `{size}` → `{size}` (ADR-0028) | `413` `file_too_large`, `409` `song_busy`, `507` `disk_full`, `400`, `404` |
| `PUT` | `/songs/{id}/cover/background?size=` | body ดิบ PNG/JPG ≤ 20 MB → ครอป เก็บ ตั้ง `background` = `image` → cover | `413`, `415` `unsupported_image`, `400` `size_mismatch`, `409` `song_busy`, `404` |
| `DELETE` | `/songs/{id}/cover/background` | ลบภาพ ตั้ง `background` = `color` → cover | `409` `song_busy`, `404` |
| `GET` | `/songs/{id}/cover/background.jpg` | ภาพที่ครอปแล้ว; หน้าเว็บขอด้วย `?v={updated_at}` | `404` |
| `POST` | `/songs/{id}/cover/listen` | `{}` → `audio/wav` ของ reel ตามค่าที่บันทึก `Cache-Control: no-store` | `503` `not_ready` (`drum_kit`; `ffmpeg` เมื่อ backing), `400` (backing กับ MIDI), `404`, `409` |
| `POST` | `/songs/{id}/cover/render` | `{}` → `202` งาน | ตาม Render job |
| `GET` | `/covers/render` | งานล่าสุด: `state`, `song_id`, `title`, `percent`, `result`, `error`, `message` หรือ `null` | — |
| `POST` | `/covers/render/cancel` | `{}` → งาน | `409` `not_running` |
| `GET` | `/songs/{id}/cover/renders` | ผลเรียงใหม่สุดก่อน (`renders.listed`) พร้อม `backing` | `404` |
| `GET` | `/songs/{id}/cover/renders/{name}.mp4` และ `.srt` | ไฟล์ (`FileResponse` ตอบ `Range`) | `404` `not_found` |
| `DELETE` | `/songs/{id}/cover/renders/{name}` | `204` | `409` `in_use`, `404` |

`song_busy` ของ route ภาพ = Render job ของ reel หรือ Pick job ของเพลงนี้ยังไม่จบ (`songs.require_idle`).

### Frontend

- `features/drum-cover` มี `CoverPage` สำหรับ `#/songs/{id}/cover`; `coverViewOf(hash)` อยู่ใน `lib` ของมัน; `App` เรียกก่อนส่งให้ `SongsPage` (D11)
- เปิดหน้า: `GET /songs/{id}` (ชื่อ ช่วงแกะ `bars`), `GET /songs/{id}/cover`, `GET /songs/{id}/cover/renders`, `GET /covers/render`; `no_analysis` → ข้อความชวนแกะก่อน
- ฟอร์มเก็บค่าที่แก้; "บันทึก" → `PUT`; "ฟัง" และ "render reel" บันทึกก่อนเมื่อยังไม่บันทึก (video-gen D29); ออกก่อนบันทึก → ถาม (story-kb D11)
- "ฟัง" → `POST /listen` เล่นด้วย `useListen` (drum-notes D21)
- "render reel" → `POST /render` แล้ว poll `GET /covers/render`; `done` → อ่าน `renders` ใหม่ เลือกอันใหม่สุด
- ภาพ: `BackgroundPicker` ใช้ร่วม → `check` แล้ว `sendFile` `PUT` body ดิบ (spoil D58) → cover ใหม่; ภาพแสดงด้วย `?v={updated_at}`
- หน้าเพลง (drum-notes): หลัง Pick job `done` คำนวณ `firstHitBar` จาก `bars[].hits` และ `analysis.hits` → Alert และปุ่ม (D9); ปุ่มเรียก `usePick.start` ด้วยช่วงใหม่; ส่วน "Reel cover" อ่าน `GET /songs/{id}/cover/renders` เพื่อนับ (D11)

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| ffmpeg | 7.1 (imageio-ffmpeg 0.7.0) | filter `amix` รับ `inputs`, `duration=first`, `normalize=0`; filter `volume` รับตัวคูณ; `-filter_complex` กับ `-map "[a]"` | [amix](https://ffmpeg.org/ffmpeg-filters.html#amix), [volume](https://ffmpeg.org/ffmpeg-filters.html#volume), [filtergraph](https://ffmpeg.org/ffmpeg.html#Advanced-options) |
| ffmpeg | 7.1 | `-ss` ก่อน `-i` และ `-t` ตัดช่วงของ m4a ตรงเวลา (accurate seek เป็นค่าตั้งต้น) แบบที่ Pick job ใช้ | [ffmpeg main options](https://ffmpeg.org/ffmpeg.html#Main-options) |
| ffmpeg | 7.1 | `-f wav -` ส่ง wav ออก stdout | [wav muxer](https://ffmpeg.org/ffmpeg-formats.html#wav) |
| Pillow | 12.3.0 | ตาม video-gen spec › Library assumptions (ครอป EXIF เบลอ) ไม่มีอะไรเพิ่ม | [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html) |
| numpy | 2.5.4 | `median` ของช่วงห่างจังหวะ | [numpy.median](https://numpy.org/doc/stable/reference/generated/numpy.median.html) |
| Starlette | 1.10.0 | `FileResponse` ตอบ `Range` ด้วย `206` | [FileResponse](https://www.starlette.io/responses/#fileresponse) |

## Seams

สาม seam ตาม D13: ทางนี้ไม่มีโมเดล ทดสอบด้วย ffmpeg จริงได้ทั้งทาง และความตรงของเสียงกับภาพตัดสินที่ `Timeline` จุดเดียว.

1. **API ของ reel** `/api/songs/{id}/cover/*`, `/api/covers/render` ผ่าน `TestClient` ด้วย ffmpeg จริง sample ปลอม (`fakes.write_drum_kit`) และเพลงที่มี `analysis` เขียนตรง
   - `GET /cover` ของเพลงที่แกะแล้วไม่มี `cover.json` → `saved` `false`, `title` = ชื่อเพลง, `start_s` = ต้นห้องแรกที่มีการตี; เพลงที่ยังไม่แกะ → `409` `no_analysis`
   - `PUT /cover` ช่วงยาว 1 วินาที, เกิน `analysis.end_s`, `volume` 5, `title` ว่าง → `400` มี `field`; ค่าดี → ไฟล์ `cover.json`; `analysis` ใหม่ที่สั้นกว่า → `GET` คืนค่าที่ดึงเข้าช่วง
   - `POST /listen` → wav ยาว `length_s` ± 0.05 วินาที; backing เปิดกับเพลงที่มี `audio.m4a` (ไฟล์ปลอมจาก ffmpeg) → wav ยาวเท่ากัน; backing เปิดกับเพลง MIDI → `400` field `backing.on`; ไม่มี sample → `503` มี `rows: ["drum_kit"]`
   - `POST /render` แล้ว poll จน `done` → `renders/` มี mp4, srt, json ที่มี `start_s`, `end_s`, `picked_at`, `backing`; `ffmpeg -i` บอก 1080×1920, 30 fps, h264, aac, ความยาวตรง `length_s` ± 0.1 วินาที
   - **เสียงตรงภาพ:** `analysis` snare ตัวเดียวที่ `start_s + 1.0` กับ sample ปลอมที่เริ่มด้วยคลิก → sample แรกของเสียงใน mp4 และเฟรมแรกที่จุดกระทบของ snare เป็นสีแดง ห่างไม่เกิน 1 เฟรม (แบบ video-gen Seams 1)
   - render ซ้อน → `409` `busy` มี `song_id`; `DELETE /songs/{id}` ระหว่าง render → `409` `song_busy`; ยกเลิกกลางการส่งเฟรม → `cancelled` ไม่มี `.partial`; `PUT /cover` ระหว่าง render → `200` และผลของงานใช้ค่าก่อนแก้
   - `PUT /background` PNG → `cover-background.jpg` 1080×1920, `background` = `image`; `DELETE /background` → `color`; ไฟล์ข้อความ → `415`; เกิน 20 MB → `413` ที่ `check` และ `PUT`; test เดิมของ `video_gen` backgrounds ยังผ่าน
   - `DELETE /songs/{id}` → `cover.json` และ `renders/` หาย; `DELETE …/renders/{name}` → `204`; id `..` → `404` ไม่มีไฟล์ใดหาย
   - start ล้าง `media/songs/.render/` และ `.partial` ใน `renders/`
2. **Timeline ของ reel และเฟรม** `drum_cover.timeline.build(song, cover)`, `frames.frame_at(scene, t)`
   - ตัวอย่างใน spec › Timeline ของ reel: snare ที่ 11.0 → sample `44100`; `length_s` 5.5; จังหวะ 10.0 เลข 1 และ 10.5 เลข 2; จังหวะก่อน downbeat แรก (cover เริ่มที่ 9.0 มี beat 9.5) → เลข 4
   - ไฮแฮท 16th 8 ตัว → R L R L …; snare + crash + ไฮแฮทช่องเดียว → ไฮแฮท `hand` `null` และยังอยู่ใน `hits`; ชิ้นเดียวสองครั้งห่าง 20 ms → ตัวที่สอง `hand` `null`
   - `level` `accent` → `layer` `hard`, `note` `accent`; `ghost` → `soft`
   - ไม่มี `downbeats` สองตัว → ห้อง 2.0 วินาที; ไม่มีการตีในช่วง → `hits` ว่าง `length_s` ยังเท่าช่วง + 1.5
   - เฟรมที่เวลาของ snare → พิกเซลที่จุดกระทบของ snare เป็นสีแดง; เฟรมก่อนหน้าไม่แดง; เวลาเดียวกันเรียกสองครั้ง → bytes เดียวกัน
   - `assemble` ให้ `Timeline` เดียวกับ `build` ของบทเรียน video-gen สำหรับบทเรียนตัวอย่าง (prefactor ไม่เปลี่ยนผล)
3. **หน้าเพลงและหน้า reel** (e2e) ผ่าน `App` กับ fetch ปลอม (story-kb D18)
   - หน้าเพลงหลัง `done` ที่ `hits` ว่าง → Alert "ไม่พบการตีกลองในช่วง 0.0–30.0 วินาที …"; ห้อง 1–5 ว่างและการตีแรกที่ 11.5 → Alert "ห้อง 1–5 ไม่มีการตี การตีแรกอยู่ที่ 11.5 วินาที" กด "เริ่มช่วงที่การตีแรก" → `PUT /range` `{start_s: 11.5, end_s: 41.5}` แล้ว `POST /pick`
   - หน้าเพลงที่มี `analysis` → ส่วน "Reel cover" อยู่เหนือ "สร้างบทเรียน" บอก "render แล้ว 2 ครั้ง" กด "ทำ reel cover" → hash `#/songs/{id}/cover`
   - เปิด `#/songs/{id}/cover` → ฟอร์มมีค่าจาก `GET /cover`; เพลงยังไม่แกะ → "แกะโน้ตก่อน แล้วกลับมาทำ reel"
   - แก้หัวเรื่องแล้วกด "บันทึก" → `PUT /cover`; "เริ่มที่การตีแรก" → ช่องเริ่ม = `suggested_start_s`; "ฟัง" → บันทึกแล้ว `POST /listen` ปุ่มเป็น "กำลังผสมเสียง…" แล้วเล่น blob
   - เลือก "กลอง + เพลงต้นฉบับ" → ช่องความดังและคำเตือนขึ้น บันทึก → `PUT` ส่ง `backing: {on: true, volume: 35}`
   - "render reel" → `POST /render` → แถบ % → `done` → รายการผลมีอันใหม่ที่เลือกอยู่; `failed` → ข้อความกับ "ลองอีกครั้ง"
   - เลือกภาพ → `background/check` แล้ว `PUT` body ดิบ แล้วเห็นภาพ; ลบภาพ → กลับเป็นสีของแอป; `415` → error ข้างปุ่ม
   - ออกจากหน้า reel ก่อนบันทึก → ถามยืนยัน; ลบผล render พร้อมยืนยัน → `DELETE`

## Testing decisions

- **Copy:** `backend/tests/test_video_gen_render_api.py` — render ด้วย ffmpeg จริง, ตรวจด้วย `ffmpeg -i`, test เสียงตรงภาพ (ดึงเฟรมจาก mp4), ยกเลิกกลางเฟรม, `busy`
- **Copy:** `backend/tests/test_drum_notes_lesson_api.py` — `written_song(project, subtitle, downbeats)` เขียนเพลงที่มี `analysis` ตรง; ย้ายไป `fakes.py` เมื่อ test ของ feature นี้ใช้เป็นไฟล์ที่สอง
- **Copy:** `backend/tests/test_video_gen_lessons_api.py` — upload ภาพพื้นหลัง `check`/`PUT`/`DELETE` และ error ขนาดกับชนิด
- **Copy:** `backend/tests/test_video_gen_timeline.py` — บทเรียนตัวอย่างสำหรับพิสูจน์ว่า `assemble` ไม่เปลี่ยนผลของ `build`
- **Copy:** `frontend/src/features/drum-notes/components/SongsPage.test.tsx` — หน้าเว็บผ่าน `App` กับ fetch ปลอม และ `sendFile` ด้วย `fakeXhr`
- `audio.m4a` ปลอมสำหรับ backing สร้างด้วย ffmpeg `lavfi` ใน fixture (ไม่ commit ไฟล์เสียง)
- `analysis` ใน test เขียนตรงด้วย `songs.new_song` + `write_new` ไม่ผ่าน Pick job
- เป้าเวลา render (D15) และหน้าตาที่เจ้าของรับ วัดมือบน Mac ไม่อยู่ใน CI

## Out of Scope

- แก้โน้ตของ reel ทีละตัว (D3, D10)
- โน้ตห้าเส้นแบบคลิปอ้างอิง (D3)
- อ่านโน้ตจากภาพของคลิป cover ของคนอื่น (D10)
- รายการ reel ของตัวเองหรือ tab ใหม่ (D1, D2)
- เปลี่ยนโหมดสอนของ video-gen หรือเอาส่วนสร้างบทเรียนออก (D1, D11)
- backing เปิดเป็นค่าตั้งต้น หรือ fade/ducking ของเพลง (D7)
- reel ยาวกว่า 90 วินาที (D6)
- Windows: ทางเดียวกับทุก feature (setup-status D25)

## Open Questions

1. legal ข้อ 1 UNVERIFIED: reel cover ที่ไม่ใช่การสอน (ไม่มีมาตรา 32 (6)) อยู่ในมาตรา 32 วรรคหนึ่งกับมาตรา 33 หรือไม่ — non-blocking: รับความเสี่ยงใน D16
2. legal ข้อ 2 UNVERIFIED: ขอบเขตของการ claim/บล็อกเมื่อมีเสียงบันทึกใน reel บนแต่ละแพลตฟอร์ม — non-blocking: ปิดเป็นค่าตั้งต้น เตือน และรับความเสี่ยงใน D7, D16

## Sources

- [FFmpeg filters: amix](https://ffmpeg.org/ffmpeg-filters.html#amix) — `inputs`, `duration`, `normalize` (accessed 2026-11-15)
- [FFmpeg filters: volume](https://ffmpeg.org/ffmpeg-filters.html#volume) — ตัวคูณความดัง (accessed 2026-11-15)
- [FFmpeg advanced options](https://ffmpeg.org/ffmpeg.html#Advanced-options) — `-filter_complex`, `-map` (accessed 2026-11-15)
- [FFmpeg main options](https://ffmpeg.org/ffmpeg.html#Main-options) — `-ss`, `-t` (accessed 2026-11-15)
- [FFmpeg formats: wav](https://ffmpeg.org/ffmpeg-formats.html#wav) — wav muxer ออก stdout (accessed 2026-11-15)
- [Pillow ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html) — `fit`, `exif_transpose` (accessed 2026-11-15)
- [numpy.median](https://numpy.org/doc/stable/reference/generated/numpy.median.html) — มัธยฐานช่วงห่างจังหวะ (accessed 2026-11-15)
- [Starlette FileResponse](https://www.starlette.io/responses/#fileresponse) — ตอบ `Range` (accessed 2026-11-15)
