// A Story's shapes, rules and hashes (story-kb spec › Data, › Frontend). No React here.

export const STORIES_PATH = "/api/stories";
export const STORIES_HASH = "#/stories";
export const NEW_STORY_HASH = "#/stories/new";

export const TITLE_MAX = 100;
export const ARTICLE_MAX = 5000;
export const CHARACTERS_MAX = 30;
export const NAME_MAX = 40;
export const DESCRIPTION_MAX = 200;

export type Character = { name: string; description: string };

/** What the form edits and `POST`/`PUT` send. */
export type StoryFields = { title: string; article: string; characters: Character[] };

/** `GET /api/stories/{id}`: the Story with how many clips remember it. */
export type Story = StoryFields & { id: string; clips: number; created_at: string; updated_at: string };

/** One row of `GET /api/stories`. */
export type StoryRow = {
  id: string;
  title: string;
  characters: number;
  clips: number;
  tokens: number | null;
  updated_at: string;
};

/** The Story a hash opens: `null` for `#/stories/new`, `undefined` for the list. */
export function storyIdOf(hash: string): string | null | undefined {
  if (hash === NEW_STORY_HASH) return null;
  return hash.startsWith(`${STORIES_HASH}/`) ? hash.slice(STORIES_HASH.length + 1) : undefined;
}

export const storyHash = (id: string) => `${STORIES_HASH}/${id}`;
export const storyPath = (id: string) => `${STORIES_PATH}/${id}`;

/** Letters as the backend counts them: code points, so Thai vowels and tone marks count (D12). */
export const lengthOf = (text: string) => [...text].length;

// The backend's cleaning (D16, D17): one-line fields make every run of spaces one space.
const oneLine = (text: string) => text.split(/\s+/).filter(Boolean).join(" ");

/** The counter's `{n}`: the article as the backend keeps it, trimmed. */
export const articleLength = (article: string) => lengthOf(article.trim());

/** The form's field keys, as `invalid_story` names them (`title`, `characters.0.name`, …). */
export type FieldErrors = Record<string, string>;

/** `characters.{index}.name` or `.description`: a character field's error key. */
export const characterKey = (index: number, field: keyof Character) => `characters.${index}.${field}`;

/** Every error key about characters: the list's own and each character field's. */
export const characterErrorKeys = (errors: FieldErrors) => Object.keys(errors).filter((key) => key.startsWith("characters"));

/**
 * The rules of spec › Data, checked before sending: every failing field with the
 * message the backend would give (spec › Frontend, error table).
 */
export function fieldErrors(fields: StoryFields): FieldErrors {
  const errors: FieldErrors = {};
  const title = oneLine(fields.title);
  if (title === "") errors.title = "ใส่ชื่อเรื่อง";
  else if (lengthOf(title) > TITLE_MAX) errors.title = `ชื่อเรื่องยาวเกิน ${TITLE_MAX} ตัวอักษร`;
  if (articleLength(fields.article) > ARTICLE_MAX) errors.article = `บทความยาวเกิน ${grouped(ARTICLE_MAX)} ตัวอักษร`;
  if (fields.characters.length > CHARACTERS_MAX) errors.characters = `ตัวละครได้ไม่เกิน ${CHARACTERS_MAX} ตัว`;
  const seen = new Set<string>();
  fields.characters.forEach((character, index) => {
    const name = oneLine(character.name);
    const key = characterKey(index, "name");
    if (name === "") errors[key] = "ใส่ชื่อตัวละคร";
    else if (lengthOf(name) > NAME_MAX) errors[key] = `ชื่อตัวละครยาวเกิน ${NAME_MAX} ตัวอักษร`;
    // The later of two names that differ only in case or spaces is the duplicate (D17); the
    // backend's `casefold` has the last word on the few letters `toLowerCase` treats differently.
    else if (seen.has(name.toLowerCase())) errors[key] = "ชื่อตัวละครซ้ำ";
    seen.add(name.toLowerCase());
    if (lengthOf(oneLine(character.description)) > DESCRIPTION_MAX) {
      errors[characterKey(index, "description")] = `คำอธิบายยาวเกิน ${DESCRIPTION_MAX} ตัวอักษร`;
    }
  });
  return errors;
}

export const sameFields = (a: StoryFields, b: StoryFields) => JSON.stringify(a) === JSON.stringify(b);

export const fieldsOf = (story: StoryFields): StoryFields => ({
  title: story.title,
  article: story.article,
  characters: story.characters.map(({ name, description }) => ({ name, description })),
});

export const EMPTY_STORY: StoryFields = { title: "", article: "", characters: [] };

const THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];

/**
 * "5 พ.ย. 14:20" from `2026-11-05T14:20:00+07:00`: the wall time the backend wrote, which is
 * the machine's own clock, read straight from the text so no time zone can shift it.
 */
export function editedAt(iso: string): string {
  const [, month, day, hour, minute] = /^\d{4}-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso) ?? [];
  if (!month) return iso;
  return `${Number(day)} ${THAI_MONTHS[Number(month) - 1]} ${hour}:${minute}`;
}

/** "1,240": the counter's digits. */
export const grouped = (n: number) => n.toLocaleString("en-US");
