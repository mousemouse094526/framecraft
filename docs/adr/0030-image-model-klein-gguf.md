# ภาพของการ์ตูนเล่าสร้างด้วย FLUX.2 klein 4B ผ่าน diffusers โดย transformer เป็น GGUF Q8_0 และ encode คำสั่งก่อนโหลด transformer

ทุกงานภาพใช้ klein 4B ใน diffusers ทั้ง Mac และ Windows: transformer จากไฟล์ GGUF Q8_0 ส่วนอื่นจาก repo ของ BFL ทั้งสองแบบ pin commit และในหนึ่งงานโหลด text encoder ไป encode ทุกคำสั่งแล้วปล่อยก่อนโหลด transformer. เลือกแบบนี้เพราะบนเครื่อง 16 GB bf16 ใช้ peak เกือบเต็มเครื่อง (14.96 GB) ส่วน GGUF Q8_0 ใช้ 11.2 GB ที่เร็วเท่ากัน และ text encoder กับ transformer อยู่พร้อมกันไม่ลง. Qwen-Image (ใบอนุญาตวิจัย หนักเกิน) และ SDXL กับ LoRA ต่อตัวละครถูกปฏิเสธ.

Source: toon D6, D34, D35

Links: [trial-klein-mac-2026-11-09](../features/toon/trial-klein-mac-2026-11-09.md)

**Status:** accepted
