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

**From:** change request · **Status:** active

## D4: timeline ของ reel สร้างใน `drum_cover` คืน `Timeline` ของ video-gen; เสียง ภาพ ตัวหนังสือ และคำสั่ง ffmpeg ใช้ของเดิม

**Chosen:** module `drum_cover.timeline` แปลง `analysis` กับช่วงของ reel เป็น `video_gen.timeline.Timeline` (การตี จังหวะ ช่วงเดียว ความยาว). `mixer.mix`, `frames.Scene`/`frame_at`, `lane`, `captions.ass_file` และคำสั่ง ffmpeg ของ `video_gen.render` ใช้ตามเดิมผ่าน Lesson ชั่วคราวหนึ่งท่อน (`lessons.unsaved`): หัวเรื่อง บรรทัดรอง คำบรรยาย พื้นหลังของ cover, ท่อนเดียวป้ายว่าง ไม่เน้นชิ้นใด, `bpm` ใช้แค่กำหนดความเร็วเลื่อนของเลน ไม่แสดง.

**Why:** ADR-0040 และ ADR-0041 กำหนดแล้วว่าทุกชั้นอ่านเวลาจาก `Timeline` ตัวเดียว; ตัววาดชุดสองไม่คุ้มและเสี่ยงเสียงกับภาพคลาด.

**Rejected:**
- ให้ `frames`/`captions` รับ "สคริปต์" ชนิดใหม่แทน Lesson — refactor สามไฟล์เพื่อผู้ใช้ที่สอง ทั้งที่ Lesson หนึ่งท่อนแทนได้พอดี
- render ด้วย `video_gen.render.render_jobs` เดิม — งานผูกกับ `lesson_id` และ folder ของบทเรียน

**Details:**
- prefactor ใน `video_gen.timeline`: `assemble(sounds, beats, spans, length_s)` เป็นทาง public ที่ `build` ของบทเรียนและ `drum_cover` ใช้ร่วม (round-robin และการเรียง)
- prefactor ใน `video_gen.captions`: ช่วง (section) ที่ยาว 0 (นับเข้าที่ไม่มี) ไม่สร้าง event
- `bpm` ของ Lesson ชั่วคราว = `round(60 / มัธยฐานช่วงห่างของจังหวะในช่วง)` จำกัด 40–240; จังหวะน้อยกว่า 2 → 120
- ช่วงเดียว `Span(0, end_s − start_s)`; `length_s` = ความยาวช่วง + 1.5
- เวลาของการตี = `hit.t − start_s` ปัดเป็น sample ที่ 44.1 kHz ใน `assemble`
- ขั้นเลขล้วนแยกจาก Render job เพื่อ test ด้วย `analysis` สังเคราะห์ (D13)

**From:** change request · **Status:** active

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
- เปลี่ยน drum-notes D15 และแทน ADR-0045: เสียงบันทึกของเพลงเข้าคลิปได้เฉพาะ reel ที่ผู้ใช้เปิดเองต่อ cover ค่าตั้งต้นปิด; เสียงกลองยังมาจาก `Timeline` ชุดเดียว (ADR-0041 ไม่ขัด: เพลงไม่ใช่โน้ต)
- ffmpeg: `-ss start_s -t ความยาวช่วง -i audio.m4a` เป็น input ที่สาม, `filter_complex` `volume` แล้ว `amix` กับ wav กลอง (`duration=first` ตาม wav ที่ยาวรวมหางเสียง, `normalize=0` ไม่ลดเสียงกลอง); ฟังผ่าน `ffmpeg.run_capture` คืน wav
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
