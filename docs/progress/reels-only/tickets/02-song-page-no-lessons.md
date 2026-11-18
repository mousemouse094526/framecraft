# 02: หน้าเพลงไม่มีบทเรียน และลบโค้ดสร้างบทเรียนจากเพลง

**What to build:** ผู้ทำคลิปเปิดเพลงที่แกะแล้วเห็นช่วงแกะกับการ์ด Reel cover ต่อกันเลย ไม่มีส่วนสร้างบทเรียน บทเรียนจากเพลงนี้ หรือผลแกะ; รายการเพลงไม่นับบทเรียน. route และโค้ดที่มีไว้สร้างบทเรียนจากเพลงหายไป และ `song.json` เก่ายังเปิดได้.

**Blocked by:** 01: หน้า reel กลอง แทนสอนกลอง

**Covers:**
- Decisions: D1, D6, D7, D8, D9, D11, drum-notes D5, drum-notes D18, drum-cover D9, drum-cover D11, drum-cover D19
- ADR: 0065
- Screens: หน้าเพลง, รายการเพลง
- Seams: 2, 3 (ข้อ route ที่ลบ และ `song.json` ที่มี `lessons`)
- User stories: 3, 4, 5

**Status:** ready-for-agent

## Acceptance criteria

- เพลงที่แกะแล้ว → มีหัวเพลง เครื่องเล่น ช่วงแกะ โหมด แกะโน้ต การ์ด Reel cover; ไม่มี section "สร้างบทเรียน" "บทเรียนจากเพลงนี้" "ผลแกะ"
- เพลงที่แกะแล้วแต่ไม่มีห้อง 4/4 → การ์ด Reel cover ขึ้น ไม่มีข้อความ "ไม่มีห้อง 4/4"
- ไม่พบการตี หรือห้องแรกว่าง → คำเตือนและ "เริ่มช่วงที่การตีแรก" เหมือนเดิม
- ยังไม่แกะ → "ตั้งช่วงแล้วกด แกะโน้ต"
- รายการเพลง → แถวไม่มี "บทเรียน"; dialog ลบเหลือ "เสียงเพลงและผลแกะหายไป"
- `MELODY_HINT` บอกสิ่งที่ reel ได้จากโหมดทำนองจริง ไม่พูดถึง groove ของบทเรียน
- `POST /api/songs/{id}/preview`, `/listen`, `/lessons` → 404 หรือ 405
- `song.json` ที่มี `lessons: ["x"]` → `GET /api/songs` และ `GET /api/songs/{id}` 200 ไม่มี `lessons`; `PUT …/range` 200 และไฟล์ที่เขียนไม่มี `lessons`; `DELETE` 204
- `drum_notes.lesson`, `from_song`, `create_from`, hook `useLessonPreview` `useLessonTitles` และส่วน lesson ของ `lib/songs` ไม่มีแล้ว; reel cover กับ reel คาลิมบา render ได้เหมือนเดิม (test เดิมผ่าน)
- grep string บนจอทั้งแอป (`frontend/src` ไม่นับ comment และ test, `message` ของ backend) → ไม่มี "บทเรียน" หรือ "สอน"
