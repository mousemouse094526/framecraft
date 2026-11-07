# Spec: spoil

ผู้ใช้วางลิงก์คลิปจาก YouTube หรือเว็บอื่นที่ yt-dlp โหลดได้ หรือเลือกไฟล์ mp4 ในเครื่อง ใน tab คลิป (spoil-maker D53, D47, D49) แล้วแอปเก็บคลิปเป็น Temp clip พร้อมหน้าต่างบอกว่าโหลดอะไรมา. จากนั้นเลือกคลิปเข้ากล่องถอดบทพูด แล้วกดให้ Whisper ถอดคำพูดเป็น Transcript ที่อ่าน คัดลอก และโหลดเป็นไฟล์ได้. ก่อนถอด ผู้ใช้ตัดช่วงที่ไม่ต้องการ (โฆษณา, เพลงเปิด-ปิด, ตัวอย่างตอนหน้า) ออกจากคลิปได้ ช่วงที่ตัดจึงไม่ไปถึง Transcript, Shot, EP หรือ Spoil draft.

**Status:** ready-to-build

## Problem

ผู้ใช้ทำคลิปสปอยหนังจากคลิปบน YouTube แต่ framecraft ยังไม่มีทางเอาคลิปต้นทางเข้ามาในแอป. ต้องโหลดด้วยเครื่องมืออื่นแล้วจัดไฟล์เอง.

## Solution

- tab ด้านบนของแอป 3 tab: ติดตั้ง · คลิป · สปอย (D10, spoil-maker D53)
- วางลิงก์คลิปเดียวจาก YouTube หรือเว็บอื่นที่ yt-dlp โหลดได้โดยไม่ต้อง login แล้วโหลดคลิปทุกแนวที่ด้านสั้นไม่เกิน 1080 px เป็น mp4 (D5, D47)
- เลือกไฟล์หรือลากไฟล์ mp4 (h264/aac ด้านสั้น ≤ 1080 px) มาวาง แอป copy เข้าเป็น Temp clip ไม่แปลง; ไฟล์ไม่ตรง → บอกเหตุให้ผู้ใช้แปลงเอง (D49, D50)
- คลิปซ้ำ (ลิงก์เว็บเดียวกัน id เดียวกัน หรือไฟล์ชื่อและขนาดเท่ากัน) ชี้แถวเดิม (D12, D51)
- เห็น % ระหว่างโหลด และกดยกเลิกได้ (D6)
- เห็นรายการ Temp clip ที่โหลดมา เล่นดูในหน้าเว็บ และกดลบได้ (D3, D7)
- Setup script ติดตั้ง yt-dlp กับ Deno และ Status check บอกว่าติดตั้งครบไหม (D1, D8, D9)
- เลือก Temp clip เข้ากล่องถอดบทพูดทางขวาของรายการใน tab คลิป มีลูกศรคั่นกลาง (D25, spoil-maker D53)
- กดถอด → Whisper large-v3-turbo ถอดคำพูดทุกภาษาเป็น Transcript พร้อมเวลา เห็น % และยกเลิกได้ (D21, D24, D26)
- Transcript เก็บคู่คลิป แถวแสดง "ถอดแล้ว", Copy ทั้งหมด, โหลด `.txt` และ `.srt` (D22, D23); แก้ข้อความทีละบรรทัดได้ (spoil-maker D54)
- ตัดช่วงออกจาก Temp clip บน timeline ใต้ player: เลือกหลายช่วง แล้วแอป encode mp4 ใหม่แทนไฟล์เดิม (D36, D38)
- ตัดคลิปที่มี Transcript, Shot, การตัด EP หรือ Spoil draft → เตือน ยืนยัน แล้วลบทั้งหมด (D37, ADR-0021)

## User Stories

**ผู้ทำคลิปสปอย**
1. As a ผู้ทำคลิปสปอย, I want สลับ tab ติดตั้ง คลิป และสปอยได้จากด้านบน, so that ใช้งานและเช็คการติดตั้งในแอปเดียว (D10)
2. As a ผู้ทำคลิปสปอย, I want วางลิงก์ YouTube แล้วกดโหลด, so that คลิปต้นทางมาอยู่ในเครื่องพร้อมทำต่อ (D2, D5)
3. As a ผู้ทำคลิปสปอย, I want เห็น % ระหว่างโหลดและยกเลิกได้, so that รู้ว่าคลิปยาวยังเดินอยู่ และหยุดเมื่อวางลิงก์ผิด (D6)
4. As a ผู้ทำคลิปสปอย, I want เห็นรายการคลิปที่โหลดมาและเล่นดูได้, so that เช็คว่าได้คลิปถูกตัว (D7)
5. As a ผู้ทำคลิปสปอย, I want ลบคลิปที่ไม่ใช้, so that ดิสก์ไม่เต็ม (D3)
6. As a ผู้ทำคลิปสปอย, I want รู้ทันทีเมื่อวางลิงก์ที่โหลดไปแล้ว, so that ไม่โหลดซ้ำ (D12)
7. As a ผู้ทำคลิปสปอย, I want รู้ว่าทำไมโหลดไม่ได้และต้องแก้ยังไง, so that แก้เองได้ (D8, D11)
8. As a ผู้ทำคลิปสปอย, I want เลือกคลิปแล้วกดถอดบทพูด, so that ได้คำพูดทั้งเรื่องไปวิเคราะห์เขียนบทสปอย (D21, D23, D25)
9. As a ผู้ทำคลิปสปอย, I want เห็น % ระหว่างถอดและยกเลิกได้ ระหว่างที่โหลดคลิปอื่นอยู่ก็ได้, so that รู้ว่าหนังยาวยังเดิน และไม่ต้องรอกัน (D24, D26)
10. As a ผู้ทำคลิปสปอย, I want อ่าน Transcript พร้อมเวลา กดบรรทัดแล้วกระโดดไปฉากนั้น, Copy และโหลด `.txt`/`.srt`, so that เอาไปใช้ที่อื่นได้ทันที (D22)
11. As a ผู้ทำคลิปสปอย, I want เห็นว่าคลิปไหนถอดแล้ว และเปิดแอปใหม่ก็ยังอยู่, so that ไม่ต้องถอดซ้ำ (D23)
12. As a ผู้ทำคลิปสปอย, I want เลือกช่วง A–B และ C–D บน timeline แล้วตัดออกจากคลิป, so that โฆษณา เพลงเปิด-ปิด และตัวอย่างตอนหน้าไม่ไปถึง Transcript, Shot, EP และบทสปอย (D36, D38)
13. As a ผู้ทำคลิปสปอย, I want เห็น % ระหว่างตัด ยกเลิกได้ และรู้ก่อนว่าการตัดจะลบอะไรของคลิป, so that ไม่เสีย Transcript หรือ Spoil draft โดยไม่รู้ตัว (D37, D41)
14. As a ผู้ทำคลิปสปอย, I want วางลิงก์จาก Facebook, TikTok หรือเว็บอื่นได้เหมือน YouTube, so that ใช้คลิปต้นทางจากที่ไหนก็ได้ที่โหลดแบบสาธารณะได้ (D47)
15. As a ผู้ทำคลิปสปอย, I want เลือกหรือลากไฟล์ mp4 ในเครื่องเข้ามา เห็น % และยกเลิกได้, so that ใช้คลิปที่โหลดเองจากเว็บที่แอปโหลดไม่ได้ (D47, D49, D50)

## Design

| Screen | User stories | Must show | Source |
|---|---|---|---|
| แถบ tab | 1 | tab "ติดตั้ง" · "คลิป" · "สปอย" ตามลำดับนี้, tab ที่เปิดอยู่เด่นกว่า (D10, spoil-maker D53) | [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) — header ของทุก frame; component `Tab`. เดิม 2 tab: [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frame "Tab bar / Setup status active" |
| tab คลิป | 2, 3, 6, 7, 14, 15 | ช่องลิงก์ (placeholder ไม่ผูก YouTube) กับปุ่ม "โหลด"; ปุ่ม "เลือกไฟล์ในเครื่อง" (รับ `.mp4`) และพื้นที่ลากไฟล์มาวางที่บอกว่ารับ mp4 h264 ≤ 1080p (D49, D50); ระหว่างส่งไฟล์: ชื่อไฟล์, แถบ %, ปุ่ม "ยกเลิก", "กำลังตรวจไฟล์…" หลังส่งครบ; error ของไฟล์ที่ไม่ตรงพร้อมบอกให้แปลงเอง; error `unsupported` และ `login_required` ชี้ไปที่ปุ่มเลือกไฟล์ (D52); ระหว่างโหลด: ชื่อคลิปเมื่อรู้แล้ว, แถบ % (ไม่รู้ขนาด → แถบไม่มีตัวเลข), ปุ่ม "ยกเลิก" (ซ่อนตอนรวมไฟล์), ปุ่มโหลด disabled (D6, D15); ข้อความ error ตาราง Frontend รวมเวอร์ชัน yt-dlp และคำสั่งอัปเดต (D8); ลิงก์ซ้ำ → highlight แถวเดิม (D12); ติดตั้งไม่ครบ → ข้อความกับลิงก์ "ไปหน้าติดตั้ง" แทนช่องลิงก์ (D9, D10); backend offline → ข้อความเดียวกับหน้า Setup status (setup-status D21) pending — current: [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frames: 1 loading, 2–3 idle, 4 downloading, 5 progress states, 6 done, 7 failed with fix, 8 messages, 9 duplicate, 11 not ready, 12 offline, 13 mobile 375px; component `Download progress` |
| หน้าต่างรายการ Temp clip | 4, 5 | ใน tab คลิปใต้ช่องลิงก์; แถวใหม่สุดก่อน: thumbnail, ชื่อคลิป, ชื่อช่อง, ความยาว, ขนาดภาพกับแนว "ตั้ง" หรือ "นอน", ขนาดไฟล์, เวลาโหลด, ปุ่มลบพร้อมยืนยัน และ error เมื่อลบไม่ได้ (D7, D15); กดแถว → player เล่นคลิปนั้น (D7); แถวของเว็บอื่นแสดงชื่อเว็บ, แถวของไฟล์ในเครื่องแสดง "ไฟล์ในเครื่อง" แทนชื่อช่อง (D52); state ว่าง: "ยังไม่มีคลิป วางลิงก์หรือเลือกไฟล์ด้านบน" | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frames: 2 empty, 3 list, 6 and 9 highlight, 10 playing and delete error; component `Clip row` (D18) |
| layout สองคอลัมน์ของ tab คลิป | 8 | จอกว้าง: รายการคลิปซ้าย, ลูกศร → กลาง, กล่องถอดบทพูดขวา; 375px เรียงบนลงล่างพร้อมลูกศร ↓ (D25); แถวที่เลือกเด่นกว่า; แถวที่ถอดแล้วมีสถานะ "ถอดแล้ว" (D23); ช่องลิงก์กับแถบโหลดอยู่คอลัมน์ซ้ายเหนือรายการ (D33) | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frames: 14 nothing selected, 15 selected, 16 transcribing while downloading, 17 transcribed, 19 mobile 375 stacked; component `Clip row` (property `Show transcribed`), icon `icon/arrow-right`, `icon/arrow-down`; ใน tab คลิป: [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) — frame คลิป |
| กล่องถอดบทพูด | 8–11 | ยังไม่เลือก: "เลือกคลิปจากรายการ"; เลือกแล้ว: player, ชื่อคลิป, ความยาว, ปุ่ม "ถอดบทพูด" (ถอดแล้ว → "ถอดใหม่" พร้อม alert "คลิปนี้ถอดแล้ว"); ระหว่างถอด: "กำลังเตรียมเสียง…" หรือ "กำลังถอด {n}%" กับแถบ % และปุ่ม "ยกเลิก"; Transcript: บรรทัด `[hh:mm:ss] ข้อความ` กดได้, ภาษาที่ตรวจได้, ปุ่ม Copy, `.txt`, `.srt`; ว่าง: "ไม่พบคำพูดในคลิปนี้"; error ของงานถอด; ติดตั้งไม่ครบ: ข้อความกับลิงก์ "ไปหน้าติดตั้ง" แทนปุ่มถอด (D22–D27); ข้อความหลังงานจบเป็น Alert ในกล่อง (D33); ชี้บรรทัดแล้วมีปุ่ม "แก้", กำลังแก้: ช่องพิมพ์กับ "บันทึก" และ "ยกเลิก", บรรทัดที่แก้แล้วมีป้าย "แก้แล้ว" (spoil-maker D54) | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — component `Transcript panel` (ทุก state), `Transcript line`, `Player`; frames: 14–17, 18 messages, 19 mobile; แก้บรรทัด: [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) — frames คลิป และ คลิป — แก้ประโยค; component `Transcript line` state hover, editing, edited |
| ส่วนตัดช่วง | 12, 13 | ในกล่องถอดบทพูดใต้ชื่อคลิป: ปุ่ม "ตัดช่วง"; timeline เต็มกว้างกล่องที่มีช่วงที่จะตัดเป็นแถบทึบ หัวท้ายลากได้ และตำแหน่งเล่น; แต่ละช่วงมีเวลาเริ่ม-จบที่พิมพ์ได้, "เริ่ม = ตอนนี้", "จบ = ตอนนี้", ลบช่วง; "เพิ่มช่วง"; "ตัดออก {x} · เหลือ {y}"; ปุ่ม "ตัดคลิป" และ "ยกเลิก"; ปุ่มถอด disabled พร้อมเหตุผลระหว่างเลือกช่วง; ระหว่างตัด: player ว่าง, "กำลังตัดคลิป {n}%" กับแถบ % และ "ยกเลิก", "กำลังแทนไฟล์…" ไม่มีปุ่มยกเลิก; คำยืนยันที่บอกสิ่งที่จะถูกลบ; Alert ผลหลังงานจบ; คลิปอื่นกำลังตัด: "ตัดช่วง" disabled กับ "กำลังตัด {ชื่อ}"; แถว Temp clip ที่ตัดแล้วมีป้าย "ตัดแล้ว"; 375px ใช้แบบเดียวกันเรียงในกล่อง หัวลากแตะได้ ≥ 44px (D36–D41) | [Figma: Components — ตัดช่วง](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8094-49867) — component `Trim timeline`, `Trim range row`, `Trim section`, `icon/scissors`; `Transcript panel` state trim closed, trim open, trim running, trim other clip (property `Show trim alert`); `Clip row` property `Show trimmed`. frames "คลิป — ตัดช่วง / 1–13 / desktop" ([start](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8098-50405)) และ 3, 6, 9 / mobile (D44) |

ออกแบบใน Figma หลัง plan (setup-status D9) ในไฟล์เดียวกับหน้า Setup status. Section "framecraft — สปอย" มี component `Tab`, `Clip row`, `Download progress` และ frame ทุก state; ใช้ token และ component ของหน้า `:: Token` (Button, Field, Alert, Badge, icon).

## Expected Outcome

ผู้ใช้เอาคลิปจาก YouTube เว็บอื่น หรือไฟล์ในเครื่องเข้า framecraft ได้ในแอปเดียว.

- **วางลิงก์คลิปแนวตั้ง:** เห็น % เดินจนครบ แล้วคลิปขึ้นบนสุดของรายการ ขนาดภาพเป็นขนาดใหญ่สุดของต้นทางที่ด้านสั้นไม่เกิน 1080 (เช่น "1080×1920 ตั้ง" หรือ "720×1280 ตั้ง") (D5)
- **วางลิงก์หนังแนวนอนยาว 2 ชั่วโมง:** โหลดได้ ได้แถว "นอน" ที่ด้านสั้นไม่เกิน 1080
- **วางลิงก์ซ้ำ:** ไม่โหลด แถวเดิมถูก highlight
- **วางลิงก์คลิป public ของ Facebook หรือ TikTok:** โหลดได้เหมือน YouTube แถวแสดงชื่อเว็บ (D47)
- **วางลิงก์เว็บที่ yt-dlp ไม่รู้จัก:** "เว็บนี้โหลดอัตโนมัติไม่ได้…" ชี้ปุ่มเลือกไฟล์ (D52)
- **ลากไฟล์ mp4 1080p ขนาด 2 GB มาวาง:** % เดินจนครบ แถวใหม่ "ไฟล์ในเครื่อง" ชื่อตามไฟล์ เล่น ถอด ตัด ได้เหมือนคลิปที่โหลด; ไฟล์ต้นฉบับไม่เปลี่ยน (D49)
- **เลือกไฟล์ `.mkv` หรือ mp4 4K/HEVC:** ไม่รับ บอกว่าไม่ตรงข้อไหนและให้แปลงเป็น mp4 h264 ≤ 1080p เอง (D49)
- **เลือกไฟล์เดิมซ้ำ:** ไม่ส่ง แถวเดิมถูก highlight (D51)
- **กดยกเลิกกลางทาง:** งานหยุด ไม่มีแถวใหม่ ไม่มีไฟล์ค้างใน `media/temp/.partial/`
- **เลือกหนังภาษาอังกฤษ 1:35 ชม. แล้วกดถอด:** % เดินจนครบ เห็น Transcript ทีละบรรทัดพร้อมเวลา ภาษา "en"; กดบรรทัดแล้ว player กระโดดไปเวลานั้น; แถวในรายการขึ้น "ถอดแล้ว" (D22, D23)
- **ถอดระหว่างโหลดคลิปอื่น:** ทั้งสองงานเดินไปพร้อมกันจนจบ (D24)
- **ลบคลิปที่ถอดแล้ว:** `{id}.transcript.json` หายพร้อมคลิป (D23)
- **ตัด 0:00–1:30 และ 1:55:10–1:58:02 ของหนัง 1:58:02:** % เดินจนครบ ความยาวในแถวเป็น 1:53:40 พร้อมป้าย "ตัดแล้ว", player เริ่มที่ฉากแรกของเรื่อง และไม่มีตอนจบที่ตัดไป (D36)
- **ตัดคลิปที่ถอดและบรรยายฉากแล้ว:** เห็นคำยืนยันว่า Transcript, ภาพฉาก และการตัด EP จะถูกลบ; ยืนยันแล้วตัดเสร็จ แถวไม่มี "ถอดแล้ว" และ "บรรยายฉากแล้ว" (D37)

**How success is judged:**
- บน Mac หลังรัน `./setup.sh`: หน้า Setup status มี 11 แถว รวม `yt_dlp` และ `deno` เป็น `ok`
- โหลด YouTube Shorts หนึ่งคลิปและคลิปแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิปได้จริง แต่ละไฟล์เล่นได้ใน player ของหน้าเว็บ
- ไฟล์ที่ได้เป็น mp4 และด้านสั้นไม่เกิน 1080 px
- restart `npm run dev` แล้วรายการเดิมยังอยู่ครบ
- โหลดคลิป public หนึ่งคลิปจาก Facebook และหนึ่งคลิปจาก TikTok ได้จริง เล่นได้ใน player; เอาไฟล์ mp4 ในเครื่องเข้ายาวกว่า 1 ชั่วโมงได้ และถอดกับตัดได้ (D47, D49)
- ถอด Shorts ภาษาไทยหนึ่งคลิปและหนังแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิปได้จริง; Copy แล้ววางได้ข้อความครบ; `.srt` เปิดใน VLC แล้ว subtitle ตรงเวลา; restart `npm run dev` แล้วยังเห็น Transcript
- ยกเลิกงานถอดแล้ว process ลูกหยุดภายใน 5 วินาที และ Transcript เดิม (ถ้ามี) ยังอยู่
- ตัดหนังยาวกว่า 1 ชั่วโมงสองช่วงบน Mac: ไฟล์ใหม่เล่นได้ใน player, ความยาวตรงกับที่คาดภายใน 1 วินาที, ภาพและเสียงตรงกันที่รอยตัด (ดูสามจุดรอบรอยตัด), ขนาดไฟล์ต่อนาทีไม่เกิน 1.2 เท่าของเดิม; ถอดคลิปที่ตัดแล้วไม่มีบรรทัดของช่วงที่ตัด
- ยกเลิกงานตัดแล้ว ffmpeg หยุดภายใน 5 วินาที, ไฟล์เดิมเล่นได้ และ Transcript เดิมยังอยู่
- ทำซ้ำข้อบนทั้งหมดบน Windows NVIDIA หลังรัน `setup.cmd` — เช็คใน `windows-check` 02 ไม่ขวางการจบ feature (ADR-0014)

## Implementation

### Modules touched

- **root**
  - `pyproject.toml` กับ `uv.lock`: เพิ่ม `yt-dlp[default,deno]` (extra `deno` ดึง package `deno` มาด้วย) (D8)
  - `.gitignore`: เพิ่ม `media/` (D14)
  - `README.md`: tab สปอย, ที่เก็บ `media/temp/` และวิธีอัปเดต yt-dlp (D3, D8)
- **backend**
  - `backend.paths`: เพิ่ม `media_temp_dir` = `{root}/media/temp` และ `partial_dir` = `{root}/media/temp/.partial` (D3, D14)
  - `backend.checks`: เพิ่มแถว `yt_dlp` และ `deno` (D9)
  - `backend.spoil` (package ใหม่): ตรวจลิงก์, Download job, คลังของ Temp clip และ adapter ที่คุยกับ yt-dlp ตัวเดียว (D6, D14)
  - `backend.routes.spoil`: route ใน ตาราง API (D6, D7)
  - `backend.app`: include router ของ spoil, lifespan ที่ล้างไฟล์ค้างตอน start และตั้ง flag ยกเลิกตอน shutdown, `TrustedHostMiddleware` (D14, D15); ตั้ง flag ยกเลิกของ Transcribe job ตอน shutdown ด้วย
  - `backend.spoil.transcribe` (ใหม่): Transcribe job, ไฟล์ Transcript, `.txt` และ `.srt` (D23, D24, D27)
  - `backend.spoil.whisper` (ใหม่): adapter ตัวเดียวที่ import `transformers` และ `torch` สำหรับถอด, เรียก ffmpeg ดึงเสียง และ `worker` ที่รันใน process ลูก (D27, D28)
  - `backend.routes.spoil`: `POST` ต้อง `Content-Type: application/json` (D29)
  - `backend.spoil.clips`: ลบ `{id}.transcript.json` พร้อมคลิป, field `transcribed` ในรายการ, `409` `transcribing` (D23, D27)
  - `backend.spoil.trim` (ใหม่): Trim job, ตรวจช่วง, คำสั่ง ffmpeg และการแทนไฟล์ (D36, D41)
  - `backend.spoil.clips`: field `trimmed` และ `trimmed_at` ใน json, ลบข้อมูลจากคลิปแยกจากการลบคลิป ให้ Trim job ใช้ส่วนเดียวกัน, ทำ marker `{id}.trimming.json` ต่อตอน start, `409` `trimming` (D37, D41)
  - `backend.spoil.transcribe` และ `PATCH` บรรทัด: คลิปที่ Trim job ยังไม่จบ → `409` `trimming` (D41)
  - `backend.spoil.links`: ลิงก์ YouTube ตามตารางเดิม หรือลิงก์ `http(s)` อื่นที่ host ไม่ใช่ loopback/private; `CLIP_ID` = `[A-Za-z0-9_-]{1,64}` แทน `VIDEO_ID` ทุกที่ที่ใช้เป็นชื่อไฟล์หรือ path (D51, D52)
  - `backend.spoil.downloads` และ `adapter`: id จาก `extractor_key` กับ `id` หลัง `fetch_info`, เช็คซ้ำหลัง `checking`, error `unsupported`, `playlist`, `download_error`, field `site` (D51, D52)
  - `backend.spoil.clips`: `TempClip.source_url`, `channel`, `yt_dlp_version` เป็น `Optional`, เพิ่ม `site`; `check_known` และ `clean_on_start` ใช้ `CLIP_ID`; `backend.spoil_maker` ที่ตรวจ id ของคลิปใช้ `CLIP_ID` เดียวกัน (D55)
  - `backend.spoil.imports` (ใหม่): File import — รับ body ดิบ, เช็คดิสก์, ตรวจ mp4 ด้วย ffmpeg, thumbnail, เขียน json (D49–D52)
  - `backend.app` และ `backend.body_types` (ใหม่): `require_json` ตัวเดิม (ย้ายไป `body_types`) ยกเว้น route ที่มี dependency `require_octet_stream` ของตัวเอง ตอนนี้มีแค่ `POST /api/spoil/imports` ที่รับ `application/octet-stream` อย่างเดียว (D50, D55, D57)
  - `backend.gpu` (ของ spoil-maker): `GpuSlot.trimming_clip` — `take()` และ `clip_untouched` ปฏิเสธคลิปที่กำลังตัด เพื่อให้ Describe, Draft, Voice, Render job และ `PUT` การตัด EP ของคลิปนั้นได้ `409` `clip_busy` (spoil-maker D49, D55, D42); แก้เฉพาะจุดนี้; `begin_render`/`end_render` ทำเครื่องหมายคลิปที่ Render job อ่าน (render ที่ไม่ต้องสร้างเสียงไม่จองช่อง GPU) ให้ Trim job ของคลิปนั้นได้ `clip_busy` และ render ระหว่างตัดได้ `clip_busy` (D46)
- **frontend**
  - `App`: แถบ tab; hook `useHashTab` ใน `lib/` อ่านและเขียน hash. ไม่มี folder `routes/` เพราะไม่ใช้ router (D10). บันทึกเรื่องนี้ใน skill `vite-react-web`
  - `features/spoil/` (folder ใหม่): ช่องลิงก์, แถบความคืบหน้า, รายการ Temp clip และ player (D6, D7); layout สองคอลัมน์และกล่องถอดบทพูด `TranscriptPanel` กับ hook `useTranscribe` (D22, D25). player ย้ายจากเหนือรายการเข้ากล่อง
  - `lib/api`: เพิ่ม `sendJson<T>(method, path, body?)` คืน `{ status, body }` ที่ body เป็น JSON หรือ `null` เมื่อไม่มี body; throw เฉพาะ network ล้มหรือเกิน 30 วินาที. timeout เดียวกับ `getJson`
  - `components/ui/`: ย้าย `OfflinePanel` จาก `features/setup-status` มาที่นี่ เพราะ tab สปอยใช้ด้วย
  - `lib/statusTypes`: ย้าย type ของ `/api/setup/status` ออกจาก `features/setup-status` เพราะ tab สปอยอ่านด้วย
  - `features/spoil/`: ปุ่มเลือกไฟล์และพื้นที่ลากวางใน `LinkForm`, hook `useFileImport` (XHR เพราะ `fetch` ไม่บอก upload progress), แถว "ไฟล์ในเครื่อง"/ชื่อเว็บใน `TempClipList`; type ของ `lib/clips` ให้ `source_url`, `channel`, `yt_dlp_version` เป็น `null` ได้และมี `site` (D52)
  - `features/spoil/`: ส่วนตัดช่วง `TrimSection` กับ hook `useTrim` ในกล่องถอดบทพูด, ป้าย "ตัดแล้ว" ใน `Clip row`, `?v=` ของ `src` ใน player (D38, D41)

### Dependencies

| Package | Version | ใช้ทำอะไร |
|---|---|---|
| `yt-dlp[default,deno]` | latest ตอน lock แล้ว pin ใน `uv.lock` | โหลดคลิป YouTube และเว็บอื่น (D47); extra `default` มี `yt-dlp-ejs`, extra `deno` มี package `deno` ที่เป็น JavaScript runtime (D8) |

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| yt-dlp | latest ตอน lock (2026.10.26 ตอนเขียน) | `YoutubeDL(params).extract_info(url, download=False)` คืน metadata โดยไม่โหลด แล้ว `process_ie_result` หรือ `download` โหลดตาม format ที่เลือก | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `format_sort: ["res:1080", "vcodec:h264", "acodec:aac"]`: `res` คือด้านสั้นของภาพ, `res:1080` เลือกตัวใหญ่สุดที่ไม่เกิน 1080 และถ้าไม่มีเอาตัวเล็กสุด | [README › Sorting Formats](https://github.com/yt-dlp/yt-dlp#sorting-formats) |
| yt-dlp | เดียวกัน | `merge_output_format: "mp4"` และ `ffmpeg_location` รับ path ของ binary ตรงๆ (ชื่อ binary ของ imageio ขึ้นต้นด้วย `ffmpeg`) | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `js_runtimes: {"deno": {"path": ...}}` ชี้ Deno ที่ไม่อยู่บน PATH | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `progress_hooks` ได้ dict ที่มี `status`, `downloaded_bytes`, `total_bytes`, `total_bytes_estimate`; raise `yt_dlp.utils.DownloadCancelled` ใน hook หยุดการโหลด | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `paths: {"home": ..., "temp": ...}` แยกไฟล์ระหว่างโหลดออกจากไฟล์ผลลัพธ์, `noplaylist: True` โหลดคลิปเดียวเมื่อลิงก์มี `list=` | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | YouTube ต้องมี JavaScript runtime; Deno ≥ 2.3.0 | [yt-dlp EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS) |
| yt-dlp | เดียวกัน | error ตอนโหลดเป็น `yt_dlp.utils.DownloadError` ที่ `exc_info[1]` คือ exception ต้นทาง (`GeoRestrictedError`, `ExtractorError` ที่ `expected=True`); คลิป upcoming ทำให้ `extract_info` raise เพราะไม่มี format | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `extract_info` ของลิงก์ที่ไม่มีตัวโหลดเฉพาะใช้ generic extractor; หาวิดีโอไม่เจอ raise `DownloadError` ที่ข้อความมี "Unsupported URL"; info มี `extractor_key` (เช่น `Youtube`, `Facebook`, `TikTok`) และ `id`; ลิงก์ playlist กับ `noplaylist` ที่เว็บไม่รองรับ ได้ `_type` `playlist` | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py), [supportedsites.md](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| starlette | 1.10.0 | `await request.stream()` ให้ body ทีละก้อนโดยไม่เก็บทั้งไฟล์ใน memory; client ตัดการเชื่อมต่อกลางทาง → `ClientDisconnect` | [Starlette requests](https://www.starlette.io/requests/#body) |
| browser `XMLHttpRequest` | — | `xhr.upload.onprogress` ให้ `loaded`/`total` ระหว่างส่ง body; `abort()` ตัดการเชื่อมต่อ; `fetch` ไม่มี upload progress | [MDN XMLHttpRequest.upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload) |
| ffmpeg (imageio) | 7.1 | stderr ของ `ffmpeg -hide_banner -i {file}` มี `Stream #0:… Video: h264 …, {w}x{h}` และ `Audio: aac` และ `Duration:`; `-ss {t} -i {file} -frames:v 1 {id}.jpg` ได้ thumbnail | [ffmpeg docs](https://ffmpeg.org/ffmpeg.html) |
| deno (PyPI) | latest ตอน lock (2.9.8 ตอนเขียน) | wheel macOS arm64 และ Windows amd64 มี binary, `deno.find_deno_bin()` คืน path | [deno on PyPI](https://pypi.org/project/deno/) |
| starlette | 1.10.0 (มากับ fastapi 0.162.0) | `FileResponse` ตอบ HTTP Range ให้ `<video>` seek ได้ | [Starlette responses](https://www.starlette.io/responses/#fileresponse) |
| imageio-ffmpeg | 0.7.0 | `get_ffmpeg_exe()` คืน path ffmpeg ที่ใช้ merge (ADR-0005) | [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) |
| transformers | 5.21.0 | `pipeline("automatic-speech-recognition", model=<folder snapshot>, device=..., dtype=...)` โหลด Whisper จาก folder ในเครื่อง; รับ `numpy` float32 16 kHz ไม่ต้องใช้ ffmpeg บน PATH; ไม่ส่ง `chunk_length_s` (experimental สำหรับ Whisper ตาม `pipelines/automatic_speech_recognition.py:306`) ให้ Whisper ถอด long-form เอง; `return_timestamps=True` คืน `chunks` ที่มี `timestamp` (เริ่ม, จบ) และ `text`; `return_language=True` ใส่ `language` ใน `chunks[i]` ไม่มีค่าบนสุด และอ่านจาก batch item แรกเท่านั้น จึงใช้ `batch_size` 1 | [ASR pipeline](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines#transformers.AutomaticSpeechRecognitionPipeline), [Whisper](https://huggingface.co/docs/transformers/v5.21.0/en/model_doc/whisper) |
| ffmpeg (imageio) | เดียวกับบน | `ffmpeg -ss {start} -t {length} -i {id}.mp4 -vn -ac 1 -ar 16000 -f f32le -` ส่ง PCM float32 ของช่วงเดียวออก stdout; คลิปไม่มีเสียงได้ exit ไม่เป็น 0 | [ffmpeg docs](https://ffmpeg.org/ffmpeg.html) |
| ffmpeg (imageio) | 7.1 | `-filter_complex` ด้วย `trim=start:end,setpts=PTS-STARTPTS` กับ `atrim=start:end,asetpts=PTS-STARTPTS` ต่อช่วงที่เหลือ แล้ว `concat=n={k}:v=1:a=1` (ไม่มีเสียง → `a=0` ไม่มี `atrim`); encoder `h264_videotoolbox` (Mac) และ `libx264` (Windows) รับ `-b:v`; `aac` รับ `-b:a`; `-movflags +faststart`; `-progress pipe:1` ให้ `out_time_us` | [ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html), [ffmpeg docs](https://ffmpeg.org/ffmpeg.html), [H.264 encoding guide](https://trac.ffmpeg.org/wiki/Encode/H.264) |
| ffmpeg (imageio) | 7.1 | `ffmpeg -hide_banner -i {id}.mp4` (ไม่มี output) exit ไม่เป็น 0 แต่ stderr มีบรรทัด `Stream #0:… Audio:` เมื่อคลิปมีเสียง — ใช้แทน ffprobe (ADR-0005) | [ffmpeg docs](https://ffmpeg.org/ffmpeg.html) |
| Python `os.replace` | 3.12 | แทนไฟล์แบบ atomic เมื่ออยู่ใน volume เดียวกัน; บน Windows ล้มด้วย `PermissionError` เมื่อไฟล์ปลายทางยังเปิดอยู่ | [os.replace](https://docs.python.org/3.12/library/os.html#os.replace) |
| Python `multiprocessing` | 3.12 | `get_context("spawn").Process` และ `Queue`; `terminate()` ส่ง SIGTERM บน Mac และ `TerminateProcess` บน Windows; `exitcode` ติดลบเมื่อตายด้วย signal | [multiprocessing](https://docs.python.org/3.12/library/multiprocessing.html) |

ข้อที่ ticket 01 ต้องลองกับ YouTube จริงก่อนเขียนต่อ: ยกเลิกด้วย `DownloadCancelled` จาก hook ได้, merge ด้วย ffmpeg ของ imageio ที่ไม่มี ffprobe (ADR-0005) ได้, ลิงก์ upcoming ได้ error ที่แยกเป็น `live` ได้, และข้อความ error ของ bot check หรือ login ที่ใช้แยก `login_required`. ยกเลิกไม่ได้ → ย้ายการโหลดไป `multiprocessing.Process` แล้ว terminate. merge ไม่ได้ → หยุดแล้วถามผู้ใช้ก่อน เพราะ format ไฟล์เดียวบน YouTube ส่วนใหญ่ไม่ถึง 1080 (ขัด D5); ทางเลือกคือหา ffprobe มาเพิ่ม (ขัด ADR-0005) หรือยอมความคมต่ำลง; ผลเป็น `D{n}` ใหม่.

ข้อที่ ticket ของงานถอดต้องลองก่อนเขียนต่อ: Whisper บน `mps` ด้วย `float16` ได้ผลถูก (ไม่ได้ → `float32` บน `mps`); pipeline รับ array 300 วินาทีโดยไม่มี `chunk_length_s` แล้วถอดแบบ long-form ได้ครบทั้งช่วง (ไม่ได้ → หยุดแล้วถาม เพราะทางเลือกคือ `chunk_length_s` ที่ library บอกว่า experimental); timestamp ของ `chunks` เป็นเวลาภายในช่วง; บรรทัดสุดท้ายที่ `timestamp` จบเป็น `None` → ใช้ความยาวของช่วงแทน; process ลูก `spawn` import `backend` ได้ทั้ง Mac และ Windows.

ข้อที่ ticket ของงานตัดต้องลองก่อนเขียนต่อ: `trim` กับ `concat` ของคลิปจริงยาวกว่า 1 ชั่วโมงสองช่วงได้ภาพและเสียงตรงกันที่รอยตัด; `h264_videotoolbox` ที่ `-b:v` เท่าไฟล์เดิมได้ภาพที่ดูไม่ต่างจากเดิม; เวลาที่ใช้ของหนัง 2 ชั่วโมงบน Mac (เขียนลง progress.md). ภาพและเสียงคลาดกัน → หยุดแล้วถาม เพราะทางเลือกคือ `select`/`aselect` หรือ encode ทีละช่วงแล้ว concat demuxer ซึ่งเปลี่ยนวิธีวัด %; ผลเป็น `D{n}` ใหม่.

### Status check

เพิ่มสองแถวต่อจาก `ffmpeg` ใน `backend.checks.run_checks` รวมเป็น 11 แถว (D9). กฎของ check เดิมใช้ทั้งหมด (setup-status D7).

| `id` | `label` | `ok` เมื่อ | ไม่ `ok` | `fix` |
|---|---|---|---|---|
| `yt_dlp` | yt-dlp | `importlib.metadata.version("yt-dlp")` ได้. `detail` = เวอร์ชัน | `missing` | คำสั่ง setup |
| `deno` | Deno | `deno.find_deno_bin()` คืน path และ `{deno} --version` exit 0 ภายใน 5 วินาที. `detail` = เวอร์ชัน | `missing` | คำสั่ง setup |

- `run_checks` รับ probe ของ Deno และ yt-dlp ใน `Probes` เหมือน ffmpeg ให้ test ส่งตัวปลอมได้ (setup-status D26)
- probe ของ Deno ไม่ cache ผล
- tab คลิปและ `POST /downloads` ใช้แค่แถว `yt_dlp`, `deno` และ `ffmpeg` ไม่ใช้ `ready` (D9); แต่ละ tab gate เฉพาะแถวที่ตัวเองใช้ (spoil-maker D53). `backend.spoil` เรียก check ของสามแถวนี้เองผ่าน `require_rows` (ตัวเดียวกับ gate ของงานถอด, D35) ไม่เรียก `run_checks` ทั้งชุด (ไม่ import torch)

### Download

ขั้นตอนของ Download job หนึ่งงาน (D5, D6, D11, D14, D15):

1. `POST /api/spoil/downloads` ตรวจตามลำดับ: probe `yt_dlp`, `deno` และ `ffmpeg` ผ่าน; ลิงก์ตรงรูปแบบ; แล้วภายใต้ lock เดียว: (ลิงก์ YouTube เท่านั้น) ไม่มี Temp clip ของ id นี้, ไม่มีงานที่ thread ยังไม่ออกและไม่มี File import ที่ยังไม่จบ, สร้างงาน. ไม่ผ่านข้อไหนตอบ error ของข้อนั้นทันที
2. เริ่ม daemon thread, state `checking`: `adapter.fetch_info(url)`
3. info เป็น playlist → `failed` code `playlist`. id ของคลิป (D51) มี Temp clip แล้ว → `failed` code `duplicate` พร้อม `clip_id` (ลิงก์เว็บอื่น). flag ยกเลิกถูกตั้ง → `cancelled`. `live_status` เป็น `is_live` หรือ `is_upcoming` หรือ error ของ upcoming → `failed` code `live` (D11)
4. ประมาณขนาด: ผลรวม `filesize` หรือ `filesize_approx` ของ `requested_formats`; ไม่มี → `tbr` (kbps) × `duration` × 125 bytes; ประมาณไม่ได้ → 0
5. `free_bytes(media/temp)` < ขนาดประมาณ + 1 GiB → `failed` code `disk_full` (D11)
6. state `downloading`: `adapter.download(info, on_progress)`. `percent` = byte ที่โหลดแล้วของทุก format ÷ ขนาดประมาณ × 100 ปัดลง ไม่เกิน 100; ขนาดประมาณเป็น 0 → `percent` เป็น `null`. hook raise `DownloadCancelled` เมื่อ flag ถูกตั้ง
7. state `merging` เมื่อ hook ของ format สุดท้ายได้ `finished`. ตั้งแต่นี้ยกเลิกไม่ได้ (D15)
8. ตรวจ mp4 ด้วยตัวตรวจของ File import ขั้น 4; ไม่ผ่าน → `failed` `unsupported_format` และลบไฟล์ (D54). อ่านขนาดภาพจากผลตรวจ, เขียน `{id}.json` แบบเขียนไฟล์ชั่วคราวแล้ว rename (D14), state `done` และ `clip_id` = id
9. ยกเลิกหรือ error ที่ขั้นไหนก็ตาม → ลบไฟล์ของ id นี้ใน `.partial/` และ `{id}.*` ที่ยังไม่มี json, state `cancelled` หรือ `failed`. งานนับว่าจบเมื่อ thread ออกจากขั้นนี้

Adapter (ตัวเดียวที่ import yt-dlp, test แทนด้วยตัวปลอม):

| ฟังก์ชัน | ทำอะไร |
|---|---|
| `fetch_info(url) -> dict` | `YoutubeDL(params).extract_info(url, download=False)` |
| `download(info, on_progress) -> Path` | `YoutubeDL(params พร้อม progress_hooks).process_ie_result(info, download=True)` ใช้ info เดิม ไม่ดึงจาก YouTube ซ้ำ; คืน path ของ mp4 |

จุด inject สำหรับ test (แบบเดียวกับ setup-status D18): `backend.spoil` มี module attribute `adapter` และ `free_bytes` ที่ test monkeypatch ได้ และ probe สามตัวที่ใช้ gate.

แยก error ของ yt-dlp (D15, D16):

| เมื่อ | `code` |
|---|---|
| upcoming (ข้อ 3): ข้อความ error มี "This live event will begin" หรือ "Premieres in" | `live` |
| ข้อความ error มี "Sign in to confirm", "not a bot", "logged-in", "registered users" หรือ "login required" | `login_required` (D56) |
| `GeoRestrictedError` หรือข้อความมี "Private video", "unavailable", "removed" | `unavailable` |
| ข้อความ error มี "Unsupported URL" หรือ "No suitable extractor found" (ลิงก์ที่ต้องใช้ generic extractor) | `unsupported` (D52, D55, D56) |
| ข้อความ error มี "Requested format is not available" หรือ selector ไม่ yield | `unsupported_format` (D54) |
| อื่นๆ ทั้งหมด รวม error ของ ffmpeg | `download_error` (เดิม `youtube_error`, D52) |

เช็คตามลำดับแถว. ข้อความยืนยันกับ YouTube จริงตอน build ticket 01 (D16).

params ของ yt-dlp (adapter เดียวใน `backend.spoil` สร้าง):

| Key | ค่า |
|---|---|
| `format` | format selector (callable) ที่เลือกภาพ `vcodec` ขึ้นต้น `avc1` หรือ `h264`, `pix_fmt` ไม่ระบุหรือ `yuv420p`, `min(width, height)` ≤ 1080 กับเสียง `acodec` ขึ้นต้น `mp4a`; หรือ format รวมที่ตรงทั้งคู่; ใหญ่สุดก่อน; ไม่มีที่ตรง → format ที่ `vcodec` และ `acodec` เป็น `null` ตัวท้ายสุดของ list (ตัวตรวจไฟล์ตัดสินหลังโหลด, D56); ไม่มีเลย → ไม่ yield อะไร → `unsupported_format` (D5, D54) |
| `allowed_extractors` | `["default", "-generic"]` (D55) |
| `socket_timeout` | `30` (D55) |
| `merge_output_format` | `"mp4"` (D5) |
| `ffmpeg_location` | `imageio_ffmpeg.get_ffmpeg_exe()` (ADR-0005) |
| `js_runtimes` | `{"deno": {"path": deno.find_deno_bin()}}` (D8) |
| `paths` | `{"home": media/temp, "temp": media/temp/.partial}` (D14) |
| `outtmpl` | `"{clip_id}.%(ext)s"` ที่ `clip_id` คำนวณจาก info ก่อนโหลด (D14, D51) |
| `writethumbnail` | `True`; thumbnail ได้นามสกุลตามที่ YouTube ให้ ไม่แปลง |
| `noplaylist` | `True` |
| `quiet`, `noprogress` | `True`; ความคืบหน้ามาจาก `progress_hooks` |

รูปแบบลิงก์ที่รับ (ตรวจโดยไม่ใช้ network, D14). id คือ 11 ตัวจาก `A-Z a-z 0-9 _ -`:

| Host | Path | id มาจาก |
|---|---|---|
| `youtube.com`, `www.youtube.com`, `m.youtube.com` | `/watch` | query `v` |
| เดียวกัน | `/shorts/{id}` | path |
| เดียวกัน | `/live/{id}` | path |
| `youtu.be` | `/{id}` | path |

- รับทั้ง `http` และ `https`, ตัดช่องว่างหัวท้าย
- query อื่น (`list`, `t`, `si`) ไม่สนใจ
- นอกตาราง: ลิงก์ `http`/`https` ที่มี host → รับเป็นลิงก์ของเว็บอื่น (D47); ตัด `.` ท้าย host แล้ว host เป็น `localhost`, ลงท้าย `.localhost`, ตัวเลขล้วนหรือตัวเลขกับจุดที่ไม่ใช่ IPv4 สี่ส่วน (`127.1`, `2130706433`), หรือเป็น IP ที่ `ipaddress` บอกว่า `is_loopback`, `is_private`, `is_link_local` หรือ `is_unspecified` → `invalid_url` (D52). ไม่ resolve DNS และไม่กัน redirect — เป็นชั้นแรก; ชั้นหลักคือปิด generic extractor (D55) ให้ yt-dlp ยิงแค่เว็บที่มีตัวโหลดเฉพาะ
- ไม่ใช่ `http`/`https` หรือไม่มี host → `invalid_url`
- ลิงก์ playlist ของ YouTube (`/playlist`) ยังเป็น `invalid_url`

id ของ Temp clip (D51):

| แหล่ง | id |
|---|---|
| YouTube (`extractor_key` `Youtube`) | video id 11 ตัว เหมือนเดิม |
| เว็บอื่น | `{extractor_key ตัวเล็ก}-{id ตามตัวพิมพ์เดิม}`; มีตัวนอก `A-Za-z0-9_-` → แทนด้วย `_` แล้วต่อ `-` + 8 ตัวแรกของ sha1 ของ `"{extractor_key}:{id}"` (D55) |
| ไฟล์ในเครื่อง | `local-` + 12 ตัวแรกของ sha1 hex ของ `"{name}|{size}"` |

ยาวเกิน 64 → 55 ตัวแรก + `-` + 8 ตัวแรกของ sha1 ของ `"{extractor_key}:{id}"`. ทุก id ตรง `CLIP_ID` = `[A-Za-z0-9_-]{1,64}`.

### File import

เอาไฟล์ mp4 ในเครื่องเข้าเป็น Temp clip ใน request เดียว (D49, D50, D52):

0. หน้าเว็บส่ง `POST /api/spoil/imports/check` body `{"name": ..., "size": ...}` (JSON) ก่อน ซึ่งตรวจข้อ 1 ทุกข้อยกเว้นการรับ body แล้วตอบ `200` `{"clip_id": ...}` หรือ error เดียวกับข้อ 1 — เพราะ server ที่ตอบ `409` ระหว่าง browser ยังส่ง body ไม่ครบ ทำให้ XHR ได้ network error แทน response. ข้อ 1 ตรวจซ้ำเพราะสถานะเปลี่ยนได้ระหว่างสอง request
1. `POST /api/spoil/imports?name={ชื่อไฟล์}&size={byte}` `Content-Type: application/octet-stream` body คือตัวไฟล์. ตรวจตามลำดับ: แถว `ffmpeg` `ok`; `name` ลงท้าย `.mp4` (ไม่สนตัวพิมพ์) ไม่งั้น `400` `not_mp4`; `size` เป็นจำนวนเต็ม > 0; id (D51) มี Temp clip แล้ว → `409` `duplicate` กับ `clip_id`; ภายใต้ lock เดียวกับ Download job: ไม่มี Download job ที่ thread ยังไม่ออก และไม่มี File import อื่น → ไม่งั้น `409` `busy`; `free_bytes(media/temp)` ≥ `size` + 1 GiB → ไม่งั้น `409` `disk_full`
2. เขียน `request.stream()` ลง `.partial/{id}.import.mp4` ทีละก้อน ใน `anyio.to_thread.run_sync` (ffmpeg ขั้น 4–5 ด้วย) ไม่ block event loop; ไม่ได้ byte ใหม่ 60 วินาที → ลบ `408` `stalled` (D55); จำนวน byte เกิน `size` → หยุด `400` `size_mismatch`; client ตัดการเชื่อมต่อ (`ClientDisconnect`) → ลบไฟล์ ไม่มีใครรับคำตอบ (handler ตอบ `400` เงียบๆ แทน 500, D57)
3. byte ที่ได้ไม่เท่า `size` → ลบ `400` `size_mismatch`
4. ตรวจด้วย `ffmpeg -hide_banner -i` (ตัวตรวจเดียวกับขั้น 8 ของ Download): stream ภาพแรกที่ไม่ใช่ `attached_pic` เป็น `h264` และ `yuv420p`; rotation ±90 (side data `displaymatrix` หรือ tag `rotate`) → สลับกว้างกับสูงก่อนคิด; ด้านสั้น ≤ 1080, ทุก stream เสียงเป็น `aac` (ไม่มีเสียงได้), อ่าน `Duration` ได้. ไม่ผ่าน → ลบ `400` `unsupported_file` พร้อม `message` ที่บอกข้อที่ไม่ตรง ("ภาพเป็น hevc", "ภาพ 2160×3840 ด้านสั้นเกิน 1080", "เสียงเป็น opus", "อ่านไฟล์ไม่ได้") ต่อด้วย "แปลงเป็น mp4 (H.264, AAC) ไม่เกิน 1080p ด้วยโปรแกรมอื่นแล้วลองอีกครั้ง"
5. thumbnail: `-ss {10% ของความยาว} -frames:v 1` เป็น `{id}.jpg`; ไม่ได้ → `null`
6. `os.replace` ไฟล์เข้า `media/temp/{id}.mp4`, เขียน `{id}.json` แบบ `.tmp` แล้ว rename สุดท้าย → `201` Temp clip
7. error ที่ขั้นไหนก็ตาม → ลบไฟล์ของ id นี้ใน `.partial/` และ `{id}.*` ที่ยังไม่มี json; flag "กำลังรับไฟล์" ปล่อยใน `finally` ทุกทาง (D55)

- ไม่มี state ใน memory นอกจาก flag "กำลังรับไฟล์" ที่ lock ใช้; restart กลางทาง → ไฟล์ค้างถูกล้างตอน start (D14)
- ไม่แตะไฟล์ต้นฉบับ: browser ส่งสำเนา (D49)

### Transcribe

ขั้นตอนของ Transcribe job หนึ่งงาน (D21, D23, D24, D26, D27, D28, D29):

1. `POST /api/spoil/transcriptions` ตรวจตามลำดับ: แถว `torch`, `transformers`, `ffmpeg`, `model_whisper` เป็น `ok` และ `device` ไม่ใช่ `cpu`; แล้วภายใต้ lock ของงานถอด (lock เดียวกับ `DELETE /clips/{id}`, D29): มี Temp clip ของ `clip_id` (มี json และ mp4), ไม่มี Transcribe job ที่ thread ยังไม่ออก, สร้างงาน. Download job ไม่มีผล (D24)
2. เริ่ม daemon thread ใน backend, state `preparing`: start process ลูก (`multiprocessing` context `spawn`) ที่รัน `backend.spoil.whisper.worker(mp4, duration_s, snapshot_dir, device, queue)` (D28)
3. process ลูก: โหลดโมเดล; ล้ม → ส่ง `("error", "model_failed", ข้อความ)`. แล้วแบ่งเวลา 0 ถึง `duration_s` เป็นช่วงละ 300 วินาที (ช่วงสุดท้ายสั้นกว่า 30 วินาทีรวมเข้าช่วงก่อน, D29); ทุกช่วง: `read_audio(mp4, start, length)` (ffmpeg ล้มที่ช่วงแรก → `("error", "no_audio", ...)`), `transcribe(model, audio)`, บวกเวลาเริ่มของช่วงให้ทุกบรรทัด แล้วส่ง `("segment", index, total, lines, language)`. จบครบ → ส่ง `("done",)` แล้ว exit
4. thread ใน backend อ่าน queue: ข้อความ `segment` แรกเปลี่ยน state เป็น `transcribing`; `percent` = ช่วงที่ได้ × 100 ÷ จำนวนช่วง ปัดลง; สะสมบรรทัดใน memory
5. flag ยกเลิกถูกตั้ง → `terminate()` process ลูก แล้ว `join`, state `cancelled`. process ลูกออกโดยไม่ได้ `done` หรือ `error` (Metal/CUDA crash, ถูก OS ฆ่า) → `failed` `crashed` (D28)
6. ได้ `done`: ตัดบรรทัดที่ข้อความว่างหลัง strip; `language` = ภาษาที่ช่วงส่วนใหญ่ตรวจได้ไม่นับ `null` (เสมอกัน → ช่วงแรก, ไม่มีเลย → `null`); เขียน `{id}.transcript.json` แบบไฟล์ `.tmp` แล้ว rename; state `done`
7. error ใดก็ตามที่ไม่อยู่ในข้อบน (รวมเขียนไฟล์ไม่ได้) → `failed` `internal`; thread ตั้ง state จบใน `finally` และ process ลูกที่ยังรันถูก `terminate()` (D29). `cancelled` และ `failed` ไม่แตะ `{id}.transcript.json` เดิม. งานนับว่าจบเมื่อ thread ออก
8. backend shutdown → ตั้ง flag ยกเลิกและ `terminate()` process ลูกที่ยังรัน (D28)

Adapter `backend.spoil.whisper` (ตัวเดียวที่ import `transformers` และ `torch` สำหรับถอด; import ภายในฟังก์ชันที่รันใน process ลูก ไม่ใช่ตอน import module):

| ฟังก์ชัน | ทำอะไร |
|---|---|
| `worker(mp4, duration_s, snapshot_dir, device, queue)` | จุดเริ่มของ process ลูก ทำขั้น 3 |
| `read_audio(mp4, start_s, length_s) -> ndarray` | ffmpeg ของ imageio ตาม Library assumptions ช่วงเดียว อ่าน stdout เป็น float32 |
| `load(snapshot_dir, device) -> Model` | `pipeline("automatic-speech-recognition", ...)` กับ `float16` บน `cuda` และ `float32` บน `mps` (D30) |
| `transcribe(model, audio, start_s, length_s) -> (lines, language)` | ส่ง array ทั้งช่วงโดยไม่ใช้ `chunk_length_s` ให้ Whisper ทำ long-form เอง, `return_timestamps=True`, `return_language=True`, `batch_size` 1; คืนบรรทัด `(start_s, end_s, text)` ที่ `to_lines` บวกเวลาเริ่มของช่วงแล้ว (จบเป็น `None` หรือเลยช่วง → จบช่วง) และภาษาจาก `chunks[0]["language"]` แปลงเป็น code (ไม่มี chunk → `null`) (D29, D30) |

จุด inject สำหรับ test: `backend.spoil` มี module attribute `start_worker` (สร้าง process ลูก) ที่ test แทนด้วยตัวปลอมที่รันใน thread และป้อนข้อความเข้า queue ตามลำดับที่ test กำหนด; probe และ status ของแถวที่ gate มาจาก `backend.checks` เหมือนงานโหลด. test ของ `worker` จริงอยู่ใน seam 3 (เช็คมือ).

`{id}.transcript.json`:

```json
{
  "clip_id": "dQw4w9WgXcQ",
  "language": "en",
  "duration_s": 5712,
  "model": "openai/whisper-large-v3-turbo",
  "revision": "41f01f3",
  "transcribed_at": "2026-10-30T10:12:00+07:00",
  "lines": [
    {"start_s": 12.4, "end_s": 15.0, "text": "Where are you going?"},
    {"start_s": 15.2, "end_s": 17.8, "text": "Home.", "edited": true}
  ]
}
```

- `lines` เรียงตาม `start_s`; ว่างได้ (ไม่พบคำพูด)
- `language` เป็น `null` เมื่อไม่มีช่วงไหนตรวจภาษาได้ (D29)
- `edited: true` มีเฉพาะบรรทัดที่ผู้ใช้แก้ข้อความ บรรทัดที่ไม่ได้แก้ไม่มี field นี้; ไม่เก็บข้อความเดิม; `.txt` และ `.srt` ใช้ข้อความที่แก้ (spoil-maker D54)
- `.txt` = บรรทัดละ `[hh:mm:ss] ข้อความ`; `.srt` = มาตรฐาน SRT เลขลำดับจาก 1 เวลา `hh:mm:ss,mmm`; ทั้งสอง UTF-8 ไม่มี BOM, ขึ้นบรรทัด `\n`

### Trim

ตัดช่วงออกจาก Temp clip ด้วยการ encode `{id}.mp4` ใหม่แทนไฟล์เดิม (D36, D37, D41). ขั้นตอนของ Trim job หนึ่งงาน:

1. `POST /api/spoil/trims` ตรวจตามลำดับ (ไม่ผ่านข้อไหนตอบ error ของข้อนั้นทันที):
   1. แถว `ffmpeg` เป็น `ok` (ผ่าน `require_rows`, D35) → ไม่ใช่ `503` `not_ready`
   2. body ถูกรูป: `clip_id` string, `ranges` list 1–20 ตัวของ `{start_s, end_s}` ที่เป็นตัวเลขจำกัด (ไม่ใช่ boolean, NaN, Infinity), `confirm_derived_loss` boolean ถ้ามี → ไม่ใช่ `400` `invalid_request`
   3. ภายใต้ lock ของงานถอด (lock เดียวกับ `DELETE /clips/{id}`, D29) แล้ว `gpu.slot.clip_untouched(clip_id)` ข้างใน (lock ของ slot อยู่ในสุดเสมอ, spoil-maker D49): มี Temp clip ของ `clip_id` → ไม่ใช่ `404` `not_found`
   4. ความยาวจริงของ mp4 จาก `backend.ffmpeg.probe` (ไม่ใช้ `duration_s` ของ json ที่เป็นจำนวนเต็มหรือ `null`); probe ล้ม → `500` `internal`; ช่วงผ่านกฎของ D41 เทียบความยาวนี้ → ไม่ใช่ `400` `invalid_ranges` (D42)
   5. Transcribe job ของคลิปนี้ยังไม่จบ → `409` `transcribing`; มี Trim job ที่ thread ยังไม่ออก → `409` `busy` (รวม `POST` ซ้ำของคลิปที่กำลังตัด, D46); งานใดก็ตามใช้คลิปนี้อยู่ใน `backend.gpu` (Describe, Draft, Voice, Render, `PUT` การตัด EP) → `409` `clip_busy`
   6. คลิปมี `{id}.transcript.json`, Shot, ไฟล์การตัด EP หรือ Spoil draft ที่ใช้คลิปนี้ และไม่มี `confirm_derived_loss: true` → `409` `has_derived` พร้อม `derived` (D37)
   7. สร้างงาน แล้วตั้ง `gpu.slot.trimming_clip` = `clip_id` (D42): `take()` ของงานทุกชนิดที่ `clip_ids` มีคลิปนี้ได้ `409` `clip_busy` และ `clip_untouched(clip_id)` ปฏิเสธไม่ว่า `by` เป็นอะไร — Trim job ไม่จองช่อง GPU แต่งานอื่นต้องเห็นมัน
2. เริ่ม daemon thread, state `trimming`:
   1. รวมและเรียงช่วง แล้วคิดช่วงที่เหลือ (ส่วนกลับของช่วงที่ตัดใน [0, ความยาวจริง)); `kept_s` = ผลรวมความยาวช่วงที่เหลือ
   2. `free_bytes(media/temp)` < `file_bytes × kept_s ÷ ความยาวจริง` + 1 GiB → `failed` `disk_full` (D41)
   3. มีเสียงไหม = `has_audio` จาก probe ของข้อ 1.4
   4. รัน ffmpeg ตาม Library assumptions ลง `.partial/{id}.trim.mp4` ด้วย bitrate ของ D41; `percent` = `out_time_us` ÷ (`kept_s` × 10⁶) × 100 ปัดลง ไม่เกิน 99
3. flag ยกเลิกถูกตั้งระหว่างขั้น 2 → kill ffmpeg แล้วรอให้ออก, ลบ `.partial/{id}.trim.mp4`, state `cancelled`
4. ffmpeg exit ไม่เป็น 0 → `failed` `ffmpeg_failed`; stderr 20 บรรทัดท้ายเขียนลง log ของ `[api]`
5. ตรวจไฟล์ผลก่อนแทน: probe `.partial/{id}.trim.mp4`; ความยาวต่างจาก `kept_s` เกิน 1 วินาที หรือไฟล์เดิมมีเสียงแต่ไฟล์ใหม่ไม่มี → ลบไฟล์ผล แล้ว `failed` `ffmpeg_failed` "ไฟล์ที่ตัดได้ไม่ครบ" ไม่แตะอะไรอื่น (D42)
6. state `replacing` (ยกเลิกไม่ได้ตั้งแต่นี้) — ลำดับ lock ตาม `Transcriptions.delete_clip` (D42):
   1. เขียน json ใหม่ของคลิปลง `{id}.trimming.json` (เขียน `.tmp` แล้ว rename): `duration_s` = ความยาวจาก probe ของไฟล์ใหม่ปัดเป็นจำนวนเต็ม (type เดิม `int`), `file_bytes` จากไฟล์ใหม่, `trimmed` ต่อท้ายด้วยช่วงที่รวมแล้ว, `trimmed_at` = เวลาตอนนี้
   2. ภายใต้ lock ของงานถอดแล้ว `clip_untouched(clip_id)`: `os.replace(.partial/{id}.trim.mp4, {id}.mp4)` ลองใหม่ทุก 0.5 วินาทีนานสุด 10 วินาทีเมื่อได้ `PermissionError`; ยังไม่ได้ → ลบ marker และไฟล์ใน `.partial/` แล้ว `failed` `in_use` ไม่ลบอะไรอื่น (D41, D42). แทนได้ → ลบ `{id}.transcript.json`, Shot และไฟล์การตัด EP ด้วยฟังก์ชันเดียวกับ `clips.delete_clip` (ไม่รวม mp4 และ json) ใน lock เดียวกันนี้
   3. หลังออกจาก lock ของ slot: `draft_file.drop_if_uses(project, clip_id)` (lock ของ draft มาก่อน lock ของ slot เสมอ, spoil-maker D49)
   4. `os.replace({id}.trimming.json, {id}.json)`
7. state `done`; `trimming_clip` = `null`
8. error ใดก็ตามที่ไม่อยู่ในข้อบน → `failed` `internal`; thread ลบไฟล์ใน `.partial/` ของงานนี้และตั้ง `trimming_clip` = `null` ใน `finally`. งานนับว่าจบเมื่อ thread ออก
9. backend shutdown → ตั้ง flag ยกเลิกและ kill ffmpeg ที่ยังรัน; state `replacing` ทำต่อจนจบก่อน thread ออก

backend start ก่อนล้าง `.partial/` (D15): ทุก `{id}.trimming.json` ที่มี `{id}.json` คู่ (D41):
- ยังมี `.partial/{id}.trim.mp4` → แทนไฟล์ยังไม่เกิด: ลบ marker
- ไม่มี → แทนไฟล์แล้ว: ลบ Transcript, Shot, ไฟล์การตัด EP และ Spoil draft ของคลิปนี้ แล้วทำขั้น 6.4 ต่อ
- marker อ่านไม่ได้ → ลบ marker และ log; ไม่แตะอย่างอื่น
- marker ที่ไม่มี `{id}.json` (คลิปถูกลบแล้ว) → ลบ marker (D46)

Encoder ตาม `sys.platform`: `darwin` → `h264_videotoolbox`; อื่น → `libx264` `-preset veryfast` (D36). คำสั่ง ffmpeg ทั้งหมดอยู่ในฟังก์ชันเดียวของ `backend.spoil.trim` ที่คืน argv ให้ test ตรวจได้โดยไม่รัน ffmpeg.

จุด inject สำหรับ test: `Trims(run_ffmpeg=…, probe=…, free_bytes=…, sleep=…, replace_mp4=…)` — ค่าเริ่มต้นคือ `backend.ffmpeg.run` (เริ่ม process, อ่าน progress, kill), `backend.ffmpeg.probe`, `disk.free_bytes` ตัวเดียวกับงานโหลด, `time.sleep` และ `os.replace`; test ส่งตัวปลอมที่เขียนไฟล์ผลและรอสัญญาณได้ (D43).

Trim job:

```json
{
  "clip_id": "dQw4w9WgXcQ",
  "state": "trimming",
  "percent": 37,
  "kept_s": 6820.0,
  "cancel_requested": false,
  "error": null
}
```

- `state` เป็นหนึ่งใน `trimming`, `replacing`, `done`, `failed`, `cancelled`; งานยังไม่จบ = `trimming`, `replacing`
- `percent` เป็น `null` นอก `trimming`
- `error` มีค่าเมื่อ `failed`: `{"code", "message"}`

| `code` | เมื่อ | `message` |
|---|---|---|
| `disk_full` | ที่ว่างไม่พอตามขั้น 2.2 | "ที่ว่างไม่พอ: ต้องการ {ต้องการ} GB มี {ว่าง} GB" |
| `ffmpeg_failed` | ffmpeg exit ไม่เป็น 0 หรือไฟล์ผลไม่ผ่านขั้น 5 (message "ตัดคลิปไม่สำเร็จ: ไฟล์ที่ตัดได้ไม่ครบ") | "ตัดคลิปไม่สำเร็จ: {บรรทัดท้ายของ stderr}"; ข้อความเต็มอยู่ใน log ของ `[api]` |
| `in_use` | แทน mp4 ไม่ได้หลังลอง 10 วินาที (ขั้น 6.2) | "แทนไฟล์ไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง" |
| `internal` | error อื่นทั้งหมด | "ตัดคลิปไม่สำเร็จ: {ข้อความสั้นของ error}"; ข้อความเต็มอยู่ใน log ของ `[api]` |

### Temp clip

`{id}.json` (D7, D14):

```json
{
  "id": "dQw4w9WgXcQ",
  "title": "ชื่อคลิป",
  "channel": "ชื่อช่อง",
  "site": "Youtube",
  "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "duration_s": 7212,
  "width": 1920,
  "height": 1080,
  "orientation": "landscape",
  "file_bytes": 1450000000,
  "thumbnail": "dQw4w9WgXcQ.webp",
  "downloaded_at": "2026-10-29T14:05:11+07:00",
  "yt_dlp_version": "2026.10.26",
  "trimmed": [{"start_s": 0.0, "end_s": 90.0}, {"start_s": 6910.0, "end_s": 7082.0}],
  "trimmed_at": "2026-11-05T10:20:00+07:00"
}
```

- `orientation` เป็น `portrait` เมื่อ `height` > `width`, ไม่งั้น `landscape`
- `site` = `extractor_key` ของ yt-dlp หรือ `"local"` สำหรับไฟล์ในเครื่อง; json เดิมที่ไม่มี field นี้อ่านเป็น `"Youtube"` (D52)
- ไฟล์ในเครื่อง: `title` = ชื่อไฟล์ไม่มีนามสกุล, `channel`, `source_url` และ `yt_dlp_version` เป็น `null`, `downloaded_at` = เวลาที่เอาเข้า (D52)
- เว็บอื่น: `channel` = `channel` หรือ `uploader` ของ info หรือ `null`
- `thumbnail` เป็น `null` เมื่อโหลด thumbnail ไม่ได้
- `file_bytes` อ่านจากไฟล์ mp4 จริงหลัง merge และหลังตัด
- `trimmed` เป็น list ว่างและ `trimmed_at` เป็น `null` เมื่อยังไม่เคยตัด; json เดิมที่ไม่มีสอง field นี้อ่านเป็นค่าเดียวกัน; แต่ละช่วงเป็นเวลาของไฟล์ก่อนการตัดรอบนั้น (D36)
- `width`, `height`, `orientation` และ `thumbnail` ไม่เปลี่ยนเมื่อตัด
- รายการ = ทุก `*.json` ใน `media/temp/` ที่มี `{id}.mp4` คู่กัน เรียง `downloaded_at` ใหม่สุดก่อน. json ที่อ่านไม่ได้หรือไม่มี mp4 คู่ → ข้าม
- ลบ = ลบ `{id}.mp4`, thumbnail และ `{id}.transcript.json` ก่อน แล้ว `{id}.json` สุดท้าย; ลบ mp4 ไม่ได้ (Windows ที่ไฟล์ยังเปิดอยู่) → `409` `in_use` และไม่แตะ json (D15, D23); คลิปที่ Transcribe job ยังไม่จบ → `409` `transcribing` ไม่ลบอะไร (D27); คลิปที่ Trim job ยังไม่จบ → `409` `trimming` ไม่ลบอะไร (D41)
- รายการมี field `transcribed`: `true` เมื่อมีไฟล์ `{id}.transcript.json` (ไม่ parse); รายการคลิปข้ามไฟล์ `*.transcript.json` (D23, D29)
- เช็คกับลบภายใต้ lock ของงานถอด (D29)
- backend start → ทำ marker `{id}.trimming.json` ต่อตาม Trim, แล้วลบ `.partial/` ทั้งหมด, ไฟล์ `{id}.*` ใน `media/temp/` ที่ไม่มี `{id}.json` เฉพาะ `{id}` รูปที่แอปสร้าง (11 ตัวของ YouTube, `local-[0-9a-f]{12}`, หรือตรง `CLIP_ID` และมี `-`; D55) และไฟล์ `*.tmp` ทั้งหมด (D15, D29); รายการคลิปข้ามไฟล์ `*.trimming.json` (D41)

### API

ทุก path อยู่ใต้ `/api/spoil`. error body เป็น `{"code": "...", "message": "..."}`; `message` เป็นภาษาไทยพร้อมแสดงในหน้าเว็บ.

| Method | Path | Response |
|---|---|---|
| `GET` | `/clips` | `200` `{"clips": [Temp clip + `transcribed`, ...]}` |
| `GET` | `/clips/{id}` | `200` Temp clip หนึ่งคลิปรูปเดียวกับแถวของ `/clips`; ไม่มี → `404` `not_found` (D46) |
| `GET` | `/clips/{id}/video` | `200` หรือ `206` ไฟล์ `video/mp4` รองรับ Range; ไม่มี → `404` `not_found`; query string ไม่มีผล (`?v=` ของ D41) |
| `GET` | `/clips/{id}/thumbnail` | `200` ไฟล์ thumbnail; นามสกุลที่ไม่บอกชนิด (TikTok `.image`) → `Content-Type` จาก byte แรก (D56); ไม่มี → `404` `not_found` |
| `DELETE` | `/clips/{id}` | `204`; ไม่มี → `404` `not_found`; ไฟล์ถูกเปิดอยู่ → `409` `in_use` "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง"; กำลังถอดคลิปนี้ → `409` `transcribing` "กำลังถอดคลิปนี้อยู่ ยกเลิกก่อนแล้วลบ"; กำลังตัดคลิปนี้ → `409` `trimming` "กำลังตัดคลิปนี้อยู่ รอให้จบหรือยกเลิกก่อน" |
| `GET` | `/clips/{id}/transcript` | `200` เนื้อ `{id}.transcript.json`; ไม่มี → `404` `not_found` |
| `GET` | `/clips/{id}/transcript.txt`, `/clips/{id}/transcript.srt` | `200` `text/plain; charset=utf-8` หรือ `application/x-subrip`, `Content-Disposition: attachment; filename="{id}.txt"` หรือ `.srt`; ไม่มี → `404` `not_found` |
| `PATCH` | `/clips/{id}/transcript/lines/{n}` | body `{"text": "..."}` แก้ข้อความบรรทัดที่ `n` (นับจาก 0) ตั้ง `edited: true` เขียนแบบ `.tmp` แล้ว rename → `200` บรรทัดนั้น; `text` ว่างหลังตัดช่องว่าง → `400` `invalid_request`; ไม่มีคลิป Transcript หรือบรรทัด → `404` `not_found`; Transcribe job ของคลิปนั้นยังไม่จบ → `409` `transcribing`; Draft job ที่ใช้คลิปนั้น → `409` `clip_busy` (spoil-maker D54); Trim job ของคลิปนั้นยังไม่จบ → `409` `trimming` (D41) |
| `POST` | `/transcriptions` | body `{"clip_id": "...", "confirm_edit_loss"?: true}`. `202` กับ Transcribe job. error: `503` `not_ready`, `404` `not_found`, `409` `busy` "กำลังถอดคลิปอื่นอยู่"; คลิปมีบรรทัด `edited` และไม่มี `confirm_edit_loss: true` → `409` `has_edits` "ถอดใหม่จะลบบทพูดที่แก้ไว้" (spoil-maker D54); Trim job ของคลิปนั้นยังไม่จบ → `409` `trimming` (D41) |
| `POST` | `/trims` | body `{"clip_id": "...", "ranges": [{"start_s": 0, "end_s": 90}], "confirm_derived_loss"?: true}`. `202` กับ Trim job. error ตามลำดับของ Trim ข้อ 1: `503` `not_ready`, `400` `invalid_request`, `404` `not_found`, `400` `invalid_ranges` "ช่วงที่ตัดไม่ถูกต้อง: {เหตุผล}", `409` `transcribing`, `409` `busy` "กำลังตัดคลิปอื่นอยู่", `409` `clip_busy`, `409` `has_derived` "ตัดคลิปจะลบ {รายการ} ของคลิปนี้ ตัดต่อไหม?" (รายการเป็นคำของหน้าเว็บ: "Transcript (รวมบรรทัดที่แก้ไว้)", "ภาพฉากและการตัด EP", "Spoil draft") พร้อม `derived` (list ของ `transcript`, `shots`, `episodes`, `draft`) (D37, D41, D46) |
| `GET` | `/trims/current` | `200` Trim job ล่าสุด หรือ `null` |
| `DELETE` | `/trims/current` | `202` ตั้ง flag ยกเลิก; state `replacing` → `409` `replacing` "กำลังแทนไฟล์ ยกเลิกไม่ได้แล้ว"; ไม่มีงานที่ยังไม่จบ → `404` `not_found` |
| `GET` | `/transcriptions/current` | `200` Transcribe job ล่าสุด หรือ `null` |
| `DELETE` | `/transcriptions/current` | `202` ตั้ง flag ยกเลิก; ไม่มีงานที่ยังไม่จบ → `404` `not_found` |
| `POST` | `/downloads` | body `{"url": "..."}`. `202` กับ Download job. error: `503` `not_ready`, `400` `invalid_url`, `409` `duplicate` (ลิงก์ YouTube; body มี `clip_id` เพิ่ม), `409` `busy` (Download job หรือ File import ยังไม่จบ) |
| `POST` | `/imports/check` | body `{"name": "...", "size": 123}`. `200` `{"clip_id": "local-…"}`; error เดียวกับ `/imports` ข้อ 1 (File import ขั้น 0) |
| `POST` | `/imports?name=…&size=…` | body ไฟล์ดิบ `application/octet-stream` (D50). `201` Temp clip. error: `503` `not_ready` (แถว `ffmpeg`), `400` `not_mp4`, `400` `invalid_request` (`name` หรือ `size` ผิด), `409` `duplicate` กับ `clip_id`, `409` `busy`, `409` `disk_full`, `400` `size_mismatch`, `400` `unsupported_file`; `Content-Type` อื่น → `415` (File import) |
| `GET` | `/downloads/current` | `200` Download job ล่าสุด หรือ `null` ถ้ายังไม่เคยมีตั้งแต่ backend start |
| `DELETE` | `/downloads/current` | `202` ตั้ง flag ยกเลิก; state เป็น `cancelled` เมื่อ thread หยุด (รอบ progress ถัดไป หรือหลัง `fetch_info` คืน); state `merging` → `409` `merging`; ไม่มีงานที่ยังไม่จบ → `404` `not_found` |

`{id}` ใน path ต้องตรง `CLIP_ID` (`[A-Za-z0-9_-]{1,64}`, D51) ไม่งั้น `404` — กัน path traversal.

ทุก `POST` ใต้ `/api/spoil` ที่ `Content-Type` ไม่ใช่ `application/json` ได้ `415` `unsupported_media_type` ยกเว้น `POST /imports` ที่รับ `application/octet-stream` อย่างเดียว — ทั้งสองบังคับ CORS preflight จึงไม่มีเว็บอื่นสั่งงานได้ (D29, D50). `sendJson` ส่ง header นี้อยู่แล้ว.

ทุก request ที่ `Host` ไม่ใช่ `127.0.0.1`, `localhost` หรือ `[::1]` (port ใดก็ได้) ได้ `400` จาก `TrustedHostMiddleware` (D15). Vite proxy ส่ง `Host: localhost:5173` ต่อมาจึงผ่าน.

Download job:

```json
{
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "id": "dQw4w9WgXcQ",
  "state": "downloading",
  "title": "ชื่อคลิป",
  "percent": 42,
  "cancel_requested": false,
  "error": null,
  "clip_id": null
}
```

- `state` เป็นหนึ่งใน `checking`, `downloading`, `merging`, `done`, `failed`, `cancelled`
- งานยังไม่จบ = `checking`, `downloading`, `merging`
- `title` เป็น `null` ระหว่าง `checking`
- `percent` เป็น `null` นอก `downloading` หรือเมื่อประมาณขนาดไม่ได้
- `clip_id` มีค่าเมื่อ `done`
- `cancel_requested` เป็น `true` หลัง `DELETE /downloads/current` จนงานจบ
- `error` มีค่าเมื่อ `failed`: `{"code": "...", "message": "...", "yt_dlp_version": "...", "fix": "..."}`; `fix` มีค่าเฉพาะ `download_error`; `duplicate` มี `clip_id` ใน `error`

Transcribe job:

```json
{
  "clip_id": "dQw4w9WgXcQ",
  "state": "transcribing",
  "percent": 35,
  "cancel_requested": false,
  "error": null
}
```

- `state` เป็นหนึ่งใน `preparing`, `transcribing`, `done`, `failed`, `cancelled`; งานยังไม่จบ = `preparing`, `transcribing`
- `percent` เป็น `null` นอก `transcribing`
- `error` มีค่าเมื่อ `failed`: `{"code", "message"}`

| `code` | เมื่อ | `message` |
|---|---|---|
| `no_audio` | ffmpeg อ่านเสียงช่วงแรกไม่ได้ | "คลิปนี้ไม่มีเสียง หรืออ่านเสียงไม่ได้" |
| `model_failed` | โหลดโมเดลหรือถอดช่วงไหนล้มเป็น exception | "ถอดไม่สำเร็จ: {ข้อความสั้นของ error}. ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง"; ข้อความเต็มอยู่ใน log ของ `[api]` |
| `crashed` | process ลูกตายโดยไม่ส่งผล (D28) | "ตัวถอดหยุดทำงานกลางทาง (exit {code}). ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง" |
| `internal` | error อื่นทั้งหมด รวมเขียนไฟล์ไม่ได้ (D29) | "ถอดไม่สำเร็จ: {ข้อความสั้นของ error}"; ข้อความเต็มอยู่ใน log ของ `[api]` |

error ของ Download job (`failed`):

| `code` | เมื่อ | `message` |
|---|---|---|
| `live` | `live_status` เป็น `is_live` หรือ `is_upcoming` | "คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้" |
| `disk_full` | ที่ว่างไม่พอตามขั้น 5 | "ที่ว่างไม่พอ: ต้องการ {ต้องการ} GB มี {ว่าง} GB" |
| `unavailable` | ตารางแยก error | "คลิปนี้เป็น private ถูกลบ หรือจำกัดประเทศ โหลดไม่ได้" |
| `login_required` | ตารางแยก error | "เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด \"เลือกไฟล์ในเครื่อง\"" (D47) |
| `unsupported` | ตารางแยก error | "เว็บนี้โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด \"เลือกไฟล์ในเครื่อง\"" (D52) |
| `playlist` | ขั้น 3 | "ลิงก์นี้เป็น playlist วางลิงก์ของคลิปเดียว" |
| `duplicate` | ขั้น 3 | "คลิปนี้โหลดไว้แล้ว"; `clip_id` ใน `error` (D51) |
| `unsupported_format` | selector ไม่ yield หรือไฟล์หลัง merge ไม่ผ่านตัวตรวจ (ขั้น 8) | "เว็บนี้ไม่มีไฟล์ H.264 ไม่เกิน 1080p ให้โหลด โหลดเองแล้วแปลง จากนั้นกด \"เลือกไฟล์ในเครื่อง\"" (D54) |
| `download_error` | ตารางแยก error | "โหลดไม่สำเร็จ (yt-dlp {version}). ถ้าเป็นทุกคลิป ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script"; `fix` = `uv lock --upgrade-package yt-dlp`; ข้อความเต็มจาก yt-dlp อยู่ใน log ของ `[api]` (D8) |

### Frontend

แถบ tab (D10, spoil-maker D53):
- hash `#/setup` → tab ติดตั้ง, `#/clips` → tab คลิป, `#/spoil` และ `#/spoil/…` → tab สปอย, อื่นหรือว่าง → tab ติดตั้ง
- กด tab → เปลี่ยน hash; ปุ่ม back ของ browser สลับ tab ตาม hash

tab คลิป (เดิม tab สปอย, spoil-maker D53):

| State | เมื่อไร | แสดง |
|---|---|---|
| loading | เปิด tab ยังไม่ได้ผลจาก `/api/setup/status` และ `/api/spoil/clips` | "กำลังโหลด…" |
| not ready | แถว `yt_dlp`, `deno` หรือ `ffmpeg` ไม่ `ok` | "ยังติดตั้งไม่ครบ: {label ที่ขาด}" กับลิงก์ "ไปหน้าติดตั้ง" แทนช่องลิงก์; รายการยังแสดง (D9) |
| idle | พร้อม ไม่มีงานที่ยังไม่จบ | ช่องลิงก์, ปุ่ม "โหลด", รายการ |
| downloading | งานเป็น `checking`, `downloading` หรือ `merging` | "กำลังเช็คลิงก์…", "กำลังโหลด {title}" กับแถบ % หรือ "กำลังรวมไฟล์…"; ปุ่ม "ยกเลิก" ยกเว้นตอน `merging` ที่แสดง "ยกเลิกไม่ได้ระหว่างรวมไฟล์" แทน (D18); ปุ่มโหลด disabled (D6, D15) |
| cancelling | `cancel_requested` เป็น `true` และงานยังไม่จบ | "กำลังยกเลิก…", ปุ่มยกเลิก disabled |
| offline | fetch ล้ม, status ที่ไม่อยู่ในตาราง API หรือเกิน 30 วินาที | `OfflinePanel` ตัวเดียวกับหน้า Setup status พร้อมปุ่ม Refresh ที่โหลด tab ใหม่ทั้งหมด |

ข้อความหลังงานจบ (แสดงเหนือรายการจนกดโหลดครั้งถัดไป):

| ผล | แสดง |
|---|---|
| `done` | "โหลดเสร็จ: {title}" และ highlight แถวใหม่ |
| `cancelled` | "ยกเลิกแล้ว" |
| `failed` | `error.message`; มี `error.fix` → แสดงคำสั่งเป็นบรรทัดพร้อมปุ่ม copy; ไม่ใช้ chip เพราะคำสั่งมีช่องว่าง (setup-status D20) |
| poll ได้ `null` ระหว่างติดตามงาน | "งานโหลดหายเพราะ backend เริ่มใหม่ ลองโหลดอีกครั้ง" แล้วโหลดรายการใหม่ (D15) |
| `409` `merging` | "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว" |
| ลบได้ `409` `in_use` | `message` จาก API ใต้แถวนั้น |
| `400` `invalid_url` | "ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป" |
| งาน `failed` `duplicate` | "คลิปนี้โหลดไว้แล้ว" และ highlight แถว `error.clip_id` (D51) |
| `409` `duplicate` | "คลิปนี้โหลดไว้แล้ว" และ highlight แถว `clip_id` พร้อมเลื่อนไปหา (D12) |
| `409` `busy` | "กำลังโหลดหรือเอาไฟล์อื่นเข้าอยู่" |
| `503` `not_ready` | state not ready |

เอาไฟล์เข้า (D49–D52):

| State | เมื่อไร | แสดง |
|---|---|---|
| importing | XHR กำลังส่ง body | "กำลังเอาไฟล์เข้า {ชื่อไฟล์}" กับแถบ % จาก `upload.onprogress`, ปุ่ม "ยกเลิก"; ช่องลิงก์ ปุ่มโหลด และปุ่มเลือกไฟล์ disabled |
| checking file | ส่ง body ครบ รอ response | "กำลังตรวจไฟล์…" ไม่มีปุ่มยกเลิก |

- ปุ่ม "เลือกไฟล์ในเครื่อง" เปิด `<input type="file" accept="video/mp4,.mp4">`; ลากไฟล์มาวางบนพื้นที่ของ `LinkForm` ได้ผลเดียวกัน; ลากหลายไฟล์ → ใช้ไฟล์แรกพร้อมข้อความ "เอาเข้าได้ทีละไฟล์"
- ไฟล์ที่ชื่อไม่ลงท้าย `.mp4` → "รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน" โดยไม่ส่ง
- ส่ง `POST /api/spoil/imports/check` ก่อน (`sendJson`); error → แสดงตามกฎข้างล่างโดยไม่ส่งไฟล์
- ส่ง `POST /api/spoil/imports` ด้วย `XMLHttpRequest`, `Content-Type: application/octet-stream`, ไม่มี timeout ของ `lib/api`
- `201` → "เอาไฟล์เข้าเสร็จ: {title}" และ highlight แถวใหม่; `409` `duplicate` → "ไฟล์นี้เอาเข้าไว้แล้ว" และ highlight `clip_id`; `400`/`409` อื่น → `message` จาก API; network ล้ม → state offline
- ยกเลิก → `xhr.abort()` แล้ว "ยกเลิกแล้ว"
- ระหว่าง importing ปิด tab ของ browser → การส่งหยุด, backend ลบไฟล์ค้าง
- XHR `error` ระหว่างส่ง (server ตอบก่อนรับ body ครบ) → "เอาไฟล์เข้าไม่สำเร็จ ลองอีกครั้ง" ไม่ใช่ offline; `408` `stalled` → `message` (D55)

กฎอื่น:
- เปิด tab → `GET /api/spoil/downloads/current` ครั้งหนึ่ง; งานยังไม่จบ → เข้า state downloading; งานจบแล้ว → แสดงข้อความผลของงานนั้น (D15)
- poll `GET /api/spoil/downloads/current` ทุก 1 วินาทีเฉพาะตอนงานยังไม่จบ; จบแล้ว → `GET /api/spoil/clips` ครั้งเดียว (D6)
- ลบ → `window.confirm("ลบ {title}?")` ก่อน; แถวนั้นเล่นอยู่ → ปลด player (`src` ว่างแล้ว `load()`) ก่อน `DELETE` (D15); สำเร็จ → เอาแถวออก
- กดแถว → `<video controls>` ที่ `src` = `/api/spoil/clips/{id}/video` แสดงเหนือรายการ; แถวที่ถูกลบหายจาก player ด้วย
- รายการมีหัว "คลิปที่โหลดมา" พร้อมจำนวนคลิป; แถวที่เล่นอยู่มี badge "กำลังเล่น" (D18)
- ความยาวแสดงเป็น `h:mm:ss` หรือ `m:ss`; ขนาดไฟล์เป็น MB หรือ GB ทศนิยมหนึ่งตำแหน่ง; เวลาโหลดเป็นเวลาท้องถิ่น
- ข้อความในหน้าเป็นภาษาไทย

กล่องถอดบทพูดใน tab คลิป (D22–D25, spoil-maker D53):

| State | เมื่อไร | แสดง |
|---|---|---|
| ยังไม่เลือก | ไม่มีคลิปที่เลือก | "เลือกคลิปจากรายการ" |
| not ready | แถว gate ของงานถอด (D27) ไม่ผ่าน | player และ "ยังติดตั้งไม่ครบ: {label ที่ขาด}" กับลิงก์ "ไปหน้าติดตั้ง" แทนปุ่มถอด |
| เลือกแล้ว | คลิปไม่มี Transcript | player, ชื่อ, ความยาว, ปุ่ม "ถอดบทพูด" |
| ถอดแล้ว | `transcribed` เป็น `true` | alert "คลิปนี้ถอดแล้ว", ปุ่ม "ถอดใหม่", Transcript (บรรทัด `edited` มีป้าย "แก้แล้ว"); ไม่มีบรรทัด → "ไม่พบคำพูดในคลิปนี้" ไม่มีปุ่ม Copy, `.txt`, `.srt` (D33) |
| กำลังถอด | งานของคลิปนี้ยังไม่จบ | "กำลังเตรียมเสียง…" กับแถบไม่มีตัวเลข หรือ "กำลังถอด" กับแถบ % และ "{percent}%" ขวา (component `Download progress`, D33), ปุ่ม "ยกเลิก"; cancel_requested → "กำลังยกเลิก…" |
| คลิปอื่นกำลังถอด | งานของคลิปอื่นยังไม่จบ | ปุ่มถอด disabled กับ "กำลังถอด {ชื่อคลิปนั้น}" |
| แก้บรรทัด | กด "แก้" ของบรรทัด | บรรทัดนั้นเป็นช่องพิมพ์ที่มีข้อความเดิม กับปุ่ม "บันทึก" และ "ยกเลิก" (spoil-maker D54) |

กฎอื่นของกล่อง:
- กดแถว = เลือกคลิปนั้นและเล่นใน player ของกล่อง (แทน player เหนือรายการ, D25); แถวที่เลือกมี badge "กำลังเล่น" (D18)
- เปิด tab → `GET /api/spoil/transcriptions/current` ครั้งหนึ่ง; งานยังไม่จบ → เลือกคลิปนั้นและเข้า state กำลังถอด
- poll `GET /api/spoil/transcriptions/current` ทุก 1 วินาทีเฉพาะตอนงานยังไม่จบ แยกจาก poll ของงานโหลด; จบ → `GET /api/spoil/clips` ครั้งเดียว และถ้า `done` โหลด Transcript ของคลิปที่เลือก
- ข้อความหลังงานถอดจบ: `done` → "ถอดเสร็จ"; `cancelled` → "ยกเลิกแล้ว"; `failed` → `error.message`; poll ได้ `null` → "งานถอดหายเพราะ backend เริ่มใหม่ ลองถอดอีกครั้ง". เป็น `Alert` ในกล่อง ใต้ชื่อคลิปและความยาว: `done` success, `cancelled` info, `failed` error, `null` warning; `404` ของ `POST` → "ไม่พบคลิปนี้" error (D33)
- บรรทัดของ Transcript: `[hh:mm:ss] ข้อความ`; กด → `video.currentTime = start_s` แล้วเล่น; ใต้หัวแสดง "ภาษา: {language}" หรือ "ภาษา: ไม่ทราบ" เมื่อ `null` (D29)
- ผลของ `POST /transcriptions`: `409` `busy` ที่งานเป็นของคลิปนี้ → เข้า state กำลังถอด; `busy` ของคลิปอื่น → "กำลังถอด {ชื่อคลิปนั้น}"; `404` `not_found` → "ไม่พบคลิปนี้" แล้วโหลดรายการใหม่; `503` `not_ready` → state not ready ของกล่อง; อื่น → offline (D29)
- แก้บรรทัด (spoil-maker D54): ชี้บรรทัดแล้วมีปุ่ม "แก้"; "บันทึก" → `PATCH /api/spoil/clips/{id}/transcript/lines/{n}` ได้ `200` → แทนบรรทัดนั้นพร้อมป้าย "แก้แล้ว"; "ยกเลิก" → กลับเป็นข้อความเดิม ไม่ส่งอะไร; ช่องว่างหลังตัดช่องว่าง → "บันทึก" กดไม่ได้; `409` `transcribing` หรือ `clip_busy` → ข้อความตาราง Frontend ของ spoil-maker
- ถอดใหม่ได้ `409` `has_edits` → ถามยืนยัน "ถอดใหม่จะลบบทพูดที่แก้ไว้"; ยืนยัน → ส่ง `POST /transcriptions` ซ้ำพร้อม `confirm_edit_loss: true` (spoil-maker D54)
- Copy → คัดลอกเนื้อเดียวกับ `.txt` ด้วย `useCopy`; `.txt` และ `.srt` เป็นลิงก์ไป API (browser โหลดไฟล์เอง)
- ลบคลิปที่เลือกอยู่ → กล่องกลับเป็น "ยังไม่เลือก"; `409` `transcribing` → `message` ใต้แถว
- แถวที่ `transcribed` มี badge "ถอดแล้ว" (D23)
- จอกว้าง ≥ 1024px สองคอลัมน์มีลูกศร →; แคบกว่าเรียงบนลงล่างมีลูกศร ↓ (D25). คอลัมน์ซ้ายกว้าง 520px มีช่องลิงก์, แถบโหลด และรายการ; กล่องกินที่เหลือ (D33)

ส่วนตัดช่วงในกล่องถอดบทพูด (D38, D41; แบบ `pending` ตาม D40, sketch [trim-sketch.md](trim-sketch.md)):

| State | เมื่อไร | แสดง |
|---|---|---|
| ปิด | เลือกคลิปแล้ว ไม่ได้เปิดส่วนตัด | ปุ่ม "ตัดช่วง" ใต้ชื่อคลิปและความยาว; disabled เมื่อแถว `ffmpeg` ไม่ `ok` หรืองานถอดของคลิปนี้ยังไม่จบ |
| เลือกช่วง | กด "ตัดช่วง" | timeline, รายการช่วง, "เพิ่มช่วง", "ตัดออก {x} · เหลือ {y}", "ตัดคลิป", "ยกเลิก"; ปุ่มถอด disabled กับ "กดตัดคลิปหรือยกเลิกก่อน" |
| กำลังตัด | Trim job ของคลิปนี้ `trimming` | player ปลด (`src` ว่างแล้ว `load()`); "กำลังตัดคลิป" กับแถบ % แบบ `Download progress` และ "{percent}%"; ปุ่ม "ยกเลิก"; `cancel_requested` → "กำลังยกเลิก…" |
| กำลังแทนไฟล์ | `replacing` | "กำลังแทนไฟล์…" กับแถบไม่มีตัวเลข ไม่มีปุ่มยกเลิก |
| คลิปอื่นกำลังตัด | Trim job ของคลิปอื่นยังไม่จบ | "ตัดช่วง" disabled กับ "กำลังตัด {ชื่อคลิปนั้น}" |

กฎของส่วนตัดช่วง:
- ช่วงที่ยังไม่ส่งเก็บใน memory แยกตาม `clip_id` ตลอดที่หน้าเปิดอยู่; "ยกเลิก" ล้างช่วงของคลิปนั้นและปิดส่วนตัด (D38)
- เปิดส่วนตัดครั้งแรกไม่มีช่วง; "เพิ่มช่วง" เพิ่มช่วงที่ตำแหน่งเล่นยาว 30 วินาที ตัดให้อยู่ในคลิปและไม่ทับช่วงอื่น; มี 20 ช่วงแล้ว หรือไม่มีที่ว่างพอ 0.5 วินาที → disabled
- timeline: ความกว้างทั้งหมด = `duration_s`; กดที่ว่าง → `video.currentTime` ไปตรงนั้น; ช่วงเป็นแถบทึบที่มีหัวท้ายลากได้ (pointer events); หัวลากไม่ข้ามหัวอีกข้างของช่วงเดียวกันหรือช่วงข้างเคียง; ปัดเวลาเป็น 0.1 วินาที
- หัวลากเป็น `role="slider"` โฟกัสได้ มี `aria-valuetext` เป็นเวลา; ลูกศรขวา/ขึ้น +1 วินาที ซ้าย/ลง −1 วินาทีตามแบบ slider ของ ARIA (D46), Shift ±10 วินาที; เป้าแตะ ≥ 44px
- แต่ละช่วงในรายการ: ช่องเวลาเริ่มและจบแบบ `h:mm:ss.s` (รับ `m:ss` และ `ss` ด้วย); พิมพ์ผิดรูป อยู่นอกคลิป หรือเริ่มไม่น้อยกว่าจบ → ช่องเป็น error และ "ตัดคลิป" disabled; "เริ่ม = ตอนนี้" และ "จบ = ตอนนี้" ใช้ `video.currentTime`; "✕" ลบช่วง
- "ตัดออก {x} · เหลือ {y}" คิดจากช่วงที่รวมกันแล้วแบบเดียวกับ backend; เหลือน้อยกว่า 10 วินาที หรือไม่มีช่วง → "ตัดคลิป" disabled
- กด "ตัดคลิป" → ส่ง `POST /trims` เลยแบบงานถอด; ได้ `409` `has_derived` → `window.confirm(message)` (message ของ API เป็นคำถามเต็ม; การตัด EP มีได้เฉพาะคลิปที่บรรยายฉากแล้ว, spoil-maker D66 จึงใช้คำเดียวกับ Shot); ยืนยัน → ส่งซ้ำพร้อม `confirm_derived_loss: true`; ไม่ยืนยัน → คืน player (D37, D46)
- ก่อนส่ง `POST /trims` ปลด player; ได้ `409` `has_derived` (ข้อมูลเปลี่ยนหลังโหลดรายการ) → ถามยืนยันด้วยรายการจาก `derived` แล้วส่งซ้ำ; error อื่นของ `POST` → ข้อความในตาราง API เป็น Alert error ในกล่อง แล้วโหลด player กลับ
- เปิด tab → `GET /api/spoil/trims/current` ครั้งหนึ่ง; งานยังไม่จบ → เลือกคลิปนั้นและเข้า state ของงาน
- poll `GET /api/spoil/trims/current` ทุก 1 วินาทีเฉพาะตอนงานยังไม่จบ แยกจาก poll อื่น; จบ → `GET /api/spoil/clips` ครั้งเดียว และโหลด player ใหม่ด้วย `?v=` ใหม่
- ข้อความหลังงานจบเป็น `Alert` ในกล่องแบบงานถอด (D33): `done` success "ตัดคลิปเสร็จ: เหลือ {h:mm:ss}" แล้วปิดส่วนตัดและล้างช่วง; `cancelled` info "ยกเลิกแล้ว" ช่วงยังอยู่; `failed` error `error.message` ช่วงยังอยู่; poll ได้ `null` warning "งานตัดหายเพราะ backend เริ่มใหม่ ลองตัดอีกครั้ง"
- `DELETE /trims/current` ได้ `409` `replacing` → "กำลังแทนไฟล์ ยกเลิกไม่ได้แล้ว"
- `src` ของ player ทุกที่เป็น `/api/spoil/clips/{id}/video?v={trimmed_at ?? downloaded_at}` (D41)
- แถวที่ `trimmed` ไม่ว่างมี badge "ตัดแล้ว" ก่อน "ถอดแล้ว"; ความยาวในแถวและกล่องใช้ `duration_s` ใหม่
- ลบคลิปได้ `409` `trimming` → `message` ใต้แถว; ถอดได้ `409` `trimming` → "กำลังตัดคลิปนี้อยู่" ในกล่อง

### Ops

- ที่ดิสก์: wheel `deno` ประมาณ 80 MB ใน `.venv`; คลิป 1080p ประมาณ 0.5–1.5 GB ต่อชั่วโมง ใน `media/temp/`
- ลบคลิปทั้งหมดด้วยมือได้โดยลบ folder `media/temp/` ตอน backend ไม่ได้รัน (README)
- YouTube เปลี่ยนแล้วโหลดไม่ได้ทุกคลิป → `uv lock --upgrade-package yt-dlp` แล้วรัน Setup script (D8, README)
- งานถอดใช้ memory ของ process ลูกประมาณ 2–4 GB (โมเดล 1.6 GB กับเสียงช่วงละ 300 วินาทีประมาณ 19 MB) ไม่โตตามความยาวคลิป และคืนทั้งหมดเมื่อ process ลูกออก (D28, D29)
- งานถอดมีปัญหา: กดยกเลิก หรือปิด `npm run dev` — process ลูกถูก terminate; ปิด feature ทั้งหมดไม่ได้นอกจากไม่กดถอด
- งานตัดใช้ที่ดิสก์ชั่วคราวเท่าไฟล์ใหม่ใน `.partial/` จนแทนไฟล์เสร็จ; ใช้ CPU หนักบน Windows (`libx264`) — ถอดคลิปอื่นพร้อมกันได้แต่ช้าลง
- ตัดพลาด: ไม่มีต้นฉบับให้คืน — ลบคลิปแล้วโหลดใหม่หรือเอาไฟล์เข้าใหม่ (D36)
- revert change นี้: คลิปที่ไม่ใช่ YouTube ไม่ขึ้นในรายการ — ลบในแอปก่อน revert หรือลบ `media/temp/{id}.*` ด้วยมือ (D55)
- เว็บหนึ่งเปลี่ยนแล้วโหลดไม่ได้ → อัปเดต yt-dlp แบบเดียวกับ YouTube; ยังไม่ได้ → ผู้ใช้โหลดเองแล้วเอาไฟล์เข้า (D47)

## Seams

ห้า seam: API ของสปอยกับ adapter ปลอม, adapter จริงกับ YouTube, adapter จริงของ Whisper, ffmpeg จริงของงานตัด (3a), และหน้าเว็บ — เพราะ yt-dlp กับ YouTube จริงช้าและเปลี่ยนตลอด จึงแยก adapter ไว้ตัวเดียวให้ส่วนอื่นทดสอบได้เร็ว (D14).

1. **Spoil API** `/api/spoil/*` และ `GET /api/setup/status` ด้วย `TestClient`, root ปลอมใน `tmp_path` และ adapter ปลอม
   - ลิงก์ทุกแบบในตารางลิงก์ → `202`; `https://vimeo.com/1` → `202`; `https://www.youtube.com/playlist?list=x`, `ftp://x.com/a`, `http://localhost:8000/a`, `http://127.0.0.1/a`, `http://192.168.1.5/a`, `http://[::1]/a`, `http://169.254.169.254/` → `400` `invalid_url` (D52)
   - adapter ปลอมคืน info `extractor_key` `Facebook` id `123` → `done` และ json `id` `facebook-123`, `site` `Facebook`; โหลดลิงก์เดิมอีกครั้ง → งาน `failed` `duplicate` กับ `clip_id` `facebook-123` และไม่เรียก download (D51)
   - id ยาว 80 ตัว → id ยาว 64 ตัวตรง `CLIP_ID`; id `a.b` กับ `a_b` ของเว็บเดียวกัน → id ต่างกัน; id `BVabc` กับ `bvabc` → ต่างกัน (D55)
   - format selector กับ list format ปลอม: มีแต่ `hevc` หรือมีแต่ด้านสั้น 1440 → `failed` `unsupported_format` และ download ไม่ถูกเรียก; มี `avc1` 1080×1920 → เลือกตัวนั้น (D54)
   - ตัวตรวจไฟล์กับ stderr ปลอม: `yuv422p10le` → ไม่ผ่าน; `attached_pic` เป็น stream แรกตามด้วย h264 → ผ่าน; 1920×1080 กับ rotation 90 → `width` 1080 `height` 1920 `portrait` (D55)
   - stream ปลอมไม่ส่ง byte 60 วินาที (เวลาปลอม) → `408` `stalled`, `.partial/` ว่าง และ `POST /imports` ถัดไปไม่ได้ `busy`
   - start app ขณะ `media/temp/` มี `notes.txt` และ `facebook-1.mp4` ที่ไม่มี json → `notes.txt` อยู่, `facebook-1.mp4` หาย
   - adapter ปลอม raise "Unsupported URL" → `failed` `unsupported`; info `_type` `playlist` → `failed` `playlist`
   - `POST /imports` mp4 h264/aac 640×360 จาก lavfi (ffmpeg จริง) → `201`, `{id}.mp4` byte เท่าต้นทาง, json `site` `local`, `channel` `null`, `title` ตามชื่อ, มี thumbnail; `GET /clips` มีแถว (D49)
   - mp4 hevc, mp4 1920×1440 (ด้านสั้น 1440), mp4 เสียง opus, ไฟล์ขยะชื่อ `.mp4` → `400` `unsupported_file` ที่ `message` บอกข้อที่ไม่ตรง และ `.partial/` ว่าง, ไม่มี json
   - `name` `a.mkv` → `400` `not_mp4` และ body ไม่ถูกเขียน; `size` ไม่ตรง byte จริง → `400` `size_mismatch`
   - ไฟล์ชื่อและขนาดเดิมซ้ำ → `409` `duplicate` กับ `clip_id`; `POST /imports/check` ของไฟล์นั้น → `409` `duplicate`, ของไฟล์ใหม่ → `200` กับ `clip_id` ที่เท่ากับ id ที่ `/imports` สร้าง
   - ระหว่าง File import (stream ปลอมรอสัญญาณ): `POST /downloads` → `409` `busy`; `POST /imports` อื่น → `409` `busy`; ระหว่าง Download job: `POST /imports` → `409` `busy`
   - ที่ว่างปลอมน้อยกว่า `size` + 1 GiB → `409` `disk_full`
   - client ตัดกลางทาง (stream ปลอม raise `ClientDisconnect`) → `.partial/` ว่าง และ `POST /imports` ถัดไป → `201`
   - `POST /imports` ที่ `multipart/form-data` หรือ `application/json` → `415`; route อื่นที่ `application/octet-stream` → `415` (D50)
   - json เดิมไม่มี `site` → `GET /clips` ได้ `site` `Youtube`; คลิป id `local-…` และ `facebook-123`: `GET /clips/{id}/video`, ถอด, ตัด, ลบ ทำได้เหมือนคลิป YouTube
   - adapter ปลอมสำเร็จ → poll จน `done`, `GET /clips` มีคลิปนั้นพร้อมทุกฟิลด์ และ `/clips/{id}/video` ตอบ `206` เมื่อส่ง `Range: bytes=0-99`
   - ลิงก์ของ id ที่มี json แล้ว → `409` `duplicate` กับ `clip_id`
   - POST ระหว่างงานยังไม่จบ → `409` `busy`
   - adapter ปลอมคืน `live_status: is_live` → `failed` `live`
   - ที่ว่างปลอมน้อยกว่าขนาดประมาณ + 1 GiB → `failed` `disk_full` และ adapter ไม่ถูกเรียกโหลด
   - `DELETE /downloads/current` ระหว่าง `downloading` → `cancelled` และ `.partial/` ไม่มีไฟล์ของ id นั้น
   - json ที่ไม่มี mp4 คู่ หรือ json เสีย → ไม่อยู่ใน `GET /clips`
   - `DELETE /clips/{id}` → `204` และไฟล์ทั้งสามหาย; `/clips/../x/video` → `404`
   - start app ขณะ `.partial/` มีไฟล์ → ไฟล์หาย
   - deno probe raise → แถว `deno` เป็น `missing`, มี 11 แถว, และ `POST /downloads` → `503` `not_ready`
   - marker ของโมเดลหาย แต่ probe สามตัวผ่าน → `POST /downloads` → `202` (D9)
   - ยกเลิกระหว่าง `checking` (adapter ปลอมรอสัญญาณใน `fetch_info`) → `cancelled` และไม่มีไฟล์
   - `DELETE /downloads/current` ระหว่าง `merging` → `409` `merging` และงานจบเป็น `done`
   - POST สองครั้งพร้อมกันจากสอง thread → หนึ่ง `202` หนึ่ง `409` `busy`
   - adapter ปลอม raise error ที่มี "Sign in to confirm" → `failed` `login_required`
   - adapter ปลอม raise `GeoRestrictedError` → `failed` `unavailable`
   - adapter ปลอม raise error อื่น → `download_error` ที่มี `yt_dlp_version` และ `fix`
   - `DELETE /clips/{id}` ขณะลบ mp4 ไม่ได้ (monkeypatch ให้ raise `PermissionError`) → `409` `in_use` และ json ยังอยู่
   - start app ขณะมี `{id}.mp4` ที่ไม่มี json → ไฟล์หาย
   - request ที่ `Host: evil.example` → `400`
   - worker ปลอมส่งสองช่วง → poll จน `done`, `GET /clips/{id}/transcript` มีบรรทัดที่เวลาของช่วงสองบวก 300; `GET /clips` มี `transcribed: true`
   - `.txt` และ `.srt` ของ Transcript สองบรรทัด → เนื้อตรงตัวอย่างใน test; `Content-Disposition` มีชื่อไฟล์
   - POST ถอดระหว่าง Download job ยังไม่จบ → `202` (D24); POST ถอดระหว่าง Transcribe job ยังไม่จบ → `409` `busy`
   - `DELETE /transcriptions/current` ระหว่างช่วงแรก (worker ปลอมรอสัญญาณ) → `cancelled`, worker ปลอมถูก terminate และ Transcript เดิมยังอยู่
   - worker ปลอมส่ง `error` `no_audio` → `failed` `no_audio`; ส่ง `error` `model_failed` → `failed` `model_failed`
   - worker ปลอมออกโดยไม่ส่ง `done` → `failed` `crashed`; POST ถัดไป → `202`
   - เขียน Transcript ไม่ได้ (monkeypatch rename ให้ raise) → `failed` `internal` และ POST ถัดไป → `202`
   - `POST /transcriptions` และ `POST /downloads` ที่ `Content-Type: text/plain` → `415`
   - start app ขณะมี `{id}.transcript.json.tmp` → ไฟล์หาย; `GET /clips` ไม่มีแถวของ `*.transcript.json`
   - worker ปลอมส่งช่วงที่ภาษา `null` ทุกช่วง → `language` เป็น `null`
   - marker ของ Whisper หาย → `POST /transcriptions` → `503` `not_ready`; device `cpu` → `503`
   - `DELETE /clips/{id}` ระหว่างถอดคลิปนั้น → `409` `transcribing`; หลังงานจบ → `204` และ `{id}.transcript.json` หาย
   - worker ปลอมส่งช่วงที่ไม่มีบรรทัด → `done` และ `lines` ว่าง
   - `PATCH /clips/{id}/transcript/lines/1` `{"text": "Home."}` → `200`; `GET /clips/{id}/transcript` บรรทัด 1 มีข้อความใหม่และ `edited: true`, บรรทัดอื่นไม่มี `edited`, เวลาและจำนวนบรรทัดเท่าเดิม; `.txt` มีข้อความใหม่ (spoil-maker D54)
   - `PATCH` `text` ช่องว่างล้วน → `400` `invalid_request`; บรรทัด `n` ที่ไม่มี → `404` `not_found`
   - `PATCH` ระหว่าง Transcribe job ของคลิปนั้น → `409` `transcribing`
   - คลิปที่มีบรรทัด `edited`: `POST /transcriptions` ไม่มี `confirm_edit_loss` → `409` `has_edits`; มี `confirm_edit_loss: true` → `202` และหลัง `done` ไม่มีบรรทัด `edited`
   - `POST /trims` คลิป 100 วินาทีช่วง 0–10 และ 90–100 กับ `run_ffmpeg` ปลอม → poll จน `done`; json มี `duration_s` 80 (จาก probe ปลอม), `trimmed` สองช่วง, `trimmed_at`, `file_bytes` ของไฟล์ใหม่; `.partial/` ว่าง (D36)
   - argv ของ ffmpeg สำหรับช่วงเดียวกัน → มี `trim=10:90` กับ `atrim=10:90` ช่วงเดียว, `concat=n=1:v=1:a=1`, `-b:v` ตามสูตร D41; `sys.platform` `darwin` → `h264_videotoolbox`, `win32` → `libx264`; คลิปไม่มีเสียง → `a=0` ไม่มี `atrim`
   - ช่วง 10–30 กับ 20–40 → รวมเป็น 10–40 ช่วงเดียว; ช่วง 0–95 ของคลิป 100 วินาที → `400` `invalid_ranges`; 21 ช่วง, `end_s` เกิน `duration_s`, ยาว 0.4 วินาที, `start_s` เป็น `true` → `400`
   - คลิปที่ถอดแล้วไม่มี `confirm_derived_loss` → `409` `has_derived` กับ `derived: ["transcript"]` และไม่มีงาน; มี → `done` แล้ว `GET /clips` มี `transcribed: false` (D37)
   - คลิปที่บรรยายฉาก ตัด EP และอยู่ใน Spoil draft → `derived` มี `shots`, `episodes`, `draft`; หลัง `done` ไม่มี Shot ไฟล์การตัด EP และ `GET /api/spoil-maker/draft` เป็น `null`
   - `DELETE /trims/current` ระหว่าง `trimming` (ffmpeg ปลอมรอสัญญาณ) → `cancelled`, ffmpeg ปลอมถูก kill, mp4 และ Transcript เดิมยังอยู่
   - ffmpeg ปลอม exit 1 → `failed` `ffmpeg_failed`, mp4 เดิมยังอยู่; POST ถัดไป → `202`
   - `os.replace` ของ mp4 raise `PermissionError` ทุกครั้ง (monkeypatch, เวลารอปลอม) → `failed` `in_use`, Transcript ยังอยู่, ไม่มี `{id}.trimming.json`
   - ระหว่าง Trim job: `POST /transcriptions`, `PATCH` บรรทัด และ `DELETE /clips/{id}` ของคลิปนั้น → `409` `trimming`; `POST /describes` ของคลิปนั้น → `409` `clip_busy`; `POST /trims` ของคลิปอื่น → `409` `busy`; `POST /downloads` → `202`
   - ระหว่าง Transcribe job ของคลิปนั้น → `POST /trims` `409` `transcribing`; ระหว่าง Describe job ของคลิปนั้น → `409` `clip_busy`
   - ระหว่าง Trim job: `POST /api/spoil-maker/render-jobs` และ Voice job `sentences` ของ draft ที่ใช้คลิปนั้น, `PUT` การตัด EP ของคลิปนั้น → `409` `clip_busy` (D42)
   - Draft job `kind: "pick"` เริ่มพร้อมกับ `replacing` (ffmpeg ปลอมคืนแล้ว test ยิงสอง thread) → ไม่ค้าง: อย่างใดอย่างหนึ่งได้ `409` และอีกงานจบ (D42)
   - ffmpeg ปลอมเขียนไฟล์ที่ probe ปลอมบอกว่าสั้นกว่า `kept_s` 5 วินาที หรือไม่มีเสียงทั้งที่ต้นฉบับมี → `failed` `ffmpeg_failed`, mp4 และ Transcript เดิมยังอยู่ (D42)
   - `os.replace` raise `PermissionError` สองครั้งแล้วผ่าน → `done` (D42)
   - json ที่ `duration_s` เป็น `null` → ตรวจช่วงด้วยความยาวจาก probe ได้ `202`
   - `DELETE /trims/current` ระหว่าง `replacing` → `409` `replacing` และงานจบเป็น `done`
   - ที่ว่างปลอมไม่พอ → `failed` `disk_full` และ ffmpeg ปลอมไม่ถูกเรียก
   - start app ขณะมี `{id}.trimming.json` และ `.partial/{id}.trim.mp4` → marker หาย, json และ Transcript เดิมอยู่; มี marker แต่ไม่มีไฟล์ใน `.partial/` → json เป็นเนื้อของ marker และ Transcript หาย (D41)
   - json ไม่มี `trimmed` → `GET /clips` ได้ `trimmed: []` และ `trimmed_at: null`; `GET /clips` ไม่มีแถวของ `*.trimming.json`
   - `POST /trims` ที่ `Content-Type: text/plain` → `415`; แถว `ffmpeg` ไม่ `ok` → `503` `not_ready`
2. **yt-dlp adapter** `backend.spoil` กับ YouTube จริง (เช็คมือ ไม่อยู่ใน test ที่รันทุกครั้ง)
   - Shorts หนึ่งคลิป → mp4 ด้านสั้น ≤ 1080 และมีเสียง
   - คลิปแนวนอนยาวกว่า 1 ชั่วโมง → mp4 1920×1080 หรือเล็กกว่า
   - กดยกเลิกที่ประมาณ 30% → หยุดภายใน 5 วินาที ไม่มีไฟล์ค้าง
   - ลิงก์ live ที่ยังไม่เริ่ม → `live`
   - Ctrl+C ระหว่างโหลด แล้ว `npm run dev` ใหม่ → ไม่มี process ค้าง และ `.partial/` ว่าง
   - Windows: เล่นคลิปใน player แล้วกดลบ → ลบได้ หรือได้ `in_use` และแถวยังอยู่
   - คลิป public หนึ่งคลิปจาก Facebook และ TikTok → mp4 ด้านสั้น ≤ 1080 มีเสียง; บันทึกข้อความ error จริงของลิงก์ที่ต้อง login และลิงก์ที่ไม่รองรับลง `docs/library-notes/yt-dlp.md` (D47, D52)
   - ไฟล์ ≥ 4 GB ผ่าน `npm run dev` (proxy ของ Vite) → `201`; ถูกตัดที่ราว 300 วินาที → ตั้ง `requestTimeout` ของ dev server ด้วย plugin เล็กใน `vite.config.ts`; แก้ไม่ได้ → หยุดแล้วถามผู้ใช้ (D55)
   - คลิป TikTok ที่มีแต่ HEVC → `unsupported_format` ก่อนโหลด (D54)
   - ลากไฟล์ mp4 ยาวกว่า 1 ชั่วโมงในหน้าเว็บจริง → % เดิน, ยกเลิกกลางทางแล้ว `.partial/` ว่าง; จดเวลาที่ใช้ของไฟล์ 2 GB ลง progress.md
3. **Whisper adapter** `backend.spoil.whisper` กับโมเดลจริง (เช็คมือ ไม่อยู่ใน test ที่รันทุกครั้ง)
   - Shorts ภาษาไทยและหนังภาษาอังกฤษยาวกว่า 1 ชั่วโมง → Transcript อ่านรู้เรื่อง ภาษาตรง เวลาของบรรทัดตรงกับเสียงในคลิปภายใน 2 วินาที (สุ่มดู 5 บรรทัด)
   - ยกเลิกกลางหนัง → process ลูกหายภายใน 5 วินาที (`ps`) และ memory ของ backend ไม่โตขึ้น
   - ฆ่า process ลูกด้วยมือระหว่างถอดขณะมีงานโหลด → งานถอด `crashed`, งานโหลดเดินต่อจน `done`
   - ช่วงละ 300 วินาทีให้ timestamp ของ `chunks` เป็นเวลาภายในช่วง และบรรทัดสุดท้ายที่ `timestamp` จบเป็น `None` → ใช้ความยาวช่วงแทน
   - ถอดพร้อมโหลดคลิปอื่น → ทั้งสองงาน `done`
   - Windows NVIDIA: ถอดได้บน `cuda`
3a. **ffmpeg ของงานตัด** `backend.spoil.trim` กับ ffmpeg จริง (เช็คมือ ไม่อยู่ใน test ที่รันทุกครั้ง)
   - หนังยาวกว่า 1 ชั่วโมงตัดสองช่วง → เล่นได้ใน player, ความยาวตรงภายใน 1 วินาที, ภาพและเสียงตรงกันรอบรอยตัด, ขนาดไฟล์ต่อนาทีไม่เกิน 1.2 เท่าของเดิม; จดเวลาที่ใช้ลง progress.md
   - คลิปไม่มีเสียงหนึ่งคลิป → ตัดได้
   - ยกเลิกที่ประมาณ 30% → ffmpeg หายภายใน 5 วินาที (`ps`), ไฟล์เดิมเล่นได้
   - ตัดแล้วถอด → ไม่มีบรรทัดของช่วงที่ตัด; บรรยายฉาก → Shot แรกเริ่มที่ฉากแรกหลังรอยตัด
   - Windows NVIDIA: ตัดด้วย `libx264` ได้; ตัดขณะ player เปิดคลิปอยู่ในอีก tab ของ browser → `done` หรือ `in_use` ที่ไฟล์เดิมยังเล่นได้ — เช็คใน `windows-check` (ADR-0016)
4. **tab คลิป** `frontend` ด้วย Vitest และ fetch ปลอม (spoil-maker D53)
   - hash ว่าง → เห็นหน้า tab ติดตั้ง; กด tab คลิป → hash เป็น `#/clips`
   - status ที่ `deno` เป็น `missing` → "ยังติดตั้งไม่ครบ: Deno" และไม่มีช่องลิงก์
   - วางลิงก์ กดโหลด, current คืน `downloading` 40 แล้ว `done` → เห็น 40%, แล้ว "โหลดเสร็จ" และแถวใหม่
   - `409` `duplicate` → "คลิปนี้โหลดไว้แล้ว" และแถวนั้น highlight
   - งาน `failed` → เห็น `error.message`; มี `fix` → เห็นคำสั่งพร้อมปุ่ม copy
   - current คืน `downloading` ที่ `percent: null` → แถบไม่มีตัวเลข
   - กำลังติดตามงานแล้ว current คืน `null` → "งานโหลดหายเพราะ backend เริ่มใหม่"
   - เปิด tab แล้ว current เป็น `failed` → เห็น `error.message`
   - กดยกเลิก → ส่ง `DELETE /api/spoil/downloads/current`; current คืน `cancel_requested: true` → เห็น "กำลังยกเลิก…"
   - รายการว่าง → "ยังไม่มีคลิป วางลิงก์หรือเลือกไฟล์ด้านบน"
   - เลือกไฟล์ `a.mp4` (XHR ปลอมยิง progress 50%) → "กำลังเอาไฟล์เข้า a.mp4" 50% แล้ว `201` → "เอาไฟล์เข้าเสร็จ" และแถวใหม่ "ไฟล์ในเครื่อง"; กดยกเลิก → `abort()` ถูกเรียก
   - เลือก `a.mkv` → "รับเฉพาะไฟล์ mp4…" และไม่มี request; ลากไฟล์มาวาง → ส่ง request เดียวกับปุ่ม
   - `400` `unsupported_file` → เห็น `message`; `409` `duplicate` → highlight แถว
   - งาน `failed` `duplicate` กับ `clip_id` → highlight แถวนั้น; `failed` `unsupported` → เห็น message
   - แถว `site` `Facebook` แสดงชื่อเว็บ
   - กดแถว → มี `<video>` ที่ `src` ถูก; กดลบและยืนยัน → แถวหาย
   - ยังไม่เลือก → "เลือกคลิปจากรายการ"; กดแถว → กล่องมีชื่อคลิปและปุ่ม "ถอดบทพูด"
   - กดถอด, current คืน `transcribing` 35 แล้ว `done` → เห็น "กำลังถอด 35%" แล้วบรรทัดของ Transcript และแถวมี "ถอดแล้ว"
   - กดบรรทัดเวลา 12.4 → `currentTime` ของ video เป็น 12.4
   - กด Copy → clipboard ได้บรรทัด `[00:00:12] ...`; ลิงก์ `.srt` ชี้ `/api/spoil/clips/{id}/transcript.srt`
   - เปิด tab ขณะ current ของงานถอดเป็น `transcribing` → คลิปนั้นถูกเลือกและเห็น %
   - status ที่ `model_whisper` เป็น `missing` → ไม่มีปุ่มถอด เห็นลิงก์ "ไปหน้าติดตั้ง"; ช่องลิงก์โหลดยังใช้ได้
   - ชี้บรรทัด กด "แก้" พิมพ์แล้วกด "บันทึก" → ส่ง `PATCH` และบรรทัดมีป้าย "แก้แล้ว"; กด "ยกเลิก" → ไม่ส่ง `PATCH` (spoil-maker D54)
   - ถอดใหม่ได้ `409` `has_edits` และยืนยัน → ส่ง `POST /transcriptions` ซ้ำพร้อม `confirm_edit_loss: true`
   - เลือกคลิป กด "ตัดช่วง", "เพิ่มช่วง" ที่ `currentTime` 0 → ช่วง 0:00:00.0–0:00:30.0 และ "เหลือ" ลดลง 30 วินาที; ปุ่มถอด disabled
   - พิมพ์เวลาจบ `1:30` → ช่วงเป็น 0–90; พิมพ์ `abc` → ช่องเป็น error และ "ตัดคลิป" disabled
   - หัวลากของจุดจบโฟกัสแล้วกดลูกศรขวา → จบเพิ่ม 1 วินาที; Shift+ลูกศรขวา → 10 วินาที; ไม่ข้ามจุดเริ่มของช่วงถัดไป
   - กด "จบ = ตอนนี้" ที่ `currentTime` 95.34 → จบเป็น 95.3
   - กด "ตัดคลิป" → `<video>` ไม่มี `src` ก่อน `POST /trims`; ได้ `409` `has_derived` → `window.confirm` แสดง message; ไม่ยืนยัน → ไม่ส่งซ้ำและ player กลับมา
   - current คืน `trimming` 37 แล้ว `done` → เห็น "กำลังตัดคลิป" 37% แล้ว "ตัดคลิปเสร็จ" และ `src` มี `?v=` ใหม่; แถวมี "ตัดแล้ว"
   - `POST /trims` ได้ `409` `has_derived` → ถามยืนยันแล้วส่งซ้ำพร้อม `confirm_derived_loss: true`
   - current คืน `failed` `in_use` → เห็น message และช่วงยังอยู่; current `replacing` → ไม่มีปุ่มยกเลิก
   - เปิด tab ขณะ current ของงานตัดเป็น `trimming` → คลิปนั้นถูกเลือกและเห็น %

## Testing decisions

- **Copy:** `backend/tests/test_app.py` — `TestClient` กับ root ปลอมใน `tmp_path`
- **Copy:** `backend/tests/fakes.py` — เพิ่ม adapter ปลอมของ yt-dlp และ deno probe ปลอมที่นี่; เพิ่ม `start_worker` ปลอมที่รันใน thread ป้อนข้อความเข้า queue และรอสัญญาณได้แบบเดียวกับ adapter ปลอมของ yt-dlp
- **Copy:** `backend/tests/test_spoil_api.py` — โครงของ test งานโหลด (poll จนจบ, ยกเลิกด้วยสัญญาณ) ใช้กับงานถอด
- **Copy:** `frontend/src/features/spoil/components/SpoilPage.test.tsx` (หน้าของ tab คลิป, spoil-maker D53) — fake backend ที่ตอบตาม route; เพิ่ม route ของ `/transcriptions` และ `/transcript`
- **Copy:** `backend/tests/test_spoil_api.py` — test งานถอด (worker ปลอมรอสัญญาณ, ยกเลิก, crash) ใช้กับ Trim job ด้วย `run_ffmpeg` ปลอม; `backend/tests/fakes.py` เพิ่ม `run_ffmpeg` ปลอมที่เขียนไฟล์ผล รายงาน progress และรอสัญญาณได้
- **Copy:** test ของ `clip_busy` และ Spoil draft ใน `backend/tests/` ของ spoil-maker — สร้าง Shot ไฟล์การตัด EP และ draft ปลอมก่อนตัด
- **Copy:** `backend/tests/test_spoil_api.py` › test ของ Trim ที่ใช้ ffmpeg จริงบนคลิป lavfi (feature review ตัดช่วง) — สร้าง mp4 h264/hevc/opus จริงสำหรับ File import; codec ที่ ffmpeg ของ imageio encode ไม่ได้ (hevc) → สร้าง stderr ปลอมของ `probe` แทน
- **Copy:** `frontend/src/features/spoil/components/ClipsPage.test.tsx` — เพิ่ม XHR ปลอม (`upload.onprogress`, `abort`) ใน fake backend
- **Copy:** `backend/tests/test_checks.py` — test แถวใหม่ของ Status check และนับ 11 แถว
- **Copy:** `frontend/src/features/setup-status/components/SetupStatusPage.test.tsx` — fetch ปลอมและการ assert ข้อความ
- test ที่มีอยู่ซึ่งนับ 9 แถวต้องแก้เป็น 11
- test ที่เช็คการล้างไฟล์ตอน start ใช้ `with TestClient(app)` เพื่อให้ lifespan รัน; การล้างอ่าน `paths.ROOT` ตอนรัน จึง monkeypatch ได้
- `TestClient` ทุกตัวใช้ `base_url="http://127.0.0.1"` เพราะ host default `testserver` ไม่ผ่าน `TrustedHostMiddleware`; แก้ `backend/tests/test_app.py` ด้วย
- adapter ปลอมเรียก progress hook เองตามลำดับที่ test กำหนด และรอสัญญาณจาก test ได้ เพื่อทดสอบ busy และยกเลิกแบบไม่ขึ้นกับเวลา
- seam 2 ไม่อยู่ใน test อัตโนมัติ: พิสูจน์ด้วย How success is judged บน Mac; ข้อ Windows เช็คใน `windows-check` 02 (ADR-0014)
- seam 3a ไม่อยู่ใน test อัตโนมัติ: argv ของ ffmpeg, การรวมช่วง และสูตร bitrate ทดสอบเป็น pure function ใน seam 1
- seam 3 ไม่อยู่ใน test อัตโนมัติ ยกเว้นฟังก์ชันที่ไม่แตะโมเดล: `backend/tests/test_whisper.py` ทดสอบ `plan_segments`, `to_lines` และว่า import adapter ไม่ import torch กับ transformers. การบวกเวลาของช่วงจึงพิสูจน์ที่นี่ ไม่ใช่ใน seam 1 ซึ่ง worker ปลอมส่งเวลาของคลิปมาแล้ว (D30)

## Out of Scope

- ตัดต่ออื่นนอกจากตัดช่วงทิ้ง (สลับลำดับ, แทรก, ใส่เอฟเฟกต์), ทำแนวตั้ง, เลือก p ของ output (D2, D5, D36); render อยู่ใน spoil-maker
- เก็บต้นฉบับหรือย้อนการตัด (D36)
- เลื่อนเวลาของ Transcript หรือ Shot ที่มีอยู่ให้ตรงไฟล์ที่ตัด (D37)
- เล่นข้ามช่วงที่เลือกไว้ก่อนกดตัดคลิป (preview) และจำช่วงที่ยังไม่ตัดข้ามการโหลดหน้าใหม่ (D38)
- หาโฆษณาหรือเพลงเปิดอัตโนมัติ
- ซ่อนบรรทัด Transcript ทีละบรรทัด (D39)
- ใส่เสียงเล่าด้วย TTS และการเลือก TTS ที่ใช้เชิงพาณิชย์ได้ (D2, D13)
- แยกเสียงพูดออกจากดนตรี และให้ไฟล์เสียงหรือวิดีโอเงียบกับผู้ใช้ (D21)
- แปลภาษา, แยกผู้พูด, เลือกภาษาเอง (D21, D22); แก้ Transcript ในแอปอยู่ใน scope แล้วตาม spoil-maker D54
- วิเคราะห์บทหรือเขียนบทสปอยด้วย AI ในแอป — ผู้ใช้ทำที่อื่น (D21)
- ถอดอัตโนมัติหลังโหลด และคิวถอดหลายคลิป (D23, D24)
- คิวหลายลิงก์ (D6)
- playlist และช่องทั้งช่อง (D5)
- ลบ Temp clip อัตโนมัติ (D3)
- คลิป live (D11)
- คลิปที่ต้อง login หรือ cookies — ได้ error `login_required` (D15)
- ยกเลิกระหว่างรวมไฟล์ (D15)
- คลิปที่ต้อง login หรือ cookies ของทุกเว็บ — ผู้ใช้โหลดเองแล้วเอาไฟล์เข้า (D47)
- รายชื่อเว็บที่แอปรับรอง (D47)
- แปลงไฟล์ที่ไม่ใช่ mp4 h264/aac ≤ 1080p (D49)
- เอาไฟล์เข้าหลายไฟล์พร้อมกันหรือเป็นคิว (D52)
- อ้างไฟล์ในเครื่องโดยไม่ copy (D49)

## Open Questions

1. TTS ตัวไหนพูดไทยและใช้เชิงพาณิชย์ได้ เพื่อ supersede ADR-0007 — non-blocking: รอบนี้ไม่ใช้ TTS (D13)
2. เรื่องลิขสิทธิ์และ ToS ของ YouTube ก่อนเผยแพร่คลิปสปอยหารายได้ — non-blocking: ผู้ใช้รับความเสี่ยงไว้แล้วและจะกลับมาดูก่อนเผยแพร่ (D13)
3. legal ข้อ 2 (yt-dlp แก้ challenge ของ YouTube ตาม ม.53/4) เป็น UNVERIFIED — non-blocking: ผู้ใช้รับความเสี่ยงนี้ใน D13

4. ช่วงละ 300 วินาทีตัดคำที่คร่อมรอยต่อได้ทุก 5 นาที — non-blocking: เช็คตอน build seam 3; ตัดจนอ่านไม่รู้เรื่อง → เพิ่ม overlap ระหว่างช่วงเป็น `D{n}` ใหม่
5. `libx264` ใน ffmpeg ของ imageio-ffmpeg บน Windows และการแทน mp4 ขณะ player เปิดอยู่ยังไม่ได้เช็คบนเครื่องจริง — non-blocking: seam 3a ข้อ Windows เพิ่มเข้า `windows-check` 02 ตอน build ticket ของงานตัด (ADR-0016)
6. legal ข้อ 7 (ToS ของ TikTok และเว็บอื่น) เป็น UNVERIFIED — non-blocking: ผู้ใช้รับความเสี่ยงใน D53
7. หน้าเว็บของการเลือกไฟล์ยังไม่มีแบบ (tab คลิป Source `pending`) — non-blocking สำหรับ backend: ticket ของหน้าเว็บรอแบบจาก `/warroom ui spoil`

## Sources

- [ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) — `trim`, `atrim`, `setpts`, `asetpts`, `concat` (accessed 2026-11-05)
- [ffmpeg docs](https://ffmpeg.org/ffmpeg.html) — `-filter_complex`, `-progress`, `-movflags +faststart`, การอ่าน stream จาก `-i` (accessed 2026-11-05)
- [FFmpeg H.264 encoding guide](https://trac.ffmpeg.org/wiki/Encode/H.264) — `libx264` `-preset`, `-b:v` (accessed 2026-11-05)
- [os.replace](https://docs.python.org/3.12/library/os.html#os.replace) — แทนไฟล์แบบ atomic, Windows ล้มเมื่อไฟล์เปิดอยู่ (accessed 2026-11-05)

- [yt-dlp YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) — params `format_sort`, `merge_output_format`, `ffmpeg_location`, `js_runtimes`, `progress_hooks`, `paths`, `noplaylist` (accessed 2026-10-29)
- [yt-dlp README › Sorting Formats](https://github.com/yt-dlp/yt-dlp#sorting-formats) — `res` คือด้านสั้นของภาพ, ความหมายของ `res:1080` (accessed 2026-10-29)
- [yt-dlp EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS) — ต้องมี JavaScript runtime, Deno ≥ 2.3.0, extra `default` (accessed 2026-10-29)
- [deno on PyPI](https://pypi.org/project/deno/) — wheel macOS arm64 และ Windows amd64, `find_deno_bin` (accessed 2026-10-29)
- [Starlette responses](https://www.starlette.io/responses/#fileresponse) — `FileResponse` รองรับ Range (accessed 2026-10-29)
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — `get_ffmpeg_exe()` (accessed 2026-10-29)
- [yt-dlp supportedsites.md](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) — รายชื่อตัวโหลดของแต่ละเว็บ, generic extractor (accessed 2026-11-07)
- [Starlette requests › Body](https://www.starlette.io/requests/#body) — `request.stream()`, `ClientDisconnect` (accessed 2026-11-07)
- [MDN XMLHttpRequest.upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload) — upload progress, `abort()` (accessed 2026-11-07)
