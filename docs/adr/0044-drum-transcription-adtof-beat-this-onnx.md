# ตัวแกะโน้ตกลองคือ ADTOF Frame_RNN กับ Beat This! ที่แปลงเป็น ONNX โดยผู้อื่น pin บน Hugging Face รันด้วย onnxruntime

แกะกลองจากเสียงด้วย ADTOF Frame_RNN (5 ชนิด 100 เฟรม/วินาที) และหาจังหวะกับต้นห้องด้วย Beat This! ทั้งคู่เป็นไฟล์ ONNX ที่ผู้อื่นแปลงและ host บน Hugging Face (`thebluescreen/*`) ลงทะเบียนและ pin ตาม ADR-0004 รันบน `onnxruntime` CPU; โหมดทำนองใช้ Basic Pitch ONNX ทางเดียวกัน. เลือกแทน demucs (license น้ำหนักไม่ชัด), madmom และ ADTOF แบบ TensorFlow (ติดตั้งไม่ได้บน Python 3.12 กับ numpy 2) และการแปลงเอง (ต้องมี TensorFlow). เปลี่ยนโมเดลคือเปลี่ยน `onnx_runner` กับ peak picking ใน `score` และตรวจ license ใหม่.

Source: drum-notes D6, D7 · legal 3, 4

Links: [ADTOF Frame_RNN (ONNX)](https://huggingface.co/thebluescreen/adtof-drums-onnx), [Beat This! (ONNX)](https://huggingface.co/thebluescreen/beat-this-onnx)
