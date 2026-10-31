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
tab ในแอปที่รับลิงก์ YouTube มาทำคลิปเล่าหรือสปอยหนัง. ตอนนี้โหลดคลิปเก็บเป็น Temp clip และถอดบทพูดเป็น Transcript ได้.
_Avoid_: recap, spoiler page

**Temp clip**:
คลิป YouTube หนึ่งคลิปที่โหลดมาเก็บใน `media/temp/` (วิดีโอ mp4, ข้อมูล json, thumbnail). อยู่จนผู้ใช้กดลบ. ไม่มีไฟล์ json คือคลิปยังไม่ครบ.
_Avoid_: cache, download, temp file

**Download job**:
การโหลด Temp clip หนึ่งคลิปที่ backend ทำเบื้องหลัง. มีได้ทีละงานและหายเมื่อ backend restart.
_Avoid_: task, queue item

**Transcript**:
บทพูดของ Temp clip หนึ่งคลิปที่ Whisper ถอดออกมา เป็นบรรทัดพร้อมเวลาเริ่มและจบ. เก็บใน `media/temp/{id}.transcript.json` และหายเมื่อลบคลิป. คลิปมี Transcript = "ถอดแล้ว".
_Avoid_: subtitle, caption, บทสปอย

**Transcribe job**:
การถอด Temp clip หนึ่งคลิปเป็น Transcript ที่ backend ทำเบื้องหลังเมื่อผู้ใช้กดถอด. มีได้ทีละงาน รันพร้อม Download job ได้ และหายเมื่อ backend restart.
_Avoid_: process, transcription task


**Shot**:
ช่วงต่อเนื่องหนึ่งช่วงของ Temp clip ระหว่างจุดตัดภาพสองจุด ยาว 1–10 วินาที: ช่วงที่ยาวกว่า 10 วินาทีถูกแบ่งเป็นหลาย Shot. หน่วยภาพที่ spoil-maker เลือกมาวางใต้ประโยคของบทบรรยาย.
_Avoid_: scene, frame, cut

**Shot description**:
คำบรรยายภาพของ Shot หนึ่ง Shot ที่ LLM เขียนจากเฟรมของ Shot นั้น. เก็บใน `media/temp/shots/{id}/` คู่ภาพเล็กของแต่ละ Shot และหายเมื่อลบคลิป. คลิปที่มี Shot description ครบ = "ดูภาพแล้ว".
_Avoid_: caption, Transcript

**Describe job**:
การตัด Temp clip หนึ่งคลิปเป็น Shot และเขียน Shot description ทุก Shot ที่ backend ทำเบื้องหลังเมื่อผู้ใช้กด. รันพร้อม Transcribe job ไม่ได้.
_Avoid_: vision job, scene detection

**Spoil draft**:
คลิปสปอยที่กำลังทำก่อน render: Temp clip ที่เลือก, ค่าตั้ง, บท (ประโยคพร้อมบรรทัดที่อ้าง), Shot ของแต่ละประโยค และเสียงของแต่ละประโยค. เก็บเป็นไฟล์ใน `media/` อยู่ข้าม restart. มีได้ทีละหนึ่ง: ร่างบทใหม่ทับของเดิมหลังผู้ใช้ยืนยัน. ผลของการ render เรียกว่าคลิปสปอย.
_Avoid_: project, บทสปอย, session

**Saved voice**:
เสียงบรรยายหนึ่งเสียงที่ผู้ใช้บันทึกไว้ใช้ซ้ำทุกคลิป: ออกแบบจากเพศ วัย ระดับเสียง (clone จากไฟล์ของผู้ใช้ยังไม่มีในรอบนี้). เก็บเป็น clone prompt ของ OmniVoice คู่กับ speed และความเร็วพูดที่วัดได้ จึงได้เสียงเดิมทุกประโยค.
_Avoid_: preset, เสียงตัวอย่าง, speaker
