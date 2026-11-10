import { useHash } from "../../../lib/useHash";
import { pageOf, pickHash } from "../lib/series";
import { CastPage } from "./CastPage";
import { EpListPage } from "./EpListPage";
import { EpPage } from "./EpPage";
import { PickPage } from "./PickPage";
import { RenderPage } from "./RenderPage";
import { SeriesForm } from "./SeriesForm";
import { SeriesList } from "./SeriesList";
import { SoundsPage } from "./SoundsPage";

/** The การ์ตูนเล่า tab: the hash picks the page (D52). `key` gives each Series a fresh page. */
export function ToonPage() {
  const page = pageOf(useHash());
  if (page.kind === "new") return <SeriesForm key="new" seriesId={null} />;
  if (page.kind === "settings") return <SeriesForm key={page.seriesId} seriesId={page.seriesId} />;
  if (page.kind === "eps") return <EpListPage key={page.seriesId} seriesId={page.seriesId} />;
  if (page.kind === "ep") return <EpPage key={page.epId} epId={page.epId} plot={page.plot} />;
  if (page.kind === "render") return <RenderPage key={page.epId} epId={page.epId} />;
  if (page.kind === "sounds") return <SoundsPage />;
  if (page.kind === "cast") return <CastPage key={page.seriesId} seriesId={page.seriesId} />;
  if (page.kind === "pick") return <PickPage key={pickHash(page.itemRef)} itemRef={page.itemRef} />;
  return <SeriesList />;
}
