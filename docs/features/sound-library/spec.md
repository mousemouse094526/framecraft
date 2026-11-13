# Spec: sound-library

tab "คลังเสียง" ให้ผู้ใช้เก็บเสียงพื้น (จิ้งหรีด ฝน ห้องเรียน) ไว้ที่เดียว แล้วใช้ได้ทั้งในช่วงของการ์ตูนเล่าและในคลิปสปอย (D1).

**Status:** ready-to-build

## Problem

คลังเสียงพื้นตอนนี้เป็นหน้า `#/toon/sounds` ที่เข้าได้จากปุ่มในรายการ Series และ toolbar เส้นเรื่องของการ์ตูนเล่าเท่านั้น: ดูเหมือนขั้นที่ซ่อนอยู่ และคลิปสปอยใช้เสียงพื้นไม่ได้เลย (spoil-maker D9). แถบ tab 5 tab ยาวเกินจอมือถือ และไม่บอกว่า tab ไหนเป็นของที่เตรียม tab ไหนสร้างคลิป.

## Solution

- เปิด tab "คลังเสียง" (`#/sounds`) จากแถบนำทาง ต่อจากคลังความรู้ (D1, D2).
- เห็นแถบนำทางแบ่งกลุ่ม "เตรียมของ" กับ "ทำคลิป" และใช้เมนูบนจอแคบ (D3).
- กดปุ่ม info ข้างหัวข้อเพื่ออ่านว่าคลังเสียงใช้ยังไง (D4).
- เอาไฟล์หรือลิงก์เข้า ฟัง เปลี่ยนชื่อ ลบเสียง ได้แบบเดิมของการ์ตูนเล่า (toon D39, D56, D70).
- เลือกเสียงพื้นหนึ่งเสียงพร้อมความดังให้คลิปสปอย (D5).
- เสียงที่เอาเข้าไว้แล้วอยู่ครบหลังอัปเดต (D6).

## User Stories

**ผู้ใช้**
1. As a ผู้ใช้, I want เปิดคลังเสียงจากแถบนำทางโดยตรง, so that ไม่ต้องรู้ว่ามันซ่อนอยู่ในการ์ตูนเล่า (D1, D2)
2. As a ผู้ใช้, I want แถบนำทางแยกของที่เตรียมกับ tab ที่สร้างคลิป และใช้ได้บนจอมือถือ, so that รู้ว่าต้องไปทางไหน (D3)
3. As a ผู้ใช้, I want อ่านคำอธิบายสั้นๆ ของคลังเสียงเมื่อต้องการ, so that รู้ว่าใช้ร่วมกันสอง tab และเอาเข้าได้จากไฟล์หรือลิงก์ (D4)
4. As a ผู้ทำคลิปสปอย, I want เลือกเสียงพื้นจากคลังพร้อมความดังในหน้าตรวจแก้บท, so that คลิปสปอยมีบรรยากาศใต้เสียงบรรยาย (D5)
5. As a ผู้ใช้, I want ลบเสียงที่ยังมีที่ใช้ไม่ได้ พร้อมบอกว่าใครใช้อยู่, so that ไม่มี EP หรือ draft ที่เสียงหายไปเงียบๆ (D7)
6. As a ผู้ใช้เดิม, I want เสียงที่เอาเข้าคลังเสียงพื้นไว้แล้วอยู่ในคลังเสียง และช่วงของ EP ยังเล่นเสียงเดิม, so that ไม่ต้องเอาเข้าใหม่ (D6)

## Design

ออกแบบใน Figma ไฟล์เดิมหลัง plan (setup-status D9). เจ้าของให้สร้างทั้งสี่จอตาม [ui-prompt.md](ui-prompt.md) กับ design system เดิมโดยไม่มีแบบใน Figma (D18).

| Screen | User stories | Must show | Source |
|---|---|---|---|
| แถบนำทาง | 1, 2 | 6 รายการ ลำดับ ติดตั้ง · คลิป · คลังความรู้ · คลังเสียง · สปอย · การ์ตูนเล่า (D2); ตั้งแต่ 640px: แถบ tab มีเส้นคั่นสามกลุ่ม ติดตั้ง, คลิป–คลังเสียง, สปอย–การ์ตูนเล่า ไม่มีข้อความหัวกลุ่ม (D3); แคบกว่า 640px: ปุ่มเดียวชื่อหน้าที่เปิดพร้อมไอคอนเมนู กดแล้วเปิดรายการ ติดตั้ง แล้วหัวกลุ่ม "เตรียมของ" (คลิป, คลังความรู้, คลังเสียง) และ "ทำคลิป" (สปอย, การ์ตูนเล่า) (D3); รายการที่เปิดอยู่เด่นกว่า (spoil-maker D53); ไม่มี scroll แนวนอนที่ 375px | ui-prompt.md (D18) |
| หน้าคลังเสียง | 1, 3, 5, 6 | หัวข้อ "คลังเสียง" กับปุ่มไอคอน info; กดแล้วกล่องคำอธิบายสามข้อใต้หัวข้อ (ข้อความใน Frontend) ปิดด้วยการกดซ้ำ `Esc` หรือคลิกนอกกล่อง (D4); ที่เหลือเหมือนแบบเดิม: รายการเสียง ชื่อแก้ได้ ความยาว ปุ่มฟัง ลบ, คำเตือนสิทธิ์ของเสียงแสดงตลอด, ไฟล์พร้อม % upload, ลิงก์พร้อม % โหลด, error ของไฟล์และลิงก์ (toon D56); ลบเสียงที่ใช้อยู่: ข้อความพร้อมรายการที่ใช้ แต่ละบรรทัดขึ้นต้นด้วยชื่อ tab "การ์ตูนเล่า" หรือ "สปอย" (D7); ว่าง: "ยังไม่มีเสียงในคลัง"; ไม่มีลิงก์ "← การ์ตูนเล่า" ของแบบเดิม: มาจากหน้าอื่นด้วย `back` → ลิงก์ "← กลับ" (D11); เสียงเดิมยังย้ายไม่ครบ: Alert warning "ยังย้ายเสียงเดิมจาก media/toon/sounds ไม่ครบ: เช็คที่ว่างดิสก์แล้วเปิดแอปใหม่" (D10) | ui-prompt.md (D18) — แบบเดิม: [Figma: คลังเสียงพื้น](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8129-80163) |
| เสียงพื้นในหน้าตรวจแก้ของสปอย | 4 | ใต้ระดับเสียงต้นฉบับ: ตัวเลือกเสียงพื้น ค่าแรก "ไม่มีเสียงพื้น" ตามด้วยชื่อเสียงในคลัง (D5); เลือกเสียงแล้วมี slider ความดัง 0–100 ที่ส่งเมื่อปล่อย และปุ่มฟัง (toon D56); คลังว่าง: บรรทัด "ยังไม่มีเสียงในคลัง" พร้อมลิงก์ "ไปคลังเสียง"; ลิงก์ "ไปคลังเสียง" อยู่ข้างตัวเลือกเสมอ เปิด `#/sounds?back=#/spoil/review` (D11); เลือกเสียงที่ถูกลบไปแล้ว: ตัวเลือกกลับค่าเดิม Alert error "เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น"; render ได้ `sound_not_found`: Alert error "ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render" (D13); ระหว่างงานที่ล็อก draft: กดไม่ได้ (spoil-maker D51) | ui-prompt.md (D18) — หน้าเดิม: [Figma: Script review](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390) |
| ผล render ของสปอย | 4 | บรรทัด "เสียงพื้น: {ชื่อเสียง}" ใต้บรรทัด "ต้นฉบับ: {ชื่อคลิป}" เมื่อคลิปมีเสียงพื้น ไม่มีบรรทัดเมื่อไม่มี (legal ข้อ 1) | ui-prompt.md (D18) — หน้าเดิม: [Figma: Render results](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8055-16850) |

หน้าการ์ตูนเล่าไม่ต้องออกแบบใหม่: ปุ่ม "คลังเสียงพื้น" ในรายการ Series และ toolbar เส้นเรื่องเปลี่ยนข้อความเป็น "คลังเสียง" และชี้ `#/sounds`; ข้อความยืนยันลบ Series เปลี่ยน "คลังเสียงพื้น" เป็น "คลังเสียง".

## Expected Outcome

ผู้ใช้เอาเสียงพื้นเข้าที่ tab คลังเสียงครั้งเดียว แล้วใช้ได้ทั้งในช่วงของการ์ตูนเล่าและในคลิปสปอย.
- **ผู้ใช้เดิมเปิดแอปหลังอัปเดต:** tab คลังเสียงมีเสียงทุกตัวที่เคยเอาเข้า; EP ที่ render ใหม่เล่นเสียงพื้นเดิม
- **คลิปสปอยกับเสียงฝน 20 วินาที:** คลิป 60 วินาทีได้เสียงฝนวนสามรอบใต้เสียงบรรยาย ตัดที่ท้ายคลิป
- **ลบเสียงฝนที่ draft ใช้:** "ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้" พร้อมบรรทัด "สปอย · Spoil draft: {ชื่อคลิป} · EP 2"
- **จอ 375px:** แถบนำทางเป็นปุ่มเดียว ไม่มี scroll แนวนอน

**How success is judged:**
- `media/toon/sounds/` ที่มีสองเสียง start แอปใหม่ → `GET /api/sounds` ได้สองเสียง id เดิม และ `media/toon/sounds/` ไม่อยู่แล้ว
- Render job ของสปอยที่มีเสียงพื้น: mp4 มีเสียงพื้นตลอดคลิป (วัดจากระดับเสียงของช่วงที่ไม่มีบรรยาย > เงียบ)
- `#/toon/sounds` เปิดหน้าคลังเสียง
- เช็คมือบนแอปจริงที่ 375px และ 1440px: 375px ไม่มี scroll แนวนอนและเห็นปุ่มเมนู; 640px ขึ้นไปเห็นแถบ tab แบบกลุ่ม (จดผลใน `progress.md`)
- `/api/toon/sounds` ได้ `404`

## Implementation

### Modules touched

- **`backend.sounds`** (ใหม่ module เดียว แบบ `backend.stories`, ADR-0037, ADR-0039)
  - ย้ายจาก `toon.sounds` ทั้งหมด: Sound import slot, `list_all`, `rename`, `delete`, `sound_file`, `clean_on_start`, `convert_command` (D6)
  - ย้ายจาก `toon.store`: `StoredSound`, `SOUND_ID`, `read_sounds`, `write_sounds`, `reconcile_sounds`, `m4a_ids` (toon D70, D71)
  - `lock`: RLock ของคลังเสียงเอง แทน `toon.store.lock` (D7)
  - `sound_users`: รายการตัวเช็คที่ feature ลงทะเบียน (D7, ADR-0033)
  - `exists(project, sound_id)` และ `path(project, sound_id)`: ที่ feature อื่นใช้เช็คและอ่านไฟล์
  - ค่าเสียงที่แปลง (aac 192k 48 kHz stereo) ไม่ import จาก `toon.compose` แล้ว: ย้ายเป็นค่าของ `backend.sounds` และ `toon.compose` อ่านจากที่นี่
- **`backend.routes.sounds`** (ใหม่): ทุก route ของ API ด้านล่าง; `backend.routes.toon` ลบ route `/sounds…` ทั้งหมด
- **`backend.paths`**: `sounds_dir` (`media/sounds/`), `sounds_file`, `sounds_partial_dir` (`media/sounds/.partial/`) แทน `toon_sounds_dir` และ `toon_sounds_file`; `legacy_sounds_dir` (`media/toon/sounds/`) ใช้ตอนย้ายเท่านั้น; upload, `folder` ของ yt-dlp และไฟล์ `.m4a.partial` ตอนแปลงใช้ `sounds_partial_dir` แทน `toon_partial_dir`; `clean_on_start` ล้าง `sounds_partial_dir` ทั้ง folder (D11)
- **`backend.app`**: `JobEntry` ของ Sound import ชี้ `backend.sounds`; การย้าย (ข้อมูล › ย้ายจากที่เดิม) ทำก่อน `clean_on_start`
- **`toon`**
  - `episodes`, `cards`, `writer`, `render` อ่านคลังผ่าน `backend.sounds` แทน `toon.store`
  - ลงทะเบียนตัวเช็คที่คืน label ของทุก EP ที่มีช่วงใช้เสียง (ย้ายจาก `toon.sounds.sound_users`) พร้อม `toon.store.lock` (D11)
  - ขั้นเขียนผลของ Cards job เช็ค `sounds.exists` ใต้ `toon.store.lock` แทนการอ่าน `store.read_sounds` (D11)
  - `pageOf` และ `ToonPage` ไม่มีหน้าชนิด `sounds`; `SOUNDS_HASH` ถูกลบ (D11)
  - `toon.sounds` ถูกลบ
- **`spoil_maker`**
  - Spoil draft มี `sound`; settings มี `sound_volume` (ข้อมูล)
  - `PATCH /draft` รับ `sound` (API)
  - Render job ผสมเสียงพื้น (Render job ของสปอย)
  - ลงทะเบียนตัวเช็คที่คืน label เมื่อ Spoil draft ใช้เสียง พร้อม `gpu.slot.draft_lock` (D11, D12)
- **frontend**
  - `lib/useHash`: `TABS` 6 รายการพร้อมกลุ่ม (D2, D3); `tabOf` รู้จัก `#/sounds`; `#/toon/sounds` แทนที่ด้วย `#/sounds` ผ่าน `history.replaceState` ทั้งในค่าเริ่มของ `useHash` และใน listener ของ `hashchange` ก่อน `setHash` (D6, D11)
  - `components/ui/PageLayout`: แถบนำทางแบบกลุ่มและเมนูจอแคบ (D3)
  - `features/sound-library/` (ใหม่): ย้าย `SoundsPage`, `useSounds`, `lib/sounds` จาก `features/toon/`; เพิ่มปุ่ม info (D4); path ของ API เป็น `/api/sounds`; ไม่ import `features/toon` (D11)
  - `components/ui` และ `lib` ของแอป: `CommitField`, `NoticeLine`, `lib/edit`, `lib/notice`, `lib/upload`, `useReadyState` และ icon ที่หน้าคลังเสียงใช้ ย้ายจาก `features/toon/` มาที่นี่ toon import จากที่ใหม่ (D11)
  - `features/toon/`: ปุ่มและข้อความตาม Design; ตัวเลือกเสียงของช่วงอ่าน `features/sound-library/lib/sounds`
  - `features/spoil-maker/`: ตัวเลือกเสียงพื้นในหน้าตรวจแก้ (D5)
  - `App`: tab `sounds`

### ข้อมูล

ทุกอย่างอยู่ใน `media/sounds/` (ADR-0003):

```
media/sounds/
  sounds.json
  {sound_id}.m4a
  .partial/
```

`sounds.json` รูปเดิมของ toon spec › ข้อมูล: `{"version": 1, "sounds": [{"id": "m_01ab23cd", "name": "ฝนตกในป่า", "duration_s": 62.4, "source": "file"}]}`. การตรวจคลังตอน start และระหว่างทำงานตาม toon D70 และ D71 ทุกข้อ เปลี่ยนแค่ folder และ lock เป็น `sounds.lock`.

**ย้ายจากที่เดิม** (D6) ทำครั้งเดียวตอน start ก่อนรับ request:

ขั้นตอน (D10):

1. ไม่มี `media/toon/sounds/` → ไม่ทำอะไร
2. ไม่มี `media/sounds/`, หรือมีแต่ไม่มี `sounds.json` และไม่มี `*.m4a` → ลบ `media/sounds/` ทั้ง folder (รวม `.partial/`, `shutil.rmtree`) แล้ว `os.replace` `media/toon/sounds/` เป็น `media/sounds/` (ดิสก์เดียวกัน, ADR-0003); log `moved sound library to media/sounds`
3. มีเสียงทั้งสองที่ → รวม: ทุก `{id}.m4a` ของที่เดิมที่ id ยังไม่มีใน `media/sounds/` ย้ายด้วย `os.replace` ทีละไฟล์ พร้อมรายการของมันจาก `sounds.json` เดิม (ไม่มีรายการ → ชื่อ = id แบบ toon D70) ต่อท้าย `sounds.json` ใหม่; id ที่มีอยู่แล้วทั้งสองที่ใช้ของ `media/sounds/`; จบแล้วลบ `media/toon/sounds/` เมื่อเหลือแค่ไฟล์ที่ซ้ำ `sounds.json` และ `.partial/`; log จำนวนที่รวม
4. ข้อ 2 หรือ 3 ล้มด้วย `OSError` → log error; สิ่งที่ย้ายแล้วอยู่ที่ใหม่ ที่เหลืออยู่ที่เดิมครบ; start ครั้งถัดไปทำข้อ 3 ต่อ (ข้อ 3 ทำซ้ำได้โดยไม่ซ้ำ id)
5. `.partial/` ที่ย้ายมาด้วยถูกล้างโดย `clean_on_start` ตามเดิม
6. หลังขั้นตอนนี้ `media/toon/sounds/` ยังมี m4a อยู่ → `GET /api/sounds/legacy` ตอบ `{"left_behind": "media/toon/sounds"}` (ไม่มี → `null`) และหน้าคลังเสียงแสดง Alert warning "ยังย้ายเสียงเดิมจาก media/toon/sounds ไม่ครบ: เช็คที่ว่างดิสก์แล้วเปิดแอปใหม่" (D10)

**Spoil draft** (spoil-maker spec › Spoil draft) เพิ่ม key `sound` ระดับ draft: `{"sound_id": "m_01ab23cd", "volume": 30}` หรือ `null`. ไฟล์เก่าที่ไม่มี key อ่านเป็น `null`; `version` คง 2. ร่างใหม่ (Draft job `kind: "draft"`) เขียน `null` เสมอ (D5); เรียบเรียงใหม่ไม่แตะ.

`sound` เป็นของ Spoil draft จึงตาม draft: หายเมื่อ draft ถูกลบหรือร่างใหม่ตาม ADR-0021 และ ADR-0022 ของ draft เดิม; `sound_volume` ใน settings อยู่ต่อ.

**settings ของสปอย** เพิ่ม `sound_volume`: 0–100 ทีละ 5 ตั้งต้น 30 (D5). `PATCH /draft` ที่ส่ง `sound` ที่มี `volume` เขียน `sound_volume` ลง settings ด้วย ใต้ lock เดิม (spoil-maker D71). เลือกเสียงโดยไม่ส่ง `volume` → ใช้ `sound_volume`.

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| ffmpeg (imageio-ffmpeg 0.7.0) | 7.1 | `-stream_loop -1` ที่ input ของเสียงพื้นวนจากต้นไฟล์ไม่จบ; `atrim`/`-t` ตัดที่ความยาวคลิป; `volume` คูณความดัง; `amix` `normalize=0` ผสมสามเสียง | [ffmpeg main options](https://ffmpeg.org/ffmpeg.html#Main-options), [ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) |
| Python | 3.12 | `os.replace` ย้าย folder ภายในดิสก์เดียวกันแบบ atomic; ล้มเมื่อปลายทางเป็น folder ที่ไม่ว่าง | [os.replace](https://docs.python.org/3.12/library/os.html#os.replace) |

### Sound users

ตัวเช็คที่ feature ลงทะเบียน (D7, D11, ADR-0038):

| feature | นับว่าใช้เมื่อ | `label` | lock ที่ตัวเช็คถือ |
|---|---|---|---|
| toon | ช่วงใดของ EP ใดมี `sound.sound_id` นี้ | `{ชื่อ Series} · EP {n} {ชื่อตอน}` | `toon.store.lock` |
| spoil | Spoil draft มี `sound.sound_id` นี้ (Render job ใช้สำเนา, D12) | `Spoil draft: {ชื่อคลิป} · EP {n}` | `gpu.slot.draft_lock` |

- ลำดับ lock (D7): `gpu.slot.draft_lock` → `toon.store.lock` → `sounds.lock`. ลบเสียงถือทั้งสามตามลำดับนี้ตั้งแต่เช็คถึงเขียน `sounds.json` จึงไม่มีช่วงไหนเลือกเสียงที่กำลังลบได้
- การลงทะเบียนส่งคู่ `(rank, lock, check)` (D11): `backend.sounds` ไม่ import feature แต่ถือ lock ที่ได้มาเรียงตาม `rank` (spoil 10, toon 20) แล้วจึง `sounds.lock`; ตัวเช็คถูกเรียกขณะถือ lock ทั้งหมดแล้ว จึงไม่ต้อง acquire เอง (RLock ซ้ำได้)
- ทุกที่ที่ feature รับ `sound_id` (`PATCH` ช่วงของ toon, `PATCH /draft` ของสปอย) เช็ค `sounds.exists` ขณะถือ lock ของ feature เอง: ลำดับเดียวกัน
- ตัวเช็คไม่ถือ lock อื่นนอกจากที่ตาราง และไม่เรียก `backend.sounds`

### Status check

ไม่มีแถวใหม่ (ADR-0009). แถวที่ต้องผ่าน:

| งาน | แถว |
|---|---|
| Sound import ไฟล์ | `ffmpeg` |
| Sound import ลิงก์ | `ffmpeg`, `yt_dlp`, `deno` |
| Render job ของสปอยที่มีเสียงพื้น | แถวเดิมของ spoil-maker ไม่เพิ่ม |

### API

ทุก route ใต้ `/api/sounds`; พฤติกรรม body และ error เหมือน `/api/toon/sounds` เดิมทุกข้อ (toon spec › คลังเสียงพื้น, toon D56) ยกเว้น `in_use`:

| Method | Path | ใช้ทำอะไร | ผล |
|---|---|---|---|
| `GET` | `/sounds` | รายการเสียง | `200` |
| `PATCH` | `/sounds/{mid}` | `{name}` | `200`; `400` `invalid_request`; `404` `not_found` |
| `DELETE` | `/sounds/{mid}` | ลบ | `204`; `409` `in_use` พร้อม `users`; `404` `not_found` |
| `GET` | `/sounds/{mid}/file` | ฟังเสียง (`audio/mp4`) | `200`; `404` `not_found` |
| `POST` | `/sounds/imports/check` | เช็คก่อนส่งไฟล์ (ADR-0028) | `200`; `400` `file_too_large`; `409` `busy`; `503` `not_ready` |
| `POST` | `/sounds/imports?name=&size=` | ไฟล์ body ดิบ (ADR-0028) | `201` เสียง; error เดิม |
| `POST` | `/sounds/downloads` | `{url}` ลิงก์ (ADR-0029) | `202` งาน; error เดิม |
| `GET`, `DELETE` | `/sounds/import/current` | งานลิงก์ปัจจุบัน, ยกเลิก | เดิม |
| `GET` | `/sounds/legacy` | เสียงเดิมที่ยังย้ายไม่ครบ (ข้อมูล › ย้ายจากที่เดิม ข้อ 6) | `200` `{left_behind}` |

- `in_use`: `{"code": "in_use", "message": "ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้", "users": [{"tab": "toon", "label": "..."}, {"tab": "spoil", "label": "..."}]}`; toon ก่อน spoil; ภายใน toon เรียงตาม Series แล้วเลข EP (D7)
- `/api/toon/sounds…` ทุกเส้นได้ `404` (D6)

Spoil draft:

| Method | Path | Body | ผล |
|---|---|---|---|
| `PATCH` | `/api/spoil-maker/draft` | เพิ่ม `sound?: {sound_id, volume?} \| null` | `200` draft; `400` `sound_not_found` (ไม่มีในคลัง), `invalid_request` (`volume` ไม่ใช่ 0–100 ทีละ 5); `409` `draft_locked` |
| `GET` | `/api/spoil-maker/draft` | — | `sound` ของ draft ตามที่เก็บ ไม่เช็คคลัง (D13) |
| `GET`, `PATCH` | `/api/spoil-maker/settings` | เพิ่ม `sound_volume` | ค่าผิด `400` `invalid_settings` |

### Render job ของสปอย

ต่อจาก spoil-maker spec › Render job:

1. เช็คคำขอเพิ่มหนึ่งข้อต่อจาก `missing_shots`: `sound` ไม่ใช่ `null` และไม่มีในคลัง → `400` `sound_not_found` (D8)
2. ใน `draft_lock` เดียวกับที่งานอ่าน draft สำหรับ render ก๊อป `{sound_id}.m4a` เข้า `media/spoil-maker/.render/` (`sounds.path`); ไม่มีแล้ว → `failed` `sound_not_found`; ffmpeg อ่านสำเนา (D12)
3. ขั้นผสม (ขั้น 3.4 เดิม): เสียงพื้นเป็น input ที่สามด้วย `-stream_loop -1` คูณ `volume / 100` แล้วผสม `amix` `normalize=0` กับเสียงต้นฉบับและเสียงบรรยาย; ตัดที่ความยาวของวิดีโอ (D5)
4. `sound` เป็น `null` → filter graph เดิมทุกตัวอักษร (test เดิมผ่านโดยไม่แก้)

- `{name}.json` ของผล render เพิ่ม `sound_name` ชื่อเสียงตอน render หรือ `null`; ไฟล์เก่าไม่มี key อ่านเป็น `null`
- ผล render แสดงบรรทัด "เสียงพื้น: {sound_name}" ใต้บรรทัด "ต้นฉบับ" เมื่อไม่ใช่ `null` (legal ข้อ 1)

### Frontend

- `#/sounds` เปิดหน้าคลังเสียง; `tabOf("#/sounds")` เป็น `sounds`; `#/sounds/…` ไม่มี
- `#/toon/sounds` → `#/sounds` (Modules touched › `lib/useHash`, D6, D11)
- `TABS` เก็บกลุ่มของแต่ละ tab: `setup` ไม่มีกลุ่ม, `prep` (คลิป คลังความรู้ คลังเสียง), `make` (สปอย การ์ตูนเล่า) (D3)
- เมนูจอแคบ: ปุ่มมี `aria-expanded`; รายการปิดเมื่อเลือก, `Esc`, หรือคลิกนอก; focus กลับที่ปุ่มเมื่อปิดด้วย `Esc`
- tab คลังเสียงไม่ gate ทั้งหน้า: gate เฉพาะการเอาเข้า ตาม Status check
- poll `/api/sounds/import/current` ด้วย `usePollWhile` ระหว่างงานลิงก์; `useLeaveGuard` ระหว่าง upload (ตามเดิม)
- กล่อง info (D4) ข้อความตายตัว:
  - "ใช้ร่วมกันทั้งการ์ตูนเล่าและสปอย: การ์ตูนเล่าเลือกเสียงพื้นต่อช่วง สปอยเลือกหนึ่งเสียงต่อคลิป"
  - "เสียงพื้นคือเสียงบรรยากาศที่เล่นวนใต้เสียงเล่า เช่น เสียงจิ้งหรีด เสียงฝน เสียงห้องเรียน"
  - "เอาเข้าได้จากไฟล์เสียงหรือวิดีโอในเครื่อง หรือวางลิงก์ แอปแปลงเป็นไฟล์เสียงให้เอง"
- ปุ่ม info: `aria-expanded`, `aria-controls` ชี้กล่อง, ชื่อ "วิธีใช้คลังเสียง"
- คำเตือนสิทธิ์ของเสียงคงข้อความเดิม (toon legal ข้อ 4, legal ข้อ 1)
- หน้าตรวจแก้ของสปอยอ่าน `/api/sounds` ตอนเปิดหน้า และอ่านใหม่เมื่อกลับมาที่ tab (`visibilitychange` หรือ hash กลับมา `#/spoil/review`)
- หน้าคลังเสียงไม่มีลิงก์ "← การ์ตูนเล่า" แบบหน้าเดิม; `#/sounds?back={hash}` ที่ `hash` ขึ้นต้นด้วย `#/spoil/` หรือ `#/toon/` แสดงลิงก์ "← กลับ" ไปที่นั้น ค่าอื่นไม่แสดง (D11); "ไปคลังเสียง" ของหน้าตรวจแก้ส่ง `back=#/spoil/review`, ปุ่ม "คลังเสียง" ของการ์ตูนเล่าส่ง hash ของหน้าที่อยู่; `tabOf` ไม่ดู query
- ตัวเลือกเสียงพื้นในหน้าตรวจแก้ เมื่อ `PATCH /draft` ล้ม: ตัวเลือกกลับเป็นค่าของ draft และ Alert error ใต้ตัวเลือก
  - `sound_not_found` → "เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น" แล้วอ่าน `/api/sounds` ใหม่
  - `draft_locked` → ข้อความของ `draft_locked` เดิม (spoil-maker D51)
- render ได้ `400` `sound_not_found` → Alert error "ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render" และอ่าน draft ใหม่
- `in_use`: แต่ละ `users` เป็นบรรทัด `{ชื่อ tab} · {label}` (`toon` → "การ์ตูนเล่า", `spoil` → "สปอย")

### Ops

- log `[api]` ตอนย้าย: `moved sound library to media/sounds` หรือ warning เมื่อมีทั้งสอง (ข้อมูล › ย้ายจากที่เดิม)
- ย้อนไปแอปรุ่นก่อน feature นี้: ปิดแอปแล้วย้าย `media/sounds/` กลับเป็น `media/toon/sounds/` เอง ก่อนเปิดรุ่นเก่า (D10); README บอกขั้นนี้
- README ภาษาไทยเปลี่ยนชื่อ "คลังเสียงพื้น" เป็น "คลังเสียง" และ path เป็น `media/sounds/` ทุกที่ที่พูดถึง

## Seams

ใช้ seam ที่มีอยู่แล้วสามที่ ไม่มีที่ใหม่ (D9).

1. **คลังเสียงผ่าน HTTP** `backend` › `/api/sounds` (ย้าย `backend/tests/test_toon_sounds_api.py`)
   - ทุก test เดิมผ่านกับ path ใหม่โดยไม่เปลี่ยนสิ่งที่เช็ค ยกเว้น `in_use` ที่เป็น `users`
   - มี `media/toon/sounds/` สองเสียงแล้ว start → `GET /api/sounds` ได้สองเสียง id เดิม; `media/toon/sounds/` ไม่มีแล้ว
   - มี `media/sounds/` หนึ่งเสียง และ `media/toon/sounds/` สองเสียง (หนึ่ง id ซ้ำ) แล้ว start → `GET /api/sounds` ได้สองเสียง; `media/toon/sounds/` ไม่มีแล้ว
   - มี `media/sounds/` ที่มีแค่ `.partial/` → ย้ายทั้ง folder ได้
   - ย้ายไฟล์ที่สองล้ม (`os.replace` patch ให้ `OSError`) → start ได้; `GET /api/sounds/legacy` `left_behind` ไม่ใช่ `null`; import หนึ่งเสียงแล้ว start ใหม่ (ไม่ patch) → เสียงครบทั้งหมด `left_behind` `null`
   - `/api/toon/sounds` → `404`
   - EP ที่ช่วงชี้ `m_…` เดิม: `PATCH` ช่วงด้วย id นั้นผ่าน; ลบเสียงนั้น → `409` `in_use` `users[0].tab` `toon`
   - Spoil draft ที่ `sound` ชี้เสียง → ลบ → `409` `in_use` `users` มี `tab` `spoil`
   - Render job ของสปอยกำลัง `rendering` ด้วยเสียง แล้ว `PATCH /draft` `sound: null` และลบเสียง (`204`) → งานจบ `done` และ mp4 มีเสียงพื้น (D12)
   - ลบเสียงพร้อมกับ `PATCH /draft` เลือกเสียงเดียวกันใน thread อื่น 50 รอบ → ทุกรอบได้ผลอย่างใดอย่างหนึ่ง (ลบได้และ PATCH ได้ `sound_not_found`, หรือ PATCH ได้และลบได้ `409`); ไม่ค้าง (timeout 5 วินาที)
2. **Render job ของสปอย** `backend` › `/api/spoil-maker/renders` (`backend/tests/test_spoil_maker_render_api.py`)
   - `sound` `null` → คำสั่ง ffmpeg เหมือนเดิมทุกตัวอักษร
   - เสียงพื้นยาว 1 วินาที `volume` 50 กับคลิป 3 วินาที (ffmpeg จริง) → mp4 ยาวเท่าเดิม และช่วงวินาทีที่ 2–3 ไม่เงียบเมื่อเสียงบรรยายและต้นฉบับเป็น 0
   - draft ชี้เสียงที่ไม่มีในคลัง → `400` `sound_not_found`
   - `PATCH /draft` `sound` `{sound_id, volume: 45}` → `GET /settings` มี `sound_volume` 45; ร่างใหม่ → `sound` `null`
3. **แถบนำทางและหน้าคลังเสียง** (e2e) `frontend` › `App` กับ `testing/testBackend.ts`
   - แถบนำทางเรียง ติดตั้ง · คลิป · คลังความรู้ · คลังเสียง · สปอย · การ์ตูนเล่า; กด "คลังเสียง" → `#/sounds` เห็นรายการเสียง
   - เปิด `#/toon/sounds` → hash เป็น `#/sounds`
   - กดปุ่ม info → เห็นสามข้อ; `Esc` → ปิด
   - ปุ่มเมนู: กดแล้ว `aria-expanded` `true` เห็นหัว "เตรียมของ" และ "ทำคลิป"; `Esc` ปิดและ focus กลับที่ปุ่ม (jsdom ไม่วาด layout: เช็คพฤติกรรม ไม่เช็คความกว้าง)
   - หน้าตรวจแก้ของสปอย: เลือกเสียง → `PATCH /draft` มี `sound`; ปล่อย slider → `PATCH /draft` หนึ่งครั้งมี `volume`; คลังว่าง → ลิงก์ "ไปคลังเสียง"
   - render ได้ `400` `sound_not_found` → Alert "ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render"
   - `PATCH /draft` ได้ `400` `sound_not_found` → ตัวเลือกกลับเป็นค่าเดิม เห็น "เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น"
   - กด "ไปคลังเสียง" → `#/sounds?back=#/spoil/review` มีลิงก์ "← กลับ"; กดแล้วกลับหน้าตรวจแก้ และรายการเสียงอ่านใหม่
   - ลบเสียงได้ `409` `in_use` สอง `users` → เห็นสองบรรทัด "การ์ตูนเล่า · …" และ "สปอย · …"
   - `GET /api/sounds/legacy` ไม่ใช่ `null` → Alert warning บนหน้าคลังเสียง
   - ผล render ที่ `sound_name` "ฝนตก" → บรรทัด "เสียงพื้น: ฝนตก"

## Testing decisions

- **Copy:** `backend/tests/test_toon_sounds_api.py` — ย้ายทั้งไฟล์เป็น `backend/tests/test_sounds_api.py` เปลี่ยน path และ helper ใน `backend/tests/fakes.py` (`write_library`, `restart`) ให้ชี้ `media/sounds/`
- **Copy:** `backend/tests/test_spoil_maker_render_api.py` — คำสั่ง ffmpeg ที่ `FakeFfmpeg` เก็บไว้ และ test ที่ใช้ `ok_ffmpeg` จริงสำหรับเช็คเสียงในไฟล์
- **Copy:** `backend/tests/test_spoil_maker_voices_api.py` — `voice_in_use` ระหว่างงานที่ยังไม่จบ สำหรับตัวเช็ค Render job
- **Copy:** `frontend/src/features/toon/components/SoundsRender.test.tsx` — ย้ายไป `features/sound-library/` คู่กับหน้า
- **Copy:** `frontend/src/App.test.tsx` — ลำดับ tab และ hash; จอแคบใช้ `window.innerWidth` กับ `matchMedia` ใน `test-setup.ts` ถ้ามี ไม่มีก็เช็คจาก class ที่ซ่อนแถบ (jsdom ไม่วาด layout)
- **Copy:** `frontend/src/features/spoil-maker/components/ScriptReview.test.tsx` — ตัวควบคุมระดับเสียงต้นฉบับ สำหรับตัวเลือกเสียงพื้นและ slider
- **Copy:** `frontend/src/features/spoil-maker/components/RenderResults.test.tsx` (หรือ test ของผล render ที่มี) — บรรทัด "ต้นฉบับ" สำหรับ "เสียงพื้น"
- fixture `/api/toon/sounds` ใน `EpPage.test.tsx`, `SoundsRender.test.tsx` และค่าตั้งต้นของ `testing/testBackend.ts` ย้ายเป็น `/api/sounds` และเพิ่ม `sound` ของ draft กับ `/api/sounds/legacy`
- test ที่ chaos ของ lock (seam 1 ข้อสุดท้าย) ใช้ `threading.Thread` สองตัวกับ `TestClient` ตัวเดียว

## Out of Scope

- เสียงพื้นหลายเสียงหรือต่อประโยคในคลิปสปอย (D5)
- AI เลือกเสียงพื้นให้คลิปสปอย (D5)
- ป้ายหมวดหรือการค้นหาในคลังเสียง (toon D16)
- AI สร้างเสียงพื้นที่ขาด (toon D5)
- เมนูด้านข้าง (D3)

## Open Questions

None.

## Sources

- [ffmpeg main options](https://ffmpeg.org/ffmpeg.html#Main-options) — `-stream_loop` (accessed 2026-11-13)
- [ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) — `amix`, `volume`, `atrim` (accessed 2026-11-13)
- [os.replace](https://docs.python.org/3.12/library/os.html#os.replace) — ย้าย folder ภายในดิสก์เดียว (accessed 2026-11-13)
