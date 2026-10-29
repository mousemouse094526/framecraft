# Design prompt: Setup status

Prompt to paste into Figma Make, v0, or another design AI. Built from [spec.md](spec.md) › Design and Frontend. The UI text is in Thai, exactly as written in spec.md.

```text
Design one desktop web screen called "Setup status" for framecraft, a local video generator app that runs on the user's own computer (Mac Apple Silicon / Windows NVIDIA). The screen shows whether everything installed by the setup script is ready. It is a developer-tool style status page: calm, clean, dense but readable, not a marketing page.

Stack to match: React + Tailwind CSS. Use a neutral palette with three status colors: green = ok, amber = warning, red = missing. Light mode first; dark mode variant welcome. Font must render Thai well (e.g. IBM Plex Sans Thai or Noto Sans Thai); use a monospace font for versions, paths and commands.

Layout (top to bottom, single centered column, max ~720px):
1. Header row: app name "framecraft" + page title "Setup status" on the left, a "Refresh" button on the right.
2. Under the header: "เช็คล่าสุด: 17:42:10" (last checked time).
3. Verdict banner, one line, colored by result. Three variants:
   - "พร้อมใช้งาน" (green)
   - "พร้อมใช้งาน (มีคำเตือน 1 รายการ)" (green with amber hint)
   - "ยังไม่พร้อม: ขาด 1 รายการ" (red)
4. Checklist of exactly 9 rows, in this order. Each row: status icon, label, detail text (monospace for versions/paths).
   ✅ Python venv — 3.12.11 (.venv)
   ✅ torch — 2.8.0
   ✅ transformers — 5.3.0
   ✅ omnivoice — 0.2.1
   ✅ fastapi — 0.115.0
   ✅ ffmpeg — 7.1 (imageio-ffmpeg)
   ❌ OmniVoice model — ไม่พบ marker ใน models/.setup
   ✅ Whisper model — whisper-large-v3-turbo (1.6 GB)
   ⚠️ Device — cpu — ไม่พบ mps/cuda (ช้า)
   Rows that are not ok also show a "fix" line under the detail: a copyable command chip, e.g. "./setup.sh" (Mac) or "setup.cmd" (Windows), or a short instruction like "ติดตั้ง NVIDIA driver แล้วปิดและเปิด npm run dev ใหม่".
   The two model rows also show a small license line: "CC BY-NC 4.0 · k2-fsa · [license] [model]" for OmniVoice and "MIT · OpenAI · [license] [model]" for Whisper, where [license] and [model] are external links.
5. Footer counter: "7/9" (ok count / total).

States to design (one frame each):
- loading: first open, no data yet. Show "กำลังเช็ค…" in place of the checklist; Refresh disabled.
- result (not ready): as above, 1 missing + 1 warning.
- result (all ready): all 9 rows green, verdict "พร้อมใช้งาน", counter "9/9".
- refreshing: the previous checklist stays visible, Refresh button disabled with a small spinner.
- offline: the whole checklist is replaced by a message block:
    "Backend offline"
    "ยังไม่ได้ start: รัน npm run dev"
    "รันอยู่แล้ว: ดู error ในบรรทัด [api] ของ terminal ที่รัน npm run dev หรือรัน setup ใหม่"
  Refresh stays clickable.

Rules:
- No polling indicator, no progress bars, no install buttons. The page only shows status; installing happens in the terminal.
- Do not use color alone for status; always pair it with an icon.
- Keep all Thai text exactly as given.
- Also show one narrow (~375px) version of the "result (not ready)" state.
```
