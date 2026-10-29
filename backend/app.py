"""The framecraft backend. Run with `npm run dev`; it binds 127.0.0.1 only."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend import paths
from backend.paths import ProjectPaths
from backend.routes import setup_status, spoil
from backend.spoil import clips, jobs, transcribe
from backend.spoil.errors import SpoilError

# Binding 127.0.0.1 doesn't stop DNS rebinding from another site (ADR 0011).
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jobs don't survive a restart, so their leftovers go (spoil D15, D29).
    clips.clean_on_start(ProjectPaths(paths.ROOT))
    yield
    jobs.downloads.stop_on_shutdown()
    transcribe.transcriptions.stop_on_shutdown()


def require_json(request: Request) -> None:
    """Every POST must be JSON: that forces a CORS preflight, which the backend
    never answers, so no other site can start a job (ADR 0013)."""
    if request.method != "POST":
        return
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type != "application/json":
        # SpoilError is the API's one refusal shape, `{"code", "message"}`.
        raise SpoilError(415, "unsupported_media_type", "ต้องส่งเป็น JSON")


app = FastAPI(title="framecraft", lifespan=lifespan, dependencies=[Depends(require_json)])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_exception_handler(SpoilError, spoil.spoil_error_response)
app.include_router(setup_status.router, prefix="/api")
app.include_router(spoil.router, prefix="/api")
