# โมเดลทุกตัวลงทะเบียนที่เดียวและ pin commit

โมเดลทุกตัวที่ project ใช้ต้องอยู่ในรายการโมเดลที่เดียว (`backend.models`) และ pin ไว้ที่ commit hash ไม่ใช่ `main`. โมเดลพร้อมใช้ก็ต่อเมื่อ Setup script เขียน Model marker ที่ revision ตรงและไฟล์ครบแล้ว. การ pin กันการโหลดหลาย GB ใหม่ทุกครั้งที่ upstream เปลี่ยน แลกกับต้องแก้ revision เองเมื่ออยากอัปเดต.

Source: setup-status D7, D13
