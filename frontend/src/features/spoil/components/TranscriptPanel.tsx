import type { RefObject } from "react";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { useCopy } from "../../../lib/useCopy";
import { notice, type Notice } from "../lib/notice";
import { CLIPS_PATH, type TempClip } from "../hooks/useTempClips";
import { transcriptPath, type TranscribeJob, type Transcript } from "../hooks/useTranscribe";
import clockIcon from "../assets/clock.svg";
import copyIcon from "../assets/copy.svg";
import fileIcon from "../assets/file-text.svg";
import emptyIcon from "../assets/panel-empty.svg";
import { formatClock, formatDuration } from "./format";
import { NoticeAlert } from "./NoticeAlert";
import { NotReady } from "./NotReady";
import { ProgressCard } from "./ProgressCard";

type Props = {
  /** The selected clip, or null (D25). */
  clip: TempClip | null;
  videoRef: RefObject<HTMLVideoElement | null>;
  /** Start the player: the user picked the clip, rather than the tab opening on its job. */
  autoPlay: boolean;
  /** Labels of the Transcribe job's items that aren't ok (D27). */
  missing: string[];
  /** The unfinished Transcribe job, of this clip or another. */
  job: TranscribeJob | null;
  /** The title of the clip `job` is on. */
  jobTitle: string | null;
  /** The message after this clip's last job or refusal (D33); also shown once the clip is gone. */
  notice: Notice | null;
  transcript: Transcript | null;
  onStart: () => void;
  onCancel: () => void;
};

/** What stands under the clip's title: one state of the panel's table (spec › Frontend). */
type Action =
  | { kind: "progress"; job: TranscribeJob }
  | { kind: "notReady" }
  | { kind: "otherClip"; title: string | null }
  | { kind: "transcribed" }
  | { kind: "start" };

function actionOf(clip: TempClip, missing: string[], job: TranscribeJob | null, jobTitle: string | null): Action {
  if (job !== null && job.clip_id === clip.id) return { kind: "progress", job };
  if (missing.length > 0) return { kind: "notReady" };
  if (job !== null) return { kind: "otherClip", title: jobTitle };
  return clip.transcribed ? { kind: "transcribed" } : { kind: "start" };
}

const TRANSCRIBED = notice("info", "คลิปนี้ถอดแล้ว");

/** Figma component `Transcript panel`: the selected clip's player, its Transcribe job and Transcript (D22–D27, D33). */
export function TranscriptPanel(props: Props) {
  const { clip, videoRef, autoPlay, missing, job, jobTitle, notice, transcript, onStart, onCancel } = props;

  if (clip === null) {
    return (
      <section
        aria-label="กล่องถอดบทพูด"
        className="flex min-w-0 flex-1 flex-col items-center gap-2 rounded-2xl border border-border bg-card px-4 py-16"
      >
        {/* A clip that turned out to be gone (404) leaves its message here (D33). */}
        {notice && (
          <div className="w-full pb-6">
            <NoticeAlert notice={notice} />
          </div>
        )}
        <img src={emptyIcon} alt="" width={24} height={24} />
        <p className="text-sm leading-[1.5] text-muted-foreground">เลือกคลิปจากรายการ</p>
      </section>
    );
  }

  const action = actionOf(clip, missing, job, jobTitle);
  return (
    <section
      aria-label="กล่องถอดบทพูด"
      className="flex min-w-0 flex-1 flex-col gap-4 rounded-2xl border border-border bg-card p-4"
    >
      {/* Figma component `Player`; keyed so another clip starts a fresh element. */}
      <video
        ref={videoRef}
        key={clip.id}
        src={`${CLIPS_PATH}/${clip.id}/video`}
        controls
        autoPlay={autoPlay}
        className="h-[284px] w-full rounded-2xl bg-surface-inverse"
      />
      <div className="flex flex-col gap-0.5 leading-[1.5]">
        <p className="text-sm font-medium break-words text-foreground">{clip.title}</p>
        {clip.duration_s !== null && (
          <p className="font-mono text-[13px] text-muted-foreground">{formatDuration(clip.duration_s)}</p>
        )}
      </div>
      {notice && <NoticeAlert notice={notice} />}
      <ActionArea action={action} transcribed={clip.transcribed} missing={missing} onStart={onStart} onCancel={onCancel} />
      {/* A new job replaces the Transcript when it ends; until then only its progress shows. */}
      {clip.transcribed && transcript && action.kind !== "progress" && (
        <TranscriptView transcript={transcript} videoRef={videoRef} />
      )}
    </section>
  );
}

type ActionProps = {
  action: Action;
  transcribed: boolean;
  missing: string[];
  onStart: () => void;
  onCancel: () => void;
};

function ActionArea({ action, transcribed, missing, onStart, onCancel }: ActionProps) {
  switch (action.kind) {
    case "progress":
      return <JobProgress job={action.job} onCancel={onCancel} />;
    case "notReady":
      return <NotReady missing={missing} />;
    case "otherClip":
      return (
        <div className="flex items-center gap-3">
          <button type="button" disabled className={`h-9 px-4 ${PRIMARY_BUTTON}`}>
            {transcribed ? "ถอดใหม่" : "ถอดบทพูด"}
          </button>
          <img src={clockIcon} alt="" width={16} height={16} className="shrink-0" />
          <p className="min-w-0 flex-1 text-sm leading-[1.5] text-mid">กำลังถอด {action.title}</p>
        </div>
      );
    case "transcribed":
      return (
        <div className="flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <NoticeAlert notice={TRANSCRIBED} />
          </div>
          <button type="button" onClick={onStart} className={`h-9 px-4 ${OUTLINE_BUTTON}`}>
            ถอดใหม่
          </button>
        </div>
      );
    case "start":
      return (
        <button type="button" onClick={onStart} className={`h-9 w-fit px-4 ${PRIMARY_BUTTON}`}>
          ถอดบทพูด
        </button>
      );
  }
}

/** "กำลังเตรียมเสียง…" with a bar and no number, then "กำลังถอด" with its percent (D33). */
function JobProgress({ job, onCancel }: { job: TranscribeJob; onCancel: () => void }) {
  const transcribing = job.state === "transcribing";
  const headline = job.cancel_requested ? "กำลังยกเลิก…" : transcribing ? "กำลังถอด" : "กำลังเตรียมเสียง…";
  const percent = transcribing ? job.percent : null;
  return (
    <ProgressCard
      headline={headline}
      percent={percent}
      bar={percent ?? "unknown"}
      cancelling={job.cancel_requested}
      onCancel={onCancel}
    />
  );
}

/** The heading, Copy and the two files, then the lines; none of the buttons when there are no lines (D33). */
function TranscriptView({ transcript, videoRef }: { transcript: Transcript; videoRef: RefObject<HTMLVideoElement | null> }) {
  const empty = transcript.lines.length === 0;

  const jumpTo = (seconds: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = seconds;
    // A refused autoplay leaves the player paused at the line; it's still there to press play.
    void video.play()?.catch(() => {});
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <div className="flex min-w-0 flex-1 flex-col leading-[1.5] whitespace-nowrap">
          <h3 className="text-sm font-medium text-foreground">บทพูด</h3>
          <p className="truncate font-mono text-xs text-muted-foreground">ภาษา: {transcript.language ?? "ไม่ทราบ"}</p>
        </div>
        {!empty && <TranscriptActions transcript={transcript} />}
      </div>
      {empty ? (
        <p className="rounded-xl bg-muted px-2 py-8 text-center text-sm leading-[1.5] text-muted-foreground">
          ไม่พบคำพูดในคลิปนี้
        </p>
      ) : (
        <ol className="flex max-h-[320px] flex-col overflow-y-auto rounded-xl bg-muted p-2 leading-[1.5]">
          {transcript.lines.map((line, index) => (
            <li key={index}>
              {/* Figma component `Transcript line`: the whole line is the button. */}
              <button
                type="button"
                onClick={() => jumpTo(line.start_s)}
                className="flex w-full items-start gap-3 rounded-md px-2 py-1 text-left hover:bg-surface-strong"
              >
                <span className="shrink-0 font-mono text-[13px] whitespace-nowrap text-link">[{formatClock(line.start_s)}]</span>
                <span className="min-w-0 flex-1 text-sm break-words text-foreground">{line.text}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

/** Copy takes the same text as `.txt` (spec › Frontend); the files are links the browser downloads. */
function TranscriptActions({ transcript }: { transcript: Transcript }) {
  const text = transcript.lines.map((line) => `[${formatClock(line.start_s)}] ${line.text}\n`).join("");
  const { copied, copy } = useCopy(text);
  const path = transcriptPath(transcript.clip_id);
  return (
    <>
      <button type="button" onClick={copy} title={copied ? "คัดลอกแล้ว" : "คัดลอก"} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
        <img src={copyIcon} alt="" width={16} height={16} />
        {/* English, as on the Button in Figma (D19). */}
        Copy
      </button>
      {(["txt", "srt"] as const).map((extension) => (
        <a key={extension} href={`${path}.${extension}`} download className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
          <img src={fileIcon} alt="" width={16} height={16} />.{extension}
        </a>
      ))}
    </>
  );
}
