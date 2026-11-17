# UI prompt: ui-nav

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/ui-nav/ui-prompt.md in {ลิงก์ไฟล์ Figma}"; หน้าเว็บสร้างตาม block นี้กับ design system เดิมเลย (D7); แบบ Figma ถ้าทำภายหลังเป็น change request ผ่าน `/warroom ui-nav`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | เมนูหลักและหัวหน้า (ทุกหน้า) | 1–6 | D1, D2, D3, D4, D5, D6, D10, D11 | redesign ของแถบ tab (sound-library D3, D16) |

```text
Design the app shell of framecraft: a local web app, used by one person on their own computer, that makes short videos (movie recaps, AI-drawn story clips, drum-lesson and song-cover reels). The shell is the header and main menu that every page sits in. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a browser; breakpoints: phone 375, tablet 768, desktop 1440 (the menu changes at 1280).
- Design system: the project's Tailwind tokens. Page background "muted" #f5f5f4; cards and menus "card" #ffffff with a 1px "border" #e7e5e4; text "foreground" #121110, secondary "mid" #44403c, muted "muted-foreground" #57534e; brand "brand" #26241f; accent "brand-accent" #5a3ee0; links "link" #4a30bd; selected item background "accent-subtle" #f3f1ff. Radius 12px for panels, 8px for items. Fonts: IBM Plex Sans Thai for UI text, Geist for the wordmark, Manrope for buttons. Icons: one existing 16px "menu" (three lines) icon; no other icons.
- Today's shell (being replaced): wordmark "framecraft" ("craft" in brand-accent) at 26px semibold, then one rounded tab bar of 8 tabs; below 640px a button with the menu icon and the open page's name opens a dropdown of the tabs under two headings.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus ring, touch targets ≥ 44px below 1280px, the open item marked for screen readers.

Step 1 — Components
- Reuse: the "menu" icon; the existing Refresh button (a page's header action) as is.
- New: "Shell/MenuButton" — a square-ish 44px button with the menu icon followed by the open topic's name; variants {closed, open (pressed look), focus}.
- New: "Shell/Header" — MenuButton, the wordmark, a location line "{topic} / {item}" in mid colour (item part in foreground), a flexible gap, then an optional action slot; variants {with action, without action}; phone: MenuButton and wordmark on one row with the action, the location line below.
- New: "Shell/MenuItem" — a full-width row: optional step number in a 20px circle, a label, an optional second line "ใช้กับ …" in 12px muted-foreground; variants {default, hover, current (accent-subtle background, semibold, brand text, number circle filled brand-accent), focus}; long labels truncate with an ellipsis on one line.
- New: "Shell/MenuGroup" — a heading in 12px medium mid colour then its items; variants {default, current topic (heading in brand colour)}; an optional small sub-heading "ล่าสุด" before up to three recent items.
- New: "Shell/MainMenu" — the full list (content below) in a card; variants {sidebar (256px wide, full height, scrolls on its own), drawer (up to 320px wide, slides from the left over the page, with a dark scrim behind)}.

Step 2 — Screens (one section per screen)
Frame names: "Shell / {state} / {breakpoint}"; realistic sample data in Thai; instances only.

Screen 1 — Main menu and header (redesign of the tab bar)
- Goal: the user reaches any step of a main task, any library, or something they opened recently, in at most two clicks from any page, and always sees where they are.
- Content of the menu, in order:
  - Link "ติดตั้ง".
  - Group "สปอย": "1 เลือกคลิป", "2 ตรวจแก้บท", "3 ผล render".
  - Group "การ์ตูนเล่า": "ชุดทั้งหมด", "สร้างชุดใหม่", then sub-heading "ล่าสุด" and up to three items, e.g. "รุ่นพี่เล่าว่า…", "รุ่นพี่เล่าว่า… · EP03".
  - Group "สอนกลอง": "บทเรียนทั้งหมด", then "ล่าสุด" with up to three lesson titles, e.g. "Rock beat พื้นฐาน".
  - Group "แกะเพลง": "เพลงทั้งหมด", then "ล่าสุด" with up to three song titles, e.g. "Smells Like Teen Spirit".
  - Group "คลัง": "คลังคลิป" with "ใช้กับ สปอย"; "คลังความรู้" with "ใช้กับ สปอย"; "คลังเสียง" with "ใช้กับ สปอย, การ์ตูนเล่า"; "เสียงที่บันทึก" with "ใช้กับ สปอย, การ์ตูนเล่า".
  - Groups are separated by a 1px border line; group headings are not clickable.
- Header: MenuButton named after the open topic (e.g. "สปอย"), wordmark, location line (e.g. "สปอย / ตรวจแก้บท"), the page's action at the right.
- Desktop (≥ 1280px): the menu is a sidebar pinned at the left, open by default; the page column (720px, or 1120px for wide pages) is centred in the space to its right. The MenuButton collapses the sidebar (page uses the full width) and opens it again.
- Below 1280px: the menu is hidden; the MenuButton opens it as a drawer over the page; picking an item, Esc, a click on the scrim, or the button again closes it.
- States: 1 Desktop, sidebar open, on "สปอย / ตรวจแก้บท" (current item highlighted, group heading in brand). 2 Desktop, sidebar collapsed. 3 Desktop on a recent EP page (the recent item highlighted). 4 Desktop with no recent items (no "ล่าสุด" sub-heading anywhere). 5 Phone 375, closed, on "แกะเพลง / เพลงทั้งหมด". 6 Phone 375, drawer open. 7 Tablet 768 and laptop 1024, drawer open. 8 Keyboard focus on a menu item.

Step 3 — Preview
- On the existing preview page "Preview", add each state frame in the order above, desktop then tablet then phone.
- Prototype links: each menu item → the existing screen of that page (e.g. "2 ตรวจแก้บท" → the สปอย review screen); MenuButton toggles between state 1 and 2 on desktop and between 5 and 6 on phone.
- The system's existing start frame stays the start; it now shows the new shell.

Do not include
- Icons for each topic or an icon-only collapsed rail.
- Collapsible groups inside the menu.
- The pages inside a Series (EPs, characters, settings) as menu items.
- Search, user accounts, notifications, or settings in the shell.
- Any field, step, screen, or feature not listed above.

Deliver: the components made, the shell frames in every state, and the preview's start link.
```

นำลิงก์กลับมาด้วย `/warroom ui-nav`.
