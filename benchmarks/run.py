"""Measured local runtime/RSS, kept separate from deterministic scientific outputs."""

import argparse
import json
from pathlib import Path
import platform
import resource
import statistics
import time
import numpy as np
import scipy
from deva.schema import Problem
from deva.model import simulate, synthesise
from deva.scenarios import sampled, declared
from deva.evolution import evolve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/performance.json")
    )
    args = parser.parse_args()
    raw = json.loads(Path("examples/emergency_water.json").read_text())
    p = Problem.parse(raw)
    ss = declared(p)
    c = synthesise(p, ss)["capacities"]
    simulate(p, c, ss[0])
    timings = []
    for s in sampled(p, 100, 100):
        start = time.perf_counter()
        simulate(p, c, s)
        timings.append(time.perf_counter() - start)
    start = time.perf_counter()
    synthesise(p, ss)
    optimisation = time.perf_counter() - start
    start = time.perf_counter()
    r = evolve(raw, 100, 1, 10, 10, 10)
    evolution = time.perf_counter() - start
    report = dict(
        environment=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            scipy=scipy.__version__,
            platform=platform.platform(),
        ),
        graph=dict(nodes=len(p.nodes), edges=len(p.edges)),
        simulation=dict(
            samples=100,
            median_seconds=statistics.median(timings),
            p95_seconds=float(np.quantile(timings, 0.95)),
            scenarios_per_second=100 / sum(timings),
        ),
        synthesis_seconds=optimisation,
        evolution=dict(
            seconds=evolution,
            candidates=len(r["science"]["candidates"]),
            candidates_per_second=len(r["science"]["candidates"]) / evolution,
        ),
        process_peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        caveat="Single-process warm local benchmark, Linux RSS; no cross-machine claim. Browser frame timings are separate.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
