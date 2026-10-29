from fastapi import APIRouter

from backend.checks import StatusResponse, run_checks

router = APIRouter(prefix="/setup")


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Always 200: anything wrong is a `missing` or `warning` item in the body."""
    return run_checks()
