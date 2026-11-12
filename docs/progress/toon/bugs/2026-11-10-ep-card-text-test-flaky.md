# Debug: test แก้ข้อความการ์ดของ EpPage ล้มเป็นครั้งคราว

**Status:** blocked: ข้อความ error ของรอบที่ล้ม (ยังไม่เคยจดไว้)

**Summary:**
- **Cause:** (เขียนท้ายสุด)
- **Fix:** (เขียนท้ายสุด)
- **Prevention:** (เขียนท้ายสุด)

## Symptom

`EpPage.test.tsx` › "a changed text is sent when the field is left; the answer shows the card as แก้เอง" ล้มราวหนึ่งในหลายรอบของ `npm --prefix frontend test` ทั้งชุด; รันไฟล์เดียวผ่าน. เคยล้มใน ticket 10, 11 และ feature review รอบหก (ครั้งนี้ไม่มีงานอื่นรันพร้อมกัน).

## Reproduce

**Command:** `npm --prefix frontend test` ทั้งชุด (ยังไม่มีคำสั่งที่ล้มซ้ำได้)

**Rate:** ทั้งชุด 1 ใน 14 รอบตอนไม่มีงานอื่นรันพร้อมกัน; 0 ใน 42 รอบที่พยายามทำให้ล้มบ่อยขึ้น (ดู Ledger)

**Minimised to:** —

## Scope

- **Docs say:** ข้อความที่เปลี่ยนส่งเมื่อออกจากช่อง (spec › เส้นเรื่อง)
- **Last good:** ไม่รู้: ล้มครั้งแรกใน ticket 10; ทุกครั้งไม่ได้จดข้อความ error
- **Ruled out:** ยังไม่ได้ตัดอะไรออก เพราะยังทำให้ล้มซ้ำไม่ได้
- **ข้อสังเกต (ไม่ใช่สาเหตุ):** บรรทัด 329 เช็ค `sent(…)` ทันทีหลัง `user.tab()` โดยไม่รอ; ต้องมีข้อความ error ก่อนจึงจะบอกได้ว่าล้มที่บรรทัดนี้หรือบรรทัด 330

## Fail path

ยังไม่รู้: ไม่มีรอบที่ล้มให้ตามดู

## Hypotheses

| # | Hypothesis | Prediction | Disproof | State |
|---|---|---|---|---|
| — | ไม่ตั้งสมมติฐาน: ยังทำให้ล้มซ้ำไม่ได้ (mantra 1) | | | |

## Ledger

| Run | Changed | Result | Rules in / out |
|---|---|---|---|
| 0 | ทั้งชุด 1 รอบ หลังแก้ของ feature review รอบหก | ล้ม 1 (ไม่ได้เก็บข้อความ error: grep เก็บแค่ชื่อ test) | ล้มตอนไม่มีงานอื่นรันพร้อมกัน |
| 1 | ทั้งชุด 3 รอบ และไฟล์เดียว 3 รอบ | ผ่านทุกรอบ | — |
| 2 | test เดียว (`-t`) 16 process พร้อมกัน | ผ่าน 16/16 | ภาระเครื่องอย่างเดียวไม่พอให้ test นี้ล้ม |
| 3 | ทั้งชุด 4 process พร้อมกัน 2 ชุด | test นี้ผ่าน 8/8; test ของ spoil-maker ล้ม (`DraftProgress` D87 ทุกรอบ, "แทรกใต้", "เลือก Shot ใหม่", `gpu_busy`) | ภาระหนักทำให้ test อื่นที่ขึ้นกับเวลาล้ม แต่ไม่ใช่ test นี้ (นอก feature, ภาระไม่ใช่ของจริง) |
| 4 | ทั้งชุดทีละรอบ 10 รอบ | ผ่าน 10/10 | — |
| 5 | test ของ toon `--sequence.shuffle`, seed 1–8 | ผ่าน 8/8 | ลำดับของ test ใน toon ไม่ใช่ตัวทำให้ล้ม (เท่าที่ seed 8 ตัวลองได้) |

## What is needed

รอบหน้าที่ test นี้ล้ม ให้เก็บข้อความ error ทั้งก้อน (`npm --prefix frontend test 2>&1 | tee …`, ห้ามกรองด้วย grep) แล้วรัน `/kiki-debug EpPage card text edit test flaky` พร้อมข้อความนั้น
