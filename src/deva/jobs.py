"""Local process workers with durable SQLite job/event records and atomic evidence."""

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import platform
from pathlib import Path
import sqlite3
import threading
import uuid
import numpy as np
import scipy
from .evolution import evolve, EVOLUTION_VERSION
from .experiment import canonical


class CancelledExperiment(Exception):
    pass


def connection(directory):
    db = sqlite3.connect(Path(directory) / "jobs.sqlite", timeout=10)
    db.row_factory = sqlite3.Row
    return db


def emit(directory, job_id, event):
    with connection(directory) as db:
        db.execute(
            "INSERT INTO events(job_id,payload) VALUES (?,?)",
            (job_id, canonical(event)),
        )


def update(directory, job_id, status, error=None):
    with connection(directory) as db:
        db.execute(
            "UPDATE jobs SET status=?, error=? WHERE id=?", (status, error, job_id)
        )


def execute(directory, job_id, configuration):
    update(directory, job_id, "running")
    emit(directory, job_id, dict(stage="started"))

    def progress(event):
        with connection(directory) as db:
            cancelled = db.execute(
                "SELECT cancel_requested FROM jobs WHERE id=?", (job_id,)
            ).fetchone()[0]
        if cancelled:
            raise CancelledExperiment()
        emit(directory, job_id, event)

    try:
        if configuration.get("engine") == "hydraulic":
            from .hydraulic_experiment import experiment

            result = experiment(
                **{k: v for k, v in configuration.items() if k != "engine"},
                progress=progress,
            )
        else:
            result = evolve(**configuration, progress=progress)
        progress(dict(stage="persisting_evidence"))
        path = Path(directory) / f"{job_id}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, allow_nan=False))
        temporary.replace(path)
        update(directory, job_id, "completed")
        emit(
            directory,
            job_id,
            dict(stage="completed", experiment_id=result["experiment_id"]),
        )
    except CancelledExperiment:
        update(directory, job_id, "cancelled")
        emit(directory, job_id, dict(stage="cancelled"))
    except Exception as error:
        update(directory, job_id, "failed", str(error))
        emit(directory, job_id, dict(stage="failed", error=str(error)))


class JobStore:
    def __init__(self, directory, workers=2, max_pending=4):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.max_pending = max_pending
        with connection(self.directory) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, cache_key TEXT, status TEXT, configuration TEXT, created TEXT, error TEXT, cancel_requested INTEGER DEFAULT 0)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT,payload TEXT)"
            )
            db.execute(
                "UPDATE jobs SET status='failed', error='Service restarted before completion' WHERE status IN ('queued','running')"
            )
        self.pool = ProcessPoolExecutor(
            max_workers=workers, mp_context=multiprocessing.get_context("spawn")
        )
        self.source_hash = hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))
        ).hexdigest()

    def submit(self, configuration):
        key = hashlib.sha256(
            canonical(
                dict(
                    config=configuration,
                    model=EVOLUTION_VERSION,
                    source=self.source_hash,
                    python=platform.python_version(),
                    numpy=np.__version__,
                    scipy=scipy.__version__,
                )
            ).encode()
        ).hexdigest()
        with self.lock, connection(self.directory) as db:
            cached = db.execute(
                "SELECT * FROM jobs WHERE cache_key=? AND status IN ('queued','running','completed') ORDER BY created DESC LIMIT 1",
                (key,),
            ).fetchone()
            if cached:
                return dict(cached), True
            pending = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')"
            ).fetchone()[0]
            if pending >= self.max_pending:
                raise ValueError("Local worker queue full")
            jid = uuid.uuid4().hex
            db.execute(
                "INSERT INTO jobs(id,cache_key,status,configuration,created) VALUES (?,?,?,?,?)",
                (
                    jid,
                    key,
                    "queued",
                    canonical(configuration),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        emit(self.directory, jid, dict(stage="queued"))
        future = self.pool.submit(execute, str(self.directory), jid, configuration)

        def handle_crash(done):
            if done.cancelled():
                update(
                    self.directory, jid, "cancelled", "Cancelled before worker startup"
                )
                emit(self.directory, jid, dict(stage="cancelled"))
                return
            error = done.exception()
            if error:
                update(self.directory, jid, "failed", str(error))
                emit(
                    self.directory,
                    jid,
                    dict(stage="failed", error="Worker process exited unexpectedly"),
                )

        future.add_done_callback(handle_crash)
        return self.get(jid), False

    def get(self, jid):
        if len(jid) != 32 or any(c not in "0123456789abcdef" for c in jid):
            raise KeyError(jid)
        with connection(self.directory) as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if row is None:
            raise KeyError(jid)
        return dict(row)

    def events(self, jid, after=0):
        self.get(jid)
        with connection(self.directory) as db:
            return [
                dict(sequence=r["sequence"], data=json.loads(r["payload"]))
                for r in db.execute(
                    "SELECT sequence,payload FROM events WHERE job_id=? AND sequence>? ORDER BY sequence",
                    (jid, after),
                )
            ]

    def cancel(self, jid):
        self.get(jid)
        with connection(self.directory) as db:
            db.execute("UPDATE jobs SET cancel_requested=1 WHERE id=?", (jid,))

    def close(self):
        self.pool.shutdown(wait=True, cancel_futures=True)
