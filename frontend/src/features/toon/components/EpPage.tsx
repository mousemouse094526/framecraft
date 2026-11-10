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

type EpJobKind = Exclude<ToonJob["kind"], "ref">;
type EpJob = ToonJob & { kind: EpJobKind };
const FAILED_TITLES: Record<EpJobKind, string> = {
  plot: "ร่างพล็อตไม่สำเร็จ",
  cards: "แตกการ์ดไม่สำเร็จ",
  image: "สร้างภาพไม่สำเร็จ",
  voice: "สร้างเสียงเล่าไม่สำเร็จ",
};

/** The latest job of this EP, or null. */
function epJobOf(job: ToonJob | null, epId: string): EpJob | null {
  if (job === null || job.ep_id !== epId || job.kind === "ref") return null;
  return { ...job, kind: job.kind }; // the copy carries `kind` narrowed past "ref"
}

/** What the running banner says of each job of this EP (Figma toon / 7 › Image job running). */
function runningText(job: EpJob): { title: string; detail: string } {
  if (job.kind === "plot") return { title: "AI กำลังร่างพล็อต", detail: "แก้ได้อีกครั้งเมื่อเสร็จ · ปิดหน้านี้ได้ งานยังทำต่อ" };
  if (job.kind === "cards") return { title: "AI กำลังเขียนการ์ด", detail: "แก้ได้อีกครั้งเมื่อเสร็จ · ปิดหน้านี้ได้ งานยังทำต่อ" };
  if (job.kind === "voice") return { title: "กำลังสร้างเสียงเล่า", detail: "ปิดหน้านี้ได้ งานยังทำต่อ" };
  const skipped = job.skipped ? ` ข้าม ${job.skipped}` : "";
  if (job.state === "translating") {
    return { title: `AI กำลังแปลคำบรรยายภาพ${skipped}`, detail: "แล้วจึงเริ่มวาด · ปิดหน้านี้ได้ งานยังทำต่อ" };
  }
  return {
    title: `กำลังสร้างภาพ ${job.done ?? 0}/${job.total ?? 0}${skipped}`,
    detail: "ภาพขึ้นทีละใบ · ข้ามการ์ดที่ยังไม่มีภาพอ้างอิง",
  };
}

/** `#/toon/eps/{epId}`: the plot until it is confirmed, then the storyline; `/plot` opens the
 * plot either way (Figma toon / 6, 7). A Plot or Cards job of this EP closes every field. */
export function EpPage({ epId, plot }: { epId: string; plot: boolean }) {
  const { state, reload, edit, startPlot, startCards, closeLost, cancelJob, ...cardJobs } = useEp(epId);

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

  const { ep, series, sounds, job, notice, lost, missing, version } = state;
  const own = epJobOf(job, epId);
  const running = own !== null && isRunning(own) ? own : null;
  const locked = ep.locked || (running !== null && (running.kind === "plot" || running.kind === "cards"));
  const failedCards = own?.kind === "image" && own.state === "done" ? (own.failed_cards ?? []) : [];
  const showPlot = plot || ep.stage === "plot";
  const busy = job !== null && isRunning(job);

  /** ลองอีกครั้ง: the failed job again, as it was asked. */
  function retry(failed: EpJob) {
    if (failed.kind === "plot") return startPlot();
    if (failed.kind === "cards") return startCards();
    if (failed.kind === "voice") return cardJobs.startVoice(failed.card_ids?.[0] ?? "");
    return failed.scope ? cardJobs.startImages(failed.scope) : cardJobs.startImage(failed.card_ids?.[0] ?? "");
  }

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
          <a href={showPlot ? epHash(epId) : plotHash(epId)} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
            {showPlot ? "ไปเส้นเรื่อง" : "แก้พล็อต"}
          </a>
        )}
      </div>
      {notice && <NoticeLine notice={notice} />}
      {running && (
        <JobBanner
          kind="running"
          {...runningText(running)}
          done={running.done ?? 0}
          total={running.total ?? 1}
          stopping={running.cancel_requested}
          onStop={() => void cancelJob()}
        />
      )}
      {own?.state === "failed" && (
        <JobBanner
          kind="failed"
          title={FAILED_TITLES[own.kind]}
          detail={own.error?.message ?? ""}
          onRetry={() => void retry(own)}
        />
      )}
      {failedCards.length > 0 && (
        <NoticeLine
          notice={{
            tone: "warning",
            title: `วาดไม่สำเร็จ ${failedCards.length} การ์ด`,
            text: "กดสร้างภาพที่ขาดทั้งหมดอีกครั้ง หรือสร้างภาพใหม่ที่การ์ดนั้น",
            setupLink: false,
          }}
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
        <StorylineView
          ep={ep}
          series={series}
          sounds={sounds}
          locked={locked}
          edit={edit}
          job={own}
          busy={busy}
          missing={own?.kind === "image" ? (own.missing_refs ?? missing) : missing}
          skipped={own?.kind === "image" ? (own.skipped ?? 0) : null}
          version={version}
          jobs={cardJobs}
        />
      )}
    </PageLayout>
  );
}
