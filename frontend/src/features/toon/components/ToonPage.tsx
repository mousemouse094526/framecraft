import { useState } from "react";
import { useHash } from "../../../lib/useHash";
import { EpViewContext, type EpView } from "../hooks/useEpView";
import { pageOf, pickHash } from "../lib/series";
import { CastPage } from "./CastPage";
import { EpListPage } from "./EpListPage";
import { EpPage } from "./EpPage";
import { PickPage } from "./PickPage";
import { RenderPage } from "./RenderPage";
import { SeriesForm } from "./SeriesForm";
import { SeriesList } from "./SeriesList";

/** The การ์ตูนเล่า tab: the hash picks the page (D52). `key` gives each Series a fresh page. */
export function ToonPage() {
  const page = pageOf(useHash());
  if (page.kind === "new") return <SeriesForm key="new" seriesId={null} />;
  if (page.kind === "settings") return <SeriesForm key={page.seriesId} seriesId={page.seriesId} />;
  if (page.kind === "eps") return <EpListPage key={page.seriesId} seriesId={page.seriesId} />;
  if (page.kind === "ep") return <EpWorkspace key={page.epId} epId={page.epId} />;
  if (page.kind === "cast") return <CastPage key={page.seriesId} seriesId={page.seriesId} />;
  if (page.kind === "pick") return <PickPage key={pickHash(page.itemRef)} itemRef={page.itemRef} />;
  return <SeriesList />;
}

/**
 * One EP, one page (`#/toon/eps/{epId}`): the storyline (the plot until there are cards), the plot, or
 * the render, as the page's view (nav-ia D8). One view at a time, so one hook follows the Toon job (D14).
 */
function EpWorkspace({ epId }: { epId: string }) {
  const [view, setView] = useState<EpView>("ep");
  return (
    <EpViewContext value={setView}>
      {view === "render" ? <RenderPage epId={epId} /> : <EpPage epId={epId} plot={view === "plot"} />}
    </EpViewContext>
  );
}
