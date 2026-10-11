"""Optional operational excess-flow isolation cascade, not physical pipe rupture.

An explicit synthetic protective-valve rule closes selected pipes whose computed
velocity exceeds their configured trip setpoint. Recompute hydraulics after each
simultaneous trip round; retain every intermediate solve. No invented time delay.
"""

from copy import deepcopy
from .hydraulic_v2 import parse, simulate
from .hydraulic_evidence import audit
from .units import si


def protective_cascade(raw, diameters, scenario, trip_setpoints):
    model = parse(raw)
    ids = [e["id"] for e in model["pipes"]]
    if (
        not isinstance(trip_setpoints, dict)
        or not trip_setpoints
        or set(trip_setpoints) - set(ids)
    ):
        raise ValueError("Explicit protective valve setpoints required")
    limits = {k: si(v, "m/s", True) for k, v in trip_setpoints.items()}
    state = deepcopy(scenario)
    closed = set(state.get("closed", []))
    trace = []
    for iteration in range(len(ids) + 1):
        current = {
            **state,
            "closed": sorted(closed),
            "id": f"protective-round:{iteration}",
        }
        result = simulate(raw, diameters, current)
        audit(raw, diameters, current, result)
        trips = [
            e["id"]
            for e, v in zip(model["pipes"], result["velocity_ms"])
            if e["id"] in limits
            and e["id"] not in closed
            and abs(v) > limits[e["id"]] + 1e-7
        ]
        trace.append(
            dict(
                round=iteration,
                scenario=current,
                result=result,
                newly_closed=trips,
                causes=[
                    dict(
                        pipe=e["id"],
                        computed_velocity_ms=abs(v),
                        trip_setpoint_ms=limits[e["id"]],
                        rule="abs(velocity) > explicit excess-flow setpoint",
                    )
                    for e, v in zip(model["pipes"], result["velocity_ms"])
                    if e["id"] in trips
                ],
            )
        )
        if not trips:
            break
        closed.update(trips)
    return dict(
        model="experimental-excess-flow-isolation-0.3.0",
        initial_disturbance=scenario,
        trip_setpoints=trip_setpoints,
        rounds=trace,
        terminal_closed=sorted(closed),
        terminated=True,
        scope="State-dependent cascade of operational valve isolation, conditional on explicit synthetic setpoints. No physical rupture, mechanical stress, calibrated device response or transition-time prediction. Closed pipes do not reopen automatically.",
    )
