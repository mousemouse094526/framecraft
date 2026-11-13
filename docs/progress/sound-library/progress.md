# Progress: sound-library

**Now:** 01 สร้างครบตามแบบเดิม เหลือข้อ "หน้าตาตรงแบบ" ที่รอ design (Blocked #2); ต่อ 02 ด้วยกติกาเดียวกัน

**Next:**

```
/warroom-build sound-library 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | คลังเสียงกลางที่ tab คลังเสียง | in-progress |
| 02 | แถบนำทางแบบกลุ่มและเมนูจอแคบ | ready |
| 03 | เสียงพื้นในคลิปสปอย | ready |

## Log

### Ticket 01: คลังเสียงกลางที่ tab คลังเสียง — in-progress (เหลือ design) 2026-11-13

**Built:**
- `backend/sounds.py` (ใหม่): ทั้ง `toon.sounds` และส่วนเสียงของ `toon.store` ย้ายมา; `lock` ของตัวเอง; `sound_users` (`SoundUser(tab, lock, check)`, ลบถือ lock ตาม `LOCK_ORDER` แล้ว `sounds.lock`); `exists`, `path`; `move_legacy` ตอน start (ทั้ง folder หรือรวมทีละไฟล์); `legacy`; ค่าเสียง aac ที่ `toon.compose` อ่าน
- `backend/routes/sounds.py`: `/api/sounds…` ทุกเส้นและ `/api/sounds/legacy`; `/api/toon/sounds…` ลบ (`404`); `paths.sounds_dir`, `sounds_file`, `sounds_partial_dir`, `legacy_sounds_dir`; upload, ลิงก์ และไฟล์แปลงอยู่ใน `media/sounds/.partial/` ที่ start ล้างทั้ง folder
- toon: `episodes.eps_playing` ลงทะเบียนเป็นผู้ใช้เสียง (label `{Series} · EP {n} {ชื่อตอน}` เรียงตาม Series แล้วเลข EP); `PATCH` ช่วงและขั้นเขียนผลของ Cards job เช็ค `sounds.exists` ใต้ `store.lock`; render อ่าน `sounds.path`; `in_use` เป็น `users` ข้อความ "ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้"
- `backend/ids.py` (`new_id`), `errors.checked_text` (ย้ายจาก toon)
- frontend: tab "คลังเสียง" ต่อจากคลังความรู้; `useHash` แทน `#/toon/sounds` ด้วย `#/sounds` ทั้งตอนโหลดและ `hashchange`; `features/sound-library/` (หน้า, `useSounds`, `lib/sounds`) ไม่ import toon; ปุ่ม info กับกล่องสามข้อ; Alert ของเสียงเดิมที่ย้ายไม่ครบ; "← กลับ" จาก `back`; `in_use` บรรทัดละ user; คลังว่าง "ยังไม่มีเสียงในคลัง"; `CommitField`, `NoticeLine` (`lines`), `lib/edit`, `lib/notice`, `lib/upload`, `lib/useReadyState` และ icon ที่ใช้ร่วมย้ายออกจาก toon; ปุ่ม "คลังเสียง" ของรายการ Series และ toolbar เส้นเรื่องเปิด `#/sounds?back=…`; ข้อความยืนยันลบ Series
- README ส่วนคลังเสียง (path, การย้าย, ย้อนไปรุ่นก่อน); conventions ทั้งสองฝั่ง; ADR-0037 แก้คำ (คลังไม่ import feature ที่ใช้มัน, ใช้ตัวโหลดลิงก์ของ tab คลิปได้); library note `os.replace`

**Decided:**
- D14 — การย้ายไม่ลบไฟล์ที่ไม่รู้จัก, เขียน `sounds.json` ต่อไฟล์, m4a ที่ชื่อไม่ใช่ id ไม่นับ `left_behind`; `backend.sounds` ใช้ adapter ของ spoil ได้ (auto mode เลือกแก้คำ ADR-0037); `LOCK_ORDER` แทนเลข rank
- D15 — ข้อความบนหน้าที่เคยพูดถึงการ์ตูนเล่าอย่างเดียว, `back` รับ `#/toon`, `in_use` ใน `NoticeLine`, ที่อยู่ของ icon
- auto mode: design ของหน้าคลังเสียงยัง pending → สร้างตามแบบเดิม (Figma คลังเสียงพื้น) ข้อ "หน้าตาตรงแบบ" ค้างกับ Blocked #2; ticket ยัง in-progress

**For the next ticket:**
- ticket 03 ลงทะเบียน `SoundUser(tab="spoil", lock=gpu.slot.draft_lock, …)`: `LOCK_ORDER` มี spoil ก่อน toon อยู่แล้ว
- ticket 02 ทำ `TABS` เป็นกลุ่ม: `tabOf("#/sounds?…")` เป็น `sounds` แล้ว
- เมื่อได้แบบใน Figma ของหน้าคลังเสียง: ตรวจหัวข้อ "เพิ่มเสียงพื้น" และ "เสียงพื้น N เสียง" ที่ยังเป็นคำเดิม

**Checks:** `uv run pytest` 1139 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 455 passed (หนึ่งรอบ `DraftProgress.test.tsx` › D87 ล้มครั้งเดียวตอนรันทั้งชุด ผ่าน 3/3 เมื่อรันแยก และสองรอบเต็มถัดมาผ่าน: ไม่ได้แตะ spoil-maker); `npm --prefix frontend run build` ผ่าน. Review สามแกนจาก `04aeca1`: Standards 3 ข้อผิดกติกา (ลำดับ lock ใน SKILL.md, ตัวสร้าง id ซ้ำ, test หา box ด้วย id) + smell 10, Spec 0 ขาด (เหลือข้อ design ที่รู้อยู่) + ADR-0037 ขัดกับ import ของ spoil + 2 กรณีขอบของการรวม + test นอก seam, Newcomer สรุปตรง What to build + เดา 12 จุด (หนักสุด m4a ชื่อไม่ใช่ id ทำให้ folder เดิมค้างพร้อม Alert ตลอด); แก้ทุกข้อแล้ว ยกเว้นชื่อ route `/imports` กับ `/import/current` (ตาม spec), ชื่อหัวข้อ "เสียงพื้น" (รอ design) และ test เดิมที่ใช้ `_params` (ยกมาจาก toon)

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 02 | design: แถบนำทาง | `/warroom sound-library` พร้อมลิงก์ design จาก `ui-prompt.md` | open |
| 2 | 01 | design: หน้าคลังเสียง | `/warroom sound-library` พร้อมลิงก์ design จาก `ui-prompt.md` | open |
| 3 | 03 | design: เสียงพื้นในหน้าตรวจแก้ของสปอย | `/warroom sound-library` พร้อมลิงก์ design จาก `ui-prompt.md` | open |
| 4 | 03 | design: ผล render ของสปอย | `/warroom sound-library` พร้อมลิงก์ design จาก `ui-prompt.md` | open |
