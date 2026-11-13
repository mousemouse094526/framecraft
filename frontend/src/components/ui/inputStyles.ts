// The Figma `Field` input; red while its field has an error (story-kb's editor, video-gen's lesson editor).
export const inputClass = (error: boolean) =>
  `h-10 w-full rounded-lg border bg-card px-3 text-sm leading-5 text-foreground outline-none focus:border-2 focus:border-brand-accent ${
    error ? "border-destructive" : "border-border"
  }`;
