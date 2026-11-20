# Flow: nav-ia

## จาก hash ถึงหน้า

ทุกครั้งที่อ่าน hash (โหลดหน้าและ `hashchange`) hash เก่าถูกแทนก่อน แล้วหัวข้อกับหน้าจึงถูกเลือก (D1, D9). เมนูอ่านแค่ hash กับ `NAV_SECTIONS` ตายตัว: ไม่มีล่าสุด และหน้าไม่เขียนอะไรให้เมนู (D22).

```mermaid
flowchart TD
    read["อ่าน location.hash"] --> moved{"ตรงแถวใน MOVED?"}
    moved -- ใช่ --> replace["replaceState เป็น hash ใหม่"]
    moved -- ไม่ --> tab
    replace --> tab["tabOf: หัวข้อจาก prefix"]
    tab --> clips{"#/spoil/clips?"}
    clips -- ใช่ --> clipsPage["หน้าคลิปทั้งหมด"]
    clips -- ไม่ --> page["หน้าของหัวข้อ<br/>spoil, toon, covers, drums,<br/>stories, sounds, voices, setup"]
    clipsPage --> menu["เมนู: ลิงก์ของ tab นี้ที่ hash ยาวที่สุดตรง<br/>หัวหน้า: ชื่อลิงก์นั้น"]
    page --> menu
```

## พื้นที่ทำงานสปอย

ขั้นเป็น state ของหน้า `#/spoil` ไม่ใช่ route (D5).

```mermaid
stateDiagram-v2
    [*] --> Loading: เปิด #/spoil
    Loading --> Review: มี Spoil draft หรือกำลังร่าง
    Loading --> Pick: ไม่มีบท หรืออ่านไม่ได้
    Pick --> Review: ร่างบทเริ่ม หรือกดขั้น 2
    Review --> Pick: ยกเลิกร่าง หรือกดขั้น 1
    Review --> Renders: render เสร็จ หรือกดขั้น 3
    Renders --> Review: กดขั้น 2
    Renders --> Pick: กดขั้น 1
    Pick --> Renders: กดขั้น 3
```

## หน้างานชิ้นเดียว

เพลง reel กลอง และ EP ทำงานในหน้าเดียวจนได้ผล render (D6, D7, D8).

```mermaid
flowchart LR
    subgraph song["#/covers/{id}"]
        pick["ช่วงแกะ + แกะโน้ต"] --> picked{"แกะแล้ว?"}
        picked -- ใช่ --> reel["ส่วน reel: เครื่องดนตรี ช่วง ข้อความ เสียง"]
        reel --> coverOut["ฟัง · render · ผล render"]
    end
    subgraph drum["#/drums/{id}"]
        form["ฟอร์ม reel กลอง"] --> drumOut["ฟังจังหวะ · render · ผล render ใต้ฟอร์ม"]
    end
    subgraph ep["#/toon/eps/{id}"]
        epOpen{"EP มีการ์ดแล้ว?"} -- ไม่ --> plot["พล็อต"]
        epOpen -- ใช่ --> story["เส้นเรื่อง"]
        plot -- "แตกการ์ดเสร็จ หรือกดเส้นเรื่อง" --> story
        story -- กดแก้พล็อต --> plot
        story <-->|"กด render (มีการ์ดเท่านั้น)"| render["render"]
    end
```
