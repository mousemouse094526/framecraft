# Decisions: drum-cover

## D1: feature ใหม่ `drum-cover`: reel cover เป็นทางออกหลักของเพลงที่แกะ ไม่ใช่บทเรียน

**Chosen:** feature ใหม่ slug `drum-cover` รับ Song ของ tab แกะเพลงเป็นต้นทาง แล้วออกเป็น reel cover หนึ่งคลิป: ชุดกลองแอนิเมต โน้ตที่ตี และเสียงกลองที่ผสม. tab แกะเพลง (drum-notes) และ tab สอนกลอง (video-gen) คงอยู่ทั้งคู่ ไม่ลบ ไม่แก้โหมดสอน.

**Why:** เจ้าของใช้ของจริงแล้วบอกว่า "ผมไม่ได้ทำการสอน แค่จะเอาคลิปที่แกะมา cover เป็น reels ลงช่อง แบบต้นฉบับ": สิ่งที่ส่งไป (บทเรียน BPM ท่อนสอน ป้าย) ไม่ใช่สิ่งที่ต้องการ. reel มีข้อมูลของตัวเอง (การตั้งค่าและผล render) และใช้ได้ด้วยตัวเองโดยไม่แตะบทเรียน จึงเป็น feature ใหม่ที่เป็นทางออกหลักแทน ไม่ใช่ change request ของ drum-notes.

**Rejected:**
- change request ใน drum-notes เพิ่มปุ่ม render ในหน้าเพลง — ผลคือ output คนละอย่างกับบทเรียน มีไฟล์ของตัวเอง และเป็นสินค้าจริงของเจ้าของ ไม่ใช่ส่วนเสริม
- เปลี่ยน video-gen เป็นโหมด cover — เจ้าของสั่งคงโหมดสอนไว้เหมือนเดิม
- tab ใหม่สำหรับ reel — ทางเข้าคือเพลงที่แกะอยู่แล้ว; tab ที่ 9 ที่มีรายการของตัวเองไม่มีใครขอ

**Details:**
- ทางเข้า: หน้าเพลง `#/songs/{id}` หลังแกะโน้ตแล้ว; ทางออก: หน้า reel `#/songs/{id}/cover` ของ feature นี้ (D11)
- code อยู่ใน package `backend/drum_cover` และ `frontend/src/features/drum-cover`
- pipeline เดิมทั้งหมดใช้ต่อ: Song import และ Pick job ของ drum-notes, sample Big Rusty Drums, ชุดกลองและเลนโน้ตของ video-gen, ffmpeg render (D4)

**From:** change request · **Status:** active

## D2: Cover เป็นการตั้งค่าหนึ่งชุดต่อเพลง อยู่ใน folder ของ Song พร้อมผล render

**Chosen:** `media/songs/{id}/cover.json` เก็บการตั้งค่า reel ของเพลงนั้นหนึ่งชุด (ช่วง ข้อความ พื้นหลัง เสียง) และ `media/songs/{id}/renders/` เก็บผลทุกครั้งแบบ `backend.renders`. แก้แล้ว render ใหม่ได้ ผลเก่าอยู่. ลบเพลง = cover และผล render หายด้วย; ระหว่าง render ลบเพลงไม่ได้ (`song_busy`).

**Why:** reel ทำจาก `analysis` ของเพลงโดยตรง เปลี่ยนช่วงแกะก็เปลี่ยน reel จึงอยู่ตามเพลงแบบข้อมูลที่สร้างต่อของ Temp clip (ADR-0021, ADR-0034); ผู้ใช้มีทางเดินเดียวจากเพลงไป reel ไม่มีรายการ reel แยก.

**Rejected:**
- Cover เป็น entity แยกใน `media/covers/` มีรายการและ tab ของตัวเอง — เพิ่มสองจอกับ tab โดยไม่มีใครขอ และต้องดูแลเพลงที่หายไปแล้ว
- เก็บการตั้งค่าใน `song.json` — แก้ schema ของ drum-notes โดยไม่จำเป็น; ไฟล์แยกให้ drum-notes ไม่ต้องรู้จัก reel
- ทำแบบบทเรียน (สำเนาทางเดียว ADR-0047) — บทเรียนถูกแก้ต่อจนไม่เหลือร่องรอยเพลง แต่ reel ไม่มีหน้าแก้โน้ต: มันคือเพลงนั้นเสมอ

**Details:**
- `cover.json` เขียน `write_atomic` ใต้ `songs.lock` ของ drum-notes (ไฟล์อยู่ใน folder เดียวกัน); ไม่มี lock ใหม่
- ภาพพื้นหลังของ reel คือ `cover-background.jpg` ใน folder เดิม (D8)
- `DELETE /songs/{id}` ของ drum-notes ลบทั้ง folder อยู่แล้ว; mp4 ที่ player เปิดอยู่บน Windows ค้างจน start ครั้งหน้าลบ folder ที่ไม่มี `song.json`
- Render job ลงทะเบียนใน `songs.song_jobs` เพื่อ `song_busy` แบบ Pick job (drum-notes D18)

**From:** change request · **Status:** active

## D3: reel เล่นการตีที่พบตามเวลาจริง ไม่ quantize ไม่มี BPM ท่อนสอน ป้าย หรือนับเข้า

**Chosen:** เสียงและภาพของ reel มาจาก `analysis.hits` ในช่วงที่เลือก ที่เวลาจริงของเพลง (ปัดเป็น sample ครั้งเดียว); ตัวนับจังหวะและเส้นห้องบนเลนมาจาก `analysis.beats` และ `downbeats`. จอมี หัวเรื่อง บรรทัดรอง ตัวนับจังหวะ ชุดกลองที่ไม้ตี วง L-R เลนโน้ตเลื่อนผ่าน playhead และคำบรรยายล่าง ตาม layout ของ video-gen (video-gen D12, D13); ไม่มีป้ายท่อน ไม่มีนับเข้า ไม่แสดง BPM ไม่มีชิ้นที่เน้น.

**Why:** เจ้าของ: "ต้องการแค่ reel วิดีโอที่เป็น animation ในการตี และ notes ที่ตี กับเสียงที่ออก … แบบต้นฉบับ"; quantize ลง 16 ช่องและเล่นซ้ำตาม BPM ทำให้ feel ของ fill จริงหาย และคือสิ่งที่เจ้าของบอกว่า "ไม่ใช่แบบนี้".

**Rejected:**
- สร้างบทเรียน 1 ท่อนจาก Groove แล้ว render ด้วย video-gen — ถูก quantize, จำกัด 4 ห้อง, มีนับเข้าและป้าย
- โน้ตห้าเส้นแบบคลิปอ้างอิงแทนเลนสามเลน — ต้องเขียนตัววาดโน้ตใหม่; เลนของ video-gen ให้ "โน้ตที่ตี + playhead" ครบตามที่ขอ

**Details:**
- ความแรง: `accent` = ชั้น `hard`, `normal` = `mid`, `ghost` = `soft` ตาม video-gen D13; หัวโน้ตตามความแรงเหมือนเดิม
- ตัวนับ 1–4 เปลี่ยนที่จังหวะจริง; ห้องที่มี 3 หรือ 5 จังหวะนับ 1–3 หรือ 1–5
- หางเสียง 1.5 วินาทีหลังจบช่วง ภาพค้าง ไม้พัก (video-gen D21)
- ไม่มีหน้าแก้โน้ตของ reel: โน้ตผิดคือผลของโมเดล (drum-notes D6); ผู้ใช้เลื่อนช่วงหรือแกะใหม่

**From:** change request · **Status:** changed by D25

## D4: timeline ของ reel สร้างใน `drum_cover` คืน `Timeline` ของ video-gen; เสียง ภาพ ตัวหนังสือ และคำสั่ง ffmpeg ใช้ของเดิม

**Chosen:** module `drum_cover.timeline` แปลง `analysis` กับช่วงของ reel เป็น `video_gen.timeline.Timeline` (การตี จังหวะ ช่วงเดียว ความยาว). `mixer.mix`, `frames.Scene`/`frame_at`, `lane`, `captions.ass_file` และคำสั่ง ffmpeg ของ `video_gen.render` ใช้ตามเดิมผ่าน Lesson ชั่วคราวหนึ่งท่อน (`lessons.unsaved`): หัวเรื่อง บรรทัดรอง คำบรรยาย พื้นหลังของ cover, ท่อนเดียวป้ายว่าง ไม่เน้นชิ้นใด, `bpm` ใช้แค่กำหนดความเร็วเลื่อนของเลน ไม่แสดง.

**Why:** ADR-0040 และ ADR-0041 กำหนดแล้วว่าทุกชั้นอ่านเวลาจาก `Timeline` ตัวเดียว; ตัววาดชุดสองไม่คุ้มและเสี่ยงเสียงกับภาพคลาด.

**Rejected:**
- ให้ `frames`/`captions` รับ "สคริปต์" ชนิดใหม่แทน Lesson — refactor สามไฟล์เพื่อผู้ใช้ที่สอง ทั้งที่ Lesson หนึ่งท่อนแทนได้พอดี
- render ด้วย `video_gen.render.render_jobs` เดิม — งานผูกกับ `lesson_id` และ folder ของบทเรียน

**Details:**
- prefactor ใน `video_gen.timeline`: `assemble(sounds, beats, spans, length_s)` เป็นทาง public ที่ `build` ของบทเรียนและ `drum_cover` ใช้ร่วม (round-robin และการเรียง)
- ~~prefactor ใน `video_gen.captions`~~ ตัดโดย D17: event ยาว 0 libass ไม่วาด
- `bpm` ของ Lesson ชั่วคราว = `round(60 / มัธยฐานช่วงห่างของจังหวะในช่วง)` จำกัด 40–240; จังหวะน้อยกว่า 2 → 120
- ช่วงเดียว `Span(0, end_s − start_s)`; `length_s` = ความยาวช่วง + 1.5
- เวลาของการตี = `hit.t − start_s` ปัดเป็น sample ที่ 44.1 kHz ใน `assemble`
- ขั้นเลขล้วนแยกจาก Render job เพื่อ test ด้วย `analysis` สังเคราะห์ (D13)

**From:** change request · **Status:** changed by D25

## D5: มือ L/R ของ reel เลือกจากกติกาของ drum-notes โดย quantize ชั่วคราว; โน้ตมือที่เกินสองต่อช่องยังมีเสียงแต่ไม่มีไม้

**Chosen:** เพื่อเลือกมือ การตีแต่ละตัวถูกปัดลงช่อง 16 ต่อห้อง (ห้องจาก `downbeats`) เฉพาะในขั้นนี้ แล้วใช้ `groove.trimmed` กับ `groove.with_hands` ของ drum-notes (D13) หามือ; เวลาที่เล่นและวาดยังเป็นเวลาจริง. โน้ตมือที่ `trimmed` ตัดออก (เกินสองมือในช่องเดียว) และโน้ตที่ชิ้นเดียวซ้ำช่องเดียว เล่นเสียงและมีหัวโน้ตตามปกติ แต่ไม่มีไม้ตี (`hand` = `null`).

**Why:** กติกามือมีอยู่แล้วและเจ้าของเคาะไว้ (drum-notes D29); สองมือวาดได้แค่สองชิ้น แต่เสียงต้องเป็นของเพลงครบ.

**Rejected:**
- ตัดโน้ตที่เกินสองมือออกจากเสียงด้วย — reel ต้องฟังเหมือนที่แกะได้
- กติกามือใหม่บนเวลาจริง (ระยะห่างเป็นวินาที) — กติกาสองชุดต้องดูแลสองที่ โดยผลต่างแค่ที่ขอบ

**Details:**
- ห้องสำหรับปัด: ช่วงระหว่าง downbeat ติดกัน; การตีก่อน downbeat แรกใช้ความยาวห้องแรกถอยหลัง หลัง downbeat สุดท้ายใช้ความยาวห้องสุดท้ายต่อไป; ไม่มี downbeat สองตัว (เพลง MIDI สั้น) → ห้องยาว 2 วินาทีจาก `start_s`
- ชิ้นเดียวซ้ำช่องเดียว: ตัวแรก (เวลาแรก) ได้มือ ตัวถัดไปไม่มีไม้
- ไม่มีรายการ `dropped` ให้ผู้ใช้: reel ไม่มีหน้าแก้โน้ต (D3)
- ต่างจาก video-gen D20 (บทเรียนตัดโน้ตที่ไม้ตีไม่ได้ออกทั้งเสียงและภาพ): บทเรียนเป็นโน้ตที่ผู้ใช้กรอก แก้ได้; reel คือเสียงของเพลงที่แกะ ตัดทิ้งไม่ได้

**From:** change request · **Status:** active

## D6: ช่วงของ reel อยู่ในช่วงแกะ ยาว 2–90 วินาที; ค่าตั้งต้นเริ่มที่ต้นห้องแรกที่มีการตี จบที่ท้ายช่วงแกะ

**Chosen:** `start_s` และ `end_s` ของ cover อยู่ใน `[analysis.start_s, analysis.end_s]` และ `2 ≤ end_s − start_s ≤ 90`. ค่าตั้งต้นเมื่อยังไม่เคยบันทึก: `start_s` = ต้นห้องที่พบตัวแรกที่มีการตี (ไม่มีการตีเลย → `analysis.start_s`; การตีแรกอยู่ก่อน downbeat แรก → เวลาการตีแรก), `end_s` = `analysis.end_s`. หน้า reel มีปุ่ม "เริ่มที่การตีแรก" ตั้ง `start_s` เป็นค่านี้.

**Why:** กรณีจริงของเจ้าของ (Yellow ของ DRUMMATE, ช่วง 0–30 มีกลองตั้งแต่ 11.5 วินาที) ห้องว่างห้าห้องทำให้ reel เริ่มด้วยความเงียบ; ค่าตั้งต้นต้องเริ่มที่กลอง.

**Rejected:**
- ตัดช่วงเงียบอัตโนมัติโดยไม่ให้แก้ — ผู้ใช้อาจต้องการจังหวะนับก่อนกลองเข้า
- ช่วงต่ำสุด 4 วินาทีเท่าช่วงแกะ — fill สั้น 2 วินาทีก็เป็น reel ได้

**Details:**
- แกะใหม่แล้วค่าที่เก็บไว้เกินช่วงใหม่ → `GET /cover` ดึงเข้าช่วง (`start_s` ≥ `analysis.start_s`, `end_s` ≤ `analysis.end_s`; สั้นกว่า 2 → ค่าตั้งต้นทั้งคู่) โดยไม่เขียนไฟล์; `PUT` ครั้งถัดไปบันทึกค่าที่เห็น
- จังหวะในช่วงก่อน downbeat แรกนับถอยหลังจาก downbeat นั้น (…, 3, 4 แล้ว 1) ต่ำสุด 1
- เพลง MIDI (ไม่มี `range`) ใช้ `analysis.start_s`/`end_s` ของไฟล์; ช่วงยาวกว่า 90 เลือกได้แค่ 90

**From:** change request · **Status:** active

## D7: เสียงของ reel เป็นกลองล้วนตั้งต้น; ผู้ใช้เปิดเสียงเพลงต้นฉบับเป็น backing ได้เองพร้อมคำเตือน

**Chosen:** `backing.on` ตั้งต้น `false`: reel มีแค่เสียงกลองจาก sample (video-gen D7). เปิด `true` → ffmpeg ผสม `audio.m4a` ช่วง `[start_s, end_s)` ที่ `backing.volume` (10–100, ตั้งต้น 35) ใต้เสียงกลอง ทั้งตอนฟังและตอน render; ข้างสวิตช์มีคำเตือนว่าเพลงต้นฉบับมีลิขสิทธิ์ แพลตฟอร์มอาจ claim ปิดเสียง หรือบล็อกคลิป. คลิปสอนของ video-gen ยังไม่มี backing เหมือนเดิม.

**Why:** เจ้าของ: "อาจจะมีพื้นหลังของเพลงบ้างก็ได้" และ brief เลือกกลองล้วนเป็นค่าตั้งต้นเพื่อเลี่ยง copyright claim โดยให้ผู้ใช้ตัดสินเอง.

**Rejected:**
- backing เปิดตั้งต้น — ทุก reel จะโดน claim ของสิ่งบันทึกเสียงทันที (legal 2)
- ไม่มี backing เลย (คง drum-notes D15 และ ADR-0045) — เจ้าของขอให้มีทางเลือก
- เสียงพื้นจากคลังเสียงแทนเพลง — คนละความต้องการ (เสียงบรรยากาศ ไม่ใช่เพลงที่ cover)

**Details:**
- เปลี่ยน drum-notes D15 และแทน ADR-0045 ด้วย ADR-0050: เสียงบันทึกของเพลงเข้าคลิปได้เฉพาะ reel ที่ผู้ใช้เปิดเองต่อ cover ค่าตั้งต้นปิด; เสียงกลองยังมาจาก `Timeline` ชุดเดียว (ADR-0041 ไม่ขัด: เพลงไม่ใช่โน้ต)
- การผสม: ทางเดียวใน numpy ตาม D17 (แทน `amix` ของคำสั่ง ffmpeg)
- ผล render บันทึก `backing` ใน json ของผล (ADR-0034)
- คำเตือนบนจอ: "เพลงต้นฉบับมีลิขสิทธิ์ แพลตฟอร์มอาจ claim ปิดเสียง หรือบล็อกคลิป เปิดเมื่อคุณมีสิทธิ์ใช้เสียงนี้" (legal 2)
- ตารางผลใน json ของผลใช้ `backing: {on, volume}` เดิมของ cover ตอน render

**Accepted risk:** การเผยแพร่ reel ที่มีเสียงบันทึกของเพลงเป็นสิทธิแต่ผู้เดียวของค่ายเพลง (legal 2 CONDITIONAL); แอปปิดเป็นค่าตั้งต้น เตือน และให้ผู้ใช้เลือกเอง ตามที่เจ้าของขอ.

**From:** change request · **Status:** active

## D8: พื้นหลังของ reel เป็นสีของแอป หรือภาพของผู้ใช้ ผ่าน module รับภาพที่ย้ายมาใช้ร่วม

**Chosen:** `background` = `color` (ตั้งต้น) หรือ `image` ตามกติกาของ video-gen D6, D36, D37: `check` ก่อน แล้ว `PUT` body ดิบ PNG/JPG ≤ 20 MB → หมุนตาม EXIF ครอป 1080×1920 เก็บ `cover-background.jpg`; ลบกลับเป็นสี; render เบลอและทำมืดแบบเดิม. โค้ดอ่าน ครอป และรับ upload ย้ายจาก `video_gen.backgrounds` ไป module ใช้ร่วม `backend.pictures` ที่รับ callback ตรวจและวางไฟล์จากผู้เรียก; `video_gen.backgrounds` เรียกมันแทน.

**Why:** brief ข้อ 2: สีของแอปเป็นค่าตั้งต้นและอัปโหลดภาพเองได้; ผู้ใช้ที่สองของโค้ดเดิม = ย้ายไปของใช้ร่วม (กติกา "Where shared code goes").

**Rejected:**
- copy โค้ดครอปมาใน `drum_cover` — สองสำเนาของกติกาเดียว

**Details:**
- routes: `POST /songs/{id}/cover/background/check`, `PUT /songs/{id}/cover/background?size=`, `DELETE /songs/{id}/cover/background`, `GET /songs/{id}/cover/background.jpg?v={updated_at}`
- ไฟล์ชั่วคราวใน `media/songs/.partial/` ของ drum-notes (ล้างตอน start อยู่แล้ว)
- หน้า reel มีคำเตือนสิทธิ์ภาพแบบ video-gen D23: "ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม"
- `BackgroundPicker` ของ video-gen ย้ายไป `components/ui/` รับ path ของ route เป็น prop

**From:** change request · **Status:** active

## D9: หลังแกะ หน้าเพลงบอกเมื่อช่วงไม่มีการตี หรือห้องแรก ๆ ว่าง และมีปุ่มเริ่มช่วงใหม่ที่การตีแรกแล้วแกะทันที

**Chosen:** เมื่อ Pick job จบ `done`: `hits` ว่าง → Alert เตือน "ไม่พบการตีกลองในช่วง {start}–{end} วินาที ลองเลื่อนช่วงไปที่กลองเริ่มเล่น"; มีการตีแต่ห้องที่พบตัวแรกว่าง → Alert "ห้อง 1–{k} ไม่มีการตี การตีแรกอยู่ที่ {t} วินาที" พร้อมปุ่ม "เริ่มช่วงที่การตีแรก" ซึ่งตั้งช่วงใหม่แล้วบันทึกและแกะใหม่ทันที (`PUT /range` แล้ว `POST /pick`).

**Why:** เจ้าของแกะ Yellow (DRUMMATE) ช่วง 0–30 แล้ว "ไม่เห็นมีอะไรเลย" เพราะ intro 11.5 วินาทีไม่มีกลอง ห้อง 1–5 ว่าง; หน้าว่างทำให้คิดว่าแอปพัง.

**Rejected:**
- Pick job หาจุดเริ่มกลองเองแล้วเลื่อนช่วงให้ — ผู้ใช้ไม่รู้ว่าช่วงที่ตั้งถูกเปลี่ยน; และต้องแกะช่วงที่ยาวกว่าที่ขอ
- แสดงแค่ตัวเลข "0 การตี" บนห้อง — เจ้าของเห็นแล้วแต่ไม่เข้าใจ

**Details:**
- ช่วงใหม่: `start` = ต้นห้องแรกที่มีการตี (การตีแรกอยู่ก่อน downbeat แรก → เวลาการตีแรก) ปัดลง 0.1 วินาที; `end` = `start` + ความยาวช่วงเดิม จำกัดที่ `duration_s`; สั้นกว่า 4 → `end` = `duration_s`
- คำนวณบนหน้าเว็บจาก `bars[].hits` และ `analysis.hits` ที่ `GET /songs/{id}` ให้อยู่แล้ว; ไม่แก้ API ของ drum-notes
- Alert อยู่เหนือส่วน "ผลแกะ" ของหน้าเพลง; หายเมื่อแกะใหม่
- ห้องว่างหมายถึง `hits` = 0 ในห้องที่พบตัวแรก; นับ `k` = จำนวนห้องติดกันจากห้องแรกที่ `hits` = 0

**From:** change request · **Status:** active

## D10: แกะโน้ตจากเสียงเป็นทางเดียว ไม่เทียบภาพโน้ตที่ขึ้นจอในคลิป cover ของคนอื่น

**Chosen:** reel ใช้ `analysis` จากเสียง (ADTOF และ Beat This!, drum-notes D6) หรือจากไฟล์ MIDI (drum-notes D10) เท่านั้น; ไม่อ่านโน้ตจากภาพของวิดีโอ.

**Why:** เจ้าของถามว่า "ลองดูใน video มันจะ note อยู่แล้ว ซึ่งจริงไม่ต้องแกะถ้าสามารถเทียบภาพได้". ตอบ: ทำได้แค่กับคลิปที่มีโน้ตบนจอ และโน้ตของแต่ละช่องคนละรูปแบบ (DRUMMATE เลื่อนแนวตั้งเป็นแถบสี, Your Turn โน้ตห้าเส้น) ต้องมีตัวอ่านภาพต่อรูปแบบที่ไม่มีโมเดลสำเร็จ; Song เก็บเสียงอย่างเดียว (ADR-0048) จึงต้องโหลดวิดีโอเพิ่ม; เสียงใช้ได้กับทุกต้นทางรวมเพลงจริงที่ไม่มีโน้ต.

**Rejected:**
- อ่านโน้ตจากเฟรมของคลิป cover (OCR หรือจับสีแถบโน้ต) — งานวิจัยต่อรูปแบบจอ ไม่มี library สำเร็จ และผิดกับช่องที่ใช้ภาพกลองจริง
- ใช้ภาพช่วยตรวจผลเสียง — สองทางต้องตรงกันเองอีกชั้น

**Details:**
- ช่องที่แจกไฟล์ MIDI ของโน้ต ใช้ทาง MIDI ของ drum-notes ได้แล้วโดยไม่ต้องแกะ
- เอกสารนี้คือคำชี้แจงที่ brief ขอ; ถ้าเจ้าของอยากลองในอนาคตเป็น feature ใหม่

**From:** change request · **Status:** active

## D11: หน้าเพลงมีส่วน "Reel cover" เหนือ "สร้างบทเรียน" เป็นทางหลัก; หน้า reel เป็นหน้าของ feature นี้ที่ `App` เลือกจาก hash

**Chosen:** หน้าเพลงหลังมี `analysis` แสดงส่วน "Reel cover" ก่อนส่วนสร้างบทเรียน: บรรทัด "ช่วงแกะ {start}–{end} วินาที · {n} การตี · render แล้ว {m} ครั้ง" กับปุ่มหลัก "ทำ reel cover" ไป `#/songs/{id}/cover`; ปุ่ม "สร้างบทเรียนกลอง" เป็นปุ่มรอง. `App` เลือก `CoverPage` ของ `features/drum-cover` เมื่อ hash เป็น `#/songs/{id}/cover` ก่อนส่งที่เหลือให้ `SongsPage`; tab ที่เน้นยังเป็น "แกะเพลง".

**Why:** reel คือสิ่งที่เจ้าของทำ (D1) จึงอยู่บนสุดและเป็นปุ่มหลัก; บทเรียนยังอยู่สำหรับคนที่อยากสอน (brief ข้อ 3). `App` เลือกหน้าเองเพื่อไม่ให้ `features/drum-notes` import `features/drum-cover`.

**Rejected:**
- ย้ายส่วนสร้างบทเรียนไปหน้าอื่น — เปลี่ยน drum-notes เกินที่ขอ
- ฝังการตั้งค่า reel ในหน้าเพลง — หน้ายาวเกิน และ render กับผลต้องมีที่ของตัวเอง

**Details:**
- `m` มาจาก `GET /songs/{id}/cover/renders` (จำนวน); ยังไม่มี cover → 0
- hash อื่นใต้ `#/songs/{id}/cover…` = หน้าเพลง
- จอแคบ: ปุ่มเป้ากด 44px ต่ำกว่า 640px ตาม drum-notes D28

**From:** change request · **Status:** active

## D12: ทางเลือกเล็กของ API และ Render job

**Chosen:** ข้อตกลงย่อยที่ builder จะต้องถาม ตัดสินตอน plan.

**Details:**
- **routes:** router `drum_cover` ไม่มี prefix: `/api/songs/{song_id}/cover…` (การตั้งค่า ฟัง render ผล ภาพ) และ `/api/covers/render`, `/api/covers/render/cancel` (งานล่าสุดของ tab); ทุก route ของ cover ตอบ `404` `not_found` เมื่อไม่มีเพลง และ `409` `no_analysis` เมื่อยังไม่แกะ
- **Render job:** `JobSlot` ของตัวเอง `drum_cover.render.render_jobs` ทีละงาน ไม่จอง GPU (video-gen D14) gate `gate_rows.drums`; state `rendering`/`done`/`failed`/`cancelled`, error `ffmpeg_failed`/`internal`; งานบอก `song_id` และ `title`
- **สำเนาก่อนตอบ:** copy `song.json`, `cover.json` และ `cover-background.jpg` เข้า `media/songs/.render/` ใต้ `songs.lock` ก่อนตอบ `202` (video-gen D33); `audio.m4a` อ่านที่เดิม เพราะ `song_busy` กันลบระหว่างงาน; `PUT /cover` ระหว่าง render ทำได้ ถึงงานถัดไป
- **ดิสก์:** `disk.require_free` ด้วย `length_s × 2 MB` (video-gen spec › Render job)
- **ผล:** `media/songs/{id}/renders/{name}.mp4|.srt|.json` ผ่าน `backend.renders`; json มี `song_id`, `title`, `length_s`, `start_s`, `end_s`, `picked_at`, `backing`, `created_at`; `.srt` หนึ่ง cue ทั้งคลิป (หัวเรื่อง บรรทัดรอง คำบรรยาย)
- **ตอน start:** ล้าง `media/songs/.render/` และ `.partial` ของทุก `renders/`
- **`GET /cover`:** ค่าที่เก็บ หรือค่าตั้งต้นเมื่อไม่มี `cover.json` (`saved: false`) พร้อม `length_s` และ `suggested_start_s` (D6)
- **`PUT /cover`:** ทับทั้งก้อน ตรวจตามตาราง spec › Data → `400` `invalid_request` มี `field`; `background` = `image` ต้องมี `cover-background.jpg`
- **ฟัง:** `POST /cover/listen` `{}` ผสมจากค่าที่บันทึก คืน `audio/wav` `Cache-Control: no-store`; gate `drum_kit` (+ `ffmpeg` เมื่อ backing เปิด) → `503` `not_ready`
- **ความยาว:** `end_s − start_s` > 90 ถูก `PUT` ปฏิเสธอยู่แล้ว; ฟังและ render ไม่มี `too_long`
- **หน้าเว็บ:** หน้า reel อ่าน `GET /covers/render` ตอนเปิดและ poll ทุก 1 วินาทีระหว่าง `rendering`; ผล render อยู่ท้ายหน้าเดียวกัน ไม่มีหน้าผลแยก

**From:** change request · **Status:** active

## D13: seam สามจุด: API ด้วย ffmpeg จริงและ `analysis` ที่เขียนเอง, timeline ของ reel ด้วยการตีสังเคราะห์, หน้าเว็บผ่าน `App`

**Chosen:** (1) `/api/songs/{id}/cover/*` และ `/api/covers/render` ผ่าน `TestClient` กับ ffmpeg จริง sample ปลอม (`fakes.write_drum_kit`) และเพลงที่มี `analysis` เขียนตรง (`written_song` ของ drum-notes); (2) `drum_cover.timeline.build` กับ `frames.frame_at` ด้วย `analysis` สังเคราะห์ รวม test เสียงตรงภาพ ≤ 1 เฟรม; (3) หน้าเพลงและหน้า reel ผ่าน `App` กับ fetch ปลอม.

**Why:** ทางนี้ไม่มีโมเดล (analysis มาจาก drum-notes แล้ว) จึง test ได้ด้วย ffmpeg จริงทั้งทางแบบ video-gen D15; ความตรงของเสียงกับภาพตัดสินที่ `Timeline` จุดเดียว.

**Rejected:**
- test ผ่าน Pick job ด้วย `FakeOnnxRunner` — ซ้ำกับ seam ของ drum-notes; reel เริ่มที่ `analysis`

**From:** change request · **Status:** active

## D14: สองจอสร้างตาม `ui-prompt.md` กับ design system เดิม ไม่รอ Figma

**Chosen:** หน้า reel และส่วนที่เพิ่มในหน้าเพลงสร้างจาก spec › Design และ `ui-prompt.md` ด้วย token และ component เดิม (`PageLayout`, `Alert`, `RefusedAlert`, `Labeled`, `ProgressBar`, การ์ด `rounded-2xl`, `buttonStyles`) ตามแบบ drum-notes D28; Source ของจอเป็น `pending` จนกว่าจะมีแบบ Figma ซึ่งถ้ามีเป็น change request.

**Why:** เจ้าของสั่ง "เริ่มทำ ticket 01 ต่อได้เลย ยังไม่ต้องรอ Figma (ใช้ ui-prompt.md เป็นสเปก)".

**From:** change request · **Status:** active

## D15: เป้าที่วัดได้

**Chosen:**
- reel 30 วินาที render จบใน ≤ 60 วินาทีบน Mac Apple Silicon (ตาม video-gen D14) — วัดมือตอน build
- ในคลิปที่ render: เฟรมแรกที่วงแหวนของโน้ตขึ้น กับจุดเริ่มเสียงของโน้ตนั้น ห่างไม่เกิน 1 เฟรม (test ใน Seams 1)
- render cover เดิมสองครั้ง (backing ปิด) ได้ `audio.wav` เหมือนกันทุก byte (video-gen D13)
- เจ้าของทำ reel จาก Yellow (DRUMMATE `Ssz69tFTS7Y`) ช่วง 11.5–30 วินาที (88 การตี) แล้วรับว่า "ใช่แบบนี้": ไม้ตรงเสียง โน้ตเห็น ไม่มี BPM และป้ายสอน
- หน้าเพลงหลังแกะ Yellow ช่วง 0–30 แสดงข้อความห้อง 1–5 ว่างและการตีแรก 11.5 วินาที (D9)

**Why:** ตัวเลขที่ build วัดได้ และข้อที่วัดไม่ได้ (หน้าตาถูกใจ) ยกให้เจ้าของ.

**From:** change request · **Status:** active

## D16: รับความเสี่ยง legal ข้อ 1–2 ที่ยังไม่ได้ยืนยัน ภายใต้กรอบไม่หารายได้

**Chosen:** เผยแพร่ reel cover (legal 1) ภายใต้ ADR-0017 และ ADR-0046 (ไม่หารายได้) โดยแสดงชื่อเพลงและศิลปินตั้งต้นและใช้แค่ท่อน ≤ 90 วินาที; backing (legal 2) ปิดเป็นค่าตั้งต้น เตือนบนจอ และบันทึกใน json ของผล ให้ผู้ใช้ที่เปิดเองรับความเสี่ยงของ claim บล็อก หรือปิดเสียง. ก่อนหารายได้ต้องตรวจทั้งสองข้อใหม่.

**Why:** โปรเจกต์ไม่หารายได้อยู่แล้ว; เจ้าของขอให้มีทางเลือก backing และ brief เลือกกลองล้วนเป็นค่าตั้งต้น.

**Rejected:**
- รอคำยืนยันทางกฎหมายก่อนสร้าง — ไม่มีแหล่งไทยที่ตอบเรื่อง cover ส่วนกลองสั้น ๆ และคลิปสอนของ video-gen รับความเสี่ยงแบบเดียวกันแล้ว (video-gen D25)

**Accepted risk:** legal ข้อ 1 UNVERIFIED ว่า cover ส่วนกลอง ≤ 90 วินาทีเป็น "บางตอนตามสมควร" ตามมาตรา 33; legal ข้อ 2 UNVERIFIED ผลจริงของแพลตฟอร์มต่อคลิปที่มีเสียงบันทึก — ยอมรับเพราะไม่หารายได้ ผู้ใช้เปิด backing เองโดยเห็นคำเตือน และเปลี่ยนค่าตั้งต้นได้ทุกเมื่อ.

**From:** legal · **Status:** active

## D17: เสียงของ reel มีทางเดียว `drum_cover.audio.reel_wav` ผสมใน numpy; ของเดิมใน video-gen เปลี่ยนแค่ที่ไม่เปลี่ยนพฤติกรรม

**Chosen:** wav ของ reel ทำที่ฟังก์ชันเดียว `drum_cover.audio.reel_wav(project, song, cover, timing)` ซึ่งทั้ง "ฟัง" และ Render job ใช้: wav กลองจาก `mixer.mix`; backing เปิด → `ffmpeg.run_capture` ถอด `audio.m4a` ช่วง `[start_s, end_s)` เป็น `f32le` 44.1 kHz stereo ออก stdout, numpy บวกใต้กลองที่ `volume / 100` แล้วปรับ peak ของผลรวมเป็น −1 dBFS แบบ `mixer` และเขียน wav 16-bit ด้วย `soundfile`. Render job เขียนผลนี้เป็น `audio.wav` แล้วใช้คำสั่ง ffmpeg เดิมของ `video_gen.render` (`_command` ไม่แก้). ของเดิมที่เปลี่ยน: `video_gen.timeline.assemble` (เพิ่ม public, `build` ให้ผลเดิม) และการย้ายโค้ดรับภาพไป `backend.pictures` กับ `BackgroundPicker` ไป `components/ui` (test เดิมผ่านโดยไม่แก้ assertion); ไม่แก้ `captions`.

**Why:** red team (Skeptic, Breaker): ฟังกับ render ผสมสองทางจะได้เสียงต่างกัน; wav จาก pipe ของ ffmpeg ไม่มีขนาดใน header; `amix normalize=0` บน peak −1 dBFS ทำให้ clip; `-map "[a]"` ทำให้ไม่มีภาพถ้าลืม `0:v`. ผสมใน numpy แก้ทั้งสี่ข้อ. เจ้าของสั่ง "ห้ามแก้หรือลบ feature เหล่านั้น ให้ต่อยอด" จึงเปลี่ยนเฉพาะที่ผลเดิมไม่เปลี่ยน ตามกติกา "Where shared code goes" ของ `fastapi-api`.

**Rejected:**
- `amix` ใน `filter_complex` ของคำสั่ง render และ `run_capture` `-f wav -` ตอนฟัง (D7 เดิม) — สองทาง, header ผิด, clip
- ไม่แตะ video-gen เลย (copy round-robin และโค้ดครอปภาพ) — สองสำเนาของกติกาเดียว
- prefactor `captions` ให้ช่วงยาว 0 ไม่มี event — event ที่เริ่มเท่ากับจบ libass ไม่วาด; test ภาพใน Seams 2 พิสูจน์แทน

**Details:**
- ฟังไม่เขียนไฟล์ชั่วคราว (ffmpeg อ่าน m4a ออก stdout); หน้าเว็บปิดปุ่ม "ฟัง" ระหว่างรอคำตอบ
- ผลรวมยาวเท่า wav กลอง (`timing.samples`); เสียงเพลงสั้นกว่า (ท้ายเพลง) เติมศูนย์
- backing ปิด → ผลคือ `mixer.mix` ตรง ๆ (byte เดียวกันทุกครั้ง D15)
- เปลี่ยน D4 Details (ตัด prefactor captions) และ D7 Details (ffmpeg `amix`)

**From:** red team · **Status:** active

## D18: หน้า reel บอกสิ่งที่เปลี่ยนใต้มือผู้ใช้: ช่วงไม่มีการตี ช่วงที่ถูกดึงเข้า backing ที่ใช้ไม่ได้ และผล render ที่เก่ากว่าผลแกะ

**Chosen:**
- ช่วงของ reel มี 0 การตี → Alert "ช่วงนี้ไม่มีการตีกลอง เลื่อนช่วงหรือกด เริ่มที่การตีแรก" และปุ่ม "ฟัง" กับ "render reel" กดไม่ได้ (หน้าเว็บ; API ไม่ปฏิเสธ)
- `GET /cover` มี `adjusted: true` เมื่อค่าที่เก็บถูกดึงเข้าช่วง → Notice "ช่วงแกะเปลี่ยน ช่วงของ reel ถูกปรับเป็น {start}–{end} วินาที" และฟอร์มเป็น "ยังไม่บันทึก"
- `GET /cover` มี `has_audio`; `false` (เพลง MIDI) → ตัวเลือก "กลอง + เพลงต้นฉบับ" กดไม่ได้พร้อมข้อความ "เพลงจาก MIDI ไม่มีเสียงต้นฉบับ"; `400` ของ D7 เหลือเป็นตัวกันฝั่ง server
- ใต้ช่อง "หัวเรื่อง" มีคำใบ้ "ค่าตั้งต้นมาจากชื่อคลิปและช่อง แก้เป็นชื่อเพลงและศิลปิน" (legal 1: ใส่ชื่อเพลงและศิลปิน)
- การ์ด "ช่วงของ reel" มีบรรทัด "อยากได้ท่อนอื่น? แกะช่วงใหม่ที่หน้าเพลง" ลิงก์ `#/songs/{id}`
- แถวผล render บอกช่วง `{start_s}–{end_s}` วินาที และป้าย "แกะใหม่แล้ว" เมื่อ `picked_at` ของผลไม่ตรง `analysis.picked_at` (ADR-0034)

**Why:** red team (Advocate, Successor): ทั้งหกจุดเป็นที่ผู้ใช้ "ไม่รู้ว่าเกิดอะไร" แบบเดียวกับห้องว่างที่ D9 แก้; ค่าตั้งต้นของหัวเรื่องคือชื่อคลิปของ DRUMMATE ไม่ใช่ชื่อเพลง (drum-notes D4).

**Rejected:**
- API ปฏิเสธ render ที่ไม่มีการตี — backing เปิดกับช่วงที่มีแต่เพลงยังเป็นคลิปได้ ให้หน้าเว็บกันกรณีปกติพอ
- ตั้งค่าตั้งต้นของบรรทัดรองเป็น "{ช่อง} · drum cover" — เดาชื่อศิลปินจากชื่อช่องไม่ได้

**From:** red team · **Status:** active

## D19: กรณีขอบของช่วงและโหมด

**Chosen:**
- เพลงที่แกะโหมดทำนอง (`analysis.mode` = `melody`): reel เล่นการตีที่พบตามจริง (snare ล้วน) ไม่เติม kick/ไฮแฮทแบบบทเรียน (drum-notes D14 เติมเฉพาะตอนสร้างบทเรียน); หน้า reel บอก "เพลงนี้แกะโหมดทำนอง reel มีแต่สแนร์"
- ค่าตั้งต้นที่สั้นกว่า 2 วินาที (การตีแรกอยู่ใน 2 วินาทีท้ายช่วงแกะ) → `start_s` = `analysis.end_s − 2` (ไม่ต่ำกว่า `analysis.start_s`); ดึงเข้าช่วงที่สั้นกว่า 2 ใช้กติกาเดียวกัน
- ปุ่ม "เริ่มช่วงที่การตีแรก" (D9) ใกล้ท้ายเพลง: `end` = `min(duration_s, start + ความยาวเดิม)`; ยังสั้นกว่า 4 → `start` = `max(0, duration_s − 4)`
- Alert "ห้อง 1–{k} ไม่มีการตี" ขึ้นเมื่อ `k` ≥ 1 และการตีแรก ≥ ท้ายห้อง `k` เท่านั้น: การตีก่อน downbeat แรกไม่ทำให้ขึ้น
- ช่วงที่ไม่มี hits เลยในเพลง (`hits` ว่าง): ส่วน "Reel cover" บนหน้าเพลงยังแสดง "0 การตี" และปุ่มยังพาไปหน้า reel ที่ D18 กันฟังและ render

**Why:** red team (Tester): กรณีเหล่านี้ไม่มีผลที่คาดไว้ใน spec; builder ต้องถาม.

**From:** red team · **Status:** active

## D20: Render job ของ reel รันพร้อมงานอื่นได้; เป้าเวลาวัดตอนรันเดี่ยว

**Chosen:** slot ของ reel แยกจาก Render job ของสอนกลองและ Pick job (D12): สามงานรันพร้อมกันได้ใน process เดียว (ADR-0010) แย่ง CPU กัน; เป้า ≤ 60 วินาทีของ D15 วัดเมื่อ reel รันเดี่ยว.

**Why:** red team (Breaker): ไม่มีคำตอบว่ารันพร้อมกันได้ไหม. ใช้ slot ร่วมกับ video-gen ต้องแก้ `DrumRenderJobs` ของ video-gen (D17) และผู้ใช้คนเดียวไม่ค่อยกดสองงานพร้อมกัน.

**Rejected:**
- ใช้ slot ร่วมกับ Render job ของสอนกลอง — แก้ video-gen และ `busy` ต้องรู้จักสองชนิดงาน

**From:** red team · **Status:** active

## D21: ทางเลือกเล็กจาก red team (Builder)

**Chosen:**
- **ห้องสำหรับเลือกมือ** มาจาก `analysis.downbeats` ทั้งหมด ไม่ใช่เฉพาะในช่วงของ reel: ก่อนตัวแรกขยายด้วยความยาวห้องแรก หลังตัวสุดท้ายด้วยความยาวห้องสุดท้าย; ห้อง 2.0 วินาทีเหลือแค่ `analysis` ที่เขียนตรงด้วย downbeat น้อยกว่า 2 (`songs.checked_analysis` ไม่ยอมอยู่แล้ว) (D5)
- **`backend.pictures`:** `checked_size(size, ...)` ตรวจขนาด (`413` 20 MB) และ `async receive(body, partial, expected, place) -> T`: รับ body ลง `partial` (ผู้เรียกให้ path ใต้ `.partial/` ของตัวเอง), อ่านด้วย Pillow (`415` `unsupported_image`), หมุน EXIF ครอป 1080×1920 เขียน jpg ข้าง `partial` แล้วเรียก `place(jpg) -> T` ของผู้เรียก (วางไฟล์ใต้ lock ของตัวเองและคืนค่าตอบ) และลบไฟล์ชั่วคราวทุกทาง; ผู้เรียกตรวจ idle และดิสก์เอง. `video_gen.backgrounds` เรียกมัน ผลและ test เดิมไม่เปลี่ยน
- **`BackgroundPicker` + `useBackground`** ย้ายไป `components/ui/` และ `lib/useBackground.ts` รับ `paths` (`check`, `put`, `delete`, `image`) และ `apply(body: unknown)` แทน `Lesson`; หน้าบทเรียนส่ง path เดิมของตัวเอง
- **`song_busy` ของ route ภาพ cover:** `drum_cover` ตรวจงานของตัวเองก่อน → `409` `song_busy` "กำลัง render reel ของเพลงนี้อยู่"; แล้ว `songs.require_idle` ของ drum-notes (Pick job). `DELETE /songs/{id}` ระหว่าง render ใช้ข้อความเดิมของ drum-notes ("กำลังแกะเพลงนี้อยู่") — ไม่แก้ drum-notes (D17); ยอมรับข้อความกว้าง
- **lock:** ลำดับ `slot ของ reel` → `songs.lock`; ไม่มี lock ใหม่

**Why:** red team (Builder) ชี้จุดที่ builder ต้องถาม; spec เขียน `downbeats < 2` อ่านได้สองแบบ.

**From:** red team · **Status:** active

## D22: ทางเลือกเล็กตอน build ticket 01

**Chosen:**
- ส่วน "Reel cover" บนหน้าเพลงเป็น component ของ drum-notes (`ReelCover` + `useReelRenders`) ที่รู้จัก reel ผ่าน HTTP (`GET …/cover/renders`) และ `reelHash` เท่านั้น ไม่ import `features/drum-cover` (ADR 0052); ปุ่ม "สร้างบทเรียนกลอง" เป็นปุ่มรอง (D11)
- `drum_cover.render` เรียก `video_gen.render._command` ตรง (ไม่แก้ ไม่ย้าย, D17) และใช้ `AUDIO`, `TEXT`, `BYTES_PER_SECOND` ของมัน; `.srt` ของ reel เป็น cue เดียวทั้งคลิปจาก `subtitles.srt_file` เอง (`captions.srt_file` จะมี cue ยาว 0 ของช่วงนับเข้า)
- ฟอร์มหน้า reel: "ยังไม่บันทึก" = แก้แล้ว หรือ `adjusted`; cover ที่ยังไม่เคยบันทึกไม่ถามก่อนออก แต่ "ฟัง"/"render reel" บันทึกก่อนเสมอ; ช่วงผิดกติกาบนหน้า → ข้อความ `RANGE_RULE` ที่ช่อง ไม่ส่ง `PUT`
- ไม่มีการ์ดพื้นหลังใน ticket 01 (ticket 02); `background` ที่ส่งกลับไปคือค่าที่เก็บ
- `fakes.written_song` (ย้ายจาก test ของ drum-notes) รับ `hits`, `beats`, `start_s`, `song_id`, `title`, `audio`; `fakes.song_m4a` ทำ `audio.m4a` ปลอมด้วย `lavfi`
- วัดเวลา render: reel 30 วินาที (การตี 270 ตัว) 12.7 วินาทีบน Mac ของเจ้าของ ด้วย sample ปลอม (D15)

**Why:** เลือกตามกติกาและโค้ดรอบข้าง ไม่เปลี่ยนสิ่งที่ spec สัญญา.

**From:** build ticket 01 · **Status:** active

## D23: ทางเลือกเล็กตอน build ticket 02

**Chosen:**
- `backend.pictures` ถือขนาด 20 MB ข้อความ และการครอป; `video_gen.backgrounds.MAX_BYTES` ชี้ไปที่ค่าเดียวกัน (test เดิมใช้ชื่อนี้) และ log หลัง `place` สำเร็จ
- ไฟล์ชั่วคราวของภาพ cover อยู่ใน `media/songs/.partial/` ชื่อ `cover-background.{hex}.tmp` ไม่ขึ้นต้นด้วย song id (Song import ลบ `{song_id}.*` ใน folder เดียวกัน)
- `PUT`/`DELETE` ภาพของ cover ที่ยังไม่เคยบันทึก บันทึก cover ด้วยค่าตั้งต้น (ดึงเข้าช่วงแล้ว) พร้อม `background` ใหม่; ข้อความอื่นที่กำลังพิมพ์บนหน้าอยู่ต่อ ฟอร์มรับแค่ `background` ใหม่
- `GET …/cover/background.jpg` ไม่มีภาพ → `404` "ยังไม่มีภาพพื้นหลัง"
- Alert ของหน้าเพลง (D9) แสดงทุกครั้งที่มี `analysis` (ไม่ใช่แค่ตอนงานเพิ่งจบ) จนกว่าแกะใหม่; ห้องว่าง 1 ห้องเขียน "ห้อง 1 ไม่มีการตี …"; เพลง MIDI ไม่มีปุ่ม (ไม่มีช่วงให้เลื่อน); `PickSection` key ตามช่วงที่บันทึก เพื่อให้ช่องแสดงช่วงใหม่หลังกดปุ่ม
- ปุ่ม "เริ่มช่วงที่การตีแรก" เริ่มที่**ต้นห้องแรกที่มีการตี** ตาม D9 Details (ตัวอย่าง 11.5 ใน Seams 3 คือกรณีที่การตีแรกตรงต้นห้อง); การตีก่อน downbeat แรกไม่เข้ากรณีนี้
- cover ที่เก็บ `image` แต่ภาพหาย → `GET` ตอบ `color` (บันทึกครั้งถัดไปไม่โดนปฏิเสธ); `PUT`/`DELETE` ภาพเขียน `cover.json` ก่อนวางหรือลบไฟล์
- การ์ดพื้นหลังของหน้า reel ใช้ `BackgroundPicker` ร่วมกับหน้าบทเรียน ("สีของแอป", "เลือกภาพ", "ลบภาพ") แทนคำใน ui-prompt ("สีเข้มของแอป"/"ภาพของฉัน"/"เปลี่ยนภาพ") — component เดียวคำเดียว (D14)

**Why:** ตามโค้ดเดิมของ video-gen และ drum-notes; ไม่เปลี่ยนสิ่งที่ spec สัญญา.

**From:** build ticket 02 · **Status:** active

## D24: ความดังกลองแยกจากเพลง: `drums` `{on, volume}` คู่กับ `backing`; ผสมแล้วลดเฉพาะเมื่อเกิน −1 dBFS

**Chosen:** `cover.json` มี `drums: {on, volume}` ทรงเดียวกับ `backing` — `on` ตั้งต้น `true` (ปิด = mute กลอง), `volume` จำนวนเต็ม 10–100 ตั้งต้น 100. เสียงของ reel = กลอง × `drums.volume/100` (เมื่อ `on`) + เพลง × `backing.volume/100` (เมื่อ `on`); peak ของผลรวมเกิน −1 dBFS → ลดลงมาที่ −1 dBFS, ไม่เกิน → คงไว้ (ไม่ดันขึ้น). ปิดทั้งกลองและเพลง → `400` `invalid_request` field `drums.on`. ผล render บันทึก `drums` ใน `.json` คู่ `backing`.

**Why:** เจ้าของขอ (Telegram): "เพิ่มปรับความดังกลอง" แยกสไลเดอร์กลองกับเพลง mute ได้ และบันทึกค่าในผล render. ถ้ายัง normalize ขึ้นถึง −1 dBFS เสมอ สไลเดอร์กลองตอนกลองล้วนจะไม่มีผลเลย จึงลดอย่างเดียว. เลือกใน auto mode ตามตัวเลือก (Recommended).

**Rejected:**
- สไลเดอร์อัตราส่วนกลอง/เพลงตัวเดียว — mute กลองแยกไม่ได้ และเจ้าของขอสองสไลเดอร์
- หน่วย dB — ช่องเดิมของเพลงเป็น 10–100 อยู่แล้ว ใช้แบบเดียวกัน
- ปิดทั้งสองแล้วได้คลิปเงียบ — ไม่มีใครต้องการ reel เงียบ; กันไว้ที่ฟอร์ม

**Details:**
- `drums.on` `true` และ `volume` 100 และ backing ปิด → wav ของ `mixer.mix` ตรง ๆ byte เดิม (D15 ยังจริง)
- กลองล้วน volume < 100 → wav ของ mixer คูณ `volume/100` แล้วปัด 16-bit ด้วย numpy (เหมือนกันทุกครั้ง)
- กลองปิด backing เปิด → เพลงล้วนของช่วง × `backing.volume/100`; ไม่เรียก `mixer.mix`; ภาพยังวาดการตีครบ
- `cover.json` เก่าที่ไม่มี `drums` → อ่านเป็น `{on: true, volume: 100}` (`version` คง 1); `.json` ของ render เก่าที่ไม่มี `drums` → `GET …/renders` ตอบ `{on: true, volume: 100}`
- gate ไม่เปลี่ยน: ฟังและ render ยังต้องมี sample (`drum_kit`) แม้กลองปิด — กติกาเดียว ไม่มีกรณีพิเศษ
- หน้า reel การ์ด "เสียง": บรรทัด "กลอง" มีสวิตช์ "ปิดเสียงกลอง" กับสไลเดอร์ "ความดังกลอง" 10–100; ตัวเลือก backing เดิมคงอยู่; ปิดทั้งคู่ → ข้อความที่การ์ด ปุ่ม "ฟัง"/"render reel" กดไม่ได้; แถวผล render มีป้าย "กลอง {v}%" เมื่อไม่ใช่ 100 และ "ไม่มีเสียงกลอง" เมื่อปิด

**From:** change request · **Status:** active

## D25: ภาพของ reel เป็นของ `drum_cover` เอง ออกแบบให้อ่านว่าตีอะไรได้ทันที ไม่อิงคลิปต้นฉบับ; คลิปสอนของ video-gen ไม่เปลี่ยน

**Chosen:** reel วาดด้วย `drum_cover.frames` และเขียนตัวหนังสือด้วย `drum_cover.captions` ของ feature นี้ ตาม [reel-picture-sketch.md](reel-picture-sketch.md) (D26). ยังเป็น Pillow ส่ง rgb24 + ASS (ADR-0040) และอ่านเวลาจาก `Timeline` ที่ `drum_cover.timeline.build` สร้าง (ADR-0041, 0051). คลิปสอนกลองของ video-gen ใช้ภาพเดิมไม่แตะ (video-gen D12, D13 ยังใช้กับบทเรียน).

**Why:** เจ้าของบอก "ตัวกลอง UI ดูไม่ชัดเจน" และ "ถ้าทำได้โดยไม่อิงตัวคลิปต้นฉบับก็น่าจะทำได้". ภาพเดิม (video-gen D12: ตำแหน่ง สี ขนาดตามคลิปอ้างอิง) มีชิ้นทับกัน (กระเดื่องบัง snare และทอม), ไม่มีชื่อชิ้น, ทอมสองใบสีเดียวกัน, crash กับ ride สีเดียวกัน, เลนโน้ต 3 เลนรวมหลายชิ้น, วงแหวนแดงชนกับสีกระเดื่อง, ไม้สองข้างสีเดียวกันไขว้กัน. ตีความคำของเจ้าของว่า "ออกแบบใหม่ได้ทั้งหมดเพื่อความชัด" — เลือกใน auto mode ตามตัวเลือก (Recommended).

**Rejected:**
- แก้ `video_gen.frames`/`kit` ที่ใช้ร่วม — เปลี่ยนคลิปสอนที่เจ้าของไม่ได้ขอ และขัด D17 (video-gen แก้เฉพาะที่ผลเดิมไม่เปลี่ยน)
- ปรับสีและขนาดของภาพเดิมนิดหน่อย — ชิ้นทับกันและเลนรวมชิ้นยังอยู่ ซึ่งเป็นต้นเหตุหลักที่อ่านไม่ออก
- ภาพกลองแบบ 3D/มุมเฉียงใหม่ — มุมเฉียงทำให้ชิ้นซ้อนกันเสมอ; มุมบนไม่ทับและติดป้ายได้

**Details:**
- เปลี่ยน D3 ส่วน "layout ของ video-gen" และ D4 ส่วน "frames/lane/captions ใช้เดิม": ภาพและตัวหนังสือของ reel ย้ายมาเป็นของ feature นี้; `timeline`, `mixer`, `ffmpeg`, `_command`, `subtitles`, `renders` ยังใช้ของเดิม
- ใช้ของ video-gen ที่ไม่ผูกกับหน้าตา: `frames.FPS`, `frames.frame_count`, `frames.WIDTH/HEIGHT`, พื้นหลัง (`frames._background` → prefactor เป็น `frames.background_image` ชื่อใหม่ ผลเดิม), จังหวะการขยับไม้ (`_tip_before` → prefactor เป็น `frames.stick_tip(times, targets, rest, t)` ผลเดิม), `captions` ของสไตล์ข้อความ (`_style`, `ass_color`, หัวเรื่อง/บรรทัดรอง/คำบรรยาย) — test เดิมของ video-gen ต้องผ่านโดยไม่แก้ assertion
- `drum_cover.render` เรียก `drum_cover.frames.Scene`/`frame_at` และ `drum_cover.captions.ass_file` แทนของ video-gen; Lesson ชั่วคราว (spec › Timeline ของ reel ข้อ 7) ยังใช้เพื่อ `bpm` (ความเร็วเลน) และข้อความ

**From:** change request · **Status:** active

## D26: หน้าตาของภาพ reel: ชุดกลองมุมบนไม่ทับกัน ติดชื่อทุกชิ้น เลนละชิ้น ไม้สองสี ตัวนับห้อง

**Chosen:** ตาม [reel-picture-sketch.md](reel-picture-sketch.md):
- **ชุดกลอง** มุมบน (top-down) วงกลมแยกไม่ทับกัน ขนาดตามชิ้นจริง (กระเดื่องใหญ่สุด ไฮแฮทเล็กกว่าฉาบ) ชื่อชิ้นภาษาอังกฤษตัวใหญ่ตรงกลางทุกชิ้น (`HI-HAT`, `CRASH`, `RIDE`, `TOM 1`, `TOM 2`, `SNARE`, `FLOOR`, `KICK`, `PEDAL`)
- **สี** แต่ละชิ้นสีต่างกันแปดสี (ไฮแฮททั้งสามแบบสีเดียว); ตอนพัก เติม 30 % ขอบเต็ม; ตอนตี เติมเต็ม ขอบขาว ขยาย 1.12 เท่าแล้วหดกลับใน 0.15 วิ — ไม่มีวงแหวนแดง
- **ไม้** สองสี: ซ้าย (L) ขาว ขวา (R) ชมพู `#FF4FD8` หัวไม้มีตัว L/R; ตอนตีมีป้ายมือ L/R สีของมือที่มุมขวาบนของชิ้นที่ถูกตี 0.15 วิ
- **เลนโน้ต** หนึ่งเลนต่อชิ้นที่มีใน reel เท่านั้น เรียงจากบนลงล่างตามลำดับชุดกลอง ชื่อชิ้นสีของมันที่หัวเลน; หัวโน้ตสีของชิ้น รูปตามชนิด (กลอง = วงกลม, ไฮแฮทปิด = X, ไฮแฮทเปิด = X ในวง, ฉาบ = เพชร, PEDAL = X เล็ก, KICK = วงกลมใหญ่) มีตัว L/R สีมือในหัวโน้ตของมือ; accent ใหญ่ 1.25 เท่าขอบขาว; ghost จาง 50 % เล็ก 0.8 เท่า
- **ตัวนับ** มุมขวาบน "ห้อง {n}" กับจุดจังหวะ 4 จุด (จุดของจังหวะที่เล่นสว่าง); เส้นห้องในเลนหนาขึ้นมีเลขห้องเล็กเหนือเลน
- หัวเรื่อง บรรทัดรอง คำบรรยายล่าง ที่เดิม (video-gen captions)

**Why:** แต่ละข้อแก้สิ่งที่อ่านไม่ออกใน D25 ตรงตัว: ชิ้นไม่ทับ + ชื่อ = รู้ว่าชิ้นไหน; สีไม่ซ้ำ = แยกทอม/ฉาบ; ไม้สองสี + ป้ายมือ = รู้ว่ามือไหน; เลนละชิ้น = อ่านโน้ตได้โดยไม่ต้องจำรูปหัว; ตัวนับห้อง = รู้ว่าอยู่ห้องไหน. เลือกใน auto mode ตามตัวเลือก (Recommended).

**Rejected:**
- ชื่อชิ้นภาษาไทย — มือกลองไทยเรียกชิ้นเป็นภาษาอังกฤษอยู่แล้ว และสั้นกว่า
- เลนแนวตั้งโน้ตตกลงแบบเกม — กินพื้นที่ชุดกลอง และเลนแนวนอนอ่านเหมือนโน้ตกลอง
- เลนครบสิบชิ้นเสมอ — ชิ้นที่ไม่เล่นทำให้แถวเล็กลงโดยไม่มีประโยชน์

**Details:** พิกัด ขนาด สี และกติกาความสูงแถวอยู่ใน sketch; เปลี่ยนตัวเลขได้ตอน build เมื่อภาพจริงอ่านยาก แต่กติกาข้างบนต้องคงอยู่ (บันทึกเป็น D ของ build).

**From:** change request · **Status:** active

## D27: เป้าที่วัดได้ของ change request

**Chosen:**
- กลองล้วน volume 100 ได้ `audio.wav` เดิมทุก byte (D15); volume 50 → peak ห่างจาก volume 100 −6.0 dB ± 0.1; กลองปิด + backing → wav ไม่มีเสียงกลอง (เทียบกับเพลงล้วน)
- เสียงตรงภาพ ≤ 1 เฟรม วัดแบบเดิม (Seams 1) แต่ดูสีเติมเต็มของชิ้นที่ถูกตีแทนวงแหวนแดง
- reel 30 วินาที render ≤ 60 วินาทีบน Mac (D15) ด้วยภาพใหม่
- เจ้าของดู reel Yellow 11.5–30 ด้วยภาพใหม่แล้วบอกได้ว่าแต่ละโน้ตตีชิ้นไหนมือไหน (แทนข้อเช็คของ D15 บนภาพเดิม)

**Why:** ทำให้ "ปรับความดัง" และ "ชัดขึ้น" ตรวจได้ทั้งในเทสต์และด้วยตาเจ้าของ.

**From:** change request · **Status:** active

## D28: ทางเลือกเล็กตอน build ticket 03

**Chosen:**
- `PUT /cover` ต้องส่ง `drums` ทุกครั้ง ทรงเดียวกับ `backing` (ไม่มีหรือ `on` ไม่ใช่ boolean → `400` field `drums.on`); ค่าตั้งต้น `{on: true, volume: 100}` ใช้เฉพาะตอนอ่าน `cover.json` และ `.json` ของ render ที่เขียนก่อน D24
- ข้อความ volume ผิด: "ความดังกลองต้องเป็นจำนวนเต็ม 10–100" (แบบ "ความดังเพลง…" เดิม); ทั้งสองตรวจด้วย `_sound` ตัวเดียว; `Drums` เป็น model แยกจาก `Backing` เพราะมีค่าตั้งต้นสำหรับไฟล์เก่า
- `cover.used(check_sound=…)` (ชื่อเดิม `check_backing`): ฟังและ render ปฏิเสธ cover ที่แก้มือจนเงียบ (`drums.on`) และ backing ของเพลง MIDI; การเปลี่ยนภาพพื้นหลังไม่ตรวจทั้งสองข้อ
- `reel_wav` อ่าน wav ของ mixer เป็น int16 แล้วหาร 32767 (กลับเป็น 16-bit ได้ค่าเดิมพอดี) แทน float32 ÷ 32768 เดิม; backing เปิดจึงต่างจากก่อน ≤ 1 LSB
- test "never clips" ใช้ `song_m4a(volume=16)` (sine ของ `lavfi` ถอดแล้ว peak ≈ 0.09 ต่อ 1.0) เพราะ D24 ไม่ดันขึ้นแล้ว เพลงต้องดังพอให้ผลรวมเกิน −1 dBFS จริง
- หน้า reel: "ความดังกลอง" เป็น `input type="range"` 10–100 step 1 พร้อมตัวเลข "{v}%"; "ความดังเพลง" คงช่องตัวเลขเดิม; สวิตช์ "ปิดเสียงกลอง" (checked = ปิด) ใช้ `Switch` ที่ย้ายจาก `spoil-maker/VideoSettings` ไป `components/ui/Switch` (ผู้ใช้คนที่สอง ตาม `vite-react-web` › Where shared code goes; ผลเดิม); ขณะปิดทั้งคู่ ข้อความ `SILENT` ที่การ์ดเสียง ปุ่ม "บันทึก" ยังกดได้ (backend ตอบ `drums.on` ที่ช่องเดียวกัน); ป้าย "กลอง {v}%"/"ไม่มีเสียงกลอง" สไตล์เดียวกับ "มีเพลงต้นฉบับ"

**Why:** ตามโค้ดและกติกาเดิมของ `backing` (D7, D17); ไม่เปลี่ยนสิ่งที่ spec สัญญา.

**From:** build ticket 03 · **Status:** active
