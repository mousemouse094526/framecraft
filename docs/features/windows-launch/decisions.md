# Decisions: windows-launch

## D1: Qwen บน Windows เป็น feature `windows-launch`; ช่องวางลิงก์โมเดลเองเป็นอีก feature ทีหลัง

**Chosen:** `windows-launch` ทำให้ Qwen บรรยายฉาก ร่างบท และเรียบเรียงบทได้บน Windows NVIDIA ด้วยตัวรันบน CUDA กับโมเดลที่ pin ใน `backend.models` ตาม ADR-0004. ช่องวางลิงก์ Hugging Face ของโมเดลเองพร้อมปุ่ม "ตรวจสอบ" เป็น feature ใหม่ที่วางแผนทีหลัง.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: งานแรกทำตาม ADR-0004 ได้โดยไม่ต้องแตะ ส่วนช่องวางลิงก์มี UI และข้อมูลของตัวเอง ใช้ได้ทั้งสอง OS และต้องตัดสิน ADR-0004 ก่อน.

**Rejected:**
- feature เดียวทำทั้งสองข้อ — ต้องตัดสิน ADR-0004 ก่อนได้ลองโมเดลบน Windows จริง
- feature เดียว จดช่องวางลิงก์เป็น Open Question — ช่องวางลิงก์ใช้ได้เองโดยไม่ต้องรอ feature นี้

**Details:**
- ชื่อ `windows-launch` มาจาก spoil-maker D50

**From:** interview · **Status:** active

## D2: Windows เป้าหมายคือการ์ด RTX (sm_75 ขึ้นไป) ที่มี VRAM ≥ 8 GB; GTX 1050 Ti ไม่อยู่ใน scope

**Chosen:** `windows-launch` คง CUDA 12.8 และ torch 2.8.0 ตาม ADR-0016 และตั้งเป้าที่การ์ด NVIDIA RTX 20xx ขึ้นไป (compute capability ≥ 7.5) ที่มี VRAM อย่างน้อย 8 GB โดยใช้ Qwen3.5-9B แบบ 4-bit. VRAM ขั้นต่ำจริงยืนยันจากการวัดบนเครื่องลอง; การเช็คบนเครื่องจริงรอจนได้เครื่องที่ตรงเป้า.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: คุณภาพบทและคำบรรยายฉากเท่า Mac และไม่ต้องเปลี่ยน CUDA ของทั้ง project; เครื่องลองที่มีอยู่ (GTX 1050 Ti 4 GB) รัน build cu128 ไม่ได้และใส่โมเดลไม่พอ.

**Rejected:**
- รองรับการ์ดเก่า 4 GB ด้วย CUDA 12.6 และ Qwen3.5 2B/4B — supersede ADR-0016, บทไทยและคำบรรยายภาพแย่ลงมาก, โมเดลต่างจาก Mac
- llama.cpp GGUF แบ่ง GPU กับ RAM — ช้าเป็นชั่วโมงต่อคลิป, ติดตั้งยากบน Windows, Whisper และ OmniVoice บน Pascal ก็ยังใช้ไม่ได้

**Details:**
- torch 2.8 build cu128 ไม่มี kernel ของ Maxwell และ Pascal (sm_50–sm_61): GTX 10xx ได้ `no kernel image is available for execution on the device`
- 1050 Ti ทำ `windows-check` ไม่ได้เช่นกัน (Whisper, OmniVoice ใช้ torch ตัวเดียวกัน)
- Qwen3.5-9B 4-bit: น้ำหนักราว 5–6 GB, รวม vision และ context 32k ราว 7 GB ตามที่การ์ดโมเดลประเมิน ยังไม่ได้วัด

**Sources:** [PyTorch: Maxwell and Pascal removed in CUDA 12.8 builds](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128) · [torch 2.8.0 release notes](https://newreleases.io/project/pypi/torch/release/2.8.0) · [uv #14742](https://github.com/astral-sh/uv/issues/14742)

**From:** interview · **Status:** changed by D10

## D3: Windows รัน Qwen ด้วย transformers กับ `Qwen/Qwen3.5-9B` ที่ย่อเป็น 4-bit ด้วย bitsandbytes ตอนโหลด

**Chosen:** บน Windows ตัวรันเป็น transformers ที่ project ติดตั้งอยู่แล้ว โหลด `Qwen/Qwen3.5-9B` (Apache-2.0) ที่ pin commit ใน `backend.models` แล้วย่อเป็น 4-bit nf4 ด้วย bitsandbytes ตอนโหลดขึ้นการ์ด; Mac ยังใช้ mlx-vlm กับ `mlx-community/Qwen3.5-9B-MLX-4bit` ตามเดิม.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: ใช้ตัวรันที่มีอยู่แล้ว ได้โมเดลจาก Qwen โดยตรง และ tokenizer ตระกูลเดียวกับ Mac ทำให้เพดาน 32,000 token นับเหมือนกัน.

**Rejected:**
- transformers กับ repo AWQ ที่คนอื่นย่อไว้ — คนย่อไม่ใช่ Qwen, kernel ของ compressed-tensors บน Windows ไม่แน่นอน, การ์ดโมเดลแนะนำ vLLM ที่ไม่มีบน Windows
- llama.cpp กับ GGUF และ mmproj — wheel CUDA บน Windows ต้อง build เอง ขัด `uv.lock`, tokenizer ของ GGUF อาจนับต่างจาก Mac

**Details:**
- dependency ใหม่: `bitsandbytes` เฉพาะ `sys_platform == 'win32'`
- ดาวน์โหลดครั้งแรกราว 19 GB (bf16 safetensors) ลง `models/` ตาม ADR-0003
- vision tower ไม่ย่อ (คง bf16) เพื่อให้คำบรรยายฉากใกล้ Mac

**Sources:** [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B/tree/main)

**From:** interview · **Status:** active

## D4: Status check มีแถว `gpu` บอกชื่อการ์ดและ VRAM; การ์ดต่ำกว่าเป้าไม่ผ่าน gate ของงาน Qwen

**Chosen:** Status check เพิ่มแถว `gpu` ที่แสดงชื่อการ์ดและ VRAM. บน Windows แถวไม่ `ok` เมื่อ compute capability ต่ำกว่า 7.5 หรือ VRAM ต่ำกว่า 8 GB พร้อมข้อความว่าต้องการ RTX 20xx ขึ้นไปที่มี VRAM ≥ 8 GB; Describe job และ Draft job gate ด้วยแถวนี้ จึงไม่เริ่มแล้วพังกลางทาง.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: ผู้ใช้เห็นสาเหตุก่อนกดงาน แทน error `out of memory` หรือ `no kernel image` หลังรอโหลดโมเดล.

**Rejected:**
- ไม่เช็ค ปล่อยงานพังเป็น `model_failed` — ผู้ใช้ไม่รู้ว่าต้องเปลี่ยนการ์ด
- แถวเตือนที่ไม่ gate — การ์ดที่ไม่ผ่านเป้ารันไม่ได้อยู่ดี (D2)

**Details:**
- ตามกฎ Status check เดิม (setup-status D7, ADR-0009): อ่านจาก `torch.cuda` โดยไม่โหลดโมเดลและไม่ใช้ network
- บน Mac แถวแสดงชิปและ memory เป็น `ok` เสมอ ไม่เพิ่ม gate ใหม่ให้ Mac

**From:** interview · **Status:** changed by D8, D9

## D5: เครื่อง Windows ลองผ่านเมื่องาน Qwen ทั้งสามจบได้ ไม่กำหนดเวลา

**Chosen:** บนเครื่อง Windows ที่ตรงเป้า (D2) กับ Temp clip `f7jkZXvaB4g` (96 นาที): Describe job ทั้งเรื่องจบ `done`, Draft job (ร่างบท เรียบเรียง เลือก Shot) ของ EP 30 นาทีจบ `done` รวมกรณี Transcript กับ Story ใกล้ 32,000 token, ปุ่ม "เรียบเรียงใหม่" จบ `done`, และผู้ใช้อ่านบทไทยแล้วบอกว่าใช้ได้. ไม่มีเพดานเวลา; เวลาที่วัดได้จดใน trial.

**Why:** ผู้ใช้เลือก: ขอแค่ใช้ได้บน Windows ความเร็วไม่ใช่เงื่อนไข.

**Rejected:**
- ไม่ช้ากว่า Mac 2 เท่า (บรรยายฉาก ≤ 105 นาที) — ผู้ใช้ไม่ต้องการเพดานเวลา
- เร็วเท่า Mac (≤ 53 นาที) — อาจบังคับให้เปลี่ยนตัวรันหลังลอง

**From:** interview · **Status:** active

## D6: Status check แสดงแถวตัวรันของ OS นั้นเท่านั้น

**Chosen:** Mac เห็นแถว `mlx_vlm`, Windows เห็นแถว `bitsandbytes` แทน; แถว `model_qwen` ชื่อ "Qwen3.5 9B model" เหมือนกันทั้งสอง OS แต่เช็ค repo และ revision ของ OS นั้น. ไม่มีแถว "ยังไม่รองรับ" ของอีก OS.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: เครื่องที่ติดตั้งครบเห็นทุกแถวเขียว และ id เดิม (`model_qwen`, `mlx_vlm`) ที่หน้าเว็บและ gate ใช้อยู่ไม่ต้องเปลี่ยน.

**Rejected:**
- แถวเดียวชื่อกลาง "Qwen runner" — ต้องเปลี่ยน id ที่หน้าเว็บ, gate และ `not_ready.rows` ใช้
- แสดงทั้งสองแถวทุก OS เป็นสีเทา — แถวที่ไม่เกี่ยวกับเครื่องรกจอ

**From:** interview · **Status:** active

## D7: timeout ของงาน Qwen ตั้งต่อ OS; Windows ใช้ค่าจากผลลอง

**Chosen:** timeout ทั้งสี่ (บรรยายต่อ Shot, เขียนบท, เรียบเรียง, เลือก Shot) มีค่าต่อ OS. Mac คงค่าเดิม (60, 600, 300, 60 วินาที); Windows ตั้งต้นที่ค่า Mac × 5 จนเครื่องลองวัดได้ แล้วเปลี่ยนเป็นเวลานานสุดที่วัดได้ × 3 ปัดขึ้นเป็นนาทีเต็ม และไม่ต่ำกว่าค่า Mac.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: Windows ช้ากว่าแล้วไม่ล้มกลางทาง (D5) และยังจับโมเดลที่ค้างได้.

**Rejected:**
- ใช้ค่าเดียวกับ Mac — เครื่องที่ช้ากว่าล้ม `model_failed` ทั้งที่ยังทำงาน ขัด D5
- ไม่มี timeout บน Windows — โมเดลค้างแล้วงานค้างจนผู้ใช้ยกเลิกเอง

**Details:**
- การโหลดโมเดลยังไม่มี timeout ตามเดิม
- ค่าตั้งต้น Windows: 300, 3000, 1500, 300 วินาที

**From:** interview · **Status:** changed by D12

## D8: รุ่นการ์ดเช็คในแถว `device` ทุกงาน GPU; แถว `gpu` มีเฉพาะ Windows และ gate เฉพาะงาน Qwen

**Chosen:** แถว `device` ไม่ `ok` เมื่อ compute capability ของการ์ด CUDA ไม่อยู่ใน arch list ของ torch ที่ติดตั้ง จึง gate ทุกงาน GPU (ถอดเสียง, สร้างเสียง, Qwen). แถว `gpu` (ชื่อการ์ด, VRAM, compute capability) มีบน Windows เท่านั้นและ gate เฉพาะ Describe job กับ Draft job; Mac ไม่มีแถว `gpu`.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: red team ชี้ว่าการ์ด Pascal ทำให้ Whisper และ OmniVoice พังกลางทางด้วย และแถว `gpu` บน Mac ที่เขียวเสมอเป็นแถวที่ไม่เกี่ยวกับเครื่อง ขัด D6.

**Rejected:**
- แถว `gpu` แถวเดียวทั้งสอง OS gate เฉพาะงาน Qwen (D4 เดิม) — ถอดเสียงและสร้างเสียงบนการ์ดเก่ายังพังกลางทาง

**Details:**
- changes D4: แถว `gpu` ไม่มีบน Mac และเงื่อนไขรุ่นการ์ดย้ายไปแถว `device`
- `device` ใช้ `torch.cuda.get_arch_list()` เทียบกับ capability ของการ์ด แทนตัวเลขตายตัว
- ทุกแถวอ่านการ์ด index 0 ตัวเดียวกับที่ worker โหลด (`cuda:0`)

**From:** red team · **Status:** active

## D9: VRAM หรือรุ่นต่ำกว่าเป้าของ Qwen เป็น `warning` ที่ยังกันงาน Qwen; Setup script ไม่โหลด Qwen บนเครื่องนั้น

**Chosen:** บน Windows แถว `gpu` เป็น `warning` เมื่อการ์ดต่ำกว่าเป้าของ Qwen (D10). gate ของงาน Qwen รับเฉพาะ `ok` จึงยังปฏิเสธ; Setup script ข้ามการโหลด `Qwen/Qwen3.5-9B` แล้วพิมพ์เหตุผล; แถว `model_qwen` และ `bitsandbytes` ของเครื่องนั้นเป็น `warning` ข้อความเดียวกัน. Setup script จบปกติ และถอดเสียงกับสร้างเสียงใช้ได้.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: เครื่องที่ใช้ได้ทุกอย่างยกเว้น Qwen ไม่ควรเห็น Setup script จบด้วย "ยังขาด" ทุกครั้ง และไม่ควรโหลด 19 GB ที่ใช้ไม่ได้; เกณฑ์ VRAM ยังเป็นค่าประมาณ.

**Rejected:**
- `missing` กันเต็มที่ (D4 เดิม) — Setup script จบด้วย "ยังขาด: GPU" ทุกครั้ง
- `warning` ที่ไม่กันงาน — งานอาจ out of memory กลางทาง

**Details:**
- changes D4: `missing` → `warning`
- เกณฑ์ VRAM 7.5 GiB ปรับได้หลัง trial (spec › Open Questions)

**From:** red team · **Status:** active

## D10: Qwen บน Windows ต้องใช้การ์ด RTX 30xx ขึ้นไป (sm_80) ใช้ bfloat16 ทางเดียว

**Chosen:** เป้าของ Qwen บน Windows เปลี่ยนจาก sm_75 เป็น compute capability ≥ 8.0 (RTX 30xx, 40xx, 50xx) ที่ VRAM ≥ 8 GB; worker คำนวณด้วย bfloat16 ทางเดียว. RTX 20xx ได้ `warning` ตาม D9 แต่ถอดเสียงและสร้างเสียงได้.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: RTX 20xx ไม่มี bfloat16 ในตัว; ทาง float16 สำรองเสี่ยงผลเป็น NaN และต้องมีเครื่อง 20xx อีกเครื่องมาลอง.

**Rejected:**
- คง RTX 20xx โดยใช้ float16 บนการ์ดนั้น — เสี่ยงผลเสีย และต้องลองเครื่องที่สอง

**Details:**
- changes D2: sm_75 → sm_80 สำหรับ Qwen; ขอบเขตของงาน GPU อื่นตาม D8

**From:** red team · **Status:** active

## D11: เขียนโค้ดและ test บน Mac ก่อน ลองบนเครื่อง Windows เมื่อได้เครื่อง

**Chosen:** ticket แรกเขียนโค้ดและ test ทั้งหมดบน Mac กับ worker ปลอม (ไม่เปลี่ยนพฤติกรรมบน Mac); ticket ลองบน Windows รอเครื่อง RTX 30xx ขึ้นไป ≥ 8 GB. ลองแล้วโมเดลไม่พอ 8 GB หรือใช้ไม่ได้ → change request.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: โค้ดส่วนใหญ่ทำได้โดยไม่ต้องมีการ์ด และไม่ต้องเสียเงินเช่า GPU.

**Rejected:**
- เช่า GPU บน cloud ลองก่อนเขียนโค้ด — มีค่าใช้จ่าย
- รอเครื่องจริงก่อนเริ่ม — งานบน Mac ทำได้เลย

**From:** red team · **Status:** active

## D12: ข้อแก้ red team ของ windows-launch

**Chosen:** รวมข้อแก้จาก red team ที่ไม่ต้องตัดสินใหม่.

**Details:**
- **ดิสก์:** `REQUIRED_FREE_BYTES["win32"]` 15 → 30 GB (โมเดลราว 24 GB รวม Qwen) — ไม่งั้นโหลดค้างกลางทางเพราะดิสก์เต็ม (spoil D11)
- **ข้ามการย่อ:** `llm_int8_skip_modules` เป็น `["visual", "lm_head"]` และ worker log ชื่อ module ที่ไม่ได้ย่อ — ค่าที่ส่งเองแทนค่า default ของ transformers ทั้งชุด ไม่ใช่เพิ่ม
- **timeout:** ค่าหลังลองไม่ต่ำกว่าค่าก่อนลอง (Mac × 5); ตารางอยู่ที่เดียวอ่านตอนเริ่มงาน และ test สลับตารางได้ — changes D7: การ์ดที่ช้ากว่าเครื่องลองยังไม่ถูกตัด
- **อ่านการ์ด:** probe `gpu` ใช้ `nvidia-smi` แทน `torch.cuda.get_device_properties` — CUDA context ใน backend process กิน VRAM ข้าง worker บนการ์ด 8 GB
- **probe พัง:** probe ของ `gpu` raise บน Windows → `warning` "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA" — ไม่บอกผิดว่าการ์ดเก่า
- **`bitsandbytes`:** แถวใช้ `check_package` แบบแถว `transformers`; `uv.lock` pin เวอร์ชันอยู่แล้ว
- **token ต่างกัน:** trial นับ token ของ `f7jkZXvaB4g` ไม่เท่ากันระหว่างสอง OS → Blocked และ change request
- **เวลาโหลด:** trial จดเวลาจากเริ่มงานถึง `Ready`; ยาวจนผู้ใช้คิดว่าค้าง → change request
- **seam:** รวม seam ตัวนับ token เข้า gate ของ API; เพิ่ม seam หน้าติดตั้งที่แสดงแถว `gpu` `warning`

**From:** red team · **Status:** active

## D13: แถว `device` ผ่านเมื่อ torch มี kernel ของ major เดียวกับการ์ด

**Chosen:** บน Windows แถว `device` เป็น `ok` เมื่อ `torch.cuda.get_arch_list()` มี `sm_` ที่ major เท่ากับ compute capability ของการ์ด ตามกฎที่ torch เองใช้ (`_check_cubins`) แทนการหา `sm_{major}{minor}` ตรงตัว.

**Why:** ผู้ใช้เลือกตัวเลือกที่แนะนำ: build cu128 ของ torch 2.8 ไม่มี `sm_89` แต่ RTX 40xx (เป้าของ D10) รัน kernel `sm_86` ได้; ถ้าเทียบตรงตัว RTX 40xx จะขึ้น "การ์ดเก่าเกิน".

**Rejected:**
- เทียบ `sm_{major}{minor}` ตรงตัวตาม spec เดิม — RTX 40xx ทุกใบขึ้นแถว Device สีแดง

**Details:**
- ยังตรง ADR-0026: "torch ที่ติดตั้งรันบนการ์ดนี้ได้"; GTX 10xx (sm_61) ยังเป็น `missing` เพราะ cu128 ไม่มี `sm_6x`
- arch list ของ cu128: `7.0;7.5;8.0;8.6;9.0;10.0;12.0` ([docs/library-notes/torch.md](../../library-notes/torch.md))

**Sources:** [torch/cuda/__init__.py v2.8.0](https://github.com/pytorch/pytorch/blob/v2.8.0/torch/cuda/__init__.py) · [build_cuda.sh v2.8.0](https://github.com/pytorch/pytorch/blob/v2.8.0/.ci/manywheel/build_cuda.sh)

**From:** build ticket 01 · **Status:** active

## D14: รายละเอียดแถว Qwen บน Windows ที่ build ticket 01 เลือก

**Chosen:** ค่าเล็กๆ ของแถว `device`, `gpu`, `model_qwen`, `bitsandbytes` ที่ spec ไม่ได้กำหนด เลือกตามโค้ดเดิม.

**Why:** อยู่ในขอบของ spec และไม่เปลี่ยนสิ่งที่ spec สัญญา.

**Details:**
- แถว `model_qwen` และ `bitsandbytes` ที่ `gpu` ไม่ `ok`: ค่าเป็น "ดูแถว GPU" และ `hint` เป็นข้อความของแถว `gpu`
- probe `gpu` พัง: แถว `device` ยังดูแค่ `cuda` (`ok`) — ไม่บอกว่าการ์ดเก่าเมื่ออ่านการ์ดไม่ได้ (D12); ค่าของแถว `gpu` เป็นข้อความ error
- VRAM ที่แสดงเป็น GiB ปัดเป็นจำนวนเต็ม: การ์ด 8 GB ที่รายงาน 7.6 GiB แสดง "8 GB"
- อ่านการ์ดครั้งเดียวต่อ Status check และต่อ gate (`checks.read_once`): `nvidia-smi` รันครั้งเดียว
- แถว `bitsandbytes` อ่านเวอร์ชันผ่าน probe `bitsandbytes` (metadata) แทน `check_package` ตรงๆ เพื่อให้ test ไม่ขึ้นกับเครื่อง (rules › testing); ผลเหมือน D12
- gate ของตัวนับ token บน Windows มีแถว `gpu` ก่อน `model_qwen`: การ์ดต่ำกว่าเป้าไม่มีไฟล์ Qwen (D9) จึงบอกแถว GPU
- Setup script พิมพ์ "ข้าม Qwen3.5 9B model: {hint ของแถว gpu}" ทั้งเมื่อการ์ดต่ำกว่าเป้าและเมื่อ `nvidia-smi` อ่านการ์ดไม่ได้; ที่ว่างบน Windows 30 GB เมื่อต้องโหลด Qwen, 15 GB เมื่อข้าม Qwen (โมเดลที่เหลือราว 5 GB)

**From:** build ticket 01 · **Status:** changed by D15 (ค่าของแถว `model_qwen` และ `bitsandbytes` เมื่อ `gpu` ไม่ `ok`, ค่าของแถว `gpu` เมื่อ probe พัง)

## D15: ค่าของแถว Windows ตามแบบ Figma

**Chosen:** ค่าของแถวบน Windows ตาม [Figma 8111-60588](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8111-60588):
- `model_qwen` และ `bitsandbytes` ที่ `gpu` ไม่ `ok`: ยังเป็น `warning` กับ `hint` ของแถว `gpu` แต่ค่าเป็นค่าของแถวเอง (revision, เวอร์ชัน, หรือ "ไม่พบ marker ใน models/.setup" เมื่อยังไม่โหลด) แทน "ดูแถว GPU"
- probe `gpu` พัง: ค่าของแถว `gpu` ว่าง แสดงแค่ `hint` "อ่านข้อมูลการ์ดไม่ได้ ตรวจ driver NVIDIA"; หน้าเว็บไม่แสดงบรรทัดค่าที่ว่าง
- `device` เป็น `missing` เพราะการ์ดเก่าเกิน: ค่าเป็น `{ชื่อการ์ด} · sm_{xy}` แทน `cuda`
- ค่าของแถว `warning` ทุกแถว (Mac ด้วย) เป็นตัว mono 13px สีเหลือง เหมือนค่าของแถว `ok`; แถว `missing` คงตัวปกติ 14px สีแดง

**Why:** ผู้ใช้เลือกตามแบบ (build ticket 01): เห็นค่าจริงของแต่ละแถว ไม่เห็น error ดิบ และแถว Device บอกการ์ดตรงๆ.

**Rejected:**
- คงข้อความเดิมของ D14 แก้แค่สีและฟอนต์ — ไม่ตรงแบบ

**From:** build ticket 01 · **Status:** active

## D16: รายละเอียด worker Windows และ timeout ที่ build ticket 02 เลือก

**Chosen:** ค่าเล็กๆ ที่ spec ไม่ได้กำหนด หรือที่ spec เขียนไม่ตรงกับ library ที่ติดตั้ง:
- `llm_int8_skip_modules` เป็น `["model.visual", "lm_head"]` แทน `["visual", "lm_head"]`: transformers 5.21.0 จับชื่อจากต้นชื่อเต็มหรือท้ายชื่อ `"visual"` จึงไม่จับ `model.visual.blocks.*` และ vision tower จะถูกย่อ ขัด D12 ([docs/library-notes/transformers.md](../../library-notes/transformers.md))
- โหลดด้วย `dtype=torch.bfloat16` ด้วย นอกจาก compute dtype: ส่วนที่ไม่ย่อก็เป็น bfloat16 ตาม D10
- log หลังโหลด: `[qwen] not quantized: model.visual (N), lm_head (1)` (นับ `Linear` ที่ไม่ย่อตามสองส่วนแรกของชื่อ) และ `[qwen] VRAM after load: {GiB} GiB` จาก `torch.cuda.max_memory_allocated`; ขึ้นใน terminal ของ `[api]`
- ตาราง `Timeouts` อยู่ใน `backend.spoil_maker.llm` (`TIMEOUTS`, `timeouts()`); Draft job อ่านตอนเริ่มงานแต่ละครั้ง; OS อื่นได้ของ Mac
- ขั้นเขียนบทและเรียบเรียงที่เกินเวลายังเป็น "ลองไม่สำเร็จหนึ่งครั้ง" ตาม spoil-maker เดิม ไม่ใช่ `model_failed`; บรรยายและเลือก Shot เป็น `model_failed` ที่บอกวินาทีจากตาราง — ticket เขียนว่า "ทั้งสี่ขั้นจบ `model_failed`" แต่ spec › ค่าต่อ OS เปลี่ยนแค่ค่า ไม่ได้เปลี่ยนพฤติกรรม
- worker Windows มี unit test กับ `torch` และ `transformers` ปลอมใน `sys.modules` (ticket ระบุพฤติกรรมไว้); โมเดลจริงเช็คมือใน ticket 03

**Why:** อยู่ในขอบของ spec และทำให้สิ่งที่ spec สัญญา (ไม่ย่อ `visual`, bfloat16 ทางเดียว, timeout ต่อ OS) เป็นจริงกับ library ที่ติดตั้ง.

**From:** build ticket 02 · **Status:** active

## Sources

- [PyTorch dev-discuss: Maxwell and Pascal support removed in CUDA 12.8 and 12.9 builds](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128) — D2 (accessed 2026-11-06)
- [torch 2.8.0 release notes](https://newreleases.io/project/pypi/torch/release/2.8.0) — D2 (accessed 2026-11-06)
- [uv #14742: GTX 1080 Ti on cu128 wheel](https://github.com/astral-sh/uv/issues/14742) — D2 (accessed 2026-11-06)
- [FreedomAISVR/Qwen3.5-9B-NVFP4-GGUF](https://huggingface.co/FreedomAISVR/Qwen3.5-9B-NVFP4-GGUF) — D2 VRAM estimate (accessed 2026-11-06)
- [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B/tree/main) — D3 license Apache-2.0, `image-text-to-text`, transformers (accessed 2026-11-06)
