import { useEffect, useRef } from "react";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import { missingLabels, TRANSCRIBE_ITEMS, TRIM_ITEMS } from "../lib/gate";
import { gpuBusyText } from "../../../lib/gpu";
import { useDescribe } from "../hooks/useDescribe";
import { useFileImport, type Upload } from "../hooks/useFileImport";
import { useSpoilDownload } from "../hooks/useSpoilDownload";
import { useTempClips } from "../hooks/useTempClips";
import { useTranscribe, type TranscribeLoss } from "../hooks/useTranscribe";
import { playerReleasedFor, trimViewOf, useTrim } from "../hooks/useTrim";
import { postConfirming } from "../lib/confirm";
import { allSettled } from "../lib/settled";
import type { Range, TempClip } from "../../../lib/clips";
import arrowDownIcon from "../assets/arrow-down.svg";
import arrowRightIcon from "../assets/arrow-right.svg";
import { DownloadProgress } from "./DownloadProgress";
import { FileDropArea } from "./FileDropArea";
import { LinkForm } from "./LinkForm";
import { NoticeAlert } from "./NoticeAlert";
import { ProgressCard } from "./ProgressCard";
import { NotReady } from "./NotReady";
import { TempClipList } from "./TempClipList";
import { TranscriptPanel } from "./TranscriptPanel";

/** The คลิป tab (spoil-maker D53): the link field and clip list, an arrow, then the transcript panel (D25, D33). */
export function ClipsPage() {
  const list = useTempClips();
  // A job that ends (or is lost) changes the list: load it once (D6).
  const download = useSpoilDownload(list.refetch);
  // A 503 to ถอดบทพูด means the install changed: check the status again.
  const transcribe = useTranscribe(list.refetch, download.recheckStatus);
  const describe = useDescribe(list.refetch, download.recheckStatus);
  const trim = useTrim(list.refetch, download.recheckStatus);
  const fileImport = useFileImport({ onImported: list.refetch, onNotReady: download.recheckStatus });
  const video = useRef<HTMLVideoElement>(null);
  const states = [download.state, list.state, transcribe.state, describe.state, trim.state] as const;

  // Opening the tab (or Refresh) on an unfinished Trim or Transcribe job selects its clip
  // once everything is in, with the player waiting (spec › Frontend).
  const jobClipChecked = useRef(false);
  const { select } = transcribe;
  useEffect(() => {
    if (jobClipChecked.current || !allSettled(states)) return;
    jobClipChecked.current = true;
    const [, listed, transcribing, , trimming] = states;
    const clipId = trimming.job?.clip_id ?? transcribing.job?.clip_id;
    const clip = listed.clips.find((one) => one.id === clipId);
    if (clip) select(clip, false);
  });

  // Behind the offline panel there is no ยกเลิก: an upload under way stops (D58).
  const othersOffline = states.some((one) => one.kind === "offline");
  const { reset: resetImport } = fileImport;
  useEffect(() => {
    if (othersOffline) resetImport();
  }, [othersOffline, resetImport]);

  const refresh = () => {
    jobClipChecked.current = false;
    download.reload();
    list.reload();
    transcribe.reload();
    describe.reload();
    trim.reload();
    fileImport.reset();
  };

  if (fileImport.state.kind === "offline" || othersOffline) {
    return (
      <PageLayout tab="clips" action={<RefreshButton onClick={refresh} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  if (!allSettled(states)) {
    return (
      <PageLayout tab="clips">
        <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
      </PageLayout>
    );
  }

  const [state, listed, panel, described, trimState] = states;
  const clips = listed.clips;
  const selected = clips.find((clip) => clip.id === panel.selectedId) ?? null;
  const transcribingClip = panel.job ? clips.find((clip) => clip.id === panel.job?.clip_id) : undefined;
  const imported = fileImport.state.kind === "ready" ? fileImport.state : null;
  const upload = imported?.upload ?? null;
  // One message above the list: the import's or the download's, whichever came last (each clears the other).
  const notice = imported?.notice ?? (state.kind === "ready" ? state.notice : null);
  const describing = described.job;
  // One GPU job at a time (spoil-maker D45): while one runs, บรรยายฉาก waits, saying for what.
  const gpuBusyReason = panel.job ? gpuBusyText("transcribe") : describing ? gpuBusyText("describe") : null;
  const titleOf = (clipId: string) => clips.find((clip) => clip.id === clipId)?.title ?? clipId;

  /** Another clip in the panel (or none): each job's last message goes with the old one (D33). */
  const selectClip = (clip: TempClip | null) => {
    transcribe.select(clip);
    trim.clearNotice();
  };

  /**
   * Transcribing again replaces the lines the user edited and removes the Spoil draft made
   * from the clip, so it asks first (spoil-maker D54, D49): the panel warns about a clip the
   * list marks `in_draft`; a loss only the API knows of (edited lines, a newer draft) is asked here.
   */
  const startTranscribe = (clip: TempClip, draftConfirmed: boolean) =>
    postConfirming<TranscribeLoss>((agreed) =>
      transcribe.start(clip.id, { editLoss: agreed.includes("has_edits"), draftLoss: draftConfirmed || agreed.includes("in_draft") }),
    );

  /**
   * A trim removes the Transcript, Shots, EP cuts and Spoil draft made from the clip: the
   * API's `has_derived` asks first (D37). The player lets go of the file for the POST and
   * gets it back when the user says no (D41).
   */
  const startTrim = async (clip: TempClip, ranges: Range[]) => {
    const went = await postConfirming<"has_derived">((agreed) => trim.start(clip.id, ranges, agreed.includes("has_derived")));
    if (!went) trim.returnPlayer();
  };

  /** Lets go of the file, then empties the panel: Windows can't delete one the player holds open (D15). */
  const closePlayer = () => {
    if (video.current) {
      video.current.removeAttribute("src");
      video.current.load();
    }
    selectClip(null);
  };

  return (
    <PageLayout tab="clips" wide>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="flex flex-col gap-4 lg:w-[520px] lg:shrink-0">
          {state.kind === "notReady" && <NotReady missing={state.missing} />}
          {state.kind === "ready" && (
            <>
              <FileDropArea
                disabled={state.job !== null || upload !== null}
                emphasis={notice?.pickFile === true}
                onFiles={(files) => {
                  download.clearNotice();
                  void fileImport.start(files);
                }}
              >
                <LinkForm
                  busy={state.job !== null || upload !== null}
                  locked={upload !== null}
                  onSubmit={(url) => {
                    fileImport.clearNotice();
                    void download.start(url);
                  }}
                />
                {state.job && <DownloadProgress job={state.job} onCancel={download.cancel} />}
                {upload && <ImportProgress upload={upload} onCancel={fileImport.cancel} />}
                {notice && <NoticeAlert notice={notice} />}
              </FileDropArea>
            </>
          )}
          {/* Shown when not ready too: the clips are still on disk (D9). */}
          <TempClipList
            clips={clips}
            selectedId={selected?.id ?? null}
            busyIds={[panel.job?.clip_id, trimState.job?.clip_id].filter((id): id is string => id !== undefined)}
            deleteErrors={listed.deleteErrors}
            highlightId={notice?.clipId ?? null}
            onSelect={selectClip}
            onClosePlayer={closePlayer}
            onDelete={list.remove}
            describe={{
              job: describing,
              errors: described.errors,
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
          trim={
            selected && {
              view: trimViewOf(trimState, selected.id, titleOf),
              blocked: missingLabels(state.status, TRIM_ITEMS).length > 0 || panel.job?.clip_id === selected.id,
              onOpen: () => trim.open(selected.id),
              onEdit: (drafts) => trim.edit(selected.id, drafts),
              onClose: () => trim.close(selected.id),
              onTrim: (ranges) => void startTrim(selected, ranges),
              onCancel: () => void trim.cancel(),
            }
          }
        />
      </div>
    </PageLayout>
  );
}

/** A file on its way in (Figma `Download progress` importing and checking file, spec › Frontend). */
function ImportProgress({ upload, onCancel }: { upload: Upload; onCancel: () => void }) {
  return upload.phase === "checking" ? (
    <ProgressCard headline="กำลังตรวจไฟล์…" percent={null} bar="unknown" cancelling={false} />
  ) : (
    <ProgressCard
      headline={`กำลังเอาไฟล์เข้า ${upload.name}`}
      percent={upload.percent}
      bar={upload.percent}
      cancelling={false}
      onCancel={onCancel}
    />
  );
}
