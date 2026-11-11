"""Whole-Mac memory during real toon image jobs, for toon D74's measurement on a 16 GB Mac.

Starts jobs through the running backend's API one after another and, every 5 seconds, writes
the swap used, `memory_pressure`'s level, vm_stat's pageouts and swapouts, and the footprint
of the backend and each of its children (Qwen, klein) next to the job's state. Standard
library only; macOS only (`sysctl`, `vm_stat`, `footprint`).

    .venv/bin/python scripts/measure_toon_memory.py OUT_DIR ref SERIES_ID ITEM_KIND ITEM_ID [COUNT]
    .venv/bin/python scripts/measure_toon_memory.py OUT_DIR image EP_ID missing|stale_ref
    .venv/bin/python scripts/measure_toon_memory.py OUT_DIR image EP_ID card CARD_ID [CARD_ID ...]

`card` runs one Image job per card, one after another.

`OUT_DIR` gets `events.log` (each job's states with seconds since its start) and `samples.tsv`.
`FRAMECRAFT_API` overrides the backend's address (default http://127.0.0.1:8000/api).
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

API = os.environ.get("FRAMECRAFT_API", "http://127.0.0.1:8000/api")
PORT = urlparse(API).port or 8000
EVERY = 5  # seconds between samples (D74)
POLL = 3  # seconds between reads of the job
ENDED = ("done", "failed", "cancelled")


def clock() -> str:
    return time.strftime("%H:%M:%S")


def get(path: str):
    with urllib.request.urlopen(API + path, timeout=30) as response:
        return json.loads(response.read() or b"null")


def post(path: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(API + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as refused:
        return refused.code, json.loads(refused.read())


def run(command: list[str]) -> str:
    return subprocess.run(command, capture_output=True, text=True).stdout


def footprint_gb(pid: str) -> float:
    found = re.search(r"Footprint: ([\d.]+) (KB|MB|GB)", run(["footprint", "-p", pid]))
    if not found:
        return 0.0
    return float(found[1]) / {"KB": 2**20, "MB": 2**10, "GB": 1}[found[2]]


def backend_pid() -> str:
    pids = run(["lsof", f"-tiTCP:{PORT}", "-sTCP:LISTEN"]).split()
    if not pids:
        raise SystemExit(f"no backend listens on port {PORT}")
    return pids[0]


class Sampler(threading.Thread):
    def __init__(self, out: Path):
        super().__init__(daemon=True)
        self.job = ""  # the job's state as the samples name it
        self._stop_event = threading.Event()
        samples = out / "samples.tsv"
        new = not samples.exists()  # runs append to the same file: one header
        self._file = samples.open("a", encoding="utf-8")
        if new:
            self._file.write("time\tswap_used_mb\tpressure_level\tpageouts\tswapouts\tbackend_gb\tchildren_gb\tjob\n")

    def run(self) -> None:
        backend = backend_pid()
        while not self._stop_event.is_set():
            swap = re.search(r"used = ([\d.]+)M", run(["sysctl", "vm.swapusage"]))[1]
            level = run(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"]).strip()  # 1 normal, 2 warn, 4 critical
            vm = run(["vm_stat"])
            pageouts = re.search(r"Pageouts:\s+(\d+)", vm)[1]
            swapouts = re.search(r"Swapouts:\s+(\d+)", vm)[1]
            children = ";".join(f"{pid}:{footprint_gb(pid):.2f}" for pid in run(["pgrep", "-P", backend]).split())
            self._file.write(
                f"{clock()}\t{float(swap):.0f}\t{level}\t{pageouts}\t{swapouts}\t{footprint_gb(backend):.2f}\t{children}\t{self.job}\n"
            )
            self._file.flush()
            self._stop_event.wait(EVERY)

    def stop(self) -> None:
        self._stop_event.set()
        self.join(EVERY * 2)


def watch(n: int, body: dict, sampler: Sampler, events) -> bool:
    """Starts one job and logs each state it passes; True when it ends `done`."""
    started = time.monotonic()
    status, answer = post("/toon/jobs", body)
    events.write(f"{clock()} job {n} POST {status} {answer.get('code', '')}\n")
    if status != 202:
        return False
    last = None
    while True:
        job = get("/toon/jobs/current") or {}
        now = (job.get("state"), job.get("done"), job.get("total"))
        sampler.job = f"{n}:{now[0]}:{now[1]}"
        if now != last:
            events.write(f"{clock()} job {n} {now[0]} {now[1]}/{now[2]} at {time.monotonic() - started:.0f} s\n")
            events.flush()
            last = now
        if now[0] in ENDED:
            extra = {key: job.get(key) for key in ("error", "failed_cards", "skipped") if job.get(key)}
            events.write(f"{clock()} job {n} END {now[0]} {json.dumps(extra, ensure_ascii=False)} after {time.monotonic() - started:.0f} s\n")
            events.flush()
            return now[0] == "done"
        time.sleep(POLL)


def bodies(args: list[str]) -> list[dict]:
    match args:
        case ["ref", series_id, item_kind, item_id, *count]:
            body = {"kind": "ref", "series_id": series_id, "item_kind": item_kind, "item_id": item_id}
            return [body] * int(count[0] if count else 1)
        case ["image", ep_id, "card", *card_ids] if card_ids:
            return [{"kind": "image", "ep_id": ep_id, "card_id": card_id} for card_id in card_ids]
        case ["image", ep_id, scope]:
            return [{"kind": "image", "ep_id": ep_id, "scope": scope}]
    raise SystemExit(__doc__)


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    jobs = bodies(sys.argv[2:])
    out.mkdir(parents=True, exist_ok=True)
    sampler = Sampler(out)
    sampler.start()
    with (out / "events.log").open("a", encoding="utf-8") as events:
        for n, body in enumerate(jobs, start=1):
            if not watch(n, body, sampler, events):
                break
            time.sleep(10)  # the child's memory goes back before the next job
    sampler.stop()


if __name__ == "__main__":
    main()
