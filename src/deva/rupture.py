"""Uncalibrated phenomenological hazard and quasi-steady stochastic cascades.

This model explores state-dependent failure hypotheses; it does not predict field
pipe rupture, fatigue, fracture mechanics, water hammer or travel-time propagation.
"""

from copy import deepcopy
import math
import numpy as np
from .hydraulic_v2 import parse, simulate
from .hydraulic_evidence import audit

VERSION = "hydraulic-hazard-cascade-0.4.0"


def hazard(pressure_m, velocity_ms, policy):
    required = {
        "base_rate_per_second",
        "stress_rate_per_second",
        "reference_pressure_m",
        "reference_velocity_ms",
        "degradation",
    }
    if set(policy) != required or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in policy.values()
    ):
        raise ValueError("Finite explicitly unit-named hazard policy required")
    if (
        not 0 <= policy["base_rate_per_second"] <= 0.01
        or not 0 <= policy["stress_rate_per_second"] <= 0.01
        or not 0 < policy["reference_pressure_m"] <= 200
        or not 0 < policy["reference_velocity_ms"] <= 10
        or not 0 <= policy["degradation"] <= 10
    ):
        raise ValueError("Hazard parameters outside bounded research domain")
    if (
        pressure_m is not None
        and not math.isfinite(pressure_m)
        or not math.isfinite(velocity_ms)
    ):
        raise ValueError("Finite state or explicitly unknown pressure required")
    pressure_excess = max(0, (pressure_m or 0) / policy["reference_pressure_m"] - 1)
    velocity_excess = max(0, abs(velocity_ms) / policy["reference_velocity_ms"] - 1)
    rate = policy["base_rate_per_second"] * (1 + policy["degradation"]) + policy[
        "stress_rate_per_second"
    ] * (pressure_excess**2 + velocity_excess**2) * (1 + policy["degradation"])
    return dict(
        rate_per_second=rate,
        pressure_excess=pressure_excess,
        velocity_excess=velocity_excess,
        pressure_known=pressure_m is not None,
        scope="Uncalibrated research hypothesis, not material rupture prediction",
    )


def policies(raw):
    return {
        p["id"]: dict(
            base_rate_per_second=0.00001,
            stress_rate_per_second=0.003,
            reference_pressure_m=50.0,
            reference_velocity_ms=0.8,
            degradation=0.0,
        )
        for p in parse(raw)["pipes"]
    }


def cascade(
    raw,
    diameters,
    initial,
    policy,
    seed=20261040,
    steps=12,
    dt_seconds=60.0,
    repairs=None,
):
    m = parse(raw)
    ids = [p["id"] for p in m["pipes"]]
    if (
        set(policy) != set(ids)
        or not isinstance(steps, int)
        or not 1 <= steps <= 100
        or isinstance(steps, bool)
        or isinstance(dt_seconds, bool)
        or not 0 < dt_seconds <= 3600
        or not math.isfinite(dt_seconds)
    ):
        raise ValueError("One hazard policy per pipe and bounded timeline required")
    for p in policy.values():
        hazard(0, 0, p)
    repair_schedule = repairs or {}
    for step, components in repair_schedule.items():
        if (
            not isinstance(step, int)
            or not 1 <= step <= steps
            or not set(components) <= set(ids)
        ):
            raise ValueError(
                "Repairs require known components at explicit future steps"
            )
    initial = deepcopy(initial)
    initial.setdefault("id", "initial-disturbance")
    closed = set(initial.get("closed", []))
    reference = simulate(
        raw, diameters, dict(initial, closed=[], id="counterfactual:no-initial-outage")
    )
    audit(
        raw,
        diameters,
        dict(initial, closed=[], id="counterfactual:no-initial-outage"),
        reference,
    )
    rng = np.random.default_rng(seed)
    frames = []
    events = []
    nodes = []
    edges = []

    def compute(step):
        scenario = dict(initial, id=f"cascade:{seed}:{step}", closed=sorted(closed))
        state = simulate(raw, diameters, scenario)
        audit(raw, diameters, scenario, state)
        return scenario, state

    scenario, state = compute(0)
    nodes.append(
        dict(id="initial", kind="DISTURBANCE", closed=sorted(closed), scenario=initial)
    )
    frames.append(
        dict(
            index=0,
            time_seconds=0.0,
            scenario=scenario,
            result=state,
            events=[],
            hazards={},
        )
    )
    for step in range(1, steps + 1):
        previous = deepcopy(state)
        hazards = {}
        new = []
        node_id = f"hydraulic:{step}"
        nodes.append(
            dict(
                id=node_id,
                kind="HYDRAULIC STATE",
                frame=step - 1,
                service_fraction=previous["service_fraction"],
            )
        )
        edges.append(
            dict(
                source="initial" if step == 1 else f"hydraulic:{step-1}",
                target=node_id,
                evidence=f"frames/{step-1}/result",
                scope="Recomputed state under accumulated failures, not an inferred field causal effect",
            )
        )
        for prior_event in frames[-1]["events"]:
            if prior_event.startswith("failure:"):
                edges.append(
                    dict(
                        source=prior_event,
                        target=node_id,
                        evidence=f"frames/{step-1}/scenario/closed",
                        scope="Recorded closure enters the subsequent hydraulic solve",
                    )
                )
        for j, p in enumerate(m["pipes"]):
            name = p["id"]
            if name in closed:
                continue
            pressures = [previous["pressure_head_m"][n] for n in (p["tail"], p["head"])]
            pressure = max((v for v in pressures if v is not None), default=None)
            h = hazard(pressure, previous["velocity_ms"][j], policy[name])
            ref_pressure = max(
                (
                    reference["pressure_head_m"][n]
                    for n in (p["tail"], p["head"])
                    if reference["pressure_head_m"][n] is not None
                ),
                default=None,
            )
            baseline = hazard(ref_pressure, reference["velocity_ms"][j], policy[name])
            probability = -math.expm1(-h["rate_per_second"] * dt_seconds)
            draw = float(rng.random())
            h.update(
                probability=probability,
                uniform_draw=draw,
                counterfactual_reference_rate=baseline["rate_per_second"],
                hazard_change=h["rate_per_second"] - baseline["rate_per_second"],
                velocity_ms=previous["velocity_ms"][j],
                pressure_m=pressure,
            )
            hazards[name] = h
            if draw < probability:
                new.append(name)
                event_id = f"failure:{step}:{name}"
                event = dict(
                    id=event_id,
                    simulation_time_seconds=step * dt_seconds,
                    component=name,
                    event="RESEARCH HAZARD FAILURE",
                    pre_event_state=dict(
                        pressure_m=pressure, velocity_ms=previous["velocity_ms"][j]
                    ),
                    trigger=h,
                    policy=policy[name],
                    scope="Seeded hazard draw, uncalibrated rupture hypothesis",
                )
                events.append(event)
                nodes.append(dict(id=event_id, kind="FAILURE", event=event))
                edges.append(
                    dict(
                        source=node_id,
                        target=event_id,
                        evidence=f"frames/{step}/hazards/{name}",
                        scope="Computed hazard probability and recorded draw",
                    )
                )
        closed.update(new)
        restored = [p for p in repair_schedule.get(step, []) if p in closed]
        closed.difference_update(restored)
        for p in restored:
            events.append(
                dict(
                    id=f"repair:{step}:{p}",
                    simulation_time_seconds=step * dt_seconds,
                    component=p,
                    event="EXOGENOUS REPAIR",
                    scope="Explicit external maintenance schedule, not spontaneous recovery",
                )
            )
        scenario, state = compute(step)
        for name in new:
            e = next(
                e
                for e in reversed(events)
                if e["event"] == "RESEARCH HAZARD FAILURE" and e["component"] == name
            )
            e["resulting_state"] = dict(
                frame=step,
                service_fraction=state["service_fraction"],
                closed=sorted(closed),
            )
            consequence = f"consequence:{step}:{name}"
            nodes.append(
                dict(
                    id=consequence,
                    kind="SERVICE CONSEQUENCE",
                    frame=step,
                    service_fraction=state["service_fraction"],
                    requirements=state["requirements"],
                )
            )
            edges.append(
                dict(
                    source=e["id"],
                    target=consequence,
                    evidence=f"frames/{step}/result",
                    scope="Joint post-event state; simultaneous failures cannot be uniquely attributed",
                )
            )
        frames.append(
            dict(
                index=step,
                time_seconds=step * dt_seconds,
                scenario=scenario,
                result=state,
                events=[
                    e["id"]
                    for e in events
                    if e["simulation_time_seconds"] == step * dt_seconds
                ],
                newly_failed=new,
                restored=restored,
                hazards=hazards,
            )
        )
    return dict(
        model_version=VERSION,
        seed=seed,
        dt_seconds=dt_seconds,
        policy=policy,
        initial=initial,
        frames=frames,
        events=events,
        causal_graph=dict(nodes=nodes, edges=edges),
        terminal=dict(
            closed=sorted(closed),
            service_fraction=state["service_fraction"],
            passes=state["passes"],
        ),
        response=(
            "ACTIVE EXOGENOUS MAINTENANCE"
            if repairs
            else "PASSIVE HYDRAULIC REDISTRIBUTION"
        ),
        limitations=[
            "Uncalibrated hazard coefficients; no field rupture reliability claim.",
            "Quasi-steady hydraulic solves; no transient pressure waves or physical propagation timing.",
            "Interval-end Bernoulli failures use pre-interval hazards; step-size dependence must be examined.",
            "Pipe closure approximation omits leakage before isolation and repair resources.",
            "Simultaneous consequences are jointly computed, not unique causal attribution.",
        ],
    )


def ensemble(raw, diameters, initial, policy, seed=20261041, count=20, steps=12):
    if not 2 <= count <= 100:
        raise ValueError("Bounded ensemble size required")
    seeds = [
        int(s.generate_state(1)[0]) for s in np.random.SeedSequence(seed).spawn(count)
    ]
    trials = [cascade(raw, diameters, initial, policy, s, steps) for s in seeds]
    a = np.array(
        [[f["result"]["service_fraction"] for f in t["frames"]] for t in trials]
    )
    return dict(
        seed=seed,
        seeds=seeds,
        trials=trials,
        time_seconds=[f["time_seconds"] for f in trials[0]["frames"]],
        service_percentiles={
            str(p): np.percentile(a, p, axis=0).tolist() for p in (5, 50, 95)
        },
        terminal_failures=sum(not t["terminal"]["passes"] for t in trials),
        samples=count,
        scope="Conditional research-hazard ensemble, not observed field failure probability",
    )
