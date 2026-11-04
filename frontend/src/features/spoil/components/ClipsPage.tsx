import { useEffect, useRef } from "react";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import { missingLabels, TRANSCRIBE_ITEMS, TRIM_ITEMS } from "../lib/gate";
import { gpuBusyText } from "../../../lib/gpu";
import { useDescribe } from "../hooks/useDescribe";
import { useSpoilDownload } from "../hooks/useSpoilDownload";
import { useTempClips } from "../hooks/useTempClips";
import { useTranscribe, type Confirmed } from "../hooks/useTranscribe";
import { playerReleasedFor, trimViewOf, useTrim } from "../hooks/useTrim";
import { derivedOf, derivedQuestion, type DerivedKind } from "../lib/trim";
import type { Range, TempClip } from "../../../lib/clips";
import arrowDownIcon from "../assets/arrow-down.svg";
import arrowRightIcon from "../assets/arrow-right.svg";
import { DownloadProgress } from "./DownloadProgress";
import { LinkForm } from "./LinkForm";
import { NoticeAlert } from "./NoticeAlert";
import { NotReady } from "./NotReady";
import { TempClipList } from "./TempClipList";
import { TranscriptPanel } from "./TranscriptPanel";

/** The คลิป tab (spoil-maker D53): the link field and clip list, an arrow, then the transcript panel (D25, D33). */
export function ClipsPage() {
  const list = useTempClips();
  // A job that ends (or is lost) changes the list: load it once (D6).
  const { state, start, cancel, reload, recheckStatus } = useSpoilDownload(list.refetch);
  // A 503 to ถอดบทพูด means the install changed: check the status again.
  const transcribe = useTranscribe(list.refetch, recheckStatus);
  const describe = useDescribe(list.refetch, recheckStatus);
  const trim = useTrim(list.refetch, recheckStatus);
  const video = useRef<HTMLVideoElement>(null);

  const refresh = () => {
    reload();
    list.reload();
    transcribe.reload();
    describe.reload();
    trim.reload();
  };

  // Opening the tab on an unfinished Trim job selects its clip once the list is in, with
  // the player waiting, as for a Transcribe job (spec › Frontend).
  const clipToSelect = trim.state.kind === "loaded" ? trim.state.clipToSelect : null;
  const loadedClips = list.state.kind === "loaded" ? list.state.clips : null;
  const { select } = transcribe;
  const { clipSelected } = trim;
  useEffect(() => {
    if (clipToSelect === null || loadedClips === null) return;
    const clip = loadedClips.find((one) => one.id === clipToSelect);
    if (clip) select(clip, false);
    clipSelected();
  }, [clipToSelect, loadedClips, select, clipSelected]);

  // Each check is spelled out, not a loop, so the code below sees every state narrowed to loaded.
  if (
    state.kind === "offline" ||
    list.state.kind === "offline" ||
    transcribe.state.kind === "offline" ||
    describe.state.kind === "offline" ||
    trim.state.kind === "offline"
  ) {
    return (
      <PageLayout tab="clips" action={<RefreshButton onClick={refresh} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  if (
    state.kind === "loading" ||
    list.state.kind === "loading" ||
    transcribe.state.kind === "loading" ||
    describe.state.kind === "loading" ||
    trim.state.kind === "loading"
  ) {
    return (
      <PageLayout tab="clips">
        <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
      </PageLayout>
    );
  }

  const clips = list.state.clips;
  const panel = transcribe.state;
  const selected = clips.find((clip) => clip.id === panel.selectedId) ?? null;
  const transcribingClip = panel.job ? clips.find((clip) => clip.id === panel.job?.clip_id) : undefined;
  const notice = state.kind === "ready" ? state.notice : null;
  const describing = describe.state.job;
  // One GPU job at a time (spoil-maker D45): while one runs, บรรยายฉาก waits, saying for what.
  const gpuBusyReason = panel.job ? gpuBusyText("transcribe") : describing ? gpuBusyText("describe") : null;
  const trimState = trim.state;
  const titleOf = (clipId: string) => clips.find((clip) => clip.id === clipId)?.title ?? clipId;

  /**
   * Transcribing again replaces the lines the user edited and removes the Spoil draft made
   * from the clip, so it asks first (spoil-maker D54, D49): the panel warns about a clip the
   * list marks `in_draft`; a loss only the API knows of (edited lines, a newer draft) is asked here.
   */
  const startTranscribe = async (clip: TempClip, draftConfirmed: boolean) => {
    const confirmed: Confirmed = { draftLoss: draftConfirmed };
    for (;;) {
      const result = await transcribe.start(clip.id, confirmed);
      if (result.kind === "handled" || !window.confirm(result.message)) return;
      if (result.kind === "has_edits") confirmed.editLoss = true;
      else confirmed.draftLoss = true;
    }
  };

  /** Lets go of the file: Windows can't delete or replace one the player holds open (D15, D41). */
  const releasePlayer = () => {
    if (video.current) {
      video.current.removeAttribute("src");
      video.current.load();
    }
  };

  /** Lets go of the file, then empties the panel. */
  const closePlayer = () => {
    releasePlayer();
    transcribe.select(null);
  };

  /**
   * A trim removes the Transcript, Shots, EP cuts and Spoil draft made from the clip, so it
   * asks first when the list shows any (D37); a loss only the API knows of is asked on its
   * `has_derived`. The player lets go of the file before each POST (D41).
   */
  const startTrim = async (clip: TempClip, ranges: Range[]) => {
    /** Asks about losing `kinds`; true when there is nothing to lose or the user goes on. */
    const agrees = (kinds: DerivedKind[]) => {
      const question = derivedQuestion(kinds);
      return question === null || window.confirm(question);
    };
    const post = (confirmed: boolean) => {
      releasePlayer();
      return trim.start(clip.id, ranges, confirmed);
    };
    const known = derivedOf(clip);
    if (!agrees(known)) return;
    const result = await post(known.length > 0);
    // Data made since the list loaded: asked once more, then sent with the loss confirmed.
    if (result.kind === "has_derived" && result.derived.length > 0 && agrees(result.derived)) await post(true);
  };

  return (
    <PageLayout tab="clips" wide>
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
            busyIds={[panel.job?.clip_id, trimState.job?.clip_id].filter((id): id is string => id !== undefined)}
            deleteErrors={list.state.deleteErrors}
            highlightId={notice?.clipId ?? null}
            onSelect={transcribe.select}
            onClosePlayer={closePlayer}
            onDelete={list.remove}
            describe={{
              job: describing,
              errors: describe.state.errors,
              busyReason: gpuBusyReason,
              onStart: (id, confirmDraftLoss) => void describe.start(id, confirmDraftLoss),
              onCancel: () => void describe.cancel(),
            }}
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
          onStart={(draftConfirmed = false) => selected && void startTranscribe(selected, draftConfirmed)}
          onCancel={() => void transcribe.cancel()}
          onEditLine={transcribe.editLine}
          playerReleased={selected !== null && playerReleasedFor(trimState, selected.id)}
          trimNotice={selected !== null && trimState.notice?.clipId === selected.id ? trimState.notice : null}
          trim={{
            view: selected ? trimViewOf(trimState, selected.id, titleOf) : { kind: "closed" },
            blocked: missingLabels(state.status, TRIM_ITEMS).length > 0 || (selected !== null && panel.job?.clip_id === selected.id),
            onOpen: trim.open,
            onEdit: trim.edit,
            onClose: trim.close,
            onTrim: (clip, ranges) => void startTrim(clip, ranges),
            onCancel: () => void trim.cancel(),
          }}
        />
      </div>
    </PageLayout>
  );
}
