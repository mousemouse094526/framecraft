# Flow: audio-player

3 diagrams, read in this order:
1. สถานะของ `PlayButton` หนึ่งปุ่ม
2. กดปุ่ม B ขณะปุ่ม A เล่นอยู่
3. ปุ่มผสมเสียง (`useListen`)

All diagrams use the same names as [spec.md](spec.md).

## 1. สถานะของปุ่มหนึ่งปุ่ม

```mermaid
stateDiagram-v2
    [*] --> Ready
    Ready --> Playing: กด
    Playing --> Paused: กด
    Paused --> Playing: กด (เล่นต่อ)
    Playing --> Ready: ended หรือ error
    Playing --> Ready: เสียงอื่นเริ่ม
    Paused --> Ready: เสียงอื่นเริ่ม
    Playing --> Paused: media อื่นเล่น
    Playing --> Ready: ปุ่ม unmount, src เปลี่ยน หรือกดไม่ได้
    Paused --> Ready: ปุ่ม unmount, src เปลี่ยน หรือกดไม่ได้
```

**ปุ่มอยู่สถานะไหนและกดแล้วไปไหน**
- Ready หลังเสียงอื่นเริ่มลืมตำแหน่ง: กดแล้วเริ่มจากต้น (D2).
- media อื่น (วิดีโอ เพลงต้นฉบับ) ทำให้หยุดชั่วคราว ไม่ลืมตำแหน่ง (D8).
- `play()` reject ในรอบปัจจุบันกลับ Ready โดยไม่มีข้อความ; `AbortError` และรอบเก่าไม่มีผล (D9, D13).
- Playing เริ่มทันทีที่เรียก `play()` ไม่รอ Promise; กดระหว่างนั้น = หยุดชั่วคราว (D13).

## 2. กดปุ่ม B ขณะ A เล่นอยู่

```mermaid
sequenceDiagram
    actor U as เจ้าของ
    participant B as PlayButton B
    participant P as เครื่องเล่นเสียง
    participant E as audio element
    participant M as media อื่นในหน้า
    U->>B: กด
    B->>P: toggle(B, srcB)
    P->>E: pause() ของ A
    P->>E: src = srcB, currentTime = 0
    P->>M: pause() ที่เล่นอยู่และไม่ muted
    P->>E: play()
    P-->>B: status playing
    E-->>P: timeupdate
    P-->>B: position, duration
    M-->>P: play event (capture) เมื่อวิดีโอเริ่มเอง
    P->>E: pause()
    P-->>B: status paused
```

**ทำไมไม่มีวันเล่นซ้อน**
- `audio` element มีตัวเดียว: เปลี่ยน `src` ทำให้เสียงเดิมหายแน่นอน (D1).
- `pause()` ของ A ถูกเรียกก่อน `play()` ของ B; seam 1 พิสูจน์ลำดับนี้ (D12).
- element ของเครื่องเล่นไม่อยู่ใน document: เครื่องเล่น pause media อื่นเองใน `toggle`; capture listener มีไว้ให้ media อื่นทำให้เครื่องเล่นหยุด (D8, D13).
- วิดีโอเริ่มเล่นก็หยุดวิดีโออื่นที่เล่นอยู่ด้วยกฎเดียวกัน (D13).

## 3. ปุ่มผสมเสียง

```mermaid
flowchart TD
    Press([กด ฟังจังหวะ หรือ ฟัง reel]) --> Same{มี wav ของปุ่มนี้ และไม่มี unsaved?}
    Same -- ใช่ --> Toggle[toggle: หยุดชั่วคราวหรือเล่นต่อ]
    Same -- ไม่ --> Mixing[กำลังผสมเสียง… กดไม่ได้]
    Mixing --> Request[request: บันทึกก่อน แล้ว POST listen]
    Request --> Reply{ผล}
    Reply -- wav --> Keep[revoke URL เก่า เก็บ url]
    Keep --> Play[toggle เล่นจากต้น]
    Reply -- null --> Idle([พร้อมเล่น ผู้เรียกบอกเหตุ])
    Reply -- ปฏิเสธหรือ offline --> Refused([RefusedAlert])
```

**ผสมเมื่อไรและเมื่อไรแค่ pause**
- แก้ค่าขณะฟัง (`unsaved`) → `release` ปุ่มกลับพร้อมเล่น และทิ้ง wav (D14).
- แกะใหม่ของ reel cover เปิดฟอร์มใหม่ จึงไม่มี wav เก่าค้าง (D14).
- request เดิมไม่เปลี่ยน: บันทึกก่อน แล้ว `POST …/listen` (D11, video-gen D29).
