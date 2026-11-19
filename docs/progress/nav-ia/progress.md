# Progress: nav-ia

**Now:** ready to merge — ทุก ticket done (01–05), feature review หลัง 05 ผ่าน

**Next:**

```
/pr-open
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เมนูและที่อยู่ใหม่ พร้อม redirect | done |
| 02 | สปอยเป็นพื้นที่ทำงานเดียว | done |
| 03 | เพลงกับ reel cover และ reel กลองกับผล render เป็นหน้าเดียว | done |
| 04 | EP การ์ตูนเล่าเป็นหน้าเดียว | done |
| 05 | เมนู 2 ชั้น | done |

## Log

### feature review (หลัง 05) — done 2026-11-19

**Built:**
- `lib/nav`: เลิก export `NAV_SECTIONS` `SETUP_ITEM` `activeItem` ที่ไม่มีใครใช้นอกไฟล์; `NavItem.tab` อธิบายใหม่
- `App.test`: ตารางหัวหน้าและลิงก์ที่เปิดเหลือคอลัมน์เดียว (ชื่อลิงก์ = หัวหน้าเสมอ); test D20 รอด้วย `waitFor` หลัง `rememberRecent`; บอกว่าทำไม "สร้าง Series" มีสองลิงก์
- docs: spec › Modules touched ตรงกับ D21 (ไม่มี `NavTopic`); ADR 0070 มี Status; legal D16–D20; D21 `detail`; ticket 05 Covers D21

**Decided:**
- ไม่มี D ใหม่; ไม่แก้: `detail` ชื่อเดิม (D21), key `framecraft.nav.recent` ใน test ตามแบบเดิมของ test อื่น, `RECENT_SOURCES` เป็นรายการเพราะลำดับคือ D18

**For the next ticket:**
- Nothing

**Checks:** typecheck · `npm test` 686 passed · build · `uv run pytest` 1547 passed — all green

### 05: เมนู 2 ชั้น — done 2026-11-19

**Built:**
- เมนู: หมวด → ลิงก์ ไม่มีหัวกลุ่มซ้อน; ทำสปอย · คลิปทั้งหมด · การ์ตูนเล่า · reel cover · reel กลอง · คลังความรู้ · คลังเสียง · เสียงพากย์ · ติดตั้ง; ไม่มี สร้างชุดใหม่ ชุดทั้งหมด เพลงทั้งหมด reel ทั้งหมด
- หมวด "ล่าสุด" ระหว่างดนตรีกับคลัง เรียง การ์ตูนเล่า → reel cover → reel กลอง บรรทัดรองบอกแหล่ง; ไม่มีของล่าสุด = ไม่มีหมวด
- `<h1>` = ชื่อลิงก์ที่เปิด; หน้าลึกกว่าของการ์ตูนเล่า reel cover reel กลอง = ชื่อลิงก์แหล่ง ไม่เปลี่ยนเมื่อหน้าเพิ่มตัวเองเข้าล่าสุด; `#/toon?x` → ติดตั้งเปิด
- ภาพแคปจากของจริง (ล่าสุดเต็มสามแหล่ง, `#/covers`): [375px drawer เปิด](screens/05-menu-375.png) · [1280px](screens/05-menu-1280.png)

**Decided:**
- D21 — `NavItem.tab` แทน `NavTopic`; `recentLinks` / `menuSections` ใน `lib/nav`
- review: หัวหน้าอ่านจากลิงก์ของเมนูที่เปิด (ไม่ใช่ `tabLabel`); `uses` → `detail`; test เมนูหาด้วย role/ชื่อ ไม่เดิน DOM; test `#/toon/new` ใช้ `testBackend`; SKILL.md อธิบาย `nav.ts` ใหม่

**For the next ticket:**
- Nothing

**Checks:** typecheck · `npm test` 686 passed · build · `uv run pytest` 1547 passed — all green

### feature review — done 2026-11-19

**Built:**
- เพลง MIDI: ส่วน reel ไม่มีปุ่ม "แกะช่วงใหม่ด้านบน" (ไม่มีช่วงแกะให้กลับไป)
- เพลงที่ถูกลบระหว่างเปิดหน้า: ส่วน reel บอก "ไม่พบเพลงนี้" ไม่ใช่ให้แกะโน้ต

**Decided:**
- ไม่มี D ใหม่

**For the next ticket:**
- Nothing

**Checks:** typecheck · `npm test` 675 passed · build — green; `uv run pytest` 1547 passed ก่อนหน้า (backend ไม่แตะ)

### 04: EP การ์ตูนเล่าเป็นหน้าเดียว — done 2026-11-19

**Built:**
- หน้า EP `#/toon/eps/{id}` สลับ พล็อต · เส้นเรื่อง · render ในหน้า hash ไม่เปลี่ยน; เปิดที่พล็อตเมื่อยังไม่มีการ์ด เส้นเรื่องเมื่อมีแล้ว; แตกการ์ดเสร็จขณะดูพล็อต → เส้นเรื่อง
- `#/toon/eps/{id}/plot` และ `/render` เก่าพามาหน้า EP

**Decided:**
- D15 — ปุ่มสลับ view คือปุ่มเดิม ("ไปหน้า render" เป็น "ไปที่ render") ไม่ใช่ `SegmentedChoice`

**For the next ticket:**
- Nothing

**Checks:** typecheck · `npm test` 673 passed · build — green

### 03: เพลงกับ reel cover และ reel กลองกับผล render เป็นหน้าเดียว — done 2026-11-19

**Built:**
- หน้าเพลง `#/covers/{id}`: ช่วงแกะ → ผลแกะ → ส่วน Reel cover (บรรทัดสรุปเดิมของการ์ด, ฟอร์ม reel, ฟัง, render, ผล render) ในหน้าเดียว; ปุ่ม "ไปที่ reel" ในแถวหัว; แกะใหม่ขณะ reel ยังไม่บันทึกถาม "ออกโดยไม่บันทึก?"
- หน้า reel กลอง `#/drums/{id}`: ผล render ใต้ฟอร์ม, render ที่เริ่มที่นี่เสร็จ → อ่านผลใหม่ เล่นอันใหม่ เลื่อนไปที่ผล; ปุ่ม "ไปที่ผล render"
- `#/songs/{id}/cover`, `#/covers/{id}/cover`, `#/drums/{id}/renders` เก่าพามาหน้าเดียวของมัน

**Decided:**
- `ReelSection` (drum-cover) รับ `song` จากหน้าเพลง ไม่อ่านเพลงเอง: `App` ใส่ผ่านช่อง `reel` keyed ด้วย `picked_at` (D14)
- ช่องช่วงของ reel ชื่อ "เริ่ม reel (วินาที)" / "จบ reel (วินาที)" เพราะอยู่หน้าเดียวกับ "เริ่ม (วินาที)" ของช่วงแกะ
- `mayLeave()` ใน `useHash` ถาม leave guard เดียวกันเมื่อหน้าจะทิ้งงานโดยไม่เปลี่ยน hash; `scrollIntoView` stub ใน `test-setup`

**For the next ticket:**
- หน้า EP: ทำแบบเดียวกัน — job hook ตัวเดียวต่อหน้า, view เป็น state, ใช้ `MOVED` ที่รับ `{id}`

**Checks:** typecheck · `npm test` 668 passed · build — green (backend ไม่แตะ)

### 02: สปอยเป็นพื้นที่ทำงานเดียว — done 2026-11-19

**Built:**
- `#/spoil` (เมนู "ทำสปอย") เปิดที่ตรวจแก้บทเมื่อมีบทหรือกำลังร่าง ไม่มีบทเปิดเลือกคลิป; แถบขั้นเป็นปุ่มในหน้า hash ไม่เปลี่ยน
- ร่างบทเริ่ม → ตรวจแก้บท, ยกเลิกร่าง → เลือกคลิป, render เสร็จ (จากตรวจแก้บท) → ผล render; ปุ่ม "ไปที่ตรวจแก้บท" / "ไปที่ตั้งค่าคลิปสปอย" / "กลับไปแก้ตั้งค่า" เปลี่ยนขั้น
- `#/spoil/review`, `#/spoil/renders` เก่าพามา `#/spoil`; เมนูไม่มีเลขขั้นอีก

**Decided:**
- ไม่มี D ใหม่; ขั้นตั้งต้นเลือกครั้งเดียวหลังอ่านสถานะครั้งแรก (D14) ผ่าน `StepGoContext`/`useGoToStep` ใน `useStepStatus`

**For the next ticket:**
- test ของขั้นเปิดขั้นด้วยการกดปุ่มขั้นก่อนโหลดเสร็จ (`openOn`, `open("ผล render")`); route ที่ phased ต้องนับว่าทั้งแถบขั้นและขั้นที่เปิดอ่าน job

**Checks:** typecheck · `npm test` 664 passed · build — green (backend ไม่แตะ)

### 01: เมนูและที่อยู่ใหม่ พร้อม redirect — done 2026-11-19

**Built:**
- เมนู: สปอยมีคลิปทั้งหมด (`#/spoil/clips`), หมวดดนตรีมี reel cover (`#/covers`), คลังเหลือ คลังความรู้ · คลังเสียง · เสียงพากย์ (`#/voices`)
- hash เก่า `#/clips`, `#/spoil/voices`, `#/songs…` พาไปหน้าใหม่ (`MOVED` แบบ pattern, `movedTo`); ล่าสุดกุญแจ `songs` อ่านเป็น `covers`
- ป้ายบนจอที่ชี้ "tab สปอย" หรือ "แกะเพลง" เปลี่ยนตาม (ฟอร์มชุด, รายการ reel กลอง, หัวรายการเพลง)

**Decided:**
- ไม่มี D ใหม่; หน้า reel ยังอยู่ที่ `#/covers/{id}/cover` ชั่วคราวจนกว่า 03 รวมหน้า

**For the next ticket:**
- ขั้นของสปอยยังเป็นรายการเมนูที่มี `step` จนกว่า 02 จะเอาออก; `REVIEW_HASH`/`RENDERS_HASH` ยังใช้อยู่
- `CLIPS_HASH` อยู่ใน `lib/clips`; `backOf` ของคลังเสียงรับ `#/spoil` แล้ว

**Checks:** typecheck · `npm test` 661 passed · build · `uv run pytest` 1547 passed — all green

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
