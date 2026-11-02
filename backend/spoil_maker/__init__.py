"""The สปอย tab's backend: Shots of Temp clips (Describe job), Saved voices (Voice
job), and the Spoil draft (Draft job), more in later tickets.

`start_worker`, `start_tts_worker`, `find_cuts` and `count_tokens` are looked up at
call time, so tests swap them for fakes (the same way as `backend.spoil`'s adapter
and worker).
"""

from backend.spoil_maker.frames import find_cuts
from backend.spoil_maker.llm import start_worker
from backend.spoil_maker.tokens import count as count_tokens
from backend.spoil_maker.tts import start_worker as start_tts_worker
