import { useId, useRef, useState, type DragEvent, type FormEvent } from "react";
import { Alert } from "../../../components/ui/Alert";
import { DESTRUCTIVE_BUTTON, GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { FixCommand } from "../../../components/ui/FixCommand";
import { inputClass } from "../../../components/ui/inputStyles";
import { ModalDialog } from "../../../components/ui/ModalDialog";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import trashIcon from "../../../components/ui/assets/trash.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { formatDuration } from "../../../lib/format";
import { useSongs, type Notice, type Upload } from "../hooks/useSongs";
import { FILE_ACCEPT, FILE_HINT, importText, isImporting, NOTES_ONLY, pickedText, songHash, SOURCE_LABELS, type PickJob, type SongImport, type SongRow } from "../lib/songs";

/** รายการเพลง (`#/songs`): the link box and file box, the running import, the songs newest first, delete (spec › Design). The design is pending, so the app's own parts. */
export function SongList({ onKnownSong }: { onKnownSong: (id: string) => void }) {
  const { state, pick, reload, startLink, importFile, cancelUpload, cancelImport, remove } = useSongs(onKnownSong);
  const [deleting, setDeleting] = useState<SongRow | null>(null);

  if (state.kind === "offline") {
    return (
      <PageLayout tab="songs" action={<RefreshButton onClick={() => void reload()} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  const ready = state.kind === "ready" ? state : null;
  const running = ready?.job && isImporting(ready.job) ? ready.job : null;
  const busy = running !== null || ready?.upload !== null;

  return (
    <PageLayout tab="songs">
      <h2 className="text-xl leading-[1.5] font-semibold text-foreground">แกะเพลง</h2>
      <section aria-label="เอาเพลงเข้า" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <LinkForm busy={busy || ready === null} onSubmit={startLink} />
        <FileBox disabled={busy || ready === null} onFile={(file) => void importFile(file)} />
        <p className="text-[13px] leading-[1.5] text-mid">{NOTES_ONLY}</p>
        {running && <ImportRow job={running} onCancel={() => void cancelImport()} />}
        {ready?.upload && <UploadRow upload={ready.upload} onCancel={cancelUpload} />}
        {ready?.notice && <NoticeAlert notice={ready.notice} />}
      </section>
      <section aria-label="เพลงทั้งหมด" aria-busy={state.kind === "loading"} className="overflow-hidden rounded-2xl border border-border bg-card">
        {ready === null ? (
          <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
        ) : ready.songs.length === 0 ? (
          <p className="px-4 py-12 text-center text-sm leading-[1.5] text-mid">ยังไม่มีเพลง วางลิงก์เพลงแรกหรือเลือกไฟล์ด้านบน</p>
        ) : (
          <ul className="divide-y divide-border">
            {ready.songs.map((song) => (
              <Row key={song.id} song={song} pick={pick} onDelete={() => setDeleting(song)} />
            ))}
          </ul>
        )}
      </section>
      {deleting && (
        <DeleteSongDialog
          song={deleting}
          onCancel={() => setDeleting(null)}
          onDelete={() => {
            setDeleting(null);
            void remove(deleting.id);
          }}
        />
      )}
    </PageLayout>
  );
}

function LinkForm({ busy, onSubmit }: { busy: boolean; onSubmit: (url: string) => Promise<boolean> }) {
  const [url, setUrl] = useState("");
  const inputId = useId();

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    void onSubmit(trimmed).then((started) => started && setUrl(""));
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <label htmlFor={inputId} className="font-button text-sm leading-5 font-medium text-foreground">
          ลิงก์เพลง
        </label>
        <input
          id={inputId}
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="วางลิงก์เพลง (YouTube หรือเว็บอื่น)"
          className={`${inputClass(false)} font-button placeholder:text-muted-foreground`}
        />
      </div>
      <button type="submit" disabled={busy || url.trim() === ""} className={`h-11 px-6 sm:h-10 ${PRIMARY_BUTTON}`}>
        เอาเพลงเข้า
      </button>
    </form>
  );
}

const isFileDrag = (event: DragEvent) => event.dataTransfer.types.includes("Files");

/** The file box: one button that opens the file dialog, and a file dropped on it goes in the same way (spoil D58). */
function FileBox({ disabled, onFile }: { disabled: boolean; onFile: (file: File) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const hintId = useId();
  const [over, setOver] = useState(false);

  const onDrop = (event: DragEvent) => {
    if (!isFileDrag(event)) return;
    event.preventDefault();
    setOver(false);
    const [file] = Array.from(event.dataTransfer.files);
    if (!disabled && file) onFile(file);
  };

  return (
    <div
      onDragOver={(event) => {
        if (!isFileDrag(event)) return;
        event.preventDefault(); // without this the drop never comes here
        event.dataTransfer.dropEffect = disabled ? "none" : "copy";
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
    >
      <button
        type="button"
        disabled={disabled}
        onClick={() => input.current?.click()}
        aria-describedby={hintId}
        className={`flex w-full flex-col items-center gap-2 rounded-2xl border-[1.5px] border-dashed px-4 py-5 ${
          over ? "border-brand-accent bg-accent-subtle" : "border-border bg-card hover:bg-muted disabled:bg-muted disabled:hover:bg-muted"
        }`}
      >
        <span className={`flex h-9 items-center justify-center px-4 ${OUTLINE_BUTTON}`}>เลือกไฟล์ในเครื่อง</span>
        <span id={hintId} className="text-center text-xs leading-[1.5] text-mid">
          หรือลากไฟล์มาวาง · {FILE_HINT}
        </span>
      </button>
      <input
        ref={input}
        type="file"
        accept={FILE_ACCEPT}
        aria-label="ไฟล์เพลง"
        hidden
        tabIndex={-1}
        onChange={(event) => {
          const [file] = Array.from(event.target.files ?? []);
          event.target.value = ""; // empty again, so the same file can be picked once more after a refusal
          if (file) onFile(file);
        }}
      />
    </div>
  );
}

/** The running link import: its title or link, what it is doing, the bar and ยกเลิก (D18). */
function ImportRow({ job, onCancel }: { job: SongImport; onCancel: () => void }) {
  return (
    <div role="group" aria-label="งานเอาเพลงเข้า" className="flex flex-col gap-2 rounded-xl bg-muted px-4 py-3">
      <div className="flex items-center gap-3">
        <p className="min-w-0 flex-1 truncate text-sm font-medium text-foreground">{job.title ?? job.url}</p>
        <p className="shrink-0 font-button text-xs leading-4 text-mid">{importText(job)}</p>
        <button type="button" disabled={job.cancel_requested} onClick={onCancel} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={xIcon} alt="" width={16} height={16} />
          ยกเลิก
        </button>
      </div>
      <ProgressBar label="เอาเพลงเข้า" percent={job.state === "downloading" ? (job.percent ?? 0) : "unknown"} cancelling={job.cancel_requested} />
    </div>
  );
}

/** A file going out: its percent, then the backend converting it (ADR 0028). */
function UploadRow({ upload, onCancel }: { upload: Upload; onCancel: () => void }) {
  return (
    <div role="group" aria-label="ส่งไฟล์" className="flex flex-col gap-2 rounded-xl bg-muted px-4 py-3">
      <div className="flex items-center gap-3">
        <p className="min-w-0 flex-1 truncate text-sm font-medium text-foreground">{upload.name}</p>
        <p className="shrink-0 font-button text-xs leading-4 text-mid">{upload.converting ? "กำลังแปลงเสียง…" : `กำลังส่ง ${upload.percent}%`}</p>
        {!upload.converting && (
          <button type="button" onClick={onCancel} className={`h-8 px-3 ${GHOST_BUTTON}`}>
            <img src={xIcon} alt="" width={16} height={16} />
            ยกเลิก
          </button>
        )}
      </div>
      <ProgressBar label={`ส่งไฟล์ ${upload.name}`} percent={upload.converting ? "unknown" : upload.percent} />
    </div>
  );
}

function NoticeAlert({ notice }: { notice: Notice }) {
  return (
    <Alert tone={notice.tone}>
      <div className="flex flex-col gap-2">
        <p>{notice.text}</p>
        {notice.fixes.map((fix) => (
          <FixCommand key={fix} command={fix} />
        ))}
      </div>
    </Alert>
  );
}

/** One song: title, subtitle, where it came from, its length, whether it was or is being picked, its lessons (spec › Design). */
function Row({ song, pick, onDelete }: { song: SongRow; pick: PickJob | null; onDelete: () => void }) {
  return (
    <li className="flex items-center gap-1 pr-2">
      <a href={songHash(song.id)} className="flex min-w-0 flex-1 flex-col gap-0.5 py-3 pl-4 leading-[1.5] hover:bg-muted">
        <span className="truncate text-sm font-medium text-foreground">{song.title}</span>
        {song.subtitle && <span className="truncate text-[13px] text-mid">{song.subtitle}</span>}
        <span className="flex flex-wrap gap-x-1.5 text-[13px] text-mid">
          <span>{SOURCE_LABELS[song.source_kind]}</span>
          <span className="text-muted-foreground">·</span>
          <span>{formatDuration(Math.round(song.duration_s))}</span>
          <span className="text-muted-foreground">·</span>
          <span>{pickedText(song, pick)}</span>
          <span className="text-muted-foreground">·</span>
          <span>{song.lessons} บทเรียน</span>
        </span>
      </a>
      <button type="button" aria-label={`ลบ ${song.title}`} onClick={onDelete} className={`size-10 ${GHOST_BUTTON} hover:bg-muted`}>
        <img src={trashIcon} alt="" width={16} height={16} />
      </button>
    </li>
  );
}

/** Focus starts on ยกเลิก; the lessons made from the song stay (D12, D18). */
function DeleteSongDialog({ song, onCancel, onDelete }: { song: SongRow; onCancel: () => void; onDelete: () => void }) {
  const titleId = useId();
  return (
    <ModalDialog titleId={titleId} onClose={onCancel} size="gap-4 sm:max-w-[480px]">
      <h3 id={titleId} className="text-lg leading-[1.5] font-semibold break-words text-foreground">
        ลบ {song.title}?
      </h3>
      <p className="text-sm leading-[1.5] text-mid">เสียงเพลงและผลแกะหายไป บทเรียนกลองที่สร้างจากเพลงนี้ยังอยู่</p>
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
