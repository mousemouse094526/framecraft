import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { useEp } from "../hooks/useEp";
import { epLabel } from "../lib/episodes";
import { epHash, isRunning, plotHash, seriesHash, type ToonJob } from "../lib/series";
import { NoticeLine } from "./NoticeLine";
import { JobBanner } from "./JobBanner";
import { PlotView } from "./PlotView";
import { StorylineView } from "./StorylineView";

type WritingKind = Extract<ToonJob["kind"], "plot" | "cards">;
const JOB_TITLES: Record<WritingKind, string> = { plot: "AI กำลังร่างพล็อต", cards: "AI กำลังเขียนการ์ด" };
const FAILED_TITLES: Record<WritingKind, string> = { plot: "ร่างพล็อตไม่สำเร็จ", cards: "แตกการ์ดไม่สำเร็จ" };

/** The latest Plot or Cards job of this EP, or null. */
function writingJobOf(job: ToonJob | null, eid: string): (ToonJob & { kind: WritingKind }) | null {
  if (job === null || job.ep_id !== eid || job.kind === "ref") return null;
  return { ...job, kind: job.kind }; // the copy carries `kind` narrowed past "ref"
}

/** `#/toon/eps/{eid}`: the plot until it is confirmed, then the storyline; `/plot` opens the
 * plot either way (Figma toon / 6, 7). A Plot or Cards job of this EP closes every field. */
export function EpPage({ eid, plot }: { eid: string; plot: boolean }) {
  const { state, reload, edit, startPlot, startCards, closeLost, cancelJob } = useEp(eid);

  if (state.kind === "offline") {
    return (
      <PageLayout tab="toon" wide action={<RefreshButton onClick={() => void reload()} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }
  if (state.kind === "loading") {
    return (
      <PageLayout tab="toon" wide>
        <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
      </PageLayout>
    );
  }

  const { ep, series, job, notice, lost } = state;
  const own = writingJobOf(job, eid);
  const writing = own !== null && isRunning(own) ? own : null;
  const locked = ep.locked || writing !== null;
  const showPlot = plot || ep.stage === "plot";
  const busy = job !== null && isRunning(job);

  return (
    <PageLayout tab="toon" wide>
      <div className="flex flex-wrap items-center gap-2">
        <a href={seriesHash(series.id)} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          {series.name}
        </a>
        <h2 className="min-w-0 flex-1 text-xl leading-[1.5] font-semibold text-foreground">
          {epLabel(ep.n)} — {showPlot ? "พล็อต" : "เส้นเรื่อง"}
        </h2>
        {ep.stage === "cards" && (
          <a href={showPlot ? epHash(eid) : plotHash(eid)} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
            {showPlot ? "ไปเส้นเรื่อง" : "แก้พล็อต"}
          </a>
        )}
      </div>
      {notice && <NoticeLine notice={notice} />}
      {writing && (
        <JobBanner
          kind="running"
          title={JOB_TITLES[writing.kind]}
          detail="แก้ได้อีกครั้งเมื่อเสร็จ · ปิดหน้านี้ได้ งานยังทำต่อ"
          done={writing.done ?? 0}
          total={writing.total ?? 1}
          stopping={writing.cancel_requested}
          onStop={() => void cancelJob()}
        />
      )}
      {own?.state === "failed" && (
        <JobBanner
          kind="failed"
          title={FAILED_TITLES[own.kind]}
          detail={own.error?.message ?? ""}
          onRetry={() => void (own.kind === "plot" ? startPlot() : startCards())}
        />
      )}
      {showPlot ? (
        <PlotView
          ep={ep}
          series={series}
          locked={locked}
          busy={busy}
          lost={lost}
          edit={edit}
          onDraft={() => void startPlot()}
          onSplit={(confirmLoss) => void startCards(confirmLoss)}
          onCloseLost={closeLost}
        />
      ) : (
        <StorylineView ep={ep} series={series} locked={locked} edit={edit} />
      )}
    </PageLayout>
  );
}
