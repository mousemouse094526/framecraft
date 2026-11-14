import { useState } from "react";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import plusWhiteIcon from "../../../components/ui/assets/plus-white.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import musicIcon from "../../../components/ui/assets/music.svg";
import chevronRightIcon from "../assets/chevron-right.svg";
import film24Icon from "../assets/film-24.svg";
import filmIcon from "../assets/film.svg";
import { useSeriesList } from "../hooks/useSeriesList";
import { soundsHash } from "../../sound-library/lib/sounds";
import { LAYOUT_LABELS, LIST_HASH, NEW_HASH, seriesHash, type ListedSeries } from "../lib/series";
import { NoticeLine } from "../../../components/ui/NoticeLine";
import { ToonDialog } from "./ToonDialog";

/** `#/toon`: the Series, each a link to its page, with delete behind a confirm (Figma toon / 1). */
export function SeriesList() {
  const { state, remove, reload } = useSeriesList();
  const [confirming, setConfirming] = useState<ListedSeries | null>(null);

  if (state.kind === "offline") {
    return (
      <PageLayout tab="toon" wide action={<RefreshButton onClick={reload} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  return (
    <PageLayout tab="toon" wide>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="min-w-0 flex-1 text-xl leading-[1.5] font-semibold text-foreground">การ์ตูนเล่า</h2>
        <a href={soundsHash(LIST_HASH)} className={`h-9 px-4 ${OUTLINE_BUTTON}`}>
          <img src={musicIcon} alt="" width={16} height={16} />
          คลังเสียง
        </a>
        <NewSeriesLink />
      </div>
      {state.kind === "result" && state.notice && <NoticeLine notice={state.notice} />}
      {state.kind === "loading" ? (
        <Loading />
      ) : state.series.length === 0 ? (
        <Empty />
      ) : (
        <section aria-label="ชุดการ์ตูน" className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-2">
          <p className="px-4 py-2 text-[13px] leading-[1.5] text-mid">ชุดการ์ตูน {state.series.length} ชุด</p>
          <ul className="flex flex-col gap-1">
            {state.series.map((series) => (
              <SeriesRow key={series.id} series={series} onDelete={() => setConfirming(series)} />
            ))}
          </ul>
        </section>
      )}
      {confirming && (
        <ToonDialog
          title={`ลบชุด ${confirming.name}?`}
          message={`ลบชุดนี้และ EP ทั้งหมด ${confirming.ep_count} ตอน? กู้คืนไม่ได้ Saved voice และคลังเสียงยังอยู่`}
          confirmLabel="ลบชุด"
          destructive
          onClose={() => setConfirming(null)}
          onConfirm={() => {
            setConfirming(null);
            void remove(confirming);
          }}
        />
      )}
    </PageLayout>
  );
}

function NewSeriesLink() {
  return (
    <a href={NEW_HASH} className={`h-9 px-4 ${PRIMARY_BUTTON}`}>
      <img src={plusWhiteIcon} alt="" width={16} height={16} />
      สร้าง Series
    </a>
  );
}

function SeriesRow({ series, onDelete }: { series: ListedSeries; onDelete: () => void }) {
  return (
    <li className="flex h-16 items-center gap-3 rounded-xl px-4 py-3 hover:bg-muted">
      <a href={seriesHash(series.id)} className="flex min-w-0 flex-1 items-center gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent-subtle">
          <img src={filmIcon} alt="" width={20} height={20} />
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5 leading-[1.5]">
          <span className="truncate text-sm font-medium text-foreground">{series.name}</span>
          <span className="flex items-center gap-1.5 truncate">
            <span className="text-[13px] text-mid">{series.channel_name || "ไม่มีชื่อช่อง"}</span>
            <span className="text-[13px] text-muted-foreground">·</span>
            <span className="font-mono text-xs font-medium text-mid">{series.ep_count} EP</span>
          </span>
        </span>
        <span className="shrink-0 rounded-full border border-border px-2 py-0.5 font-button text-xs leading-4 font-medium text-foreground">
          {LAYOUT_LABELS[series.layout]}
        </span>
      </a>
      <button
        type="button"
        aria-label={`ลบชุด ${series.name}`}
        onClick={onDelete}
        className="flex size-9 shrink-0 items-center justify-center rounded-lg hover:bg-card"
      >
        <img src={trashIcon} alt="" width={16} height={16} />
      </button>
      <img src={chevronRightIcon} alt="" width={20} height={20} className="shrink-0" />
    </li>
  );
}

function Empty() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-border bg-card p-12 text-center">
      <span className="flex size-14 items-center justify-center rounded-full bg-accent-subtle">
        <img src={film24Icon} alt="" width={24} height={24} />
      </span>
      <p className="text-base leading-[1.5] font-medium text-foreground">ยังไม่มีชุด สร้างชุดแรกเพื่อเริ่มทำการ์ตูนเล่า</p>
      <p className="text-[13px] leading-[1.5] text-mid">ชุดเก็บแบบจอ สไตล์ภาพ ตัวละคร และฉากหลังไว้ใช้ซ้ำทุก EP</p>
      <NewSeriesLink />
    </div>
  );
}

function Loading() {
  return (
    <div aria-busy="true" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-6">
      {[0, 1, 2].map((row) => (
        <div key={row} className="flex items-center gap-3">
          <div className="size-10 rounded-lg bg-muted" />
          <div className="flex flex-col gap-2">
            <div className="h-3 w-60 rounded-full bg-muted" />
            <div className="h-2.5 w-40 rounded-full bg-muted" />
          </div>
        </div>
      ))}
      <p className="text-[13px] leading-[1.5] text-mid">กำลังโหลดชุดการ์ตูน…</p>
    </div>
  );
}
