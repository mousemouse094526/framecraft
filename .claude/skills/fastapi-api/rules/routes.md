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
- Errors a user should see go inside the response body, not as 5xx, when the
  spec says so (setup-status: always 200).
- A refusal with its own status (`400`, `404`, `409`, `503`) is raised by the
  module as `backend.errors.ApiError`; one handler registered in `app.py`
  (`errors.error_response`) turns it into `{"code", "message", ...}`. Routes
  never build error responses themselves.
- A rule for every route (`POST` and `PATCH` must be JSON, `415`) is an app-wide
  dependency in `app.py` (`FastAPI(dependencies=[Depends(...)])`) that raises
  the API's refusal (`ApiError`).
- A route that serves a file built in memory calls one module function that
  returns its text (`transcribe.transcript_srt`), then wraps it in a `Response`.
- A file download built in memory is a `Response` with `media_type` and
  `Content-Disposition: attachment; filename="..."`.
- Status codes other than 200 on success go in the decorator
  (`status_code=202`).

## Good examples

- [backend/routes/setup_status.py](../../../../backend/routes/setup_status.py) — one router, one call to `run_checks`, always 200.
- [backend/routes/spoil.py](../../../../backend/routes/spoil.py) — each route one call on `downloads.downloads` or `transcribe.transcriptions`.
- [backend/routes/spoil_maker.py](../../../../backend/routes/spoil_maker.py) — a file route (`FileResponse`) whose path the module checks before it reaches the disk.
