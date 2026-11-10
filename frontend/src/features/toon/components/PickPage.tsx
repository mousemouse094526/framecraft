import type { ReactNode } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import circleAlert24Icon from "../assets/circle-alert-24.svg";
import infoIcon from "../assets/info.svg";
import loader24Icon from "../assets/loader-24.svg";
import radio18Icon from "../assets/radio-18.svg";
import radioSelected18Icon from "../assets/radio-selected-18.svg";
import { usePickRef } from "../hooks/usePickRef";
import { castHash, isRunning, pendingUrl, REF_PICTURES, type Item, type ItemKind, type ItemRef, type ToonJob } from "../lib/series";
import { ITEM_KINDS } from "../lib/kinds";
import { JobBanner } from "./JobBanner";

const PICTURES = Array.from({ length: REF_PICTURES }, (_, i) => i + 1);

type Props = { itemRef: ItemRef };

/** `#/toon/series/{seriesId}/{itemKind}/{itemId}/pick`: เลือกภาพอ้างอิง (Figma toon / 4). */
export function PickPage({ itemRef }: Props) {
  const { state, choose, pick, retry, cancel, reload } = usePickRef(itemRef);
  const back = castHash(itemRef.seriesId);

  const title = (
    <div className="flex items-center gap-2">
      <a href={back} className={`h-8 px-3 ${GHOST_BUTTON}`}>
        <img src={arrowLeftIcon} alt="" width={16} height={16} />
        กลับ
      </a>
      <h2 className="text-xl leading-[1.5] font-semibold text-foreground">
        เลือกภาพอ้างอิง{state.kind === "ready" ? ` — ${state.item.name}` : ""}
      </h2>
    </div>
  );

  if (state.kind !== "ready") {
    return (
      <PageLayout tab="toon" wide action={state.kind === "offline" && <RefreshButton onClick={() => void reload()} />}>
        {title}
        {state.kind === "offline" ? (
          <OfflinePanel />
        ) : state.kind === "missing" ? (
          <Alert tone="warning">ไม่พบตัวละครหรือฉากหลังนี้แล้ว</Alert>
        ) : (
          <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
        )}
      </PageLayout>
    );
  }

  const { item, job, choice, sending, error } = state;
  const running = job !== null && isRunning(job) ? job : null;
  const ready = item.pending > 0 && running === null;
  const retryButton = (
    <button type="button" disabled={sending} onClick={() => void retry()} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
      สร้างภาพ 3 แบบ
    </button>
  );

  return (
    <PageLayout tab="toon" wide>
      {title}
      {running ? (
        <JobBanner
          kind="running"
          title="กำลังสร้างภาพ 3 แบบ"
          detail="ราว 4.5 นาที · ปิดหน้านี้ได้ งานยังทำต่อ"
          done={running.done ?? 0}
          total={running.total ?? REF_PICTURES}
          stopping={running.cancel_requested}
          onStop={() => void cancel()}
        />
      ) : ready ? (
        <JobBanner kind="done" title="สร้างครบ 3 แบบแล้ว" detail="เลือก 1 แบบแล้วกด ใช้ภาพนี้" />
      ) : job?.state === "failed" ? (
        <JobBanner
          kind="failed"
          title="สร้างภาพไม่สำเร็จ"
          detail={job.error?.message ?? "ลองอีกครั้ง"}
          onRetry={() => void retry()}
        />
      ) : job?.state === "cancelled" ? (
        <Alert tone="info" title="ยกเลิกแล้ว" action={retryButton}>
          หยุดสร้างแล้ว ภาพที่สร้างไม่ครบ 3 แบบไม่ถูกเก็บ
        </Alert>
      ) : (
        <Alert tone="info" action={retryButton}>
          ยังไม่มีภาพรอเลือก
        </Alert>
      )}
      {error && <Alert tone="error">{error}</Alert>}
      <section className="flex flex-col gap-5 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <Subject item={item} />
        <div role="radiogroup" aria-label="เลือกภาพอ้างอิง" className="flex flex-wrap gap-4">
          {PICTURES.map((n) => (
            <Option
              key={n}
              n={n}
              kind={itemRef.itemKind}
              selected={choice === n}
              onChoose={ready ? () => choose(n) : undefined}
            >
              {ready ? (
                <img src={pendingUrl(itemRef, n)} alt="" className="size-full rounded-xl bg-accent-subtle object-contain" />
              ) : (
                <Waiting n={n} job={running ?? job} />
              )}
            </Option>
          ))}
        </div>
        <p className="flex items-center gap-2 text-[13px] leading-[1.5] text-mid">
          <img src={infoIcon} alt="" width={16} height={16} />
          ภาพที่ยังไม่เลือกหายเมื่อปิดแอป
        </p>
        <div className="h-px bg-border" />
        <div className="flex justify-end gap-3">
          <button type="button" disabled={sending} onClick={() => void cancel()} className={`h-9 px-4 ${GHOST_BUTTON}`}>
            ยกเลิก
          </button>
          <button
            type="button"
            disabled={!ready || choice === null || sending}
            onClick={() => choice !== null && void pick(choice)}
            className={`h-9 px-4 ${PRIMARY_BUTTON}`}
          >
            ใช้ภาพนี้
          </button>
        </div>
      </section>
    </PageLayout>
  );
}

function Subject({ item }: { item: Item }) {
  return (
    <div className="flex flex-col gap-1 leading-[1.5]">
      <div className="flex items-center gap-2">
        <p className="text-base font-semibold text-foreground">{item.name}</p>
        {item.tag && <span className="rounded-full bg-muted px-2 py-px font-mono text-xs font-medium text-mid">{item.tag}</span>}
      </div>
      {item.description && <p className="text-[13px] text-mid">{item.description}</p>}
    </div>
  );
}

type OptionProps = { n: number; kind: ItemKind; selected: boolean; onChoose?: () => void; children: ReactNode };

/** Figma `Toon/PickOption`: one of the three pictures as a radio; chosen, a 3px ring and "เลือกแล้ว". */
function Option({ n, kind, selected, onChoose, children }: OptionProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      aria-label={`แบบ ${n}`}
      disabled={!onChoose}
      onClick={onChoose}
      className={`flex w-full flex-col gap-2.5 rounded-2xl bg-card p-2 text-left sm:w-auto ${
        selected ? "border-3 border-brand-accent" : "border border-border"
      }`}
    >
      <div className={ITEM_KINDS[kind].pickSlot}>
        {children}
      </div>
      <span className="flex items-center gap-2 px-1">
        <img src={selected ? radioSelected18Icon : radio18Icon} alt="" width={18} height={18} />
        <span className="flex-1 text-sm leading-[1.5] font-medium text-foreground">แบบ {n}</span>
        {selected && (
          <span className="rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">
            เลือกแล้ว
          </span>
        )}
      </span>
    </button>
  );
}

/** A picture not there to pick: drawing, waiting its turn, or not drawn (a failed or stopped job). */
function Waiting({ n, job }: { n: number; job: ToonJob | null }) {
  const done = job?.done ?? 0;
  if (job !== null && isRunning(job)) {
    return (
      <div className="flex size-full flex-col items-center justify-center gap-2 rounded-xl bg-muted">
        {n === done + 1 && <img src={loader24Icon} alt="" width={24} height={24} className="motion-safe:animate-spin" />}
        <p className="font-mono text-xs font-medium text-mid">{n <= done ? "เสร็จแล้ว" : n === done + 1 ? "กำลังสร้าง" : "รอคิว"}</p>
      </div>
    );
  }
  if (job?.state === "failed") {
    return (
      <div className="flex size-full flex-col items-center justify-center gap-2 rounded-xl bg-error-surface">
        <img src={circleAlert24Icon} alt="" width={24} height={24} />
        <p className="text-[13px] leading-[1.5] text-destructive">แบบนี้สร้างไม่สำเร็จ</p>
      </div>
    );
  }
  return <div className="size-full rounded-xl bg-muted" />;
}
