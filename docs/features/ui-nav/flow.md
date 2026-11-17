# Flow: ui-nav

3 diagrams, read in this order:
1. เมนูหลักมีอะไร และแต่ละรายการพาไป hash ไหน
2. ปุ่ม ☰ เปิดและปิดเมนูอย่างไรบนสองจอ
3. ล่าสุดถูกเขียนและลบเมื่อไร

All diagrams use the same names as [spec.md](spec.md).

## 1. ต้นไม้เมนูหลัก

```mermaid
flowchart LR
    menu["เมนูหลัก"]
    menu --> setup["ติดตั้ง #/setup"]
    menu --> spoil["สปอย"]
    menu --> toon["การ์ตูนเล่า"]
    menu --> drums["สอนกลอง"]
    menu --> songs["แกะเพลง"]
    menu --> lib["คลัง"]

    spoil --> s1["1 เลือกคลิป #/spoil"]
    spoil --> s2["2 ตรวจแก้บท #/spoil/review"]
    spoil --> s3["3 ผล render #/spoil/renders"]

    toon --> t1["ชุดทั้งหมด #/toon"]
    toon --> t2["สร้างชุดใหม่ #/toon/new"]
    toon --> tr["ล่าสุด: ชุดหรือ EP ไม่เกิน 3"]

    drums --> d1["บทเรียนทั้งหมด #/drums"]
    drums --> dr["ล่าสุด: บทเรียน ไม่เกิน 3"]

    songs --> g1["เพลงทั้งหมด #/songs"]
    songs --> gr["ล่าสุด: เพลง ไม่เกิน 3"]

    lib --> l1["คลังคลิป #/clips ใช้กับ สปอย"]
    lib --> l2["คลังความรู้ #/stories ใช้กับ สปอย"]
    lib --> l3["คลังเสียง #/sounds ใช้กับ สปอย, การ์ตูนเล่า"]
    lib --> l4["เสียงที่บันทึก #/spoil/voices ใช้กับ สปอย, การ์ตูนเล่า"]
```

**เมนูมีกี่ชั้น และกดอะไรแล้วไปไหน**
- ทุกปลายทางอยู่ลึกไม่เกินสองชั้นจากเมนู: หัวข้อ → รายการ (D3)
- หัวข้อที่มีรายการเป็นหัวกลุ่ม ไม่ใช่ลิงก์; ติดตั้งเป็นลิงก์เอง (D3)
- รายการที่เปิดอยู่หาจาก hash ด้วย prefix ที่ยาวที่สุด (D6)
- ล่าสุดไม่มี = ไม่มีหัวเล็ก "ล่าสุด" ใต้หัวข้อนั้น (D5)

## 2. เปิดและปิดเมนู

```mermaid
stateDiagram-v2
    direction LR
    state "จอ ≥1280px" as wide {
        [*] --> Shown: ค่ายุบไม่มีหรืออ่านไม่ได้
        [*] --> Collapsed: ค่ายุบ = true
        Shown --> Collapsed: กด ☰
        Collapsed --> Shown: กด ☰
        Shown --> Shown: เลือกรายการ
    }
    state "จอ <1280px" as narrow {
        [*] --> Closed
        Closed --> Open: กด ☰
        Open --> Closed: เลือกรายการ
        Open --> Closed: Esc แล้วโฟกัสกลับ ☰
        Open --> Closed: กดนอกเมนู
        Open --> Closed: กด ☰
    }
```

**ปุ่ม ☰ ทำอะไรบนแต่ละจอ**
- เป็น `<nav>` ตัวเดียว ปุ่มเดียว; `aria-expanded` บอกว่าเมนูเห็นอยู่หรือไม่บนจอนั้น (D4)
- ค่ายุบเก็บใน `framecraft.nav.collapsed` เฉพาะจอกว้าง; drawer ของจอแคบปิดทุกครั้งที่ load (D4)
- ข้ามจุดแบ่งระหว่างเปิดหน้า: drawer ที่เปิดอยู่ปิด แล้วใช้ค่ายุบของจอกว้าง (D4)
- เลือกรายการขณะมีงานไม่บันทึก: leave guard ถามก่อน hash เปลี่ยน; drawer ปิดไม่ว่าตอบอะไร (D6, D10)
- drawer เปิด: โฟกัสไปรายการที่เปิดอยู่ หน้าข้างหลัง `inert`; ปิดด้วยการเลือกหรือ `Esc` โฟกัสกลับ ☰ (D10)

## 3. ล่าสุด

```mermaid
sequenceDiagram
    participant P as หน้าของชิ้น
    participant R as recent.ts
    participant S as localStorage
    participant M as เมนูหลัก
    P->>P: โหลดชุด EP บทเรียน หรือเพลง
    alt โหลดสำเร็จ
        P->>R: rememberRecent(หัวข้อ, hash, ชื่อ, parent)
        R->>S: เขียน ใหม่สุดก่อน ไม่ซ้ำ ไม่เกิน 3
        R-->>M: แจ้งให้อ่านใหม่
    else ผู้ใช้ลบชิ้นนั้น หรือ not_found ของบทเรียนหรือเพลง
        P->>R: forgetRecent(hash)
        R->>S: ลบรายการนั้น
        R-->>M: แจ้งให้อ่านใหม่
    end
    M->>S: อ่านตอน render
```

**ล่าสุดเปลี่ยนเมื่อไร**
- หน้าย่อย (`/cast`, `/render`, `/renders`, `/cover`, …) ไม่เขียน แต่เน้นล่าสุดของชิ้นแม่ (D11)
- การ์ตูนเล่าลบล่าสุดได้ทางลบเท่านั้น; ลบชุดลบ EP ของมันด้วย (D11)
- `localStorage` โยนหรือ JSON เสีย = ไม่มีล่าสุด ไม่มี error บนจอ (D5)
- แท็บอื่นเปลี่ยนค่า → event `storage` ให้เมนูอ่านใหม่ (D5)
