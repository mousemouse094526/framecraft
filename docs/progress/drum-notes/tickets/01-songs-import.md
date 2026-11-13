# 01: เอาเพลงเข้า: ลิงก์ ไฟล์เสียง ไฟล์ MIDI และโมเดล

**What to build:** ผู้ใช้เปิด tab ใหม่ "แกะเพลง" วางลิงก์เพลงหรือเลือกไฟล์เสียง แล้วเพลงอยู่ในรายการพร้อม player; เลือกไฟล์ MIDI แล้วอยู่ที่หน้าเพลงที่เห็นห้องที่พบครบทันที. Setup script โหลดโมเดล ONNX สามตัวและ onnxruntime มีแถวใน Status check; โค้ดเอาเสียงเข้าที่ซ้ำกับคลังเสียงพื้นของ toon ย้ายเป็น `backend.audio_imports` ที่ทั้งสองใช้. ก่อนเขียนของจริง ticket นี้เริ่มด้วย spike: รัน Beat This! และ ADTOF ที่ pin บน `reel.mp4` กับเพลงเต็มหนึ่งเพลง ดูว่า downbeat ตรงเส้นห้อง (ล้ม → Blocked row และแผนสองใน D20).

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D3, D4, D7, D10, D16, D18, D20, spoil D47, spoil D50, spoil D51, spoil D53, spoil D58, toon D39, setup-status D26, story-kb D12
- ADR: 0041, 0043, 0045, 0046
- Screens: รายการเพลง, หน้าเพลง (หัว, player, ห้องที่พบจาก MIDI; ส่วนแกะและสร้างบทเรียนมาใน 02 และ 03)
- Seams: 1 (Song import, Song, MIDI, start), 2 (MIDI), 3 (รายการ, ลิงก์, ไฟล์)
- User stories: 1, 4 (เห็นห้องจาก MIDI; สร้างบทเรียนใน 03), 6 (รายการและลบ)
- Legal: 1, 2, 3 (เครดิตใน `NOTICE.md` และหน้าสถานะ), 4

**Status:** done

## Acceptance criteria

### Spike และโมเดล

- รัน `beat_this.onnx` และ `adtof_frame_rnn.onnx` ที่ pin บน `~/.hermes/cache/scratch/fbreel/reel.mp4` และเพลงเต็มหนึ่งเพลง (เจ้าของเลือก) ด้วย onnxruntime → downbeat ที่ได้ตรงเส้นห้องเมื่อฟังเทียบ และจำนวน kick/snare ของ reel ใกล้ผล `adtof_test.py` ของเจ้าของ (49 และ 31); บันทึกผลใน Log ของ progress.md; ไม่ตรง → Blocked row และหยุด ticket
- Setup script บนเครื่องที่ยังไม่มีโมเดล → โหลด `adtof_frame_rnn.onnx`, `beat_this.onnx`, `analysis/basic_pitch_nmp.onnx` ลง `models/hub/` ที่ revision ที่ pin, สร้าง `InferenceSession` ของแต่ละไฟล์หนึ่งครั้ง แล้วเขียน marker; ไฟล์ที่ session สร้างไม่ได้ → Setup จบด้วย error ชื่อไฟล์ ไม่มี marker
- Status check → แถว `model_adtof`, `model_beat_this`, `model_basic_pitch` ต่อจาก `drum_kit` และ `onnxruntime` ok เมื่อเวอร์ชันตรง `1.32.0`; ไม่มี marker → `missing` พร้อม `fix` คำสั่ง Setup script
- หน้าสถานะและ `NOTICE.md` แสดง license กับผู้เขียนของ ADTOF (Zehren, Alunno, Bientinesi; ผู้แปลง thebluescreen; CC BY-NC-SA 4.0), Beat This! (MIT), Basic Pitch (Apache-2.0), onnxruntime (MIT)
- `pyproject.toml` มี `onnxruntime==1.32.0`; `uv sync` ติดตั้งบน Mac Apple Silicon ได้

### `backend.audio_imports` ใช้ร่วม

- `toon.sounds` เรียก `audio_imports` สำหรับงานลิงก์ รับไฟล์ดิบ แปลง m4a และล้าง `.partial/` → test เดิมของ `test_toon_sounds_api.py` ผ่านโดยไม่แก้พฤติกรรม
- module รับ folder ปลายทาง เพดานความยาว และ callback เขียนผล จากผู้เรียก; ไม่มี import จาก `toon` หรือ `drum_notes` ข้างใน

### Song import

- กด tab "แกะเพลง" → `#/songs` รายการว่างกับข้อความชวน และข้อความ "ใช้เพลงเพื่อแกะโน้ตเท่านั้น เสียงเพลงไม่เข้าคลิป" (e2e)
- `POST /songs/link` ลิงก์ YouTube → `202`; poll `GET /songs/import` ผ่าน `checking` → `downloading` (%) → `converting` → `done` มี `song_id`; `media/songs/{id}/audio.m4a` เป็น aac ความยาวตรงไฟล์ ± 0.1 วินาที และ `song.json` ตาม schema (`title` จากเว็บ, `subtitle` ช่อง, `range` ตั้งต้น 0 ถึง min(30, duration), `analysis` null)
- หน้าเว็บวางลิงก์แล้วกด "เอาเพลงเข้า" → แถวงาน % แล้ว `done` → เพลงในรายการ ชนิด "ลิงก์" ความยาว "ยังไม่แกะ" "0 บทเรียน" (e2e)
- ลิงก์ YouTube ที่ id ซ้ำ → `200` `{song_id}` ไม่มีงาน; ลิงก์เว็บอื่นที่ id ซ้ำ (รู้หลัง `fetch_info`) → งาน `done` `song_id` เดิม `percent` 100 adapter ไม่ถูกเรียก download และ `song.json` เดิมไม่เปลี่ยน; หน้าเว็บ → ข้อความ "เพลงนี้มีอยู่แล้ว" แล้วไป `#/songs/{id}` (e2e)
- info `duration` 700 → `failed` `too_long` "เพลงยาวเกิน 10 นาที"; `duration` ไม่มีค่า แต่ไฟล์ที่โหลดยาว 700 วินาที (วัดด้วย ffmpeg) → `failed` `too_long` ไม่มี folder; ไฟล์ 2 วินาที → `failed` `too_short`
- คำสั่งแปลงมี `-t 600`; error ของ yt-dlp map ตาม `adapter.error_code` (`unsupported`, `playlist`, `live`, `login_required`, `unavailable`, `download_error`); ลิงก์ host private → `400` `invalid_request`; แถว `yt_dlp`/`deno`/`ffmpeg` ขาด → `503` `not_ready` มี `rows` และหน้าเว็บแสดง `fix`
- งานลิงก์รันอยู่ → `POST /songs/link` และ `POST /songs/check` ตอบ `409` `busy`; ยกเลิก → `cancelled` ไม่มีไฟล์ใน `.partial/`
- `POST /songs/check` `{name, size}` → `{size}`; `size` > 200 MB (หรือ `.mid` > 5 MB) → `413` `file_too_large`; ชื่อ+ขนาดซ้ำ → `200` `{song_id}`; ดิสก์ไม่พอ → `507`
- `PUT /songs?name=&size=` mp3 สั้น (fixture สร้างด้วย ffmpeg) → `201` Song มี `audio.m4a` `source.kind` = `file`; wav 2 วินาที → `422` `too_short`; ไฟล์ข้อความ → `415` `unsupported_file` "ไฟล์นี้ไม่มีเสียงที่อ่านได้"; `size` ไม่ตรง body → `400` `size_mismatch`; ไม่ได้ byte 60 วินาที → `stalled`
- หน้าเว็บเลือกไฟล์ (หรือวางไฟล์ลงกล่อง) → `check` แล้ว `sendFile` `PUT` แถบ % แล้ว "กำลังแปลงเสียง…" → ไป `#/songs/{id}` (e2e)
- หน้าเว็บปิดระหว่างแปลง → ffmpeg หยุด ไม่มี folder เพลง

### MIDI

- `PUT /songs` ไฟล์ `.mid` format 1 ช่อง 10 โน้ต 36, 38, 42 tempo 100 velocity 110 → `201` `source.kind` = `midi` ไม่มี `audio.m4a` `range` null; `analysis` มี `beats` ทุกจังหวะ `downbeats` ทุก 2.4 วินาที `hits` ชิ้น `kick`, `snare`, `hihat_closed` level `accent`; `duration_s` = โน้ตสุดท้าย + 1 ห้อง
- `.mid` 3/4, ไม่มีโน้ตช่อง 10, tempo 1,000 BPM, division 10, หรือการตี 20,001 ตัว → `415` `unsupported_file` "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง"; เวลาจบ > 600 → `422` `too_long`; SMPTE → `415`
- GM map ครบ 10 ชิ้น (35/36 kick, 38/40 snare, 42 hihat_closed, 44 hihat_pedal, 46 hihat_open, 49/55/57 crash, 51/53/59 ride, 48/50 tom_high, 45/47 tom_mid, 41/43 tom_floor); โน้ตอื่นทิ้ง
- หน้าเพลงของ MIDI → หัว ชนิด "MIDI" ไม่มี player ช่วงแกะ และปุ่มแกะ; แสดง "BPM ที่พบ 100" และแถบห้องที่พบ (เลขห้อง เวลาเริ่ม จำนวนการตี) (e2e)

### Song และรายการ

- `GET /songs` เรียง `updated_at` ใหม่สุดก่อน ส่ง `analysis` ย่อ (`mode`, `bars`) ไม่ส่ง `hits`; `song.json` อ่านไม่ได้ → ข้ามและ log
- `GET /songs/{id}` → Song เต็ม; id `..`, `%2E%2E`, ยาวเกิน 64 → `404` และไม่มีไฟล์ใดหาย
- `GET /songs/{id}/audio.m4a` → ไฟล์ ตอบ `Range` ด้วย `206`; หน้าเพลงมี `<audio controls>` เล่นได้ (e2e)
- `DELETE /songs/{id}` → `204` folder หาย; หน้าเว็บถามยืนยันพร้อมข้อความว่าบทเรียนไม่หาย (e2e); `in_use` → `409`
- start → `media/songs/.partial/` ว่าง และ folder เพลงที่ไม่มี `song.json` ถูกลบ
- `App` และ `useHash`: tab "แกะเพลง" ต่อท้าย "สอนกลอง"; `#/songs/{id}` เปิดหน้าเพลง hash อื่นใต้ `#/songs` เปิดรายการ
- วัดมือ: ไฟล์ mp3 5 นาที หลังรับครบ → `201` ภายใน 30 วินาทีบน Mac (D19); บันทึกใน Log
