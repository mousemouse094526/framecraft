# Spec: story-kb

ผู้ใช้เก็บ Story (ชื่อเรื่อง บทความ ตัวละคร) ไว้ใน tab คลังความรู้ แล้วเลือก Story ให้ Temp clip ในขั้น 1 ของ tab สปอย เพื่อให้ AI ร่างบทสปอยด้วยชื่อและพื้นหลังที่ถูก.

**Status:** ready-to-build

## Problem

AI ร่างบทจาก Transcript อย่างเดียว: ไม่รู้ว่าหนังเรื่องอะไร ใครเป็นใคร และเขียนชื่อตัวละครตามที่ Whisper ถอดผิด (เช่น "โคนัง"). ผู้ใช้ต้องตามแก้ชื่อทุกประโยคเอง.

## Solution

- เพิ่ม แก้ ลบ Story ใน tab คลังความรู้: ชื่อเรื่อง บทความ และรายการตัวละคร (กดบวกเพิ่ม) แต่ละตัวมีชื่อกับคำอธิบายสั้น (D1, D2, D6, D9, D10, D11)
- ขั้น 1 ของ tab สปอย เลือก Story ของคลิปที่เลือก หรือ "ไม่ใช้"; กดร่างแล้วคลิปจำไว้ให้ทุก EP (D3, D7, D15)
- คำสั่งเขียนบทและเรียบเรียงมี Story ของคลิปตอนเริ่มงาน เป็นพื้นหลังและตัวสะกดชื่อ (D4, D5, D8)

## User Stories

**ผู้ใช้**
1. As a ผู้ใช้, I want สร้าง Story ด้วยชื่อเรื่องและบทความ, so that AI รู้ว่าหนังเรื่องอะไร (D1, D6)
2. As a ผู้ใช้, I want กดบวกเพิ่มตัวละครพร้อมคำอธิบายสั้น และลบทีละตัว, so that AI เขียนชื่อถูกและรู้ว่าใครเป็นใคร (D2)
3. As a ผู้ใช้, I want แก้ Story แล้วกดบันทึกครั้งเดียว, so that แก้หลายช่องได้โดยไม่ต้องบันทึกทีละช่อง (D11)
4. As a ผู้ใช้, I want ลบ Story ที่ไม่ใช้แล้ว, so that คลังไม่รก (D10)
5. As a ผู้ใช้, I want เลือก Story ให้คลิปในขั้นเลือกคลิป, so that ทุก EP ของคลิปใช้เรื่องเดียวกันโดยไม่ต้องเลือกซ้ำ (D3, D15)
6. As a ผู้ใช้, I want กดร่างบทหรือเรียบเรียงใหม่แล้ว AI ใช้ Story ล่าสุด, so that ชื่อตัวละครถูกตาม Story (D4, D5, D8)

## Design

ออกแบบใน Figma หลัง plan (setup-status D9). ทุกจออยู่ใน section [framecraft — คลังความรู้ (story-kb)](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8102-52561): components, state ของแต่ละจอที่ 1440 และ 375, prototype เริ่มที่ "คลังความรู้ — desktop".

| Screen | User stories | Must show | Source |
|---|---|---|---|
| คลังความรู้ (รายการ Story) | 1, 4 | ปุ่ม "เพิ่มเรื่อง"; แต่ละแถว: ชื่อเรื่อง, จำนวนตัวละคร, "ใช้อยู่ {n} คลิป" (เมื่อ n > 0, D21), แก้ล่าสุด; กดแถวเปิด Story; ว่าง: "ยังไม่มีเรื่องในคลังความรู้" กับปุ่ม "เพิ่มเรื่อง"; กำลังโหลด; offline (`OfflinePanel`) (D9) | [Figma 8103-52679](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8103-52679) |
| แก้ Story | 1, 2, 3, 4 | ช่องชื่อเรื่อง (ต้องมี, ≤ 100, บรรทัดเดียว), ช่องบทความหลายบรรทัด (≤ 5,000) พร้อมตัวนับ "{n} / 5,000", รายการตัวละคร (ชื่อ ≤ 40, คำอธิบาย ≤ 200, ปุ่มลบแต่ละตัว) และปุ่ม "+ เพิ่มตัวละคร" (ซ่อนเมื่อครบ 30) (D2, D6); ปุ่ม "บันทึก" กดไม่ได้เมื่อไม่มีอะไรเปลี่ยนและระหว่างรอคำตอบ (D16); error ใต้ช่องที่ไม่ผ่าน; บันทึกแล้ว "บันทึกแล้ว"; ออกจากหน้าตอนยังไม่บันทึก ถาม "ออกโดยไม่บันทึก?" (D11); ปุ่ม "ลบเรื่อง" เปิดกล่องยืนยัน "ลบ {ชื่อเรื่อง}? ใช้อยู่ {n} คลิป คลิปเหล่านั้นจะเป็น ไม่ใช้" (บรรทัดใช้อยู่แสดงเมื่อ n > 0) (D10); Story ไม่มีแล้ว: "ไม่พบเรื่องนี้" กับลิงก์กลับคลังความรู้ | [Figma 8104-52899](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8104-52899) |
| ขั้น 1 ตั้งค่าคลิปสปอย: ช่อง Story | 5 | ช่องเลือก "เรื่องในคลังความรู้" ใต้คลิปที่เลือก: ตัวเลือก "ไม่ใช้" กับทุก Story เรียงตามชื่อ; ค่าตั้งต้นคือ Story ที่คลิปจำไว้ (D3, D15); บรรทัดช่วย "จำให้คลิปนี้ทุก EP เมื่อกดร่างบท" (D15); ลิงก์ "เพิ่มเรื่องในคลังความรู้" เปิดแท็บใหม่ (D16); ลิงก์ "แก้เรื่องนี้" เปิด `#/stories/{id}` ในแท็บใหม่เมื่อเลือกอยู่; ตัวนับ token เป็น "{EP + Story} / 32,000" พร้อม "เรื่อง {n} token" เมื่อเลือก Story (D14); ระหว่างร่าง (spoil-maker D82) เป็นข้อความ `order.story_title` หรือ "ไม่ใช้" ไม่ใช่ช่องเลือก | [Figma 8105-55260](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8105-55260) |
| ขั้น 2 กล่องเรียบเรียงใหม่ | 6 | บรรทัด "ใช้เรื่อง: {ชื่อเรื่อง}" หรือ "ไม่ได้ใช้เรื่องในคลังความรู้"; บรรทัด "hook และชื่อตอนไม่ถูกเรียบเรียง แก้เองได้ที่ช่องด้านบน" เมื่อ layout เป็น A หรือ C (D5, D16) | [Figma 8105-56552](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8105-56552) |


## Expected Outcome

ผู้ใช้ใส่ชื่อตัวละครครั้งเดียวใน Story แล้วทุก EP ของคลิปได้บทที่เขียนชื่อตาม Story.
- **คลิปโคนันมี Story "โคนัน" ที่มีตัวละคร "โคนัน":** กดร่างบท EP 2 → บทใช้ "โคนัน" แม้ Transcript ถอดเป็น "โคนัง"
- **แก้ชื่อตัวละครใน Story หลังร่าง:** กด "เรียบเรียงใหม่" → ประโยคที่ไม่ใช่ "แก้เอง" ใช้ชื่อใหม่; hook หรือชื่อตอนต้องแก้เอง (D16)
- **ลบ Story ที่คลิปใช้:** ขั้น 1 ของคลิปนั้นเป็น "ไม่ใช้"
- **EP ยาวกับ Story ยาว:** ตัวนับบอก "31,500 / 32,000 · เรื่อง 4,200 token"; เกิน → ปุ่มร่างกดไม่ได้ (D14)

**How success is judged:**
- คำสั่งเขียนบทและเรียบเรียงของคลิปที่จำ Story มีชื่อเรื่อง บทความ และตัวละครทุกตัว; คลิปที่ "ไม่ใช้" ได้คำสั่งเหมือนก่อนมี feature นี้ทุกตัวอักษร
- ปิดแล้วเปิด backend ใหม่ Story และ Story ที่คลิปจำยังอยู่
- ร่างบทด้วย Story แล้วเปิดขั้น 1 ของคลิปเดิมใหม่ ช่อง Story เป็นเรื่องนั้น (D15)
- ตัดช่วงหรือถอดคลิปใหม่ Story ที่คลิปจำยังอยู่; ลบคลิปแล้วหาย (D7)

## Implementation

### Modules touched

- **`backend.stories`** (ใหม่): อ่าน เขียน ลบ Story และ Story ที่คลิปจำ; บล็อกข้อความของ Story สำหรับคำสั่ง LLM; token ของบล็อก (`backend.qwen_tokens.count`, D14, D19); lock ตัวในสุด (D16)
- **`backend.routes.stories`** (ใหม่): router `/api/stories` และ `/api/story-clips`
- **`backend.app`**: ใส่ router; ล้างไฟล์ค้างตอน start (Ops)
- **`backend.spoil.transcribe`**: `Transcriptions.delete_clip` ลบ key ของคลิปต่อจาก `draft_file.drop_if_uses` หลังออกจาก `clip_untouched` (D7, D16); `clips.delete_derived` (ที่ Trim job ใช้) ไม่แตะ
- **`backend.spoil_maker.script`**: `Brief` และ `polish_prompt` รับ Story หรือ `None`; ตำแหน่งบล็อกตาม คำสั่ง LLM (D4, D8, D16)
- **`backend.spoil_maker.draft`**: Draft job `kind: "draft"` รับ `story_id` เช็ค token รวม และจำให้คลิป; `kind: "polish"` อ่าน Story ที่คลิปจำ; `order` มี `story_id`, `story_title` (D5, D14, D15)
- **`frontend/src/features/story-kb/`** (ใหม่): หน้ารายการและหน้าแก้ Story, hook ของ API
- **`frontend/src/lib/useHash`**: `TABS` 4 tab; `#/stories/…` เป็น tab คลังความรู้ (D9); ตัวกันออก (D16)
- **`frontend/src/App`**: tab `stories`
- **`frontend/src/features/spoil-maker`**: ขั้น 1 มีช่อง Story และตัวนับรวม; `DraftOrder` มี `story_id`, `story_title`; `DraftAsk` ตัด `story_title` (แบบ `clip_title`) และมี `story_id`; การ์ดความคืบหน้าแสดงชื่อเรื่อง; กล่องเรียบเรียงใหม่บอกเรื่องที่ใช้

### Data

ไฟล์ทั้งหมดใน `media/stories/` เขียนผ่าน `.tmp` แล้ว rename ใต้ lock เดียวของ `backend.stories` (D12):

`media/stories/{id}.json` — Story หนึ่งเรื่อง; `id` ตรง `^st_[0-9a-f]{8}$`:

```json
{
  "id": "st_3fa91c07",
  "title": "ยอดนักสืบจิ๋วโคนัน",
  "article": "คุโด้ ชินอิจิ นักสืบมัธยมปลาย ถูกองค์กรชุดดำบังคับกินยาจนตัวหดเป็นเด็ก ใช้ชื่อใหม่ว่า เอโดงาวะ โคนัน…",
  "characters": [
    { "name": "โคนัน", "description": "ชินอิจิในร่างเด็ก ไขคดีแทนลุงโคโกโร่" },
    { "name": "รัน", "description": "" }
  ],
  "created_at": "2026-11-05T14:00:00+07:00",
  "updated_at": "2026-11-05T14:20:00+07:00"
}
```

`media/stories/clip-stories.json` — Story ที่คลิปจำ `{clip_id: story_id}`; คลิปที่ "ไม่ใช้" ไม่มี key (D3):

```json
{ "abc123": "st_3fa91c07" }
```

กฎของค่า (D6, D12):

| ฟิลด์ | กฎ |
|---|---|
| `title` | 1–100 ตัวอักษรหลังตัดช่องว่างหัวท้าย; ขึ้นบรรทัดใหม่เป็นช่องว่าง (D16) |
| `article` | 0–5,000 ตัวอักษรหลังตัดช่องว่างหัวท้าย; ขึ้นบรรทัดใหม่ได้ |
| `characters` | 0–30 ตัว ตามลำดับที่ผู้ใช้ใส่ |
| `characters[].name` | 1–40 ตัวอักษรหลังตัดช่องว่าง; ขึ้นบรรทัดใหม่เป็นช่องว่าง; ไม่ซ้ำกันในเรื่องเดียว (เทียบหลังตัดช่องว่างและตัวพิมพ์เล็ก) |
| `characters[].description` | 0–200 ตัวอักษรหลังตัดช่องว่าง; ขึ้นบรรทัดใหม่เป็นช่องว่าง |

- "ตัวอักษร" = จำนวน code point (`len` ใน Python, `[...text].length` ในหน้าเว็บ) จึงนับสระและวรรณยุกต์ไทยด้วย
- ไม่ผ่านกฎ → `400` `invalid_story` พร้อม `field` (`title`, `article`, `characters`, `characters.{i}.name`, `characters.{i}.description`)
- ชื่อเรื่องซ้ำกันได้

### คำสั่ง LLM

บล็อก Story อยู่ในคำสั่งเขียนบทและคำสั่งเรียบเรียง (D4, D8, D16); คลิปไม่มี Story → ไม่มีบล็อก คำสั่งเหมือนเดิมทุกตัวอักษร:

- คำสั่งเขียนบท (`script_prompt`): บล็อกอยู่หลัง `rules` ชุดแรก ก่อน `Transcript, one line each…` ครั้งเดียว รวมตอนสั่งใหม่; กฎชุดที่ซ้ำหลัง Transcript เพิ่มบรรทัดท้าย `เขียนชื่อตัวละครตาม Story: {name}, {name}` เมื่อมีตัวละคร
- คำสั่งเรียบเรียง (`polish_prompt`): บล็อกอยู่หลังบรรทัด `top_text` ก่อน `The script, one sentence each…`; คำสั่งยังขึ้นต้นด้วยข้อความเดิม

บล็อก:

```text
ข้อมูลพื้นหลังของเรื่อง (ใช้เข้าใจเรื่องและสะกดชื่อเท่านั้น ห้ามเล่าเหตุการณ์จากส่วนนี้ เหตุการณ์ต้องมาจากบรรทัดของ Transcript):
ชื่อเรื่อง: {title}
บทความ:
{article}
ตัวละคร (เขียนชื่อตามนี้ แม้ Transcript สะกดต่าง):
- {name}: {description}
- {name}
```

- `article` ว่าง → ไม่มีบรรทัด `บทความ:`; ไม่มีตัวละคร → ไม่มีส่วน `ตัวละคร`
- ตัวละครที่ `description` ว่าง → `- {name}` ไม่มี `:`
- คำสั่งเลือก Shot ไม่มีบล็อก Story (D4)
- `max_tokens` ของร่างบทและเรียบเรียงไม่เปลี่ยน: ขึ้นกับความยาวบท ไม่ใช่คำสั่ง
- token ของบล็อก (นับทั้งบล็อก) รวมกับ token ของ EP ในเพดาน 32,000 ของคำสั่งเขียนบท (D14); บรรทัดชื่อหลัง Transcript เล็กจนไม่นับ

### API

ทุก route อยู่ใต้ `/api/stories` และ `/api/story-clips` (แยก prefix: path `{id}` ไม่ทับ). POST, PUT ต้องเป็น JSON (ADR-0013); ผ่าน `TrustedHostMiddleware` (ADR-0011). Error รูป `ApiError` `{"code", "message", ...extra}` แบบ spoil-maker.

| Method | Path | ทำอะไร | ตอบ |
|---|---|---|---|
| `GET` | `/api/stories` | `[{id, title, characters: จำนวน, clips: จำนวนคลิปที่จำ, tokens, updated_at}]` แก้ล่าสุดก่อน; `tokens` ของบล็อก Story หรือ `null` เมื่อไม่มี tokenizer ของ Qwen (D14) | `200` |
| `POST` | `/api/stories` | `{title, article, characters: [{name, description}]}` สร้าง | `201` Story เต็มพร้อม `clips`; `400` `invalid_story` |
| `GET` | `/api/stories/{id}` | Story เต็มพร้อม `clips` | `200`; `404` `not_found` |
| `PUT` | `/api/stories/{id}` | body แบบ `POST` แทนทั้งเรื่อง; `updated_at` เป็นตอนนี้ | `200`; `400` `invalid_story`; `404` `not_found` |
| `DELETE` | `/api/stories/{id}` | ลบไฟล์ Story แล้วลบทุก key ที่ชี้ Story นี้ใน `clip-stories.json` (D10) | `204`; `404` `not_found` |
| `GET` | `/api/story-clips` | `{clip_id: story_id}` ทั้งหมด (D3) | `200` |

- `{id}` ไม่ตรง `^st_[0-9a-f]{8}$` → `404` `not_found`
- body ที่ไม่ใช่ object หรือฟิลด์ผิดชนิด → `400` `invalid_request` (แบบ spoil-maker)
- `description` ไม่ส่ง = `""`; `article` ไม่ส่ง = `""`; `characters` ไม่ส่ง = `[]`
- แก้หรือลบ Story ระหว่าง Draft job → ได้: งานอ่าน Story ไปแล้ว (D5)
- ไม่มี route ตั้ง Story ของคลิป: จำตอนร่าง (D15)

### spoil-maker เปลี่ยน

- `POST /draft-jobs` `kind: "draft"` รับ `story_id: string | null` (ไม่ส่ง = `null`, D15)
- Draft job ข้อ 1 (เช็คคำขอ) เพิ่มหลังข้อ 1.4 (Saved voice): `story_id` ไม่ใช่ `null` และไม่มีไฟล์ → `400` `story_not_found`; ไฟล์อ่านไม่ได้ → เหมือนไม่มี พร้อม log id
- ข้อ 1.5 (token): token ของบรรทัดใน EP + token ของบล็อก Story ไม่เกิน 32,000 → ไม่ใช่ `400` `transcript_too_long` พร้อม `tokens` (รวม) และ `story_tokens` (D14); tokenizer ไม่มี → `503` `not_ready` แบบเดิม
- ผ่านทุกข้อและจองช่อง GPU สำเร็จแล้ว (ใต้ lock ของ draft): เขียน key ของคลิปใน `clip-stories.json` (ลบ key เมื่อ `null`) แล้วอ่าน Story ที่ใช้; ถูกปฏิเสธข้อใด (รวม `gpu_busy`, `draft_exists`) → ไม่เขียน key (D5, D15)
- `order` (spoil-maker D82) เพิ่ม `story_id` และ `story_title` (ชื่อตอนเริ่ม หรือ `null`)
- Draft job `kind: "polish"`: อ่าน Story ที่ `clip_id` ของ Spoil draft จำ ตอนรับคำขอ หลังเช็คของเรียบเรียงใหม่ผ่าน; Story ไม่มีแล้ว → ไม่มีบล็อก; `order` ยัง `null` (หน้าเว็บบอกเรื่องที่ใช้จาก `GET /api/story-clips` กับ `GET /api/stories`)
- `kind: "pick"` ไม่อ่าน Story (D4)
- ลบคลิป (`DELETE /api/spoil/clips/{id}`) ลบ key ของคลิปใน `clip-stories.json` (D7, D16)
- spoil-maker spec มีโน้ตชี้มาที่ story-kb ในแถวขั้น 1, Draft job ข้อ 1, `order`, เรียบเรียงใหม่ (D16)

### Frontend

- แถบ tab: ติดตั้ง · คลิป · คลังความรู้ (`#/stories`) · สปอย (D9); `tabOf` จับ `#/stories/…` เป็น `stories`
- `#/stories` รายการ; `#/stories/new` หน้าแก้ว่าง (บันทึกครั้งแรก `POST` แล้วเปลี่ยน hash เป็น `#/stories/{id}`); `#/stories/{id}` หน้าแก้ของ Story นั้น
- หน้าแก้เช็คกฎของ Data ก่อนส่ง แสดง error ใต้ช่อง; `400` `invalid_story` จาก backend → error ใต้ช่องตาม `field`
- ปุ่มบันทึกกดไม่ได้ระหว่างรอคำตอบ; สำเร็จ → ฟอร์มเป็นไม่มีที่ยังไม่บันทึก ก่อนเปลี่ยน hash (D16)
- ตัวกันออก (D16): `useHash` รับ callback จากหน้าแก้; `hashchange` ขณะยังไม่บันทึก → `window.confirm("ออกโดยไม่บันทึก?")` ก่อน `setHash`; ปฏิเสธ → คืน hash เดิมด้วย `history.replaceState` (ไม่เกิด `hashchange` ซ้ำ) และหน้าแก้อยู่ต่อพร้อมค่าที่พิมพ์; ปิดแท็บ → `beforeunload` (D11)
- ลบ: กล่องยืนยันแบบ `ModalDialog` ของ spoil-maker; สำเร็จ → `#/stories`
- ขั้น 1: อ่าน `GET /api/stories` และ `GET /api/story-clips` พร้อมรายการคลิป; อ่านใหม่เมื่อหน้ากลับมา focus (`visibilitychange`) เพราะลิงก์เพิ่มและแก้เรื่องเปิดแท็บใหม่ (D16)
- เลือกคลิป → ช่อง Story ตั้งที่ Story ที่คลิปจำ; ไม่อยู่ใน `GET /api/stories` (ถูกลบ) → "ไม่ใช้"; เปลี่ยนช่องไม่ส่ง request (D15)
- ตัวนับ token: `ep.tokens + story.tokens` / `limit`; Story `tokens` `null` → ตัวนับ "— / —" และปุ่มร่างกดไม่ได้พร้อม `tokens_not_ready` แบบ EP (D14)
- กดร่าง → `POST /draft-jobs` ส่ง `story_id` ของช่อง; `400` `story_not_found` → อ่านรายการ Story ใหม่ ช่องเป็น "ไม่ใช้" พร้อม Alert
- ค่าของขั้น 1 จาก `order` (spoil-maker D87): ช่อง Story ใช้ `order.story_id` (ไม่อยู่แล้ว → "ไม่ใช้"); "ลองอีกครั้ง" ส่ง `order.story_id` เดิม (D15)
- ระหว่าง Draft job ยังไม่จบ ช่อง Story เป็นข้อความ `order.story_title` หรือ "ไม่ใช้" (spoil-maker D82); การ์ดความคืบหน้า (spoil-maker D81) แสดง "เรื่อง: {story_title}" เมื่อไม่ `null`
- กล่องเรียบเรียงใหม่: อ่าน `GET /api/story-clips` กับ `GET /api/stories` ตอนเปิด แสดงเรื่องที่ใช้ (D16)
- backend ไม่ตอบ → `OfflinePanel` แบบ tab อื่น

ข้อความ error:

| code | ข้อความ | ทางต่อ |
|---|---|---|
| `invalid_story` | ตาม `field`: "ใส่ชื่อเรื่อง", "ชื่อเรื่องยาวเกิน 100 ตัวอักษร", "บทความยาวเกิน 5,000 ตัวอักษร", "ตัวละครได้ไม่เกิน 30 ตัว", "ใส่ชื่อตัวละคร", "ชื่อตัวละครยาวเกิน 40 ตัวอักษร", "ชื่อตัวละครซ้ำ", "คำอธิบายยาวเกิน 200 ตัวอักษร" | แก้ช่องนั้น |
| `story_not_found` | "ไม่พบเรื่องนี้ในคลังความรู้แล้ว" | อ่านรายการ Story ใหม่ ช่องเป็น "ไม่ใช้" |
| `transcript_too_long` (มี `story_tokens`) | "EP กับเรื่องรวม {tokens} token เกิน 32,000 (เรื่อง {story_tokens})" | ลดความยาวต่อ EP หรือย่อบทความ |
| `not_found` (หน้าแก้) | "ไม่พบเรื่องนี้" | ลิงก์กลับคลังความรู้ |

### Ops

- start backend: ลบ `media/stories/*.tmp`; ลบ key ใน `clip-stories.json` ที่ Temp clip ไม่มี json หรือ Story ไม่มีไฟล์
- `clip-stories.json` อ่านไม่ได้ → ถือว่าว่าง, log เหตุผล, เขียนใหม่เมื่อมีการเลือกครั้งถัดไป
- Story ไฟล์อ่านไม่ได้ → ไม่อยู่ในรายการ, log id
- ไม่ log บทความหรือชื่อตัวละคร
- ปิด feature: ไม่มีสวิตช์; ลบ `media/stories/` ได้โดยคลิปทุกคลิปเป็น "ไม่ใช้"
- ดิสก์: Story ละไม่เกินราว 50 KB

## Seams

สองชั้นแบบ spoil-maker: API กับ worker ปลอมของ LLM ที่จดคำสั่ง, หน้าเว็บกับ fetch ปลอม (spoil-maker D47, D51; D13).

1. **Stories API และคำสั่งที่ LLM ได้** `/api/stories/*`, `/api/story-clips`, `/api/spoil-maker/draft-jobs`, `/api/spoil/clips/{id}` ด้วย `TestClient`, root ปลอมใน `tmp_path`, worker ปลอมของ LLM (`llm.requests`)
   - `POST` แล้ว `GET /api/stories/{id}` → ค่าเดิมหลังตัดช่องว่าง ขึ้นบรรทัดใน `title` เป็นช่องว่าง; `GET /api/stories` เรียงแก้ล่าสุดก่อน มี `tokens`
   - `title` ว่าง, บทความ 5,001 ตัวอักษร, ตัวละคร 31 ตัว, ชื่อตัวละครซ้ำ → `400` `invalid_story` พร้อม `field` ที่ถูก; บทความ 5,000 ตัวอักษร → `201`
   - `kind: "draft"` `story_id` ของ Story → `202`, `GET /api/story-clips` มี key, `order.story_id` และ `story_title` ตรง; `story_id` `null` → key หาย; ไม่มี Story → `400` `story_not_found`
   - token ปลอม EP 30,000 + Story 2,001 → `400` `transcript_too_long` `tokens` 32,001 `story_tokens` 2,001; Story ไม่ใช้ → `202`
   - คำสั่งเขียนบทมีบล็อก Story ก่อน `Transcript, one line each` และบรรทัดชื่อในกฎท้าย; คำสั่งเรียบเรียงมีบล็อกก่อน `The script, one sentence each`; คำสั่งเลือก Shot ไม่มี
   - `story_id` `null` → คำสั่งเขียนบทและเรียบเรียงเท่ากับข้อความที่เก็บเป็นค่าคาดหวังจากก่อน feature นี้
   - `PUT` Story หลังร่าง แล้ว `kind: "polish"` → คำสั่งเรียบเรียงมีค่าใหม่ (D5)
   - `DELETE` Story ที่ 2 คลิปจำ → `204` และ `GET /api/story-clips` ไม่มีทั้ง 2 key
   - `DELETE /api/spoil/clips/{id}` → key ของคลิปหาย; Trim job ของคลิป `done` → key ยังอยู่ (D7)
   - restart (สร้าง app ใหม่บน root เดิม) → Story และ key ยังอยู่; `.tmp` ถูกลบ; key ของคลิปที่ไม่มี json ถูกลบ
2. **หน้าคลังความรู้และขั้น 1** `frontend/src/features/story-kb`, `frontend/src/features/spoil-maker`, `frontend/src/lib/useHash` ด้วย Vitest กับ fetch ปลอม
   - ไม่มี Story → "ยังไม่มีเรื่องในคลังความรู้"; กด "เพิ่มเรื่อง" ใส่ชื่อ เพิ่มตัวละคร 2 ตัว ลบ 1 ตัว บันทึก → `POST` body ตรง, hash เป็น `#/stories/{id}` และไม่ถาม "ออกโดยไม่บันทึก?"
   - กดบันทึก 2 ครั้งเร็วๆ → `POST` ครั้งเดียว
   - เปิด Story เดิม แก้ 2 ช่อง กดบันทึก → `PUT` ครั้งเดียว body ครบ, "บันทึกแล้ว", ปุ่มบันทึกกดไม่ได้จนแก้อีก; `400` `invalid_story` `field` `characters.0.name` → error ใต้ช่องนั้น
   - ชื่อเรื่องว่าง → "ใส่ชื่อเรื่อง" ไม่ส่ง request; ครบ 30 ตัว → ไม่มีปุ่ม "+ เพิ่มตัวละคร"
   - แก้แล้วกด tab อื่น → ถาม "ออกโดยไม่บันทึก?"; ปฏิเสธ → hash เดิม ค่าที่พิมพ์ยังอยู่ ไม่ถามซ้ำ
   - ลบ Story ที่ใช้อยู่ 2 คลิป → กล่องยืนยันบอก "ใช้อยู่ 2 คลิป"; ยืนยัน → `DELETE` แล้ว hash `#/stories`
   - ขั้น 1: เลือกคลิปที่จำ Story → ช่อง Story ตั้งที่เรื่องนั้น และตัวนับรวม token; คลิปที่จำ Story ที่ถูกลบ → "ไม่ใช้"; เปลี่ยนช่องไม่ส่ง request; กดร่าง → `POST /draft-jobs` มี `story_id` ของช่อง
   - ขั้น 1 ระหว่างร่าง → ช่อง Story เป็นข้อความ `order.story_title`; การ์ดความคืบหน้ามี "เรื่อง: {story_title}"
   - กล่องเรียบเรียงใหม่ของคลิปที่จำ Story → "ใช้เรื่อง: {ชื่อ}"

## Testing decisions

- **Copy:** `backend/tests/test_spoil_maker_voices_api.py` — CRUD ที่มีไฟล์ใน root ปลอม, `400` พร้อมฟิลด์, ลบของที่ถูกใช้
- **Copy:** `backend/tests/test_spoil_maker_draft_api.py` — Draft job กับ worker ปลอมของ LLM; คำสั่งที่ worker ได้อยู่ใน `llm.requests` แล้ว
- **Copy:** `backend/tests/test_spoil_trim_api.py` — Trim job จบแล้วเช็คไฟล์ที่เหลือ (D7)
- **Copy:** `frontend/src/features/spoil-maker/components/SavedVoicePage.test.tsx` — หน้ารายการกับลบพร้อมยืนยัน
- **Copy:** `frontend/src/features/spoil-maker/components/SpoilerSetup.test.tsx` — ขั้น 1 กับ fetch ปลอมตาม route และ `setupFixtures.ts`
- **Copy:** `frontend/src/features/spoil-maker/components/DraftProgress.test.tsx` — การ์ดความคืบหน้าและ "ลองอีกครั้ง" ด้วย `order`
- คำสั่งของคลิป "ไม่ใช้" เทียบกับข้อความที่ `script_prompt` และ `polish_prompt` สร้างก่อน feature นี้ (เก็บเป็นค่าคาดหวังใน test) เพื่อพิสูจน์ว่าไม่เปลี่ยน
- ไม่มีเช็คมือกับ Qwen จริงในรอบนี้: คุณภาพการสะกดชื่อดูตอน user trial

## Out of Scope

- ค้นหาหรือดึงบทความจากเว็บเอง (D1)
- ชื่ออื่นหรือชื่อที่ Whisper ถอดผิดของตัวละคร (D2)
- ใช้ Story ตอนเลือก Shot (D4)
- สำเนา Story ใน Spoil draft (D5)
- เล่าเหตุการณ์จากบทความ (D8)
- กันการแก้ Story พร้อมกันจากสองแท็บ: บันทึกหลังทับก่อน (D12)
- ตั้ง Story ของคลิปโดยไม่ร่าง (D15)
- เรียบเรียง hook หรือชื่อตอน (`top_text`) ด้วยชื่อใหม่ (D16)
- ใช้ Story ใน tab คลิป (ถอดบทพูด, บรรยายฉาก)

## Open Questions

None.
