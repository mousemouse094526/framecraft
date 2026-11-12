import { useRef, useState, type ReactNode } from "react";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import plusIcon from "../../../components/ui/assets/plus.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import loader24Icon from "../assets/loader-24.svg";
import uploadIcon from "../assets/upload.svg";
import wandIcon from "../assets/wand.svg";
import { useCast, type ItemFields } from "../hooks/useCast";
import { NoticeLine } from "./NoticeLine";
import {
  DESCRIPTION_MAX,
  isRunning,
  ITEM_NAME_MAX,
  pickHash,
  REF_PICTURES,
  refUrl,
  seriesHash,
  settingsHash,
  TAG_MAX,
  type Item,
  type ItemKind,
  type ItemRef,
  type Series,
  type ToonJob,
} from "../lib/series";
import { ITEM_KINDS } from "../lib/kinds";
import { JobBanner } from "./JobBanner";
import { ToonDialog } from "./ToonDialog";

const SECONDS_PER_PICTURE = 90; // a Ref job's picture on an M1, ~4.5 min for three (D31)

/** `#/toon/series/{seriesId}`: ตัวละครและฉากหลัง of a Series (Figma toon / 3). */
export function CastPage({ seriesId }: { seriesId: string }) {
  const { state, add, remove, startRef, cancelJob, upload, reload } = useCast(seriesId);

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

  const { series, job, notice, upload: sending } = state;
  const running = job !== null && isRunning(job) && job.series_id === seriesId ? job : null;
  const actions = {
    running,
    sending,
    onRemove: remove,
    onStartRef: (kind: ItemKind, item: Item) => void startRef(kind, item),
    onUpload: (kind: ItemKind, item: Item, file: File) => void upload(kind, item, file),
  };

  return (
    <PageLayout tab="toon" wide>
      <div className="flex flex-wrap items-center gap-2">
        <a href={seriesHash(seriesId)} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          กลับไปที่ชุด
        </a>
        <h2 className="min-w-0 flex-1 text-xl leading-[1.5] font-semibold text-foreground">
          ตัวละครและฉากหลัง — {series.name}
        </h2>
        <a href={settingsHash(seriesId)} className={`h-9 px-4 ${OUTLINE_BUTTON}`}>
          ตั้งค่า Series
        </a>
      </div>
      {notice && <NoticeLine notice={notice} />}
      {running && <RunningBanner job={running} series={series} onStop={() => void cancelJob()} />}
      <ItemSection kind="characters" series={series} onAdd={add} {...actions} />
      <ItemSection kind="backgrounds" series={series} onAdd={add} {...actions} />
    </PageLayout>
  );
}

function RunningBanner({ job, series, onStop }: { job: ToonJob; series: Series; onStop: () => void }) {
  const item = [...series.characters, ...series.backgrounds].find((i) => i.id === job.item_id);
  return (
    <JobBanner
      kind="running"
      title={`กำลังสร้างภาพอ้างอิง ${item?.name ?? ""}`}
      detail="ราว 4.5 นาที · ปิดหน้านี้ได้ งานยังทำต่อ"
      done={job.done ?? 0}
      total={job.total ?? REF_PICTURES}
      stopping={job.cancel_requested}
      onStop={onStop}
    />
  );
}

type Actions = {
  running: ToonJob | null;
  sending: { id: string; percent: number } | null;
  onRemove: (kind: ItemKind, item: Item) => void;
  onStartRef: (kind: ItemKind, item: Item) => void;
  onUpload: (kind: ItemKind, item: Item, file: File) => void;
};

type SectionProps = Actions & {
  kind: ItemKind;
  series: Series;
  onAdd: (kind: ItemKind, fields: ItemFields) => Promise<boolean>;
};

function ItemSection({ kind, series, onAdd, ...actions }: SectionProps) {
  const [adding, setAdding] = useState(false);
  const items = series[kind];
  const look = ITEM_KINDS[kind];

  return (
    <section aria-label={look.name} className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <div className="flex items-center gap-2">
        <h3 className="text-base leading-[1.5] font-semibold text-foreground">{look.name}</h3>
        <span className="font-mono text-xs text-mid">{items.length}</span>
        <div className="flex-1" />
        <button type="button" disabled={adding} onClick={() => setAdding(true)} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
          <img src={plusIcon} alt="" width={16} height={16} />
          {look.add}
        </button>
      </div>
      {items.length === 0 && !adding ? (
        <div className="flex flex-col items-center gap-2 rounded-xl bg-muted py-8 text-center leading-[1.5]">
          <img src={look.icon} alt="" width={24} height={24} />
          <p className="text-sm font-medium text-foreground">{look.empty}</p>
          <p className="text-[13px] text-mid">AI จะเสนอ{look.name}ให้ตอนร่างพล็อต หรือเพิ่มเองได้</p>
        </div>
      ) : (
        <ul className="flex flex-wrap gap-4">
          {items.map((item) => (
            <RefTile key={item.id} itemRef={{ seriesId: series.id, itemKind: kind, itemId: item.id }} item={item} {...actions} />
          ))}
          {adding && (
            <ItemForm
              kind={kind}
              onCancel={() => setAdding(false)}
              onAdd={async (fields) => {
                if (await onAdd(kind, fields)) setAdding(false);
              }}
            />
          )}
        </ul>
      )}
    </section>
  );
}

type TileProps = Actions & { itemRef: ItemRef; item: Item };

/** Figma `Toon/RefTile`: the reference image (or why there is none), name, tag, description, actions. */
function RefTile({ itemRef, item, running, sending, onRemove, onStartRef, onUpload }: TileProps) {
  const kind = itemRef.itemKind;
  const { tileSlot: slot, fileNotice } = ITEM_KINDS[kind];
  const file = useRef<HTMLInputElement>(null);
  const [noticing, setNoticing] = useState(false);
  const generating = running?.item_id === item.id ? running : null;
  const upload = sending?.id === item.id ? sending : null;
  // A set waiting to be picked doesn't lock the item: a new Ref job or a file replaces it (spec › Ref job).
  const busy = generating !== null || upload !== null;

  // A character's file asks first, every time, nothing to accept (legal item 2); a background's opens the picker at once.
  const pickFile = () => (fileNotice ? setNoticing(true) : file.current?.click());

  return (
    <li aria-label={item.name} className="flex w-full flex-col gap-3 rounded-2xl border border-border bg-card p-3 sm:w-[288px]">
      {generating ? (
        <Slot className={`${slot} bg-muted`}>
          <img src={loader24Icon} alt="" width={24} height={24} className="motion-safe:animate-spin" />
          <p className="font-mono text-xs font-medium text-mid">
            กำลังสร้าง {generating.done ?? 0}/{generating.total ?? REF_PICTURES}
          </p>
          <div className="w-40">
            <ProgressBar label={`สร้างภาพอ้างอิง ${item.name}`} percent={Math.round(((generating.done ?? 0) / REF_PICTURES) * 100)} />
          </div>
          <p className="text-xs text-muted-foreground">
            ราว {(((generating.total ?? REF_PICTURES) - (generating.done ?? 0)) * SECONDS_PER_PICTURE) / 60} นาที
          </p>
        </Slot>
      ) : upload ? (
        <Slot className={`${slot} bg-muted`}>
          <p className="font-mono text-xs font-medium text-mid">กำลังส่งไฟล์ {upload.percent}%</p>
          <div className="w-40">
            <ProgressBar label={`ส่งไฟล์ ${item.name}`} percent={upload.percent} />
          </div>
        </Slot>
      ) : item.pending > 0 ? (
        <Slot className={`${slot} bg-accent-subtle`}>
          <span className="rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">
            3 แบบรอเลือก
          </span>
          <a href={pickHash(itemRef)} className={`flex h-8 items-center px-3 ${PRIMARY_BUTTON}`}>
            เลือกภาพ
          </a>
        </Slot>
      ) : item.ref_rev > 0 ? (
        <img
          src={refUrl(itemRef, item.ref_rev)}
          alt={`ภาพอ้างอิง ${item.name}`}
          className={`${slot} rounded-xl bg-accent-subtle object-contain`}
        />
      ) : (
        <Slot className={`${slot} border border-dashed border-border-disabled bg-muted`}>
          <img src={ITEM_KINDS[kind].icon} alt="" width={24} height={24} />
          <p className="text-[13px] text-muted-foreground">ยังไม่มีภาพ</p>
        </Slot>
      )}
      <div className="flex items-center gap-2">
        <p className="text-sm leading-[1.5] font-semibold text-foreground">{item.name}</p>
        {item.tag && (
          <span className="rounded-full bg-muted px-2 py-px font-mono text-xs leading-[1.5] font-medium text-mid">
            {item.tag}
          </span>
        )}
        <div className="flex-1" />
        <button
          type="button"
          aria-label={`ลบ ${item.name}`}
          disabled={busy}
          onClick={() => onRemove(kind, item)}
          className="flex size-9 shrink-0 items-center justify-center rounded-lg hover:bg-muted disabled:opacity-45"
        >
          <img src={trashIcon} alt="" width={16} height={16} />
        </button>
      </div>
      {item.description && <p className="text-[13px] leading-[1.5] break-words text-mid">{item.description}</p>}
      <div className="flex gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => onStartRef(kind, item)}
          className={`h-8 px-3 disabled:opacity-45 ${OUTLINE_BUTTON}`}
        >
          <img src={wandIcon} alt="" width={16} height={16} />
          สร้างภาพ 3 แบบ
        </button>
        <button type="button" disabled={busy} onClick={pickFile} className={`h-8 px-3 disabled:opacity-45 ${GHOST_BUTTON}`}>
          <img src={uploadIcon} alt="" width={16} height={16} />
          เอาไฟล์เข้า
        </button>
        <input
          ref={file}
          type="file"
          accept="image/png,image/jpeg"
          aria-label={`ไฟล์ภาพ ${item.name}`}
          className="hidden"
          onChange={(event) => {
            const picked = event.target.files?.[0];
            event.target.value = "";
            if (picked) onUpload(kind, item, picked);
          }}
        />
      </div>
      {noticing && fileNotice && (
        <ToonDialog
          title={fileNotice.title}
          message={fileNotice.message}
          confirmLabel="เลือกไฟล์"
          onClose={() => setNoticing(false)}
          onConfirm={() => {
            setNoticing(false);
            file.current?.click();
          }}
        />
      )}
    </li>
  );
}

function Slot({ className, children }: { className: string; children: ReactNode }) {
  return <div className={`flex flex-col items-center justify-center gap-2 rounded-xl ${className}`}>{children}</div>;
}

const INPUT = "h-10 w-full rounded-lg border border-border bg-card px-3 text-sm leading-[1.5] text-foreground";
const LABEL = "font-button text-sm leading-5 font-medium text-foreground";

function ItemForm({ kind, onCancel, onAdd }: { kind: ItemKind; onCancel: () => void; onAdd: (fields: ItemFields) => void }) {
  const [name, setName] = useState("");
  const [tag, setTag] = useState("");
  const [description, setDescription] = useState("");
  const { form, tagged } = ITEM_KINDS[kind];

  return (
    <li className="w-full sm:w-[288px]">
      <form
        aria-label={form}
        onSubmit={(event) => {
          event.preventDefault();
          onAdd(tagged ? { name: name.trim(), tag: tag.trim(), description } : { name: name.trim(), description });
        }}
        className="flex flex-col gap-3 rounded-2xl border-2 border-brand-accent bg-card p-3"
      >
        <label className="flex flex-col gap-2">
          <span className={LABEL}>ชื่อ</span>
          <input value={name} maxLength={ITEM_NAME_MAX} onChange={(e) => setName(e.target.value)} className={INPUT} />
        </label>
        {tagged && (
          <div className="flex flex-col gap-2">
            <label className="flex flex-col gap-2">
              <span className={LABEL}>คำสั้น (ไม่บังคับ)</span>
              <input value={tag} maxLength={TAG_MAX} onChange={(e) => setTag(e.target.value)} className={INPUT} />
            </label>
            <span className="font-button text-xs leading-4 text-muted-foreground">
              ขึ้นบนป้ายชื่อ เช่น "เจ๊หน่อย / ร้านชำ"
            </span>
          </div>
        )}
        <label className="flex flex-col gap-2">
          <span className={LABEL}>คำอธิบาย</span>
          <input
            value={description}
            maxLength={DESCRIPTION_MAX}
            onChange={(e) => setDescription(e.target.value)}
            className={INPUT}
          />
        </label>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onCancel} className={`h-8 px-3 ${GHOST_BUTTON}`}>
            ยกเลิก
          </button>
          <button type="submit" disabled={name.trim() === ""} className={`h-8 px-3 ${PRIMARY_BUTTON}`}>
            เพิ่ม
          </button>
        </div>
      </form>
    </li>
  );
}
