import { useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import {
  useSpoilerSetup,
  useTokens,
  type Banner,
  type Order,
  type SetupState,
} from "../hooks/useSpoilerSetup";
import type { Voice } from "../hooks/useVoices";
import { ClipPicker, isReady } from "./ClipPicker";
import { SetupSettings, type Settings } from "./SetupSettings";

const DEFAULT_TARGET_S = 60; // D39

/** The voice ร่างบท starts with: the one of the last draft while it is still saved, else the newest (spec › ค่าที่จำไว้). */
function startingVoice(voices: Voice[], lastVoiceId: string | null): string | null {
  return voices.find((voice) => voice.id === lastVoiceId)?.id ?? voices[0]?.id ?? null;
}

/** Step 1 of the สปอย tab, ตั้งค่าคลิปสปอย (Figma `Spoiler setup`, spoil-maker D5, D7, D8, D25, D28, D39, D46). */
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

type Loaded = Extract<SetupState, { kind: "loaded" }>;

type FormProps = {
  state: Loaded;
  onDraft: (order: Order, replace: boolean) => void;
  onAskReplace: (asking: boolean) => void;
  onCancel: () => void;
};

function SetupForm({ state, onDraft, onAskReplace, onCancel }: FormProps) {
  const [picked, setPicked] = useState<string[]>([]);
  const [settings, setSettings] = useState<Settings>({
    style: "drama",
    layout: "B",
    targetS: DEFAULT_TARGET_S,
    voiceId: startingVoice(state.voices, state.lastVoiceId),
  });
  // Only clips still ready count: one redone elsewhere drops out of the pick.
  const readyPicked = picked.filter((id) => state.clips.some((clip) => clip.id === id && isReady(clip)));
  const tokens = useTokens(readyPicked);
  const canDraft =
    readyPicked.length > 0 &&
    settings.voiceId !== null &&
    tokens.kind === "counted" &&
    tokens.total <= tokens.limit &&
    state.job === null;

  const order = (): Order => ({
    clip_ids: readyPicked,
    style: settings.style,
    layout: settings.layout,
    target_s: settings.targetS,
    voice_id: settings.voiceId ?? "",
  });

  const banner = state.banner ?? (tokens.kind === "refused" ? tokens.banner : null);

  return (
    <div className="flex flex-col gap-4">
      {/* ลองอีกครั้ง sends the same draft again; a draft there was already agreed to be replaced. */}
      {banner && <SetupBanner banner={banner} onRetry={() => onDraft(order(), state.draftExists)} />}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <ClipPicker clips={state.clips} picked={readyPicked} disabled={state.job !== null} onChange={setPicked} />
        <SetupSettings
          settings={settings}
          voices={state.voices}
          tokens={tokens}
          canDraft={canDraft}
          job={state.job}
          confirmingReplace={state.confirmingReplace}
          onChange={setSettings}
          onDraft={() => (state.draftExists ? onAskReplace(true) : onDraft(order(), false))}
          onReplace={() => onDraft(order(), true)}
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
