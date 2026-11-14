// The Figma "Button" looks; each caller adds its own height and padding.
export const PRIMARY_BUTTON =
  "flex shrink-0 items-center justify-center gap-2 rounded-lg bg-brand font-button text-sm leading-5 font-medium text-card hover:opacity-90 disabled:opacity-60";

// The Figma "Button" secondary: a grey fill, as ตัดช่วง, เพิ่มช่วง and the trim section's ยกเลิก (spoil D44).
export const SECONDARY_BUTTON =
  "flex shrink-0 items-center justify-center gap-2 rounded-lg bg-muted font-button text-sm leading-5 font-medium text-brand hover:bg-surface-strong disabled:opacity-60 disabled:hover:bg-muted";

// No fill until hovered, as ยกเลิก and แก้ on a Transcript line.
export const GHOST_BUTTON =
  "flex shrink-0 items-center justify-center gap-2 rounded-lg font-button text-sm leading-5 font-medium text-foreground hover:bg-card disabled:opacity-60";

export const OUTLINE_BUTTON =
  "flex shrink-0 items-center justify-center gap-2 rounded-lg border border-border bg-card font-button text-sm leading-5 font-medium text-foreground hover:bg-muted disabled:opacity-60 disabled:hover:bg-card";

// Red fill, for the step that deletes or loses work (ทำต่อ on a Spoil draft warning, ลบ a sentence).
export const DESTRUCTIVE_BUTTON =
  "flex shrink-0 items-center justify-center gap-2 rounded-lg bg-destructive font-button text-sm leading-5 font-medium text-card hover:opacity-90 disabled:opacity-60";
