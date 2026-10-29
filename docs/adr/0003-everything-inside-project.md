# ทุกอย่างอยู่ใน folder ของ project และโมเดลอยู่ใน models/

ทุกอย่างที่ project ใช้อยู่ใน folder ของ project. โมเดลเก็บใน `models/` และทุกจุดที่โหลดหรือดาวน์โหลดโมเดลต้องส่ง `cache_dir` ตรงๆ ห้ามพึ่ง cache กลางของเครื่องหรือ env `HF_HOME` และ `HF_HUB_CACHE`. "Portable" หมายถึงก๊อป folder ไปเครื่อง OS เดียวกันแล้วรัน Setup script ซ้ำ: โมเดลใช้ต่อได้ ส่วน `.venv` สร้างใหม่ (ต้องมี internet).

Source: setup-status D6, D12, D13
