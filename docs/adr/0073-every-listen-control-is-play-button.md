# ทุกปุ่มฟังเสียงคือ `PlayButton` ชื่อตามการกระทำถัดไป

ปุ่มที่เล่นเสียงทุกปุ่มใช้ `components/ui/PlayButton`: ไอคอน play/pause, `aria-label` "ฟัง {x}" / "หยุดชั่วคราว {x}" ไม่ใช้ `aria-pressed` และไม่มีคำ "ฟัง" เปล่า ๆ บนจอ; ปุ่มที่ backend ผสมเสียงก่อนแสดงคำของมันเองซึ่งขึ้นต้นชื่อปุ่ม. เพราะเจ้าของบอกว่าปุ่ม "ฟัง" ดูแปลกและควรเป็นเครื่องหมาย play/pause และแนวทาง WAI-ARIA ห้ามเปลี่ยนชื่อปุ่มที่ใช้ `aria-pressed`.

**Status:** accepted

Source: audio-player D3, D4

Links: [WAI-ARIA APG Button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/) — ชื่อ toggle button ต้องคงที่เมื่อใช้ `aria-pressed`
