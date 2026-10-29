"""The spoil tab's backend: YouTube links in, Temp clips in media/temp/ out,
and Transcripts of them from Whisper.

`adapter`, `free_bytes` and `start_worker` are looked up at call time, so
tests swap them for fakes (the same way as `backend.checks`' probes).
"""

from backend import disk
from backend.spoil.adapter import YtDlpAdapter
from backend.spoil.whisper import start_worker

adapter = YtDlpAdapter()
free_bytes = disk.free_bytes
