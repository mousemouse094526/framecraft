import { useCallback, useEffect, useRef, useState } from "react";
import { postForBlob, sendJson } from "../../../lib/api";
import { lessonHash } from "../../../lib/lesson";
import { OFFLINE, refusedOf, type Refused } from "../../../lib/refused";
import type { Refusal } from "../../../lib/refusal";
import { useListen } from "../../../lib/useListen";
import { useMountedState } from "../../../lib/useMountedState";
import { bpmOk, firstPickable, listenPath, pickableFrom, previewPath, songLessonsPath, type Created, type Choice, type FoundBar, type Preview } from "../lib/songs";

/** How long the page waits after the last change before it asks for the preview (spec › Frontend). */
export const PREVIEW_DEBOUNCE_MS = 300;

export type PreviewState =
  | { kind: "loading" }
  /** What `POST /preview` answered for the pick shown. */
  | ({ kind: "ready" } & Preview)
  /** The API refused the pick: its line, and the field (`bar`, `bars`, `bpm`) when it named one. */
  | ({ kind: "refused" } & Refused);

export type Creating = { kind: "idle" } | { kind: "creating" } | ({ kind: "refused" } & Refused);

/**
 * สร้างบทเรียน on the song page (spec › Frontend; D11, D13, D20, D21): the first bar (pressed on the
 * strip), how many bars (1–4, no further than the 4/4 bars left) and the BPM (the Score's default
 * until typed) are previewed 300 ms after the last change through `POST /preview`; ฟัง mixes the
 * same pick through `POST /listen`; สร้างบทเรียนกลอง writes it through `POST /lessons` and opens the
 * lesson's editor. Only a song with a 4/4 bar gets here: `firstPickable(found) >= 0`.
 */
export function useLessonPreview(songId: string, found: FoundBar[]) {
  const [bar, setBar] = useState(() => firstPickable(found));
  const [bars, setBars] = useState(1);
  // What the BPM field shows while the user types; null shows the preview's BPM.
  const [bpmText, setBpmText] = useState<string | null>(null);
  const [preview, , setPreviewIfMounted] = useMountedState<PreviewState>({ kind: "loading" });
  const [creating, , setCreatingIfMounted] = useMountedState<Creating>({ kind: "idle" });
  const sequences = useRef(0); // the number of the latest preview asked: an older answer is dropped

  const typedBpm = bpmText === null ? null : Number(bpmText);
  const bpmFault = typedBpm !== null && !bpmOk(typedBpm);
  const previewBpm = preview.kind === "ready" ? preview.bpm : null;
  /** What `POST /preview` is asked: the typed BPM when there is a sound one, else no BPM, for the Score's default. */
  const asked: Choice = typedBpm !== null && !bpmFault ? { bar, bars, bpm: typedBpm } : { bar, bars };
  /** What ฟัง and สร้าง send, which need a BPM: `asked` with the BPM the field shows; null until the preview said what it is. */
  const withBpm: Choice | null = asked.bpm !== undefined ? asked : previewBpm === null ? null : { ...asked, bpm: previewBpm };

  useEffect(() => {
    if (bpmFault) return;
    const sequence = ++sequences.current;
    const timer = setTimeout(async () => {
      try {
        const reply = await sendJson<Preview | Refusal>("POST", previewPath(songId), asked);
        if (sequence !== sequences.current) return; // a later change asked again
        if (reply.status === 200 && reply.body) return setPreviewIfMounted({ kind: "ready", ...(reply.body as Preview) });
        const refused = await refusedOf(reply.body);
        if (sequence === sequences.current) setPreviewIfMounted({ kind: "refused", ...refused });
      } catch {
        if (sequence === sequences.current) setPreviewIfMounted({ kind: "refused", ...OFFLINE });
      }
    }, PREVIEW_DEBOUNCE_MS);
    return () => clearTimeout(timer);
    // `asked` is a new object each render: its parts are the dependencies.
  }, [songId, bar, bars, asked.bpm, bpmFault, setPreviewIfMounted]);

  /** A bar pressed on the strip: the first bar of the lesson, the count cut to the 4/4 bars left from it. */
  const pickBar = useCallback(
    (index: number) => {
      setBar(index);
      setBars((now) => Math.max(1, Math.min(now, pickableFrom(found, index))));
    },
    [found],
  );

  const listen = useListen(useCallback(() => (withBpm ? postForBlob(listenPath(songId), withBpm) : Promise.resolve(null)), [songId, withBpm]));

  const create = useCallback(async () => {
    if (!withBpm) return;
    setCreatingIfMounted({ kind: "creating" });
    try {
      const reply = await sendJson<Created | Refusal>("POST", songLessonsPath(songId), withBpm);
      if (reply.status === 201 && reply.body) {
        window.location.hash = lessonHash((reply.body as Created).lesson_id);
        return;
      }
      setCreatingIfMounted({ kind: "refused", ...(await refusedOf(reply.body)) });
    } catch {
      setCreatingIfMounted({ kind: "refused", ...OFFLINE });
    }
  }, [songId, withBpm, setCreatingIfMounted]);

  return {
    bar,
    bars,
    /** How many bars may be picked from `bar`. */
    pickable: pickableFrom(found, bar),
    /** What the BPM field shows: the text typed, else the preview's BPM, else nothing yet. */
    bpmShown: bpmText ?? (previewBpm === null ? "" : String(previewBpm)),
    bpmFault,
    preview,
    creating,
    listen,
    pickBar,
    setBars,
    setBpmText,
    create,
  };
}
