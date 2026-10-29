"""The spoil API's refusals and job failures, shared by `downloads`, `transcribe` and `clips`."""

from collections.abc import Callable, Mapping

from backend.checks import Check


class SpoilError(Exception):
    """A refusal the route turns into `{"code", "message"}` with `status`."""

    def __init__(self, status: int, code: str, message: str, **extra: str):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


class JobFailed(Exception):
    """Ends a job as `failed` with an error `code` the job's API defines."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def require_rows(rows: Mapping[str, Check | Callable[[], object]]) -> None:
    """The gate of a job: raises `SpoilError` 503 `not_ready` naming every Status
    check row in `rows` (label → its check) that isn't `ok` (spoil D9, D27).

    A check that raises counts as not `ok`, the same as in the Status check.
    """
    missing = []
    for label, check in rows.items():
        try:
            status, _ = check()
        except Exception:
            status = "missing"
        if status != "ok":
            missing.append(label)
    if missing:
        raise SpoilError(503, "not_ready", f"ยังติดตั้งไม่ครบ: {', '.join(missing)}")
