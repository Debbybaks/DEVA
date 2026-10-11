"""Uncertainty-weighted hydraulic parameter inference, not field certification."""

from copy import deepcopy
from datetime import datetime
from itertools import combinations
import math
import numpy as np
from scipy.optimize import least_squares
from .units import Quantity, si
from .hydraulic_v2 import parse, simulate
from .hydraulic_evidence import audit

VERSION = "hydraulic-calibration-0.4.0"
MEASUREMENTS = {
    "pressure": "m",
    "flow": "m3/s",
    "source_output": "m3/s",
    "service": "1",
}


def observations(raw, records):
    """Validate observation identities, dimensions, known excitation and provenance."""
    m = parse(raw)
    nodes = {n["id"] for n in m["nodes"]}
    pipes = {p["id"] for p in m["pipes"]}
    out, identities = [], set()
    if not records or len(records) > 1000:
        raise ValueError("Between 1 and 1000 observations required")
    required = {
        "id",
        "timestamp",
        "sensor_id",
        "component",
        "measurement_type",
        "measurement",
        "uncertainty",
        "scenario",
        "provenance",
    }
    for r in records:
        if (
            not isinstance(r, dict)
            or set(r) != required
            or not isinstance(r["id"], str)
            or not r["id"]
            or r["id"] in identities
        ):
            raise ValueError(
                "Unique observation ID and exact observation fields required"
            )
        identities.add(r["id"])
        if not isinstance(r["timestamp"], str):
            raise ValueError("Timestamp must be ISO text")
        t = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
        if t.tzinfo is None:
            raise ValueError("Observation timestamp must have timezone")
        kind = r["measurement_type"]
        if not isinstance(kind, str) or kind not in MEASUREMENTS:
            raise ValueError("Unsupported observation quantity")
        component = r["component"]
        allowed = (
            pipes
            if kind == "flow"
            else set(m["sources"]) if kind == "source_output" else nodes
        )
        if not isinstance(component, str) or component not in allowed:
            raise ValueError("Unknown or incompatible observation component")
        if (
            kind == "service"
            and next(n["demand"] for n in m["nodes"] if n["id"] == component) <= 0
        ):
            raise ValueError("Service observations need demand nodes")
        if (
            not isinstance(r["sensor_id"], str)
            or not r["sensor_id"]
            or not isinstance(r["provenance"], dict)
            or r["provenance"].get("kind") not in ("SYNTHETIC", "REFERENCE", "FIELD")
            or not r["provenance"].get("source")
        ):
            raise ValueError("Sensor ID and explicit data provenance required")
        v = si(r["measurement"], MEASUREMENTS[kind])
        sigma = si(r["uncertainty"], MEASUREMENTS[kind], positive=True)
        if not isinstance(r["scenario"], dict) or not r["scenario"].get("id"):
            raise ValueError("Known observation operating condition required")
        out.append(
            dict(**r, value_si=v, sigma_si=sigma, canonical_unit=MEASUREMENTS[kind])
        )
    return out


def parameters(raw, specs):
    m = parse(raw)
    if not specs or len(specs) > 8 or len({p["id"] for p in specs}) != len(specs):
        raise ValueError("One to eight distinct parameters required")
    ownership = set()
    for p in specs:
        if set(p) != {"id", "kind", "components", "initial", "lower", "upper"}:
            raise ValueError("Exact parameter fields required")
        kind = p["kind"]
        allowed = (
            {e["id"] for e in m["pipes"]}
            if kind == "friction_multiplier"
            else (
                {n["id"] for n in m["nodes"] if n["demand"] > 0}
                if kind == "demand_multiplier"
                else set(m["sources"]) if kind == "source_head_offset" else set()
            )
        )
        bounds = (-10, 10) if kind == "source_head_offset" else (0.3, 3)
        vals = [p[k] for k in ("lower", "initial", "upper")]
        if (
            any(
                isinstance(v, bool)
                or not isinstance(v, (float, int))
                or not math.isfinite(v)
                for v in vals
            )
            or not bounds[0] <= vals[0] < vals[2] <= bounds[1]
            or not vals[0] <= vals[1] <= vals[2]
        ):
            raise ValueError("Finite bounded parameter interval required")
        if (
            not p["components"]
            or len(set(p["components"])) != len(p["components"])
            or not set(p["components"]) <= allowed
        ):
            raise ValueError("Invalid parameter components")
        for c in p["components"]:
            if (kind, c) in ownership:
                raise ValueError("Overlapping parameter ownership is ambiguous")
            ownership.add((kind, c))
    return specs


def apply(raw, specs, values):
    parameters(raw, specs)
    if len(values) != len(specs):
        raise ValueError("Parameter dimension mismatch")
    model = deepcopy(raw)
    for p, v in zip(specs, values):
        if not math.isfinite(float(v)) or not p["lower"] <= v <= p["upper"]:
            raise ValueError("Parameter outside declared domain")
        kind = p["kind"]
        for c in p["components"]:
            if kind == "friction_multiplier":
                e = next(e for e in model["pipes"] if e["id"] == c)
                e["friction_factor"] = dict(
                    value=si(e["friction_factor"], "1") * v, unit="1"
                )
            elif kind == "demand_multiplier":
                n = next(n for n in model["nodes"] if n["id"] == c)
                n["demand"] = dict(value=si(n["demand"], "m3/s") * v, unit="m3/s")
            else:
                s = next(s for s in model["sources"] if s["node"] == c)
                s["head"] = dict(value=si(s["head"], "m") + v, unit="m")
    parse(model)
    return model


def quantity(m, state, record):
    c, kind = record["component"], record["measurement_type"]
    if kind == "pressure":
        v = state["pressure_head_m"][c]
    elif kind == "flow":
        v = state["flow_m3s"][next(i for i, e in enumerate(m["pipes"]) if e["id"] == c)]
    elif kind == "source_output":
        v = state["boundary_injection_m3s"].get(c)
    else:
        v = state["delivered_m3s"][c] / state["requested_m3s"][c]
    if v is None:
        raise ValueError("Disconnected quantity is unknown, not a pressure measurement")
    return float(v)


def predict(raw, diameters, specs, values, records):
    model = apply(raw, specs, values)
    m, cache = parse(model), {}
    out = []
    for r in records:
        # Group by full operating condition, never by timestamp alone.
        import json

        key = json.dumps(r["scenario"], sort_keys=True)
        if key not in cache:
            s = simulate(model, diameters, r["scenario"])
            audit(model, diameters, r["scenario"], s)
            cache[key] = s
        out.append(quantity(m, cache[key], r))
    return np.array(out)


def jacobian(raw, diameters, specs, values, records):
    """Central differences, one-sided at boundaries; derivatives per parameter unit."""
    values = np.asarray(values, dtype=float)
    sigma = np.array([r["sigma_si"] for r in records])
    cols = []
    for i, p in enumerate(specs):
        h = 1e-4 * (p["upper"] - p["lower"])
        a, b = values.copy(), values.copy()
        a[i], b[i] = max(p["lower"], values[i] - h), min(p["upper"], values[i] + h)
        cols.append(
            (
                predict(raw, diameters, specs, b, records)
                - predict(raw, diameters, specs, a, records)
            )
            / ((b[i] - a[i]) * sigma)
        )
    return np.column_stack(cols)


def identifiability(j, specs):
    # Scaling makes rank diagnosis independent of parameter units.
    scaled = j * np.array([p["upper"] - p["lower"] for p in specs])
    singular = np.linalg.svd(scaled, compute_uv=False)
    tolerance = max(float(singular[0]) * 1e-6, 1e-8) if len(singular) else 1e-8
    rank = int(np.sum(singular > tolerance))
    gram = scaled.T @ scaled
    norms = np.sqrt(np.diag(gram))
    corr = np.divide(
        gram,
        np.outer(norms, norms),
        out=np.zeros_like(gram),
        where=np.outer(norms, norms) > 0,
    )
    return dict(
        rank=rank,
        parameters=len(specs),
        locally_identifiable=rank == len(specs),
        singular_values=singular.tolist(),
        relative_rank_tolerance=1e-6,
        condition_number=(
            float(singular[0] / singular[-1]) if rank == len(specs) else None
        ),
        sensitivity_column_cosines=corr.tolist(),
        scope="Local numerical sensitivity rank, not global structural identifiability or unique nonlinear solution",
    )


def calibrate(
    raw,
    diameters,
    specs,
    training,
    validation,
    seed=20261030,
    starts=3,
    max_evaluations=60,
):
    parameters(raw, specs)
    train, valid = observations(raw, training), observations(raw, validation)
    if {r["id"] for r in train} & {r["id"] for r in valid}:
        raise ValueError("Calibration and validation observation IDs must be disjoint")
    if not 1 <= starts <= 8 or not 1 <= max_evaluations <= 200:
        raise ValueError("Bounded calibration computation required")
    y, sigma = np.array([r["value_si"] for r in train]), np.array(
        [r["sigma_si"] for r in train]
    )
    lower, upper = np.array([p["lower"] for p in specs]), np.array(
        [p["upper"] for p in specs]
    )
    initial = np.array([p["initial"] for p in specs])
    before = identifiability(jacobian(raw, diameters, specs, initial, train), specs)
    rng, searches = np.random.default_rng(seed), []
    best = None
    for start in range(starts):
        history = []

        def residual(v):
            r = (predict(raw, diameters, specs, v, train) - y) / sigma
            history.append(
                dict(parameters=v.tolist(), weighted_sum_squares=float(r @ r))
            )
            return r

        fit = least_squares(
            residual,
            initial if start == 0 else rng.uniform(lower, upper),
            bounds=(lower, upper),
            max_nfev=max_evaluations,
            xtol=1e-9,
            ftol=1e-9,
            gtol=1e-9,
            x_scale=upper - lower,
        )
        searches.append(
            dict(
                start=start,
                success=bool(fit.success),
                evaluations=fit.nfev,
                message=fit.message,
                history=history,
                weighted_sum_squares=float(fit.fun @ fit.fun),
            )
        )
        if best is None or fit.fun @ fit.fun < best.fun @ best.fun:
            best = fit
    j = jacobian(raw, diameters, specs, best.x, train)
    ident = identifiability(j, specs)
    boundary = any(
        min(v - lo, hi - v) < 1e-5 * (hi - lo)
        for v, lo, hi in zip(best.x, lower, upper)
    )
    covariance = (
        np.linalg.inv(j.T @ j)
        if ident["locally_identifiable"] and not boundary
        else None
    )
    rows, metrics = {}, {}
    for label, data in [("calibration", train), ("validation", valid)]:
        predicted = predict(raw, diameters, specs, best.x, data)
        initial_predicted = predict(raw, diameters, specs, initial, data)
        sj = (
            jacobian(raw, diameters, specs, best.x, data)
            if covariance is not None
            else None
        )
        rows[label] = []
        for i, r in enumerate(data):
            param_var = (
                float(sj[i] @ covariance @ sj[i]) * r["sigma_si"] ** 2
                if covariance is not None
                else None
            )
            # Gaussian measurement variance + local parameter-estimation variance.
            sd = (
                math.sqrt(r["sigma_si"] ** 2 + max(0, param_var))
                if param_var is not None
                else None
            )
            interval = (
                [float(predicted[i] - 1.96 * sd), float(predicted[i] + 1.96 * sd)]
                if sd is not None
                else None
            )
            rows[label].append(
                dict(
                    observation=r,
                    prediction=float(predicted[i]),
                    initial_prediction=float(initial_predicted[i]),
                    residual=float(predicted[i] - r["value_si"]),
                    standardized_residual=float(
                        (predicted[i] - r["value_si"]) / r["sigma_si"]
                    ),
                    parameter_variance=param_var,
                    measurement_variance=r["sigma_si"] ** 2,
                    prediction_interval_95=interval,
                    covered=(
                        interval[0] <= r["value_si"] <= interval[1]
                        if interval
                        else None
                    ),
                )
            )
        metrics[label] = dict(
            weighted_rmse=float(
                np.sqrt(
                    np.mean(
                        (
                            (predicted - np.array([r["value_si"] for r in data]))
                            / np.array([r["sigma_si"] for r in data])
                        )
                        ** 2
                    )
                )
            ),
            initial_weighted_rmse=float(
                np.sqrt(
                    np.mean(
                        (
                            (
                                initial_predicted
                                - np.array([r["value_si"] for r in data])
                            )
                            / np.array([r["sigma_si"] for r in data])
                        )
                        ** 2
                    )
                )
            ),
            rmse_by_quantity={
                k: float(
                    np.sqrt(
                        np.mean(
                            [
                                row["residual"] ** 2
                                for row in rows[label]
                                if row["observation"]["measurement_type"] == k
                            ]
                        )
                    )
                )
                for k in sorted({r["measurement_type"] for r in data})
            },
            interval_coverage_95=(
                float(np.mean([r["covered"] for r in rows[label]]))
                if covariance is not None
                else None
            ),
        )
    # Predeclared benchmark gate. Model adequacy still cannot be inferred from low residuals alone.
    accepted = (
        best.success
        and ident["locally_identifiable"]
        and not boundary
        and metrics["validation"]["weighted_rmse"] <= 2
        and metrics["validation"]["interval_coverage_95"] >= 0.8
    )
    return dict(
        model_version=VERSION,
        status=(
            "BENCHMARK CALIBRATED" if accepted else "INSUFFICIENT CALIBRATION EVIDENCE"
        ),
        parameters=[
            dict(
                **p,
                estimate=float(v),
                standard_error=(
                    float(math.sqrt(max(0, covariance[i, i])))
                    if covariance is not None
                    else None
                ),
                unit="m" if p["kind"] == "source_head_offset" else "1",
            )
            for i, (p, v) in enumerate(zip(specs, best.x))
        ],
        initial_identifiability=before,
        fitted_identifiability=ident,
        at_bound=boundary,
        covariance=covariance.tolist() if covariance is not None else None,
        searches=searches,
        metrics=metrics,
        rows=rows,
        seed=seed,
        solver="scipy.optimize.least_squares / bounded uncertainty-weighted linear loss",
        acceptance_criteria=dict(
            local_full_rank=True,
            no_active_boundary=True,
            heldout_weighted_rmse_max=2,
            heldout_prediction_coverage_min=0.8,
        ),
        uncertainty_scope="Known independent Gaussian measurement noise; local linearised covariance. No field/model-discrepancy calibration, global uniqueness or Bayesian posterior claimed.",
    )


def sensor_placement(
    raw, diameters, specs, values, records, budget=2, current_sensors=()
):
    """Exact bounded design search maximises information from a registered observation pool."""
    data = observations(raw, records)
    sensors = sorted({r["sensor_id"] for r in data})
    if len(set(current_sensors)) != len(current_sensors) or not set(
        current_sensors
    ) <= set(sensors):
        raise ValueError("Current sensors must be distinct registered locations")
    available = [s for s in sensors if s not in current_sensors]
    if (
        isinstance(budget, bool)
        or not isinstance(budget, int)
        or not 1 <= budget <= min(3, len(available))
        or len(sensors) > 12
    ):
        raise ValueError("Sensor design limited to 12 locations and three sensors")
    j = jacobian(raw, diameters, specs, values, data)
    scale = np.array([p["upper"] - p["lower"] for p in specs])
    base = j[[r["sensor_id"] in current_sensors for r in data]] * scale
    information = np.eye(len(specs)) + base.T @ base
    base_score = float(np.linalg.slogdet(information)[1])
    layouts = []
    for added in combinations(available, budget):
        selected = tuple(sorted([*current_sensors, *added]))
        mask = [r["sensor_id"] in selected for r in data]
        a = j[mask] * scale
        score = float(np.linalg.slogdet(np.eye(len(specs)) + a.T @ a)[1])
        layouts.append(
            dict(
                sensors=list(selected),
                added_sensors=list(added),
                information_score=score,
                information_gain=score - base_score,
                identifiability=identifiability(j[mask], specs),
            )
        )
    layouts.sort(key=lambda r: (-r["information_score"], r["sensors"]))
    current = []
    # Conditional one-sensor value of information, same forward model and excitation.
    for s in available:
        a = j[[r["sensor_id"] == s for r in data]] * scale
        score = float(np.linalg.slogdet(information + a.T @ a)[1])
        current.append(
            dict(sensor=s, information_score=score, information_gain=score - base_score)
        )
    return dict(
        budget=budget,
        current_sensors=list(current_sensors),
        baseline_information_score=base_score,
        recommendation=layouts[0]["sensors"],
        layouts=layouts,
        value_of_information=sorted(current, key=lambda r: -r["information_score"]),
        criterion="log det(I + J_scaled^T J_scaled)",
        scope="Local information proxy with identity regularisation, independent known noise and fixed excitation; not monetary value or global identification guarantee",
    )
