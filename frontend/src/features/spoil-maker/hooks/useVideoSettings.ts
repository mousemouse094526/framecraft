import { useCallback, useEffect, useRef } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { SETTINGS_PATH } from "../lib/draft";
import { type VideoSettings, type Watermark } from "../lib/render";

export type SettingsState =
  | { kind: "loading" }
  | { kind: "offline" }
  /** `error`: the last refusal of a change, to show under the watermarks. */
  | { kind: "loaded"; watermarks: Watermark[]; error: string | null };

const NO_WATERMARKS: Watermark[] = [];

/** What เพิ่มลายน้ำ starts with: the API keeps no empty text, so the user types over it (D41). */
export const NEW_WATERMARK: Watermark = { text: "ลายน้ำ", position: "bottom_right", size: "small", enabled: true };

/**
 * The watermarks every render draws (spoil-maker D41, spec › ค่าที่จำไว้): read from
 * `GET /settings`, each change sent whole with `PATCH /settings` so the app remembers it.
 */
export function useVideoSettings() {
  const [state, , setIfMounted] = useMountedState<SettingsState>({ kind: "loading" });
  // The list the server has: a row's text saves late (useAutoSave), so a change builds on this.
  const marks = useRef<Watermark[]>([]);

  useEffect(() => {
    void (async () => {
      try {
        const settings = await getJson<VideoSettings>(SETTINGS_PATH);
        marks.current = settings.watermarks;
        setIfMounted({ kind: "loaded", watermarks: settings.watermarks, error: null });
      } catch {
        setIfMounted({ kind: "offline" });
      }
    })();
  }, [setIfMounted]);

  /** Sends the whole list; resolves to false when it was refused, and the list stays as it was. */
  const save = useCallback(
    async (watermarks: Watermark[]): Promise<boolean> => {
      try {
        const reply = await sendJson<VideoSettings | Refusal>("PATCH", SETTINGS_PATH, { watermarks });
        if (reply.status === 200) {
          marks.current = (reply.body as VideoSettings).watermarks;
          setIfMounted({ kind: "loaded", watermarks: marks.current, error: null });
          return true;
        }
        const refusal = refusalOf(reply.body);
        if (refusal) {
          setIfMounted((s) => (s.kind === "loaded" ? { ...s, error: refusal.message } : s));
          return false;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
      return false;
    },
    [setIfMounted],
  );

  const add = useCallback(() => save([...marks.current, NEW_WATERMARK]), [save]);
  const change = useCallback(
    (index: number, mark: Watermark) => save(marks.current.map((old, i) => (i === index ? mark : old))),
    [save],
  );
  const remove = useCallback((index: number) => save(marks.current.filter((_, i) => i !== index)), [save]);

  /** The list as loaded, empty until then. */
  const watermarks = state.kind === "loaded" ? state.watermarks : NO_WATERMARKS;

  return { state, watermarks, add, change, remove };
}
