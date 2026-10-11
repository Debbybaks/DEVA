"""Predeclared cross-domain search comparison and frozen water decision analysis."""

import argparse
import json
import hashlib
from pathlib import Path
import numpy as np
from .general_engineer import investigate, STRATEGIES
from .domains.water import WaterDomain
from .domains.microgrid import MicrogridDomain
from .experiment import canonical
from .verification import wilson
from .audit import verify_hash
from .provenance import source_revision

ROOT = Path(__file__).resolve().parents[2]


def decision_analysis(package, count=120, seed=20261120):
    verify_hash(package)
    agent = package["science"]["engineering_agent"]
    verify_hash(agent)
    science = agent["science"]
    raw = science["effective_configuration"]
    domain = WaterDomain(raw)
    selected = next(
        c
        for c in science["outputs"]["simulate_training"]["candidates"]
        if c["id"] == science["selection"]
    )
    base = selected["diameters_m"]
    i = next(i for i, s in enumerate(domain.variables) if s["id"] == "west-trunk")
    scenarios = domain.scenarios(seed, count)
    rows = []
    for name, diameter in [
        ("current", base[i]),
        ("compromise", 0.15),
        ("upgrade", 0.175),
    ]:
        d = list(base)
        d[i] = diameter
        records = []
        for s in scenarios:
            r = domain.simulate(d, s)
            hospital = r["state"]["pressure_head_m"]["hospital"]
            service = (
                r["state"]["delivered_m3s"]["hospital"]
                / r["state"]["requested_m3s"]["hospital"]
            )
            passes = (
                hospital is not None
                and hospital >= domain.model["pmin"] - 1e-6
                and service >= domain.model["target"] - 1e-7
            )
            records.append(
                dict(
                    scenario=s,
                    outcome=r,
                    hospital_passes=passes,
                    hospital_service=service,
                    hospital_pressure_m=hospital,
                )
            )
        failures = sum(not r["hospital_passes"] for r in records)
        rows.append(
            dict(
                id=name,
                design=d,
                cost=domain.cost(d),
                records=records,
                failures=failures,
                samples=count,
                wilson_95=list(wilson(failures, count)),
            )
        )
    limit = science["plan"]["constraints"]["maximum_cost"]
    improved = [r for r in rows if r["failures"] < rows[0]["failures"]]
    least = min(improved, key=lambda r: r["cost"]) if improved else None
    return dict(
        domain="water",
        source_experiment=package["experiment_id"],
        source_hash=package["scientific_sha256"],
        seed=seed,
        engineering_budget=limit,
        candidates=rows,
        smallest_known_relaxation=(
            dict(
                candidate=least["id"],
                additional_budget=max(0, least["cost"] - limit),
                observed_failures_removed=rows[0]["failures"] - least["failures"],
            )
            if least
            else None
        ),
        scope="Three predeclared designs evaluated on a fresh shared synthetic test population; no reselection, global optimum or infeasibility proof. Historical 4/40 unchanged.",
    )


def run(seeds=(20261101, 20261102, 20261103)):
    domains = [
        WaterDomain(
            json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        ),
        MicrogridDomain(json.loads((ROOT / "examples/microgrid.json").read_text())),
    ]
    results = []
    performance = {}
    summaries = []
    for domain in domains:
        for strategy in STRATEGIES:
            group = []
            for seed in seeds:
                e = investigate(
                    domain,
                    seed=seed,
                    strategy=strategy,
                    maximum_cost=500 if domain.descriptor["id"] == "water" else 300,
                    maximum_candidates=16,
                    maximum_generations=4,
                    maximum_simulations=400,
                    training_samples=8,
                    validation_samples=12,
                    heldout_samples=40,
                )
                performance[e["experiment_id"]] = e.pop("performance")
                results.append(e)
                s = e["science"]
                selected = next(
                    (c for c in s["candidates"] if c["id"] == s["selection"]), None
                )
                group.append(
                    dict(
                        experiment=e["experiment_id"],
                        failure_rate=(
                            s["heldout"]["failure_rate"] if s["heldout"] else None
                        ),
                        cost=selected["cost"] if selected else None,
                        solver_calls=s["solver_calls"],
                        diversity=s["diversity"],
                        stop=s["stopping_reason"],
                    )
                )
            summaries.append(
                dict(
                    domain=domain.descriptor["id"],
                    strategy=strategy,
                    trials=group,
                    mean_failure_rate=(
                        float(
                            np.mean(
                                [
                                    r["failure_rate"]
                                    for r in group
                                    if r["failure_rate"] is not None
                                ]
                            )
                        )
                        if any(r["failure_rate"] is not None for r in group)
                        else None
                    ),
                )
            )
    curves = []
    for domain in domains:
        example = next(
            e["science"]
            for e in results
            if e["science"]["domain"]["id"] == domain.descriptor["id"]
            and e["science"]["strategy"] == "hybrid"
        )
        selected = next(
            c for c in example["candidates"] if c["id"] == example["selection"]
        )
        for severity in [0, 0.5, 1, 1.5, 2]:
            scenarios = domain.scenarios(20261130, 20, severity=severity)
            records = [
                dict(scenario=s, outcome=domain.simulate(selected["design"], s))
                for s in scenarios
            ]
            failures = sum(not r["outcome"]["passes"] for r in records)
            curves.append(
                dict(
                    domain=domain.descriptor["id"],
                    design=selected["design"],
                    severity=severity,
                    seed=20261130,
                    failures=failures,
                    samples=20,
                    records=records,
                    scope="Common random numbers; severity scales demand and resource conditions, outage distribution fixed",
                )
            )
    package = json.loads((ROOT / "artifacts/digital-twin-evidence.json").read_text())
    science = dict(
        schema_version="5.0",
        code=source_revision(),
        predeclared_seeds=list(seeds),
        domain_descriptors=[d.descriptor for d in domains],
        experiments=results,
        ablation=summaries,
        robustness_curves=curves,
        decision_analysis=decision_analysis(package),
        limitations=[
            "Three seeds and a small catalogue are exploratory, not statistical proof of search superiority",
            "Equal upper solver budgets; strategies may consume different actual calls",
            "No empirical general engineering intelligence claim from two domains",
            "Synthetic distributions and perfect-foresight microgrid dispatch exclude field certification",
        ],
    )
    digest = hashlib.sha256(canonical(science).encode()).hexdigest()
    return dict(
        experiment_id="deva-cross-domain-" + digest[:16],
        scientific_sha256=digest,
        science=science,
        performance=performance,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    a = p.parse_args()
    e = run()
    Path(a.output).write_text(json.dumps(e, indent=2, allow_nan=False) + "\n")
    print(e["experiment_id"])
