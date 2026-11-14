import { useId, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { DESTRUCTIVE_BUTTON, GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { ModalDialog } from "../../../components/ui/ModalDialog";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import downloadIcon from "../../../components/ui/assets/download.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { editedAt, formatDuration } from "../../../lib/format";
import { useDrumRender } from "../hooks/useDrumRender";
import { useRenders } from "../hooks/useRenders";
import { DRUMS_HASH, lessonHash } from "../../../lib/lesson";
import { downloadName, renderFile, renderingOf, type RenderResult } from "../lib/render";
import { RenderProgress } from "./RenderProgress";

/**
 * ผล render ของบทเรียน (`#/drums/{id}/renders`): newest first, the newest playing in a 9:16
 * player; download the mp4 and `.srt`, delete after asking (D10). This lesson's render shows its
 * percent on top. The design is pending, so the app's own parts.
 */
export function RendersPage({ id }: { id: string }) {
  const { state, reload, remove } = useRenders(id);
  // A render that ends adds its result.
  const { job } = useDrumRender(() => void reload());
  const [chosen, setChosen] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<RenderResult | null>(null);
  const rendering = renderingOf(job, id);

  return (
    <PageLayout tab="drums" wide action={state.kind === "offline" ? <RefreshButton onClick={() => void reload()} /> : undefined}>
      <div className="flex items-center gap-2">
        <a href={lessonHash(id)} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          กลับไปแก้บทเรียน
        </a>
        {state.kind === "ready" && (
          <h2 className="min-w-0 flex-1 truncate text-xl leading-[1.5] font-semibold text-foreground">{state.title} — ผล render</h2>
        )}
      </div>
      {rendering && (
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-4 py-3">
          <span className="text-sm leading-[1.5] font-medium text-foreground">กำลัง render</span>
          <RenderProgress percent={rendering.percent} />
        </div>
      )}
      {state.kind === "loading" && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "offline" && <OfflinePanel />}
      {state.kind === "not_found" && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card px-4 py-12">
          <p className="text-base leading-[1.5] font-medium text-foreground">ไม่พบบทเรียนนี้</p>
          <a href={DRUMS_HASH} className={`h-11 px-4 text-brand sm:h-9 ${GHOST_BUTTON} hover:bg-muted`}>
            กลับรายการบทเรียน
          </a>
        </div>
      )}
      {state.kind === "ready" && state.failure && <Alert tone="error">{state.failure}</Alert>}
      {state.kind === "ready" &&
        (state.renders.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-border bg-card px-4 py-12 text-center leading-[1.5]">
            <p className="text-base font-medium text-foreground">ยังไม่เคย render บทเรียนนี้</p>
            <p className="text-[13px] text-muted-foreground">กด render ในหน้าแก้บทเรียน แล้วผลจะขึ้นที่นี่</p>
          </div>
        ) : (
          <Results
            id={id}
            renders={state.renders}
            // The newest plays unless another was picked: the one a render just made (D35).
            playing={state.renders.find((r) => r.name === chosen) ?? state.renders[0]}
            onPlay={setChosen}
            onDelete={setDeleting}
          />
        ))}
      {deleting && (
        <DeleteRenderDialog
          result={deleting}
          onCancel={() => setDeleting(null)}
          onDelete={() => {
            setDeleting(null);
            void remove(deleting.name);
          }}
        />
      )}
    </PageLayout>
  );
}

type ResultsProps = {
  id: string;
  renders: RenderResult[];
  playing: RenderResult;
  onPlay: (name: string) => void;
  onDelete: (result: RenderResult) => void;
};

function Results({ id, renders, playing, onPlay, onDelete }: ResultsProps) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
      <video
        key={playing.name}
        src={renderFile(id, playing.name, ".mp4")}
        controls
        aria-label={`ผล render ${playing.name}`}
        className="aspect-[9/16] w-full max-w-[320px] self-center rounded-xl bg-black lg:self-start"
      />
      <ul aria-label="ผล render ทั้งหมด" className="flex min-w-0 flex-1 flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card">
        {renders.map((result) => (
          <li key={result.name} aria-current={result.name === playing.name} className="flex flex-wrap items-center gap-1 px-4 py-2.5 aria-[current=true]:bg-muted">
            <button type="button" onClick={() => onPlay(result.name)} className="flex min-w-0 flex-1 flex-col items-start gap-0.5 text-left leading-[1.5]">
              <span className="text-sm font-medium text-foreground">{editedAt(result.created_at)}</span>
              <span className="text-[13px] text-mid">{formatDuration(Math.round(result.length_s))} · 1080×1920</span>
            </button>
            <a href={renderFile(id, result.name, ".mp4")} download={downloadName(result, ".mp4")} className={`h-9 px-3 ${OUTLINE_BUTTON}`}>
              <img src={downloadIcon} alt="" width={16} height={16} />
              mp4
            </a>
            <a href={renderFile(id, result.name, ".srt")} download={downloadName(result, ".srt")} className={`h-9 px-3 ${GHOST_BUTTON}`}>
              <img src={downloadIcon} alt="" width={16} height={16} />
              .srt
            </a>
            <button type="button" aria-label={`ลบผล render ${result.name}`} onClick={() => onDelete(result)} className={`size-10 ${GHOST_BUTTON} hover:bg-muted`}>
              <img src={trashIcon} alt="" width={16} height={16} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Focus starts on ยกเลิก. */
function DeleteRenderDialog({ result, onCancel, onDelete }: { result: RenderResult; onCancel: () => void; onDelete: () => void }) {
  const titleId = useId();
  return (
    <ModalDialog titleId={titleId} onClose={onCancel} size="gap-4 sm:max-w-[480px]">
      <h3 id={titleId} className="text-lg leading-[1.5] font-semibold text-foreground">
        ลบผล render {editedAt(result.created_at)}?
      </h3>
      <p className="text-sm leading-[1.5] text-mid">ไฟล์ mp4 และ .srt จะหายไป</p>
      <div className="flex justify-end gap-2">
        <button type="button" autoFocus onClick={onCancel} className={`h-11 px-6 sm:h-10 ${OUTLINE_BUTTON}`}>
          ยกเลิก
        </button>
        <button type="button" onClick={onDelete} className={`h-11 px-6 sm:h-10 ${DESTRUCTIVE_BUTTON}`}>
          ลบ
        </button>
      </div>
    </ModalDialog>
  );
}
