"""Pressure-dependent, signed-flow Darcy–Weisbach model with explicit SI boundaries.

This is an uncalibrated extended-period research model, not a transient solver.
All recorded states satisfy independent continuity and pipe-energy residual checks.
"""

import math
from copy import deepcopy
import numpy as np
from scipy.optimize import least_squares
from .units import si
from .schema import keys

VERSION = "hydraulic-pdd-darcy-0.3.0"
G = 9.80665
MASS_TOL = 1e-8
ENERGY_TOL = 1e-6


def parse(raw):
    keys(
        raw,
        [
            "id",
            "objective",
            "nodes",
            "pipes",
            "sources",
            "target",
            "minimum_pressure",
            "full_service_pressure",
            "maximum_velocity",
            "budget",
            "diameter_options",
        ],
    )
    if not isinstance(raw["id"], str) or not isinstance(raw["objective"], str):
        raise ValueError("Identifiers required")
    if not isinstance(raw["nodes"], list) or not 2 <= len(raw["nodes"]) <= 30:
        raise ValueError("Require 2–30 hydraulic nodes")
    nodes = []
    for n in raw["nodes"]:
        keys(n, ["id", "elevation", "demand"])
        if not isinstance(n["id"], str) or not 1 <= len(n["id"]) <= 100:
            raise ValueError("Invalid node")
        d = si(n["demand"], "m3/s")
        z = si(n["elevation"], "m")
        if d < 0:
            raise ValueError("Negative demand")
        nodes.append(dict(id=n["id"], z=z, demand=d))
    names = [n["id"] for n in nodes]
    if len(set(names)) != len(names) or sum(n["demand"] for n in nodes) <= 0:
        raise ValueError("Unique nodes and positive demand required")
    if not isinstance(raw["pipes"], list) or not 1 <= len(raw["pipes"]) <= 60:
        raise ValueError("Require 1–60 pipes")
    pipes = []
    for e in raw["pipes"]:
        keys(
            e,
            [
                "id",
                "tail",
                "head",
                "length",
                "friction_factor",
                "cost_per_m_at_100mm",
                "corridor",
            ],
        )
        if e["tail"] not in names or e["head"] not in names or e["tail"] == e["head"]:
            raise ValueError("Invalid endpoints")
        if not isinstance(e["id"], str) or not isinstance(e["corridor"], str):
            raise ValueError("Invalid pipe identifier")
        length = si(e["length"], "m", True)
        friction = si(e["friction_factor"], "1", True)
        cost = e["cost_per_m_at_100mm"]
        if (
            isinstance(cost, bool)
            or not isinstance(cost, (int, float))
            or not math.isfinite(cost)
            or cost <= 0
            or not 0.001 <= friction <= 0.2
        ):
            raise ValueError("Invalid friction or cost")
        pipes.append(
            dict(
                id=e["id"],
                tail=e["tail"],
                head=e["head"],
                length=length,
                friction=friction,
                cost_per_m=float(cost),
                corridor=e["corridor"],
            )
        )
    if len({e["id"] for e in pipes}) != len(pipes):
        raise ValueError("Duplicate pipes")
    sources = {}
    for s in raw["sources"]:
        keys(s, ["node", "head", "maximum_supply"])
        if (
            s["node"] not in names
            or s["node"] in sources
            or next(n for n in nodes if n["id"] == s["node"])["demand"] > 0
        ):
            raise ValueError("Invalid source boundary")
        sources[s["node"]] = dict(
            head=si(s["head"], "m"),
            maximum_supply=si(s["maximum_supply"], "m3/s", True),
        )
    if not sources:
        raise ValueError("Source boundary required")
    pmin = si(raw["minimum_pressure"], "m")
    pfull = si(raw["full_service_pressure"], "m")
    vmax = si(raw["maximum_velocity"], "m/s", True)
    if not 0 <= pmin < pfull:
        raise ValueError("Pressure requirements invalid")
    target = raw["target"]
    budget = raw["budget"]
    if (
        any(
            isinstance(v, bool)
            or not isinstance(v, (int, float))
            or not math.isfinite(v)
            for v in [target, budget]
        )
        or not 0 < target <= 1
        or budget <= 0
    ):
        raise ValueError("Invalid target/budget")
    options = [si(q, "m", True) for q in raw["diameter_options"]]
    if (
        not options
        or len(options) > 12
        or any(not 0.01 <= d <= 2 for d in options)
        or options != sorted(set(options))
    ):
        raise ValueError("Sorted unique diameter catalogue required")
    return dict(
        nodes=nodes,
        pipes=pipes,
        sources=sources,
        pmin=pmin,
        pfull=pfull,
        vmax=vmax,
        target=target,
        budget=budget,
        options=options,
    )


def cost(model, diameters):
    return sum(
        e["length"] * e["cost_per_m"] * (d / 0.1) ** 1.5
        for e, d in zip(model["pipes"], diameters)
    )


def delivered(pressure, requested, pfull):
    # Wagner-style pressure-dependent service, zero pressure cut-off and exponent 1/2.
    return requested * np.sqrt(np.clip(np.asarray(pressure) / pfull, 0, 1))


def simulate(raw, diameters, scenario=None):
    model = parse(raw)
    scenario = deepcopy(scenario or {})
    allowed = {
        "id",
        "closed",
        "demand_factor",
        "source_head_delta_m",
        "friction_factor",
        "source_losses",
        "head_overrides_m",
    }
    if set(scenario) - allowed:
        raise ValueError("Unknown hydraulic disturbance")
    nodes = model["nodes"]
    pipes = model["pipes"]
    names = [n["id"] for n in nodes]
    ids = [p["id"] for p in pipes]
    if len(diameters) != len(pipes) or any(
        isinstance(d, bool)
        or not isinstance(d, (int, float))
        or not math.isfinite(d)
        or not 0.01 <= d <= 2
        for d in diameters
    ):
        raise ValueError("Invalid SI diameters")
    closed = scenario.get("closed", [])
    lost = scenario.get("source_losses", [])
    if (
        not isinstance(closed, list)
        or len(set(closed)) != len(closed)
        or set(closed) - set(ids)
        or not isinstance(lost, list)
        or set(lost) - set(model["sources"])
    ):
        raise ValueError("Invalid outage set")
    factor = scenario.get("demand_factor", 1.0)
    friction = scenario.get("friction_factor", 1.0)
    delta = scenario.get("source_head_delta_m", 0.0)
    if (
        any(
            isinstance(v, bool)
            or not isinstance(v, (int, float))
            or not math.isfinite(v)
            for v in [factor, friction, delta]
        )
        or not 0 < factor <= 3
        or not 0.5 <= friction <= 2
        or abs(delta) > 100
    ):
        raise ValueError("Invalid uncertainty parameters")
    overrides = scenario.get("head_overrides_m", {})
    if (
        not isinstance(overrides, dict)
        or set(overrides) - set(model["sources"])
        or any(
            not isinstance(v, (int, float))
            or isinstance(v, bool)
            or not math.isfinite(v)
            for v in overrides.values()
        )
    ):
        raise ValueError("Invalid head boundaries")
    fixed = {
        n: overrides.get(n, s["head"] + delta)
        for n, s in model["sources"].items()
        if n not in lost
    }
    active = [j for j, e in enumerate(pipes) if e["id"] not in closed]
    reachable = set(fixed)
    while True:
        grown = (
            reachable
            | {pipes[j]["head"] for j in active if pipes[j]["tail"] in reachable}
            | {pipes[j]["tail"] for j in active if pipes[j]["head"] in reachable}
        )
        if grown == reachable:
            break
        reachable = grown
    # Unanchored islands have no water source. Equal arbitrary datum head <= min elevation,
    # zero demand and zero flow: no spurious service or fabricated absolute island pressure.
    free = [n for n in names if n in reachable and n not in fixed]
    connected = [j for j in active if pipes[j]["tail"] in reachable]
    m = len(connected)
    B = np.zeros((len(free), m))
    for k, j in enumerate(connected):
        e = pipes[j]
        if e["tail"] in free:
            B[free.index(e["tail"]), k] = -1
        if e["head"] in free:
            B[free.index(e["head"]), k] = 1
    elevations = {n["id"]: n["z"] for n in nodes}
    requested = {n["id"]: n["demand"] * factor for n in nodes}
    resistance = np.array(
        [
            8
            * pipes[j]["friction"]
            * friction
            * pipes[j]["length"]
            / (G * math.pi**2 * diameters[j] ** 5)
            for j in connected
        ]
    )
    qscale = max(sum(requested.values()), 0.001)
    hscale = max(max(fixed.values(), default=1), model["pfull"], 1.0)

    def unpack(x):
        return {**fixed, **dict(zip(free, x[m:] * hscale))}, x[:m] * qscale

    def residual(x):
        h, q = unpack(x)
        d = delivered(
            [h[n] - elevations[n] for n in free],
            np.array([requested[n] for n in free]),
            model["pfull"],
        )
        energy = np.array(
            [h[pipes[j]["tail"]] - h[pipes[j]["head"]] for j in connected]
        ) - resistance * q * np.abs(q)
        return np.r_[(B @ q - d) / qscale, energy / hscale]

    if m or free:
        zero_equilibrium = len(set(fixed.values())) == 1 and max(fixed.values()) <= min(
            elevations.values()
        )
        initial = np.r_[
            np.full(m, 0.0 if zero_equilibrium else 0.5 / max(m, 1)),
            np.full(len(free), np.mean(list(fixed.values())) / hscale),
        ]
        solution = least_squares(
            residual, initial, xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=2000
        )
        h, q = unpack(solution.x)
        converged = bool(solution.success)
        evaluations = int(solution.nfev)
    else:
        h, q = fixed, np.array([])
        converged = True
        evaluations = 0
    flows = np.zeros(len(pipes))
    for j, value in zip(connected, q):
        flows[j] = value
    pressures = {
        n: (float(h[n] - elevations[n]) if n in reachable else None) for n in names
    }
    service = {
        n: (
            float(delivered([pressures[n] or 0.0], [requested[n]], model["pfull"])[0])
            if n in reachable
            else 0.0
        )
        for n in names
    }
    heads = {n: (float(h[n]) if n in reachable else None) for n in names}
    injections = {
        n: float(
            sum(flows[j] for j, e in enumerate(pipes) if e["tail"] == n)
            - sum(flows[j] for j, e in enumerate(pipes) if e["head"] == n)
        )
        for n in fixed
    }
    mass = float(
        max(
            [
                abs(
                    sum(flows[j] for j, e in enumerate(pipes) if e["head"] == n)
                    - sum(flows[j] for j, e in enumerate(pipes) if e["tail"] == n)
                    - service[n]
                )
                for n in free
            ],
            default=0,
        )
    )
    energy = float(
        max(
            [
                abs(
                    h[pipes[j]["tail"]]
                    - h[pipes[j]["head"]]
                    - r * flows[j] * abs(flows[j])
                )
                for j, r in zip(connected, resistance)
            ],
            default=0,
        )
    )
    if not converged or mass > MASS_TOL or energy > ENERGY_TOL:
        raise RuntimeError(
            f"Hydraulic convergence failed: continuity={mass}, energy={energy}"
        )
    velocities = [float(4 * f / (math.pi * d * d)) for f, d in zip(flows, diameters)]
    demand_nodes = [n for n in names if requested[n] > 0]
    sf = min(service[n] / requested[n] for n in demand_nodes)
    requirements = {
        "service": sf >= model["target"] - 1e-7,
        "pressure": all(
            pressures[n] is not None and pressures[n] >= model["pmin"] - 1e-6
            for n in demand_nodes
        ),
        "velocity": all(abs(v) <= model["vmax"] + 1e-7 for v in velocities),
        "source_supply": all(
            -MASS_TOL <= v <= model["sources"][n]["maximum_supply"] + MASS_TOL
            for n, v in injections.items()
        ),
        "budget": cost(model, diameters) <= model["budget"] + 1e-7,
    }
    return dict(
        scenario_id=scenario.get("id", "nominal"),
        model_version=VERSION,
        head_m=heads,
        pressure_head_m=pressures,
        flow_m3s=flows.tolist(),
        velocity_ms=velocities,
        requested_m3s=requested,
        delivered_m3s=service,
        boundary_injection_m3s=injections,
        disconnected_nodes=sorted(set(names) - reachable),
        service_fraction=float(sf),
        requirements=requirements,
        passes=all(requirements.values()),
        mass_residual_m3s=mass,
        energy_residual_m=energy,
        solver_evaluations=evaluations,
        scope="Numerically validated PDD steady state; uncalibrated fixed Darcy factors, prescribed reservoir heads; source limits checked, not regulated; disconnected absolute heads untested",
    )


def timeline(raw, diameters, tank, steps, dt_seconds, events=None):
    """Explicit conservative tank integration; every frame is a fresh hydraulic solve.

    Piecewise-constant exogenous demands/events, mixed well tank and quasi-steady pipes.
    Exact empty/full clipping shortens integration interval; no water-hammer dynamics.
    """
    keys(
        tank,
        ["node", "area", "initial_volume", "maximum_volume", "base_head", "inflow"],
    )
    model = parse(raw)
    node = tank["node"]
    if node not in model["sources"]:
        raise ValueError("Tank must be explicit source boundary")
    area = si(tank["area"], "m2", True)
    volume = si(tank["initial_volume"], "m3")
    maximum = si(tank["maximum_volume"], "m3", True)
    base = si(tank["base_head"], "m")
    inflow = si(tank["inflow"], "m3/s")
    if (
        not 0 <= volume <= maximum
        or inflow < 0
        or isinstance(steps, bool)
        or not isinstance(steps, int)
        or not 1 <= steps <= 500
        or not math.isfinite(dt_seconds)
        or not 0 < dt_seconds <= 3600
    ):
        raise ValueError("Invalid temporal configuration")
    events = events or []
    if any(
        set(e) != {"step", "scenario"}
        or not isinstance(e["step"], int)
        or not 0 <= e["step"] <= steps
        for e in events
    ):
        raise ValueError("Invalid event steps")
    frames = []
    time_s = 0.0
    scenario = {}
    cumulative = 0.0
    spilled = 0.0
    initial_volume = volume
    for index in range(steps + 1):
        markers = []
        for event in events:
            if event["step"] == index:
                scenario = deepcopy(event["scenario"])
                markers.append("disturbance_change")
        state_scenario = deepcopy(scenario)
        state_scenario["id"] = f"time:{index}"
        state_scenario["head_overrides_m"] = {
            **state_scenario.get("head_overrides_m", {}),
            node: base + volume / area,
        }
        # At empty volume the tank outlet is closed; inflow continues to refill.
        if volume <= 1e-12:
            state_scenario["source_losses"] = list(
                set(state_scenario.get("source_losses", [])) | {node}
            )
            markers.append("tank_empty")
        result = simulate(raw, diameters, state_scenario)
        rate = inflow - result["boundary_injection_m3s"].get(node, 0.0)
        actual_dt = dt_seconds
        if rate < 0 and volume + rate * actual_dt < 0:
            actual_dt = volume / -rate
        if index == steps:
            actual_dt = 0.0
        new_volume = volume + rate * actual_dt
        overflow = max(new_volume - maximum, 0.0)
        frames.append(
            dict(
                index=index,
                time_seconds=time_s,
                volume_m3=volume,
                head_m=base + volume / area,
                result=result,
                scenario=state_scenario,
                events=markers,
                interval_seconds=actual_dt,
                net_volume_change_m3=rate * actual_dt,
                overflow_m3=overflow,
            )
        )
        cumulative += rate * actual_dt
        spilled += overflow
        volume = min(max(new_volume, 0.0), maximum)
        time_s += actual_dt
    error = abs(volume - initial_volume - cumulative + spilled)
    return dict(
        model="quasi-steady-tank-euler-0.3.0",
        frames=frames,
        volume_balance_error_m3=error,
        scope="Computed extended-period states; event steps are integration boundaries, shortened intervals stop at empty storage. No interpolation is scientific data; no pipe inertia, water hammer or physical rupture cascade.",
    )
