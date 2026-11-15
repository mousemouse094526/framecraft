# Progress: drum-cover

**Now:** plan approved (D1–D21, ADR 0050–0053), tickets 01–02 cut; กำลังทำ 01

**Next:**

```
/warroom-build drum-cover 01
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | reel cover จากเพลงที่แกะ: ตั้งช่วง ข้อความ เสียง ฟัง render | ready |
| 02 | ภาพพื้นหลังของ reel และหน้าเพลงบอกเมื่อกลองเข้าช้า | ready |

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01, 02 | design: หน้าเพลง — ส่วนที่เพิ่ม, หน้า reel | ไม่รอ Figma: สร้างตาม `ui-prompt.md` กับ design system เดิม (D14, แบบ drum-notes D28) | closed |

## Log

### Planning — 2026-11-15

- Phase 1–2.5 (session ก่อน): `spec`, `decisions` D1–D16, `flow`, `legal` (commit `6742a45`)
- Red team (5 subagent `opus`): 3 BLOCKER + 22 CONCERN → แก้ docs 14, ตัดสินใหม่ D17–D21, ปัด 3 (Skeptic: ตัดภาพพื้นหลัง — brief ของเจ้าของขอ; ตัด D9 — user story 7 ของเจ้าของ; ตัดตัวนับ/BAR — D3 เลือกแล้ว เจ้าของตัดสินบน Yellow ตาม D15)
  - BLOCKER Skeptic (แก้ video-gen หลายไฟล์) → D17: ตัด prefactor `captions` และ `_command`, เหลือ `assemble` + ย้ายของรับภาพ ที่ผลเดิมไม่เปลี่ยน
  - BLOCKER Builder (`amix` index ผิด, `-map` ทำภาพหาย) + Breaker (clip, wav header จาก pipe) → D17: ผสม backing ใน numpy ทางเดียว
- ADR sweep (The Successor): 0050 แทน 0045 (backing ใน reel), 0051 ต่อ 0041 (Timeline จากเวลาจริง), 0052 (cover เป็นของ Song), 0053 ต่อ 0046 (ไม่หารายได้); 0028 เพิ่ม route ภาพของ cover; ปัด D (ทิศ import — อยู่ใน 0052) และ E (stack video-gen — D17 ลด coupling)
- Gate: Approve (auto mode, Recommended); Open Questions 2 ข้อ non-blocking (legal 1–2, D16)
- `ui-prompt.md` เขียนแล้ว เป็นสเปกจอแทน Figma (D14)
