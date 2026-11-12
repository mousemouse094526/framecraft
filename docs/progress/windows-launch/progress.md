# Progress: windows-launch

**แถวเดียวของงาน Windows** (board `Manual = true`, 2026-11-10) — ทุกอย่างที่ต้องทำบนเครื่อง Windows อยู่ที่นี่ รวม `windows-check` (ticket 01–02 ของแถวนั้น) เข้ามาด้วย เพราะเป็นเช็คบนเครื่องเดียวกันและต้องรอเครื่องเดียวกัน

| ที่มา | งาน | สถานะ |
|---|---|---|
| windows-check 01 | เช็ค setup-status บน Windows NVIDIA | ready (ย้ายมา) |
| windows-check 02 | เช็ค spoil บน Windows NVIDIA | ready (ย้ายมา) |

**Now:** 01, 02 done — โค้ด Windows ครบ เช็คด้วย worker ปลอมบน Mac แล้ว; 03 รอเครื่อง Windows RTX 30xx ขึ้นไป (Blocked #2)

**Next:** บนเครื่อง Windows ที่ clone `develop` แล้ว (หลัง merge branch นี้):

```
/warroom-build windows-launch 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | Status check, gate และ Setup script ของ Qwen ต่อ OS | done |
| 02 | Worker Qwen บน Windows และ timeout ต่อ OS | done |
| 03 | ลอง Qwen บนเครื่อง Windows RTX 30xx ขึ้นไป | ready |

## Log

### 02: Worker Qwen บน Windows และ timeout ต่อ OS — done 2026-11-06

**Built:**
- บน Windows งานบรรยายฉาก ร่างบท และเรียบเรียงเริ่ม worker transformers ตัวใหม่ (`spoil_maker/llm_windows.py`) ที่โหลด `Qwen/Qwen3.5-9B` แบบ 4-bit nf4 บน `cuda:0` จาก snapshot เท่านั้น; Mac ใช้ mlx-vlm เดิม ข้อความระหว่าง process เหมือนเดิม
- หลังโหลด worker พิมพ์ module ที่ไม่ได้ย่อ และ VRAM ลง terminal ของ `[api]` ให้ ticket 03 จด
- timeout ทั้งสี่อยู่ในตารางเดียว `llm.TIMEOUTS` (Mac 60/600/300/60, Windows 300/3000/1500/300 วินาที) อ่านตอนเริ่มงาน; งานที่ช้ากว่า Mac บน Windows ไม่ถูกตัด
- เจอว่า `llm_int8_skip_modules=["visual"]` ตามแผนไม่จับ vision tower ใน transformers 5.21.0 → ใช้ `"model.visual"`

**Decided:**
- D16 — skip `model.visual`, dtype bfloat16, รูปแบบ log, ที่อยู่ของตาราง timeout, เขียน/เรียบเรียงเกินเวลายังเป็น "ลองไม่สำเร็จ" (ไม่ใช่ `model_failed`), test worker Windows ด้วย `torch`/`transformers` ปลอม; ticket และ spec อ้าง D16 แล้ว

**For the next ticket:**
- ticket 03 ดูใน log `[qwen] not quantized:` ต้องมีแค่ `model.visual (…)` กับ `lm_head (1)`; ถ้ามีอย่างอื่น skip list พลาด
- ยังไม่ได้เช็คกับโมเดลจริง: `BatchFeature.to` คืนตัวเอง, processor รับ path ของภาพ, `pixel_values` float32 เข้า vision tower bf16 — ดูตอนลองใน 03
- timeout Windows หลังลอง: แก้ค่าใน `llm.TIMEOUTS["win32"]` เป็น max(ค่าเดิม, นานสุด × 3 ปัดขึ้นเป็นนาที) (D7)
- `llm_windows.load` และ `spoil_maker/tokens.py` ไม่ส่ง `cache_dir` (SKILL บอกทุก HF call): ทั้งคู่อ่าน folder snapshot ตรงด้วย `local_files_only` จึงไม่แตะ cache — แก้กฎให้ยกเว้น หรือส่ง `cache_dir` ทั้งสองที่
- `slow_first` ใน `fakes.py` ใช้ `time.sleep(0.5)` จริงตาม seam 3 (0.2 / 0.5 / 1 วินาที); ถ้า test สะดุดบนเครื่องช้า ให้เปลี่ยนเป็นจับวินาทีที่ `_reply` ได้รับ
- ข้อจาก 01 ยังค้าง: `qwen_snapshot(project)` ซ้ำใน `describe.py`, `draft.py`, `qwen_tokens.py`; `QWEN_TARGET` ใน `test_checks.py`

**Checks:** `uv run pytest` (733) · `npm --prefix frontend run typecheck` · `npm --prefix frontend test` (321) · `npm --prefix frontend run build` — all green

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
