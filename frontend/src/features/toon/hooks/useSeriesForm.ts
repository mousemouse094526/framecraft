import { useCallback, useEffect } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import type { Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { VOICES_PATH, type SavedVoice } from "../../../lib/voices";
import {
  GENRE_DEFAULTS,
  SERIES_PATH,
  seriesHash,
  seriesPath,
  type Series,
  type SeriesFields,
} from "../lib/series";
import { refusalTextOf } from "../lib/notice";

export type SeriesFormState =
  | { kind: "loading" }
  | { kind: "offline" }
  /** `saving` while the request is out; `error` is the refusal of the last one. */
  | { kind: "ready"; initial: SeriesFields; voices: SavedVoice[]; saving: boolean; error: string | null };

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
 * ตั้งค่า Series: a new one (`sid` null) or an existing one's fields, the Saved voices to pick
 * from, and save. A new one is sent whole: style, tone and acts start as its genre's and the
 * user may change them before saving (D52).
 */
export function useSeriesForm(sid: string | null) {
  const [state, , setState] = useMountedState<SeriesFormState>({ kind: "loading" });

  useEffect(() => {
    void (async () => {
      try {
        const voices = await getJson<SavedVoice[]>(VOICES_PATH);
        const initial = sid === null ? newSeries(voices) : await getJson<Series>(seriesPath(sid));
        setState({ kind: "ready", initial, voices, saving: false, error: null });
      } catch {
        setState({ kind: "offline" });
      }
    })();
  }, [sid, setState]);

  const save = useCallback(
    async (fields: SeriesFields) => {
      setState((s) => (s.kind === "ready" ? { ...s, saving: true, error: null } : s));
      let error = OFFLINE_TEXT;
      try {
        const reply =
          sid === null
            ? await sendJson<Series | Refusal>("POST", SERIES_PATH, fields)
            : await sendJson<Series | Refusal>("PATCH", seriesPath(sid), editable(fields));
        if (reply.status === 200 || reply.status === 201) {
          window.location.hash = seriesHash((reply.body as Series).id);
          return;
        }
        error = refusalTextOf(reply.body).text;
      } catch {
        // no answer: OFFLINE_TEXT
      }
      setState((s) => (s.kind === "ready" ? { ...s, saving: false, error } : s));
    },
    [sid, setState],
  );

  return { state, save };
}

/** Every field a `PATCH` may change: not `layout` or `genre` (D7, D10). */
function editable(fields: SeriesFields) {
  const { name, channel_name, style, tone, acts, voice_id, name_tags } = fields;
  return { name, channel_name, style, tone, acts, voice_id, name_tags };
}
