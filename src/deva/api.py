"""Typed local research API. Scientific work runs in separate processes."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import platform
import numpy as np
import scipy
import json
import os
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from .schema import Problem
from .model import Scenario, simulate
from .audit import audit_result, ancestors
from .jobs import JobStore
from .view import project
from .experiment import canonical
from . import MODEL_VERSION

ROOT = Path(__file__).resolve().parents[2]


class EvolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    raw: dict
    seed: int = Field(default=20261013, ge=0, lt=2**32)
    generations: int = Field(default=3, ge=1, le=4)
    train_samples: int = Field(default=60, ge=2, le=120)
    validation_samples: int = Field(default=80, ge=2, le=120)
    test_samples: int = Field(default=200, ge=2, le=300)


class LabRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    raw: dict
    capacities: list[float] = Field(max_length=60, min_length=1)
    availability: list[float] = Field(max_length=60, min_length=1)
    supply_factor: float = Field(default=1.0, ge=0, le=2, allow_inf_nan=False)
    demand_factor: float = Field(default=1.0, gt=0, le=2, allow_inf_nan=False)
    source_losses: list[str] = Field(default_factory=list, max_length=30)


def check_problem(raw):
    try:
        p = Problem.parse(raw)
        if len(p.nodes) > 30 or len(p.edges) > 60:
            raise ValueError("Local API graph limit: 30 nodes, 60 pipes")
        return p
    except (ValueError, TypeError) as error:
        raise HTTPException(422, str(error)) from error


def compute_lab(configuration):
    request = LabRequest(**configuration)
    p = Problem.parse(request.raw)
    supplies = tuple(
        0.0 if n in request.source_losses else s for n, s in zip(p.nodes, p.supply)
    )
    effective = replace(p, supply=supplies)
    scenario = Scenario(
        "interactive-lab",
        tuple(request.availability),
        request.supply_factor,
        request.demand_factor,
    )
    result = simulate(effective, request.capacities, scenario)
    result["independent_audit"] = audit_result(
        effective, request.capacities, scenario, result
    )
    science = dict(
        configuration=request.raw,
        capacities=request.capacities,
        source_losses=request.source_losses,
        scenario=dict(
            id=scenario.id,
            availability=list(scenario.availability),
            supply_factor=scenario.supply_factor,
            demand_factor=scenario.demand_factor,
        ),
        result=result,
        model_version=MODEL_VERSION,
        software=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            scipy=scipy.__version__,
            solver="HiGHS",
        ),
        scope="Static adaptive transport; animation is not hydraulic propagation",
    )
    digest = hashlib.sha256(canonical(science).encode()).hexdigest()
    return dict(
        experiment_id="deva-lab-" + digest[:16],
        scientific_sha256=digest,
        timestamp=datetime.now(timezone.utc).isoformat(),
        science=science,
        scenario=science["scenario"],
        source_losses=request.source_losses,
        result=result,
        scope=science["scope"],
    )


def create_app(directory=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.jobs = JobStore(
            directory or os.getenv("DEVA_RUNTIME_DIR", str(ROOT / ".runtime"))
        )
        yield
        app.state.jobs.close()

    app = FastAPI(title="DEVA Scientific Engine", version="0.2.0", lifespan=lifespan)

    def job(jid):
        try:
            return app.state.jobs.get(jid)
        except KeyError:
            raise HTTPException(404, "Unknown job")

    @app.get("/api/health")
    def health():
        return dict(status="ready", science="Python", formal_verification=False)

    @app.get("/api/problem")
    def problem():
        return json.loads((ROOT / "examples/emergency_water.json").read_text())

    @app.get("/api/evidence/{name}")
    def evidence(name: str):
        files = dict(
            baseline="emergency-water-evidence.json",
            evolution="evolution-evidence.json",
            diagnosis="baseline-failure-analysis.json",
        )
        if name not in files:
            raise HTTPException(404, "Unknown evidence")
        path = ROOT / "artifacts" / files[name]
        if not path.exists():
            raise HTTPException(404, "Evidence not generated")
        return FileResponse(path, media_type="application/json")

    @app.get("/api/view/{name}")
    def view(name: str):
        files = dict(
            baseline="emergency-water-evidence.json",
            evolution="evolution-evidence.json",
        )
        if name not in files:
            raise HTTPException(404, "Unknown evidence")
        return project(json.loads((ROOT / "artifacts" / files[name]).read_text()))

    @app.get("/api/jobs/{jid}/view")
    def job_view(jid: str):
        row = job(jid)
        if row["status"] != "completed":
            raise HTTPException(409, "Evidence not completed")
        return project(
            json.loads((app.state.jobs.directory / f"{jid}.json").read_text())
        )

    @app.post("/api/jobs", status_code=202)
    def submit(request: EvolutionRequest):
        check_problem(request.raw)
        try:
            row, cached = app.state.jobs.submit(request.model_dump())
        except ValueError as error:
            raise HTTPException(429, str(error))
        return dict(job_id=row["id"], status=row["status"], cached=cached)

    @app.get("/api/jobs/{jid}")
    def status(jid: str):
        row = job(jid)
        return dict(
            job_id=jid,
            status=row["status"],
            error=row["error"],
            cancel_requested=bool(row["cancel_requested"]),
        )

    @app.delete("/api/jobs/{jid}", status_code=202)
    def cancel(jid: str):
        row = job(jid)
        if row["status"] not in ("queued", "running"):
            raise HTTPException(409, "Job already terminal")
        app.state.jobs.cancel(jid)
        return dict(job_id=jid, cancel_requested=True)

    @app.get("/api/jobs/{jid}/evidence")
    def job_evidence(jid: str):
        row = job(jid)
        if row["status"] != "completed":
            raise HTTPException(409, "Evidence not completed")
        return FileResponse(
            app.state.jobs.directory / f"{jid}.json", media_type="application/json"
        )

    @app.get("/api/jobs/{jid}/events")
    async def events(
        jid: str,
        after: Annotated[int, Query(ge=0)] = 0,
        last_event_id: Annotated[int, Header(ge=0)] = 0,
    ):
        job(jid)

        async def stream():
            last = max(after, last_event_id)
            while True:
                rows = await asyncio.to_thread(app.state.jobs.events, jid, last)
                for row in rows:
                    last = row["sequence"]
                    yield f'id: {last}\ndata: {json.dumps(row["data"])}\n\n'
                state = await asyncio.to_thread(job, jid)
                if state["status"] in ("completed", "failed", "cancelled"):
                    # Drain the terminal event in case status changed after the read.
                    for row in await asyncio.to_thread(
                        app.state.jobs.events, jid, last
                    ):
                        yield f'id: {row["sequence"]}\ndata: {json.dumps(row["data"])}\n\n'
                    break
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.25)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.post("/api/lab")
    async def lab(request: LabRequest):
        p = check_problem(request.raw)
        if set(request.source_losses) - {n for n, s in zip(p.nodes, p.supply) if s > 0}:
            raise HTTPException(422, "Unknown source loss")
        try:
            # Validate before crossing the process boundary.
            Scenario(
                "lab",
                tuple(request.availability),
                request.supply_factor,
                request.demand_factor,
            ).validate(p)
            computed = await asyncio.wrap_future(
                app.state.jobs.pool.submit(compute_lab, request.model_dump())
            )
            path = app.state.jobs.directory / f"{computed['experiment_id']}.json"
            # Content-derived science identity, unique temporary file, atomic replace.
            import uuid

            temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
            await asyncio.to_thread(
                temporary.write_text, json.dumps(computed, allow_nan=False)
            )
            await asyncio.to_thread(temporary.replace, path)
            return computed
        except (ValueError, RuntimeError) as error:
            raise HTTPException(422, str(error))

    @app.get("/api/lab/{experiment_id}")
    def lab_evidence(experiment_id: str):
        prefix = "deva-lab-"
        suffix = experiment_id.removeprefix(prefix)
        if (
            not experiment_id.startswith(prefix)
            or len(suffix) != 16
            or any(c not in "0123456789abcdef" for c in suffix)
        ):
            raise HTTPException(404, "Unknown lab experiment")
        path = app.state.jobs.directory / f"{experiment_id}.json"
        if not path.exists():
            raise HTTPException(404, "Unknown lab experiment")
        return FileResponse(path, media_type="application/json")

    @app.get("/api/provenance/{name}")
    def trace(name: str, node: str = "conclusion:recommendation"):
        if name != "evolution":
            raise HTTPException(404, "Unknown graph")
        graph = json.loads((ROOT / "artifacts/evolution-evidence.json").read_text())[
            "science"
        ]["provenance"]
        try:
            return dict(node=node, ancestors=ancestors(graph, node))
        except ValueError as error:
            raise HTTPException(422, str(error))

    return app


app = create_app()
