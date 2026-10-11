"""Typed local research API. Scientific work runs in separate processes."""

import asyncio
from functools import lru_cache
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
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from .schema import Problem
from .model import Scenario, simulate
from .audit import audit_result, ancestors
from .jobs import JobStore
from .view import project
from .experiment import canonical
from . import MODEL_VERSION

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=8)
def twin_projection(path, modified_ns, size):
    """Immutable artifact projection; metadata changes invalidate bounded cache."""
    from .twin_view import project as twin_project

    return twin_project(json.loads(Path(path).read_text()))


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


class HydraulicRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    raw: dict
    seed: int = Field(default=20261020, ge=0, lt=2**32)
    generations: int = Field(default=2, ge=1, le=3)
    train_count: int = Field(default=24, ge=2, le=80)
    validation_count: int = Field(default=24, ge=2, le=80)
    test_count: int = Field(default=100, ge=2, le=200)


class TwinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    raw: dict
    diameters: list[float] = Field(min_length=1, max_length=60)
    seed: int = Field(default=20261030, ge=0, lt=2**32 - 21)


class HydraulicLabRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    raw: dict
    diameters_m: list[float] = Field(min_length=1, max_length=60)
    closed: list[str] = Field(default_factory=list, max_length=60)
    demand_factor: float = Field(default=1.0, gt=0, le=3, allow_inf_nan=False)
    source_head_delta_m: float = Field(
        default=0.0, ge=-100, le=100, allow_inf_nan=False
    )
    friction_factor: float = Field(default=1.0, ge=0.5, le=2, allow_inf_nan=False)
    source_losses: list[str] = Field(default_factory=list, max_length=30)


def compute_hydraulic_lab(configuration):
    from .hydraulic_v2 import simulate, VERSION
    from .hydraulic_evidence import audit, envelope, provenance_revision
    from .hydraulic_view import state, causal_trace

    r = HydraulicLabRequest(**configuration)
    scenario = dict(
        id="hydraulic-interactive",
        closed=r.closed,
        demand_factor=r.demand_factor,
        source_head_delta_m=r.source_head_delta_m,
        friction_factor=r.friction_factor,
        source_losses=r.source_losses,
    )
    result = simulate(r.raw, r.diameters_m, scenario)
    check = audit(r.raw, r.diameters_m, scenario, result)
    e = envelope(
        dict(
            model_version=VERSION,
            configuration=r.raw,
            diameters_m=r.diameters_m,
            scenario=scenario,
            result=result,
            verification_object=check,
            code=provenance_revision(),
            software=dict(
                python=platform.python_version(),
                numpy=np.__version__,
                scipy=scipy.__version__,
            ),
        )
    )
    e["experiment_id"] = "deva-hydraulic-lab-" + e["scientific_sha256"][:16]
    e["causal_trace"] = causal_trace(r.raw, scenario, result)
    e["state"] = state(r.raw, r.diameters_m, scenario, result)
    return e


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

    app = FastAPI(title="DEVA Scientific Engine", version="0.4.0", lifespan=lifespan)

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
        return JSONResponse(
            project(json.loads((ROOT / "artifacts" / files[name]).read_text()))
        )

    @app.get("/api/jobs/{jid}/view")
    def job_view(jid: str):
        row = job(jid)
        if row["status"] != "completed":
            raise HTTPException(409, "Evidence not completed")
        record = json.loads((app.state.jobs.directory / f"{jid}.json").read_text())
        if record["science"]["schema_version"] == "4.0":
            from .twin_view import project as twin_project

            path = app.state.jobs.directory / f"{jid}.json"
            metadata = path.stat()
            return JSONResponse(
                twin_projection(str(path), metadata.st_mtime_ns, metadata.st_size)
            )
        if record["science"]["schema_version"] == "3.0":
            if record["science"]["recommendation"] is None:
                raise HTTPException(
                    409,
                    "No budget-feasible catalogue design; full negative evidence retained at this job evidence endpoint",
                )
            from .hydraulic_view import project as hydraulic_project

            return JSONResponse(hydraulic_project(record))
        return JSONResponse(project(record))

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

    @app.get("/api/hydraulic/{kind}")
    def hydraulic_artifact(kind: str):
        from .hydraulic_view import project as hydraulic_project

        if kind not in ("view", "evidence"):
            raise HTTPException(404, "Unknown hydraulic artifact")
        path = ROOT / "artifacts/hydraulic-evidence.json"
        if not path.exists():
            raise HTTPException(404, "Hydraulic experiment not generated")
        record = json.loads(path.read_text())
        return JSONResponse(hydraulic_project(record) if kind == "view" else record)

    @app.post("/api/hydraulic/jobs", status_code=202)
    def hydraulic_job(request: HydraulicRequest):
        from .hydraulic_v2 import parse

        try:
            parse(request.raw)
            record, cached = app.state.jobs.submit(
                dict(engine="hydraulic", **request.model_dump())
            )
            return dict(job_id=record["id"], cached=cached)
        except ValueError as error:
            raise HTTPException(422, str(error))
        except RuntimeError as error:
            raise HTTPException(429, str(error))

    @app.post("/api/hydraulic/lab")
    async def hydraulic_lab(request: HydraulicLabRequest):
        from .hydraulic_v2 import parse

        try:
            parse(request.raw)
            computed = await asyncio.wrap_future(
                app.state.jobs.pool.submit(compute_hydraulic_lab, request.model_dump())
            )
            path = app.state.jobs.directory / f"{computed['experiment_id']}.json"
            import uuid

            temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
            await asyncio.to_thread(
                temporary.write_text, json.dumps(computed, allow_nan=False)
            )
            await asyncio.to_thread(temporary.replace, path)
            return JSONResponse(computed)
        except (ValueError, RuntimeError) as error:
            raise HTTPException(422, str(error))

    @app.get("/api/hydraulic/lab/{experiment_id}")
    def hydraulic_lab_download(experiment_id: str):
        prefix = "deva-hydraulic-lab-"
        suffix = experiment_id.removeprefix(prefix)
        if (
            not experiment_id.startswith(prefix)
            or len(suffix) != 16
            or any(c not in "0123456789abcdef" for c in suffix)
        ):
            raise HTTPException(404, "Unknown hydraulic evidence")
        path = app.state.jobs.directory / f"{experiment_id}.json"
        if not path.exists():
            raise HTTPException(404, "Unknown hydraulic evidence")
        return FileResponse(path, media_type="application/json")

    @app.get("/api/twin/{kind}")
    def twin_artifact(kind: str):
        from .twin_view import project as twin_project

        if kind not in ("view", "evidence"):
            raise HTTPException(404, "Unknown twin artifact")
        path = ROOT / "artifacts/digital-twin-evidence.json"
        if not path.exists():
            raise HTTPException(404, "Synthetic twin benchmark not generated")
        record = json.loads(path.read_text())
        metadata = path.stat()
        return JSONResponse(
            twin_projection(str(path), metadata.st_mtime_ns, metadata.st_size)
            if kind == "view"
            else record
        )

    @app.post("/api/twin/jobs", status_code=202)
    def twin_job(request: TwinRequest):
        from .hydraulic_v2 import parse
        import math

        try:
            model = parse(request.raw)
            if len(request.diameters) != len(model["pipes"]) or any(
                not math.isfinite(d) or d <= 0 or d > 1 for d in request.diameters
            ):
                raise ValueError(
                    "Explicit positive SI diameters required for every pipe"
                )
            # The benchmark has explicit component names and corridor ownership.
            from .digital_twin import benchmark_data

            benchmark_data(request.raw, request.diameters, request.seed, noise=False)
            record, cached = app.state.jobs.submit(
                dict(engine="twin", **request.model_dump())
            )
            return dict(job_id=record["id"], cached=cached)
        except ValueError as error:
            raise HTTPException(422, str(error))
        except RuntimeError as error:
            raise HTTPException(429, str(error))

    return app


app = create_app()
