"""One-way projection of stored twin computation into the existing scientific world."""

from .audit import verify_hash
from .hydraulic_view import render_problem, state
from .hydraulic_v2 import simulate, parse
from .hydraulic_evidence import audit


def project(record):
    verify_hash(record)
    s = record["science"]
    raw = s["configuration"]
    d = s["diameters_m"]
    model = s["digital_twin"]["estimated_model"]
    frames = []
    pipes = parse(raw)["pipes"]

    def gpu(result):
        import math

        return [
            dict(
                pipe_id=p["id"],
                length_m=p["length"],
                signed_velocity_ms=result["velocity_ms"][i],
                flow_m3s=result["flow_m3s"][i],
                particle_count=min(
                    2048, int(math.ceil(abs(result["flow_m3s"][i]) / 0.03 * 2048))
                ),
            )
            for i, p in enumerate(pipes)
        ]

    for label, rows in s["calibration"]["rows"].items():
        conditions = {
            row["observation"]["scenario"]["id"]: row["observation"]["scenario"]
            for row in rows
        }
        for scenario in conditions.values():
            a = simulate(raw, d, scenario)
            b = simulate(model, d, scenario)
            audit(raw, d, scenario, a)
            audit(model, d, scenario, b)
            frames.append(
                dict(
                    id=scenario["id"],
                    split=label,
                    timestamp=next(
                        r["observation"]["timestamp"]
                        for r in rows
                        if r["observation"]["scenario"]["id"] == scenario["id"]
                    ),
                    baseline=state(raw, d, scenario, a),
                    estimated=state(model, d, scenario, b),
                    baseline_gpu=gpu(a),
                    estimated_gpu=gpu(b),
                    observations=[
                        r
                        for r in rows
                        if r["observation"]["scenario"]["id"] == scenario["id"]
                    ],
                )
            )
    cascade = [
        dict(
            index=f["index"],
            time_seconds=f["time_seconds"],
            state=state(model, d, f["scenario"], f["result"]),
            gpu=gpu(f["result"]),
            hazards=f["hazards"],
            events=f["events"],
            newly_failed=f.get("newly_failed", []),
            restored=f.get("restored", []),
        )
        for f in s["cascade"]["frames"]
    ]
    agent = s["engineering_agent"]["science"]
    proof = agent["outputs"].get("verify_property", {})
    agent_candidates = []
    for c in agent["outputs"].get("simulate_training", {}).get("candidates", []):
        r = c["training"]["records"][0]
        actual = r.get("result")
        agent_candidates.append(
            dict(
                id=c["id"],
                parents=c["parents"],
                mutation=c["mutation"],
                cost=c["cost"],
                rejection_reason=c["rejection_reason"],
                training_failures=c["training"]["failures"],
                training_samples=c["training"]["samples"],
                state=(
                    state(
                        agent["effective_configuration"],
                        c["diameters_m"],
                        r["scenario"],
                        actual,
                    )
                    if actual
                    else None
                ),
                gpu=gpu(actual) if actual else None,
            )
        )
    counterexample = None
    if proof.get("counterexample_simulation"):
        r = proof["counterexample_simulation"]["records"][0]
        c = next(
            c
            for c in agent["outputs"]["simulate_training"]["candidates"]
            if c["id"] == agent["selection"]
        )
        if r.get("result"):
            counterexample = dict(
                state=state(
                    agent["effective_configuration"],
                    c["diameters_m"],
                    r["scenario"],
                    r["result"],
                ),
                gpu=gpu(r["result"]),
                scope=proof["scope"],
            )
    selected = next(
        (
            c
            for c in agent["outputs"].get("simulate_training", {}).get("candidates", [])
            if c["id"] == agent["selection"]
        ),
        None,
    )
    failed_cases, unknown_cases = [], []
    for i, row in enumerate(
        agent["outputs"].get("validate_selected", {}).get("records", [])
    ):
        if row["component_passes"]:
            continue
        if not row.get("result") or selected is None:
            unknown_cases.append(
                dict(
                    index=i,
                    scenario=row["scenario"],
                    reason=row.get("unknown_solver_state", "Unknown state"),
                )
            )
            continue
        failed_cases.append(
            dict(
                index=i,
                scenario=row["scenario"],
                component_service=row["component_service"],
                component_pressure_m=row["component_pressure_m"],
                state=state(
                    agent["effective_configuration"],
                    selected["diameters_m"],
                    row["scenario"],
                    row["result"],
                ),
                gpu=gpu(row["result"]),
            )
        )
    return dict(
        experiment_id=record["experiment_id"],
        scientific_sha256=record["scientific_sha256"],
        label=s["dataset"]["label"],
        problem=render_problem(raw),
        frames=frames,
        cascade=cascade,
        causal_graph=s["cascade"]["causal_graph"],
        cascade_events=s["cascade"]["events"],
        ensemble=dict(
            time_seconds=s["ensemble"]["time_seconds"],
            service_percentiles=s["ensemble"]["service_percentiles"],
            terminal_failures=s["ensemble"]["terminal_failures"],
            samples=s["ensemble"]["samples"],
            trajectories=[
                [f["result"]["service_fraction"] for f in t["frames"]]
                for t in s["ensemble"]["trials"]
            ],
            scope=s["ensemble"]["scope"],
        ),
        calibration={
            k: s["calibration"][k]
            for k in (
                "status",
                "parameters",
                "metrics",
                "initial_identifiability",
                "fitted_identifiability",
                "covariance",
                "searches",
                "acceptance_criteria",
                "uncertainty_scope",
            )
        },
        incremental_calibration=s["incremental_calibration"],
        sensor_placement=s["sensor_placement"],
        next_observation=s["next_observation"],
        claim_ledger=s["claim_ledger"],
        provenance_graph=s["provenance_graph"],
        engineering_agent=s["engineering_agent"]["science"],
        verification=proof,
        counterexample=counterexample,
        agent_candidates=agent_candidates,
        failed_cases=failed_cases,
        unknown_cases=unknown_cases,
        knowledge_states=s["digital_twin"]["states"],
        limitations=s["limitations"],
        code=s["code"],
        seed=s["seed"],
    )
