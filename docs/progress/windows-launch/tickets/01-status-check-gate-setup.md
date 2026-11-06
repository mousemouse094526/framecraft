# 01: Status check, gate และ Setup script ของ Qwen ต่อ OS

**What to build:** บน Windows หน้าติดตั้งแสดงแถว "GPU" กับ "bitsandbytes" แทน "mlx-vlm" และแถว "Qwen3.5 9B model" เช็ค `Qwen/Qwen3.5-9B`; การ์ดเก่าเกินถูกกันทุกงาน GPU และการ์ดต่ำกว่าเป้าถูกกันเฉพาะงาน Qwen พร้อมเหตุผล. Setup script บน Windows โหลด Qwen เฉพาะเมื่อการ์ดผ่านเป้าและเช็คดิสก์ 30 GB. บน Mac ทุกอย่างเหมือนเดิม.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D3 (spec ของ Windows, `bitsandbytes` ใน dependency), D6, D8, D9, D10, D12 (ดิสก์, อ่านการ์ด, probe พัง, `bitsandbytes`, seam), spoil-maker D46, story-kb D14, setup-status D7, setup-status D18
- ADR: 0004, 0008, 0009, 0016, 0025, 0026
- Screens: ติดตั้ง (Status check)
- Seams: 1, 2 (gate และตัวนับ token), 4
- User stories: 1, 5, 6

**Status:** ready-for-agent

## Acceptance criteria

### Model spec ต่อ OS

- `qwen_for("win32")` → spec `Qwen/Qwen3.5-9B` revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` ตาม spec › Modules touched; `darwin` และ `linux` → spec MLX เดิม
- ทุกจุดที่เคยอ่าน Qwen spec ตรงๆ (checks, gate, ตัวนับ token, Describe job, Draft job) อ่านผ่าน `qwen_for(checks.this_platform())` ตอนใช้งาน
- `bitsandbytes` เป็น dependency เฉพาะ `sys_platform == 'win32'` และ pin ใน lock; import backend บน Mac ไม่ import transformers หรือ bitsandbytes (test import เดิมผ่าน)

### Status check บน Windows

- `GpuInfo` sm 8.6 12 GiB, marker ของ `Qwen/Qwen3.5-9B` ครบ, `bitsandbytes` ติดตั้ง → `device`, `gpu`, `model_qwen`, `bitsandbytes` เป็น `ok`; ไม่มีแถว `mlx_vlm`; `bitsandbytes` อยู่ตำแหน่งเดิมของ `mlx_vlm`
- แถว `gpu` อยู่หลัง `device` ชื่อ "GPU" ค่า `{name} · {VRAM} GB · sm_{xy}`
- sm 7.5 8 GiB → `gpu`, `model_qwen`, `bitsandbytes` เป็น `warning` `hint` "Qwen ต้องใช้การ์ด NVIDIA RTX 30xx ขึ้นไปที่มี VRAM อย่างน้อย 8 GB"; `ready` true
- sm 8.6 6 GiB → `gpu` เป็น `warning`
- sm 6.1 ไม่อยู่ใน `arch_list` → `device` เป็น `missing` `hint` "การ์ด {name} (sm_61) เก่าเกินสำหรับ torch ที่ติดตั้ง"
- probe `gpu` raise → `gpu` เป็น `warning` "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA"
- marker ของตัว MLX อย่างเดียว และการ์ดผ่าน → `model_qwen` เป็น `missing` พร้อมคำสั่ง setup
- probe `gpu` อ่านจาก `nvidia-smi` ตาม spec › Status check ไม่สร้าง CUDA context ใน backend process

### Status check บน Mac

- `darwin` → แถวและค่าเหมือนก่อน ticket ทุกแถว; ไม่มี `gpu` และ `bitsandbytes`

### Gate และตัวนับ token บน Windows

- `gpu` เป็น `warning` → `POST /api/describes` และ `POST /api/draft-jobs` ได้ `503` `not_ready` ที่ `rows` มี `gpu`; worker ปลอมไม่ถูกเรียก
- `device` ไม่ผ่าน → `POST` ถอดเสียงและสร้างเสียงได้ `503` `not_ready` ที่ `rows` มี `device`
- ไม่มี marker ของ `Qwen/Qwen3.5-9B` → `GET /api/clips/{clip_id}/episodes` ได้ `503` `not_ready` ที่ `rows` มี `model_qwen`
- มี marker → ตัวนับ token ปลอมได้ snapshot ของ `Qwen/Qwen3.5-9B`; เพดานยัง 32,000

### Setup script

- `win32` ที่ `gpu` เป็น `warning` → `download` ปลอมไม่ได้รับ `Qwen/Qwen3.5-9B`, พิมพ์ข้อความของแถว `gpu`, exit 0
- `win32` ที่ว่าง 20 GB และต้องโหลด Qwen → ปฏิเสธด้วยข้อความดิสก์ไม่พอ (เกณฑ์ 30 GB)
- `darwin` → โหลดเฉพาะ spec MLX ตามเดิม

### หน้าติดตั้ง

- status มีแถว `gpu` `warning` พร้อม `hint` → เห็นชื่อ "GPU", ค่า, และข้อความ hint ไม่มีปุ่ม copy
- หน้าตาของแถว `device`, `gpu`, `bitsandbytes`, `model_qwen` ตรงแบบใน Figma (รอแบบ: progress › Blocked #1)
