# UI prompt: ui-nav

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/ui-nav/ui-prompt.md in {ลิงก์ไฟล์ Figma}"; หน้าเว็บสร้างตาม block นี้กับ design system เดิมเลย (D7); แบบ Figma ถ้าทำภายหลังเป็น change request ผ่าน `/warroom ui-nav`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | เมนูหลักและหัวหน้า (ทุกหน้า) | 1–7 | D1, D2, D3, D4, D5, D6, D10, D11, D12, D13, D14 | change request: แบรนด์ย้ายไปหัวเมนู หัวหน้าเป็นหัวข้อหน้า (current: หัวของ PR #20) |

```text
Design the app shell of framecraft: a local web app, used by one person on their own computer, that makes short vertical videos (reels) only: movie recaps, AI-drawn story clips, song-cover and drum reels. The shell is the header and main menu that every page sits in. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a browser; breakpoints: phone 375, tablet 768, desktop 1440 (the menu changes at 1280).
- Design system: the project's Tailwind tokens. Page background "muted" #f5f5f4; cards and menus "card" #ffffff with a 1px "border" #e7e5e4; text "foreground" #121110, secondary "mid" #44403c, muted "muted-foreground" #57534e; brand "brand" #26241f; accent "brand-accent" #5a3ee0; links "link" #4a30bd; selected item background "accent-subtle" #f3f1ff. Radius 12px for panels, 8px for items. Fonts: IBM Plex Sans Thai for UI text, Geist for the wordmark, Manrope for buttons. Icons: the existing 16px "menu" (three lines) and "x" icons, plus one new 16px "sidebar" (panel-left) icon in the same 1.5px stroke; no other icons.
- Today's shell (being revised): a bordered 44px menu button sits next to a 26px wordmark and a small grey location line in the page header, so the button, the brand and the page read as unrelated pieces, and on desktop the button that collapses the sidebar floats far from it. This revision moves the brand and the collapse/close control into the menu's own head and turns the page header into the page's title.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus ring, touch targets ≥ 44px below 1280px, the open item marked for screen readers.

Step 1 — Components
- Reuse: the "menu" icon; the existing Refresh button (a page's header action) as is.
- New: "Shell/MenuButton" — a 44px borderless icon button (menu icon), hover fill "card"; shown only while the menu is hidden; variants {default, hover, focus}.
- New: "Shell/Header" — [MenuButton when the menu is hidden] the page title "{topic} / {item}" as one 18px line (topic part muted-foreground medium, item part foreground semibold, truncates), a flexible gap, then an optional action slot; one row at every width; the menu icon sits flush with the content edge so button and title read as one unit.
- New: "Shell/MenuHead" — the first row of the menu, 44px tall: wordmark "framecraft" at 22px Geist semibold ("craft" in brand-accent) on the left, a ghost icon button on the right: "ยุบเมนู" (sidebar icon, 36px) on the sidebar, "ปิดเมนู" (x icon, 44px) on the drawer.
- New: "Shell/MenuItem" — a full-width row: optional step number in a 20px circle, a label, an optional second line "ใช้กับ …" in 12px muted-foreground; variants {default, hover, current (accent-subtle background, semibold, brand text, number circle filled brand-accent), focus}; long labels truncate with an ellipsis on one line.
- New: "Shell/MenuGroup" — a heading in 12px medium mid colour then its items; variants {default, current topic (heading in brand colour)}; an optional small sub-heading "ล่าสุด" before up to three recent items.
- New: "Shell/MenuSection" — a section heading in 11px semibold muted-foreground (not clickable, never highlighted), then its topic groups or items; sections are separated by a 1px border line, topic groups inside a section are not.
- New: "Shell/MainMenu" — the full list (content below) in a card; variants {sidebar (256px wide, full height, scrolls on its own), drawer (up to 320px wide, slides from the left over the page, with a dark scrim behind)}.

Step 2 — Screens (one section per screen)
Frame names: "Shell / {state} / {breakpoint}"; realistic sample data in Thai; instances only.

Screen 1 — Main menu and header (redesign of the tab bar)
- Goal: the user reaches any step of a main task, any library, or something they opened recently, in at most two clicks from any page, and always sees where they are.
- Content of the menu, in order:
  - Section "เล่าเรื่อง":
    - Group "สปอย": "1 เลือกคลิป", "2 ตรวจแก้บท", "3 ผล render".
    - Group "การ์ตูนเล่า": "ชุดทั้งหมด", "สร้างชุดใหม่", then sub-heading "ล่าสุด" and up to three items, e.g. "รุ่นพี่เล่าว่า…", "รุ่นพี่เล่าว่า… · EP03".
  - Section "ดนตรี":
    - Group "แกะเพลง": "เพลงทั้งหมด", then "ล่าสุด" with up to three song titles, e.g. "Smells Like Teen Spirit".
    - Group "สอนกลอง": "บทเรียนทั้งหมด", then "ล่าสุด" with up to three lesson titles, e.g. "Rock beat พื้นฐาน".
  - Section "คลัง": "คลังคลิป" with "ใช้กับ สปอย"; "คลังความรู้" with "ใช้กับ สปอย"; "คลังเสียง" with "ใช้กับ สปอย, การ์ตูนเล่า"; "เสียงที่บันทึก" with "ใช้กับ สปอย, การ์ตูนเล่า".
  - Section "ตั้งค่า": link "ติดตั้ง".
  - Section and group headings are not clickable.
- Header: page title (e.g. "สปอย / ตรวจแก้บท") with the page's action at the right; the MenuButton before the title only while the menu is hidden. The menu starts with MenuHead.
- Desktop (≥ 1280px): the menu is a sidebar pinned at the left, open by default; the page column (720px, or 1120px for wide pages) is centred in the space to its right. "ยุบเมนู" in MenuHead collapses the sidebar (page uses the full width, the MenuButton appears before the title); the MenuButton opens it again.
- Below 1280px: the menu is hidden; the MenuButton opens it as a drawer over the page; picking an item, Esc, a click on the scrim, or "ปิดเมนู" closes it.
- States: 1 Desktop, sidebar open, on "สปอย / ตรวจแก้บท" (current item highlighted, group heading in brand). 2 Desktop, sidebar collapsed. 3 Desktop on a recent EP page (the recent item highlighted). 4 Desktop with no recent items (no "ล่าสุด" sub-heading anywhere). 5 Phone 375, closed, on "แกะเพลง / เพลงทั้งหมด". 6 Phone 375, drawer open. 7 Tablet 768 and laptop 1024, drawer open. 8 Keyboard focus on a menu item.

Step 3 — Preview
- On the existing preview page "Preview", add each state frame in the order above, desktop then tablet then phone.
- Prototype links: each menu item → the existing screen of that page (e.g. "2 ตรวจแก้บท" → the สปอย review screen); MenuButton toggles between state 1 and 2 on desktop and between 5 and 6 on phone.
- The system's existing start frame stays the start; it now shows the new shell.

Do not include
- Icons for each topic or an icon-only collapsed rail.
- Collapsible groups or sections inside the menu.
- Lesson-making items (anything that teaches without producing a clip).
- The pages inside a Series (EPs, characters, settings) as menu items.
- Search, user accounts, notifications, or settings in the shell.
- Any field, step, screen, or feature not listed above.

Deliver: the components made, the shell frames in every state, and the preview's start link.
```

นำลิงก์กลับมาด้วย `/warroom ui-nav`.
