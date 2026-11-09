"""The การ์ตูนเล่า tab's backend (toon spec): Series with their characters and backgrounds,
their reference pictures (Ref job), and the Toon job slot.

`start_klein_worker` is looked up at call time, so tests swap it for a fake (as
`spoil_maker.start_worker`, which the Toon job's Qwen steps call too).
"""

from backend.toon.klein import start_worker as start_klein_worker
