import { createContext, useContext } from "react";

/** What an EP's one page shows: the storyline (or the plot until there are cards), the plot, or its render (nav-ia D8). */
export type EpView = "ep" | "plot" | "render";

/**
 * Shows another view of the EP's page; what used to move the hash to `/plot` or `/render` moves the
 * view (nav-ia D8). Alone (no page, as in a part's own test) it does nothing.
 */
export const EpViewContext = createContext<(view: EpView) => void>(() => {});

export const useEpView = () => useContext(EpViewContext);
