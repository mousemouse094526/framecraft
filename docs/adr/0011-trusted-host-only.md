# ทุก request ต้องมี Host เป็น localhost

Backend ใส่ `TrustedHostMiddleware` ที่รับแค่ `127.0.0.1`, `localhost` และ `[::1]` กับทุก route. การ bind `127.0.0.1` ไม่กันเว็บอื่นที่ใช้ DNS rebinding ใน browser ของผู้ใช้มาอ่านหรือลบไฟล์ผ่าน API. Test ทุกตัวสร้าง `TestClient` ด้วย `base_url="http://127.0.0.1"`.

Source: spoil D15
