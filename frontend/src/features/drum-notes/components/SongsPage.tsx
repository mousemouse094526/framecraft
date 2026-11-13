import { useCallback, useEffect, useState } from "react";
import { useHash } from "../../../lib/useHash";
import { ALREADY_IN, songHash, songsViewOf } from "../lib/songs";
import { SongList } from "./SongList";
import { SongPage } from "./SongPage";

/**
 * The แกะเพลง tab: `#/songs/{id}` opens a song, any other `#/songs…` hash the list (spec › Frontend, D2).
 * A link or file that is a song already sends the page to that song with a word about it (D3, D20).
 */
export function SongsPage() {
  const view = songsViewOf(useHash());
  const [arrival, setArrival] = useState<{ id: string; text: string } | null>(null);

  const openKnown = useCallback((id: string) => {
    setArrival({ id, text: ALREADY_IN });
    window.location.hash = songHash(id);
  }, []);

  // Said once: back on the list, the word is spent.
  useEffect(() => {
    if (view.kind === "list") setArrival(null);
  }, [view.kind]);

  // Keyed, so another song's hash starts a fresh page.
  if (view.kind === "song") return <SongPage key={view.id} id={view.id} notice={arrival?.id === view.id ? arrival.text : null} />;
  return <SongList onKnownSong={openKnown} />;
}
