"""Speaking texts in a Saved voice with OmniVoice in a child process (ADR 0012, ADR 0019):
spoil-maker's Voice and Render jobs and the การ์ตูนเล่า tab's Voice job share the loop, and
the wav files they write.
"""

import wave
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from backend import checks, spoil_maker
from backend.models import OMNIVOICE
from backend.paths import ProjectPaths
from backend.spoil_maker.tts import Designed, Ready, Speak, Spoken
from backend.workers import Worker

NUM_STEP = 16  # spoil-maker D37


class Voice(Protocol):
    """What speaking needs of a Saved voice (`voices.SavedVoice`)."""

    speed: float
    prompt: bytes


class Slot(Protocol):
    """What a Speaker asks of the job slot that holds it (`jobs.ModelJobSlot`)."""

    def start_child(self, worker: Worker, first: type, timeout: float | None = None) -> Worker: ...

    def ask(self, worker: Worker, request, expected: tuple[type, ...], timeout: float | None = None): ...


class Speaker:
    """Speaks texts in an OmniVoice child for the job slot that holds it: through that slot's
    `start_child` (so shutdown and the job's end stop the child) and `ask` (so a failure names
    the slot's child)."""

    def __init__(self, slot: Slot):
        self._slot = slot

    def start(self, project: ProjectPaths) -> Worker:
        """Starts the OmniVoice child and waits until it is loaded."""
        device = checks.probe_device()
        snapshot = project.snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
        return self._slot.start_child(spoil_maker.start_tts_worker(snapshot, device), Ready)

    def speak(self, project: ProjectPaths, texts: list[str], voice: Voice) -> Iterator[Spoken]:
        """Each text (numbers already words) spoken in one child in `voice`, in order, as
        soon as it is: the caller writes it before the next is asked for, so a cancel keeps
        the finished ones. Ask once more after the last text and it ends its child."""
        worker = self.start(project)
        for text in texts:
            request = Speak(text=text, prompt=voice.prompt, speed=voice.speed, num_step=NUM_STEP)
            yield self._slot.ask(worker, request, (Spoken,))
        worker.end()


def write_wav(path: Path, spoken: Designed | Spoken) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(spoken.sample_rate)
        audio.writeframes(spoken.audio)


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()
