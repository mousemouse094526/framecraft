# Progress: windows-launch

**Now:** 01 ทำครบยกเว้นหน้าตาแถวให้ตรง Figma ที่รอแบบ (Blocked #1); 02 รอ 01 done

**Next:**

```
/warroom windows-launch
```

ทำแบบจาก [ui-prompt.md](../../features/windows-launch/ui-prompt.md) แล้วส่งลิงก์ Figma; ปิด Blocked #1 แล้ว `/warroom-build windows-launch 01` เก็บข้อสุดท้าย

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | Status check, gate และ Setup script ของ Qwen ต่อ OS | in-progress |
| 02 | Worker Qwen บน Windows และ timeout ต่อ OS | ready |
| 03 | ลอง Qwen บนเครื่อง Windows RTX 30xx ขึ้นไป | ready |

## Log

### 01: Status check, gate และ Setup script ของ Qwen ต่อ OS — in-progress 2026-11-06

**Built:**
- บน Windows หน้าติดตั้งมีแถว "GPU" (ชื่อการ์ด · VRAM · sm) และ "bitsandbytes" แทน "mlx-vlm"; แถว "Qwen3.5 9B model" เช็ค `Qwen/Qwen3.5-9B` ที่ pin; Mac เหมือนเดิมทุกแถว
- การ์ดต่ำกว่า RTX 30xx / 8 GB: แถว GPU, Qwen, bitsandbytes เหลืองพร้อมเหตุผล, บรรยายฉาก/ร่างบทได้ `not_ready` ที่บอก GPU, ถอดเสียงและสร้างเสียงยังใช้ได้; การ์ดเก่าเกิน (GTX 10xx) แถว Device แดง กันทุกงาน GPU
- Setup script บน Windows โหลด Qwen เฉพาะการ์ดที่ผ่านเป้า (ดิสก์ 30 GB, ข้าม Qwen = 15 GB) และจบปกติเมื่อข้าม; `bitsandbytes==0.50.2` เฉพาะ Windows ใน `uv.lock`
- เหลือ: ข้อ "หน้าตาของแถว `device`, `gpu`, `bitsandbytes`, `model_qwen` ตรงแบบใน Figma" — รอแบบ (Blocked #1); หน้าเว็บแสดงแถวใหม่ได้แล้วด้วยแบบแถวเดิม

**Decided:**
- D13 — แถว `device` ผ่านเมื่อ torch มี `sm_` major เดียวกับการ์ด (ผู้ใช้เลือก; cu128 ไม่มี `sm_89` แต่ RTX 40xx รันได้); ADR-0026 อ้าง D13
- D14 — "ดูแถว GPU", probe พังไม่ทำให้ Device แดง, VRAM GiB ปัดเต็ม, อ่านการ์ดครั้งเดียว, probe `bitsandbytes`, gate token มีแถว `gpu`, ข้าม Qwen = ดิสก์ 15 GB

**For the next ticket:**
- Qwen's spec comes from `models.qwen_for(checks.this_platform())`; `QWEN_MAC` / `QWEN_WINDOWS` never directly in prod code (SKILL.md). `qwen = qwen_for(...); project.snapshot_dir(qwen, qwen.revision)` repeats in `describe.py`, `draft.py`, `qwen_tokens.py` — ticket 02 touches `start_worker` per OS: extract one `qwen_snapshot(project)` there
- A check may return a third value, a `Fix` that replaces the row's own (`checks.CheckResult`); a small NamedTuple would read better if more rows need it
- `probe_gpu` runs `torch_arch_list()` inside: a broken torch install shows the driver hint on the GPU row (the torch row is missing too)
- Windows fakes: `fakes.card(...)`, `broken_gpu`, `on_windows(monkeypatch, card(...))`, `CU128_ARCHS`

**Checks:** `uv run pytest` (712) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` (320) · `npm --prefix frontend run build` — all green

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: ติดตั้ง (Status check) — แถว `device`, `gpu`, `bitsandbytes`, `model_qwen` ยังไม่มีแบบ | `/warroom windows-launch` พร้อมลิงก์แบบที่ทำจาก [ui-prompt.md](../../features/windows-launch/ui-prompt.md) | open |
| 2 | 03 | ต้องมีเครื่อง Windows ที่การ์ด RTX 30xx ขึ้นไปและ VRAM ≥ 8 GB (spec Open Question 1) | ผู้ใช้ clone `develop` บนเครื่องนั้นแล้ว `/warroom-build windows-launch 03` | open |
