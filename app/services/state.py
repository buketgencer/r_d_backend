from __future__ import annotations
import uuid, threading, time

_jobs: dict[str, dict] = {}
_lock = threading.Lock()

def new_job() -> str:
    jid = uuid.uuid4().hex
    with _lock:
        _jobs[jid] = {"status": "processing", "created": time.time()}
    return jid

def update(jid: str, **fields):
    with _lock:
        if jid in _jobs:
            _jobs[jid].update(fields)

def get(jid: str) -> dict | None:
    return _jobs.get(jid)
