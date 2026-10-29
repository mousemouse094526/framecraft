# framecraft

เครื่องมือ generate video ที่ใช้ React เป็น UI และเรียก Python กับเครื่องมือ AI (OmniVoice, Whisper, ffmpeg) บนเครื่องผู้ใช้.

## Language

**Setup script**:
คำสั่งเดียว (`setup.sh` บน Mac, `setup.cmd` บน Windows) ที่ติดตั้ง Python env, package, ffmpeg และโมเดลทั้งหมดของ project.
_Avoid_: installer, install script

**Status check**:
การเช็คแบบเบาว่าแต่ละส่วนติดตั้งครบหรือยัง โดยไม่โหลดโมเดลและไม่ใช้ network.
_Avoid_: health check, smoke test

**Checklist item**:
หนึ่งรายการใน Status check มีสถานะ `ok`, `missing` หรือ `warning`.
_Avoid_: requirement, dependency row

**Model marker**:
ไฟล์ใน `models/.setup/` ที่ Setup script เขียนหลังโหลดโมเดลหนึ่งตัวเสร็จ. ไม่มี marker คือโมเดลยังไม่ครบ.
_Avoid_: lock file, done flag
