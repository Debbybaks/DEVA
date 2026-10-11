"""Local calibration-estimation uncertainty on fixed diagnostic failure scenarios."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from .audit import verify_hash
from .calibration import apply, parameters
from .experiment import canonical
from .hydraulic_evidence import audit, provenance_revision
from .hydraulic_v2 import parse, simulate


def propagate(package, *, samples=64, seed=20261031):
    if type(samples) is not int or not 2 <= samples <= 256:
        raise ValueError("Between 2 and 256 parameter draws required")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Unsigned 32-bit seed required")
    verify_hash(package)
    twin = package["science"]
    agent = twin["engineering_agent"]
    verify_hash(agent)
    science = agent["science"]
    raw = science["configuration"]
    specs = twin["dataset"]["parameters"]
    parameters(raw, specs)
    calibration = twin["calibration"]
    if calibration["status"] != "BENCHMARK CALIBRATED":
        raise ValueError("Accepted synthetic calibration required")
    if [p["id"] for p in specs] != [p["id"] for p in calibration["parameters"]]:
        raise ValueError("Parameter covariance order must match specification order")
    if calibration["covariance"] is None or calibration["at_bound"]:
        raise ValueError(
            "Interior, locally identifiable calibration covariance required"
        )
    mean = np.array([p["estimate"] for p in calibration["parameters"]])
    if canonical(apply(raw, specs, mean)) != canonical(science["effective_configuration"]):
        raise ValueError("Agent effective model must match the supplied calibration estimate")
    covariance = np.asarray(calibration["covariance"], dtype=float)
    if (
        covariance.shape != (len(specs), len(specs))
        or not np.isfinite(covariance).all()
    ):
        raise ValueError("Invalid covariance dimensions or values")
    if not np.allclose(covariance, covariance.T, atol=1e-12):
        raise ValueError("Symmetric covariance required")
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    if min(eigenvalues) < -1e-12:
        raise ValueError("Positive-semidefinite covariance required")
    root = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0)))
    selected = next(
        c
        for c in science["outputs"]["simulate_training"]["candidates"]
        if c["id"] == science["selection"]
    )
    cases = [
        r
        for r in science["outputs"]["validate_selected"]["records"]
        if not r["component_passes"]
    ]
    component = science["plan"]["objective"]["component"]
    rng = np.random.default_rng(seed)
    draws, rejected = [], 0
    for _ in range(samples * 100):
        values = mean + root @ rng.standard_normal(len(specs))
        if any(v < p["lower"] or v > p["upper"] for p, v in zip(specs, values)):
            rejected += 1
            continue
        updated = apply(raw, specs, values)
        model = parse(updated)
        records = []
        for case in cases:
            scenario = case["scenario"]
            try:
                state = simulate(updated, selected["diameters_m"], scenario)
                audit(updated, selected["diameters_m"], scenario, state)
                pressure = state["pressure_head_m"][component]
                service = (
                    state["delivered_m3s"][component]
                    / state["requested_m3s"][component]
                )
                records.append(
                    dict(
                        scenario_id=scenario["id"],
                        state=state,
                        pressure_m=pressure,
                        service_fraction=service,
                        passes=pressure is not None
                        and pressure >= model["pmin"] - 1e-6
                        and service >= model["target"] - 1e-7,
                    )
                )
            except RuntimeError as error:
                records.append(
                    dict(
                        scenario_id=scenario["id"],
                        status="UNKNOWN SOLVER STATE",
                        error=str(error),
                    )
                )
        draws.append(dict(parameters=values.tolist(), records=records))
        if len(draws) == samples:
            break
    if len(draws) != samples:
        raise ValueError(
            "Parameter rejection budget exhausted; uncertainty not established"
        )
    summaries = []
    for i, case in enumerate(cases):
        rows = [draw["records"][i] for draw in draws]
        known = [r for r in rows if "passes" in r]
        pressures = [r["pressure_m"] for r in known if r["pressure_m"] is not None]
        summaries.append(
            dict(
                scenario_id=case["scenario"]["id"],
                samples=samples,
                known_states=len(known),
                unknown_states=samples - len(known),
                failure_count=sum(not r["passes"] for r in known),
                pressure_quantiles_m=(
                    np.quantile(pressures, [0.025, 0.5, 0.975]).tolist()
                    if pressures
                    else None
                ),
                service_quantiles=(
                    np.quantile(
                        [r["service_fraction"] for r in known], [0.025, 0.5, 0.975]
                    ).tolist()
                    if known
                    else None
                ),
            )
        )
    result = dict(
        model_version="local-calibration-risk-0.4.0",
        code=provenance_revision(),
        source_experiment=package["experiment_id"],
        source_sha256=package["scientific_sha256"],
        seed=seed,
        samples=samples,
        rejected_out_of_bounds_draws=rejected,
        covariance=calibration["covariance"],
        parameter_ids=[p["id"] for p in specs],
        draws=draws,
        cases=summaries,
        scope="Local Gaussian estimation-error approximation, conditioned on parameter bounds and frozen failed scenarios; not a Bayesian posterior or population reliability estimate.",
        limitations=[
            "Known independent sensor noise only; no structural model discrepancy or field calibration.",
            "Same parameter draw shared across cases captures common epistemic uncertainty, not physical failure dependence.",
            "Quantiles are finite ensemble summaries, not formally guaranteed coverage.",
            "Unknown solver states are retained separately, never silently counted as successful service.",
        ],
    )
    return dict(
        science=result,
        scientific_sha256=hashlib.sha256(canonical(result).encode()).hexdigest(),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence")
    parser.add_argument("--output", required=True)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261031)
    args = parser.parse_args()
    Path(args.output).write_text(
        json.dumps(
            propagate(
                json.loads(Path(args.evidence).read_text()),
                samples=args.samples,
                seed=args.seed,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
