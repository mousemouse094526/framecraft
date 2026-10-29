# Legal check: setup-status

**Jurisdiction:** Thailand — checked 2026-10-28

- ผู้ใช้ติดตั้งและใช้บนเครื่องตัวเอง ไม่แจกจ่ายให้คนอื่น
- ผลงานใช้ส่วนตัวหรือทดลอง ไม่หารายได้ (D11)
- ไม่มีการเก็บข้อมูลส่วนบุคคลของใคร จึงไม่เข้า PDPA

## 1. ดาวน์โหลดและใช้โมเดล OmniVoice (D6, D11)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ใช้แบบไม่หารายได้เท่านั้น ไม่ใช้เพื่อประโยชน์ทางการค้าหรือรับค่าตอบแทน [1][2]
- มี attribution: ชื่อผู้สร้าง, ลิงก์ license CC BY-NC 4.0 และลิงก์โมเดล ใน `NOTICE.md` และหน้าสถานะ [2]
- ถ้าจะเผยแพร่เสียงหรือวิดีโอที่สร้าง ให้ใส่เครดิตโมเดลด้วย [2]

## 2. ดาวน์โหลดและใช้โมเดล Whisper large v3 turbo (D6)

**Verdict: ALLOWED** [3]

## 3. ใช้ ffmpeg binary จาก imageio-ffmpeg ในเครื่องตัวเอง (D4)

**Verdict: ALLOWED** [4][5]

## Summary
| # | Item | Verdict | Required to be allowed |
|---|------|---------|------------------------|
| 1 | ดาวน์โหลดและใช้โมเดล OmniVoice | CONDITIONAL | ใช้แบบไม่หารายได้ · attribution ใน `NOTICE.md` และหน้าสถานะ · ใส่เครดิตเมื่อเผยแพร่ผลงาน |
| 2 | ดาวน์โหลดและใช้โมเดล Whisper large v3 turbo | ALLOWED | — |
| 3 | ใช้ ffmpeg จาก imageio-ffmpeg ในเครื่องตัวเอง | ALLOWED | — |

ข้อ 3: เงื่อนไขของ LGPL และ GPL ใน checklist ของ FFmpeg ผูกกับการแจกจ่าย binary ให้คนอื่น [5]. ถ้าวันหนึ่งจะแจก app ที่รวม ffmpeg ต้องเช็คใหม่.

## References
1. OmniVoice model card (license CC-BY-NC) — https://huggingface.co/k2-fsa/OmniVoice (accessed 2026-10-28)
2. Creative Commons Attribution-NonCommercial 4.0 — https://creativecommons.org/licenses/by-nc/4.0/ (accessed 2026-10-28)
3. Whisper large v3 turbo model card (license MIT) — https://huggingface.co/openai/whisper-large-v3-turbo (accessed 2026-10-28)
4. imageio-ffmpeg — https://github.com/imageio/imageio-ffmpeg (accessed 2026-10-28)
5. FFmpeg License and Legal Considerations — https://ffmpeg.org/legal.html (accessed 2026-10-28)

*บันทึกด้าน compliance สำหรับวิศวกรรม ไม่ใช่คำแนะนำทางกฎหมาย*
