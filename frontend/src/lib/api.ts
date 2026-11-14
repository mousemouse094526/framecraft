// Every backend call goes through here, so none can hang the UI forever: all but
// `sendFile`, whose upload the user cancels instead (spoil D50, D58).

/** The line a refused action shows when the backend gave no answer. */
export const OFFLINE_TEXT = "ติดต่อ backend ไม่ได้";

const TIMEOUT_MS = 30_000;

/** Throws when the network fails or no response comes in 30 s. */
async function fetchWithTimeout(path: string, init: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  // Racing the timer (not only aborting) also ends a fetch that ignores the signal.
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new Error(`${path}: no response in ${TIMEOUT_MS / 1000} s`));
    }, TIMEOUT_MS);
  });
  try {
    return await Promise.race([fetch(path, { ...init, signal: controller.signal }), timeout]);
  } finally {
    clearTimeout(timer);
  }
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetchWithTimeout(path);
  if (response.status !== 200) {
    throw new Error(`${path}: HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export type JsonReply<T> = { status: number; body: T | null };

/** A GET whose refusals are answers (`404` for a file not there yet); see `sendJson`. */
export function getReply<T>(path: string): Promise<JsonReply<T>> {
  return sendJson<T>("GET", path);
}

/**
 * For calls whose refusals are answers (`409 busy`), not failures: returns
 * every status with its JSON body, or `null` when there is none. Throws only
 * when the network fails or no response comes in 30 s.
 */
export async function sendJson<T>(method: string, path: string, body?: unknown): Promise<JsonReply<T>> {
  const response = await fetchWithTimeout(path, {
    method,
    ...(body === undefined ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
  });
  const text = await response.text();
  return { status: response.status, body: text ? (JSON.parse(text) as T) : null };
}

/** The status of a `HEAD`: whether a file is there without downloading it. Throws as `sendJson` does. */
export async function headStatus(path: string): Promise<number> {
  return (await fetchWithTimeout(path, { method: "HEAD" })).status;
}

/** How an upload ended: the server's answer, a failure with no answer, or `abort()`. */
export type FileReply<T> =
  | { kind: "answer"; status: number; body: T | null }
  | { kind: "failed" }
  | { kind: "aborted" };

export type FileUpload<T> = {
  reply: Promise<FileReply<T>>;
  abort: () => void;
};

/**
 * Sends `file` as the raw body (`application/octet-stream`, ADR-0028) with `XMLHttpRequest`,
 * which reports upload progress where `fetch` doesn't. The one call with no timeout: a file of
 * several GB takes as long as it takes, and the server stops one that stalls (spoil D50, D55, D58).
 * `onProgress` gets the percent sent; `onSent` runs once the whole body is out. `method` is the
 * route's: `PUT` where the file replaces one (a drum lesson's background).
 */
export function sendFile<T>(
  path: string,
  file: File,
  onProgress: (percent: number) => void,
  onSent: () => void,
  method: "POST" | "PUT" = "POST",
): FileUpload<T> {
  const xhr = new XMLHttpRequest();
  const reply = new Promise<FileReply<T>>((resolve) => {
    // Upload listeners go on before send(), or the browser never fires them (docs/library-notes/web-platform.md).
    xhr.upload.addEventListener("progress", (event) => {
      onProgress(event.total > 0 ? Math.floor((event.loaded / event.total) * 100) : 100);
    });
    xhr.upload.addEventListener("load", onSent);
    xhr.addEventListener("load", () => {
      let body: T | null = null;
      try {
        body = xhr.responseText ? (JSON.parse(xhr.responseText) as T) : null;
      } catch {
        // Not JSON (a proxy's error page): the status alone decides.
      }
      resolve({ kind: "answer", status: xhr.status, body });
    });
    xhr.addEventListener("error", () => resolve({ kind: "failed" }));
    xhr.addEventListener("abort", () => resolve({ kind: "aborted" }));
  });
  xhr.open(method, path);
  xhr.setRequestHeader("Content-Type", "application/octet-stream");
  // The default already, said out loud: no timeout (spec › Frontend, เอาไฟล์เข้า).
  xhr.timeout = 0;
  xhr.send(file);
  return { reply, abort: () => xhr.abort() };
}

/** A file answer (`audio/wav`) or, for a refusal, its JSON body. */
export type BlobReply = { status: number; blob: Blob | null; body: unknown };

/**
 * A `POST` of `body` as JSON whose answer is a file: `blob` when the response isn't JSON,
 * else `body` holds the refusal. Throws as `sendJson` does.
 */
export async function postForBlob(path: string, body: unknown): Promise<BlobReply> {
  const response = await fetchWithTimeout(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (response.headers.get("Content-Type")?.startsWith("application/json")) {
    return { status: response.status, blob: null, body: await response.json() };
  }
  return { status: response.status, blob: await response.blob(), body: null };
}
