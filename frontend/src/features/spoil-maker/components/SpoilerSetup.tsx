import { useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import type { Refusal, RefusalLine } from "../../../lib/refusal";
import { draftLabel, REVIEW_HASH, runningDraft, wholeDraft, type DraftAsk, type DraftOrder, type WholeDraftJob } from "../lib/draft";
import { useEpisodes, type Episode, type Episodes } from "../hooks/useEpisodes";
import { useSpoilerSetup, type Banner, type SetupState } from "../hooks/useSpoilerSetup";
import { useDraftRun } from "../hooks/useStepStatus";
import type { Voice } from "../hooks/useVoices";
import { ClipPicker, isReady } from "./ClipPicker";
import { EpisodePicker } from "./EpisodePicker";
import { SetupSettings, type Settings } from "./SetupSettings";
import { StoryPicker } from "./StoryPicker";
import { listedStory, type StoryRow } from "../../../lib/stories";

const DEFAULT_TARGET_S = 60; // D39

/** The voice ร่างบท starts with: the one of the last draft while it is still saved, else the newest (spec › ค่าที่จำไว้). */
function startingVoice(voices: Voice[], lastVoiceId: string | null): string | null {
  return voices.find((voice) => voice.id === lastVoiceId)?.id ?? voices[0]?.id ?? null;
}

/** Step 1 of the สปอย tab, ตั้งค่าคลิปสปอย (Figma `Spoiler setup`, spoil-maker D7, D8, D25, D28, D39, D46, D66–D71). */
export function SpoilerSetup() {
  const { state, draft, askReplace } = useSpoilerSetup();
  const run = useDraftRun();
  if (state.kind === "offline") return <OfflinePanel />;
  // The form starts from the latest whole draft's order, so it waits for the steps too (D87).
  if (state.kind === "loading" || !run.loaded) return <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>;
  const job = wholeDraft(run.job);
  // A job that ends while the form is open (another tab's) starts the form again from its order (D87).
  const formKey = runningDraft(job) ? "locked" : (job?.started_at ?? "");
  return <SetupForm key={formKey} state={state} job={job} onDraft={draft} onAskReplace={askReplace} />;
}

/** Why the EP with its Story can't be drafted (spec › Frontend, D71, story-kb D14); null when it can. */
function draftBlocked(ep: Episode, cut: Episodes, story: StoryRow | null): RefusalLine | null {
  if (ep.lines === 0) return { text: "EP นี้ไม่มีบทพูด", setupLink: false };
  if (ep.tokens === null) return { text: cut.tokens_not_ready ?? "", setupLink: true };
  // The EPs' "not ready" text, when there is one, says why both can't be counted: no Qwen.
  if (story && story.tokens === null) return { text: cut.tokens_not_ready ?? STORY_TOKENS_NOT_READY, setupLink: true };
  return null;
}

/** The EPs were counted, but not the Story: Qwen's tokenizer broke in between (story-kb D19). */
const STORY_TOKENS_NOT_READY = "นับ token ของเรื่องไม่ได้";

/**
 * What the user did with the Story field (story-kb D3, D15, D23): `followsClip` until they touch it,
 * when the field shows the picked clip's own Story; a picked Story; ไม่ใช้ (`none`); or `gone`:
 * the Story ร่างบท sent was deleted, and the field says so with the API's `message`. `gone` sends
 * and shows as ไม่ใช้, as `none` does.
 */
type StoryChoice = { kind: "followsClip" } | { kind: "story"; id: string } | { kind: "none" } | { kind: "gone"; message: string };

/** The field's choice for a picked id; null is ไม่ใช้. */
const choiceOf = (id: string | null): StoryChoice => (id === null ? { kind: "none" } : { kind: "story", id });

/** The Story id ร่างบท sends for the choice, the clip's own while untouched; null is ไม่ใช้. */
function sentStoryId(choice: StoryChoice, clipStoryId: string | null): string | null {
  if (choice.kind === "followsClip") return clipStoryId;
  return choice.kind === "story" ? choice.id : null;
}

/** The EP's tokens with the Story's (story-kb D14); null while either can't be counted. */
function draftTokens(ep: Episode | null, story: StoryRow | null): number | null {
  if (ep?.tokens == null) return null;
  if (!story) return ep.tokens;
  return story.tokens === null ? null : ep.tokens + story.tokens;
}

type Loaded = Extract<SetupState, { kind: "loaded" }>;

type FormProps = {
  state: Loaded;
  /** The latest whole new draft: running, it locks the form; ended, its order is what the form starts from (D82, D87). */
  job: WholeDraftJob | null;
  /** Resolves to the API's refusal when it refused. */
  onDraft: (order: DraftAsk, replace: boolean) => Promise<Refusal | null>;
  onAskReplace: (asking: boolean) => void;
};

/**
 * The order the form starts from: a whole draft's that runs, failed or was cancelled (D87).
 * A `done` one wrote the Spoil draft, so the draft's clip is picked instead.
 */
function orderOf(job: WholeDraftJob | null): DraftOrder | null {
  return job && job.state !== "done" ? job.order : null;
}

/** The fields of an order; a voice no longer saved is kept only while it locks the form (D87). */
function settingsOf(order: DraftOrder, voices: Voice[], fallbackVoice: string | null, locked: boolean): Settings {
  const saved = voices.some((voice) => voice.id === order.voice_id);
  return {
    style: order.style,
    layout: order.layout,
    targetS: order.target_s,
    voiceId: saved || locked ? order.voice_id : fallbackVoice,
  };
}

/** The order's EP in the cut now: the same number and range, else the first (spec › Frontend). */
function orderEp(cut: Episodes, order: DraftOrder): Episode | null {
  const same = cut.episodes.find((one) => one.n === order.ep.n && Math.abs(one.start_s - order.ep.start_s) <= 0.01 && Math.abs(one.end_s - order.ep.end_s) <= 0.01);
  return same ?? cut.episodes[0] ?? null;
}

function SetupForm({ state, job, onDraft, onAskReplace }: FormProps) {
  const order = orderOf(job);
  const locked = runningDraft(job) !== null;
  // While it runs, every field shows its order, even one started in another tab (D82).
  const lockedOrder = locked ? order : null;
  const pickable = (id: string | null) => state.clips.some((clip) => clip.id === id && isReady(clip));
  const lastVoice = startingVoice(state.voices, state.lastVoiceId);
  // The order's clip, else the Spoil draft's, is picked when the page opens (spec › Frontend).
  const [clipId, setClipId] = useState<string | null>(() => {
    const id = order?.clip_id ?? state.draftClipId;
    return pickable(id) ? id : null;
  });
  const [pickedEp, setPickedEp] = useState<number | null>(null);
  const [settings, setSettings] = useState<Settings>(() =>
    order
      ? settingsOf(order, state.voices, lastVoice, false)
      : { style: "drama", layout: "B", targetS: DEFAULT_TARGET_S, voiceId: lastVoice },
  );
  // An order's Story, ไม่ใช้ included, counts as picked: the form starts from the order (D87).
  const [storyChoice, setStoryChoice] = useState<StoryChoice>(() => (order ? choiceOf(order.story_id) : { kind: "followsClip" }));
  const shown = lockedOrder ? settingsOf(lockedOrder, state.voices, lastVoice, true) : settings;
  const shownClipId = lockedOrder ? (pickable(lockedOrder.clip_id) ? lockedOrder.clip_id : null) : clipId;
  const episodes = useEpisodes(shownClipId);
  const cut = episodes.state.kind === "loaded" ? episodes.state.cut : null;
  // Until one is picked: the order's EP while the order's clip is open, else the Spoil draft's, else the first.
  const fromOrder = order && order.clip_id === shownClipId && (lockedOrder || pickedEp === null) ? order : null;
  const ep = !cut
    ? null
    : fromOrder
      ? orderEp(cut, fromOrder)
      : (cut.episodes.find((one) => one.n === pickedEp) ?? cut.episodes.find((one) => one.in_draft) ?? cut.episodes[0] ?? null);
  const clipStoryId = clipId === null ? null : (state.clipStories[clipId] ?? null);
  // A Story deleted since shows ไม่ใช้ (story-kb D15).
  const story = listedStory(state.stories, lockedOrder ? lockedOrder.story_id : sentStoryId(storyChoice, clipStoryId));
  const limit = cut?.limit ?? null;
  const blocked = ep && cut ? draftBlocked(ep, cut, story) : null;
  const tokens = draftTokens(ep, story);
  const canDraft = ep !== null && blocked === null && tokens !== null && limit !== null && tokens <= limit && settings.voiceId !== null && !locked;

  const pickClip = (id: string) => {
    setClipId(id);
    setPickedEp(null);
    setStoryChoice({ kind: "followsClip" });
  };

  const send = async (replace: boolean) => {
    if (clipId === null || ep === null) return;
    // The range is read once a cut still being saved is answered: it is the one the backend has (D71).
    const found = (await episodes.settled())?.episodes.find((one) => one.n === ep.n);
    if (!found) return; // the EP went with the new cut; the list shows what there is now
    const refused = await onDraft(
      {
        clip_id: clipId,
        ep: { n: found.n, start_s: found.start_s, end_s: found.end_s },
        style: settings.style,
        layout: settings.layout,
        target_s: settings.targetS,
        voice_id: settings.voiceId ?? "",
        story_id: story?.id ?? null,
      },
      replace,
    );
    if (refused?.code === "episodes_changed") episodes.reload();
    if (refused?.code === "story_not_found") setStoryChoice({ kind: "gone", message: refused.message });
  };

  return (
    <div className="flex flex-col gap-4">
      {state.banner && <SetupBanner banner={state.banner} />}
      {locked && order && (
        <Alert
          tone="info"
          action={
            <a href={REVIEW_HASH} className="flex h-11 items-center font-button text-sm leading-5 font-medium text-brand sm:h-9 sm:px-4">
              ไปที่ตรวจแก้บท
            </a>
          }
        >
          กำลังร่างบท {draftLabel(order)}: ยกเลิกการร่างก่อนจึงเลือกใหม่ได้
        </Alert>
      )}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="flex flex-col gap-4 lg:w-[560px] lg:shrink-0">
          <ClipPicker clips={state.clips} picked={shownClipId} disabled={locked} onChange={pickClip} />
          {locked && order && shownClipId === null && (
            // The order's clip is no longer in the list: its title only, no EPs (spec › Frontend).
            <p className="rounded-2xl border border-border bg-card px-4 py-3.5 text-sm leading-[21px] font-medium text-foreground">
              {draftLabel(order)}
            </p>
          )}
          {(shownClipId !== null || lockedOrder) && (
            <StoryPicker
              stories={state.stories}
              storyId={story?.id ?? null}
              lockedText={lockedOrder ? (lockedOrder.story_title ?? "ไม่ใช้") : null}
              goneText={storyChoice.kind === "gone" ? storyChoice.message : null}
              onChange={(id) => setStoryChoice(choiceOf(id))}
            />
          )}
          {shownClipId !== null && (
            <EpisodePicker
              clipId={shownClipId}
              state={episodes.state}
              picked={ep?.n ?? null}
              disabled={locked}
              onPick={setPickedEp}
              onMinutes={(minutes) => episodes.put({ minutes })}
              onCuts={(cuts) => cut && episodes.put({ minutes: cut.minutes, cuts })}
            />
          )}
        </div>
        <SetupSettings
          settings={shown}
          voices={state.voices}
          ep={ep}
          story={story}
          tokens={tokens}
          limit={limit}
          draftBlocked={blocked}
          canDraft={canDraft}
          locked={locked}
          confirmingReplace={state.confirmingReplace}
          onChange={setSettings}
          onDraft={() => (state.draftExists ? onAskReplace(true) : void send(false))}
          onReplace={() => void send(true)}
          onKeep={() => onAskReplace(false)}
        />
      </div>
    </div>
  );
}

/** Figma component `Setup banner`: built from Alert. */
function SetupBanner({ banner }: { banner: Banner }) {
  if (banner.kind === "not_ready") {
    return (
      <Alert
        tone="warning"
        action={
          <a href="#/setup" className="flex h-11 items-center font-button text-sm leading-5 font-medium text-brand sm:h-9 sm:px-4">
            ไปที่ Setup status
          </a>
        }
      >
        {banner.text}
      </Alert>
    );
  }
  return <Alert tone={banner.kind === "gpu_busy" ? "warning" : "error"}>{banner.text}</Alert>;
}
