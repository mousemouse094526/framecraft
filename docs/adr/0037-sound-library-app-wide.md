# คลังเสียงเป็นของ `backend.sounds` ทั้งแอป feature ที่ใช้เก็บแค่ id ของเสียง

เสียงพื้นทุกเสียงและ id `m_` อยู่ใน `backend.sounds` ที่เดียว (`media/sounds/`, `/api/sounds`); การ์ตูนเล่า สปอย และ feature ต่อไปเก็บแค่ `sound_id` และอ่านเสียงผ่าน `backend.sounds` ซึ่งไม่ import feature ใดเลย. เลือกแบบนี้แทนการคงคลังไว้ใต้การ์ตูนเล่าหรือแยกคลังต่อ tab เพราะเสียงเดียวกันใช้ได้ทุกคลิป และ feature หนึ่งไม่ควร import อีก feature เพื่ออ่านของกลาง. คลังเคยเป็นของ tab การ์ตูนเล่า (toon D16) ข้อมูลเดิมจึงถูกย้ายมาตอน start.

Source: sound-library D1, D6, D10

**Status:** accepted
