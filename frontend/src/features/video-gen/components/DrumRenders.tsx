import { useEffect, useId, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { DESTRUCTIVE_BUTTON, GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { ModalDialog } from "../../../components/ui/ModalDialog";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import downloadIcon from "../../../components/ui/assets/download.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { editedAt, formatDuration } from "../../../lib/format";
import { useRenders } from "../hooks/useRenders";
import { downloadName, renderFile, type RenderResult } from "../lib/render";

/**
 * ผล render ของ reel กลอง, under the form on the reel's page (`#/drums/{id}`): newest first, the newest
 * playing in a 9:16 player; download the mp4 and `.srt`, delete after asking (D10). It was a page of
 * its own (nav-ia D7). The page holds the one Render job: `ended` changes when a render ends, and the
 * results are read again then; `chosen` is the one a render just made (D35, nav-ia D14).
 */
export function DrumRenders({ id, ended, made }: { id: string; ended: number; made: string | null }) {
  const { state, reload, remove } = useRenders(id);
  const [chosen, setChosen] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<RenderResult | null>(null);
  const titleId = useId();

  useEffect(() => {
    if (ended > 0) void reload();
  }, [ended, reload]);
  useEffect(() => {
    if (made) setChosen(made);
  }, [made]);

  return (
    <section aria-labelledby={titleId} className="flex scroll-mt-4 flex-col gap-4">
      <div className="flex items-center gap-2">
        <h2 id={titleId} className="min-w-0 flex-1 pt-2 text-xl leading-[1.5] font-semibold text-foreground">
          ผล render
        </h2>
        {state.kind === "offline" && <RefreshButton onClick={() => void reload()} />}
      </div>
      {state.kind === "loading" && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "offline" && <OfflinePanel />}
      {state.kind === "ready" && state.failure && <Alert tone="error">{state.failure}</Alert>}
      {state.kind === "ready" &&
        (state.renders.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-border bg-card px-4 py-12 text-center leading-[1.5]">
            <p className="text-base font-medium text-foreground">ยังไม่เคย render reel นี้</p>
            <p className="text-[13px] text-muted-foreground">กด render ด้านบน แล้วผลจะขึ้นที่นี่</p>
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
    </section>
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
