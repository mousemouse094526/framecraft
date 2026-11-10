import { useHash } from "../../../lib/useHash";
import { pageOf } from "../lib/series";
import { CastPage } from "./CastPage";
import { PickPage } from "./PickPage";
import { SeriesForm } from "./SeriesForm";
import { SeriesList } from "./SeriesList";

/** The การ์ตูนเล่า tab: the hash picks the page (D52). `key` gives each Series a fresh page. */
export function ToonPage() {
  const page = pageOf(useHash());
  if (page.kind === "new") return <SeriesForm key="new" sid={null} />;
  if (page.kind === "settings") return <SeriesForm key={page.sid} sid={page.sid} />;
  if (page.kind === "cast") return <CastPage key={page.sid} sid={page.sid} />;
  if (page.kind === "pick") return <PickPage key={`${page.sid}/${page.itemKind}/${page.id}`} sid={page.sid} kind={page.itemKind} id={page.id} />;
  return <SeriesList />;
}
