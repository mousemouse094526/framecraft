# ทิศ import ระหว่าง `drum_cover` กับ package ของเครื่องดนตรี

เสียง ภาพ และ timeline ของแต่ละเครื่องดนตรีอยู่ใน package ของตัวเอง (`kalimba_cover`) ซึ่ง import `drum_cover` ได้; `drum_cover` ถือ Cover, routes, Render job slot เดียว และ `reel_wav` และ import package เครื่องดนตรีได้แค่ใน `render` กับ `cover` → `arrange` ที่ import แค่ `drum_notes.songs` เพื่อไม่ให้ import วน. เลือกแทนการเปลี่ยนชื่อ `drum_cover` (แตะทุก import test และ ADR โดยไม่เปลี่ยนพฤติกรรม) และแทนการใส่คาลิมบาใน `drum_cover` (ภาพกลองปนกับภาพคาลิมบา). helper ของ `drum_cover` ที่คาลิมบาเรียก (ตัวนับ จุดจังหวะ หัวเรื่อง) เปลี่ยนหน้าตาได้เมื่อตั้งใจให้ reel ทุกเครื่องดนตรีเปลี่ยนด้วย.

**Status:** accepted — extends ADR-0052, ADR-0054

Source: kalimba-cover D7, D8, D14
