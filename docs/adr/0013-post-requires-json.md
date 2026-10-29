# ทุก POST ของ API ต้องเป็น application/json

ทุก `POST` ใต้ `/api` ที่ `Content-Type` ไม่ใช่ `application/json` ได้ `415`. Header นี้บังคับ CORS preflight ซึ่ง backend ไม่ตอบ จึงไม่มีเว็บอื่นที่เปิดใน browser เดียวกันสั่งงานบน `127.0.0.1` ได้ — `TrustedHostMiddleware` (ADR-0011) กันไม่ได้เพราะ `Host` ของ request แบบนั้นถูกต้อง.

Source: spoil D29
