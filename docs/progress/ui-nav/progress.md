# Progress: ui-nav

**Now:** merged — change request ([PR #20](https://github.com/mousemouse094526/framecraft/pull/20), `6040d74`); 01–02 ([PR #19](https://github.com/mousemouse094526/framecraft/pull/19), `50b04c4`)

**Next:**

```
/warroom next
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เมนูหลัก 5 หัวข้อ พร้อมขั้นและคลัง | done |
| 02 | ล่าสุดในเมนู | done |
| 03 | เมนูเป็น 4 หมวด เฉพาะทางที่ได้ reel | done |

## Log

### 03: เมนูเป็น 4 หมวด เฉพาะทางที่ได้ reel — done 2026-11-17

**Built:**
- เมนูหลักแบ่ง 4 หมวดที่มีหัว: เล่าเรื่อง (สปอย, การ์ตูนเล่า) · ดนตรี (แกะเพลง, สอนกลอง) · คลัง · ตั้งค่า (ติดตั้ง)
- ตรวจทุกรายการกับกฎ reel (D13): ไม่มีรายการที่ถูกเอาออก; สอนกลองไม่แน่ใจจึงคงไว้ (Blocked 2); ส่วนบทเรียนในหน้าเพลงอยู่นอกเมนู (Blocked 3)
- hash ข้อความตำแหน่ง ล่าสุด ปุ่ม ☰ และ leave guard เหมือนเดิม

**Decided:**
- D12, D13 (change request) และ ADR-0064; Breaker 10 ข้อ (0 blocker) แก้ในเอกสารทั้งหมด: หมวดไม่ current, ตาราง Hash ของติดตั้ง "—", ชื่อหมวดห้ามซ้ำหัวข้อ, ถอยกลับ, ผลของการเอาสอนกลองออก

**For the next ticket:**
- `NAV_SECTIONS` ใน `lib/nav.ts` เป็นที่เดียวของเมนู; `NAV_TOPICS` ได้จากมัน
- test แยกหมวดจากหัวข้อด้วยตำแหน่ง (ลูกตรงของ `<nav>`)
- ตรวจมือ 1440px (`#/spoil/review`) และ 375px drawer (`#/songs`) ด้วย dev server พอร์ต 5174

**Checks:** `uv run pytest` 1555 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 656 passed; `npm --prefix frontend run build` ผ่าน

### Feature review — 2026-11-17

**Fixed (reviewer 1 สีแดง 5 สีเหลือง ทั้งหมด):**
- action ในหัวหน้าเป็น `inert` ขณะ drawer เปิด เหลือแค่ปุ่ม ☰ (D10)
- คืนโฟกัสหลังเลือก: หน้าที่วาด hash ใหม่รับโฟกัสจาก flag แทนการเดาเวลา; ทางสำรองเมื่อ leave guard ไม่ยอม
- back/forward ขณะ drawer เปิด → drawer ปิด หน้าไม่ค้าง `inert`
- ชื่อล่าสุดตัดที่ 80 ตัวอักษรจริง ไม่ผ่า emoji
- test "เลือกรายการเดิม" เข้า branch hash เดิมจริง; test หน้า reel ตรวจว่า storage ไม่ถูกเขียน
- test guard รอ `hashchange` ที่ค้างจาก test ก่อนหน้า

**Checks:** `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend run build` ผ่าน; `npm --prefix frontend test` 655 tests: ผ่านครบ 4 ใน 5 รอบ (ปิด dev server ระหว่างวัด); อีกรอบ D87 ล้ม — ดู Blocked 1


### 02: ล่าสุดในเมนู — done 2026-11-17

**Built:**
- ชุดหรือ EP บทเรียนกลอง และเพลงที่เปิดล่าสุดขึ้นใต้หัวข้อของมันในเมนู ไม่เกิน 3 รายการ กดแล้วถึงทันที; หน้าย่อย (`/cast`, `/renders`, `/cover`, …) เน้นชิ้นแม่
- ลบชุด (พร้อม EP ของมัน) EP บทเรียน หรือเพลง แล้วหายจากล่าสุด; บทเรียนหรือเพลงที่ได้ `not_found` ก็หาย
- storage เสียหรือถูกแก้มือ = ไม่มีล่าสุด หน้าเปิดปกติ; แท็บอื่นเปลี่ยนแล้วเมนูตาม

**Decided:**
- ไม่มี D ใหม่: ตาม D5, D10, D11

**For the next ticket:**
- `useRecentPage(area, hash, page)` ใน `lib/recent.ts` คือทางเดียวที่หน้าเขียนล่าสุด; หน้าใหม่ของชิ้นเดียวเรียกมันตัวเดียว
- test ลบ EP และลบบทเรียนผ่านหน้าไม่ได้เขียนแยก: ทางเดียวกับลบเพลง (มี test) และ `forgetRecent` มี unit test ของ cascade
- `DraftProgress.test.tsx` › D87 ล้มบางรอบเมื่อรันทั้งชุด (2 ใน 7 รอบ) ผ่านทุกรอบเมื่อรันเดี่ยว: test ใช้ `shouldAdvanceTime` และคอมเมนต์ในตัวบอกว่าลำดับ poll ไม่แน่นอน (`0da9252` แก้ไปครั้งหนึ่งแล้ว) — ไม่ได้แตะในงานนี้

**Checks:** `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 653 tests (652 passed + D87 flake ข้างบน; รอบอื่นผ่านครบ); `npm --prefix frontend run build` ผ่าน; `uv run pytest` 1555 passed (ticket 01, backend ไม่เปลี่ยน)

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
| 1 | 02 | `DraftProgress.test.tsx` › D87 (spoil-maker) ล้มราว 1 ใน 5 รอบเมื่อรันทั้งชุดบน branch นี้ (บน develop 0 ใน 5); ผ่านเสมอเมื่อรันเดี่ยว. การกด "เลือก Shot ใหม่" ไม่ส่ง POST บางรอบ. ลองสลับลำดับ phase และ poll วนแล้ว ทั้งสองแบบแย่ลง จึงถอยคืน; ยังไม่รู้สาเหตุ | `/kiki-debug DraftProgress D87 flaky on feat/ui-nav` | done (`2aef071`, [record](bugs/2026-11-17-draftprogress-d87-flaky.md)) |
| 2 | 03 | สอนกลอง (`#/drums`) ได้ mp4 แนวตั้งแต่เป็นบทเรียน: นับเป็น reel (เก็บ) หรือบทเรียน (เอาออกจากเมนู)? — spec › Open Questions 4 | เจ้าของตัดสิน แล้ว `/warroom ui-nav` | open |
| 3 | 03 | ส่วน "สร้างบทเรียน" / "บทเรียนจากเพลงนี้" ในหน้าเพลงเป็นบทเรียนที่ไม่ได้คลิป: ซ่อนหรือลบไหม? อยู่นอกเมนู — spec › Open Questions 5 | เจ้าของตัดสิน แล้ว `/warroom drum-notes` | open |
