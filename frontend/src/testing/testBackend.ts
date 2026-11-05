import type { Mock } from "vitest";

/** The fake backend the tabs' tests answer `fetch` with: routes matched by method and path. */

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export type Route = { method?: string; path: string; reply: () => Response | Promise<Response> };

export const get = (path: string, body: unknown): Route => ({ path, reply: () => jsonResponse(body) });

export const send = (method: string, path: string, body: unknown, code: number): Route => ({
  method,
  path,
  reply: () => jsonResponse(body, code),
});

/** One answer per poll, however many hooks poll the path: the test moves `phases.at` on (the steps poll too, D68). */
export function phased(path: string, ...bodies: unknown[]) {
  const phases = { at: 0 };
  const route: Route = { path, reply: () => jsonResponse(bodies[Math.min(phases.at, bodies.length - 1)]) };
  return { route, phases };
}

/**
 * Answers `fetchMock` from `routes`: the first matching route answers; of several for one
 * path, each answers once in order and the last keeps answering. A `GET` of a path in
 * `defaults` that no route answers gets its default body.
 */
export function serve(fetchMock: Mock<typeof fetch>, routes: Route[], defaults: [string, unknown][] = []) {
  const has = (path: string) => routes.some((r) => r.path === path && (r.method ?? "GET") === "GET");
  for (const [path, body] of defaults) if (!has(path)) routes.push(get(path, body));
  fetchMock.mockImplementation(async (input, init) => {
    const method = init?.method ?? "GET";
    const matches = routes.filter((r) => r.path === String(input) && (r.method ?? "GET") === method);
    if (matches.length === 0) throw new Error(`unexpected ${method} ${String(input)}`);
    const route = matches[0];
    if (matches.length > 1) routes.splice(routes.indexOf(route), 1);
    return route.reply();
  });
}

/** The JSON bodies sent with `method` to `path`, in order; null for a request without one. */
export function sent(fetchMock: Mock<typeof fetch>, method: string, path: string): unknown[] {
  return fetchMock.mock.calls
    .filter(([input, init]) => String(input) === path && init?.method === method)
    .map(([, init]) => (init?.body ? JSON.parse(String(init.body)) : null));
}
