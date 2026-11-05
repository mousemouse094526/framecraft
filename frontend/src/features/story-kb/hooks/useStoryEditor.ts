import { useCallback, useEffect, useRef } from "react";
import { getReply, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import { useLeaveGuard } from "../../../lib/useHash";
import { useMountedState } from "../../../lib/useMountedState";
import { EMPTY_STORY, fieldErrors, fieldsOf, sameFields, storyPath, type FieldErrors, type Story, type StoryFields } from "../lib/story";
import { STORIES_HASH, STORIES_PATH, storyHash } from "../../../lib/stories";

/** The form on screen. Saving and "บันทึกแล้ว" are flags of it, not states of their own: the form stays put through them. */
export type Editing = {
  kind: "ready";
  /** `null` until the first save of `#/stories/new`. */
  id: string | null;
  /** The Story as the backend last answered it: the form is unsaved while it differs. */
  saved: StoryFields;
  clips: number;
  form: StoryFields;
  errors: FieldErrors;
  saving: boolean;
  /** "บันทึกแล้ว" shows from a save until the next edit. */
  justSaved: boolean;
  /** A save or delete that failed for no field: the API's message, or offline. */
  failure: string | null;
};

export type EditorState = { kind: "loading" } | { kind: "offline" } | { kind: "not_found" } | Editing;

/**
 * แก้ Story: loads `#/stories/{id}` (or an empty form for `#/stories/new`), checks the rules
 * before sending, saves every field in one `POST`/`PUT`, and deletes (D11, D16).
 */
export function useStoryEditor(id: string | null) {
  const [state, setState, setIfMounted] = useMountedState<EditorState>({ kind: "loading" });
  // Mirrors of the state, written the moment things change rather than on the next render,
  // because the leave guard and a second submit read them before React renders again (D16).
  /** The form as typed. */
  const form = useRef<StoryFields | null>(null);
  /** The Story as the backend last answered it. */
  const saved = useRef<StoryFields | null>(null);
  /** A `POST`/`PUT` is out: a second submit does nothing. */
  const saving = useRef(false);
  /** Deleted: the move to the list must not ask. */
  const leaving = useRef(false);
  /** The id the first save of `#/stories/new` got: the hash moving to it is this page's own move. */
  const created = useRef<string | null>(null);

  const ready = useCallback(
    (next: Omit<Editing, "kind" | "errors" | "saving" | "justSaved" | "failure"> & Partial<Editing>) => {
      form.current = next.form;
      saved.current = next.saved;
      setIfMounted({ kind: "ready", errors: {}, saving: false, justSaved: false, failure: null, ...next });
    },
    [setIfMounted],
  );

  useEffect(() => {
    // The Story this page just created keeps its form: the hash only caught up with it.
    if (id !== null && id === created.current) return;
    form.current = saved.current = null;
    if (id === null) {
      ready({ id: null, saved: EMPTY_STORY, clips: 0, form: EMPTY_STORY });
      return;
    }
    setIfMounted({ kind: "loading" });
    void (async () => {
      try {
        const reply = await getReply<Story>(storyPath(id));
        if (reply.status === 200 && reply.body) {
          const fields = fieldsOf(reply.body);
          ready({ id, saved: fields, clips: reply.body.clips, form: fields });
        } else setIfMounted(reply.status === 404 ? { kind: "not_found" } : { kind: "offline" });
      } catch {
        setIfMounted({ kind: "offline" });
      }
    })();
  }, [id, ready, setIfMounted]);

  useLeaveGuard(
    useCallback(
      (next) =>
        !leaving.current &&
        !(created.current !== null && next === storyHash(created.current)) &&
        form.current !== null &&
        saved.current !== null &&
        !sameFields(form.current, saved.current),
      [],
    ),
  );

  const patch = useCallback(
    (change: Partial<Editing>) => setIfMounted((now) => (now.kind === "ready" ? { ...now, ...change } : now)),
    [setIfMounted],
  );

  /** Changes the form; `fields` are the error keys the change answers. */
  const edit = useCallback(
    (change: (fields: StoryFields) => StoryFields, fields: string[]) => {
      setState((now) => {
        if (now.kind !== "ready") return now;
        const next = change(now.form);
        form.current = next;
        const errors = { ...now.errors };
        for (const key of fields) delete errors[key];
        return { ...now, form: next, errors, justSaved: false, failure: null };
      });
    },
    [setState],
  );

  const save = useCallback(async () => {
    if (state.kind !== "ready" || saving.current || form.current === null) return;
    const sent = form.current;
    const errors = fieldErrors(sent);
    if (Object.keys(errors).length > 0) {
      patch({ errors, justSaved: false });
      return;
    }
    saving.current = true;
    patch({ saving: true, failure: null });
    try {
      const reply =
        state.id === null
          ? await sendJson<Story>("POST", STORIES_PATH, sent)
          : await sendJson<Story>("PUT", storyPath(state.id), sent);
      const body = reply.body;
      if ((reply.status === 200 || reply.status === 201) && body) {
        const fields = fieldsOf(body);
        // Typing during the save stays in the form, still unsaved.
        const kept = form.current === sent ? fields : form.current;
        ready({ id: body.id, saved: fields, clips: body.clips, form: kept, justSaved: true });
        if (state.id === null) {
          created.current = body.id;
          window.location.hash = storyHash(body.id);
        }
        return;
      }
      const refusal = refusalOf(body);
      if (reply.status === 404) setIfMounted({ kind: "not_found" });
      else if (refusal?.code === "invalid_story" && refusal.field) patch({ errors: { [refusal.field]: refusal.message } });
      else patch({ failure: refusal?.message ?? OFFLINE_TEXT });
    } catch {
      patch({ failure: OFFLINE_TEXT });
    } finally {
      saving.current = false;
      patch({ saving: false });
    }
  }, [state, patch, ready, setIfMounted]);

  const remove = useCallback(async () => {
    if (state.kind !== "ready" || state.id === null) return;
    try {
      const reply = await sendJson("DELETE", storyPath(state.id));
      // Already gone is what was asked for.
      if (reply.status === 204 || reply.status === 404) {
        leaving.current = true;
        window.location.hash = STORIES_HASH;
        return;
      }
      patch({ failure: refusalOf(reply.body)?.message ?? OFFLINE_TEXT });
    } catch {
      patch({ failure: OFFLINE_TEXT });
    }
  }, [state, patch]);

  return { state, edit, save, remove };
}
