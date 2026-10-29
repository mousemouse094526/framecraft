# งาน AI และสื่อทั้งหมดรันใน FastAPI backend ตัวเดียว

งาน AI และสื่อทั้งหมด (TTS, Whisper, ffmpeg) รันใน Python backend ตัวเดียวที่เป็น FastAPI และอยู่ตลอด process. React เป็นแค่ UI ที่เรียก backend ผ่าน HTTP JSON. ไม่ใช้ Node server ที่ spawn python script ทีละงานเพราะต้องโหลดโมเดลใหม่ทุกครั้ง และไม่ใช้ Electron หรือ Tauri เพราะหนักเกินไปสำหรับขั้นแรก.

Source: setup-status D1
