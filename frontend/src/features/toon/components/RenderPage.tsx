import { useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import chevronRightIcon from "../assets/chevron-right-16.svg";
import downloadIcon from "../../../components/ui/assets/download.svg";
import filmIcon from "../assets/film.svg";
import filmWhiteIcon from "../assets/film-white.svg";
import playIcon from "../assets/play.svg";
import { isRendering, renderFilePath, useRender, type RenderJob, type RenderResult } from "../hooks/useRender";
import { cannotRender, cardsOf, epLabel, madeAt, type Ep } from "../lib/episodes";
import { epHash, LAYOUT_LABELS, type Series } from "../lib/series";
import { JobBanner } from "./JobBanner";
import { NoticeLine } from "./NoticeLine";

const FAILED_TITLE = "render ไม่สำเร็จ";

/** `#/toon/eps/{eid}/render`: render the EP and its clips (Figma toon / 9, D38, D45). */
export function RenderPage({ eid }: { eid: string }) {
  const { state, reload, start, cancel, remove } = useRender(eid);

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

  const { ep, series, job, renders, notice, notReady } = state;
  const cards = cardsOf(ep);
  const numbered = cards.map((card, index) => ({ card, number: index + 1 }));
  // The page knows the cards with no picture before the API says so (spec › Render job step 1).
  const missing = notReady ?? cards.filter(cannotRender).map((c) => c.id);
  const blocked = ep.stage !== "cards" || cards.length === 0 || missing.length > 0;
  const running = job !== null && isRendering(job) ? job : null;
  const own = job?.ep_id === eid ? job : null;

  return (
    <PageLayout tab="toon" wide>
      <div className="flex flex-wrap items-center gap-2">
        <a href={epHash(eid)} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          เส้นเรื่อง
        </a>
        <h2 className="min-w-0 text-xl leading-[1.5] font-semibold text-foreground">
          {epLabel(ep.n)} {ep.title} — render
        </h2>
      </div>
      {notice && <NoticeLine notice={notice} />}
      <section aria-label="render" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex min-w-0 flex-1 flex-col gap-0.5 leading-[1.5]">
            <h3 className="text-base font-semibold text-foreground">{blocked ? "ยังไม่พร้อม render" : "พร้อม render"}</h3>
            <p className="text-[13px] text-mid">{summary(ep, series)}</p>
          </div>
          <button
            type="button"
            disabled={blocked || running !== null}
            onClick={() => void start()}
            className={`h-9 px-4 ${PRIMARY_BUTTON}`}
          >
            <img src={filmWhiteIcon} alt="" width={16} height={16} />
            render
          </button>
        </div>
        {running && running.ep_id === eid && (
          <JobBanner kind="running" {...runningText(running)} stopping={running.cancel_requested} onStop={() => void cancel()} />
        )}
        {running && running.ep_id !== eid && (
          <Alert tone="warning" title="มี render ของ EP อื่นอยู่">
            รอให้เสร็จก่อน แล้วจึง render EP นี้
          </Alert>
        )}
        {own?.state === "failed" && (
          <JobBanner kind="failed" title={FAILED_TITLE} detail={own.error?.message ?? ""} onRetry={() => void start()} />
        )}
        {missing.length > 0 && (
          <>
            <Alert tone="error" title={`การ์ด ${missing.length} ใบยังไม่มีภาพ`}>
              render ได้เมื่อทุกการ์ดมีภาพ กดเพื่อไปที่การ์ดนั้น
            </Alert>
            <div className="flex flex-wrap gap-1">
              {numbered
                .filter(({ card }) => missing.includes(card.id))
                .map(({ card, number }) => (
                  <a key={card.id} href={epHash(eid)} className={`h-8 px-3 ${GHOST_BUTTON}`}>
                    <img src={chevronRightIcon} alt="" width={16} height={16} />
                    ไปที่การ์ด {number}
                  </a>
                ))}
            </div>
          </>
        )}
      </section>
      <section aria-label="คลิปที่ render แล้ว" className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-2">
        <h3 className="px-4 py-2 text-base leading-[1.5] font-semibold text-foreground">
          คลิปที่ render แล้ว {renders.length} คลิป
        </h3>
        {renders.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 text-center leading-[1.5]">
            <img src={filmIcon} alt="" width={24} height={24} />
            <p className="text-base font-medium text-foreground">ยังไม่มีคลิปของ EP นี้</p>
            <p className="text-[13px] text-muted-foreground">กด render แล้วคลิปจะขึ้นที่นี่</p>
          </div>
        ) : (
          <ul className="flex flex-col gap-1">
            {renders.map((result) => (
              <ClipRow key={result.name} eid={eid} result={result} onDelete={() => void remove(result)} />
            ))}
          </ul>
        )}
      </section>
    </PageLayout>
  );
}

/** "30 การ์ด · 84 วิ · กรอบดำ 1080×1920 · เสียงเล่าครบ 25/30 (ที่ขาดสร้างให้ตอน render)" */
function summary(ep: Ep, series: Series): string {
  const cards = cardsOf(ep);
  const spoken = cards.filter((card) => card.audio_status !== "silent");
  const voiced = spoken.filter((card) => card.audio_status === "ready").length;
  const voices =
    voiced === spoken.length ? "เสียงเล่าครบ" : `เสียงเล่าครบ ${voiced}/${spoken.length} (ที่ขาดสร้างให้ตอน render)`;
  return `${cards.length} การ์ด · ${Math.round(ep.duration_s)} วิ · ${LAYOUT_LABELS[series.layout]} 1080×1920 · ${voices}`;
}

function runningText(job: RenderJob) {
  if (job.state === "voicing") {
    return {
      title: "กำลังสร้างเสียงเล่าที่ขาด",
      detail: "แล้วจึง render · ปิดหน้านี้ได้ งานยังทำต่อ",
      done: job.done ?? 0,
      total: job.total ?? 1,
    };
  }
  const percent = job.percent ?? 0;
  return { title: "กำลัง render", detail: "ปิดหน้านี้ได้ งานยังทำต่อ", done: percent, total: 100, count: `${percent}%` };
}

/** The file name a download saves as: `ep03-คืนที่ไฟดับ-20261108-214000.mp4`. */
function downloadName(result: RenderResult): string {
  const title = result.title.trim().replace(/[\\/:*?"<>|\s]+/g, "-");
  return `${epLabel(result.n).toLowerCase()}${title ? `-${title}` : ""}-${result.name}.mp4`;
}

/** Figma `Toon/ClipRow`: a 9:16 thumbnail, the file name, length and time; เล่น, ดาวน์โหลด, ลบ. */
function ClipRow({ eid, result, onDelete }: { eid: string; result: RenderResult; onDelete: () => void }) {
  const [playing, setPlaying] = useState(false);
  const file = renderFilePath(eid, result.name);
  const name = downloadName(result);
  return (
    <li aria-label={name} className="flex flex-col gap-2 rounded-xl px-4 py-2.5">
      <div className="flex flex-wrap items-center gap-3">
        <span aria-hidden className="relative h-16 w-9 shrink-0 overflow-hidden rounded-lg bg-black">
          <span className="absolute top-[7px] left-1 h-[3px] w-[22px] bg-white" />
          <span className="absolute top-[22px] left-0 h-5 w-9 bg-accent-subtle" />
          <span className="absolute top-14 left-2.5 h-0.5 w-4 bg-white" />
        </span>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5 leading-[1.5]">
          <p className="truncate text-sm font-medium text-foreground">
            {epLabel(result.n)} {result.title}
          </p>
          <p className="truncate font-mono text-xs font-medium text-mid">{name}</p>
          <p className="text-xs text-muted-foreground">
            {Math.round(result.duration_s)} วิ · 1080×1920 · {madeAt(result.created_at)}
          </p>
        </div>
        <button type="button" onClick={() => setPlaying((p) => !p)} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={playIcon} alt="" width={16} height={16} />
          {playing ? "ปิด" : "เล่น"}
        </button>
        <a href={file} download={name} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
          <img src={downloadIcon} alt="" width={16} height={16} />
          ดาวน์โหลด
        </a>
        <button
          type="button"
          aria-label={`ลบคลิป ${name}`}
          onClick={onDelete}
          className="flex size-9 items-center justify-center rounded-lg hover:bg-muted"
        >
          <img src={trashIcon} alt="" width={16} height={16} />
        </button>
      </div>
      {playing && <video src={file} controls autoPlay className="max-h-[480px] w-auto self-center rounded-lg bg-black" />}
    </li>
  );
}
