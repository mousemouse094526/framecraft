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

**สปอย**:
tab ในแอปที่รับลิงก์ YouTube มาทำคลิปเล่าหรือสปอยหนัง. ตอนนี้ทำได้แค่โหลดคลิปเก็บเป็น Temp clip.
_Avoid_: recap, spoiler page

**Temp clip**:
คลิป YouTube หนึ่งคลิปที่โหลดมาเก็บใน `media/temp/` (วิดีโอ mp4, ข้อมูล json, thumbnail). อยู่จนผู้ใช้กดลบ. ไม่มีไฟล์ json คือคลิปยังไม่ครบ.
_Avoid_: cache, download, temp file

**Download job**:
การโหลด Temp clip หนึ่งคลิปที่ backend ทำเบื้องหลัง. มีได้ทีละงานและหายเมื่อ backend restart.
_Avoid_: task, queue item

