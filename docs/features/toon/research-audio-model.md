# วิจัยโมเดลสร้างเสียงบรรยากาศ/ดนตรีพื้นหลัง สำหรับ การ์ตูนเล่า (`toon`)

ค้นเมื่อ 2026-11-08 จาก model card บน Hugging Face, HF API (`/api/models/{id}?blobs=true` เพื่อเช็ค `gated`, license, ขนาดไฟล์ และ `lfs.sha256`), GitHub ของแต่ละโมเดล และ paper Stable Audio 3. ยังไม่ได้ลองรันจริงสักตัว: ตัวเลขเวลาที่ไม่มีแหล่งอ้างเป็น **ค่าประมาณ** (เขียนว่า "ประมาณ") ต้องลองบนเครื่องจริงก่อนตัดสิน.

## ความต้องการที่ใช้กรอง

- เสียง AMBIENCE / SFX แบบวนซ้ำได้ (เช่น "night forest crickets wind", "rain on tin roof", "low eerie drone") และ music bed ง่ายๆ ยาว ~10–47 วินาที วางใต้เสียงบรรยายของคลิป 60–120 วินาที
- รันได้ทั้ง Mac Apple Silicon 16 GB (MPS, ใช้ GPU ทีละงานตาม ADR-0015, GPU job อยู่ใน child process ตาม ADR-0012) และ Windows RTX sm_75+ VRAM ≥ 8 GB, torch 2.8.0 + CUDA 12.8
- pin commit บน HF, setup script โหลดลง `models/` แบบไม่มีคนเฝ้า (ADR-0004) → **repo ที่ gated (ต้องล็อกอิน HF/กดยอมรับ) ใช้ตรงๆ ไม่ได้** ต้องหา mirror ที่ไม่ gated และ license เดียวกัน
- ใช้แบบไม่หารายได้ (ADR-0007/0017) → license NC รับได้ แต่ต้องจดไว้
- stack ปัจจุบันของ project: `torch==2.8.0`, `transformers` 5.21.0, `numpy` 2.5.4, ยังไม่มี `diffusers`; Mac มี `mlx` อยู่แล้ว (ผ่าน `mlx-vlm`). ADR-0025 อนุญาตให้ Mac กับ Windows ใช้ตัวรันต่างกันใต้แถวโมเดลเดียว

## สรุปเร็ว

| โมเดล | repo (ทางการ) | gated | mirror ไม่ gated | license | ขนาดที่ต้องโหลด | ยาวสุด/ครั้ง | sample rate | ตัวรัน |
|---|---|---|---|---|---|---|---|---|
| **Stable Audio 3 small-sfx** | `stabilityai/stable-audio-3-small-sfx` | auto (ต้องล็อกอิน) | `cocktailpeanut/stable-audio-3-small-sfx` (ไฟล์ตรงกัน byte ต่อ byte) | Stability AI Community + Gemma ToU | 3.5 GB | 120 วิ | 44.1 kHz stereo | `stable-audio-3` (repo แยก) |
| **Stable Audio 3 small-music** | `stabilityai/stable-audio-3-small-music` | auto | `cocktailpeanut/stable-audio-3-small-music` (ตรงกัน) | เหมือนบน | 3.5 GB | 120 วิ | 44.1 kHz stereo | `stable-audio-3` |
| Stable Audio 3 medium | `stabilityai/stable-audio-3-medium` | auto | `cocktailpeanut/stable-audio-3-medium` | เหมือนบน | 10.4 GB | 380 วิ | 44.1 kHz stereo | `stable-audio-3`, ต้องการ CUDA |
| Stable Audio Open 1.0 | `stabilityai/stable-audio-open-1.0` | auto | `AEmotionStudio/stable-audio-open-models`, `ModelsLab/stable-audio-open-1.0` (ตรงกัน) | Stability AI Community | ~5.3 GB (เฉพาะ diffusers folders) | 47 วิ | 44.1 kHz stereo | `diffusers` `StableAudioPipeline` |
| Stable Audio Open Small | `stabilityai/stable-audio-open-small` | auto | `FastVideo/stable-audio-open-small-Diffusers` (แปลงใหม่ ไม่ตรง byte) | Stability AI Community | ~1.7–2 GB | 11 วิ | 44.1 kHz stereo | `stable-audio-tools` |
| MOSS-SoundEffect v2.0 | `OpenMOSS-Team/MOSS-SoundEffect-v2.0` | ไม่ | — | **Apache 2.0** | 11.2 GB | 30 วิ | 48 kHz | package แยก (diffusers-style) |
| TangoFlux | `declare-lab/TangoFlux` | ไม่ | — | SAI Community + WavCaps **academic only** | 4.1 GB | 30 วิ | 44.1 kHz stereo | `tangoflux` (repo แยก) |
| AudioLDM 2 | `cvssp/audioldm2` | ไม่ | — | CC BY-NC-SA 4.0 | ~4.5 GB (safetensors) | ~10 วิ (ตั้งยาวได้) | 16 kHz mono | `diffusers` `AudioLDM2Pipeline` |
| Tango 2 | `declare-lab/tango2` | ไม่ | — | CC BY-NC-SA 4.0 | 5.3 GB | 10 วิ | 16 kHz mono | repo แยก |
| AudioGen medium | `facebook/audiogen-medium` | ไม่ | — | CC BY-NC 4.0 | 3.9 GB | 10 วิ (ต่อยาวได้) | 16 kHz mono | `audiocraft` |
| MusicGen small/medium | `facebook/musicgen-small` / `-medium` | ไม่ | — | CC BY-NC 4.0 | 2.4 / 8 GB | 30 วิ | 32 kHz mono | `transformers` |
| MAGNeT | `facebook/magnet-small-10secs` ฯลฯ, `facebook/audio-magnet-medium` | ไม่ | — | CC BY-NC 4.0 | 1.1–3.9 GB | 10 / 30 วิ | 32 / 16 kHz | `audiocraft` |
| MMAudio (text mode) | `hkchengrex/MMAudio` | ไม่ | — | CC BY-NC 4.0 | ~5–6 GB (เลือกไฟล์) | 8 วิ (ฝึก) | 44.1 kHz | repo แยก |
| AudioX / AudioX-Turbo | `HKUSTAudio/AudioX`, `-Turbo` | ไม่ | — | CC BY-NC 4.0 | 6 / 23 GB | ~10 วิ | 44.1 kHz | `stable-audio-tools` fork |
| Woosh (Sony AI) | `drbaph/Woosh` (mirror ชุมชน) | ไม่ | — | CC BY-NC 4.0 | ~3–4 GB ต่อชุด | สั้น | band-limited ตาม paper SA3 | repo แยก / ComfyUI |

## ผู้สมัครหลัก

### 1. Stable Audio 3 small-sfx / small-music (Stability AI, ออก 2026-05-17)

- **โครงสร้าง**: latent diffusion transformer ~433M (GitHub) / 459M (บางรีวิว) + autoencoder SAME-S + text encoder T5Gemma-b-b-ul2. post-train แบบ adversarial → **8 steps, ไม่ใช้ CFG** (sampler `pingpong`). small แยกเป็นสองตัวเพราะ paper พบว่าเอา SFX มาฝึกรวมทำให้ดนตรีของ small แย่ลง
- **ยาวสุด 120 วินาที**, variable length (สั่ง `duration` ตรงๆ ได้ ไม่ต้องสร้างเต็มแล้วตัด), 44.1 kHz stereo (`model_config.json`: `sample_rate` 44100, `sample_size` 5292032 = 120 วิ, `audio_channels` 2). รองรับ **inpainting / continuation** (`inpaint_mask_start_seconds`/`_end_seconds`) และ audio-to-audio (`init_audio`)
- **คุณภาพ (paper, BBC Sound Effects, 5 วิ)**: small-sfx FAD 0.395 / CLAP 0.351 / OVL 3.35 ดีกว่า SAO 1.0 (0.501 / 0.263 / 2.95), SAO-small (0.500 / 0.277), TangoFlux (0.760 / 0.179) และ Woosh. medium ดีที่สุด (0.369 / 0.369 / 3.65). paper ไม่ใช้ AudioCaps เพราะเสียงอ้างอิง band-limited
- **รีวิว (Dubspot)**: small-sfx เด่นเรื่อง foley และ ambient texture, small-music เหมาะกับ loop, bed, ambient drone, atmospheric bed; จุดอ่อนคือดนตรี "ถูกแต่ไม่น่าสนใจ" และ seed ต่างกันได้ทำนองคล้ายกัน — สำหรับ bed ใต้เสียงบรรยายถือว่าไม่เสียหาย. ไม่มีเสียงร้อง
- **หน่วยความจำ (GitHub, H200)**: small peak 1.69 GB (5 วิ), 1.89 GB (30 วิ), 2.40 GB (120 วิ) → **เหลือเฟือทั้ง Mac 16 GB และ RTX 8 GB**
- **ความเร็ว (GitHub)**: small สร้าง 30 วิ ใช้ 1.72 วิ บน **Mac CPU**, 0.63 วิ ด้วย CoreML; 120 วิ ใช้ 5.92 วิ (CPU) — ตัวเลข Mac น่าจะเป็น MacBook Pro M4 ตาม card. **ประมาณ** M2 ธรรมดา 3–10 วินาทีต่อคลิป 30–47 วิ (CPU หรือ MPS fp32), RTX 3060 ประมาณ < 2 วินาที
- **MPS**: `StableAudioModel.from_pretrained` เลือก `cuda` → `mps` → `cpu` เองอัตโนมัติ และบังคับ `model_half=False` ถ้าไม่มี CUDA (= fp32 บน MPS, 433M fp32 ≈ 1.8 GB ไม่มีปัญหา). README พูดถึง Apple แค่ CoreML/MLX ไม่ได้รับรอง MPS ตรงๆ → **ต้องลองว่า MPS ผ่าน**; ถ้าไม่ผ่าน CPU ก็เร็วพออยู่แล้ว. `flash_attn` เป็น optional (fallback เป็น SDPA) จำเป็นแค่ medium
- **ทางเลือกตัวรันบน Mac (ADR-0025)**: repo ทางการ `stabilityai/stable-audio-3-optimized` **ไม่ gated** (commit `30cb2644da54bfa63275d1bc7f1fa67fc718680f`) มี `MLX/dit_sm-sfx_f16.npz` (0.92 GB), `MLX/same_s_*`, `MLX/t5gemma_f16.npz` และ ONNX/TFLite/TensorRT ของ small-sfx (แต่ **ไม่มี small-music** ในโฟลเดอร์ ONNX/TFLite; MLX มีทั้งคู่). ชุมชนมี `mlx-community/stable-audio-3-small-sfx` (`mlx-audio`) และ GGUF ของ `thepatch`
- **การติดตั้ง**: library `stable-audio-3` (GitHub `Stability-AI/stable-audio-3`, code MIT, ใช้ uv) **pin `torch==2.7.1`/`torchaudio==2.7.1`** แต่ `transformers>=5.8.0` (เข้ากับ 5.21 ของเรา). ทางแก้: เพิ่มเป็น git dependency pin commit แล้วใช้ `[tool.uv] override-dependencies` บังคับ torch 2.8.0 หรือ vendor เฉพาะโค้ด inference (`stable_audio_3/models`, `inference`, `loading_utils.py`). ต้องลองว่ารันบน torch 2.8 ได้จริง
- **ปัญหา gated และ mirror**:
  - ทางการ `stabilityai/stable-audio-3-small-sfx` = `gated: auto` (ต้องล็อกอิน HF และยอมรับ license + privacy + Gemma terms); T5Gemma ต้นฉบับ `google/t5gemma-b-b-ul2` = `gated: manual` ยิ่งแย่
  - `cocktailpeanut/stable-audio-3-small-sfx` ไม่ gated, commit `84c4bc8e3281c5bc6d6f09525fec1c5c5fd411ab`: `model.safetensors` sha256 `ed9cf1b6…f515` และ `t5gemma-b-b-ul2/model.safetensors` `9b05ea5a…00d3` **ตรงกับของทางการทุก byte**, มี `LICENSE.md`, `LICENSE_GEMMA.md`, `NOTICE` ครบ. ต่างแค่ `model_config.json` ที่แก้ `repo_id` ของ T5Gemma ให้ชี้ mirror เอง → ในโค้ดเราควรโหลดผ่าน `load_diffusion_cond(config, ckpt)` แล้วแก้ path T5Gemma เป็นโฟลเดอร์ใน `models/` เพื่อไม่ให้ไปเรียก HF ตอนรัน
  - small-music: `cocktailpeanut/stable-audio-3-small-music` commit `d237d3dfb35015f1c770213724223f3c89f4dd78`, sha256 ตรงกับทางการ (`da85866b…4b64`)
  - `Comfy-Org/stable-audio-3` (ไม่ gated, org ของ ComfyUI) มี DiT ไฟล์ตรงกับทางการ แต่ T5Gemma แพ็กใหม่และไม่มี `model_config.json` — ใช้เป็นแหล่งสำรองของ DiT ได้
  - ความเสี่ยง: mirror ส่วนตัวอาจถูกลบ; การ pin commit กันไฟล์เปลี่ยนได้แต่ไม่กันหาย. ตรวจ `sha256` หลังโหลดเทียบค่าทางการที่จดไว้ในตารางโมเดล
- **License (Stability AI Community License)**: ใช้ฟรีสำหรับ non-commercial รวม "personal use (i.e., hobbyist)"; เชิงพาณิชย์ฟรีถ้ารายได้ < USD 1M/ปี แต่ต้องลงทะเบียน. ข้อที่เกี่ยวข้อง:
  - ห้ามใช้ model หรือ output ไป "create or improve any foundational generative AI model" — เราไม่ทำ
  - ถ้า **แจกจ่าย** model/derivative/ผลิตภัณฑ์ที่ใช้ model ต้องแนบ license, NOTICE และแสดง "Powered by Stability AI" — framecraft ไม่ได้แจกไฟล์ model (setup script โหลดเอง) แต่ถ้าแจก framecraft เองอาจนับเป็น "product that uses them" → ควรใส่ข้อความนี้ใน `NOTICE.md` ไว้ก่อน (ไม่บังคับใส่ในคลิป เพราะ license ไม่ได้พูดถึง output; สอดคล้อง ADR-0017 ที่ไม่บังคับเครดิตในคลิป แต่ควรให้ `/warroom legal` ยืนยัน)
  - output เป็นของผู้ใช้ "to the extent permitted by applicable law"; ต้องทำตาม Acceptable Use Policy
  - T5Gemma อยู่ใต้ Gemma Terms of Use: ห้ามใช้ตาม Prohibited Use Policy, Google ไม่อ้างสิทธิ์ใน output, ถ้าแจกจ่ายต้องแนบ terms/NOTICE
- **ข้อมูลฝึก**: AudioSparx (licensed) 806k + Freesound CC0/CC-BY/CC-Sampling+ 472k — สะอาดกว่าโมเดลที่ฝึกด้วย AudioSet/WavCaps

### 2. Stable Audio Open 1.0 (`stabilityai/stable-audio-open-1.0`)

- DiT ~1.1B + T5-base + VAE, 44.1 kHz stereo, **ยาวสุด 47 วิ**. `diffusers` `StableAudioPipeline` รองรับเป็นทางการ (ต้องเพิ่ม `diffusers` เข้า stack) หรือ `stable-audio-tools`
- gated auto (commit ทางการ `f21265c1e2710b3bd2386596943f0007f55f802e`). mirror ไม่ gated ที่ไฟล์ตรงกัน: `AEmotionStudio/stable-audio-open-models` (`385bdecabe7f8a613a4e1d568362f0e00d1f692b`) และ `ModelsLab/stable-audio-open-1.0` (`836348c7020297467318078dd37a04ecd709fe75`) — `transformer/` sha256 `65ae9715…06fd` ตรงทางการ. `FastVideo/stable-audio-open-1.0-Diffusers` แปลงใหม่ hash ไม่ตรง. ใช้ `allow_patterns` เอาแค่ `transformer/ vae/ text_encoder/ tokenizer/ projection_model/ scheduler/ *.json` ≈ 5.3 GB
- หน่วยความจำ ประมาณ 5–7 GB fp16 ที่ 47 วิ (พอ 8 GB; Mac fp32 ประมาณ 8–10 GB — ขอบ). ช้า: ใช้ 100–200 steps + CFG; paper SA3 วัด 12.3 วิ บน H200 สำหรับ 5 วิ (ช้ากว่า small-sfx ~30 เท่า) → **ประมาณ M2 2–6 นาทีต่อคลิป 47 วิ**, RTX 3060 30–60 วิ
- MPS: ไม่พบ issue ที่ยืนยันว่าเสีย แต่ตัวอย่างทางการใช้ CUDA fp16 อย่างเดียว → ต้องลอง (fp16 บน MPS อาจมีปัญหา; fp32 ปลอดภัยกว่า)
- คุณภาพด้อยกว่า SA3 small-sfx ทุก metric ใน paper; ข้อดีเดียวคือ diffusers ทางการ. **ถูกแทนที่ด้วย SA3 แล้ว**

### 3. MOSS-SoundEffect v2.0 (`OpenMOSS-Team/MOSS-SoundEffect-v2.0`)

- ตัวเดียวในกลุ่มที่ **Apache 2.0 และไม่ gated** (commit `e35df4d82fbe87fcd5d14e5d100e349c0c3c076d`). DiT 1.3B flow matching + DAC VAE 48 kHz + text encoder Qwen3-1.7B, ยาวสุด **30 วิ**, prompt อังกฤษ/จีน, เน้นธรรมชาติ เมือง สัตว์ การกระทำ (ตรงกับ ambience)
- ขนาด 11.2 GB; bf16 ประมาณ 6–8 GB ตอนรัน (ประมาณ; card ไม่บอก)
- **ข้อเสีย**: 100 steps + CFG 4 (ช้า, ประมาณ M2 1–3 นาทีต่อ 30 วิ), ห่อ DiT ด้วย `torch.compile` + Triton CUDA Graph (Triton ไม่มีบน Mac/Windows ต้องปิด `TORCHDYNAMO_DISABLE=1`), package pin `transformers==4.57.1`, `numpy==1.26.4`, `diffusers==0.37.1`, `descript-audiotools` → **ชนกับ stack เรา (transformers 5.21, numpy 2.5)**; ไม่มีคำพูดเรื่อง MPS. ยังไม่มี benchmark อิสระเทียบกับ SA3
- เหมาะเป็นแผนสำรองถ้าต้องการ license ที่ใช้เชิงพาณิชย์ได้ แต่ต้อง vendor โค้ดและลองว่ารันบน transformers 5 ได้

## ผู้สมัครอื่น (ตัดออกหรือเป็นสำรองท้ายๆ)

- **Stable Audio Open Small** (`stabilityai/stable-audio-open-small`, gated auto, 341M, 44.1 kHz stereo, 8 steps): **ยาวสุด 11 วิ** สั้นไปสำหรับ bed; ไม่มีใน diffusers ทางการ (มี `FastVideo/...-Diffusers` แปลงเอง). ถูกแทนด้วย SA3 small ซึ่งคุณภาพดีกว่าและยาวได้ 120 วิ
- **Stable Audio 3 medium**: คุณภาพดีสุด แต่ GitHub ระบุว่าออกแบบสำหรับ CUDA, ต้องการ Flash Attention 2, peak VRAM 5–6.5 GB; บน Mac ต้องใช้ MLX (`stable-audio-3-optimized/MLX/dit_medium_f16.npz`). เป็นตัวอัปเกรดบน Windows ได้ภายหลังถ้า small ไม่พอ
- **TangoFlux** (`declare-lab/TangoFlux`, ไม่ gated, commit `367005e963cb3a9fb2e03a46104d7de23e34ceea`, 515M, 44.1 kHz stereo, 30 วิ, ~25–50 steps): license ซ้อนสามชั้น — Stability AI Community + **WavCaps "only academic uses"** + "non-commercial, research-only… UK data copyright exemption" → **แคบกว่า personal use**, ต้อง `/warroom legal` ถ้าจะใช้. คุณภาพใน paper SA3 ต่ำสุดในตาราง
- **AudioLDM 2** (`cvssp/audioldm2`, CC BY-NC-SA 4.0, ไม่ gated): diffusers ทางการแต่ **16 kHz mono** เสียงทึบเมื่อวางคู่เสียงพูด 24–44 kHz; pipeline ใช้ `GPT2Model` ภายใน ซึ่งเป็นจุดเสี่ยงกับ transformers 5 (ไม่พบรายงานยืนยัน ต้องลองถ้าจะใช้). รุ่นเก่า (2023) คุณภาพตามหลังชัด
- **Tango 2**: 16 kHz, 10 วิ, CC BY-NC-SA, ฐาน AudioLDM — ตัดออก
- **AudioGen / MusicGen / MAGNeT** (audiocraft, CC BY-NC 4.0, ไม่ gated): AudioGen 16 kHz mono 10 วิ, `audiocraft` pin torch เก่า (2.1.x) + `xformers` → ติดตั้งยากบน Mac/Windows. MusicGen อยู่ใน `transformers` (`MusicgenForConditionalGeneration`) ไม่ต้อง repo แยก, 32 kHz mono 30 วิ, ทำ music bed/drone ได้แต่ autoregressive ช้า (ประมาณ M2 1–3 นาทีต่อ 30 วิ สำหรับ small) และไม่ทำ ambience. ตกรุ่นแล้วเมื่อเทียบ SA3 small-music
- **MMAudio text mode** (`hkchengrex/MMAudio`, CC BY-NC 4.0): ฝึกที่ **8 วิ** ยาวกว่านี้คุณภาพตก, README "only tested on Ubuntu" ไม่พูดถึง MPS, repo 54.6 GB ต้องเลือกไฟล์. เหมาะกับ video-to-audio มากกว่า
- **AudioX / AudioX-Turbo / AudioX-MAF** (HKUST, CC BY-NC 4.0): โมเดล any-to-audio บน `stable-audio-tools`, ~10 วิ, Turbo repo 23 GB. ไม่คุ้มสำหรับงาน text อย่างเดียว
- **Woosh** (Sony AI, weights CC BY-NC 4.0, mirror `drbaph/Woosh`): DFlow 4 steps เร็วมาก แต่ paper SA3 ระบุ output band-limited และคุณภาพต่ำกว่า SA3 small-sfx
- **ดนตรีล้วน (เผื่อ music bed ที่มีโครงสร้าง)**: `ACE-Step/Ace-Step1.5` (MIT, ไม่ gated, ~10 GB รวม LM 1.7B), `google/magenta-realtime-2` (CC BY 4.0, มี `.mlxfn` สำหรับ Mac). เกินความต้องการ "bed ง่ายๆ" ของรอบนี้ ยังไม่ได้ตรวจลึก

## เรื่องการวนซ้ำ (loop)

ไม่มีโมเดลไหนสร้าง seamless loop ให้เองตรงๆ. ทางที่ใช้ได้:

1. สั่งความยาวให้พอดีกับคลิป (SA3 ยาวได้ 120 วิ ครอบคลุมคลิป 60–120 วิ ในครั้งเดียว → **อาจไม่ต้อง loop เลย**)
2. ถ้าต้อง loop: crossfade หัว-ท้ายด้วย ffmpeg (`acrossfade`) — ambience/drone ทนการ crossfade ได้ดี
3. ใช้ inpainting ของ SA3: ต่อท้ายคลิปด้วยหัวคลิปแล้ว inpaint ช่วงรอยต่อ ให้โมเดลเติมเสียงเชื่อม (เป็นแนวคิด ต้องลอง)

## ข้อแนะนำ

1. **หลัก: Stable Audio 3 small-sfx** (ambience/SFX) **+ small-music** (bed/drone) — คุณภาพดีสุดที่ลงเครื่องได้ (ชนะ SAO/TangoFlux/Woosh ใน paper), เร็วระดับวินาทีแม้บน CPU, ใช้หน่วยความจำ ~2–2.5 GB, ยาวได้ 120 วิ 44.1 kHz stereo, license รองรับ personal use. โหลดจาก mirror `cocktailpeanut/stable-audio-3-small-sfx` @ `84c4bc8e…` และ `cocktailpeanut/stable-audio-3-small-music` @ `d237d3df…` (ไฟล์ตรงทางการ ตรวจ sha256 ได้), รวมประมาณ 5.8 GB (T5Gemma ซ้ำกันสองชุด — โหลดชุดเดียวแล้วแชร์ได้ เหลือ ~4.6 GB). ตัวรัน: PyTorch (`stable-audio-3` vendored/override torch 2.8) ทั้งสอง OS; ถ้า MPS มีปัญหาให้ใช้ CPU หรือ MLX จาก `stabilityai/stable-audio-3-optimized` (ทางการ ไม่ gated) ตาม ADR-0025
2. **สำรอง: MOSS-SoundEffect v2.0** — ถ้า mirror SA3 หายหรืออยากได้ Apache 2.0; ต้องแก้ปัญหา dependency (transformers 4.57/numpy 1.26) และช้ากว่ามาก

## สิ่งที่ต้องลองบนเครื่องจริง

- SA3 small-sfx/small-music รันด้วย `torch==2.8.0` (แทน 2.7.1 ที่ pin) ได้ไหม ทั้ง Mac และ Windows cu128
- บน Mac: MPS fp32 ผ่านไหม (output ไม่เงียบ/ไม่ NaN) และเร็วกว่า CPU จริงไหม; เวลาจริงบน M2 16 GB สำหรับ 30/47/120 วิ
- บน RTX sm_75 (ไม่มี bf16): `model_half=True` (fp16) ให้เสียงปกติไหม หรือต้อง fp32
- โหลด T5Gemma จากโฟลเดอร์ใน `models/` แทน `repo_id` ใน `model_config.json` ได้โดยไม่แตะเน็ต (`HF_HUB_OFFLINE=1`)
- คุณภาพ prompt ที่ใช้จริง: "night forest crickets wind", "rain on tin roof", "low eerie drone", เสียงประตูไม้เอี๊ยด, ฝีเท้าบนพื้นไม้ — ฟังว่า small-sfx พอไหม หรือต้อง medium (Windows) / MLX medium (Mac)
- seed ต่างกันได้ผลต่างกันพอไหม (รีวิวบอก small-music ซ้ำกันง่าย)
- ความยาว 120 วิ ครั้งเดียว vs 30 วิ + crossfade loop แบบไหนฟังดีกว่าใต้เสียงบรรยาย; ลอง inpainting ปิดรอยต่อ
- ขนาด download จริงหลังใช้ `allow_patterns` และการแชร์ T5Gemma ระหว่างสองโมเดล
- `/warroom legal`: Stability AI Community License + Gemma ToU กับการโพสต์คลิปส่วนตัว และควรใส่ "Powered by Stability AI" ใน `NOTICE.md` ไหม

## แหล่งอ้างอิง

- HF API ที่ใช้เช็ค gated/license/ขนาด/sha256: `https://huggingface.co/api/models/{repo}?blobs=true` (ทุก repo ในตาราง)
- Stable Audio 3 card: https://huggingface.co/stabilityai/stable-audio-3-small-sfx, https://huggingface.co/stabilityai/stable-audio-3-optimized
- Stable Audio 3 GitHub (ขนาด, ความยาว, หน่วยความจำ, เวลา, `pyproject.toml`, `model.py`, `model_configs.py`): https://github.com/Stability-AI/stable-audio-3
- Stable Audio 3 paper (Table 5 BBC SFX): https://arxiv.org/abs/2605.17991, https://arxiv.org/html/2605.17991
- รีวิว Dubspot: https://blog.dubspot.com/stable-audio-3-review
- mirror SA3: https://huggingface.co/cocktailpeanut/stable-audio-3-small-sfx, https://huggingface.co/cocktailpeanut/stable-audio-3-small-music, https://huggingface.co/Comfy-Org/stable-audio-3
- Stability AI Community License: https://stability.ai/community-license-agreement
- Gemma Terms of Use: https://ai.google.dev/gemma/terms
- Stable Audio Open 1.0: https://huggingface.co/stabilityai/stable-audio-open-1.0, diffusers: https://huggingface.co/docs/diffusers/api/pipelines/stable_audio
- mirror SAO: https://huggingface.co/AEmotionStudio/stable-audio-open-models, https://huggingface.co/ModelsLab/stable-audio-open-1.0
- Stable Audio Open Small: https://huggingface.co/stabilityai/stable-audio-open-small
- MOSS-SoundEffect v2.0: https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0, https://github.com/OpenMOSS/MOSS-TTS/tree/main/moss_soundeffect_v2
- TangoFlux: https://huggingface.co/declare-lab/TangoFlux (LICENSE.md)
- AudioLDM 2: https://huggingface.co/cvssp/audioldm2, https://huggingface.co/docs/diffusers/api/pipelines/audioldm2
- Tango 2: https://huggingface.co/declare-lab/tango2
- AudioGen / MusicGen / MAGNeT: https://huggingface.co/facebook/audiogen-medium, https://huggingface.co/facebook/musicgen-small, https://huggingface.co/facebook/magnet-small-10secs
- MMAudio: https://github.com/hkchengrex/MMAudio, https://huggingface.co/hkchengrex/MMAudio
- AudioX: https://huggingface.co/HKUSTAudio/AudioX, https://huggingface.co/HKUSTAudio/AudioX-Turbo
- Woosh: https://huggingface.co/drbaph/Woosh
- ACE-Step 1.5: https://huggingface.co/ACE-Step/Ace-Step1.5; Magenta RealTime 2: https://huggingface.co/google/magenta-realtime-2
