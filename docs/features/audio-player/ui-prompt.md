# UI prompt: audio-player

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/audio-player/ui-prompt.md in {ลิงก์ไฟล์ Figma}"; หน้าเว็บทำตาม block นี้กับ design system เดิม ไม่รอ Figma (D10); แบบ Figma ถ้าทำภายหลังเป็น change request ผ่าน `/warroom audio-player`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | `PlayButton` (component) | 1–5, 7 | D3, D4, D5, D7, D13 | new |
| 2 | เสียงพากย์ › ออกแบบเสียง | 1–4 | D3, D6 | new (ปุ่มแทน "ฟัง") |
| 3 | เสียงพากย์ › แถวเสียงที่บันทึก | 1–4 | D3 | new (ปุ่มแทน "ฟัง") |
| 4 | ทำสปอย › การ์ดประโยค | 1–4 | D3 | new (ปุ่มแทน "ฟัง") |
| 5 | ทำสปอย › เสียงพื้น | 1–4 | D3 | new (ปุ่มแทนไอคอน play) |
| 6 | การ์ตูนเล่า › การ์ด (เสียงเล่า) | 1–4 | D3 | new (ปุ่มแทน "ฟัง") |
| 7 | คลังเสียง › แถวเสียง | 1–4 | D3 | new (ปุ่มแทนไอคอน play) |
| 8 | reel กลอง › ฟังจังหวะ | 1, 2, 4, 5 | D3, D7 | new (ปุ่มแทน "ฟังจังหวะ") |
| 9 | reel cover › แถบทำ reel | 1, 2, 4, 5 | D3, D7 | new (ปุ่มแทน "ฟัง") |

```text
Design the audio play button of framecraft: a local desktop web app, used by one person on their own Mac, that makes short vertical clips (story recaps, cartoon narration, drum and kalimba reels). Every place that plays a sound becomes one play/pause button with elapsed time; only one sound plays in the whole app at a time. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a desktop browser; breakpoints: desktop 1440 (primary), narrow 375. Touch targets ≥ 44px below 640px.
- Design system: the project's existing Tailwind tokens: page bg warm grey, cards white with 1px border and 16px radius, text #121110, secondary text "mid" #44403c, brand #26241f, accent #5a3ee0; fonts IBM Plex Sans Thai for UI, IBM Plex Mono for numbers. Buttons: "Button/Outline" (white, border, 8px radius), "Button/Ghost" (no fill until hover), "Button/Secondary" (grey fill), "Button/Icon" (square, no border, hover grey). Icons: Lucide-style 16px strokes (play, pause, loader).
- Figma file: the project's framecraft file; components on "Components", tokens on "Tokens", preview on "Preview". If these pages do not exist, create them.
- Existing screens this feature changes: "เสียงพากย์", "ทำสปอย / ตรวจแก้บท", "การ์ตูนเล่า / EP", "คลังเสียง", "reel กลอง", "reel cover / หน้าเพลง". Only the listen button changes on each; everything else stays.
- Language on screen: Thai. Use the copy below exactly. Times stay Latin digits.
- Accessibility: WCAG 2.2 AA contrast, visible focus ring (2px accent, 2px offset), touch targets ≥ 44px below 640px; the button's accessible name changes with its state ("ฟัง {name}" / "หยุดชั่วคราว {name}"), no aria-pressed.

Step 1 — Components
- New: "Audio/PlayButton" — one button: icon, then optional word, then optional time.
  - Properties: look {outline, ghost, icon-only}; word {none, "ฟังจังหวะ", "ฟัง reel"}; size {40 desktop, 44 narrow}.
  - Variants (state): ready (play icon, no time); mixing (spinning loader + "กำลังผสมเสียง…", disabled); playing (pause icon + time "0:03 / 0:12"); playing, length unknown (pause icon + "0:03"); paused (play icon + "0:03 / 0:12"); disabled (play icon at 60% opacity); focus.
  - Time: IBM Plex Mono 12px tabular figures, "mid" colour, 6px after the icon or word; the button grows to fit it.
- Reuse as is: "Button/Outline", "Button/Ghost", "Button/Secondary", "Button/Icon", "Feedback/RefusedAlert".
- Auto layout everywhere; colour, type, spacing and radius bound to the tokens; each state is a variant.

Step 2 — Screens (one section per screen)
Frame names: "Audio / {screen} / {state} / {breakpoint}"; realistic sample data in Thai; instances only.

Screen 1 — PlayButton sheet (new)
- Goal: one frame showing every variant of each look side by side, with one row "two buttons: A playing, B ready" and "A after B was pressed: A ready, B playing" to show that only one plays.

Screen 2 — เสียงพากย์ › ออกแบบเสียง (button replaces "ฟัง")
- Content: outline PlayButton (icon only), name "ฟัง เสียงตัวอย่าง", left of the "สุ่ม" outline button, shown only once a sample exists.
- States: 1 Ready. 2 Playing "0:02 / 0:05". 3 Paused. 4 Generating a new sample (button gone, existing progress bar).

Screen 3 — เสียงพากย์ › แถวเสียงที่บันทึก (button replaces "ฟัง")
- Content: outline PlayButton (icon only), name "ฟัง {ชื่อเสียง}", before "เปลี่ยนชื่อ" and "ลบ".
- States: 1 Ready. 2 Playing "0:01 / 0:06". 3 Paused.

Screen 4 — ทำสปอย › การ์ดประโยค (button replaces "ฟัง")
- Content: outline PlayButton (icon only), name "ฟัง ประโยค {n}", first in the card's action row before "สร้างเสียงใหม่".
- States: 1 Ready. 2 Playing "0:04 / 0:09". 3 Disabled: sentence has no voice, tooltip "ประโยคนี้ยังไม่มีเสียง".

Screen 5 — ทำสปอย › เสียงพื้น (button replaces the play icon)
- Content: icon-only PlayButton, name "ฟัง {ชื่อเสียง}", right of the sound select.
- States: 1 Ready. 2 Playing "0:07 / 0:12".

Screen 6 — การ์ตูนเล่า › การ์ด เสียงเล่า (button replaces "ฟัง")
- Content: ghost PlayButton (icon only), name "ฟัง เสียงเล่าการ์ด {n}", before "สร้างใหม่"; badge "เสียงเก่า" stays.
- States: 1 Ready. 2 Playing "0:03 / 0:08".

Screen 7 — คลังเสียง › แถวเสียง (button replaces the play icon)
- Content: icon-only PlayButton, name "ฟัง {ชื่อเสียง}", between the length "0:12" and the trash icon.
- States: 1 Two rows ready. 2 Row "ฝนตก" playing "0:05 / 0:12". 3 Row "ลมพัด" pressed after: "ฝนตก" ready, "ลมพัด" playing "0:01 / 0:08".

Screen 8 — reel กลอง › ฟังจังหวะ (button replaces "ฟังจังหวะ")
- Content: secondary PlayButton with word "ฟังจังหวะ".
- States: 1 Ready. 2 Mixing "กำลังผสมเสียง…". 3 Playing "ฟังจังหวะ 0:06 / 0:24". 4 Paused. 5 Disabled (clip over 90 s). 6 Refused: RefusedAlert under the button.

Screen 9 — reel cover › แถบทำ reel (button replaces "ฟัง")
- Content: secondary PlayButton with word "ฟัง reel", between "บันทึก" and "render reel" in the sticky bar.
- States: 1 Ready. 2 Mixing. 3 Playing "ฟัง reel 0:10 / 0:30". 4 Paused. 5 Disabled (no hits in the stretch).

Step 3 — Preview
- On the existing preview page "Preview", add each screen's default frame in the order above, its state frames under it, at each breakpoint.
- Prototype links: on every screen, the button's ready frame → playing frame → paused frame → playing frame; on Screen 7 pressing "ลมพัด" while "ฝนตก" plays → state 3; on Screens 8 and 9 ready → mixing → playing.
- The system's existing start frame stays the start.

Do not include
- A seek bar, volume control or speed control.
- Time on a ready button.
- Any change to video players or to the song page's audio player.
- Any field, step, screen, or feature not listed above.

Deliver: the PlayButton component set, the screen frames, and the preview's start link.
```

ส่งลิงก์แบบกลับมาด้วย `/warroom audio-player`.
