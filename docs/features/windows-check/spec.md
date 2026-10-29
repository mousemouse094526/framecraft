# Spec: windows-check

ผู้ใช้เอา framecraft ไปรันบนเครื่อง Windows ที่มีการ์ด NVIDIA จริง แล้วเช็คว่าทุก feature ที่จบบน Mac แล้วใช้ได้เหมือนกัน.

**Status:** ready-to-build

## Problem

feature จบได้เมื่อผ่านบน Mac (setup-status D25) แต่โค้ดทาง Windows ยังไม่เคยรันบนเครื่องจริง. ไม่มีที่เดียวที่บอกว่าต้องลองอะไรบ้างเมื่อได้เครื่อง Windows.

## Solution

- ticket ละ feature ที่จบบน Mac แล้ว รวมทุกข้อที่ต้องเช็คมือบน Windows (setup-status D25)
- ได้เครื่อง Windows เมื่อไร ทำทีละ ticket ตามลำดับ
- ข้อที่พัง → แก้ใน ticket นั้น ด้วย regression test ถ้าทำได้ (setup-status D25)

## User Stories

**ผู้ใช้ Windows**
1. As a ผู้ใช้ Windows ที่มีการ์ด NVIDIA, I want ทุก feature ทำงานเหมือนบน Mac, so that ใช้ได้ทั้งสองเครื่อง (setup-status D5, D25)

## Expected Outcome

ผู้ใช้ Windows NVIDIA ติดตั้งและใช้ทุก feature ที่ผ่านบน Mac แล้วได้.
- **ได้เครื่อง Windows:** clone `develop` แล้วทำ ticket ตามลำดับ แต่ละ ticket จบเมื่อทุกข้อผ่าน

**How success is judged:**
- ทุก ticket ใน `docs/progress/windows-check/tickets/` เป็น `done`

## Implementation

### Modules touched

- ไม่มีโค้ดใหม่ล่วงหน้า. แก้เฉพาะที่พังบน Windows ในโมดูลของ feature นั้น ตาม conventions ของ feature นั้น

### เพิ่ม ticket

- feature ใหม่ที่มีของเฉพาะ Windows (path, process, file lock, `cuda`) เพิ่ม ticket ที่นี่ตอนตัด ticket ของตัวเอง (setup-status D25)
- ticket ใหม่ blocked by ticket ก่อนหน้าใน feature นี้ เพราะทุกตัวต้องการ `setup.cmd` ที่ใช้ได้จาก ticket 01
- กฎนี้อยู่ใน ADR-0014 ซึ่ง warroom อ่านก่อนวางแผนทุก feature

### จบรอบ

- ทุก ticket ที่มี `done` → feature review และ PR ตามปกติ
- feature ใหม่เพิ่ม ticket ทีหลัง → feature นี้กลับไป `ready` เป็นรอบใหม่

## Seams

ใช้ seam ของ feature ต้นทาง บนเครื่อง Windows (setup-status D25).

1. **Setup และ Status check** ตาม setup-status spec › How success is judged ข้อ Windows
   - ticket 01
2. **tab สปอย** ตาม spoil spec › How success is judged และ Seams 2, 3 ข้อ Windows
   - ticket 02

## Testing decisions

- เช็คมือบนเครื่องจริงเป็นหลัก. สิ่งที่แก้ระหว่างเช็คได้ regression test ตามแบบ `backend/tests/test_wrappers.py` และ `run_checks` ที่รับ `sys_platform` (setup-status D18, D23)

## Out of Scope

- Linux, AMD GPU, Intel GPU และ Windows CPU-only (setup-status D5)
- CI บน Windows

## Open Questions

1. ได้เครื่อง Windows ที่มีการ์ด NVIDIA เมื่อไร — non-blocking: ไม่มีงานอื่นรอ feature นี้ (setup-status D25)
