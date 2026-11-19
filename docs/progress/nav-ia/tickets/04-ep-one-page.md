# 04: EP การ์ตูนเล่าเป็นหน้าเดียว

**What to build:** หน้า EP `#/toon/eps/{id}` สลับ พล็อต · เส้นเรื่อง · render ในหน้าโดยไม่เปลี่ยนที่อยู่; เปิดที่พล็อตเมื่อยังไม่มีการ์ด เส้นเรื่องเมื่อมีแล้ว. `/plot` และ `/render` เก่าพามาที่หน้า EP.

**Blocked by:** 01: เมนูและที่อยู่ใหม่ พร้อม redirect

**Covers:**
- Decisions: D8, D9 (plot, render), D14 (job hook ตัวเดียว, แตกการ์ดเสร็จพาไปเส้นเรื่องเฉพาะจากพล็อต)
- ADR: 0069
- Seams: 3 (EP)
- User stories: 6

**Status:** ready-for-agent

## Acceptance criteria

- EP ที่ยังเป็นพล็อต → พล็อตเปิด ไม่มี render
- EP ที่มีการ์ด → เส้นเรื่องเปิด; สลับพล็อต เส้นเรื่อง render ได้ hash ยังเป็น `#/toon/eps/{id}`
- แตกการ์ดเสร็จขณะพล็อตเปิด → เส้นเรื่องเปิด
- view render ทำได้ครบเหมือนหน้า render เดิม (เริ่ม หยุด ลบ โหลด)
- `#/toon/eps/{id}/plot`, `#/toon/eps/{id}/render` → `#/toon/eps/{id}`
