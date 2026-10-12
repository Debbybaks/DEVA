# DEVA Phase 5 — bounded cross-domain engineering research

Study `deva-cross-domain-82054fcee8506f21`; SHA256 `82054fcee8506f21a4a3a290a6cfc5fc11d8841e573fa496f2aeb75938d57ac6`.
Validation `deva-phase5-validation-f94b6b05592d6d12`; SHA256 `f94b6b05592d6d1235e2b0fef62226e97e1d2eef40c5512ae33a0ac8a2927b2b`.

## Problem and architecture

The research question is whether one bounded, explicit-tool investigation engine can operate across different physical models. Domain-neutral budgets, candidate ancestry, training-only selection, Pareto comparison, counterexample interventions, memory and stopping are implemented in deva.general_engineer. Physics remains in independently validated domain adapters. No LLM or hidden reasoning is required to produce these results.

## Domain contract

Descriptors declare identity/version, units, state, governing equations, constraints, uncertainty, observable quantities, evidence and validity scope. Outcomes and cached records are domain/configuration/model/source scoped. The water adapter calls the existing solver and independent audit without replacing legacy experiments. New source hashes include nested Python modules; old replay identity remains pinned.

## Physical models

Water: steady signed Darcy flow and pressure-dependent service with prescribed sources. Microgrid: chronological energy adequacy with charging/discharging losses, generator outages, renewable limits and power/energy bounds. Lexicographic linear optimisation first maximises worst-interval service and then reduces generation/throughput. Perfect foresight and finite-horizon battery depletion are explicit optimistic planning assumptions. No AC voltage/frequency/protection model is claimed.

## Validation

Water adapter tests compare complete states against unchanged original functions. Microgrid independent analytical cases check two-hour storage-limited service, efficiency loss and converter power limitation. Every state is checked for conservation and bounds. A Z3 rational necessary-energy certificate proves one precisely bounded insufficient-energy case; SAT would not certify a feasible electrical dispatch.

## Autonomous search and experiment design

Five fixed strategies run on three predeclared seeds per domain: random catalogue exploration, incremental evolutionary ordering, witnessed-counterexample ranking, Pareto-parent exploration and hybrid Pareto/intervention ranking. Fixed budgets are 400 simulations, 16 candidates and four generations. Selection uses eight training scenarios only; 12 validation and 40 held-out scenarios are sealed until selection. An additional biased severity attack is separate from IID reliability. Actual solver counts differ between strategies and are preserved. These algorithms are bounded catalogue heuristics, not global optimisation guarantees.

## Search ablation

| Domain | Strategy | Mean held-out failure | Actual solver calls by seed |
|---|---|---:|---|
| water | random | 21.6667% | 172, 172, 140 |
| water | evolutionary | 16.6667% | 188, 164, 116 |
| water | guided | 16.6667% | 188, 164, 116 |
| water | pareto | 16.6667% | 188, 164, 116 |
| water | hybrid | 16.6667% | 190, 164, 116 |
| microgrid | random | 35.8333% | 132, 140, 148 |
| microgrid | evolutionary | 45.8333% | 164, 164, 164 |
| microgrid | guided | 45.8333% | 164, 164, 164 |
| microgrid | pareto | 51.6667% | 188, 188, 188 |
| microgrid | hybrid | 51.6667% | 191, 189, 191 |

Guided search is not established as superior. Water incremental strategies tie on mean held-out failure in this small study. Random exploration is stronger than incremental/guided search on this microgrid catalogue. Three seeds do not support a general statistical superiority claim. No method was retuned after viewing these held-out results. The earlier dirty-source exploratory pilot is retained separately as provisional evidence.

## Larger frozen populations

| Domain | Failures / scenarios | Runtime (s) | Throughput (scenarios/s) |
|---|---:|---:|---:|
| water | 93/512 | 2.786 | 183.76 |
| microgrid | 300/512 | 2.573 | 198.99 |

These populations test fixed hybrid designs using a fresh seed. They do not replace the original held-out study or establish field reliability. Stratified and biased populations deliberately do not receive IID intervals.

## Cost and constraint negotiation

The historical calibrated hospital investigation remains 4/40 and its 2% target unestablished. Three predeclared related designs are compared on a fresh shared 120-scenario population:

| Design | Synthetic construction cost | Hospital failures | 95% Wilson interval |
|---|---:|---:|---|
| current | 395.325706 | 22/120 | [0.12430300356014223, 0.2620091351717033] |
| compromise | 421.700195 | 7/120 | [0.028541010000220295, 0.11552592033630113] |
| upgrade | 450.375100 | 5/120 | [0.017926716880109515, 0.09384085233703535] |

Smallest known relaxation among these tested designs: {'candidate': 'compromise', 'additional_budget': 8.474832583505929, 'observed_failures_removed': 15}. This is an observed engineering benefit, not proof of global minimal relaxation or infeasibility.

## Uncertainty and observation design

Local water covariance propagation from Phase 4 remains preserved. Phase 5 additionally sweeps microgrid discharge-efficiency assumptions without pretending they are calibrated probabilities. The existing water sensor-layout information proxy is compared against 32 seeded random layouts. This measures local identifiability information, not real failure detection.
- Assumed discharge efficiency 0.8: 20/32 failures on common diagnostic scenarios.
- Assumed discharge efficiency 0.9: 19/32 failures on common diagnostic scenarios.
- Assumed discharge efficiency 1.0: 17/32 failures on common diagnostic scenarios.
- Sensor information: best 30.994422; random mean 24.132899.

## Memory, hypotheses and evidence

Physical outcomes are cached by domain, model, configuration, scenario, design and recursive source fingerprint. Durable memory also preserves experiment summaries, failed candidates, seeds, validation results and hypotheses. Hypothesis transitions require domain-correct experimental references and scope. Claims never inherit evidence from another domain. Unknown solver states and budget-incomplete evaluations are retained.

## Visual experience

Engineering Worlds uses progressive experiment loading and exact stored states. Water and microgrid have distinct physical representations. Candidate ancestry, same-scenario parent comparison, X-ray, local uncertainty and evidence lenses expose computations. Researcher Mode can launch bounded registered investigations through process workers and streamed scientific events; Judge and Portfolio modes share the same evidence; Demonstration 3.0 guides stored outcomes and never manufactures success. Responsive numerical 2D is intentional; software 3D remains slow and no WebGPU adapter was available in the measured environment.

## Contributions and limits

Implementation contribution: a domain contract, two different physical adapters and one computationally exercised bounded investigation engine. Engineering contribution: inspectable budget/service trade-offs and retained counterexamples. Algorithmic contribution: an implemented intervention-ranked search heuristic; algorithmic novelty is not established. Research hypothesis: guidance may improve search efficiency in suitable domains; current microgrid results weaken an unconditional superiority hypothesis. Validated result: the same engine runs both models and preserves scoped evidence, budgets and independent evaluation. This does not establish general autonomous engineering intelligence.

Field calibration, physical rupture prediction, AC dynamics, field-certified safety, global search guarantees, general topology mutation, rare-event probability estimation and hardware GPU acceleration are deliberately unclaimed. No sufficient rupture validation data were available; that subsystem remains a research hazard model. Public full-network reference-solver comparisons remain deferred; current independent validation consists of analytical cases and invariant audits.

## Reproducibility

The complete search study must be replayed at its recorded clean source revision. Timestamps and wall-clock performance are excluded from scientific hashes. Runtime budgets must not bind for exact replay. Historical 38/200, 44/200 → 13/200 and 4/40 evidence remains immutable.

Search source: `48f51811e84afe9630ff05a4f42518d9242866a5`
Validation source: `67c8c770cd8affd7064f5337f943cebb2e9d1ef0`

```bash
python scripts/replay_history.py
python scripts/replay_twin.py
python scripts/replay_phase5.py
python scripts/phase5_report.py
```
