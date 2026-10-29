# Sketch: Setup status checklist

Sketch ที่ผู้ใช้เลือกใน interview (D7) ปรับตาม red team (D13). ใช้เป็น brief ของหน้าจอ ไม่ใช่ design จริง (D9). ข้อความจริงอยู่ใน spec.md › Frontend.

```text
framecraft — Setup status        [Refresh]
เช็คล่าสุด: 17:42:10
ยังไม่พร้อม: ขาด 1 รายการ

✅ Python venv        3.12.11 (.venv)
✅ torch              2.8.0
✅ transformers       4.5x
✅ omnivoice          0.x
✅ fastapi            0.11x
✅ ffmpeg             7.1 (imageio-ffmpeg)
❌ OmniVoice model    k2-fsa/OmniVoice — ไม่พบใน models/
                      → ./setup.sh
                      CC BY-NC 4.0 · k2-fsa · [license] [model]
✅ Whisper model      whisper-large-v3-turbo (1.6 GB)
                      MIT · OpenAI · [license] [model]
⚠️ Device             cpu — ไม่พบ mps/cuda (ช้า)

7/9

--- backend ไม่ตอบ ---
Backend offline
ยังไม่ได้ start: รัน npm run dev
รันอยู่แล้ว: ดู error ในบรรทัด [api] ของ terminal หรือรัน setup ใหม่
```
