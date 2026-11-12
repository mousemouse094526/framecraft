# 08: โหลดคลิปจากหลายเว็บ

**What to build:** วางลิงก์คลิป public จาก Facebook, TikTok หรือเว็บอื่นที่ yt-dlp มีตัวโหลดเฉพาะ แล้วได้ Temp clip เหมือน YouTube: id ตามแหล่ง, เช็คซ้ำหลังอ่านข้อมูล, เลือกเฉพาะ h264/aac ด้านสั้น ≤ 1080 และตรวจไฟล์หลัง merge, error ใหม่ที่ชี้ให้เอาไฟล์เข้าเอง. หน้าเว็บแสดงข้อความใหม่และชื่อเว็บในแถวด้วย component เดิม. งานเตรียม: `CLIP_ID` แทน `VIDEO_ID` ทุกที่ และ model ที่ field เป็น `null` ได้ — ticket 09 ใช้ต่อ.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D47, D51, D52 (ตรวจลิงก์, error, ข้อมูลในแถว), D53, D54, D55 (ทุกข้อยกเว้นของ File import)
- ADR: 0027, 0029, 0008, 0011
- Seams: 1 (ข้อของลิงก์, id, format selector, ตัวตรวจไฟล์, ล้างตอน start, json ไม่มี `site`), 2 (Facebook, TikTok, HEVC), 4 (ข้อความของลิงก์, แถวชื่อเว็บ)
- User stories: 14
- Legal: 7

**Status:** done

## Acceptance criteria

### งานเตรียม

- `CLIP_ID` ใน `backend.spoil.links` ใช้ใน `check_known`, `clean_on_start` และตัวตรวจ id ของ `backend.spoil_maker`; คลิป id `facebook-123` เล่น ถอด ตัด บรรยายฉาก และลบได้
- ล้างตอน start ลบเฉพาะชื่อรูปที่แอปสร้าง (spec › Temp clip); `notes.txt` ใน `media/temp/` ไม่หาย
- `TempClip` ฝั่ง backend และ type ใน `frontend/src/lib/clips.ts` มี `site` และ `source_url`, `channel`, `yt_dlp_version` เป็น `null` ได้; json เดิมอ่าน `site` เป็น `Youtube`
- ตัวตรวจไฟล์ mp4 (spec › File import ขั้น 4: h264 `yuv420p`, aac, ≤ 1080, ข้าม `attached_pic`, rotation) เป็นฟังก์ชันเดียวที่ ticket 09 เรียกซ้ำ

### โหลดหลายเว็บ

- test ของ seam 1 ข้อลิงก์ id format selector ตัวตรวจไฟล์ และการล้างตอน start ผ่าน; test เดิมทั้งหมดผ่าน (`youtube_error` ใน test เดิมเปลี่ยนเป็น `download_error`)
- params ของ yt-dlp ตาม spec › Download: `format` selector, `allowed_extractors`, `socket_timeout`, `outtmpl` จาก `clip_id`
- error ทุกแถวในตารางแยก error และตาราง error ของ Download job ทำตาม spec
- ลองก่อนเขียนต่อ: format selector แบบ callable ทำงานกับ `extract_info` + `process_ie_result` ของ YouTube จริง; ไม่ได้ → หยุดแล้วถามผู้ใช้

### หน้าเว็บ

- seam 4 ข้อของลิงก์และแถวชื่อเว็บผ่าน; placeholder และข้อความว่างของรายการเป็นคำใหม่ตาม spec › Frontend
- ใช้ component เดิม (`Alert`, `Clip row`) — ไม่รอแบบของ ticket 10

### เช็คมือบน Mac

- seam 2: คลิป public ของ Facebook และ TikTok ได้ mp4 h264 ≤ 1080 เล่นได้; คลิป TikTok ที่มีแต่ HEVC ได้ `unsupported_format`; ข้อความ error จริงของลิงก์ที่ต้อง login และลิงก์ที่ไม่รองรับจดลง `docs/library-notes/yt-dlp.md`
- ข้อ Windows เพิ่มเข้า `windows-check` 02 (ADR-0016)
