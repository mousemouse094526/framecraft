# Progress: toon

**Now:** ตัด ticket 11 (Blocked #26, #27) และ 12 (Blocked #25, #28) จาก smell ของ feature review รอบสี่; เช็คมือบน Mac ของ 03 และ 04 (Blocked #11, #12) ยังรอ owner

**Next:**

```
/warroom-build toon 11
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้ง klein, Series และภาพอ้างอิง | done |
| 02 | EP, พล็อต และเส้นเรื่อง | done |
| 03 | ภาพการ์ดและเสียงเล่า | done |
| 04 | คลังเสียงพื้นและ render | done |
| 05 | แยกงานของ toon ออกเป็นส่วน | done |
| 06 | ส่วนที่ซ้ำและช่องโหว่เล็ก | done |
| 07 | โครงงานของ toon และชื่อที่ชนกัน | done |
| 08 | เริ่มและหยุด child และ render ที่ซ้ำข้าม feature | done |
| 09 | ItemRef และ fixture ของ test ที่ใช้ร่วม | done |
| 10 | state ที่ใช้ร่วมของ hook หน้าเว็บ toon | done |
| 11 | ค่า EP เดียวและ helper ของ test ที่ใช้ร่วม | ready |
| 12 | ItemRef และ ITEM_KINDS ของหน้าเว็บ toon | ready |

## Log

### 10: state ที่ใช้ร่วมของ hook หน้าเว็บ toon — done 2026-11-10

**Built:**
- `features/toon/hooks/useReadyState`: `useMountedState` บวก `update` ที่แก้แค่ state `ready`; `useRender`, `useSounds`, `usePickRef`, `useCast`, `useEp` ใช้แทน `update` ที่เขียนเองห้าที่
- `features/toon/lib/edit.sendEdit`: 200/201 เป็น `{ kind: "saved", value }` ไม่งั้น `{ kind: "refused", notice }`; `useCast.sendItem` และ `useEp.edit` ใช้ทางเดียว
- test: `useReadyState.test.ts` (`renderHook`), `edit.test.ts`; หน้า: เพิ่มตัวละครที่ถูกปฏิเสธแล้วส่งใหม่ผ่าน, แก้การ์ดที่ถูกปฏิเสธแล้วส่งใหม่ผ่าน (ผ่านกับโค้ดก่อนแก้ด้วย)
- spec › Modules touched, `rules/testing.md`

**Decided:**
- D65 — `useReadyState`, `sendEdit`

**For the next ticket:**
- review ไม่แก้ (ตั้งใจ): สองบรรทัดท้าย `sendItem`/`edit` ต่างกันที่ field; `useSeriesForm` คง 200/201 ของตัวเอง (เปิดหน้าใหม่ ไม่ใช่ notice); `refused` ของ `useCast` ยังใช้ใน `startRef`, `upload`; `edit.test.ts` เทียบ `Notice` ทั้งก้อน (`tone: "error"` เป็นสัญญาของ `sendEdit`)
- test ที่ล้มครั้งเดียว: `EpPage.test.tsx` › "a changed text is sent when the field is left…" (test เดิม ไม่ได้แก้) ล้มหนึ่งรอบขณะ reviewer รัน vitest พร้อมกัน; รันซ้ำ 4 รอบเฉพาะไฟล์และ 4 รอบทั้งชุดผ่าน — ถ้าล้มอีกเมื่อไม่มีงานอื่น → `/kiki-debug EpPage card text edit test flaky`

**Checks:** `uv run pytest` 1055 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 409 passed (+8); `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `71afff8`: Standards ไม่มีข้อผิดกติกา + smell (แก้: union ของ `sendEdit` มี `kind`, `sendJson<T | Refusal>`, test เรียกตามชื่อไม่ใช่ index), Spec ไม่มีพฤติกรรมเปลี่ยน (แก้: ลบ test หลัง unmount ที่ผ่านเสมอ; กติกาใน testing.md คงไว้ให้ทุก feature, D65), Newcomer สรุปตรง What to build (แก้: docstring ตำแหน่ง `setState` ของ `useReadyState`, `sendEdit` ครอบการเพิ่มและการลบ และ `error` เสมอ, คอมเมนต์ใน test ว่าส่งซ้ำได้เพราะอะไร)

### 09: ItemRef และ fixture ของ test ที่ใช้ร่วม — done 2026-11-10

**Built:**
- `series.ItemRef(project, series_id, item_kind, item_id)`: `change_item`, `delete_item`, `ref_plan`, `ref_image`, `pending_image`, `pending_path`, `put_pending`, `pick`, `check_upload`, `receive_upload` และ helper รับค่าเดียว; `_require_item` (Series และ item หรือ `404` เดิม) แทน `_item(require_series(...))` เจ็ดที่; `RefPlan.item_ref`
- `routes/toon.py`: dependency `item_ref` สร้าง `ItemRef` จาก path ครั้งเดียวใน 7 route ที่มี `{item_id}`; `refs.plan` สร้างจาก body
- test: `fakes.toon_api(answers, tts_seconds=, uses=)` คืน `llm`, `klein`, `tts`, `client` ของไฟล์ test API ของ toon ทั้งหก; `TOON_VOICE`, `write_toon_voice` ย้ายไป `fakes.py`; probe yt-dlp/Deno อยู่ใน fixture `adapter`; conftest มีแค่ `fake_root`
- test ใหม่: 7 route ของ item หนึ่งตัว `404` ข้อความเดิมเมื่อไม่มี Series หรือไม่มี item (ผ่านกับโค้ดก่อนแก้ด้วย); ภาพที่รอเลือกใน test อ่านผ่าน API
- spec › Modules touched, `fastapi-api` SKILL.md, `rules/testing.md`

**Decided:**
- D64 — `series.ItemRef`, dependency `item_ref`, `_require_item`, `fakes.toon_api`

**For the next ticket:**
- review ไม่แก้ (ตั้งใจ): `refs.run`/`WORK.ready`/`clean_up` ยังรับ `project` แยกจาก `plan.item_ref.project` (รูปของ `steps.Work` ที่ทุก kind ใช้); `uses=` ของ `toon_api` เป็นชื่อ fixture แบบ string (`getfixturevalue`, docstring บอก); path ของภาพอ้างอิงยังต่อสตริงใน `series` ไม่ได้เป็น method ของ `ItemRef`; `ItemRef` คู่กับ `EpRef` ชื่อคล้ายกัน (ticket ตั้งชื่อ `ItemRef`, docstring บอกว่าเป็นที่อยู่ของ item ไม่ใช่ภาพอ้างอิง)

**Checks:** `uv run pytest` 1055 passed (+7 test ใหม่); `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 401 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `3a639c3`: Standards 2 ข้อผิดกติกา (แก้: `test_toon_series_api.py` ใช้ `toon_api`, คำว่า "plain helpers" ใน testing.md) + smell (แก้: `_require_item` แทนเจ็ดที่, `_find` → `_item_or_none`, อ่าน field แทนแกะ tuple ตามลำดับ, type ของ `toon_api`), Spec ไม่มีข้อหนัก (แก้: test อ่านภาพที่รอเลือกผ่าน API ไม่ผ่าน `ItemRef`, D64 บอกที่ที่แปดคือ `refs.plan`), Newcomer สรุปตรง What to build (แก้: docstring `ItemRef` ว่าเป็นที่อยู่ ไม่ใช่ภาพอ้างอิงและไม่ใช่แค่จาก path, ชื่อ `_item_or_none`/`_require_item`, docstring `toon_api` ว่าต้องคงชื่อ fixture, ตัด "`series` the stored one")

### Feature review (รอบสี่) — done 2026-11-10

**Built:**
- `klein.DRAW_TIMEOUTS` ของ Windows = 900 × `llm.WINDOWS_START`; `llm.TIMEOUTS["win32"]` สร้างจากค่า Mac × ตัวเดียวกัน
- `gate_rows.LINK_TOOLS` (yt-dlp, Deno): `spoil.downloads` และ `toon.sounds.link_rows` ใช้ร่วม
- `useSeriesForm` ใช้ `useReadyState`
- `episodes._editing` (ล็อก, เขียน EP, ลบไฟล์การ์ดที่เอาออก) ในการแก้ act/segment/card เก้าตัว; `_require_background`, `_placed_segments`; `card_seconds(status: AudioStatus)`
- ชื่อและคอมเมนต์: `folder` ใน `refs.run`, `choose`/`pick` ของ `usePickRef`, `nothing_to_draw` ใน `useEp.start`
- spec › Modules touched, `fastapi-api` SKILL.md

**Decided:**
- D66 — timeout ของ klein จาก `llm`, `gate_rows.LINK_TOOLS`, `useSeriesForm` ใช้ `useReadyState`, `episodes._editing`

**For the next ticket:**
- ไม่แก้ (ตั้งใจ, บันทึกในรอบก่อนแล้ว): `plan` สองรอบ, `running()` อ่านไม่ล็อก, registry `ep_jobs`/`series_jobs`, test นอก seam (`test_toon_klein.py`, `test_toon_modules.py`, D59), `sendItem`/`edit` ต่างที่ field (D65), `job` ของ `steps.Run` ทุก `run` (D66)
- ค่าที่คงไว้ตอนโหลดใหม่ (`notice: s.kind === "ready" ? …`) ต่างกันทุก hook จึงไม่รวม (D66); `pending: int` (0 หรือ 3) มีคอมเมนต์อยู่แล้ว; `speaking.speak` ต้องดึงอีกครั้งจึงปิด child (docstring บอก)
- test ที่ล้มครั้งเดียวของ ticket 10 (`EpPage.test.tsx` แก้ข้อความการ์ด): รัน `EpPage` ซ้ำ 3 รอบและทั้งชุด 2 รอบผ่าน
- smell ใหญ่ → Blocked #25–28

**Checks:** `uv run pytest` 1055 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 409 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `912c7c4`: Standards ไม่มีข้อผิดกติกา + smell 6 (หนักสุด Duplicated ของการแก้ EP เก้าตัวใน `episodes.py`), Spec ไม่มี gap ที่ขวาง + 6 (หนักสุด แถว gate yt-dlp/Deno สองที่ ขัด D59; timeout ของ klein บน Windows ไม่ผูก `llm`), Newcomer สรุปตรง spec › Solution + เดา 16 จุด (หนักสุด `useEp.start` ที่ไปต่อหลัง `nothing_to_draw`)

### Feature review (รอบสาม) — done 2026-11-10

**Built:**
- Cards job อ่านคลังเสียงพื้นอีกครั้งตอนเขียนผล: เสียงที่ถูกลบระหว่างงานเป็น `sound: null` (spec › Cards job ขั้น 5); test ลบเสียงระหว่าง Qwen แตกองก์
- `disk.require_free` / `disk.MIN_FREE_BYTES` ที่เดียว (Ref, Image, Render job, Sound import ของ toon และ Render job ของสปอยเมกเกอร์); `series.require_series` แทน `_series` สองตัว; `steps.Qwen.once` / `end` ที่ `answer` และ `scenes` ใช้ร่วม
- `missing_refs[].item_kind` (เดิม `kind`); `ffmpeg_failed` ออกจาก `ErrorCode` ของ Toon job และ spec
- หน้าเว็บ: `lib/kinds.ts` `ITEM_KINDS` (ชื่อ icon); `VOICES_HASH` ใน `lib/voices.ts`; `useEp` ใช้ `noticeOf`; test ข้อความ legal เขียนข้อความเต็ม
- docstring ของ `test_toon_klein.py` และ `test_toon_modules.py` อธิบายในตัว; `clean_up(_state)`; spec, `fastapi-api` SKILL.md

**Decided:**
- D63 — `disk.require_free`, `series.require_series`, `Qwen.once`, เสียงที่ถูกลบระหว่าง Cards job, `missing_refs[].item_kind`, `ITEM_KINDS`, `VOICES_HASH`

**For the next ticket:**
- ไม่แก้ (ตั้งใจ): `OSError` ตอน copy ภาพอ้างอิงออกเป็น 500 ของ framework (ทั้งแอปไม่มี handler ของ error ที่ไม่คาด, D63); test นอก seam (`test_toon_modules.py` ของ D59, `parse_scene` และ `named_patterns` เป็นฟังก์ชันล้วน); `renders.latest_at` มีผู้ใช้ตัวเดียวแต่ SKILL.md เขียนไว้; `SoundsRender.test.tsx` ครอบสองหน้า; ขนาดช่องภาพและการถามก่อนเลือกไฟล์ของตัวละครยังแตกกิ่งตาม kind (พฤติกรรมต่างกัน ไม่ใช่แค่หน้าตา); `running()` อ่านไม่ล็อก (docstring บอกไว้); `plan` สองรอบ (คอมเมนต์บอกไว้)
- smell ใหญ่ → Blocked #22–24

**Checks:** `uv run pytest` 1048 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 401 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `912c7c4`: Standards ไม่มีข้อผิดกติกาหนัก + 9 (หนักสุด เช็คดิสก์ 1 GiB ซ้ำโดยไม่ย้ายไปที่ส่วนกลาง ผิด SKILL.md "Where shared code goes"), Spec 6 (หนักสุด Cards job เขียน `sound_id` ที่ถูกลบแล้ว), Newcomer 12 (หนักสุด `reply` คืน `worker_error` เมื่อขอไว้; `ffmpeg_failed` ที่ไม่มีใครใช้)

### 08: เริ่มและหยุด child และ render ที่ซ้ำข้าม feature — done 2026-11-10

**Built:**
- `ModelJobSlot.start_child` (track แล้วรอข้อความแรก), `ask`, `stop_child`, `free_gpu`; `Worker.end`: Qwen (`steps.start_qwen`, Describe, Draft), klein (`steps.open_klein`, `steps.draw` แทน `klein_reply`) และ `speaking.Speaker` เริ่มและหยุด child ทางเดียว; `_finish` ใช้ `stop_child`; `_free_gpu` สองตัวของ render หายไป
- `renders.PIECES_SHARE`, `pieces_percent`, `encode_progress`: `percent` ของ render ทั้งสอง feature; `renders.Render(folder, name)` (`next_free`, `file`, `finish`, `require`, `complete`, `delete`)
- `series.ref_revs` (หน้า EP, Image job, Render job); `episodes.plot_items(…, from_qwen)` ตัวเดียวแทน `_plot_items` สองตัว (ของ Qwen ที่ผิดตัดทิ้ง, ของผู้ใช้ `invalid_request`)
- test: Qwen, klein, OmniVoice ตายตอนโหลด → `crashed` และ GPU ว่าง (`FakeModel.crash_on_load`); ลองของ Plot job ที่ช้าเกินหยุด child ตัวนั้นแล้วเปิดตัวใหม่; คำตอบพล็อตของ Qwen ที่มีของผิดรูป
- spec › Modules touched, `fastapi-api` SKILL.md

**Decided:**
- D62 — `start_child`/`ask`/`stop_child`/`free_gpu`, `Worker.end`, `steps.draw`, `renders.Render`, `encode_progress`, `series.ref_revs`, `episodes.plot_items`

**For the next ticket:**
- review ไม่แก้ (ตั้งใจ): `plot_items` ใน `episodes` อ่าน `llm_reply` (ผู้ใช้กับ Qwen ใช้ตัวเดียวตามตั๋ว; SKILL.md เขียนไว้); `result_file`/`delete_result` สองบรรทัดคล้ายกันใน render สองฝั่ง (folder ต่างกัน); `stop_on_shutdown` เรียก `stop_process` ตรง (D62); `llm.respond.__self__.plot` ใน test เป็นแบบเดิมของหลายไฟล์; id ของ Qwen ที่ไม่ใช่ string ตอนนี้ถูกตัดทิ้งแทน `internal`

**Checks:** `uv run pytest` 1047 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 401 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `34c5b91`: Standards ไม่มีข้อผิดกติกา + smell (แก้: การจบ/ตรวจ/ลบเป็น method ของ `Render`, `new` → `next_free`, `draw` รับ tuple, ตัวแปรดิบใน `writer`, สร้าง request ก่อน `ask`, `plot_items` ใช้ `drop()`), Spec (แก้: `"id": null` ของ Qwen ตัดทิ้งแบบเดิม — เดิมเปลี่ยนพฤติกรรม, test klein ตายตอนโหลด, `stop_on_shutdown` ใน D62), Newcomer สรุปตรง What to build (แก้: พารามิเตอร์ `ready` → `first`, คอมเมนต์ว่าเมื่อไรใช้ `stop_child`/`free_gpu`, ชื่อ test, คอมเมนต์ test timeout, คืน GPU ใน test)

### 07: โครงงานของ toon และชื่อที่ชนกัน — done 2026-11-10

**Built:**
- `backend/workers.py` `Worker` (process, คิวคำขอ, คิวคำตอบ เป็นค่าเดียว): `start_worker` ของ llm, tts, klein คืนตัวนี้; `ModelJobSlot.reply(worker, …)` รับตัวนี้
- `JobSlot.update`, `running`, `ModelJobSlot.track`, `reply` เป็น public; `ToonJobs.update`/`track`/`reply` ที่ส่งต่อหายไป; `_running`/`series_use` สองชุดหายไป (`series_jobs` เก็บ slot)
- `episodes.EpUse(ep_id, how)` และ `episodes.rendering`: `plot.writable` ไม่ import `toon.render`
- `steps.open_klein` เปิด klein ที่เดียว (Ref job, Image job); test patch `backend.toon.klein.start_worker`; `toon/__init__.py` ไม่ re-export
- `series.new_items` สร้างตัวละครและฉากหลังใหม่จากพล็อต (แทนใน `cards.run`)
- ชื่อ: `kinds.ItemKind` (characters/backgrounds), `KindRow`; ตัวแปรและ path parameter `item_kind`; หน้าเว็บ `ItemKind`; `speaker` ทั้งสาม slot, `speaking.Speaker(slot)`; คอมเมนต์ขั้นเป็น `Spec › X job step N`
- test: Plot job ระหว่าง render EP เดียวกัน `409` `ep_busy`
- spec › Modules touched, `fastapi-api` SKILL.md

**Decided:**
- D61 — `Worker`, slot method public, `EpUse`, `open_klein`, `new_items`, `ItemKind`

**For the next ticket:**
- review ไม่แก้: `worker.requests.put(None)` (ปิด child) และ put แล้ว `reply` ซ้ำหลายที่ — ticket 08 (เริ่มและหยุด child); `series_jobs` อ่าน `series_id` ของงานที่ `JobSlot` ไม่ได้สัญญาไว้ในชนิด; `Worker` field เป็น `Any` (fake ของ test ไม่ใช่ `multiprocessing`); test patch klein ด้วย string เพราะ fixture ชื่อ `klein` บัง module

**Checks:** `uv run pytest` 1042 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 401 passed; `npm --prefix frontend run build` ผ่าน. Review สามแกนจาก `9e64c3d`: Standards ไม่มีข้อผิดกติกา + smell (แก้: `_taken` ใช้ `running`, `prompts` บัง module, `EpUse` สอง bool เป็น `how`, `Speaker` รับ slot, ข้อยกเว้น `missing_refs[].kind` ใน SKILL.md), Spec ครบ (แก้: test Plot job ระหว่าง render), Newcomer (แก้: `ep_id is not None` คืน, docstring `KindRow`, คอมเมนต์ `EpUse`)

### Feature review (รอบสอง) — done 2026-11-10

**Built:**
- Render job ของ toon `zip` ตัวพูดก่อนการ์ด: OmniVoice ได้ `None` แล้วออกเอง (เดิมถูกหยุดด้วย `_free_gpu`); test ดูว่า child ถูกขอให้ออก (`asked_to_end` ใน `fakes.py`)
- `renders.finish` (srt, json, เอา `.partial` ออก json ท้าย), `renders.listed`, `Stored`: render ของสปอยและการ์ตูนเล่าใช้ร่วม; `gate_rows.voice` แทน `voices.needed_rows`, `gate_rows.render(project, voices_first)`
- ชื่อ: `ToonRenderJobError`, `_cards_to_voice`, `ToonJobs.use_child`, `speaking.Voice`; `episodes._use` สามค่าเป็น `_jobs_on`/`_locked`; คอมเมนต์ของ `work.plan` สองรอบ, `clean_up`, `done` ที่นับต่อ state
- หน้าเว็บ: `cancelToonJob` ข้าง `useToonJobPoll`, `useEp` ใช้ `NOT_NOW`, ชนิดและ path ของ Render job ย้ายเป็น `features/toon/lib/render.ts`, token `--color-info` (Alert แบบ info ไม่ใช้สีขอบเป็นสีตัวหนังสือ)
- test: `series_busy` ของ Plot, Cards, Voice job; Image job กับ `diffusers` รุ่นอื่น `503` `not_ready` (แทน test ที่เทียบ `gate_rows.klein` ตรง); test วน import นับ `from backend import toon`
- spec: ตาราง API มี `PATCH …/acts/{aid}`, `gpu_kind` คงทั้งงาน, Modules touched › `backend.renders`; D59 แก้ชื่อ; `fastapi-api` SKILL.md

**Decided:**
- D60 — render จบที่ `backend.renders`, `gate_rows.voice`, ตัวพูดถูกถามก่อนใน `zip`, `gpu_kind` คงทั้งงาน

**For the next ticket:**
- ไม่แก้ (ตั้งใจ): `renders._is_name` ใช้ `strptime` ทั้งสอง feature (D59 บันทึกไว้); test วน import อยู่นอก seam (D59 เลือก); test `in_use` patch `Path.unlink` ทั้ง process (Mac เปิดไฟล์ค้างให้ลบไม่ได้ไม่ได้); path ใน `lib/gpu.ts` เป็น string แบบเดียวกับทุก feature (lib ไม่ import feature)
- smell ใหญ่ → Blocked #19–21

**Checks:** `uv run pytest` 1041 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 401 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `912c7c4`: Standards ไม่มีข้อผิดกติกา + smell 6 (หนักสุด การจบ render ซ้ำสองฝั่ง), Spec 15 (หนักสุด `zip` ที่ถามการ์ดก่อน), Newcomer 12 (หนักสุด `work.plan` สองรอบ, `Kind`/`JobKind`)

### 06: ส่วนที่ซ้ำและช่องโหว่เล็ก — done 2026-11-10

**Built:**
- `backend/renders.py`: ชื่อว่าง, ผลที่ครบ (`complete_names`, `results`, `require`), `latest_at`, การลบ (mp4 ก่อน json ท้าย, `409` `in_use`), `.partial` ที่ค้าง; แถว gate ของ render เป็น `gate_rows.render`; `spoil_maker.render` และ `toon.render` เรียกตัวนี้; `toon.episodes` อ่าน `renders.latest_at` จึงไม่ import `toon.render` (ไม่มี import ในฟังก์ชันใน `toon/` แล้ว)
- `checks.klein_packages(probes)`: แถว `diffusers` และ `gguf` ที่ Status check และ `gate_rows.klein` อ่าน
- Sound import ไฟล์: ถาม `request.is_disconnected()` ทุก 0.25 วินาทีระหว่าง ffmpeg แปลง; หน้าเว็บหาย → ffmpeg หยุด, ไม่เขียน `sounds.json`, ไม่มีไฟล์ค้าง
- หน้าเว็บ: `hooks/useToonJobPoll` ที่ `useCast`, `usePickRef`, `useEp` ใช้; `playAudio` ย้ายเป็น `lib/audio.ts` (ปุ่ม "ฟัง" ของการ์ดและคลังเสียงพื้น ใช้ร่วมกับสปอย)
- test: หน้าเว็บหายระหว่างแปลงเสียง และหายตอน ffmpeg จบพอดี (ASGI `Upload(then="leave")`, `play(path=)` ใน `fakes.py`), ลบคลิปที่ player เปิด `409` `in_use`, ไม่มีวง import ใน `backend.toon` (`test_toon_modules.py`), gate ของ klein ได้แถวเดียวกับ Status check, `GENRE_DEFAULTS`/`DEFAULTS` เทียบ `backend/tests/golden/toon_genre_defaults.json` ทั้งสองฝั่ง, "ฟัง" ของการ์ดและของคลังเสียงพื้น
- spec › Modules touched, คลังเสียงพื้น, Render job, ตาราง API; `fastapi-api` และ `vite-react-web` SKILL.md

**Decided:**
- D59 — `backend.renders`, `checks.klein_packages`, Sound import หยุดเมื่อหน้าเว็บหาย, ไฟล์ golden ของค่าตั้งต้นแนว, `lib/audio.ts`

**For the next ticket:**
- review ไม่ได้แก้: `(folder, name)` เดินคู่กันใน `backend.renders` (Data Clump, ชื่อเป็น `str`); `Upload(then="leave")` จำลองพฤติกรรมของ uvicorn เอง ยังไม่ได้ลองกับ uvicorn จริง (เช็คมือ: ปิดแท็บระหว่างเอาไฟล์เสียงยาวเข้า)
- feature review: smell ที่ค้างจาก 05 (`cards.run` สร้างตัวละครเอง, Data Clump `process, requests, replies`, Middle Man ของ `ToonJobs`, เปิด klein ซ้ำใน `refs`/`images`, `_running`/`series_use` ซ้ำ), `series_busy` ของ Plot/Cards/Voice ไม่มี test; เช็คมือบน Mac (Blocked #11, #12) ยังรอ owner

**Checks:** `uv run pytest` 1038 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 401 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `b676fb4`: Standards ไม่มีข้อผิดกติกา + smell (แก้: แถว gate ของ render ย้ายเป็น `gate_rows.render` ให้ `backend.renders` ไม่ import `spoil_maker`, `renders.results`/`require` แทนบรรทัดซ้ำสองฝั่ง, ชื่อ `complete_names` `_run_unless_gone` `page_gone`, `Upload`/`Gate`/`play` ย้ายเป็น `fakes.py`, log ซ้ำใน `receive`), Spec 1 race (หน้าเว็บหายช่วง 0.25 วิสุดท้ายของ ffmpeg ยังได้เสียง: แก้ด้วยการถามอีกครั้งก่อนเข้าคลัง + test) + `playAudio` ไม่กัน `new Audio` throw (แก้) + เช็คหลัง ffmpeg ทำให้ลิงก์ที่ยกเลิกช้าเป็น `cancelled` (เอาออก), Newcomer สรุปตรง What to build; แก้ log ของ `latest_at`, test comedy ที่ซ้ำ golden ออก, คอมเมนต์ test ของ gate klein

### 05: แยกงานของ toon ออกเป็นส่วน — done 2026-11-10

**Built:**
- `speaking.Speaker` เป็นตัวพูดที่ slot ถือ (`Speaker(self._track, self._reply)`, `start`, `speak`); `ToonJobs`, `toon.render.RenderJobs`, `spoil_maker.voices.SentenceVoicer` ถือตัวนี้ ไม่สืบทอด
- งานแต่ละ kind เป็น `steps.Work` ใน module ของตัวเอง: `toon/plot.py`, `toon/cards.py`, `toon/refs.py`, `toon/images.py` (Image job), `toon/voicing.py` (Voice job); `toon/jobs.py` เหลือ slot (~160 บรรทัด) ที่ทำขั้น 1 ของทุก kind แบบเดียวกันจาก `WORKS`; `toon/steps.py`: `Child`, `Run`, `Qwen` (ถาม Qwen สามครั้ง), `scenes`, child ของ klein, `image_rows`
- `toon/kinds.py`: ตาราง `KINDS` (model, ตัวนำหน้า id, `tagged`, `sizes`, `upload_side`, แม่แบบภาพ, `scene_ask`) และ `CARD_SIZE`; ไม่เหลือกิ่ง `kind == "characters"` ใน `toon/`
- ทุก kind เริ่มใต้ `store.lock` (slot ถือเอง; Voice job `draft_lock` ก่อน); ลบ Series อ่าน `series.series_jobs` แทน `ToonJobs.delete_series`; route เรียก `series.delete`
- `kind` ที่ไม่ใช่ string (list, dict) → `400` `invalid_request` เหมือนเดิม (ไม่ใช่ 500)
- test: ยกเลิกระหว่าง render `voicing` ปิด OmniVoice และเก็บเสียงที่พูดจบ, ลบ Series ระหว่าง Image job `series_busy`, `kind` ที่ไม่รู้จัก; test ของ images patch `series.disk`, `images.shutil` ตรง
- spec › Modules touched, `fastapi-api` SKILL.md (toon, speaking)

**Decided:**
- D58 — ตัวพูดที่ slot ถือ, `SentenceVoicer` คงเป็นฐานของ spoil-maker, `Work` ต่อ kind, ตาราง `KINDS`, งานเริ่มใต้ `store.lock`, `series_jobs`

**For the next ticket:**
- smell ที่ review เห็นแต่ไม่แก้ใน ticket นี้: `cards.run` สร้างตัวละครและฉากหลังใหม่เอง (ควรอยู่ `series`); `plot.writable` อ่าน `render.render_jobs.ep_use()` ตรง (D57) แทน `episodes.ep_jobs`; `process, requests, replies` เดินด้วยกันทุกที่ (Data Clump); `ToonJobs.update`/`track`/`reply` แค่ส่งต่อ (Middle Man เพื่อ `steps.Run`) และ `use()` เขียนทับค่าของ `ModelJobSlot`; เปิด klein (`Encode` แล้ว `Draw` ทีละใบ) ซ้ำใน `refs.run` กับ `images.run`; `_running`/`series_use` ซ้ำระหว่าง `ToonJobs` กับ `RenderJobs`
- `series_busy` ของ Plot, Cards, Voice job ยังไม่มี test (Ref, Image, render มี)
- ruff (ไม่อยู่ใน CI) เตือนของเดิม: `Callable` ไม่ใช้ใน `toon/sounds.py`

**Checks:** `uv run pytest` 1032 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 398 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `d7e2969`: Standards ไม่มีข้อผิดกติกา + smell (แก้ `upload_side`, ลูปลองใหม่ของ Plot/Cards, ชื่อ `WritePlan` `_pictures_dir` `log_name` `scene_ask`, `Work.locks` มีค่าตั้งต้น), Spec 1 bug (`kind` list → 500, แก้) + test ยกเลิกระหว่างพูดที่ขาด (เพิ่ม), Newcomer สรุปตรง What to build; แก้ชื่อ `Work.steps` → `run`, `steps.Writer` → `Qwen`, คอมเมนต์ `Work.child`, `store.lock` บังคับใน slot

### Feature review — done 2026-11-10

**Built:**
- Plot job และ Cards job บน EP ที่ Render job ยังไม่จบเป็น `409` `ep_busy` (D57): ก่อนนี้ Cards job เริ่มได้หลัง render คืนช่อง GPU และล็อก EP ระหว่าง render
- `uploads.UploadCheck` และ `uploads.require_size` ที่ภาพอ้างอิงกับ Sound import ใช้ร่วม; `features/toon/lib/notice.ts` (`noticeOf`, `refusalTextOf`, `NOT_NOW`) แทนบรรทัดแปลง refusal ที่เขียนซ้ำ 5 hook; `prompts.parse_scene` ใช้ `llm_reply.json_object`; `episodes.ep_cards` ตัวเดียว
- test: เสียงพื้นอยู่หลังลบ Series (seam 1), ฉากหลังที่ช่วงใช้ลบไม่ได้ `in_use` (D25), Cards job ระหว่าง render; spec › Modules touched ตรงกับโค้ด

**Decided:**
- D57 — Plot/Cards job บน EP ที่กำลัง render → `ep_busy`

**For the next ticket:**
- ไม่ได้แก้ (ตั้งใจ): แก้การ์ดระหว่าง `voicing` ทำให้ render ล้ม `internal` พร้อมข้อความ "EP เปลี่ยนระหว่าง render: กด render ใหม่" (อยู่ในรายการ code ของ spec); ไฟกะพริบเป็นสอง sine (D56); `fallback_scene` บอกแค่ "character 1"; ไฟล์ Q8_0 ค้างใน `models/hub`
- smell ใหญ่ → Blocked #13–18

**Checks:** `uv run pytest` 1026 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 398 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). Review สามแกนจาก `912c7c4`: Standards 2 ข้อ + smell, Spec 7 (หนักสุด EP lock กับ render), Newcomer 10 (ชื่อ `frames`, `_cards` สองตัว, `timeouts().pick`, ข้อความ `TRANSLATOR`)

### 04: คลังเสียงพื้นและ render — done 2026-11-10

**Built:**
- backend: `toon/sounds.py` (คลังเสียงพื้น: รายการ แก้ชื่อ ลบ `in_use` พร้อม `eps`, ไฟล์ m4a; Sound import slot: ไฟล์เป็น request เดียว `check` + body ดิบ, ลิงก์เป็นงาน `checking`/`downloading`/`converting` ผ่าน adapter ของ spoil ด้วย `LINK_OPTIONS`; ffmpeg แปลงเป็น aac 192k 48 kHz stereo, `unsupported_file`, `too_long`, `file_too_large`), `toon/render.py` (Render job slot ของตัวเอง, `voicing` ผ่าน `speaking.Speaker` แล้วคืน GPU, `rendering` อ่าน EP ครั้งเดียวและ copy ลง `.render/`, ผล `renders/{name}.mp4|.srt|.json`, รายการ ไฟล์ ลบ, `ep_use` ใน `episodes.ep_jobs`, `series_busy`, start ใหม่ล้าง `.render/` และ `.partial`), `toon/compose.py` (timeline เป็นเฟรม, piece ต่อการ์ด `zoompan`/`eq`/layout, `xfade` 0.3 วิ, ท่อนเสียงพื้น `-stream_loop` + `acrossfade` 1 วิ, `amix normalize=0`, ASS: ชื่อตอน ≤ 2 บรรทัด ป้าย `EP{n:02}` ชื่อช่อง ซับทีละท่อน ป้ายชื่อการ์ดแรก)
- `YtDlpAdapter.download`/`fetch_info` รับ `DownloadOptions` (ค่าตั้งต้นของ Temp clip); `gpu.Kind` มี `toon_render`; `JOB_HOLDERS` มี Render job และ Sound import; `ListedEp.rendered_at`; `ProjectPaths.ep_renders_dir`, `toon_sounds_dir`, `toon_render_dir`; `spoil_maker.captions` เปิด `chunks`, `split_time`, `cut_lines`, `event`, `ass_time`; `voicing.ep_voice`, `plan_card`
- หน้าเว็บ: `#/toon/sounds` (คำเตือน legal ข้อ 4, เอาไฟล์เข้าพร้อม %, ลิงก์พร้อม % และยกเลิก, แถวเสียง แก้ชื่อ ฟัง ลบ, `useLeaveGuard` ระหว่างส่งไฟล์), `#/toon/eps/{eid}/render` (สรุป EP, render, banner `voicing`/`rendering` %, การ์ดที่ยังไม่มีภาพพร้อมลิงก์, รายการคลิป เล่น ดาวน์โหลด ลบ); ปุ่ม "คลังเสียงพื้น" บนรายการ Series และ toolbar เส้นเรื่อง, "ไปหน้า render"; หัวช่วงมีเสียงพื้นและ slider ความดัง; `GPU_JOB_PATHS` มี `toon_voice`, `toon_render`; icon จาก Figma (`download`, `download-white`, `film-white`, `arrow-right`, `volume`)
- test: `backend/tests/test_toon_sounds_api.py` (14), `test_toon_render_api.py` (14, render จริงด้วย ffmpeg), `SoundsRender.test.tsx` (11, e2e 2)

**Decided:**
- D56 — Sound import ไฟล์ request เดียว ลิงก์เป็นงาน, `DownloadOptions`, `in_use` ของเสียง, `-stream_loop` แทน `aloop`, ไฟกะพริบสอง sine, ขนาดตัวหนังสือจาก layout A, หน้า `#/toon/sounds` และ `/render`

**For the next ticket:**
- feature review: เช็คมือบน Mac ของ 04 (Blocked #12) ยังไม่ทำ; ขนาดและตำแหน่งตัวหนังสือในคลิปเป็นค่าตั้งต้นจาก layout A (D56) รอผลเช็คมือ
- review ไม่ได้แก้: ไฟล์เสียงที่หน้าเว็บหายไประหว่างแปลง ffmpeg ยังแปลงจนจบและเข้าคลัง (ส่ง `threading.Event()` ใหม่ให้ `_take_in`); test adapter เรียก `_params` ตรง; `DELETE …/renders/{name}` มี `409` `in_use` แบบ spoil-maker ที่ spec ไม่ได้เขียน
- smell ที่ค้าง: `RenderJobs` สืบทอด `speaking.Speaker` เพื่อใช้ `_speak` แบบ `ToonJobs`; `toon.render` กับ `spoil_maker.render` มี `_free_name`, `_needed_rows`, การลบผลคล้ายกัน; `episodes.list_for` import `render` ในฟังก์ชัน (วนกัน)
- ของค้างจาก 01–03 ยังค้าง (`GENRE_DEFAULTS`, `useCast` / `usePickRef` poll ซ้ำ, ตารางต่อ kind, ปุ่ม "ฟัง" ไม่มี test)

**Checks:** `uv run pytest` 1024 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 398 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). e2e = Vitest ผ่าน `App`. Review สามแกน: แก้ icon ซ้ำ (`download.svg` ย้ายไป `components/ui/assets`), ส่วนกลางของซับย้ายเป็น `backend/subtitles.py`, `is_int`, `noticeOf`/`NOT_NOW`, `cardsOf`/`cannotRender`, test ยกเลิกช่วง encode สุดท้าย, test ชื่อตอนยาวผ่าน ASS จริง, spec บรรทัด `aloop` → D56. เช็คมือบน Mac ยังไม่ได้ทำ → Blocked #12

### 03: ภาพการ์ดและเสียงเล่า — done 2026-11-10

**Built:**
- ย้ายก่อน: ลูปสร้างเสียงทีละข้อความเป็น `backend/speaking.py` (`Speaker._speak`, `write_wav`, `wav_seconds`, `NUM_STEP`) ที่ spoil-maker (`SentenceVoicer`) และ Toon job ใช้ร่วม; `voices.saved_voice` / `SavedVoice` (speed + clone prompt)
- backend: `toon/images.py` (แผนของ Image job: การ์ดเดียวหรือ `scope` `missing` / `stale_ref`, `skipped`, `missing_refs`, `no_ref`, `nothing_to_draw`; copy ภาพอ้างอิงลง `.image-job/`; เขียนภาพทีละใบพร้อมภาพก่อนหน้าและลบภาพก่อนหน้าเดิม; ทิ้งภาพของการ์ดที่หายระหว่างงาน; `swap-image`; ไฟล์ภาพ; start ใหม่ลบ `.image-job/` และ PNG ที่ไม่มี `ep.json` อ้าง), `toon/voicing.py` (Voice job การ์ดเดียว, `silent_card`, wav, `audio`), `ToonJobs` มี `image` (Qwen แปลทุกการ์ดก่อน แล้ว klein encode ทั้งงานและวาดทีละใบ, `failed_cards`) และ `voice` (`toon_voice` "สร้างเสียงเล่า"); `prompts` มีแม่แบบภาพการ์ด ค่าสำรอง และคำสั่งแปลคำบรรยาย; klein ตอบ `WorkerError` ที่ `Draw` แล้วรอภาพถัดไป; `_reply` คืน worker error ที่ขอไว้; `ProjectPaths.image_job_dir`, `card_images_dir`, `card_audio_dir`; การ์ดใน `GET` EP มี `has_image`
- หน้าเว็บ (เส้นเรื่อง): ปุ่ม "สร้างภาพที่ขาดทั้งหมด" และ "สร้างภาพใหม่การ์ดที่ภาพอ้างอิงเปลี่ยน", banner ของ Image/Voice job (นับ ข้าม หยุด ลองอีกครั้ง), กล่อง "ต้องสร้างภาพอ้างอิงก่อน" พร้อมลิงก์ไปหน้าตัวละคร, ภาพการ์ด (กำลังวาด…, สร้างภาพใหม่, สลับภาพก่อนหน้า), แถวเสียงเล่า (สร้างเสียง / ฟัง / สร้างใหม่ / เสียงเก่า); ระหว่าง Image job ที่ `done` เพิ่มอ่าน EP ใหม่ให้ภาพขึ้น; icon จาก Figma (`undo`, `mic`, `mic-dark`, `play`, `triangle-alert`, `chevron-right-16`, `users-16`, `mountain-16`)
- test: `backend/tests/test_toon_images_api.py` (23), `EpPage.test.tsx` เพิ่ม 5 (2 e2e ของ ticket)

**Decided:**
- D55 — `card_ids` กับ `scope` ใน Toon job, ขอบเขตตามภาพ, `silent_card`, klein ล้มหนึ่งภาพแล้วรอภาพถัดไป, `has_image`, `?v=` ของภาพ, ลูปเสียงกลางใน `backend/speaking.py`, ปุ่มคลังเสียงพื้นและ render รอ 04

**For the next ticket:**
- ticket 04: Render job สร้างเสียงที่ขาดด้วย `speaking.Speaker._speak` และ `voicing.put_audio` ได้เลย; ปุ่ม "คลังเสียงพื้น" และ "ไปหน้า render" บน toolbar ของเส้นเรื่องยังไม่มี (แบบมี); `icon/arrow-right` ของปุ่ม render ต้องโหลดจาก Figma
- smell ที่ไม่ได้แก้: `ToonJobs` สืบทอด `speaking.Speaker` เพื่อใช้ `_speak` (composition จะตรงกว่า); การแตกกิ่งตาม `job.kind` ใน `EpPage` (`FAILED_TITLES`, `runningText`, `retry`) และ `ToonJobs.start`
- ปุ่ม "ฟัง" ใช้ `new Audio(src).play()` ไม่มี test; หน้าตาเทียบ Figma ด้วยมือยังไม่ได้ทำ
- ของค้างจาก 01–02 ยังค้าง (`GENRE_DEFAULTS`, `useCast` / `usePickRef` poll ซ้ำ, ตารางต่อ kind)

**Checks:** `uv run pytest` 996 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 387 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). e2e = Vitest ผ่าน `App`. เช็คมือบน Mac M1 ยังไม่ได้ทำ: เครื่องนี้ยังไม่ได้รัน setup (ไม่มี Qwen, OmniVoice, marker) → Blocked #11

### 02: EP, พล็อต และเส้นเรื่อง — done 2026-11-10

**Built:**
- backend: `toon/episodes.py` (EP สร้าง แก้ ลบ, เลข EP ตาม `max_ep` D40, `invalid_ep_number`, องก์ ช่วง การ์ด, สถานะภาพ เสียง ความยาวต่อการ์ดและรวม, `ep_locked` / `ep_busy` ผ่าน `ep_jobs`, `in_use` ของตัวละครและฉากหลังที่การ์ดหรือ `plot` ใช้, `voice_in_use` ของ EP), `toon/writer.py` (คำสั่งและการอ่านคำตอบของ Plot job กับ Cards job), `ToonJobs` มี `plot` และ `cards` บน `toon_write` ("ร่างการ์ตูนเล่า"); Cards job เขียน Series กับ `ep.json` พร้อมกันตอนจบ (ยกเลิกหรือ crash แล้วไม่เปลี่ยน), แตกใหม่เฉพาะองก์ที่ `summary` ≠ `cards_from`, `cards_will_be_lost` ต่อองก์, `nothing_to_split`
- `backend/llm_reply.py` ใหม่: `json_object` และ `clean` ย้ายจาก `spoil_maker.script` (ผู้ใช้คนที่สองคือ `toon.writer`); `store.ep_ids` ให้ id ของ EP ไม่ซ้ำทั้ง tab
- หน้าเว็บ: รายการ EP (`#/toon/series/{sid}`, EP ใหม่ส่ง Plot job ทันที), ตัวละครย้ายไป `/cast`, หน้า EP (`#/toon/eps/{eid}`, `/plot`): พล็อต (ชื่อตอน สรุปต่อองก์ ป้าย "ใหม่" สลับเป็นของใน Series, องก์ที่จะแตกใหม่, dialog ของที่จะหาย), เส้นเรื่อง (องก์ แก้ชื่อที่หัวองก์, ช่วงพร้อมฉากหลัง, `CardEditor`, `LengthMeter` เทียบเป้า 60–120), ช่องแก้ปิดระหว่าง Plot/Cards job ของ EP; `NoticeLine` เป็น component ของตัวเอง
- test: `backend/tests/test_toon_eps_api.py` (33), `features/toon/components/EpPage.test.tsx`

**Decided:**
- D53 — hash ใหม่ (`/cast`, `/eps/{eid}`, `/plot`), EP ใหม่เริ่ม Plot job ทันที, `PATCH` องก์, Cards job เขียนตอนจบ, ขีดจำกัดข้อความ, ค่าตั้งต้นของช่วงใหม่
- D54 — พล็อตที่ยืนยันแล้วไม่รับของใหม่ (`invalid_request`), id ของ EP ไม่ซ้ำทั้ง tab, ชื่อองก์แก้ที่หัวองก์

**For the next ticket:**
- ticket 03: การ์ดมี `has_previous_image` และ `previous_image` รอแล้ว; ภาพการ์ด ปุ่มเสียงเล่า และสถานะบน `CardEditor` ยังไม่ขึ้น (D53)
- ticket 04: `PATCH` ช่วง `sound` / `volume` (`episodes._sound`) และ `ListedEp.rendered_at` มีแล้วแต่หน้าเว็บยังไม่ใช้; Render slot ต้องเพิ่มตัวเองใน `episodes.ep_jobs` (ตอนนี้มีแค่ `toon_jobs.ep_use`)
- smell ที่ไม่ได้แก้: `writer._plot_items` (อ่านคำตอบ Qwen แบบทิ้งของเสีย) กับ `episodes._plot_items` (API ปฏิเสธ) คล้ายกันแต่กติกาต่างกัน; แตกกิ่ง `characters` / `backgrounds` เพิ่มใน `_cards`, `_plot_items` — รวมเป็นตารางต่อ kind พร้อมที่ ticket 01 บอกไว้
- test backend บางตัวผูกกับถ้อยคำในคำสั่ง (`Writer.respond` แยกด้วย "เขียนพล็อต" และ "องก์นี้ ("); `edit_stored` เขียน `ep.json` ตรงเพื่อใส่ภาพและเสียง จนกว่า ticket 03 จะมี API
- `GENRE_DEFAULTS` ซ้ำ `DEFAULTS`, `lib/voices.ts` และ smell ของ `useCast` / `usePickRef` จาก ticket 01 ยังค้าง; `useEp` poll `JOB_PATH` เป็นตัวที่สาม → ticket 03 รวมเป็น hook เดียว

**Checks:** `uv run pytest` 973 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 382 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). e2e = Vitest ผ่าน `App`; หน้าตาเทียบ Figma ด้วยมือยังไม่ได้ทำ

### 01: ติดตั้ง klein, Series และภาพอ้างอิง — done 2026-11-10

**Built:**
- tab ที่ห้า "การ์ตูนเล่า" (`#/toon/…`, `ToonPage` เลือกหน้าจาก `pageOf`): รายการ Series (ว่าง, กำลังโหลด, ลบพร้อมยืนยันจำนวน EP, `series_busy`), ตั้งค่า Series (สร้างและแก้, แนวเติมสไตล์ น้ำเสียง โครงองก์, แบบจอล็อกหลังสร้าง, ไม่มี Saved voice → ลิงก์ `#/spoil/voices`), ตัวละครและฉากหลัง (เพิ่ม ลบ, tile ทุกสถานะ, Ref job banner, upload พร้อม %, คำเตือน legal ข้อ 2 ก่อนเลือกไฟล์ตัวละคร, `gpu_busy` / `not_ready` เป็น Alert), เลือกภาพอ้างอิง (ติดตามงาน, เลือก 1 ใน 3, ล้ม / หยุด / ลองอีกครั้ง)
- `GPU_JOB_PATHS` และ `RUNNING_NAMES` มี `toon_image`; `Alert` มี `title`; icon ที่สอง feature ใช้ (`chevron-down`, `radio-selected`, `plus-white`) ย้ายไป `components/ui/assets`
- backend: `POST /series` รับ `style`, `tone`, `acts` (กติกาเดียวกับ `PATCH`, D52)
- test: `features/toon/components/ToonPage.test.tsx` (16, ผ่าน `App` กับ `testBackend`), backend test ใหม่ 1

**Decided:**
- D52 — hash ของหน้า tab, `POST /series` ส่งครั้งเดียว, Ref job ล้มหรือหยุดไม่มีภาพให้เลือก, ปุ่มคลังเสียงพื้นรอ 04, ลบตัวละครไม่ถามก่อน

**For the next ticket:**
- ticket 02: `#/toon/series/{sid}` เป็นรายการ EP ตามแบบ → ย้ายหน้าตัวละครและฉากหลังไป hash ใหม่ (เช่น `/cast`) และปุ่ม "กลับไปที่ชุด" ชี้รายการ EP; ลิงก์ "ตั้งค่า Series" บนหน้า cast ย้ายตามแบบรายการ EP
- ticket 04: ปุ่ม "คลังเสียงพื้น" บนรายการ Series (`assets/music.svg` เตรียมไว้แล้ว)
- `GENRE_DEFAULTS` (frontend) ซ้ำ `DEFAULTS` (backend) ไม่มี test เทียบ: เปลี่ยนที่หนึ่งต้องเปลี่ยนอีกที่
- shared ใหม่: `lib/voices.ts` (`VOICES_PATH`, `SavedVoice`) แทนค่าที่ซ้ำใน spoil-maker
- build มีคำเตือน chunk > 500 kB ของ Vite (ไม่ใช่ error)
- review ไม่ได้แก้ (smell): `useCast` กับ `usePickRef` ซ้ำ `update` และการ poll `JOB_PATH` — ถ้า ticket 03 เพิ่ม hook ที่ poll Toon job อีก ให้รวมเป็น hook เดียว; `(sid, kind, id)` เดินด้วยกันหลายที่ (อาจเป็น type `ItemRef`)

**Checks:** `uv run pytest` 940 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 371 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). e2e ตาม testing rules = Vitest ผ่าน `App`; หน้าตาเทียบ Figma ด้วยมือยังไม่ได้ทำ

### design — 2026-11-10

- แบบ 9 จอจาก Figma (Blocked #1–9 done); spec › Design Source เป็นลิงก์ section ของแต่ละจอ; `ui-prompt.md` ลบ; spec › Design ไม่มีจอ `pending`

### 01: ติดตั้ง klein, Series และภาพอ้างอิง — stopped 2026-11-09 (รอบ 2)

**Done:** ทุกกลุ่มยกเว้นหน้าเว็บ; โค้ดจาก `wip/toon-01` เข้า `feat/toon` แล้ว (`wip/toon-01` ไม่ใช้อีก)
- ลด memory ตาม D49 → ใช้ขั้น 3: transformer Q4_K_M + ภาพอ้างอิง ≤ 512 + `empty_cache` หลังทุกภาพ (D51); `allow_patterns`, `GGUF_FILE`, ที่ว่าง 32/42/27 GB, spec, `NOTICE.md`
- Status check: marker ของ Q8_0 กับ spec Q4_K_M → `model_klein_gguf` `missing` (D50); setup ตรวจทุก pattern ที่ระบุไฟล์หรือ folder หลังโหลดด้วยกฎเดียวกัน
- Ref job และเอาไฟล์เข้า: test ครบกลุ่มใน `backend/tests/test_toon_ref_api.py` (translating → drawing 3/3, `pending` 3, `busy`, `gpu_busy`, `not_ready`, ทุกทางออกคืน GPU, pick, `no_pending`, upload, start ใหม่ล้าง `.pending`, shutdown หยุด process ลูก); `FakeKlein` ใน `fakes.py`
- review: ลำดับเช็ค `busy` → `gpu_busy` → `disk_full`; ลบ Series กับเริ่มงานไม่แข่งกันแล้ว (`ToonJobs.delete_series` ถือ lock ของ slot); `RefPlan` อยู่ใน `series`; upload ใช้ไฟล์ `.partial` ต่อ request; `check` ตอบเป็น model; `json_values` ย้ายเป็น `backend/json_values.py` (ผู้ใช้คนที่สอง); SKILL.md มี `toon/`, `uploads.py`, adapter ของ diffusers, ลำดับ lock ของ `toon.store.lock`; ADR-0028 มี route upload ของ toon

**Left:** กลุ่มหน้าเว็บ (รอแบบ: Blocked #1–4)

**ลองจริง D49** (Mac M1 16 GB, torch 2.8.0, กรณีหนักสุด 576×1024 + 3 ภาพอ้างอิง, 5 ภาพต่อ process, seed และคำสั่งตายตัว, ผ่าน `backend.toon.klein` จริง; ปิดแอปอื่นไม่ได้: swap 4–7 GB ก่อนเริ่มทุกรอบ)

| ขั้น | รอบ | peak MPS ภาพ 1–5 | เวลา/ภาพ | swap ก่อน → peak |
|---|---|---|---|---|
| 1: Q8_0 + ref 512 + `empty_cache` | 1 | 13.08 ทุกภาพ | 185–236 วิ | 4.3 → 10.7 GB |
| 2: Q6_K + ref 512 + `empty_cache` | 1 (2 ภาพ) | 12.88, 12.88 | 197–199 วิ | 5.7 → 8.4 GB |
| 3: Q4_K_M + ref 512 + `empty_cache` | 1 | 11.83 ทุกภาพ | 192–197 วิ | 6.4 → 7.6 GB |
| 3 | 2 | 11.83 ทุกภาพ | 194–201 วิ | 6.5 → 7.6 GB |
| 3 | 3 | 11.83 ทุกภาพ | 194–198 วิ | 6.8 → 7.1 GB |

- ขั้น 1 และ 2 เกิน 12 GB ตั้งแต่ภาพแรก จึงหยุดที่รอบเดียว; ขั้น 3 ผ่านทั้ง 3 รอบ และภาพ 3–5 ไม่สูงกว่าภาพ 2
- encode 1 คำสั่ง 19–33 วิ peak 9.4–9.8 GB; โหลด transformer + vae 5–11 วิ
- วัดแยกของขั้น 1 ไม่ครบ: Q8_0 + ref 768 + `empty_cache` thrash (swap 11 GB, 10 นาทีต่อ step) จึงหยุด; เทียบกับรอบก่อนแทน: ref 768 ไม่มี `empty_cache` ได้ 13.09 → 13.98 GB (ไต่ขึ้นภาพที่ 2) ส่วน ref 512 + `empty_cache` ได้ 13.08 คงที่ → `empty_cache` ตัดการไต่, ขนาดภาพอ้างอิงแทบไม่มีผลต่อ peak
- **คงตัวละคร 10 ภาพ (Q4_K_M, ref 1 ภาพ):** ✅ ผมดำ หัวกลม ตาจุด เสื้อโปโลกรมท่าปกดำ กางเกงดำ ครบทุกภาพ ไม่มีหน้าบิดหรือตัวซ้ำ ([consistency-10-q4km.png](../../features/toon/trial-images/consistency-10-q4km.png)); peak 10.6–11.2 GB, 142–145 วิ/ภาพ
- **ไทยตรงเข้า klein (ข้อมูลให้ D36):** ได้ภาพรวมถูก (ผู้ชายข้างกองไฟ, ผู้หญิงตกใจหน้าห้องน้ำแสงฟ้า, เด็กวิ่งตอนกลางคืนป้ายเขียว) แต่รายละเอียดหลุด: เสื้อฮาวายเป็นเสื้อยืด, ทางเดินโรงเรียนเป็นถนนนอกอาคาร, สไตล์หัวกลมตาจุดไม่ติด, ป้ายเป็นตัวหนังสือมั่ว → ยืนยัน D36 (Qwen แปลก่อน); 119–121 วิ/ภาพ 1024×576

**Decided:**
- D50 — Status check และ setup เทียบ pattern ที่ระบุไฟล์หรือ folder กับไฟล์จริง; pattern ชนิดไฟล์ไม่เทียบ
- D51 — transformer Q4_K_M (ขั้น 3 ของ D49), ที่ว่าง 32/42/27 GB

**For the next ticket:**
- `series.delete_item` ยังไม่มี `409` `in_use` ของ D25 (การ์ดหรือ `plot` ของ EP อ้างอยู่): ticket 02 สร้าง EP และ `plot` ต้องเพิ่มพร้อม test
- เครื่องที่โหลด Q8_0 ไว้ setup โหลด Q4_K_M ใหม่ แต่ไฟล์ Q8_0 (4.3 GB) ค้างใน `models/hub`; ยังไม่มีอะไรลบ
- smell จาก review ที่ไม่ได้แก้: ตัวละคร/ฉากหลังแตกกิ่ง `kind == "characters"` หลายที่ (`add_item`, `change_item`, `picture_size`, `_take_upload`, `prompts`) — ถ้า Image job เพิ่มอีกที่ ให้รวมเป็นตารางต่อ kind; แถว `diffusers`/`gguf` เขียนทั้งใน `checks.run_checks` และ `gate_rows.klein`
- ภาพการ์ดกับ 3 ภาพอ้างอิง 576×1024 ใช้ ~195 วิ/ภาพบน M1 (ref 1 ภาพ ~143 วิ, ไม่มี ref ~120 วิ): ใช้ตั้งความคาดหวังของ "สร้างภาพที่ขาดทั้งหมด"

**Checks:** `uv run pytest` 938 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 355 passed (รอบหนึ่งระหว่าง klein รัน `DraftProgress.test.tsx` ตก 1 เพราะเครื่องโหลดหนัก, รันซ้ำผ่าน; ticket ไม่แตะ frontend); `npm --prefix frontend run build` ผ่าน

### 01: ติดตั้ง klein, Series และภาพอ้างอิง — stopped 2026-11-09

**Done:** (โค้ดอยู่บน `wip/toon-01`, test backend 897 ผ่าน)
- ติดตั้งและ Status check: `KLEIN` และ `KLEIN_GGUF` ใน `MODELS` (GGUF pin `a09d5bb51ac4000ccd9643d10e9db3ed14200508`), setup ตรวจทุก folder ใน `allow_patterns` หลังโหลด, ที่ว่างที่ต้องการ 33/43/28 GB, แถว `model_klein` `model_klein_gguf` `diffusers` `gguf` ต่อจาก `font_kanit`, `NOTICE.md`
- Series ตัวละคร ฉากหลัง: สร้าง แก้ ลบ (`confirm_needed`, `series_busy`), `voice_in_use` ของ Series, ข้าม `series.json` ที่อ่านไม่ได้; test ใน `backend/tests/test_toon_series_api.py`
- เริ่มแล้วแต่ยังไม่มี test: Ref job (`backend/toon/jobs.py`), worker ของ klein (`backend/toon/klein.py`), pick และ upload ภาพอ้างอิง

**Left:** กลุ่ม Ref job และเอาไฟล์เข้า (test ทั้งกลุ่ม), กลุ่มหน้าเว็บ (รอแบบ: Blocked #1–4)

**ลองจริง (Open Question 1):** Mac M1 16 GB, torch 2.8.0, diffusers 0.42.1, gguf 0.19.0, GGUF Q8_0, 4 steps

| ขั้น | เวลา | peak MPS | peak ทั้งระบบ | swap |
|---|---|---|---|---|
| โหลด text encoder | 9.7 วิ | — | — | — |
| encode 4 prompt | 9.3 วิ/prompt | 9.77 GB | 15.58 GB | — |
| โหลด transformer GGUF + vae | 11.2 วิ | — | — | — |
| ภาพ 576×1024, 3 ภาพอ้างอิง (รอบ 1) | 178 วิ | **13.09 GB** | 16.41 GB | 5.37 → 9.27 GB |
| ภาพ 576×1024, 3 ภาพอ้างอิง (รอบ 2) | 231 วิ | **13.98 GB** | 16.34 GB | → 10.96 GB |

- peak MPS ของ klein อย่างเดียวเกิน ~12 GB ของ D34 ทั้งสองรอบ และเครื่อง swap จริง; ตัวเลขทั้งระบบรวมแอปอื่นที่เปิดอยู่ (swap 5.4 GB ก่อนเริ่ม และ pytest รันช่วงรอบ 2) แต่ MPS เป็นของ klein เอง
- เทียบผลลองเดิม (torch 2.15, 1024×576, 1 ภาพอ้างอิง): 11.2 GB; กรณี 3 ภาพอ้างอิงกับภาพแนวตั้งไม่เคยวัดมาก่อน
- ภาพไทยตรงเข้า klein (ข้อมูลให้ D36): รอบนี้ยังไม่ได้ผล ไปลองต่อพร้อมทางแก้ใน `/warroom toon`
- สคริปต์ลองอยู่นอก repo; ขั้นตอนเหมือน `backend/toon/klein.py` (encode แยก, `device_map`, `no_grad`, `config=` ของ transformer ในเครื่อง)

**Decided:**
- D47 — gguf pin 0.19.0 แทน 0.10.0 ที่อ่าน GGUF ไม่ได้บน numpy 2
- D48 — ค่าเล็กของ Series และ Ref job (ความยาว style/tone, `file_too_large`, `item_id`, ค่าสำรองของคำแปล, `backend/uploads.py`)

**For the next ticket:**
- `backend/uploads.py` คือการรับ body ดิบที่ spoil import และ upload ภาพอ้างอิงใช้ร่วมกัน; Sound import ของ ticket 04 ใช้ตัวนี้
- `gate_rows.klein(project)` เป็นฟังก์ชัน (ต้องใช้ project) ไม่ใช่ค่าคงที่ `gate_rows.KLEIN` ตามที่ spec เขียน

**Checks:** `uv run pytest` 897 passed บน `wip/toon-01`; frontend ไม่ได้แตะ

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: รายการ Series (หน้าแรกของ tab) | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8121-65674)) |
| 2 | 01 | design: ตั้งค่า Series | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8122-66685)) |
| 3 | 01 | design: ตัวละครและฉากหลัง | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8123-68692)) |
| 4 | 01 | design: เลือกภาพอ้างอิง | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8124-70163)) |
| 5 | 02 | design: รายการ EP ใน Series | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8126-71235)) |
| 6 | 02 | design: พล็อต | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8127-72204)) |
| 7 | 02 | design: เส้นเรื่อง (การ์ด) | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8128-76737)) |
| 8 | 04 | design: คลังเสียงพื้น | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8129-80163)) |
| 9 | 04 | design: render และผล | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8130-81152)) |
| 10 | 01 | klein บน torch 2.8.0 กรณีหนักสุด (GGUF Q8_0, 3 ภาพอ้างอิง, 576×1024) peak MPS 13.1–14.0 GB เกิน ~12 GB ของ D34 และ swap; ต้องเลือก: ภาพอ้างอิงเล็กลง, GGUF ที่เล็กกว่า (Q6_K/Q4_K_M), ภาพอ้างอิงสูงสุดน้อยลง, torch รุ่นใหม่ หรือยอมรับ | `/warroom toon` | done (this ticket, D51) |
| 11 | 03 | เช็คมือบน Mac M1 16 GB: Image job `scope: missing` ~20 การ์ด 3 ภาพอ้างอิง (peak ทั้งระบบ ≤ ~12 GB ไม่ swap, จดเวลาต่อภาพ), หน้าตัวละครใน ~5 การ์ดของ EP แรกและ EP ที่สอง, ปิด backend กลาง "สร้างภาพที่ขาดทั้งหมด" แล้วเปิดใหม่; เครื่องที่ build ยังไม่ได้รัน setup (ไม่มี Qwen, OmniVoice) | owner รัน `./setup.sh` แล้วทำตามรายการใน ticket 03 › เช็คมือ และจดผลใน `progress.md` | open |
| 12 | 04 | เช็คมือบน Mac: render EP แรกของ Series หลอนแบบกรอบดำ ดูด้วยตาว่าตำแหน่งชื่อตอน ภาพ ซับ ชื่อช่อง ตรง layout-sketch และขนาดตัวหนังสือ (ค่าจาก layout A, D56) | owner รัน `./setup.sh` แล้ว render EP จริง และจดผลใน `progress.md` | open |
| 13 | review | `ToonJobs` และ `RenderJobs` สืบทอด `speaking.Speaker` เพื่อใช้ `_speak` (Refused Bequest): เปลี่ยนเป็น composition | `/warroom tickets toon` | done (ticket 05) |
| 14 | review | `toon/jobs.py` 608 บรรทัดทำหลายเรื่อง (Plot, Cards, Ref, Image, Voice, child ของ klein, `delete_series`, `image_rows`); แตกกิ่ง `kind == "characters"` 22 ที่ใน `toon/`: แยก module และตารางต่อ kind | `/warroom tickets toon` | done (ticket 05) |
| 15 | review | `toon.render` กับ `spoil_maker.render` ซ้ำ `_free_name`, `_needed_rows`, การลบผล; `episodes.list_for` import `render` ในฟังก์ชัน (วนกัน) | `/warroom tickets toon` | done (ticket 06) |
| 16 | review | หน้าเว็บ: poll `JOB_PATH` ซ้ำ 3 hook (`useCast`, `usePickRef`, `useEp`) ควรเป็น hook เดียว; `GENRE_DEFAULTS` ซ้ำ `DEFAULTS` ของ backend ไม่มี test เทียบ; ปุ่ม "ฟัง" ไม่มี test | `/warroom tickets toon` | done (ticket 06) |
| 17 | review | แถว `diffusers`/`gguf` เขียนทั้งใน `checks.run_checks` และ `gate_rows.klein` | `/warroom tickets toon` | done (ticket 06) |
| 18 | review | ไฟล์เสียงที่หน้าเว็บหายไประหว่างแปลง ffmpeg ยังแปลงจนจบและเข้าคลัง (`_take_in` ได้ `threading.Event()` ใหม่); `DELETE …/renders/{name}` มี `409` `in_use` ที่ spec ไม่ได้เขียน | `/warroom tickets toon` | done (ticket 06) |
| 19 | review | smell ที่ค้างจาก 05: `cards.run` สร้างตัวละครและฉากหลังใหม่เอง (ควรอยู่ `series`); `plot.writable` อ่าน `render.render_jobs.ep_use()` ตรงแทน `episodes.ep_jobs`; `process, requests, replies` เดินด้วยกัน (Data Clump); `ToonJobs.update`/`track`/`reply` แค่ส่งต่อ (Middle Man); เปิด klein (`Encode` แล้ว `Draw`) ซ้ำใน `refs.run` กับ `images.run`; `_running`/`series_use` ซ้ำระหว่าง `ToonJobs` กับ `RenderJobs` | `/warroom tickets toon` | done (ticket 07) |
| 20 | review | ซ้ำ: เริ่ม child (start, `track`, `Ready`) ใน `start_qwen`/`start_klein`/`Speaker.start` และหยุด (`track(None)`, `stop_process`) 3 ที่ใน `steps.py` + `_free_gpu`; `on_progress` และ `_free_gpu` ของสอง render; map `ref_rev` สร้าง 3 ที่ (`images._ref_revs`, `render._cards_to_voice`, `cards.run`); `_plot_items` สองตัวที่ทำต่างกัน (`writer` ตัดทิ้ง, `episodes` raise); `(folder, name)` ใน `backend.renders` | `/warroom tickets toon` | done (ticket 08) |
| 21 | review | ชื่อ: `kinds.Kind` (characters/backgrounds) ชนกับ `JobKind` จน body ต้องใช้ `item_kind` และ `{kind}` ใน route เป็นชนิดของ item; ตัวพูดเป็น `speaker` ใน `ToonJobs` แต่ `_speaker` ใน `RenderJobs`/`SentenceVoicer`; คอมเมนต์ "Step 1", "Steps 2–3" ไม่บอกว่าขั้นของ spec ส่วนไหน; `toon/__init__.py` re-export ไว้ให้ test patch | `/warroom tickets toon` | done (ticket 07) |
| 22 | review | หน้าเว็บ: `update = useCallback((change) => setState((s) => (s.kind === "ready" ? change(s) : s)))` ซ้ำ 5 hook (`useRender`, `useSounds`, `usePickRef`, `useCast`, `useEp`); `useCast.sendItem` กับ `useEp.edit` รูปเดียวกัน (ส่ง, 200/201 แทนค่าและล้าง notice, ไม่งั้น `refused`) | `/warroom tickets toon` | done (ticket 10) |
| 23 | review | Data Clump `(project, series_id, item_kind, item_id)` ใน `series.ref_plan`, `ref_image`, `pending_image`, `pick`, `check_upload`, `_upload_checks`, `_take_upload`, `put_pending` และ 8 route ของ `routes/toon.py`: รวมเป็น type `ItemRef` | `/warroom tickets toon` | done (ticket 09) |
| 24 | review | test: fixture `llm`, `klein`, `tts`, `client` เกือบซ้ำใน `test_toon_images_api.py`, `test_toon_ref_api.py`, `test_toon_render_api.py`, `test_toon_eps_api.py`, `test_toon_sounds_api.py`: ย้ายเป็น helper ใน `tests/fakes.py` (conftest คง `fake_root` อย่างเดียว) | `/warroom tickets toon` | done (ticket 09) |
| 25 | review | หน้าเว็บยังส่ง `(sid, kind, id)` สามค่าใน `itemPath`, `pickHash`, `startRefJob` (`lib/series.ts`) ขณะ backend ใช้ `ItemRef` (D64); ชื่อ `sid`/`eid` ของ hook และ lib → `seriesId`/`epId` | `/warroom tickets toon` | → ticket 12 |
| 26 | review | Data Clump `(project, series_id, ep_id)` ราว 20 signature ใน `toon/` และ `paths.py` (`render._run`, `_voice_and_render`, `_render`, `episodes.remove_card_files`): type เดียวแบบ `ItemRef` (ชื่อ `EpRef` ถูก response model ใช้แล้ว) | `/warroom tickets toon` | → ticket 11 |
| 27 | review | test: fixture `project(fake_root)` ซ้ำหกไฟล์ test API ของ toon และ helper (`Writer`, `new_ep`, `run`, `start`, `create`, `png`, `upload`, `add`, `import_tone`) import ข้ามไฟล์ test: ย้ายเข้า `fakes.py` (ticket 09 "fixture … มาจาก helper ใน fakes ตัวเดียว") | `/warroom tickets toon` | → ticket 11 |
| 28 | review | หน้าเว็บ: ขนาดช่องภาพ, aspect และการถามก่อนเลือกไฟล์ยังแตกกิ่ง `kind === "characters"` ใน `CastPage.tsx` (3 ที่) และ `PickPage.tsx`: ย้ายเข้า `ITEM_KINDS`; flow เช็คแล้ว `sendFile` ซ้ำใน `useCast` กับ `useSounds` | `/warroom tickets toon` | → ticket 12 |
