"""The API's refusals and job failures: every feature answers in one flat shape,
`{"code", "message", ...extra}` (spoil D20, spoil-maker spec › API)."""

from collections.abc import Callable, Mapping

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.checks import Check


class ApiError(Exception):
    """A refusal the handler turns into `{"code", "message", ...extra}` with `status`."""

    def __init__(self, status: int, code: str, message: str, **extra: object):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


def error_response(request: Request, error: ApiError) -> JSONResponse:
    """Registered in app.py for every `ApiError`."""
    return JSONResponse(
        status_code=error.status,
        content={"code": error.code, "message": error.message, **error.extra},
    )


class JobFailed(Exception):
    """Ends a job as `failed` with an error `code` the job's API defines."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


Row = tuple[str, Check | Callable[[], object]]  # a Status check row's label and its check


def require_rows(rows: Mapping[str, Row]) -> None:
    """The gate of a job: raises `ApiError` 503 `not_ready` when a Status check row in
    `rows` (id → label and check) isn't `ok` (spoil D9, D27). The message names the
    rows by label, `rows` lists their ids (spoil-maker spec › Status check).

    A check that raises counts as not `ok`, the same as in the Status check.
    """
    missing: dict[str, str] = {}
    for row_id, (label, check) in rows.items():
        try:
            status, _ = check()
        except Exception:
            status = "missing"
        if status != "ok":
            missing[row_id] = label
    if missing:
        names = ", ".join(missing.values())
        raise ApiError(503, "not_ready", f"ยังติดตั้งไม่ครบ: {names}", rows=list(missing))
