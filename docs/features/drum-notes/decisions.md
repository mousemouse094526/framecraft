# Decisions: drum-notes

ทุกข้อที่มาจาก `interview` ในไฟล์นี้ตัดสินตอน auto mode เปิด: แอปเลือกตัวเลือก (Recommended) ให้และแจ้งเจ้าของทาง Telegram; Why คือเหตุผลที่เขียนไว้ในตัวเลือกนั้น. ข้อเท็จจริงเรื่องโมเดล (ADTOF, Beat This!, Basic Pitch เป็น ONNX) มาจากผลค้นหาที่เจ้าของส่งมาระหว่าง plan และตรวจที่มาซ้ำแล้ว (D6, D7).

## D1: รับเพลงเข้าสามทาง: เสียงกลองจากเพลง, ไฟล์ MIDI, และทำนองจากเสียง

**Chosen:** feature นี้ทำโน้ตกลองจาก (ก) เสียงเพลงจริงจากลิงก์หรือไฟล์ แกะส่วนกลองอัตโนมัติ, (ข) ไฟล์ MIDI ที่มีแทร็กกลอง, (ค) เสียงทำนอง (piano, kalimba, ร้อง) แปลงจังหวะทำนองเป็น pattern กลอง (D14). ทาง (ก) กับ (ข) มาก่อน ทาง (ค) เป็น ticket สุดท้าย.

**Why:** คำพูดเจ้าของคือ "เอาเพลงมาแกะ" ทาง (ก) จึงเป็นแกน; MIDI ถูกเพราะโน้ตแน่นอนอยู่แล้ว; ทาง (ค) เจ้าของเสนอมาพร้อมโมเดล Basic Pitch ที่ทดสอบแล้ว และคนทำคลิป kalimba/piano มีโน้ตแบบนี้อยู่.

**Rejected:**
- พิมพ์หรือวางโน้ตเป็นข้อความ (ASCII drum tab, โน้ตตัวเลข) — รูปแบบไม่มีมาตรฐาน parser ต่อรูปแบบ; ผู้ใช้กรอกบนตารางของ tab สอนกลองได้อยู่แล้ว
- MusicXML — ไฟล์กลองแบบนี้หายากสำหรับคนทำคลิป; MIDI ครอบกรณีเดียวกัน
- เสียงเพลงอย่างเดียว ไม่ทำ MIDI และทำนอง — MIDI เพิ่มงานน้อย (parser เดียว เข้าทางเดียวกับ Hit); ทำนองเป็นสิ่งที่เจ้าของขอ

**From:** interview · **Status:** changed by D20

## D2: feature ใหม่เป็น tab "แกะเพลง" ที่จบด้วยการสร้างบทเรียนกลอง

**Chosen:** tab ใหม่ "แกะเพลง" (`#/songs`) ต่อท้าย tab สอนกลอง: เอาเพลงเข้า แกะโน้ต เลือกช่วง แล้วสร้างบทเรียนกลองใน tab สอนกลอง (`#/drums/{id}`) ซึ่งแก้ ฟัง และ render ด้วยของเดิมทั้งหมด. slug `drum-notes`, backend package `drum_notes`, route prefix `/api/songs`.

**Why:** มีข้อมูลของตัวเอง (Song, การตีที่พบ) ที่อยู่ข้ามบทเรียน และหนึ่งเพลงทำได้หลายบทเรียน; โครงบทเรียนและ render ของ video-gen ไม่ต้องแก้.

**Rejected:**
- ปุ่ม "สร้างจากเพลง" ในรายการบทเรียนกลอง (change request ของ video-gen) — เพลงกับงานแกะต้องมีที่เก็บและหน้าของตัวเองอยู่ดี; รายการบทเรียนจะยาวขึ้นด้วยของที่ไม่ใช่บทเรียน
- บทเรียนกลองจำเพลงต้นทางและเล่นเพลงประกอบ — แก้ schema และ render ของ video-gen และขัด video-gen D7 (เสียงกลองล้วน)

**Details:**
- hash: `#/songs` รายการเพลง, `#/songs/{id}` หน้าเพลง (spec › Design)
- `App` และ `useHash` รู้จัก tab `songs` ต่อท้าย `drums`

**From:** interview · **Status:** active

## D3: Song เป็น folder ใน `media/songs/` id ตามกฎของ Temp clip

**Chosen:** เพลงหนึ่งเพลง (Song) อยู่ที่ `media/songs/{song_id}/`: `song.json` กับ `audio.wav` (ไม่มี `audio.wav` เมื่อมาจาก MIDI); อยู่จนผู้ใช้กดลบ. id ใช้กฎ spoil D51: ลิงก์ = เว็บ + id ของคลิป, ไฟล์ = `local-{sha1 ของชื่อ+ขนาด}`; เพลงซ้ำชี้แถวเดิมไม่โหลดใหม่.

**Why:** ทางเดียวกับ Temp clip และคลังเสียงพื้นของ toon ที่คนในโปรเจกต์รู้จัก; id จากต้นทางทำให้วางลิงก์เดิมซ้ำแล้วไม่ได้เพลงซ้ำ.

**Rejected:**
- ใช้ Temp clip ของ tab คลิปเป็นต้นทาง — Temp clip รับแค่ mp4 h264 (spoil D49) และผูกกับสปอย; เพลงต้องการแค่เสียง
- เก็บเสียงเป็น m4a แบบ toon — Pick job ต้องถอดเป็น PCM อยู่ดี และ wav เล่นได้ทุก browser โดยไม่ต้องถอดซ้ำ

**Details:**
- `audio.wav` คือเสียงทั้งเพลงที่ ffmpeg แปลงมา: 44.1 kHz stereo 16-bit (D4)
- MIDI: `song.json` เก็บการตีทั้งไฟล์ (D10) ไม่มีไฟล์เสียง id = `local-{sha1}` เช่นกัน
- ไฟล์ค้างระหว่างเอาเข้าอยู่ใน `media/songs/.partial/` ล้างตอน start (spoil D14)

**From:** interview · **Status:** changed by D20

## D4: เอาเพลงเข้าจากลิงก์หรือไฟล์ แปลงเป็น wav เดียว ยาวได้ 10 นาที

**Chosen:** ลิงก์โหลดด้วย yt-dlp `bestaudio` ผ่าน `spoil.adapter` แบบคลังเสียงพื้นของ toon (ADR-0029 ตรวจ host, ไม่ใช้ cookies); ไฟล์ในเครื่องรับทุกชนิดที่ ffmpeg อ่านเสียงได้ (mp3, m4a, wav, mp4, …) ≤ 200 MB ส่งแบบ ADR-0028 (`check` แล้ว `PUT` body ดิบ); ไฟล์ MIDI (`.mid`) ≤ 5 MB ส่งทางเดียวกัน. เสียงถูก ffmpeg แปลงเป็น `audio.wav` เสมอ; ยาวเกิน 10 นาที = `too_long`. Song import เป็นงานทีละงานใน slot ของตัวเอง.

**Why:** ทุกชิ้นมีอยู่แล้วใน `toon.sounds` และ `spoil.adapter`; wav เดียวทำให้ Pick job กับ player อ่านรูปแบบเดียว.

**Rejected:**
- รับเฉพาะ mp4 copy ตรงแบบ spoil D49 — เพลงมาเป็น mp3/m4a เป็นหลัก และต้องถอดเป็น PCM อยู่แล้ว เงื่อนไข "สำเนาตรงรูปแบบเดียว" (ADR-0027) ไม่ใช่ปัญหาที่นี่
- ไม่จำกัดความยาว — wav 10 นาทีคือ 100 MB; เพลงปกติสั้นกว่านั้น และบทเรียนต้องการแค่ท่อน

**Details:**
- ลิงก์: `fetch_info` ก่อน (ชื่อ ช่อง ความยาว; `duration` > 600 → `too_long` ก่อนโหลด) แล้วโหลดลง `.partial/` แล้ว ffmpeg แปลง
- ไฟล์: `POST /songs/check` `{name, size}` → ตรวจขนาด ชื่อ ดิสก์ แล้ว `PUT /songs?name=&size=` body ดิบ; ไฟล์ที่ ffmpeg อ่านเสียงไม่ได้ = `415` `unsupported_file`
- MIDI: นามสกุล `.mid` หรือ `.midi` → ทาง D10; ไฟล์อื่นเข้าทาง ffmpeg
- `title` = ชื่อคลิปจากเว็บ หรือชื่อไฟล์ตัดนามสกุล (ตัดที่ 60); `subtitle` = ช่องหรือศิลปินจากเว็บ ว่างได้
- ดิสก์: `disk.require_free` ด้วยขนาดไฟล์ + wav ประมาณ (ความยาว × 176 kB/วินาที) ก่อนโหลดและก่อนแปลง
- สถานะงานลิงก์: `checking` → `downloading` (มี %) → `converting` → `done`/`failed`/`cancelled`; ไฟล์เป็น request เดียวแบบ toon

**From:** interview · **Status:** changed by D20

## D5: เลือกช่วงแกะไม่เกิน 90 วินาทีก่อนแกะ ไม่แกะทั้งเพลง

**Chosen:** ผู้ใช้ตั้งจุดเริ่มและจุดจบของช่วงแกะบนเพลง (4–90 วินาที) แล้วกด "แกะโน้ต"; งานวิเคราะห์เฉพาะช่วงนั้น. แกะใหม่ด้วยช่วงอื่นได้ ทับผลเดิม.

**Why:** คลิปสอนใช้โน้ตแค่ 1–4 ห้องของท่อนเดียว; ช่วงสั้นทำให้งานจบในไม่กี่วินาทีและผลบนจออ่านง่าย.

**Rejected:**
- แกะทั้งเพลงแล้วให้เลือกห้องจากทั้งเพลง — Beat This! ทั้งเพลงหลายนาทีช้าบน CPU และแถบห้องยาวหลายร้อยห้องเลือกยาก
- ตัดท่อนอัตโนมัติ (หา intro, verse, chorus) — ต้องมีตัวแบ่งโครงเพลงอีกตัว; ผู้ใช้รู้อยู่แล้วว่าจะสอนท่อนไหน

**Details:**
- ค่าตั้งต้นของช่วง: 0 ถึง `min(30, duration)` วินาที
- MIDI ไม่มีช่วงแกะ: การตีทั้งไฟล์คือผลอยู่แล้ว (D10)

**From:** interview · **Status:** active

## D6: แกะด้วย ADTOF Frame_RNN (ONNX) หาจังหวะและห้องด้วย Beat This! (ONNX) ผลเป็นร่างให้แก้

**Chosen:** Pick job รันสองโมเดลบน onnxruntime CPU: ADTOF Frame_RNN ให้ activation 5 ชนิด (kick, snare, toms, hi-hat, cymbals) ที่ 100 เฟรม/วินาที แล้ว peak-pick ตาม threshold ของผู้เขียนโมเดล; Beat This! ให้จังหวะและจังหวะต้นห้อง (downbeat) ที่ 50 เฟรม/วินาที. ผลคือ "โน้ตหยาบ" ที่ผู้ใช้ตรวจแก้ในหน้าแก้บทเรียนกลอง; แอปไม่รับผิดชอบความแม่น.

**Why:** ADTOF เรียนจากเพลงเต็ม 359 ชั่วโมง จึงไม่ต้องแยก stem; ไฟล์ 2 MB รัน CPU ได้ (เจ้าของทดสอบบนคลิปอ้างอิง 19 วินาทีแล้ว); Beat This! ให้ต้นห้องซึ่งตารางเวลาของบทเรียนต้องการ. ทั้งคู่มี ONNX ที่เอกสาร input/output ครบและ pin บน Hugging Face ได้.

**Rejected:**
- demucs แยก stem กลอง + onset/จำแนกย่านความถี่ด้วย librosa — น้ำหนัก htdemucs ไม่มี license ชัด (ผู้เขียนบอก "research purpose", ถอด license ออกจาก model card แล้ว) และตัวจำแนกเองได้แค่ 3 ชนิดหยาบ
- madmom, ADTLib, ADTOF แบบ TensorFlow — madmom ไม่รองรับ numpy 2 และ Python 3.12 (project ใช้ numpy 2.5.4); TensorFlow ไม่มี wheel บน macOS รุ่นนี้
- onset curve สองย่านของ Drumduino `align.ts` — ออกแบบมาเทียบเสียงกับ score ที่มีอยู่แล้ว ไม่ได้แยกชนิดกลอง
- BPM จากช่วงห่างของ kick/snare แทน Beat This! — ไม่บอกต้นห้อง ผู้ใช้ต้องคลิกหาห้องเอง

**Details:**
- threshold ต่อชนิด 0.22, 0.24, 0.32, 0.22, 0.30 และ peak picking `pre_avg 0.1, post_avg 0.01, pre_max 0.02, post_max 0.01, combine 0.02` วินาที ตาม model card (ทำเองด้วย numpy ไม่ใช้ madmom)
- Beat This!: จังหวะคือ peak ของ logit `beat` ในหน้าต่าง 7 เฟรมที่ logit > 0, peak ห่าง 1 เฟรมรวมกัน; downbeat ย้ายไปจังหวะที่ใกล้สุด; เสียงถูก resample เป็น 22.05 kHz mono ด้วย ffmpeg ก่อนป้อน
- ช่วงแกะที่พบ downbeat น้อยกว่า 2 ตัว = `no_beats` (D18)
- ผลเก็บใน `song.json` › `analysis` (spec › Data) และแสดงบนหน้าเพลงเป็นห้องที่พบกับการตีต่อห้อง
- ความแม่นวัดจริงโดยเจ้าของบนคลิปอ้างอิง (spec › Expected Outcome); test อัตโนมัติพิสูจน์แค่ขั้นหลังโมเดล (D17)

**Sources:** [ADTOF Frame_RNN ONNX model card](https://huggingface.co/thebluescreen/adtof-drums-onnx), [Beat This! ONNX model card](https://huggingface.co/thebluescreen/beat-this-onnx), [demucs README › license of the weights](https://github.com/adefossez/demucs), [madmom issue #485](https://git.tdem.in/CPJKU/madmom/issues/485)

**From:** interview · **Status:** active

## D7: โมเดล ONNX สามตัวลงทะเบียนใน `backend.models` pin commit บน Hugging Face; onnxruntime pin ใน `pyproject.toml`

**Chosen:** เพิ่ม `ModelSpec` สามตัว (ADR-0004): `model_adtof` จาก `thebluescreen/adtof-drums-onnx` revision `d0e809bb1c1b6fe8a4a00c576852117a0636ab5a` ไฟล์ `adtof_frame_rnn.onnx` (2.2 MB, CC BY-NC-SA 4.0); `model_beat_this` จาก `thebluescreen/beat-this-onnx` revision `92842057ebb781a31fcf0d638f04a098fb887313` ไฟล์ `beat_this.onnx` (82 MB, MIT); `model_basic_pitch` จาก `Andremi/audioweb-models` revision `953d0a9e46fd364860c9413ee4c7a9aa4fbcae4b` ไฟล์ `analysis/basic_pitch_nmp.onnx` (230 kB, Apache-2.0). `onnxruntime==1.32.0` เป็น dependency ตรง มีแถว Status check `onnxruntime` แบบ `pythainlp`.

**Why:** ทั้งสามอยู่บน Hugging Face จึงใช้ `_snapshot_download`, marker และ `check_model` ของเดิมได้ทันที; sha256 ของไฟล์ตรงกับที่เจ้าของทดสอบ (`189ca3c2…`, `2c3c1d14…`).

**Rejected:**
- commit ไฟล์ ONNX เข้า repo — ADR-0004 ให้โมเดลทุกตัวอยู่ในรายการเดียวและโหลดผ่าน Setup script; ไฟล์ 82 MB ไม่ควรอยู่ใน git
- โหลดจาก GitHub ของผู้เขียนต้นฉบับแล้วแปลงเอง — ADTOF ต้นฉบับเป็น TensorFlow; Beat This! เป็น PyTorch checkpoint; การแปลงเป็นงานใหญ่และ TensorFlow ติดตั้งไม่ได้
- ใช้ `beat_this.onnx` 83 MB ที่เจ้าของทดสอบ (sha `66f85612…`) — หา repo ที่มี sha นี้ไม่พบ จึง pin ไม่ได้; ตัวที่เลือกเป็นการแปลง `final0` เดียวกันโดยผู้แปลง ADTOF มีเอกสาร input/output

**Details:**
- `platforms` ทั้ง darwin และ win32; Setup script โหลดหลัง drum kit
- แถว `model_adtof`, `model_beat_this`, `model_basic_pitch`, `onnxruntime` ต่อจาก `drum_kit` ใน Status check (ADR-0009)
- gate ของ Pick job โหมดกลอง: `model_adtof`, `model_beat_this`, `onnxruntime`, `ffmpeg`; โหมดทำนอง: `model_basic_pitch`, `model_beat_this`, `onnxruntime`, `ffmpeg`; Song import ลิงก์: `yt_dlp`, `deno`, `ffmpeg`; ไฟล์: `ffmpeg`
- `NOTICE.md` และหน้าสถานะแสดง license กับ attribution ของทั้งสาม (ADR-0017) รวมเครดิตผู้เขียน ADTOF ตาม `NOTICE.md` ของ model card
- `allow_patterns` ของ Basic Pitch คือไฟล์เดียว ไม่โหลดโมเดลอื่นใน repo นั้น (มี demucs ONNX 56 MB อยู่ด้วย)

**Sources:** [thebluescreen/adtof-drums-onnx](https://huggingface.co/thebluescreen/adtof-drums-onnx), [thebluescreen/beat-this-onnx](https://huggingface.co/thebluescreen/beat-this-onnx), [Andremi/audioweb-models](https://huggingface.co/Andremi/audioweb-models), [onnxruntime on PyPI](https://pypi.org/project/onnxruntime/)

**From:** interview · **Status:** active

## D8: Pick job รันเป็น thread ใน backend ไม่จองช่อง GPU

**Chosen:** Pick job เป็น `JobSlot` ธรรมดา (ADR-0010): โหลดโมเดล ONNX ด้วย onnxruntime บน CPU ใน thread ของ backend ทีละงาน ไม่จองช่อง GPU และไม่รันใน process ลูก. แคบความหมายของ ADR-0015 และ ADR-0012: "งานที่โหลดโมเดล" ที่ต้องจองช่องและรันใน process ลูก คืองานที่โหลดโมเดลขึ้นการ์ด (Metal หรือ CUDA) หรือกิน memory เป็น GB.

**Why:** โมเดลสามตัวรวม 85 MB บน CPU กิน memory หลักร้อย MB และไม่แตะ Metal/CUDA ที่เป็นเหตุผลของทั้งสอง ADR (crash ฆ่า process, memory 10 GB); รันพร้อม Qwen หรือ Whisper ได้.

**Rejected:**
- `ModelJobSlot` + process ลูก + ช่อง GPU — ผู้ใช้จะถูกปฏิเสธ "รอให้งานถอดบทพูดเสร็จก่อน" ทั้งที่งานนี้ไม่ใช้การ์ด; โค้ด worker เพิ่มโดยไม่ได้อะไร
- onnxruntime บน CoreML หรือ CUDA — ช่วงแกะ ≤ 90 วินาทีจบบน CPU ในไม่กี่วินาทีอยู่แล้ว; provider อื่นต้องการ package อื่น

**Details:**
- `InferenceSession` ด้วย `providers=["CPUExecutionProvider"]` เท่านั้น
- session สร้างใหม่ทุกงานแล้วทิ้ง (ไม่ cache ใน memory): โหลด 82 MB ใช้เวลาต่ำกว่า 1 วินาที
- Pick job ของ Song เดียวกันระหว่าง Song import ไม่เกิด: import เป็น request เดียวหรือจบก่อนมี Song

**From:** interview · **Status:** active

## D9: การตีที่พบแปลงเป็นชิ้นกลองของแอปแบบตายตัว ความแรงเป็น `normal` ทั้งหมด

**Chosen:** ชนิดของ ADTOF → ชิ้นกลอง (video-gen › Drum kit): kick → `kick`, snare → `snare`, toms → `tom_mid`, hi-hat → `hihat_closed`, cymbals → `crash`. ทุกการตีจากเสียงเป็น `normal`; จาก MIDI: velocity ≥ 100 = `accent`, ≤ 50 = `ghost`, อื่น `normal`. ไฮแฮทเปิด เท้าไฮแฮท ไรด์ ทอมสูง/ต่ำ และ flam ผู้ใช้เติมในหน้าแก้.

**Why:** ADTOF แยกได้ 5 ชนิดและ activation ไม่ใช่ความแรงเสียง จึงไม่เดาความแรง; MIDI มี velocity จริง.

**Rejected:**
- ใช้ค่า activation เป็นความแรง — activation คือความมั่นใจของโมเดล ไม่ใช่ velocity; จะได้ accent ผิดที่
- แยกไรด์จากฉาบด้วยความถี่ — ADTOF รวมไรด์กับฉาบเป็นชนิดเดียวแล้ว การแยกเพิ่มไม่มีข้อมูล

**From:** interview · **Status:** active

## D10: MIDI: แทร็กกลอง GM ช่อง 10 เป็นการตี เวลาจาก tempo ของไฟล์ ต้องเป็น 4/4

**Chosen:** parser MIDI ของแอปเอง (Standard MIDI File format 0 และ 1, ไม่รับ SMPTE): โน้ตช่อง 10 (หรือทุกช่องถ้าไม่มีช่อง 10) แปลงด้วย GM percussion map เป็นชิ้นกลอง 10 ชิ้นของแอป; tempo ตัวแรกของไฟล์เป็น BPM; เวลาจังหวะและต้นห้องคำนวณจาก tempo กับ time signature; ไม่ใช่ 4/4 หรือไม่มีโน้ตกลอง = `unsupported_file`. ผลคือ `analysis` แบบเดียวกับ Pick job (D6) ทั้งไฟล์.

**Why:** ทางเดียวกับ Drumduino `importers.ts` ที่ใช้งานจริงแล้ว; ได้ `analysis` รูปเดียวกันทำให้ขั้นเลือกช่วงบทเรียน (D11) ใช้ร่วมกัน.

**Rejected:**
- library `mido` — parser ที่ต้องการมีราว 100 บรรทัด และ Drumduino มีต้นแบบแล้ว; ไม่เพิ่ม dependency
- รองรับ 3/4, 6/8 — video-gen D5 รับแค่ 4/4

**Details:**
- GM map: 35, 36 → `kick`; 38, 40 → `snare`; 42 → `hihat_closed`; 44 → `hihat_pedal`; 46 → `hihat_open`; 49, 55, 57 → `crash`; 51, 53, 59 → `ride`; 48, 50 → `tom_high`; 45, 47 → `tom_mid`; 41, 43 → `tom_floor`; โน้ตอื่นทิ้ง
- `title` จากชื่อแทร็กแรกที่มี ไม่มีก็ชื่อไฟล์
- tempo เปลี่ยนกลางไฟล์ไม่รองรับ: ใช้ตัวแรก (เพลงกลองสำหรับคลิปสั้นมีตัวเดียว)

**From:** interview · **Status:** changed by D20

## D11: เลือกช่วงบทเรียนเป็นห้องที่พบ 1–4 ห้องติดกัน แล้วปัดการตีลงตาราง 16 ช่อง

**Chosen:** หน้าเพลงแสดงห้องที่พบ (จาก downbeat หรือ time signature) เรียงตามเวลา; ผู้ใช้เลือกห้องแรกและจำนวนห้อง 1–4 (ไม่เกินห้องที่พบ). BPM ของบทเรียน = 60 / ค่ามัธยฐานของช่วงห่างระหว่างจังหวะในช่วงที่เลือก ปัดเป็นจำนวนเต็ม (40–240) แก้ได้ก่อนสร้าง. การตีแต่ละตัวปัดไปช่องที่ใกล้สุด (ช่อง = จังหวะ / 4 ของห้องนั้น); ชิ้นเดียวกันซ้ำช่องเดียวกันเหลือตัวเดียว (ความแรงสูงสุด).

**Why:** Groove ของบทเรียนกลองคือ 1–4 ห้อง 16 ช่อง (video-gen D4, D5) ทางนี้ไม่แก้ schema; ห้องจาก downbeat ทำให้ตารางเริ่มที่ต้นห้องจริง.

**Rejected:**
- ให้คลิกจุดเริ่มเองบน waveform — มี downbeat แล้ว; การคลิกเองคลาดง่ายกว่า
- quantize ละเอียด 32 ช่องหรือสามพยางค์ — video-gen D5 ไม่รับ

**Details:**
- ช่องของการตี = `round((t − ต้นห้อง) / (ความยาวห้อง / 16))` ใช้ต้นห้องและความยาวห้องของห้องนั้นจริง (ไม่ใช่ BPM เฉลี่ย) ก่อนรวมเป็นตารางเดียว
- การตีที่ปัดได้ช่อง 16 ของห้องสุดท้าย (ต้นห้องถัดไป) ทิ้ง
- ก่อนสร้าง หน้าเพลงแสดงตารางผลแบบอ่านอย่างเดียว (ชิ้น × ช่อง) และจำนวนการตีที่ถูกทิ้งเพราะกฎ D13

**From:** interview · **Status:** changed by D20

## D12: บทเรียนที่สร้างใช้ค่าตั้งต้นของ video-gen ยกเว้นหัวเรื่อง บรรทัดรอง BPM และ Groove

**Chosen:** `POST /songs/{id}/lessons` สร้างบทเรียนกลองผ่าน module `video_gen.lessons` (ไม่ผ่าน HTTP): `title` = ชื่อเพลงตัดที่ 40, `subtitle` = บรรทัดรองของเพลง (ศิลปิน/ช่อง) ตัดที่ 60, `bpm` จาก D11, `groove` จาก D11 และ D13, ที่เหลือ (ท่อนสอนสองท่อน, `caption` ว่าง, พื้นหลัง `color`) ตามบทเรียนใหม่ของ video-gen (D22, D23). Song จำ id ของบทเรียนที่สร้างใน `song.json` › `lessons`; `lesson.json` ไม่เปลี่ยน.

**Why:** ผู้ใช้แก้ทุกอย่างในหน้าแก้บทเรียนที่มีอยู่แล้ว; schema ของ video-gen ไม่แตะ จึงไม่มี Blocked ข้าม feature.

**Rejected:**
- ท่อนสอนอัตโนมัติจากโครงเพลง (KICK, FLAMS, …) — ท่อนสอนเน้นทีละชิ้นเป็นดุลยพินิจผู้สอน; ค่าตั้งต้นสองท่อนของ video-gen ก็ render ได้ทันที
- บทเรียนจำ `song_id` — แก้ schema ของ video-gen และต้องดูแลตอนลบเพลง

**Details:**
- บทเรียนที่ถูกลบใน tab สอนกลองหลุดจาก `lessons` ของเพลงตอนอ่าน (ไม่ error)
- หน้าเพลงแสดงบทเรียนที่สร้างจากเพลงนี้เป็นลิงก์ `#/drums/{id}`
- สร้างแล้วพาไป `#/drums/{id}` ทันที

**From:** interview · **Status:** extended by D21

## D13: มือ L/R เลือกอัตโนมัติตามกติกาของ Drumduino และตัดโน้ตที่ขัดกฎ D20

**Chosen:** หลัง quantize แอปเลือกมือให้ทุกโน้ตมือ: สองชิ้นในช่องเดียว → R ให้ชิ้นที่อยู่ขวาของมือกลอง (`ride` > `hihat_closed`/`hihat_open` > `crash` > `tom_floor` > `tom_mid` > `tom_high` > `snare`), อีกชิ้น L; ชิ้นเดียว: ตีห่างจากโน้ตมือก่อนหน้าไม่เกินครึ่งจังหวะ (8th) สลับมือ; หลังช่วงพัก: ฉาบ R, `snare` และ `tom_high` เป็น L เมื่อมือ R ตีฉาบภายในครึ่งจังหวะก่อนหน้า ไม่งั้น R; ชิ้นอื่น R. ช่องที่มีโน้ตมือเกินสองตัวตัดให้เหลือสองตามลำดับ `snare` > `crash` > `hihat_closed` > `hihat_open` > `ride` > ทอม; `hihat_open` คู่ `hihat_closed` เหลือ `hihat_closed`.

**Why:** `PUT` ของ video-gen ปฏิเสธโน้ตที่มือเดียวตีไม่ได้ (D20) จึงต้องตัดก่อน; กติกาของ Drumduino `sticking.ts` เป็นวิธีที่มือกลองจริงใช้ และผู้ใช้แก้มือทีละโน้ตได้ในหน้าแก้.

**Rejected:**
- มือ R ทั้งหมด — จังหวะ 16th บนไฮแฮทจะเป็น R ติดกัน ซึ่งผิดจริงและ D20 ยังผ่าน แต่ภาพไม้ตีผิด
- ส่งโน้ตที่ขัดกฎไปให้ `PUT` ปฏิเสธ — ผู้ใช้ไม่มีทางแก้ก่อนสร้าง

**Details:**
- ตารางลำดับความสำคัญและกติกามืออยู่ใน `drum_notes.score` ที่เดียว (D17)
- จำนวนโน้ตที่ถูกตัดแสดงบนหน้าเพลงก่อนสร้าง (D11)

**From:** interview · **Status:** changed by D20

## D14: โหมดทำนอง: จังหวะของโน้ตทำนองเป็น snare บน groove พื้นฐาน

**Chosen:** เมื่อผู้ใช้เลือกโหมด "ทำนอง" Pick job รัน Basic Pitch (ONNX) บนช่วงแกะ: onset ของโน้ตทำนองทุกตัว → การตี `snare`; Beat This! ให้จังหวะและห้องเหมือนโหมดกลอง; ตอนสร้างบทเรียนแอปเติม `kick` ที่จังหวะ 1 และ 3 กับ `hihat_closed` ทุก 8th ของทุกห้อง. โน้ตทำนองที่ onset ห่างกันต่ำกว่า 1 ช่องถูกปัดรวมอยู่แล้วตาม D11.

**Why:** เจ้าของขอให้ใช้ Basic Pitch กับทำนอง kalimba/piano; "ตีจังหวะทำนองบน snare" เป็นแบบฝึกที่มือกลองใช้จริง และยังเป็นบทเรียนที่ตารางของ video-gen รับได้.

**Rejected:**
- แปลงระดับเสียง (pitch) เป็นชิ้นกลองต่างกัน — ไม่มีความหมายทางดนตรี; ผลสุ่ม
- ไม่ทำโหมดทำนอง — เจ้าของขอ และต้นทุนคือโมเดล 230 kB กับ mapping เดียว

**Details:**
- Basic Pitch: input หน้าต่าง 43,844 sample ที่ 22.05 kHz mono, output `note`/`onset` 172 เฟรม × 88 โน้ต ต่อหน้าต่าง; onset = เฟรมที่ `onset` ≥ 0.5 (threshold ตั้งต้นของ Basic Pitch); หน้าต่างซ้อน 30 เฟรมตามตัวต้นฉบับ
- รวม onset ทุกโน้ตที่อยู่ในเฟรมเดียวกันเป็นการตีเดียว
- `kick` และ `hihat_closed` ที่เติมเป็น `normal`; ช่องที่มี snare แล้วไฮแฮทยังอยู่ (สองมือ) ตามกฎ D13
- gate: `model_basic_pitch` แทน `model_adtof` (D7)

**Sources:** [spotify/basic-pitch README](https://github.com/spotify/basic-pitch), [basic_pitch/constants.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/constants.py)

**From:** interview · **Status:** active

## D15: เสียงเพลงต้นฉบับใช้วิเคราะห์เท่านั้น ไม่เข้าคลิปที่ render

**Chosen:** `audio.wav` ของ Song ใช้ให้ Pick job อ่านและให้ผู้ใช้ฟังในหน้าเพลง; คลิปสอนกลองที่ render จากบทเรียนที่สร้างมีเสียงกลองจาก sample เท่านั้น (video-gen D7) ไม่มีเสียงเพลง ไม่มี backing track.

**Why:** คลิปที่เผยแพร่ไม่มีเสียงบันทึกของเพลง จึงอยู่ในกรอบเดียวกับ video-gen legal ข้อ 2; เสียงเพลงอยู่ในเครื่องผู้ใช้.

**Rejected:**
- เล่นเพลงจริงเบาๆ ใต้เสียงกลอง — เป็นการทำซ้ำสิ่งบันทึกเสียง ต้องขออนุญาตค่ายเพลง และขัด ADR-0038 (เสียงจากโน้ตชุดเดียว)

**From:** interview · **Status:** active

## D16: รับความเสี่ยงด้าน legal สามข้อ: โมเดล NC ใช้แบบไม่หารายได้, โหลดเพลงจากเว็บ, เผยแพร่คลิปที่แกะจากเพลง

**Chosen:** ใช้ ADTOF (CC BY-NC-SA 4.0) เป็นเครื่องมือวิเคราะห์ในเครื่องภายใต้ ADR-0017 (ไม่หารายได้) ให้เครดิตใน `NOTICE.md` และหน้าสถานะ ไม่แจกจ่ายไฟล์โมเดล; การโหลดเสียงจากลิงก์และไฟล์ของผู้ใช้รับความเสี่ยงแบบ spoil D13 และ D53; การเผยแพร่คลิปสอนที่โน้ตมาจากเพลงมีลิขสิทธิ์รับความเสี่ยงแบบ video-gen D25. จะหารายได้ต้องเปลี่ยนตัวแกะกลองก่อน (legal ข้อ 3).

**Why:** โปรเจกต์เป็นแบบไม่หารายได้อยู่แล้วเพราะ OmniVoice; ทางเลือกโมเดลกลองที่ license เปิดกว่ายังไม่มี.

**Rejected:**
- หาโมเดลกลอง license เชิงพาณิชย์ก่อนเริ่ม — ไม่พบตัวที่ติดตั้งบน Python 3.12 ได้; เลื่อนไปตอนจะหารายได้

**Accepted risk:** โน้ตที่ได้จากโมเดล NC ถูกใช้ต่อในคลิปที่ผู้ใช้เผยแพร่ (ไม่หารายได้) — ข้อนี้ UNVERIFIED ใน legal ข้อ 3 ว่าผลลัพธ์ของโมเดลถือเป็น "adaptation" หรือไม่; ยอมรับเพราะใช้ส่วนตัวและเปลี่ยนโมเดลได้ก่อนหารายได้.

**From:** legal · **Status:** active

## D17: seam สามจุด: API ด้วย ffmpeg จริงและโมเดลปลอม, ชั้นหลังโมเดลด้วยข้อมูลสังเคราะห์, หน้าเว็บผ่าน `App`

**Chosen:** (1) API `/api/songs/*` ผ่าน `TestClient` กับ ffmpeg จริง, `YtDlpAdapter` ปลอม และตัวรันโมเดลปลอมที่คืน activation/logit ที่ test กำหนด; (2) `drum_notes.score` (peak picking, จังหวะและห้อง, quantize, มือ, กฎ D20, mapping โหมดทำนอง) ด้วย activation สังเคราะห์และตารางเวลาของบทเรียน video-gen (round trip); (3) หน้าเว็บ tab แกะเพลง (e2e) ผ่าน `App` กับ fetch ปลอม. onnxruntime กับโมเดลจริงไม่รันใน CI.

**Why:** โมเดลโหลดจากเน็ตและไม่ deterministic ข้ามเครื่อง จึงถูกแทนด้วย fake ที่ขอบเดียว (`drum_notes.onnx_runner`); ทุกอย่างหลังจากนั้นเป็นเลขล้วนทดสอบได้แน่นอน.

**Rejected:**
- test ด้วยโมเดลจริงเมื่อมีไฟล์ในเครื่อง (skip-if-missing) — ผล CI ต่างกันตามเครื่อง; ความแม่นเป็นเรื่องที่เจ้าของตัดสิน

**Details:**
- round trip: `video_gen.timeline.build(lesson)` → การตี (เวลา, ชิ้น) → `score.quantize` ที่ BPM เดิม → Groove เท่ากับของบทเรียนทุกโน้ตที่อยู่ในชิ้นที่ ADTOF แยกได้ (kick, snare, tom_mid, hihat_closed, crash)
- ตัวรันโมเดลปลอมรับเสียงแล้วคืน array รูปเดียวกับโมเดลจริง (`[1, frames, 5]`, `beat`/`downbeat` `[1, T]`, `note`/`onset` `[1, 172, 88]`)

**From:** interview · **Status:** active

## D18: ทางเลือกเล็กของ API และงาน

**Chosen:** ข้อตกลงย่อยที่ builder จะต้องถาม ตัดสินตอน plan.

**Details:**
- **สถานะ Pick job:** `preparing` (ตัด wav ช่วงแกะและ resample ด้วย ffmpeg) → `picking` (รันโมเดล; `percent` จากหน้าต่างที่ป้อนแล้ว) → `done`/`failed`/`cancelled`; ยกเลิกเช็คระหว่างหน้าต่าง (ADTOF ป้อนทีละ 30 วินาที, Beat This! ทีละ 1,500 เฟรม) — ให้ปุ่มยกเลิกมีผลภายใน 2 วินาที
- **error ของ Pick job:** `no_beats` (downbeat < 2 ในช่วง), `model_failed` (onnxruntime โยน error; `message` บรรทัดแรก), `internal`
- **busy:** Pick job ทีละงานทั้ง tab → `409` `busy` พร้อม `song_id` ของงานที่รัน; ลบเพลงระหว่าง Pick job ของเพลงนั้น → `409` `song_busy`; ลบ `audio.wav` ที่ player เปิดอยู่บน Windows → `409` `in_use` (spoil D15)
- **ลบเพลง:** ไม่ลบบทเรียนที่สร้างจากเพลง (บทเรียนเป็นของ tab สอนกลอง)
- **poll:** หน้าเว็บ poll `GET /songs/import` และ `GET /songs/pick` ทุก 1 วินาทีระหว่างงานรัน (spoil D6)
- **restart:** งานใน memory หาย; start ล้าง `media/songs/.partial/`; `analysis` ที่เขียนเสร็จแล้วอยู่ต่อ (เขียนด้วย `write_atomic` หลัง `done`)
- **ช่วงแกะไม่ถูก:** `end − start` < 4 หรือ > 90 หรือ `end` > `duration` → `400` `invalid_request` มี `field`
- **เพลงจาก MIDI:** `POST /songs/{id}/pick` → `409` `not_applicable`; หน้าเพลงไม่มีปุ่มแกะ
- **`in_use` และ `song_busy` ของ import:** เอาเพลงเข้าระหว่าง Song import อื่นรัน → `409` `busy`; Song import กับ Pick job รันพร้อมกันได้ (คนละ slot)
- **ขนาด `song.json`:** การตี 90 วินาทีราวหลักร้อยถึงพันตัว อยู่ใน json ได้

**From:** interview · **Status:** changed by D20

## D19: เป้าที่วัดได้

**Chosen:**
- Pick job โหมดกลองของช่วง 90 วินาทีจบใน ≤ 60 วินาทีบน Mac Apple Silicon (CPU) — วัดมือตอน build
- Song import จากไฟล์ mp3 5 นาที (หลังรับไฟล์ครบ) จบใน ≤ 30 วินาที
- round trip ของ D17 ได้โน้ตตรง 100 % เมื่อ activation สังเคราะห์วางที่เวลาของการตีพอดี และยังตรงเมื่อเลื่อนสุ่ม ±20 ms ทุกตัว (ครึ่งช่องที่ BPM 240 คือ 31 ms)
- ความแม่นบนเพลงจริง: เจ้าของแกะ intro fill ของ Smells Like Teen Spirit จากคลิปอ้างอิง แล้วตัดสินว่าร่างใช้แก้ต่อได้ (ไม่มีตัวเลข; D6)

**Why:** ตัวเลขที่ build วัดได้ และข้อที่วัดไม่ได้ (ความแม่นของโมเดล) ยกให้เจ้าของ.

**From:** interview · **Status:** active

## D20: ข้อแก้จาก red team

**Chosen:** ข้อที่ reviewer ห้าคนพบและมีทางแก้ชัด แก้ในเอกสารรอบเดียว; ข้อที่เปลี่ยน D เดิมระบุไว้ที่ Status ของข้อนั้น.

**Details:**
- **กฎห้องของการตี (Tester BLOCKER, แก้ D11):** การตีอยู่ในห้อง `i` เมื่ออยู่ในหน้าต่าง `[downbeat_i − ช่อง_i/2, downbeat_{i+1} − ช่อง_i/2)` โดย `ช่อง_i` = ความยาวห้อง `i` / 16; ช่อง = `round((t − downbeat_i) / ช่อง_i) + 16 × i`; เก็บเฉพาะ `0 ≤ ช่อง < 16 × bars` — โน้ตที่ช่อง 0 ของห้องแรกที่เลื่อนมาก่อน downbeat ครึ่งช่องยังอยู่ในห้องแรก; test round trip เลื่อนแบบตายตัวสลับ +20/−20 ms ไม่ใช้ค่าสุ่ม
- **BPM จากความยาวห้อง (Breaker, แก้ D11):** BPM ตั้งต้น = `round(240 / median(ความยาวห้องที่เลือก))` จำกัด 40–240; ห้องที่พบที่มีจังหวะไม่เท่ากับ 4 ตัวเลือกไม่ได้ (`400` `invalid_request` field `bar` "ห้องนี้ไม่ใช่ 4/4") และหน้าเพลงแสดงห้องนั้นจาง — ตารางกับ BPM จึงมาจากค่าเดียวกัน ไม่ต้องมีกรณีจังหวะน้อยกว่าสองตัว
- **กฎมือ (Advocate, Builder, แก้ D13):** สลับมือเฉพาะเมื่อห่างจากโน้ตมือก่อนหน้า**น้อยกว่า** 2 ช่อง (16th จริง); ห่าง 2 ช่องขึ้นไป (8th และช้ากว่า) ฉาบเป็น R และ `snare`/`tom_high` เป็น L เมื่อโน้ตมือก่อนหน้าภายใน 2 ช่องเป็นฉาบมือ R; "โน้ตมือก่อนหน้า" เมื่อช่องก่อนมีสองมือคือตัว R — groove ร็อก (ไฮแฮท 8th, snare ช่อง 4 และ 12) จึงได้ไฮแฮท R ทุกตัวและ snare L ไม่ต้องแก้มือ
- **เสียงเก็บเป็น m4a ร่วมทางกับคลังเสียงพื้นของ toon (Skeptic, แก้ D3, D4):** `audio.m4a` aac แบบ `toon.compose` (ไม่ใช่ wav); ส่วนที่ซ้ำกับ `toon.sounds` (งานลิงก์ `bestaudio`, รับไฟล์ดิบพร้อมเช็คหน้าเว็บหาย, ffmpeg แปลง, ล้าง `.partial/`) ย้ายเป็น module ใช้ร่วม `backend.audio_imports` ใน ticket แรก (prefactor) และ `toon.sounds` เรียกใช้ — กติกา "Where shared code goes" เมื่อมีผู้ใช้ที่สอง; ดิสก์ประมาณ 16 kB ต่อวินาที
- **ตรวจความยาวจากไฟล์จริง (Breaker, แก้ D4):** หลังโหลดหรือรับไฟล์ครบ ffmpeg อ่านความยาวของไฟล์ก่อนแปลง: > 600 วินาที = `too_long`, < 4 วินาที = `too_short` (Tester); คำสั่งแปลงมี `-t 600` เสมอ; `duration` จาก yt-dlp ใช้ปฏิเสธก่อนโหลดเมื่อมีค่าเท่านั้น
- **ลิงก์ซ้ำที่รู้ id หลัง `fetch_info` (Breaker, Builder, แก้ D3, D18):** id ของเว็บอื่นมาจาก `links.clip_id` หลัง `fetch_info`; มี `song.json` อยู่แล้ว → งานจบ `done` ด้วย `song_id` เดิม `percent` 100 ไม่โหลด ไม่เขียนทับ; `POST /songs/check` ตอบ `200` `{song_id}` เมื่อชื่อ+ขนาดซ้ำก่อนส่ง body; start ลบ folder เพลงที่ไม่มี `song.json`
- **MIDI ต้องมีช่อง 10 (Advocate, แก้ D10):** ไม่มีโน้ตช่อง 10 = `unsupported_file` "ไฟล์นี้ไม่มีแทร็กกลอง" (ไม่ map ทุกช่อง); ไฟล์เกิน 600 วินาที = `too_long`; tempo ต้องอยู่ 20–400 BPM และ division 24–960 ไม่งั้น `unsupported_file`; การตีเกิน 20,000 ตัว = `unsupported_file` (Breaker)
- **โน้ตที่ตัดเป็นรายการ (Advocate, แก้ D11):** `POST /preview` คืน `dropped` เป็นรายการ `{piece, step}`; หน้าเพลงแสดงใต้ตาราง; `POST /lessons` คืนจำนวน
- **ยกเลิกมีผลเมื่อจบ chunk (Tester, แก้ D18):** ADTOF ป้อนช่วงทั้งก้อนครั้งเดียว (RNN ไม่ตัดหน้าต่าง); Beat This! ทีละ chunk 1,500 เฟรม; ยกเลิกเช็คระหว่าง chunk และก่อนเริ่มแต่ละโมเดล — ไม่สัญญา 2 วินาที; `percent` = โมเดลและ chunk ที่เสร็จ
- **ต่อ chunk ของ Beat This! ใน `score` (Builder):** `onnx_runner` คืน logit ต่อ chunk; `score.stitch` ทำตาม model card: `pad_frames` 6 ที่ต้นและท้ายของทั้งช่วง 0 ที่อื่น, ตัด 6 เฟรมแต่ละด้านของ chunk, chunk สุดท้ายเลื่อนให้จบที่ท้ายช่วง, ต่อเป็น array เดียว — test ด้วย logit สังเคราะห์
- **ไฟล์โมเดลเสีย (Breaker):** สร้าง `InferenceSession` ไม่ได้ → Pick job `failed` `model_broken` มี `rows` และ `fix` คำสั่ง Setup script (แยกจาก `model_failed` ของขั้น `run`); Setup script สร้าง session ของแต่ละไฟล์หนึ่งครั้งหลังโหลด ล้ม = Setup จบด้วย error ชื่อไฟล์
- **ffmpeg จับ stdout (Builder):** `backend.ffmpeg.run_capture(command, cancel) -> bytes` ใหม่: kill เมื่อยกเลิก, `FfmpegFailed` พร้อมบรรทัดท้ายของ stderr; `drum_notes.pick` ใช้ถอดช่วงเป็น PCM
- **fake ตามกติกา testing (Tester):** `FakeOnnxRunner` มี `pause_at(step)`, `wait_until()`, `release()` และนับการเรียก; `PickJobs(run_model=…, run_ffmpeg=…)` รับตัวรันทาง constructor; ModelSpec สามตัวอยู่ใน `MODELS` ให้ `fake_root` เขียน snapshot กับ marker เอง (ไม่มี `write_onnx_models`); test `not_ready` ลบ marker
- **เกณฑ์ตัดสินบนเพลงเต็ม (Skeptic, แก้ D19):** เพิ่มกรณีที่สอง: ลิงก์ YouTube ของเพลงจริง (mix เต็ม) ท่อน intro เดียวกัน; "ใช้แก้ต่อได้" อย่างน้อยคือ kick กับ snare สองห้องแรกถูกตำแหน่ง
- **spike Beat This! ก่อนสร้างของจริง (Skeptic):** ticket แรกเริ่มด้วยรันไฟล์ที่ pin บน `reel.mp4` และเพลงเต็มหนึ่งเพลง ดูว่า downbeat ตรงเส้นห้อง; ล้ม → Blocked row และแผนสอง: BPM จากช่วงห่าง kick/snare (แบบ `adtof_test.py`) กับให้ผู้ใช้กดห้องแรกบนการตี
- **หน้าเพลงก่อนแกะ (Advocate):** `analysis` ว่าง → ซ่อนส่วนผลและสร้างบทเรียน แสดง "ตั้งช่วงแล้วกด แกะโน้ต"; กดห้องบนแถบ → player เลื่อนไปต้นห้องนั้น
- **คำใน D1:** โมเดล Basic Pitch คือ "โมเดลที่เจ้าของหามา" ไม่ใช่ "ทดสอบแล้ว" (เจ้าของทดสอบเฉพาะ ADTOF บนคลิปอ้างอิง)
- **ลิงก์เอกสาร:** overlap 30 เฟรมของ Basic Pitch อยู่ใน `inference.py` ไม่ใช่ `constants.py`

**From:** red team · **Status:** active — changed by D24 (ชื่อ `run_model` → `open_session`)

## D21: ฟังโน้ตที่เลือกก่อนสร้างบทเรียน

**Chosen:** หน้าเพลงมีปุ่ม "ฟัง" ข้างตารางตัวอย่าง: `POST /songs/{id}/listen` `{bar, bars, bpm}` ผสมเสียง Groove ของตัวอย่างด้วย `video_gen.timeline` และ `video_gen.mixer` จากบทเรียนชั่วคราวในหน่วยความจำ (ค่าตั้งต้นของ video-gen, ไม่เขียนไฟล์) คืน wav แบบ `/listen` ของ video-gen.

**Why:** ผู้ใช้ตัดสินว่าเลือกห้องถูกและ quantize ถูกไหมด้วยหู; ไม่งั้นต้องสร้างบทเรียนแล้วลบใน tab อื่นทุกครั้ง (Advocate).

**Rejected:**
- ให้ไปฟังในหน้าแก้บทเรียนอย่างเดียว — สร้างแล้วลบวนไปมา
- เล่นเพลงจริงพร้อมโน้ตที่แกะ — ต้องซิงก์เสียงสองทาง และเสียงเพลงไม่เข้าทาง render อยู่แล้ว (D15)

**Details:**
- gate เดียวกับ `/listen` ของ video-gen (`drum_kit`) → `503` `not_ready`
- error เหมือน `/preview` (`invalid_request`, `no_analysis`)
- หน้าเว็บเล่นด้วย `playAudio` จาก blob แบบ "ฟังจังหวะ"

**From:** red team · **Status:** active

## D22: ไฟล์ MIDI ที่ไม่รับทุกกรณีตอบข้อความเดียว; ความแรงจาก velocity สามระดับ

**Chosen:** `unsupported_file` ของไฟล์ MIDI ใช้ข้อความเดียว "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง" ทุกเหตุ (ไม่ใช่ 4/4, ไม่มีโน้ตช่อง 10, tempo หรือ division นอกช่วง, SMPTE, format 2, การตีเกิน 20,000, ไฟล์อ่านไม่ได้) ตาม ticket 01 และ spec › Design; ข้อความ "ไฟล์นี้ไม่มีแทร็กกลอง" ใน D20 ไม่ใช้. velocity → `level`: ≤ 50 `ghost`, ≥ 100 `accent`, อื่น `normal`. ความยาว = เวลาโน้ตสุดท้าย + 1 ห้อง (spec › Data ตามตัวอักษร) จังหวะและต้นห้องถึงเวลานั้นรวมตัวสุดท้าย ห้องที่มีโน้ตสุดท้ายจึงปิดเสมอ. ไฟล์ที่ไม่มี time signature หรือ tempo ใช้ค่าตั้งต้นของรูปแบบ (4/4, 120 BPM) ไม่ปฏิเสธ.

**Why:** ผู้ใช้แก้ไฟล์ไม่ได้อยู่ดี ข้อความเดียวบอกเงื่อนไขทั้งสองที่ไฟล์ส่วนใหญ่ขาด; D9 บอกว่า MIDI ใช้ velocity แต่ไม่ได้ตั้งเกณฑ์.

**From:** build ticket 01 · **Status:** active

## D23: ทางเลือกเล็กของ API และหน้าเว็บจาก ticket 01

**Chosen:**
- แถวใน `GET /songs` ส่ง `source_kind` (ไม่ใช่ `source` ทั้งก้อน) และ `analysis` เป็น `{mode, bars}` โดย `bars` = จำนวน downbeat − 1; `lessons` เป็นจำนวน
- `POST /songs/import/cancel` ตอนไม่มีงาน → `409` `not_running` ตาม spec › API (toon และ spoil ใช้ `404`)
- `PUT /songs` ของไฟล์ที่เป็นเพลงอยู่แล้ว (ชื่อ+ขนาดซ้ำ หลัง `check` ตอบ `200` ไปแล้ว) ตอบ Song เดิม ไม่เขียนทับ
- ลิงก์เว็บอื่นที่ซ้ำ: งานบอก `song_id` ตั้งแต่รู้ id (หลัง `fetch_info`) ไม่ใช่ตอน `done` เท่านั้น เพื่อให้ปลายทางล้างไฟล์ตาม id ได้
- `audio_imports` รับ `Limits(max_seconds, too_long, min_seconds, too_short)` และ `place(seconds)` จากผู้เรียก; คำสั่งแปลงของทั้ง toon และ songs มี `-t {max_seconds}` (toon 1,200 ไม่เปลี่ยนผล: ไฟล์ยาวกว่าถูกปฏิเสธก่อน)
- ข้อความ "เพลงนี้มีอยู่แล้ว" แสดงเป็น Alert บนหน้าเพลงที่พาไป (ไม่ค้างบนรายการ); กล่องไฟล์ของ tab เป็นปุ่มเดียวทั้งกล่องพร้อม input ซ่อน `aria-label="ไฟล์เพลง"` (แบบ spoil D58 แต่ไม่ใช้ `FileDropArea` ของ spoil ที่ผูกข้อความ mp4)
- `setupFixes.ts` ย้ายจาก video-gen ไป `src/lib/` เมื่อ drum-notes เป็นผู้ใช้ที่สอง; helper `edit`/`notice`/`upload` ของ toon ไม่ย้าย (hook ของ tab นี้ใช้ `sendJson`/`refusalOf` ตรงแบบ video-gen) — รวมสามทางเป็นหนึ่งเป็นงานข้าม feature ถ้าเจ้าของต้องการ

**Why:** ทางเลือกที่ spec ไม่ได้ตั้ง ตัดสินตามโค้ดเดิมที่ใกล้ที่สุด (video-gen) และ spec › API.

**From:** build ticket 01 · **Status:** active

## D24: ทางเลือกเล็กของ Pick job และหน้าเพลงจาก ticket 02

**Chosen:**
- `GET /songs/{id}`, `PUT /songs`, `PUT /range` ตอบ `SongView` = Song + `bars` (`n`, `start_s`, `end_s`, `beats`, `hits`, `four_four`) ที่ `songs.bars_of` (Score ขั้น 1 อยู่ข้างชนิดข้อมูลของมัน ไม่ใช่ใน `score` ที่ import `songs`) คำนวณตอนอ่าน ไม่เก็บลง `song.json`; เพลงจาก MIDI ได้ `bars` ทางเดียวกัน; หน้าเพลงวาดแถบจาก `bars` ของ server (ตัด `barsOf` ฝั่งหน้าเว็บ) เหลือ `bpmOf(bars)` ไว้แสดง "BPM ที่พบ" จน ticket 03 ให้ BPM มาจาก `POST /preview`
- ขอบของโมเดลคือ `PickJobs(open_session=…, run_ffmpeg=…)` (เปลี่ยนชื่อ `run_model` ของ D20 และ spec › Testing decisions): fake แทนที่ระดับ session (`FakeOnnxRunner(model_file)` → `FakeSession.run(names, feeds)` คืน array รูปเดียวกับโมเดลจริงจากความยาว input และ `pad_frames`) ไม่ใช่ `run_model`; แผน chunk, `pad_frames`, การตัดและต่ออยู่ใน `score` จึงถูกทดสอบด้วย fake นี้
- `GET /songs/pick` มี `cancel_requested` และ `started_at` เพิ่มจากรายการช่องใน spec › API ตามแบบงานทุก slot (`SongImport`, `DrumRenderJob`): ปุ่มยกเลิกปิดตัวเองจาก `cancel_requested`
- แผน chunk ของ Beat This!: เริ่มที่ −6 แล้วเลื่อนทีละ 1,488 ตราบที่เฟรมที่เก็บยังไม่ถึงท้ายช่วง; chunk สุดท้ายเลื่อนให้เริ่มที่ `F + 6 − 1500` (chunk ก่อนหน้าเก็บเฟรมที่ซ้ำกันไว้ก่อน) ช่วงสั้นกว่า 1,494 เฟรมเป็น chunk เดียว pad 6 ทั้งสองข้าง; เช็คยกเลิกอีกครั้งหลัง chunk สุดท้ายก่อนให้คะแนน จึงไม่เขียนอะไรเมื่อยกเลิกระหว่าง chunk สุดท้าย
- จังหวะ: peak ของ logit > 0 ที่เป็นค่าสูงสุดในหน้าต่าง ±3 เฟรม เฟรมติดกันที่สูงเท่ากันนับเป็นจังหวะเดียว (ตัวแรก); downbeat ย้ายไปจังหวะใกล้สุด ซ้ำแล้วทิ้ง; เวลาปัด 3 ตำแหน่ง
- `percent` = (โมเดลและ chunk ที่เสร็จ) / (1 + จำนวน chunk) × 100 ค้างที่ 99 จน `done`
- โหมดทำนอง: `PUT /range` รับ `melody` ได้ แต่ `POST /pick` ตอบ `400` `invalid_request` field `mode` "โหมดทำนองยังไม่เปิดใช้" จน ticket 04; หน้าเพลงแสดงปุ่ม "ทำนอง" กดไม่ได้พร้อมคำอธิบายของ D14
- ข้อความ: `busy` "กำลังแกะเพลงอื่นอยู่ รอให้เสร็จก่อน"; `song_busy` "กำลังแกะเพลงนี้อยู่"; `not_applicable` "เพลงจาก MIDI ไม่มีช่วงแกะ: การตีทั้งไฟล์คือผลอยู่แล้ว"; ช่วงผิดทุกเหตุ "ช่วงต้องยาว 4–90 วินาที และอยู่ในเพลง" ที่ field `start_s` (< 0) หรือ `end_s` (เกินเพลง ยาวผิด); `model_broken` "ไฟล์โมเดลเสีย รัน Setup script ใหม่ ({label})" `rows` = แถวของโมเดลนั้น `fix` = `checks.setup_fix()`; `model_failed` "โมเดลทำงานผิดพลาด: {บรรทัดแรก}"; ffmpeg พัง = `internal` "แกะโน้ตไม่สำเร็จ: {บรรทัดท้าย}"
- หน้าเพลงเช็คกฎช่วงเดียวกันก่อนถาม backend (ไม่ส่ง `PUT` เมื่อผิด); ปุ่ม "ใช้เวลาที่เล่นอยู่" ปัด `currentTime` เป็น 0.1 วินาที; Alert ของงานที่ `failed` แสดงเฉพาะบนหน้าเพลงของงานนั้น; งานของเพลงอื่นที่รันอยู่แค่ปิดปุ่ม "แกะโน้ต" พร้อมบรรทัดบอก; รายการเพลง poll `GET /songs/pick` ระหว่างงานและโหลดรายการใหม่เมื่อจบ
- `songs.song_jobs` hook แบบ `lessons.lesson_jobs` ให้ `delete` ตอบ `song_busy`; `PickJobs.start` ตั้งงานใต้ lock ของ slot แล้ว `songs.lock` (ลำดับตาม SKILL) จึงไม่มีช่องให้ลบเพลงระหว่างอ่านกับเริ่มงาน; `pick_jobs` อยู่ใน `JOB_HOLDERS` โดยไม่มี clean (งานไม่ทิ้งอะไรบนดิสก์); gate `pick_melody` ยังไม่สร้างจน ticket 04 (ไม่สร้างของใช้ร่วมล่วงหน้า); `Labeled` ย้ายไป `components/ui/` เมื่อหน้าเพลงเป็นผู้ใช้ที่สอง; รายการเพลงใช้ `usePick` ตัวเดียวกับหน้าเพลงอ่านและ poll งาน

**Why:** ทางเลือกที่ spec ไม่ได้ตั้ง ตัดสินตามโค้ดเดิมที่ใกล้ที่สุด (`video_gen.render`, `useDrumRender`) และ spec › API; `bars` จาก server ให้ "ไม่ใช่ 4/4" มาจากกฎเดียวกับ `POST /preview` ที่จะมา (ข้อของ Log ticket 01).

**From:** build ticket 02 · **Status:** changed by D26 (โหมดทำนองรันได้แล้ว ไม่ตอบ `400` field `mode`) — changes D20 (ชื่อ `run_model`)

## D25: ทางเลือกเล็กของบทเรียนจากเพลงจาก ticket 03

**Chosen:**
- module ใหม่ `drum_notes.lesson` ถือ `preview`/`listen`/`create` ของสาม route: ตรวจ body (`bar` จำนวนเต็ม ≥ 0 ไม่งั้น `invalid_request` ธรรมดา; `bars` นอก 1–4 → field `bars`; `bpm` นอก 40–240 หรือไม่ใช่จำนวนเต็ม → field `bpm`; `/listen` และ `/lessons` ต้องส่ง `bpm`), Score ขั้น 2 (`chosen_bars`: ไม่มี `analysis` → `409` `no_analysis` "ยังไม่ได้แกะโน้ต ตั้งช่วงแล้วกด แกะโน้ต"; ห้องเกินหรือไม่ใช่ 4/4 → field `bar` "ห้องนี้ไม่ใช่ 4/4") แล้วส่งต่อ `score.preview` (ขั้น 3–8 เลขล้วน); ไม่ถือ `songs.lock` ระหว่างเรียก `video_gen.lessons` (lock ของ songs เป็นตัวในสุด); เพลงหายระหว่างสร้าง → ลบบทเรียนที่เพิ่งเขียนแล้วตอบ `404` จึงไม่มีบทเรียนที่ไม่มีเพลงชี้
- `video_gen.lessons` ได้ `from_song(title, subtitle, bpm, groove)` (ตัดชื่อ 40 บรรทัดรอง 60 แล้วตรวจด้วย `_checked_fields` ของ `PUT` บนค่าตั้งต้นของบทเรียนใหม่), `create_from(project, fields)` และ `unsaved(fields)` (Lesson ในหน่วยความจำ `id` ว่าง ให้ `timeline.build`/`mixer.mix`); `/listen` ตอบ `422` `too_long` เหมือน `/listen` ของ video-gen เมื่อบทเรียนชั่วคราวยาวเกิน 90 วินาที (4 ห้อง BPM ต่ำ)
- การปัดช่อง: `floor(x + 0.5)` (ครึ่งปัดขึ้น ไม่ใช่ banker's rounding ของ Python); `dropped` เรียงตามช่องแล้วตามลำดับ keep order โดย `hihat_open` ที่คู่ `hihat_closed` ไปก่อน; โน้ตที่ `step` เดียวกันเรียงตาม `kit.PIECES`
- หน้าเพลง: เปิดมาเลือกห้อง 4/4 ห้องแรก 1 ห้อง แล้วขอ `POST /preview` ทันที (หลัง 300 ms); กดห้องบนแถบ = ห้องแรก (ปุ่มห้องมี `aria-pressed`) และตัดจำนวนห้องให้ไม่เกินห้อง 4/4 ติดกันที่เหลือ; ช่อง BPM แสดง `bpm` ของ preview จนผู้ใช้พิมพ์ ค่าที่พิมพ์คงอยู่เมื่อเปลี่ยนห้อง; BPM ที่ผิดกฎแสดง "BPM ต้องเป็นจำนวนเต็ม 40–240" ที่ช่องและไม่ถาม backend; ไม่มีห้อง 4/4 เลย → "ไม่มีห้อง 4/4 ให้เลือก ลองแกะช่วงอื่น" และไม่มีส่วนสร้างบทเรียน; บรรทัด "BPM ที่พบ" ของ ticket 02 ตัด (`bpmOf` หาย) หัวแถบบอกจำนวนห้องแทน; ส่วน "บทเรียนจากเพลงนี้" เป็นลิงก์ "บทเรียน n" คู่ id ไม่อ่านชื่อจาก `/api/drums` (ทุกบทเรียนจากเพลงเดียวกันชื่อเดียวกันอยู่แล้ว)
- ของใช้ร่วมเมื่อ drum-notes เป็นผู้ใช้ที่สอง: `features/video-gen/lib/kit.ts` และ `lesson.ts` (กับ test) ย้ายไป `src/lib/`; `GrooveGrid` ย้ายไป `components/ui/` รับ `editing` (ไม่ส่ง = อ่านอย่างเดียว: ช่องเป็น `<span aria-label>` ไม่มีปุ่มห้อง); `useListen` ย้ายไป `src/lib/` รับ `request()` ที่คืน `BlobReply` หรือ `null` (= ไม่เล่น เช่น บันทึกไม่ผ่าน) แทนคู่ `(id, saveFirst)`
- vitest 5.0.5 ติดตั้ง / 5.1.0 ล่าสุด (minor): ไม่อัปเกรดใน ticket นี้ (ไม่ได้ใช้ API ใหม่)
- จาก review ของ ticket: BPM ตั้งต้นปัดครึ่งขึ้นเหมือนช่อง (`floor(x + 0.5)`); body ของสาม route เป็น `lesson.Choice` (ไม่ชื่อ Pick เพราะชนกับ Pick job); `score` คืน `Scored`/`Dropped` (NamedTuple เลขล้วน) ส่วน response model `Preview`/`DroppedNote` อยู่ใน `lesson`; "ห้องนี้ไม่ใช่ 4/4" ใช้กับห้องเกินท้ายด้วยตาม ticket (หน้าเว็บไม่ให้เลือกจำนวนที่เกินอยู่แล้ว); `lib/lesson.ts` ถือ `notePlace`/`hitName`/`BAR_COUNTS` ที่ตารางและรายการที่ตัดใช้ร่วม; `useListen` มี test ของตัวเอง (`renderHook`) ตามกติกา lib ที่ใช้ร่วม

**Why:** ทางเลือกที่ spec ไม่ได้ตั้ง ตัดสินตามโค้ดเดิมที่ใกล้ที่สุด (`video_gen.lessons`, `mixer.listen`, `useListen`) และกติกา "Where shared code goes".

**From:** build ticket 03 · **Status:** active

## D26: ทางเลือกเล็กของโหมดทำนองจาก ticket 04

**Chosen:**
- ไฟล์ `basic_pitch_nmp.onnx` ที่ pin อ่านจริงแล้ว (ปิด Open Question 1): input `serving_default_input_2:0` `[N, 43844, 1]`; output สามตัวเรียง `:2`, `:1`, `:0` ใน `get_outputs()` — ตรวจด้วยโน้ตสังเคราะห์สามตัวว่า `:2` คือ onset (ขึ้นเกิน 0.5 แค่เฟรมที่โน้ตเริ่ม) `:1` คือ note `:0` คือ contour `[N, 172, 264]`; `onnx_runner.run_basic_pitch` ขอ output ตามชื่อ ไม่พึ่งลำดับ; บันทึกใน `docs/library-notes/basic-pitch.md`
- หน้าต่างตามโค้ดต้นฉบับ (`get_audio_input`/`unwrap_output`): pad ศูนย์ 3,840 sample (15 เฟรม) ที่ต้น แล้วหน้าต่าง 43,844 ทุก 36,164 sample ตราบที่หน้าต่างเริ่มในช่วงที่ pad แล้ว หน้าต่างท้าย pad ศูนย์; ตัด 15 เฟรมต่อด้าน; **เวลาของเฟรมคิดจากต้นหน้าต่างของมันเอง** (`first_sample + frame × 256`) ไม่ต่อเป็นตารางเฟรมเดียว เพราะ hop 36,164 เกินพหุคูณของ 256 อยู่ 68 sample ตารางเดียวจะเลื่อน 8.5 ms ต่อหน้าต่าง (0.47 s บน 90 s)
- onset ที่เฟรมติดกัน (ห่าง < 512 sample รวมข้ามหน้าต่าง ที่ห่าง 68 sample) นับเป็นการตีเดียวที่เฟรมแรก (`score.ONSET_MERGE_SAMPLES`) — โมเดลให้ onset กินสองเฟรมเสมอ (11.6 ms) ถ้าไม่รวมโน้ตเดียวอาจเป็นสอง snare เมื่อคร่อมขอบช่อง; เฟรมที่ sample เกินท้ายช่วงทิ้ง
- โหมดทำนองถอดเสียงอัตราเดียว (22.05 kHz ใช้ทั้ง Basic Pitch และ Beat This!) ไม่ถอด 44.1 kHz ที่ ADTOF ใช้; `percent` = (หน้าต่าง Basic Pitch + chunk Beat This! ที่เสร็จ) / ทั้งหมด (`pick.Steps`) เช็คยกเลิกก่อนทุกหน้าต่าง; gate เลือกตาม `range.mode` ก่อน `busy` ตามลำดับ spec; `analysis.mode` = `range.mode`
- ขั้น 5 ของ Score อยู่ใน `score.preview(hits, bars, bpm, mode)` (`base_groove`: kick ช่อง 0, 8 และ `hihat_closed` ช่องคู่ของทุกห้อง `normal`) หลัง quantize ก่อนตัด/เลือกมือ — ผลเป็น Groove ธรรมดา จึงเดินทางเดิมของ `lesson.preview`/`listen`/`create`; `lesson._scored` ส่ง `analysis.mode`
- หน้าเพลง: คำอธิบายโหมดทำนองแสดงเมื่อเลือก "ทำนอง" เท่านั้น; หัวแถบ "ผลแกะ" บอกโหมด ("ห้องที่พบ n ห้อง · โหมดทำนอง"); ใต้ตารางตัวอย่างของเพลงโหมดทำนองมีบรรทัด "สแนร์คือจังหวะทำนอง · กระเดื่องจังหวะ 1 และ 3 กับไฮแฮทปิดทุกครึ่งจังหวะ แอปเติมให้" (ชื่อชิ้นภาษาไทยตามตาราง) (`MELODY_BASE`); รายการเพลงยังพูด "แกะแล้ว n ห้อง" เหมือนโหมดกลองตาม ticket
- fake: `FakeOnnxRunner(onset=…)` รับ callable `(first_sample) → [172, 88]` และนับหน้าต่างเองเพื่อรู้ตำแหน่ง (`melody_onsets` ตั้งต้น onset ทุก 0.5 วินาที), checkpoint `window n`
- vitest 5.0.5 / 5.1.0 คงเดิมตาม D25
- เปลี่ยน D24: `POST /pick` ของโหมดทำนองไม่ตอบ `400` field `mode` อีก; spec › Pick job เรียงขั้นตามโค้ด (กฎ range ก่อน gate เพราะโหมดอยู่ใน range) และ `preparing` ของโหมดทำนองอัตราเดียว

**Why:** ทางเลือกที่ spec ไม่ได้ตั้ง ตัดสินตามโค้ดต้นฉบับของ Basic Pitch (ที่ spec อ้าง) และโค้ดเดิมของ ticket 02–03 (`score` เลขล้วน, `Chunk`/`stitch`, fake ระดับ session).

**From:** build ticket 04 · **Status:** active

## D27: ผล feature review

**Chosen:**
- แก้ทันที: bug ช่วงตั้งต้นของเพลงที่เอาเข้าใหม่สร้างจากความยาวก่อนปัด (เช่น 6.24 s) ขณะ `duration_s` ปัดเป็น 6.2 → `POST /pick` ครั้งแรกตอบ `400` field `end_s` — ตอนนี้ `default_range(round(seconds, 1))` (+ regression test); `busy` บอกชื่อเพลงที่แกะอยู่ "กำลังแกะ {title} อยู่ รอให้เสร็จก่อน" (เพลงหายแล้ว = "เพลงอื่น") ตาม spec › Design; Song import ตรวจลิงก์ก่อน gate ตามลำดับ spec; `RefusedAlert` (Alert + FixCommand) เป็นของใช้ร่วมใน `components/ui/` แทนที่สามสำเนา (SongPage, SongList, LessonEditor ของ video-gen); `fixesFor(refusal)` ใน `lib/setupFixes.ts` แทนบรรทัดซ้ำสี่ที่; `BAR_COUNTS` ย้ายมา `features/drum-notes/lib/songs.ts` (ผู้ใช้เดียว); ชนิดฝั่งหน้าเว็บ `Pick` (body) → `Choice` ตาม backend, `Hit` → `FoundHit` (ไม่ชนกับ `Hit` ของ `lib/lesson.ts`); `running` ใช้ `isPicking`; `setup.OpenSession` = ของ `onnx_runner`; ข้อความไทยของ imports เป็นค่าคงที่; test เพิ่ม `413` ที่ `PUT`, `in_use` ตอนลบ (`Path.unlink` โยน `PermissionError`), test ที่ query `<audio>` ทั้งหน้าเปลี่ยนเป็นในส่วน "เพลง", ตัด assert ค่าคงที่ของ GM map
- คงไว้และบันทึก: ชื่อเพลง MIDI จาก track name (meta 0x03) ก่อนชื่อไฟล์ — เกิน D10 แต่ให้ชื่อที่ดีกว่าโดยไม่เปลี่ยน schema; หน้า "ไม่พบเพลงนี้" พร้อมลิงก์กลับแทนเด้งกลับรายการ; รายละเอียดแถว Status check แสดง revision สั้นกับขนาดตามแบบโมเดลอื่น (`_model_item`) ไม่มี repo; test `run_capture` ยกเลิกด้วย `threading.Timer(0.3)` — ยอมรับ: cancel ที่ตั้งก่อนเริ่ม ระหว่างอ่าน หรือหลังจบล้วนให้ `Cancelled` จึงไม่ขึ้นกับเวลา; fixture ของ songs/lesson API ไม่สลับ `gpu.slot` เหมือน toon sounds และ video-gen render ที่ไม่มีงาน GPU
- ไม่ทำใน feature นี้ (Blocked → `/warroom tickets drum-notes`): `JobSlot.cancel` ร่วมของสาม slot, รูป "API ปฏิเสธ" สี่แบบในหน้าเว็บ, แยก `score.py` เป็นเลขสัญญาณกับกฎ Groove, ตารางต่อโหมดแทน `if mode` สามที่, fake Beat This! ถูกเฉพาะ chunk แรก, `Placed.piece: str`, `_take_in` รับ title/subtitle/source แยก, `SongImports.start` คืน tuple, `tabOf`/`App` และ helper ของ toon (ข้าม feature)
- ต้องเจ้าของ (Blocked → `/warroom drum-notes`): Beat This! ให้ 2 จังหวะต่อห้องบนท่อนเบา/เพลงทำนอง (รวมห้องเป็นคู่?), `crash` + ไฮแฮทช่องเดียว → crash ได้ L (เปลี่ยน D13?), `Song.title` 1–60 ตอนอ่าน; และฟังเทียบตาราง intro (03) กับ kalimba (04)

**Why:** กติกา feature review: แก้สิ่งเล็กที่ไม่เปลี่ยน spec ทันที ส่วนที่เปลี่ยน spec หรือเป็น refactor ข้าม module ไปเป็น ticket.

**From:** feature review · **Status:** active

## Sources

- [ADTOF Frame_RNN (ONNX) model card](https://huggingface.co/thebluescreen/adtof-drums-onnx) — input/output, threshold, peak picking, license CC BY-NC-SA 4.0, revision (accessed 2026-11-14)
- [Beat This! (ONNX) model card](https://huggingface.co/thebluescreen/beat-this-onnx) — input 22.05 kHz, logit 50 เฟรม/วินาที, การหา peak, license MIT, revision (accessed 2026-11-14)
- [Andremi/audioweb-models](https://huggingface.co/Andremi/audioweb-models) — `analysis/basic_pitch_nmp.onnx` sha256 และ license Apache-2.0 (accessed 2026-11-14)
- [spotify/basic-pitch README](https://github.com/spotify/basic-pitch) — resample 22,050 Hz, license Apache-2.0 (accessed 2026-11-14)
- [basic_pitch/constants.py](https://github.com/spotify/basic-pitch/blob/main/basic_pitch/constants.py) — ขนาดหน้าต่าง 43,844 sample, 172 เฟรม, overlap 30 เฟรม (accessed 2026-11-14)
- [demucs README](https://github.com/adefossez/demucs) — "The license of the weights is not clear" (accessed 2026-11-14)
- [madmom issue #485](https://git.tdem.in/CPJKU/madmom/issues/485) — ไม่รองรับ Python และ numpy ใหม่ (accessed 2026-11-14)
- [onnxruntime on PyPI](https://pypi.org/project/onnxruntime/) — 1.32.0, MIT, wheel cp312 macOS arm64 และ win_amd64 (accessed 2026-11-14)
- [MZehren/ADTOF README](https://github.com/MZehren/ADTOF) — license CC BY-NC-SA 4.0 ของ repo ต้นฉบับ (accessed 2026-11-14)
- [CPJKU/beat_this README](https://github.com/CPJKU/beat_this) — โค้ดและน้ำหนัก MIT (accessed 2026-11-14)
