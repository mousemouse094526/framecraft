// The Saved voices of the สปอย tab: the การ์ตูนเล่า tab reads them too, as a Series' narrator (toon D8).

export const VOICES_PATH = "/api/spoil-maker/voices";
export const VOICES_HASH = "#/spoil/voices"; // where Saved voices are made

/** What a voice picker needs of a Saved voice; `useVoices` (spoil-maker) reads the whole row. */
export type SavedVoice = { id: string; name: string };
