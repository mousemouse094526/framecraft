# ภาพของการ์ตูนเล่าสร้างด้วย FLUX.2 klein 4B ผ่าน diffusers โดย transformer เป็น GGUF ระดับสูงสุดที่ peak MPS ไม่เกิน 12 GB และ encode คำสั่งก่อนโหลด transformer

ทุกงานภาพใช้ klein 4B ใน diffusers ทั้ง Mac และ Windows: transformer จากไฟล์ GGUF ของ unsloth ส่วนอื่นจาก repo ของ BFL ทั้งสองแบบ pin commit และในหนึ่งงานโหลด text encoder ไป encode ทุกคำสั่งแล้วปล่อยก่อนโหลด transformer. ระดับของ GGUF คือระดับสูงสุด (Q8_0 → Q6_K → Q4_K_M) ที่กรณีหนักสุดบน Mac 16 GB ใช้ peak MPS ของ process ลูกไม่เกิน 12 GB และยังคงหน้าตาตัวละคร เพราะ Q8_0 บน torch ของ project วัดได้ 13–14 GB และเครื่อง swap. Qwen-Image (ใบอนุญาตวิจัย หนักเกิน) และ SDXL กับ LoRA ต่อตัวละครถูกปฏิเสธ.

Source: toon D6, D34, D35, D49

Links: [trial-klein-mac-2026-11-09](../features/toon/trial-klein-mac-2026-11-09.md)

**Status:** superseded by ADR-0036 (เดิม supersedes ADR-0030)
