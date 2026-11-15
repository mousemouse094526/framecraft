import { useEffect } from "react";
import { getJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { reelRendersPath } from "../lib/songs";

/** How many reel covers of the song were rendered (drum-cover D11); null until read, or with no backend. */
export function useReelRenders(id: string): number | null {
  const [count, , setIfMounted] = useMountedState<number | null>(null);
  useEffect(() => {
    getJson<unknown[]>(reelRendersPath(id))
      .then((renders) => setIfMounted(renders.length))
      .catch(() => setIfMounted(null));
  }, [id, setIfMounted]);
  return count;
}
