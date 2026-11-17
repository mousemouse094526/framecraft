# Progress: ui-nav

**Now:** 01 done; 02 next

**Next:**

```
/warroom-build ui-nav 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เมนูหลัก 5 หัวข้อ พร้อมขั้นและคลัง | done |
| 02 | ล่าสุดในเมนู | ready |

## Log

### 01: เมนูหลัก 5 หัวข้อ พร้อมขั้นและคลัง — done 2026-11-17

**Built:**
- ทุกหน้ามีปุ่ม ☰ wordmark และตำแหน่ง "{หัวข้อ} / {รายการ}"; เมนูหลักมี ติดตั้ง, สปอย (3 ขั้น), การ์ตูนเล่า, สอนกลอง, แกะเพลง และส่วนคลัง 4 รายการพร้อม "ใช้กับ …"
- จอ ≥1280px เมนูเป็น sidebar ตรึงซ้าย ยุบได้และจำค่า; จอแคบเป็น drawer มีพื้นมืด โฟกัสไปรายการที่เปิดอยู่ หน้าข้างหลัง `inert`
- hash เดิมทุกตัวพาไปหน้าเดิม; leave guard กับปุ่ม back ทำงานเหมือนเดิม

**Decided:**
- ไม่มี D ใหม่: ทุกอย่างตาม D1–D11

**For the next ticket:**
- `locationOf(hash, tab, extra)` ใน `lib/nav.ts` รับรายการเพิ่มต่อหัวข้อ (`extra`) — ล่าสุดส่งเข้าทางนี้ แล้ว `MainMenu` ใน `PageLayout` แสดงใต้หัวข้อ
- `aria-current="true"` อยู่ที่ `role="group"` ของหัวข้อที่เปิด; ชื่อรายการไม่รวมเลขขั้นและบรรทัด "ใช้กับ" (`aria-hidden` + `aria-describedby`)
- `stubMatchMedia` ใน `src/testing/fakeMatchMedia.ts` สำหรับจอกว้าง
- test ที่แก้ตาม D8: `App.test.tsx` (ส่วน tab bar/groups/menu → main menu, drawer, sidebar), `SoundsPage.test.tsx` และ `StoryEditor.test.tsx` (หา "เมนูหลัก"), และ test ที่กดหัวข้อเดิมเป็นลิงก์: `SongsPage` ("เพลงทั้งหมด"), `DrumsPage` ("บทเรียนทั้งหมด"), `ToonPage` ("ชุดทั้งหมด"), `SavedVoicePage` ("เสียงที่บันทึก" + กลุ่มสปอย)
- ตรวจมือ: 1440px (sidebar, สปอย / ตรวจแก้บท), 1280px (คลังคลิป ไม่บีบ), 375px (drawer ปิด/เปิด มีพื้นมืด)

**Checks:** `uv run pytest` 1555 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 641 passed; `npm --prefix frontend run build` ผ่าน

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
