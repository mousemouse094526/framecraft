import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import arrowLeftIcon from "../assets/arrow-left.svg";
import userIcon from "../assets/user.svg";
import { useVoices } from "../hooks/useVoices";
import { VoiceDesigner } from "./VoiceDesigner";
import { VoiceRow } from "./VoiceRow";

/** `#/spoil/voices`: design a voice, hear it, save it; rename and delete saved ones (spoil-maker D32, D43). */
export function SavedVoicePage() {
  const { state, design, save, rename, remove, reload } = useVoices();

  if (state.kind === "offline") {
    return (
      <PageLayout tab="spoil" wide action={<RefreshButton onClick={reload} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  return (
    <PageLayout tab="spoil" wide>
      <div className="flex items-center gap-2">
        <a
          href="#/spoil"
          aria-label="กลับ"
          className="flex size-11 shrink-0 items-center justify-center rounded-lg hover:bg-card sm:size-9"
        >
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
        </a>
        <h2 className="text-xl leading-7 font-semibold text-foreground">เสียงบรรยาย</h2>
      </div>
      {state.kind === "loading" ? (
        <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
      ) : (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
          <VoiceDesigner
            generating={state.job !== null}
            previewVersion={state.previewVersion}
            gpu={state.gpu}
            error={state.error}
            onDesign={(choices) => void design(choices)}
            onSave={save}
          />
          <section
            aria-label="เสียงที่บันทึกไว้"
            className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card lg:min-w-0 lg:flex-1"
          >
            <div className="flex items-center gap-2 px-4 py-3 leading-[1.5]">
              <h3 className="text-sm font-medium text-foreground">เสียงที่บันทึกไว้</h3>
              <span className="font-mono text-[13px] text-muted-foreground">{state.voices.length}</span>
            </div>
            <div className="h-px bg-border" />
            {state.voices.length === 0 ? (
              <div className="flex flex-col items-center gap-2 px-4 py-14">
                <img src={userIcon} alt="" width={24} height={24} />
                <p className="text-center text-sm leading-[21px] text-mid">ยังไม่มีเสียง กดสุ่มเพื่อออกแบบเสียงแรก</p>
              </div>
            ) : (
              <ul className="divide-y divide-border">
                {state.voices.map((voice) => (
                  <VoiceRow
                    key={voice.id}
                    voice={voice}
                    onRename={(name) => rename(voice.id, name)}
                    onDelete={() => remove(voice.id)}
                  />
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </PageLayout>
  );
}
