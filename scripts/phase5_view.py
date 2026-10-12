"""Create a compact, hash-linked scientific world from stored research outputs."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from deva.audit import verify_hash
from deva.experiment import canonical
from deva.hydraulic_v2 import parse


def project(evidence):
    verify_hash(evidence)
    experiments = []
    for e in evidence["science"]["experiments"]:
        verify_hash(e)
        s = e["science"]
        domain = s["domain"]["id"]

        def frames(records):
            out = []
            for row in records:
                result = row["outcome"]
                state = result["state"]
                flags = {}
                if state and domain == "microgrid":
                    flags = {
                        "critical-load": [
                            served >= s["configuration"]["target"] * demand - 1e-5
                            for served, demand in zip(
                                state["served_W"], state["demand_W"]
                            )
                        ]
                    }
                elif state and domain == "water":
                    model = parse(s["configuration"])
                    flags = {
                        n["id"]: [
                            state["pressure_head_m"][n["id"]] is not None
                            and state["pressure_head_m"][n["id"]]
                            >= model["pmin"] - 1e-6
                            and state["delivered_m3s"][n["id"]]
                            / state["requested_m3s"][n["id"]]
                            >= model["target"] - 1e-7
                        ]
                        for n in model["nodes"]
                        if n["demand"] > 0
                    }
                out.append(
                    dict(
                        scenario=row["scenario"], outcome=result, component_passes=flags
                    )
                )
            return out

        candidates = [
            dict(
                id=c["id"],
                parent=c["parent"],
                generation=c["generation"],
                design=c["design"],
                cost=c["cost"],
                counterexample=c["counterexample"],
                rejection_reason=c["rejection_reason"],
                training_failures=c.get("training", {}).get("failures"),
                frames=frames(c.get("training", {}).get("records", [])),
            )
            for c in s["candidates"]
        ]
        experiments.append(
            dict(
                id=e["experiment_id"],
                domain=domain,
                descriptor=s["domain"],
                configuration=s["configuration"],
                variables=s["variables"],
                strategy=s["strategy"],
                seed=evidence["science"]["predeclared_seeds"][
                    len(experiments) % len(evidence["science"]["predeclared_seeds"])
                ],
                selection=s["selection"],
                frontier=s["frontier"],
                plan=s["plan"],
                stop=s["stopping_reason"],
                target_achieved=s["target_achieved"],
                candidates=candidates,
                heldout=s["heldout"],
                adversarial=s["adversarial"],
                verification=s["verification"],
                claim_ledger=s["claim_ledger"],
                solver_calls=s["solver_calls"],
                diversity=s["diversity"],
            )
        )
    # Machine references stay domain-specific; no cross-domain averaging of cost.
    view = dict(
        source_experiment=evidence["experiment_id"],
        source_sha256=evidence["scientific_sha256"],
        label="SYNTHETIC / BOUNDED CROSS-DOMAIN RESEARCH",
        experiments=experiments,
        ablation=evidence["science"]["ablation"],
        curves=[
            {k: v for k, v in row.items() if k != "records"}
            for row in evidence["science"]["robustness_curves"]
        ],
        decision={
            k: v
            for k, v in evidence["science"]["decision_analysis"].items()
            if k != "candidates"
        },
        decision_candidates=[
            {k: v for k, v in c.items() if k != "records"}
            for c in evidence["science"]["decision_analysis"]["candidates"]
        ],
        limitations=evidence["science"]["limitations"],
    )
    return dict(
        science=view,
        scientific_sha256=hashlib.sha256(canonical(view).encode()).hexdigest(),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("evidence")
    p.add_argument("--output", required=True)
    a = p.parse_args()
    opener = gzip.open if a.evidence.endswith(".gz") else open
    with opener(a.evidence, "rt") as f:
        e = json.load(f)
    Path(a.output).write_text(
        json.dumps(project(e), separators=(",", ":"), allow_nan=False) + "\n"
    )
