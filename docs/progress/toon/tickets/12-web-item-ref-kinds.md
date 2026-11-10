# 12: ItemRef และ ITEM_KINDS ของหน้าเว็บ toon

**What to build:** หน้าเว็บของ toon ส่งตัวละครหรือฉากหลังหนึ่งตัวเป็นค่าเดียวแบบเดียวกับ `ItemRef` ของ backend (D64) แทน `(sid, kind, id)` สามค่า, และชื่อ `sid`/`eid` เป็น `seriesId`/`epId`. สิ่งที่ต่างกันระหว่างตัวละครกับฉากหลัง (ขนาดช่องภาพ, aspect, การถามก่อนเลือกไฟล์) อยู่ใน `ITEM_KINDS` แทนกิ่ง `kind === "characters"`. การเช็คไฟล์แล้วส่งด้วย `sendFile` ของ `useCast` กับ `useSounds` ใช้ทางเดียว. ผู้ใช้เห็นทุกอย่างเหมือนเดิม.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D63, D64, D65
- Blocked: #25, #28 (feature review รอบสี่)

**Status:** ready

## Acceptance criteria

### ค่า item เดียวและชื่อ

- `itemPath`, `refUrl`, `pendingUrl`, `pickHash`, `startRefJob` ใน `features/toon/lib/series.ts` และผู้เรียกรับค่า item เดียว ไม่รับ `(sid, kind, id)` สามตัวคู่กัน; path และ hash ที่ได้เหมือนเดิมทุกตัว
- ไม่มีชื่อ `sid` หรือ `eid` ใน `features/toon/` (hook, lib, component, test) — ใช้ `seriesId` และ `epId`

### ITEM_KINDS

- ขนาดช่องภาพและ aspect ของ `CastPage.tsx` และ `PickPage.tsx` และการถามก่อนเลือกไฟล์ (ตัวละครถาม ฉากหลังเปิดเลือกไฟล์ตรง) อ่านจาก `ITEM_KINDS`; ไม่เหลือกิ่ง `kind === "characters"` ใน component ของ toon
- ตัวละคร → ช่องภาพสี่เหลี่ยมจัตุรัสและถามก่อนเลือกไฟล์ เหมือนเดิม; ฉากหลัง → ช่องภาพ 16:9 และเปิดเลือกไฟล์ทันที เหมือนเดิม (มี test ทั้งสองชนิด)

### ส่งไฟล์ทางเดียว

- `useCast` และ `useSounds` เช็คไฟล์แล้วส่งด้วย `sendFile` ผ่านตัวช่วยตัวเดียว: ไฟล์ไม่ผ่านเช็ค → notice เดิม ไม่ส่ง; ส่งแล้ว 200/201 → ค่าบนหน้าเปลี่ยนตามที่ backend ตอบ; error → `refused` เดิม; ยกเลิกระหว่างส่งของคลังเสียงพื้นยังทำงานเหมือนเดิม
- ตัวช่วยอยู่ตามกติกาของ `vite-react-web` SKILL.md และมี test ของตัวเอง
- test ของ hook และหน้าที่มีอยู่ยังผ่าน จำนวนไม่ลด
- `npm --prefix frontend run typecheck`, `npm test`, `npm run build`, `uv run pytest` และ CI ทั้งหมดเขียว
