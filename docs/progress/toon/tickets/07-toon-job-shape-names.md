# 07: โครงงานของ toon และชื่อที่ชนกัน

**What to build:** งานของ toon (Plot, Cards, Ref, Image, Voice, render) เหลือเจ้าของเดียวต่อเรื่อง: ตัวละครและฉากหลังใหม่สร้างใน `series`, การเปิด klein อยู่ที่เดียว, สิ่งที่ทั้งสอง job slot ใช้ร่วมกันไม่ซ้ำ, และชื่อในโค้ดไม่ชนกัน. ผู้ใช้เห็นทุกอย่างเหมือนเดิม; route, body และรหัส error ไม่เปลี่ยน.

**Blocked by:** 06: ส่วนที่ซ้ำและช่องโหว่เล็ก

**Covers:**
- Decisions: D45, D60
- ADR: 0010, 0012, 0015
- Blocked: #19, #21 (feature review)

**Status:** done

## Acceptance criteria

### โครงงาน (#19)

- Cards job เจอตัวละครหรือฉากหลังใหม่ในการ์ด → สร้างผ่านฟังก์ชันของ `series` (id ใหม่, ช่องของ model) ไม่ใช่ใน `cards`; test ของ Cards job ผ่านเหมือนเดิม
- `plot.writable` รู้ว่า EP ถูก render อยู่ผ่าน `episodes.ep_jobs` ไม่อ่าน `render_jobs.ep_use()` ตรง → เริ่ม Plot job ระหว่าง render EP เดียวกันได้ error เดิม
- process ของ child, คิวคำขอ และคิวคำตอบ เดินเป็นค่าเดียว (ไม่ส่งสามตัวคู่กันทุกที่)
- `ToonJobs.update`/`track`/`reply` ที่แค่ส่งต่อ หายไป หรือมีงานของตัวเอง; ผู้เรียกใช้ตัวจริง
- ลำดับเปิด klein (`Encode` แล้ว `Draw`) อยู่ที่เดียว; Ref job และ Image job เรียกตัวนั้น → test ของทั้งสองผ่านเหมือนเดิม
- `_running` และ `series_use` เขียนที่เดียว; `ToonJobs` และ `RenderJobs` ใช้ร่วมกัน → ลบ Series ระหว่าง job ใดทำงานได้ `series_busy` เหมือนเดิม

### ชื่อ (#21)

- ชนิดของ item (characters/backgrounds) ชื่อ `ItemKind` ไม่ชน `JobKind`; ตัวแปรและ path parameter ใน route ใช้ชื่อเดียวกัน; URL และ body field `item_kind` ไม่เปลี่ยน
- ตัวพูดชื่อเดียวกันใน `ToonJobs`, `RenderJobs` และ `SentenceVoicer`
- คอมเมนต์ "Step 1", "Steps 2–3" บอกชื่อส่วนใน spec ที่อ้าง (เช่น spec › Plot job ขั้น 1)
- test patch `start_klein_worker` ที่ module ที่ใช้จริง; `toon/__init__.py` ไม่ re-export ไว้ให้ test
- `uv run pytest`, `npm test`, `npm run build` และ CI ทั้งหมดเขียว
