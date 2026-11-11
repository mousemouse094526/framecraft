# ภาพของการ์ตูนเล่าสร้างด้วย FLUX.2 klein 4B ผ่าน diffusers ด้วยค่าที่ทั้งเครื่อง Mac 16 GB ไม่ swap

ทุกงานภาพใช้ klein 4B ใน diffusers ทั้ง Mac และ Windows: transformer จากไฟล์ GGUF ของ unsloth ส่วนอื่นจาก repo ของ BFL ทั้งสองแบบ pin commit และในหนึ่งงาน encode ทุกคำสั่งให้เสร็จและปล่อย text encoder ก่อนโหลด transformer. ค่าที่ใช้ (encode ใน process ลูกแยก, ระดับ GGUF, ขนาดวาด) ต้องผ่านสองเกณฑ์บน M1 16 GB: peak MPS ของ process ลูกไม่เกิน 12 GB และทั้งเครื่องที่เปิด `npm run dev` กับหน้าเว็บหนึ่ง tab ใช้ swap เพิ่มไม่เกิน 1 GB ระหว่างงาน, เพราะเกณฑ์ของ process ลูกอย่างเดียวผ่านได้ทั้งที่เครื่อง swap 4–5 GB และงานค้าง. Qwen-Image (ใบอนุญาตวิจัย หนักเกิน) และ SDXL กับ LoRA ต่อตัวละครถูกปฏิเสธ.

Source: toon D6, D34, D35, D49, D74

Links: [trial-klein-mac-2026-11-09](../features/toon/trial-klein-mac-2026-11-09.md)

**Status:** accepted · supersedes ADR-0035
