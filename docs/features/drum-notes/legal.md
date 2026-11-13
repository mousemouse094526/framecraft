# Legal check: drum-notes

**Jurisdiction:** Thailand — checked 2026-11-14

- แอปทำงานในเครื่องผู้ใช้คนเดียว ไม่มี server ไม่เก็บข้อมูลส่วนบุคคลของใคร: ไม่มีเรื่อง PDPA ให้ตรวจ
- โปรเจกต์ใช้แบบไม่หารายได้ (ADR-0017); การหารายได้เป็น change request ที่ต้องตรวจข้อ 3 และ 5 ใหม่
- เสียงเพลงที่เอาเข้าอยู่ในเครื่องผู้ใช้ ใช้วิเคราะห์และฟังในแอปเท่านั้น ไม่เข้าคลิปที่ render (D15)
- ข้อยกเว้นเรื่องการเผยแพร่คลิปสอนกลองตรวจแล้วใน [video-gen legal.md](../video-gen/legal.md) ข้อ 2; ข้อ 5 ด้านล่างอ้างและเพิ่มเฉพาะส่วนที่ feature นี้เปลี่ยน
- การโหลดคลิปจากเว็บตรวจแล้วใน [spoil legal.md](../spoil/legal.md) (spoil D13, D53); ข้อ 1 อ้างและเพิ่มเฉพาะส่วนที่ต่าง (เสียงอย่างเดียว เพื่อวิเคราะห์)

## 1. โหลดเสียงเพลงจากลิงก์ YouTube หรือเว็บอื่นมาเก็บในเครื่องเพื่อแกะโน้ต (D4)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ไฟล์เสียงอยู่ในเครื่องผู้ใช้เพื่อการศึกษาส่วนกลองของเพลงโดยไม่หากำไร: การทำซ้ำเพื่อวิจัยหรือศึกษางานนั้นที่ไม่ใช่เพื่อหากำไร เป็นข้อยกเว้นตามมาตรา 32 (1) [1]
- ไม่เผยแพร่ ไม่แจกจ่าย และไม่ใส่ไฟล์เสียงนี้ในคลิปที่ render (D15) [1]
- ลบไฟล์ได้จากหน้ารายการเพลง และข้อความข้างกล่องลิงก์บอกว่าใช้เพื่อแกะโน้ตเท่านั้น (spec › Design)
- โหลดเฉพาะเว็บที่ yt-dlp มีตัวโหลดเฉพาะ ไม่ใช้ cookies หรือ login (ADR-0029)

ข้อกำหนดการใช้งานของ YouTube ห้ามดาวน์โหลดเนื้อหาเว้นแต่มีปุ่มหรือลิงก์ให้ดาวน์โหลด [2]: ความเสี่ยงด้าน ToS เป็นข้อเดียวกับ Temp clip ของ tab คลิป ซึ่งรับไว้แล้ว (spoil D13, D53) และ D16 รับต่อ.

UNVERIFIED — from model knowledge, verify before relying: ยังไม่พบคำพิพากษาไทยที่ชี้ว่าการดาวน์โหลดเพลงจาก YouTube มาฟังหรือวิเคราะห์ส่วนตัวเข้าข้อยกเว้นมาตรา 32 (1) หรือเป็นการละเมิดต่อเจ้าของสิ่งบันทึกเสียง.

## 2. เอาไฟล์เสียงหรือไฟล์ MIDI ของผู้ใช้เข้ามาแกะหรืออ่านโน้ต (D4, D10)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ไฟล์เป็นของผู้ใช้หรือได้มาโดยชอบ (เพลงที่ซื้อ ไฟล์ที่ผู้ใช้ทำเอง): ทางเดียวกับการเอาไฟล์ mp4 เข้า Temp clip (spoil D53) [1]
- ไฟล์ MIDI ที่คนอื่นเรียบเรียง (transcription) เป็นงานดัดแปลงที่มีลิขสิทธิ์ของผู้เรียบเรียง: ใช้เมื่อผู้เรียบเรียงอนุญาตหรือเป็นไฟล์ของผู้ใช้เอง [1]
- การอ่านไฟล์เกิดในเครื่อง ไม่ส่งไฟล์ออก (ADR-0003)

## 3. ใช้โมเดล ADTOF Frame_RNN (CC BY-NC-SA 4.0) แกะโน้ตกลองในเครื่อง (D6, D7, D16)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ใช้แบบไม่หารายได้เท่านั้น ทั้งแอปและคลิปที่โน้ตมาจากโมเดลนี้: NonCommercial ห้ามใช้เพื่อประโยชน์ทางการค้า [3]; สอดคล้องกับ ADR-0017 อยู่แล้ว
- ให้เครดิตผู้สร้าง (Zehren, Alunno, Bientinesi, ADTOF) และผู้แปลงเป็น ONNX พร้อมชื่อ license และลิงก์ ใน `NOTICE.md` และหน้าสถานะ: Attribution [3]; ข้อความเครดิตตาม `NOTICE.md` ของ model card [4]
- ไม่แก้หรือ fine-tune ไฟล์โมเดล; Setup script โหลดไฟล์จาก Hugging Face เข้าเครื่องผู้ใช้เอง ไม่แจกจ่ายในตัวแอป (ADR-0004): ShareAlike บังคับเฉพาะ adaptation ที่เผยแพร่ [3]
- ก่อนหารายได้: เปลี่ยนตัวแกะกลองเป็นโมเดลที่ license อนุญาต หรือตัดทางเสียงออกเหลือ MIDI (D16)

repo ต้นฉบับประกาศ license CC BY-NC-SA 4.0 ครอบเนื้อหาทั้ง repo รวมน้ำหนักโมเดล [5]; model card ของไฟล์ ONNX ใช้ license เดียวกันและระบุว่าแปลงรูปแบบโดยไม่แก้น้ำหนัก [4].

UNVERIFIED — from model knowledge, verify before relying: CC BY-NC-SA ไม่ได้เขียนถึง "ผลลัพธ์" ของโมเดล (โน้ตที่แกะได้) ว่าเป็น adaptation หรือไม่; ความเห็นทั่วไปคือ output ไม่ใช่ adaptation ของไฟล์โมเดล แต่ยังไม่มีคำตัดสิน. D16 รับความเสี่ยงนี้เพราะใช้ส่วนตัวและเปลี่ยนโมเดลได้.

## 4. ใช้ Beat This! (MIT), Basic Pitch (Apache-2.0) และ onnxruntime (MIT) ในแอป (D7, D14)

**Verdict: ALLOWED** [6][7][8][9]

## 5. เผยแพร่คลิปสอนกลองที่โน้ตมาจากการแกะเพลงที่มีลิขสิทธิ์ (D11, D12, D15)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- ทุกข้อของ [video-gen legal.md](../video-gen/legal.md) ข้อ 2: ช่วงสั้น (1–4 ห้อง), เป็นการสอนด้วยคำของผู้ใช้, ระบุชื่อเพลงและศิลปิน, ไม่ใช้โลโก้วง, ตรวจใหม่ก่อนหารายได้ [1][10]
- ไม่มีเสียงบันทึกของเพลงต้นฉบับในคลิป (D15): เสียงในคลิปเป็นกลองจาก sample CC0 เท่านั้น (video-gen D7, ADR-0039) [1]
- บทเรียนที่สร้างมีหัวเรื่องเป็นชื่อเพลงและบรรทัดรองเป็นศิลปิน/ช่องตั้งต้น (D12) ซึ่งเป็นการรับรู้ความเป็นเจ้าของตามมาตรา 32 วรรคหนึ่ง และผู้ใช้ไม่ควรลบออก [1]

ความไม่แน่นอนว่าโน้ตกลองไม่กี่ห้องเป็น "สาระสำคัญ" ของดนตรีกรรมหรือไม่ อยู่ใน video-gen legal ข้อ 2 (UNVERIFIED) และรับไว้แล้วใน video-gen D25; D16 รับต่อ.

## 6. โหมดทำนอง: เผยแพร่คลิปที่จังหวะของทำนองเพลงอื่นถูกตีบน snare (D14)

**Verdict: CONDITIONAL**

**Required to be allowed:**
- เงื่อนไขทุกข้อของข้อ 5 [1]
- คลิปไม่มีระดับเสียงของทำนอง (มีแค่จังหวะบนกลอง) และไม่มีคำร้อง: ส่วนที่ทำซ้ำคือจังหวะของทำนอง ไม่ใช่ทำนอง [1]

UNVERIFIED — from model knowledge, verify before relying: ไม่พบแหล่งไทยที่ชี้ว่าจังหวะของทำนอง (rhythm) โดยไม่มีระดับเสียงเป็นสาระสำคัญของดนตรีกรรมหรือไม่. D16 รับความเสี่ยงต่อจากข้อ 5.

## Summary
| # | Item | Verdict | Required to be allowed |
|---|------|---------|------------------------|
| 1 | โหลดเสียงเพลงจากลิงก์มาเก็บในเครื่องเพื่อแกะโน้ต | CONDITIONAL (UNVERIFIED ว่าดาวน์โหลดเพื่อศึกษาส่วนตัวเข้ามาตรา 32 (1)) | ศึกษาส่วนตัว ไม่หากำไร · ไม่เผยแพร่และไม่เข้าคลิป · ลบได้และบอกผู้ใช้ · เฉพาะเว็บที่มีตัวโหลดเฉพาะ ไม่ใช้ cookies |
| 2 | เอาไฟล์เสียงหรือ MIDI ของผู้ใช้เข้า | CONDITIONAL | ไฟล์ของผู้ใช้หรือได้มาโดยชอบ · MIDI ของคนอื่นต้องได้รับอนุญาต · อ่านในเครื่อง |
| 3 | ใช้โมเดล ADTOF (CC BY-NC-SA 4.0) แกะโน้ตกลอง | CONDITIONAL (UNVERIFIED ว่าโน้ตที่ได้เป็น adaptation ของโมเดลหรือไม่) | ไม่หารายได้ · เครดิตผู้สร้างและผู้แปลงใน `NOTICE.md` และหน้าสถานะ · ไม่แก้และไม่แจกจ่ายไฟล์โมเดล · เปลี่ยนโมเดลก่อนหารายได้ |
| 4 | ใช้ Beat This! (MIT), Basic Pitch (Apache-2.0), onnxruntime (MIT) | ALLOWED | — |
| 5 | เผยแพร่คลิปสอนที่โน้ตมาจากเพลงมีลิขสิทธิ์ | CONDITIONAL (UNVERIFIED ตาม video-gen legal ข้อ 2) | ทุกข้อของ video-gen legal ข้อ 2 · ไม่มีเสียงต้นฉบับในคลิป · คงชื่อเพลงและศิลปินในบทเรียน |
| 6 | โหมดทำนอง: จังหวะทำนองของเพลงอื่นบน snare | CONDITIONAL (UNVERIFIED ว่าจังหวะโดยไม่มีระดับเสียงเป็นสาระสำคัญ) | ทุกข้อของข้อ 5 · ไม่มีระดับเสียงและคำร้องในคลิป |

## References
1. พระราชบัญญัติลิขสิทธิ์ พ.ศ. 2537 มาตรา 4, 15, 27, 28, 32, 33 — https://th.wikisource.org/wiki/พระราชบัญญัติลิขสิทธิ์_พ.ศ._2537 (accessed 2026-11-13, ผ่าน video-gen legal.md)
2. YouTube Terms of Service › Permissions and Restrictions — https://www.youtube.com/t/terms (accessed 2026-11-14)
3. Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Legal Code — https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en (accessed 2026-11-14)
4. ADTOF Frame_RNN (ONNX) model card และ NOTICE.md — https://huggingface.co/thebluescreen/adtof-drums-onnx (accessed 2026-11-14)
5. MZehren/ADTOF README › License — https://github.com/MZehren/ADTOF (accessed 2026-11-14)
6. CPJKU/beat_this README › License (code and published model weights, MIT) — https://github.com/CPJKU/beat_this (accessed 2026-11-14)
7. Beat This! (ONNX) model card (MIT) — https://huggingface.co/thebluescreen/beat-this-onnx (accessed 2026-11-14)
8. spotify/basic-pitch README › License (Apache License 2.0) และ Andremi/audioweb-models (ไฟล์ ONNX, Apache-2.0) — https://github.com/spotify/basic-pitch และ https://huggingface.co/Andremi/audioweb-models (accessed 2026-11-14)
9. onnxruntime on PyPI (MIT License) — https://pypi.org/project/onnxruntime/ (accessed 2026-11-14)
10. LawLink (Legardy), Cover เพลงลง YouTube ต้องขออนุญาตเจ้าของลิขสิทธิ์หรือไม่ — https://legardy.com/free-qna/989 (accessed 2026-11-13, ผ่าน video-gen legal.md)

*บันทึกด้าน compliance สำหรับวิศวกรรม ไม่ใช่คำแนะนำทางกฎหมาย*
