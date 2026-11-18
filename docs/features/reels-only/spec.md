# Spec: reels-only

แอปเหลืองานเดียวคือทำ reel: หน้าสอนกลองกลายเป็น "reel กลอง" ที่ทำแค่ Groove เล่นซ้ำเป็นคลิป และส่วนบทเรียนทุกที่ (หน้าเพลง ป้ายนับ คำบนจอ glossary) หายไป.

**Status:** ready-to-build

## Problem

เจ้าของตอบ ui-nav Blocked 2 กับ 3 ว่า: "ตัวสอนกลองเอาออกแล้วเปลี่ยนเป็น สร้าง reels กลองแทน ให้แค่สร้าง reels กลองได้พอ", "สร้างบทเรียน ออกให้หมด ไม่ได้จะทำบทเรียน", และ "อยากให้มันใช้ง่ายไม่สับสน อะไรที่เกี่ยวกับบทเรียนเอาออกเลย ไม่ต้องเอามา และอะไรที่เกิน ๆ หลงประเด็นเอาออกเลย".

วันนี้หน้า `#/drums` ชื่อ "สอนกลอง" มีรายการ "บทเรียนกลอง" และหน้าแก้ที่มีท่อนสอน 1–6 ท่อน (ป้าย คำอธิบาย ชิ้นที่เน้น ความเร็ว %); หน้าเพลงมีส่วน "สร้างบทเรียน" กับ "บทเรียนจากเพลงนี้"; รายการเพลงนับ "N บทเรียน".

## Solution

- หน้า `#/drums` ชื่อ "reel กลอง": รายการ reel กลอง สร้าง ทำซ้ำ ลบ เหมือนเดิม (D2, D5)
- หน้าแก้ reel กลองเหลือ หัวเรื่อง BPM บรรทัดรอง คำบรรยาย พื้นหลัง Groove จำนวนรอบ ฟังจังหวะ render บันทึก (D2)
- ไม่มีท่อนสอน และไม่มีนับเข้า: คลิปเริ่มที่ห้องแรกของ Groove (D2, D15)
- reel แบบเก่าที่มีหลายท่อนเปิดได้ และถูกรวมเป็น Groove เล่นซ้ำเมื่อบันทึก (D4)
- หน้าเพลงไม่มีส่วนสร้างบทเรียน บทเรียนจากเพลงนี้ และแถบห้องที่พบ; ทางไป reel cover อยู่ครบ (D6)
- route และโค้ดที่มีไว้สร้างบทเรียนจากเพลงเท่านั้นถูกลบ (D7)
- ไม่มีคำว่า บทเรียน สอน หรือท่อนสอน บนจอที่ไหนอีก (D1, D8)

## User Stories

**ผู้ทำคลิป**
1. As a ผู้ทำคลิป, I want สร้าง reel กลองจาก Groove ที่กรอก ตั้ง BPM กับจำนวนรอบ แล้ว render เป็น mp4 กับ .srt, so that ได้คลิปกลองแนวตั้งโดยไม่ต้องตั้งท่อนสอน (D2, D4)
6. As a ผู้ทำคลิป, I want คลิป reel กลองเริ่มที่ห้องแรกของ Groove ทันที ไม่มีนับเข้า, so that คนดูเห็นจังหวะตั้งแต่วินาทีแรก (D15)
2. As a ผู้ทำคลิป, I want เปิด reel กลองที่ทำไว้ก่อน (รวมแบบหลายท่อน) แล้วแก้ต่อหรือ render ใหม่ได้, so that งานเก่าไม่หาย (D4)
3. As a ผู้ทำคลิป, I want หน้าเพลงพาไปทำ reel cover โดยไม่มีส่วนบทเรียนมาเกะกะ, so that รู้ทันทีว่าหน้านี้มีไว้ทำอะไร (D6)
4. As a ผู้ทำคลิป, I want ไม่เห็นคำว่าบทเรียนหรือสอนที่ไหนในแอป, so that ไม่สับสนว่าแอปทำ reel อย่างเดียว (D1, D8)
5. As a ผู้ทำคลิป, I want ลิงก์ `#/drums…` และ `#/songs…` เดิมยังเปิดได้, so that bookmark กับล่าสุดไม่พัง (D5)

## Design

ใช้ component เดิมของแอป ไม่มีจอรอออกแบบ (D10).

| Screen | User stories | Must show | Source |
|---|---|---|---|
| รายการ reel กลอง (`#/drums`) | 1, 4, 5 | หัว "reel กลอง" กับบรรทัดใต้หัวว่า reel จาก Groove ที่กรอกเอง ส่วน reel จากเพลงทำในแกะเพลง (D5), ปุ่ม "reel ใหม่", section `aria-label` "reel ทั้งหมด", ว่าง: "ยังไม่มี reel กลอง" กับปุ่ม "สร้าง reel แรก", แถวละ หัวเรื่อง ความยาว render กี่ครั้ง แก้ล่าสุด ทำซ้ำ ลบ (D2, video-gen D10); dialog ใหม่หัว "reel ใหม่" | existing components |
| หน้าแก้ reel กลอง (`#/drums/{id}`) | 1, 2, 4 | หัวเรื่อง BPM บรรทัดรอง คำบรรยาย พื้นหลัง Groove (ตารางเดิม) และ select "จำนวนรอบ" 1–8 ใต้ Groove (D2); ความยาวคลิป / 90 วินาที (video-gen D16); ฟังจังหวะ render บันทึก (video-gen D14, D22); reel แบบเก่า: Alert info ว่าบันทึกแล้วอะไรหาย เหลือกี่รอบ และกดทำซ้ำในรายการก่อนถ้าอยากเก็บแบบเดิม (D4); ไม่พบ: "ไม่พบ reel นี้" กับลิงก์ "กลับรายการ reel" | existing components |
| ผล render reel กลอง (`#/drums/{id}/renders`) | 1, 4 | เหมือนเดิม คำเปลี่ยน: "กลับไปแก้ reel", "ยังไม่เคย render reel นี้", "กด render ในหน้าแก้ reel แล้วผลจะขึ้นที่นี่" (D8) | existing components |
| หน้าเพลง (`#/songs/{id}`) | 3, 4, 5 | หัวเพลงกับเครื่องเล่น ช่วงแกะ โหมด แกะโน้ต (drum-notes D5, D18), คำเตือนการตีแรก (drum-cover D9, D19), การ์ด Reel cover (drum-cover D11); ไม่มีส่วนสร้างบทเรียน บทเรียนจากเพลงนี้ ผลแกะ (D6); การ์ด Reel cover ขึ้นทุกครั้งที่แกะแล้ว รวมเพลงที่ไม่มีห้อง 4/4 (D6); ยังไม่แกะ: "ตั้งช่วงแล้วกด แกะโน้ต" | existing components |
| รายการเพลง (`#/songs`) | 4 | แถวไม่มี "N บทเรียน"; dialog ลบไม่มีประโยคเรื่องบทเรียน (D9) | existing components |

## Expected Outcome

ผู้ทำคลิปเปิดแอปแล้วเห็นแต่ทางทำ reel คลังของมัน และติดตั้ง ไม่มีที่ไหนพูดถึงบทเรียน.

- **reel กลองใหม่:** กด "reel ใหม่" ใส่หัวเรื่อง แก้ Groove ตั้ง 4 รอบ กด render → ได้ mp4 แนวตั้งกับ .srt ในผล render; คลิปขึ้นหัวเรื่องกับบรรทัดรองทั้งคลิป ทุกชิ้นสว่าง
- **ไม่มีนับเข้า:** reel ใหม่ (100 BPM 1 ห้อง 4 รอบ) ยาว 11.1 วินาที (เดิม 13.5) = 333 เฟรม; เฟรมแรกตัวนับเป็น 1 ของห้องแรก ไม่มีไฮแฮทเบา 4 ครั้งก่อน Groove; `.srt` มี cue เดียว `00:00:00,000 --> 00:00:11,100` เป็นหัวเรื่อง บรรทัดรอง คำบรรยาย (D15)
- **reel แบบเก่า:** เปิด reel ที่มี 3 ท่อน (2+2+2 รอบ) → จำนวนรอบเป็น 6 พร้อมบรรทัดบอก; กดบันทึก → `GET` ได้ `chapters` ท่อนเดียว 6 รอบ ความเร็ว 100
- **หน้าเพลง:** เพลงที่แกะแล้วโชว์ช่วงแกะกับการ์ด Reel cover ต่อกันเลย ไม่มีแถบห้อง

**How success is judged:**
- `grep` ข้อความ "บทเรียน" และ "สอน" ใน string ที่หน้าเว็บโชว์ (`frontend/src` ยกเว้น comment และ test) และใน `message` ของ backend ได้ 0 ตัว
- `POST /api/songs/{id}/preview`, `/listen`, `/lessons` ไม่มีแล้ว
- `uv run pytest`, `npm --prefix frontend run typecheck`, `npm --prefix frontend test`, `npm --prefix frontend run build` ผ่าน
- render reel cover และ reel คาลิมบาได้ไฟล์เหมือนก่อน (test ของ `drum_cover` `kalimba_cover` ผ่านโดยไม่แก้ assertion ยกเว้น test ที่เรียก `video_gen.timeline.build` ตรง)
- render reel กลองจริงหนึ่งตัว: `ffprobe` นับเฟรมได้ `ceil(length_s × 30)` ของสูตรใหม่ และ `.srt` บรรทัดแรกเริ่ม `00:00:00,000` (D15)

## Implementation

### Modules touched

- **`frontend/src/features/video-gen`**
  - `LessonEditor` ตัด `ChapterList` ใส่ select "จำนวนรอบ" ที่แก้ `form.chapters[0].repeats` (D2)
  - `useLessonEditor` ตอนโหลด: `saved` เก็บ lesson ดิบ, `form` เก็บ `chapters` ที่รวมเป็นท่อนเดียวแล้ว, `Editing.legacy` = `saved` เป็นแบบเก่า; `sameFields(form, saved)` จึงเป็น false เองเมื่อแบบเก่า (D4)
  - Alert แบบเก่าหายเมื่อบันทึกสำเร็จ (`saved` ใหม่เป็นท่อนเดียว)
  - ลบ `ChapterList`; `NoteBox` กับ `components/ui/GrooveGrid` คงเดิม
  - ไฟล์ซ้ำที่ค้างใน video-gen (`lib/lesson`, `lib/lesson.test`, `lib/kit`, `lib/setupFixes`, `components/GrooveGrid`, `components/Labeled`, `hooks/useListen`): grep แล้วไม่มีใคร import → ลบ
  - `LessonList`, `RendersPage`, `LessonEditor` เปลี่ยนคำบนจอตาม spec › Design (D8)
- **`frontend/src/lib/lesson`**
  - เพิ่มตัวแปลง `chapters` ↔ จำนวนรอบ: อ่านแล้วรวมรอบ (ไม่เกิน `REPEATS_MAX`) และบอกว่าเป็นแบบเก่าหรือไม่; เขียนเป็นท่อนเดียว (D4)
  - `lengthOf` คำนวณจาก `chapters` ที่จะส่ง ไม่เปลี่ยนสูตร
  - ลบ `CHAPTERS_MAX`, `NEW_CHAPTER`, `SPEEDS`, `LABEL_MAX` ถ้าไม่มีใครใช้; `fieldErrors` เลิกตรวจป้ายกับคำอธิบายของท่อน
- **`frontend/src/lib/nav` + `lib/useHash`**
  - หัวข้อ `drums` ชื่อ "reel กลอง" รายการ "reel ทั้งหมด"; `TAB_LABELS.drums` = "reel กลอง"; comment ที่บอกว่าสอนกลองรอเจ้าของตัดสินลบ (D5)
- **`frontend/src/features/drum-notes`**
  - `SongPage` ลบ `LessonPick`, `LessonSection`, `MadeLessons`, `FoundBars` และทางของ `NO_FOUR_FOUR`; การ์ด Reel cover ขึ้นเมื่อมี `analysis` (D6)
  - ลบ `useLessonPreview`, `useLessonTitles`; `lib/songs` ลบส่วน lesson (`Preview`, `Choice`, `Created`, `Dropped`, `BAR_COUNTS`, `pickableFrom`, `firstPickable`, `NO_FOUR_FOUR`, `BPM_RULE`, `bpmOk`, `droppedText`, `MELODY_BASE`, `songLessonsPath`) และ field `lessons` ของ `Song`/`SongRow` (D7)
  - `SongList` ลบ "N บทเรียน" และประโยคบทเรียนใน dialog ลบ; `MELODY_HINT` เขียนใหม่ (D9)
- **`backend/drum_notes`** + **`backend/routes/drum_notes`**
  - ลบ module `lesson`, route `preview`, `listen`, `lessons`, `Song.lessons`, `SongRow.lessons`, `add_lesson`, `_with_live_lessons`; `delete` ไม่พูดถึงบทเรียน (D7)
  - ลบ `video_gen.lessons.from_song` กับ `create_from` และของใน `drum_notes.groove` ที่มีแต่ `lesson` เรียก; `unsaved` กับ `Placed` คงไว้ (`drum_cover.timeline` ใช้)
  - ก่อนจบ grep import และ symbol ที่ไม่มีใครใช้แล้ว
- **`backend/video_gen`**
  - `lessons.new` (หรือที่สร้างค่าตั้งต้น) เริ่มท่อนเดียว 4 รอบ ไม่มี `NEW_LABEL` (D4)
  - `PUT` ที่เขียนทับ reel แบบเก่าคัดลอก `lesson.before-reels-only.json` ครั้งเดียวก่อน (D12)
  - `message` ที่หน้าเว็บโชว์: "บทเรียน" → "reel", "ท่อนสอน" → ข้อความเรื่องรอบ (D8)
  - `render` แก้แค่ `NOT_RUNNING` เป็นคำของ reel (D8)
  - ตัดนับเข้า (D15): ดู › ตัดนับเข้า
- **docs**
  - ADR-0065, ADR-0066 เขียนแล้ว; ADR-0047 `superseded by ADR-0065`
  - `CONTEXT.md`: สอนกลอง → reel กลอง, ลบ บทเรียนกลอง ท่อนสอน ช่วงบทเรียน, แก้ แกะเพลง Score นับเข้า Groove ล่าสุด เมนูหลัก หัวข้อใหญ่ สปอย (ประโยค "แอปมี 5 หัวข้อ") Reel cover Backing Cover (D1, D8)

### ตัดนับเข้า

ตาม D15; `mixer` และ `render` ไม่แก้ เพราะอ่านทุกอย่างจาก `timeline` (ADR-0041).

- **`backend/video_gen/timeline.py`**
  - `length_s` = `sum(repeats × bars × 4 × beat_s(bpm, speed))` + `TAIL_S`
  - `build` เริ่ม `start = 0`: ไม่มี loop นับเข้า, beats มีแต่ของทุกห้อง เริ่มที่ 1
  - โน้ตนำของ flam ที่เวลา < 0 ไม่ถูกใส่ (D16)
  - ลบ `COUNT_IN_PIECE` และ `"count"` ออกจาก `NoteKind`; docstring ของ `Hit` `Beat` และ comment ของ `NoteKind` ไม่พูดถึงนับเข้า
- **`backend/video_gen/captions.py`** `sections` ไม่มีส่วนหัวของนับเข้า: ส่วนแรกคือท่อนแรกตั้งแต่ 0; docstring ใหม่
- **`backend/video_gen/lane.py`** `segments` ไม่มี segment นับเข้า; docstring `Segment` และ comment `chapter_index` ใหม่
- **`backend/video_gen/frames.py`** `shown_hits` เป็นทุก hit (ไม่มี hit นับเข้าให้กรอง); comment ใหม่
- **`backend/drum_cover/timeline.py`** docstring `lesson` ไม่พูดถึงนับเข้า (พฤติกรรมไม่เปลี่ยน)
- **`frontend/src/lib/lesson.ts`** `lengthOf` ไม่มีห้องนับเข้า; comment ใหม่ (keep the two alike)
- **docs** `CONTEXT.md` › นับเข้า: บอกว่าไม่มีในคลิปไหนของแอปแล้ว (D15)

ความยาวที่เปลี่ยน (สูตรเดียวกันสองฝั่ง):

| reel | เดิม | ใหม่ |
|---|---|---|
| ใหม่: 100 BPM 1 ห้อง 4 รอบ | 13.5 วิ | 11.1 วิ (333 เฟรม) |
| 120 BPM 1 ห้อง 1 รอบ | 5.5 วิ | 3.5 วิ (105 เฟรม) |
| 40 BPM 2 ห้อง 8 รอบ | 103.5 วิ (เกิน) | 97.5 วิ (ยังเกิน 90) |

### คำบนจอ

ข้อความที่เปลี่ยน (D8); test ที่ assert ข้อความเดิมแก้ตาม.

| ที่ | เดิม | ใหม่ |
|---|---|---|
| `nav`, `useHash` | สอนกลอง · บทเรียนทั้งหมด | reel กลอง · reel ทั้งหมด |
| `LessonList` หัว | บทเรียนกลอง | reel กลอง |
| `LessonList` ใต้หัว | — | reel จาก Groove ที่กรอกเอง · reel จากเพลงทำในแกะเพลง |
| `LessonList` ปุ่ม และหัว dialog | บทเรียนใหม่ | reel ใหม่ |
| `LessonList` section | บทเรียนทั้งหมด | reel ทั้งหมด |
| `LessonList` ว่าง | ยังไม่มีบทเรียนกลอง · สร้างบทเรียนแรก | ยังไม่มี reel กลอง · สร้าง reel แรก |
| `LessonEditor`, `RendersPage` ไม่พบ | ไม่พบบทเรียนนี้ · กลับรายการบทเรียน | ไม่พบ reel นี้ · กลับรายการ reel |
| `LessonEditor` reel แบบเก่า | — | บันทึกแล้ว ป้าย คำอธิบาย ชิ้นที่เน้น และความเร็วของแต่ละท่อนจะหาย เหลือ Groove {n} รอบที่ BPM เดียว (จาก {รวม} รอบ เมื่อเกิน 8) · อยากเก็บแบบเดิม กดทำซ้ำในรายการก่อน |
| `RendersPage` | กลับไปแก้บทเรียน · ยังไม่เคย render บทเรียนนี้ · กด render ในหน้าแก้บทเรียน แล้วผลจะขึ้นที่นี่ | กลับไปแก้ reel · ยังไม่เคย render reel นี้ · กด render ในหน้าแก้ reel แล้วผลจะขึ้นที่นี่ |
| `SongList` แถว | {n} บทเรียน | (ลบ) |
| `SongList` dialog ลบ | เสียงเพลงและผลแกะหายไป บทเรียนกลองที่สร้างจากเพลงนี้ยังอยู่ | เสียงเพลงและผลแกะหายไป |
| `songs` `MELODY_HINT` | แกะจังหวะของโน้ตทำนอง (piano, kalimba) เป็น snare บน groove พื้นฐาน | build เขียนตามสิ่งที่ reel ได้จริง (D9) |
| `video_gen.lessons` | ท่อนสอนมีได้ 1–6 ท่อน · ท่อนสอนไม่ถูกต้อง | ท่อนมีได้ 1–6 ท่อน · ท่อนไม่ถูกต้อง |
| `video_gen.lessons` | บทเรียนนี้ไม่มีภาพพื้นหลัง · ไม่พบบทเรียนนี้ · กำลัง render บทเรียนนี้อยู่ | reel นี้ไม่มีภาพพื้นหลัง · ไม่พบ reel นี้ · กำลัง render reel นี้อยู่ |
| `video_gen.render` `NOT_RUNNING` | ไม่มีงาน render บทเรียนกลองที่ยังไม่จบ | ไม่มีงาน render reel กลองที่ยังไม่จบ |

### Data

ไม่เปลี่ยน schema. ท่อนที่หน้าแก้ส่งเสมอ (D4):

```json
{ "chapters": [{ "label": "", "text": "", "focus": [], "repeats": 4, "speed": 100 }] }
```

`song.json` เก่ามี `lessons` ได้; อ่านแล้วข้าม เขียนครั้งหน้าไม่มี (D7).

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| pydantic | 2.14.1 | `BaseModel` ที่ไม่ได้ตั้ง `extra` ข้าม key ที่ไม่รู้จักตอน `model_validate_json` | [Configuration › extra](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) |

### API ที่ลบ

| Route | ก่อน | หลัง |
|---|---|---|
| `POST /api/songs/{id}/preview` | Groove ตัวอย่างของห้องที่เลือก | ไม่มี |
| `POST /api/songs/{id}/listen` | wav ของ Groove ตัวอย่าง | ไม่มี |
| `POST /api/songs/{id}/lessons` | สร้างบทเรียนกลอง | ไม่มี |
| `GET /api/songs`, `GET /api/songs/{id}` | มี `lessons` | ไม่มี `lessons`; `bars` คงไว้ |

`/api/drums/lessons…` และ `/api/songs/{id}/cover…` ไม่เปลี่ยน.

## Seams

test หน้าเว็บที่มีอยู่กับ test API ของเพลง (D11).

1. **หน้า reel กลองและเมนู** `DrumsPage` และ `App` ใน jsdom
   - เปิด `#/drums` → หัว "reel กลอง" ปุ่ม "reel ใหม่" ไม่มีคำว่าบทเรียน
   - เมนูหมวดดนตรี → หัวข้อ "reel กลอง" รายการ "reel ทั้งหมด" ที่ `#/drums`; `#/drums/{id}` เน้นรายการเดิม (ui-nav D9)
   - เปิด reel ท่อนเดียว 4 รอบ → select จำนวนรอบเป็น 4 ไม่มีกลุ่ม "ท่อน n"
   - เปลี่ยนเป็น 6 แล้วบันทึก → `PUT` ส่ง `chapters` ท่อนเดียว `repeats` 6 `speed` 100 ป้ายกับคำอธิบายว่าง
   - เปิด reel 3 ท่อน (2, 2, 2) ความเร็ว 80 → จำนวนรอบ 6 และ Alert บอกการรวม; ยังไม่บันทึก → ไม่มี `PUT`
   - reel ท่อนเดียวที่มีป้าย → Alert ขึ้น
   - reel แบบเก่าเปิดแล้ว → ปุ่มบันทึกกดได้ และเปลี่ยน hash แล้วถามก่อนออก
   - reel แบบเก่ากด ฟังจังหวะ หรือ render → `PUT` ท่อนเดียวไปก่อน request ของงาน
   - reel 5 ท่อนรวม 12 รอบ → จำนวนรอบ 8 และ Alert บอก "จาก 12 รอบ"
2. **หน้าเพลงกับรายการเพลง** `SongsPage` ใน jsdom
   - เพลงที่แกะแล้ว → มีช่วงแกะ การ์ด Reel cover; ไม่มี section "สร้างบทเรียน" "บทเรียนจากเพลงนี้" "ผลแกะ"
   - เพลงที่แกะแล้วแต่ไม่มีห้อง 4/4 → การ์ด Reel cover ขึ้น
   - รายการเพลง → ไม่มีข้อความ "บทเรียน"
3. **API เพลง** `TestClient` ของ backend
   - `POST /api/songs/{id}/lessons` → 404 หรือ 405
   - `GET /api/songs/{id}` ของ `song.json` ที่มี `lessons` → 200 ไม่มี `lessons`
   - `song.json` ที่มี `lessons: ["x"]` → `GET /api/songs` 200 ไม่มี `lessons`, `DELETE` 204, `PUT …/range` 200 และไฟล์ที่เขียนไม่มี `lessons`
   - `POST /api/drums/lessons` → reel ใหม่มี `chapters` ท่อนเดียว 4 รอบ
   - `PUT` reel 3 ท่อนเป็นท่อนเดียว → มี `lesson.before-reels-only.json` เท่าไฟล์เดิม; `PUT` ครั้งที่สอง → สำเนาไม่เปลี่ยน
4. **timeline ไม่มีนับเข้า** test ของ `video_gen` ใน backend (D15)
   - `timeline.build` ของ 120 BPM 1 ห้อง 1 รอบ สแนร์ step 0 → hit แรกที่ sample 0 เป็นสแนร์, ไม่มี hit `count`, beats `[1, 2, 3, 4]` ที่ 0, 0.5, 1.0, 1.5 วิ, `length_s` 3.5
   - `length_s` สองท่อน (50 %, 100 %) = ทุกท่อน + 1.5 ไม่มีห้องนับเข้า
   - `captions.sections` ของท่อนเดียวไม่มีป้าย → ส่วนเดียว 0 ถึง `length_s` เป็นหัวเรื่องกับบรรทัดรอง; `srt_file` → cue แรก `00:00:00,000`
   - `lane.segments` → segment แรกเริ่ม 0 เป็นท่อนแรก ตามด้วยหาง
   - flam ที่ step 0 สองรอบ → รอบแรกไม่มีโน้ตนำ (ไม่มี hit ที่ sample < 0) รอบสองมีโน้ตนำ 0.03 วิ ก่อน; ฟังจังหวะของ lesson นั้นตอบ 200 (D16)
   - `frames` สแนร์ step 4 ที่ 120 BPM ตีที่ 0.5 วิ (เดิม 2.5)
   - API ฟังจังหวะ: wav ยาว `length_s` ใหม่ เสียงแรกที่ 0; render API: mp4 ยาว `length_s` ใหม่
   - หน้าเว็บ `lengthOf` และบรรทัดความยาวใน `DrumsPage.test.tsx` ตามสูตรใหม่

## Testing decisions

- **Copy:** `frontend/src/features/video-gen/components/DrumsPage.test.tsx` — fake fetch ของ lesson และการอ่าน body ของ `PUT`; test ที่พึ่ง `ChapterList` เขียนใหม่ตาม Seam 1
- **Copy:** `frontend/src/features/drum-notes/components/SongsPage.test.tsx` — test ของส่วนบทเรียนลบ; test การ์ด Reel cover กับ DrumsStart คงไว้
- **Copy:** `backend/tests/test_drum_notes_songs_api.py` — Seam 3 เพิ่มที่นี่; ลบ `backend/tests/test_drum_notes_lesson_api.py`
- **Copy:** `backend/tests/test_video_gen_lessons_api.py` — ค่าตั้งต้นของ reel ใหม่
- `frontend/src/App.test.tsx` แก้ชื่อหัวข้อ
- `NEW_LABEL` ("ลองเล่นเอง") อยู่ใน `test_video_gen_lessons_api.py`, `test_drum_notes_lesson_api.py` (ลบทั้งไฟล์), fixture ของ `DrumsPage.test.tsx` และ `SongsPage.test.tsx`; `test_video_gen_captions.py` ใส่ป้ายเองจึงคงไว้; `drum_cover.timeline` สร้าง `Lesson` ผ่าน `lessons.unsaved` ไม่เรียกค่าตั้งต้นของ reel ใหม่
- test render ของ video-gen ที่สร้าง lesson เองด้วยหลายท่อนคงไว้: backend ยังรับหลายท่อน (D4)
- **Copy (D15):** test ที่ตัวเลขอ้างนับเข้า แก้เป็นค่าของสูตรใหม่ ห้ามแค่หลวม assertion:
  - `test_video_gen_timeline.py` › half-speed count-in, length, beats after the count-in, round-robin comment
  - `test_video_gen_captions.py:33` และ `:71` — ส่วนหัวนับเข้าหาย จำนวน cue ลดหนึ่ง
  - `test_video_gen_frames.py:30` — สแนร์ step 4 ที่ 120 BPM ตีที่ 0.5 วิ
  - `test_video_gen_render_api.py:72,120-127` — `short_lesson` ยาว 2.5 วิ สแนร์ที่ 0 วิ
  - `test_video_gen_lessons_api.py:86` (11.1), `:158`, `:601` (ฟังจังหวะเริ่มที่โน้ตแรก)
  - `backend/tests/test_drum_cover_timeline.py` › `test_assemble_gives_a_lesson_the_timeline_build_always_gave_it` แก้ hit แรกกับจำนวน hit; test อื่นของ `drum_cover` `kalimba_cover` ไม่แก้
- **ของจริง (D15):** render reel ใหม่ผ่าน API ใน project ชั่วคราว (นอก `media/` ของเจ้าของ) แล้ววัดด้วย `ffprobe -count_frames` และอ่าน `.srt` บรรทัดแรก; ตัวเลขลง progress.md

## Out of Scope

- เปลี่ยนชื่อ `lesson` ในโค้ด API path และ folder บนดิสก์ (D8)
- reel cover และ reel คาลิมบา: ไม่เคยมีนับเข้า ไม่แก้ (D15)
- เปลี่ยน schema ของ `lesson.json` (D4)
- เอาหน้าอื่นออก (D9)

## Open Questions

1. ชื่อในโค้ดที่ยังใช้คำว่า lesson (`video_gen.lessons`, `Lesson`, `LessonFields`, `Chapter`, `lessons_dir`, `media/drums/lessons/`, `/api/drums/lessons`, `lesson_id` ในงาน render, `LessonEditor`, `LessonList`, `useLessons`, `useLessonEditor`, `lib/lesson`, `drumsViewOf`, test `test_video_gen_lessons_api.py`, `DrumsPage.test.tsx`) จะเปลี่ยนเป็น reel ไหม — non-blocking: ผู้ใช้ไม่เห็น และเป็นงาน rename แยกที่ต้อง migrate ไฟล์บนดิสก์ (D8)
2. ~~นับเข้า 1 ห้องตอนต้น reel กลอง เจ้าของอยากตัดไหมหลังเห็นคลิปจริง~~ — ตอบแล้ว: ตัด (D15)
3. นอกจากบทเรียน เจ้าของอยากตัดหน้าไหนอีกไหม (D9 ตรวจแล้วว่าทุกหน้าที่เหลือทำ reel ใช้กับ reel หรือตั้งค่าเครื่อง) — non-blocking: ตัดหน้าเพิ่มเป็น change request ได้ใน `NAV_SECTIONS` และ feature ของหน้านั้น

## Sources

- [Pydantic — Configuration › extra](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) — key ที่ไม่รู้จักถูกข้ามเป็นค่าตั้งต้น (accessed 2026-11-18)
