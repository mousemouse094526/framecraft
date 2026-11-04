/** A span of a clip's time in seconds, `[start_s, end_s)` (backend.spoil.clips.Range). */
export type Range = { start_s: number; end_s: number };

// The shape of a Temp clip (backend.spoil.clips.ListedClip, spoil spec › Temp clip): the คลิป tab lists
// them, the สปอย tab picks from them.
export type TempClip = {
  id: string;
  title: string;
  channel: string | null;
  source_url: string;
  duration_s: number | null;
  width: number | null;
  height: number | null;
  orientation: "portrait" | "landscape";
  file_bytes: number;
  thumbnail: string | null;
  downloaded_at: string;
  yt_dlp_version: string;
  /** Has a Transcript (D23). */
  transcribed: boolean;
  /** Has Shots from a Describe job (spoil-maker D16). */
  described: boolean;
  /** The Spoil draft is made from it: redoing or deleting it removes the draft (spoil-maker D49). */
  in_draft: boolean;
  /**
   * The ranges cut out of it, oldest trim first; each in the file's time just before its own
   * trim, so a later trim's times are of the already-trimmed file. Empty when never trimmed (D36).
   */
  trimmed: Range[];
  trimmed_at: string | null;
};

export const CLIPS_PATH = "/api/spoil/clips";

/** The clip's mp4 with no `?v=`: only for a clip whose list entry can't be read. */
export function videoPath(clipId: string): string {
  return `${CLIPS_PATH}/${clipId}/video`;
}

/** The clip's mp4; `?v=` changes with each trim, so the browser never plays a cached file from before it (D41). */
export function videoUrl(clip: Pick<TempClip, "id" | "downloaded_at" | "trimmed_at">): string {
  return `${videoPath(clip.id)}?v=${encodeURIComponent(clip.trimmed_at ?? clip.downloaded_at)}`;
}
