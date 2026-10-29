# Docs

What each folder is for. Start with `progress/board.md` to see where every
feature stands, and `decisions.md` before deciding anything.

| Folder | Holds | Written by | Read it when |
|---|---|---|---|
| `decisions.md` | ทุก decision ใน project บรรทัดละหนึ่ง แยกตามหัวข้อ ลิงก์ไปตัวเต็ม | warroom skills ทันทีที่ตัดสิน | ก่อนถามหรือตัดสินอะไร |
| `features/{slug}/` | feature หนึ่งคืออะไร: spec, decisions, flow, legal check, sketch | warroom | ทำงานกับ feature นั้น |
| `progress/` | งานที่กำลังทำ: `board.md` ของทุก feature, แล้วแต่ละ feature มี tickets, progress log, user trials, bugs | warroom skills | หยิบงานต่อหรือเช็คความคืบหน้า |
| `adr/` | กฎที่ทุก feature ต้องทำตาม หนึ่งไฟล์สั้นต่อกฎ | warroom ที่ gate | เริ่ม feature ใดก็ตาม |
| `library-notes/` | best practice ของภาษาและ library ตาม version ที่ติดตั้ง หนึ่งไฟล์ต่อ library | warroom-build ก่อนเขียน code ที่ใช้ library นั้น | ก่อนเขียนหรือ review code ที่เรียก library นั้น |
