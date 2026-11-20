# 18: EP ที่แก้ล่าสุดบนหน้า `#/toon`, ไม่มีปุ่มคลังเสียงซ้ำเมนู, "ไปที่การ์ด n" ที่ไปถึงการ์ด

**What to build:** หน้า `#/toon` มีส่วน "EP ที่แก้ล่าสุด" เหนือรายการชุด — ลิงก์เดียวไป EP ที่ `ep.json` เขียนใหม่สุดของทุกชุด (จาก `latest_ep` ของ `GET /api/toon/series`) และไม่มีปุ่ม "คลังเสียง" ที่ซ้ำเมนูแล้ว. ใน render ของ EP ปุ่ม "ไปที่การ์ด n" สลับไปเส้นเรื่อง เลื่อนไปที่การ์ด n และย้ายโฟกัสไปที่การ์ดนั้น. มาจาก nav-ia Open Questions 1–5 (ข้อ 3, 5 คงเดิม D90).

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D87, D88, D89, D90
- Blocked: —

**Status:** done

## Acceptance criteria

- `GET /api/toon/series`: ชุดที่ไม่มี EP → `latest_ep: null`; ชุดที่มีสอง EP → `latest_ep` เป็น EP ที่ mtime ของ `ep.json` ใหม่กว่า พร้อม `id`, `n`, `title`, `edited_at` (ISO มี timezone); แก้ EP (PATCH) แล้ว `latest_ep` เปลี่ยนเป็น EP นั้น
- `#/toon` มี EP ในชุดใดก็ได้ → ส่วน "EP ที่แก้ล่าสุด" เหนือรายการชุด ลิงก์ `#/toon/eps/{id}` ของ EP ที่ `edited_at` ใหม่สุดข้ามชุด บอกชื่อชุดและ `EP n` ชื่อตอน
- ไม่มี EP เลย (หรือไม่มีชุด) → ไม่มีส่วนนี้และไม่มีหัวข้อว่าง
- `#/toon` ไม่มีลิงก์ "คลังเสียง" นอกเมนู; เส้นเรื่องของ EP ยังมี `#/sounds?back=#/toon/eps/{id}`
- render ของ EP ที่การ์ด 2 ไม่มีภาพ: กด "ไปที่การ์ด 2" → เห็นเส้นเรื่อง, `scrollIntoView` ถูกเรียกบน `article` "การ์ด 2" และ `article` นั้นถูกโฟกัส; hash ไม่เปลี่ยน
- กด "แก้พล็อต" แล้ว "ไปเส้นเรื่อง" หลังจากนั้นไม่เลื่อนไปการ์ดเดิมอีก
- ไม่แตะเมนู, hash, `lib/nav.ts`, ปุ่ม play/pause; ไม่มี `localStorage`
- `uv run pytest`, typecheck, `npm test`, build เขียว; จำนวน test ไม่ลด

## Notes

- `store.write_ep` ใช้ `files.write_atomic` (เขียนไฟล์ใหม่แล้ว rename) mtime จึงเป็นเวลาที่เขียนเสมอ
- `test-setup.ts` มี `Element.prototype.scrollIntoView ??= () => {}` อยู่แล้ว
