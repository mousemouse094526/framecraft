# Decisions: kalimba-cover

## D1: Reel cover มีเครื่องดนตรีสองแบบ `กลอง` / `คาลิมบา` ใน Cover เดียวของเพลง; กลองเป็นค่าตั้งต้น

**Chosen:** `cover.json` ของเพลงได้ฟิลด์ `instrument` (`drums` หรือ `kalimba`) ตั้งต้น `drums`; ช่วง ข้อความบนจอ พื้นหลัง และ backing ใช้ชุดเดียวกันทั้งสองแบบ ผล render บันทึกว่าเป็นแบบไหน.

**Why:** เจ้าของขอ "มีให้ render 2 แบบ คือ kalimba กับกลอง" จากเพลงเดียวกัน และให้กลองเป็นพฤติกรรมเดิม.

**Rejected:**
- Cover แยกต่อเครื่องดนตรี (`cover.json` กับ `kalimba.json`) — ต้องตั้งช่วงและข้อความสองครั้งสำหรับท่อนเดียวกัน และหน้า reel ต้องมีสองหน้า
- tab หรือรายการ reel ใหม่ — drum-cover D1 ตัดไว้แล้ว: ทางเข้าคือหน้าเพลงเดิม
- เปลี่ยนค่าตั้งต้นเป็นคาลิมบา — เจ้าของบอกให้กลองเป็นค่าตั้งต้น

**Details:**
- เป็น feature ใหม่บนบอร์ด (`kalimba-cover`) ตามที่เจ้าของเปิดไว้ แต่โค้ดต่อจาก drum-cover: Cover, Render job และหน้า reel ของ drum-cover ใช้ต่อ (drum-cover D2, ADR-0052)
- `cover.json` เก่าที่ไม่มี `instrument` อ่านเป็น `drums` (แบบ `drums` ของ drum-cover D24)

**From:** change request · **Status:** active

## D2: โน้ตทำนองเก็บเป็น `analysis.notes` แยกจาก `hits`; Pick job ทุกโหมดถอด Basic Pitch ด้วย

**Chosen:** `Analysis` ได้ `notes` (`t`, `pitch` เลข MIDI 0–127, `level`) แยกจาก `hits` ของกลอง; ทุก Pick job ทั้งโหมดกลองและโหมดทำนองรัน Basic Pitch แล้วเก็บ onset ทุกคีย์เป็นโน้ต; โหมดทำนองใช้ผลรอบเดียวกันทำ snare ตามเดิม.

**Why:** เพลงหนึ่งมีผลแกะชุดเดียว ถ้าคาลิมบาได้เฉพาะโหมดทำนอง เพลงเดียวกันจะ render กลองกับคาลิมบาไม่ได้ทั้งคู่ (ตัวเลือก Recommended ที่ auto mode เลือก).

**Rejected:**
- คาลิมบาเฉพาะเพลงที่แกะโหมดทำนอง — สลับไปกลองต้องแกะใหม่และผลเดิมหาย
- เพิ่ม `pitch` ลงใน `Hit` ของกลอง (ตามที่ brief เสนอ) — `hits` ของโหมดกลองมาจาก ADTOF ไม่มี pitch; การรวมสองสายใน list เดียวทำให้ reel กลองต้องกรองโน้ตทำนองออกทุกที่ที่อ่าน `hits`
- รัน Basic Pitch เฉพาะตอนเปิดหน้า reel คาลิมบา — ต้องมีงานถอดเสียงที่สอง และ ADR-0052 ให้ reel อ่าน `analysis` ปัจจุบันเท่านั้น

**Details:**
- `notes` ไม่มีในไฟล์ (เพลงที่แกะก่อน feature นี้) = `null`: หน้า reel บอกให้แกะใหม่; `[]` = แกะแล้วไม่พบโน้ต
- onset ของแต่ละคีย์ ≥ 0.5 คือโน้ต (เกณฑ์เดียวกับ drum-notes D14); เฟรมติดกันของคีย์เดียวกันคือโน้ตเดียว; `level` จากเสียง = `normal` ทั้งหมด (แบบ drum-notes D9)
- โหมดกลองไม่ต้องพึ่ง Basic Pitch: โมเดลไม่มีหรือพัง → `notes` `null` งานกลองจบตามเดิม (D14); เป้า Pick job 90 วิ ≤ 60 วิ ของ drum-notes D19 ต้องยังผ่าน (D12)
- โน้ตจากเสียงเป็นร่างแบบผลแกะกลอง (drum-notes D6): Basic Pitch ฟังทั้ง mix
- เพดาน `MAX_HITS` 20,000 ใช้กับ `notes` แยกกัน

**From:** interview · **Status:** active

## D3: แผ่นโน้ต = ไฟล์ MIDI ผ่านทาง import เดิม อ่านช่องทำนองเป็น `notes`

**Chosen:** `drum_notes.midi` อ่าน note-on ของทุกช่องที่ไม่ใช่ช่อง 10 เป็น `notes`; ไฟล์รับได้เมื่อมีการตีกลองหรือโน้ตทำนองอย่างน้อยหนึ่งอย่าง; กติกา 4/4 tempo แรก และเพดานเดิมคงไว้ (drum-notes D10, D22).

**Why:** brief ของเจ้าของให้ทางเข้าที่สั้นที่สุด: `.mid` มีทาง import อยู่แล้วใน `#/songs` ไม่ต้องถอดเสียง และ MuseScore กับแอปแผ่นโน้ตส่วนใหญ่ export MIDI ได้.

**Rejected:**
- MusicXML (`.musicxml`, `.mxl`) ตอนนี้ — ต้องมี parser XML ของโน้ตและ tie/voice/repeat ใหม่; เป็นคำถามของเจ้าของใน progress.md › Blocked
- PDF หรือภาพแผ่นโน้ต — ต้องมี OMR (เช่น Audiveris เป็น Java AGPL) ขัด ADR-0001 และไม่แม่น
- เลือกแทร็กเดียวในไฟล์ — ต้องมีหน้าเลือกแทร็ก; การจัดโน้ต (D4, D14) ทิ้งโน้ตต่ำกว่า C3 และเหลือแต่โน้ตบนสุดของคอร์ด ซึ่งพอสำหรับไฟล์ทำนองกับเปียโนสองมือส่วนใหญ่

**Details:**
- ข้อความ `unsupported_file` ใหม่: "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลองหรือโน้ตทำนอง"
- ความยาวเพลง = เวลาของการตีหรือโน้ตตัวสุดท้าย + 1 ห้อง
- ความยาวโน้ต (note-off) ไม่ใช้: คาลิมบาดังจนหมดเสียงเอง (D5)
- ไฟล์ที่มีแต่ทำนอง: `hits` ว่าง → reel กลองเจอ Alert เดิม "ช่วงนี้ไม่มีการตีกลอง" (drum-cover D18); ค่าตั้งต้น `instrument` เป็น `kalimba` (D9)

**From:** change request · **Status:** active

## D4: จัดโน้ตลงคาลิมบา 17 คีย์ C major ตอนสร้าง timeline ด้วยกติกาตายตัว

**Chosen:** คาลิมบา 17 คีย์ตั้งเสียง C major C4–E6 เรียงแบบมาตรฐาน; ตอนสร้าง timeline โน้ตในช่วงถูกย้ายคีย์ทั้งชุด ทิ้งเบส ปัดเข้าสเกล เหลือโน้ตบนสุดของโน้ตที่พร้อมกัน และพับอ็อกเทฟ ตาม spec › การจัดโน้ตลงคาลิมบา; `analysis.notes` ไม่ถูกแก้.

**Why:** โน้ตจากเพลงจริงมีเบส คอร์ด และเสียงนอกสเกล ซึ่งคาลิมบา 17 คีย์เล่นไม่ได้; กติกาตายตัวให้ผลเดิมทุกครั้งและไม่ต้องมีหน้าแก้โน้ต (drum-cover D3).

**Rejected:**
- คาลิมบาโครมาติก (มีคีย์ครึ่งเสียง) — ไม่ใช่คาลิมบาที่คนดู reel คุ้น และภาพต้องมีสองแถว
- ตัดโน้ตนอกช่วงทิ้ง — เพลงที่ทำนองอยู่ต่ำกว่า C4 จะเหลือแทบไม่มีโน้ต
- เก็บผลที่จัดแล้วลง `song.json` — ผลจะไม่ตามเมื่อเปลี่ยนช่วง และต้องมี schema ที่สอง

**Details:**
- ลำดับคีย์ซ้ายไปขวา: D6 B5 G5 E5 C5 A4 F4 D4 C4 E4 G4 B4 D5 F5 A5 C6 E6 (C4 กลางยาวที่สุด)
- ย้ายคีย์ทั้งชุด `k` ใน −6…+5 ครึ่งเสียง ที่ทำให้โน้ตตกในสเกล C major มากที่สุด เสมอกันเลือก `|k|` น้อย แล้ว `k` บวก
- หน้า reel บอกผล: "ย้ายคีย์ {k}", "{n} โน้ต", "ตัด {d} โน้ต", "ปรับ {b} โน้ตให้เข้าสเกล" (D9, D14)

**From:** change request · **Status:** active

## D5: เสียงคาลิมบาสังเคราะห์ด้วย numpy ก่อน; sample CC0 เป็นทางเลือกที่เจ้าของตัดสิน

**Chosen:** `kalimba_cover.sound` สังเคราะห์โน้ตแบบ additive (ความถี่หลักกับ partial ของก้านโลหะ decay แบบ exponential และเสียงกระทบสั้น) ด้วย numpy ผสมตาม timeline ที่ 16-bit 44.1 kHz stereo peak −1 dBFS แบบ `video_gen.mixer`; ไม่มีไฟล์ให้โหลด ไม่มีแถว Status check.

**Why:** ตัวเลือก Recommended ที่ auto mode เลือก: ได้ทุก pitch ตรงเสียง ไม่ต้องติดตั้ง ผลเดิมทุก byte และไม่มีคำถาม license; ชุด CC0 เดียวที่พบเป็น mbira ตั้งเสียงคนละแบบ.

**Rejected:**
- VCSL "Kalimba, Tanzania" (CC0, 27 คีย์ ชั้นเดียว ~23 MB) ตอนนี้ — ตั้งเสียงแบบ mbira ไม่ตรง C major ต้องเลื่อน pitch ทุกโน้ต และเสียงซ่าของ mbira ไม่ใช่คาลิมบาสมัยใหม่; เก็บเป็นคำถามของเจ้าของ (progress.md › Blocked)
- Karplus-strong — เสียงออกกีตาร์มากกว่าก้านโลหะ
- sample จาก Freesound, Gumroad, pianobook — ไม่พบว่าเป็น CC0 ชัด (ADR-0042 ต้อง CC0)

**Details:**
- interface เดียว `sound.note(pitch, level) -> float32 mono` ให้เปลี่ยนเป็น sample ภายหลังได้โดยไม่แตะ timeline หรือภาพ
- ค่าเริ่มต้นของเสียงอยู่ใน spec › เสียงคาลิมบา; ปรับได้ตอน build เมื่อเจ้าของฟัง

**Sources:** [VCSL](https://github.com/sgossner/VCSL)

**From:** interview · **Status:** active

## D6: Reel คาลิมบามี timeline ของตัวเองที่เสียงและภาพอ่านจากที่เดียว

**Chosen:** `kalimba_cover.timeline.build(analysis, cover) -> KalimbaTimeline` ให้โน้ตที่จัดแล้ว (sample, คีย์, pitch, level) จังหวะที่มีเลข และความยาว; `sound.mix`, `frames` และ `captions` ของคาลิมบาอ่านเวลาจาก `KalimbaTimeline` เท่านั้น.

**Why:** `video_gen.timeline.Timeline` ผูกกับชิ้นกลอง (kit order, round-robin ของ `drum_kit.SAMPLES`); หลักเสียงตรงภาพเพราะมาจากโน้ตชุดเดียว (ADR-0041, ADR-0051) ใช้ต่อได้ด้วยชนิดของตัวเอง.

**Rejected:**
- ใช้ `Timeline` เดิมโดยให้ `piece` เป็น `tine_N` — `assemble` จะล้มที่ kit order และ round-robin; ต้องแก้ของ video-gen ที่ใช้ร่วม
- คำนวณเวลาโน้ตใน frames เอง — ขัด ADR-0041

**Details:**
- กติกาช่วง จังหวะ และเลขจังหวะเหมือน `drum_cover.timeline` ทุกข้อ (drum-cover spec › Timeline ของ reel ข้อ 5–6); ฟังก์ชันจังหวะใช้ร่วม ไม่คัดลอก
- ความยาว = `end_s − start_s + 1.5` วิ (หางเสียงแบบเดิม)

**From:** code · **Status:** active

## D7: ภาพ reel คาลิมบา: โน้ตตกลงตามคอลัมน์ของคีย์ คาลิมบาด้านล่าง คีย์ที่ถูกเล่นสว่าง

**Chosen:** 1080×1920 ตาม [kalimba-picture-sketch.md](kalimba-picture-sketch.md): หัวเรื่องและตัวนับที่เดิมของ reel กลอง, โน้ตตกลงในคอลัมน์ของแต่ละคีย์ถึงเส้นเล่นเหนือคาลิมบา, คาลิมบา 17 คีย์ด้านล่างที่คีย์ถูกเล่นเติมสีเต็มแล้วจางใน 0.15 วิ, ป้ายเลขโน้ต 1–7 มีจุดบอกอ็อกเทฟใต้คีย์; โน้ตที่ตกบอกเลขด้วยสี ไม่มีตัวหนังสือ (D14).

**Why:** brief ของเจ้าของขอ "ไม้ที่ถูกตีสว่างขึ้น" ในสไตล์เดียวกับ reel กลอง; โน้ตตกลงตามคอลัมน์และเลขโน้ตเป็นแบบที่คลิปคาลิมบาทั่วไปใช้ คนดูเล่นตามได้.

**Rejected:**
- เลนแนวนอนแบบ reel กลอง 17 แถว — แถวละ ~25 px อ่านไม่ออก
- ป้ายชื่อโน้ตแบบตัวอักษร (C D E) อย่างเดียว — คลิปคาลิมบาส่วนใหญ่ใช้เลข; ตัวอักษรเล็กใส่ใต้เลข
- ภาพมือและนิ้วโป้ง — ต้องมีกติกาเลือกนิ้วที่ไม่มีใครขอ

**Details:**
- ของนิ่งวาดครั้งเดียว ของที่ขยับวาดจาก `t` ด้วย Pillow ตัวหนังสือทุกตัวเป็น ASS (ADR-0040); พื้นหลังจาก `video_gen.frames.background_image` (drum-cover D8)
- สีของคีย์ตามเลขโน้ต 7 สี ใช้สีเดียวกันกับโน้ตที่ตก
- ภาพเป็นของ `kalimba_cover` แบบที่ ADR-0054 อนุญาต "ทำของตัวเองตามกติกาเดียวกัน"

**From:** change request · **Status:** active

## D8: โค้ดคาลิมบาอยู่ใน package ใหม่ `backend/kalimba_cover`; Cover, routes และ Render job คงอยู่ใน `drum_cover`

**Chosen:** `kalimba_cover` ถือ `arrange`, `timeline`, `sound`, `frames`, `captions` ของคาลิมบา; `drum_cover.cover`, `audio.reel_wav`, `render` และ routes เลือกทางตาม `instrument`; `kalimba_cover.arrange` import แค่ `drum_notes.songs` และ `drum_cover.cover` import มันได้; module อื่นของ `kalimba_cover` import `drum_cover` ได้ `drum_cover` ไม่ import มัน ยกเว้น `render` (D14).

**Why:** Cover หนึ่งชุดต่อเพลงมีเจ้าของคนเดียวอยู่แล้ว (ADR-0052); ของที่ต่างกันจริงคือเสียงกับภาพ ซึ่ง ADR-0054 ให้แต่ละเครื่องดนตรีมีของตัวเอง.

**Rejected:**
- เปลี่ยนชื่อ `drum_cover` เป็น `reel_cover` — แตะทุก import test และ ADR โดยไม่เปลี่ยนพฤติกรรม
- ใส่คาลิมบาใน `drum_cover` ทั้งหมด — `frames.py` 449 บรรทัดของกลองจะปนกับของคาลิมบา
- Render job ใหม่ slot ของคาลิมบา — reel สองแบบของเพลงเดียวจะ render ซ้อนกันได้และต้องมี route งานชุดที่สอง

**Details:**
- `reel_wav` รับเสียงเครื่องดนตรีเป็น wav ที่ผสมแล้ว: กลอง = `mixer.mix`, คาลิมบา = `kalimba_cover.sound.mix`; ความดังและ backing ทำทางเดิม (drum-cover D17, D24)
- Render job เดิมหนึ่ง slot: reel กลองและคาลิมบา render ทีละงาน `busy` ตามเดิม (drum-cover D12)

**From:** code · **Status:** active

## D9: ข้อมูลและ API ของ Cover ที่เพิ่ม

**Chosen:** bundle ของฟิลด์ ค่าตั้งต้น และ error ที่เพิ่มใน Cover และผล render เพื่อรองรับสองเครื่องดนตรี.

**Details:**
- **`kalimba`:** `{on, volume}` 10–100 ตั้งต้นเปิด 100 แบบ `drums` (drum-cover D24); ไฟล์เก่าไม่มี → ค่าตั้งต้น — ความดังแยกของแต่ละเสียงตามที่ brief ขอ
- **ห้ามเงียบ:** เสียงของเครื่องดนตรีที่เลือกปิดและ backing ปิด → `400` field `{instrument}.on` "เปิดเสียง{กลอง/คาลิมบา}หรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง" — กติกาเดิมของ drum-cover D24 ต่อเครื่องดนตรี
- **ค่าตั้งต้นของ `instrument`:** `drums`; ยกเว้นช่วงตั้งต้นไม่มีการตีกลองแต่มีโน้ตทำนอง → `kalimba` — เพลง MIDI ทำนองล้วนเปิดมาเห็นคาลิมบา ไม่ใช่ Alert ไม่มีกลอง
- **`GET /cover`:** เพิ่ม `notes` (จำนวนโน้ตหลังจัดในช่วง), `notes_picked` (`false` เมื่อ `analysis.notes` เป็น `null`), `transpose`, `dropped` — หน้า reel บอกผลการจัดได้โดยไม่คำนวณเอง
- **ผล render:** `.json` เพิ่ม `instrument` และ `kalimba`; ไฟล์เก่า → `drums` และค่าตั้งต้น — แถวผลมีป้าย "คาลิมบา"
- **ไม่มีโน้ต:** `instrument` `kalimba` กับ `notes` 0 → `listen` และ `render` ตอบ `409` `no_notes`; `notes_picked` `false` → ข้อความ "แกะใหม่" — ปุ่มบนหน้าปิดไว้ก่อนแล้ว
- **gate:** render คาลิมบาต้องมี Kanit, ffmpeg, pythainlp (ไม่ต้องมี sample กลอง); ฟังคาลิมบาไม่ต้องมีแถวใด (ffmpeg เมื่อ backing) — เพลงที่ยังไม่โหลด sample กลองก็ทำคาลิมบาได้

**From:** code · **Status:** active

## D10: หน้า reel เลือกเครื่องดนตรีด้วยปุ่มสองทาง และหน้าจอที่เพิ่มสร้างตาม `ui-prompt.md` ไม่รอ Figma

**Chosen:** การ์ดแรกของหน้า reel คือ "เครื่องดนตรี" ปุ่มสองทาง "กลอง" / "คาลิมบา"; การ์ด "เสียง" แสดงแถวของเครื่องดนตรีที่เลือก; แบบหน้าจอทำจาก `ui-prompt.md` กับ design system เดิม (แบบ drum-cover D14).

**Why:** brief ของเจ้าของ: ถ้ายังไม่มี Figma ให้ทำตาม `ui-prompt.md` ที่เขียนเองตามสไตล์แอปแล้วบันทึกเป็น decision ไม่ต้องรอ.

**Rejected:**
- สองปุ่ม render ("render กลอง", "render คาลิมบา") — ฟังกับ render ต้องตรงกัน และความดังต้องตั้งแยกอยู่ดี
- รอแบบใน Figma — เจ้าของบอกไม่ต้องรอ

**From:** change request · **Status:** active

## D11: seam สามจุดของ drum-cover ใช้ต่อ เพิ่มกรณีคาลิมบาเข้าแต่ละจุด

**Chosen:** (1) API ของ reel ผ่าน `TestClient` ด้วย ffmpeg จริง, (2) ตัวเลขล้วน: `drum_notes.score`/`midi` และ `kalimba_cover.arrange`/`timeline`/`sound`/`frames`/`captions`, (3) หน้าเพลงและหน้า reel ผ่าน `App` (e2e).

**Why:** seam เดิมของ drum-cover D13 และ drum-notes D17 พิสูจน์ทางเดียวกันได้ทั้งทางแล้ว; คาลิมบาไม่มีโมเดลใหม่และไม่มีไฟล์ใหม่ให้โหลด.

**Rejected:**
- seam ที่สี่ของเสียงคาลิมบา — `sound` อยู่ในตัวเลขล้วน (seam 2) พร้อม test FFT ของ D12 ไม่ต้องมี seam แยก

**From:** code · **Status:** active

## D12: เป้าที่วัดได้

**Chosen:** bundle ของเป้า pass/fail ของ feature นี้.

**Details:**
- **เสียงตรงภาพ:** เฟรมแรกที่คีย์ของโน้ตเติมสีเต็ม กับจุดเริ่มเสียงของโน้ตนั้น ห่างไม่เกิน 1 เฟรม — แบบ drum-cover D15
- **ผลเดิม:** reel คาลิมบาเดิม render สองครั้ง (backing ปิด) ได้ `audio.wav` เหมือนกันทุก byte; reel กลองที่ volume 100 ได้ byte เดียวกับก่อน feature นี้
- **เวลา render:** reel คาลิมบา 30 วิ render จบ ≤ 60 วิบน Mac Apple Silicon
- **Pick job:** ช่วง 90 วิโหมดกลอง (ADTOF + Basic Pitch + Beat This!) ยังจบ ≤ 60 วิบน Mac (drum-notes D19)
- **ระดับเสียง:** โน้ต C4 ตัวเดียว: ความถี่หลักใน FFT อยู่ที่ 261.6 Hz ± 1 Hz; คาลิมบา volume 50 → peak ต่ำกว่า volume 100 6.0 dB ± 0.1
- **เจ้าของ (เสียง):** แกะเพลงจริงหนึ่งเพลงใหม่ (Yellow 11.5–30) แล้วฟังคาลิมบาจาก `/listen`: ยังจำทำนองได้ หรือเป็นคำถามใน Blocked (เกณฑ์ onset หรือจำนวนโน้ตต่อวินาที) — ก่อนทำภาพ (D14)
- **เจ้าของ:** import MIDI ทำนองหนึ่งไฟล์ (เช่นเพลงพื้นบ้านที่หมดลิขสิทธิ์) แล้วรับว่า reel คาลิมบาเล่นทำนองถูก; ฟังเสียงสังเคราะห์แล้วตอบคำถาม sample จริงใน Blocked

**From:** code · **Status:** active

## D13: รับความเสี่ยง legal ข้อ 1–2 (UNVERIFIED) ภายใต้กรอบไม่หารายได้เดิม

**Chosen:** เผยแพร่ reel คาลิมบาของทำนองเพลงที่มีลิขสิทธิ์ได้ภายใต้เงื่อนไขเดียวกับ drum-cover D16 (ท่อน ≤ 90 วิ, ชื่อเพลงและศิลปิน, ไม่หารายได้) และ MIDI ที่ผู้ใช้นำเข้าเป็นความรับผิดชอบของผู้ใช้ พร้อมคำใบ้บนหน้าเพลง.

**Why:** auto mode เลือกตัวเลือกเดียวกับที่เจ้าของรับไว้แล้วใน drum-cover D16 (ADR-0053); feature นี้เพิ่มความเสี่ยงชนิดเดียวกัน.

**Rejected:**
- ไม่ทำคาลิมบาของเพลงที่มีลิขสิทธิ์ — ขัดคำขอของเจ้าของ
- บังคับให้ MIDI มาจากแหล่งที่มี license — แอปตรวจที่มาของไฟล์ไม่ได้

**Accepted risk:** ทำนองเป็นแก่นของงานดนตรีมากกว่าส่วนกลอง: มาตรา 33 "บางตอนตามสมควร" อ่อนกว่ากรณี drum-cover และแพลตฟอร์มมีแนวโน้ม claim เมื่อทำนองตรง; ยอมรับเพราะไม่หารายได้ ท่อนสั้น และผู้ใช้เผยแพร่เอง (legal ข้อ 1–2).

**From:** legal · **Status:** active

## D14: ข้อแก้จาก red team

**Chosen:** bundle ของข้อแก้ที่ red team เสนอและรับไว้ (auto mode); ข้อที่ไม่รับอยู่ใน Rejected.

**Rejected:**
- ใช้ `drums {on, volume}` เป็นความดังของเครื่องดนตรีที่เลือก (The Skeptic) — ชื่อฟิลด์ `drums` ที่หมายถึงคาลิมบาทำให้อ่าน `cover.json` และผล render ผิด; การตรวจค่าใช้ `_sound` ตัวเดียวกันอยู่แล้ว
- `\clip` และเวลาปัด centisecond ของเลขบนโน้ตที่ตก (The Breaker) — ตัดเลขบนโน้ตที่ตกออกแล้ว

**Details:**
- **ทำนองด้านบน:** กลุ่มพร้อมกันเหลือโน้ตสูงสุดตัวเดียว ไม่เก็บตัวต่ำสุด — ตัวต่ำสุดคือเบสหรือมือซ้ายที่พับขึ้นมาทับทำนอง (Skeptic, Advocate, Breaker)
- **ทิ้งเบส:** โน้ตต่ำกว่า C3 (48) ทิ้งก่อนย้ายคีย์; เลือกตัวบนสุดก่อนพับอ็อกเทฟ; คีย์ซ้ำในกลุ่มเหลือตัวแรก — เบสที่ไม่ตรงจังหวะทำนองไม่ถูกตัดด้วยกฎกลุ่ม (Advocate, Breaker, Tester)
- **`bent`:** นับโน้ตที่ปรับเข้าสเกล แสดงบนหน้า reel — การปรับครึ่งเสียงเปลี่ยนทำนองที่ได้ยินมากที่สุด (Advocate)
- **คำเตือนย้ายคีย์กับ backing:** คาลิมบา + backing + `transpose` ไม่ใช่ 0 → "คาลิมบาย้ายคีย์ {k} เสียงจะไม่ตรงกับเพลงต้นฉบับ" — คีย์ชนกับเพลงจริงดูเหมือน bug (Advocate)
- **ไม่มีเลขบนโน้ตที่ตก:** สีบอกเลข เลขอยู่ใต้คีย์ — ตัด animation ASS ชุดที่สองที่ต้องตรงกับ Pillow (Skeptic)
- **Basic Pitch ไม่ทำให้แกะกลองพัง:** โหมดกลองที่โมเดลไม่มีหรือพัง → `notes` `null`; gate `pick_drums` ไม่เปลี่ยน — แกะกลองที่ใช้ได้วันนี้ต้องยังใช้ได้ (Breaker, Advocate)
- **MIDI เก่า:** import ไฟล์ MIDI เดิมของเพลงที่ `notes` `null` → เติม `notes` ตอบเพลงเดิม; ข้อความ "นำเข้าไฟล์ MIDI เดิมอีกครั้ง" — แกะใหม่ของเพลง MIDI ตอบ `not_applicable` จึงเป็นทางตัน (Breaker)
- **โครงสร้าง:** `kalimba_cover.arrange` ไม่ import `drum_cover` ให้ `cover.py` เรียกได้; helper ที่ใช้ร่วมระบุ signature ใน spec (`numbered_beats`, `bars_of(beats)`, `beat_dots`, `text_events`, `bar_counter_events`); `components/ui/SegmentedChoice`; ลำดับ error ของ render/listen เขียนครบ; ความเร็วตกต่ำสุด 350 px/วิ; สูตร y ใช้ `at / 44100`; เป้าเจ้าของฟังโน้ตจากเสียง; seam 2 รวม `sound`/`captions` — Builder 1 (BLOCKER), 2, 3, 4; Tester 1–5; Breaker 5; Advocate 2

**From:** red team · **Status:** active

## Sources

- [VCSL — Versilian Community Sample Library (CC0)](https://github.com/sgossner/VCSL) — ชุด CC0 ที่มี "Kalimba, Tanzania" 27 ไฟล์ (accessed 2026-11-16)
