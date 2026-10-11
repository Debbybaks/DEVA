"""Post-hoc audit of the sealed Phase-2 test set, never a training input."""

import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from .analysis import diagnose
from .audit import verify_hash
from .schema import Problem
from .model import Scenario, operational, simulate
from .experiment import canonical


def augmentation(p, capacities, scenario):
    m, n = len(p.edges), len(p.nodes)
    _, _, demand, supply, balance = operational(p, scenario)
    cost = np.array([e.unit_cost for e in p.edges])
    objective = np.r_[cost, np.zeros(m + 2 * n)]
    rows = np.zeros((m + 1, 2 * m + 2 * n))
    rows[:m, :m] = -np.diag(scenario.availability)
    rows[:m, m : 2 * m] = np.eye(m)
    rows[-1, :m] = cost
    bounds = (
        [(c, e.max_capacity) for c, e in zip(capacities, p.edges)]
        + [(0, None)] * m
        + [(0, s) for s in supply]
        + [(p.target * d, d) for d in demand]
    )
    result = linprog(
        objective,
        A_ub=rows,
        b_ub=np.r_[np.zeros(m), p.budget],
        A_eq=np.c_[np.zeros((n, m)), balance],
        b_eq=np.zeros(n),
        bounds=bounds,
        method="highs",
    )
    if result.status == 2:
        return {
            "status": "infeasible_within_existing_topology_bounds_and_budget",
            "additional_cost": None,
        }
    if not result.success:
        raise RuntimeError(result.message)
    c = result.x[:m]
    state = simulate(p, c, scenario)
    if not state["passes"]:
        raise RuntimeError("Augmentation audit failed")
    return {
        "status": "numerically_feasible",
        "additional_cost": float(cost @ (c - np.asarray(capacities))),
        "capacities": c.tolist(),
        "result": state,
    }


def analyse(path):
    envelope = json.loads(Path(path).read_text())
    verify_hash(envelope)
    s = envelope["science"]
    p = Problem.parse(s["configuration"])
    c = next(c for c in s["candidates"] if c["id"] == s["recommendation"])
    scenarios = [
        Scenario(
            x["id"], tuple(x["availability"]), x["supply_factor"], x["demand_factor"]
        )
        for x in s["scenarios"]["heldout"]
    ]
    diagnosis = diagnose(p, c["capacities"], scenarios, c["heldout"]["results"])
    repairs = [
        dict(scenario_id=t.id, **augmentation(p, c["capacities"], t))
        for t, r in zip(scenarios, c["heldout"]["results"])
        if not r["passes"]
    ]
    return dict(
        source_experiment=envelope["experiment_id"],
        source_sha256=envelope["scientific_sha256"],
        candidate=c["id"],
        cost=c["cost"],
        diagnosis=diagnosis,
        posthoc_repairs=repairs,
        scope="Sealed test set opened for diagnosis only. Repair cost is a one-case continuous capacity lower bound, not a generalising design recommendation. Topology changes are not priced. No calibrated event likelihood or hydraulic interpretation exists for historical capacities.",
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("evidence")
    p.add_argument("--output", required=True)
    a = p.parse_args()
    Path(a.output).write_text(json.dumps(analyse(a.evidence), indent=2) + "\n")
