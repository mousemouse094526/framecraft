"""The stack dumpers of a child that hangs (toon D76), with `faulthandler`'s timer recorded."""

from contextlib import nullcontext

import pytest

from backend import workers


class FakeFaulthandler:
    def __init__(self):
        self.calls = []

    def dump_traceback_later(self, seconds, repeat=False):
        self.calls.append(("later", seconds, repeat))

    def cancel_dump_traceback_later(self):
        self.calls.append(("cancel",))


@pytest.mark.parametrize("fails", [False, True])
def test_dump_stacks_after_prints_again_each_time_while_the_block_runs_and_stops_however_it_ends(monkeypatch, fails):
    fake = FakeFaulthandler()
    monkeypatch.setattr(workers, "faulthandler", fake)

    with pytest.raises(RuntimeError) if fails else nullcontext():
        with workers.dump_stacks_after(600):
            assert fake.calls == [("later", 600, True)]
            if fails:
                raise RuntimeError("klein failed")

    assert fake.calls == [("later", 600, True), ("cancel",)]
