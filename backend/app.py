"""The framecraft backend. Run with `npm run dev`; it binds 127.0.0.1 only."""

from fastapi import FastAPI

from backend.routes import setup_status

app = FastAPI(title="framecraft")
app.include_router(setup_status.router, prefix="/api")
