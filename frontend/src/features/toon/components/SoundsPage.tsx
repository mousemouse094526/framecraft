import { useRef, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { playAudio } from "../../../lib/audio";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import downloadWhiteIcon from "../assets/download-white.svg";
import loaderIcon from "../assets/loader.svg";
import musicIcon from "../assets/music.svg";
import playIcon from "../assets/play.svg";
import uploadIcon from "../assets/upload.svg";
import { useSounds } from "../hooks/useSounds";
import { isImporting, SOUND_NAME_MAX, soundFilePath, soundLength, type Sound } from "../lib/sounds";
import { LIST_HASH } from "../lib/series";
import { CommitField } from "./CommitField";
import { NoticeLine } from "./NoticeLine";

/** legal item 4, shown before every file or link, nothing to accept (spec › Frontend). */
export const SOUND_RIGHTS = "ใช้เสียงของคุณเอง หรือเสียงที่ license ให้ใช้ในวิดีโอที่เผยแพร่ได้ และใส่เครดิตตามที่ license กำหนด";

/** `#/toon/sounds`: the tab's background sound library (Figma toon / 8, D5, D16, D39). */
export function SoundsPage() {
  const { state, reload, rename, remove, uploadFile, cancelUpload, download, cancelDownload } = useSounds();
  const file = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState("");

  if (state.kind === "offline") {
    return (
      <PageLayout tab="toon" wide action={<RefreshButton onClick={() => void reload()} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }
  if (state.kind === "loading") {
    return (
      <PageLayout tab="toon" wide>
        <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
      </PageLayout>
    );
  }

  const { sounds, job, importNotice, listNotice, upload } = state;
  const loading = job !== null && isImporting(job) ? job : null;
  const busy = loading !== null || upload !== null;
  const count = sounds.length + (upload ? 1 : 0);

  return (
    <PageLayout tab="toon" wide>
      <div className="flex flex-wrap items-center gap-2">
        <a href={LIST_HASH} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          การ์ตูนเล่า
        </a>
        <h2 className="text-xl leading-[1.5] font-semibold text-foreground">คลังเสียงพื้น</h2>
      </div>
      <section aria-label="เพิ่มเสียงพื้น" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
        <h3 className="text-base leading-[1.5] font-semibold text-foreground">เพิ่มเสียงพื้น</h3>
        <Alert tone="info" title="ก่อนเอาเสียงเข้า">
          {SOUND_RIGHTS}
        </Alert>
        <form
          className="flex flex-col gap-4 sm:flex-row sm:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            void download(url.trim()).then((started) => started && setUrl(""));
          }}
        >
          <div className="flex flex-col gap-1.5">
            <p className="text-xs leading-[1.5] text-mid">ไฟล์เสียง (mp3, wav, m4a ยาวไม่เกิน 20 นาที)</p>
            <button type="button" disabled={busy} onClick={() => file.current?.click()} className={`h-9 self-start px-4 ${OUTLINE_BUTTON}`}>
              <img src={uploadIcon} alt="" width={16} height={16} />
              เอาไฟล์เข้า
            </button>
            <input
              ref={file}
              type="file"
              accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac"
              aria-label="เลือกไฟล์เสียง"
              className="hidden"
              onChange={(event) => {
                const picked = event.target.files?.[0];
                event.target.value = "";
                if (picked) void uploadFile(picked);
              }}
            />
          </div>
          <p className="text-[13px] leading-[1.5] text-muted-foreground">หรือ</p>
          <label className="flex min-w-0 flex-1 flex-col gap-2">
            <span className="font-button text-sm leading-5 font-medium text-foreground">ลิงก์เสียง</span>
            <input
              type="url"
              value={url}
              disabled={busy}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://"
              className="h-10 rounded-lg border border-border bg-card px-3 font-button text-sm text-foreground"
            />
            {loading && (
              <span className="font-button text-xs leading-4 text-muted-foreground">
                {loading.state === "converting" ? "กำลังแปลงไฟล์…" : `กำลังโหลด ${loading.percent ?? 0}%`}
              </span>
            )}
          </label>
          <button type="submit" disabled={busy || url.trim() === ""} className={`h-9 px-4 ${PRIMARY_BUTTON}`}>
            <img src={downloadWhiteIcon} alt="" width={16} height={16} />
            {loading ? "กำลังโหลด…" : "โหลด"}
          </button>
        </form>
        {loading && (
          <div className="flex items-center gap-2">
            <div className="w-80 max-w-full">
              <ProgressBar label="โหลดเสียงจากลิงก์" percent={loading.percent ?? 0} cancelling={loading.cancel_requested} />
            </div>
            <p className="font-mono text-xs font-medium text-mid">{loading.percent ?? 0}%</p>
            <button
              type="button"
              disabled={loading.cancel_requested}
              onClick={() => void cancelDownload()}
              className={`h-8 px-3 ${GHOST_BUTTON}`}
            >
              <img src={xIcon} alt="" width={16} height={16} />
              ยกเลิก
            </button>
          </div>
        )}
        {importNotice && <NoticeLine notice={importNotice} />}
      </section>
      <section aria-label="เสียงพื้น" className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-2">
        <div className="flex items-center gap-2 px-4 py-2 leading-[1.5]">
          <h3 className="text-base font-semibold text-foreground">เสียงพื้น {count} เสียง</h3>
          <p className="text-[13px] text-mid">ใช้ร่วมกันทุก Series</p>
        </div>
        {listNotice && (
          <div className="px-2">
            <NoticeLine notice={listNotice} />
          </div>
        )}
        {count === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 text-center leading-[1.5]">
            <img src={musicIcon} alt="" width={24} height={24} />
            <p className="text-base font-medium text-foreground">ยังไม่มีเสียงพื้น</p>
            <p className="text-[13px] text-muted-foreground">เอาไฟล์หรือลิงก์เข้า แล้ว AI จะเลือกเสียงให้แต่ละช่วง</p>
          </div>
        ) : (
          <ul className="flex flex-col gap-1">
            {upload && (
              <li className="flex h-[60px] items-center gap-3 rounded-xl px-4 py-2.5">
                <Thumb icon={loaderIcon} spin />
                <p className="flex h-9 min-w-0 flex-1 items-center truncate rounded-lg border border-border bg-card px-2.5 text-sm text-foreground">
                  {upload.name}
                </p>
                <div className="w-40">
                  <ProgressBar label={`ส่งไฟล์ ${upload.name}`} percent={upload.percent} />
                </div>
                <p className="font-mono text-xs font-medium text-mid">{upload.percent}%</p>
                <button type="button" onClick={cancelUpload} className={`h-8 px-3 ${GHOST_BUTTON}`}>
                  <img src={xIcon} alt="" width={16} height={16} />
                  ยกเลิก
                </button>
              </li>
            )}
            {sounds.map((sound) => (
              <SoundRow key={sound.id} sound={sound} onRename={(name) => rename(sound, name)} onDelete={() => void remove(sound)} />
            ))}
          </ul>
        )}
      </section>
    </PageLayout>
  );
}

function Thumb({ icon, spin = false }: { icon: string; spin?: boolean }) {
  return (
    <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent-subtle">
      <img src={icon} alt="" width={18} height={18} className={spin ? "motion-safe:animate-spin" : undefined} />
    </span>
  );
}

/** Figma `Toon/SoundRow`: the name (edited in place), its length, ฟัง and ลบ. */
function SoundRow({ sound, onRename, onDelete }: { sound: Sound; onRename: (name: string) => Promise<boolean>; onDelete: () => void }) {
  return (
    <li aria-label={sound.name} className="flex h-[60px] items-center gap-3 rounded-xl px-4 py-2.5">
      <Thumb icon={musicIcon} />
      <CommitField
        required
        aria-label={`ชื่อเสียง ${sound.name}`}
        value={sound.name}
        maxLength={SOUND_NAME_MAX}
        onCommit={onRename}
        className="h-9 min-w-0 flex-1 rounded-lg border border-border bg-card px-2.5 text-sm text-foreground"
      />
      <p className="font-mono text-xs font-medium text-mid">{soundLength(sound.duration_s)}</p>
      <button
        type="button"
        aria-label={`ฟัง ${sound.name}`}
        onClick={() => playAudio(soundFilePath(sound.id))}
        className="flex size-9 items-center justify-center rounded-lg hover:bg-muted"
      >
        <img src={playIcon} alt="" width={16} height={16} />
      </button>
      <button
        type="button"
        aria-label={`ลบ ${sound.name}`}
        onClick={onDelete}
        className="flex size-9 items-center justify-center rounded-lg hover:bg-muted"
      >
        <img src={trashIcon} alt="" width={16} height={16} />
      </button>
    </li>
  );
}
