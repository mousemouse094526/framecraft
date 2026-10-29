# framecraft

Local video generator: a React UI calling a FastAPI backend that runs
OmniVoice, Whisper, and ffmpeg on your machine. Personal, non-commercial use
only — see [NOTICE.md](NOTICE.md).

Supported: Mac with Apple Silicon, and Windows with an NVIDIA card (Windows setup not yet tested on a real machine).

## ติดตั้งและใช้งาน (ทีละขั้น)

ไม่เคยใช้ terminal ก็ทำได้ ทำตามทีละข้อ. ติดตั้งครั้งเดียว (ข้อ 1–3), ใช้งานทุกครั้ง (ข้อ 4–6).

### Mac (Apple Silicon)

1. **ติดตั้ง Node.js** — เปิด https://nodejs.org กดดาวน์โหลดตัว LTS (เวอร์ชัน 22 ขึ้นไป) แล้วติดตั้งแบบกด Next ไปจนจบ
2. **เปิด Terminal ที่ folder ของ framecraft** — เปิดแอป Terminal (กด ⌘ Space พิมพ์ `Terminal` แล้วกด Enter) พิมพ์ `cd ` (มีเว้นวรรคท้าย) แล้วลาก folder `framecraft` จาก Finder มาวางในหน้าต่าง Terminal แล้วกด Enter
3. **ติดตั้ง** — พิมพ์คำสั่งนี้แล้วกด Enter:

   ```sh
   ./setup.sh
   ```

   ครั้งแรกใช้เวลานาน (โหลดประมาณ 5 GB) ต้องต่อ internet และมีที่ว่างอย่างน้อย 15 GB. เสร็จแล้วจะเห็นรายการ 11 ข้อ และ "ขั้นต่อไป: รัน npm run dev". รันซ้ำได้เสมอ ถ้าเน็ตหลุดกลางทางให้รันใหม่ มันจะทำต่อจากเดิม
4. **เปิดโปรแกรม** — ใน Terminal เดิม (ที่อยู่ใน folder framecraft) พิมพ์:

   ```sh
   npm run dev
   ```

   รอจนเห็นบรรทัด `[api] ... Uvicorn running` และ `[web] ... Local: http://localhost:5173/`
5. **เปิดหน้าเว็บ** — เปิด browser ไปที่ http://localhost:5173 จะเห็นหน้า Setup status. ถ้าครบจะขึ้น "พร้อมใช้งาน" 11/11
6. **ปิดโปรแกรม** — กลับไปที่ Terminal แล้วกด `Control` + `C`. ปิด Terminal ได้เลย

ครั้งต่อไปทำแค่ข้อ 2, 4, 5 และ 6.

### Windows (การ์ด NVIDIA)

1. **ติดตั้ง Node.js** — เหมือน Mac ข้อ 1
2. **ติดตั้ง** — เปิด folder `framecraft` แล้วดับเบิลคลิก `setup.cmd`. รอจนเห็นรายการ 11 ข้อ แล้วกดปุ่มใดก็ได้เพื่อปิดหน้าต่าง. ใช้ได้แม้ PowerShell ตั้ง execution policy เป็น `Restricted`
3. **เปิด Command Prompt ที่ folder ของ framecraft** — ใน File Explorer ที่เปิด folder `framecraft` อยู่ คลิกที่ช่อง address ด้านบน พิมพ์ `cmd` แล้วกด Enter
4. **เปิดโปรแกรม** — พิมพ์ `npm run dev` แล้วกด Enter
5. **เปิดหน้าเว็บ** — เหมือน Mac ข้อ 5
6. **ปิดโปรแกรม** — กด `Ctrl` + `C` ในหน้าต่าง Command Prompt (ถ้าถาม `Terminate batch job (Y/N)?` พิมพ์ `Y` แล้ว Enter)

ครั้งต่อไปทำแค่ข้อ 3–6. ถ้ารันใน PowerShell ให้พิมพ์ `.\setup.cmd` แทน `setup.cmd`.

Windows ยังไม่ได้ทดสอบบนเครื่องจริง.

### ถ้ามีปัญหา

- **`ยังไม่ได้ติดตั้ง: รัน ./setup.sh ก่อน`** — ยังไม่ได้ทำขั้นติดตั้ง ให้รัน `./setup.sh` (Windows: `setup.cmd`) ก่อน
- **`Node.js 22+ required`** หรือ **`npm: command not found`** — ยังไม่ได้ติดตั้ง Node.js หรือติดตั้งแล้วแต่ยังไม่ได้เปิด Terminal ใหม่: ปิดแล้วเปิด Terminal ใหม่
- **หน้าเว็บขึ้น Backend offline** — ดูใน Terminal ว่าบรรทัด `[api]` มี error ไหม. ถ้าเห็น `address already in use` แปลว่า port 8000 ถูกใช้อยู่ คือมี `npm run dev` อีกอันเปิดค้างอยู่ ให้ปิดอันนั้นก่อน
- **`ปิด npm run dev ก่อนรัน setup`** — กด `Control` + `C` ที่ Terminal ที่รัน `npm run dev` อยู่ แล้วรัน setup ใหม่
- **รายการไหนไม่ผ่าน** — หน้า Setup status บอกวิธีแก้ในแต่ละแถว ส่วนใหญ่คือรัน setup ซ้ำ แล้วกด Refresh

### สิ่งที่ setup ติดตั้ง

[uv](https://docs.astral.sh/uv/) (ถ้ายังไม่มี), Python 3.12, package ทั้งหมด, ffmpeg, yt-dlp กับ Deno (ใช้โหลดคลิป YouTube), โมเดลสองตัว และ npm package ของหน้าเว็บ — ทั้งหมดอยู่ใน folder นี้ (ประมาณ 10 GB). `npm run dev` ไม่ติดตั้งอะไร: มัน start backend ที่ `127.0.0.1:8000` (บรรทัด `[api]`) และหน้าเว็บ (บรรทัด `[web]`). `GET /api/setup/status` คืนรายการเดียวกันเป็น JSON.

### คลิปที่โหลดจาก YouTube

- เปิด tab **สปอย** ด้านบน วางลิงก์คลิป YouTube แล้วกด **โหลด**. คลิปที่โหลดแล้วอยู่ในรายการ "คลิปที่โหลดมา" ใต้ช่องลิงก์: กดแถวเพื่อเล่น, กดถังขยะเพื่อลบ
- คลิปที่โหลดเก็บใน `media/temp/` ของ folder นี้ (`{id}.mp4`, thumbnail และ `{id}.json`) และอยู่จนกดลบเอง. ไม่เข้า git
- ลบทั้งหมดด้วยมือได้: ปิด `npm run dev` ก่อน แล้วลบ folder `media/temp/`
- ถอดบทพูด: backend ถอดคำพูดทั้งคลิปด้วย Whisper large-v3-turbo บน GPU ของเครื่อง (`POST /api/spoil/transcriptions` กับ `{"clip_id": "..."}`; ดู % ที่ `GET /api/spoil/transcriptions/current`). หนังยาว 1 ชั่วโมงครึ่งใช้ราว 20 นาทีบน Mac. ผลเก็บคู่คลิปเป็น `media/temp/{id}.transcript.json` อยู่ข้าม restart, โหลดเป็นไฟล์ได้ที่ `/api/spoil/clips/{id}/transcript.txt` และ `.srt`, และหายไปพร้อมคลิปเมื่อกดลบ
- ช่วงที่มีแต่ดนตรีหรือเสียงเงียบ Whisper อาจแต่งบรรทัดที่ไม่มีใครพูด (เช่น "THE END", "Thank you.") — ลบเองตอนเอาไปใช้
- ถ้าโหลดไม่ได้ทุกคลิป (YouTube เปลี่ยน) ให้อัปเดต yt-dlp แล้วรัน setup ใหม่:

  ```sh
  uv lock --upgrade-package yt-dlp
  ./setup.sh
  ```

  (Windows: `uv lock --upgrade-package yt-dlp` แล้ว `setup.cmd`)
- Windows ลบคลิปที่ player ยังเปิดอยู่ไม่ได้: หน้าเว็บบอก "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่" ใต้แถวนั้น ปิด player แล้วลองอีกครั้ง
- API อยู่ใต้ `/api/spoil` เช่น `POST /api/spoil/downloads` กับ `{"url": "..."}` แล้ว poll `GET /api/spoil/downloads/current`; รายการคือ `GET /api/spoil/clips`

## Tests

```sh
uv run pytest
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Moving to another machine

Copy the whole folder to another machine with the same OS and run
`./setup.sh` (Windows: `setup.cmd`) again. The models in `models/` are reused; `.venv` is rebuilt,
which needs internet.

## Uninstall

1. Delete the project folder — `.venv/`, `models/`, and `node_modules/` are
   all inside it.
2. Remove uv's cache and Python: `uv cache clean` and `uv python uninstall 3.12`.
3. Remove uv itself: follow
   [uv's uninstall guide](https://docs.astral.sh/uv/getting-started/installation/#uninstallation).
