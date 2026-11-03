"""The framecraft backend. Run with `npm run dev`; it binds 127.0.0.1 only."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException

from backend import errors, files, paths
from backend.errors import ApiError
from backend.paths import ProjectPaths
from backend.routes import setup_status, spoil, spoil_maker
from backend.spoil import clips, downloads, transcribe
from backend.spoil_maker import describe, draft, render, shots, voices

# Binding 127.0.0.1 doesn't stop DNS rebinding from another site (ADR 0011).
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jobs don't survive a restart, so their leftovers go (spoil D15, D29).
    project = ProjectPaths(paths.ROOT)
    clips.clean_on_start(project)
    # After the clips: Shots of a clip that start-up removed go too (spoil-maker spec › Ops).
    shots.clean_on_start(project, {clip.id for clip in clips.list_clips(project)})
    voices.clean_on_start(project)
    render.clean_on_start(project)
    # Half-written `draft.json`, `settings.json`, voice files (spoil-maker spec › Ops).
    files.remove_unfinished(project.spoil_maker_dir)
    yield
    downloads.downloads.stop_on_shutdown()
    transcribe.transcriptions.stop_on_shutdown()
    describe.describes.stop_on_shutdown()
    draft.draft_jobs.stop_on_shutdown()
    voices.voice_jobs.stop_on_shutdown()
    render.render_jobs.stop_on_shutdown()


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
