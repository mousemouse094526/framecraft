# Progress: windows-check

> **ย้ายไป [windows-launch](../windows-launch/progress.md) แล้ว 2026-11-10** — งาน Windows ทั้งหมดถูกรวมเป็นแถวเดียวบน board (`Manual = true`) ไฟล์นี้เก็บไว้เป็นประวัติ; ticket 01–02 ถูกอ้างถึงใน progress ของ windows-launch

**Now:** รอเครื่อง Windows NVIDIA (Blocked #1); ticket 01 กับ 02 พร้อมทำ

**Next:**

```
/warroom-build windows-check 01
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | เช็ค setup-status บน Windows NVIDIA | ready |
| 02 | เช็ค spoil บน Windows NVIDIA | ready |

## Log

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | ต้องมีเครื่อง Windows ที่มีการ์ด NVIDIA (spec Open Question 1) | ผู้ใช้ clone `develop` บน Windows แล้ว `/warroom-build windows-check 01` | open |
