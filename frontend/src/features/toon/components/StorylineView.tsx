import { useState } from "react";
import chevronDownIcon from "../../../components/ui/assets/chevron-down.svg";
import plusIcon from "../../../components/ui/assets/plus.svg";
import refreshIcon from "../../../components/ui/assets/refresh-cw.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import arrowRightIcon from "../assets/arrow-right.svg";
import chevronRightIcon from "../assets/chevron-right-16.svg";
import mountainIcon from "../assets/mountain.svg";
import musicIcon from "../../../components/ui/assets/music.svg";
import triangleAlertIcon from "../assets/triangle-alert.svg";
import volumeIcon from "../assets/volume.svg";
import wandWhiteIcon from "../assets/wand-white.svg";
import { cardsOf, DEFAULT_VOLUME, VOLUME_MAX, type Act, type Ep, type Segment } from "../lib/episodes";
import {
  ACT_NAME_MAX,
  castHash,
  epHash,
  isRunning,
  renderHash,
  type ImageScope,
  type MissingRef,
  type Series,
  type ToonJob,
} from "../lib/series";
import { ITEM_KINDS } from "../lib/kinds";
import { soundsHash, type Sound } from "../../sound-library/lib/sounds";
import { CardEditor, type CardWork } from "./CardEditor";
import { CommitField } from "../../../components/ui/CommitField";
import { LengthMeter } from "./LengthMeter";

type Edit = (method: string, path: string, body: unknown) => Promise<boolean>;

/** The Image and Voice jobs of the EP's cards, and swapping a card's picture back (`useEp`). */
export type CardJobs = {
  startImages: (scope: ImageScope) => Promise<void>;
  startImage: (cardId: string) => Promise<void>;
  startVoice: (cardId: string) => Promise<void>;
  swapImage: (cardId: string) => Promise<void>;
};

type Props = {
  ep: Ep;
  series: Series;
  /** The background sound library (D16). */
  sounds: Sound[];
  locked: boolean;
  edit: Edit;
  /** The latest job of this EP, or null. */
  job: ToonJob | null;
  /** Any Toon job runs: no other can start. */
  busy: boolean;
  /** What has no reference image yet, from the latest Image job or `nothing_to_draw` (D13). */
  missing: MissingRef[] | null;
  /** The cards that Image job skipped; null: none ran. */
  skipped: number | null;
  version: number;
  jobs: CardJobs;
};

const NEW_ACT_NAME = "องก์ใหม่"; // D53: renamed in its header

/** เส้นเรื่อง: acts → segments (their background) → cards, the edits of each, the EP's length
 * against its target, and the Image jobs of the whole EP (D9, D10, D14, D21, D33, D44). Closed
 * while a job locks the EP. */
export function StorylineView({ ep, series, sounds, locked, edit, job, busy, missing, skipped, version, jobs }: Props) {
  const cards = cardsOf(ep);
  const stale = cards.some((card) => card.image_status === "stale_ref");
  const working = cardWork(job);
  let number = 0;
  return (
    <>
      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-4">
        <LengthMeter seconds={ep.duration_s} />
        <span className="w-4 flex-1" />
        <button
          type="button"
          disabled={busy || locked}
          onClick={() => void jobs.startImages("missing")}
          className={`h-8 px-3 ${PRIMARY_BUTTON}`}
        >
          <img src={wandWhiteIcon} alt="" width={16} height={16} />
          สร้างภาพที่ขาดทั้งหมด
        </button>
        <button
          type="button"
          disabled={busy || locked || !stale}
          onClick={() => void jobs.startImages("stale_ref")}
          className={`h-8 px-3 ${OUTLINE_BUTTON}`}
        >
          <img src={refreshIcon} alt="" width={16} height={16} />
          สร้างภาพใหม่การ์ดที่ภาพอ้างอิงเปลี่ยน
        </button>
        <div className="flex w-full flex-wrap gap-2">
          <a href={soundsHash(epHash(ep.id))} className={`h-8 px-3 ${GHOST_BUTTON}`}>
            <img src={musicIcon} alt="" width={16} height={16} />
            คลังเสียง
          </a>
          <a href={renderHash(ep.id)} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
            <img src={arrowRightIcon} alt="" width={16} height={16} />
            ไปหน้า render
          </a>
        </div>
      </div>
      {missing && missing.length > 0 && (
        <MissingRefs
          missing={missing}
          // `nothing_to_draw` says what is missing, not how many cards: those are the EP's `no_ref` ones.
          skipped={skipped ?? cards.filter((card) => card.image_status === "no_ref").length}
          seriesId={series.id}
        />
      )}
      {ep.acts.map((act, index) => (
        <section key={act.id} aria-label={`องก์ ${index + 1} ${act.name}`} className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs leading-[1.5] font-medium text-mid">องก์ {index + 1}</span>
            <CommitField
              required
              aria-label={`ชื่อองก์ ${index + 1}`}
              value={act.name}
              maxLength={ACT_NAME_MAX}
              disabled={locked}
              onCommit={(name) => edit("PATCH", `/acts/${act.id}`, { name })}
              className="min-w-0 flex-1 rounded-lg bg-transparent px-1 text-base leading-[1.5] font-semibold text-foreground hover:bg-card focus:bg-card"
            />
            <button
              type="button"
              disabled={locked || series.backgrounds.length === 0}
              onClick={() => void addSegment(edit, ep, act, series)}
              className={`h-8 px-3 ${GHOST_BUTTON}`}
            >
              <img src={plusIcon} alt="" width={16} height={16} />
              เพิ่มช่วง
            </button>
            <button
              type="button"
              aria-label={`ลบองก์ ${index + 1}`}
              disabled={locked}
              onClick={() => void edit("DELETE", `/acts/${act.id}`, undefined)}
              className="flex size-9 items-center justify-center rounded-lg hover:bg-card disabled:opacity-45"
            >
              <img src={trashIcon} alt="" width={16} height={16} />
            </button>
          </div>
          {act.segments.length === 0 && (
            <p className="rounded-xl bg-muted px-3 py-2.5 text-[13px] leading-[1.5] text-mid">
              องก์นี้ยังไม่มีการ์ด: เขียนสรุปในพล็อตแล้วแตกการ์ดใหม่ หรือเพิ่มช่วงเอง
            </p>
          )}
          {act.segments.map((segment, s) => (
            <div key={segment.id} className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-3 rounded-xl bg-muted px-3 py-2.5">
                <img src={mountainIcon} alt="" width={18} height={18} />
                <div className="flex min-w-0 flex-1 flex-col leading-[1.5]">
                  <span className="text-xs text-mid">ช่วง {s + 1} · ฉากหลัง</span>
                  <span className="relative flex items-center">
                    <select
                      aria-label={`ฉากหลังของช่วง ${s + 1}`}
                      value={segment.background_id}
                      disabled={locked}
                      onChange={(event) => void edit("PATCH", `/segments/${segment.id}`, { background_id: event.target.value })}
                      className="appearance-none bg-transparent pr-6 text-sm font-semibold text-foreground"
                    >
                      {series.backgrounds.map((background) => (
                        <option key={background.id} value={background.id}>
                          {background.name}
                        </option>
                      ))}
                    </select>
                    <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none -ml-5" />
                  </span>
                </div>
                <SegmentSound segment={segment} number={s + 1} sounds={sounds} locked={locked} edit={edit} />
              </div>
              {segment.cards.map((card) => {
                number += 1;
                return (
                  <CardEditor
                    key={card.id}
                    card={card}
                    number={number}
                    series={series}
                    epId={ep.id}
                    version={version}
                    locked={locked}
                    busy={busy}
                    work={working?.cardId === card.id ? working.work : null}
                    jobs={jobs}
                    onChange={(body) => void edit("PATCH", `/cards/${card.id}`, body)}
                    onDelete={() => void edit("DELETE", `/cards/${card.id}`, undefined)}
                  />
                );
              })}
              <button
                type="button"
                disabled={locked}
                onClick={() => void edit("POST", "/cards", { segment_id: segment.id, text: "" })}
                className={`h-8 self-start px-3 ${GHOST_BUTTON}`}
              >
                <img src={plusIcon} alt="" width={16} height={16} />
                เพิ่มการ์ด
              </button>
            </div>
          ))}
        </section>
      ))}
      <button
        type="button"
        disabled={locked}
        onClick={() => void edit("POST", "/acts", { name: NEW_ACT_NAME })}
        className={`h-9 self-start px-4 ${OUTLINE_BUTTON}`}
      >
        <img src={plusIcon} alt="" width={16} height={16} />
        เพิ่มองก์
      </button>
    </>
  );
}

/** A segment at the end of the act, on the background of the act's last segment, else the plot's
 * first, else the Series' first; the user changes it in the segment's header. */
function addSegment(edit: Edit, ep: Ep, act: Act, series: Series) {
  const background =
    act.segments.at(-1)?.background_id ?? ep.plot.backgrounds.find((b) => b.id)?.id ?? series.backgrounds[0].id;
  return edit("POST", "/segments", { act_id: act.id, background_id: background });
}

/** The card a running job of this EP works on now, and how: klein draws it, or OmniVoice speaks it. */
function cardWork(job: ToonJob | null): { cardId: string; work: CardWork } | null {
  if (job?.kind === "image" && job.state === "drawing") {
    const cardId = job.card_ids?.[job.done ?? 0];
    return cardId ? { cardId, work: "drawing" } : null;
  }
  if (job?.kind === "voice" && isRunning(job) && job.card_ids?.[0]) return { cardId: job.card_ids[0], work: "voicing" };
  return null;
}

/** Figma `ต้องสร้างภาพอ้างอิงก่อน`: each character and background with no reference image yet,
 * how many cards it holds back, and a link to the page that makes one (D13). */
function MissingRefs({ missing, skipped, seriesId }: { missing: MissingRef[]; skipped: number; seriesId: string }) {
  return (
    <section
      aria-label="ต้องสร้างภาพอ้างอิงก่อน"
      className="flex flex-col gap-2 rounded-2xl border border-warning-border bg-warning-surface p-4"
    >
      <div className="flex flex-wrap items-center gap-2 leading-[1.5]">
        <img src={triangleAlertIcon} alt="" width={18} height={18} />
        <p className="text-sm font-semibold text-foreground">ต้องสร้างภาพอ้างอิงก่อน</p>
        <p className="text-[13px] text-mid">การ์ด {skipped} ใบยังวาดไม่ได้</p>
      </div>
      <ul className="flex flex-col gap-2">
        {missing.map((item) => (
          <li key={item.id} className="flex flex-wrap items-center gap-2">
            <img src={ITEM_KINDS[item.item_kind].icon16} alt="" width={16} height={16} />
            <span className="text-sm leading-[1.5] font-medium text-foreground">
              {ITEM_KINDS[item.item_kind].name} {item.name}
            </span>
            <span className="font-mono text-xs leading-[1.5] font-medium text-mid">{item.cards} การ์ด</span>
            <span className="flex-1" />
            <a href={castHash(seriesId)} className={`h-8 px-3 ${GHOST_BUTTON} text-brand`}>
              <img src={chevronRightIcon} alt="" width={16} height={16} />
              ไปสร้างภาพอ้างอิง
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Figma `Toon/SegmentHeader`'s sound: the library's sound or none, and its volume 0–100,
 * sent when the slider is let go (D5, D17). */
function SegmentSound({ segment, number, sounds, locked, edit }: { segment: Segment; number: number; sounds: Sound[]; locked: boolean; edit: Edit }) {
  const sound = segment.sound;
  return (
    <>
      <span className="relative flex h-9 w-full items-center gap-2 rounded-lg border border-border bg-card px-3 sm:w-[220px]">
        <img src={musicIcon} alt="" width={16} height={16} />
        <select
          aria-label={`เสียงพื้นของช่วง ${number}`}
          value={sound?.sound_id ?? ""}
          disabled={locked}
          onChange={(event) =>
            void edit("PATCH", `/segments/${segment.id}`, {
              sound: event.target.value ? { sound_id: event.target.value, volume: sound?.volume ?? DEFAULT_VOLUME } : null,
            })
          }
          className="min-w-0 flex-1 appearance-none bg-transparent pr-5 text-sm text-foreground"
        >
          <option value="">ไม่มีเสียงพื้น</option>
          {sounds.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name}
            </option>
          ))}
        </select>
        <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none -ml-6" />
      </span>
      <VolumeSlider
        key={`${segment.id}-${sound?.volume ?? "none"}`}
        number={number}
        volume={sound?.volume ?? null}
        disabled={locked || sound === null}
        onCommit={(volume) => void edit("PATCH", `/segments/${segment.id}`, { sound: { volume } })}
      />
    </>
  );
}

function VolumeSlider({ number, volume, disabled, onCommit }: { number: number; volume: number | null; disabled: boolean; onCommit: (volume: number) => void }) {
  const [value, setValue] = useState(volume ?? DEFAULT_VOLUME);
  const commit = () => {
    if (volume !== null && value !== volume) onCommit(value);
  };
  return (
    <span className="flex items-center gap-2">
      <img src={volumeIcon} alt="" width={16} height={16} />
      <input
        type="range"
        aria-label={`ความดังของช่วง ${number}`}
        min={0}
        max={VOLUME_MAX}
        value={value}
        disabled={disabled}
        onChange={(event) => setValue(Number(event.target.value))}
        onPointerUp={commit}
        onKeyUp={commit}
        onBlur={commit}
        className="h-4 w-[120px] accent-primary disabled:opacity-45"
      />
      <span className="w-7 font-mono text-xs font-medium text-mid">{volume === null ? "–" : value}</span>
    </span>
  );
}
