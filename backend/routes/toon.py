from typing import Any

from fastapi import APIRouter, Body, Depends, Request, Response
from fastapi.responses import FileResponse

from backend import body_types, paths
from backend.toon import episodes, images, jobs, render, series, sounds, voicing
from backend.toon.episodes import EpView, ListedEp
from backend.toon.jobs import ToonJob
from backend.toon.render import RenderResult, ToonRenderJob
from backend.toon.kinds import ItemKind
from backend.toon.series import ListedSeries, SeriesView
from backend.toon.sounds import SoundImport, SoundView
from backend.uploads import UploadCheck

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
    series.delete(paths.project(), series_id, body)
    return Response(status_code=204)


# Before `/series/{series_id}/{item_kind}`: the first route that matches a path answers it.
@router.get("/series/{series_id}/eps")
def list_eps(series_id: str) -> list[ListedEp]:
    return episodes.list_for(paths.project(), series_id)


@router.post("/series/{series_id}/eps", status_code=201)
def create_ep(series_id: str, body: dict[str, Any]) -> EpView:
    return episodes.create(paths.project(), series_id, body)


@router.post("/series/{series_id}/{item_kind}", status_code=201)
def add_item(series_id: str, item_kind: ItemKind, body: dict[str, Any]) -> SeriesView:
    return series.add_item(paths.project(), series_id, item_kind, body)


@router.patch("/series/{series_id}/{item_kind}/{item_id}")
def change_item(series_id: str, item_kind: ItemKind, item_id: str, body: dict[str, Any]) -> SeriesView:
    return series.change_item(paths.project(), series_id, item_kind, item_id, body)


@router.delete("/series/{series_id}/{item_kind}/{item_id}")
def delete_item(series_id: str, item_kind: ItemKind, item_id: str) -> SeriesView:
    return series.delete_item(paths.project(), series_id, item_kind, item_id)


@router.get("/series/{series_id}/{item_kind}/{item_id}/ref")
def get_ref(series_id: str, item_kind: ItemKind, item_id: str) -> FileResponse:
    return FileResponse(series.ref_image(paths.project(), series_id, item_kind, item_id), media_type="image/png")


@router.get("/series/{series_id}/{item_kind}/{item_id}/ref/pending/{n}")
def get_pending_ref(series_id: str, item_kind: ItemKind, item_id: str, n: int) -> FileResponse:
    return FileResponse(series.pending_image(paths.project(), series_id, item_kind, item_id, n), media_type="image/png")


@router.post("/series/{series_id}/{item_kind}/{item_id}/ref/pick")
def pick_ref(series_id: str, item_kind: ItemKind, item_id: str, body: dict[str, Any]) -> SeriesView:
    return series.pick(paths.project(), series_id, item_kind, item_id, body)


@router.post("/series/{series_id}/{item_kind}/{item_id}/ref/upload/check")
def check_ref_upload(series_id: str, item_kind: ItemKind, item_id: str, body: dict[str, Any]) -> UploadCheck:
    return series.check_upload(paths.project(), series_id, item_kind, item_id, body)


@router.post("/series/{series_id}/{item_kind}/{item_id}/ref/upload", dependencies=[Depends(body_types.require_octet_stream)])
async def upload_ref(request: Request, series_id: str, item_kind: ItemKind, item_id: str, size: str | None = None) -> SeriesView:
    """The body is the picture itself (ADR 0028); `size` stays text so the module answers a
    bad one with `invalid_request`."""
    return await series.receive_upload(paths.project(), series_id, item_kind, item_id, size, request.stream())


@router.get("/eps/{ep_id}")
def get_ep(ep_id: str) -> EpView:
    return episodes.view(paths.project(), ep_id)


@router.patch("/eps/{ep_id}")
def change_ep(ep_id: str, body: dict[str, Any]) -> EpView:
    return episodes.change(paths.project(), ep_id, body)


@router.delete("/eps/{ep_id}", status_code=204)
def delete_ep(ep_id: str) -> Response:
    episodes.delete(paths.project(), ep_id)
    return Response(status_code=204)


@router.post("/eps/{ep_id}/acts", status_code=201)
def add_act(ep_id: str, body: dict[str, Any]) -> EpView:
    return episodes.add_act(paths.project(), ep_id, body)


@router.patch("/eps/{ep_id}/acts/{act_id}")
def change_act(ep_id: str, act_id: str, body: dict[str, Any]) -> EpView:
    return episodes.change_act(paths.project(), ep_id, act_id, body)


@router.delete("/eps/{ep_id}/acts/{act_id}")
def delete_act(ep_id: str, act_id: str) -> EpView:
    return episodes.delete_act(paths.project(), ep_id, act_id)


@router.post("/eps/{ep_id}/segments", status_code=201)
def add_segment(ep_id: str, body: dict[str, Any]) -> EpView:
    return episodes.add_segment(paths.project(), ep_id, body)


@router.patch("/eps/{ep_id}/segments/{segment_id}")
def change_segment(ep_id: str, segment_id: str, body: dict[str, Any]) -> EpView:
    return episodes.change_segment(paths.project(), ep_id, segment_id, body)


@router.delete("/eps/{ep_id}/segments/{segment_id}")
def delete_segment(ep_id: str, segment_id: str) -> EpView:
    return episodes.delete_segment(paths.project(), ep_id, segment_id)


@router.post("/eps/{ep_id}/cards", status_code=201)
def add_card(ep_id: str, body: dict[str, Any]) -> EpView:
    return episodes.add_card(paths.project(), ep_id, body)


@router.patch("/eps/{ep_id}/cards/{card_id}")
def change_card(ep_id: str, card_id: str, body: dict[str, Any]) -> EpView:
    return episodes.change_card(paths.project(), ep_id, card_id, body)


@router.delete("/eps/{ep_id}/cards/{card_id}")
def delete_card(ep_id: str, card_id: str) -> EpView:
    return episodes.delete_card(paths.project(), ep_id, card_id)


@router.post("/eps/{ep_id}/cards/{card_id}/swap-image")
def swap_image(ep_id: str, card_id: str) -> EpView:
    return images.swap(paths.project(), ep_id, card_id)


@router.get("/eps/{ep_id}/cards/{card_id}/image")
def get_image(ep_id: str, card_id: str) -> FileResponse:
    return FileResponse(images.image_file(paths.project(), ep_id, card_id), media_type="image/png")


@router.get("/eps/{ep_id}/cards/{card_id}/previous-image")
def get_previous_image(ep_id: str, card_id: str) -> FileResponse:
    return FileResponse(images.image_file(paths.project(), ep_id, card_id, previous=True), media_type="image/png")


@router.get("/eps/{ep_id}/cards/{card_id}/audio")
def get_audio(ep_id: str, card_id: str) -> FileResponse:
    return FileResponse(voicing.audio_file(paths.project(), ep_id, card_id), media_type="audio/wav")


@router.get("/eps/{ep_id}/renders")
def list_renders(ep_id: str) -> list[RenderResult]:
    return render.list_results(paths.project(), ep_id)


@router.get("/eps/{ep_id}/renders/{name}")
def get_render(ep_id: str, name: str) -> FileResponse:
    path = render.result_file(paths.project(), ep_id, name)
    return FileResponse(path, media_type="video/mp4", filename=path.name, content_disposition_type="inline")


@router.delete("/eps/{ep_id}/renders/{name}", status_code=204)
def delete_render(ep_id: str, name: str) -> Response:
    render.delete_result(paths.project(), ep_id, name)
    return Response(status_code=204)


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


@router.get("/sounds")
def list_sounds() -> list[SoundView]:
    return sounds.list_all(paths.project())


@router.patch("/sounds/{sound_id}")
def rename_sound(sound_id: str, body: dict[str, Any]) -> SoundView:
    return sounds.rename(paths.project(), sound_id, body)


@router.delete("/sounds/{sound_id}", status_code=204)
def delete_sound(sound_id: str) -> Response:
    sounds.delete(paths.project(), sound_id)
    return Response(status_code=204)


@router.get("/sounds/{sound_id}/file")
def get_sound_file(sound_id: str) -> FileResponse:
    return FileResponse(sounds.sound_file(paths.project(), sound_id), media_type="audio/mp4")


# A Sound import (spec › API): a file is `/imports` (one request), a link `/downloads` (a job);
# `/import/current` is the latest link's, the only one that runs on after its request.
@router.post("/sounds/imports/check")
def check_sound_import(body: dict[str, Any]) -> UploadCheck:
    return sounds.sound_imports.check(body)


@router.post("/sounds/imports", status_code=201, dependencies=[Depends(body_types.require_octet_stream)])
async def import_sound(request: Request, name: str | None = None, size: str | None = None) -> SoundView:
    """The body is the sound file itself (ADR 0028)."""
    return await sounds.sound_imports.receive(name, size, request.stream(), request.is_disconnected)


@router.post("/sounds/downloads", status_code=202)
def download_sound(body: dict[str, Any]) -> SoundImport:
    return sounds.sound_imports.start(body)


@router.get("/sounds/import/current")
def get_current_sound_import() -> SoundImport | None:
    """The latest link import, or null when none ran since the backend started."""
    return sounds.sound_imports.current()


@router.delete("/sounds/import/current", status_code=202)
def cancel_sound_import() -> SoundImport:
    return sounds.sound_imports.cancel()


@router.post("/render", status_code=202)
def start_render(body: dict[str, Any]) -> ToonRenderJob:
    return render.render_jobs.start(body)


@router.get("/render/current")
def get_current_render() -> ToonRenderJob | None:
    """The latest Render job, or null when none ran since the backend started."""
    return render.render_jobs.current()


@router.delete("/render/current", status_code=202)
def cancel_render() -> ToonRenderJob:
    return render.render_jobs.cancel()
