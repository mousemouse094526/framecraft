# 01: หน้า reel กลอง แทนสอนกลอง

**What to build:** ผู้ทำคลิปเปิด "reel กลอง" จากเมนู สร้าง reel ใหม่ กรอก Groove ตั้ง BPM กับจำนวนรอบ แล้วฟังหรือ render เป็น mp4 กับ .srt โดยไม่เห็นท่อนสอนหรือคำว่าบทเรียน. reel ที่ทำไว้ก่อน (หลายท่อน) เปิดได้ บอกว่าบันทึกแล้วจะรวมเป็นท่อนเดียว และเก็บสำเนาไฟล์เดิมไว้ก่อนเขียนทับ.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D3, D4, D5, D8, D10, D11, D12, video-gen D10, video-gen D16, video-gen D22, ui-nav D6, ui-nav D9
- ADR: 0065, 0066
- Screens: รายการ reel กลอง, หน้าแก้ reel กลอง, ผล render reel กลอง
- Seams: 1, 3 (ข้อ reel ใหม่ และสำเนา `lesson.before-reels-only.json`)
- User stories: 1, 2, 4, 5

**Status:** ready-for-agent

## Acceptance criteria

### เมนูและรายการ

- เปิดแอป → หมวดดนตรีมีหัวข้อ "reel กลอง" รายการ "reel ทั้งหมด" ที่ `#/drums`; `#/drums/{id}` และ `#/drums/{id}/renders` เปิดได้และเน้นรายการเดิม
- `#/drums` → หัว "reel กลอง" บรรทัดใต้หัวบอก reel จาก Groove ที่กรอกเอง กับ reel จากเพลงทำในแกะเพลง ปุ่ม "reel ใหม่"; ว่าง → "ยังไม่มี reel กลอง" กับ "สร้าง reel แรก"
- `POST /api/drums/lessons` → reel ใหม่มี `chapters` ท่อนเดียว `repeats` 4 `speed` 100 ป้ายว่าง

### หน้าแก้

- reel ท่อนเดียว → select "จำนวนรอบ" 1–8 แสดงรอบของมัน ไม่มีกลุ่ม "ท่อน n" ป้าย คำอธิบาย ชิ้นที่เน้น ความเร็ว
- เปลี่ยนรอบแล้วบันทึก → `PUT` ส่ง `chapters` ท่อนเดียว `{label: "", text: "", focus: [], repeats: n, speed: 100}`; ความยาวคลิปบนหน้าเปลี่ยนตาม
- reel 3 ท่อน (2, 2, 2) ความเร็ว 80 → จำนวนรอบ 6, Alert ตาม spec › คำบนจอ, บันทึกกดได้, เปลี่ยน hash ถามก่อนออก; ยังไม่กด → ไม่มี `PUT`
- reel ท่อนเดียวที่มีป้าย → Alert ขึ้น
- reel 5 ท่อนรวม 12 รอบ → จำนวนรอบ 8 และ Alert บอก "จาก 12 รอบ"
- reel แบบเก่ากด ฟังจังหวะ หรือ render → `PUT` ท่อนเดียวก่อน request ของงาน
- รวมแล้วเกิน 90 วินาที → บรรทัดความยาวบอกเกิน ฟังจังหวะกับ render กดไม่ได้

### backend

- `PUT` ที่เขียนทับ reel แบบเก่า → มี `lesson.before-reels-only.json` เท่าไฟล์เดิม; `PUT` ครั้งสอง → สำเนาไม่เปลี่ยน; `PUT` ของ reel ท่อนเดียว → ไม่มีสำเนา
- `message` ของ `video_gen` ตาม spec › คำบนจอ; render reel กลองได้ไฟล์เหมือนเดิม (test render เดิมผ่าน)

### คำและ docs

- string บนจอของ `#/drums…` และเมนูไม่มี "บทเรียน" "สอน" "ท่อนสอน"
- ไฟล์ซ้ำที่ไม่มีใคร import ใน video-gen ถูกลบ
