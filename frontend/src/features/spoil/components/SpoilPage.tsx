import { useRef } from "react";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import { missingLabels, TRANSCRIBE_ITEMS } from "../lib/gate";
import { useSpoilDownload } from "../hooks/useSpoilDownload";
import { useTempClips } from "../hooks/useTempClips";
import { useTranscribe } from "../hooks/useTranscribe";
import arrowDownIcon from "../assets/arrow-down.svg";
import arrowRightIcon from "../assets/arrow-right.svg";
import { DownloadProgress } from "./DownloadProgress";
import { LinkForm } from "./LinkForm";
import { NoticeAlert } from "./NoticeAlert";
import { NotReady } from "./NotReady";
import { TempClipList } from "./TempClipList";
import { TranscriptPanel } from "./TranscriptPanel";

/** The สปอย tab: the link field and clip list, an arrow, then the transcript panel (D25, D33). */
export function SpoilPage() {
  const list = useTempClips();
  // A job that ends (or is lost) changes the list: load it once (D6).
  const { state, start, cancel, reload, recheckStatus } = useSpoilDownload(list.refetch);
  // A 503 to ถอดบทพูด means the install changed: check the status again.
  const transcribe = useTranscribe(list.refetch, recheckStatus);
  const video = useRef<HTMLVideoElement>(null);

  const refresh = () => {
    reload();
    list.reload();
    transcribe.reload();
  };

  if (state.kind === "offline" || list.state.kind === "offline" || transcribe.state.kind === "offline") {
    return (
      <PageLayout tab="spoil" action={<RefreshButton onClick={refresh} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  if (state.kind === "loading" || list.state.kind === "loading" || transcribe.state.kind === "loading") {
    return (
      <PageLayout tab="spoil">
        <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
      </PageLayout>
    );
  }

  const clips = list.state.clips;
  const panel = transcribe.state;
  const selected = clips.find((clip) => clip.id === panel.selectedId) ?? null;
  const transcribingClip = panel.job ? clips.find((clip) => clip.id === panel.job?.clip_id) : undefined;
  const notice = state.kind === "ready" ? state.notice : null;

  /** Lets go of the file (Windows can't delete one the player holds open, D15), then empties the panel. */
  const closePlayer = () => {
    if (video.current) {
      video.current.removeAttribute("src");
      video.current.load();
    }
    transcribe.select(null);
  };

  return (
    <PageLayout tab="spoil" wide>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="flex flex-col gap-4 lg:w-[520px] lg:shrink-0">
          {state.kind === "notReady" && <NotReady missing={state.missing} />}
          {state.kind === "ready" && (
            <>
              <LinkForm busy={state.job !== null} onSubmit={start} />
              {state.job && <DownloadProgress job={state.job} onCancel={cancel} />}
              {notice && <NoticeAlert notice={notice} />}
            </>
          )}
          {/* Shown when not ready too: the clips are still on disk (D9). */}
          <TempClipList
            clips={clips}
            selectedId={selected?.id ?? null}
            transcribingId={panel.job?.clip_id ?? null}
            deleteErrors={list.state.deleteErrors}
            highlightId={notice?.clipId ?? null}
            onSelect={transcribe.select}
            onClosePlayer={closePlayer}
            onDelete={list.remove}
          />
        </div>
        <div className="flex justify-center lg:pt-[140px]">
          <img src={arrowDownIcon} alt="" width={24} height={24} className="lg:hidden" />
          <img src={arrowRightIcon} alt="" width={24} height={24} className="hidden self-start lg:block" />
        </div>
        <TranscriptPanel
          clip={selected}
          videoRef={video}
          autoPlay={panel.autoPlay}
          missing={missingLabels(state.status, TRANSCRIBE_ITEMS)}
          job={panel.job}
          jobTitle={transcribingClip?.title ?? panel.job?.clip_id ?? null}
          notice={panel.notice}
          transcript={panel.transcript}
          onStart={() => selected && void transcribe.start(selected.id)}
          onCancel={() => void transcribe.cancel()}
        />
      </div>
    </PageLayout>
  );
}
