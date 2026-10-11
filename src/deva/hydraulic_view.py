"""Explicit SI-to-display projection; browser receives physics without solving it."""

from .hydraulic_v2 import parse, cost
from .units import Quantity


def render_problem(raw):
    m = parse(raw)
    return dict(
        id=raw["id"],
        objective=raw["objective"],
        nodes=[n["id"] for n in m["nodes"]],
        supply={
            n: Quantity.of(s["maximum_supply"], "m3/s").to("m3/h")
            for n, s in m["sources"].items()
        },
        demand={
            n["id"]: Quantity.of(n["demand"], "m3/s").to("m3/h")
            for n in m["nodes"]
            if n["demand"]
        },
        budget=m["budget"],
        target=m["target"],
        edges=[
            dict(
                id=e["id"],
                tail=e["tail"],
                head=e["head"],
                unit_cost=e["cost_per_m"],
                max_capacity=1000.0,
                corridor=e["corridor"],
            )
            for e in m["pipes"]
        ],
    )


def state(raw, diameters, scenario, result):
    import math

    m = parse(raw)
    names = [n["id"] for n in m["nodes"]]
    total = sum(result["requested_m3s"].values())
    delivery = sum(result["delivered_m3s"].values())
    c = cost(m, diameters)
    return dict(
        scenario=dict(
            id=result["scenario_id"],
            availability=[
                0.0 if e["id"] in scenario.get("closed", []) else 1.0
                for e in m["pipes"]
            ],
            demand_factor=scenario.get("demand_factor", 1.0),
            supply_factor=1.0,
        ),
        result=dict(
            scenario_id=result["scenario_id"],
            flow=[Quantity.of(v, "m3/s").to("m3/h") for v in result["flow_m3s"]],
            injection=[
                Quantity.of(result["boundary_injection_m3s"].get(n, 0.0), "m3/s").to(
                    "m3/h"
                )
                for n in names
            ],
            delivered=[
                Quantity.of(result["delivered_m3s"][n], "m3/s").to("m3/h")
                for n in names
            ],
            demand=[
                Quantity.of(result["requested_m3s"][n], "m3/s").to("m3/h")
                for n in names
            ],
            service_fraction=result["service_fraction"],
            passes=result["passes"],
            max_residual=result["mass_residual_m3s"],
        ),
        candidate=dict(
            id="hydraulic-frame",
            parents=[],
            generation=0,
            mutations=[],
            capacities=[
                Quantity.of(m["vmax"] * math.pi * d * d / 4, "m3/s").to("m3/h")
                for d in diameters
            ],
            cost=c,
            disposition="hydraulic_evaluated",
            rejection_reason=None,
            verification=dict(
                level="STRESS TESTED",
                requirements_pass=result["passes"],
                formal_verification=False,
                scope="Property-specific numerical hydraulic evaluation; topology proof separate",
                budget_margin=m["budget"] - c,
            ),
            splits={},
            visual_fields=[],
        ),
        hydraulic=dict(
            pressure_head_m=result["pressure_head_m"],
            head_m=result["head_m"],
            diameters_m=diameters,
            velocity_ms=result["velocity_ms"],
            requirements=result["requirements"],
            requested_m3s=result["requested_m3s"],
            delivered_m3s=result["delivered_m3s"],
            minimum_pressure_m=m["pmin"],
            full_service_pressure_m=m["pfull"],
            energy_residual_m=result["energy_residual_m"],
            mass_residual_m3s=result["mass_residual_m3s"],
        ),
    )


def project(envelope):
    s = envelope["science"]
    raw = s["configuration"]
    candidates = []
    for c in s["candidates"]:
        states = {}
        for split in ["declared", "training", "validation", "heldout"]:
            states[split] = [
                (
                    state(raw, c["diameters_m"], scenario, r)
                    if r.get("service_fraction") is not None
                    else None
                )
                for scenario, r in zip(s["scenarios"][split], c[split]["results"])
            ]
        candidates.append(
            dict(
                id=c["id"],
                parents=c["parents"],
                generation=c["generation"],
                mutation=c["mutation"],
                cost=c["cost"],
                diameters_m=c["diameters_m"],
                rejection_reason=c["rejection_reason"],
                states=states,
                metrics={k: c[k]["metrics"] for k in states},
            )
        )
    selected = next(c for c in s["candidates"] if c["id"] == s["recommendation"])
    frames = [
        dict(
            **{k: v for k, v in f.items() if k != "result"},
            state=state(raw, selected["diameters_m"], {}, f["result"]),
        )
        for f in s["timeline"]["frames"]
    ]
    # Recover actual temporal closed set from zero-flow is unsafe; preserve scenarios directly.
    for f, original in zip(frames, s["timeline"]["frames"]):
        if "scenario" in original:
            f["state"] = state(
                raw, selected["diameters_m"], original["scenario"], original["result"]
            )
    cascades = [
        dict(
            round=r["round"],
            newly_closed=r["newly_closed"],
            causes=r["causes"],
            state=state(raw, selected["diameters_m"], r["scenario"], r["result"]),
        )
        for r in s["cascade"]["rounds"]
    ]
    return dict(
        adversarial_scenario=s["adversarial"]["continuous_worst"]["scenario"],
        causal_trace=causal_trace(
            raw,
            s["adversarial"]["continuous_worst"]["scenario"],
            s["adversarial"]["continuous_worst"]["result"],
        ),
        experiment_id=envelope["experiment_id"],
        scientific_sha256=envelope["scientific_sha256"],
        problem=render_problem(raw),
        configuration=raw,
        recommendation=s["recommendation"],
        candidates=candidates,
        frames=frames,
        cascade=cascades,
        frontier=s["resilience_frontier"],
        verification_objects=s["verification_objects"],
        claim_ledger=s["claim_ledger"],
        uncertainty=s["uncertainty"],
        code=s["code"],
        seeds=s["seeds"],
        limitations=s["limitations"],
    )


def causal_trace(raw, scenario, result):
    """Observed linked facts, not a claim of uniquely identified physical causality."""
    m = parse(raw)
    items = []
    for pipe in scenario.get("closed", []):
        items.append(
            dict(
                component=pipe,
                event="imposed_pipe_outage",
                evidence="scenario.closed",
                value=0.0,
                unit="available fraction",
            )
        )
    for node in result["disconnected_nodes"]:
        items.append(
            dict(
                component=node,
                event="no_active_source_path",
                evidence="computed connectivity",
                value=None,
                unit=None,
            )
        )
    for n in m["nodes"]:
        if not n["demand"]:
            continue
        name = n["id"]
        p = result["pressure_head_m"][name]
        if p is not None and p < m["pmin"]:
            items.append(
                dict(
                    component=name,
                    event="pressure_requirement_violated",
                    evidence="result.pressure_head_m",
                    value=p,
                    unit="m pressure head",
                )
            )
        ratio = result["delivered_m3s"][name] / result["requested_m3s"][name]
        if ratio < m["target"]:
            items.append(
                dict(
                    component=name,
                    event="service_requirement_violated",
                    evidence="pressure-dependent delivery / requested demand",
                    value=ratio,
                    unit="fraction",
                )
            )
    return dict(
        facts=items,
        scope="Observed disturbance → computed connectivity/pressure → computed delivery → requirement violation. Not unique causal attribution; no fabricated travel or propagation time.",
    )
