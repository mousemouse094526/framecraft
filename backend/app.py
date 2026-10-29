"""The framecraft backend. Run with `npm run dev`; it binds 127.0.0.1 only."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend import paths
from backend.paths import ProjectPaths
from backend.routes import setup_status, spoil
from backend.spoil import clips, jobs
from backend.spoil.jobs import SpoilError

# Binding 127.0.0.1 doesn't stop DNS rebinding from another site (ADR 0011).
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Download jobs don't survive a restart, so their leftovers go (spoil D15).
    clips.clean_on_start(ProjectPaths(paths.ROOT))
    yield
    jobs.downloads.stop_on_shutdown()


app = FastAPI(title="framecraft", lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_exception_handler(SpoilError, spoil.spoil_error_response)
app.include_router(setup_status.router, prefix="/api")
app.include_router(spoil.router, prefix="/api")
