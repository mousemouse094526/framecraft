# anyio

**Kind:** library

**Version:** 4.15.1 (comes with starlette 1.10.0)

**Docs:** https://anyio.readthedocs.io/en/stable/

## Best practices

- `await anyio.to_thread.run_sync(func, *args)` runs a blocking call (file writes, `subprocess.run`) in a worker thread and keeps the event loop free; pass arguments positionally, or wrap in `functools.partial` for keywords — [Working with threads](https://anyio.readthedocs.io/en/stable/threads.html)
- The default limiter allows 40 threads at once for the whole process, shared with Starlette's sync routes; one long call holds one — [Working with threads](https://anyio.readthedocs.io/en/stable/threads.html)
- `with anyio.fail_after(seconds):` raises the builtin `TimeoutError` when the block outlives its deadline; the code inside is cancelled at its next `await` — [Cancellation and timeouts](https://anyio.readthedocs.io/en/stable/cancellation.html)
- **Avoid:** expecting a thread to stop when the awaiting task is cancelled: without `abandon_on_cancel=True` the task waits for the thread to finish; with it, the thread runs on alone — [Working with threads](https://anyio.readthedocs.io/en/stable/threads.html)

## Pattern

```python
async def copy_body(chunks, out: BinaryIO, stall_s: float) -> int:
    received = 0
    stream = aiter(chunks)
    while True:
        with anyio.fail_after(stall_s):  # TimeoutError when no chunk comes
            chunk = await anext(stream, None)
        if chunk is None:
            return received
        await anyio.to_thread.run_sync(out.write, chunk)
        received += len(chunk)
```

## Traps

- `fail_after` around `anext()` of an async generator cancels the generator mid-`await`: it is closed and can't be iterated again — the caller must stop reading it
- A `fail_after` deadline is checked only at an `await`: a blocking call inside the block runs past it unnoticed (one more reason to hand it to a thread)

## Sources

- [Working with threads](https://anyio.readthedocs.io/en/stable/threads.html) — `to_thread.run_sync`, limiter, cancellation, checked against `anyio/to_thread.py` 4.15.1 in `.venv` (accessed 2026-11-07)
- [Cancellation and timeouts](https://anyio.readthedocs.io/en/stable/cancellation.html) — `fail_after`, `move_on_after`, checked against `anyio/_core/_tasks.py` 4.15.1 in `.venv` (accessed 2026-11-07)
