"""A card's narration: what a Voice job speaks, the wav it writes, and serving it (toon spec ›
Voice job, D8, D14, D21, spoil-maker D30, D32–D37).

A card's narration is `audio/{card_id}.wav`; `audio` keeps what was spoken (`thai.spoken` of
the text) and in which voice, so a changed text or a new EP voice makes it `stale_audio`.
"""

import os
from pathlib import Path

from pydantic import BaseModel

from backend import gpu, speaking
from backend.errors import ApiError
from backend.paths import ProjectPaths
from backend.spoil_maker import thai, voices
from backend.spoil_maker.tts import Spoken
from backend.toon import episodes, store
from backend.toon.store import Audio


class VoicePlan(BaseModel):
    """What one card's Voice job speaks, read once as it starts."""

    series_id: str
    ep_id: str
    card_id: str
    tts_text: str
    voice_id: str
    voice: voices.SavedVoice


def plan(project: ProjectPaths, body: dict) -> VoicePlan:
    """Raises `not_found`, `silent_card` for a card with no text (D21), and `voice_not_found`
    when the EP's Saved voice is gone."""
    ep_id, card_id = body.get("ep_id"), body.get("card_id")
    # The voice is read under the draft's lock, so a Saved voice delete can't slip in (D25).
    with gpu.slot.draft_lock, store.lock:
        series_now, ep = episodes.find(project, ep_id)
        card = episodes.card_of(ep, card_id)
        if not card.text:
            raise ApiError(400, "silent_card", "การ์ดเงียบไม่มีเสียงเล่า")
        voice = voices.saved_voice(project, ep.voice_id)
        if voice is None:
            raise ApiError(400, "voice_not_found", "ไม่พบเสียงเล่าของ EP นี้: เลือกเสียงที่บันทึกไว้")
        return VoicePlan(
            series_id=series_now.id,
            ep_id=ep.id,
            card_id=card.id,
            tts_text=thai.spoken(card.text),
            voice_id=ep.voice_id,
            voice=voice,
        )


def put_audio(project: ProjectPaths, plan: VoicePlan, spoken: Spoken) -> bool:
    """The wav, then under the lock the card's `audio`: what was spoken, in which voice, how
    long. False when the card went meanwhile: the narration is dropped."""
    folder = project.card_audio_dir(plan.series_id, plan.ep_id)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{plan.card_id}.wav"
    temporary = target.with_name(target.name + ".tmp")
    speaking.write_wav(temporary, spoken)
    seconds = round(speaking.wav_seconds(temporary), 3)
    with store.lock:
        ep = store.read_ep(project, plan.series_id, plan.ep_id)
        card = next((c for _, c in episodes.placed_cards(ep) if c.id == plan.card_id), None) if ep else None
        if card is None:
            temporary.unlink(missing_ok=True)
            return False
        os.replace(temporary, target)
        card.audio = Audio(tts_text=plan.tts_text, voice_id=plan.voice_id, duration_s=seconds)
        store.write_ep(project, plan.series_id, ep)
    return True


def audio_file(project: ProjectPaths, ep_id: str, card_id: str) -> Path:
    with store.lock:
        series_now, ep = episodes.find(project, ep_id)
        card = episodes.card_of(ep, card_id)
        path = project.card_audio_dir(series_now.id, ep_id) / f"{card_id}.wav"
        if card.audio is None or not path.is_file():
            raise ApiError(404, "not_found", "การ์ดนี้ยังไม่มีเสียงเล่า")
        return path
