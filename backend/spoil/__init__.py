"""The spoil tab's backend: YouTube links in, Temp clips in media/temp/ out.

`adapter` and `free_bytes` are looked up at call time, so tests swap them for
fakes (the same way as `backend.checks`' probes).
"""

from backend import disk
from backend.spoil.adapter import YtDlpAdapter

adapter = YtDlpAdapter()
free_bytes = disk.free_bytes
