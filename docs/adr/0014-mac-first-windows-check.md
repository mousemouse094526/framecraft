# รองรับ Mac และ Windows แต่ feature จบได้เมื่อผ่านบน Mac

Project รองรับแค่ Mac Apple Silicon (device `mps`) และ Windows ที่มีการ์ด NVIDIA (CUDA 12.8, device `cuda`); Linux, AMD GPU, Intel GPU และ Windows CPU-only ไม่อยู่ใน scope. ทุก feature เขียนโค้ดและ test สำหรับทั้งสองแพลตฟอร์ม แต่จบได้เมื่อเช็คบน Mac ผ่าน. การเช็คมือบนเครื่อง Windows จริงเป็น ticket ใน feature `windows-check` เพื่อไม่ให้ขวางงานบน Mac.

Source: setup-status D5, D25

Status: supersedes ADR-0006 · superseded by ADR-0016
