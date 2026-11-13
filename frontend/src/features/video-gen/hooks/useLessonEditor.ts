import { useCallback, useEffect, useRef } from "react";
import { getReply, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import { useLeaveGuard } from "../../../lib/useHash";
import { useMountedState } from "../../../lib/useMountedState";
import { fieldErrors, fieldsOf, lessonPath, sameFields, type FieldErrors, type Lesson, type LessonFields } from "../lib/lesson";

/** The form on screen; saving and "บันทึกแล้ว" are flags of it, so the form stays put through them. */
export type Editing = {
  kind: "ready";
  id: string;
  /** The lesson as the backend last answered it: the form is unsaved while it differs. */
  saved: LessonFields;
  form: LessonFields;
  errors: FieldErrors;
  saving: boolean;
  /** "บันทึกแล้ว" shows from a save until the next edit. */
  justSaved: boolean;
  /** A save that failed for no field: the API's message, or offline. */
  failure: string | null;
};

export type EditorState = { kind: "loading" } | { kind: "offline" } | { kind: "not_found" } | Editing;

/**
 * หน้าแก้บทเรียนกลอง: loads `#/drums/{id}`, checks the text and number rules before sending, and
 * saves the whole lesson in one `PUT`; leaving unsaved asks first (story-kb D11, D16).
 */
export function useLessonEditor(id: string) {
  const [state, setState, setIfMounted] = useMountedState<EditorState>({ kind: "loading" });
  // Mirrors of the state, written the moment things change: the leave guard and a second
  // submit read them before React renders again (story-kb D16).
  const form = useRef<LessonFields | null>(null);
  const saved = useRef<LessonFields | null>(null);
  const saving = useRef(false);

  const ready = useCallback(
    (lesson: Lesson, kept: LessonFields | null, change: Partial<Editing> = {}) => {
      const fields = fieldsOf(lesson);
      form.current = kept ?? fields;
      saved.current = fields;
      setIfMounted({ kind: "ready", id, saved: fields, form: form.current, errors: {}, saving: false, justSaved: false, failure: null, ...change });
    },
    [id, setIfMounted],
  );

  useEffect(() => {
    form.current = saved.current = null;
    setIfMounted({ kind: "loading" });
    void (async () => {
      try {
        const reply = await getReply<Lesson>(lessonPath(id));
        if (reply.status === 200 && reply.body) ready(reply.body, null);
        else setIfMounted(reply.status === 404 ? { kind: "not_found" } : { kind: "offline" });
      } catch {
        setIfMounted({ kind: "offline" });
      }
    })();
  }, [id, ready, setIfMounted]);

  const unsaved = useCallback(() => form.current !== null && saved.current !== null && !sameFields(form.current, saved.current), []);
  useLeaveGuard(unsaved);

  const patch = useCallback(
    (change: Partial<Editing>) => setIfMounted((now) => (now.kind === "ready" ? { ...now, ...change } : now)),
    [setIfMounted],
  );

  /** Changes the form; `answered` says which error keys the change answers. */
  const edit = useCallback(
    (change: (fields: LessonFields) => LessonFields, answered: (key: string) => boolean) => {
      setState((now) => {
        if (now.kind !== "ready") return now;
        const next = change(now.form);
        form.current = next;
        const errors = Object.fromEntries(Object.entries(now.errors).filter(([key]) => !answered(key)));
        return { ...now, form: next, errors, justSaved: false, failure: null };
      });
    },
    [setState],
  );

  /** `PUT`s the form when it is unsaved; true once the backend has what is on screen. */
  const save = useCallback(async (): Promise<boolean> => {
    if (state.kind !== "ready" || saving.current || form.current === null) return false;
    if (!unsaved()) return true;
    const sent = form.current;
    const errors = fieldErrors(sent);
    if (Object.keys(errors).length > 0) {
      patch({ errors, justSaved: false });
      return false;
    }
    saving.current = true;
    patch({ saving: true, failure: null });
    try {
      const reply = await sendJson<Lesson>("PUT", lessonPath(id), sent);
      if (reply.status === 200 && reply.body) {
        // Typing during the save stays in the form, still unsaved.
        ready(reply.body, form.current === sent ? null : form.current, { justSaved: true });
        // Saved means nothing was typed meanwhile: `ready` made the reply both form and saved.
        return form.current === saved.current;
      }
      const refusal = refusalOf(reply.body);
      if (reply.status === 404) setIfMounted({ kind: "not_found" });
      else if (refusal?.code === "invalid_request" && refusal.field) patch({ errors: { [refusal.field]: refusal.message } });
      else patch({ failure: refusal?.message ?? OFFLINE_TEXT });
      return false;
    } catch {
      patch({ failure: OFFLINE_TEXT });
      return false;
    } finally {
      saving.current = false;
      patch({ saving: false });
    }
  }, [state.kind, id, unsaved, patch, ready, setIfMounted]);

  return { state, edit, save };
}
