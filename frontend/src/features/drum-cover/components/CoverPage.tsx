import { useCallback, useId, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { BackgroundPicker } from "../../../components/ui/BackgroundPicker";
import { DESTRUCTIVE_BUTTON, GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON, SECONDARY_BUTTON } from "../../../components/ui/buttonStyles";
import { inputClass } from "../../../components/ui/inputStyles";
import { Labeled } from "../../../components/ui/Labeled";
import { ModalDialog } from "../../../components/ui/ModalDialog";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import { RefusedAlert } from "../../../components/ui/RefusedAlert";
import { SegmentedChoice } from "../../../components/ui/SegmentedChoice";
import { Switch } from "../../../components/ui/Switch";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import downloadIcon from "../../../components/ui/assets/download.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { postForBlob } from "../../../lib/api";
import { editedAt, formatDuration } from "../../../lib/format";
import { refusedLine, type Refused } from "../../../lib/refused";
import { useLeaveGuard } from "../../../lib/useHash";
import { useListen } from "../../../lib/useListen";
import { seconds, SONGS_HASH, songHash, type Song } from "../../drum-notes/lib/songs";
import { useCover } from "../hooks/useCover";
import { useCoverRender } from "../hooks/useCoverRender";
import {
  adjustedText,
  BACKING_WARNING,
  coverBackgroundPath,
  coverBackgroundUrl,
  coverListenPath,
  downloadName,
  fieldsOf,
  hitsIn,
  INSTRUMENT_NAME,
  isCoverRendering,
  isSilent,
  isStale,
  LINE_MAX,
  MAX_S,
  MELODY_ONLY,
  MIN_S,
  NO_ANALYSIS,
  NO_AUDIO,
  NO_HITS,
  NO_NOTES,
  NOT_IMPORTED,
  NOT_PICKED,
  notesLine,
  RANGE_RULE,
  silentText,
  stretchFault,
  TITLE_HINT,
  TITLE_MAX,
  transposeWarning,
  soundLabel,
  soundOf,
  VOLUME_MAX,
  VOLUME_MIN,
  type Cover,
  type CoverFields,
  type CoverRenderResult,
  type Instrument,
  type Sound,
} from "../lib/cover";

/**
 * หน้า reel (`#/songs/{id}/cover`): the instrument, the stretch, the text, the sound, ฟัง and render
 * reel, and the renders made (spec › Design, D6, D7, D11, D12, D18, D19, D24; ui-prompt.md screen 2,
 * D14; kalimba-cover spec › Design, D9, D10, D14).
 */
export function CoverPage({ id }: { id: string }) {
  const cover = useCover(id);
  const { state } = cover;
  return (
    <PageLayout tab="songs" wide>
      <div className="flex items-center gap-2">
        <a href={state.kind === "not_found" ? SONGS_HASH : songHash(id)} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          {state.kind === "ready" || state.kind === "no_analysis" ? state.song.title : "รายการเพลง"}
        </a>
        <h2 className="min-w-0 flex-1 truncate text-xl leading-[1.5] font-semibold text-foreground">Reel cover</h2>
      </div>
      {state.kind === "loading" && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "offline" && <OfflinePanel />}
      {state.kind === "not_found" && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card px-4 py-12">
          <p className="text-base leading-[1.5] font-medium text-foreground">ไม่พบเพลงนี้</p>
          <a href={SONGS_HASH} className={`h-11 px-4 sm:h-9 ${GHOST_BUTTON}`}>
            กลับไปรายการเพลง
          </a>
        </div>
      )}
      {state.kind === "no_analysis" && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card px-4 py-12">
          <p className="text-base leading-[1.5] font-medium text-foreground">{NO_ANALYSIS}</p>
          <a href={songHash(id)} className={`h-11 px-4 sm:h-9 ${GHOST_BUTTON}`}>
            กลับไปหน้าเพลง
          </a>
        </div>
      )}
      {state.kind === "ready" && (
        // Keyed by the pick, so a new analysis starts the form over from the cover it pulled in.
        <CoverForm key={state.song.analysis?.picked_at} song={state.song} saved={state.cover} renders={state.renders} failure={state.failure} cover={cover} />
      )}
    </PageLayout>
  );
}

type FormProps = {
  song: Song;
  saved: Cover;
  renders: CoverRenderResult[];
  failure: string | null;
  cover: ReturnType<typeof useCover>;
};

/** The form as typed: the stretch as text, so a field being typed can be empty. */
type Draft = Omit<CoverFields, "start_s" | "end_s"> & { start: string; end: string };

const draftOf = (cover: Cover): Draft => {
  const { start_s, end_s, ...rest } = fieldsOf(cover);
  return { ...rest, start: String(start_s), end: String(end_s) };
};
/** A box left empty is no number, not 0. */
const numberOf = (text: string) => (text.trim() === "" ? NaN : Number(text));
const fieldsFrom = (draft: Draft): CoverFields => {
  const { start, end, ...rest } = draft;
  return { ...rest, start_s: numberOf(start), end_s: numberOf(end) };
};
const sameFields = (a: CoverFields, b: CoverFields) =>
  a.start_s === b.start_s &&
  a.end_s === b.end_s &&
  a.title === b.title &&
  a.subtitle === b.subtitle &&
  a.caption === b.caption &&
  a.background === b.background &&
  a.drums.on === b.drums.on &&
  a.drums.volume === b.drums.volume &&
  a.backing.on === b.backing.on &&
  a.backing.volume === b.backing.volume &&
  a.instrument === b.instrument &&
  a.kalimba.on === b.kalimba.on &&
  a.kalimba.volume === b.kalimba.volume;

function CoverForm({ song, saved, renders, failure, cover }: FormProps) {
  const id = useId();
  const [draft, setDraft] = useState<Draft>(() => draftOf(saved));
  const [refused, setRefused] = useState<Refused | null>(null);
  const [chosen, setChosen] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<CoverRenderResult | null>(null);
  const [saving, setSaving] = useState(false);
  const analysis = song.analysis!; // a ready page's song is picked
  const fields = fieldsFrom(draft);
  // Edited, or a stretch pulled into a new pick's range, which isn't what is stored (D18).
  const dirty = saved.adjusted || !sameFields(fields, fieldsOf(saved));
  // A cover never saved plays its defaults; ฟัง and render save it first all the same.
  const unsaved = dirty || !saved.saved;
  const fault = stretchFault(fields.start_s, fields.end_s, analysis);
  const hits = fault ? saved.hits : hitsIn(song, fields.start_s, fields.end_s);
  const kalimba = fields.instrument === "kalimba";
  const name = INSTRUMENT_NAME[fields.instrument];
  // The backend arranges the notes (D9), so its counts are the saved stretch's: shown while that is the stretch typed (D16).
  const savedStretch = fields.start_s === saved.start_s && fields.end_s === saved.end_s;
  const noNotes = !saved.notes_picked ? (song.source.kind === "midi" ? NOT_IMPORTED : NOT_PICKED) : savedStretch && saved.notes === 0 ? NO_NOTES : null;
  const render = useCoverRender((job) => {
    if (job.song_id !== song.id) return;
    void cover.reloadRenders();
    if (job.state === "done") setChosen(job.result);
  });
  const rendering = render.job !== null && isCoverRendering(render.job) ? render.job : null;
  const ownRendering = rendering?.song_id === song.id ? rendering : null;
  const failed = render.job?.song_id === song.id && (render.job.state === "failed" || render.job.state === "cancelled") ? render.job : null;

  useLeaveGuard(useCallback(() => dirty, [dirty]));

  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => {
    setDraft((now) => ({ ...now, [key]: value }));
    // A field the backend refused is being fixed: its line goes (`backing` covers `backing.on` and `.volume`;
    // either sound, or the other instrument, covers `drums.on` and `kalimba.on`, the silent reel's).
    const field = key === "start" ? "start_s" : key === "end" ? "end_s" : key;
    const silentField = (refusedField: string) => refusedField === "drums.on" || refusedField === "kalimba.on";
    const fixes = (refusedField: string) => refusedField.startsWith(`${field}.`) || (silentField(refusedField) && (key === "backing" || key === "instrument"));
    setRefused((now) => (now?.field === field || (now?.field && fixes(now.field)) ? null : now));
  };
  /** กลองล้วน puts a volume the backend would refuse back to the saved one: hidden, it can't be fixed. */
  const chooseBacking = (on: boolean) => {
    const volume = draft.backing.volume;
    set("backing", { on, volume: on || (volume >= VOLUME_MIN && volume <= VOLUME_MAX) ? volume : saved.backing.volume });
  };

  /** Saves when anything changed; false when the save was refused (its line shows at its field or under the bar). */
  const saveFirst = async (): Promise<boolean> => {
    if (fault) {
      setRefused(refusedLine(RANGE_RULE));
      return false;
    }
    if (!unsaved) return true;
    setSaving(true);
    const reply = await cover.save(fields);
    setSaving(false);
    if (reply.kind === "refused") {
      setRefused(reply);
      return false;
    }
    setRefused(null);
    // What was typed while the save went stays; what was sent takes the backend's form of it.
    setDraft((now) => (sameFields(fieldsFrom(now), fields) ? draftOf(reply.cover) : now));
    return true;
  };

  const listen = useListen(async () => ((await saveFirst()) ? postForBlob(coverListenPath(song.id), {}) : null));
  const mixing = listen.state.kind === "mixing";
  const silent = isSilent(fields);
  const canPlay = !fault && !silent && (kalimba ? noNotes === null : hits > 0);

  const fieldError = (name: string) => (refused?.field === name ? refused.text : undefined);
  // The found bars the stretch takes in; the saved stretch's while a box is wrong.
  const [from, to] = fault ? [saved.start_s, saved.end_s] : [fields.start_s, fields.end_s];
  const shownBars = song.bars.filter((bar) => bar.end_s > from && bar.start_s < to);
  const playing = renders.find((r) => r.name === chosen) ?? renders[0];

  return (
    <>
      {saved.adjusted && <Alert tone="info">{adjustedText(saved)}</Alert>}
      <section aria-label="เครื่องดนตรี" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <h3 className="text-base leading-[1.5] font-semibold text-foreground">เครื่องดนตรี</h3>
        <SegmentedChoice<Instrument>
          label="เครื่องดนตรี"
          options={[
            { value: "drums", label: INSTRUMENT_NAME.drums },
            { value: "kalimba", label: INSTRUMENT_NAME.kalimba },
          ]}
          value={draft.instrument}
          onChoose={(instrument) => set("instrument", instrument)}
        />
        {kalimba && noNotes === null && savedStretch && <p className="text-[13px] leading-[1.5] text-mid">{notesLine(saved)}</p>}
        {kalimba && noNotes !== null && (
          <Alert tone="warning">
            {noNotes}
            {noNotes !== NO_NOTES && (
              <>
                {" "}
                <a href={noNotes === NOT_IMPORTED ? SONGS_HASH : songHash(song.id)} className="text-brand underline">
                  {noNotes === NOT_IMPORTED ? "ไปรายการเพลง" : "กลับไปหน้าเพลง"}
                </a>
              </>
            )}
          </Alert>
        )}
      </section>
      {analysis.mode === "melody" && !kalimba && <Alert tone="info">{MELODY_ONLY}</Alert>}
      <section aria-label="ช่วงของ reel" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <h3 className="text-base leading-[1.5] font-semibold text-foreground">ช่วงของ reel</h3>
        <p className="text-[13px] leading-[1.5] text-mid">
          ภายในช่วงแกะ {seconds(analysis.start_s)}–{seconds(analysis.end_s)} ·{" "}
          <a href={songHash(song.id)} className="text-brand underline">
            อยากได้ท่อนอื่น? แกะช่วงใหม่ที่หน้าเพลง
          </a>
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Labeled label="เริ่ม (วินาที)" htmlFor={`${id}-start`} error={fault === "start_s" ? RANGE_RULE : fieldError("start_s")}>
            <input id={`${id}-start`} type="number" step={0.1} value={draft.start} onChange={(e) => set("start", e.target.value)} className={inputClass(fault === "start_s")} />
          </Labeled>
          <Labeled label="จบ (วินาที)" htmlFor={`${id}-end`} error={fault === "end_s" ? RANGE_RULE : fieldError("end_s")}>
            <input id={`${id}-end`} type="number" step={0.1} value={draft.end} onChange={(e) => set("end", e.target.value)} className={inputClass(fault === "end_s")} />
          </Labeled>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-[13px] leading-[1.5] text-mid">
            {Number.isNaN(fields.end_s - fields.start_s) ? "" : `ยาว ${seconds(fields.end_s - fields.start_s)} (${MIN_S}–${MAX_S}) · ${hits} การตี`}
          </p>
          <button type="button" onClick={() => set("start", String(saved.suggested_start_s))} className={`h-11 px-3 sm:h-9 ${OUTLINE_BUTTON}`}>
            เริ่มที่การตีแรก
          </button>
        </div>
        <ol aria-label="ห้องที่พบ" className="flex flex-wrap gap-2">
          {shownBars.map((bar) => (
            <li key={bar.n} className="flex flex-col rounded-lg border border-border bg-card px-3 py-2 leading-[1.5]">
              <span className="font-button text-sm font-medium">ห้อง {bar.n}</span>
              <span className="font-mono text-xs">{seconds(bar.start_s)}</span>
              <span className="text-xs">{bar.hits} การตี</span>
            </li>
          ))}
        </ol>
        {hits === 0 && !fault && !kalimba && <Alert tone="warning">{NO_HITS}</Alert>}
      </section>

      <section aria-label="ข้อความบนจอ" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <h3 className="text-base leading-[1.5] font-semibold text-foreground">ข้อความบนจอ</h3>
        <TextField id={`${id}-title`} label="หัวเรื่อง" value={draft.title} max={TITLE_MAX} hint={TITLE_HINT} error={fieldError("title")} onChange={(v) => set("title", v)} />
        <TextField id={`${id}-subtitle`} label="บรรทัดรอง" value={draft.subtitle} max={LINE_MAX} error={fieldError("subtitle")} onChange={(v) => set("subtitle", v)} />
        <TextField id={`${id}-caption`} label="คำบรรยายล่าง" value={draft.caption} max={LINE_MAX} error={fieldError("caption")} onChange={(v) => set("caption", v)} />
      </section>

      <div className="rounded-2xl border border-border bg-card p-4 sm:p-6">
        <BackgroundPicker
          path={coverBackgroundPath(song.id)}
          background={saved.background}
          imageUrl={coverBackgroundUrl(song.id, saved.updated_at)}
          apply={(body) => {
            const next = body as Cover;
            cover.applyCover(next);
            // Saved at once: the form takes the new background, whatever else is being typed.
            setDraft((now) => ({ ...now, background: next.background }));
          }}
        />
      </div>

      <section aria-label="เสียง" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <h3 className="text-base leading-[1.5] font-semibold text-foreground">เสียง</h3>
        <SoundRow key={fields.instrument} id={`${id}-sound`} name={name} sound={soundOf(draft)} error={fieldError(`${draft.instrument}.volume`)} onChange={(sound) => set(draft.instrument, sound)} />
        <SegmentedChoice<boolean>
          label="เสียงของ reel"
          options={[
            { value: false, label: `${name}ล้วน` },
            { value: true, label: `${name} + เพลงต้นฉบับ`, disabled: !saved.has_audio },
          ]}
          value={draft.backing.on}
          onChoose={chooseBacking}
        />
        {!saved.has_audio && <p className="text-xs leading-4 text-muted-foreground">{NO_AUDIO}</p>}
        {draft.backing.on && (
          <>
            <Labeled label="ความดังเพลง" htmlFor={`${id}-volume`} error={fieldError("backing.volume")} hint={`${VOLUME_MIN}–${VOLUME_MAX}`}>
              <input
                id={`${id}-volume`}
                type="number"
                min={VOLUME_MIN}
                max={VOLUME_MAX}
                value={draft.backing.volume}
                onChange={(e) => set("backing", { ...draft.backing, volume: Number(e.target.value) })}
                className={inputClass(fieldError("backing.volume") !== undefined)}
              />
            </Labeled>
            <Alert tone="warning">{BACKING_WARNING}</Alert>
            {kalimba && savedStretch && saved.transpose !== 0 && <Alert tone="warning">{transposeWarning(saved.transpose)}</Alert>}
          </>
        )}
        {fieldError("backing.on") && <p className="font-button text-xs leading-4 text-destructive">{fieldError("backing.on")}</p>}
        {(silent || fieldError(`${draft.instrument}.on`)) && <p className="font-button text-xs leading-4 text-destructive">{silent ? silentText(draft.instrument) : fieldError(`${draft.instrument}.on`)}</p>}
      </section>

      <section aria-label="ทำ reel" className="sticky bottom-0 flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <button type="button" disabled={!unsaved || saving} onClick={() => void saveFirst()} className={`h-11 px-5 sm:h-10 ${SECONDARY_BUTTON}`}>
            บันทึก
            {dirty && <span className="text-xs text-warning">· ยังไม่บันทึก</span>}
          </button>
          <button type="button" disabled={!canPlay || mixing || saving} onClick={() => void listen.listen()} className={`h-11 px-5 sm:h-10 ${SECONDARY_BUTTON}`}>
            {mixing ? "กำลังผสมเสียง…" : "ฟัง"}
          </button>
          {ownRendering ? (
            <div role="group" aria-label="งาน render" className="flex min-w-0 flex-1 items-center gap-3">
              <ProgressBar percent={ownRendering.percent} label="กำลัง render" />
              <span className="text-[13px] leading-[1.5] text-mid">{ownRendering.percent}%</span>
              <button type="button" onClick={() => void render.cancel()} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
                <img src={xIcon} alt="" width={16} height={16} />
                ยกเลิก
              </button>
            </div>
          ) : (
            <button
              type="button"
              disabled={!canPlay || rendering !== null || saving}
              onClick={async () => {
                if (await saveFirst()) await render.start(song.id);
              }}
              className={`h-11 px-6 sm:h-10 ${PRIMARY_BUTTON}`}
            >
              {failed ? "ลองอีกครั้ง" : "render reel"}
            </button>
          )}
        </div>
        {rendering && !ownRendering && <p className="text-[13px] leading-[1.5] text-mid">กำลัง render {rendering.title} อยู่ รอให้เสร็จก่อน</p>}
        {listen.state.kind === "refused" && <RefusedAlert refused={listen.state} />}
        {refused &&
          !["start_s", "end_s", "title", "subtitle", "caption", "backing.on", `${draft.instrument}.on`, ...(soundOf(draft).on ? [`${draft.instrument}.volume`] : []), ...(draft.backing.on ? ["backing.volume"] : [])].includes(refused.field ?? "") && <RefusedAlert refused={refused} />}
        {render.refused && <RefusedAlert refused={render.refused} />}
        {failed && <Alert tone={failed.state === "failed" ? "error" : "info"}>{failed.state === "failed" ? failed.message : "ยกเลิก render แล้ว"}</Alert>}
      </section>

      <section aria-label="ผล render" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
        <h3 className="text-base leading-[1.5] font-semibold text-foreground">ผล render</h3>
        {failure && <Alert tone="error">{failure}</Alert>}
        {renders.length === 0 || !playing ? (
          <p className="text-sm leading-[1.5] text-mid">ยังไม่เคย render reel นี้</p>
        ) : (
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
            <video key={playing.name} src={cover.fileOf(playing.name, ".mp4")} controls aria-label={`ผล render ${playing.name}`} className="aspect-[9/16] w-full max-w-[320px] self-center rounded-xl bg-black lg:self-start" />
            <ul aria-label="ผล render ทั้งหมด" className="flex min-w-0 flex-1 flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border">
              {renders.map((result) => (
                <li key={result.name} aria-current={result.name === playing.name} className="flex flex-wrap items-center gap-1 px-4 py-2.5 aria-[current=true]:bg-muted">
                  <button type="button" onClick={() => setChosen(result.name)} className="flex min-w-0 flex-1 flex-col items-start gap-0.5 text-left leading-[1.5]">
                    <span className="text-sm font-medium text-foreground">{editedAt(result.created_at)}</span>
                    <span className="flex flex-wrap gap-1.5 text-[13px] text-mid">
                      {formatDuration(Math.round(result.length_s))} · {seconds(result.start_s)}–{seconds(result.end_s)}
                      {result.backing.on && <span className="rounded bg-muted px-1.5 text-xs">มีเพลงต้นฉบับ</span>}
                      <SoundBadge result={result} />
                      {isStale(result, song) && <span className="rounded bg-warning-surface px-1.5 text-xs text-warning">แกะใหม่แล้ว</span>}
                    </span>
                  </button>
                  <a href={cover.fileOf(result.name, ".mp4")} download={downloadName(song, result, ".mp4")} className={`h-9 px-3 ${OUTLINE_BUTTON}`}>
                    <img src={downloadIcon} alt="" width={16} height={16} />
                    โหลด mp4
                  </a>
                  <a href={cover.fileOf(result.name, ".srt")} download={downloadName(song, result, ".srt")} className={`h-9 px-3 ${GHOST_BUTTON}`}>
                    <img src={downloadIcon} alt="" width={16} height={16} />
                    โหลด .srt
                  </a>
                  <button type="button" aria-label={`ลบผล render ${result.name}`} onClick={() => setDeleting(result)} className={`size-10 ${GHOST_BUTTON} hover:bg-muted`}>
                    <img src={trashIcon} alt="" width={16} height={16} />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>
      {deleting && (
        <DeleteRenderDialog
          result={deleting}
          onCancel={() => setDeleting(null)}
          onDelete={() => {
            setDeleting(null);
            void cover.removeRender(deleting.name);
          }}
        />
      )}
    </>
  );
}

type SoundRowProps = { id: string; name: string; sound: Sound; error?: string; onChange: (sound: Sound) => void };

/** A render's instrument and sound, when its row marks them (`soundLabel`). */
function SoundBadge({ result }: { result: CoverRenderResult }) {
  const label = soundLabel(result);
  return label && <span className="rounded bg-muted px-1.5 text-xs">{label}</span>;
}

/** The chosen instrument's sound: ปิดเสียง{name}, and its volume while it plays (D24, kalimba-cover D9). */
function SoundRow({ id, name, sound, error, onChange }: SoundRowProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-3">
        <span className="flex-1 text-sm leading-[1.5] font-medium text-foreground">{name}</span>
        <span aria-hidden className="text-sm leading-[1.5] text-mid">
          ปิดเสียง{name}
        </span>
        {/* On = muted: the switch says ปิดเสียง{name}, the field says whether the instrument plays. */}
        <Switch label={`ปิดเสียง${name}`} on={!sound.on} onToggle={() => onChange({ ...sound, on: !sound.on })} />
      </div>
      {sound.on && (
        <Labeled label={`ความดัง${name}`} htmlFor={id} error={error}>
          <div className="flex items-center gap-3">
            <input id={id} type="range" min={VOLUME_MIN} max={VOLUME_MAX} value={sound.volume} onChange={(e) => onChange({ ...sound, volume: Number(e.target.value) })} className="h-11 w-full accent-brand-accent" />
            <span className="w-12 text-right font-mono text-sm text-mid">{sound.volume}%</span>
          </div>
        </Labeled>
      )}
    </div>
  );
}

type TextFieldProps = { id: string; label: string; value: string; max: number; hint?: string; error?: string; onChange: (value: string) => void };

/** A one-line text with its letter count, in code points as the backend counts (story-kb D12). */
function TextField({ id, label, value, max, hint, error, onChange }: TextFieldProps) {
  const count = [...value].length;
  return (
    <Labeled label={label} htmlFor={id} error={error ?? (count > max ? `${label}ยาวเกิน ${max} ตัวอักษร` : undefined)} hint={hint}>
      <input id={id} type="text" value={value} onChange={(e) => onChange(e.target.value)} className={inputClass(error !== undefined || count > max)} />
      <p className="text-right text-xs leading-4 text-muted-foreground">
        {count}/{max}
      </p>
    </Labeled>
  );
}

/** Focus starts on ยกเลิก. */
function DeleteRenderDialog({ result, onCancel, onDelete }: { result: CoverRenderResult; onCancel: () => void; onDelete: () => void }) {
  const titleId = useId();
  return (
    <ModalDialog titleId={titleId} onClose={onCancel} size="gap-4 sm:max-w-[480px]">
      <h3 id={titleId} className="text-lg leading-[1.5] font-semibold text-foreground">
        ลบผล render นี้?
      </h3>
      <p className="text-sm leading-[1.5] text-mid">{editedAt(result.created_at)} · ไฟล์ mp4 และ .srt จะหายไป</p>
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
