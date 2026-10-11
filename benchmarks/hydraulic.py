"""Measured hydraulic throughput and solver behavior, never a performance guarantee."""

import json, time, resource, platform
from pathlib import Path
import numpy as np, scipy
from deva.hydraulic_v2 import parse, simulate
from deva.hydraulic_experiment import sampled

raw = json.loads(Path("examples/emergency_water_hydraulic.json").read_text())
record = json.loads(Path("artifacts/hydraulic-evidence.json").read_text())
c = next(
    c
    for c in record["science"]["candidates"]
    if c["id"] == record["science"]["recommendation"]
)
scenarios = sampled(parse(raw), 20261024, 100)
times = []
failures = []
evaluations = []
for s in scenarios:
    start = time.perf_counter()
    try:
        r = simulate(raw, c["diameters_m"], s)
        evaluations.append(r["solver_evaluations"])
    except RuntimeError as e:
        failures.append(dict(scenario=s, error=str(e)))
    times.append(time.perf_counter() - start)
report = dict(
    environment=dict(
        python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__
    ),
    experiment=record["experiment_id"],
    seed=20261024,
    samples=100,
    median_seconds=float(np.median(times)),
    p95_seconds=float(np.quantile(times, 0.95)),
    scenarios_per_second=len(times) / sum(times),
    maximum_solver_evaluations=max(evaluations, default=None),
    solver_failures=failures,
    peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    caveat="Warm six-node fixed-friction local nonlinear benchmark, not hardware/field-scale validation",
)
Path("artifacts/hydraulic-performance.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
print(json.dumps(report))
