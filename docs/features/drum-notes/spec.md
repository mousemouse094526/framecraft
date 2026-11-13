# Spec: drum-notes

tab "แกะเพลง" ให้ผู้ใช้เอาเพลงจากลิงก์ ไฟล์เสียง หรือไฟล์ MIDI เข้ามา แล้วแอปแกะโน้ตกลอง (หรือจังหวะทำนอง) ของช่วงที่เลือก เป็นบทเรียนกลองใน tab สอนกลอง โดยไม่ต้องกรอกโน้ตทีละช่อง.

**Status:** ready-to-build

## Problem

tab สอนกลองต้องกรอกโน้ตบนตาราง 16 ช่องต่อห้องทีละตัว; ผู้ใช้มีเพลงหรือโน้ตอยู่แล้วและอยาก "เอาเพลงมาแกะ" ให้ได้โน้ตกลองมาทำอนิเมชันตีกลองเลย โดยใส่แค่ลิงก์เพลงหรือไฟล์โน้ต.

## Solution

- เอาเพลงเข้าจากลิงก์ (YouTube และเว็บที่ yt-dlp มีตัวโหลดเฉพาะ) หรือไฟล์เสียงในเครื่อง (D4, D20)
- เอาไฟล์ MIDI ที่มีแทร็กกลองเข้าเป็นเพลง (D10)
- เลือกช่วงของเพลงไม่เกิน 90 วินาที แล้วแกะโน้ตกลองอัตโนมัติ: ชนิดกลอง จังหวะ และต้นห้อง (D5, D6)
- โหมดทำนอง: แกะจังหวะของโน้ตทำนอง (piano, kalimba) เป็น snare บน groove พื้นฐาน (D14)
- เลือกห้องที่พบ 1–4 ห้อง เห็นตารางผลพร้อมมือ L/R ฟังก่อน แล้วสร้างบทเรียนกลองพร้อมแก้ต่อใน tab สอนกลอง (D11, D12, D13, D21)
- เพลงอยู่ในเครื่องจนลบ แกะใหม่ด้วยช่วงอื่นได้ และเห็นบทเรียนที่สร้างจากเพลงนั้น (D3, D12)

## User Stories

**ผู้ทำคลิป**
1. As a ผู้ทำคลิป, I want วางลิงก์เพลงหรือเลือกไฟล์เสียงแล้วได้เพลงอยู่ในแอป, so that ไม่ต้องตัดเสียงเองก่อน (D4)
2. As a ผู้ทำคลิป, I want เลือกช่วงของเพลงแล้วให้แอปแกะโน้ตกลอง, so that ได้ร่างโน้ตของท่อนที่จะสอนโดยไม่ต้องฟังแล้วกรอกเอง (D5, D6)
3. As a ผู้ทำคลิป, I want เลือกห้อง 1–4 ห้องจากที่แกะได้ ฟังตัวอย่าง แล้วสร้างบทเรียนกลอง, so that ไปแก้ ฟัง และ render ใน tab สอนกลองต่อได้ทันที (D11, D12, D13, D21)
4. As a ผู้ทำคลิป, I want เอาไฟล์ MIDI ของเพลงกลองเข้าแล้วเลือกห้องได้เหมือนกัน, so that โน้ตที่มีอยู่แล้วไม่ต้องกรอกซ้ำ (D10)
5. As a ผู้ทำคลิป, I want แกะจังหวะทำนองของเพลง kalimba หรือ piano เป็น pattern กลอง, so that ทำคลิปฝึกตีจังหวะทำนองได้ (D14)
6. As a ผู้ทำคลิป, I want เห็นเพลงที่เคยเอาเข้า ลบได้ และเห็นบทเรียนที่สร้างจากแต่ละเพลง, so that กลับมาแกะท่อนอื่นของเพลงเดิมได้ (D3, D12)

## Design

แบบหน้าจอทำหลัง plan (setup-status D9): ทั้งสองหน้า `pending` ใช้ [ui-prompt.md](ui-prompt.md) เป็นสเปกจอ. ทุกหน้าใต้ `#/songs` อ่าน `GET /songs/import` และ `GET /songs/pick` ตอนเปิดและ poll ระหว่างงานรัน (D18).

| Screen | User stories | Must show | Source |
|---|---|---|---|
| รายการเพลง (`#/songs`) | 1, 4, 6 | กล่องลิงก์กับปุ่ม "เอาเพลงเข้า" และปุ่ม "เลือกไฟล์ในเครื่อง" (เสียงหรือ MIDI; วางไฟล์ลงกล่องได้ แบบ tab คลิป spoil D58) (D4); งานลิงก์ที่รัน: ชื่อ สถานะ `checking`/`downloading` %/`converting` ปุ่มยกเลิก; ไฟล์: แถบ % ของ upload แล้ว "กำลังแปลงเสียง…" (ADR-0028); เพลงเรียงตาม `updated_at` ใหม่สุดก่อน: ชื่อ บรรทัดรอง ชนิดต้นทาง (ลิงก์ ไฟล์ MIDI) ความยาว สถานะแกะ (ยังไม่แกะ, แกะแล้ว n ห้อง, กำลังแกะ %) จำนวนบทเรียนที่สร้าง ปุ่มลบ (ถามยืนยัน บอกว่าบทเรียนไม่หาย; `song_busy` "กำลังแกะเพลงนี้อยู่", `in_use`) (D3, D18); กดแถว → หน้าเพลง; ว่าง: ข้อความชวนวางลิงก์เพลงแรก; error ของลิงก์: `unsupported`, `playlist`, `live`, `login_required`, `unavailable`, `too_long` "เพลงยาวเกิน 10 นาที", `too_short` "เพลงสั้นกว่า 4 วินาที", `download_error`, `disk_full`, `busy`; ไฟล์: `unsupported_file` ("ไฟล์นี้ไม่มีเสียงที่อ่านได้" หรือ "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง"), `file_too_large`; ลิงก์หรือไฟล์ซ้ำ → ข้อความ "เพลงนี้มีอยู่แล้ว" แล้วพาไปหน้าเพลงเดิม (D3, D20); `not_ready` แสดง `fix` ของแถวที่ขาด (setup-status D26); ข้อความข้างกล่อง "ใช้เพลงเพื่อแกะโน้ตเท่านั้น เสียงเพลงไม่เข้าคลิป" (D15, legal 1) | pending |
| หน้าเพลง (`#/songs/{id}`) | 2, 3, 5, 6 | หัว: ชื่อ บรรทัดรอง ความยาว ชนิดต้นทาง; player `<audio controls>` ของ `audio.m4a` (ไม่มีสำหรับ MIDI); ช่วงแกะ: ช่องเริ่มและจบ (วินาที) ปุ่ม "ใช้เวลาที่เล่นอยู่" ทั้งสองช่อง ความยาวช่วงกับเพดาน 90 วินาที (D5); โหมด: "กลอง" หรือ "ทำนอง" (D14); ปุ่ม "แกะโน้ต": บันทึกช่วงและโหมดก่อน (`PUT /range`) แล้วเริ่มงาน แถบ % กับยกเลิก; `failed` แสดง `no_beats` "หาจังหวะในช่วงนี้ไม่ได้ ลองช่วงอื่น", `model_failed`, `model_broken` พร้อม `fix`, `busy` บอกเพลงที่แกะอยู่, `not_ready` แสดง `fix` (D6, D18, D20); ยังไม่มี `analysis`: ซ่อนส่วนผลและสร้างบทเรียน แสดง "ตั้งช่วงแล้วกด แกะโน้ต" (D20); ผลแกะ (หรือผลจาก MIDI): BPM ที่พบ, แถบห้องที่พบเรียงตามเวลา (เลขห้อง เวลาเริ่ม จำนวนการตี; ห้องที่จังหวะไม่ครบ 4 จางและเลือกไม่ได้) กดห้อง → player เลื่อนไปต้นห้องนั้น (D6, D10, D20); เลือกช่วงบทเรียน: ห้องแรก (กดที่แถบ) และจำนวนห้อง 1–4 ไม่เกินห้องที่เหลือ, BPM ของบทเรียนแก้ได้ (40–240), ตารางผลแบบอ่านอย่างเดียว ชิ้น × ช่อง เหมือน Groove ของหน้าแก้ ที่โน้ตมีมือ L/R, รายการโน้ตที่ถูกตัดตามกฎมือ (ชิ้น ห้อง ช่อง), ปุ่ม "ฟัง" เล่น wav ของตัวอย่าง (D11, D13, D20, D21); โหมดทำนอง: ตารางรวม kick และไฮแฮทที่เติม (D14); ปุ่ม "สร้างบทเรียนกลอง" → `201` แล้วพาไป `#/drums/{id}` (D12); รายการบทเรียนที่สร้างจากเพลงนี้เป็นลิงก์ `#/drums/{id}` (D12); MIDI: ไม่มี player ช่วงแกะ โหมด และปุ่มแกะ (D18); error: `invalid_request` ที่ช่อง (`field`; `bar` = "ห้องนี้ไม่ใช่ 4/4"), `no_analysis`, `not_found` → กลับรายการ | pending |

Pending screens: one design prompt in [ui-prompt.md](ui-prompt.md).

## Expected Outcome

ผู้ใช้วางลิงก์เพลง เลือกท่อน แล้วได้บทเรียนกลองที่มีโน้ตร่างพร้อมแก้ โดยไม่กรอกโน้ตเอง.

- **วางลิงก์:** เห็นชื่อเพลงและ % โหลด แล้วเพลงอยู่ในรายการ กดแถวแล้วเห็น player
- **แกะโน้ต:** กด "แกะโน้ต" ที่ช่วง 30 วินาที แถบ % เดินจนจบภายในไม่กี่สิบวินาที แล้วเห็นห้องที่พบกับ BPM
- **สร้างบทเรียน:** เลือก 2 ห้อง กด "ฟัง" ได้ยินกลองของตารางนั้น กดสร้าง แล้วอยู่ที่หน้าแก้บทเรียนกลองที่ตารางมีโน้ตและมือ L/R แล้ว
- **MIDI:** เลือกไฟล์ `.mid` แล้วอยู่ที่หน้าเพลงที่มีห้องครบทันที เลือก 2 ห้องแล้วสร้างได้โดยไม่ต้องแกะ

**How success is judged:**
- เจ้าของแกะ intro fill ของ Smells Like Teen Spirit จากคลิปอ้างอิง (กลองล้วน; path ใน [video-gen kit-sketch.md](../video-gen/kit-sketch.md)) และจากลิงก์ YouTube ของเพลงจริง (mix เต็ม) ท่อนเดียวกัน แล้วตัดสินว่าร่างใช้แก้ต่อได้: อย่างน้อย kick กับ snare สองห้องแรกถูกตำแหน่ง (D19, D20)
- round trip: Groove ของบทเรียน video-gen → ตารางเวลา → การตี → quantize → Groove เดิมทุกโน้ตใน 5 ชิ้นที่ ADTOF แยกได้ ทั้งที่เวลาตรงและเลื่อนสลับ +20/−20 ms (D19, D20; Seams 2)
- Pick job โหมดกลองของช่วง 90 วินาทีจบใน ≤ 60 วินาทีบน Mac Apple Silicon (D19)
- Song import ไฟล์ mp3 5 นาทีจบใน ≤ 30 วินาทีหลังรับไฟล์ครบ (D19)
- spike ของ ticket แรก: Beat This! ที่ pin ให้ downbeat ตรงเส้นห้องของ `reel.mp4` และเพลงเต็มหนึ่งเพลง (D20)

## Implementation

### Modules touched

- **`backend/audio_imports`** (module ใหม่ ใช้ร่วม, prefactor จาก `toon.sounds`, D20)
  - งานลิงก์เสียง (`bestaudio` ผ่าน `spoil.adapter`, `checking` → `downloading` → `converting`), รับไฟล์ดิบพร้อมเช็คว่าหน้าเว็บยังอยู่, ffmpeg อ่านความยาวและแปลงเป็น m4a (`-t` เพดาน), ล้าง `.partial/`; รับ folder ปลายทาง เพดานความยาว และ callback เขียนผลจากผู้เรียก
  - `toon.sounds` เรียก module นี้แทนโค้ดเดิม พฤติกรรมของคลังเสียงพื้นไม่เปลี่ยน (test เดิมของ toon ยังผ่าน)
- **`backend/drum_notes`** (package ใหม่)
  - `songs`: อ่าน เขียน ตรวจค่า ลบ Song ใต้ lock เดียว; `lessons` ของเพลงกรองบทเรียนที่หายตอนอ่าน; start ลบ folder ที่ไม่มี `song.json` (D3, D12, D18, D20)
  - `imports`: Song import บน `audio_imports` — งานลิงก์ (slot ของตัวเอง, ซ้ำหลัง `fetch_info` จบ `done` ด้วย id เดิม) และไฟล์เป็น request เดียว; ไฟล์ `.mid` ส่งต่อ `midi` (D4, D20)
  - `midi`: parser Standard MIDI File → `analysis` พร้อมเพดาน (D10, D20)
  - `pick`: Pick job (slot ของตัวเอง, thread, D8): `ffmpeg.run_capture` ถอดช่วง → `onnx_runner` → `score` → เขียน `analysis` (D6, D14, D18, D20)
  - `onnx_runner`: ที่เดียวที่เรียก onnxruntime: โหลดไฟล์โมเดลจาก snapshot (ล้ม = `model_broken`), รัน ADTOF ทั้งช่วง, Beat This! ทีละ chunk, Basic Pitch ทีละหน้าต่าง คืน array ดิบ; test แทนด้วย fake (D7, D8, D17, D20)
  - `score`: เลขล้วน — ต่อ chunk ของ Beat This!, peak picking, จังหวะและห้องจาก logit, quantize, มือ L/R, ตัดตามกฎ D20 ของ video-gen, mapping โหมดทำนอง, และ Groove ที่ได้ (D9, D11, D13, D14, D20)
- **`backend.ffmpeg`**: `run_capture(command, cancel) -> bytes` ใหม่ (D20)
- **`backend.models`**: `ADTOF`, `BEAT_THIS`, `BASIC_PITCH` ใน `MODELS` (D7)
- **`backend.checks`**: แถว `model_adtof`, `model_beat_this`, `model_basic_pitch`, `onnxruntime` ต่อจาก `drum_kit` (D7, ADR-0009)
- **`backend.gate_rows`**: `songs_link` (`yt_dlp`, `deno`, `ffmpeg`), `songs_file` (`ffmpeg`), `pick_drums`, `pick_melody` (D7); `/listen` ของเพลงใช้ `drum_kit_row` (D21)
- **`backend.setup`**: โหลดสามโมเดลหลัง drum kit แล้วสร้าง `InferenceSession` ของแต่ละไฟล์หนึ่งครั้ง (D7, D20)
- **`backend.jobs`**: docstring บอกว่างานโมเดล ONNX บน CPU เป็น `JobSlot` ธรรมดา (D8, ADR ใหม่)
- **`backend.paths`**: `songs_dir` (`media/songs/`), `songs_partial_dir` (D3)
- **`backend.body_types`**: `PUT /api/songs` ในรายการ `require_octet_stream` (ADR-0028, D4)
- **`backend.routes`**: router ใหม่ `drum_notes` prefix `/songs` (D2)
- **`backend.app`**: `JOB_HOLDERS` เพิ่ม Song import และ Pick job (D18)
- **`backend.video_gen.lessons`**: ทางสร้างบทเรียนจากค่าเต็ม (หัวเรื่อง บรรทัดรอง BPM Groove) ที่ `drum_notes` เรียก — ตรวจค่าด้วยกฎเดิมของ `PUT`; และบทเรียนชั่วคราวให้ `timeline`/`mixer` ผสมเสียงตัวอย่าง (D12, D21)
- **`pyproject.toml`**: `onnxruntime==1.32.0` (D7)
- **`NOTICE.md`**: license และ attribution ของ ADTOF (ผู้เขียนและผู้แปลง), Beat This!, Basic Pitch (Apache-2.0 ของ Spotify และ MIT ของ repo ที่ host), onnxruntime (D7, D16)
- **`.claude/skills/fastapi-api`**: บรรทัด Never break เรื่องช่อง GPU เพิ่มข้อยกเว้นโมเดล ONNX บน CPU ตาม ADR ใหม่ (D8)
- **`frontend/src/features/drum-notes`**: สองหน้าใต้ `#/songs` (D2); `App` และ `useHash` รู้จัก tab `songs` ต่อท้าย `drums`

### Data

ไฟล์ใน `media/songs/` (D3, D20):

| Path | Holds |
|---|---|
| `{song_id}/song.json` | Song (schema ด้านล่าง) เขียนแบบ `write_atomic` |
| `{song_id}/audio.m4a` | เสียงทั้งเพลง aac แบบคลังเสียงพื้นของ toon; ไม่มีสำหรับ MIDI |
| `.partial/` | ไฟล์ที่กำลังโหลด รับ หรือแปลง ล้างตอน start |

`song_id` ตาม spoil D51 (`[A-Za-z0-9_-]{1,64}`); ทุก route เช็ค `fullmatch` ก่อนสร้าง path ไม่ตรง = `404` `not_found`. folder ที่ไม่มี `song.json` ถูกลบตอน start (D20). Schema ของ `song.json`:

```json
{
  "version": 1,
  "id": "dQw4w9WgXcQ",
  "title": "Smells Like Teen Spirit",
  "subtitle": "Nirvana",
  "source": { "kind": "link", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" },
  "duration_s": 301.2,
  "range": { "start_s": 0.0, "end_s": 30.0, "mode": "drums" },
  "analysis": {
    "mode": "drums",
    "start_s": 0.0,
    "end_s": 30.0,
    "beats": [0.52, 1.04],
    "downbeats": [0.52, 2.6],
    "hits": [{ "t": 0.52, "piece": "kick", "level": "normal" }],
    "picked_at": "2026-11-14T10:30:00+07:00"
  },
  "lessons": ["k3v9x0a1b2c4"],
  "created_at": "2026-11-14T10:20:00+07:00",
  "updated_at": "2026-11-14T10:30:00+07:00"
}
```

| Field | Rule |
|---|---|
| `title` | 1–60 ตัวอักษร (นับ code point แบบ story-kb D12) |
| `subtitle` | 0–60 ตัวอักษร |
| `source.kind` | `link` (มี `url`), `file` (มี `name`, `size`), `midi` (มี `name`, `size`) |
| `duration_s` | 4–600 วัดจากไฟล์จริง (D4, D20); MIDI = เวลาจบของโน้ตสุดท้าย + 1 ห้อง ≤ 600 |
| `range` | `null` สำหรับ MIDI; `start_s` ≥ 0, `end_s` ≤ `duration_s`, 4 ≤ `end_s − start_s` ≤ 90 (D5, D18) |
| `range.mode`, `analysis.mode` | `drums` หรือ `melody` (D14); MIDI = `drums` |
| `analysis` | `null` จนแกะเสร็จ; `beats` และ `downbeats` เป็นวินาทีของเพลงเรียงขึ้น `downbeats` ⊆ `beats` และยาว ≥ 2; `hits[].t` วินาทีของเพลง; `hits[].piece` id ใน `kit` (video-gen); `hits[].level` `ghost`, `normal`, `accent` (D9); `hits` ≤ 20,000 ตัว (D20) |
| `lessons` | id ของบทเรียนกลอง ไม่ซ้ำ |

ค่าไม่ผ่าน = `400` `invalid_request` พร้อม `field`. `GET /songs` ส่งแค่สรุปของ `analysis` ไม่ส่ง `hits` (D20).

### Song import

งานลิงก์ (thread, ADR-0010, slot ของตัวเอง, บน `audio_imports`) (D4, D20):

1. ตรวจ `url` ด้วย `spoil.links.parse` (host สาธารณะ, ADR-0029) → `400` `invalid_request`
2. `gate_rows.songs_link` ไม่ ok → `503` `not_ready`
3. งานลิงก์หรือไฟล์กำลังรัน → `409` `busy`
4. ลิงก์ YouTube ที่ id ซ้ำกับเพลงที่มี → `200` `{song_id}` ไม่เริ่มงาน (D3)
5. ตอบ `202` แล้วใน thread: `fetch_info` (`checking`; id ของเว็บอื่นจาก `links.clip_id` — มี `song.json` แล้ว → `done` ด้วย `song_id` เดิม `percent` 100 ไม่โหลด; `duration` ที่มีค่า > 600 → `too_long`; error ตาม `adapter.error_code`) → `disk.require_free` (ขนาดไฟล์ + ความยาว × 16 kB) → โหลด `bestaudio` ลง `.partial/` (`downloading`, %) → ffmpeg อ่านความยาวจริง (< 4 → `too_short`, > 600 → `too_long`) → แปลงเป็น `audio.m4a` ใน `.partial/` ด้วย `-t 600` (`converting`) → ย้ายเข้า folder แล้วเขียน `song.json` สุดท้าย (`done`, มี `song_id`); ไม่เขียนทับ `song.json` ที่มีอยู่
6. ยกเลิก: `DownloadCancelled` ใน hook หรือ kill ffmpeg แล้วลบไฟล์ใน `.partial/` → `cancelled`

ไฟล์ (request เดียว, ADR-0028): `POST /songs/check` `{name, size}` ตรวจ `size` ≤ 200 MB (`.mid` ≤ 5 MB) และดิสก์; ชื่อ+ขนาดซ้ำ → `200` `{song_id}` ก่อนส่ง body (D20). แล้ว `PUT /songs?name=&size=` body ดิบเขียน `.partial/` ทีละก้อน (ค้าง 60 วินาที = `stalled`, `uploads.receive`); `.mid`/`.midi` → `midi.parse` → `song.json`; อื่น → ffmpeg อ่านความยาว (`unsupported_file` เมื่ออ่านเสียงไม่ได้, `too_short` < 4, `too_long` > 600) แล้วแปลงเป็น `audio.m4a`; ตอบ `201` Song. หน้าเว็บปิดระหว่างแปลง → ffmpeg หยุด ไม่มีเพลงเกิด (แบบ `toon.sounds`).

MIDI (D10, D20): รับ format 0 และ 1 ไม่รับ SMPTE; ต้องมีโน้ตช่อง 10 (ไม่มี = `unsupported_file` "ไฟล์นี้ไม่มีแทร็กกลอง"); time signature ตัวแรกต้อง 4/4; tempo ตัวแรก 20–400 BPM และ division 24–960 ไม่งั้น `unsupported_file`; เวลาจบ > 600 วินาที = `too_long`; การตี > 20,000 = `unsupported_file`; `beats` และ `downbeats` คำนวณจาก tempo ทุกจังหวะจนถึงห้องสุดท้าย.

### Pick job

หนึ่งงานต่อครั้งทั้ง tab, `JobSlot` ธรรมดา, thread, ไม่จองช่อง GPU (D8). `POST /songs/{id}/pick` `{}`:

1. `{id}` ไม่ตรงรูปแบบหรือไม่มี → `404` `not_found`; `source.kind` = `midi` → `409` `not_applicable`
2. gate ตาม `range.mode` (`pick_drums` หรือ `pick_melody`) ไม่ ok → `503` `not_ready`
3. งานรันอยู่ → `409` `busy` (มี `song_id`)
4. `range` ไม่ผ่านกฎ → `400` `invalid_request`
5. อ่าน `range` ครั้งเดียว ตอบ `202` แล้วใน thread:
   - `preparing`: `ffmpeg.run_capture` ถอด `audio.m4a` ช่วง `[start_s, end_s)` เป็น float32 mono สองอัตรา: 44.1 kHz (ADTOF) และ 22.05 kHz (Beat This!, Basic Pitch) ไม่เขียนไฟล์
   - `picking`: โหมดกลอง — ADTOF ป้อนทั้งช่วงครั้งเดียว (RNN; D20) ได้ `activations [1, frames, 5]`; Beat This! ทีละ chunk 1,500 เฟรม (`pad_frames` 6 ที่ต้นและท้ายของทั้งช่วง 0 ที่อื่น) ได้ `beat`, `downbeat` ต่อ chunk; โหมดทำนอง — Basic Pitch ทีละหน้าต่าง 43,844 sample ซ้อน 30 เฟรม แทน ADTOF; `percent` = (โมเดลและ chunk ที่เสร็จ) / ทั้งหมด; เช็ค `cancel` ก่อนเริ่มแต่ละโมเดลและระหว่าง chunk (D18, D20)
   - `score`: `stitch` ต่อ chunk ของ Beat This! (ตัด 6 เฟรมแต่ละด้าน chunk สุดท้ายเลื่อนให้จบที่ท้ายช่วง); peak picking ต่อชนิดด้วย threshold และหน้าต่างของ model card (D6) → การตี; จังหวะ = peak ของ `beat` ในหน้าต่าง 7 เฟรมที่ logit > 0, peak ติดกันรวม; downbeat = peak ของ `downbeat` ย้ายไปจังหวะใกล้สุด; เวลาทุกค่าบวก `start_s` กลับเป็นวินาทีของเพลง; downbeat < 2 → `failed` `no_beats`
   - เขียน `analysis` ลง `song.json` ใต้ lock (`done`); แกะใหม่ทับของเดิม

| State | ความหมาย |
|---|---|
| `preparing` | ffmpeg กำลังถอดช่วง |
| `picking` | รันโมเดล, `percent` 0–100 |
| `done` | `analysis` เขียนแล้ว |
| `failed` | `error` = `no_beats`, `model_broken` (สร้าง session ไม่ได้; มี `rows` และ `fix` คำสั่ง Setup script), `model_failed` (ขั้น `run` โยน error; บรรทัดแรกใน `message`), `internal` |
| `cancelled` | ผู้ใช้ยกเลิก |

restart ระหว่างรัน: งานหาย `analysis` เดิม (ถ้ามี) อยู่ต่อ.

### Score

ขั้นเลขล้วนใน `drum_notes.score` (D9, D11, D13, D14, D20) ใช้ร่วมกันทุกต้นทาง (เสียง, MIDI):

1. ห้องที่พบ = ช่วงระหว่าง downbeat ติดกัน; ห้องสุดท้ายจบที่ downbeat สุดท้าย (ห้องที่ไม่มีจุดจบไม่นับ); ห้องที่มีจังหวะ (`beats` ในช่วง รวมต้นห้อง) ไม่เท่ากับ 4 ตัว = "ไม่ใช่ 4/4" เลือกไม่ได้; MIDI: ห้องจาก tempo กับ time signature (D10)
2. ผู้ใช้เลือกห้องแรก `bar` (0 ขึ้นไป) และจำนวน `bars` 1–4 โดย `bar + bars` ≤ จำนวนห้อง และทุกห้องที่เลือกเป็น 4/4 ไม่งั้น `400` `invalid_request` field `bar`
3. BPM ตั้งต้น = `round(240 / median(ความยาวห้องที่เลือก))` จำกัด 40–240; ผู้ใช้แก้ได้
4. การตีอยู่ในห้อง `i` เมื่อ `downbeat_i − ช่อง_i/2 ≤ t < downbeat_{i+1} − ช่อง_i/2` โดย `ช่อง_i` = ความยาวห้อง `i` / 16; ช่อง = `round((t − downbeat_i) / ช่อง_i) + 16 × (i − bar)`; เก็บเฉพาะ `0 ≤ ช่อง < 16 × bars`; ชิ้นเดียวกันซ้ำช่องเดียวกันเหลือตัวที่ `level` สูงสุด
5. โหมดทำนอง: การตีจากโมเดลเป็น `snare`; เติม `kick` ที่ช่อง 0 และ 8 ของทุกห้อง และ `hihat_closed` ทุกช่องคู่ (D14)
6. ตัดต่อช่อง: `hihat_open` คู่ `hihat_closed` เหลือ `hihat_closed`; โน้ตมือเกินสองตัวเหลือสองตามลำดับ `snare` > `crash` > `hihat_closed` > `hihat_open` > `ride` > `tom_high` > `tom_mid` > `tom_floor`; ที่ตัดเก็บเป็นรายการ `dropped` `{piece, step}`
7. มือ: สองโน้ตมือในช่อง → R ให้ชิ้นที่อยู่ขวา (`ride` > `hihat_closed`/`hihat_open` > `crash` > `tom_floor` > `tom_mid` > `tom_high` > `snare`); หนึ่งโน้ตมือ: "โน้ตมือก่อนหน้า" คือโน้ตมือล่าสุดก่อนช่องนี้ (ช่องที่มีสองมือนับตัว R); ห่าง**น้อยกว่า** 2 ช่อง → มือตรงข้ามของตัวก่อน; ไม่งั้น ฉาบ (ไฮแฮท ไรด์ แครช) R, `snare`/`tom_high` L เมื่อโน้ตมือก่อนหน้าห่าง ≤ 2 ช่องและเป็นฉาบมือ R ไม่งั้น R, ทอมอื่น R; เท้า (`kick`, `hihat_pedal`) ไม่มีมือ
8. ผล: `groove` ตาม schema ของ video-gen (`bars`, `notes[]` ที่มี `piece`, `step`, `hand`, `hit`) ผ่านกฎ D20 ของ video-gen ทุกข้อ, `bpm`, `dropped`

ตัวอย่างที่ test ใช้ (Seams 2): ห้องยาว 2.0 วินาที ต้นห้อง 10.0 → BPM 120; การตีที่ 10.49 ลงช่อง 4 (`0.49 / 0.125 = 3.92`); ที่ 9.95 (ก่อนต้นห้องแรก 50 ms น้อยกว่าครึ่งช่อง 62.5 ms) ลงช่อง 0; ที่ 11.94 เมื่อเลือกห้องเดียวได้ช่อง 16 = ทิ้ง.

### API

ทุก route อยู่ใต้ `/api/songs`. `POST`/`PUT` เป็น JSON (ADR-0013) ยกเว้น `PUT /songs` ที่รับ `application/octet-stream` (ADR-0028). error เป็น `{code, message}` (spoil-maker D63).

| Method | Path | ทำอะไร | Error |
|---|---|---|---|
| `GET` | `/songs` | รายการ: `id`, `title`, `subtitle`, `source.kind`, `duration_s`, `analysis` ย่อ (`mode`, `bars`) หรือ `null`, `lessons` (จำนวน), `updated_at`; ข้าม `song.json` ที่อ่านไม่ได้ (log) | — |
| `POST` | `/songs/link` | `{url}` → `202` งาน หรือ `200` `{song_id}` เมื่อ YouTube ซ้ำ | `400` `invalid_request`, `503` `not_ready`, `409` `busy` |
| `GET` | `/songs/import` | งานลิงก์ล่าสุด: `url`, `state`, `title`, `percent`, `error`, `song_id` หรือ `null` | — |
| `POST` | `/songs/import/cancel` | `{}` → งาน | `409` `not_running` |
| `POST` | `/songs/check` | `{name, size}` → `{size}` (ADR-0028) หรือ `200` `{song_id}` เมื่อซ้ำ | `413` `file_too_large`, `409` `busy`, `507` `disk_full`, `503` `not_ready`, `400` `invalid_request` |
| `PUT` | `/songs?name=&size=` | body ดิบ → `201` Song | `413`, `415` `unsupported_file`, `422` `too_long`, `422` `too_short`, `400` `size_mismatch`, `409` `busy`, `507` |
| `GET` | `/songs/{id}` | Song เต็ม (`lessons` กรองที่หายแล้ว) | `404` `not_found` |
| `DELETE` | `/songs/{id}` | `204` ลบ `audio.m4a` แล้ว `song.json` แล้ว folder; บทเรียนไม่ถูกลบ | `409` `song_busy`, `409` `in_use`, `404` |
| `GET` | `/songs/{id}/audio.m4a` | `FileResponse` (ตอบ `Range` ให้ player เลื่อนได้) | `404` |
| `PUT` | `/songs/{id}/range` | `{start_s, end_s, mode}` → Song | `400` `invalid_request` (มี `field`), `409` `not_applicable` (MIDI), `404` |
| `POST` | `/songs/{id}/pick` | `{}` → `202` งาน | ตาม Pick job |
| `GET` | `/songs/pick` | งานล่าสุด: `song_id`, `state`, `percent`, `error`, `message`, `rows`, `fix`, `cancel_requested`, `started_at` (D24) หรือ `null` | — |
| `POST` | `/songs/pick/cancel` | `{}` → งาน | `409` `not_running` |
| `POST` | `/songs/{id}/preview` | `{bar, bars, bpm?}` → `{groove, bpm, dropped: [{piece, step}]}` ของ Score ขั้น 2–8 | `400` `invalid_request` (field `bar` เมื่อห้องไม่ใช่ 4/4), `409` `no_analysis`, `404` |
| `POST` | `/songs/{id}/listen` | `{bar, bars, bpm}` → `audio/wav` ของ Groove ตัวอย่าง (นับเข้า 1 ห้อง + ท่อนสอนตั้งต้นของ video-gen) `Cache-Control: no-store` (D21) | `503` `not_ready` (`drum_kit`), `400`, `409` `no_analysis`, `404` |
| `POST` | `/songs/{id}/lessons` | `{bar, bars, bpm}` → `201` `{lesson_id, dropped}` (จำนวน); สร้างบทเรียนตาม D12 แล้วเติม `lessons` | `400` `invalid_request`, `409` `no_analysis`, `404` |

`song_busy` = Pick job ที่ยังไม่จบเป็นของเพลงนี้. `PUT /range` ระหว่าง Pick job ของเพลงเดียวกันทำได้ (งานอ่าน `range` ครั้งเดียวตอนเริ่ม).

### Status check and Setup

- `ModelSpec` สามตัว (D7) ใน `MODELS` โหลดด้วย `_snapshot_download` + marker แบบโมเดลอื่น (ADR-0004); แถว `model_adtof` ("ADTOF drum model"), `model_beat_this` ("Beat This! model"), `model_basic_pitch` ("Basic Pitch model") ค่าแสดง repo กับ revision สั้น
- Setup script สร้าง `InferenceSession` ของแต่ละไฟล์หนึ่งครั้งหลังโหลดครบ (smoke) ก่อนเขียน marker; ล้ม = Setup จบด้วย error ชื่อไฟล์ (D20)
- แถว `onnxruntime` ("onnxruntime") ok เมื่อ import ได้และเวอร์ชันตรง `1.32.0` (`check_pinned` แบบ `pythainlp`); `fix` คือคำสั่ง Setup script
- หน้าสถานะและ `NOTICE.md` แสดง license กับผู้เขียนของสามโมเดล (ADR-0017, D16)

### Frontend

- `features/drum-notes` มี `SongsPage` ที่เลือกหน้าตาม hash: `#/songs` รายการ, `#/songs/{id}` หน้าเพลง; hash อื่นใต้ `#/songs` = รายการ
- ลิงก์: `POST /songs/link` แล้ว poll `GET /songs/import` (`usePollWhile`); `done` → รายการใหม่ (ไม่พาไปหน้าเพลงเอง); `200` ซ้ำ → ข้อความแล้วพาไปหน้าเพลง
- ไฟล์: `POST /songs/check` (ซ้ำ → พาไปหน้าเพลงเดิม) แล้ว `sendFile` `PUT /songs` (spoil D58) → `201` → พาไป `#/songs/{id}`
- หน้าเพลง: "แกะโน้ต" → `PUT /range` แล้ว `POST /pick` แล้ว poll `GET /songs/pick`; `done` → อ่าน Song ใหม่
- กดห้องบนแถบ → `audio.currentTime` = ต้นห้อง และเป็นห้องแรกของช่วงบทเรียน (D20)
- เลือกห้องหรือแก้ BPM → `POST /preview` (debounce 300 ms) → ตารางอ่านอย่างเดียวและรายการที่ตัด; "ฟัง" → `POST /listen` เล่นด้วย `playAudio` (D21); "สร้างบทเรียนกลอง" → `POST /lessons` → `#/drums/{lesson_id}`
- ตารางอ่านอย่างเดียวใช้ตัววาดตารางของ video-gen (`GrooveGrid`) ในโหมดกดไม่ได้; ย้ายไป `components/ui/` เมื่อเป็นผู้ใช้ที่สอง (กติกา "Where shared code goes")

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| onnxruntime | 1.32.0 | `InferenceSession(path, providers=["CPUExecutionProvider"])`, `get_inputs()`/`get_outputs()` บอกชื่อและรูปร่าง, `run(None, {name: ndarray})` คืน list ของ ndarray; สร้าง session จากไฟล์เสียโยน exception | [Python API](https://onnxruntime.ai/docs/api/python/api_summary.html) |
| onnxruntime | 1.32.0 | wheel `cp312` สำหรับ `macosx_14_0_arm64` และ `win_amd64`, license MIT, `requires_python >= 3.11` | [PyPI](https://pypi.org/project/onnxruntime/) |
| ADTOF Frame_RNN (ONNX) | revision `d0e809bb` | input `waveform` `[1, samples]` float32 mono 44.1 kHz ใน [−1, 1]; output `activations` `[1, ceil(samples/441), 5]` sigmoid 100 เฟรม/วินาที ลำดับ kick, snare, toms, hi-hat, cymbals; threshold 0.22, 0.24, 0.32, 0.22, 0.30; peak picking `pre_avg 0.1, post_avg 0.01, pre_max 0.02, post_max 0.01, combine 0.02` | [model card](https://huggingface.co/thebluescreen/adtof-drums-onnx) |
| Beat This! (ONNX) | revision `92842057` | input `waveform` `[1, N]` float32 mono 22.05 kHz, `N = (frames − 1) × 441 + 1024`, และ `pad_frames` `[2]` int64; output `beat`, `downbeat` `[1, T]` logit 50 เฟรม/วินาที `T = pad_frames[0] + frames + pad_frames[1]`; peak ในหน้าต่าง 7 เฟรม logit > 0; chunk 1,500 เฟรม ซ้อน 6 ตัด 6 ต่อด้าน chunk สุดท้ายเลื่อนให้จบที่ท้าย | [model card](https://huggingface.co/thebluescreen/beat-this-onnx) |
| Basic Pitch (ONNX) | sha256 `2c3c1d14` | หน้าต่าง 43,844 sample ที่ 22,050 Hz; output `note`, `onset` 172 เฟรม × 88 โน้ต (`ANNOTATIONS_FPS` 86); ซ้อน 30 เฟรม (`DEFAULT_OVERLAPPING_FRAMES`, ตัด 15 ต่อด้าน); onset threshold ตั้งต้น 0.5 — ชื่อ input/output อ่านจากไฟล์ตอน build (Open Question 1) | [constants.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/constants.py), [inference.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/inference.py), [README](https://github.com/spotify/basic-pitch) |
| ffmpeg | 7.1 (imageio-ffmpeg 0.7.0) | `-ss`/`-t` ตัดช่วงและเพดาน, `-ac 1 -ar 22050 -f f32le -` ส่ง PCM float ดิบออก stdout; `-c:a aac -b:a {bitrate} -vn` แปลงเป็น m4a (แบบ `toon.compose`) | [ffmpeg main options](https://ffmpeg.org/ffmpeg.html#Main-options), [raw PCM muxers](https://ffmpeg.org/ffmpeg-formats.html#Raw-muxers) |
| yt-dlp | 2026.10.26 | `format: "bestaudio"` โหลดเสียงอย่างเดียว; `duration` ใน info dict อาจเป็น `None` | [README › Format selection](https://github.com/yt-dlp/yt-dlp#format-selection) |
| numpy | 2.5.4 | `median`, `argmax`, `sliding_window_view` สำหรับ peak picking และหน้าต่าง max/mean | [sliding_window_view](https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html) |
| Starlette | 1.10.0 | `FileResponse` ตอบ `Range` ด้วย `206` (video-gen ใช้กับ mp4 แล้ว) | [FileResponse](https://www.starlette.io/responses/#fileresponse) |
| Python | 3.12 | `struct` อ่าน big-endian ของ MIDI header และ track | [struct](https://docs.python.org/3.12/library/struct.html) |

## Seams

สาม seam ตาม D17: โมเดลจริงอยู่หลังขอบเดียว (`onnx_runner`) ที่ test แทนด้วย fake ที่หยุดได้ (`pause_at`, D20); ทุกอย่างหลังจากนั้นเป็นเลขล้วน; ทางเดินของผู้ใช้พิสูจน์ผ่าน `App`.

1. **API ของ tab แกะเพลง** `/api/songs/*` ผ่าน `TestClient` ด้วย ffmpeg จริง, `YtDlpAdapter` ปลอม, `FakeOnnxRunner` และ snapshot กับ marker จาก `fake_root` (ModelSpec อยู่ใน `MODELS`)
   - `POST /songs/link` แล้ว poll จน `done` → `media/songs/{id}/audio.m4a` เป็น aac ความยาวตรงไฟล์ปลอม ± 0.1 วินาที; `GET /songs` มีเพลง `source.kind` = `link`
   - ลิงก์ YouTube เดิมซ้ำ → `200` `{song_id}` เดิม ไม่มีงานใหม่; ลิงก์เว็บอื่นที่ id ซ้ำ → งาน `done` `song_id` เดิมโดย adapter ไม่ถูกเรียก download และ `analysis` เดิมอยู่; info `duration` 700 → `failed` `too_long`; ไฟล์เสียงปลอม 2 วินาที → `failed` `too_short` ไม่มี folder
   - `PUT /songs` mp3 สั้น → `201` มี `audio.m4a`; ไฟล์ข้อความ → `415` `unsupported_file`; `.mid` ที่มีช่อง 10 → `201` `source.kind` = `midi` มี `analysis` และไม่มี `audio.m4a`; `.mid` 3/4 หรือไม่มีช่อง 10 → `415`; เกินขนาด → `413` ที่ `check` และ `PUT`; `check` ชื่อ+ขนาดซ้ำ → `200` `{song_id}`
   - `PUT /range` 2 วินาที หรือ 100 วินาที หรือเกิน `duration_s` → `400` มี `field`; MIDI → `409` `not_applicable`
   - `POST /pick` แล้ว poll จน `done` → `analysis` มี `beats`, `downbeats`, `hits` ที่เวลาบวก `start_s` แล้ว; fake ที่คืน `downbeat` ต่ำกว่า 2 ตัว → `failed` `no_beats`; fake ที่โยนตอนสร้าง session → `failed` `model_broken` มี `fix`; ไม่มี marker → `503` `not_ready` มี `rows`; fake หยุดที่ chunk แรก: งานซ้อน → `409` `busy`, ลบเพลง → `409` `song_busy`, ยกเลิก → `cancelled` และ `analysis` เดิมอยู่
   - `POST /preview` → `groove`, `bpm`, `dropped` รายการ; `POST /listen` → wav ยาวตาม `length_s` ของบทเรียนชั่วคราว; `POST /lessons` `{bar: 0, bars: 2}` → `201` `lesson_id`; `GET /api/drums/lessons/{id}` มี Groove 2 ห้อง BPM และโน้ตตาม Score, `title` = ชื่อเพลง, ท่อนสอนสองท่อน; `GET /songs/{id}` › `lessons` มี id; ลบบทเรียนแล้ว → `lessons` ว่าง; `bar + bars` เกิน หรือห้องที่ไม่ใช่ 4/4 → `400` field `bar`; ยังไม่แกะ → `409` `no_analysis`
   - id `..`, `%2E%2E` → `404` และไม่มีไฟล์ใดหาย; `DELETE` → folder หาย บทเรียนที่สร้างยังอยู่
   - start ล้าง `.partial/` และ folder ที่ไม่มี `song.json`
   - test เดิมของ `toon.sounds` ผ่านหลังย้ายโค้ดไป `audio_imports`
2. **Score** `drum_notes.score`
   - `stitch`: logit สังเคราะห์สาม chunk ซ้อน 6 → array เดียวยาวเท่าจำนวนเฟรมของช่วง ค่าตรงต้นฉบับทุกเฟรม
   - activation สังเคราะห์ (ค่า 1.0 ที่เฟรมของการตี ที่เหลือ 0) และ logit สังเคราะห์ (จังหวะทุก 0.5 วินาที downbeat ทุก 2.0) → การตี จังหวะ และห้องตรงเวลาที่วาง ± 10 ms
   - round trip: บทเรียน video-gen (Groove 2 ห้อง BPM 120 มี kick, snare, tom_mid, hihat_closed, crash) → `video_gen.timeline.build` → การตี → quantize → `groove.notes` เท่ากับของเดิมทุกตัว (ชิ้น ช่อง); เลื่อนเวลาสลับ +20/−20 ms ทุกตัว → ยังเท่ากัน
   - ตัวอย่างใน Score: 10.49 → ช่อง 4; 9.95 → ช่อง 0; 11.94 → ทิ้ง เมื่อห้องเดียว
   - ห้องที่มี 3 จังหวะ → เลือกไม่ได้ (field `bar`); ห้อง 4 จังหวะยาว 2.0 → BPM 120
   - `hihat_closed` และ `snare` และ `crash` ช่องเดียวกัน → เหลือ `snare` และ `crash`, `dropped` = `[{hihat_closed, step}]`; `hihat_open` คู่ `hihat_closed` → เหลือ `hihat_closed`
   - มือ: ไฮแฮท 16th ติดกัน 8 ตัว → R L R L …; groove ร็อก (ไฮแฮท 8th + snare ช่อง 4, 12) → ไฮแฮท R ทุกตัว snare L; crash หลังพัก 4 ช่อง → R
   - โหมดทำนอง: onset 2 ตัวในห้อง → `snare` 2 ตัว + `kick` ช่อง 0 และ 8 + `hihat_closed` 8 ตัว; ผลผ่าน `video_gen.lessons` ตรวจกฎ D20 ไม่ error
   - MIDI: ไฟล์ format 1 ช่อง 10 โน้ต 36, 38, 42 tempo 100 → `analysis` BPM 100 ห้องยาว 2.4 วินาที ชิ้น kick, snare, hihat_closed; velocity 110 → `accent`; ไฟล์ที่ tempo 1,000 BPM หรือการตี 20,001 ตัว → `unsupported_file`
3. **หน้าเว็บ tab แกะเพลง** (e2e) ผ่าน `App` กับ fetch ปลอม (story-kb D18)
   - กด tab "แกะเพลง" → `#/songs` รายการ; ว่าง → ข้อความชวน
   - วางลิงก์แล้วกด → `POST /songs/link` แถวงาน % แล้ว `done` → เพลงในรายการ; error `too_long` → ข้อความ "เพลงยาวเกิน 10 นาที"; `200` ซ้ำ → พาไปหน้าเพลง
   - เลือกไฟล์ → `check` แล้ว `PUT /songs` → พาไป `#/songs/{id}`
   - หน้าเพลงยังไม่แกะ → "ตั้งช่วงแล้วกด แกะโน้ต"; ตั้งช่วง เลือกโหมด กด "แกะโน้ต" → `PUT /range` แล้ว `POST /pick` → แถบ % → `done` → เห็น BPM และห้องที่พบ
   - กดห้องบนแถบ → player เลื่อน และห้องนั้นเป็นห้องแรก; เลือก 2 ห้อง → `POST /preview` → ตารางมีโน้ตและ L/R และรายการที่ตัด; "ฟัง" → `POST /listen` เล่น blob; "สร้างบทเรียนกลอง" → `POST /lessons` → hash เป็น `#/drums/{lesson_id}`
   - เพลง MIDI → ไม่มี player ช่วงแกะ และปุ่มแกะ แต่เลือกห้องและสร้างได้
   - ลบพร้อมยืนยัน → `DELETE`; `song_busy` → ข้อความ

## Testing decisions

- **Copy:** `backend/tests/test_toon_sounds_api.py` — งานลิงก์เสียงด้วย adapter ปลอม, ไฟล์ body ดิบ, ffmpeg จริงแปลงเสียง, error ขนาดและความยาว, fake ที่หยุด (`pause_at`) สำหรับ `busy`
- **Copy:** `backend/tests/test_video_gen_lessons_api.py` — id ที่ไม่ถูก, `write_atomic`, การกรองไฟล์ที่อ่านไม่ได้
- **Copy:** `backend/tests/test_video_gen_timeline.py` — สร้างบทเรียนตัวอย่างและอ่าน `Hit.at` สำหรับ round trip
- **Copy:** `backend/tests/test_setup.py` — การโหลดโมเดลด้วย `fetch` ปลอมและ marker; smoke ของ session ผ่าน runner ปลอม
- **Copy:** `frontend/src/features/video-gen/components/DrumsPage.test.tsx` — หน้าเว็บผ่าน `App` กับ fetch ปลอม และ `sendFile` ด้วย `fakeXhr`
- `fakes.FakeOnnxRunner`: คืน array ที่ test ตั้ง (`activations`, `beat`/`downbeat` ต่อ chunk, `onset`), นับการเรียก, `pause_at(step)`/`wait_until()`/`release()` แบบ `FakeAdapter`; โยนตอนสร้าง session ได้; `PickJobs(open_session=…, run_ffmpeg=…)` รับทาง constructor (กติกา testing; ชื่อตาม D24)
- ModelSpec สามตัวอยู่ใน `MODELS` จึงมี snapshot กับ marker จาก `fake_root` ของ conftest; test `not_ready` ลบ marker
- เสียงปลอมสำหรับ ffmpeg: wav สั้นจาก `soundfile` และ mp3 สั้นที่ ffmpeg สร้างใน fixture (ไม่ commit ไฟล์เสียง)
- ไฟล์ MIDI ใน test สร้างด้วย `struct` ใน fixture
- round trip ใช้ค่าเลื่อนตายตัวสลับ +20/−20 ms ไม่ใช้ค่าสุ่ม (กติกา testing)
- เป้าเวลา (D19), spike Beat This! และความแม่นบนเพลงจริงวัดมือบน Mac ใน ticket ไม่อยู่ใน CI

## Out of Scope

- โน้ตเป็นข้อความ (ASCII drum tab, โน้ตตัวเลข), MusicXML (D1)
- แกะทั้งเพลงหรือตัดท่อนอัตโนมัติ (D5)
- ท่อนสอนอัตโนมัติจากโครงเพลง (D12)
- เสียงเพลงจริงหรือ backing track ในคลิป, เล่นเพลงพร้อมโน้ตที่แกะ (D15, D21)
- waveform หรือตัวลากช่วงบนเสียง (ช่วงเป็นตัวเลขวินาที) (D5)
- รับประกันความแม่นของโน้ต (D6)
- ความแรงจาก activation, แยกไรด์ ไฮแฮทเปิด ทอมสูง/ต่ำ จากเสียง (D9)
- MIDI ที่เปลี่ยน tempo กลางไฟล์ ไม่ใช่ 4/4 หรือไม่มีช่อง 10 (D10, D20)
- onnxruntime บน GPU หรือ CoreML (D8)
- หารายได้จากคลิปที่แกะด้วย ADTOF (D16, legal 3)
- Windows: ทางเดียวกับทุก feature (setup-status D25)

## Open Questions

1. ชื่อ input/output และรูปร่างจริงของ `basic_pitch_nmp.onnx` ใน repo ที่ pin ไม่อยู่ใน model card (รูปร่างใน Library assumptions มาจากต้นฉบับ) — non-blocking: ticket ของโหมดทำนองอ่าน `get_inputs()`/`get_outputs()` จากไฟล์ตอน build; mapping ของ D14 ไม่เปลี่ยน
2. legal ข้อ 3 UNVERIFIED: โน้ตที่ได้จากโมเดล CC BY-NC-SA ถือเป็น adaptation ของโมเดลหรือไม่ — non-blocking: รับความเสี่ยงแล้วใน D16 (ไม่หารายได้ ADR-0017)
3. legal ข้อ 1, 5, 6 UNVERIFIED ตาม spoil D53 และ video-gen D25 — non-blocking: รับความเสี่ยงต่อใน D16
4. Beat This! ที่ pin ยังไม่เคยรันบนเครื่องเจ้าของ (ไฟล์ที่เจ้าของโหลดคือ sha อื่นที่หา repo ไม่พบ) — non-blocking: ticket แรกเริ่มด้วย spike; ล้ม → Blocked row และแผนสองใน D20

## Sources

- [ADTOF Frame_RNN (ONNX) model card](https://huggingface.co/thebluescreen/adtof-drums-onnx) — input/output, threshold, peak picking (accessed 2026-11-14)
- [Beat This! (ONNX) model card](https://huggingface.co/thebluescreen/beat-this-onnx) — input/output, การหา peak, chunk และ `pad_frames` (accessed 2026-11-14)
- [spotify/basic-pitch constants.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/constants.py) — ขนาดหน้าต่าง, 172 เฟรม, 88 โน้ต, `ANNOTATIONS_FPS` (accessed 2026-11-14)
- [spotify/basic-pitch inference.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/inference.py) — `DEFAULT_OVERLAPPING_FRAMES` 30 (accessed 2026-11-14)
- [spotify/basic-pitch README](https://github.com/spotify/basic-pitch) — resample 22,050 Hz (accessed 2026-11-14)
- [onnxruntime Python API](https://onnxruntime.ai/docs/api/python/api_summary.html) — `InferenceSession`, `run` (accessed 2026-11-14)
- [onnxruntime on PyPI](https://pypi.org/project/onnxruntime/) — 1.32.0 wheel และ license (accessed 2026-11-14)
- [FFmpeg main options](https://ffmpeg.org/ffmpeg.html#Main-options) — `-ss`, `-t`, `-ac`, `-ar`, `-c:a` (accessed 2026-11-14)
- [FFmpeg raw muxers](https://ffmpeg.org/ffmpeg-formats.html#Raw-muxers) — `f32le` (accessed 2026-11-14)
- [yt-dlp README › Format selection](https://github.com/yt-dlp/yt-dlp#format-selection) — `bestaudio` (accessed 2026-11-14)
- [numpy sliding_window_view](https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html) — หน้าต่างสำหรับ peak picking (accessed 2026-11-14)
- [Starlette FileResponse](https://www.starlette.io/responses/#fileresponse) — ตอบ `Range` (accessed 2026-11-14)
- [Python struct](https://docs.python.org/3.12/library/struct.html) — อ่าน MIDI (accessed 2026-11-14)
