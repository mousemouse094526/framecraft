# Spec: audio-player

ทุกปุ่มฟังเสียงในแอปเป็นปุ่ม play/pause ตัวเดียวกัน มีเวลา และเล่นได้ทีละเสียงทั้งแอป.

**Status:** ready-to-build

## Problem

เจ้าของบอกว่า "พวกที่เป็นการกดฟังต่างๆในระบบ ... มันดูแปลกๆ มันควรเป็นเครื่องหมาย กด play และ pause และมี time ไหม มันกดฟังซ้ำและทำให้มันเล่นซ้ำๆทับกันได้ ... ปรับหน่อยทั้งโปรเจคเลย". วันนี้มีสองกลไก:

- `playAudio` (`lib/audio`) สร้าง `<audio>` ใหม่ทุกครั้งที่กด ไม่มี pause ไม่มีเวลา: กดซ้ำ = เสียงซ้อนกัน. ใช้อยู่ 6 จุด.
- `useListen` (`lib/useListen`) ขอ wav ที่ backend ผสมแล้วเล่น หยุดตัวเก่าก่อน แต่ไม่มี pause ไม่มีเวลา และกดซ้ำ = ผสมใหม่ทุกครั้ง. ใช้อยู่ 2 จุด.

ปุ่มส่วนใหญ่เป็นคำว่า "ฟัง" เปล่า ๆ (ภาพของเจ้าของ: หน้าเสียงพากย์ › ออกแบบเสียง). เจ้าของย้ำว่า play/pause ต้องมีครบทุกที่ เวลาเป็นของแถม.

## Solution

- เครื่องเล่นเสียงตัวเดียวของทั้งแอป: เริ่มเสียงใหม่ = เสียงที่เล่นอยู่หยุดก่อน (D1).
- กดปุ่มเดิม = หยุดชั่วคราว; กดอีกครั้ง = เล่นต่อ (D2).
- ทุกจุดฟังเสียงใช้ `PlayButton` ไอคอน play/pause แทนคำว่า "ฟัง" (D3) ชื่อสำหรับ screen reader เปลี่ยนตามสถานะ (D4).
- ปุ่มแสดงเวลา `0:03 / 0:12` ขณะเล่นและหยุดชั่วคราว (D5, D13).
- ปุ่มที่ backend ต้องผสมเสียงบอก "กำลังผสมเสียง…" แล้วเป็น play/pause ไม่ผสมซ้ำถ้าค่าที่บันทึกไม่เปลี่ยน (D7, D13).
- media ทุกตัวในหน้า (ปุ่มเล่น วิดีโอ เสียงเพลงในหน้าเพลง) เล่นได้ทีละตัว โดยไม่แก้โค้ดตัวเล่นวิดีโอ (D8, D13).

## User Stories

**เจ้าของ (คนทำ reel)**
1. As เจ้าของ, I want กดฟังเสียงหนึ่งแล้วกดอีกเสียง เสียงแรกหยุด, so that ไม่มีเสียงซ้อนกัน (D1)
2. As เจ้าของ, I want กดปุ่มเดิมเพื่อหยุดชั่วคราวและกดอีกครั้งเพื่อเล่นต่อ, so that ฟังซ้ำบางช่วงได้โดยไม่เริ่มใหม่ (D2)
3. As เจ้าของ, I want เห็นไอคอน play หรือ pause บนปุ่ม, so that รู้ว่ากดแล้วจะเกิดอะไร (D3)
4. As เจ้าของ, I want เห็นเวลาที่เล่นไปกับความยาวทั้งหมด, so that รู้ว่าเสียงเหลืออีกเท่าไร (D5)
5. As เจ้าของ, I want ปุ่มฟัง reel บอกว่ากำลังผสม แล้วกด pause/เล่นต่อได้โดยไม่ผสมใหม่, so that ไม่รอผสมซ้ำ (D7)
6. As เจ้าของ, I want เปิดวิดีโอหรือเพลงต้นฉบับแล้วเสียงอื่นหยุด (และกลับกัน), so that ทั้งแอปมีเสียงเดียว (D8)
7. As ผู้ใช้ screen reader หรือคีย์บอร์ด, I want ปุ่มบอกว่า "ฟัง …" หรือ "หยุดชั่วคราว …" และเห็นโฟกัส, so that ใช้ได้โดยไม่ต้องเห็นไอคอน (D4)

## Design

ทุกจุดใช้ `PlayButton` ตัวเดียว (D3) สร้างกับ design system เดิม ไม่รอ Figma (D10).

| Screen | User stories | Must show | Source |
|---|---|---|---|
| `PlayButton` (component) | 1–5, 7 | ตารางสถานะด้านล่าง; โฟกัสเห็นชัด; เป้ากด 44px ต่ำกว่า 640px (D3) | pending |
| เสียงพากย์ › ออกแบบเสียง | 1–4 | "ฟัง" → `PlayButton` หน้าตา outline เดิม ข้าง "สุ่ม" ชื่อ "ฟัง เสียงตัวอย่าง"; สุ่มใหม่ = เสียงเดิมหยุด (D6) | pending |
| เสียงพากย์ › แถวเสียงที่บันทึก | 1–4 | "ฟัง" → `PlayButton` outline ชื่อ "ฟัง {ชื่อเสียง}" | pending |
| ทำสปอย › การ์ดประโยค | 1–4 | "ฟัง" → `PlayButton` outline ชื่อ "ฟัง ประโยค {n}"; ไม่มีเสียง = กดไม่ได้ พร้อม title เดิม | pending |
| ทำสปอย › เสียงพื้น | 1–4 | ปุ่มไอคอน → `PlayButton` กรอบไอคอนเดิม ชื่อ "ฟัง {ชื่อ}" | pending |
| การ์ตูนเล่า › การ์ด (เสียงเล่า) | 1–4 | "ฟัง" → `PlayButton` ghost เดิม ชื่อ "ฟัง เสียงเล่าการ์ด {n}" | pending |
| คลังเสียง › แถวเสียง | 1–4 | ปุ่มไอคอน → `PlayButton` กรอบไอคอนเดิม ชื่อ "ฟัง {ชื่อ}"; ความยาวเดิมข้างชื่อคงอยู่ | pending |
| reel กลอง › ฟังจังหวะ | 1, 2, 4, 5 | `PlayButton` คำ "ฟังจังหวะ"; ผสม → play/pause (D7); เกินเพดานเวลา = กดไม่ได้ (video-gen D16); `RefusedAlert` ใต้ปุ่ม | pending |
| reel cover › แถบทำ reel | 1, 2, 4, 5 | `PlayButton` คำ "ฟัง reel" (เดิม "ฟัง"); ผสม → play/pause (D7); เงื่อนไขกดไม่ได้เดิม (drum-cover D18) | pending |

Pending screens: one design prompt in [ui-prompt.md](ui-prompt.md). หน้าเว็บสร้างตาม prompt นั้นกับ design system เดิมโดยไม่รอแบบ (D10).

### สถานะของปุ่ม

| สถานะ | ไอคอน | เวลา | `aria-label` | กดแล้ว |
|---|---|---|---|---|
| พร้อมเล่น | play | — | "ฟัง {x}" | เล่นจากต้น หยุด media อื่นก่อน |
| กำลังผสม (ปุ่มผสมเสียงเท่านั้น) | loader หมุน | — | "กำลังผสมเสียง…" | กดไม่ได้ |
| กำลังเล่น | pause | `0:03 / 0:12` หรือ `0:03` เมื่อยังไม่รู้ความยาว | "หยุดชั่วคราว {x}" | หยุดชั่วคราว |
| หยุดชั่วคราว | play | `0:03 / 0:12` | "ฟัง {x}" | เล่นต่อจากเดิม |
| กดไม่ได้ | play จาง | — | "ฟัง {x}" | — (ถ้าเสียงของมันเล่นอยู่ หยุด, D13) |

- ปุ่มผสมเสียงแสดงคำ ("ฟังจังหวะ", "ฟัง reel") ต่อจากไอคอนในทุกสถานะยกเว้นกำลังผสม; ชื่อขึ้นต้นด้วยคำนั้น: "ฟังจังหวะ" / "หยุดชั่วคราว ฟังจังหวะ" (D4).
- ปุ่มที่มีแต่ไอคอนไม่มีคำ "ฟัง" บนจอ (D3).
- เวลาเป็นตัว `font-mono` `tabular-nums` ขนาด `text-xs` สี `mid` ใน `<span aria-hidden>` ต่อจากไอคอนภายในปุ่มเดียวกัน; ปุ่มกว้างขึ้นตามเวลา (D5).

## Expected Outcome

กดฟังเสียงที่ไหนก็ได้ยินเสียงเดียว หยุดชั่วคราวและเล่นต่อได้จากปุ่มเดิม และเห็นเวลา.

- **กดฟังสองแถวในคลังเสียง:** แถวแรกหยุด กลับเป็นไอคอน play; แถวที่สองเป็นไอคอน pause และเวลาเดิน.
- **กดปุ่มที่กำลังเล่น:** เสียงหยุด ไอคอนเป็น play เวลาค้างที่ตำแหน่งนั้น; กดอีกครั้งเล่นต่อจากตรงนั้น.
- **กดฟังจังหวะแล้วกดอีกครั้งโดยไม่แก้อะไร:** ครั้งที่สองหยุดชั่วคราวทันที "กำลังผสมเสียง…" ไม่ขึ้นอีก.
- **แก้ Groove ระหว่างฟังจังหวะ:** เสียงหยุด ปุ่มกลับเป็นพร้อมเล่น; กดอีกครั้งบันทึกและผสมใหม่.
- **เล่นวิดีโอใน Transcript ระหว่างฟังเสียงประโยค:** เสียงประโยคหยุดชั่วคราว.

**How success is judged:**
- `grep` ไม่พบ `playAudio` และ `new Audio(` นอก module เครื่องเล่นเสียง.
- ไม่มีปุ่มที่บนจอเป็นคำ "ฟัง" อย่างเดียว.
- test ของ module เครื่องเล่นพิสูจน์: เริ่มเสียงที่สอง = เสียงแรกถูก `pause` ก่อน `play` ของเสียงที่สอง.

## Implementation

### Modules touched

- **`lib/player` (module ใหม่: เครื่องเล่นเสียง)**
  - ถือ `HTMLAudioElement` ตัวเดียว (`new Audio()` ไม่ใส่ใน document) สร้างเมื่อเล่นครั้งแรก (D1).
  - state: `{ owner, src, status: "playing" | "paused", position, duration }` หรือ `null`; `duration` เป็น `null` เมื่อ `NaN`/`Infinity`; อ่านผ่าน `usePlayer(owner)` ที่ใช้ `useSyncExternalStore` และคืน state เฉพาะเมื่อ owner ตรง ไม่งั้น `null` (D1).
  - สถานะเป็นของ module เอง ไม่อ่าน `audio.paused` (D13).
  - `toggle(owner, src)`:
    1. owner และ src ตรงกับเสียงปัจจุบัน: `playing` → `pause()` เป็น `paused`; `paused` → `play()` เป็น `playing`.
    2. อื่น ๆ: เพิ่มเลขรอบ, `pause()` เสียงเดิม, ตั้ง `src` และ `currentTime = 0`, `pause()` ทุก `audio`/`video` ในหน้าที่เล่นอยู่และไม่ `muted`, `play()`, state เป็น `playing` ทันที (D1, D2, D8, D13).
  - `release(owner)`: owner ตรง → เพิ่มเลขรอบ `pause()` ล้าง `src` state เป็น `null` (D6).
  - `play()` reject: ไม่มีผลถ้าเป็น `AbortError` หรือเลขรอบเปลี่ยนแล้ว; ไม่งั้น state เป็น `null` (D9, D13).
  - `ended`/`error`: state เป็น `null` เฉพาะเมื่อเลขรอบตรง (D13).
  - `timeupdate`/`durationchange`/`loadedmetadata` → อัปเดต `position`/`duration`.
  - capture listener `play` ที่ `document` ติดครั้งแรกที่ import: media ที่ไม่ `muted` (ไม่ใช่ element ของเครื่องเล่น) เริ่มเล่น → `pause()` media อื่นที่เล่นอยู่ในหน้า และหยุดชั่วคราวเสียงของเครื่องเล่น (state `paused`) (D8, D13).
  - `resetPlayerForTests()` (D13).
- **`components/ui/PlayButton`** (ใหม่)
  - props: `label` (สิ่งที่เล่น), `onPress`, `status` (`ready` | `mixing` | `playing` | `paused`), `position`, `duration`, `text` (คำที่เห็น ไม่บังคับ), `disabled`, `title`, `className` (หน้าตาของจุดนั้น) — ปุ่มแสดงผลอย่างเดียว (D3).
  - `useSound(src)` (hook ใน `lib/player`): `useId` เป็น owner; คืน `{ status, position, duration, toggle }`; `release` เมื่อ unmount หรือ `src` เปลี่ยน หรือ caller บอก `disabled` (D6, D13).
  - ไอคอน `play-16.svg` เดิม; `pause-16.svg` ใหม่ (stroke `#121110` แบบเดียวกัน); `loader.svg` เดิม หมุนด้วย `motion-safe:animate-spin`.
  - โฟกัส: `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-accent`.
- **`lib/useListen`** (D7, D13)
  - `useListen(request, { unsaved, disabled })` คืน `{ state, status, position, duration, press }`; `state` คือ `idle` · `mixing` · `refused` เหมือนเดิม; owner คือ `useId` ภายใน hook.
  - `press()`:
    1. มี wav ที่ผสมไว้ และ `!unsaved` → `toggle` ไม่เรียก `request` (เล่นจบแล้วกด = เล่น wav เดิมจากต้น) (D14).
    2. อื่น ๆ → `mixing` → `request()` (บันทึกก่อนตามเดิม) → wav: revoke URL เก่า เก็บ URL แล้ว `toggle(owner, url)`.
  - `unsaved` หรือ `disabled` เป็นจริง → `release` และ revoke wav (D14).
  - unmount → `release`, revoke, ล้าง cache.
- **ผู้เรียกปุ่มผสมเสียง**
  - reel กลอง (`video-gen` `LessonEditor`): `unsaved` = `!sameFields(form, editing.saved)` เดิม; `disabled` = เกินเพดานเวลา.
  - reel cover (`drum-cover` `ReelSection`): `unsaved` เดิมของหน้า; `disabled` = `!canPlay`; แกะใหม่เปิด `CoverForm` ใหม่ (key `picked_at`) จึงทิ้ง wav.
- **แปดจุดที่ใช้** — ตาราง Design; `lib/audio.ts` ลบ (D1).
- **`lib/format`** — `clockOf(seconds)`: `m:ss` ปัดลงทั้งวินาที (`formatDuration` เดิมไม่ปัดลงจึงไม่ใช้) (D13).

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| React | 19.3 | `useSyncExternalStore` อ่าน store นอก React โดยไม่มี provider | [useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore) |
| DOM `HTMLMediaElement` | browser | `play()` คืน Promise ที่ reject เมื่อเล่นไม่ได้ และ reject ด้วย `AbortError` เมื่อถูก `pause()` หรือเปลี่ยน `src` ก่อนเริ่ม | [play()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play) |
| DOM `HTMLMediaElement` | browser | `timeupdate` ยิงขณะเล่น; `duration` เป็น `NaN`/`Infinity` เมื่อไม่รู้ | [timeupdate](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/timeupdate_event), [duration](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/duration) |
| DOM `HTMLMediaElement` | browser | `play` event ไม่ bubble จับได้ด้วย capture ที่ `document` | [play event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play_event) |
| jsdom | 30 | `play`/`pause`/`load` ไม่ทำงาน (test stub), `paused` ไม่เปลี่ยน, `currentTime` เป็นค่าธรรมดา, `duration` เป็น `NaN` (test ใช้ `Object.defineProperty`) | [jsdom README](https://github.com/jsdom/jsdom#unimplemented-parts-of-the-web-platform) |

## Seams

สาม seam: module กับ component, hook ผสมเสียง, และ test ของหน้าเดิม (D12).

1. **เครื่องเล่นเสียงกับ `PlayButton`** `lib/player` + `components/ui/PlayButton` ใน jsdom
   - กด A แล้วกด B → `pause` ของ A ถูกเรียกก่อน `play` ของ B; ปุ่ม A ชื่อ "ฟัง A" ปุ่ม B ชื่อ "หยุดชั่วคราว B".
   - กด A สองครั้ง → `pause` หนึ่งครั้ง; กดครั้งที่สาม → `play` โดย `currentTime` ไม่ถูกตั้งเป็น 0.
   - B เล่นแล้วกด A อีก → A เริ่มที่ `currentTime` 0.
   - `ended` → ปุ่มกลับเป็น "ฟัง A".
   - `timeupdate` ที่ 3.7 วิ `duration` 12 → ปุ่มแสดง `0:03 / 0:12`; `duration` `NaN` → `0:03`.
   - ปุ่มที่เล่นอยู่ unmount หรือกลายเป็น `disabled` → `pause`.
   - `play` event ของ `<video>` อื่น → เสียงของเครื่องเล่นหยุดชั่วคราว; `<video muted>` → ไม่มีผล.
   - เครื่องเล่นเริ่ม A → `<video>` ที่เล่นอยู่ถูก `pause`.
   - `play()` ของ A reject ด้วย `AbortError` หลังกด B → B ยังชื่อ "หยุดชั่วคราว B".
   - `play()` reject ด้วย error อื่นในรอบปัจจุบัน → ปุ่มกลับเป็น "ฟัง A" ไม่มีข้อความ.
2. **ปุ่มผสมเสียง** `lib/useListen` ใน jsdom
   - กดสองครั้งโดยไม่แก้ → `request` หนึ่งครั้ง ครั้งที่สอง `pause`.
   - `unsaved` เป็นจริงขณะเล่น → สถานะพร้อมเล่น revoke URL; บันทึกแล้วกด → `request` ใหม่.
   - mount ใต้ `StrictMode` แล้วกด → wav เล่น.
   - ข้อปฏิเสธ offline และ `null` → เหมือน test เดิม.
3. **แปดหน้าเดิม** test ของหน้าใน jsdom
   - ทุก test ที่หาปุ่ม "ฟัง" หาชื่อใหม่ ("ฟัง ลมพัด", "ฟัง ประโยค 1", "ฟัง เสียงตัวอย่าง", "ฟังจังหวะ", "ฟัง reel") และยังพิสูจน์ URL ที่เล่นเหมือนเดิม.
   - `DrumsPage.test` "pressed again while playing stops the first wav before the second" เขียนใหม่เป็น "pressed again pauses: one POST, no second mix".
   - `CoverPage.test` query `button("ฟัง")` เป็น `button("ฟัง reel")`.

## Testing decisions

- **Copy:** `frontend/src/lib/useListen.test.ts` — วิธี stub `HTMLMediaElement.prototype.play`/`pause` และ `URL.createObjectURL`.
- **Copy:** `frontend/src/features/sound-library/components/SoundsPage.test.tsx` › "ฟัง plays that sound of the library" — test ระดับหน้าที่อ่าน `src` จาก `play.mock.contexts`.
- `resetPlayerForTests()` เรียกใน `frontend/src/test-setup.ts` `afterEach` ก่อน `cleanup()` (D14): vitest แยก module ต่อไฟล์ แต่ไม่แยกต่อ test และ `useId` ซ้ำได้ข้าม root (D13).
- ชื่อ test เดิมคงความหมาย แก้เฉพาะ query ของปุ่ม ยกเว้น test ของ DrumsPage ข้างบน.

## Out of Scope

- แถบความคืบหน้าแบบลากได้ และปุ่มความเร็ว (D5).
- เวลาตอนพร้อมเล่น (D13).
- รื้อตัวเล่นวิดีโอ หรือ `<audio controls>` ของหน้าเพลง (`drum-notes` `SongPage`) (D8).
- แก้ backend หรือ endpoint (D11).
- จำตำแหน่งของเสียงที่ถูกแทน (D2).

## Open Questions

None.

## Sources

- [React: useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore) — อ่าน store นอก React (accessed 2026-11-20)
- [MDN: HTMLMediaElement.play()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play) — Promise ของ `play()` และ `AbortError` (accessed 2026-11-20)
- [MDN: timeupdate event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/timeupdate_event) — เวลาที่เล่นไป (accessed 2026-11-20)
- [MDN: HTMLMediaElement.duration](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/duration) — `NaN`/`Infinity` เมื่อไม่รู้ความยาว (accessed 2026-11-20)
- [MDN: play event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play_event) — ไม่ bubble (accessed 2026-11-20)
- [jsdom: unimplemented parts](https://github.com/jsdom/jsdom#unimplemented-parts-of-the-web-platform) — jsdom ไม่เล่น media (accessed 2026-11-20)
