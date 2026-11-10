/** Plays a sound from the API once; a newer `?v=` in `url` skips the browser's cached copy (spoil-maker spec › Frontend). */
export function playAudio(url: string): void {
  // A blocked autoplay, a missing file or a browser without audio output only means no sound:
  // nothing to show for it.
  try {
    void new Audio(url).play().catch(() => {});
  } catch {
    // `new Audio` itself threw.
  }
}
