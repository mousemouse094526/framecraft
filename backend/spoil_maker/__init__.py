"""The สปอย tab's backend: Shots of Temp clips (Describe job) and Saved voices (Voice
job), more in later tickets.

`start_worker`, `start_tts_worker` and `find_cuts` are looked up at call time, so
tests swap them for fakes (the same way as `backend.spoil`'s adapter and worker).
"""

from backend.spoil_maker.frames import find_cuts
from backend.spoil_maker.llm import start_worker
from backend.spoil_maker.tts import start_worker as start_tts_worker
