import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { VOICES_PATH, type SavedVoice } from "../../../lib/voices";
import {
  GENRE_DEFAULTS,
  SERIES_PATH,
  seriesHash,
  seriesPath,
  type Series,
  type SeriesFields,
} from "../lib/series";
import { sendEdit } from "../lib/edit";
import type { Notice } from "../lib/notice";
import { useReadyState } from "./useReadyState";

export type SeriesFormState =
  | { kind: "loading" }
  | { kind: "offline" }
  /** `saving` while the request is out; `notice` is the refusal of the last one (the form shows its text only, untitled). */
  | { kind: "ready"; initial: SeriesFields; voices: SavedVoice[]; saving: boolean; notice: Notice | null };

const SAVE_REFUSED = "บันทึก Series ไม่ได้";

function newSeries(voices: SavedVoice[]): SeriesFields {
  return {
    name: "",
    channel_name: "",
    layout: "frame",
    genre: "horror",
    voice_id: voices[0]?.id ?? "",
    name_tags: true,
    ...GENRE_DEFAULTS.horror,
  };
}

/**
 * ตั้งค่า Series: a new one (`seriesId` null) or an existing one's fields, the Saved voices to pick
 * from, and save. A new one is sent whole: style, tone and acts start as its genre's and the
 * user may change them before saving (D52).
 */
export function useSeriesForm(seriesId: string | null) {
  const [state, setState, update] = useReadyState<SeriesFormState>({ kind: "loading" });

  useEffect(() => {
    void (async () => {
      try {
        const voices = await getJson<SavedVoice[]>(VOICES_PATH);
        const initial = seriesId === null ? newSeries(voices) : await getJson<Series>(seriesPath(seriesId));
        setState({ kind: "ready", initial, voices, saving: false, notice: null });
      } catch {
        setState({ kind: "offline" });
      }
    })();
  }, [seriesId, setState]);

  const save = useCallback(
    async (fields: SeriesFields) => {
      update((s) => ({ ...s, saving: true, notice: null }));
      const reply =
        seriesId === null
          ? await sendEdit<Series>("POST", SERIES_PATH, fields, SAVE_REFUSED)
          : await sendEdit<Series>("PATCH", seriesPath(seriesId), editable(fields), SAVE_REFUSED);
      if (reply.kind === "ok") {
        window.location.hash = seriesHash(reply.value.id);
        return;
      }
      update((s) => ({ ...s, saving: false, notice: reply.notice }));
    },
    [seriesId, update],
  );

  return { state, save };
}

/** Every field a `PATCH` may change: not `layout` or `genre` (D7, D10). */
function editable(fields: SeriesFields) {
  const { name, channel_name, style, tone, acts, voice_id, name_tags } = fields;
  return { name, channel_name, style, tone, acts, voice_id, name_tags };
}
