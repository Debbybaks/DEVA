"""Human-readable report projected from a hash-validated hydraulic package."""

import argparse, json
from pathlib import Path
from deva.audit import verify_hash

p = argparse.ArgumentParser()
p.add_argument("evidence")
p.add_argument("--output", required=True)
a = p.parse_args()
e = json.loads(Path(a.evidence).read_text())
verify_hash(e)
s = e["science"]
if s["schema_version"] != "3.0" or s["recommendation"] is None:
    raise ValueError("A completed hydraulic design experiment is required")
c = next(c for c in s["candidates"] if c["id"] == s["recommendation"])
lines = [
    "# DEVA hydraulic Engineering Evidence Package",
    "",
    s["configuration"]["objective"],
    "",
    f"Experiment: `{e['experiment_id']}`",
    f"Scientific hash: `{e['scientific_sha256']}`",
    "",
    f"Training-selected candidate: `{c['id']}`; illustrative construction cost {c['cost']:.6f}.",
    "",
    "| Split | Failures / trials | Failure Wilson 95% interval |",
    "|---|---|---|",
]
for split in ["training", "validation", "heldout", "declared"]:
    m = c[split]["metrics"]
    lo, hi = m["failure_rate_wilson_95"]
    lines.append(
        f"| {split} | {m['failures']}/{m['samples']} | {100*lo:.2f}%–{100*hi:.2f}% |"
    )
lines += [
    "",
    "Declared intervals are descriptive counting intervals; declared scenarios are not IID field samples. Held-out intervals are conditional on synthetic IID sampling and the fixed model.",
    "",
    s["selection_policy"],
    "",
    "## Models and units",
    "",
    "Signed Darcy–Weisbach flow and pressure-dependent demand; canonical m, s, m³/s. Full variable/assumption definitions: HYDRAULIC_MODEL_V2.md. No historical capacity-to-diameter conversion or cross-model cost comparison.",
    "",
    "## Retained design ancestry",
    "",
    "| Candidate | Parents | Cost | Held-out failures | Rejection reason |",
    "|---|---|---|---|---|",
]
for x in s["candidates"]:
    lines.append(
        f"| {x['id']} | {', '.join(x['parents']) or 'origin'} | {x['cost']:.3f} | {x['heldout']['metrics']['failures']} | {x['rejection_reason'] or 'training frontier'} |"
    )
lines += ["", "## Scientific Claim Ledger", ""]
for claim in s["claim_ledger"]:
    lines += [
        f"### {claim['id']}",
        "",
        claim["claim"],
        "",
        f"Status: {claim['status']}",
        f"Evidence paths: {', '.join(claim['evidence'])}",
        f"Assumptions: {'; '.join(claim['assumptions'])}",
        f"Limitations: {'; '.join(claim['limitations'])}",
        f"Reproduce: {claim['reproduction']}",
        "",
    ]
lines += [
    "## Resilience frontier",
    "",
    "```json",
    json.dumps(s["resilience_frontier"], indent=2),
    "```",
    "",
    "## Uncertainty and adversarial scope",
    "",
    s["uncertainty"]["aleatoric"],
    "",
    s["uncertainty"]["epistemic"],
    "",
    s["adversarial"]["scope"],
    "",
    "## Computed time and operational cascade",
    "",
    s["timeline"]["scope"],
    "",
    s["cascade"]["scope"],
    "",
    "## Reproducibility",
    "",
    "```json",
    json.dumps(
        {
            "configuration": s["experiment_config"],
            "code": s["code"],
            "software": s["software"],
            "seeds": s["seeds"],
        },
        indent=2,
    ),
    "```",
    "",
    "## Limitations",
    "",
] + [f"- {x}" for x in s["limitations"]]
Path(a.output).write_text("\n".join(lines) + "\n")
print(a.output)
