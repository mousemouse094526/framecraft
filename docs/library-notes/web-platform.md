# web-platform

**Kind:** runtime

**Version:** browser APIs as of 2026 (Chrome, Edge, Safari, Firefox current); jsdom 30.1.3 in tests

**Docs:** https://developer.mozilla.org/en-US/docs/Web/API

Covers the browser APIs the คลิป tab's file import calls directly: `XMLHttpRequest` with an upload body, file drag and drop, and `<input type="file">`; and the สอนกลอง tab's ฟังจังหวะ: a `Blob` played through an object URL.

## Best practices

- `fetch` reports no upload progress; `XMLHttpRequest.upload` fires `loadstart`, `progress` (with `loaded` and `total`), `abort`, `error`, `load`, `timeout`, `loadend` — [XMLHttpRequest.upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload), [progress event](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequestUpload/progress_event)
- Register upload listeners before `send()` (some browsers want them before `open()`), or upload events are not dispatched — [XMLHttpRequest.upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload)
- `xhr.timeout` defaults to `0`: no timeout — [timeout](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/timeout)
- `abort()` sets `readyState` and `status` to 0 and fires `readystatechange`, `abort`, `loadend` — not `error` — [abort()](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/abort)
- `error` fires when the request fails at the network level; there is no HTTP status to read then — [error event](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/error_event)
- A drop target must `preventDefault()` its `dragover`, or `drop` never fires there; `preventDefault()` on `window`'s `drop` too, or a file dropped elsewhere is opened by the browser and the page is gone — [File drag and drop](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/File_drag_and_drop)
- `accept` on a file input is a hint, not a check: the user can pick "All files"; validate the name yourself — [input type=file](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/file)
- Setting a file input's `value` to `""` empties its file list (the only value a script may set), so the same file can be picked again — [HTML › value mode filename](https://html.spec.whatwg.org/multipage/input.html#dom-input-value-filename)
- Each `URL.createObjectURL(blob)` makes a new URL that keeps the blob in memory until `URL.revokeObjectURL(url)` or the document unloads: revoke it once the sound is no longer played — [createObjectURL](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static), [revokeObjectURL](https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static)
- `HTMLMediaElement.play()` returns a Promise that rejects (`NotAllowedError`) when autoplay is blocked; catch it. `pause()` stops playback and keeps the position — [play()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play), [pause()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/pause)

## Pattern

```ts
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener("progress", (event) => onPercent(Math.floor((event.loaded / event.total) * 100)));
xhr.upload.addEventListener("load", onAllSent);
xhr.addEventListener("load", () => onAnswer(xhr.status, xhr.responseText));
xhr.addEventListener("error", onFailed);
xhr.open("POST", path);
xhr.setRequestHeader("Content-Type", "application/octet-stream");
xhr.send(file);
```

Follows [XMLHttpRequest.upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload).

## Traps

- Upload listeners make a cross-origin request preflighted; same origin through the Vite proxy is unaffected — [XMLHttpRequest.upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload)
- `dragenter`/`dragleave` fire for every child the pointer crosses; a "drag-over" look needs a counter or `relatedTarget`, not a single flag — [File drag and drop](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/File_drag_and_drop)
- jsdom has no `URL.createObjectURL`/`revokeObjectURL` and no media playback: a test assigns stand-ins to `URL` and spies on `HTMLMediaElement.prototype.play`/`pause` — [jsdom README › Unimplemented parts](https://github.com/jsdom/jsdom#unimplemented-parts-of-the-web-platform)

## Sources

- [XMLHttpRequest.upload](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/upload), [progress event](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequestUpload/progress_event), [abort()](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/abort), [error event](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/error_event), [timeout](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/timeout) (accessed 2026-11-07)
- [File drag and drop](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/File_drag_and_drop) (accessed 2026-11-07)
- [input type=file](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/file), [HTML › value mode filename](https://html.spec.whatwg.org/multipage/input.html#dom-input-value-filename) (accessed 2026-11-07)
- [createObjectURL](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static), [revokeObjectURL](https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static), [play()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play), [pause()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/pause), [jsdom README › Unimplemented parts](https://github.com/jsdom/jsdom#unimplemented-parts-of-the-web-platform) (accessed 2026-11-13)
