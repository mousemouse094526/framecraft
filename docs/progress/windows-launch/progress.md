# Progress: windows-launch

**Now:** ตัด ticket แล้ว; 01 พร้อมทำบน Mac

**Next:**

```
/warroom-build windows-launch 01
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | Status check, gate และ Setup script ของ Qwen ต่อ OS | ready |
| 02 | Worker Qwen บน Windows และ timeout ต่อ OS | ready |
| 03 | ลอง Qwen บนเครื่อง Windows RTX 30xx ขึ้นไป | ready |

## Log

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: ติดตั้ง (Status check) — แถว `device`, `gpu`, `bitsandbytes`, `model_qwen` ยังไม่มีแบบ | `/warroom windows-launch` พร้อมลิงก์แบบที่ทำจาก [ui-prompt.md](../../features/windows-launch/ui-prompt.md) | open |
| 2 | 03 | ต้องมีเครื่อง Windows ที่การ์ด RTX 30xx ขึ้นไปและ VRAM ≥ 8 GB (spec Open Question 1) | ผู้ใช้ clone `develop` บนเครื่องนั้นแล้ว `/warroom-build windows-launch 03` | open |
