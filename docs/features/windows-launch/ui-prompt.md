# UI prompt: windows-launch

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP บอกว่า "design docs/features/windows-launch/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วนำลิงก์กลับมาด้วย `/warroom windows-launch`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | ติดตั้ง (Status check) บน Windows | 1, 5, 6 | D6, D8, D9, D10, D12 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8004-7488) |

```text
Design one change to framecraft, a local desktop web app that downloads YouTube videos and turns them into narrated vertical Thai recap videos for one creator: the Setup status screen (tab ติดตั้ง) as it looks on a Windows PC with an NVIDIA card, where the local AI model Qwen now runs too. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app; breakpoints: mobile 375, desktop 1440.
- Design system: the one already in the Figma file (React + Tailwind CSS in code); tokens: the file's variables on page ":: Token" (surface, border, text mid/subtle, accent, destructive, warning); icons: Lucide.
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft; the current screen is section "framecraft — Setup status" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8004-7488) with frames 1 loading, 2 result not ready, 3 ready with warning, 4 all ready, 5 refreshing, 6 offline, 7 mobile 375px.
- Existing screens this connects to: the tab bar ติดตั้ง · คลิป · คลังความรู้ · สปอย. Match the current Setup status look exactly; this is a redesign of its checklist rows only.
- Language on screen: Thai, except row labels and values, which stay as the API sends them (English names, numbers). Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, touch targets ≥ 44px; the warning row's meaning must not rely on colour alone (icon + text).

Step 1 — Components
- Reuse: the existing Checklist row component with its three states ok, warning, missing; its "fix" area as a hint (plain text, no copy button) and as a command (chip with copy button).
- Reuse: the existing model row variant (license, author, license link, model link).
- No new components unless a row below cannot be shown with these.

Step 2 — Screens
Frame names: "Setup status Windows / {state} / {breakpoint}"; sample data below; instances only.

Screen 1 — Setup status on Windows (redesign of https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8004-7488: new rows and row states for Windows)
- Goal: a Windows user runs the setup script, opens tab ติดตั้ง, and sees whether every part is ready, including whether their graphics card can run Qwen.
- Row order on Windows: Python venv, torch, transformers, omnivoice, fastapi, ffmpeg, yt-dlp, Deno, OmniVoice model, Whisper model, Device, GPU, Qwen3.5 9B model, bitsandbytes, pythainlp, Kanit font.
- Rows that change:
  - "Device": value "cuda". Missing state: value "NVIDIA GeForce GTX 1050 Ti · sm_61", hint "การ์ด NVIDIA GeForce GTX 1050 Ti (sm_61) เก่าเกินสำหรับ torch ที่ติดตั้ง".
  - "GPU" (new): value "NVIDIA GeForce RTX 3060 · 12 GB · sm_86". Warning state: value "NVIDIA GeForce RTX 2060 · 6 GB · sm_75", hint "Qwen ต้องใช้การ์ด NVIDIA RTX 30xx ขึ้นไปที่มี VRAM อย่างน้อย 8 GB". Second warning: value empty, hint "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA".
  - "Qwen3.5 9B model": model row, value "c202236", license "Apache-2.0", author "Qwen", model link "huggingface.co/Qwen/Qwen3.5-9B". Warning state (when GPU is a warning): the same hint as GPU. Missing state: the setup command chip.
  - "bitsandbytes" (new, replaces "mlx-vlm" on Windows): value is a version number such as "0.48.2". Warning state (when GPU is a warning): the same hint as GPU. Missing state: the setup command chip.
  - There is no "mlx-vlm" row on Windows.
- States:
  1. All ready: every row ok.
  2. Card below Qwen's target: GPU, Qwen3.5 9B model and bitsandbytes are warnings; verdict is the existing "ready with warning" verdict.
  3. Card too old: Device missing; GPU warning; verdict is the existing "not ready" verdict.
  4. Card unreadable: GPU warning with the driver hint.
  5. Qwen not downloaded yet: Qwen3.5 9B model missing with the setup command chip.
  Each state at 1440 and at 375.

Step 3 — Preview
- On the file's existing preview page, add the Windows frames beside the existing Setup status frames, default state first and the other states under it, at each breakpoint.
- Prototype links: the tab bar "ติดตั้ง" → Screen 1 all ready; the existing Refresh button on each state → the refreshing frame.
- The system's existing start frame stays the start.

Do not include
- A field to paste a Hugging Face model link or a "ตรวจสอบ" button.
- Any change to the Mac Setup status frames.
- Any field, step, screen, or feature not listed above.

Deliver: the components changed (if any), the screen frames, and the preview's start link.
```

นำลิงก์ Figma กลับมาด้วย `/warroom windows-launch`.
