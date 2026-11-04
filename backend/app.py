"""The framecraft backend. Run with `npm run dev`; it binds 127.0.0.1 only."""

from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Protocol

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException

from backend import errors, files, paths
from backend.errors import ApiError
from backend.paths import ProjectPaths
from backend.routes import setup_status, spoil, spoil_maker
from backend.spoil import clips, downloads, transcribe
from backend.spoil_maker import describe, draft, episodes, render, shots, voices

# Binding 127.0.0.1 doesn't stop DNS rebinding from another site (ADR 0011).
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]


class Stoppable(Protocol):
    def stop_on_shutdown(self) -> None: ...


@dataclass(frozen=True)
class JobEntry:
    """One kind of job in `JOB_HOLDERS`."""

    # The module's holder as it is when the app stops: a test may have swapped it since import.
    current: Callable[[], Stoppable]
    # What this job leaves half-done that start-up removes. None: its half-written files are
    # `.tmp` ones, which the clips' clean (a Transcript) or `files.remove_unfinished` (a draft) remove.
    clean_on_start: Callable[[ProjectPaths], None] | None = None


def _clean_shots(project: ProjectPaths) -> None:
    """Shots of a clip that start-up removed go too, and EP cuts of a clip with no Shots
    (spoil-maker spec › Ops). Here, not in `shots`: `spoil.clips` imports `shots`, so
    `shots` can't list the clips."""
    listed = clips.list_clips(project)
    shots.clean_on_start(project, {clip.id for clip in listed})
    episodes.clean_on_start(project, {clip.id for clip in listed if clip.described})


# Every job, once. Start-up cleans in this order: the clips (a Download job's) before their Shots.
JOB_HOLDERS = (
    JobEntry(lambda: downloads.downloads, clips.clean_on_start),
    JobEntry(lambda: transcribe.transcriptions),
    JobEntry(lambda: describe.describes, _clean_shots),
    JobEntry(lambda: draft.draft_jobs),
    JobEntry(lambda: voices.voice_jobs, voices.clean_on_start),
    JobEntry(lambda: render.render_jobs, render.clean_on_start),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jobs don't survive a restart, so their leftovers go (spoil D15, D29).
    project = paths.project()
    for job in JOB_HOLDERS:
        if job.clean_on_start:
            job.clean_on_start(project)
    # Half-written `draft.json`, `settings.json`, voice files (spoil-maker spec › Ops).
    files.remove_unfinished(project.spoil_maker_dir)
    yield
    for job in JOB_HOLDERS:
        job.current().stop_on_shutdown()


def require_json(request: Request) -> None:
    """Every POST and PATCH must be JSON: that forces a CORS preflight, which the
    backend never answers, so no other site can start a job or change a file (ADR 0013)."""
    if request.method not in ("POST", "PATCH"):
        return
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type != "application/json":
        # ApiError is the API's one refusal shape, `{"code", "message"}`.
        raise ApiError(415, "unsupported_media_type", "ต้องส่งเป็น JSON")


# What the framework refuses before a route runs, in the API's one refusal shape too
# (spoil-maker spec › API). `..%2F` decodes to `../` before routing, so it is a 404 here.
FRAMEWORK_REFUSALS = {
    404: ("not_found", "ไม่พบ"),
    405: ("method_not_allowed", "ใช้ method นี้กับ path นี้ไม่ได้"),
}


async def framework_refusal_response(request: Request, error: HTTPException):
    code, message = FRAMEWORK_REFUSALS.get(error.status_code, ("http_error", str(error.detail)))
    return errors.error_response(request, ApiError(error.status_code, code, message))


async def invalid_body_response(request: Request, error: RequestValidationError):
    """A body that isn't the JSON object a route takes, the same `400` as any other bad field."""
    return errors.error_response(request, ApiError(400, "invalid_request", "ข้อมูลที่ส่งมาไม่ถูกต้อง"))


app = FastAPI(title="framecraft", lifespan=lifespan, dependencies=[Depends(require_json)])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_exception_handler(ApiError, errors.error_response)
app.add_exception_handler(HTTPException, framework_refusal_response)
app.add_exception_handler(RequestValidationError, invalid_body_response)
app.include_router(setup_status.router, prefix="/api")
app.include_router(spoil.router, prefix="/api")
app.include_router(spoil_maker.router, prefix="/api")
