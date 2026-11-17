# Debug: DraftProgress D87 ล้มบางรอบบน feat/ui-nav

**Status:** fixed

**Summary:**
- **Cause:** test ตั้ง fake backend ให้ pick job รันก่อนกด "เลือก Shot ใหม่"; เมื่อบทโหลดหลังจากนั้น หน้าเห็น pick รันอยู่ ปุ่มจึงถูกปิด (D51) และคลิกไม่ส่ง POST
- **Fix:** test รอปุ่มกดได้ก่อนคลิก และ fake backend เริ่มตอบ pick ใน reply ของ POST; แอปไม่เปลี่ยน
- **Prevention:** สถานะ backend ที่การกดทำให้เกิด เปลี่ยนใน reply ของคำขอนั้น ไม่ใช่บรรทัดของ test ก่อนกด

## Symptom

"DraftProgress D87 flaky on feat/ui-nav". `DraftProgress.test.tsx` › "the failure's Alert stays until a new Draft job starts, of any kind (D87)" ล้มราว 1 ใน 5 รอบเมื่อรันทั้งชุด `npm --prefix frontend test` บน branch นี้ (บน develop 0 ใน 5); ผ่านเสมอเมื่อรันเดี่ยว. การกด "เลือก Shot ใหม่" ไม่ส่ง POST บางรอบ (progress.md › Blocked 1).

## Reproduce

**Command:** `npx vitest run src/features/spoil-maker/components/DraftProgress.test.tsx -t "of any kind"` (ใน `frontend/`)

**Rate:** รันเดี่ยว test นี้ตัวเดียว ล้ม 5/5 บน feat/ui-nav และ 3/3 บน develop (`2dff570`); 8 process ขนานกัน 3 รอบ ล้ม 24/24. ทั้งไฟล์รันเดี่ยวผ่าน (test ก่อนหน้า warm module ให้)

**Minimised to:** test D87 ตัวเดียว ไม่ต้องมีภาระ: `AssertionError: expected [] to have a length of 1 but got +0` ที่ `DraftProgress.test.tsx:216`

## Scope

- **Docs say:** Alert ของร่างล้มอยู่จนงาน Draft ใหม่เริ่ม ไม่ว่า kind ไหน (spoil-maker D87); ระหว่าง Draft job `pick` ปุ่มแก้ทุกปุ่มกดไม่ได้ (spoil-maker D51) — `SentenceCard` ปิดปุ่ม "เลือก Shot ใหม่" เมื่อ `locked`
- **Last good:** ไม่มี: ล้มบน develop ด้วยเมื่อรันเดี่ยว. ประวัติ: `369a1fc` (ย้าย `phases.at = 1` + `nextPoll()` มาก่อนคลิก เพราะ `getByRole` ไม่เจอปุ่ม) และ `0da9252` (`waitFor` ตอนท้าย) แก้ไปแล้วสองครั้ง
- **Ruled out:** code ของ ui-nav — develop รันเดี่ยวล้มเหมือนกัน; ui-nav แค่เปลี่ยนจังหวะในชุดเต็ม (เมนูทำให้ render หนักขึ้น)

## Fail path

Alert ของร่างล้มมาจาก hook ที่ตามงานร่าง; บท (การ์ดประโยคพร้อมปุ่ม) มาจาก `useScriptReview.load` ซึ่งอ่าน `draft-jobs/current` ด้วย (path เดียวกับ `CURRENT_PATH`). Alert จึงขึ้นได้ก่อนบท. รอบที่ล้ม: ตอน Alert ขึ้นบทยังไม่มา, test ตั้ง `phases.at = 1` (pick กำลังทำ) แล้ว `nextPoll()`; `load` อ่านงานได้ pick ที่ยังรัน → `job` ไม่ใช่ `null` → `SentenceCard` `locked` → ปุ่ม "เลือก Shot ใหม่" `disabled` → `user.click` ไม่ทำอะไร → ไม่มี POST. Knob: บทโหลดเสร็จก่อนหรือหลัง `phases.at = 1` (test ก่อนหน้าในไฟล์ warm module ให้บทมาเร็ว จึงผ่านเมื่อรันทั้งไฟล์)

## Hypotheses

| # | Hypothesis | Prediction | Disproof | State |
|---|---|---|---|---|
| H1 | test ตั้ง pick job ก่อนกด: บทที่โหลดทีหลังเห็น pick รันอยู่ ปุ่มจึงถูกปิด (D51) | ตั้ง `phases.at = 1` หลังคลิก และรอปุ่ม enabled ก่อนคลิก → ผ่านทุกรอบ | probe เห็นปุ่ม enabled ตอนคลิกในรอบที่ล้ม | confirmed |
| H2 | `user.click` กับ fake timer `shouldAdvanceTime` ทำคลิกหาย | ปุ่ม enabled แต่ยังไม่มี POST | probe เห็นปุ่ม disabled ในรอบที่ล้ม | killed by #5 |
| H3 | code ของ ui-nav (เมนู) เปลี่ยนพฤติกรรมหน้าตรวจแก้ | develop ไม่ล้ม | รันเดี่ยวบน develop | killed by #4 (สำหรับ repro; ในชุดเต็ม ui-nav แค่เปลี่ยนจังหวะ) |
| H4 | route POST ของ fake backend ไม่ match หรือถูกใช้ไปแล้ว | มี POST ใน `fetchMock.mock.calls` แต่ `sent` ไม่เห็น | ดู calls ทั้งหมดตอนคลิก | killed by #5 |
| H5 | (Outsider) repro รันเดี่ยวไม่ใช่ความล้มเดียวกับชุดเต็ม | แก้ตาม H1 แล้ว D87 ในชุดเต็มยังล้ม | ชุดเต็มหลายรอบหลังแก้ | killed by #10 |

## Ledger

| Run | Changed | Result | Rules in / out |
|---|---|---|---|
| 1 | ทั้งไฟล์รันเดี่ยว 1 รอบ (`-t "D87"` match ทั้ง describe) | green 16/16 | ทั้งไฟล์ไม่ล้มเมื่อเครื่องว่าง |
| 2 | เฉพาะ test D87 (`-t "of any kind"`), 8 process ขนาน × 3 รอบ | red 24/24 ที่บรรทัด 216 | repro ได้ |
| 3 | เฉพาะ test D87 เรียงกัน 5 รอบ ไม่มีภาระ | red 5/5 | ไม่ใช่ภาระ: ขึ้นกับว่ามี test ก่อนหน้าหรือไม่ |
| 4 | เฉพาะ test D87 บน develop `2dff570` 3 รอบ | red 3/3 | H3 out |
| 5 | probe `[DBG-d87]`: ปุ่มกับ fetch ตอน Alert และตอนคลิก, รันเดี่ยว | red; ตอน Alert ไม่มีปุ่ม (บทยังไม่มา); ตอนคลิกปุ่ม `disabled: true`; ไม่มี POST ใน calls เลย | H2 out, H4 out, H1 in |
| 6 | probe เดิม, ทั้งไฟล์ | green; ตอน Alert มีปุ่มแล้ว; ตอนคลิก `disabled: false` | H1 in: ผลขึ้นกับว่าบทมาก่อน `phases.at = 1` |
| 7 | ลบ probe; รอปุ่ม enabled ก่อนคลิก, `phases.at = 1` ย้ายมาหลังรอ ก่อนคลิก; รันเดี่ยว 10 รอบ + 8 ขนาน × 3 | green 10/10, 24/24 | H1 in (ทดสอบด้วยการเปลี่ยน ไม่ใช่แค่สังเกต) |
| 8 | ตาม Outsider: สลับ phase ใน reply ของ POST แทนบรรทัดของ test (ปิดช่องที่ poll ตอบ `failed` หลัง 202); รันเดี่ยว 10 รอบ + 8 ขนาน × 3 | green 10/10, 24/24 | ไม่มีช่องเหลือระหว่าง POST กับ pick |
| 9 | ชุดเต็ม `npx vitest run` 1 รอบ | green 655/655 | — |
| 10 | ชุดเต็ม 10 รอบ | D87 green 10/10; 1 รอบล้มที่ test อื่น `spoil/ClipsPage.test.tsx` › "keeps the browser from opening a file dropped beside the box" | H5 out: อาการเดิม (D87 ในชุดเต็ม) หาย; ClipsPage เป็น flake แยก นอก bug นี้ |

## Outsider

จัด H1 อันดับหนึ่ง (code ยืนยัน: `load` เก็บงานที่รันและไม่ใช่ `draft`, `useScriptReview.ts:93`); เสนอ H5 อันดับสอง: repro รันเดี่ยวอาจไม่ใช่ความล้มเดียวกับชุดเต็ม. ไม่มีแถวไหนขัด H1 แต่ #4 กับ #5 ตัด H2–H4 ได้เฉพาะ repro และ H1 ยังไม่เคยทดสอบด้วยการเปลี่ยน. Experiment: รอปุ่ม enabled ก่อนสลับ phase แล้วรันเดี่ยวภายใต้ภาระ และชุดเต็มหลายรอบ (#7, #10). เตือนว่าถ้าสลับ phase หลัง 202 จะมีช่องที่ poll ยังตอบ `failed` ทำให้แอปเห็นงานจบ → ให้สลับใน reply ของ POST (#8)

## Fix

- **Regression test:** test เดิม "the failure's Alert stays until a new Draft job starts, of any kind (D87)" ที่ seam ของหน้า (App + fake backend); รันเดี่ยวคือ repro ที่แดงก่อนแก้ (#3, #4) เขียวหลังแก้ (#7, #8)
- **Change:** test รอปุ่ม "เลือก Shot ใหม่" ขึ้นและกดได้ก่อนคลิก; fake backend เริ่มตอบ pick job ตอนตอบ POST (ไม่ใช่ก่อนผู้ใช้กด) จึงไม่มีลำดับไหนที่บทโหลดทีหลังแล้วเห็น pick ก่อนกด. แอปไม่เปลี่ยน: ปุ่มถูกปิดระหว่าง pick ตรงตาม D51
- **Probes removed:** `[DBG-d87]`; grep ไม่เจอแล้ว

## Postmortem

**Timeline:**
- 2026-11-10 — เห็นครั้งแรกใน toon (Blocked 31), แก้ที่ test ด้วย `369a1fc` (ตั้ง pick ก่อนกด + `nextPoll`) และ `0da9252` (`waitFor`)
- 2026-11-11 ถึง 2026-11-17 — ยังล้มบางรอบใน sound-library และ ui-nav (1 ใน 5 รอบชุดเต็ม)
- 2026-11-17 — repro แน่นอนด้วยการรันเดี่ยว, พบ fail path ด้วย probe, แก้

**Root cause:** ปุ่มไม่ส่ง POST → ปุ่มถูกปิด → หน้าเห็น pick job รันอยู่ก่อนผู้ใช้กด → test ตั้งสถานะ backend ล่วงหน้า (pick รัน) ก่อนการกดที่ทำให้มันเกิด → การแก้ครั้งก่อน (`369a1fc`) อ่านอาการ "ไม่เจอปุ่ม" เป็น "ปุ่มรอ pick job" แทน "บทยังโหลดไม่เสร็จ" จึงย้ายการตั้ง phase ไปก่อนกด → fake backend `phased` ให้ test เลื่อนสถานะได้ตามใจโดยไม่ผูกกับคำขอที่ทำให้มันเปลี่ยน และไม่มีกติกาว่าสถานะที่การกดทำให้เกิดต้องเปลี่ยนใน reply ของคำขอนั้น

**Prevention:**
- สถานะ backend ที่เกิดจากการกดของผู้ใช้ เปลี่ยนใน reply ของคำขอนั้น: ทำแล้วใน test นี้ และเป็นกติกาใน `.claude/skills/vite-react-web/rules/testing.md` — tracked in this commit
- flake แยก `spoil/ClipsPage.test.tsx` › "keeps the browser from opening a file dropped beside the box" (1 ใน 10 รอบชุดเต็ม) — note เท่านั้น ยังไม่ได้ตาม (ไม่ได้เปิด ticket)

**What helped:** รันเดี่ยว test ตัวเดียวทำให้จาก 1 ใน 5 กลายเป็น 5/5 ทันที; probe ตัวเดียวที่พิมพ์ `disabled` ตอนคลิกชี้ fail path. ที่ทำให้ช้า: การแก้สองครั้งก่อนเป็นการเพิ่มการรอ (`nextPoll`, `waitFor`) โดยไม่มี repro ที่แดงทุกรอบ
