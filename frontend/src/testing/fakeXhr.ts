import { act } from "react";
import { vi } from "vitest";

/**
 * The `XMLHttpRequest` that `sendFile` (lib/api.ts) uploads with: jsdom's would go to the
 * network (docs/library-notes/testing-library.md). Stub it with
 * `vi.stubGlobal("XMLHttpRequest", FakeXhr)`, empty `FakeXhr.sent` per test, and fire its
 * events from the test.
 */
export class FakeXhr {
  static sent: FakeXhr[] = [];
  method = "";
  url = "";
  headers: Record<string, string> = {};
  body: unknown = null;
  // Not the browser's 0, so the test sees that `sendFile` sets no timeout itself.
  timeout = -1;
  status = 0;
  responseText = "";
  readonly upload = new EventTarget();
  private readonly events = new EventTarget();
  readonly abort = vi.fn(() => {
    this.events.dispatchEvent(new Event("abort"));
  });
  addEventListener(type: string, listener: EventListener) {
    this.events.addEventListener(type, listener);
  }
  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }
  setRequestHeader(name: string, value: string) {
    this.headers[name] = value;
  }
  send(body: unknown) {
    this.body = body;
    FakeXhr.sent.push(this);
  }
  progress(loaded: number, total: number) {
    act(() => {
      this.upload.dispatchEvent(new ProgressEvent("progress", { loaded, total, lengthComputable: true }));
    });
  }
  allSent() {
    act(() => {
      this.upload.dispatchEvent(new Event("load"));
    });
  }
  async respond(status: number, body: unknown) {
    this.status = status;
    this.responseText = JSON.stringify(body);
    await act(async () => {
      this.events.dispatchEvent(new Event("load"));
    });
  }
  async fail() {
    await act(async () => {
      this.events.dispatchEvent(new Event("error"));
    });
  }
}
