import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { epPath, type Ep, type LostCards } from "../lib/episodes";
import { SOUNDS_PATH, type Sound } from "../lib/sounds";
import { epHash, JOB_PATH, JOBS_PATH, seriesPath, type ImageScope, type MissingRef, type Series, type ToonJob } from "../lib/series";
import { sendEdit } from "../lib/edit";
import { noticeOf, NOT_NOW, type Notice } from "../lib/notice";
import { cancelToonJob, useToonJobPoll } from "./useToonJobPoll";
import { useReadyState } from "./useReadyState";

export type EpState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "ready";
      ep: Ep;
      series: Series;
      /** The background sound library, for each segment's sound (D16). */
      sounds: Sound[];
      /** The latest Toon job, whatever it works on: a running one disables every start. */
      job: ToonJob | null;
      notice: Notice | null;
      /** `cards_will_be_lost`: what each act would lose, until the user confirms or cancels (D43). */
      lost: LostCards[] | null;
      /** `nothing_to_draw`: what has no reference image yet, until another job starts (D13). */
      missing: MissingRef[] | null;
      /** Goes up with every read of the EP, so a card picture or narration made since loads again. */
      version: number;
    };

/**
 * An EP: its plot (Plot job, edits, confirm), its storyline (acts, segments, cards and their
 * edits), the Cards job that splits the plot, and the Image and Voice jobs of its cards (spec ›
 * Plot job, › Cards job, › Image job, › Voice job). While a Plot or Cards job of this EP runs,
 * the page closes every field; a job that ends reads the EP again, and so does each picture drawn.
 */
export function useEp(epId: string) {
  const [state, setState, update] = useReadyState<EpState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const [ep, job, sounds] = await Promise.all([
        getJson<Ep>(epPath(epId)),
        getJson<ToonJob | null>(JOB_PATH),
        getJson<Sound[]>(SOUNDS_PATH),
      ]);
      const series = await getJson<Series>(seriesPath(ep.series_id));
      setState((s) => ({
        kind: "ready",
        ep,
        series,
        sounds,
        job,
        notice: s.kind === "ready" ? s.notice : null,
        lost: s.kind === "ready" ? s.lost : null,
        missing: s.kind === "ready" ? s.missing : null,
        version: s.kind === "ready" ? s.version + 1 : 0,
      }));
    } catch {
      setState({ kind: "offline" });
    }
  }, [epId, setState]);

  useEffect(() => {
    void load();
  }, [load]);

  const job = state.kind === "ready" ? state.job : null;
  useToonJobPoll(
    job,
    (next) => {
      // A picture of this EP is written as soon as it is drawn: read the EP for it (spec › Frontend).
      // `job` is the previous poll's answer, so a `done` that moved means one more picture.
      const drew = next.kind === "image" && next.ep_id === epId && next.state === "drawing" && next.done !== job?.done;
      update((s) => ({ ...s, job: next }));
      if (drew) void load();
    },
    (next) => {
      // A Cards job of this EP that is done opens the storyline (the plot page may be open).
      if (next?.kind === "cards" && next.ep_id === epId && next.state === "done") window.location.hash = epHash(epId);
      void load();
    },
    () => setState({ kind: "offline" }),
  );

  const refused = (title: string, body: unknown, warnings: readonly string[] = []) => {
    update((s) => ({ ...s, notice: noticeOf(title, body, warnings) }));
  };

  /** An edit: its answer is the EP as it is now; a refusal becomes the notice. */
  const edit = async (method: string, path: string, body: unknown, title = "บันทึกไม่ได้") => {
    const reply = await sendEdit<Ep>(method, `${epPath(epId)}${path}`, body, title);
    update((s) => (reply.kind === "saved" ? { ...s, ep: reply.value, notice: null } : { ...s, notice: reply.notice }));
    return reply.kind === "saved";
  };

  const start = async (body: Record<string, unknown>, title: string) => {
    try {
      const reply = await sendJson<ToonJob | Refusal>("POST", JOBS_PATH, { ep_id: epId, ...body });
      if (reply.status === 202) {
        update((s) => ({ ...s, job: reply.body as ToonJob, notice: null, lost: null, missing: null }));
        void load(); // the EP reads as locked now
        return;
      }
      const refusal = refusalOf(reply.body) as (Refusal & { acts?: LostCards[]; missing_refs?: MissingRef[] }) | null;
      if (refusal?.code === "cards_will_be_lost") return update((s) => ({ ...s, lost: refusal.acts ?? [] }));
      // `nothing_to_draw` lists the missing references and shows its notice too
      if (refusal?.code === "nothing_to_draw") update((s) => ({ ...s, missing: refusal.missing_refs ?? [] }));
      refused(title, reply.body, [...NOT_NOW, "nothing_to_split", "nothing_to_draw"]);
    } catch {
      refused(title, null);
    }
  };

  const cancelJob = () => cancelToonJob((job) => update((s) => ({ ...s, job })));

  return {
    state,
    reload: load,
    edit,
    startPlot: () => start({ kind: "plot" }, "ยังร่างพล็อตไม่ได้"),
    /** First without `confirm_loss`: a `cards_will_be_lost` answer opens the confirm (D43). */
    startCards: (confirmLoss = false) => start({ kind: "cards", confirm_loss: confirmLoss }, "ยังแตกการ์ดไม่ได้"),
    closeLost: () => update((s) => ({ ...s, lost: null })),
    /** Every card with no image, or every `stale_ref` one (D33, D44). */
    startImages: (scope: ImageScope) => start({ kind: "image", scope }, "ยังสร้างภาพไม่ได้"),
    startImage: (cardId: string) => start({ kind: "image", card_id: cardId }, "ยังสร้างภาพไม่ได้"),
    startVoice: (cardId: string) => start({ kind: "voice", card_id: cardId }, "ยังสร้างเสียงไม่ได้"),
    swapImage: async (cardId: string) => {
      if (await edit("POST", `/cards/${cardId}/swap-image`, {}, "สลับภาพไม่ได้")) update((s) => ({ ...s, version: s.version + 1 }));
    },
    cancelJob,
  };
}
