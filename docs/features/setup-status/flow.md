# Flow: setup-status

2 diagrams, read in this order:
1. Setup script ติดตั้งอะไรตามลำดับไหน และหยุดตรงไหน
2. กด Refresh แล้วหน้าเว็บได้ checklist หรือ offline อย่างไร

All diagrams use the same names as [spec.md](spec.md).

## 1. Setup script

### 1.1 Wrapper

```mermaid
flowchart TD
    start([ผู้ใช้รัน setup.sh หรือ setup.cmd]) --> hasUv{มี uv?}
    hasUv -- ไม่มี --> installUv[ติดตั้ง uv ด้วย installer ทางการ]
    installUv -. ล้ม .-> errW([พิมพ์ error แล้ว exit 1])
    hasUv -- มี --> hasNode{มี node และ npm?}
    installUv --> hasNode
    hasNode -- ไม่มี --> needNode([Node.js 22+ required แล้ว exit 1])
    hasNode -- มี --> sync[uv sync: Python 3.12, torch ตาม OS, package ทั้งหมด]
    sync -. ล้ม .-> errW
    sync --> runSetup([uv run --no-sync python -m backend.setup])
```

### 1.2 backend.setup

```mermaid
flowchart TD
    begin([backend.setup]) --> busy{127.0.0.1:8000 ตอบ?}
    busy -- ตอบ --> stopDev([ปิด npm run dev ก่อนรัน setup แล้ว exit 1])
    busy -- ไม่ตอบ --> lock{lock ของ PID ที่ยังทำงาน?}
    lock -- มี --> running([setup กำลังรันอยู่อีกหน้าต่าง แล้ว exit 1])
    lock -- ไม่มี --> takeLock[เขียน setup.lock]
    takeLock --> allOk{โมเดลทุกตัว ok?}
    allOk -- ใช่ --> npm
    allOk -- ไม่ --> disk{ที่ว่าง >= 15 GB?}
    disk -- ไม่พอ --> noDisk([พิมพ์ที่ว่าง ลบ lock แล้ว exit 1])
    disk -- พอ --> loop[แต่ละโมเดลที่ยังไม่ ok: snapshot_download ด้วย revision ที่ pin แล้วเขียน marker]
    loop --> npm[npm install ที่ root และ frontend]
    npm --> unlock[ลบ lock]
    unlock --> print[พิมพ์ checklist จาก backend.checks]
    print --> anyMissing{มีรายการ missing?}
    anyMissing -- ไม่มี --> ok([พิมพ์ขั้นต่อไป npm run dev แล้ว exit 0])
    anyMissing -- มี --> fail([พิมพ์รายการที่ขาด แล้ว exit 1])
    loop -. ล้ม .-> err([พิมพ์ขั้นที่ล้ม ลบ lock แล้ว exit 1])
    npm -. ล้ม .-> err
```

**Setup script ทำอะไรตามลำดับไหน และหยุดตรงไหน**
- รันซ้ำได้ทุกครั้ง: โมเดลที่ `ok` ถูกข้าม, ที่ค้างโหลดต่อ (D3, D13)
- marker เขียนหลังโหลดเสร็จเท่านั้น ไม่มี marker = แถวโมเดลเป็น `missing` (D7)
- ล้มกลางทางไม่ลบสิ่งที่โหลดมาแล้ว
- Windows เข้าทาง `setup.cmd` ที่ bypass execution policy (D13)
- torch และ torchaudio เลือก index `cu128` บน Windows จาก `pyproject.toml` (D5, D13)

## 2. Refresh

```mermaid
sequenceDiagram
    actor User as ผู้ใช้
    participant Page as หน้า Setup status
    participant API as backend /api/setup/status
    participant Checks as backend.checks

    User->>Page: กด Refresh
    Page->>Page: ปุ่ม Refresh disabled
    Page->>API: GET /api/setup/status (timeout 30 วินาที)
    alt backend ตอบ
        API->>Checks: run_checks 9 รายการ
        Checks-->>API: items พร้อม status, detail, fix, license
        API-->>Page: 200 checked_at, ready, counts, items
        Page-->>User: คำตัดสิน, checklist และ n/9
    else ไม่ตอบ, ไม่ใช่ 200 หรือเกิน 30 วินาที
        Page-->>User: แทน checklist ด้วยข้อความ offline
    end
    Page->>Page: ปุ่ม Refresh กดได้อีกครั้ง
```

**กด Refresh แล้วได้ checklist หรือ offline อย่างไร**
- เปิดหน้าครั้งแรกเรียก API เหมือนกด Refresh หนึ่งครั้ง. ไม่ poll (D7)
- เช็คไม่ใช้ network และไม่โหลดโมเดล (D7)
- device cache เฉพาะผล `cuda` หรือ `mps` (D13)
- รายการหนึ่งพังไม่ทำให้รายการอื่นหาย: รายการนั้นเป็น `missing`
