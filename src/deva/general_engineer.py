"""One domain-blind budgeted investigator; physics and mutations are supplied tools."""

from copy import deepcopy
import hashlib
import math
import time
import json
from pathlib import Path
import numpy as np
from .domain_contract import validate_domain, validate_outcome
from .experiment import canonical
from .verification import wilson
from .provenance import source_revision

STRATEGIES = ("random", "evolutionary", "guided", "pareto", "hybrid")


class BudgetExhausted(Exception):
    pass


class ExperimentMemory:
    """Domain/model/configuration/source-scoped physical outcomes, never prose memory."""

    def __init__(self):
        self.records = {}
        self.experiments = {}

    def save(self, path):
        path = Path(path)
        temporary = path.with_suffix(path.suffix + ".tmp")
        payload = dict(
            schema_version="5.0", records=self.records, experiments=self.experiments
        )
        temporary.write_text(json.dumps(payload, allow_nan=False))
        temporary.replace(path)

    @classmethod
    def load(cls, path):
        payload = json.loads(Path(path).read_text())
        if payload.get("schema_version") != "5.0" or not isinstance(
            payload.get("records"), dict
        ):
            raise ValueError("Invalid scientific memory")
        memory = cls()
        memory.experiments = payload.get("experiments", {})
        for key, record in payload["records"].items():
            if (
                hashlib.sha256(canonical(record["outcome"]).encode()).hexdigest()
                != record["sha256"]
            ):
                raise ValueError("Memory output checksum mismatch")
            memory.records[key] = record
        return memory

    def remember(self, experiment):
        from .audit import verify_hash

        verify_hash(experiment)
        s = experiment["science"]
        self.experiments[experiment["experiment_id"]] = dict(
            domain=s["domain"]["id"],
            model_version=s["domain"]["model_version"],
            scientific_sha256=experiment["scientific_sha256"],
            configuration=s["configuration"],
            seeds=s["seeds"],
            selection=s["selection"],
            candidates=[
                {k: v for k, v in c.items() if k != "training"} for c in s["candidates"]
            ],
            hypotheses=s["hypotheses"],
            heldout=(
                {k: v for k, v in s["heldout"].items() if k != "records"}
                if s["heldout"]
                else None
            ),
        )

    def key(self, domain, design, scenario, source):
        return hashlib.sha256(
            canonical(
                dict(
                    domain=domain.descriptor["id"],
                    model=domain.descriptor["model_version"],
                    configuration=domain.configuration,
                    design=design,
                    scenario=scenario,
                    source=source,
                )
            ).encode()
        ).hexdigest()


def dominates(a, b):
    x = (a["cost"], a["training"]["failures"], -a["training"]["mean_service"])
    y = (b["cost"], b["training"]["failures"], -b["training"]["mean_service"])
    return all(p <= q for p, q in zip(x, y)) and any(p < q for p, q in zip(x, y))


def investigate(
    domain,
    *,
    seed=20261101,
    strategy="hybrid",
    maximum_cost=500,
    maximum_simulations=800,
    maximum_candidates=24,
    maximum_generations=5,
    maximum_seconds=120,
    training_samples=12,
    validation_samples=12,
    heldout_samples=60,
    target_failure_probability=0.02,
    memory=None,
    progress=None,
):
    validate_domain(domain)
    if strategy not in STRATEGIES:
        raise ValueError("Unknown registered search strategy")
    for x, lo, hi in [
        (maximum_simulations, 1, 20000),
        (maximum_candidates, 1, 500),
        (maximum_generations, 0, 50),
        (training_samples, 2, 200),
        (validation_samples, 2, 200),
        (heldout_samples, 2, 2000),
    ]:
        if type(x) is not int or not lo <= x <= hi:
            raise ValueError("Bounded integer research budgets required")
    if (
        type(seed) is not int
        or not 0 <= seed < 2**32
        or not math.isfinite(maximum_cost)
        or maximum_cost <= 0
        or not 0 < maximum_seconds <= 600
        or not 0 <= target_failure_probability <= 1
    ):
        raise ValueError("Invalid experiment constraints")
    started = time.monotonic()
    source = source_revision()
    memory = memory if memory is not None else ExperimentMemory()
    streams = np.random.SeedSequence(seed).spawn(4)
    seeds = {
        name: int(stream.generate_state(1)[0])
        for name, stream in zip(
            ("training", "validation", "heldout", "adversarial"), streams
        )
    }
    training = domain.scenarios(seeds["training"], training_samples)
    validation = domain.scenarios(seeds["validation"], validation_samples)
    heldout = domain.scenarios(seeds["heldout"], heldout_samples)
    rng = np.random.default_rng(seeds["adversarial"])
    calls = hits = 0
    invocations = []
    candidates = []
    seen = set()
    stop = "GENERATION BUDGET EXHAUSTED"

    def solve(design, scenario, phase):
        nonlocal calls, hits
        if progress:
            progress(
                dict(
                    stage="simulate",
                    domain=domain.descriptor["id"],
                    phase=phase,
                    simulations=calls,
                    design=list(design),
                    scenario=scenario,
                )
            )
        if time.monotonic() - started > maximum_seconds:
            raise BudgetExhausted("WALL CLOCK BUDGET EXHAUSTED")
        key = memory.key(domain, design, scenario, source["scientific_source_sha256"])
        if key in memory.records:
            hits += 1
            cached_record = memory.records[key]
            out = validate_outcome(domain, deepcopy(cached_record["outcome"]))
            if (
                hashlib.sha256(canonical(out).encode()).hexdigest()
                != cached_record["sha256"]
            ):
                raise ValueError("Memory output checksum mismatch")
            cached = True
        else:
            if calls >= maximum_simulations:
                raise BudgetExhausted("SIMULATION BUDGET EXHAUSTED")
            calls += 1
            cached = False
            try:
                out = validate_outcome(domain, domain.simulate(design, scenario))
            except RuntimeError as e:
                out = dict(
                    domain=domain.descriptor["id"],
                    model_version=domain.descriptor["model_version"],
                    scenario_id=scenario["id"],
                    passes=False,
                    service=None,
                    violations=["unknown_solver_state"],
                    state=None,
                    status="UNKNOWN",
                    error=str(e),
                )
            memory.records[key] = dict(
                outcome=deepcopy(out),
                sha256=hashlib.sha256(canonical(out).encode()).hexdigest(),
            )
        invocations.append(
            dict(
                tool="simulate",
                phase=phase,
                design=list(design),
                scenario=scenario,
                output=out,
                cached=cached,
                output_sha256=hashlib.sha256(canonical(out).encode()).hexdigest(),
            )
        )
        if progress:
            progress(
                dict(
                    stage="scientific_result",
                    domain=domain.descriptor["id"],
                    phase=phase,
                    simulations=calls,
                    result=out,
                    output_sha256=invocations[-1]["output_sha256"],
                )
            )
        return out

    def measure(design, scenarios, phase):
        records = [dict(scenario=s, outcome=solve(design, s, phase)) for s in scenarios]
        failed = sum(not r["outcome"]["passes"] for r in records)
        return dict(
            records=records,
            failures=failed,
            samples=len(records),
            mean_service=float(
                np.mean([r["outcome"]["service"] or 0 for r in records])
            ),
            failure_rate=failed / len(records),
            failure_rate_wilson_95=list(wilson(failed, len(records))),
        )

    def add(design, parent, generation, witness=None):
        identity = tuple(design)
        if identity in seen:
            return
        if len(candidates) >= maximum_candidates:
            raise BudgetExhausted("CANDIDATE BUDGET EXHAUSTED")
        seen.add(identity)
        candidate = dict(
            id=f"{domain.descriptor['id']}:g{generation}:c{len(candidates):04}",
            parent=parent,
            generation=generation,
            design=list(design),
            cost=domain.cost(design),
            counterexample=witness,
            rejection_reason=None,
        )
        candidates.append(candidate)
        if candidate["cost"] > maximum_cost + 1e-8:
            candidate["rejection_reason"] = "ENGINEERING COST EXCEEDED"
            return
        try:
            candidate["training"] = measure(design, training, "training")
        except BudgetExhausted:
            candidate["rejection_reason"] = "INCOMPLETE EVALUATION / BUDGET"
            raise

    try:
        add(domain.baseline, None, 0)
        for generation in range(1, maximum_generations + 1):
            feasible = [c for c in candidates if "training" in c]
            if not feasible:
                stop = "NO EVALUATED BUDGET-FEASIBLE BASELINE"
                break
            frontier = [
                c for c in feasible if not any(dominates(a, c) for a in feasible)
            ]
            best = min(
                feasible,
                key=lambda c: (
                    c["training"]["failures"],
                    -c["training"]["mean_service"],
                    c["cost"],
                ),
            )
            parents = frontier if strategy in ("pareto", "hybrid") else [best]
            before = len(seen)
            for parent in parents:
                witness = next(
                    (
                        r
                        for r in parent["training"]["records"]
                        if not r["outcome"]["passes"]
                    ),
                    None,
                )
                if strategy == "random":
                    children = [
                        [float(rng.choice(v["options"])) for v in domain.variables]
                        for _ in range(len(domain.variables))
                    ]
                else:
                    children = domain.mutations(
                        parent["design"],
                        witness if strategy in ("guided", "hybrid") else None,
                    )
                    if strategy in ("guided", "hybrid") and witness:
                        ranked = []
                        for d in children:
                            # Rank explicit physical interventions under the same simulation budget.
                            r = solve(
                                d, witness["scenario"], "counterexample_intervention"
                            )
                            ranked.append((r["service"] or 0, domain.cost(d), d))
                        children = [
                            x[2] for x in sorted(ranked, key=lambda x: (-x[0], x[1]))
                        ]
                    elif strategy == "evolutionary":
                        rng.shuffle(children)
                for child in children:
                    add(
                        child,
                        parent["id"],
                        generation,
                        witness["scenario"]["id"] if witness else None,
                    )
            if len(seen) == before:
                stop = "NO NOVEL CATALOGUE MUTATION"
                break
    except BudgetExhausted as e:
        stop = str(e)
    feasible = [c for c in candidates if "training" in c]
    frontier = [c for c in feasible if not any(dominates(a, c) for a in feasible)]
    selected = (
        min(
            feasible,
            key=lambda c: (
                c["training"]["failures"],
                -c["training"]["mean_service"],
                c["cost"],
            ),
        )
        if feasible
        else None
    )
    result_validation = result_heldout = result_adversarial = None
    verification = []
    if selected:
        try:
            result_validation = measure(
                selected["design"], validation, "validation_after_selection_frozen"
            )
            result_heldout = measure(
                selected["design"], heldout, "heldout_after_selection_frozen"
            )
            result_adversarial = measure(
                selected["design"],
                domain.scenarios(seeds["adversarial"], 8, severity=2),
                "adversarial_severity_search",
            )
            if time.monotonic() - started <= maximum_seconds:
                verification = domain.verify(selected["design"])
        except BudgetExhausted as e:
            stop = str(e) + " / GENERALISATION INCOMPLETE"
    achieved = (
        result_heldout is not None
        and result_heldout["failure_rate_wilson_95"][1] <= target_failure_probability
    )
    if achieved:
        stop = "CONFIDENCE TARGET ACHIEVED UNDER DECLARED SYNTHETIC DISTRIBUTION"
    diversity = 0.0
    if len(candidates) > 1:
        diversity = float(
            np.mean(
                [
                    np.mean(np.array(a["design"]) != np.array(b["design"]))
                    for i, a in enumerate(candidates)
                    for b in candidates[i + 1 :]
                ]
            )
        )
    payload = dict(
        schema_version="5.0",
        domain=domain.descriptor,
        configuration=domain.configuration,
        variables=domain.variables,
        code=source,
        seeds=seeds,
        strategy=strategy,
        seed=seed,
        plan=dict(
            objective="Minimise critical-service failures within engineering cost; preserve cost/performance frontier",
            maximum_cost=maximum_cost,
            budgets=dict(
                simulations=maximum_simulations,
                candidates=maximum_candidates,
                generations=maximum_generations,
                seconds=maximum_seconds,
            ),
            target_failure_probability=target_failure_probability,
            tools=["simulate", "counterexample_intervention", "mutate", "verify"],
            selection="Training only; freeze before validation and held-out; no reselection",
            sample_counts=dict(
                training=training_samples,
                validation=validation_samples,
                heldout=heldout_samples,
            ),
        ),
        scenario_sets=dict(training=training, validation=validation, heldout=heldout),
        candidates=candidates,
        frontier=[c["id"] for c in frontier],
        selection=selected["id"] if selected else None,
        validation=result_validation,
        heldout=result_heldout,
        adversarial=result_adversarial,
        verification=verification,
        invocations=invocations,
        solver_calls=calls,
        cache_hits=hits,
        diversity=diversity,
        stopping_reason=stop,
        target_achieved=achieved,
        critique=[
            "Finite catalogue search failure is not infeasibility proof",
            "No transfer of physical validation between domains",
            "Wall-clock budget stopping is host-dependent; scientific replay requires it not binding",
        ],
    )
    interventions = [
        dict(
            reference=f"invocations/{i}",
            scenario=x["scenario"]["id"],
            service=x["output"]["service"],
        )
        for i, x in enumerate(invocations)
        if x["phase"] == "counterexample_intervention"
    ]
    payload["hypotheses"] = [
        dict(
            id="H-CAPACITY-INTERVENTION",
            statement="Catalogue capacity interventions change service in fixed witnessed training scenarios",
            predicted_observations="Solved critical-service value changes under design intervention",
            experiment="counterexample_intervention",
            evidence_for=interventions,
            status="TESTING" if interventions else "INCONCLUSIVE",
            limitations="Intervention results retained; no general causal or field conclusion automatically inferred",
        )
    ]
    payload["claim_ledger"] = [
        dict(
            domain=domain.descriptor["id"],
            model_version=domain.descriptor["model_version"],
            claim=(
                f"Frozen candidate has {result_heldout['failures']}/{result_heldout['samples']} held-out failures"
                if result_heldout
                else "Held-out generalisation incomplete"
            ),
            evidence="heldout",
            verification_level="EMPIRICAL" if result_heldout else "UNTESTED",
            assumptions=domain.descriptor["validity_envelope"],
            limitations=payload["critique"],
            reproduction_route="deva.general_engineer.investigate with stored plan/configuration/seeds",
        )
    ]
    digest = hashlib.sha256(canonical(payload).encode()).hexdigest()
    experiment = dict(
        experiment_id="deva-domain-" + digest[:16],
        scientific_sha256=digest,
        science=payload,
        performance=dict(runtime_seconds=time.monotonic() - started),
    )
    memory.remember(experiment)
    return experiment
