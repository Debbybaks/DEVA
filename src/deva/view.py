"""Read-only UI projection. Scientific summaries stay in Python."""

from .analysis import metrics
from .schema import Problem


def project(envelope):
    s = envelope["science"]
    p = Problem.parse(s["configuration"])
    if s["schema_version"] == "2.0":
        candidates = [
            dict(
                id=c["id"],
                parents=c["parents"],
                generation=c["generation"],
                mutations=c["mutations"],
                capacities=c["capacities"],
                cost=c["cost"],
                disposition=c["disposition"],
                rejection_reason=c["rejection_reason"],
                verification=c["verification"],
                splits={
                    k: c[k] for k in ("declared", "training", "validation", "heldout")
                },
                visual_fields=c["visual_fields"],
            )
            for c in s["candidates"]
        ]
        return dict(
            experiment_id=envelope["experiment_id"],
            scientific_sha256=envelope["scientific_sha256"],
            problem=s["configuration"],
            recommendation=s["recommendation"],
            candidates=candidates,
            scenarios=s["scenarios"],
            pareto_frontier=s["pareto_frontier"],
            adversarial=s["adversarial"],
            provenance=s["provenance"],
            sensitivity=s["sensitivity"],
            limitations=s["limitations"],
            seeds=s["seeds"],
            software=s["software"],
            failure_taxonomy=s["failure_taxonomy"],
            infeasible_attempts=s["infeasible_attempts"],
        )
    candidates = []
    for c in s["candidates"]:
        if c["synthesis"]["capacities"] is None:
            continue
        candidates.append(
            dict(
                id=c["id"],
                parents=c["parents"],
                generation=c["generation"],
                mutations=[dict(operator=c["id"])],
                capacities=c["synthesis"]["capacities"],
                cost=c["verification"]["cost"],
                disposition=c["disposition"],
                rejection_reason=c["reason"],
                verification=c["verification"],
                splits=dict(
                    declared=dict(
                        results=c["declared_results"],
                        metrics=metrics(p, c["declared_results"]),
                    ),
                    heldout=dict(
                        results=c["heldout_results"],
                        metrics=metrics(p, c["heldout_results"]),
                    ),
                ),
                visual_fields=[],
            )
        )
    return dict(
        experiment_id=envelope["experiment_id"],
        scientific_sha256=envelope["scientific_sha256"],
        problem=s["configuration"],
        recommendation=s["winner"],
        candidates=candidates,
        scenarios=dict(declared=s["scenarios"], heldout=s["heldout_scenarios"]),
        pareto_frontier=[],
        adversarial=None,
        provenance=None,
        sensitivity=None,
        limitations=s["limitations"],
        seeds=dict(heldout=s["seed"]),
        software=s["software"],
        failure_taxonomy=None,
    )
