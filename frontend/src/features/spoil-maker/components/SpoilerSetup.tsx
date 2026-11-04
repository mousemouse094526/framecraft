import { useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import type { RefusalLine } from "../../../lib/refusal";
import { useEpisodes, type Episode, type Episodes } from "../hooks/useEpisodes";
import { useSpoilerSetup, type Banner, type Order, type SetupState } from "../hooks/useSpoilerSetup";
import type { Voice } from "../hooks/useVoices";
import { ClipPicker, isReady } from "./ClipPicker";
import { EpisodePicker } from "./EpisodePicker";
import { SetupSettings, type Settings } from "./SetupSettings";

const DEFAULT_TARGET_S = 60; // D39

/** The voice ร่างบท starts with: the one of the last draft while it is still saved, else the newest (spec › ค่าที่จำไว้). */
function startingVoice(voices: Voice[], lastVoiceId: string | null): string | null {
  return voices.find((voice) => voice.id === lastVoiceId)?.id ?? voices[0]?.id ?? null;
}

/** Step 1 of the สปอย tab, ตั้งค่าคลิปสปอย (Figma `Spoiler setup`, spoil-maker D7, D8, D25, D28, D39, D46, D66–D71). */
export function SpoilerSetup() {
  const { state, draft, askReplace, cancel } = useSpoilerSetup();
  if (state.kind === "offline") return <OfflinePanel />;
  if (state.kind === "loading") return <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>;
  return (
    <SetupForm
      state={state}
      onDraft={draft}
      onAskReplace={askReplace}
      onCancel={() => void cancel()}
    />
  );
}

/** Why an EP can't be drafted (spec › Frontend, D71); null when it can. */
function epBlocked(ep: Episode, cut: Episodes): RefusalLine | null {
  if (ep.lines === 0) return { text: "EP นี้ไม่มีบทพูด", setupLink: false };
  if (ep.tokens === null) return { text: cut.tokens_not_ready ?? "", setupLink: true };
  return null;
}

type Loaded = Extract<SetupState, { kind: "loaded" }>;

type FormProps = {
  state: Loaded;
  /** Resolves to the refusal's code when the API refused. */
  onDraft: (order: Order, replace: boolean) => Promise<string | null>;
  onAskReplace: (asking: boolean) => void;
  onCancel: () => void;
};

function SetupForm({ state, onDraft, onAskReplace, onCancel }: FormProps) {
  // The Spoil draft's clip is picked when the page opens (spec › Frontend).
  const [clipId, setClipId] = useState<string | null>(
    state.clips.some((clip) => clip.id === state.draftClipId && isReady(clip)) ? state.draftClipId : null,
  );
  const [pickedEp, setPickedEp] = useState<number | null>(null);
  const [settings, setSettings] = useState<Settings>({
    style: "drama",
    layout: "B",
    targetS: DEFAULT_TARGET_S,
    voiceId: startingVoice(state.voices, state.lastVoiceId),
  });
  const episodes = useEpisodes(clipId);
  const cut = episodes.state.kind === "loaded" ? episodes.state.cut : null;
  // Until one is picked: the EP of the Spoil draft, else the first.
  const ep = cut?.episodes.find((one) => one.n === pickedEp) ?? cut?.episodes.find((one) => one.in_draft) ?? cut?.episodes[0] ?? null;
  const limit = cut?.limit ?? null;
  const blocked = ep && cut ? epBlocked(ep, cut) : null;
  const canDraft =
    ep !== null && blocked === null && ep.tokens !== null && limit !== null && ep.tokens <= limit && settings.voiceId !== null && state.job === null;

  const pickClip = (id: string) => {
    setClipId(id);
    setPickedEp(null);
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
      },
      replace,
    );
    if (refused === "episodes_changed") episodes.reload();
  };

  return (
    <div className="flex flex-col gap-4">
      {/* ลองอีกครั้ง sends the same draft again; a draft there was already agreed to be replaced. */}
      {state.banner && <SetupBanner banner={state.banner} onRetry={() => void send(state.draftExists)} />}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="flex flex-col gap-4 lg:w-[560px] lg:shrink-0">
          <ClipPicker clips={state.clips} picked={clipId} disabled={state.job !== null} onChange={pickClip} />
          {clipId !== null && (
            <EpisodePicker
              clipId={clipId}
              state={episodes.state}
              picked={ep?.n ?? null}
              disabled={state.job !== null}
              onPick={setPickedEp}
              onMinutes={(minutes) => episodes.put({ minutes })}
              onCuts={(cuts) => cut && episodes.put({ minutes: cut.minutes, cuts })}
            />
          )}
        </div>
        <SetupSettings
          settings={settings}
          voices={state.voices}
          ep={ep}
          limit={limit}
          epBlocked={blocked}
          canDraft={canDraft}
          job={state.job}
          confirmingReplace={state.confirmingReplace}
          onChange={setSettings}
          onDraft={() => (state.draftExists ? onAskReplace(true) : void send(false))}
          onReplace={() => void send(true)}
          onKeep={() => onAskReplace(false)}
          onCancel={onCancel}
        />
      </div>
    </div>
  );
}

/** Figma component `Setup banner`: built from Alert. */
function SetupBanner({ banner, onRetry }: { banner: Banner; onRetry: () => void }) {
  if (banner.kind === "failed") {
    return (
      <Alert
        tone="error"
        action={
          <button type="button" onClick={onRetry} className={`h-11 self-start px-3 sm:h-8 sm:self-auto ${OUTLINE_BUTTON}`}>
            ลองอีกครั้ง
          </button>
        }
      >
        {banner.text}
      </Alert>
    );
  }
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
