# Progress: windows-launch

**Now:** 01 done — แถว Windows ตรง Figma แล้ว; ต่อ 02 (worker Qwen บน Windows และ timeout ต่อ OS)

**Next:**

```
/warroom-build windows-launch 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | Status check, gate และ Setup script ของ Qwen ต่อ OS | done |
| 02 | Worker Qwen บน Windows และ timeout ต่อ OS | ready |
| 03 | ลอง Qwen บนเครื่อง Windows RTX 30xx ขึ้นไป | ready |

## Log

### 01: Status check, gate และ Setup script ของ Qwen ต่อ OS — done 2026-11-06

**Built:**
- แถว `device`, `gpu`, `bitsandbytes`, `model_qwen` บนหน้าติดตั้งตรง [Figma 8111-60588](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8111-60588) — เทียบในเบราว์เซอร์ด้วยสถานะ Windows ปลอม
- การ์ดต่ำกว่าเป้า: แถว Qwen และ bitsandbytes เหลือง แต่แสดงค่าของตัวเอง (revision / เวอร์ชัน / ยังไม่ติดตั้ง) แทน "ดูแถว GPU"; bitsandbytes ไม่ได้ติดตั้งบนการ์ดต่ำกว่าเป้ายังเป็น `warning` และ `ready` true (เดิมหลุดเป็น `missing`)
- อ่านการ์ดไม่ได้: แถว GPU ไม่มีบรรทัดค่า เหลือแค่ "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA"; การ์ดเก่าเกิน: แถว Device แสดง `{การ์ด} · sm_xy`
- ค่าของแถว `warning` (ทั้ง Mac และ Windows) เป็นตัว mono 13px สีเหลือง

**Decided:**
- D15 — ค่าของแถว Windows ตาม Figma (ผู้ใช้เลือก); D14 changed by D15

**For the next ticket:**
- `QWEN_TARGET` ใน `backend/tests/test_checks.py` เก็บข้อความของ `checks.QWEN_GPU_FIX`: ใช้ `QWEN_GPU_FIX.text` แทน หรือเปลี่ยนชื่อ
- `qwen_gpu_problem` อ่าน `status, _, *fix = check_gpu(gpu)` — ok เป็น tuple 2 ตัว ปัญหาเป็น 3 ตัว; `CheckResult` เป็น NamedTuple จะอ่านง่ายกว่า (ข้อเดิม)
- ข้อจาก entry ด้านล่างยังค้าง: `qwen_snapshot(project)` ตอนแตะ `start_worker`

**Checks:** `uv run pytest` (715) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` (321) · `npm --prefix frontend run build` — all green

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
### design link — 2026-11-06

- ออกแบบแถว Windows ใน Figma: 5 สถานะ (ครบ, การ์ดต่ำกว่าเป้า Qwen, การ์ดเก่าเกิน, อ่านการ์ดไม่ได้, Qwen ยังไม่โหลด) × 1440/375 [Figma 8111-60588](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8111-60588); ปุ่ม Refresh ลิงก์ไป frame refreshing เดิม
- spec › Design Source เป็นลิงก์นี้; `ui-prompt.md` ลบ; spec › Design ไม่มีจอ `pending`

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: ติดตั้ง (Status check) — แถว `device`, `gpu`, `bitsandbytes`, `model_qwen` ยังไม่มีแบบ | `/warroom windows-launch` พร้อมลิงก์แบบ | done ([Figma 8111-60588](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8111-60588)) |
| 2 | 03 | ต้องมีเครื่อง Windows ที่การ์ด RTX 30xx ขึ้นไปและ VRAM ≥ 8 GB (spec Open Question 1) | ผู้ใช้ clone `develop` บนเครื่องนั้นแล้ว `/warroom-build windows-launch 03` | open |
