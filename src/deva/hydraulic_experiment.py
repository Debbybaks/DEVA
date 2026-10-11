"""Coupled diameter evolution, sealed hydraulic tests, adversarial probes and claims."""

from copy import deepcopy
from itertools import combinations
import json
import math
import platform
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import differential_evolution
from .hydraulic_v2 import parse, simulate, cost, timeline, VERSION
from .hydraulic_evidence import (
    audit,
    envelope,
    topology_verification,
    provenance_revision,
)
from .verification import wilson


def sampled(model, seed, count):
    rng = np.random.default_rng(seed)
    pipes = model["pipes"]
    out = []
    for i in range(count):
        closed = [e["id"] for e in pipes if rng.random() < 0.06]
        if rng.random() < 0.08:
            corridor = rng.choice(sorted({e["corridor"] for e in pipes}))
            closed = sorted(
                set(closed) | {e["id"] for e in pipes if e["corridor"] == corridor}
            )
        out.append(
            dict(
                id=f"iid:{seed}:{i}",
                closed=closed,
                demand_factor=float(rng.uniform(0.9, 1.4)),
                source_head_delta_m=float(rng.uniform(-6, 2)),
                friction_factor=1.0,
            )
        )
    return out


def evaluated(raw, diameters, scenarios):
    results = []
    for s in scenarios:
        try:
            r = simulate(raw, diameters, s)
            r["independent_audit"] = audit(raw, diameters, s, r)
            results.append(r)
        except RuntimeError as e:
            results.append(
                dict(
                    scenario_id=s["id"],
                    passes=False,
                    service_fraction=None,
                    solver_failure=str(e),
                    requirements={},
                    scope="Solver failure retained as unknown physical state and conservative failed evaluation",
                )
            )
    failures = sum(not r["passes"] for r in results)
    valid = [r for r in results if r["service_fraction"] is not None]
    return dict(
        results=results,
        metrics=dict(
            failures=failures,
            samples=len(results),
            failure_rate=failures / len(results),
            failure_rate_wilson_95=wilson(failures, len(results)),
            mean_service=(
                float(np.mean([r["service_fraction"] for r in valid]))
                if valid
                else None
            ),
            unknown_solver_states=len(results) - len(valid),
        ),
    )


def frontier(candidates, split="training"):
    def objectives(c):
        v = c[split]["metrics"]
        return (c["cost"], v["failure_rate"], 1 - (v["mean_service"] or 0.0))

    return [
        c["id"]
        for c in candidates
        if not any(
            all(a <= b + 1e-10 for a, b in zip(objectives(o), objectives(c)))
            and any(a < b - 1e-10 for a, b in zip(objectives(o), objectives(c)))
            for o in candidates
            if o["id"] != c["id"]
        )
    ]


def minimal_outages(raw, diameters, scenario):
    current = deepcopy(scenario)
    initial = simulate(raw, diameters, current)
    if initial["passes"]:
        raise ValueError("Failure minimisation requires a failed state")
    checks = []
    for pipe in list(current.get("closed", [])):
        trial = {
            **current,
            "closed": [p for p in current.get("closed", []) if p != pipe],
        }
        r = simulate(raw, diameters, trial)
        checks.append(dict(removed_pipe=pipe, scenario=trial, result=r))
        if not r["passes"]:
            current = trial
    # Monotonicity is not presumed: final one-element removals must all pass.
    final_checks = []
    for pipe in current.get("closed", []):
        t = {**current, "closed": [p for p in current["closed"] if p != pipe]}
        r = simulate(raw, diameters, t)
        final_checks.append(dict(removed_pipe=pipe, passes=r["passes"]))
    return dict(
        initial=scenario,
        minimized=current,
        result=simulate(raw, diameters, current),
        interventions=checks,
        final_removal_checks=final_checks,
        one_minimal=all(c["passes"] for c in final_checks),
        scope="One-minimal outage set conditional on fixed continuous disturbance. No causal attribution, global cardinality guarantee or physical temporal cascade.",
    )


def adversary(raw, diameters, seed):
    model = parse(raw)
    probes = []
    for k in [0, 1, 2]:
        for closed in combinations([e["id"] for e in model["pipes"]], k):
            s = dict(
                id=f"cut-probe:{len(probes)}", closed=list(closed), demand_factor=1.0
            )
            r = simulate(raw, diameters, s)
            probes.append(dict(scenario=s, result=r))
    # Active continuous search on the most vulnerable tested SINGLE-pipe scenario.
    one = [p for p in probes if len(p["scenario"]["closed"]) <= 1]
    weakest = min(one, key=lambda p: p["result"]["service_fraction"])
    continuous = []

    def objective(x):
        s = dict(
            id=f"adaptive:{len(continuous)}",
            closed=weakest["scenario"]["closed"],
            demand_factor=float(x[0]),
            source_head_delta_m=float(x[1]),
            friction_factor=float(x[2]),
        )
        r = simulate(raw, diameters, s)
        continuous.append(dict(scenario=s, result=r))
        return r["service_fraction"]

    differential_evolution(
        objective,
        [(1.0, 1.6), (-10.0, 0.0), (0.9, 1.3)],
        rng=np.random.default_rng(seed),
        popsize=4,
        maxiter=6,
        polish=False,
        workers=1,
    )
    worst = min(probes + continuous, key=lambda p: p["result"]["service_fraction"])
    continuous_worst = min(continuous, key=lambda p: p["result"]["service_fraction"])
    failures = [p for p in probes if not p["result"]["passes"]]
    chosen = (
        min(
            failures,
            key=lambda p: (
                len(p["scenario"]["closed"]),
                p["result"]["service_fraction"],
            ),
        )
        if failures
        else continuous_worst
    )
    minimized = (
        minimal_outages(raw, diameters, chosen["scenario"])
        if not chosen["result"]["passes"]
        else None
    )
    return dict(
        graph_probes=probes,
        adaptive_probes=continuous,
        worst=worst,
        continuous_worst=continuous_worst,
        minimal_failure=minimized,
        scope="Bounded active differential-evolution search after graph probes; biased adaptive probes have no failure-probability interpretation. No importance-sampling estimator.",
    )


def experiment(
    raw,
    seed=20261020,
    generations=2,
    train_count=24,
    validation_count=24,
    test_count=100,
    progress=None,
):
    model = parse(raw)
    emit = progress or (lambda event: None)
    emit(dict(stage="hydraulic_started"))
    if (
        any(
            isinstance(v, bool) or not isinstance(v, int)
            for v in [seed, generations, train_count, validation_count, test_count]
        )
        or isinstance(seed, bool)
        or not isinstance(seed, int)
        or not 0 <= seed < 2**32
        or not 1 <= generations <= 3
        or not all(2 <= n <= 200 for n in [train_count, validation_count, test_count])
    ):
        raise ValueError("Bounded experiment configuration required")
    streams = np.random.SeedSequence(seed).spawn(4)
    seeds = {
        name: int(s.generate_state(1)[0])
        for name, s in zip(
            ["training", "validation", "heldout", "adversarial"], streams
        )
    }
    training = sampled(model, seeds["training"], train_count)
    declared = [dict(id="declared:nominal", closed=[])] + [
        dict(id="declared:" + e["id"], closed=[e["id"]]) for e in model["pipes"]
    ]
    candidates = []
    history = []

    def add(diameters, parents, generation, mutation):
        cid = f"h{generation}-c{len(candidates):03d}"
        c = dict(
            id=cid,
            parents=parents,
            generation=generation,
            mutation=mutation,
            diameters_m=diameters,
            cost=cost(model, diameters),
            training=evaluated(raw, diameters, training),
            declared=evaluated(raw, diameters, declared),
        )
        c["rejection_reason"] = (
            "Budget exceeded" if c["cost"] > model["budget"] else None
        )
        candidates.append(c)
        emit(dict(stage="hydraulic_candidate", candidate_id=cid, generation=generation))
        return c

    for d in model["options"]:
        add([d] * len(model["pipes"]), [], 0, "uniform catalogue diameter")
    if not any(c["cost"] <= model["budget"] for c in candidates):
        return envelope(
            dict(
                schema_version="3.0",
                model_version=VERSION,
                configuration=raw,
                experiment_config=dict(
                    seed=seed,
                    generations=generations,
                    train_count=train_count,
                    validation_count=validation_count,
                    test_count=test_count,
                ),
                code=provenance_revision(),
                seeds=seeds,
                candidates=candidates,
                scenarios=dict(training=training, declared=declared),
                recommendation=None,
                status="NO_BUDGET_FEASIBLE_CATALOGUE_DESIGN",
                claim_ledger=[
                    dict(
                        claim="No generated catalogue design is within the stated budget",
                        status="NUMERICAL_VALIDATION",
                        evidence=[c["id"] for c in candidates],
                        scope="Catalogue candidates retained, not proof of infeasibility beyond this catalogue",
                    )
                ],
                limitations=[
                    "No candidate selected; failed catalogue candidates and training evidence retained",
                    "No held-out data opened for unsuccessful selection",
                ],
            )
        )
    for generation in range(1, generations + 1):
        feasible = [c for c in candidates if c["cost"] <= model["budget"]]
        f = frontier(feasible)
        parents = sorted(
            [c for c in feasible if c["id"] in f],
            key=lambda c: (c["training"]["metrics"]["failure_rate"], c["cost"]),
        )[:3]
        for parent in parents:
            rs = [
                r
                for r in parent["training"]["results"]
                if r["service_fraction"] is not None
            ]
            worst = min(rs, key=lambda r: r["service_fraction"])
            # Increase highest-loss pipe in a failed TRAINING state; signed pressure loss.
            losses = [
                (
                    abs(
                        (worst["head_m"][e["tail"]] or 0)
                        - (worst["head_m"][e["head"]] or 0)
                    )
                    if e["id"]
                    not in next(
                        s for s in training if s["id"] == worst["scenario_id"]
                    ).get("closed", [])
                    else -1
                )
                for e in model["pipes"]
            ]
            eligible = [
                j
                for j, d in enumerate(parent["diameters_m"])
                if d < model["options"][-1] - 1e-10
            ]
            if eligible:
                j = max(eligible, key=lambda j: losses[j])
                new = parent["diameters_m"].copy()
                new[j] = next(d for d in model["options"] if d > new[j] + 1e-10)
                add(
                    new,
                    [parent["id"]],
                    generation,
                    dict(
                        operator="training_headloss_reinforcement",
                        pipe=model["pipes"][j]["id"],
                    ),
                )
            # Resource-saving competing child: remove one catalogue size from a low-flow pipe.
            eligible = [
                j
                for j, d in enumerate(parent["diameters_m"])
                if d > model["options"][0] + 1e-10
            ]
            if eligible:
                j = min(eligible, key=lambda j: abs(worst["flow_m3s"][j]))
                new = parent["diameters_m"].copy()
                new[j] = max(d for d in model["options"] if d < new[j] - 1e-10)
                add(
                    new,
                    [parent["id"]],
                    generation,
                    dict(
                        operator="low_flow_cost_reduction", pipe=model["pipes"][j]["id"]
                    ),
                )
        history.append(
            dict(
                generation=generation,
                parents=[p["id"] for p in parents],
                training_frontier=frontier(
                    [c for c in candidates if c["cost"] <= model["budget"]]
                ),
            )
        )
    feasible = [c for c in candidates if c["cost"] <= model["budget"]]
    f = frontier(feasible)
    # Explicit operating target, training-only decision, never held-out targets.
    acceptable = [
        c
        for c in feasible
        if c["training"]["metrics"]["failure_rate"] <= 0.10
        and c["declared"]["metrics"]["failures"] == 0
    ]
    recommendation = (
        min(acceptable, key=lambda c: c["cost"])
        if acceptable
        else min(
            feasible,
            key=lambda c: (c["training"]["metrics"]["failure_rate"], c["cost"]),
        )
    )
    emit(dict(stage="hydraulic_heldout_audit"))
    validation = sampled(model, seeds["validation"], validation_count)
    test = sampled(model, seeds["heldout"], test_count)
    for c in candidates:
        c["validation"] = evaluated(raw, c["diameters_m"], validation)
        c["heldout"] = evaluated(raw, c["diameters_m"], test)
        if c["rejection_reason"] is None:
            c["rejection_reason"] = (
                None
                if c["id"] in f
                else "Dominated on training cost/failure/service objectives"
            )
        c["verification_status"] = (
            "STRESS TESTED"  # No full-design formal promotion from topology proof.
        )
    selected = next(c for c in candidates if c["id"] == recommendation["id"])
    emit(dict(stage="hydraulic_adversary"))
    search = adversary(raw, selected["diameters_m"], seeds["adversarial"])
    # Epistemic intervals: sensitivity envelope, NOT random credible intervals.
    epistemic = []
    for friction in [0.8, 1.0, 1.2]:
        for head_delta in [-3.0, 0.0, 3.0]:
            s = dict(
                id=f"epistemic:{friction}:{head_delta}",
                closed=[],
                friction_factor=friction,
                source_head_delta_m=head_delta,
            )
            epistemic.append(
                dict(scenario=s, result=simulate(raw, selected["diameters_m"], s))
            )
    # These audit frontiers are descriptive after test opening, not a selection procedure.
    audit_frontier = frontier(feasible, "heldout")
    sorted_frontier = sorted(
        [c for c in feasible if c["id"] in audit_frontier], key=lambda c: c["cost"]
    )
    segments = []
    for a, b in zip(sorted_frontier, sorted_frontier[1:]):
        delta = (
            a["heldout"]["metrics"]["failure_rate"]
            - b["heldout"]["metrics"]["failure_rate"]
        )
        segments.append(
            dict(
                from_candidate=a["id"],
                to_candidate=b["id"],
                additional_cost=b["cost"] - a["cost"],
                observed_failure_rate_reduction=delta,
                cost_per_percentage_point=(
                    (b["cost"] - a["cost"]) / (100 * delta) if delta > 0 else None
                ),
            )
        )
    levels = []
    for reliability in [0.9, 0.95, 0.975, 0.99, 0.995, 1.0]:
        matches = [
            c
            for c in feasible
            if 1 - c["heldout"]["metrics"]["failure_rate"] >= reliability
        ]
        best = min(matches, key=lambda c: c["cost"]) if matches else None
        levels.append(
            dict(
                requested_empirical_reliability=reliability,
                candidate=best["id"] if best else None,
                cost=best["cost"] if best else None,
                status="observed in retained catalogue" if best else "not demonstrated",
            )
        )
    tank = dict(
        node="source-west",
        area={"value": 20, "unit": "m2"},
        initial_volume={"value": 100, "unit": "m3"},
        maximum_volume={"value": 120, "unit": "m3"},
        base_head={"value": 40, "unit": "m"},
        inflow={"value": 0.003, "unit": "m3/s"},
    )
    times = timeline(
        raw,
        selected["diameters_m"],
        tank,
        24,
        300,
        [
            dict(step=6, scenario=dict(closed=["east-trunk"], demand_factor=1.3)),
            dict(step=16, scenario=dict(closed=[], demand_factor=1.0)),
        ],
    )
    emit(dict(stage="hydraulic_formal_properties"))
    formal = [topology_verification(raw, 1), topology_verification(raw, 2)]
    claims = [
        dict(
            id="claim:hydraulic-declared",
            claim=f'{selected["id"]} satisfies pressure-dependent service, pressure, velocity, supply and budget in the declared suite',
            status=(
                "EMPIRICAL_ROBUSTNESS"
                if selected["declared"]["metrics"]["failures"] == 0
                else "REFUTED"
            ),
            evidence=["candidates/" + selected["id"] + "/declared"],
            assumptions=[
                "Explicit uncalibrated geometry and friction",
                "Fixed-head sources; supply constraints checked",
            ],
            limitations=["Finite scenario evidence; no field accuracy"],
            reproduction="python -m deva.hydraulic_experiment examples/emergency_water_hydraulic.json --seed "
            + str(seed),
        ),
        dict(
            id="claim:heldout",
            claim=f'{selected["id"]} failed {selected["heldout"]["metrics"]["failures"]}/{test_count} fresh hydraulic trials',
            status="EMPIRICAL_ESTIMATE",
            evidence=["candidates/" + selected["id"] + "/heldout"],
            confidence=selected["heldout"]["metrics"]["failure_rate_wilson_95"],
            assumptions=[
                "Synthetic IID scenario generator; held-out stream excluded from selection"
            ],
            limitations=[
                "Aleatoric variability conditional on model; epistemic envelope not included in Wilson CI"
            ],
            reproduction="Same seeded CLI; exact scientific payload hash",
        ),
        dict(
            id="claim:topology",
            claim=formal[0]["property"],
            status=formal[0]["status"],
            evidence=["verification_objects/0"],
            assumptions=formal[0]["assumptions"],
            limitations=formal[0]["limitations"],
            reproduction="Replay stored SMT-LIB with Z3; inspect proof object",
        ),
    ]
    from .cascade import protective_cascade

    cascade = protective_cascade(
        raw,
        selected["diameters_m"],
        dict(closed=["east-trunk"]),
        {"west-trunk": {"value": 0.5, "unit": "m/s"}},
    )
    science = dict(
        cascade=cascade,
        schema_version="3.0",
        model_version=VERSION,
        configuration=raw,
        experiment_config=dict(
            seed=seed,
            generations=generations,
            train_count=train_count,
            validation_count=validation_count,
            test_count=test_count,
        ),
        code=provenance_revision(),
        software=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            scipy=scipy.__version__,
            solver="scipy.optimize.least_squares",
            formal_tool=formal[0]["tool"],
        ),
        seeds=seeds,
        scenarios=dict(
            training=training, validation=validation, heldout=test, declared=declared
        ),
        candidates=candidates,
        recommendation=selected["id"],
        selection_policy="Cheapest with training failure <=10% and all declared tests; otherwise least training failure then cost. Frozen before test generation.",
        stopping="Fixed generation/diameter catalogue budget; no global optimality claim",
        training_frontier=f,
        resilience_frontier=dict(
            heldout_frontier=audit_frontier,
            marginal_segments=segments,
            requested_levels=levels,
            scope="Descriptive held-out frontier; not permitted as further optimisation data",
        ),
        optimisation_history=history,
        adversarial=search,
        uncertainty=dict(
            aleatoric="Synthetic IID demand, head and correlated outage variability; Wilson intervals conditional on fixed geometry/friction model",
            epistemic="Fixed factor and boundary-head sensitivity envelope; no probability distribution or credible interval claimed",
            epistemic_sweep=epistemic,
        ),
        timeline=times,
        verification_objects=formal,
        claim_ledger=claims,
        limitations=[
            "Uncalibrated fixed Darcy friction; no Reynolds-dependent friction",
            "Pressure heads, not mechanical pipe stresses",
            "Source supply constraints checked rather than pressure-regulated pumps",
            "Storage explicit first-order mixed tank; no physical rupture cascade",
            "Historical capacity designs have no geometry; no retroactive hydraulic approval",
            "Finite catalogue heuristic, empirical frontier, no global optimum or field certification",
        ],
    )
    return envelope(science)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("problem")
    p.add_argument("--seed", type=int, default=20261020)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    result = experiment(json.loads(Path(a.problem).read_text()), seed=a.seed)
    Path(a.output).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            dict(
                experiment_id=result["experiment_id"],
                recommendation=result["science"]["recommendation"],
            )
        )
    )
