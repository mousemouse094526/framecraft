"""Speaking texts in a Saved voice with OmniVoice in a child process (ADR 0012, ADR 0019):
spoil-maker's Voice and Render jobs and the การ์ตูนเล่า tab's Voice job share the loop, and
the wav files they write.
"""

import wave
from collections.abc import Callable, Iterator
from pathlib import Path

from backend import checks, spoil_maker
from backend.models import OMNIVOICE
from backend.paths import ProjectPaths
from backend.spoil_maker.tts import Designed, Ready, Speak, Spoken

NUM_STEP = 16  # spoil-maker D37


class Speaker:
    """Speaks texts in an OmniVoice child for the job slot that holds it: through that slot's
    `track` (so shutdown and the job's end stop the child) and `reply` (so a failure names
    the slot's child)."""

    def __init__(self, track: Callable[[object], None], reply: Callable[..., object]):
        self._track = track
        self._reply = reply

    def start(self, project: ProjectPaths):
        """Starts the OmniVoice child and waits until it is loaded; returns it with its queues."""
        device = checks.probe_device()
        snapshot = project.snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
        process, requests, replies = spoil_maker.start_tts_worker(snapshot, device)
        self._track(process)
        self._reply(process, replies, (Ready,))
        return process, requests, replies

    def speak(self, project: ProjectPaths, texts: list[str], voice) -> Iterator[Spoken]:
        """Each text (numbers already words) spoken in one child in `voice` (a
        `voices.SavedVoice`), in order, as soon as it is: the caller writes it before the next
        is asked for, so a cancel keeps the finished ones."""
        process, requests, replies = self.start(project)
        for text in texts:
            requests.put(Speak(text=text, prompt=voice.prompt, speed=voice.speed, num_step=NUM_STEP))
            yield self._reply(process, replies, (Spoken,))
        requests.put(None)


def write_wav(path: Path, spoken: Designed | Spoken) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(spoken.sample_rate)
        audio.writeframes(spoken.audio)


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()
