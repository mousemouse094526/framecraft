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
};

export const CLIPS_PATH = "/api/spoil/clips";
