import plusIcon from "../../../components/ui/assets/plus.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import refreshIcon from "../../../components/ui/assets/refresh-cw.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { playAudio } from "../../../lib/audio";
import flameIcon from "../assets/flame.svg";
import imageIcon from "../assets/image.svg";
import loaderIcon from "../assets/loader.svg";
import micDarkIcon from "../assets/mic-dark.svg";
import micIcon from "../assets/mic.svg";
import minusIcon from "../assets/minus.svg";
import playIcon from "../assets/play.svg";
import undoIcon from "../assets/undo.svg";
import {
  cardAudioPath,
  cardImagePath,
  CARD_CHARACTERS_MAX,
  CARD_DESCRIPTION_MAX,
  HOLD_MAX,
  HOLD_STEP,
  MOTION_LABELS,
  TEXT_MAX,
  type Card,
  type Motion,
} from "../lib/episodes";
import type { Series } from "../lib/series";
import { CommitField } from "./CommitField";
import type { CardJobs } from "./StorylineView";

type Props = {
  card: Card;
  /** The card's number in the EP, from 1. */
  number: number;
  series: Series;
  epId: string;
  /** Goes up with each read of the EP: a picture or narration made since loads again. */
  version: number;
  locked: boolean;
  /** Any Toon job runs: its buttons wait. */
  busy: boolean;
  /** What a running job does to this card now; null: nothing. */
  work: CardWork | null;
  jobs: CardJobs;
  onChange: (body: Partial<Card>) => void;
  onDelete: () => void;
};

const LABEL = "text-xs leading-[1.5] font-medium text-mid";
const FIELD = "w-full rounded-lg border border-border bg-card px-3 py-2 text-sm leading-[1.5] text-foreground disabled:bg-muted";

export type CardWork = "drawing" | "voicing";

const ACTION = "h-8 px-3";

/** Figma `Toon/Card`: the fields of one card (card-sketch, D20, D21, D30), its picture with
 * สร้างภาพใหม่ and สลับภาพก่อนหน้า (D27, D33), and its narration's buttons (D21). */
export function CardEditor(props: Props) {
  const { card, number, series, epId, version, locked, busy, work, jobs, onChange, onDelete } = props;
  const named = (id: string) => series.characters.find((c) => c.id === id)?.name ?? id;
  const addable = series.characters.filter((c) => !card.character_ids.includes(c.id));
  const full = card.character_ids.length >= CARD_CHARACTERS_MAX;

  return (
    <article aria-label={`การ์ด ${number}`} className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:flex-row">
      <div className="flex shrink-0 flex-col gap-2">
        <CardPicture card={card} number={number} src={cardImagePath(epId, card.id, version)} drawing={work === "drawing"} full={series.layout === "full"} />
        <div className="flex flex-wrap gap-1">
          <button
            type="button"
            disabled={busy || locked || card.image_status === "no_ref"}
            onClick={() => void jobs.startImage(card.id)}
            className={`${ACTION} ${GHOST_BUTTON}`}
          >
            <img src={refreshIcon} alt="" width={16} height={16} />
            {card.has_image ? "สร้างภาพใหม่" : "สร้างภาพ"}
          </button>
          {card.has_previous_image && (
            <button
              type="button"
              disabled={busy || locked}
              onClick={() => void jobs.swapImage(card.id)}
              className={`${ACTION} ${GHOST_BUTTON}`}
            >
              <img src={undoIcon} alt="" width={16} height={16} />
              สลับภาพก่อนหน้า
            </button>
          )}
        </div>
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs leading-[1.5] font-medium text-mid">การ์ด {number}</span>
          {card.edited && <Badge className="bg-info-surface text-info-border">แก้เอง</Badge>}
          {card.image_status === "stale_ref" && <Badge className="bg-warning-surface text-warning">ภาพอ้างอิงเปลี่ยน</Badge>}
          {card.image_status === "no_ref" && <Badge className="bg-destructive text-card">ยังไม่มีภาพอ้างอิง</Badge>}
          <span className="flex-1" />
          <span className="font-mono text-xs leading-[1.5] font-medium text-mid">{card.duration_s} วิ</span>
          <button
            type="button"
            aria-label={`ลบการ์ด ${number}`}
            disabled={locked}
            onClick={onDelete}
            className="flex size-9 items-center justify-center rounded-lg hover:bg-muted disabled:opacity-45"
          >
            <img src={trashIcon} alt="" width={16} height={16} />
          </button>
        </div>
        <label className="flex flex-col gap-1.5">
          <span className={LABEL}>ข้อความเล่า</span>
          <CommitField
            value={card.text}
            maxLength={TEXT_MAX}
            disabled={locked}
            onCommit={(text) => onChange({ text })}
            className={FIELD}
          />
        </label>
        <div className="flex flex-col gap-1.5">
          <span className={LABEL}>ตัวละครในภาพ (0–{CARD_CHARACTERS_MAX})</span>
          <div className="flex flex-wrap items-center gap-1.5">
            {card.character_ids.map((id) => (
              <span key={id} className="flex items-center gap-1 rounded-full bg-accent-subtle px-2.5 py-1 text-[13px] leading-[1.5] font-medium text-foreground">
                {named(id)}
                <button
                  type="button"
                  aria-label={`เอา ${named(id)} ออก`}
                  disabled={locked}
                  onClick={() => onChange({ character_ids: card.character_ids.filter((c) => c !== id) })}
                >
                  <img src={xIcon} alt="" width={14} height={14} />
                </button>
              </span>
            ))}
            <span className={`relative flex h-8 items-center gap-2 rounded-lg px-3 ${full || locked ? "opacity-45" : "hover:bg-muted"}`}>
              <img src={plusIcon} alt="" width={16} height={16} />
              <span className="font-button text-sm leading-5 font-medium text-foreground">เพิ่ม</span>
              <select
                aria-label="เพิ่มตัวละคร"
                value=""
                disabled={full || locked || addable.length === 0}
                onChange={(event) => onChange({ character_ids: [...card.character_ids, event.target.value] })}
                className="absolute inset-0 cursor-pointer opacity-0 disabled:cursor-default"
              >
                <option value="">เพิ่มตัวละคร</option>
                {addable.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </span>
          </div>
        </div>
        <label className="flex flex-col gap-1.5">
          <span className={LABEL}>คำบรรยายภาพ</span>
          <CommitField
            value={card.description}
            maxLength={CARD_DESCRIPTION_MAX}
            disabled={locked}
            onCommit={(description) => onChange({ description })}
            className={FIELD}
          />
        </label>
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1.5">
            <span className={LABEL}>การขยับ</span>
            <select
              value={card.motion}
              disabled={locked}
              onChange={(event) => onChange({ motion: event.target.value as Motion })}
              className="h-9 w-40 rounded-lg border border-border bg-card px-3 text-sm text-foreground disabled:bg-muted"
            >
              {Object.entries(MOTION_LABELS).map(([motion, label]) => (
                <option key={motion} value={motion}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <div className="flex flex-col gap-1.5">
            <span className={LABEL}>ไฟกะพริบ</span>
            <span className="flex h-9 items-center gap-2">
              <img src={flameIcon} alt="" width={16} height={16} />
              <button
                type="button"
                role="switch"
                aria-checked={card.flicker}
                aria-label="ไฟกะพริบ"
                disabled={locked}
                onClick={() => onChange({ flicker: !card.flicker })}
                className={`relative h-5 w-9 rounded-full transition-colors disabled:opacity-45 ${card.flicker ? "bg-brand-accent" : "bg-surface-strong"}`}
              >
                <span className={`absolute top-0.5 size-4 rounded-full bg-card transition-[left] ${card.flicker ? "left-[18px]" : "left-0.5"}`} />
              </button>
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <span className={LABEL}>ค้างเพิ่ม (0–{HOLD_MAX} วิ)</span>
            <div className="flex items-center rounded-lg border border-border">
              <StepButton
                label="ลดวินาทีค้าง"
                icon={minusIcon}
                disabled={locked || card.hold_s <= (card.text ? 0 : HOLD_STEP)}
                onClick={() => onChange({ hold_s: card.hold_s - HOLD_STEP })}
              />
              <span className="flex h-9 w-14 items-center justify-center font-mono text-sm text-foreground">{card.hold_s}</span>
              <StepButton
                label="เพิ่มวินาทีค้าง"
                icon={plusIcon}
                disabled={locked || card.hold_s >= HOLD_MAX}
                onClick={() => onChange({ hold_s: card.hold_s + HOLD_STEP })}
              />
            </div>
          </div>
        </div>
        {card.audio_status !== "silent" && (
          <Narration
            card={card}
            src={cardAudioPath(epId, card.id, version)}
            disabled={busy || locked}
            voicing={work === "voicing"}
            onVoice={() => void jobs.startVoice(card.id)}
          />
        )}
      </div>
    </article>
  );
}

/** The card's picture as big as the design's 144 px high, a frame card wide and a full-screen one
 * upright (D37); while the Image job draws it, กำลังวาด…. */
function CardPicture({ card, number, src, drawing, full }: { card: Card; number: number; src: string; drawing: boolean; full: boolean }) {
  const size = full ? "h-36 w-[81px]" : "h-36 w-64";
  if (drawing) {
    return (
      <div className={`flex flex-col items-center justify-center gap-1.5 rounded-lg bg-accent-subtle ${size}`}>
        <img src={loaderIcon} alt="" width={20} height={20} className="motion-safe:animate-spin" />
        <p className="text-xs leading-[1.5] text-mid">กำลังวาด…</p>
      </div>
    );
  }
  if (!card.has_image) {
    return (
      <div className={`flex flex-col items-center justify-center gap-1.5 rounded-lg border border-dashed border-border-disabled bg-muted ${size}`}>
        <img src={imageIcon} alt="" width={20} height={20} />
        <p className="text-xs leading-[1.5] text-muted-foreground">ยังไม่มีภาพ</p>
      </div>
    );
  }
  return <img src={src} alt={`ภาพการ์ด ${number}`} className={`rounded-lg bg-muted object-cover ${size}`} />;
}

/** Figma `Narration voice`: สร้างเสียง until the card has narration, then ฟัง and สร้างใหม่ with
 * its length; a changed text or EP voice says the narration is old (D8, D21). */
function Narration({ card, src, disabled, voicing, onVoice }: { card: Card; src: string; disabled: boolean; voicing: boolean; onVoice: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <img src={micIcon} alt="" width={16} height={16} />
      <span className={LABEL}>เสียงเล่า</span>
      {voicing ? (
        <span className="flex h-8 items-center gap-2 px-3 text-sm text-mid">
          <img src={loaderIcon} alt="" width={16} height={16} className="motion-safe:animate-spin" />
          กำลังสร้างเสียง…
        </span>
      ) : card.audio_status === "no_audio" ? (
        <button type="button" disabled={disabled} onClick={onVoice} className={`${ACTION} ${OUTLINE_BUTTON}`}>
          <img src={micDarkIcon} alt="" width={16} height={16} />
          สร้างเสียง
        </button>
      ) : (
        <>
          <button type="button" onClick={() => playAudio(src)} className={`${ACTION} ${GHOST_BUTTON}`}>
            <img src={playIcon} alt="" width={16} height={16} />
            ฟัง
          </button>
          <button type="button" disabled={disabled} onClick={onVoice} className={`${ACTION} ${GHOST_BUTTON}`}>
            <img src={refreshIcon} alt="" width={16} height={16} />
            สร้างใหม่
          </button>
          {card.audio_status === "stale_audio" && <Badge className="bg-warning-surface text-warning">เสียงเก่า</Badge>}
        </>
      )}
    </div>
  );
}

function Badge({ className, children }: { className: string; children: string }) {
  return <span className={`rounded-full px-2 py-0.5 font-button text-xs leading-4 font-medium ${className}`}>{children}</span>;
}

function StepButton({ label, icon, disabled, onClick }: { label: string; icon: string; disabled: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="flex size-9 items-center justify-center rounded-lg hover:bg-muted disabled:opacity-45 disabled:hover:bg-transparent"
    >
      <img src={icon} alt="" width={16} height={16} />
    </button>
  );
}
