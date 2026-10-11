"""Read-only diagnosis of an existing immutable evidence package."""

import argparse
import hashlib
import json
from pathlib import Path
from .schema import Problem
from .model import Scenario
from .analysis import diagnose, sensitivity
from .scenarios import sampled
from .experiment import canonical


def analyse_baseline(path, sensitivity_samples=100):
    raw = Path(path).read_bytes()
    evidence = json.loads(raw)
    science = evidence["science"]
    if (
        hashlib.sha256(canonical(science).encode()).hexdigest()
        != evidence["scientific_sha256"]
    ):
        raise ValueError("Evidence scientific hash mismatch")
    p = Problem.parse(science["configuration"])
    candidate = next(c for c in science["candidates"] if c["id"] == "robust-lp")
    scenarios = [
        Scenario(
            s["id"], tuple(s["availability"]), s["supply_factor"], s["demand_factor"]
        )
        for s in science["heldout_scenarios"]
    ]
    return dict(
        source_experiment=evidence["experiment_id"],
        source_file_sha256=hashlib.sha256(raw).hexdigest(),
        diagnosis=diagnose(
            p,
            candidate["synthesis"]["capacities"],
            scenarios,
            candidate["heldout_results"],
        ),
        sensitivity_seed=20261012,
        sensitivity=sensitivity(
            p,
            candidate["synthesis"]["capacities"],
            sampled(p, 20261012, sensitivity_samples),
        ),
    )


def main():
    parser = argparse.ArgumentParser(description="Read-only baseline failure diagnosis")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=100)
    args = parser.parse_args()
    result = analyse_baseline(args.evidence, args.samples)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            dict(
                failures=result["diagnosis"]["failures"],
                labels=result["diagnosis"]["label_counts"],
            )
        )
    )


if __name__ == "__main__":
    main()
