# Debug: test frontend ล้มสุ่มครั้งละตัว

**Status:** fixed

**Summary:**
- **Cause:** test assert แบบ sync หลัง `await` ที่ไม่ได้รอผลที่ assert (คำตอบของ `fetch` หรือ `useEffect`); ปกติทันพอดี ใต้โหลดไม่ทัน จึงล้มสุ่มครั้งละตัว
- **Fix:** 11 test รอเงื่อนไขที่ assert ด้วย `findBy…`/`waitFor`; guard `drop` ของ `FileDropArea` เป็น `useLayoutEffect` (commit: ดู Fix)
- **Prevention:** กฎใน `.claude/skills/vite-react-web/rules/testing.md`; ทั้งชุดรันปกติ 24 รอบแดง 0 (เดิม 1 ใน 8)

## Symptom

Blocked 1 ของ reels-only: "test frontend ที่ไม่เกี่ยวกับงานนี้ล้มสุ่ม ~1 ใน 3 รอบของทั้งชุด (ครั้งละตัว: `SpoilMakerPage` polish, `ClipsPage` drop, …) มีตั้งแต่ก่อนเริ่ม feature บน `bf5383c`; รันซ้ำผ่าน".

## Reproduce

**Command:** `npm --prefix frontend test` (ทั้งชุด, `vitest run`)

**Rate:** ทั้งชุด 1 ใน 8 รอบ (2026-11-18); ตัวที่ล้ม: `SongsPage.test.tsx` › "เพลงทั้งหมด in the menu opens #/songs…" — `expect(linkBox()).toHaveFocus()` แต่ focus อยู่ที่ปุ่มเมนู "เมนู: แกะเพลง / เพลงทั้งหมด"

**Minimised to:** `npx vitest run src/features/drum-notes/components/SongsPage.test.tsx -t "เพลงทั้งหมด in the menu"` กับ probe หน่วง focus ของ `LinkForm` 30 ms → แดง 5/5

## Scope

- **Docs say:** หน้าเพลงว่าง: cursor อยู่ในช่องลิงก์ (drum-notes D28, ui-prompt screen 1 state 2); เลือกจาก drawer แล้ว focus ไปปุ่มเมนูของหน้าใหม่ (ui-nav D10)
- **Last good:** — (มีตั้งแต่ก่อน `bf5383c` ตาม Blocked 1)
- **Ruled out:** รายการเพลงโหลดไว้ก่อนเปลี่ยนหน้า — `useSongs` เริ่ม `loading` ทุกครั้งที่ mount ไม่มี cache ร่วม

## Fail path

`SongList.tsx` › `LinkForm`: `useEffect(() => { if (focused) input.current?.focus() }, [focused])`. React commit ข้อความ "ยังไม่มีเพลง…" กับ `focused = true` พร้อมกัน แต่ passive effect รันใน task หลัง commit; `findByText` resolve จาก MutationObserver (microtask) ก่อนนั้นได้ แล้ว `expect(linkBox()).toHaveFocus()` เห็น focus ที่ `PageLayout` ให้ปุ่มเมนูไว้ตอน mount (ui-nav D10). knob: เวลาระหว่าง commit กับ passive effect flush

## Hypotheses

| # | Hypothesis | Prediction | Disproof | State |
|---|---|---|---|---|
| H1 | `findByText` จบทันทีที่ DOM commit (MutationObserver เป็น microtask) แต่ `LinkForm` focus ช่องลิงก์ใน `useEffect` ซึ่ง React flush ใน task ถัดไป; `toHaveFocus()` ที่ตามมาแบบ sync จึงแข่งกับ effect | หน่วง effect ให้ช้าลง → แดงทุกรอบ; test รอ focus → เขียวแม้หน่วง | log รอบที่แดงมี focus ช่องลิงก์ก่อน assertion | confirmed by #5, #7 |
| H2 | `setTimeout` สำรองของ `picked` (ui-nav D10) ดึง focus กลับไปปุ่มเมนูหลังช่องลิงก์ได้ focus | log รอบที่แดง: focus ปุ่มเมนูมาทีหลัง focus ช่องลิงก์ | log รอบที่แดงไม่มี focus ช่องลิงก์เลย | killed by #4 |
| H4 | (กว้างกว่า H1) test หลายตัว assert แบบ sync หลัง `await` (`findBy…`, `user.click`) ที่ไม่ได้รอผลของงาน async ที่ assert: passive `useEffect` (focus, listener ของ `window`) หรือ `fetch` ที่ตอบแล้ว `setState`; ปกติงานนั้นเสร็จระหว่าง delay ภายในของ user-event พอดี, ใต้โหลดไม่ทัน | ทำให้ test รอเงื่อนไขที่ assert (หรือให้ app ทำในcommit เดียว) → ทั้งชุดใต้โหลดเดียวกับ run 6 เขียวทุกรอบ | run 6 ซ้ำหลังแก้ ยังมี test ล้มที่ไม่ใช่แบบนี้ | confirmed |
| H3 | รายการเพลงยังไม่โหลดตอน assert | ข้อความว่างไม่ขึ้น | `findByText` ข้อความว่างผ่านก่อน assertion ทุกรอบ | killed by #1 |
| H5 | (Outsider) `ClipsPage` drop: event หายเพราะยิงก่อน listener ใน `useEffect` ติด — `waitFor` แก้ไม่ได้ | listener ใน `useLayoutEffect` → drop ไม่ล้มอีก | run 8 ยังมี drop ล้ม | confirmed by #8, #10, #12 |

## Ledger

| Run | Changed | Result | Rules in / out |
|---|---|---|---|
| 1 | ทั้งชุด 8 รอบ (JSON reporter) | 1/8 แดง: `SongsPage` focus | ตัวที่ล้มครั้งนี้เป็น focus ไม่ใช่ timeout |
| 2 | test เดียว (`-t "เพลงทั้งหมด in the menu"`) 15 รอบต่อกัน | 1/15 แดง | ล้มได้โดยไม่มีไฟล์อื่น: ไม่ใช่ state รั่วข้ามไฟล์ |
| 3 | test เดียว 6 ตัวพร้อมกัน × 3 | 1/18 แดง | load จาก CPU ไม่ดันอัตราขึ้นชัด |
| 4 | probe `[DBG-f7k1]` บันทึกทุก `focus()` พร้อม stack (เขียนไฟล์ตอน `afterEach`), 6 loop พร้อมกัน × 12 | 5/72 แดง; ทุกรอบที่แดง: hashchange `#/songs` → focus ปุ่มเมนูจาก `PageLayout.tsx:84` (effect ของ hash) → **ไม่มี** focus ช่องลิงก์ก่อน assertion; รอบที่เขียว focus ช่องลิงก์ ~7 ms หลังปุ่ม | H2 ออก; H1 เข้า |
| 5 | probe หน่วง focus ใน `LinkForm` effect 30 ms (`setTimeout`) | 5/5 แดง | H1 เข้า: repro ได้ทุกรอบ |
| 6 | ทั้งชุด 2 ชุดพร้อมกัน × 12 (โหลด CPU), JSON reporter | 20/24 แดง, 6 test: `ClipsPage` drop ×12, `SongsPage` focus ×3, `ScriptReview` ยกเลิก pick ×2, `ScriptReview` แทรกใต้, `DraftProgress` ยกเลิก, `SongsPage` ยกเลิก Pick disabled | ทุกตัวเป็นแบบเดียวกับ H1 (H4): assertion แบบ sync หลัง `await` ที่ไม่ได้รอสิ่งที่ assert |
| 7 | test focus แก้เป็น `await waitFor(() => expect(linkBox()).toHaveFocus())` + probe หน่วง 30 ms ของ run 5 | 5/5 เขียว | H4 เข้า: test รอผลจริงแล้วไม่ขึ้นกับจังหวะ |
| 8 | แก้ 6 test ของ run 6 (5 ตัวรอใน test, `FileDropArea` เป็น `useLayoutEffect`), ทำ run 6 ซ้ำ | 5/24 แดง; 6 ตัวเดิมไม่ล้มเลย; ตัวใหม่ 3 ตัวแบบเดียวกัน: `ScriptReview` ยกเลิก polish, `ClipsPage` 37% หลัง `nextPoll`, `DrumsPage` ล่าสุดใน `localStorage` | H4, H5 เข้า; ใต้โหลด 2 เท่ามี test แบบเดียวกันอีก |
| 9 | `Response.json()` ใน Node นับ microtask/macrotask | resolve หลัง 3 microtask | ตัด "fake backend ช้าเพราะ stream" ออก: ไม่แก้ `testBackend` |
| 10 | แก้ 3 ตัวของ run 8, ทำ run 6 ซ้ำ | 3/24 แดง: `ScriptReview` เลือก Shot ใหม่, `App` drawer ปิดหลัง back | แบบเดียวกัน แก้ 2 ตัว |
| 11 | ทั้งชุดรันปกติ (ทีละชุด) 24 รอบ | 0/24 แดง (ก่อนแก้ 1/8) | อาการที่เจ้าของเห็นหาย |
| 12 | ทำ run 6 ซ้ำ | 2/24 แดง: `RenderResults` render 50% หลัง `tick` (แบบเดียวกัน แก้แล้ว), `SongsPage` ทำนอง `findByRole("Reel cover")` เกิน 1 วิ | ตัวหลังรอด้วย `findBy` อยู่แล้ว: หมดเวลาใต้โหลด 2 เท่า ไม่ใช่ H4 — ไม่แก้ (ยืด timeout คือกลบ) |

## Outsider

จัดลำดับ: H1 แน่นสำหรับ `SongsPage`; H4 กว้างไปเพราะ run 6 จัดกลุ่มด้วยตา; เสนอ H5 (`ClipsPage` drop = event หาย ไม่ใช่มาช้า — `waitFor` ช่วยไม่ได้) และ H6 (D10 ให้ focus ปุ่มเมนู แล้ว D28 ให้ช่องลิงก์ ~7 ms หลัง: focus กระโดด). การทดลองที่ตัดสิน: ทำ run 6 ซ้ำหลังแก้ → run 8: 6 ตัวเดิม 0 ครั้ง, ตัวที่ล้มต่อดูทีละตัวแล้วเป็นแบบเดียวกัน (run 10, 12). H6: focus สุดท้ายตรง D28 ทุกรอบ; ช่องลิงก์ได้ cursor เมื่อรายการโหลด ซึ่งเป็นสิ่งที่ D28 ตั้งใจ — ไม่เปิด spec ใหม่.

## Fix

- **Regression test:** test เดิม 12 ตัว (11 ตัวที่แก้ + `ClipsPage` drop) คือ seam; ไม่มี seam ที่ทำให้แดงทุกรอบโดยไม่หน่วงโค้ด — probe หน่วง 30 ms (run 5) แดง 5/5 ก่อนแก้ เขียว 5/5 หลังแก้ (run 7)
- **Change:** test รอสิ่งที่ assert: `SongsPage` (focus ช่องลิงก์, ยกเลิก Pick disabled), `DraftProgress` (กำลังยกเลิก), `ScriptReview` (แทรกใต้, ยกเลิก pick, ยกเลิก polish, เลือก Shot ใหม่), `ClipsPage` (37%), `DrumsPage` (ล่าสุด), `App` (drawer ปิดหลัง back), `RenderResults` (render 50%); `FileDropArea` guard `dragover`/`drop` ของ `window` เป็น `useLayoutEffect`. ไม่มี retry ไม่ปิด shuffle ไม่ยืด timeout
- **Probes removed:** `[DBG-f7k1]` — `grep -rn DBG-f7k1 frontend/src` ไม่พบ

## Postmortem

**Timeline:**
- ก่อน `bf5383c` — เริ่ม (drum-cover progress บันทึก "flaky เดิม" ตั้งแต่ ticket ของมัน)
- 2026-11-18 — reels-only ticket 01 บันทึกเป็น Blocked 1
- 2026-11-18 — พบ (run 4–6), แก้ (run 7–12)

**Root cause:** test ล้มสุ่ม → assertion อ่านหน้าก่อน React ทำงานที่ assert เสร็จ → `await` ก่อนหน้ารอสิ่งอื่น (DOM ของอีกอย่าง, คลิก, ตัวจับเวลา) ไม่ใช่ผลที่ assert → แบบนี้ผ่านเกือบทุกรอบบนเครื่องว่าง จึงถูก copy ต่อกันในหลาย feature และกฎ test ของ repo ไม่ได้บอกว่าห้าม.

**Prevention:**
- กฎ "ผลของ request หรือ effect assert ด้วย `findBy…`/`waitFor`" และ listener ของ `window` ใน `useLayoutEffect` — tracked in `.claude/skills/vite-react-web/rules/testing.md`
- test แบบเดียวกันที่ยังไม่ล้มให้เห็น: แก้เมื่อเจอ ใช้ run 6 (ทั้งชุด 2 ชุดพร้อมกัน) เป็นเครื่องมือหา — tracked in this record

**What helped:** probe ที่เก็บ stack ของทุก `focus()` ใน memory (เขียนไฟล์ตอนจบ test ไม่ให้ IO ไปเปลี่ยนจังหวะ) ชี้ว่าช่องลิงก์ไม่เคยได้ focus; โหลด 2 ชุดพร้อมกันดันอัตราจาก 1/8 เป็น 20/24 จนเห็นทั้งตระกูล.
