# วิจัยโมเดลสร้างภาพสำหรับ การ์ตูนเล่า (`toon`)

ค้นเมื่อ 2026-11-08 จาก model card บน Hugging Face, docs ของ diffusers และ HF API (`/api/models`) เพื่อเช็คว่า repo gated ไหม, license อะไร, ขนาดไฟล์เท่าไร. ยังไม่ได้ลองรันจริงสักตัว: เวลาต่อภาพทุกตัวเลขที่ไม่มีแหล่งอ้างเป็น **ค่าประมาณ** (เขียนว่า "ประมาณ") ต้องลองจริงก่อนตัดสิน.

## ความต้องการที่ใช้กรอง

- ภาพแนวนอนราว 16:9 แสดงกว้างราว 1080 px ในเฟรม 9:16 → สร้างที่ 1024×576 หรือ 1280×720 ก็พอ (ไม่ต้อง 1 MP เต็ม; จำนวน token น้อยลง = เร็วขึ้น)
- สไตล์ 2D แบน หัวกลม ตาจุด โทนมืด สว่างเฉพาะแหล่งแสง
- **ตัวละครหน้าตา/ชุดเดิม** ข้ามหลายภาพและข้ามตอน
- รันได้ทั้ง Mac M2 16 GB (MPS, ใช้ GPU ทีละงานตาม ADR-0015) และ Windows RTX sm_75+ VRAM ≥ 8 GB, torch 2.8.0 + CUDA 12.8
- pin commit บน HF, setup script โหลดลง `models/` แบบไม่มีคนเฝ้า (ADR-0004) → **repo ที่ gated ต้องล็อกอิน HF และกดยอมรับเงื่อนไขก่อน = ใช้กับ setup script ไม่ได้**
- ใช้แบบไม่หารายได้ (ADR-0017) แต่ license ที่ใช้เชิงพาณิชย์ได้เป็นข้อดี; ADR-0025 อนุญาตให้ Mac กับ Windows ใช้ตัวรันหรือไฟล์ quantize ต่างกันได้ใต้แถวเดียว

## ข้อสังเกตเรื่องเครื่อง

- **Mac 16 GB**: GPU ใช้ unified memory ได้จริงราว 10–11 GB (ค่า default ของ Metal working set) ถ้าเกินจะ swap ช้ามาก. แปลว่า transformer bf16 ต้อง ≤ ~8 GB และ text encoder ต้องรันก่อนแล้วปล่อยหน่วยความจำ ไม่อยู่พร้อมกัน. MPS ไม่รองรับ `float8` และ `bitsandbytes` (nf4/int8) บน MPS ยังไม่น่าเชื่อถือ; ทางที่ใช้ได้คือ bf16 ตรงๆ, GGUF ผ่าน diffusers (dequantize ด้วย torch ops — ต้องลองว่าบน MPS ทำงาน), `optimum-quanto`/`torchao` int8, หรือ mlx (`mflux`) บน Mac คู่กับ diffusers บน Windows
- **RTX 20xx (Turing, sm_75) ไม่มี bf16 ในฮาร์ดแวร์**: โมเดลตระกูล FLUX/DiT ที่ฝึกด้วย bf16 เมื่อรัน fp16 มักได้ภาพดำหรือ NaN. ถ้าจะรองรับ sm_75 จริงต้องลองโหมด fp16 หรือใช้ GGUF/fp8 ที่ dequantize เป็น fp32 บางส่วน; RTX 30xx/40xx (sm_86/89) ใช้ bf16 ได้ปกติ. นี่เป็นความเสี่ยงที่ต้องลองบนเครื่องจริง
- **VRAM 8 GB**: transformer bf16 ขนาด ~7.8 GB ใส่ไม่ลงพร้อม activation → ต้องใช้ GGUF Q8/Q6, fp8 (Ampere+ ใน diffusers ผ่าน layerwise casting), หรือ group offload

## ผู้สมัครหลัก

### 1. FLUX.2 [klein] 4B — `black-forest-labs/FLUX.2-klein-4B`

- **ขนาด**: transformer 4B (rectified flow) + text encoder Qwen3 4B; bf16 transformer 7.8 GB, text encoder 8.0 GB, VAE 0.2 GB. repo ทั้งหมด 23.7 GB เพราะมีไฟล์ single-file ซ้ำที่ root 7.8 GB → ใช้ `allow_patterns` เอาแค่ `transformer/ text_encoder/ vae/ tokenizer/ scheduler/ *.json` ≈ 16 GB
- **License**: Apache 2.0, **ไม่ gated** (เช็คจาก HF API). ใช้เชิงพาณิชย์ได้. หมายเหตุ: ตัว 9B ใช้ FLUX Non-Commercial License และ gated — ไม่เอา
- **commit ณ วันค้น**: `e7b7dc27f91deacad38e78976d1f2b499d76a294`; ตัว base (undistilled สำหรับฝึก LoRA) `black-forest-labs/FLUX.2-klein-base-4B` `a3b4f4849157f664bdbc776fd7453c2783562f4d` (Apache, ไม่ gated)
- **diffusers**: `Flux2KleinPipeline` (text encoder `Qwen3ForCausalLM`), รับ `image=` เป็น list ของภาพอ้างอิงได้ = **multi-reference editing ในโมเดลเดียว** ทั้ง text-to-image และแก้ภาพ. ตัว distilled ใช้ 4 steps, `guidance_scale=1.0`. ต้องใช้ diffusers เวอร์ชันใหม่ (main ตอนออก, ตอนนี้น่าจะอยู่ใน release แล้ว — ต้องเช็คเวอร์ชันตอน pin). มี `Flux2KleinKVPipeline` ที่ cache K/V ของภาพอ้างอิง แต่ repo `-kv` มีเฉพาะ 9B (gated, NC)
- **quantize**: `black-forest-labs/FLUX.2-klein-4b-fp8` (4.07 GB, Apache, ไม่ gated — ใช้บน CUDA เท่านั้น), `black-forest-labs/FLUX.2-klein-4b-nvfp4` (Blackwell), `unsloth/FLUX.2-klein-4B-GGUF` (`a09d5bb51ac4000ccd9643d10e9db3ed14200508`, Q8_0 4.3 GB / Q6_K 3.4 GB / Q4_K_M 2.6 GB, Apache). บน Mac มี mlx 4-bit จากชุมชน (เช่น `ar9av/FLUX.2-klein-4B-mflux-4bit`) และ `mlx-community/FLUX.2-klein-4B-bf16`
- **หน่วยความจำ**: BFL บอก ~13 GB (รวม text encoder อยู่พร้อมกัน), README GitHub บอก ~8 GB. แยกรัน text encoder → ปล่อย → transformer bf16 จะใช้ราว 9–11 GB ตอน denoise ที่ 1024×576 (ประมาณ) — **พอดีขอบ Mac 16 GB**; ใช้ GGUF Q8 แทนจะเหลือ ~6 GB. ภาพอ้างอิงแต่ละภาพเพิ่ม token (≈ 1 MP ต่อภาพ = ~4k token) → ย่อภาพอ้างอิงเหลือ ~512–768 px จะประหยัดทั้งเวลาและหน่วยความจำ
- **เวลา**: M1 Max 1024² 4 steps 30–40 วินาที (mflux/iris.c, lilting.ch); M4 Max ~17 วินาทีรวมโหลด (Core AI conversion). M2 ธรรมดา GPU 8–10 core ช้ากว่า M1 Max ราว 2–3 เท่า → **ประมาณ 60–120 วินาทีต่อภาพ 1024×576 พร้อมภาพอ้างอิง 1–2 ภาพ**. RTX 3060 Ti 8 GB Q4_K_M 1024² 4 steps 15–30 วินาที (localaimaster); RTX 3060 12 GB bf16 **ประมาณ 6–12 วินาที**
- **ความเหมือนตัวละคร**: ใส่ภาพตัวละคร (character sheet) เป็น reference แล้วสั่งฉากใหม่ใน prompt. BFL โฆษณา consistency ของตระกูล FLUX.2 สูง แต่ยังไม่พบรีวิวอิสระที่ทดสอบ klein 4B กับการ์ตูนแบน → ต้องลองเอง. LoRA ตัวละคร/สไตล์ฝึกบน base 4B ได้ และใช้ร่วมกับ reference ได้
- **เหมาะกับสไตล์**: เป็นโมเดลทั่วไป ทำการ์ตูนแบนได้จาก prompt + ภาพอ้างอิงสไตล์; ฉากมืดที่มีแหล่งแสงน่าจะทำได้ดีเพราะเป็น flow model รุ่นใหม่ (ต้องลอง)

### 2. Qwen-Image-2.1-Turbo — `Qwen/Qwen-Image-2.1-Turbo`

- รุ่นใหม่สุดของ Qwen (repo สร้าง 2026-10-09; ตัวเต็ม `Qwen/Qwen-Image-2.1` 2026-09-14). โมเดลเดียวทำทั้ง text-to-image และแก้ภาพ, **รับภาพอ้างอิงได้ถึง 10 ภาพ**, การ์ดบอกว่ารักษาตัวตนคน/สินค้าได้ (ตัวอย่างรวม 6 คนเป็นภาพกลุ่ม), มีแก้เฉพาะจุดด้วยวงกลม/mask, สร้างภาพ RGBA โปร่งใสและตัดวัตถุออกจากภาพได้ — **ฟีเจอร์ RGBA มีประโยชน์มากกับการซ้อนตัวละครบนฉาก**
- **ขนาด**: visual DiT 7B (bf16 14.2 GB) + text encoder Qwen3-VL-8B (17.5 GB) + VAE 0.7 GB; repo 32.5 GB. commit `fc13ba1986fcb905854dc8de2f52eee395f49b5b`. 8 steps, CFG 1, `use_kv_cache=True` cache ภาพอ้างอิงข้าม step
- **diffusers**: `QwenImage21Pipeline` ต้องติดตั้ง diffusers จาก source (PR #14950) และ `transformers>=5.17` — **ชนกับ stack ปัจจุบันได้**, ต้องเช็คว่าเข้ากับ transformers ที่ Qwen3.5 LLM ของ project ใช้
- **License**: Qwen Research License — ไม่ gated แต่ **อนุญาตเฉพาะ "research or evaluation purposes only"**; เชิงพาณิชย์ต้องขอ license แยก. เข้มกว่า "ไม่หารายได้" ของ ADR-0017: การทำคลิปแล้วโพสต์ส่วนตัวไม่ใช่ research ชัดๆ → **ต้องให้ `/warroom legal` ดูก่อนใช้**
- **หน่วยความจำ**: bf16 ไม่มีทางลง 16 GB. ต้อง text encoder 4-bit (~5 GB) แล้วปล่อย, transformer int8/GGUF Q8 (~7.5 GB) — พอได้บนกระดาษ แต่มี quantized ในชุมชน 172 ตัวยังไม่ได้ตรวจว่าตัวไหนใช้กับ diffusers/MPS ได้. Windows 8 GB ต้อง Q4–Q5 + offload
- **เวลา**: ไม่มีแหล่งอ้าง. ประมาณ M2 2–5 นาทีต่อภาพ, RTX 3060 12 GB 15–40 วินาที (เดาจาก 7B × 8 steps)
- **สรุป**: คุณภาพและฟีเจอร์ consistency น่าจะดีที่สุดในกลุ่มที่พอลงเครื่องได้ แต่ติด license และหนักกว่า klein ราว 2 เท่า

### 3. Qwen-Image-Edit-2511 — `Qwen/Qwen-Image-Edit-2511`

- Apache 2.0, ไม่ gated, commit `6f3ccc0b56e431dc6a0c2b2039706d7d26f22cb9`. `QwenImageEditPlusPipeline` รับหลายภาพ (ตัวอย่าง 2 ภาพ), การ์ดบอกว่าปรับ character consistency ดีขึ้นชัดจาก 2509 และฝัง LoRA ยอดนิยม (เปลี่ยนมุมกล้อง, แสง) ไว้ในตัว
- **หนักมาก**: transformer 20B (bf16 40.9 GB) + Qwen2.5-VL-7B (16.6 GB); repo 57.7 GB. GGUF `unsloth/Qwen-Image-Edit-2511-GGUF` Q4 ≈ 12 GB; Lightning LoRA 4 steps `lightx2v/Qwen-Image-Edit-2511-Lightning` (Apache) — ชุมชนรายงานว่า Lightning + GGUF ต่ำทำสีเพี้ยนและทำตาม prompt แย่ลง
- **Mac 16 GB: ไม่สมเหตุผล** (Q3/Q4 transformer ~9–12 GB + VL encoder ที่ต้องอ่านภาพอ้างอิงด้วย). Windows 8 GB ได้แค่ด้วย Q4 + offload หนัก ประมาณหลายนาทีต่อภาพ
- เหมาะเป็นทางเลือกเฉพาะ Windows ที่ VRAM ≥ 16 GB เท่านั้น

### 4. Z-Image-Turbo / Z-Image — `Tongyi-MAI/Z-Image-Turbo`

- 6B single-stream DiT, Apache 2.0, ไม่ gated, commit `f332072aa78be7aecdf3ee76d5c247082da564a6`. `ZImagePipeline`, 8 NFE (`num_inference_steps=9`, `guidance_scale=0`). text encoder Qwen3 4B (8 GB). โฟลเดอร์ `transformer/` 24.6 GB เพราะมีหลายความแม่น → ต้อง `allow_patterns` เลือกเฉพาะ bf16 (~12 GB). มี `Tongyi-MAI/Z-Image` (base, 2026-01) สำหรับฝึก LoRA
- **ไม่มีโหมดแก้ภาพ/ภาพอ้างอิง**: Z-Image-Edit และ Omni-Base ยังเป็น "To be released" (HF org ยังมีแค่ 2 repo ภาพ) → consistency ได้ทาง LoRA อย่างเดียว
- bf16 transformer ~12 GB **เกินงบ Mac 16 GB**; mlx 4-bit บน M4 16 GB 1024² 9 steps ~240 วินาที (MLX_z-image) — ช้ากว่า klein ชัด
- ใช้ได้เป็นตัวสร้างฉากพื้นหลังหรือ character sheet แรก ถ้าคุณภาพสไตล์ดีกว่า klein, แต่ไม่คุ้มเพิ่มโมเดลที่สอง

### 5. SDXL + IP-Adapter / LoRA — `stabilityai/stable-diffusion-xl-base-1.0` + `h94/IP-Adapter`

- SDXL: UNet 2.6B, fp16 ~7 GB, OpenRAIL++-M, ไม่ gated. IP-Adapter: Apache, ไม่ gated, diffusers รองรับ (`load_ip_adapter`), รันบน MPS ได้มานาน
- **ข้อดี**: เล็ก เบา ecosystem สไตล์การ์ตูนแบนเยอะ, ฝึก LoRA บน Mac 16 GB เป็นไปได้ (diffusers `train_dreambooth_lora_sdxl` บน MPS ประมาณ 1–3 ชั่วโมงต่อตัวละคร, ประมาณ). M2 1024×576 25 steps ประมาณ 40–70 วินาที; ใส่ Lightning/LCM LoRA 4–8 steps ประมาณ 10–20 วินาที
- **ข้อเสีย**: ทำตาม prompt ฉากซับซ้อนแย่กว่ารุ่น DiT มาก, IP-Adapter ล็อก "บรรยากาศ" มากกว่าล็อกหน้า/ชุด (FaceID ใช้กับหน้าการ์ตูนตาจุดไม่ได้), checkpoint การ์ตูนแบนส่วนใหญ่อยู่ Civitai ไม่ใช่ HF (pin commit ไม่ได้, license ต่างกันไป). เป็นแผนสำรองถ้า klein ช้าเกินบน M2

### ตัวที่ตัดออก (และเหตุผล)

| repo | เหตุผล |
|---|---|
| `black-forest-labs/FLUX.1-Kontext-dev` (12B) | **gated** + FLUX.1 Non-Commercial License; หนักกว่า klein 4B และ klein ทำงานเดียวกันได้ |
| `black-forest-labs/flux-3-image-klein` (5.6B + Qwen3-VL-4B, 2026-10) | **gated** + FLUX Kommunity License (เชิงพาณิชย์เฉพาะรายได้ < US$5M); peak 25–31 GB บน B200 ที่ 1024²; แนะนำให้ใช้ prompt upsampler 9B (`flux-3-image-klein-pup`, Apache, 18.8 GB) คู่กันเสมอ → ไม่ลง 16 GB. น่าติดตามถ้ามีรุ่นเล็กหรือเปิดไม่ gated |
| `black-forest-labs/FLUX.2-klein-9B` / `-9b-kv` | gated + Non-Commercial; ~20–29 GB |
| `stabilityai/stable-diffusion-3.5-medium` | **gated** + Community License (ฟรีถ้ารายได้ < US$1M); ไม่มี reference editing |
| `meituan-longcat/LongCat-Image-Edit-Turbo` | Apache, 8 steps แต่รับภาพเดียว, ต้อง ~18 GB แม้ offload, text encoder Qwen2.5-VL-7B 16.6 GB |
| `OmniGen2/OmniGen2` | Apache, รับหลายภาพ แต่ ~31 GB repo, consistency ด้อยกว่ารุ่นใหม่, ใช้โค้ดของ repo เอง |
| `stepfun-ai/Step1X-Edit-v1p2` | Apache แต่หนัก (DiT ~12B + Qwen2.5-VL-7B), รับภาพเดียว |
| `HiDream-ai/HiDream-I1` / `E1-1` | MIT แต่ใช้ Llama-3.1-8B เป็น text encoder (repo Meta gated) และหนัก ~17B |
| `lodestones/Chroma1-HD`, `Alpha-VLLM/Lumina-Image-2.0`, Sana 1.5 | Apache ไม่ gated แต่เป็น text-to-image ล้วน ไม่มีกลไกภาพอ้างอิง; Sana เล็กเร็ว (1.6B) แต่คุณภาพการ์ตูน/องค์ประกอบด้อย |

## วิธีทำให้ตัวละครเหมือนเดิม

1. **Reference-image (แนะนำเป็นหลัก)**: ต่อซีรีส์เก็บ "character sheet" ต่อตัวละคร (ภาพเต็มตัวด้านหน้า + ด้านข้างบนพื้นเรียบ) สร้างครั้งเดียวแล้วให้ผู้ใช้เลือก/ล็อก — แนวเดียวกับ "เสียงล็อก" ของ TTS. ทุกฉากส่ง sheet ของตัวละครที่อยู่ในฉากเป็น `image=[...]` ของ klein. ข้อดี: ไม่ต้องฝึก, ข้ามตอนได้ทันที, เหมือนกันทั้งสอง OS. ข้อเสีย: ตัวละครหลายตัวในภาพเดียว = ภาพอ้างอิงหลายภาพ = ช้าขึ้นและอาจสลับลักษณะกัน
2. **LoRA ต่อตัวละคร**: ฝึกบน `FLUX.2-klein-base-4B` ด้วยภาพ 10–20 ภาพจาก sheet. มีรายงานฝึกบน RTX 4090 ~60 นาทีและต้อง ≤ 24 GB; **บน M2 16 GB ยังไม่พบใครทำสำเร็จ** (มีโปรเจกต์ Swift/MLX ที่อ้างว่าฝึกได้บน Apple Silicon แต่ไม่มีตัวเลข) → ถือว่าไม่ใช้ในรอบแรก. ถ้าใช้ SDXL ฝึกบน Mac ได้จริงแต่ช้า. LoRA เป็นไฟล์เดียวใช้ข้าม OS ได้
3. **ฉากซ้ำ**: สร้าง "ภาพฉาก" ต่อสถานที่ครั้งเดียว แล้วส่งเป็นภาพอ้างอิงคู่กับ sheet ตัวละคร ("วางตัวละครในฉากนี้") — ฉากกับแสงจะสอดคล้องกันเพราะโมเดลวาดรวม. ทางเลือก: สร้างตัวละครบนพื้นเรียบ → ตัดพื้นหลัง (Qwen-Image-2.1 ทำ RGBA ได้เอง; ถ้าใช้ klein ต้องเพิ่มโมเดลตัดพื้น เช่น BiRefNet) → ซ้อนบนฉากด้วย Pillow. วิธีซ้อนเร็วและคุมได้ แต่แสงจากกองไฟ/ไฟหน้ารถจะไม่ตกบนตัวละคร ซึ่งขัดกับสไตล์ "มืด สว่างเฉพาะแหล่งแสง" → ใช้ซ้อนเฉพาะช็อตที่แสงไม่สำคัญ
4. **Inpainting**: แก้เฉพาะจุดของภาพเดิม (เช่นเปลี่ยนท่าตัวละครแต่ฉากเหมือนเดิมทุกพิกเซล) — klein ทำแบบ instruction edit ได้, Qwen-Image-2.1 มี mask/วงกลม. ใช้กับประโยคต่อเนื่องในฉากเดียว: ภาพก่อนหน้าเป็น `image=` แล้วสั่งเปลี่ยนแค่ท่าทาง

## ข้อเสนอ

**ชุด A (แนะนำ): FLUX.2 klein 4B ทั้งสอง OS + character sheet + ฉากเป็นภาพอ้างอิง**
- Apache, ไม่ gated, pin ได้, โมเดลเดียวทำทั้งสร้าง sheet, สร้างฉาก, ใส่ตัวละครเข้าฉาก, แก้ภาพต่อเนื่อง
- Mac: diffusers bf16 (แยก text encoder ออกก่อน) หรือ GGUF Q8 ถ้าหน่วยความจำไม่พอ; ทางสำรองคือ mflux 4/8-bit (ADR-0025 อนุญาต). Windows: bf16 บนการ์ด ≥ 12 GB, GGUF Q8 หรือ fp8 บน 8 GB
- เสีย: M2 ประมาณ 1–2 นาทีต่อภาพ → คลิป 30 ประโยคประมาณ 30–60 นาที; คุณภาพ consistency การ์ตูนยังไม่มีใครยืนยัน

**ชุด B (คุณภาพสูงสุดที่น่าจะลงเครื่องได้): Qwen-Image-2.1-Turbo + quantize**
- 10 ภาพอ้างอิง, รักษาตัวตน, RGBA, mask edit ในโมเดลเดียว
- เสีย: **Qwen Research License (research/evaluation only)** — ต้องผ่าน legal ก่อน; text encoder 8B + DiT 7B ต้อง quantize หนักบน Mac; ต้องใช้ diffusers จาก source และ transformers ≥ 5.17; ช้ากว่า klein ราว 2–4 เท่า (ประมาณ)

**ชุด C (เบาและแน่นอนที่สุด): SDXL + LoRA ตัวละคร + IP-Adapter สไตล์**
- เล็ก เร็ว (มี Lightning LoRA), รันบน MPS ได้แน่, ฝึก LoRA บน Mac ได้
- เสีย: ทำตาม prompt ฉากแย่, ต้องฝึก LoRA ต่อตัวละคร (ชั่วโมงต่อตัว), checkpoint สไตล์ดีๆ อยู่นอก HF

## ต้องลองจริงก่อนตัดสิน

1. klein 4B bf16 บน M2 16 GB ใน diffusers: peak memory และเวลาต่อภาพที่ 1024×576 กับภาพอ้างอิง 0, 1, 2, 3 ภาพ (ย่อเหลือ 512/768 px); ต้องตั้ง `PYTORCH_MPS_HIGH_WATERMARK_RATIO` ไหม
2. GGUF ของ klein (Q8/Q6) ผ่าน diffusers `GGUFQuantizationConfig` รันบน MPS ได้ไหม และช้าลงเท่าไร; หรือต้องไป mflux
3. คุณภาพ consistency: sheet ตัวละครหัวกลมตาจุด → 10 ฉากต่างกัน ดูว่าชุด/สี/สัดส่วนหัวเพี้ยนไหม, 2 ตัวละครในภาพเดียวสลับลักษณะกันไหม
4. สไตล์โทนมืดสว่างเฉพาะแหล่งแสง: klein ทำได้จาก prompt หรือต้องใส่ภาพอ้างอิงสไตล์ทุกครั้ง
5. Windows: klein bf16 บน RTX 3060 12 GB, GGUF Q8/fp8 บนการ์ด 8 GB, และ **Turing (RTX 20xx) โหมด fp16 ได้ภาพดำ/NaN ไหม** — ถ้าได้ อาจต้องเลื่อนขั้นต่ำเป็น sm_86 สำหรับ feature นี้
6. เวอร์ชัน diffusers ที่มี `Flux2KleinPipeline` (และ `QwenImage21Pipeline` ถ้าลองชุด B) เข้ากับ transformers ที่ project ใช้อยู่ไหม
7. license ของ Qwen-Image-2.1 กับการโพสต์คลิปส่วนตัว (ถ้าจะลองชุด B)
8. ฝึก LoRA บน klein-base-4B บน Mac 16 GB เป็นไปได้ไหม (ถ้า reference อย่างเดียวไม่พอ)

## แหล่งอ้างอิง

- FLUX.2 klein 4B model card: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- BFL blog FLUX.2 [klein]: https://bfl.ai/blog/flux2-klein-towards-interactive-visual-intelligence
- diffusers Flux2 / Flux2KleinPipeline docs: https://huggingface.co/docs/diffusers/main/en/api/pipelines/flux2
- FLUX.2 klein GGUF: https://huggingface.co/unsloth/FLUX.2-klein-4B-GGUF
- FLUX.2 klein fp8: https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8
- klein 4B บน M1 Max (mflux, iris.c): https://lilting.ch/en/articles/flux2-klein-4b-mflux-iris-m1-max
- klein 4B Core AI บน M4 Max: https://huggingface.co/mlboydaisuke/FLUX.2-klein-4B-CoreAI
- klein 4B mflux 4-bit: https://huggingface.co/ar9av/FLUX.2-klein-4B-mflux-4bit
- klein บน GPU VRAM ต่ำ (3060 Ti 8 GB): https://localaimaster.com/blog/run-flux-on-low-vram-gpu
- ฝึก LoRA klein บน RTX 4090: https://discuss.pytorch.kr/t/flux-2-klein-lora-rtx-4090-60/10566
- MLX LoRA training บน Apple Silicon: https://github.com/VincentGourbin/flux-2-swift-mlx
- Qwen-Image-2.1: https://huggingface.co/Qwen/Qwen-Image-2.1 · License: https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE
- Qwen-Image-2.1-Turbo: https://huggingface.co/Qwen/Qwen-Image-2.1-Turbo
- Qwen-Image-Edit-2511: https://huggingface.co/Qwen/Qwen-Image-Edit-2511
- Qwen-Image-Edit-2511 ใน ComfyUI (Lightning LoRA): https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511
- Qwen-Image-Edit-2511 GGUF: https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF
- Z-Image-Turbo: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- Z-Image MLX บน Apple Silicon: https://awesome.ecosyste.ms/projects/github.com%2Fuqer1244%2FMLX_z-image
- FLUX 3 Image Klein: https://huggingface.co/black-forest-labs/flux-3-image-klein · PUP: https://huggingface.co/black-forest-labs/flux-3-image-klein-pup
- LongCat-Image-Edit-Turbo: https://huggingface.co/meituan-longcat/LongCat-Image-Edit-Turbo
- consistency ตระกูล FLUX.2 (เปรียบเทียบอิสระ): https://techstackups.com/comparisons/comparing-image-generators-character-consistency/
- สถานะ gated / license / ขนาดไฟล์ / commit: HF API `https://huggingface.co/api/models/{repo}?blobs=true` ณ 2026-11-08
