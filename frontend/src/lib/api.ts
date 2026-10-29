// Every backend call goes through here, so none can hang the UI forever.
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
