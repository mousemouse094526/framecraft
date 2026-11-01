# UI prompts: spoil-maker

ทั้ง 7 จอมีแบบใน Figma แล้ว (ลิงก์อยู่ใน spec.md › Design); บล็อกด้านล่างเก็บไว้ใช้ทำแบบใหม่: copy บล็อกไปวางใน design tool (Figma Make หรืออื่นๆ) แล้วเอาผลกลับมาด้วย `/warroom spoil-maker`.

| Screen | User stories | Prompt |
|---|---|---|
| แถว Temp clip ใน tab คลิป | 1, 3 | [below](#แถว-temp-clip-ใน-tab-คลิป) |
| Transcript ที่แก้ได้ใน tab คลิป | 13 | [below](#transcript-ที่แก้ได้ใน-tab-คลิป) |
| Saved voice | 2, 4 | [below](#saved-voice) |
| ตั้งค่าคลิปสปอย | 5, 6 | [below](#ตั้งค่าคลิปสปอย) |
| หน้าตรวจแก้ | 7, 8, 9, 10, 11 | [below](#หน้าตรวจแก้) |
| ตัวเลือก Shot | 8 | [below](#ตัวเลือก-shot) |
| ผล render | 11 | [below](#ผล-render) |

## แถว Temp clip ใน tab คลิป

เพิ่มปุ่มดูภาพ (Describe job) ในแถวคลิปเดิม และคำเตือนเมื่อการกระทำจะลบ Spoil draft (D16, D29, D45, D49).

```text
Design new states of the existing "Clip row" component in framecraft — a local desktop web app that downloads YouTube clips, transcribes them, and turns them into Thai vertical "spoiler" videos. One user, on their own Mac.

Context
- Platform: web app in a desktop browser; breakpoints: mobile 375, desktop 1440 (layout switches at 1024).
- Design system: use the existing Figma file "framecraft", section "framecraft — สปอย", and its ":: Token" page (Button, Field, Alert, Badge, icons). Tailwind v4 tokens: foreground #121110, muted bg #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff, destructive #dc2626, warning #b45309 on #fffbeb, success #15803d on #f0fdf4. Fonts: IBM Plex Sans Thai (body), IBM Plex Mono (numbers, timestamps), Manrope (buttons). Radius: rounded-lg for controls, rounded-xl/2xl for cards. Match the existing "Clip row" and "Download progress" components (screenshot attached).
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, labels on every input, touch targets ≥ 44px.

Who and why
- The user wants to have a downloaded, transcribed clip "described" shot by shot, so the AI can later pick matching images for each spoken sentence.
- This lives in the existing clip list on the "คลิป" tab, next to the existing "ถอดแล้ว" status. Describing a 96-minute film takes about 45 minutes.

Content (added to each clip row)
- Button "ดูภาพ" — starts describing this clip.
- While describing: a percent figure with a progress bar, and button "ยกเลิก".
- When finished: status "ดูภาพแล้ว" (a badge, next to "ถอดแล้ว").
- Disabled "ดูภาพ" while another GPU job runs, with the reason shown: "รอให้งาน{running}เสร็จก่อน", where {running} is one of "ถอดบทพูด", "ดูภาพ", "ร่างบท", "สร้างเสียง", "render".
- Clip in use by another job: "คลิปนี้กำลังถูกใช้ในงานอื่น".
- Pressing "ดูภาพ" on a clip already described: a confirm step before redoing it.
- Deleting, re-transcribing, or re-describing a clip that is part of the current Spoil draft: a warning confirm "คลิปนี้อยู่ใน Spoil draft: ทำต่อจะลบ Spoil draft", with a continue action and a cancel action.

States — one frame each, at every breakpoint
1. Default: a list of 4 clips with realistic Thai titles — one not transcribed, one transcribed with "ดูภาพ", one describing at 37%, one with "ถอดแล้ว" and "ดูภาพแล้ว".
2. Describing: progress bar with % and "ยกเลิก".
3. Disabled: "ดูภาพ" greyed out with "รอให้งานถอดบทพูดเสร็จก่อน".
4. Confirm redo on an already described clip.
5. Spoil draft warning: "คลิปนี้อยู่ใน Spoil draft: ทำต่อจะลบ Spoil draft".
6. Error: "งานหยุดกลางทาง" with a way to press "ดูภาพ" again.

Do not include
- Resuming a cancelled or crashed describe job.
- Any field, step, or feature not listed above.

Deliver: one frame per state per breakpoint, named "Clip row / {state} / {breakpoint}", as new variants of the existing "Clip row" component with auto layout.
```

## Saved voice

หน้าออกแบบเสียงบรรยาย ฟังก่อน บันทึก และจัดการรายการ (D32, D35, D43). ป้ายภาษาไทยของตัวเลือกเพศ วัย ระดับเสียง ยังไม่ได้ตัดสิน: prompt ให้ใช้ค่าภาษาอังกฤษตาม spec ไปก่อน.

```text
Design the "Saved voice" screen of framecraft — a local desktop web app that turns downloaded clips into Thai vertical "spoiler" videos with an AI Thai narrator. One user, on their own Mac.

Context
- Platform: web app in a desktop browser; breakpoints: mobile 375, desktop 1440 (layout switches at 1024). Route: a sub-page of the "สปอย" tab.
- Design system: use the existing Figma file "framecraft", section "framecraft — สปอย", and its ":: Token" page (Button, Field, Alert, Badge, icons). Tailwind v4 tokens: foreground #121110, muted bg #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff, destructive #dc2626, warning #b45309 on #fffbeb, success #15803d on #f0fdf4. Fonts: IBM Plex Sans Thai (body), IBM Plex Mono (numbers), Manrope (buttons). Radius: rounded-lg for controls, rounded-xl/2xl for cards. Match the existing "Transcript panel" card (screenshot attached).
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, labels on every input, touch targets ≥ 44px.

Who and why
- The user wants to design a narrator voice, hear it before keeping it, and save it under a name, so every spoiler video uses the same voice.
- Arrives from the spoiler setup screen (link when no voice exists) or the "สปอย" tab; goes back to setup after saving.

Content
- Designer card:
  - Gender: one of male, female.
  - Age: one of child, teenager, young adult, middle-aged, elderly.
  - Pitch: one of very low pitch, low pitch, moderate pitch, high pitch, very high pitch.
  - Speed: slider 0.8–1.2 in steps of 0.05, value shown.
  - Button "สุ่ม" — generates a preview voice from the choices (takes a while; pressing again replaces the previous preview).
  - Button "ฟัง" — plays the preview; shown once a preview exists.
  - Name field (1–40 characters, required) and button "บันทึก" — shown once a preview exists.
- Saved list, one row per voice: name, "ฟัง", "เปลี่ยนชื่อ", "ลบ" with a confirm step. Speed cannot be changed after saving.

States — one frame each, at every breakpoint
1. Default: designer with a finished preview, name filled, and a list of 3 saved voices with realistic Thai names.
2. Empty list: "ยังไม่มีเสียง กดสุ่มเพื่อออกแบบเสียงแรก".
3. Loading: preview being generated — progress shown in the designer card, "สุ่ม" disabled.
4. Renaming a row inline.
5. Delete confirm on a row.
6. Error: deleting a voice the current draft uses → "เสียงนี้ใช้อยู่ใน Spoil draft".
7. Error: another GPU job running → "รอให้งาน{running}เสร็จก่อน" (e.g. "รอให้งานดูภาพเสร็จก่อน").

Do not include
- Cloning a voice from the user's own audio file.
- Editing a saved voice's speed.
- Any field, step, or feature not listed above.

Deliver: one frame per state per breakpoint, named "Saved voice / {state} / {breakpoint}", built from reusable components with auto layout.
```

## ตั้งค่าคลิปสปอย

เลือก EP เรียงลำดับ สไตล์ layout ความยาว เสียง แล้วกดร่างบท (D5, D7, D8, D16, D28, D39, D46).

```text
Design the "Spoiler setup" screen of framecraft — a local desktop web app that turns downloaded, transcribed clips into Thai vertical (1080×1920) "spoiler" videos: an AI writes a Thai script, picks matching shots, and narrates it. One user, on their own Mac.

Context
- Platform: web app in a desktop browser; breakpoints: mobile 375, desktop 1440 (layout switches at 1024). Route: a sub-page of the "สปอย" tab.
- Design system: use the existing Figma file "framecraft", section "framecraft — สปอย", and its ":: Token" page (Button, Field, Alert, Badge, icons). Tailwind v4 tokens: foreground #121110, muted bg #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff, destructive #dc2626, warning #b45309 on #fffbeb, success #15803d on #f0fdf4. Fonts: IBM Plex Sans Thai (body), IBM Plex Mono (numbers), Manrope (buttons). Radius: rounded-lg for controls, rounded-xl/2xl for cards. Match the existing "Clip row" component for clip items (screenshot attached).
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, labels on every input, touch targets ≥ 44px.

Who and why
- The user wants to pick one film or several episodes in order, choose a style, layout, length, and voice, and press once to get a draft script with images.
- Arrives from the "สปอย" tab; goes to the review screen when drafting finishes.

Content
- Clips: multi-select list of downloaded clips with order controls (move up / down; the chosen order is the episode order 1, 2, 3…). Each item: thumbnail, title, length.
  - Clips that cannot be picked show the reason "ยังไม่ถอด" or "ยังไม่ดูภาพ" with a button "ไปถอด" or "ไปดูภาพ" that goes to the "คลิป" tab.
- Style: 3 options — "ปั่นตัดเร็ว", "เล่าละครหักมุม", "เล่าตามลำดับ".
- Layout: 3 options A, B, C, each with a small vertical-frame thumbnail; picking a style sets its default layout (ปั่นตัดเร็ว → A, เล่าละครหักมุม → B, เล่าตามลำดับ → C), and the user can change it.
  - A: blurred full-screen background, tall centre-cropped image, a 2-line hook pinned at top, big short subtitles mid-screen.
  - B: black background, 16:9 image in the middle, sentence subtitles under it (max 2 lines), no top text.
  - C: black background, 16:9 image in the upper part, yellow episode title with red outline pinned at top, no subtitles.
- Length: 30–180 seconds, default 60.
- Voice: a Saved voice picker, defaulting to the last used. No saved voice → a link to create one.
- Transcript size: "{total} / 32,000" token meter for the chosen clips.
- Button to start drafting — disabled when the total is over 32,000.
- If a draft already exists: a confirm step before replacing it.

States — one frame each, at every breakpoint
1. Default: 3 episodes of a Thai-titled anime picked in order 1, 2, 3; style "เล่าละครหักมุม"; layout B; 60 seconds; a voice chosen; meter 18,400 / 32,000.
2. Empty: "ยังไม่มีคลิปที่ถอดและดูภาพแล้ว" with a link to the clip list.
3. No saved voice: link to the Saved voice screen in place of the picker.
4. Over limit: error "Transcript รวม 34,120 token เกิน 32,000", meter in error colour, draft button disabled; hint to remove an episode.
5. Replace confirm: a draft already exists.
6. Drafting, step 1: "กำลังเขียนบท" with button "ยกเลิก".
7. Drafting, step 2: "กำลังเลือกภาพ 4/15" with progress and button "ยกเลิก".
8. Errors (banner): "AI ร่างบทไม่สำเร็จ 3 ครั้ง" with a retry; "รอให้งานดูภาพเสร็จก่อน"; "ยังติดตั้งไม่ครบ: Qwen3.5 9B model" with a link to Setup status.

Do not include
- More than one draft, or a list of drafts.
- Summarising or trimming a transcript that is too long.
- Background music, colour or font choices.
- Script languages other than Thai.
- Any field, step, or feature not listed above.

Deliver: one frame per state per breakpoint, named "Spoiler setup / {state} / {breakpoint}", built from reusable components with auto layout.
```

## หน้าตรวจแก้

จอหลักของ feature: ตรวจแก้บท Shot เสียง ลายน้ำ แล้ว render (D19, D25, D27, D30, D40, D41, D51). อิงร่าง [review-sketch.md](review-sketch.md).

```text
Design the "Script review" screen of framecraft — a local desktop web app that turns downloaded, transcribed clips into Thai vertical (1080×1920) "spoiler" videos. An AI has drafted a Thai script and picked 2 images (shots) per sentence; here the user checks and fixes everything before rendering. One user, on their own Mac.

Context
- Platform: web app in a desktop browser; breakpoints: mobile 375, desktop 1440 (layout switches at 1024). Route: a sub-page of the "สปอย" tab.
- Design system: use the existing Figma file "framecraft", section "framecraft — สปอย", and its ":: Token" page (Button, Field, Alert, Badge, icons). Tailwind v4 tokens: foreground #121110, muted bg #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff, destructive #dc2626, warning #b45309 on #fffbeb, success #15803d on #f0fdf4. Fonts: IBM Plex Sans Thai (body), IBM Plex Mono (timestamps, durations), Manrope (buttons). Radius: rounded-lg for controls, rounded-xl/2xl for cards. Match the existing "Transcript panel" and "Transcript line" components (screenshot attached).
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, labels on every input, touch targets ≥ 44px.

Who and why
- The user wants to fix the script, swap wrong images, hear the narration, set watermarks and original-audio level, then render the video.
- Arrives from the spoiler setup screen when drafting finishes (or reopens the app — the draft is kept). Goes to the render results on "render". Clicking a shot image opens the shot picker.

Content
- Header:
  - Top text field: the hook (layout A) or episode title (layout C); hidden for layout B.
  - Estimated length / target and sentence count, e.g. "ความยาวประมาณ 58 / 60 วินาที · 15 ประโยค"; a warning when the estimate is more than 25% off target.
- Sentence list, one card per sentence, numbered:
  - 2 shot thumbnails (16:9) with their timestamps; click to change.
  - Editable sentence text (saves on its own while typing; no save button).
  - Cited transcript line, e.g. "อ้าง: EP1 00:01:12 "Where am I?"", or "—" when the AI could not cite one.
  - Status badge, one of 4: "ไม่มี Shot", "ยังไม่มีเสียง", "ต้องสร้างเสียงใหม่", "พร้อม".
  - Voice duration when present, e.g. "3.4 วิ".
  - Actions: "ฟัง", "สร้างเสียงใหม่", ask the AI to pick shots again, delete with a confirm step, "แทรกใต้" (insert a new sentence below).
- Settings panel:
  - Original audio volume: 0–100 in steps of 5, default 20.
  - Watermarks: add / remove, up to 6. Each: text (1–40 characters), position — one of 6 (top left, top centre, top right, bottom left, bottom centre, bottom right; show as a 3×2 picker on a tiny vertical frame), size small or medium.
- Footer actions: "สร้างเสียงทั้งหมด" and "render". "render" is disabled while any sentence is "ไม่มี Shot".

States — one frame each, at every breakpoint
1. Default: 6 sentences in natural Thai about a mystery film, mixed statuses (mostly "พร้อม", one "ต้องสร้างเสียงใหม่", one "ยังไม่มีเสียง"), 2 watermarks set, layout A hook filled.
2. Missing shot: one sentence with "ไม่มี Shot", empty shot placeholders, cited line "—", "render" disabled.
3. Length warning: "ความยาวประมาณ 82 / 60 วินาที" in warning colour.
4. Locked while generating voices: "สร้างเสียง 5/15" with progress and "ยกเลิก"; every editable field and action disabled.
5. Locked while rendering: "render 42%" with progress and "ยกเลิก"; everything disabled.
6. Locked while the AI re-picks shots for one sentence: that card shows progress; everything disabled.
7. Delete confirm on a sentence.
8. No draft: empty state with a link to the setup screen.
9. Errors (banner): "render ไม่สำเร็จ" with retry; "ที่ว่างดิสก์ไม่ถึง 1 GiB" with a hint to delete old renders; "งานหยุดกลางทาง".

Do not include
- Drag-to-reorder sentences.
- Moving, tilting, overlapping images or transitions.
- Choosing font, colour, or dragging text position.
- Background music.
- Any field, step, or feature not listed above.

Deliver: one frame per state per breakpoint, named "Script review / {state} / {breakpoint}", built from reusable components ("Sentence card", "Shot thumb", "Status badge", "Watermark row") with auto layout.
```

## ตัวเลือก Shot

หน้าต่างเลือกภาพให้ประโยค เปิดจากภาพ Shot ในหน้าตรวจแก้ (D26, D27).

```text
Design the "Shot picker" dialog of framecraft — a local desktop web app that turns downloaded clips into Thai vertical "spoiler" videos. Each script sentence shows 2 shots (short stretches of the source video); this dialog lets the user swap one. One user, on their own Mac.

Context
- Platform: web app in a desktop browser; breakpoints: mobile 375 (full-screen sheet), desktop 1440 (modal).
- Design system: use the existing Figma file "framecraft", section "framecraft — สปอย", and its ":: Token" page (Button, Field, Alert, Badge, icons). Tailwind v4 tokens: foreground #121110, muted bg #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff. Fonts: IBM Plex Sans Thai (body), IBM Plex Mono (timestamps), Manrope (buttons). Radius: rounded-lg for controls, rounded-2xl for the dialog. Match the existing "Player" component (screenshot attached).
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, focus trapped in the dialog, Esc closes, touch targets ≥ 44px.

Who and why
- The user wants to replace a shot that doesn't match what the sentence says.
- Opens by clicking a shot thumbnail on the script review screen; closes back to it after picking.

Content
- Title "เลือกภาพให้ประโยค 2" and a close button.
- A grid of small 16:9 thumbnails, each with its start timestamp — by default, shots within ±30 seconds of the sentence's cited line.
- "ดูทั้งคลิป" with an episode picker (EP1, EP2…) — shows every shot of that episode instead.
- Hovering (or focusing) a thumbnail shows its shot description (an English one-line description written by the AI).
- A player area that plays the hovered/selected shot's stretch only.
- The currently used shot is marked as selected.

States — one frame each, at every breakpoint
1. Default: ±30 s grid of 12 thumbnails, one hovered with its description, the current shot marked.
2. Whole clip: "ดูทั้งคลิป" active on EP2, a long scrolling grid.
3. Sentence with no cited line: opens straight on the whole clip of the first episode.
4. Playing a shot's stretch in the player.
5. Loading thumbnails.

Do not include
- Uploading your own image.
- Cropping, zooming, or moving the image.
- Any field, step, or feature not listed above.

Deliver: one frame per state per breakpoint, named "Shot picker / {state} / {breakpoint}", built from reusable components with auto layout.
```

## ผล render

รายการผล render ที่เก็บทุกครั้ง เล่น โหลด ลบ พร้อมบรรทัดเครดิตต้นฉบับ (D10, D42, legal 1).

```text
Design the "Render results" screen of framecraft — a local desktop web app that turns downloaded clips into Thai vertical (1080×1920) "spoiler" videos with a Thai AI narrator. Every render is kept so the user can compare versions. One user, on their own Mac.

Context
- Platform: web app in a desktop browser; breakpoints: mobile 375, desktop 1440 (layout switches at 1024). Route: a sub-page of the "สปอย" tab.
- Design system: use the existing Figma file "framecraft", section "framecraft — สปอย", and its ":: Token" page (Button, Field, Alert, Badge, icons). Tailwind v4 tokens: foreground #121110, muted bg #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff, destructive #dc2626, warning #b45309 on #fffbeb. Fonts: IBM Plex Sans Thai (body), IBM Plex Mono (times, durations), Manrope (buttons). Radius: rounded-lg for controls, rounded-xl/2xl for cards. Match the existing "Clip row" component (screenshot attached).
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, touch targets ≥ 44px.

Who and why
- The user wants to watch the finished video, download the mp4 and .srt to post themselves, and delete old attempts.
- Arrives from "render" on the script review screen.

Content
- Progress card while a render runs: "สร้างเสียง x/y", then "render %", with a progress bar and button "ยกเลิก".
- List, newest first, one row per render: time rendered, video length, play (a vertical 9:16 player), download mp4, download ".srt", delete with a confirm step.
- A credit line on each row: "ต้นฉบับ: {ชื่อคลิป}" with a copy button (for pasting into the post description).

States — one frame each, at every breakpoint
1. Default: 3 renders with realistic times and lengths (e.g. 0:58, 1:02), Thai clip titles in the credit lines, one playing in the vertical player.
2. Empty: "ยังไม่มีผล render".
3. Rendering, voice step: "สร้างเสียง 5/15" above the list.
4. Rendering, video step: "render 64%" above the list.
5. Delete confirm on a row.
6. Errors (banner): "render ไม่สำเร็จ"; "ที่ว่างดิสก์ไม่ถึง 1 GiB" with a hint to delete old renders.

Do not include
- Uploading to YouTube or TikTok.
- An automatic model-credit line in the video.
- Any field, step, or feature not listed above.

Deliver: one frame per state per breakpoint, named "Render results / {state} / {breakpoint}", built from reusable components with auto layout.
```

ออกแบบเสร็จแล้ว: วาง Figma link (หรือ path ของรูป) พร้อม `/warroom spoil-maker` เพื่อเปลี่ยน Source ของจอเป็น link นั้น.

## Transcript ที่แก้ได้ใน tab คลิป

แก้ข้อความ Transcript ทีละบรรทัดในกล่องถอดบทพูดของ tab คลิป (D53, D54). ออกแบบแล้วใน [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) — frames คลิป และ คลิป — แก้ประโยค.

```text
Design new states of the existing "Transcript line" component inside the "Transcript panel" of framecraft — a local desktop web app that downloads YouTube clips, transcribes them, and turns them into Thai vertical "spoiler" videos. One user, on their own Mac.

Context
- Platform: web app in a desktop browser; breakpoints: mobile 375, desktop 1440 (layout switches at 1024). Route: the "คลิป" tab (#/clips): clip list on the left, arrow, transcript box with player and Transcript on the right; stacked on narrow screens.
- Design system: use the existing Figma file "framecraft", section "framecraft — สปอย", and its ":: Token" page (Button, Field, Alert, Badge, icons). Tailwind v4 tokens: foreground #121110, muted bg #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff, destructive #dc2626, warning #b45309 on #fffbeb, success #15803d on #f0fdf4. Fonts: IBM Plex Sans Thai (body), IBM Plex Mono (numbers, timestamps), Manrope (buttons). Radius: rounded-lg for controls, rounded-xl/2xl for cards. Match the existing "Transcript panel" and "Transcript line" components (screenshot attached).
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, labels on every input, touch targets ≥ 44px.

Who and why
- The user wants to fix words Whisper got wrong, one line at a time, before the AI writes a spoiler script from the Transcript.
- Only the text changes: line times, line count, and order stay the same.

Content (added to each Transcript line)
- On hover or focus: button "แก้".
- Editing: the line becomes a text field holding the current text, with buttons "บันทึก" and "ยกเลิก". The timestamp stays shown and cannot be edited.
- A saved line shows a badge "แก้แล้ว".
- Pressing "ถอดใหม่" on a clip with edited lines: a confirm step "ถอดใหม่จะลบบทพูดที่แก้ไว้", with a continue action and a cancel action.
- Clip in use by a draft job: "คลิปนี้กำลังถูกใช้ในงานอื่น".

States — one frame each, at every breakpoint
1. Default: a Transcript of 8 lines with realistic Thai text, two of them with "แก้แล้ว".
2. Hover: one line showing "แก้".
3. Editing: one line as a text field with "บันทึก" and "ยกเลิก".
4. Re-transcribe confirm: "ถอดใหม่จะลบบทพูดที่แก้ไว้".
5. Error: "คลิปนี้กำลังถูกใช้ในงานอื่น" while saving.

Do not include
- Splitting, merging, deleting, or re-timing lines.
- Showing or restoring the original text.
- Any field, step, or feature not listed above.

Deliver: one frame per state per breakpoint, named "Transcript line / {state} / {breakpoint}", as new variants of the existing "Transcript line" component with auto layout.
```
