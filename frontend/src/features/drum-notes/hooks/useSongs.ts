import { useCallback, useEffect, useRef } from "react";
import { getJson, OFFLINE_TEXT, sendFile, sendJson, type FileUpload } from "../../../lib/api";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { fixesFor } from "../../../lib/setupFixes";
import { useLeaveGuard } from "../../../lib/useHash";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { IMPORT_PATH, isImporting, songHash, songPath, SONGS_PATH, type Song, type SongImport, type SongRow } from "../lib/songs";
import { usePick } from "./usePick";

/** A line above the list: why a link, a file or a delete was refused, with the fix commands a `not_ready` names. */
export type Notice = { tone: "error" | "warning"; text: string; fixes: string[] };

/** The file being sent: its percent out, then the backend converting it (ADR 0028). */
export type Upload = { name: string; percent: number; converting: boolean };

export type SongsState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "ready";
      songs: SongRow[];
      /** The latest link import, null when none ran since the backend started. */
      job: SongImport | null;
      upload: Upload | null;
      notice: Notice | null;
    };

type Ready = Extract<SongsState, { kind: "ready" }>;

/** The codes that mean "not now", not "wrong" (toon D72). */
const NOT_NOW = ["busy", "not_ready"];

/** What a request answered as a notice; `not_ready` brings the fix of each row it names (setup-status D26). */
async function noticeOf(body: unknown): Promise<Notice> {
  const refusal = refusalOf(body);
  if (!refusal) return { tone: "error", text: OFFLINE_TEXT, fixes: [] };
  const fixes = await fixesFor(refusal);
  return { tone: NOT_NOW.includes(refusal.code) ? "warning" : "error", text: refusal.message, fixes };
}

/** The id in a `200` of `/link` or `/check`: the link or file is a song already (D3, D20). */
function knownIdOf(status: number, body: unknown): string | undefined {
  return status === 200 ? (body as { song_id?: string } | null)?.song_id : undefined;
}

/**
 * รายการเพลง: the songs newest change first as the API sorts them, the link import and the Pick job
 * polled while they run, a file sent after its check, and delete (spec › Frontend, D18). `onKnownSong` gets the id of
 * a link or file that is a song already (D3, D20).
 */
export function useSongs(onKnownSong: (id: string) => void) {
  const [state, , setIfMounted] = useMountedState<SongsState>({ kind: "loading" });
  const sending = useRef<FileUpload<Song | Refusal> | null>(null);

  const update = useCallback((change: (s: Ready) => Ready) => setIfMounted((s) => (s.kind === "ready" ? change(s) : s)), [setIfMounted]);

  const load = useCallback(async () => {
    try {
      const [songs, job] = await Promise.all([getJson<SongRow[]>(SONGS_PATH), getJson<SongImport | null>(IMPORT_PATH)]);
      setIfMounted((s) => (s.kind === "ready" ? { ...s, songs, job } : { kind: "ready", songs, job, upload: null, notice: null }));
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  const job = state.kind === "ready" ? state.job : null;
  usePollWhile<SongImport | null>(
    job !== null && isImporting(job),
    IMPORT_PATH,
    (next) => {
      update((s) => ({ ...s, job: next, notice: next?.state === "failed" && next.error ? { tone: "error", text: next.error.message, fixes: [] } : s.notice }));
      if (next === null || !isImporting(next)) void load();
    },
    () => setIfMounted({ kind: "offline" }),
  );

  // The latest Pick job, of any song: a row says "กำลังแกะ n%" while it is its own, and the list is read again once it ends (D18).
  const { job: pick } = usePick(
    () => {},
    () => void load(),
  );

  useLeaveGuard(useCallback(() => sending.current !== null, []));

  const showNotice = useCallback(async (body: unknown) => {
    const notice = await noticeOf(body);
    update((s) => ({ ...s, notice }));
  }, [update]);

  /** `POST /songs/link`: the job to poll, or the id of a song the link already is. True when something started. */
  const startLink = useCallback(
    async (url: string): Promise<boolean> => {
      try {
        const reply = await sendJson<unknown>("POST", `${SONGS_PATH}/link`, { url });
        if (reply.status === 202 && reply.body) {
          update((s) => ({ ...s, job: reply.body as SongImport, notice: null }));
          return true;
        }
        const known = knownIdOf(reply.status, reply.body);
        if (known) {
          onKnownSong(known);
          return true;
        }
        await showNotice(reply.body);
      } catch {
        await showNotice(null);
      }
      return false;
    },
    [update, onKnownSong, showNotice],
  );

  /** `POST /songs/check`, then the file as the raw body with `PUT` (ADR 0028); the new song opens. */
  const importFile = useCallback(
    async (file: File) => {
      update((s) => ({ ...s, notice: null }));
      let check: { status: number; body: unknown };
      try {
        check = await sendJson<unknown>("POST", `${SONGS_PATH}/check`, { name: file.name, size: file.size });
      } catch {
        return showNotice(null);
      }
      if (check.status !== 200) return showNotice(check.body);
      const known = knownIdOf(check.status, check.body);
      if (known) return onKnownSong(known);
      const query = `name=${encodeURIComponent(file.name)}&size=${file.size}`;
      const upload = sendFile<Song | Refusal>(
        `${SONGS_PATH}?${query}`,
        file,
        (percent) => update((s) => ({ ...s, upload: s.upload && { ...s.upload, percent } })),
        () => update((s) => ({ ...s, upload: s.upload && { ...s.upload, percent: 100, converting: true } })),
        "PUT",
      );
      sending.current = upload;
      update((s) => ({ ...s, upload: { name: file.name, percent: 0, converting: false } }));
      const reply = await upload.reply;
      sending.current = null;
      update((s) => ({ ...s, upload: null }));
      if (reply.kind === "answer" && reply.status === 201 && reply.body) {
        window.location.hash = songHash((reply.body as Song).id);
        return;
      }
      if (reply.kind !== "aborted") await showNotice(reply.kind === "answer" ? reply.body : null);
    },
    [update, onKnownSong, showNotice],
  );

  const cancelUpload = useCallback(() => sending.current?.abort(), []);

  const cancelImport = useCallback(async () => {
    try {
      const reply = await sendJson<SongImport>("POST", `${IMPORT_PATH}/cancel`, {});
      if (reply.status === 200 && reply.body) update((s) => ({ ...s, job: reply.body }));
      else await load(); // `not_running`: it ended before the cancel came
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [update, load, setIfMounted]);

  const remove = useCallback(
    async (id: string) => {
      try {
        const reply = await sendJson("DELETE", songPath(id));
        // Already gone is what was asked for.
        if (reply.status === 204 || reply.status === 404) await load();
        else await showNotice(reply.body);
      } catch {
        await showNotice(null);
      }
    },
    [load, showNotice],
  );

  return { state, pick, reload: load, startLink, importFile, cancelUpload, cancelImport, remove };
}
