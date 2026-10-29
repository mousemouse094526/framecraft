// Every backend call goes through here, so none can hang the UI forever.
const TIMEOUT_MS = 30_000;

export async function getJson<T>(path: string): Promise<T> {
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
    const response = await Promise.race([fetch(path, { signal: controller.signal }), timeout]);
    if (response.status !== 200) {
      throw new Error(`${path}: HTTP ${response.status}`);
    }
    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}
