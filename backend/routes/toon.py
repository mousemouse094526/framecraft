from typing import Any

from fastapi import APIRouter, Body, Depends, Request, Response
from fastapi.responses import FileResponse

from backend import body_types, paths
from backend.toon import jobs, series
from backend.toon.jobs import ToonJob
from backend.toon.series import Kind, ListedSeries, SeriesView, UploadCheck

router = APIRouter(prefix="/toon")


@router.get("/series")
def list_series() -> list[ListedSeries]:
    return series.list_all(paths.project())


@router.post("/series", status_code=201)
def create_series(body: dict[str, Any]) -> SeriesView:
    return series.create(paths.project(), body)


@router.get("/series/{series_id}")
def get_series(series_id: str) -> SeriesView:
    return series.view(paths.project(), series_id)


@router.patch("/series/{series_id}")
def change_series(series_id: str, body: dict[str, Any]) -> SeriesView:
    return series.change(paths.project(), series_id, body)


@router.delete("/series/{series_id}", status_code=204)
def delete_series(series_id: str, body: dict[str, Any] | None = Body(None)) -> Response:
    jobs.toon_jobs.delete_series(paths.project(), series_id, body)
    return Response(status_code=204)


@router.post("/series/{series_id}/{kind}", status_code=201)
def add_item(series_id: str, kind: Kind, body: dict[str, Any]) -> SeriesView:
    return series.add_item(paths.project(), series_id, kind, body)


@router.patch("/series/{series_id}/{kind}/{item_id}")
def change_item(series_id: str, kind: Kind, item_id: str, body: dict[str, Any]) -> SeriesView:
    return series.change_item(paths.project(), series_id, kind, item_id, body)


@router.delete("/series/{series_id}/{kind}/{item_id}")
def delete_item(series_id: str, kind: Kind, item_id: str) -> SeriesView:
    return series.delete_item(paths.project(), series_id, kind, item_id)


@router.get("/series/{series_id}/{kind}/{item_id}/ref")
def get_ref(series_id: str, kind: Kind, item_id: str) -> FileResponse:
    return FileResponse(series.ref_image(paths.project(), series_id, kind, item_id), media_type="image/png")


@router.get("/series/{series_id}/{kind}/{item_id}/ref/pending/{n}")
def get_pending_ref(series_id: str, kind: Kind, item_id: str, n: int) -> FileResponse:
    return FileResponse(series.pending_image(paths.project(), series_id, kind, item_id, n), media_type="image/png")


@router.post("/series/{series_id}/{kind}/{item_id}/ref/pick")
def pick_ref(series_id: str, kind: Kind, item_id: str, body: dict[str, Any]) -> SeriesView:
    return series.pick(paths.project(), series_id, kind, item_id, body)


@router.post("/series/{series_id}/{kind}/{item_id}/ref/upload/check")
def check_ref_upload(series_id: str, kind: Kind, item_id: str, body: dict[str, Any]) -> UploadCheck:
    return series.check_upload(paths.project(), series_id, kind, item_id, body)


@router.post("/series/{series_id}/{kind}/{item_id}/ref/upload", dependencies=[Depends(body_types.require_octet_stream)])
async def upload_ref(request: Request, series_id: str, kind: Kind, item_id: str, size: str | None = None) -> SeriesView:
    """The body is the picture itself (ADR 0028); `size` stays text so the module answers a
    bad one with `invalid_request`."""
    return await series.receive_upload(paths.project(), series_id, kind, item_id, size, request.stream())


@router.post("/jobs", status_code=202)
def start_job(body: dict[str, Any]) -> ToonJob:
    return jobs.toon_jobs.start(body)


@router.get("/jobs/current")
def get_current_job() -> ToonJob | None:
    """The latest Toon job, or null when none ran since the backend started."""
    return jobs.toon_jobs.current()


@router.delete("/jobs/current", status_code=202)
def cancel_job() -> ToonJob:
    return jobs.toon_jobs.cancel()
