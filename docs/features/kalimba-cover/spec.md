# Spec: kalimba-cover

Reel cover ของเพลงเลือกได้ว่าจะ render เป็นกลองหรือคาลิมบา จากช่วงเดียวกัน และไฟล์ MIDI ทำนองเข้าเป็นเพลงที่ทำ reel คาลิมบาได้ทันทีโดยไม่ต้องถอดเสียง.

**Status:** ready-to-build

## Problem

เจ้าของทำ reel cover กลองจากเพลงที่แกะได้แล้ว (drum-cover) แต่อยากได้ "แบบเดียวกันแต่เป็นเสียง kalimba ด้วย แบบมีให้ render 2 แบบ คือ kalimba กับกลอง" และ "ถ้าเอา sheet note เข้าไปต้อง render ออกมาเป็น reels ได้ด้วย". วันนี้ทำไม่ได้เพราะ:

- ผลแกะไม่มี pitch: โหมดทำนองยุบทุก onset ของ Basic Pitch เป็น snare (`score.melody_hits`)
- import MIDI อ่านแต่ช่อง 10: ไฟล์ทำนองล้วนตอบ "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง"
- ไม่มีเสียงหรือภาพของคาลิมบา

## Solution

- หน้า reel เลือกเครื่องดนตรี "กลอง" (ตั้งต้น) หรือ "คาลิมบา"; ช่วง ข้อความ พื้นหลัง backing ใช้ชุดเดียวกัน (D1, D10)
- ทุกการแกะเก็บโน้ตทำนองพร้อม pitch ไว้ข้างการตีกลอง เพลงเดียวจึงได้ทั้งสองแบบ (D2)
- ไฟล์ MIDI ที่มีแต่ทำนองเข้าได้ ช่องอื่นนอกจากช่อง 10 เป็นโน้ตทำนอง (D3)
- โน้ตถูกจัดลงคาลิมบา 17 คีย์ C major อัตโนมัติ: ย้ายคีย์ พับอ็อกเทฟ เหลือโน้ตบนสุดเมื่อหลายโน้ตพร้อมกัน; หน้า reel บอกผลการจัด (D4, D9, D14)
- เสียงคาลิมบาสังเคราะห์ในแอป ความดังตั้งแยกและปิดได้แบบเสียงกลอง (D5, D9)
- ภาพ: โน้ตตกลงตามคอลัมน์ของคีย์ คาลิมบาด้านล่างที่คีย์ถูกเล่นสว่าง เลขโน้ตใต้คีย์ ตัวนับห้องเดิม (D7)

## User Stories

**ผู้ทำคลิป**
1. As a ผู้ทำคลิป, I want เลือก "คาลิมบา" บนหน้า reel ของเพลงที่แกะแล้ว, so that ได้ reel คาลิมบาของท่อนเดียวกับ reel กลองโดยไม่ต้องตั้งค่าใหม่ (D1, D2, D10)
2. As a ผู้ทำคลิป, I want ฟังคาลิมบาของช่วงก่อน render และเห็นว่าแอปย้ายคีย์หรือตัดโน้ตไปเท่าไร, so that รู้ว่าทำนองยังเป็นเพลงเดิมก่อนเสียเวลา render (D4, D9)
3. As a ผู้ทำคลิป, I want render reel คาลิมบาเป็น mp4 แนวตั้งที่คีย์สว่างตรงเสียงทุกโน้ต, so that โพสต์ลง reels ได้ และคนดูเล่นตามเลขโน้ตได้ (D7, D12)
4. As a ผู้ทำคลิป, I want ตั้งความดังคาลิมบาแยกจากเพลงต้นฉบับและปิดได้, so that ได้ balance ที่ต้องการเหมือน reel กลอง (D9)
5. As a ผู้ทำคลิป, I want นำเข้าไฟล์ MIDI ทำนองแล้วได้ reel คาลิมบา, so that ทำ reel จากแผ่นโน้ตได้โดยไม่มีคลิปเสียง (D3)
6. As a ผู้ทำคลิป, I want รู้เมื่อเพลงเก่ายังไม่มีโน้ตทำนองหรือช่วงไม่มีโน้ต, so that ไม่เจอ reel เงียบแล้วคิดว่าแอปพัง (D2, D9)

## Design

แบบหน้าจอทำจาก [ui-prompt.md](ui-prompt.md) กับ design system เดิม ไม่รอ Figma (D10). ทุกอย่างที่ไม่เขียนในตารางนี้คงตาม drum-cover spec › Design.

| Screen | User stories | Must show | Source |
|---|---|---|---|
| หน้า reel (`#/songs/{id}/cover`) — ส่วนที่เพิ่ม | 1, 2, 3, 4, 6 | การ์ดแรก "เครื่องดนตรี": ปุ่มสองทาง "กลอง" / "คาลิมบา" ค่าจาก `instrument` (D1, D9); เมื่อคาลิมบา: บรรทัด "{notes} โน้ตทำนองในช่วง" + "ย้ายคีย์ {+k}" เมื่อ `transpose` ไม่ใช่ 0 + "ตัด {dropped} โน้ต" เมื่อ `dropped` > 0 + "ปรับ {bent} โน้ตให้เข้าสเกล" เมื่อ `bent` > 0 (D4, D14); คาลิมบา + backing เปิด + `transpose` ไม่ใช่ 0 → คำเตือนข้าง backing "คาลิมบาย้ายคีย์ {k} เสียงจะไม่ตรงกับเพลงต้นฉบับ" (D14); การ์ด "เสียง": แถวของเครื่องดนตรีที่เลือก — "กลอง" (ของเดิม) หรือ "คาลิมบา" สวิตช์ "ปิดเสียงคาลิมบา" สไลเดอร์ "ความดังคาลิมบา" 10–100 ตั้งต้น 100 ซ่อนเมื่อปิด; "กลองล้วน" / "กลอง + เพลงต้นฉบับ" เปลี่ยนเป็น "คาลิมบาล้วน" / "คาลิมบา + เพลงต้นฉบับ"; ปิดเสียงและไม่มีเพลง → "เปิดเสียงคาลิมบาหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง" ปุ่ม "ฟัง"/"render reel" กดไม่ได้ (D9); `notes_picked` `false` → Alert "เพลงนี้แกะก่อนมีคาลิมบา แกะใหม่ที่หน้าเพลงเพื่อได้โน้ตทำนอง" กับลิงก์กลับหน้าเพลง ปิด "ฟัง"/"render reel"; `notes` 0 → Alert "ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง" ปิดสองปุ่ม; บรรทัด "เพลงนี้แกะโหมดทำนอง reel มีแต่สแนร์" แสดงเฉพาะเมื่อเลือกกลอง; แถวผล render: ป้าย "คาลิมบา" เมื่อ `instrument` `kalimba`, "คาลิมบา {v}%" เมื่อ volume ไม่ใช่ 100, "ไม่มีเสียงคาลิมบา" เมื่อปิด; error `no_notes` แสดง `message` | pending |
| หน้าเพลงและรายการเพลง (`#/songs/{id}`, `#/songs`) — ส่วนที่เพิ่ม | 5, 6 | ส่วน "Reel cover" ของหน้าเพลง: บรรทัดเดิมเพิ่ม "· {m} โน้ตทำนอง" เมื่อ `analysis.notes` ไม่ใช่ `null` (D2); คำใบ้ใต้ปุ่มเลือกไฟล์ของรายการเพลงเพิ่ม "MIDI: ช่อง 10 เป็นกลอง ช่องอื่นเป็นทำนองสำหรับคาลิมบา" และ "ใช้ไฟล์ MIDI ที่ทำเองหรือมีสิทธิ์ใช้" (D3, D13); error `unsupported_file` ของ MIDI แสดงข้อความใหม่ "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลองหรือโน้ตทำนอง" (D3) | pending |

Pending screens: one design prompt in [ui-prompt.md](ui-prompt.md).

## Expected Outcome

ผู้ใช้กดสลับ "คาลิมบา" บนหน้า reel ของเพลงเดิม ฟัง แล้ว render ได้ reel คาลิมบาของท่อนเดียวกัน หรือ import ไฟล์ MIDI ทำนองแล้วได้ reel คาลิมบาโดยไม่ต้องแกะ.

- **เพลงที่แกะใหม่:** หน้า reel สลับกลอง/คาลิมบาได้ การ์ดบอกจำนวนโน้ตและการย้ายคีย์; "ฟัง" ได้ยินทำนองบนคาลิมบา
- **render คาลิมบา:** mp4 1080×1920 ที่โน้ตตกถึงเส้นเล่นและคีย์สว่างพร้อมเสียง; ใต้คีย์มีเลขโน้ต; หัวเรื่องและตัวนับห้องแบบ reel กลอง
- **MIDI ทำนองล้วน:** import ได้ หน้า reel เปิดมาที่ "คาลิมบา" (D9)
- **เพลงที่แกะก่อน feature นี้:** เลือกคาลิมบาแล้วเห็น Alert ให้แกะใหม่ (เพลง MIDI: นำเข้าไฟล์เดิมอีกครั้ง) ไม่ใช่ reel เงียบ
- **โน้ตจากเสียง:** เป็นร่างแบบผลแกะกลอง (drum-notes D6): Basic Pitch ฟังทั้ง mix จึงอาจมีโน้ตเกินหรือขาด; เจ้าของตัดสินด้วยการฟัง (D12)
- **reel กลอง:** เหมือนเดิมทุกอย่าง

**How success is judged:**
- เป้าทุกข้อใน D12 ผ่าน
- reel กลองของเพลงเดิม (volume 100, backing ปิด) ได้ `audio.wav` byte เดียวกับก่อน feature นี้ (D12)
- `song.json` และ `cover.json` ที่เขียนก่อน feature นี้อ่านได้ไม่มี error (D2, D9)

## Implementation

### Modules touched

- **`backend/drum_notes/songs`**
  - `Note` (`t`, `pitch`, `level`) และ `Analysis.notes: list[Note] | None = None` (D2)
- **`backend/drum_notes/score`**
  - `melody_notes(outputs, samples, start_s) -> list[Note]` จาก onset ของ Basic Pitch ทีละคีย์ (spec › โน้ตทำนองจากเสียง); `melody_hits` คงเดิม (D2)
- **`backend/drum_notes/pick`**
  - `_pick` รัน Basic Pitch ทุกโหมดครั้งเดียว แล้วโหมดทำนองใช้ผลชุดนั้นทำ snare; `percent` นับหน้าต่างของ Basic Pitch ทุกโหมด (D2); โหมดกลอง: โมเดล Basic Pitch ไม่มีหรือรันพัง → log แล้ว `notes` `null` งานกลองจบตามเดิม (D14)
- **`backend/gate_rows`**
  - `pick_drums` ไม่เปลี่ยน (D14); `kalimba(project)` = Kanit + ffmpeg + pythainlp (D9)
- **`backend/drum_notes/midi`**
  - อ่าน note-on ทุกช่อง: ช่อง 10 เป็น `hits` ตาม GM map เดิม ช่องอื่นเป็น `notes`; ข้อความใหม่ (D3)
- **`backend/drum_notes/imports`**
  - ไฟล์ MIDI ที่ตรงเพลงเดิม (`KnownSong`) และเพลงนั้น `notes` `null` → อ่านไฟล์ใหม่ เขียน `analysis.notes` ใต้ `songs.lock` แล้วตอบเพลงเดิม (D14)
- **`backend/kalimba_cover`** (package ใหม่, D8)
  - `arrange`: คีย์ของคาลิมบาและ `arranged(notes, start_s, end_s) -> Arranged` (spec › การจัดโน้ตลงคาลิมบา, D4); import ได้แค่ `drum_notes.songs` เพื่อให้ `drum_cover.cover` เรียกได้ (D8, D14)
  - `timeline`: `build(analysis, cover) -> KalimbaTimeline` (D6)
  - `sound`: `note(pitch, level)` และ `mix(timing) -> bytes` (spec › เสียงคาลิมบา, D5)
  - `frames`: `Scene(lesson, timing, background)`, `frame_at(scene, t) -> bytes` ตาม [kalimba-picture-sketch.md](kalimba-picture-sketch.md) (D7)
  - `captions`: `ass_file(project, lesson, timing, title_font)` — หัวเรื่อง บรรทัดรอง คำบรรยาย ตัวนับ เลขและตัวอักษรของคีย์ (D7, D14)
- **`backend/drum_cover`**
  - `cover`: `instrument`, `kalimba`, ค่าตั้งต้น, กติกาห้ามเงียบต่อเครื่องดนตรี, ฟิลด์ใหม่ของ `CoverView` (D9)
  - `audio.reel_wav`: รับ wav ของเครื่องดนตรีที่เลือกแทนการเรียก `mixer.mix` เอง (D8)
  - `render`: เลือก timeline เสียง ภาพ ตัวหนังสือ และ gate ตาม `instrument`; `.json` เพิ่ม `instrument`, `kalimba` (D8, D9)
  - `timeline`: `_numbered_beats` เป็น `numbered_beats(analysis, start, end)` (`scroll_bpm`, `lesson` public อยู่แล้ว) (D6)
  - `frames`: `bars_of(beats)` รับ `Timeline.beats` แทน timing, `beat_dots(frame, bars, beat_times, beats, t)` แทน `_dots(frame, scene, t)` — ไม่อ่าน `Scene` ของกลอง (D7, D14)
  - `captions`: `text_events(project, lesson, end_s, font)` (หัวเรื่อง บรรทัดรอง คำบรรยายที่วันนี้เขียนใน `ass_file`) และ `bar_counter_events(bars, length_s)` ("ห้อง n") แยกออกจาก `ass_file`; `ass_file` ของกลองเรียกสองตัวนี้ ได้ข้อความเดิมทุกตัวอักษร (D7, D14)
- **`.claude/skills/fastapi-api`**: แถว `kalimba_cover/` ในโครงสร้าง
- **`frontend/src/features/drum-cover`**: การ์ด "เครื่องดนตรี", แถวเสียงคาลิมบา, Alert ของโน้ต, ป้ายผล render (D10)
- **`frontend/src/features/drum-notes`**: บรรทัด "{m} โน้ตทำนอง", คำใบ้ MIDI ใน `FILE_HINT` (D3)

### Data

`song.json` (drum-notes) — `analysis` เพิ่ม:

```json
"notes": [
  { "t": 12.034, "pitch": 67, "level": "normal" }
]
```

| Field | Rule |
|---|---|
| `notes` | ไม่มีหรือ `null` = แกะก่อน feature นี้; `[]` = ไม่พบโน้ต; ไม่เกิน 20,000 ตัว เรียงตาม `t` แล้ว `pitch` |
| `notes[].t` | วินาทีของเพลง ใน `analysis.start_s ≤ t < analysis.end_s` |
| `notes[].pitch` | เลข MIDI 0–127 (60 = C4) |
| `notes[].level` | `ghost`, `normal`, `accent`; จากเสียง = `normal`; จาก MIDI ตาม velocity แบบ drum-notes D22 |

`cover.json` (drum-cover) — เพิ่ม (D9):

```json
"instrument": "kalimba",
"kalimba": { "on": true, "volume": 100 }
```

| Field | Rule |
|---|---|
| `instrument` | `drums` หรือ `kalimba`; ไม่มีในไฟล์ → `drums`; `PUT` ต้องมี |
| `kalimba.on` | `true`/`false`; `false` กับ `instrument` `kalimba` ต้องคู่ `backing.on` `true` ไม่งั้น `400` field `kalimba.on` "เปิดเสียงคาลิมบาหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง" |
| `kalimba.volume` | จำนวนเต็ม 10–100; ไม่มีในไฟล์ → `{on: true, volume: 100}`; `PUT` ต้องมี |
| `drums.on` | กติกาห้ามเงียบของ drum-cover D24 ใช้เฉพาะเมื่อ `instrument` `drums` |

ไม่มี `cover.json` → `instrument` ตั้งต้น = `kalimba` เมื่อช่วงตั้งต้นมี `hits` 0 และ `notes` ที่จัดแล้ว > 0; ที่เหลือ `drums` (D9). ผล render `.json` เพิ่ม `instrument` และ `kalimba`; `.json` เก่า → `drums` และ `{on: true, volume: 100}`.

### โน้ตทำนองจากเสียง

`score.melody_notes(outputs, samples, start_s)` บน output onset `[172, 88]` ชุดเดียวกับ `melody_hits` (D2):

1. ทุกหน้าต่าง: เฟรมที่ 15 ≤ frame < 157 (ตัด 15 เฟรมแต่ละข้างแบบเดิม); เวลาเป็น sample = `window.first_sample + frame × 256`
2. ทุกคีย์ `key` 0–87 ที่ค่า ≥ 0.5 เป็น onset ของ `pitch = 21 + key`
3. onset ของคีย์เดียวกันที่ห่างจากตัวก่อนหน้า (รวมหรือไม่รวม) น้อยกว่า 512 sample เป็นโน้ตเดียว ที่เฟรมแรก (กติกาเดียวกับ `melody_hits`)
4. ทิ้ง sample < 0 หรือ ≥ `samples`; `t = round(start_s + sample / 22050, 3)`, `level` `normal`; เรียงตาม `t` แล้ว `pitch`
5. เกิน 20,000 ตัว → เก็บ 20,000 ตัวแรกตามเวลา (ไม่ fail งาน)

### การจัดโน้ตลงคาลิมบา

`kalimba_cover.arrange.arranged(notes, start_s, end_s) -> Arranged(notes, transpose, dropped, bent)` เลขล้วน ผลเดิมทุกครั้ง (D4):

1. โน้ตในช่วง `start_s ≤ t < end_s` เรียงตาม `t` แล้ว `pitch`; ทิ้งโน้ตที่ `pitch` < 48 (ต่ำกว่า C3: เบส) ก่อนทำอะไร นับเป็น `dropped`
2. ย้ายคีย์ `k` ใน −6…+5: นับโน้ตที่ `(pitch + k) mod 12` อยู่ใน {0, 2, 4, 5, 7, 9, 11}; เลือก `k` ที่นับได้มากสุด เสมอกันเลือก `|k|` น้อย แล้ว `k` บวก; ไม่มีโน้ต → `k` 0
3. โน้ตนอกสเกลหลังย้าย → ลงครึ่งเสียง (C# → C, D# → D, F# → F, G# → G, A# → A); นับเป็น `bent`
4. กลุ่มพร้อมกัน: โน้ตที่ `t` ห่างจากโน้ตแรกของกลุ่มไม่เกิน 0.03 วิ; ในกลุ่มเหลือโน้ตที่ pitch (หลังข้อ 3 ก่อนพับ) สูงสุดตัวเดียวที่ `t` และ `level` ของตัวเอง; เสมอกันเลือกตัวที่ `t` น้อยกว่า (ทำนองด้านบน D14)
5. พับอ็อกเทฟโน้ตที่เหลือ: ต่ำกว่า 60 (C4) บวก 12 จนถึง ≥ 60; สูงกว่า 88 (E6) ลบ 12 จนถึง ≤ 88
6. คีย์เดียวกันซ้ำภายใน 0.08 วิหลังตัวที่เก็บก่อนหน้า (นับเฉพาะโน้ตที่ผ่านข้อ 4) → ทิ้งตัวหลัง
7. `dropped` = จำนวนโน้ตที่ทิ้งในข้อ 1, 4 และ 6; `bent` = จำนวนที่ปรับในข้อ 3 ของโน้ตที่เหลือ; `transpose` = `k`

คีย์ (`tine`) เรียงจากซ้ายไปขวาบนภาพ index 0–16:

| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| โน้ต | D6 | B5 | G5 | E5 | C5 | A4 | F4 | D4 | C4 | E4 | G4 | B4 | D5 | F5 | A5 | C6 | E6 |
| pitch | 86 | 83 | 79 | 76 | 72 | 69 | 65 | 62 | 60 | 64 | 67 | 71 | 74 | 77 | 81 | 84 | 88 |
| เลข | 2 | 7 | 5 | 3 | 1 | 6 | 4 | 2 | 1 | 3 | 5 | 7 | 2 | 4 | 6 | 1 | 3 |
| จุด | 2 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 2 | 2 |

ตัวอย่างที่ test ใช้ (Seams 2):

- โน้ต G#3 A#3 C4 (56, 58, 60) ห่างกันตัวละ 0.5 วิ: `k` −1, −3, +4 ได้ 3 ตัวในสเกลเท่ากัน → `k` −1 (`|k|` น้อยสุด); ได้ G3 A3 B3 → พับเป็น G4 A4 B4 (67, 69, 71); `transpose` −1
- โน้ต C4 E4 G4 C5 พร้อมกัน → เหลือ C5; `dropped` 3
- C3 กับ C4 พร้อมกัน → เหลือ C4 (60) ตัวเดียว; `dropped` 1
- ทำนอง E5 D5 C5 ทุก 0.5 วิ กับเบส C2 (36) ทุกจังหวะ → เหลือแต่ทำนอง; `dropped` = จำนวนเบส
- C4 สองครั้งห่าง 0.05 วิ → ตัวที่สองทิ้ง; `dropped` 1
- C#4 (61) ตัวเดียว: `k` −1 ได้ C และ `k` +1 ได้ D อยู่ในสเกลทั้งคู่ (`k` 0 ไม่อยู่) → `|k|` เท่ากัน เลือก `k` บวก → `k` +1, D4 (62)

### Timeline ของคาลิมบา

`kalimba_cover.timeline.build(analysis, cover) -> KalimbaTimeline` (D6):

| Field | Is |
|---|---|
| `notes` | `KalimbaNote(at, tine, pitch, level)` — `at` = `round((t − start_s) × 44100)` ครั้งเดียว, เรียงตาม `at` แล้ว `tine` |
| `beats` | `video_gen.timeline.Beat` ตามกติกาเลขจังหวะของ `drum_cover.timeline` (ใช้ฟังก์ชันเดียวกัน) |
| `length_s` | `end_s − start_s + 1.5` |
| `transpose`, `dropped`, `bent` | จาก `arranged` |
| `samples` | `round(length_s × 44100)` |

Lesson ชั่วคราวสำหรับตัวหนังสือและพื้นหลังใช้ `drum_cover.timeline.lesson` เดิม (BPM ใช้แค่ความเร็วตกของโน้ต).

### เสียงคาลิมบา

`kalimba_cover.sound` (D5) ค่าเริ่มต้นให้ build ใช้ ปรับตอนเจ้าของฟังได้ แต่กติกาผลเดิมทุก byte ต้องคง:

1. `note(pitch, level)`: `f0 = 440 × 2^((pitch − 69) / 12)`; ผลรวมของ sine สามตัว ratio (1, 5.4, 13.0) amplitude (1.0, 0.12, 0.04) decay τ (`1.4 × (261.63 / f0)^0.5`, 0.18, 0.05) วิ; partial ที่สูงกว่า 20 kHz ไม่ใส่
2. เสียงกระทบ: noise จาก `numpy.random.default_rng(0)` ยาว 6 ms × amplitude 0.06 decay 1.5 ms — seed ตายตัว ผลเดิมทุกครั้ง
3. attack เชิงเส้น 2 ms; ยาว `min(5 × τ0, 4.0)` วิ; คูณตาม `level`: ghost 0.45, normal 0.7, accent 1.0
4. `mix(timing)`: วาง `note` ที่ `at` ของแต่ละโน้ต (cache ต่อ `(pitch, level)` ในหนึ่งครั้งที่เรียก); คีย์เดียวกันถูกเล่นซ้ำ → เสียงก่อนหน้า fade 10 ms จาก `at` ใหม่แล้วหยุด (แบบ choke ของ `mixer`)
5. ผลรวม float32 → peak −1 dBFS → `rint` เป็น 16-bit → wav stereo สองช่องเท่ากัน 44.1 kHz ยาว `timing.samples` ด้วย `soundfile` (แบบ `video_gen.mixer.mix`)
6. ไม่มีโน้ต → wav เงียบยาว `timing.samples`

### เสียงของ reel

`drum_cover.audio.reel_wav(audio, fields, instrument_wav, samples, cancel)` (D8, D16): `instrument_wav` = `mixer.mix(project, timing)` เมื่อกลอง หรือ `sound.mix(timing)` เมื่อคาลิมบา; `None` เมื่อเสียงของเครื่องดนตรีที่เลือกปิด. ความดังของเครื่องดนตรีที่เลือก (`drums.volume` หรือ `kalimba.volume`), backing และ peak เป็นกติกาเดิมของ drum-cover spec › เสียง ข้อ 2–5 ทุกข้อ. `volume` 100 + backing ปิด → `instrument_wav` ตรง ๆ (byte เดิม).

### ภาพของ reel คาลิมบา

`kalimba_cover.frames` และ `captions` (D7) วาดตาม [kalimba-picture-sketch.md](kalimba-picture-sketch.md); เวลาทุกอย่างอ่านจาก `KalimbaTimeline` (ADR-0041) ตัวหนังสือทุกตัวอยู่ใน ASS (ADR-0040).

1. `Scene`: ของนิ่งวาดครั้งเดียว — พื้นหลัง (`video_gen.frames.background_image`), ตัวคาลิมบาและคีย์ตอนพัก, จุดอ็อกเทฟ, กรอบคอลัมน์, เส้นเล่น
2. `frame_at(scene, t)` วาดบนสำเนาตามลำดับ: เส้นจังหวะและเส้นห้อง → โน้ตที่ตก → คีย์ที่ถูกเล่นใน 0.15 วิ → จุดจังหวะของตัวนับ (ของ `drum_cover.frames`); `t` เดียวกันได้ bytes เดียวกัน
3. ตำแหน่งโน้ต: `y = 1330 − (at / 44100 − now) × px_per_s`, `px_per_s = max(350, 810 / (1.5 × 4 × 60 / bpm))` (โน้ตสูง 28 px ที่ห่าง 0.08 วิไม่ทับกัน D14); `now` = `min(t, end_s − start_s)`
4. `captions.ass_file`: หัวเรื่อง บรรทัดรอง คำบรรยาย และตัวนับ "ห้อง {n}" ด้วย helper ของ `drum_cover.captions` + เลขและตัวอักษรใต้คีย์ตลอดคลิป; โน้ตที่ตกไม่มีตัวหนังสือ (D14)

### Render job

Render job ของ reel เดิม (drum-cover spec › Render job) slot เดียว `busy` เดิม; ลำดับตรวจของ `POST …/render` ใหม่ทั้งหมด (D8, D9, D14):

1. `{id}` ผิดหรือไม่มี → `404` `not_found`; ไม่มี `analysis` → `409` `no_analysis`
2. อ่าน cover ใต้ `songs.lock` (`cover.used`): backing กับ MIDI หรือเงียบ → `400`
3. `instrument` `kalimba` และ `notes_picked` `false` หรือ `notes` 0 → `409` `no_notes`
4. gate ตาม `instrument`: `drums` → `gate_rows.drums`, `kalimba` → `gate_rows.kalimba` → `503` `not_ready`
5. มี Render job ของ reel รันอยู่ → `409` `busy`
6. `disk.require_free` → `507`; copy เข้า `media/songs/.render/` แล้วตอบ `202`
7. ใน thread: `kalimba` → `kalimba_cover.timeline.build` → `sound.mix` → `reel_wav`; `kalimba_cover.captions.ass_file`; `kalimba_cover.frames.Scene`; `drums` ทางเดิม
8. `.json` เพิ่ม `instrument`, `kalimba`; `.srt` cue เดียวเดิม; ffmpeg `_command`, `percent`, `cancelled`, `failed` และการล้างตอน start เดิม

`POST …/listen` ตรวจข้อ 1–3 ตามลำดับเดียวกัน แล้ว gate: `drums` → `drum_kit`; `kalimba` → ไม่มีแถว; backing เปิด → เพิ่ม `ffmpeg`.

### API

route ของ drum-cover spec › API คงเดิม; ที่เปลี่ยน (D9):

| Method | Path | ที่เพิ่ม | Error ที่เพิ่ม |
|---|---|---|---|
| `GET` | `/songs/{id}/cover` | `instrument`, `kalimba`, `notes`, `notes_picked`, `transpose`, `dropped`, `bent` | — |
| `PUT` | `/songs/{id}/cover` | ต้องมี `instrument`, `kalimba` | `400` field `instrument`, `kalimba.volume`, `kalimba.on` |
| `POST` | `/songs/{id}/cover/listen` | `kalimba` → wav ของคาลิมบา; ไม่ต้องมีแถวใด (ffmpeg เมื่อ backing) | `409` `no_notes` |
| `POST` | `/songs/{id}/cover/render` | ตาม Render job | `409` `no_notes`, `503` `not_ready` ของ `gate_rows.kalimba` |
| `GET` | `/songs/{id}/cover/renders` | แต่ละแถวมี `instrument`, `kalimba` | — |
| `GET` | `/songs/{id}` | `analysis.notes` ทั้งรายการ | — |
| `PUT` | `/songs` (ไฟล์ `.mid` body ดิบ) | ไฟล์ทำนองล้วนรับได้; ไฟล์เดิมของเพลง MIDI ที่ `notes` `null` → เติม `notes` แล้วตอบเพลงเดิม (D14) | `415` ข้อความใหม่ (D3) |

ข้อความของ `no_notes`: `notes_picked` `false` → "เพลงนี้แกะก่อนมีคาลิมบา แกะใหม่ที่หน้าเพลงเพื่อได้โน้ตทำนอง" (เพลง MIDI: "เพลงนี้นำเข้าก่อนมีคาลิมบา นำเข้าไฟล์ MIDI เดิมอีกครั้ง"); `notes` 0 → "ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง".

### Frontend

- `features/drum-cover/lib/cover`: ชนิด `instrument`, `kalimba`, ฟิลด์ใหม่ของ view และ render; ข้อความใหม่ทุกตัวในที่เดียว
- `components/ui/SegmentedChoice.tsx` (ใหม่): `radiogroup` สองทางที่ดึงออกจาก "กลองล้วน"/"กลอง + เพลงต้นฉบับ" ใน `CoverPage` เดิม; `CoverPage`: การ์ด "เครื่องดนตรี" และการ์ดเสียงใช้ตัวนี้ (D14); สลับแล้วฟอร์ม "ยังไม่บันทึก"; "ฟัง"/"render reel" บันทึกก่อนเหมือนเดิม
- แถวเสียงเป็น component เดียวรับ label ("กลอง"/"คาลิมบา") ไม่คัดลอกแถวกลอง
- Alert ของโน้ต ปิดปุ่มตาม `notes_picked`, `notes` เมื่อเลือกคาลิมบา; Alert การตีกลองเดิมแสดงเฉพาะเมื่อเลือกกลอง
- drum-notes: `FILE_HINT` ข้อความใหม่, ส่วน "Reel cover" นับ `analysis.notes`

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| numpy | 2.5.4 | `random.default_rng(seed)` ให้ลำดับเดิมทุกครั้งใน version เดียวกัน; `exp`, `sin` บน `float32` | [Random Generator](https://numpy.org/doc/stable/reference/random/generator.html) |
| numpy | 2.5.4 | `fft.rfft` หาความถี่หลักใน test (D12) | [numpy.fft.rfft](https://numpy.org/doc/stable/reference/generated/numpy.fft.rfft.html) |
| soundfile | ตาม `uv.lock` | เขียน `PCM_16` wav ลง `BytesIO` แบบ `mixer` | [soundfile.write](https://python-soundfile.readthedocs.io/en/latest/#soundfile.write) |
| Pillow | 12.3.0 | `ImageDraw.rounded_rectangle` สำหรับคีย์และโน้ต | [ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html) |
| libass (ffmpeg 7.1) | ตาม imageio-ffmpeg 0.7.0 | `\an` และ `\pos` ตามที่ reel กลองใช้อยู่ ไม่มีอะไรเพิ่ม | [ASS tags](https://aegisub.org/docs/latest/ass_tags/) |

## Seams

สาม seam ของ drum-cover ใช้ต่อ เพิ่มกรณีคาลิมบาเข้าแต่ละจุด (D11).

1. **API ของ reel และเพลง** `/api/songs/*`, `/api/covers/render` ผ่าน `TestClient` ด้วย ffmpeg จริง เพลงที่มี `analysis` เขียนตรง (`fakes.written_song` เพิ่ม `notes`)
   - `GET /cover` ของ `song.json` เก่าไม่มี `notes` → `notes_picked` `false`, `instrument` `drums`; `cover.json` เก่าไม่มี `instrument`/`kalimba` → `drums` และ `{on: true, volume: 100}`
   - เพลงที่ช่วงตั้งต้นไม่มี `hits` แต่มี `notes` → `instrument` ตั้งต้น `kalimba`; มีทั้งคู่ → `drums`
   - render คาลิมบาลำดับ error ตาม spec › Render job: ไม่มี Kanit + `notes` 0 → `409` `no_notes` (ข้อ 3 ก่อน 4); ไม่มี Kanit + งานกลองรันอยู่ → `503` (ข้อ 4 ก่อน 5)
   - `PUT /songs` ไฟล์ MIDI เดิมของเพลงที่ `notes` `null` → ตอบเพลงเดิม `analysis.notes` ครบ `hits` เท่าเดิม; Pick job โหมดกลองที่ Basic Pitch ปลอมโยน error → `done` `notes` `null` `hits` ครบ
   - `PUT /cover` ไม่มี `instrument`, `instrument` `piano`, `kalimba.volume` 5, `kalimba.on` `false` กับ backing ปิดและคาลิมบา → `400` มี `field`; `drums.on` `false` กับคาลิมบา → `200`
   - `POST /listen` คาลิมบา → wav ยาว `length_s` ± 0.05 วิ ไม่เงียบ; สองครั้ง → bytes เดียวกัน; volume 50 → peak ต่ำกว่า 6.0 dB ± 0.1; ไม่มี sample กลองบนดิสก์ → ยังตอบ `200`; `notes` 0 → `409` `no_notes`; `notes_picked` `false` → `409` `no_notes` ข้อความแกะใหม่
   - `POST /listen` กลอง volume 100 → bytes เดียวกับ `mixer.mix` ตรง (ผลเดิม D12)
   - `POST /render` คาลิมบา poll จน `done` → mp4 1080×1920 30 fps h264 aac ความยาว `length_s` ± 0.1; `.json` มี `instrument` `kalimba` และ `kalimba`; `GET …/renders` ของ `.json` เก่า → `drums`
   - **เสียงตรงภาพ:** โน้ต C4 ตัวเดียวที่ `start_s + 1.0` → sample แรกของเสียงใน mp4 กับเฟรมแรกที่จุดวัดสีของคีย์ C4 เป็นสีเติมเต็ม (± 12 ต่อช่องสี) ห่างไม่เกิน 1 เฟรม
   - render คาลิมบาไม่มี Kanit → `503` `not_ready` มี `rows`; render ซ้อนกับ reel กลอง → `409` `busy`
   - `PUT /songs` ไฟล์ MIDI ทำนองล้วน (ช่อง 1) → `201` Song ที่ `hits` ว่าง `notes` ครบ; MIDI กลองล้วนเดิม → `notes` `[]`; ไม่มีทั้งสอง → `415` ข้อความใหม่
   - Pick job โหมดกลองด้วย `onnx_runner` ปลอม → `analysis.notes` จาก onset ปลอมของ Basic Pitch; ไม่มีโมเดล Basic Pitch → งานจบ `done` `notes` `null`
2. **ตัวเลขล้วน** `score.melody_notes`, `midi.read`, `kalimba_cover.arrange`/`timeline`/`sound`/`frames`/`captions`
   - onset ปลอม: คีย์ 39 (pitch 60) ที่เฟรม 20–21 และคีย์ 43 ที่เฟรม 20 → โน้ต 60 และ 64 ที่เวลาเดียวกัน ตัวละหนึ่ง; เฟรม 10 (ถูกตัด) ไม่มีโน้ต; `melody_hits` ของ output เดียวกันเท่าเดิม
   - MIDI: ช่อง 1 note 60 velocity 40 → `notes` `{pitch: 60, level: ghost}`; ช่อง 10 note 38 → `hits` snare; ช่อง 10 note 60 (นอก GM map) → ไม่มีทั้งสอง
   - ตัวอย่างใน spec › การจัดโน้ตลงคาลิมบา ทุกข้อ; ไม่มีโน้ต → `transpose` 0 `notes` ว่าง
   - `timeline.build`: โน้ตที่ `start_s + 1.0` → `at` 44100; เลขจังหวะเท่า `drum_cover.timeline` สำหรับ `analysis` เดียวกัน
   - `sound.note(60, "normal")` → ความถี่หลักใน FFT 261.6 ± 1 Hz; `mix` สองครั้ง → bytes เดียวกัน; peak −1 dBFS
   - `frames.frame_at` ที่ `bpm` 60 กับ C4 สองครั้งห่าง 0.08 วิ → สองโน้ตในคอลัมน์ไม่ทับกัน
   - `frames.frame_at` ที่เวลาโน้ต → จุดวัดสีของคีย์นั้นเป็นสีเติมเต็ม; 0.2 วิหลัง → สีพัก; `t` เดียวกันสองครั้ง → bytes เดียวกัน; ตารางคีย์ใน sketch: คีย์ไม่ทับกัน อยู่ในกรอบ สีของเลข 1–7 ต่างกันทุกคู่
   - `captions.ass_file`: เลขและตัวอักษรใต้คีย์ทั้ง 17 (34 event ไม่ขึ้นกับจำนวนโน้ต), ไม่มี event ของโน้ตที่ตก, หัวเรื่องและ "ห้อง 1" เท่ากับของ reel กลอง
   - test เดิมของ `drum_cover` timeline/frames/captions ผ่านโดยไม่แก้ assertion หลังทำ helper เป็น public
3. **หน้า reel และหน้าเพลง** (e2e) ผ่าน `App` กับ fetch ปลอม
   - เปิด `#/songs/{id}/cover` ที่ `instrument` `drums` → "กลอง" ถูกเลือก แถวเสียง "กลอง"; กด "คาลิมบา" → แถว "คาลิมบา" บรรทัด "48 โน้ตทำนองในช่วง · ย้ายคีย์ +2 · ตัด 3 โน้ต…" จุด "ยังไม่บันทึก"; "บันทึก" → `PUT` ส่ง `instrument: "kalimba"`, `kalimba: {on: true, volume: 100}`
   - GET ตอบ `instrument` `kalimba` กับ `hits` 0 → "คาลิมบา" ถูกเลือก แถวเสียง "คาลิมบา" ไม่มี "ช่วงนี้ไม่มีการตีกลอง…" และ "เพลงนี้แกะโหมดทำนอง…"; คาลิมบา + backing + `transpose` 2 → คำเตือน "คาลิมบาย้ายคีย์ +2…"
   - คาลิมบา + `notes_picked` `false` → Alert "เพลงนี้แกะก่อนมีคาลิมบา…" ปุ่ม "ฟัง"/"render reel" กดไม่ได้; `notes` 0 → Alert "ช่วงนี้ไม่มีโน้ตทำนอง…"
   - เลื่อน "ความดังคาลิมบา" เป็น 60 → `PUT` ส่ง `kalimba.volume` 60; "ปิดเสียงคาลิมบา" กับ "คาลิมบาล้วน" → ข้อความห้ามเงียบ ปุ่มกดไม่ได้
   - "ฟัง" คาลิมบา → บันทึกแล้ว `POST /listen`; "render reel" → แถวผลใหม่มีป้าย "คาลิมบา"
   - หน้าเพลงที่ `analysis.notes` 120 ตัว → ส่วน "Reel cover" มี "· 120 โน้ตทำนอง"; รายการเพลง → คำใบ้ MIDI ใหม่; MIDI ที่ไม่รับ → ข้อความใหม่

## Testing decisions

- **Copy:** `backend/tests/test_drum_cover_api.py` — render ด้วย ffmpeg จริง, test เสียงตรงภาพ, `busy`, `.json` เก่า
- **Copy:** `backend/tests/test_drum_cover_frames.py` และ `test_drum_cover_captions.py` — จุดวัดสี, bytes เดียวกัน, ตารางใน sketch, อ่าน event ของ ASS
- **Copy:** `backend/tests/test_drum_cover_timeline.py` — `analysis` เขียนมือ, sample ของการตี
- **Copy:** `backend/tests/test_drum_notes_score.py` — onset ปลอมของ Basic Pitch ต่อหน้าต่าง; `backend/tests/test_drum_notes_midi.py` — ไฟล์ MIDI ที่สร้างเป็น bytes ใน test
- **Copy:** `backend/tests/test_drum_notes_pick_api.py` — `onnx_runner` ปลอม (เพิ่ม Basic Pitch ให้ test โหมดกลองเดิม)
- **Copy:** `frontend/src/features/drum-cover/components/CoverPage.test.tsx` — หน้า reel ผ่าน `App` กับ fetch ปลอม
- `fakes.written_song` เพิ่ม parameter `notes` (ตั้งต้นไม่ส่ง = ไม่มี key ใน `analysis` แบบไฟล์เก่า) โดย test เดิมเรียกแบบเดิมได้
- ไม่ commit ไฟล์เสียงหรือ MIDI: MIDI สร้างเป็น bytes ใน test
- เป้าเวลา render, Pick job และการฟังของเจ้าของ (D12) วัดมือบน Mac ไม่อยู่ใน CI; ตอน build ภาพ ดึง 3 เฟรมของ reel คาลิมบาแนบใน progress.md ให้เจ้าของดู

## Out of Scope

- MusicXML, PDF หรือภาพแผ่นโน้ต (D3) — MusicXML เป็นคำถามใน progress.md › Blocked
- คาลิมบาโครมาติก คาลิมบาจำนวนคีย์อื่น หรือตั้งเสียงอื่นนอก C major (D4)
- แก้โน้ตหรือเลือกการจัดโน้ตเอง (D4, drum-cover D3)
- sample คาลิมบาจริงตอนนี้ (D5) — เป็นคำถามใน progress.md › Blocked
- reel ที่มีกลองและคาลิมบาพร้อมกันในคลิปเดียว (D1)
- เสียงประสานหรือคอร์ดบนคาลิมบา และเลขบนโน้ตที่ตก (D14)
- ภาพมือหรือนิ้วโป้ง (D7)
- เลือกแทร็กของไฟล์ MIDI (D3)
- Windows: ทางเดียวกับทุก feature (setup-status D25)

## Open Questions

1. legal ข้อ 1 UNVERIFIED: reel คาลิมบาของทำนองที่มีลิขสิทธิ์ ≤ 90 วิ เข้ามาตรา 33 "บางตอนตามสมควร" หรือไม่ — non-blocking: รับความเสี่ยงใน D13
2. legal ข้อ 2 UNVERIFIED: ไฟล์ MIDI ที่โหลดจากเว็บเป็นงานเรียบเรียงที่มีลิขสิทธิ์ของผู้ทำไฟล์หรือไม่ — non-blocking: ผู้ใช้รับผิดชอบ คำใบ้บนหน้า (D13)
3. เจ้าของอยากได้ sample คาลิมบาจริง (VCSL CC0) แทนเสียงสังเคราะห์หรือไม่ — non-blocking: `sound.note` เปลี่ยนแหล่งเสียงได้โดยไม่แตะ timeline หรือภาพ (D5)
4. เจ้าของอยากให้รับ MusicXML ด้วยหรือไม่ — non-blocking: MIDI ครอบเส้นทาง "sheet note → reel" แล้ว (D3)

## Sources

- [numpy Random Generator](https://numpy.org/doc/stable/reference/random/generator.html) — `default_rng(seed)` (accessed 2026-11-16)
- [numpy.fft.rfft](https://numpy.org/doc/stable/reference/generated/numpy.fft.rfft.html) — ความถี่หลักใน test (accessed 2026-11-16)
- [soundfile.write](https://python-soundfile.readthedocs.io/en/latest/#soundfile.write) — wav 16-bit (accessed 2026-11-16)
- [Pillow ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html) — `rounded_rectangle` (accessed 2026-11-16)
- [Aegisub ASS override tags](https://aegisub.org/docs/latest/ass_tags/) — `\an`, `\pos` (accessed 2026-11-16)
