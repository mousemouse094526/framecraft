"""The สปอย tab's backend: Shots of Temp clips first (Describe job), more in later tickets.

`start_worker` and `find_cuts` are looked up at call time, so tests swap them
for fakes (the same way as `backend.spoil`'s adapter and worker).
"""

from backend.spoil_maker.frames import find_cuts
from backend.spoil_maker.llm import start_worker
