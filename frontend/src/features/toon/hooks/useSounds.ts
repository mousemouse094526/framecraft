import { useCallback, useEffect, useRef } from "react";
import { getJson, type FileUpload } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import type { Refusal } from "../../../lib/refusal";
import { useLeaveGuard } from "../../../lib/useHash";
import { usePollWhile } from "../../../lib/usePollWhile";
import { isImporting, SOUND_IMPORT_PATH, SOUNDS_PATH, soundPath, type Sound, type SoundImport } from "../lib/sounds";
import { sendEdit } from "../lib/edit";
import { NOT_NOW, type Notice } from "../lib/notice";
import { sendChecked } from "../lib/upload";
import { useReadyState } from "./useReadyState";

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

/** คลังเสียงพื้น: the library, renaming, deleting, a file's import with its % out, and a link's
 * import polled while it runs (spec › คลังเสียงพื้น, ADR 0028). */
export function useSounds() {
  const [state, setState, update] = useReadyState<SoundsState>({ kind: "loading" });
  const sending = useRef<FileUpload<Sound | Refusal> | null>(null);

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

  const rename = async (sound: Sound, name: string) => {
    const reply = await sendEdit<Sound>("PATCH", soundPath(sound.id), { name }, `เปลี่ยนชื่อ ${sound.name} ไม่ได้`, {
      warnings: NOT_NOW,
    });
    if (reply.kind === "refused") {
      update((s) => ({ ...s, listNotice: reply.notice }));
      return false;
    }
    const renamed = reply.value;
    update((s) => ({ ...s, listNotice: null, sounds: s.sounds.map((x) => (x.id === renamed.id ? renamed : x)) }));
    return true;
  };

  const remove = async (sound: Sound) => {
    const title = `ลบ ${sound.name} ไม่ได้`;
    const reply = await sendEdit<null, Refusal & { eps?: SoundUser[] }>("DELETE", soundPath(sound.id), undefined, title, {
      ok: [204],
      warnings: NOT_NOW,
    });
    if (reply.kind === "ok") {
      update((s) => ({ ...s, listNotice: null, sounds: s.sounds.filter((x) => x.id !== sound.id) }));
      return;
    }
    // `in_use` names the EPs that still play it
    const eps = reply.refusal?.eps;
    const notice = eps?.length ? { ...reply.notice, text: `ยังใช้อยู่ใน ${eps.map(epName).join(", ")}` } : reply.notice;
    update((s) => ({ ...s, listNotice: notice }));
  };

  /** `/imports/check` first, then the file as the raw body (ADR 0028); the answer is the new sound. */
  const uploadFile = async (file: File) => {
    const toSend = {
      path: `${SOUNDS_PATH}/imports`,
      checkBody: { name: file.name, size: file.size },
      query: `name=${encodeURIComponent(file.name)}&size=${file.size}`,
    };
    const reply = await sendChecked<Sound>({ ...toSend, file, title: `เอาไฟล์ ${file.name} เข้าไม่ได้`, warnings: NOT_NOW }, {
      started: (upload) => {
        sending.current = upload;
        update((s) => ({ ...s, importNotice: null, upload: { name: file.name, percent: 0 } }));
      },
      progress: (percent) => update((s) => ({ ...s, upload: s.upload && { ...s.upload, percent } })),
    });
    sending.current = null;
    update((s) => {
      const done = { ...s, upload: null };
      if (reply.kind === "sent") return { ...done, sounds: [...s.sounds, reply.value] };
      return reply.kind === "refused" ? { ...done, importNotice: reply.notice } : done;
    });
  };

  const cancelUpload = () => sending.current?.abort();

  const download = async (url: string) => {
    const reply = await sendEdit<SoundImport>("POST", `${SOUNDS_PATH}/downloads`, { url }, "โหลดเสียงจากลิงก์นี้ไม่ได้", {
      ok: [202],
      warnings: NOT_NOW,
    });
    update((s) => (reply.kind === "ok" ? { ...s, importNotice: null, job: reply.value } : { ...s, importNotice: reply.notice }));
    return reply.kind === "ok";
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
