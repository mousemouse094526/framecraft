# ffmpeg มาจาก imageio-ffmpeg เท่านั้น

ffmpeg ที่ project ใช้มาจาก package `imageio-ffmpeg` ใน venv และทุกจุดหา path ด้วย `imageio_ffmpeg.get_ffmpeg_exe()` ไม่พึ่ง PATH ของเครื่อง. ไม่ใช้ Homebrew เพราะใช้บน Windows ไม่ได้และไม่ portable. ชุดนี้ไม่มี ffprobe: ใครต้องการข้อมูลสื่อต้องอ่านจาก `ffmpeg` หรือ Python.

Source: setup-status D4

Links: [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
