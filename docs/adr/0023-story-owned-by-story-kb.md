# Story และ Story ที่คลิปจำเป็นของ story-kb ไม่ใช่ของ Temp clip

Story และการที่คลิปจำ Story เก็บและเปิด API ใน story-kb เอง ไม่เป็นฟิลด์ของ Temp clip หรือของ `/api/spoil/clips`; spoil เรียกเข้า story-kb ทางเดียวคือตอนลบคลิป. เลือกแบบนี้เพื่อให้ spoil ไม่ต้องรู้จัก Story และ Story ใช้ได้กับคลิปหลายคลิปโดยไม่ต้องย้ายข้อมูลของคลิป. feature ที่จะใช้ Story (เช่นการออกเสียงชื่อ) อ่านจาก story-kb ไม่เก็บสำเนาไว้กับคลิป.

Source: story-kb D1, D12

**Status:** accepted
