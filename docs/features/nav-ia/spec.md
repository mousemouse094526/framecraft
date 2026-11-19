# Spec: nav-ia

เมนู route และทางทำงานของแต่ละหัวข้อจัดใหม่ทั้งชุด: ที่อยู่ตรงกับที่ในเมนู และงานหนึ่งชิ้นเป็นพื้นที่ทำงานเดียว.

**Status:** ready-to-build

## Problem

เจ้าของบอกว่า "route และ menu ต่างดูแปลกๆมาก ... menu ไหนควรอยู่อันไหน แล้วการทำงานแต่ละ menu ก็มีความแปลกเหมือนกัน ทำต้องเข้าหลายขั้น". ui-nav เปลี่ยนแค่ป้ายกับที่วางในเมนูโดยไม่แตะ route (ui-nav D6) ชื่อกับที่อยู่จึงไม่ตรงกัน และขั้นของแต่ละงาน (สปอย 3 ขั้น, เพลง → reel, reel กลอง → ผล render, EP → render) เป็นหน้าแยกที่ต้องเดินต่อกัน.

## Solution

- ทุกหน้าอยู่ใต้ hash ของที่มันอยู่ในเมนู (D1); hash เก่าทุกตัวพาไปหน้าใหม่ (D9).
- คลิปของสปอยอยู่ใต้หัวข้อสปอย หมวดคลังเหลือของอ้างอิง (D2, D3); เสียงพากย์มีที่อยู่ของตัวเอง (D4).
- สปอยเป็นพื้นที่ทำงานเดียวที่ขั้นเป็นสถานะในหน้า (D5).
- เพลงหนึ่งเพลงมีแกะโน้ตกับ reel cover ในหน้าเดียว ใต้หัวข้อ "reel cover" (D6).
- reel กลองหนึ่งชิ้นมีผล render ในหน้าเดียวกับฟอร์ม (D7).
- EP การ์ตูนเล่ามี พล็อต · เส้นเรื่อง · render ในหน้าเดียว (D8).

## User Stories

**เจ้าของ (คนทำ reel)**
1. As เจ้าของ, I want ชื่อในเมนูกับที่อยู่ของหน้าตรงกัน, so that เปิดหน้าไหนก็รู้ว่าอยู่หัวข้อไหน (D1)
2. As เจ้าของ, I want โหลดและถอดคลิปจากหัวข้อสปอย, so that เตรียมของของสปอยอยู่ที่เดียวกับที่ทำสปอย (D2)
3. As เจ้าของ, I want เปิดสปอยแล้วอยู่ที่งานที่ค้าง ข้ามขั้นได้ในหน้าเดียว, so that ไม่ต้องเดิน 3 หน้าต่อกัน (D5)
4. As เจ้าของ, I want เปิดเพลงแล้วทำ reel cover ต่อในหน้าเดียว, so that ไม่ต้องหาการ์ด Reel cover แล้วเปิดอีกหน้า (D6)
5. As เจ้าของ, I want render reel กลองแล้วเห็นผลใต้ฟอร์ม, so that แก้แล้ว render ใหม่ได้โดยไม่สลับหน้า (D7)
6. As เจ้าของ, I want สลับพล็อต เส้นเรื่อง และ render ของ EP ในหน้าเดียว, so that EP หนึ่งตอนเป็นที่ทำงานเดียว (D8)
7. As เจ้าของ, I want bookmark และ "ล่าสุด" เดิมยังพาไปหน้าที่ถูก, so that ไม่มีลิงก์พัง (D9)

## Design

ทุกจอใช้ component เดิม (D11). ตารางนี้คือภาพเดียวของโครงสร้างใหม่: เมนู ↔ route ↔ งานที่ทำได้.

| หมวด | หัวข้อ › รายการ | route | งานที่ทำได้ | ทำไมอยู่ที่นี่ |
|---|---|---|---|---|
| เล่าเรื่อง | สปอย › ทำสปอย | `#/spoil` | ขั้นในหน้า: เลือกคลิป (EP, Story, ตั้งค่า, ร่างบท) · ตรวจแก้บท (ประโยค ภาพ เสียงเล่า เสียงพื้น render) · ผล render (ดู โหลด ลบ) | งานชิ้นเดียว ขั้นเป็นสถานะ (D5) |
| เล่าเรื่อง | สปอย › คลิปทั้งหมด | `#/spoil/clips` | โหลดคลิปจากลิงก์หรือไฟล์ ตัดช่วง ถอดบทพูด บรรยายฉาก แก้ Transcript | วัตถุดิบของสปอยหัวข้อเดียว (D2) |
| เล่าเรื่อง | การ์ตูนเล่า › ชุดทั้งหมด | `#/toon` | รายการชุด ลบชุด | เหมือนเดิม |
| เล่าเรื่อง | การ์ตูนเล่า › สร้างชุดใหม่ | `#/toon/new` | ตั้งค่าชุดใหม่ | เหมือนเดิม |
| เล่าเรื่อง | การ์ตูนเล่า › (หน้าของชุด) | `#/toon/series/{id}` `/cast` `/settings` `/{kind}/{id}/pick` | EP ของชุด, ตัวละครและฉากหลัง, ตั้งค่าชุด, เลือกภาพอ้างอิง | ชุด → EP คือการเลือกของ (D8) |
| เล่าเรื่อง | การ์ตูนเล่า › (หน้า EP) | `#/toon/eps/{id}` | สถานะในหน้า: พล็อต · เส้นเรื่อง · render | งานชิ้นเดียว (D8) |
| ดนตรี | reel cover › เพลงทั้งหมด | `#/covers` | เพิ่มเพลงจากลิงก์ ไฟล์เสียง หรือ MIDI ลบเพลง | วัตถุดิบของ reel cover (D2, D6) |
| ดนตรี | reel cover › (หน้าเพลง) | `#/covers/{id}` | ช่วงแกะ แกะโน้ต → reel กลองหรือคาลิมบา ช่วง ข้อความ เสียง ฟัง render ผล render | งานชิ้นเดียว (D6) |
| ดนตรี | reel กลอง › reel ทั้งหมด | `#/drums` | สร้าง ทำซ้ำ ลบ reel | เหมือนเดิม |
| ดนตรี | reel กลอง › (หน้า reel) | `#/drums/{id}` | หัวเรื่อง Groove BPM พื้นหลัง รอบ ฟังจังหวะ render ผล render | งานชิ้นเดียว (D7) |
| คลัง | คลังความรู้ (ใช้กับ สปอย) | `#/stories` `/new` `/{id}` | เขียน แก้ ลบ Story | ของอ้างอิง (D3) |
| คลัง | คลังเสียง (ใช้กับ สปอย, การ์ตูนเล่า) | `#/sounds` (`?back=`) | เพิ่ม ฟัง ลบเสียงพื้น | ของใช้ร่วม (ADR-0037) |
| คลัง | เสียงพากย์ (ใช้กับ สปอย, การ์ตูนเล่า) | `#/voices` | ออกแบบ ฟัง บันทึก เปลี่ยนชื่อ ลบ Saved voice | ของใช้ร่วม (D4) |
| ตั้งค่า | ติดตั้ง | `#/setup` (hash ว่างหรือไม่รู้จัก) | Setup status | เหมือนเดิม |

"ล่าสุด" ยังอยู่ใต้การ์ตูนเล่า reel cover และ reel กลอง (ui-nav D5) โดยของ reel cover เป็น `#/covers/{id}`.

### ทางเดินถึงของที่ใช้บ่อย

นับตาม D10: sidebar ตรึง / จอแคบ (บวก ☰).

| ของที่ใช้บ่อย | ก่อน | หลัง |
|---|---|---|
| ตรวจแก้บทสปอยที่ค้าง | 1 / 2 (ตรวจแก้บท) | 1 / 2 (ทำสปอย เปิดที่ตรวจแก้บท) |
| ร่างสปอยใหม่ | 1 / 2 | 1–2 / 2–3 (ทำสปอย, ขั้นเลือกคลิปเมื่อมีบทอยู่) |
| ผล render สปอยรอบก่อน | 1 / 2 | 2 / 3 (D10 Accepted risk) |
| เพิ่มหรือถอดคลิป | 1 / 2 (คลังคลิป) | 1 / 2 (คลิปทั้งหมด) |
| reel cover ของเพลงที่เปิดล่าสุด | 2 / 3 (ล่าสุด → การ์ด Reel cover) | 1 / 2 (ล่าสุด) |
| reel cover ของเพลงใดก็ได้ | 3 / 4 | 2 / 3 |
| ผล render reel กลองที่เปิดล่าสุด | 2 / 3 | 1 / 2 |
| render EP ที่เปิดล่าสุด | 2 / 3 | 2 / 3 (ล่าสุด → render ในหน้า) |
| เสียงพากย์, คลังเสียง, คลังความรู้, ติดตั้ง | 1 / 2 | 1 / 2 |

## Expected Outcome

เจ้าของเปิดหัวข้อใดก็ทำงานชิ้นหนึ่งจนได้ reel ในหน้าเดียว และที่อยู่บอกว่าอยู่ตรงไหนของเมนูเสมอ.
- **เปิด `#/spoil` เมื่อมีบทค้าง:** เห็นแถบขั้นที่ขั้นตรวจแก้บทเลือกอยู่ และบท; กด "ผล render" เห็นผลโดยที่อยู่ยังเป็น `#/spoil`.
- **เปิด bookmark `#/songs/abc/cover`:** ที่อยู่กลายเป็น `#/covers/abc` และเห็นหน้าเพลงที่มีส่วน reel.
- **เปิด `#/voices`:** หัวหน้าบอก "คลัง / เสียงพากย์" และหัวข้อสปอยไม่สว่าง.

**How success is judged:**
- เมนูมีรายการตามตาราง Design ตามลำดับนี้ ไม่มีรายการขั้นของสปอย
- hash เก่าทุกแถวในตาราง Redirect เปิดหน้าใหม่ของมัน และ `location.hash` เป็น hash ใหม่
- ไม่มี route `#/spoil/review`, `#/spoil/renders`, `#/songs/…`, `#/drums/{id}/renders`, `#/toon/eps/{id}/plot`, `#/toon/eps/{id}/render` ที่เปิดหน้าของตัวเอง
- ทุกความสามารถในตาราง Design ทำได้ (test เดิมของหน้าเหล่านั้นผ่านหลังแก้ hash)
- checks ทั้งสี่ผ่าน

## Implementation

### Modules touched
- **`frontend/src/lib`**
  - `nav`: `NAV_SECTIONS` ตามตาราง Design; สปอยมีรายการ ทำสปอย (`#/spoil`, prefix) กับ คลิปทั้งหมด (`#/spoil/clips`); ไม่มี `step` ในรายการอีก; `LIBRARY_ITEMS` 3 รายการ (D2–D5)
  - `useHash`: `TAB_LABELS` เป็น `setup stories sounds voices spoil toon drums covers` ("covers" ชื่อ "reel cover", "voices" ชื่อ "เสียงพากย์", ไม่มี `clips` `songs`); `tabOf` ตาม prefix ใหม่; `MOVED` เป็นรายการ pattern (D9)
  - `recent`: area `songs` เป็น `covers` รูป `#/covers/{id}`; กุญแจเก่า `songs` ที่อ่านได้แปลงเป็น `covers` (D9)
  - `voices`: `VOICES_HASH = "#/voices"`
- **`frontend/src/App.tsx`**: `#/spoil/clips` เปิด `ClipsPage`; หัวข้อ `voices` เปิดหน้า Saved voice; หัวข้อ `covers` เปิด `SongsPage`; ไม่มี `coverViewOf` (D2, D4, D6)
- **`components/ui/PageLayout`**: ไม่เปลี่ยนโครง; ถ้าไม่มีรายการไหนมี `step` แล้ว เลขขั้นในรายการเมนูเอาออก
- **spoil-maker**: `SpoilMakerPage` ถือขั้นที่เปิด (state) และส่งตัวเปลี่ยนขั้นผ่าน context ให้ขั้นที่เคยตั้ง `location.hash` หรือมีลิงก์ไปขั้นอื่น; `SpoilSteps` เป็นปุ่ม `aria-current="step"`; หน้า Saved voice ไม่อยู่ใน `SpoilMakerPage` อีก (D4, D5)
- **spoil**: `ClipsPage` เป็นหน้าของหัวข้อ `spoil`
- **drum-notes + drum-cover**: hash `#/covers`, `#/covers/{id}`; `SongPage` รับช่อง `reel` ที่ `App` ใส่ `ReelSection` ของ drum-cover (เนื้อหาของหน้า reel เดิมโดยไม่มี `PageLayout` และแถวหัว, keyed ด้วย `picked_at`) ใต้ผลแกะ; การ์ด Reel cover เอาออก; ปุ่ม "ไปที่ reel"; แกะใหม่ถาม leave guard ก่อน (D6, D14). ข้อความเงื่อนไขการใช้ของ reel cover และ reel คาลิมบาย้ายมาครบ (legal.md)
- **`useHash`**: เพิ่มตัวถาม leave guard ตอนนี้ (`mayLeave()`: ไม่มีงานค้าง หรือผู้ใช้ตอบตกลง) ให้หน้าที่เปลี่ยนสิ่งที่เห็นโดยไม่เปลี่ยน hash ใช้ (D14)
- **docs**: `docs/features/kalimba-cover/ui-prompt.md` และข้อความ Left ของแถว drum-notes บน board เปลี่ยนเป็นหน้าเดียว `#/covers/{id}` และชื่อ "reel cover" (D6)
- **video-gen**: `drumsViewOf` เหลือ list กับ edit; หน้าแก้ reel วางส่วนผล render ใต้ฟอร์ม; หน้าถือ `useDrumRender` ตัวเดียวและส่งงานกับ `reload` ให้ส่วนผล; render ที่หน้านี้เริ่มเสร็จ → อ่านผลใหม่และเลื่อนไปที่ส่วนผลด้วย `scrollIntoView` (D7, D14)
- **toon**: `pageOf` ไม่มี `render` และ `plot` ของ EP; หน้า EP ถือ view (`plot` · `storyline` · `render`) เป็น state และวางเนื้อหาของหน้า render เดิมเมื่อเลือก render (D8)
- **sound-library**: `backOf` รับ `#/spoil` (ไม่มี `/`) ด้วย เพราะสปอยไม่มี `#/spoil/review` อีก

### Redirect

`MOVED` ทำงานตอนอ่าน hash ทุกครั้ง (โหลดหน้าและ `hashchange`) ด้วย `replaceState` แบบเดิม (D9). ลำดับ: แถวแรกที่ตรงชนะ.

| hash เก่า | hash ใหม่ |
|---|---|
| `#/toon/sounds` | `#/sounds` (เดิม) |
| `#/clips` | `#/spoil/clips` |
| `#/spoil/voices` | `#/voices` |
| `#/spoil/review` | `#/spoil` |
| `#/spoil/renders` | `#/spoil` |
| `#/songs` | `#/covers` |
| `#/songs/{id}` | `#/covers/{id}` |
| `#/songs/{id}/cover` | `#/covers/{id}` |
| `#/drums/{id}/renders` | `#/drums/{id}` |
| `#/toon/eps/{id}/plot` | `#/toon/eps/{id}` |
| `#/toon/eps/{id}/render` | `#/toon/eps/{id}` |

`{id}` รับตัวอักษรเดียวกับที่ parser ของหน้านั้นรับ (`[A-Za-z0-9_-]{1,64}`, reel กลอง `[a-z0-9]{12}`).

### พื้นที่ทำงานสปอย

| เหตุการณ์ | เดิม | ใหม่ |
|---|---|---|
| เปิด `#/spoil` | ขั้นเลือกคลิปเสมอ | หลังอ่านสถานะครั้งแรก: มี Spoil draft หรือกำลังร่าง → ตรวจแก้บท, อื่น ๆ → เลือกคลิป; ระหว่างอ่าน แถบขั้นขึ้น ส่วนเนื้อหาบอก "กำลังโหลด…" |
| กดขั้นในแถบ | ลิงก์ hash | ปุ่ม เปลี่ยนขั้นในหน้า |
| ร่างบทเริ่ม | hash → `#/spoil/review` | ขั้น → ตรวจแก้บท |
| ยกเลิกร่างจากการ์ดร่าง | hash → `#/spoil` | ขั้น → เลือกคลิป |
| render ที่ตรวจแก้บทเริ่มเสร็จ | hash → `#/spoil/renders` | ขั้น → ผล render เมื่อตรวจแก้บทยังเปิดอยู่; ขั้นอื่นเปิดอยู่ → บรรทัดของขั้น 3 บอกผล (D14) |
| กดขั้นระหว่างอ่านสถานะครั้งแรก | — | ขั้นที่กดคงอยู่ (D14) |
| กด "ทำสปอย" ในเมนูขณะอยู่ `#/spoil` | — | ไม่มีอะไรเปลี่ยน (D14) |
| "ไปที่ตรวจแก้บท" / "ไปที่ตั้งค่าคลิปสปอย" | ลิงก์ | ปุ่มเปลี่ยนขั้น |
| เสียงพื้น → คลังเสียง | `#/sounds?back=#/spoil/review` | `#/sounds?back=#/spoil` |

ขั้นที่ไม่มี context (test ของขั้นเดี่ยว) ได้ตัวเปลี่ยนขั้นที่ไม่ทำอะไร.

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| — | — | ไม่ใช้ library ใหม่; `history.replaceState` เป็น Web API ที่ `useHash` ใช้อยู่ | [MDN replaceState](https://developer.mozilla.org/en-US/docs/Web/API/History/replaceState) |
| — | — | `Element.scrollIntoView` เลื่อนส่วนผลเข้าจอ; jsdom ไม่มี ต้อง stub ใน test | [MDN scrollIntoView](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView) |

## Seams

`App` กับหน้าใน jsdom ตามแบบที่มีอยู่ (D12).

1. **เมนูและ route** `App` ใน jsdom
   - render ที่ hash ใดก็ได้ → เมนูมีรายการตามตาราง Design ตามลำดับ พร้อม "ใช้กับ …" ของคลัง
   - hash ของแต่ละแถว Design → รายการที่ `aria-current="page"` หัวข้อที่สว่าง และ `<h1>` ตรงกับแถวนั้น (`#/voices` → "คลัง / เสียงพากย์" ไม่มีหัวข้อสว่าง)
   - hash เก่าแต่ละแถว Redirect → `location.hash` เป็น hash ใหม่ และหน้าใหม่ขึ้น
   - ล่าสุดที่เก็บ `songs: [{hash: "#/songs/x"}]` → เมนูมีรายการ `#/covers/x` ใต้ reel cover
2. **พื้นที่ทำงานสปอย** `SpoilMakerPage` ใน jsdom
   - ไม่มี draft → ขั้นเลือกคลิปเปิด; มี draft → ตรวจแก้บทเปิด; กดผล render → เห็นผล `location.hash` ยังเป็น `#/spoil`
   - ร่างบทเริ่ม → ตรวจแก้บทเปิด; render เสร็จขณะตรวจแก้บทเปิด → ผล render เปิด; ยกเลิกร่าง → เลือกคลิปเปิด
   - ปุ่ม "ไปที่ตรวจแก้บท" และ "ไปที่ตั้งค่าคลิปสปอย" → เปลี่ยนขั้น; กดขั้นระหว่างกำลังโหลด → ขั้นที่กดคงอยู่หลังโหลดเสร็จ
3. **หน้างานชิ้นเดียว** `SongsPage` (ผ่าน `App`), `DrumsPage`, `ToonPage` ใน jsdom — หนึ่ง `it` ขึ้นไปต่อหน้า
   - เพลงที่แกะแล้ว → หน้าเดียวมีผลแกะ ปุ่ม "ไปที่ reel" และส่วน reel (ฟัง render ผล render) ทำงานเหมือนหน้า reel เดิม; เพลงที่ยังไม่แกะ → ไม่มีส่วน reel
   - แกะใหม่ขณะ reel ยังไม่บันทึก → ถาม "ออกโดยไม่บันทึก?"; ตอบไม่ → ไม่แกะ; แกะเสร็จ → ส่วน reel อ่าน cover ใหม่
   - หน้า reel กลองมีผล render; render ที่หน้านี้เริ่มเสร็จ → ผลใหม่ขึ้น `scrollIntoView` ถูกเรียกที่ส่วนผล hash ไม่เปลี่ยน
   - EP ที่มีการ์ด → เส้นเรื่องเปิด; EP ที่ยังเป็นพล็อต → พล็อตเปิด ไม่มี render; สลับพล็อตและ render ได้ hash ยังเป็น `#/toon/eps/{id}`; แตกการ์ดเสร็จขณะพล็อตเปิด → เส้นเรื่องเปิด

## Testing decisions

- **Copy:** `frontend/src/App.test.tsx` — ตาราง `it.each` ของ hash → รายการ/หัวข้อ/หัวหน้า; เพิ่มตาราง Redirect แบบเดียวกัน
- **Copy:** `frontend/src/lib/recent.test.ts` — กุญแจเก่า `songs`
- **Copy:** `frontend/src/features/spoil/components/ClipsPage.test.tsx` (stub `Element.prototype.scrollIntoView` แล้วดูว่าเรียกที่ element ไหน) — การเลื่อนไปที่ผล
- test ที่ assert hash ที่ย้ายต้องแก้ด้วย: `RenderResults.test.tsx`, `SavedVoicePage.test.tsx`, `SoundsPage.test.tsx` (เพิ่ม `backOf` ของ `#/sounds?back=#/spoil`), `SoundsRender.test.tsx`, test ของ `video-gen/lib`
- **Copy:** test เดิมของแต่ละหน้า (`SpoilMakerPage.test.tsx`, `ScriptReview.test.tsx`, `SpoilerSetup.test.tsx`, `SongsPage.test.tsx`, `CoverPage.test.tsx`, `DrumsPage.test.tsx`, `EpPage.test.tsx`, `ToonPage.test.tsx`) — แก้ที่ assert `location.hash` ของขั้นเป็น assert ขั้นที่เปิด (`aria-current="step"`) หรือ view ที่เห็น; test ของหน้า reel cover ย้ายไป render ผ่านหน้าเพลง
- test ทุกตัวที่ผ่านอยู่ต้องยังผ่าน หรือแก้แค่ hash และวิธีเปิดหน้า ไม่ลดสิ่งที่ตรวจ (ความสามารถไม่หาย)

## Out of Scope

- เปลี่ยน API หรือชื่อในโค้ด backend (D13)
- เปลี่ยนหน้าตา sidebar, drawer, หัวเมนู (ui-nav D11, D14)
- รวมหน้าชุดกับหน้า EP ของการ์ตูนเล่า (D8)
- ชื่อ "เสียงบรรยาย" → "เสียงพากย์" บนหน้าและในขั้น 1 ของสปอย: งานของ `feat/ui-nav-3` (D4 ใช้แค่ป้ายเมนู)

## Open Questions

None.

## Sources

- [MDN History.replaceState](https://developer.mozilla.org/en-US/docs/Web/API/History/replaceState) — เปลี่ยน hash โดยไม่ยิง `hashchange` (accessed 2026-11-19)
