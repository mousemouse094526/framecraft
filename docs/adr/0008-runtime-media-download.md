# Backend โหลดสื่อตามลิงก์ของผู้ใช้ได้ตอนรัน แต่ติดตั้งผ่าน Setup script เท่านั้น

Backend โหลดสื่อตามลิงก์ที่ผู้ใช้ใส่เองได้ตอนรัน (เช่นคลิป YouTube ใน tab สปอย). การติดตั้ง package และการดาวน์โหลดโมเดลยังทำผ่าน Setup script เท่านั้น และโค้ดที่โหลดโมเดลต้องโหลดจาก snapshot ในเครื่อง. แยกสองอย่างนี้เพราะ feature ต้องดึงสื่อตอนใช้งาน แต่เหตุผลเดิมของ ADR-0002 (ไม่มีปุ่ม Install บนเว็บ, โมเดลตรงตาม lock) ยังใช้กับ package และโมเดล.

**Status:** accepted — supersedes ADR-0002

Source: spoil D1 · setup-status D3, D8
