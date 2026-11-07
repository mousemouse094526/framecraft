# Spec: windows-launch

ผู้ใช้ Windows ที่มีการ์ด NVIDIA RTX 30xx ขึ้นไปบรรยายฉาก ร่างบท และเรียบเรียงบทสปอยด้วย Qwen ได้เหมือนบน Mac.

**Status:** ready-to-build

## Problem

บน Windows หน้าติดตั้งมีแถว "Qwen3.5 9B model" กับ "mlx-vlm" ที่ขึ้นว่ายังไม่รองรับ เพราะ Qwen ตอนนี้เป็นโมเดล MLX ที่รันด้วย mlx-vlm ซึ่งใช้ได้แค่บน Mac (spoil-maker D50). ผู้ใช้ Windows จึงกด "บรรยายฉาก" ใน tab คลิป และร่างบทหรือเรียบเรียงบทใน tab สปอยไม่ได้เลย.

## Solution

- Setup script บน Windows โหลด `Qwen/Qwen3.5-9B` ที่ pin commit ไว้ลง `models/` เมื่อการ์ดผ่านเป้า (D3, D9).
- บน Windows Qwen รันด้วย transformers และย่อเป็น 4-bit ด้วย bitsandbytes ตอนโหลดขึ้นการ์ด (D3).
- หน้าติดตั้งแสดงแถวตัวรัน Qwen ของ OS นั้นเท่านั้น (D6).
- แถว `device` บอกเมื่อการ์ดเก่าจน torch รันไม่ได้ และกันทุกงาน GPU (D8).
- บน Windows แถว `gpu` บอกชื่อการ์ดและ VRAM และเตือนเมื่อต่ำกว่าเป้าของ Qwen (D8, D9, D10).
- timeout ของงาน Qwen บน Windows ยาวกว่า Mac (D7, D12).
- เพดาน 32,000 token ของ Transcript รวม Story นับด้วย tokenizer ของ repo ที่ OS นั้นใช้ (spoil-maker D46, story-kb D14).

## User Stories

**ผู้ใช้ Windows ที่มีการ์ด RTX 30xx ขึ้นไป ≥ 8 GB**
1. As a ผู้ใช้ Windows, I want รัน Setup script แล้วทุกแถวของหน้าติดตั้งเป็นสีเขียว, so that รู้ว่าเครื่องพร้อมทำสปอย (D3, D6)
2. As a ผู้ใช้ Windows, I want กด "บรรยายฉาก" ใน tab คลิปแล้วงานจบ, so that คลิปพร้อมทำสปอย (D3, D5)
3. As a ผู้ใช้ Windows, I want ร่างบทและเรียบเรียงบทใน tab สปอยได้, so that ทำคลิปสปอยได้ครบบน Windows (D3, D5)
4. As a ผู้ใช้ Windows, I want งานที่ช้ากว่า Mac ไม่ถูกตัดกลางทาง, so that ไม่ต้องกดซ้ำ (D7, D12)

**ผู้ใช้ Windows ที่การ์ดต่ำกว่าเป้า**

5. As a ผู้ใช้ที่มี RTX 20xx หรือการ์ด VRAM < 8 GB, I want หน้าติดตั้งเตือนว่าใช้ Qwen ไม่ได้และต้องใช้การ์ดแบบไหน โดยถอดเสียงกับสร้างเสียงยังใช้ได้, so that ไม่ต้องโหลดโมเดล 19 GB ที่ใช้ไม่ได้ (D9, D10)
6. As a ผู้ใช้ที่มีการ์ด GTX 10xx หรือเก่ากว่า, I want หน้าติดตั้งบอกว่าการ์ดเก่าเกินสำหรับงาน GPU ทุกงาน, so that ไม่กดงานแล้วพังกลางทาง (D8)

## Design

| Screen | User stories | Must show | Source |
|---|---|---|---|
| ติดตั้ง (Status check) | 1, 5, 6 | แถว `device` ที่ไม่ `ok` บอกชื่อการ์ดกับ capability และ `hint` ว่าการ์ดเก่าเกินสำหรับ torch ที่ติดตั้ง (D8); บน Windows แถว `gpu` ชื่อ "GPU" ค่าเป็นชื่อการ์ด VRAM และ capability (D8); `gpu` เป็น `warning` พร้อม `hint` "Qwen ต้องใช้การ์ด NVIDIA RTX 30xx ขึ้นไปที่มี VRAM อย่างน้อย 8 GB" (D9, D10); แถว `model_qwen` และ `bitsandbytes` เป็น `warning` ข้อความเดียวกันเมื่อ `gpu` ไม่ `ok` (D9); probe พัง → `gpu` `warning` "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA" (D12); บน Windows แถว `bitsandbytes` แทน `mlx_vlm` (D6); แถว "Qwen3.5 9B model" แสดง revision ของ repo ของ OS (D6); Mac ไม่มีแถว `gpu` และ `bitsandbytes` (D6, D8) | pending |

Pending screens: one design prompt in [ui-prompt.md](ui-prompt.md).

## Expected Outcome

ผู้ใช้ Windows ที่มีการ์ด RTX 30xx ขึ้นไป ≥ 8 GB ทำคลิปสปอยได้ครบทุกขั้นเหมือนผู้ใช้ Mac.

- **RTX 30xx ขึ้นไป ≥ 8 GB ที่ติดตั้งครบ:** หน้าติดตั้งทุกแถวเขียว รวม "Qwen3.5 9B model", "bitsandbytes" และ "GPU".
- **RTX 2060 6 GB:** Setup script จบปกติโดยไม่โหลด Qwen และพิมพ์เหตุผล; แถว "GPU", "Qwen3.5 9B model", "bitsandbytes" เป็นสีเหลือง; กดบรรยายฉากหรือร่างบทได้ข้อความ `not_ready` ที่บอกแถว "GPU"; ถอดเสียงและสร้างเสียงใช้ได้.
- **GTX 1050 Ti:** แถว "Device" เป็นสีแดงพร้อมเหตุผล; กดถอดเสียง สร้างเสียง บรรยายฉาก หรือร่างบทได้ข้อความ `not_ready` ที่บอกแถว "Device".
- **Mac:** หน้าติดตั้งและงานทุกงานเหมือนเดิม.

**How success is judged:**

- บนเครื่อง Windows ที่ตรงเป้า (D10) ผ่านทุกข้อของ D5 กับ Temp clip `f7jkZXvaB4g`.
- จำนวน token ของ Transcript ทั้งหมดของ `f7jkZXvaB4g` นับบน Windows ได้เท่ากับบน Mac; ไม่เท่า → Blocked (D12).
- บน Mac test ทั้งหมดผ่าน และหน้าติดตั้งไม่มีแถวใหม่.

## Implementation

### Modules touched

- **`backend.models`**
  - เพิ่ม `ModelSpec` ตัวที่สองของ Qwen สำหรับ Windows (D3):
    - `check_id` `model_qwen`
    - label "Qwen3.5 9B model"
    - `repo_id` `Qwen/Qwen3.5-9B`
    - `revision` `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
    - `allow_patterns` เหมือนตัว MLX (`*.json`, `*.safetensors`, `*.txt`, `*.jinja`)
    - license Apache-2.0, `license_url` เดียวกับตัว MLX, author Qwen
    - `platforms` `("win32",)`
  - ฟังก์ชัน `qwen_for(sys_platform)` คืน spec ของ OS นั้น; OS อื่น (Linux ใน test) คืนตัว Mac.
  - ทุกจุดที่ใช้ `QWEN` ตรงๆ (`checks`, `gate_rows`, `qwen_tokens`, `spoil_maker.describe`, `spoil_maker.draft`) เปลี่ยนไปเรียก `qwen_for(checks.this_platform())` ตอนใช้งาน.
  - `MODELS` มีทั้งสอง spec; Setup script โหลดเฉพาะตัวที่ `platforms` ตรงตามเดิม.
- **`backend.checks`**
  - แถว `device` เช็ครุ่นการ์ด ดู ### Status check (D8).
  - แถว `gpu` หลังแถว `device` บน Windows เท่านั้น (D8).
  - บน Windows แถว `bitsandbytes` แทนแถว `mlx_vlm` ในตำแหน่งเดียวกัน ใช้ `check_package("bitsandbytes")` (D6, D12).
  - แถว `model_qwen` เช็ค spec ของ OS นั้น (D6).
  - เลิกใช้ `MAC_ONLY_FIX` และ `UNSUPPORTED_HERE` กับแถว Qwen.
  - `Probes` เพิ่ม `gpu` ที่คืน `GpuInfo` ให้ test สลับได้ (setup-status D18).
- **`backend.gate_rows`**
  - `DEVICE` ใช้เงื่อนไขใหม่ของแถว `device` จึงกันงานถอดเสียง สร้างเสียง และ Qwen ทั้งหมด (D8).
  - `qwen_jobs` = `ffmpeg`, `device`, `gpu` (Windows เท่านั้น), `model_qwen`, และแถวตัวรันของ OS (D6, D8).
- **`backend.setup`**
  - `REQUIRED_FREE_BYTES["win32"]` 15 → 30 GB (D12).
  - บน Windows อ่านแถว `gpu` ก่อนโหลด; ไม่ `ok` → ข้าม spec Qwen ของ Windows และพิมพ์ข้อความของแถว (D9).
  - ผลสุดท้ายนับ `warning` เป็นผ่านตามเดิม จึงจบปกติ (D9).
- **`backend.spoil_maker.llm`**
  - ข้อความระหว่าง process (`Generate`, `Ready`, `Generated`, `WorkerError`) ไม่เปลี่ยน.
  - `start_worker` เลือก worker ตาม OS: Mac ใช้ worker mlx-vlm เดิม, Windows ใช้ worker transformers ใหม่ (D3).
  - worker ของ Windows อยู่ใน module ของตัวเอง ที่ import transformers และ bitsandbytes ภายใน process ลูกเท่านั้น (ADR-0012).
- **`backend.spoil_maker.describe`** และ **`backend.spoil_maker.draft`**
  - timeout ทั้งสี่อ่านจากตารางต่อ OS ตอนเริ่มงาน (D7, D12) ดู ### ค่าต่อ OS.
  - ข้อความ `JobFailed` ที่บอกจำนวนวินาทีใช้ค่าจากตาราง.
- **`backend.qwen_tokens`**
  - นับด้วย tokenizer ใน snapshot ของ `qwen_for(...)`; เพดานยังเป็น 32,000 (spoil-maker D46, story-kb D14).
- **`pyproject.toml`** และ **`uv.lock`**
  - เพิ่ม `bitsandbytes` เฉพาะ `sys_platform == 'win32'` pin ใน `uv.lock` (D3).
- **`frontend`**
  - หน้าติดตั้งแสดงแถวจาก API อยู่แล้ว; เปลี่ยนเฉพาะที่แบบใน Figma ต่างจากแถวเดิม.

### Data

```python
class GpuInfo(NamedTuple):
    name: str                    # nvidia-smi name of GPU 0
    memory_bytes: int            # nvidia-smi memory.total (MiB × 2**20)
    capability: tuple[int, int]  # nvidia-smi compute_cap, e.g. "8.6" → (8, 6)
    arch_list: tuple[str, ...]   # torch.cuda.get_arch_list(), e.g. ("sm_75", "sm_80", ...)
```

probe `gpu` คืน `GpuInfo` หรือ raise; บน Mac ไม่ถูกเรียก.

### Windows worker

ขั้นตอนใน process ลูก (D3, D10, D12):

1. snapshot ไม่ใช่ folder → raise `FileNotFoundError` ก่อนเรียก transformers เพราะ `from_pretrained` โหลดจาก network เมื่อไม่เจอ folder (ADR-0008).
2. โหลด `AutoProcessor` และ `AutoModelForImageTextToText` จาก snapshot ด้วย `local_files_only=True`, `device_map` `cuda:0`.
3. `quantization_config` เป็น `BitsAndBytesConfig`:
   - `load_in_4bit=True`
   - `bnb_4bit_quant_type="nf4"`
   - `bnb_4bit_compute_dtype=torch.bfloat16`
   - `llm_int8_skip_modules=["visual", "lm_head"]`
4. log ชื่อ module ที่ไม่ได้ย่อ และ VRAM ที่ใช้หลังโหลด (trial อ่านค่านี้).
5. ส่ง `Ready`.
6. ต่อ `Generate`: สร้างข้อความ chat ด้วย `processor.apply_chat_template(..., enable_thinking=False)` (spoil-maker D51) พร้อมภาพเมื่อมี แล้ว `generate` ด้วย `max_new_tokens` และ `temperature` ของคำขอ; `temperature` 0 = `do_sample=False`.
7. ส่ง `Generated` เป็นข้อความที่ถอดเฉพาะ token ใหม่ ไม่รวม prompt และ special token.
8. exception ใดๆ → `WorkerError("model_failed", …)` แล้วออก ตาม worker เดิม.

### Status check

| Row | OS | `ok` เมื่อ | ไม่ `ok` |
|---|---|---|---|
| `device` | Windows | `cuda` และ `sm_{major}{minor}` อยู่ใน `arch_list` | `missing` `hint` "การ์ด {name} (sm_{xy}) เก่าเกินสำหรับ torch ที่ติดตั้ง" (D8) |
| `device` | Mac | เหมือนเดิม (`mps`) | เหมือนเดิม |
| `gpu` | Windows | capability ≥ (8, 0) และ `memory_bytes` ≥ 7.5 GiB | `warning` `hint` เป้าของ Qwen (D9, D10); probe raise → `warning` "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA" (D12) |
| `bitsandbytes` | Windows | `gpu` `ok` และติดตั้งแล้ว | `gpu` ไม่ `ok` → `warning` ข้อความของ `gpu`; ไม่ได้ติดตั้ง → `missing` คำสั่ง setup |
| `mlx_vlm` | Mac | เหมือนเดิม | เหมือนเดิม |
| `model_qwen` | Windows | `gpu` `ok` และ Model marker ของ `Qwen/Qwen3.5-9B` ตรง revision และไฟล์ครบ | `gpu` ไม่ `ok` → `warning` ข้อความของ `gpu`; ไม่ครบ → `missing` คำสั่ง setup |
| `model_qwen` | Mac | เหมือนเดิม | เหมือนเดิม |

- ค่าที่แถว `gpu` แสดง: `{name} · {VRAM} GB · sm_{xy}`.
- VRAM 7.5 GiB: การ์ด 8 GB รายงาน total memory ต่ำกว่า 8 GiB เล็กน้อย.
- ทุกแถวอ่านการ์ด index 0 ตัวเดียวกับ worker (D8).
- ไม่โหลดโมเดลและไม่ใช้ network (setup-status D7).
- probe `gpu` อ่านชื่อ VRAM และ capability จาก `nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader,nounits -i 0` (timeout 5 วินาที) ไม่เรียก `torch.cuda.get_device_properties` เพื่อไม่ให้ backend process สร้าง CUDA context ที่กิน VRAM ข้าง worker (D12); `arch_list` มาจาก `torch.cuda.get_arch_list()`.
- gate รับเฉพาะ `ok`, จึง `warning` ของ `gpu` กันงาน Qwen แต่ไม่ทำให้ `ready` เป็น false (D9).

### ค่าต่อ OS

ตาราง `Timeouts(describe, write, polish, pick)` ต่อ OS อยู่ที่เดียวใน `backend.spoil_maker` อ่านด้วย `checks.this_platform()` ตอนเริ่มงาน; test สลับตารางแทนการ patch ค่าคงที่ (D12).

| ค่า | Mac | Windows ก่อนลอง | Windows หลังลอง |
|---|---|---|---|
| บรรยายต่อ Shot | 60 วินาที | 300 วินาที | max(300, นานสุดที่วัด × 3 ปัดขึ้นเป็นนาที) |
| เขียนบท | 600 วินาที | 3000 วินาที | max(3000, นานสุดที่วัด × 3 ปัดขึ้นเป็นนาที) |
| เรียบเรียง | 300 วินาที | 1500 วินาที | max(1500, นานสุดที่วัด × 3 ปัดขึ้นเป็นนาที) |
| เลือก Shot | 60 วินาที | 300 วินาที | max(300, นานสุดที่วัด × 3 ปัดขึ้นเป็นนาที) |

(D7, D12)

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| transformers | 5.21.0 (installed) | `AutoModelForImageTextToText` map `qwen3_5` ไป `Qwen3_5ForConditionalGeneration`, vision tower ชื่อ `visual` | [modeling_qwen3_5.py v5.21.0](https://github.com/huggingface/transformers/blob/v5.21.0/src/transformers/models/qwen3_5/modeling_qwen3_5.py) |
| transformers | 5.21.0 (installed) | `BitsAndBytesConfig` nf4; `llm_int8_skip_modules` แทน default ทั้งชุด จึงต้องใส่ `lm_head` เอง | [bitsandbytes quantization](https://huggingface.co/docs/transformers/en/quantization/bitsandbytes) |
| transformers | 5.21.0 (installed) | `processor.apply_chat_template` ส่ง kwarg ที่ไม่รู้จัก (`enable_thinking`) ต่อให้ jinja template | [Chat templates](https://huggingface.co/docs/transformers/en/chat_templating) |
| transformers | 5.21.0 (installed) | `AutoTokenizer` จาก `Qwen/Qwen3.5-9B` นับ token เท่ากับ repo MLX (`vocab.json` และ `chat_template.jinja` ตรงกันทุก byte, `tokenizer.json` ไม่ตรง) | [Qwen/Qwen3.5-9B files](https://huggingface.co/Qwen/Qwen3.5-9B/tree/main) |
| bitsandbytes | to be added | wheel บน PyPI รันบน Windows กับ CUDA 12.8 และ sm_80 ขึ้นไป | [bitsandbytes installation](https://huggingface.co/docs/bitsandbytes/main/en/installation) |
| torch | 2.8.0 cu128 (installed) | `get_arch_list()` ให้ sm ที่ build รองรับ | [torch.cuda](https://docs.pytorch.org/docs/2.8/cuda.html) |
| nvidia-smi | มากับ driver NVIDIA | `--query-gpu=name,memory.total,compute_cap` คืนค่า CSV ของการ์ด index 0 โดยไม่สร้าง CUDA context | [nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html) |
| torch | 2.8.0 cu128 (installed) | build cu128 ไม่มี kernel ของ Maxwell และ Pascal (sm_50–sm_61) | [PyTorch dev-discuss](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128) |

## Seams

ใช้ seam เดิมของ spoil-maker ที่ API คุยกับ worker ปลอม (spoil-maker D47) และ `run_checks` กับ probe ปลอม (setup-status D18); worker จริงเช็คมือบนเครื่อง Windows (D5, D11).

1. **Status check และ Setup script ต่อ OS** `backend.checks.run_checks(sys_platform=…, probes=…)` และ `backend.setup` กับ `download` ปลอม
   - `win32`, `GpuInfo` sm 8.6 12 GiB, marker ของ `Qwen/Qwen3.5-9B` ครบ, `bitsandbytes` ติดตั้ง → `device`, `gpu`, `model_qwen`, `bitsandbytes` เป็น `ok`; ไม่มีแถว `mlx_vlm`.
   - `win32`, sm 7.5 8 GiB → `gpu`, `model_qwen`, `bitsandbytes` เป็น `warning`; `ready` true.
   - `win32`, sm 8.6 6 GiB → `gpu` เป็น `warning`.
   - `win32`, sm 6.1 ไม่อยู่ใน `arch_list` → `device` เป็น `missing`.
   - `win32`, probe `gpu` raise → `gpu` เป็น `warning` ข้อความ driver.
   - `win32`, marker ของตัว MLX อย่างเดียว และการ์ดผ่าน → `model_qwen` เป็น `missing`.
   - `darwin` → แถวเหมือนเดิมทุกแถว; ไม่มี `gpu` และ `bitsandbytes`.
   - setup บน `win32` ที่ `gpu` เป็น `warning` → `download` ปลอมไม่ได้รับ `Qwen/Qwen3.5-9B`; exit 0.
   - setup บน `win32` ที่ว่าง 20 GB และต้องโหลด Qwen → ปฏิเสธด้วยข้อความดิสก์ไม่พอ.
2. **gate และตัวนับ token ของงาน Qwen** `POST /api/describes`, `POST /api/draft-jobs`, `GET /api/clips/{clip_id}/episodes` กับ worker ปลอม บน `win32`
   - `gpu` เป็น `warning` → `503` `not_ready` ที่ `rows` มี `gpu`; worker ปลอมไม่ถูกเรียก.
   - `device` ไม่ผ่าน → `POST` ถอดเสียงและสร้างเสียงได้ `503` `not_ready` ที่ `rows` มี `device`.
   - ทุกแถวผ่าน → งานเริ่ม และ worker ปลอมได้ snapshot ของ `Qwen/Qwen3.5-9B`.
   - ไม่มี marker ของ `Qwen/Qwen3.5-9B` → `GET .../episodes` ตอบ `503` `not_ready` ที่ `rows` มี `model_qwen`; มี marker → ตัวนับปลอมได้ snapshot ของ `Qwen/Qwen3.5-9B`.
3. **timeout ต่อ OS** Describe job และ Draft job กับตาราง timeout ที่สลับเป็นค่าเล็ก (Mac 0.2 วินาที, Windows 1 วินาที) และ worker ปลอมที่ตอบใน 0.5 วินาที
   - ทั้งสี่ขั้น (บรรยาย, เขียน, เรียบเรียง, เลือก Shot) บน `win32` → `done`.
   - ทั้งสี่ขั้นบน `darwin` → `model_failed` ข้อความบอกวินาทีจากตาราง.
4. **หน้าติดตั้ง** `SetupStatusPage` กับ fetch ปลอม
   - status มีแถว `gpu` `warning` พร้อม `hint` → เห็นชื่อ "GPU", ค่า, และข้อความ hint ไม่มีปุ่ม copy.

## Testing decisions

- **Copy:** `backend/tests/test_checks.py` — การเรียก `run_checks` กับ `sys_platform` และ probe ปลอม.
- **Copy:** `backend/tests/test_setup.py` — `download` ปลอม, `free_bytes` ปลอม, การข้ามโมเดลตาม `platforms`.
- **Copy:** `backend/tests/test_spoil_maker_describe_api.py` และ `backend/tests/test_spoil_maker_draft_api.py` — worker ปลอม, `checks.this_platform`, gate `not_ready`, และ test timeout เดิมที่ patch ค่าคงที่ (เปลี่ยนเป็นสลับตาราง).
- **Copy:** `backend/tests/test_spoil_maker_episodes_api.py` — ตัวนับ token ปลอม.
- **Copy:** `frontend/src/features/setup-status/components/SetupStatusPage.test.tsx` — แถว `warning` กับ `hint`.
- worker ของ Windows ไม่มี unit test ที่โหลดโมเดล; ticket ลองเช็คมือตาม D5 แล้วจดใน `docs/features/windows-launch/windows-trial.md`:
  - เวลาจากเริ่มงานถึง `Ready`, เวลานานสุดต่อขั้น, VRAM สูงสุด
  - module ที่ไม่ได้ย่อจาก log
  - จำนวน token ของ Transcript ทั้งหมดของ `f7jkZXvaB4g` บนทั้งสอง OS
- `backend/tests/test_model_imports.py` ต้องยังผ่าน: import backend ไม่ import module ของ worker Windows หรือ transformers.

## Out of Scope

- ช่องวางลิงก์ Hugging Face ของโมเดลเองและปุ่ม "ตรวจสอบ" — feature แยกที่วางแผนทีหลัง (D1).
- Qwen บน RTX 20xx และการ์ด VRAM < 8 GB (D9, D10).
- งาน GPU ใดๆ บน GTX 10xx หรือเก่ากว่า (D8).
- เพดานเวลาของงานบน Windows (D5).
- เปลี่ยนโมเดลหรือตัวรันบน Mac (D3).
- การ์ดหลายใบ: ใช้การ์ด index 0 เท่านั้น (D8).
- การเช็ค setup-status และ spoil บน Windows — อยู่ใน `windows-check`.

## Open Questions

1. ต้องมีเครื่อง Windows ที่การ์ด RTX 30xx ขึ้นไปและ VRAM ≥ 8 GB เพื่อทำ trial (เครื่องที่มีคือ GTX 1050 Ti 4 GB) — non-blocking: โค้ดและ test บน Mac ทำได้ก่อน (D11); เป็น Blocked ของ ticket ลองบน Windows.
2. เวอร์ชัน `bitsandbytes` ที่ pin — non-blocking: build เลือกเวอร์ชันล่าสุดที่มี wheel Windows ตอนนั้นและจดใน `uv.lock`.
3. Qwen 4-bit ทำงานบน 8 GB ที่ 32,000 token โดยไม่ out of memory หรือไม่ — non-blocking: วัดใน trial; ไม่พอ → change request ปรับเกณฑ์ VRAM ของแถว `gpu` (D9, D11).
4. Qwen3.5 ต้องใช้ kernel เสริมของ linear attention ที่ไม่มีบน Windows หรือไม่ — non-blocking: ถ้าไม่มี transformers ใช้ทาง torch ล้วนที่ช้ากว่า ซึ่ง D5 ไม่กำหนดเวลา; trial จดเวลา.

## Sources

- [Qwen/Qwen3.5-9B files](https://huggingface.co/Qwen/Qwen3.5-9B/tree/main) — revision ที่ pin, ขนาด 19.3 GB, license, ไฟล์ tokenizer (accessed 2026-11-06)
- [transformers modeling_qwen3_5.py v5.21.0](https://github.com/huggingface/transformers/blob/v5.21.0/src/transformers/models/qwen3_5/modeling_qwen3_5.py) — class และชื่อ `visual` (accessed 2026-11-06)
- [transformers: bitsandbytes quantization](https://huggingface.co/docs/transformers/en/quantization/bitsandbytes) — nf4 และ `llm_int8_skip_modules` (accessed 2026-11-06)
- [transformers: Chat templates](https://huggingface.co/docs/transformers/en/chat_templating) — kwarg ของ template (accessed 2026-11-06)
- [bitsandbytes installation](https://huggingface.co/docs/bitsandbytes/main/en/installation) — wheel บน Windows (accessed 2026-11-06)
- [torch.cuda 2.8](https://docs.pytorch.org/docs/2.8/cuda.html) — `get_arch_list` (accessed 2026-11-06)
- [nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html) — query ของแถว `gpu` (accessed 2026-11-06)
- [PyTorch dev-discuss: Maxwell and Pascal removed in CUDA 12.8 builds](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128) — เหตุผลของแถว `device` (accessed 2026-11-06)
