"""Bounded deterministic scientific tool orchestration, without generated-code execution."""

from copy import deepcopy
import hashlib
import math
import numpy as np
from .hydraulic_v2 import parse, simulate, cost
from .hydraulic_evidence import (
    audit,
    topology_verification,
    envelope,
    provenance_revision,
)
from .hydraulic_experiment import sampled, evaluated, adversary, minimal_outages
from .verification import wilson
from .experiment import canonical

VERSION = "bounded-engineering-agent-0.4.0"


def objective(raw, value):
    m = parse(raw)
    required = {
        "component",
        "maximum_failure_probability",
        "maximum_cost_increase",
        "training_samples",
        "validation_samples",
        "maximum_candidates",
        "maximum_tool_calls",
        "seed",
    }
    if set(value) != required or value["component"] not in {
        n["id"] for n in m["nodes"] if n["demand"] > 0
    }:
        raise ValueError(
            "Exact structured objective and known demand component required"
        )
    for name, low, high in [
        ("maximum_failure_probability", 0, 1),
        ("maximum_cost_increase", 0, 1),
        ("training_samples", 2, 80),
        ("validation_samples", 2, 200),
        ("maximum_candidates", 1, 20),
        ("maximum_tool_calls", 1, 12),
        ("seed", 0, 2**32 - 1),
    ]:
        v = value[name]
        if (
            isinstance(v, bool)
            or not isinstance(v, (int, float))
            or not math.isfinite(v)
            or not low <= v <= high
        ):
            raise ValueError("Invalid bounded investigation objective")
        if name not in (
            "maximum_failure_probability",
            "maximum_cost_increase",
        ) and not isinstance(v, int):
            raise ValueError("Integer computational budget required")
    return value


def engineering_plan(raw, diameters, request):
    o = objective(raw, request)
    m = parse(raw)
    if len(diameters) != len(m["pipes"]) or any(
        isinstance(d, bool)
        or not isinstance(d, (int, float))
        or not math.isfinite(d)
        or not 0 < d <= 1
        for d in diameters
    ):
        raise ValueError("Explicit bounded SI pipe diameters required")
    base = cost(m, diameters)
    return dict(
        model_version=VERSION,
        objective=o,
        constraints=dict(
            maximum_cost=base * (1 + o["maximum_cost_increase"]),
            baseline_cost=base,
            cost_scope="Hydraulic synthetic diameter cost, not historical capacity price",
        ),
        assumptions=[
            "Synthetic scenario distribution, prescribed reservoir heads, fixed Darcy friction and pressure-dependent demand.",
            "Validation scenario stream sealed until candidate selected; target confidence is a Wilson upper bound.",
            "No calibrated field reliability, nonlinear hydraulic proof or global optimisation guarantee.",
        ],
        tools=[
            "inspect_baseline",
            "run_sensitivity_analysis",
            "generate_candidates",
            "simulate_training",
            "search_adversarial_scenarios",
            "validate_selected",
            "verify_property",
        ],
        experiments=dict(
            training_samples=o["training_samples"],
            validation_samples=o["validation_samples"],
            seed=o["seed"],
        ),
        success_criteria=dict(
            component=o["component"],
            minimum_service_fraction=m["target"],
            minimum_pressure_m=m["pmin"],
            failure_probability_upper_95_max=o["maximum_failure_probability"],
            cost_max=base * (1 + o["maximum_cost_increase"]),
        ),
        stopping_conditions=[
            "maximum_tool_calls",
            "bounded_candidate_catalogue_exhausted",
            "confidence_target_achieved",
            "insufficient_evidence",
            "no_budget_feasible_design",
        ],
        security="Only registered Python scientific tools; no generated Python, shell, eval or arbitrary tool names",
    )


def counterexample_scenario(raw, verification):
    if (
        verification.get("status") != "COUNTEREXAMPLE"
        or verification.get("result") != "sat"
    ):
        raise ValueError("A SAT bounded-topology counterexample is required")
    closed = verification.get("counterexample_closed")
    if (
        not isinstance(closed, list)
        or not closed
        or not set(closed) <= {p["id"] for p in parse(raw)["pipes"]}
    ):
        raise ValueError("Invalid counterexample component set")
    return dict(
        id="formal-counterexample",
        closed=closed,
        provenance=dict(
            requirement_id=verification["requirement_id"], scope=verification["scope"]
        ),
    )


def investigate(raw, diameters, request, progress=None, calibration_data=None):
    original = deepcopy(raw)
    o = objective(raw, request)
    m = parse(raw)
    plan = engineering_plan(raw, diameters, o)
    if calibration_data is not None:
        if set(calibration_data) != {"parameters", "calibration", "validation"}:
            raise ValueError("Explicit calibration data fields required")
        plan["tools"] = ["calibrate_model", "recommend_observations"] + plan["tools"]
    streams = np.random.SeedSequence(o["seed"]).spawn(3)
    seeds = {
        k: int(s.generate_state(1)[0])
        for k, s in zip(("training", "validation", "adversarial"), streams)
    }
    training = sampled(m, seeds["training"], o["training_samples"])
    # Validation is constructed only after selection, not available to training tools.
    outputs = {}
    invocations = []
    narrative = []
    stopped = None

    def measured(d, scenarios):
        records = []
        for s in scenarios:
            try:
                r = simulate(raw, d, s)
                audit(raw, d, s, r)
                n = o["component"]
                service = r["delivered_m3s"][n] / r["requested_m3s"][n]
                pressure = r["pressure_head_m"][n]
                passes = (
                    service >= m["target"] - 1e-7
                    and pressure is not None
                    and pressure >= m["pmin"] - 1e-6
                )
                records.append(
                    dict(
                        scenario=s,
                        result=r,
                        component_service=service,
                        component_pressure_m=pressure,
                        component_passes=passes,
                    )
                )
            except RuntimeError as error:
                records.append(
                    dict(
                        scenario=s,
                        unknown_solver_state=str(error),
                        component_passes=False,
                    )
                )
        failures = sum(not r["component_passes"] for r in records)
        return dict(
            records=records,
            failures=failures,
            samples=len(records),
            failure_rate=failures / len(records),
            failure_rate_wilson_95=list(wilson(failures, len(records))),
        )

    def inspect():
        return measured(diameters, [dict(id="baseline:nominal")])

    def sensitivity():
        base = simulate(raw, diameters, dict(id="sensitivity:baseline"))
        result = []
        for i, p in enumerate(m["pipes"]):
            d = list(diameters)
            d[i] *= 1.01
            r = simulate(raw, d, dict(id="sensitivity:" + p["id"]))
            audit(raw, d, dict(id="sensitivity:" + p["id"]), r)
            n = o["component"]
            a, b = base["pressure_head_m"][n], r["pressure_head_m"][n]
            result.append(
                dict(
                    component=p["id"],
                    perturbation_fraction=0.01,
                    pressure_delta_m=b - a if a is not None and b is not None else None,
                    cost_delta=cost(m, d) - cost(m, diameters),
                )
            )
        return dict(
            rows=result,
            scope="Local one-percent diameter sensitivity; not global reliability attribution",
        )

    def generate():
        out = [
            dict(
                id="agent:c000",
                parents=[],
                diameters_m=list(diameters),
                cost=cost(m, diameters),
                mutation="baseline",
            )
        ]
        ranked = sorted(
            outputs["run_sensitivity_analysis"]["rows"],
            key=lambda r: -(r["pressure_delta_m"] or 0),
        )
        for p in ranked:
            if len(out) >= o["maximum_candidates"]:
                break
            i = next(i for i, e in enumerate(m["pipes"]) if e["id"] == p["component"])
            higher = [v for v in m["options"] if v > diameters[i] + 1e-8]
            if not higher:
                continue
            d = list(diameters)
            d[i] = min(higher)
            out.append(
                dict(
                    id=f"agent:c{len(out):03}",
                    parents=["agent:c000"],
                    diameters_m=d,
                    cost=cost(m, d),
                    mutation=dict(
                        pipe=p["component"],
                        diameter_before_m=diameters[i],
                        diameter_after_m=d[i],
                    ),
                )
            )
        return out

    def train():
        records = []
        for c in outputs["generate_candidates"]:
            row = dict(c, training=measured(c["diameters_m"], training))
            row["rejection_reason"] = (
                "Cost constraint exceeded"
                if c["cost"] > plan["constraints"]["maximum_cost"] + 1e-9
                else None
            )
            records.append(row)
        feasible = [c for c in records if c["rejection_reason"] is None]
        selected = (
            min(feasible, key=lambda c: (c["training"]["failures"], c["cost"], c["id"]))
            if feasible
            else None
        )
        return dict(
            candidates=records,
            selection=selected["id"] if selected else None,
            selection_policy="Minimum training component failures, then synthetic cost; freeze before validation",
        )

    def chosen():
        t = outputs["simulate_training"]
        return next(c for c in t["candidates"] if c["id"] == t["selection"])

    def attack():
        c = chosen()
        scenarios = [
            dict(
                id="attack:" + p["id"],
                closed=[p["id"]],
                demand_factor=1.4,
                source_head_delta_m=-6.0,
            )
            for p in m["pipes"]
        ]
        tested = measured(c["diameters_m"], scenarios)
        failures = [r for r in tested["records"] if not r["component_passes"]]
        minimal = []
        for r in failures:
            if "result" in r:
                minimal.append(minimal_outages(raw, c["diameters_m"], r["scenario"]))
        return dict(
            evaluation=tested,
            minimal_failures=minimal,
            scope="Bounded single-outage search with continuous stress; biased adversarial scenarios are not IID reliability samples",
        )

    def validate():
        return measured(
            chosen()["diameters_m"],
            sampled(m, seeds["validation"], o["validation_samples"]),
        )

    def verify():
        proof = topology_verification(raw, 1)
        counter = topology_verification(raw, 2)
        if counter["status"] == "COUNTEREXAMPLE":
            s = counterexample_scenario(raw, counter)
            physical = {k: v for k, v in s.items() if k != "provenance"}
            result = measured(chosen()["diameters_m"], [physical])
        else:
            s = None
            result = None
        return dict(
            objects=[proof, counter],
            counterexample_scenario=s,
            counterexample_simulation=result,
            scope="Graph proof only; counterexample becomes a physically evaluated experiment, not an instruction to exceed budget",
        )

    def fit_model():
        from .calibration import calibrate

        return calibrate(
            raw,
            diameters,
            calibration_data["parameters"],
            calibration_data["calibration"],
            calibration_data["validation"],
            seed=o["seed"],
            starts=1,
        )

    def observe_next():
        from .calibration import sensor_placement

        fit = outputs["calibrate_model"]
        return sensor_placement(
            original,
            diameters,
            calibration_data["parameters"],
            [p["estimate"] for p in fit["parameters"]],
            calibration_data["calibration"],
            budget=2,
        )

    registry = dict(
        calibrate_model=fit_model,
        recommend_observations=observe_next,
        inspect_baseline=inspect,
        run_sensitivity_analysis=sensitivity,
        generate_candidates=generate,
        simulate_training=train,
        search_adversarial_scenarios=attack,
        validate_selected=validate,
        verify_property=verify,
    )
    for tool in plan["tools"]:
        if len(invocations) >= o["maximum_tool_calls"]:
            stopped = "COMPUTATIONAL TOOL BUDGET EXHAUSTED"
            break
        if (
            tool
            in ("search_adversarial_scenarios", "validate_selected", "verify_property")
            and outputs["simulate_training"]["selection"] is None
        ):
            stopped = "NO BUDGET FEASIBLE DESIGN"
            break
        if progress:
            progress(dict(stage="tool", tool=tool, index=len(invocations)))
        output = registry[tool]()
        outputs[tool] = output
        if tool == "calibrate_model" and output["status"] == "BENCHMARK CALIBRATED":
            from .calibration import apply

            raw = apply(
                original,
                calibration_data["parameters"],
                [p["estimate"] for p in output["parameters"]],
            )
            m = parse(raw)
        invocation = dict(
            index=len(invocations),
            tool=tool,
            input_references=["plan", "configuration", "prior_tools"],
            output_reference=f"outputs/{tool}",
            output_sha256=hashlib.sha256(canonical(output).encode()).hexdigest(),
        )
        invocations.append(invocation)
        narrative.append(
            dict(
                text=f"{tool} completed; recorded authoritative scientific output.",
                evidence=invocation["output_reference"],
            )
        )
    selection = outputs.get("simulate_training", {}).get("selection")
    validation = outputs.get("validate_selected")
    achieved = (
        validation is not None
        and validation["failure_rate_wilson_95"][1] <= o["maximum_failure_probability"]
    )
    if stopped is None:
        stopped = (
            "CONFIDENCE TARGET ACHIEVED"
            if achieved
            else "BOUNDED CATALOGUE EXHAUSTED / INSUFFICIENT TARGET EVIDENCE"
        )
    claims = []
    if validation:
        text = f"Candidate {selection}: {validation['failures']}/{validation['samples']} held-out {o['component']} service/pressure failures; Wilson upper bound {validation['failure_rate_wilson_95'][1]:.6f}."
        claims.append(
            dict(
                claim=text,
                evidence="outputs/validate_selected",
                status="EMPIRICAL ROBUSTNESS",
                assumptions=plan["assumptions"],
                limitations=[
                    "Finite synthetic sample, no universal robustness or hydraulic proof."
                ],
                reproduction_route="deva.engineering_agent.investigate with stored configuration, diameters and objective",
            )
        )
        narrative.append(dict(text=text, evidence="outputs/validate_selected"))
    critique = [
        dict(
            issue=(
                "Failure-probability target not established"
                if not achieved
                else "Target established only under assumed synthetic distribution"
            ),
            evidence="outputs/validate_selected" if validation else "plan",
        ),
        dict(
            issue="Hydraulic parameters and rupture hazard remain uncalibrated to field data",
            evidence="plan/assumptions",
        ),
        dict(
            issue="Bounded candidate mutations are not a global optimum",
            evidence="outputs/generate_candidates",
        ),
        dict(
            issue="Topology proof does not prove hydraulic service",
            evidence=(
                "outputs/verify_property" if "verify_property" in outputs else "plan"
            ),
        ),
    ]
    science = dict(
        schema_version="4.1",
        model_version=VERSION,
        configuration=original,
        effective_configuration=raw,
        calibration_data=calibration_data,
        diameters_m=diameters,
        plan=plan,
        seeds=seeds,
        invocations=invocations,
        outputs=outputs,
        selection=selection,
        stopping_reason=stopped,
        target_achieved=achieved,
        claim_ledger=claims,
        self_critique=critique,
        research_narrative=narrative,
        code=provenance_revision(),
    )
    e = envelope(science)
    e["experiment_id"] = "deva-agent-" + e["scientific_sha256"][:16]
    return e
