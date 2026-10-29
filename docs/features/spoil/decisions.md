# Decisions: spoil

## D1: Backend โหลดสื่อตามลิงก์ที่ผู้ใช้ใส่ได้ตอนรัน

**Chosen:** แก้ ADR-0002 ให้แคบลง: การติดตั้ง package และโหลดโมเดลยังทำผ่าน Setup script เท่านั้น แต่ backend โหลดสื่อตามลิงก์ที่ผู้ใช้ใส่เองได้ตอนรัน. ตัวโหลด (yt-dlp) ติดตั้งผ่าน Setup script.

**Why:** tab สปอยต้องโหลดคลิป YouTube ตอนรัน ซึ่ง ADR-0002 ห้ามไว้ทั้งหมด. เหตุผลเดิมของ ADR-0002 (ไม่ทำ install บนเว็บ, โมเดลโหลดจาก snapshot) ยังใช้กับ package และโมเดล.

**Rejected:**
- ทำตาม ADR-0002 เดิม ให้ผู้ใช้โหลดคลิปเองแล้วลากไฟล์เข้ามา — ไม่ตรงกับที่ขอ

**Details:**
- supersedes ADR-0002 บางส่วน (แคบลง ไม่ยกเลิก): ADR ใหม่เขียนตอน gate

**From:** interview · **Status:** active

## D2: รอบนี้ทำแค่โหลดคลิป YouTube เก็บเป็น temp, ปลายทางคือคลิปสปอยหนัง

**Chosen:** feature สปอยรอบนี้มีแค่รับลิงก์ YouTube, โหลดเก็บเป็น temp และแสดงว่าโหลดอะไรมา. ปลายทางภายหลังคือคลิปเล่าหรือสปอยหนัง (ตัดต่อคลิปและใส่เสียงเล่าด้วย OmniVoice) ซึ่งไม่อยู่ในรอบนี้.

**Why:** ผู้ใช้ขอ "ทำแค่นี้ก่อน". ปลายทางกำหนดชื่อ tab และขอบเขตเรื่องกฎหมาย.

**Rejected:**
- แปลหรือพากย์คลิปเดิมด้วย Whisper — ไม่ใช่งานที่ผู้ใช้ต้องการ
- ไม่กำหนดปลายทาง — ทำให้เช็คกฎหมายไม่ได้

**From:** interview · **Status:** active

## D3: Temp clip อยู่จนผู้ใช้กดลบเอง

**Chosen:** คลิปที่โหลดเก็บใน `media/temp/` ของ project (gitignore) อยู่ข้าม restart จนผู้ใช้กดลบทีละคลิปในหน้าต่างรายการ.

**Why:** ขั้นต่อไป (ตัดต่อ, ใส่เสียงเล่า) ต้องหยิบคลิปเดิมไปใช้ได้หลัง restart.

**Rejected:**
- ลบทั้งหมดเมื่อ start backend — เสียคลิปทุกครั้งที่ restart
- ลบอัตโนมัติตามอายุ — มีกฎซ่อนที่ผู้ใช้อาจไม่รู้, ยังไม่จำเป็น

**Details:**
- อยู่ใน folder ของ project ตาม ADR-0003

**From:** interview · **Status:** active

## D4: โหลดคลิปแนวตั้ง ความคม 720 เป็น mp4

**Chosen:** รับเฉพาะคลิปแนวตั้งแบบ reels. โหลดวิดีโอที่ด้านสั้นไม่เกิน 720 px (เช่น 720×1280) รวมเสียงเป็นไฟล์ mp4 ด้วย ffmpeg จาก imageio (ADR-0005).

**Why:** ผู้ใช้ทำแค่คลิป reels แนวตั้ง และ 720 คมพอ.

**Rejected:**
- สูงสุด 1080p — ผู้ใช้ไม่ต้องการ
- สูงสุดที่มี (4K, webm) — ไฟล์ใหญ่และบาง browser เล่นไม่ได้

**Details:**
- "720" คือด้านสั้นของภาพ: คลิปแนวตั้งคือความกว้าง ≤ 720
- ไม่มี format ที่ ≤ 720 → เอาตัวที่เล็กที่สุดที่ใหญ่กว่า 720 แทน (กติกาใน spec › Implementation)

**From:** interview · **Status:** superseded by D5

## D5: รับคลิป YouTube ทุกแนว, โหลด temp ที่ด้านสั้นไม่เกิน 1080 เป็น mp4

**Chosen:** รับลิงก์ YouTube คลิปเดียวทุกแนว (ตั้งหรือนอน). โหลดวิดีโอที่ด้านสั้นไม่เกิน 1080 px รวมเสียงเป็น mp4 ด้วย ffmpeg จาก imageio (ADR-0005). Output ภายหลังเป็นแนวตั้งเท่านั้น และผู้ใช้เลือกความคมเองได้สูงสุด 1080p.

**Why:** ผู้ใช้รับคลิปต้นทางทุกแนว แต่ output เป็นแนวตั้งที่เลือก p ได้ถึง 1080. โหลดที่ 1080 เผื่อ output ทุกค่า และคลิปแนวนอนที่ต้อง crop เป็นแนวตั้งจะไม่แตก.

**Rejected:**
- เลือก p ตอนโหลด — ต้องโหลดใหม่ถ้าภายหลังอยากได้ output คมกว่า
- 720 เสมอ (D4) — output 1080 จะแค่ขยายภาพ
- รับเฉพาะลิงก์ `/shorts/` หรือปฏิเสธคลิปแนวนอน — ผู้ใช้ต้องการรับทุกแนว

**Details:**
- supersedes D4
- "1080" คือด้านสั้นของภาพ: แนวตั้ง กว้าง ≤ 1080, แนวนอน สูง ≤ 1080
- การเลือก p และทำเป็นแนวตั้งอยู่ใน feature render รอบหน้า ไม่อยู่ในรอบนี้

**From:** interview · **Status:** active

## D6: โหลดทีละคลิปเป็นงานเบื้องหลัง แสดง % และยกเลิกได้

**Chosen:** Backend โหลดเป็นงานเบื้องหลังได้ทีละคลิป. หน้าเว็บ poll ความคืบหน้าทุก 1 วินาทีและแสดงเป็น %. ระหว่างโหลดปุ่มโหลด disabled และมีปุ่มยกเลิก.

**Why:** คลิปยาวต้องเห็นว่ายังเดินอยู่ และทีละคลิปไม่ต้องมีคิว.

**Rejected:**
- คิวหลายลิงก์ — งานเยอะกว่า ยังไม่จำเป็น
- request เดียวรอจนเสร็จกับ spinner — คลิปยาวไม่รู้ว่าค้างหรือเปล่า

**From:** interview · **Status:** active

## D7: หน้าต่างรายการคลิปที่โหลดมา พร้อมเล่นดูได้

**Chosen:** รายการคลิปใน temp เรียงใหม่สุดก่อน. แต่ละแถวมี thumbnail, ชื่อคลิป, ชื่อช่อง, ความยาว, ขนาดภาพและแนว (ตั้งหรือนอน), ขนาดไฟล์, เวลาโหลด และปุ่มลบ. กดแถวแล้วเล่นคลิปในหน้าเว็บ.

**Why:** ผู้ใช้ขอหน้าต่างที่บอกว่าโหลดอะไรมา และต้องดูได้ว่าคลิปถูกตัวก่อนเอาไปทำต่อ.

**Rejected:**
- รายการอย่างเดียวไม่มี player — ต้องเปิดไฟล์นอกแอปเพื่อเช็ค
- แค่ชื่อไฟล์และขนาด — ไม่รู้ว่าคลิปไหนเป็นเรื่องอะไร

**From:** interview · **Status:** extended by D25

## D8: yt-dlp และ Deno pin ใน uv.lock, โหลดพังแล้วบอกวิธีอัปเดต

**Chosen:** `yt-dlp[default]` และ `deno` (wheel จาก PyPI) เป็น dependency ใน `pyproject.toml` และ pin เวอร์ชันใน `uv.lock` เหมือน package อื่น ติดตั้งผ่าน Setup script. โหลดล้มเพราะฝั่ง YouTube → หน้าเว็บแสดงเวอร์ชัน yt-dlp ที่ใช้และวิธีอัปเดต (`uv lock --upgrade-package yt-dlp` แล้วรัน Setup script).

**Why:** ทุกเครื่องได้เวอร์ชันเดียวกันตาม lock และไม่ขัด ADR-0002.

**Rejected:**
- Setup script อัปเดต yt-dlp เป็นตัวล่าสุดทุกครั้ง — แต่ละเครื่องได้เวอร์ชันไม่ตรงกันและไม่ตรง `uv.lock`

**Details:**
- yt-dlp ต้องมี JavaScript runtime สำหรับ YouTube; ใช้ Deno ≥ 2.3.0 จาก wheel `deno` บน PyPI (มี macOS arm64 และ Windows amd64) จึงอยู่ใน `.venv` ตาม ADR-0003
- extra `default` มี `yt-dlp-ejs` ที่เวอร์ชันตรงกับ yt-dlp

**Sources:** [yt-dlp EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS), [deno on PyPI](https://pypi.org/project/deno/)

**From:** interview · **Status:** active

## D9: เพิ่มแถว yt-dlp และ Deno ใน Status check

**Chosen:** Status check ของ setup-status เพิ่มจาก 9 เป็น 11 แถว: `yt_dlp` และ `deno` ต่อจากแถว `ffmpeg`. Tab สปอยใช้แค่แถว `yt_dlp`, `deno` และ `ffmpeg` ตัดสินว่าโหลดได้ไหม ไม่ใช้ `ready` (โมเดลที่ขาดไม่เกี่ยวกับการโหลด).

**Why:** ผู้ใช้อยากให้หน้า Setup status เป็นที่เดียวที่บอกว่าติดตั้งครบไหม.

**Rejected:**
- บอกใน tab สปอยเองอย่างเดียว ไม่แตะ Status check — สถานะการติดตั้งกระจายหลายที่
- ทั้งสองที่ — งานเยอะสุด

**Details:**
- extends setup-status D7 (9 แถว → 11 แถว); กฎของ check เดิมยังใช้ทั้งหมด (ไม่ใช้ network, timeout 5 วินาที)
- `yt_dlp`: `importlib.metadata.version("yt-dlp")` ได้ → `ok`, ไม่ได้ → `missing`
- `deno`: หา binary จาก package `deno` ใน venv และ `{deno} --version` exit 0 ภายใน 5 วินาที → `ok`; ไม่งั้น `missing`

**From:** interview · **Status:** active

## D10: Tab ด้านบน "สปอย" และ "Setup status" จำด้วย URL hash, เปิดมาที่ Setup status

**Chosen:** แถบ tab ด้านบนของแอปมีสอง tab ตามลำดับ: สปอย (`#/spoil`) และ Setup status (`#/setup`). ไม่มี hash หรือ hash ไม่รู้จัก → เปิด Setup status. Refresh แล้วอยู่ tab เดิม. ไม่ใช้ router library.

**Why:** ผู้ใช้เลือกสอง tab จำด้วย hash และให้เริ่มที่ Setup status.

**Rejected:**
- เปิดมาที่ tab สปอย — ผู้ใช้อยากเริ่มที่ Setup status
- react-router กับ URL จริง — สองหน้ายังไม่คุ้ม dependency ใหม่

**Details:**
- tab สปอยเมื่อติดตั้งไม่ครบ (D9) แสดงข้อความพร้อมลิงก์ไป `#/setup` แทนช่องลิงก์

**From:** interview · **Status:** active

## D11: ไม่จำกัดความยาวคลิป แต่เช็คดิสก์ก่อนโหลด

**Chosen:** ไม่จำกัดความยาว. ปฏิเสธ live และคลิปที่ยังไม่เริ่มฉาย. ก่อนโหลดเช็คว่าดิสก์ที่ `media/temp/` ว่าง ≥ ขนาดโดยประมาณจาก metadata + 1 GB; ไม่พอ → error ไม่เริ่มโหลด.

**Why:** คลิปต้นทางของสปอยหนังอาจยาวหลายชั่วโมง; ดิสก์เต็มกลางทางเสียเวลาและทิ้งไฟล์ค้าง.

**Rejected:**
- จำกัดความยาว เช่น 3 ชั่วโมง — ตัดคลิปหนังยาวที่ใช้ได้จริง
- ไม่เช็คอะไร — ดิสก์เต็มกลางทาง

**Details:**
- metadata ไม่มีขนาดโดยประมาณ → ประมาณจาก bitrate × ความยาว; ประมาณไม่ได้ → เช็คแค่ ≥ 1 GB

**From:** interview · **Status:** active

## D12: ลิงก์ซ้ำไม่โหลดใหม่ ชี้คลิปเดิม

**Chosen:** เทียบด้วย video id ของ YouTube. คลิปนั้นอยู่ใน temp แล้ว → ไม่โหลด, highlight แถวเดิมพร้อมข้อความ. อยากโหลดใหม่ต้องลบแถวเดิมก่อน.

**Why:** ประหยัดเวลาและดิสก์ และไม่มีแถวซ้ำในรายการ.

**Rejected:**
- โหลดทับของเดิม — เสียเวลาโหลดโดยไม่ได้อะไรใหม่
- โหลดเป็นอีกคลิป — แถวซ้ำกันในรายการ

**From:** interview · **Status:** active

## D13: ยอมรับความเสี่ยงด้านลิขสิทธิ์และ ToS ของ YouTube, ทำ feature ก่อน

**Chosen:** โหลดหนังเต็มเรื่องที่มีคนปล่อยบน YouTube เพื่อทำคลิปสปอยหารายได้ภายหลัง. ผู้ใช้ยอมรับความเสี่ยงด้านกฎหมายเอง และให้ทำ feature ออกมาก่อนแล้วค่อยกลับมาดูเรื่องกฎหมาย.

**Why:** ผู้ใช้บอกว่า "ถ้าผิด เดี๋ยว youtube แบนเอง ไม่ต้องคิดแทน" และ "ไม่ต้องสนเรื่องกฎหมาย ทำออกมาก่อน".

**Rejected:**
- โหลดเฉพาะคลิปที่มีสิทธิ์ — ไม่ตรงกับงานที่ผู้ใช้ทำ
- ใช้ส่วนตัวเท่านั้น — ผู้ใช้จะหารายได้

**Details:**
- verdict ทั้งหมดอยู่ใน [legal.md](legal.md)
- การหารายได้ขัด ADR-0007 (OmniVoice เป็น CC BY-NC). รอบนี้ไม่ใช้ OmniVoice จึงยังไม่ supersede; feature ใส่เสียงเล่าต้องเลือก TTS ที่ใช้เชิงพาณิชย์ได้แล้ว supersede ADR-0007 ตอนนั้น

**Accepted risk:** ผิด ToS ของ YouTube (บัญชีหรือช่องถูกแบน) และอาจละเมิดลิขสิทธิ์ภาพยนตร์ตาม พ.ร.บ.ลิขสิทธิ์ ม.15, ม.53/4 (โทษปรับ 1 หมื่นถึง 1 แสนบาท, เชิงการค้าจำคุกได้ถึง 2 ปีตาม ม.70/1). ผู้ใช้รับเอง.

**From:** legal · **Status:** active

## D14: รายละเอียดการเก็บไฟล์และงานโหลดที่ตัดสินจากโค้ด

**Chosen:** กติกาที่ builder ต้องใช้ ตัดสินจากโค้ดที่มีอยู่และเอกสารของ yt-dlp.

**Details:**
- **ไฟล์:** Temp clip หนึ่งคลิปคือ `{id}.mp4`, `{id}.json` และ thumbnail `{id}.{ext}` ใน `media/temp/` โดย `{id}` คือ video id ของ YouTube — ชื่อไม่ชนกันและเช็คซ้ำได้จากชื่อไฟล์ (D12)
- **คลิปครบ:** `{id}.json` เขียนเป็นไฟล์สุดท้ายด้วยการเขียนไฟล์ชั่วคราวแล้ว rename — ไม่มี json คือคลิปไม่ครบ เหมือน Model marker ของ setup-status
- **ไฟล์ค้าง:** yt-dlp เขียนไฟล์ระหว่างโหลดใน `media/temp/.partial/`. ยกเลิกหรือล้ม → ลบไฟล์ของ id นั้น. Backend start → ล้าง `.partial/` ทั้งหมด — งานโหลดไม่รอดข้าม restart
- **สถานะงาน:** Download job อยู่ใน memory ของ backend ตัวเดียว ไม่เขียนลงดิสก์ — มีทีละงาน (D6) และ backend เป็น process เดียว (ADR-0001)
- **ยกเลิก:** progress hook raise `DownloadCancelled` ของ yt-dlp เมื่อมีคำขอยกเลิก — ไม่ต้องมี process แยก
- **ลิงก์:** backend ตรวจรูปแบบลิงก์และเช็คซ้ำจาก video id ในลิงก์โดยไม่ใช้ network — ตอบผิดได้ทันทีก่อนเริ่มงาน
- **gitignore:** เพิ่ม `media/` — คลิปไม่เข้า git

**From:** code · **Status:** active

## D15: กติกาจาก red team ของงานโหลด, การลบ และ API

**Chosen:** ชุดกติกาที่ red team เจอว่าขาดในแผน. รายละเอียดอยู่ใน spec.md › Implementation.

**Details:**
- **ยกเลิกแต่ละ state:** `checking` → flag ถูกเช็คหลัง `extract_info` คืน; `downloading` → hook raise `DownloadCancelled`; `merging` → ยกเลิกไม่ได้ (`409` `merging`) เพราะ merge แบบ copy stream ใช้ไม่กี่วินาทีและไม่มี hook — กันงานที่ "ยกเลิกแล้ว" กลับจบเป็น `done`
- **busy:** หนึ่ง `threading.Lock` ครอบ "เช็ค busy, เช็คซ้ำ, สร้างงาน" และงานนับว่ายังไม่จบจน thread ออก — กัน POST สองครั้งพร้อมกัน
- **thread:** daemon thread; shutdown ของ app ตั้ง flag ยกเลิก — Ctrl+C ไม่ค้างรอโหลดจบ
- **ลบคลิป:** หน้าเว็บปลด `<video>` ก่อน; backend ลบ mp4 และ thumbnail ก่อน json สุดท้าย; ลบ mp4 ไม่ได้ → `409` `in_use` และแถวยังอยู่ — Windows ลบไฟล์ที่เปิดอยู่ไม่ได้
- **start:** ล้าง `.partial/` และไฟล์ `{id}.*` ที่ไม่มี json คู่ — ไม่มีไฟล์ใหญ่ซ่อนค้าง
- **error ของ yt-dlp:** แยก code จาก exception: ต้อง login หรือ bot check → `login_required`, ประเทศหรือ private หรือถูกลบ → `unavailable`, upcoming → `live`; ที่เหลือ → `youtube_error` พร้อมคำสั่งอัปเดตใน `fix` — คำแนะนำ "อัปเดต yt-dlp" ใช้กับกรณีที่ช่วยได้เท่านั้น
- **Host:** `TrustedHostMiddleware` ให้แค่ `127.0.0.1`, `localhost`, `[::1]` — กัน DNS rebinding อ่านหรือลบคลิปจากเว็บอื่น
- **หน้าเว็บหลังงานจบ:** เปิด tab แล้วได้งานที่จบแล้ว → แสดงผลของงานนั้น; poll ได้ `null` ระหว่างติดตามงาน → "งานโหลดหายเพราะ backend เริ่มใหม่ ลองโหลดอีกครั้ง"; `percent` ไม่เกิน 100

**From:** red team · **Status:** active

## D16: ตารางแยก error ของ yt-dlp ตามข้อความจริงจาก YouTube

**Chosen:** แยก code จากข้อความ error ตามลำดับนี้: มี "This live event will begin" หรือ "Premieres in" → `live`; มี "Sign in to confirm" หรือ "not a bot" → `login_required`; `GeoRestrictedError` หรือมี "Private video", "unavailable", "removed" → `unavailable`; ที่เหลือ → `youtube_error`. ไม่ใช้คำว่า "age" เดี่ยวๆ.

**Why:** ลองกับ YouTube จริงตอน build ticket 01 (yt-dlp 2026.10.26, 2026-10-29): live ที่ยังไม่เริ่มทำให้ `extract_info` raise "This live event will begin in 4 days." โดยไม่มี info จึงไม่มี `live_status` ให้เช็ค; คลิปจำกัดอายุได้ "Sign in to confirm your age…" ซึ่ง "Sign in to confirm" ครอบอยู่แล้ว; คำว่า "age" เดี่ยวๆ ชนข้อความอื่น เช่น "Unable to download webpage" แล้วจะบอกผู้ใช้ผิดว่าต้อง login.

**Rejected:**
- ตารางเดิมใน spec ที่มี "age" — แยก error ผิดเมื่อข้อความมีคำว่า page

**From:** build ticket 01 · **Status:** active

## D17: ทางเลือกเล็กตอน build งานโหลด

**Chosen:** รายละเอียดที่ build ticket 01 ตัดสินเองตามโค้ดเดิมและ conventions.

**Details:**
- **probe ของ gate:** แถว `yt_dlp`, `deno`, `ffmpeg` ของ Status check กับ `POST /downloads` ใช้ probe ตัวเดียวกันใน `backend.checks` (`probe_yt_dlp`, `probe_deno`, `probe_ffmpeg`) ที่ gate เรียกตอนเรียก — test monkeypatch ที่เดียวได้ทั้งสองที่ และ `run_checks` รับ `yt_dlp_probe`, `deno_probe` แบบเดียวกับ `ffmpeg_probe` (setup-status D18)
- **ลิงก์:** ตัดช่องว่างหัวท้ายก่อนเก็บใน Download job และก่อนส่งให้ yt-dlp — yt-dlp ไม่รับลิงก์ที่มีช่องว่าง
- **ลบไฟล์ค้างไม่ได้:** ลบทีละไฟล์แบบ best effort; ไฟล์ที่ Windows ยังเปิดอยู่ถูก log ไว้และรอการล้างตอน start ถัดไป — งานยังจบเป็น `failed` หรือ `cancelled` ไม่ค้างเป็น busy
- **percent:** ไม่ลดลงเมื่อ yt-dlp เริ่มโหลด format ใหม่จาก 0
- **ที่ว่างบนดิสก์:** `backend.disk.free_bytes` ใช้ร่วมกับ setup
- **adapter:** `download(info, project, on_progress)` รับ `ProjectPaths` แทนที่จะอ่าน `paths.ROOT` เอง — adapter ปลอมเขียนไฟล์ลง root ปลอมได้โดยไม่ต้องอ่าน global
- **`not_ready`:** message เป็น "ยังติดตั้งไม่ครบ: {label ที่ขาด}" เหมือนข้อความของ tab สปอย
- **งานจบ:** state สุดท้ายถูกตั้งหลังลบไฟล์ค้างเสร็จ และ busy เช็คจาก state — ได้ผลเดียวกับ "จบเมื่อ thread ออก" โดยไม่ต้องรอ thread
- **ขนาดประมาณ:** ไม่มี `requested_formats` (YouTube ให้ format เดียวที่มีทั้งภาพและเสียง เช่นคลิปเก่า) → ใช้ `filesize` ของ info เอง แล้วค่อย `tbr` × `duration`
- **thumbnail:** หาไฟล์ `{id}.*` ใน `media/temp/` ที่ไม่ใช่ mp4 หรือ json — `filepath` ของ thumbnail ที่ yt-dlp คืนชี้ไป `.partial/` ทั้งที่ไฟล์ย้ายไปแล้ว
- **error ที่ไม่ใช่ `youtube_error`:** มี `yt_dlp_version` ด้วยและ `fix` เป็น `null`

**From:** build ticket 01 · **Status:** active

## D18: ของบนจอที่ design เพิ่มจาก spec

**Chosen:** เก็บสามอย่างที่ frame ใน Figma เพิ่มจาก spec: หัวรายการ "คลิปที่โหลดมา" พร้อมจำนวนคลิป, badge "กำลังเล่น" บนแถวที่ player เล่นอยู่, และข้อความ "ยกเลิกไม่ได้ระหว่างรวมไฟล์" แทนปุ่มยกเลิกตอน `merging`.

**Why:** ผู้ใช้เลือกเก็บทั้งสามตอนรับ design. เป็นข้อความบนจออย่างเดียว ไม่เปลี่ยน API หรือพฤติกรรม: จำนวนนับจาก `GET /clips`, badge มาจากแถวที่กด, และข้อความตอน merging บอกเหตุที่ปุ่มหายไป (D15).

**Rejected:**
- เอาออกให้ตรง spec เดิม — ผู้ใช้อยากเก็บไว้

**From:** design · **Status:** active


## D19: ทางเลือกเล็กตอน build แถบ tab และ tab สปอย

**Chosen:** รายละเอียดที่ build ticket 02 ตัดสินเองตาม Figma, conventions และโค้ดเดิม.

**Details:**
- **loading:** รอ `/api/setup/status` กับ `GET /downloads/current` — `GET /clips` มาใน ticket 03 แล้วค่อยรอด้วย
- **tab:** เป็นลิงก์ `<a href="#/…">` ที่มี `aria-current="page"` บน tab ที่เปิด — กดกับปุ่ม back แค่เปลี่ยน hash; `useHashTab` ตามอย่างเดียว ไม่มี setter
- **layout ร่วม:** `components/ui/PageLayout` (wordmark, แถบ tab, ปุ่มขวาสุด) ใช้ทั้งสอง tab; หัวข้อหน้าเป็น `h1` แบบ `sr-only` ตามชื่อ tab เพราะ header ใหม่ใน Figma ไม่มีชื่อหน้า. wordmark 26px ทุกจอตาม frame 13 (เดิมมือถือ 20.8px)
- **ย้ายของร่วม:** `RefreshButton`, `OfflinePanel` ไป `components/ui/`; สไตล์ปุ่ม outline เป็น `OUTLINE_BUTTON`; การ copy เป็น `lib/useCopy` ที่ใช้ทั้งปุ่ม copy ของ Checklist และของคำสั่ง `fix` — clipboard ถูกปฏิเสธก็ไม่ throw
- **tab สปอย offline:** ปุ่ม Refresh อยู่ขวาของ header เฉพาะตอน offline ตาม frame 12
- **ข้อความหลังงานจบ:** อยู่ใต้แถบความคืบหน้า (409 `merging` ขึ้นระหว่างงานยังไม่จบ); tone ตาม frame 6–9: done = success, cancelled และ duplicate = info, busy, merging และงานหาย = warning, ที่เหลือ = error
- **ข้อความของ refusal:** ใช้ข้อความตาราง Frontend ไม่ใช้ `message` ของ API. `duplicate` แสดง "คลิปนี้โหลดไว้แล้ว" ใน ticket นี้; highlight แถวเดิมมาใน ticket 03
- **code ที่ไม่รู้จัก:** `400` หรือ `409` ที่ code ไม่อยู่ในตาราง และ `DELETE` ที่ได้ `409` ที่ไม่ใช่ `merging` → offline ตาม "status ที่ไม่อยู่ในตาราง API"
- **ยกเลิกได้ `404`:** งานจบก่อนคำสั่งยกเลิกไปถึง — ไม่ทำอะไร poll รอบถัดไปแสดงผลจบ
- **`503` `not_ready`:** โหลด status ใหม่แล้วเข้า state not ready พร้อมชื่อแถวที่ขาด
- **ชื่อคลิปตอน done:** `title` เป็น `null` → ใช้ `id` แทน
- **ปุ่ม copy:** ข้อความบนปุ่มเป็น "Copy" ภาษาอังกฤษตาม Button ใน frame 7 (เหมือน "Refresh"); `aria-label` เป็น `คัดลอก {คำสั่ง}` (setup-status D21)
- **token ใหม่ใน `index.css`:** `accent-subtle`, `border-strong`, `info-surface`, `info-border` จาก Figma
- **`<title>` ของหน้า:** "framecraft" — เดิม "framecraft — Setup status" ซึ่งผิดเมื่อมีสอง tab

**From:** build ticket 02 · **Status:** active


## D20: ทางเลือกเล็กตอน build รายการ Temp clip

**Chosen:** รายละเอียดที่ build ticket 03 ตัดสินเองตาม Figma, conventions และโค้ดเดิม.

**Details:**
- **`404` `not_found`:** message "ไม่พบคลิปนี้"; คลิปที่ "มีอยู่" = มี `{id}.json` (เหมือนเช็คซ้ำของ `POST /downloads`). video ต้องมี mp4 ด้วย — mp4 ที่ json ยังไม่ถูกเขียนได้ `404`
- **ลบ json ที่ mp4 หาย:** `204` และลบ json — ไม่งั้นลิงก์นั้นเป็น `duplicate` ตลอดทั้งที่รายการไม่แสดง
- **thumbnail ลบไม่ได้:** log แล้วลบ json ต่อ; การล้างตอน start เก็บไฟล์ที่เหลือ (D15)
- **เรียงรายการ:** เทียบ `downloaded_at` เป็นเวลาจริงไม่ใช่ข้อความ; เวลาที่อ่านไม่ได้หรือไม่มี offset → ข้าม json นั้น เหมือน json เสีย — `GET /clips` ไม่ตอบ 500 เพราะไฟล์เดียว
- **`SpoilError`:** ย้ายไป `backend.spoil.errors` เพราะ `clips` กับ `jobs` raise ทั้งคู่ (`jobs` import `clips`). route สร้าง `ProjectPaths(paths.ROOT)` ต่อ request แล้วส่งให้ `clips` เหมือนฟังก์ชันอื่นใน `clips.py`
- **หน้าเว็บ:** hook `useTempClips` แยกจาก `useSpoilDownload`; งานจบหรือหาย → `useSpoilDownload` เรียก `refetch` ของรายการ (ไม่ขึ้น loading). แถวที่ highlight มาจาก `clipId` ของข้อความหลังงานจบ จึงหายพร้อมข้อความตอนกดโหลดครั้งถัดไป. เลื่อนไปหาแถวที่ highlight ทั้ง `done` และ `duplicate`
- **ลบได้ `404`:** แถวหายเหมือน `204` (ไฟล์ถูกลบด้วยมือ) — ข้อยกเว้นของ "status ที่ไม่อยู่ในตาราง = offline" (D19); status อื่นนอก `204`, `404`, `409` `in_use` → offline
- **error ใต้แถว:** หายเมื่อรายการโหลดใหม่ (เป็นเรื่องของรายการเก่า)
- **player:** `autoPlay` เพราะผู้ใช้กดแถวเพื่อดู; กดลบแถวที่เล่นอยู่ → player ปิดและไม่เปิดกลับแม้ได้ `in_use`
- **แถว:** ทั้ง thumbnail กับข้อความเป็นปุ่มเล่นปุ่มเดียว, ปุ่มลบแยก (`aria-label` "ลบ {title}"); ไม่มี thumbnail → กล่องเทาตาม Figma; ไม่มีขนาดภาพ → แสดงแค่ "ตั้ง"/"นอน"; ไม่มีช่องหรือความยาว → ตัดส่วนนั้น
- **ขนาดไฟล์:** ฐาน 1000 (1e6 MB, 1e9 GB) เหมือนข้อความ `disk_full`. เวลา: `Intl` `th-TH` วันกับเดือนย่อและ `HH:mm` = "29 ต.ค. 18:52" ตาม Figma
- **ของร่วม:** `lib/useMountedState` แทน ref `mounted` ที่ซ้ำในสาม hook; `features/spoil/hooks/refusal.ts` อ่าน refusal ของ API ให้ทั้งสอง hook
- **token ใหม่ใน `index.css`:** `surface-strong`, `surface-inverse` จาก Figma

**From:** build ticket 03 · **Status:** active

## D21: ถอดบทพูดของ Temp clip ด้วย Whisper large-v3-turbo ที่ติดตั้งแล้ว

**Chosen:** ผู้ใช้เลือก Temp clip หนึ่งคลิปแล้วให้แอปถอดคำพูดในคลิปเป็นข้อความด้วย Whisper large-v3-turbo (`openai/whisper-large-v3-turbo` ที่ pin ไว้ใน setup-status D16) ตรวจภาษาเอง. ผลที่ผู้ใช้ได้คือ Transcript อย่างเดียว; การดึงเสียงออกจากวิดีโอเป็นขั้นภายในเพื่อส่งให้ Whisper ไม่ใช่ไฟล์ที่ผู้ใช้เอาไปใช้.

**Why:** ผู้ใช้ต้องการแค่คำที่พูดในคลิปเพื่อเอาไปวิเคราะห์เขียนบทสปอยที่อื่น. คลิปต้นทางมีหลายภาษา และ Whisper turbo เป็นโมเดลฟรี (MIT) ที่ติดตั้งมากับ Setup script แล้ว ไม่ต้องโหลดเพิ่ม.

**Rejected:**
- แยกเสียงพูดออกจากดนตรีด้วย AI (เช่น Demucs) — ผู้ใช้ไม่ต้องการไฟล์เสียง ต้องการแค่คำพูด
- แยกเป็นไฟล์วิดีโอเงียบกับไฟล์เสียงให้ผู้ใช้ — ไม่มีใครใช้ไฟล์เหล่านั้น
- Whisper ที่ fine-tune ภาษาไทย — คลิปต้นทางหลายภาษา โมเดลไทยถอดภาษาอื่นแย่ลง และต้องโหลดเพิ่ม ~3 GB

**From:** change request · **Status:** active

## D22: แสดง Transcript ทีละบรรทัดพร้อมเวลา, Copy ทั้งหมด และโหลด .txt กับ .srt

**Chosen:** หน้าเว็บแสดง Transcript ทีละบรรทัดพร้อมเวลาเริ่ม `[hh:mm:ss]`; กดบรรทัดแล้ว player กระโดดไปเวลานั้น. มีปุ่ม Copy ข้อความทั้งหมด และปุ่มโหลดไฟล์ `.txt` กับ `.srt`.

**Why:** ผู้ใช้จะเอาบทพูดไปวิเคราะห์เขียนบทสปอยที่อื่น — Copy ใช้วางใน AI ตัวอื่น, ไฟล์ใช้เก็บหรือเปิดในโปรแกรมอื่น, เวลาบอกว่าบทพูดอยู่ตรงไหนของหนัง.

**Rejected:**
- แสดงกับ Copy อย่างเดียว ไม่มีไฟล์ — ผู้ใช้เลือกให้มีไฟล์ด้วย
- แสดงอย่างเดียว — ต้องลากคลุมข้อความเองถ้าจะเอาไปใช้

**From:** change request · **Status:** active

## D23: ถอดเมื่อผู้ใช้กดเท่านั้น, เก็บ Transcript คู่กับ Temp clip และแสดงสถานะ "ถอดแล้ว"

**Chosen:** การถอดเริ่มเมื่อผู้ใช้กดปุ่มถอดของคลิปที่เลือกเท่านั้น ไม่ถอดอัตโนมัติหลังโหลด. Transcript เก็บเป็นไฟล์ใน `media/temp/` คู่กับ Temp clip อยู่ข้าม restart; แถวในรายการคลิปแสดงสถานะว่าถอดแล้ว. ลบคลิป → ลบ Transcript และสถานะหายไปพร้อมแถว. กดถอดใหม่ทับของเดิมได้.

**Why:** ผู้ใช้บอกให้ถอด "ตอน user กดโปรเซสว่าจะถอดคลิปนี้เท่านั้น" และให้มี status กับ alert บอกว่าคลิปนี้ถอดแล้ว ซึ่งหายเมื่อลบคลิป. เก็บไว้เพราะหนังยาวถอดนานหลายนาที ไม่ควรต้องถอดซ้ำเมื่อเปิดแอปใหม่.

**Rejected:**
- ถอดอัตโนมัติหลังโหลดเสร็จ — ผู้ใช้ไม่ต้องการ; ไม่ใช่ทุกคลิปจะเอามาทำสปอย
- เก็บใน memory อย่างเดียว — หายเมื่อ backend restart ต้องถอดซ้ำ

**From:** change request · **Status:** active

## D24: ถอดได้ทีละคลิป ทำพร้อมกับงานโหลดได้, เห็น % และยกเลิกได้

**Chosen:** มี Transcribe job ได้ทีละงาน ไม่มีคิว. งานถอดกับ Download job รันพร้อมกันได้ (ถอด B ระหว่างโหลด A). หน้าเว็บ poll % และกดยกเลิกได้ แบบเดียวกับงานโหลด (D6, ADR-0010).

**Why:** งานโหลดใช้ network ส่วนงานถอดใช้ GPU จึงไม่แย่งกัน และผู้ใช้ไม่ต้องรอโหลดเสร็จก่อนถอดคลิปที่มีอยู่แล้ว.

**Rejected:**
- ทั้งแอปทำทีละงาน — ต้องรอโดยไม่จำเป็น
- คิวหลายคลิป — ไม่ได้ขอ และ D6 ก็ไม่มีคิว

**From:** change request · **Status:** active

## D25: tab สปอยเป็นสองคอลัมน์ รายการคลิป → ลูกศร → กล่องถอดบทพูด

**Chosen:** จอกว้าง: ซ้ายเป็นรายการคลิปที่โหลดมา, กลางเป็นลูกศร →, ขวาเป็นกล่องถอดบทพูด. กดแถวคลิป = เลือกคลิปเข้ากล่องขวา; player ย้ายเข้ากล่องขวาพร้อมชื่อคลิป ปุ่มถอด ความคืบหน้า และ Transcript. จอแคบ 375px เรียงบนลงล่าง ลูกศรชี้ลง ↓.

**Why:** ผู้ใช้ขอลูกศรกลางระหว่างรายการคลิปที่โหลดมากับกล่องเลือกคลิปไปทำสปอย และเลือก layout นี้จาก sketch.

**Rejected:**
- บนลงล่างทุกจอ — ผู้ใช้เลือกสองคอลัมน์

**Details:**
- extends D7: player ยังเล่นในหน้าเว็บ แต่อยู่ในกล่องขวาแทนเหนือรายการ
- ออกแบบใน Figma หลัง plan (setup-status D9)

**From:** change request · **Status:** active

## D26: ไม่จำกัดเวลาถอด แต่ต้องเห็น % และยกเลิกได้

**Chosen:** ไม่มีเป้าเวลาถอดต่อความยาวคลิป. หน้าเว็บต้องเห็น % ที่เดินตามส่วนของเสียงที่ถอดแล้ว และกดยกเลิกได้.

**Why:** ผู้ใช้บอกว่า "ไม่จำกัด เห็น % พอ".

**Rejected:**
- หนัง 1:30 ชม. ต้องเสร็จใน 15 หรือ 30 นาที — ผู้ใช้ไม่ต้องการเป้าเวลา

**From:** change request · **Status:** active

## D27: กติกาของงานถอดที่ตัดสินจากโค้ดและ library

**Chosen:** รายละเอียดที่ builder ต้องใช้ ตัดสินจากโค้ดที่มีอยู่และ `transformers` 5.21.0 ที่ติดตั้งอยู่.

**Details:**
- **ดึงเสียง:** ffmpeg ของ `imageio-ffmpeg` (ADR-0005) แปลงเสียงของ `{id}.mp4` เป็น 16 kHz mono float32 ส่งผ่าน pipe เข้า memory แล้วส่ง array ให้ pipeline — ส่ง path ไฟล์ให้ pipeline ตรงๆ ไม่ได้ เพราะ `ffmpeg_read` ของ `transformers` เรียก `ffmpeg` บน PATH (setup-status Open Question 2). ไม่เขียนไฟล์เสียงลงดิสก์
- **โหลดโมเดล:** `pipeline("automatic-speech-recognition")` จาก folder snapshot ของ revision ที่ pin (`ProjectPaths.snapshot_dir`) ไม่ใช้ network (ADR-0004); โหลดตอนเริ่มงาน ปล่อยหลังงานจบ (`del` แล้ว `empty_cache` ของ device) เพื่อคืน memory ให้งานอื่น
- **ส่วนของเสียง:** แบ่งเสียงเป็นช่วงละ 5 นาที ส่งทีละช่วงด้วย `chunk_length_s=30` และ `return_timestamps=True` แล้วบวกเวลาเริ่มของช่วงให้ทุกบรรทัด — % = ช่วงที่เสร็จ ÷ ช่วงทั้งหมด และเช็ค flag ยกเลิกระหว่างช่วง (D24, D26)
- **gate:** ถอดได้เมื่อแถว `torch`, `transformers`, `ffmpeg`, `model_whisper` เป็น `ok` และ `device` เป็น `ok` (ไม่ใช่ `cpu`) — แบบเดียวกับ gate ของงานโหลด (D9) และ ADR-0006
- **ลบคลิประหว่างถอด:** `DELETE /clips/{id}` ของคลิปที่กำลังถอด → `409` `transcribing` ไม่ยกเลิกงานให้เอง
- **ไม่มีคำพูด:** ถอดจบแล้วไม่มีบรรทัด → Transcript ว่าง เก็บได้ แสดง "ไม่พบคำพูดในคลิปนี้"
- **ไฟล์:** `{id}.transcript.json` เขียนไฟล์ชั่วคราวแล้ว rename เหมือน `{id}.json` (D14); ถอดใหม่ทับเมื่องานใหม่ `done` เท่านั้น — ยกเลิกหรือล้มไม่แตะของเดิม

**From:** code · **Status:** changed by D28, D29

## D28: งานถอดรันใน process ลูก ไม่ใช่ thread ใน backend

**Chosen:** Transcribe job ยังมี thread ใน backend ถือสถานะใน memory (ADR-0010) แต่ตัวถอดจริง (ffmpeg, Whisper, torch) รันใน `multiprocessing` process ลูกแบบ `spawn`. process ลูกส่ง % และบรรทัดกลับผ่าน queue; backend เป็นผู้เขียน Transcript คนเดียว. ยกเลิก = `terminate()` process ลูก; process ลูกตายโดยไม่ส่งผล → `failed` `crashed`.

**Why:** Metal หรือ CUDA crash ฆ่าทั้ง process ไม่ใช่ exception — ถ้าอยู่ใน backend งานโหลดที่รันพร้อมกันหายด้วย ขัด D24. process ลูกยังให้ยกเลิกได้ทันทีและคืน memory ครบเมื่อจบ. ผู้ใช้เลือก.

**Rejected:**
- thread ใน backend ตาม ADR-0010 แล้วรับความเสี่ยง — crash ล้มทั้ง backend, ยกเลิกต้องรอจบช่วง, memory ของ host ไม่คืน

**Details:**
- extends ADR-0010: งานที่ใช้ GPU รันใน process ลูก; สถานะยังอยู่ใน thread ของ backend และหายเมื่อ restart
- `spawn` ทั้ง Mac และ Windows — ไม่ fork process ที่มี thread อยู่แล้ว
- backend shutdown → `terminate()` process ลูกที่ยังรัน

**From:** red team · **Status:** active

## D29: กติกาจาก red team ของงานถอด

**Chosen:** ข้อที่ The Breaker เจอ แก้ใน spec แล้ว.

**Details:**
- **ล้มนอกตาราง:** error ใดก็ตามในขั้นไหน (รวมเขียนไฟล์ไม่ได้) → `failed` `internal`; thread ตั้ง state จบใน `finally` — ไม่มีงานค้าง `transcribing` ที่ทำให้ `busy` ตลอด
- **memory:** ffmpeg ดึงเสียงทีละช่วง 300 วินาทีด้วย `-ss`/`-t` ใน process ลูก ไม่ดึงทั้งเรื่อง — memory คงที่ตามความยาวช่วงไม่ใช่ความยาวคลิป (D11 ไม่จำกัดความยาว). supersedes ส่วน "ดึงเสียง" ของ D27
- **long-form:** ส่ง array 300 วินาทีให้ pipeline โดยไม่ใช้ `chunk_length_s` (ใน `transformers` 5.21.0 ยังเป็น "very experimental" สำหรับ Whisper) ให้ Whisper ถอดแบบ long-form เอง, `batch_size` 1; ภาษาอ่านจาก `chunks[i]["language"]` ไม่ใช่ค่าบนสุด. supersedes ส่วน "ส่วนของเสียง" ของ D27
- **ช่วงท้ายสั้น:** ช่วงสุดท้ายที่สั้นกว่า 30 วินาทีรวมเข้าช่วงก่อนหน้า — กัน Whisper แต่งคำจากเสียงสั้นๆ
- **ภาษา:** `language` เป็น `null` ได้ (ไม่พบคำพูด) หน้าเว็บแสดง "ภาษา: ไม่ทราบ"
- **ลบกับถอดชนกัน:** `DELETE /clips/{id}` เช็คและลบภายใต้ lock เดียวกับ `POST /transcriptions`; POST เช็คว่าคลิปมีอยู่ภายใต้ lock นั้น
- **ไฟล์ Transcript กับคลังคลิป:** รายการคลิปข้าม `*.transcript.json`; `transcribed` = ไฟล์มีอยู่ (ไม่ parse); backend start ลบ `*.tmp` ใน `media/temp/`
- **POST จากเว็บอื่น:** ทุก `POST` ใต้ `/api/spoil` ต้องมี `Content-Type: application/json` ไม่งั้น `415` — บังคับ preflight ของ CORS กันเว็บอื่นสั่งงาน (รวม `POST /downloads`); เพิ่มจาก ADR-0011

**From:** red team · **Status:** active


## D30: ทางเลือกเล็กตอน build งานถอดบทพูด

**Chosen:** รายละเอียดที่ build ticket 04 ตัดสินเองจากการลองกับโมเดลจริงบน Mac, conventions และโค้ดเดิม.

**Details:**
- **dtype:** `float32` บน `mps`, `float16` บน `cuda` — ลองแล้ว `float16` บน `mps` ได้ข้อความขยะ ("The!!! I! THE!") ตามทางสำรองใน spec › Library assumptions; `cuda` เช็คใน ticket 06
- **ภาษา:** `return_language=True` คืนชื่อภาษา (`"english"`, `"thai"`) ไม่ใช่ code จึงแปลงด้วย `TO_LANGUAGE_CODE` ของ Whisper tokenizer เป็น `en`, `th` ใน process ลูก
- **เวลา:** เวลาจบที่ `None` → จบช่วง, เวลาจบเลยความยาวช่วง (เจอจริง 298.5 → 328.5 บนช่วง 300 วินาที) → ตัดที่จบช่วง; ปัดสองตำแหน่ง
- **ความยาวคลิปไม่รู้ (`duration_s` null):** ถอดเป็นช่วงเดียวจนจบไฟล์ (ไม่มี `-t`)
- **ffmpeg ล้มที่ช่วงหลังช่วงแรก:** `model_failed` (ช่วงแรกเท่านั้นที่เป็น `no_audio`)
- **ไม่ `del` โมเดลหรือ `empty_cache`:** process ลูกออกเมื่องานจบ ซึ่งคืน memory ครบอยู่แล้ว (D28) — แทนข้อ "โหลดโมเดล" ของ D27 ส่วนนั้น
- **gate:** ใช้ฟังก์ชันเดียวกับ Status check (`check_package`, `check_model`, `check_device` ซึ่งเปลี่ยนเป็น public) เพื่อไม่ให้หน้า Setup status กับ gate ไม่ตรงกัน; message "ยังติดตั้งไม่ครบ: {label, ...}" ตาม label ของแถว เหมือนงานโหลด
- **`404` ของ Transcript:** คลิปไม่มี → "ไม่พบคลิปนี้"; คลิปมีแต่ยังไม่ถอด → "คลิปนี้ยังไม่ได้ถอดบทพูด"; ไฟล์ Transcript อ่านไม่ได้ → log แล้ว "อ่าน Transcript ไม่ได้ ถอดใหม่อีกครั้ง" ไม่ตอบ 500
- **`415`:** dependency ระดับ app ใน `app.py` ทุก `POST` ใต้ `/api` ตาม ADR 0013 (กว้างกว่า "ใต้ `/api/spoil`" ใน spec ซึ่งตอนนี้เท่ากัน), message "ต้องส่งเป็น JSON"; ไม่มี `Content-Type` ก็ `415`; `application/json; charset=utf-8` ผ่าน
- **ลบ Transcript ไม่ได้ตอนลบคลิป:** log แล้วลบ json ต่อ เหมือน thumbnail; การล้างตอน start เก็บ Transcript ที่ไม่มี json
- **message ของ process ลูก:** `NamedTuple` `Segment`, `WorkerError`, `Done` ใน `backend.spoil.whisper` แทน tuple เปล่า — ลำดับ field ตาม spec
- **ส่วนร่วมของสอง job:** `backend.spoil.job_slot.JobSlot` ถือ lock, job ล่าสุด, flag ยกเลิก, `current()` ให้ทั้ง `Downloads` และ `Transcriptions`
- **ยกเลิก:** thread ดู flag ทุก 0.2 วินาที; `terminate()` แล้ว `join` 5 วินาที ไม่ออก → `kill()`. วัดบน Mac: process ลูกหายใน 0.18 วินาที
- **ลบคลิป:** route เรียก `transcriptions.delete_clip` ที่เช็ค `transcribing` และลบภายใต้ lock เดียวกับ `POST /transcriptions` (D29)
- **message ที่ไม่รู้จักจาก process ลูก:** `internal` และ terminate process ลูก
- **ล้างตอน start:** `*.tmp` ทุกไฟล์ใน `media/temp/` รวม `{id}.json.tmp` ของคลิปที่มี json แล้ว

**From:** build ticket 04 · **Status:** active

## D31: ไม่กรองบรรทัดที่ Whisper แต่งเองในช่วงไม่มีคำพูด

**Chosen:** เก็บทุกบรรทัดที่ Whisper ให้ ไม่กรองเพิ่ม. ช่วงที่มีแต่ดนตรี Whisper อาจแต่งบรรทัดเต็มหน้าต่าง 30 วินาที (เช่น "THE END", "Thank you for listening." เวลา `0.0–29.98`) หรือคำซ้ำ ("โห โห โห…") — ผู้ใช้ลบเองตอนเอา Transcript ไปใช้.

**Why:** ผู้ใช้บอก "ให้ทางผู้ใช้ไปพิจารณาเอาว่าจะตัดหรือลบได้เองไม่ต้องทำโปรเศษเพิ่ม". ตัวกรองแบบ heuristic อาจตัดคำพูดจริง และ `no_speech_threshold` ของ `transformers` 5.21.0 ไม่ช่วย (ลองแล้ว), temperature fallback crash.

**Rejected:**
- ตัดบรรทัดที่กินเต็มหน้าต่าง 30 วินาที — อาจตัดคำพูดจริงที่หายาก; ผู้ใช้ไม่ต้องการ
- VAD ก่อนถอด — งานเพิ่มนอก spec

**From:** build ticket 04 · **Status:** active

## D32: ยอมรับเวลาบรรทัดตามที่ Whisper long-form ให้ แม้บางบรรทัดคลาด 2–3 วินาที

**Chosen:** ใช้เวลาเริ่มและจบของบรรทัดตามที่ Whisper long-form ให้มา โดยไม่ปรับเพิ่ม. ตอนเช็คมือ build ticket 04 สุ่ม 5 บรรทัดของหนัง 1:35 ชม.: 3 บรรทัดคลาด 0.02, 0.64 และ 1.46 วินาที, 1 บรรทัดคลาด 2.50 วินาที (บรรทัดที่เริ่มตรงเวลาจบของบรรทัดก่อนพอดี), อีก 1 บรรทัดตรวจไม่ได้. ผู้ใช้ยอมรับและปิด ticket.

**Why:** ผู้ใช้เลือก "ยอมรับ ปิด ticket". เวลาใช้กระโดดไปฉากและทำ `.srt` ซึ่งคลาด 2–3 วินาทีก็ยังหาฉากเจอ. ทางแก้คือ timestamp ระดับคำ ซึ่งบน `mps` ช้ามาก (30 วินาทีของเสียงไม่จบใน 10 นาที).

**Rejected:**
- timestamp ระดับคำ (`return_timestamps="word"`) — ช้าเกินบน `mps`
- หยุด ticket ไปคิดใน `/warroom` — ผู้ใช้ไม่เลือก

**From:** build ticket 04 · **Status:** active

## D33: ของบนจอที่ design ของกล่องถอดบทพูดเพิ่มจาก spec

**Chosen:** เก็บสี่อย่างที่ frame 14–19 ใน Figma เพิ่มจาก spec:
- จอกว้าง: ช่องลิงก์, แถบความคืบหน้าของงานโหลด และรายการคลิปอยู่ในคอลัมน์ซ้ายกว้าง 520px; ลูกศร → กลาง; กล่องถอดบทพูดกินที่เหลือ. 375px เรียงช่องลิงก์ → รายการ → ลูกศร ↓ → กล่อง
- ข้อความหลังงานถอดจบ (`done`, `cancelled`, `failed`, poll ได้ `null`) และ `404` ของ `POST /transcriptions` เป็น `Alert` ในกล่อง ใต้ชื่อคลิปและความยาว เหนือปุ่มถอดหรือ Transcript; tone ตามข้อความหลังงานโหลด (`done` success, `cancelled` info, `failed` และ `404` error, `null` warning)
- ระหว่างถอดใช้ component `Download progress` เดิม: ข้อความ "กำลังถอด" ซ้าย, "{percent}%" ขวา; `preparing` ใช้แถบไม่มีตัวเลข
- Transcript ที่ไม่มีบรรทัด ("ไม่พบคำพูดในคลิปนี้") ไม่แสดงปุ่ม Copy, `.txt`, `.srt`

**Why:** ผู้ใช้เลือกเก็บทั้งสี่ตอนรับ design. เป็นตำแหน่งและหน้าตาบนจออย่างเดียว ไม่เปลี่ยน API หรือ state: ช่องลิงก์อยู่กับรายการเพราะเป็นที่มาของคลิป, ข้อความอยู่ในกล่องเพราะเป็นผลของงานในกล่อง, แถบ % ใช้ component เดียวกับงานโหลด, และไฟล์ว่างไม่มีอะไรให้ Copy หรือโหลด.

**Rejected:**
- แก้ design ให้ตรง spec เดิม — ผู้ใช้อยากเก็บไว้

**From:** design · **Status:** active

## D34: ทางเลือกเล็กตอน build กล่องถอดบทพูด

**Chosen:** รายละเอียดที่ build ticket 05 ตัดสินเองจาก conventions, Figma และโค้ดเดิม.

**Details:**
- **คลิปที่เลือก:** อยู่ใน `useTranscribe` (`selectedId`) ไม่ใช่ `useTempClips` เพราะเป็นของกล่อง (D25); แถวที่เลือก = แถว "กำลังเล่น" (D18)
- **status ตัวเดียว:** `useSpoilDownload` เก็บ `/api/setup/status` ไว้ใน state ให้กล่องคิดแถว gate ของงานถอด (`torch`, `transformers`, `ffmpeg`, `model_whisper`, `device`) เอง — ไม่ GET status ซ้ำ; `503` ของ `POST /transcriptions` GET status อย่างเดียวใหม่ ไม่มีหน้า loading และข้อความของงานโหลดยังอยู่
- **loading:** รอ `GET /transcriptions/current` ด้วย เพราะต้องรู้ว่าเลือกคลิปไหนตอนเปิด tab; ไม่ได้ → offline เหมือน route อื่น
- **เลือกเพราะงานยังไม่จบตอนเปิด tab:** ไม่ `autoPlay` (เล่นเองเฉพาะเมื่อผู้ใช้กดแถว) และโหลด Transcript เดิมไว้ — ถอดใหม่แล้วยกเลิกหรือล้มยังเห็นของเดิม; งานจบทุกแบบโหลด Transcript ของคลิปนั้นใหม่ (`404` ตอนนั้นแปลว่ายังไม่เคยถอด ไม่โหลดรายการซ้ำ)
- **`404` ของ `POST`:** รายการใหม่ไม่มีคลิปนั้นแล้ว กล่องจึงกลับเป็น "เลือกคลิปจากรายการ" พร้อม Alert "ไม่พบคลิปนี้" เหนือข้อความนั้น
- **`409` `busy`:** body ไม่บอกคลิป จึง GET `/transcriptions/current` แล้วตามงานนั้น: คลิปนี้ → แถบ %, คลิปอื่น → "กำลังถอด {ชื่อ}"
- **ข้อความหลังงานถอด:** ตั้งเฉพาะเมื่อคลิปของงานถูกเลือกอยู่ตอนงานจบ; หายเมื่อเลือกคลิปใหม่หรือกดถอด (frame 18). `done` จึงเห็น "ถอดเสร็จ" กับ "คลิปนี้ถอดแล้ว" พร้อมกันจนเลือกคลิปใหม่
- **ลบคลิปที่กำลังถอด:** ไม่ปลด player และไม่ล้างกล่อง เพราะ API ตอบ `409` `transcribing` แน่ — ความคืบหน้ายังเห็นอยู่ (คลิปที่เลือกอื่นๆ ยังปลด player ก่อนลบตาม D15)
- **Transcript `404` ทั้งที่ `transcribed`:** (ไฟล์ถูกลบด้วยมือ) โหลดรายการใหม่ให้แถวหาย "ถอดแล้ว"
- **ระหว่างถอดใหม่:** ซ่อน Transcript เดิมจนงานจบ แล้วโหลดใหม่ (frame 16 ไม่มี Transcript)
- **คลิปอื่นกำลังถอดแต่คลิปนี้ถอดแล้ว:** ปุ่ม disabled เขียน "ถอดใหม่" และยังเห็น Transcript เดิม
- **หน้าตา:** กล่องบรรทัดสูงไม่เกิน 320px (Figma สูง 320 คงที่) ให้ Transcript สั้นไม่มีที่ว่าง; hover ของบรรทัดใช้ `surface-strong` เพราะสี hover ใน Figma (`muted`) เท่ากับพื้นกล่อง; สองคอลัมน์ที่ ≥ 1024px ด้วย `PageLayout wide` (กว้าง 1120); ปุ่ม primary ใช้ `PRIMARY_BUTTON` ร่วมกับปุ่มโหลด (disabled `opacity-60` แทน 50 ใน Figma ให้สองปุ่มเท่ากัน)
- **ส่วนร่วม:** `ProgressCard` (component `Download progress`) และ `usePollWhile` (poll ทุก 1 วินาที) ใช้ทั้งงานโหลดและงานถอด; `NotReady`, `Notice` (`hooks/notice.ts`), `formatDuration`/`formatClock` (`components/format.ts`), `PRIMARY_BUTTON` (`components/ui/buttonStyles.ts`) ย้ายออกมาเมื่อมีผู้ใช้คนที่สอง

**From:** build ticket 05 · **Status:** active
