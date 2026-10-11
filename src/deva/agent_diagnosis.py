"""Post-selection diagnosis; reused held-out cases never establish generalisation."""

from copy import deepcopy
import argparse
import json
from pathlib import Path

from .audit import verify_hash
from .experiment import canonical
from .hydraulic_v2 import parse, simulate, cost
from .hydraulic_evidence import audit
from .verification import wilson
import hashlib


def diagnose(package):
    verify_hash(package)
    agent = package["science"]["engineering_agent"]
    verify_hash(agent)
    science = agent["science"]
    raw = science["effective_configuration"]
    model = parse(raw)
    component = science["plan"]["objective"]["component"]
    selected = next(
        c
        for c in science["outputs"]["simulate_training"]["candidates"]
        if c["id"] == science["selection"]
    )
    diameters = selected["diameters_m"]
    validation = science["outputs"]["validate_selected"]

    def evaluate(d, scenario):
        try:
            state = simulate(raw, d, scenario)
            audit(raw, d, scenario, state)
        except RuntimeError as error:
            return {"status": "UNKNOWN SOLVER STATE", "error": str(error)}
        pressure = state["pressure_head_m"][component]
        service = state["delivered_m3s"][component] / state["requested_m3s"][component]
        return dict(
            status="NUMERICALLY AUDITED",
            state=state,
            pressure_margin_m=None if pressure is None else pressure - model["pmin"],
            service_margin=service - model["target"],
            passes=pressure is not None
            and pressure >= model["pmin"] - 1e-6
            and service >= model["target"] - 1e-7,
        )

    failures = []
    for index, record in enumerate(validation["records"]):
        if record["component_passes"]:
            continue
        scenario = record["scenario"]
        counterfactuals = {}
        for label, changes in [
            ("remove_outages", {"closed": []}),
            ("nominal_demand", {"demand_factor": 1.0}),
            ("nominal_source_head", {"source_head_delta_m": 0.0}),
            (
                "nominal_demand_and_head",
                {"demand_factor": 1.0, "source_head_delta_m": 0.0},
            ),
        ]:
            altered = deepcopy(scenario)
            altered.update(changes)
            altered["id"] = scenario["id"] + ":" + label
            counterfactuals[label] = evaluate(diameters, altered)
        replay = evaluate(diameters, scenario)
        if "result" in record and replay.get("state") != record["result"]:
            raise ValueError(
                "Stored failure no longer replays exactly; diagnose at recorded source revision"
            )
        single_outages = {}
        for pipe_id in scenario.get("closed", []):
            altered = deepcopy(scenario)
            altered.update(id=scenario["id"] + ":only:" + pipe_id, closed=[pipe_id])
            single_outages[pipe_id] = evaluate(diameters, altered)
        disconnected = component in replay.get("state", {}).get(
            "disconnected_nodes", []
        )
        failures.append(
            dict(
                validation_index=index,
                scenario=scenario,
                original_record=record,
                replay=replay,
                mechanism=(
                    "TOPOLOGICAL DISCONNECTION"
                    if disconnected
                    else (
                        "CONNECTED HYDRAULIC SERVICE/PRESSURE DEFICIT"
                        if replay["status"] == "NUMERICALLY AUDITED"
                        else "UNKNOWN"
                    )
                ),
                counterfactuals=counterfactuals,
                single_outage_probes=single_outages,
            )
        )

    # Single-pipe catalogue probes are intentionally diagnostic, not a new winner.
    probes = []
    for i, pipe in enumerate(model["pipes"]):
        for option in model["options"]:
            if option <= diameters[i] + 1e-8:
                continue
            modified = list(diameters)
            modified[i] = option
            results = [evaluate(modified, f["scenario"]) for f in failures]
            resolved = sum(r.get("passes", False) for r in results)
            delta = cost(model, modified) - selected["cost"]
            probes.append(
                dict(
                    pipe=pipe["id"],
                    diameter_before_m=diameters[i],
                    diameter_after_m=option,
                    cost_delta=delta,
                    total_cost=cost(model, modified),
                    resolved_observed_failures=resolved,
                    cost_per_resolved_case=delta / resolved if resolved else None,
                    results=results,
                )
            )
    result = dict(
        source_experiment=package["experiment_id"],
        source_sha256=package["scientific_sha256"],
        agent_experiment=agent["experiment_id"],
        selected_candidate=science["selection"],
        selected_cost=selected["cost"],
        samples=validation["samples"],
        failures=validation["failures"],
        failure_rate_wilson_95=list(
            wilson(validation["failures"], validation["samples"])
        ),
        cases=failures,
        diagnostic_design_probes=probes,
        scope="Post-selection diagnosis on reused held-out evidence. No new reliability claim, candidate selection, or target achievement.",
        limitations=[
            "Counterfactual attribution is conditional on this steady hydraulic model, not physical causal proof.",
            "No temporal cascade or statistical dependence can be inferred from static IID cases.",
            "Calibration covariance and structural model discrepancy are not propagated in this diagnosis.",
            "Diagnostic cost per resolved case is not cost per unit population reliability.",
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
    args = parser.parse_args()
    Path(args.output).write_text(
        json.dumps(diagnose(json.loads(Path(args.evidence).read_text())), indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
