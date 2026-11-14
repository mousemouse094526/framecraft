# โมเดล ONNX เล็กที่รันบน CPU เป็นงาน thread ธรรมดา ไม่จองช่อง GPU ไม่ต้องแถว `device`

งานที่โหลดโมเดล ONNX ด้วย onnxruntime บน CPU (Pick job ของ tab แกะเพลง; ไฟล์รวมไม่ถึง 100 MB) เป็น `JobSlot` ใน thread ตาม ADR-0010: ไม่จองช่อง GPU, ไม่รันใน process ลูก และ gate ของมันไม่มีแถว `device`. ADR-0015 และ ADR-0026 จึงครอบเฉพาะงานที่โหลดโมเดลขึ้นการ์ด (Metal หรือ CUDA) หรือกิน memory เป็น GB ซึ่งเป็นเหตุผลเดิมของสอง ADR นั้น (crash ของการ์ดฆ่าทั้ง process, LLM กิน 10 GB); ADR-0012 ไม่เปลี่ยน. เลือกแบบนี้แทน `ModelJobSlot` กับ process ลูก เพราะผู้ใช้จะถูกปฏิเสธว่า "รอให้งานถอดบทพูดเสร็จก่อน" ทั้งที่งานไม่แตะการ์ด.

**Status:** accepted — narrows ADR-0015, ADR-0026

Source: drum-notes D8
