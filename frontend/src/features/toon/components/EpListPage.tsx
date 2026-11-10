import { useId, useState } from "react";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import plusWhiteIcon from "../../../components/ui/assets/plus-white.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import chevronRightIcon from "../assets/chevron-right.svg";
import film24Icon from "../assets/film-24.svg";
import usersIcon from "../assets/users.svg";
import wandWhiteIcon from "../assets/wand-white.svg";
import { useEpList } from "../hooks/useEpList";
import { epLabel, IDEA_MAX, madeAt, type ListedEp } from "../lib/episodes";
import { castHash, epHash, GENRE_LABELS, LAYOUT_LABELS, LIST_HASH, settingsHash, type Series } from "../lib/series";
import { NoticeLine } from "./NoticeLine";
import { ToonDialog } from "./ToonDialog";

const STAGE_LABELS: Record<ListedEp["stage"], string> = { plot: "พล็อต", cards: "การ์ด" };

/** `#/toon/series/{seriesId}`: a Series' EPs, a new EP from an idea, delete behind a confirm (Figma toon / 5). */
export function EpListPage({ seriesId }: { seriesId: string }) {
  const { state, create, remove, reload } = useEpList(seriesId);
  const [writing, setWriting] = useState(false);
  const [confirming, setConfirming] = useState<ListedEp | null>(null);

  if (state.kind === "offline") {
    return (
      <PageLayout tab="toon" wide action={<RefreshButton onClick={reload} />}>
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

  const { series, eps, notice } = state;
  const newButton = (
    <button type="button" onClick={() => setWriting(true)} className={`flex h-8 items-center gap-2 px-3 ${PRIMARY_BUTTON}`}>
      <img src={plusWhiteIcon} alt="" width={16} height={16} />
      EP ใหม่
    </button>
  );

  return (
    <PageLayout tab="toon" wide>
      <div className="flex flex-wrap items-center gap-2">
        <a href={LIST_HASH} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          การ์ตูนเล่า
        </a>
        <h2 className="text-xl leading-[1.5] font-semibold text-foreground">รายการ EP</h2>
      </div>
      {notice && <NoticeLine notice={notice} />}
      <SeriesHeader series={series} />
      <section aria-label="EP" className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-2">
        <div className="flex items-center gap-2 px-4 py-2">
          <h3 className="min-w-0 flex-1 text-base leading-[1.5] font-semibold text-foreground">EP {eps.length} ตอน</h3>
          {newButton}
        </div>
        {writing && (
          <IdeaForm
            onCancel={() => setWriting(false)}
            onSubmit={async (idea) => {
              if (await create(idea)) setWriting(false);
            }}
          />
        )}
        {eps.length === 0 && !writing ? (
          <div className="flex flex-col items-center gap-2 p-10 text-center">
            <p className="text-base leading-[1.5] font-medium text-foreground">ยังไม่มี EP</p>
            <p className="text-[13px] leading-[1.5] text-mid">พิมพ์ไอเดียสั้นๆ แล้วให้ AI ร่างพล็อต</p>
            {newButton}
          </div>
        ) : (
          <ul className="flex flex-col gap-1">
            {eps.map((ep) => (
              <EpRow key={ep.id} ep={ep} onDelete={() => setConfirming(ep)} />
            ))}
          </ul>
        )}
      </section>
      {confirming && (
        <ToonDialog
          title={`ลบ ${epLabel(confirming.n)} ${confirming.title}?`}
          message="ลบพล็อต การ์ด ภาพการ์ด เสียงเล่า และคลิปที่ render ของ EP นี้ กู้คืนไม่ได้ ตัวละครและฉากหลังยังอยู่ในชุด"
          confirmLabel="ลบ EP"
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

function SeriesHeader({ series }: { series: Series }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-card p-5">
      <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-accent-subtle">
        <img src={film24Icon} alt="" width={24} height={24} />
      </span>
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <p className="truncate text-base leading-[1.5] font-semibold text-foreground">{series.name}</p>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-border px-2 py-0.5 font-button text-xs leading-4 font-medium text-foreground">
            {LAYOUT_LABELS[series.layout]}
          </span>
          <span className="rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">
            {GENRE_LABELS[series.genre]}
          </span>
          <span className="text-[13px] leading-[1.5] text-mid">
            {series.channel_name || "ไม่มีชื่อช่อง"} · ตัวละคร {series.characters.length} · ฉากหลัง {series.backgrounds.length}
          </span>
        </div>
      </div>
      <a href={castHash(series.id)} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
        <img src={usersIcon} alt="" width={16} height={16} />
        ตัวละครและฉากหลัง
      </a>
      <a href={settingsHash(series.id)} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
        ตั้งค่า Series
      </a>
    </div>
  );
}

function IdeaForm({ onCancel, onSubmit }: { onCancel: () => void; onSubmit: (idea: string) => Promise<void> }) {
  const [idea, setIdea] = useState("");
  const [sending, setSending] = useState(false);
  const id = useId();
  const trimmed = idea.trim();
  return (
    <form
      className="flex flex-col gap-3 rounded-xl bg-accent-subtle p-4"
      onSubmit={(event) => {
        event.preventDefault();
        setSending(true);
        void onSubmit(trimmed).finally(() => setSending(false));
      }}
    >
      <div className="flex flex-col gap-2">
        <label htmlFor={id} className="text-sm leading-[1.5] font-medium text-foreground">
          ไอเดียของ EP ใหม่
        </label>
        <textarea
          id={id}
          value={idea}
          maxLength={IDEA_MAX}
          rows={4}
          onChange={(event) => setIdea(event.target.value)}
          className="rounded-lg border border-border bg-card px-3 py-2.5 text-sm leading-[1.5] text-foreground"
        />
        <span className="flex gap-3 text-xs leading-[1.5]">
          <span className="flex-1 text-muted-foreground">AI ร่างพล็อตจากไอเดียนี้ ตามโครงองก์และตัวละครในชุด</span>
          <span className="font-mono text-mid">
            {idea.length} / {IDEA_MAX}
          </span>
        </span>
      </div>
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onCancel} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          ยกเลิก
        </button>
        <button type="submit" disabled={!trimmed || sending} className={`flex h-8 items-center gap-2 px-3 ${PRIMARY_BUTTON}`}>
          <img src={wandWhiteIcon} alt="" width={16} height={16} />
          ให้ AI ร่างพล็อต
        </button>
      </div>
    </form>
  );
}

function EpRow({ ep, onDelete }: { ep: ListedEp; onDelete: () => void }) {
  return (
    <li className="flex h-16 items-center gap-3 rounded-xl px-4 py-3 hover:bg-muted">
      <a href={epHash(ep.id)} className="flex min-w-0 flex-1 items-center gap-3">
        <span className="shrink-0 rounded-lg bg-surface-inverse px-2 py-0.5 font-mono text-xs leading-[1.5] text-card">
          {epLabel(ep.n)}
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5 leading-[1.5]">
          <span className="truncate text-sm font-medium text-foreground">{ep.title || "ยังไม่มีชื่อตอน"}</span>
          <span className="flex items-center gap-1.5 truncate">
            <span className="font-mono text-xs font-medium text-mid">
              ภาพ {ep.images}/{ep.cards}
            </span>
            <span className="text-[13px] text-muted-foreground">·</span>
            <span className="text-[13px] text-mid">{ep.rendered_at ? `render ล่าสุด ${madeAt(ep.rendered_at)}` : "ยังไม่เคย render"}</span>
          </span>
        </span>
        <span className="shrink-0 rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">
          {STAGE_LABELS[ep.stage]}
        </span>
      </a>
      <button
        type="button"
        aria-label={`ลบ ${epLabel(ep.n)}`}
        onClick={onDelete}
        className="flex size-9 shrink-0 items-center justify-center rounded-lg hover:bg-card"
      >
        <img src={trashIcon} alt="" width={16} height={16} />
      </button>
      <img src={chevronRightIcon} alt="" width={20} height={20} className="shrink-0" />
    </li>
  );
}
