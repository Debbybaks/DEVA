"""Evidence-backed report; no publication, novelty or search-superiority fabrication."""

import gzip, json
from pathlib import Path
from deva.audit import verify_hash

with gzip.open("artifacts/phase5-search-evidence.json.gz", "rt") as f:
    e = json.load(f)
with gzip.open("artifacts/phase5-validation-study.json.gz", "rt") as f:
    v = json.load(f)
verify_hash(e)
verify_hash(v)
s = e["science"]
x = v["science"]
lines = [
    "# DEVA Phase 5 — bounded cross-domain engineering research",
    "",
    f"Study `{e['experiment_id']}`; SHA256 `{e['scientific_sha256']}`.",
    f"Validation `{v['experiment_id']}`; SHA256 `{v['scientific_sha256']}`.",
    "",
    "## Problem and architecture",
    "",
    "The research question is whether one bounded, explicit-tool investigation engine can operate across different physical models. Domain-neutral budgets, candidate ancestry, training-only selection, Pareto comparison, counterexample interventions, memory and stopping are implemented in deva.general_engineer. Physics remains in independently validated domain adapters. No LLM or hidden reasoning is required to produce these results.",
    "",
    "## Domain contract",
    "",
    "Descriptors declare identity/version, units, state, governing equations, constraints, uncertainty, observable quantities, evidence and validity scope. Outcomes and cached records are domain/configuration/model/source scoped. The water adapter calls the existing solver and independent audit without replacing legacy experiments. New source hashes include nested Python modules; old replay identity remains pinned.",
    "",
    "## Physical models",
    "",
    "Water: steady signed Darcy flow and pressure-dependent service with prescribed sources. Microgrid: chronological energy adequacy with charging/discharging losses, generator outages, renewable limits and power/energy bounds. Lexicographic linear optimisation first maximises worst-interval service and then reduces generation/throughput. Perfect foresight and finite-horizon battery depletion are explicit optimistic planning assumptions. No AC voltage/frequency/protection model is claimed.",
    "",
    "## Validation",
    "",
    "Water adapter tests compare complete states against unchanged original functions. Microgrid independent analytical cases check two-hour storage-limited service, efficiency loss and converter power limitation. Every state is checked for conservation and bounds. A Z3 rational necessary-energy certificate proves one precisely bounded insufficient-energy case; SAT would not certify a feasible electrical dispatch.",
    "",
    "## Autonomous search and experiment design",
    "",
    "Five fixed strategies run on three predeclared seeds per domain: random catalogue exploration, incremental evolutionary ordering, witnessed-counterexample ranking, Pareto-parent exploration and hybrid Pareto/intervention ranking. Fixed budgets are 400 simulations, 16 candidates and four generations. Selection uses eight training scenarios only; 12 validation and 40 held-out scenarios are sealed until selection. An additional biased severity attack is separate from IID reliability. Actual solver counts differ between strategies and are preserved. These algorithms are bounded catalogue heuristics, not global optimisation guarantees.",
    "",
    "## Search ablation",
    "",
    "| Domain | Strategy | Mean held-out failure | Actual solver calls by seed |",
    "|---|---|---:|---|",
]
for r in s["ablation"]:
    lines.append(
        f"| {r['domain']} | {r['strategy']} | {r['mean_failure_rate']:.4%} | {', '.join(str(t['solver_calls']) for t in r['trials'])} |"
    )
lines += [
    "",
    "Guided search is not established as superior. Water incremental strategies tie on mean held-out failure in this small study. Random exploration is stronger than incremental/guided search on this microgrid catalogue. Three seeds do not support a general statistical superiority claim. No method was retuned after viewing these held-out results. The earlier dirty-source exploratory pilot is retained separately as provisional evidence.",
    "",
    "## Larger frozen populations",
    "",
    "| Domain | Failures / scenarios | Runtime (s) | Throughput (scenarios/s) |",
    "|---|---:|---:|---:|",
]
for p in x["populations"]:
    t = v["performance"]["populations"][p["domain"]]
    lines.append(
        f"| {p['domain']} | {p['failures']}/{p['count']} | {t['seconds']:.3f} | {t['scenarios_per_second']:.2f} |"
    )
lines += [
    "",
    "These populations test fixed hybrid designs using a fresh seed. They do not replace the original held-out study or establish field reliability. Stratified and biased populations deliberately do not receive IID intervals.",
    "",
    "## Cost and constraint negotiation",
    "",
    "The historical calibrated hospital investigation remains 4/40 and its 2% target unestablished. Three predeclared related designs are compared on a fresh shared 120-scenario population:",
    "",
    "| Design | Synthetic construction cost | Hospital failures | 95% Wilson interval |",
    "|---|---:|---:|---|",
]
for r in s["decision_analysis"]["candidates"]:
    lines.append(
        f"| {r['id']} | {r['cost']:.6f} | {r['failures']}/{r['samples']} | {r['wilson_95']} |"
    )
lines += [
    "",
    f"Smallest known relaxation among these tested designs: {s['decision_analysis']['smallest_known_relaxation']}. This is an observed engineering benefit, not proof of global minimal relaxation or infeasibility.",
    "",
    "## Uncertainty and observation design",
    "",
    "Local water covariance propagation from Phase 4 remains preserved. Phase 5 additionally sweeps microgrid discharge-efficiency assumptions without pretending they are calibrated probabilities. The existing water sensor-layout information proxy is compared against 32 seeded random layouts. This measures local identifiability information, not real failure detection.",
]
for r in x["assumption_sweeps"]:
    lines.append(
        f"- Assumed discharge efficiency {r['assumed_discharge_efficiency']}: {r['failures']}/{r['count']} failures on common diagnostic scenarios."
    )
lines += [
    f"- Sensor information: best {x['sensor_comparison']['best_information_score']:.6f}; random mean {x['sensor_comparison']['random_mean']:.6f}.",
    "",
    "## Memory, hypotheses and evidence",
    "",
    "Physical outcomes are cached by domain, model, configuration, scenario, design and recursive source fingerprint. Durable memory also preserves experiment summaries, failed candidates, seeds, validation results and hypotheses. Hypothesis transitions require domain-correct experimental references and scope. Claims never inherit evidence from another domain. Unknown solver states and budget-incomplete evaluations are retained.",
    "",
    "## Visual experience",
    "",
    "Engineering Worlds uses progressive experiment loading and exact stored states. Water and microgrid have distinct physical representations. Candidate ancestry, same-scenario parent comparison, X-ray, local uncertainty and evidence lenses expose computations. Researcher Mode can launch bounded registered investigations through process workers and streamed scientific events; Judge and Portfolio modes share the same evidence; Demonstration 3.0 guides stored outcomes and never manufactures success. Responsive numerical 2D is intentional; software 3D remains slow and no WebGPU adapter was available in the measured environment.",
    "",
    "## Contributions and limits",
    "",
    "Implementation contribution: a domain contract, two different physical adapters and one computationally exercised bounded investigation engine. Engineering contribution: inspectable budget/service trade-offs and retained counterexamples. Algorithmic contribution: an implemented intervention-ranked search heuristic; algorithmic novelty is not established. Research hypothesis: guidance may improve search efficiency in suitable domains; current microgrid results weaken an unconditional superiority hypothesis. Validated result: the same engine runs both models and preserves scoped evidence, budgets and independent evaluation. This does not establish general autonomous engineering intelligence.",
    "",
    "Field calibration, physical rupture prediction, AC dynamics, field-certified safety, global search guarantees, general topology mutation, rare-event probability estimation and hardware GPU acceleration are deliberately unclaimed. No sufficient rupture validation data were available; that subsystem remains a research hazard model. Public full-network reference-solver comparisons remain deferred; current independent validation consists of analytical cases and invariant audits.",
    "",
    "## Reproducibility",
    "",
    "The complete search study must be replayed at its recorded clean source revision. Timestamps and wall-clock performance are excluded from scientific hashes. Runtime budgets must not bind for exact replay. Historical 38/200, 44/200 → 13/200 and 4/40 evidence remains immutable.",
    "",
    f"Search source: `{s['code']['git_revision']}`",
    f"Validation source: `{x['code']['git_revision']}`",
    "",
    "```bash",
    "python scripts/replay_history.py",
    "python scripts/replay_twin.py",
    "python scripts/replay_phase5.py",
    "python scripts/phase5_report.py",
    "```",
]
Path("RESEARCH_REPORT_PHASE5.md").write_text("\n".join(lines) + "\n")
