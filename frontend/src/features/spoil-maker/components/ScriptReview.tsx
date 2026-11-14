import { useId, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import arrowRightIcon from "../assets/arrow-right-white.svg";
import fileTextIcon from "../assets/file-text-36.svg";
import triangleAlertIcon from "../assets/triangle-alert-24.svg";
import { useAutoSave } from "../hooks/useAutoSave";
import { useDraftProgress } from "../hooks/useDraftProgress";
import { useLibrarySounds } from "../hooks/useLibrarySounds";
import { useReviewJobs } from "../hooks/useReviewJobs";
import { useScriptReview } from "../hooks/useScriptReview";
import { useVideoSettings } from "../hooks/useVideoSettings";
import { epLabel, reviewJobText, SETUP_HASH, TOP_TEXT_LABELS, type Draft } from "../lib/draft";
import { markNumbersOverTopText, type Watermark } from "../lib/render";
import type { RefusalLine } from "../../../lib/refusal";
import { BackgroundSound } from "./BackgroundSound";
import { DraftNotice, DraftProgressCard } from "./DraftProgress";
import { PolishDialog } from "./PolishDialog";
import { ReviewBanner } from "./ReviewBanner";
import { ReviewFooter } from "./ReviewFooter";
import { ReviewJobProgress, SentenceCard } from "./SentenceCard";
import { ShotPicker } from "./ShotPicker";
import { VideoSettings } from "./VideoSettings";

const TOP_TEXT_MAX = 40;
const TOLERANCE = 0.25; // an estimate further off the target than this warns (D18)
/** The dialog open over the page: the Shot picker of one sentence's slot, or the choice before เรียบเรียงใหม่. */
type Overlay = { kind: "picker"; sentenceId: string; slot: number } | { kind: "polish" };

/** What แทรกใต้ puts in a new sentence: the API keeps no empty one, and the user types over it (D27). */
const NEW_SENTENCE = "ประโยคใหม่";

/**
 * Step 2 of the สปอย tab while a whole new draft is written (D81): its progress card in place
 * of the script; once it ends, the script read again, under how it ended (D83, D85–D87).
 */
export function ScriptReview() {
  const progress = useDraftProgress();
  const { view } = progress;
  if (view.kind === "offline") return <OfflinePanel />;
  if (view.kind === "running") return <DraftProgressCard job={view.job} onCancel={() => void progress.cancel()} />;
  return (
    <div className="flex flex-col gap-4">
      {view.kind !== "none" && (
        <DraftNotice
          view={view}
          retryStep={progress.retryStep}
          onRetry={progress.retry}
          onReplace={progress.replaceDraft}
          onKeep={progress.keepDraft}
        />
      )}
      <ScriptReviewBody key={progress.scriptKey} />
    </div>
  );
}

/**
 * Step 2 of the สปอย tab, ตรวจแก้บท (Figma `Script review`): the text on top, the length,
 * every sentence with its voice, the original and background sounds and the watermarks beside them, the
 * sticky footer that voices and renders, and เรียบเรียงใหม่ (spoil-maker D19, D25–D27, D30,
 * D40–D42, D51, D72–D76).
 */
function ScriptReviewBody() {
  const review = useScriptReview();
  const { state } = review;
  const { jobs, ...run } = useReviewJobs(review.refresh, review.goOffline);
  const video = useVideoSettings();
  const library = useLibrarySounds();
  const [overlay, setOverlay] = useState<Overlay | null>(null);
  const [focusId, setFocusId] = useState<string | null>(null);

  if (state.kind === "offline") return <OfflinePanel />;
  if (state.kind === "loading") return <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>;
  if (state.kind === "empty") return <NoDraft />;

  const { draft, shots, job, pickingId } = state;
  const running = jobs.voice ?? jobs.render;
  // A render that is past its voicing doesn't lock the draft, but the page waits for it too (Figma).
  const locked = draft.locked || job !== null || running !== null;
  const unvoiced = draft.sentences.filter((s) => s.status !== "ready").map((s) => s.id);
  const picker = overlay?.kind === "picker" ? overlay : null;
  const pickerIndex = picker ? draft.sentences.findIndex((s) => s.id === picker.sentenceId) : -1;

  /** แทรกใต้, then focus the new sentence, the one id the draft didn't have, so the user types over its text. */
  const insertAfter = async (afterId: string) => {
    const before = new Set(draft.sentences.map((s) => s.id));
    const result = await review.insertAfter(afterId, NEW_SENTENCE);
    if (result.kind === "saved") setFocusId(result.draft.sentences.find((s) => !before.has(s.id))?.id ?? null);
  };

  return (
    <div className="flex flex-col gap-4">
      {jobs.banner && (
        <ReviewBanner
          banner={jobs.banner}
          onRetry={() => void (jobs.banner?.kind === "render" ? run.render() : run.voice(unvoiced))}
        />
      )}
      {jobs.refused && <RefusedAlert refused={jobs.refused} />}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="flex min-w-0 flex-col gap-4 lg:w-[744px] lg:shrink-0">
          <TopCard
            draft={draft}
            watermarks={video.watermarks}
            locked={locked}
            onSave={async (top_text) => (await review.changeDraft({ top_text })).kind === "saved"}
            onPolish={() => setOverlay({ kind: "polish" })}
          />
          {state.message && <Alert tone={state.message.tone}>{state.message.text}</Alert>}
          {/* A polish, or a pick this page didn't start (it ran before the page opened): which sentence isn't known. */}
          {job && !draft.sentences.some((s) => s.id === pickingId) && (
            <section aria-label="งานที่กำลังทำ" className="rounded-2xl border border-border bg-card p-4">
              <ReviewJobProgress job={job} onCancel={() => void review.cancel()} />
            </section>
          )}
          <ol className="flex flex-col gap-4">
            {draft.sentences.map((sentence, index) => (
              <SentenceCard
                key={sentence.id}
                sentence={sentence}
                number={index + 1}
                episode={epLabel(draft.ep.n)}
                shots={shots}
                locked={locked}
                picking={pickingId === sentence.id ? job : null}
                focus={focusId === sentence.id}
                onText={async (text) => (await review.changeText(sentence.id, text)).kind === "saved"}
                onOpenPicker={(slot) => setOverlay({ kind: "picker", sentenceId: sentence.id, slot })}
                onPick={() => void review.pick(sentence.id)}
                onCancelPick={() => void review.cancel()}
                onVoice={() => void run.voice([sentence.id])}
                onInsert={() => void insertAfter(sentence.id)}
                onDelete={() => void review.remove(sentence.id)}
              />
            ))}
          </ol>
        </div>
        <div className="min-w-0 flex-1">
          <VideoSettings
            volume={draft.original_volume}
            onVolume={async (original_volume) => (await review.changeDraft({ original_volume })).kind === "saved"}
            backgroundSound={
              <BackgroundSound
                sound={draft.sound}
                sounds={library.sounds}
                unreadable={library.unreadable}
                locked={locked}
                onChange={review.changeSound}
                onSoundGone={() => void library.reload()}
              />
            }
            settings={video.state}
            watermarks={video.watermarks}
            locked={locked}
            onAdd={video.add}
            onChange={video.change}
            onRemove={video.remove}
          />
        </div>
      </div>
      <ReviewFooter
        job={running}
        waitingFor={job ? reviewJobText(job).waitingFor : null}
        noShot={draft.sentences.filter((s) => s.status === "no_shot").length}
        unvoiced={unvoiced.length}
        onVoiceAll={() => void run.voice(unvoiced)}
        onRender={() => void run.render()}
        onCancel={() => void run.cancel()}
      />
      {overlay?.kind === "polish" && (
        <PolishDialog
          draft={draft}
          onClose={() => setOverlay(null)}
          onPolish={(includeEdited) => {
            setOverlay(null);
            void review.polish(includeEdited);
          }}
        />
      )}
      {picker && pickerIndex >= 0 && (
        <ShotPicker
          sentence={draft.sentences[pickerIndex]}
          number={pickerIndex + 1}
          slot={picker.slot}
          clipId={draft.clip_id}
          ep={draft.ep}
          shots={shots}
          videoSrc={state.videoSrc}
          onClose={() => setOverlay(null)}
          onPick={(shot) => {
            const slots = [...draft.sentences[pickerIndex].shots];
            slots[picker.slot] = shot;
            setOverlay(null);
            void review.changeShots(picker.sentenceId, slots);
          }}
        />
      )}
    </div>
  );
}

/** A refusal of a start; `not_ready` links to ติดตั้ง (spec › Frontend). */
function RefusedAlert({ refused }: { refused: RefusalLine }) {
  return (
    <Alert tone="error">
      {refused.text}
      {refused.setupLink && (
        <>
          {" "}
          <a href="#/setup" className="font-medium text-link underline">
            ไปหน้าติดตั้ง
          </a>
        </>
      )}
    </Alert>
  );
}

type TopCardProps = {
  draft: Draft;
  watermarks: Watermark[];
  locked: boolean;
  onSave: (text: string) => Promise<boolean>;
  /** เรียบเรียงใหม่: opens the choice before it starts (D75). */
  onPolish: () => void;
};

/**
 * The text on top (layouts A and C) with a warning when a watermark covers it, the
 * length: estimate / target and the number of sentences, and เรียบเรียงใหม่ (D19, D30, D64, D72).
 */
function TopCard({ draft, watermarks, locked, onSave, onPolish }: TopCardProps) {
  const label = TOP_TEXT_LABELS[draft.layout];
  const top = useAutoSave(draft.top_text, onSave);
  // As typed, not as saved: clearing the text clears the warning at once. Layout B has none.
  const covering = label ? markNumbersOverTopText(watermarks, top.value) : [];
  const id = useId();
  const estimate = Math.round(draft.estimated_total_s);
  const off = Math.abs(draft.estimated_total_s - draft.target_s) > TOLERANCE * draft.target_s;
  const length = `ความยาวประมาณ ${estimate} / ${draft.target_s} วินาที · ${draft.sentences.length} ประโยค`;
  return (
    <section aria-label="ภาพรวมบท" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
      {label && (
        <div className="flex flex-col gap-1.5">
          <label htmlFor={id} className="text-sm leading-5 font-medium text-foreground">
            {label}
          </label>
          <input
            id={id}
            value={top.value}
            disabled={locked}
            maxLength={TOP_TEXT_MAX * 2}
            onChange={(event) => top.change(event.target.value)}
            onBlur={() => void top.flush()}
            className="h-10 rounded-lg border border-border bg-card px-3 font-button text-sm text-foreground disabled:bg-muted"
          />
          <p className="text-xs text-muted-foreground">ข้อความบนสุดของวิดีโอ</p>
        </div>
      )}
      {covering.length > 0 && (
        <Alert tone="warning">
          ลายน้ำ {covering.join(", ")} อยู่บนกลาง จะทับ {label} ในวิดีโอ: ปิดหรือย้ายลายน้ำถ้าไม่ต้องการ
        </Alert>
      )}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        {off ? (
          <p className="flex w-fit items-center gap-1.5 rounded-lg border border-warning-border bg-warning-surface py-1.5 pr-3 pl-2.5 text-sm font-medium text-warning">
            <img src={triangleAlertIcon} alt="" width={24} height={24} />
            {length}
          </p>
        ) : (
          <p className="text-sm font-medium text-mid">{length}</p>
        )}
        <span className="hidden flex-1 sm:block" />
        <button
          type="button"
          onClick={onPolish}
          disabled={locked || draft.sentences.length === 0}
          className={`h-11 px-6 ${OUTLINE_BUTTON}`}
        >
          เรียบเรียงใหม่
        </button>
      </div>
    </section>
  );
}

/** Figma `Script review / No draft`. */
function NoDraft() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card px-6 py-14 text-center">
      <img src={fileTextIcon} alt="" width={36} height={36} />
      <p className="text-base font-semibold text-foreground">ยังไม่มีบท</p>
      <p className="text-sm text-mid">ร่างบทจากหน้าตั้งค่าคลิปสปอยก่อน แล้วกลับมาตรวจที่นี่</p>
      <a href={SETUP_HASH} className={`h-11 px-6 ${PRIMARY_BUTTON}`}>
        <img src={arrowRightIcon} alt="" width={16} height={16} />
        ไปที่ตั้งค่าคลิปสปอย
      </a>
    </div>
  );
}
