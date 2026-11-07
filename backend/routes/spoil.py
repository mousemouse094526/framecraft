from typing import Any

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend import paths
from backend.spoil import clips, downloads, transcribe, trim
from backend.spoil.clips import ListedClip
from backend.spoil.downloads import DownloadJob
from backend.spoil.transcribe import TranscribeJob, Transcript, TranscriptLine
from backend.spoil.trim import TrimJob


router = APIRouter(prefix="/spoil")


class DownloadRequest(BaseModel):
    url: str


class TranscribeRequest(BaseModel):
    clip_id: str
    confirm_edit_loss: bool = False
    confirm_draft_loss: bool = False


class LineEdit(BaseModel):
    text: str


class ClipList(BaseModel):
    clips: list[ListedClip]


@router.get("/clips")
def list_clips() -> ClipList:
    return ClipList(clips=clips.list_clips(paths.project()))


@router.get("/clips/{clip_id}")
def get_clip(clip_id: str) -> ListedClip:
    return clips.listed_clip(paths.project(), clip_id)


@router.get("/clips/{clip_id}/video")
def get_video(clip_id: str) -> FileResponse:
    """FileResponse answers `Range` with 206, so the player can seek."""
    return FileResponse(clips.video_file(paths.project(), clip_id), media_type="video/mp4")


@router.get("/clips/{clip_id}/thumbnail")
def get_thumbnail(clip_id: str) -> FileResponse:
    thumbnail = clips.thumbnail(paths.project(), clip_id)
    return FileResponse(thumbnail.path, media_type=thumbnail.media_type)


@router.delete("/clips/{clip_id}", status_code=204)
def delete_clip(clip_id: str) -> Response:
    transcribe.transcriptions.delete_clip(clip_id)
    return Response(status_code=204)


@router.get("/clips/{clip_id}/transcript")
def get_transcript(clip_id: str) -> Transcript:
    return transcribe.read_transcript(paths.project(), clip_id)


@router.patch("/clips/{clip_id}/transcript/lines/{n}")
def edit_transcript_line(clip_id: str, n: str, body: LineEdit) -> TranscriptLine:
    return transcribe.transcriptions.edit_line(clip_id, n, body.text)


@router.get("/clips/{clip_id}/transcript.txt")
def get_transcript_txt(clip_id: str) -> Response:
    text = transcribe.transcript_txt(paths.project(), clip_id)
    return _download(text, "text/plain; charset=utf-8", f"{clip_id}.txt")


@router.get("/clips/{clip_id}/transcript.srt")
def get_transcript_srt(clip_id: str) -> Response:
    text = transcribe.transcript_srt(paths.project(), clip_id)
    return _download(text, "application/x-subrip", f"{clip_id}.srt")


def _download(text: str, media_type: str, filename: str) -> Response:
    # `filename` is a checked clip id (`CLIP_ID`) plus a suffix, so it needs no quoting.
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(text.encode("utf-8"), media_type=media_type, headers=headers)


@router.post("/transcriptions", status_code=202)
def start_transcription(body: TranscribeRequest) -> TranscribeJob:
    return transcribe.transcriptions.start(body.clip_id, body.confirm_edit_loss, body.confirm_draft_loss)


@router.get("/transcriptions/current")
def get_current_transcription() -> TranscribeJob | None:
    """The latest job, or null when none ran since the backend started."""
    return transcribe.transcriptions.current()


@router.delete("/transcriptions/current", status_code=202)
def cancel_transcription() -> TranscribeJob:
    return transcribe.transcriptions.cancel()


@router.post("/downloads", status_code=202)
def start_download(body: DownloadRequest) -> DownloadJob:
    return downloads.downloads.start(body.url)


@router.get("/downloads/current")
def get_current_download() -> DownloadJob | None:
    """The latest job, or null when none ran since the backend started."""
    return downloads.downloads.current()


@router.delete("/downloads/current", status_code=202)
def cancel_download() -> DownloadJob:
    return downloads.downloads.cancel()


@router.post("/trims", status_code=202)
def start_trim(body: dict[str, Any]) -> TrimJob:
    return trim.trims.start(body)


@router.get("/trims/current")
def get_current_trim() -> TrimJob | None:
    """The latest Trim job, or null when none ran since the backend started."""
    return trim.trims.current()


@router.delete("/trims/current", status_code=202)
def cancel_trim() -> TrimJob:
    return trim.trims.cancel()
