/** Plays a wav from the API once; a newer `?v=` in `url` skips the browser's cached copy (spoil-maker spec › Frontend). */
export function playAudio(url: string): void {
  // A blocked autoplay or a missing file only means no sound: nothing to show for it.
  void new Audio(url).play().catch(() => {});
}
