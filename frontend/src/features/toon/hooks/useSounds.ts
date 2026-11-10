import { useCallback, useEffect, useRef } from "react";
import { getJson, sendFile, sendJson, type FileUpload } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import type { Refusal } from "../../../lib/refusal";
import { useLeaveGuard } from "../../../lib/useHash";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { isImporting, SOUND_IMPORT_PATH, SOUNDS_PATH, soundPath, type Sound, type SoundImport } from "../lib/sounds";
import { noticeOf, NOT_NOW, type Notice } from "../lib/notice";

/** The EPs a sound plays in, as `in_use` names them. */
type SoundUser = { series_name: string; n: number; title: string };

export type SoundsState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "ready";
      sounds: Sound[];
      /** The latest link import, null when none ran since the backend started. */
      job: SoundImport | null;
      /** Why a file or link didn't come in (Figma toon / 8 › Errors). */
      importNotice: Notice | null;
      /** Why a sound can't be deleted (Figma toon / 8 › Delete blocked). */
      listNotice: Notice | null;
      /** The file being sent: its name and the percent out. */
      upload: { name: string; percent: number } | null;
    };

type Ready = Extract<SoundsState, { kind: "ready" }>;

/** คลังเสียงพื้น: the library, renaming, deleting, a file's import with its % out, and a link's
 * import polled while it runs (spec › คลังเสียงพื้น, ADR 0028). */
export function useSounds() {
  const [state, , setState] = useMountedState<SoundsState>({ kind: "loading" });
  const sending = useRef<FileUpload<Sound | Refusal> | null>(null);

  const update = useCallback(
    (change: (s: Ready) => SoundsState) => setState((s) => (s.kind === "ready" ? change(s) : s)),
    [setState],
  );

  const load = useCallback(async () => {
    try {
      const [sounds, job] = await Promise.all([
        getJson<Sound[]>(SOUNDS_PATH),
        getJson<SoundImport | null>(SOUND_IMPORT_PATH),
      ]);
      setState((s) =>
        s.kind === "ready"
          ? { ...s, sounds, job }
          : { kind: "ready", sounds, job, importNotice: null, listNotice: null, upload: null },
      );
    } catch {
      setState({ kind: "offline" });
    }
  }, [setState]);

  useEffect(() => {
    void load();
  }, [load]);

  const job = state.kind === "ready" ? state.job : null;
  usePollWhile<SoundImport | null>(
    job !== null && isImporting(job),
    SOUND_IMPORT_PATH,
    (next) => {
      update((s) => ({ ...s, job: next, importNotice: next?.state === "failed" ? failedNotice(next) : s.importNotice }));
      if (next === null || !isImporting(next)) void load();
    },
    () => setState({ kind: "offline" }),
  );

  useLeaveGuard(useCallback(() => sending.current !== null, []));

  const lineOf = (title: string, body: unknown) => noticeOf(title, body, NOT_NOW);

  const rename = async (sound: Sound, name: string) => {
    try {
      const reply = await sendJson<Sound | Refusal>("PATCH", soundPath(sound.id), { name });
      if (reply.status === 200) {
        const renamed = reply.body as Sound;
        update((s) => ({ ...s, listNotice: null, sounds: s.sounds.map((x) => (x.id === renamed.id ? renamed : x)) }));
        return true;
      }
      update((s) => ({ ...s, listNotice: lineOf(`เปลี่ยนชื่อ ${sound.name} ไม่ได้`, reply.body) }));
    } catch {
      update((s) => ({ ...s, listNotice: lineOf(`เปลี่ยนชื่อ ${sound.name} ไม่ได้`, null) }));
    }
    return false;
  };

  const remove = async (sound: Sound) => {
    const title = `ลบ ${sound.name} ไม่ได้`;
    try {
      const reply = await sendJson<Refusal & { eps?: SoundUser[] }>("DELETE", soundPath(sound.id));
      if (reply.status === 204) {
        update((s) => ({ ...s, listNotice: null, sounds: s.sounds.filter((x) => x.id !== sound.id) }));
        return;
      }
      const eps = reply.body?.eps;
      const notice =
        eps && eps.length > 0
          ? { tone: "error" as const, title, text: `ยังใช้อยู่ใน ${eps.map(epName).join(", ")}`, setupLink: false }
          : lineOf(title, reply.body);
      update((s) => ({ ...s, listNotice: notice }));
    } catch {
      update((s) => ({ ...s, listNotice: lineOf(title, null) }));
    }
  };

  /** `/imports/check` first, then the file as the raw body (ADR 0028); the answer is the new sound. */
  const uploadFile = async (file: File) => {
    const title = `เอาไฟล์ ${file.name} เข้าไม่ได้`;
    try {
      const checked = await sendJson<Refusal>("POST", `${SOUNDS_PATH}/imports/check`, { name: file.name, size: file.size });
      if (checked.status !== 200) return update((s) => ({ ...s, importNotice: lineOf(title, checked.body) }));
    } catch {
      return update((s) => ({ ...s, importNotice: lineOf(title, null) }));
    }
    update((s) => ({ ...s, importNotice: null, upload: { name: file.name, percent: 0 } }));
    const query = `name=${encodeURIComponent(file.name)}&size=${file.size}`;
    sending.current = sendFile<Sound | Refusal>(
      `${SOUNDS_PATH}/imports?${query}`,
      file,
      (percent) => update((s) => ({ ...s, upload: s.upload && { ...s.upload, percent } })),
      () => {},
    );
    const reply = await sending.current.reply;
    sending.current = null;
    update((s) => ({ ...s, upload: null }));
    if (reply.kind === "answer" && reply.status === 201) {
      const added = reply.body as Sound;
      update((s) => ({ ...s, sounds: [...s.sounds, added] }));
    } else if (reply.kind !== "aborted") {
      update((s) => ({ ...s, importNotice: lineOf(title, reply.kind === "answer" ? reply.body : null) }));
    }
  };

  const cancelUpload = () => sending.current?.abort();

  const download = async (url: string) => {
    const title = "โหลดเสียงจากลิงก์นี้ไม่ได้";
    try {
      const reply = await sendJson<SoundImport | Refusal>("POST", `${SOUNDS_PATH}/downloads`, { url });
      if (reply.status === 202) {
        update((s) => ({ ...s, importNotice: null, job: reply.body as SoundImport }));
        return true;
      }
      update((s) => ({ ...s, importNotice: lineOf(title, reply.body) }));
    } catch {
      update((s) => ({ ...s, importNotice: lineOf(title, null) }));
    }
    return false;
  };

  const cancelDownload = async () => {
    const reply = await cancelCurrent<SoundImport>(SOUND_IMPORT_PATH);
    if (reply.kind === "cancelling") update((s) => ({ ...s, job: reply.job }));
  };

  return { state, reload: load, rename, remove, uploadFile, cancelUpload, download, cancelDownload };
}

function epName(user: SoundUser): string {
  const ep = `EP${String(user.n).padStart(2, "0")}`;
  return `${user.series_name} ${ep}${user.title ? ` ${user.title}` : ""}`;
}

function failedNotice(job: SoundImport): Notice {
  return { tone: "error", title: "โหลดเสียงจากลิงก์ไม่สำเร็จ", text: job.error?.message ?? "", setupLink: false };
}
