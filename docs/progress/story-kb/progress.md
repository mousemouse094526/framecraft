# Progress: story-kb

**Now:** merged — [PR #8](https://github.com/mousemouse094526/framecraft/pull/8) (d75f574)

**Next:** —

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | คลังความรู้ — เพิ่ม แก้ ลบ Story | done |
| 02 | ร่างบทด้วย Story | done |
| 03 | เรียบเรียงใหม่ใช้ Story ล่าสุด | done |
| 04 | ค่าเลือก Story ของขั้น 1 เป็นค่าเดียว | done |

## Log

### feature review รอบสอง — 2026-11-06

**Built:**
- Review สามแกนทั้ง branch จาก merge-base d5557214 (เน้น ticket 04); แก้ใน 56d9980:
- ลองอีกครั้งถูกปฏิเสธเป็น `story_not_found` (Story ของ order ถูกลบ) → ไม่มีปุ่มลองอีกครั้ง มีแค่ "กลับไปแก้ตั้งค่า" (`SETUP_REFUSALS`) — ก่อนนี้ส่ง `story_id` เดิมซ้ำได้ไม่จบ; test ใหม่ใน `DraftProgress.test.tsx`
- ช่อง Story แสดง `message` ของ API (`gone` เก็บข้อความ, `onDraft` คืน `Refusal`) แทนข้อความซ้ำใน `StoryPicker`; test ใช้ข้อความของ API ที่ต่างจากในหน้า
- test ใหม่: order ที่ `story_id` `null` + คลิปจำ Story → ช่องเป็น "ไม่ใช้" (เช็คแล้วว่าจับได้: เปลี่ยน order `null` เป็น `followsClip` → แดง)
- ชื่อ: `storyIdOf` ของขั้น 1 → `sentStoryId`, `clipStory` → `clipStoryId`, ลบ `FOLLOWS_CLIP`; `remembering(stories, links)` ใช้แทน route ซ้ำ; ชื่อ test "picking one calls the API for nothing until ร่างบท"
- comment: ตัวคั่นของ `_story_part`, test Trim job (ADR 0022); spoil D39 และแถว index กำกับว่า D90–D95 เป็นเลขของ branch `feat/spoil-maker-transcript-remove`

**Decided:**
- D24 — `story_not_found` ของลองอีกครั้งเป็นเหตุต้องแก้ตั้งค่า, ข้อความจาก API, ชื่อ `sentStoryId`/`clipStoryId`, กำกับเลข D90

**For the next ticket:**
- Spec: `ClipStory` (`useClipStory.ts`, `unknown`/`none`/`story` + title) กับ `StoryChoice` (`story` + id) ใช้ `kind` ชื่อเดียวกันคนละ payload ในโฟลเดอร์เดียว — ไม่เปลี่ยน; ระวังตอนใช้ร่วมกัน
- Newcomer: `clips` ของ `StoryRow` เป็นจำนวน, `_tokens` คืน `None` ทุก error, "— / —" เมื่อนับ Story ไม่ได้ — ตาม spec › API, D17, D19; ไม่เปลี่ยน

**Checks:** `uv run pytest` (679) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` (319) · `npm --prefix frontend run build` — all green

### 04: ค่าเลือก Story ของขั้น 1 เป็นค่าเดียว — done 2026-11-06

**Built:**
- `SpoilerSetup.tsx`: `StoryChoice` เป็น union เดียว `followsClip` · `story` · `none` · `gone` แทน `string | null | undefined` + ธง `storyGone`; `choiceOf` (id จากช่องหรือ order → ค่าเลือก), `storyIdOf` (ค่าเลือก → id ที่ส่ง); ลบ `pickStory`; เปลี่ยนคลิปคืน `followsClip`, `story_not_found` → `gone`
- `listedStory` รับ `string | null` (ไม่รับ `undefined` อีก); `useClipStory` ส่ง `?? null`
- test ใหม่ใน `SpoilerSetup.test.tsx` (ผ่าน `App`): ไม่แตะแล้วเปลี่ยนคลิปตามเรื่องของคลิปใหม่, เรื่องที่เลือกหายเมื่อเปลี่ยนคลิป (ไม่ใช้/เรื่องของคลิปกลับมา), "ไม่ใช้" ส่ง `story_id` `null`, หลัง `story_not_found` เลือกเรื่องหรือเปลี่ยนคลิปแล้วข้อความหาย, ร่างใหม่ส่ง `null`; test เดิมไม่แก้สักบรรทัด
- เช็คว่า test จับได้: เอาการคืน `followsClip` ตอนเปลี่ยนคลิปออก → 2 test แดง

**Decided:**
- D23 — union สี่แบบ, ชื่อ `followsClip` (Newcomer อ่าน `clip` เป็น "คลิป"), `gone` ส่ง `null` เหมือน `none`, order ที่ `story_id` `null` เป็น `none` (D87)

**For the next ticket:**
- Review (Standards): `StoryPicker` ยังส่ง `null` = ไม่ใช้ ให้ `choiceOf` แปลง — ขอบของ component รับได้; ไม่เปลี่ยน prop
- Review (Standards): test ของขั้น 1 ยังหา radio ของคลิปด้วย `getByRole("radio", …)` ซ้ำ ~30 ที่ — test ใหม่ใช้ `clipRadio`; ย้าย test เดิมไปใช้ตอนแตะไฟล์อีก
- Feature review รอบใหม่: โค้ดเปลี่ยนหลัง 2e8eb0d

**Checks:** `uv run pytest` (679) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` (317) · `npm --prefix frontend run build` — all green

### feature review — 2026-11-06

**Built:**
- Review สามแกนทั้ง branch (Standards, Spec, Newcomer) จาก merge-base d5557214; แก้ใน b276e69:
- `#/stories/` (ไม่มี id) เปิดรายการแทนพังเป็น offline — test ใหม่ใน `StoryList.test.tsx`
- กล่องเรียบเรียงใหม่ตาม Figma 8105-56586: "เรียบเรียงบทใหม่", คำอธิบายใหม่, บรรทัดเสียง 13px, ช่องติ๊กน้ำหนักปกติ (ไม่ได้เทียบใน browser จริง — test หา dialog ด้วยชื่อใหม่)
- golden `polish_again_prompt_no_story.txt` จับใหม่จาก d5557214 (worktree ชั่วคราว) — ตรงทุกตัวอักษร; comment ใน test ชี้ commit นั้น
- `remember()` ใน `test_stories_api.py` จำผ่าน `stories.set_clip_story`; สถานะค้างจาก crash ใช้ `left_behind`
- `backend/stories.py`: `_rewrite_clip_stories` ตัวเดียว (ลบ/เพิ่ม key), `_remembered` นับคลิปที่เดียว, `_checked_fields`, `StoredStory.modified_ns`, ชื่อ lambda ชัด; `names_rule`/`block_tokens` รับ `None` → `script._story_part` เหลือเงื่อนไขเดียว
- frontend: `grouped` → `src/lib/format.ts` (EpisodePicker ใช้ด้วย), `listedStory` → `src/lib/stories.ts` (ขั้น 1 และกล่องเรียบเรียง), prop `epBlocked` → `draftBlocked`, `setupFixtures` ไม่ re-export path ของ Story, comment ของ `StoryPicker`, `useHash` beforeunload, ข้อความ not-ready ของ Story
- docs: spec › Modules touched (`backend.qwen_tokens.count`), D19 (`set_clip_story`), ADR 0024 (ร่างบทอ่าน Story ของคำขอ), spec › Design (badge เมื่อ n > 0), spoil-maker spec › Frontend (หัวข้อกล่อง)

**Decided:**
- D21 — กล่องเรียบเรียงใหม่ตาม Figma (ปุ่มคง 44px), `story-clips` ไม่ห่อ RootModel, `#/stories/` เปิดรายการ, badge "ใช้อยู่" เมื่อ n > 0, fixture ของ API ยัง import ข้ามไฟล์ตามแบบ spoil-maker (ย้าย conftest แตะ test ทั้งชุด), ของใช้ร่วม

**For the next ticket:**
- Spec: spoil-maker D90 (เลือกสไตล์ไม่เปลี่ยน layout) อยู่ใน branch นี้ตั้งแต่ 4c62661 ตามคำขอผู้ใช้ — บอกใน PR
- Spec: test ที่ patch `stories.now_iso` และ tokenizer ปลอมที่ลบ Story ผูกกับลำดับภายใน — รับได้ (ไม่มีทางอื่นผ่าน API)
- Standards: `story_id`/`story_title` และ `ep`/`story`/`tokens`/`limit` เดินคู่ (Data Clump) — ไม่รวม ตาม 02

**Checks:** `uv run pytest` (679) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` (311) · `npm --prefix frontend run build` — all green

### 03: เรียบเรียงใหม่ใช้ Story ล่าสุด — done 2026-11-05

**Built:**
- Draft job `kind: "polish"` อ่าน Story ที่คลิปของ Spoil draft จำ ตอนรับคำขอ หลังเช็คของเรียบเรียงใหม่ผ่าน (`stories.read_clip_story`, ไม่ raise) แล้วส่งให้ `polish_prompt` — `PUT` Story หลังร่างแล้วเรียบเรียงใหม่ได้ค่าใหม่; ไม่จำ, ถูกลบ, อ่านไม่ได้ → คำสั่งเท่ากับ golden `polish_again_prompt_no_story.txt` (เขียนจากโค้ดที่ 60a1a6b); `order` ยัง `null`; `kind: "pick"` ไม่มีบล็อก
- กล่องเรียบเรียงใหม่: "ใช้เรื่อง: {ชื่อ}" หรือ "ไม่ได้ใช้เรื่องในคลังความรู้" (`useClipStory` อ่าน `GET /api/story-clips` กับ `GET /api/stories` ตอนเปิด), อ่านไม่ได้ → ไม่มีบรรทัด; layout A/C → "hook และชื่อตอนไม่ถูกเรียบเรียง แก้เองได้ที่ช่องด้านบน"
- `readStoryLinks` และ `ClipStories` ใน `src/lib/stories.ts` (ขั้น 1 ใช้ด้วย); `TOP_TEXT_LABELS` ย้ายไป `lib/draft.ts`; `stories._read_if_stored` ใช้ร่วมกับ `for_draft`
- spoil-maker spec: แถวหน้าตรวจแก้ และ Frontend ของปุ่ม "เรียบเรียงใหม่" ชี้มาที่ story-kb (ข้อ Draft job `kind: "polish"` ชี้อยู่แล้ว)
- หน้าตาเทียบ Figma 8105-56552 (remote Figma MCP) ใน browser จริงด้วย fetch ปลอมในหน้า ที่ desktop และ 375: บรรทัดใหม่ 13px `text-mid` ใต้คำอธิบาย ก่อนช่องติ๊ก — ตรง

**Decided:**
- D20 — `read_clip_story` ไม่ raise, golden ของ "ไม่ใช้", ไม่เช็ค token ตอนเรียบเรียงใหม่, กล่องไม่บอกเรื่องเมื่ออ่านไม่ได้, `readStoryLinks` ใช้ร่วม, หัวข้อกล่องของ spoil-maker ไม่เปลี่ยน

**For the next ticket:**
- Figma กล่องเรียบเรียงใหม่ (section story-kb) หัวข้อ "เรียบเรียงบทใหม่", คำอธิบาย "AI จะแก้ถ้อยคำให้ประโยคเล่าต่อกัน ภาพและลำดับประโยคไม่เปลี่ยน" และบรรทัดเสียง 13px — โค้ดยังเป็นข้อความเดิมของ spoil-maker ("เรียบเรียงใหม่", 14px); feature review ตัดสินว่าจะตาม Figma ไหม (test ของ spoil-maker หา dialog ด้วยชื่อ "เรียบเรียงใหม่")
- Review (Newcomer): ระหว่างเปิดกล่องแล้ว Story ถูกแก้ บรรทัด "ใช้เรื่อง" เป็นค่าตอนเปิด งานใช้ค่าตอนส่ง — รับได้ตาม ADR 0024 (D20)

**Checks:** `uv run pytest` (ที่ root ของ repo) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` · `npm --prefix frontend run build` — all green

### 02: ร่างบทด้วย Story — done 2026-11-05

**Built:**
- Draft job `kind: "draft"` รับ `story_id`: เช็คหลัง Saved voice (`story_not_found` เมื่อไม่มีไฟล์ อ่านไม่ได้ หรือ id ผิดรูป), token EP + บล็อก Story ≤ 32,000 (`transcript_too_long` มี `tokens` รวมและ `story_tokens`), จำ/ลืม key ใน `clip-stories.json` ใต้ lock ของ draft หลังจองช่อง GPU; `order` มี `story_id`, `story_title`
- คำสั่งเขียนบทมีบล็อก Story ครั้งเดียวก่อน `Transcript, one line each` (รวมตอนสั่งใหม่) และบรรทัด `เขียนชื่อตัวละครตาม Story: …` ท้ายกฎ; คำสั่งเรียบเรียงตอนร่างมีบล็อกหลัง `top_text`; คำสั่งเลือก Shot ไม่มี; "ไม่ใช้" เท่ากับไฟล์ golden จากโค้ดก่อน story-kb ทุกตัวอักษร
- `backend/qwen_tokens.py` นับ token ที่เดียว (EP และบล็อก Story); `stories.for_draft`, `stories.set_clip_story`, `stories.names_rule`, `stories.block_tokens`
- ขั้น 1: การ์ด "เรื่องในคลังความรู้" (`StoryPicker`) ระหว่างการ์ดคลิปกับ EP — "ไม่ใช้" + Story เรียงตามชื่อแบบไทย, ค่าตั้งต้นจาก `order` หรือ Story ที่คลิปจำ, ลิงก์แท็บใหม่ "แก้เรื่องนี้" / "เพิ่มเรื่องในคลังความรู้", อ่านรายการใหม่เมื่อกลับมา focus, `story_not_found` → Alert ในการ์ดและ "ไม่ใช้"; ระหว่างร่างเป็นข้อความ `order.story_title` หรือ "ไม่ใช้"
- ตัวนับ "Transcript ของ EP {n} + เรื่อง" กับ "เรื่อง {n} token", เกินรวม → Alert และปุ่มร่างกดไม่ได้, Story `tokens` `null` → "— / —"; การ์ดความคืบหน้ามี "เรื่อง: {story_title}"; "ลองอีกครั้ง" ส่ง `order.story_id`
- `StoryRow`, path และ hash ของ Story ที่สอง tab อ่าน ย้ายไป `frontend/src/lib/stories.ts`; นับคลิปของ Story ด้วย `Counter` ทั้งรายการและ Story เดียว (ข้อจาก 01)
- หน้าตาเทียบ Figma (remote Figma MCP) ใน browser จริงด้วย fetch ปลอมในหน้า: ช่อง Story ที่ 1440 (560×164) และ 375 (343×164), เกินเพดาน, ระหว่างร่าง (สูง 80) — ตรง

**Decided:**
- D19 — ค่าคาดหวังเป็นไฟล์ golden, รอยต่อของบล็อก, อ่าน Story ครั้งเดียวตอนเช็ค, ข้อความ `transcript_too_long` เมื่อมี Story, `backend.qwen_tokens`, ช่อง Story เป็นการ์ดของตัวเอง, ชื่อตัวนับตาม Figma, "นับ token ของเรื่องไม่ได้", Alert `story_not_found` ในการ์ด, เรียง `localeCompare(…, "th")`, ไอคอน 16px, ของ Story ใน `src/lib/stories.ts`

**For the next ticket:**
- ticket 03: `_polish_draft` ส่ง `None` เป็น Story ของ `_ask_to_polish` ตรงๆ (argument บังคับแล้ว) — เปลี่ยนเป็น Story ที่คลิปของ draft จำตอนรับคำขอ
- Review (Spec): `remember()` ใน `test_stories_api.py` ยังเขียน `clip-stories.json` ตรง — fixture ของ Draft API อยู่ใน `test_spoil_maker_draft_api.py`; ย้าย fixture ไป conftest ตอน feature review แล้วจำผ่าน Draft job
- Review (Spec): ระหว่างร่าง ตัวนับใช้ `tokens` ของ Story ตอนนี้จากรายการ ไม่ใช่ตอนเริ่มงาน — `order` ไม่มี token; รับได้เพราะช่องอ่านอย่างเดียว
- Review (Standards): `story_id`/`story_title` เดินคู่กันใน `DraftOrder` ทั้งสองฝั่ง (Data Clump) — ตาม spec › `order` แบบ `clip_id`/`clip_title`; ไม่รวม
- Review (Standards): prop `epBlocked` ของ `SetupSettings` ตอนนี้รวมเหตุของ Story ด้วย (`draftBlocked` ในฟอร์ม) — เปลี่ยนชื่อ prop ตอนแตะไฟล์อีก
- `ไอคอน external-link` มีสองแบบ (setup-status 12px ม่วง, spoil-maker 16px เข้ม) ตาม Figma — ถาม designer ว่าควรเป็นตัวเดียวไหม

**Checks:** `uv run pytest` (ที่ root ของ repo) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` · `npm --prefix frontend run build` — all green

### 01: คลังความรู้ — เพิ่ม แก้ ลบ Story — done 2026-11-05

**Built:**
- แถบ tab 4 tab (ติดตั้ง · คลิป · คลังความรู้ · สปอย); `tabOf` จับ `#/stories/…`; `useLeaveGuard` ใน `lib/useHash` ถาม "ออกโดยไม่บันทึก?" ก่อน hash เปลี่ยน (ปฏิเสธ → `replaceState` คืน hash เดิม) และ `beforeunload`
- `features/story-kb/`: รายการ Story (ว่าง, กำลังโหลด skeleton, offline, แถวพร้อม "ใช้อยู่ {n} คลิป" และ "แก้ล่าสุด"), หน้าแก้ Story (ชื่อเรื่อง, บทความพร้อมตัวนับ code point, ตัวละคร ≤ 30, error ใต้ช่องจากเช็คในหน้าและจาก `invalid_story`, "บันทึกแล้ว", ลบพร้อมกล่องยืนยัน, "ไม่พบเรื่องนี้")
- ของใช้ร่วม: `ModalDialog` และ `arrow-left.svg` → `components/ui/`, `testBackend.ts` → `src/testing/`, `OFFLINE_TEXT` → `lib/api`; `Refusal` มี `field`
- หน้าตาเทียบ Figma ใน browser จริง (fetch ปลอมในหน้า): รายการที่ 1440, แก้ Story ที่ 1440 และ 375, บันทึกแล้ว, กล่องยืนยันลบ — ตรง; backend ที่รันอยู่ของเครื่องยังเป็นโค้ดเก่า (`/api/stories` 404 → `OfflinePanel`)
- กลุ่ม "tab คลังความรู้" ครบ; ข้อ (e2e) เป็น Vitest ผ่าน `App` (D18)

**Decided:**
- D18 — ข้อ e2e ด้วย Vitest, ตัวกันออกลงทะเบียนตอนโหลด module, บันทึกครั้งแรกไม่ remount และไม่ถามตอนไป `#/stories/{id}`, Alert เมื่อบันทึก/ลบไม่ได้, วันเวลาจากข้อความ `updated_at`, ไอคอน + สีขาวบนปุ่ม "เพิ่มเรื่อง", ของใช้ร่วมย้ายที่

**For the next ticket:**
- Review (Spec): test ที่ใช้ `remember()` เขียน `clip-stories.json` ตรง — ticket 02 เปลี่ยนเป็นจำผ่าน Draft job (`kind: "draft"`) เมื่อมีแล้ว
- Review (Standards): `stories.list_rows` กับ `stories._view` นับคลิปของ Story คนละแบบ (`Counter` กับ `sum`) — รวมตอนแตะไฟล์นี้ใน 02
- Review (Standards): `GET /api/story-clips` ตอบ `dict[str, str]` ไม่ใช่ Pydantic model — ตามรูปของ spec › API; feature review ตัดสินว่าจะห่อเป็น `RootModel` ไหม
- `ModalDialog` มุม `sm:rounded-3xl` (24px) ส่วน Figma `Delete story dialog` 16px — ของใช้ร่วมของ spoil-maker ไม่แก้ใน ticket นี้
- Actions ของหน้าแก้ใน Figma มี Spacer สูง 100px (แถวสูงกว่าปุ่ม) — ทำเป็นแถวสูงตามปุ่ม; ถาม designer ถ้าตั้งใจ

**Checks:** `uv run pytest` (ที่ root ของ repo) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` · `npm --prefix frontend run build` — all green

### design: 4 จอ — 2026-11-05

**Built:**
- Figma section [framecraft — คลังความรู้ (story-kb)](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8102-52561): คลังความรู้ 4 state, แก้ Story 8 state, ขั้น 1 ช่อง Story 6 state + การ์ดร่างบทมีบรรทัด "เรื่อง:", กล่องเรียบเรียงใหม่ 2 state; แต่ละ state ที่ 1440 และ 375; prototype link และ start point "คลังความรู้ — desktop/mobile"
- Components ใหม่: Tab bar (4 tab), Story row, Character row (desktop/mobile), Article field, Story picker, Delete story dialog, icon/book-open
- Components ที่แก้: Token meter เพิ่ม `ok story` / `over story`; Polish dialog เพิ่ม `Story line` กับ `Show hook note`; Draft progress card เพิ่ม `Story` กับ `Show story` (ปิดไว้เป็นค่าตั้งต้น)
- `ui-prompt.md` ลบ; spec › Design ไม่มีจอ `pending`

**For the next ticket:**
- Polish dialog แสดง `Story line` ทุก instance รวม frame เก่าของ spoil-maker; ใช้ frame ใน section story-kb เป็นแบบล่าสุด
- state "กำลังบันทึก" ของแก้ Story ไม่มีข้อความใหม่: ปุ่ม "บันทึก" กดไม่ได้ + `aria-busy` ตาม D16

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
| 1 | 01 | design: คลังความรู้ (รายการ Story) | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | done ([Figma 8103-52679](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8103-52679)) |
| 2 | 01 | design: แก้ Story | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | done ([Figma 8104-52899](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8104-52899)) |
| 3 | 02 | design: ขั้น 1 ตั้งค่าคลิปสปอย: ช่อง Story | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | done ([Figma 8105-55260](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8105-55260)) |
| 4 | 03 | design: ขั้น 2 กล่องเรียบเรียงใหม่ | `/warroom story-kb` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/story-kb/ui-prompt.md`) | done ([Figma 8105-56552](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8105-56552)) |
| 5 | review | designer: `ModalDialog` มุม `sm:rounded-3xl` (24px) แต่ Figma `Delete story dialog` 16px — ของใช้ร่วมกับ spoil-maker | `/warroom tickets story-kb` (หลังถาม designer) | → D22 |
| 6 | review | designer: Actions ของหน้าแก้ Story ใน Figma มี Spacer สูง 100px — โค้ดทำแถวสูงตามปุ่ม | `/warroom tickets story-kb` (หลังถาม designer) | → D22 |
| 7 | review | designer: ไอคอน external-link สองแบบ (setup-status 12px ม่วง, spoil-maker 16px เข้ม) ควรเป็นตัวเดียวไหม | `/warroom tickets story-kb` (หลังถาม designer) | → D22 |
| 8 | review | refactor: `StoryChoice` (`string \| null \| undefined`) กับ `storyGone` ใน `SpoilerSetup.tsx` เป็น union type เดียว | `/warroom tickets story-kb` | done (ticket 04) |
