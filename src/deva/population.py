"""Bounded domain-neutral scenario populations; biased attacks are not IID confidence."""

import time
from .domain_contract import validate_domain, validate_outcome
from .verification import wilson


def evaluate_population(domain, design, seed, count=512, kind="iid"):
    validate_domain(domain)
    if (
        type(count) is not int
        or not 2 <= count <= 2000
        or type(seed) is not int
        or not 0 <= seed < 2**32
        or kind not in ["iid", "stratified", "adversarial"]
    ):
        raise ValueError("Bounded population and explicit sampling class required")
    started = time.perf_counter()
    records = []
    if kind == "stratified":
        severity = [0.5, 1, 1.5, 2]
        scenarios = [
            domain.scenarios(seed + i, 1, s)[0]
            for i, s in enumerate(severity * (count // 4 + 1))
        ][:count]
    else:
        scenarios = domain.scenarios(
            seed, count, severity=2 if kind == "adversarial" else 1
        )
    for scenario in scenarios:
        try:
            outcome = validate_outcome(domain, domain.simulate(design, scenario))
        except RuntimeError as error:
            outcome = dict(
                domain=domain.descriptor["id"],
                model_version=domain.descriptor["model_version"],
                passes=False,
                service=None,
                status="UNKNOWN",
                error=str(error),
            )
        records.append(dict(scenario=scenario, outcome=outcome))
    failures = sum(not r["outcome"]["passes"] for r in records)
    runtime = time.perf_counter() - started
    return dict(
        science=dict(
            domain=domain.descriptor["id"],
            model_version=domain.descriptor["model_version"],
            design=design,
            seed=seed,
            sampling=kind,
            count=count,
            records=records,
            failures=failures,
            wilson_95=list(wilson(failures, count)) if kind == "iid" else None,
            scope="Frozen design; unknown solver states conservatively failed. Stratified/biased attacks have no IID reliability interval.",
        ),
        performance=dict(seconds=runtime, scenarios_per_second=count / runtime),
    )
