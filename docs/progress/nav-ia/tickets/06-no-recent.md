# 06: เมนูไม่มี "ล่าสุด"

**What to build:** เอาหมวด "ล่าสุด" ออกจากเมนูหลักทั้งชุดตาม D22: ลบ `lib/recent.ts` กับ test, `recentLinks` `menuSections` ใน `lib/nav`, การอ่านล่าสุดใน `PageLayout`, และทุกที่ที่เรียก `useRecentPage` / `forgetRecent`; เมนูเป็น `NAV_SECTIONS` ตายตัว. กุญแจเก่าใน `localStorage` ปล่อยไว้ (D23). แก้ comment ที่ผิดชัดสองที่ที่การสำรวจ route เจอ (`CastPage` hash, `useHash` "tabs and steps").

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D22, D23
- ADR: 0075
- Seams: 4
- User stories: 9

**Status:** done

## Acceptance criteria

- เมนูมีหมวด เล่าเรื่อง · ดนตรี · คลัง · ตั้งค่า เท่านั้น ทุกหน้า แม้ `localStorage["framecraft.nav.recent"]` มีของเก่าทั้งสามแหล่ง
- `#/covers/{id}` `#/drums/{id}` `#/toon/series/{id}` `#/toon/eps/{id}` → ลิงก์ของหัวข้อเปิดลิงก์เดียว `<h1>` เป็นชื่อหัวข้อ; หน้าโหลดเสร็จแล้วไม่มีอะไรเขียนลงกุญแจ
- ลบเพลง reel กลอง ชุด EP ยังทำงานเหมือนเดิม (ไม่มี `forgetRecent`)
- ไม่มี `recent` ใน `frontend/src` นอกจาก test ที่ยืนยันว่าไม่มี; ไม่มี import หรือ export ที่ไม่มีใครใช้ (typecheck ผ่านด้วย `noUnusedLocals`)
- route, hash, `MOVED`, เมนู 2 ชั้น, หัวหน้า, ปุ่มฟังของ audio-player ไม่เปลี่ยน: test เดิมของมันผ่านโดยไม่แก้
- ภาพแคปเมนูก่อน (1280px) และหลัง (1280px, 375px drawer เปิด) แนบใน `progress.md`
- checks ทั้งสี่ผ่าน
