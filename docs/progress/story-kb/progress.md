# Progress: story-kb

**Now:** 01 backend เสร็จ (Stories API, Story ที่คลิปจำ, Ops); ส่วนหน้าเว็บของ 01 หยุดรอ design คลังความรู้ กับ แก้ Story (Blocked 1, 2)

**Next:** ทำ Figma frame จาก `docs/features/story-kb/ui-prompt.md` แล้ว

```
/warroom story-kb
```

จากนั้น `/warroom-build story-kb 01` ทำกลุ่ม tab คลังความรู้

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | คลังความรู้ — เพิ่ม แก้ ลบ Story | in-progress |
| 02 | ร่างบทด้วย Story | ready |
| 03 | เรียบเรียงใหม่ใช้ Story ล่าสุด | ready |

## Log

### 01: คลังความรู้ — เพิ่ม แก้ ลบ Story — stopped 2026-11-05

**Built:**
- `backend/stories.py` + `backend/routes/stories.py`: `GET/POST /api/stories`, `GET/PUT/DELETE /api/stories/{id}`, `GET /api/story-clips`; เช็คค่าตาม spec › Data (`invalid_story` + `field`, `invalid_request`); รายการมี `tokens` ของบล็อก Story (`null` ไม่มี tokenizer)
- ลบคลิป (`Transcriptions.delete_clip`) ลืม Story ของคลิป; Trim job ไม่แตะ; start backend ลบ `.tmp` และ key ค้าง; `clip-stories.json` หรือไฟล์ Story อ่านไม่ได้ → ว่าง/ไม่อยู่ในรายการ, log แค่ id
- กลุ่ม "Stories API" และ "Story ที่คลิปจำ และ Ops" ครบ; กลุ่ม "tab คลังความรู้" ยังไม่เริ่ม — design ของ 2 หน้าจอเป็น `pending` (Blocked 1, 2)

**Decided:**
- D17 — ไม่ส่ง `title`/`name` = ว่าง; ช่องบรรทัดเดียวรวมช่องว่าง; ชื่อซ้ำเทียบ casefold; ไม่สนฟิลด์ที่ไม่รู้จัก; Story อ่านไม่ได้เป็น `404`; `tokens` `null` เมื่อ tokenizer อ่านไม่ได้

**For the next ticket:**
- ยังไม่มีอะไรเขียน `clip-stories.json` นอกจาก test (`remember()` ใน `test_stories_api.py`): ticket 02 เขียนตอน Draft job `kind: "draft"` ผ่าน `stories` (ใต้ `_lock`, ตัวในสุด)
- `stories.prompt_block` มีแล้ว (ใช้นับ `tokens`) แต่ยังไม่มี test ข้อความตรงตัว: ticket 02 ทดสอบผ่านคำสั่งที่ `llm.requests` ได้
- token ของ Story ใน Draft job (D14) ต้องเป็น `503` `not_ready` ไม่ใช่ `null` แบบรายการ — `stories._tokens` คืน `None`; ticket 02 ต้องมีทางที่ raise
- `test_stories_api.py` import fixture จาก `test_spoil_trim_api.py` (pytest note บอกให้ใช้ `conftest.py`; มีแบบนี้อยู่แล้วใน `test_spoil_maker_episodes_api.py`) — ย้าย fixture ของ API ไป conftest ตอน feature review
- `stories._tokens` กับ `episodes.tokens` เรียก `count_tokens(project.snapshot_dir(QWEN, …))` ซ้ำกัน — รวมเป็นที่เดียวเมื่อ ticket 02 ใช้เป็นครั้งที่สาม

**Checks:** `uv run pytest` · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` · `npm --prefix frontend run build` — all green

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: คลังความรู้ (รายการ Story) | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | open |
| 2 | 01 | design: แก้ Story | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | open |
| 3 | 02 | design: ขั้น 1 ตั้งค่าคลิปสปอย: ช่อง Story | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | open |
| 4 | 03 | design: ขั้น 2 กล่องเรียบเรียงใหม่ | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | open |
