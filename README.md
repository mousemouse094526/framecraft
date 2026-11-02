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

   ครั้งแรกใช้เวลานาน (โหลดประมาณ 11 GB บน Mac, 5 GB บน Windows) ต้องต่อ internet และมีที่ว่างอย่างน้อย 20 GB (Windows 15 GB). เสร็จแล้วจะเห็นรายการ 13 ข้อ และ "ขั้นต่อไป: รัน npm run dev". รันซ้ำได้เสมอ ถ้าเน็ตหลุดกลางทางให้รันใหม่ มันจะทำต่อจากเดิม
4. **เปิดโปรแกรม** — ใน Terminal เดิม (ที่อยู่ใน folder framecraft) พิมพ์:

   ```sh
   npm run dev
   ```

   รอจนเห็นบรรทัด `[api] ... Uvicorn running` และ `[web] ... Local: http://localhost:5173/`
5. **เปิดหน้าเว็บ** — เปิด browser ไปที่ http://localhost:5173 จะเห็น tab **ติดตั้ง** (Setup status). ถ้าครบจะขึ้น "พร้อมใช้งาน" 11/11
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
- **รายการไหนไม่ผ่าน** — tab ติดตั้งบอกวิธีแก้ในแต่ละแถว ส่วนใหญ่คือรัน setup ซ้ำ แล้วกด Refresh

### สิ่งที่ setup ติดตั้ง

[uv](https://docs.astral.sh/uv/) (ถ้ายังไม่มี), Python 3.12, package ทั้งหมด, ffmpeg, yt-dlp กับ Deno (ใช้โหลดคลิป YouTube), โมเดลสองตัว และ npm package ของหน้าเว็บ — ทั้งหมดอยู่ใน folder นี้ (ประมาณ 10 GB). `npm run dev` ไม่ติดตั้งอะไร: มัน start backend ที่ `127.0.0.1:8000` (บรรทัด `[api]`) และหน้าเว็บ (บรรทัด `[web]`). `GET /api/setup/status` คืนรายการเดียวกันเป็น JSON.

### คลิปที่โหลดจาก YouTube

- แอปมี 3 tab ด้านบน: **ติดตั้ง**, **คลิป** (โหลด ถอดบทพูด แก้บทพูด บรรยายฉาก) และ **สปอย**
- เปิด tab **คลิป** วางลิงก์คลิป YouTube แล้วกด **โหลด**. คลิปที่โหลดแล้วอยู่ในรายการ "คลิปที่โหลดมา" ใต้ช่องลิงก์: กดแถวเพื่อเล่น, กดถังขยะเพื่อลบ
- คลิปที่โหลดเก็บใน `media/temp/` ของ folder นี้ (`{id}.mp4`, thumbnail และ `{id}.json`) และอยู่จนกดลบเอง. ไม่เข้า git
- ลบทั้งหมดด้วยมือได้: ปิด `npm run dev` ก่อน แล้วลบ folder `media/temp/`
- ถอดบทพูด: backend ถอดคำพูดทั้งคลิปด้วย Whisper large-v3-turbo บน GPU ของเครื่อง (`POST /api/spoil/transcriptions` กับ `{"clip_id": "..."}`; ดู % ที่ `GET /api/spoil/transcriptions/current`). หนังยาว 1 ชั่วโมงครึ่งใช้ราว 20 นาทีบน Mac. ผลเก็บคู่คลิปเป็น `media/temp/{id}.transcript.json` อยู่ข้าม restart, โหลดเป็นไฟล์ได้ที่ `/api/spoil/clips/{id}/transcript.txt` และ `.srt`, และหายไปพร้อมคลิปเมื่อกดลบ
- ช่วงที่มีแต่ดนตรีหรือเสียงเงียบ Whisper อาจแต่งบรรทัดที่ไม่มีใครพูด (เช่น "THE END", "Thank you.") — ลบเองตอนเอาไปใช้
- แก้บทพูดที่ถอดผิดได้ทีละบรรทัด: ชี้บรรทัดแล้วกด **แก้** (`PATCH /api/spoil/clips/{id}/transcript/lines/{n}` กับ `{"text": "..."}`). เวลาและจำนวนบรรทัดไม่เปลี่ยน; `.txt` และ `.srt` ใช้ข้อความที่แก้. ถอดใหม่จะลบบรรทัดที่แก้ไว้ หน้าเว็บจึงถามก่อน
- บรรยายฉาก (Mac เท่านั้น): คลิปที่ถอดแล้วมีปุ่ม **บรรยายฉาก**. backend หาจุดตัดภาพด้วย ffmpeg แบ่งเป็น Shot (ไม่เกิน 10 วินาที) แล้วให้ Qwen3.5 9B บรรยายเฟรมกลางของทุก Shot (`POST /api/spoil-maker/describes`; ดู % ที่ `GET /api/spoil-maker/describes/current`). ผลอยู่ใน `media/temp/shots/{id}/` (`shots.json` และภาพเล็ก `{n}.jpg`) และหายไปพร้อมคลิป. บรรยายฉากใหม่ ผลเดิมอยู่จนกว่างานใหม่เสร็จ
- งานที่ใช้ GPU (ถอดบทพูด, บรรยายฉาก, ร่างบท, สร้างเสียง) รันได้ทีละงาน: ปุ่มของอีกงานกดไม่ได้และบอกว่ารองานไหน. โหลดคลิปทำพร้อมกันได้
- ถ้าโหลดไม่ได้ทุกคลิป (YouTube เปลี่ยน) ให้อัปเดต yt-dlp แล้วรัน setup ใหม่:

  ```sh
  uv lock --upgrade-package yt-dlp
  ./setup.sh
  ```

  (Windows: `uv lock --upgrade-package yt-dlp` แล้ว `setup.cmd`)
- Windows ลบคลิปที่ player ยังเปิดอยู่ไม่ได้: หน้าเว็บบอก "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่" ใต้แถวนั้น ปิด player แล้วลองอีกครั้ง
- API อยู่ใต้ `/api/spoil` เช่น `POST /api/spoil/downloads` กับ `{"url": "..."}` แล้ว poll `GET /api/spoil/downloads/current`; รายการคือ `GET /api/spoil/clips`

### เสียงบรรยาย (tab สปอย)

- เปิด `#/spoil/voices`: เลือกเพศ วัย ระดับเสียง และความเร็ว 0.8–1.2 แล้วกด **สุ่ม** (OmniVoice สร้างประโยคตัวอย่าง ราว 10 วินาทีบน M2). ฟังแล้วชอบก็ตั้งชื่อแล้ว **บันทึก** เป็น Saved voice; ไม่ชอบก็กดสุ่มใหม่ (ทับเสียงที่ยังไม่บันทึก)
- Saved voice เก็บใน `media/spoil-maker/voices/` (`{id}.json`, `.pt`, `.wav`) อยู่ข้าม restart; เปลี่ยนชื่อและลบได้ แต่แก้ความเร็วไม่ได้: อยากได้ความเร็วอื่นให้ออกแบบใหม่. เสียงที่สุ่มแล้วยังไม่บันทึกหายเมื่อ restart
- ตัวเลขในประโยคถูกอ่านเป็นคำไทยก่อนส่งให้ OmniVoice (`1968` → หนึ่งพันเก้าร้อยหกสิบแปด) แต่บทและซับยังเป็นตัวเลข
- เปลี่ยนชื่อได้เสมอ แต่ลบเสียงที่ Spoil draft ใช้อยู่ไม่ได้ ("เสียงนี้ใช้อยู่ใน Spoil draft")

### ร่างบทและตรวจแก้ (tab สปอย, Mac เท่านั้น)

- ขั้น 1 **เลือกคลิป** (`#/spoil`): ติ๊กคลิปที่ถอดและบรรยายฉากแล้ว (หลายคลิปได้ เรียงตอนด้วยลูกศร), เลือกสไตล์ layout ความยาว 30–180 วินาที และเสียงบรรยาย. แถบ Transcript บอก token รวม: เกิน 32,000 ร่างไม่ได้ ให้เอาตอนออก. กด **ร่างบท**: Qwen3.5 9B เขียนบทไทยแล้วเลือก 2 Shot ต่อประโยค (`POST /api/spoil-maker/draft-jobs`; ดูที่ `GET /api/spoil-maker/draft-jobs/current`) เสร็จแล้วเปิดขั้น 2 เอง
- ขั้น 2 **ตรวจแก้บท** (`#/spoil/review`): แก้ hook หรือชื่อตอน และข้อความของแต่ละประโยค (บันทึกเองเมื่อหยุดพิมพ์หรือออกจากช่อง), แทรกหรือลบประโยค, กดภาพ Shot เพื่อเลือกภาพจากช่วง ±30 วินาทีรอบบรรทัดที่อ้างหรือจากทั้งคลิป, หรือกด **เลือก Shot ใหม่** ให้ AI เลือกจากข้อความที่แก้แล้ว
- งานที่ร่างไว้ (Spoil draft) มีได้ทีละหนึ่ง เก็บใน `media/spoil-maker/draft.json` อยู่ข้าม restart; ร่างใหม่ทับของเดิมหลังกดยืนยัน. ถอดใหม่ บรรยายฉากใหม่ หรือลบคลิปที่อยู่ใน draft จะลบ draft ด้วย หน้าเว็บจึงเตือนก่อน
- ค่าที่แอปจำไว้ (เสียงที่ใช้ล่าสุด ระดับเสียงต้นฉบับ) อยู่ใน `media/spoil-maker/settings.json`

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
