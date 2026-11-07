# Routes

**Owns:** HTTP shape — path, method, request parsing, response model.

**Must not:** hold logic beyond calling one module function; touch the
filesystem or libraries directly.

## Shape

```python
router = APIRouter(prefix="/setup")

@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    return run_checks()
```

## Rules

- One router file per feature in `backend/routes/`, mounted in `app.py` under `/api`.
- Response models are Pydantic models; field names in snake_case.
- Request bodies are Pydantic models too. The one exception: a body whose bad
  values the spec answers with its own code (`400` `invalid_voice`) or whose shape
  depends on a field (`kind`) is taken as `dict[str, Any]` or `Any` fields and
  checked by the module, so FastAPI's `422` never stands in for the spec's code
  (`routes/spoil_maker.py` voice routes).
- Errors a user should see go inside the response body, not as 5xx, when the
  spec says so (setup-status: always 200).
- A refusal with its own status (`400`, `404`, `409`, `503`) is raised by the
  module as `backend.errors.ApiError`; one handler registered in `app.py`
  (`errors.error_response`) turns it into `{"code", "message", ...}`. Routes
  never build error responses themselves.
- A rule for every route (`POST` and `PATCH` must be JSON, `415`; a raw-file route
  opts out below, ADR 0028) is an app-wide dependency in `app.py` (`FastAPI(dependencies=[Depends(...)])`) that raises
  the API's refusal (`ApiError`).
- A route that serves a file built in memory calls one module function that
  returns its text (`transcribe.transcript_srt`), then wraps it in a `Response`.
- A file download built in memory is a `Response` with `media_type` and
  `Content-Disposition: attachment; filename="..."`.
- A route that takes a raw file body is `async def`, takes `request: Request` and no
  body parameter, lists `Depends(body_types.require_octet_stream)` in its decorator,
  and hands `request.stream()` to one module function, which writes the chunks and
  runs ffmpeg in threads (`anyio.to_thread.run_sync`); its query values are `str | None`
  so the module answers a bad one with its own code (`routes/spoil.py` `import_file`).
- A client that goes away mid-body raises `ClientDisconnect`; the module cleans up and
  lets it go, and `app.py`'s handler answers nobody quietly instead of a 500.
- Status codes other than 200 on success go in the decorator
  (`status_code=202`).

## Good examples

- [backend/routes/setup_status.py](../../../../backend/routes/setup_status.py) — one router, one call to `run_checks`, always 200.
- [backend/routes/spoil.py](../../../../backend/routes/spoil.py) — each route one call on `downloads.downloads` or `transcribe.transcriptions`.
- [backend/routes/spoil_maker.py](../../../../backend/routes/spoil_maker.py) — a file route (`FileResponse`) whose path the module checks before it reaches the disk.
