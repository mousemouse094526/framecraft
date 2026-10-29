import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import { useSpoilDownload } from "../hooks/useSpoilDownload";
import notReadyIcon from "../assets/not-ready.svg";
import { DownloadProgress } from "./DownloadProgress";
import { LinkForm } from "./LinkForm";
import { NoticeAlert } from "./NoticeAlert";

export function SpoilPage() {
  const { state, start, cancel, reload } = useSpoilDownload();

  if (state.kind === "offline") {
    return (
      <PageLayout tab="spoil" action={<RefreshButton onClick={reload} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  return (
    <PageLayout tab="spoil">
      {state.kind === "loading" && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "notReady" && <NotReady missing={state.missing} />}
      {state.kind === "ready" && (
        <>
          <LinkForm busy={state.job !== null} onSubmit={start} />
          {state.job && <DownloadProgress job={state.job} onCancel={cancel} />}
          {state.notice && <NoticeAlert notice={state.notice} />}
        </>
      )}
    </PageLayout>
  );
}

/** In place of the link field while yt-dlp, Deno or ffmpeg is missing (D9, D10). */
function NotReady({ missing }: { missing: string[] }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-warning-border bg-warning-surface px-4 py-3.5">
      <img src={notReadyIcon} alt="" width={20} height={20} className="shrink-0" />
      <p className="flex-1 text-sm leading-[1.5] font-medium text-warning">ยังติดตั้งไม่ครบ: {missing.join(", ")}</p>
      <a
        href="#/setup"
        className="flex h-9 shrink-0 items-center rounded-lg px-4 font-button text-sm leading-5 font-medium text-brand hover:bg-warning-border/10"
      >
        ไปหน้า Setup status
      </a>
    </div>
  );
}
