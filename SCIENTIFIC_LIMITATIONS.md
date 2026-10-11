# Scientific limitations — always visible

* The historical 38/200 failures remain an immutable baseline, not a defect to erase.
* Capacity-network evolution is steady-state transport, with perfect recourse, continuous capacities, fixed directed topology and synthetic hazards.
* Pressure is absent from the capacity solver. The separate Darcy–Weisbach adapter requires physical geometry and is not linked to capacity cost, calibrated, pressure-dependent or transient.
* No topology mutations, source construction, pumps, storage, sensor inference, repair/recovery, dynamic cascade, water quality or contamination are implemented.
* Min-cut witnesses establish topological vulnerability within a graph; they do not establish physical resilience.
* Pareto and reliability results are empirical over declared scenario families and finite samples. Sampled success is not proof, and repeated adaptive selection can overfit training. Validation and held-out audits remain separate.
* Independent audit recomputes numerical primal feasibility; no rational primal/dual certificate, theorem prover or model checker exists. MATHEMATICALLY VERIFIED and FORMALLY VERIFIED are unavailable statuses.
* The local API is a research development service, not authenticated multi-tenant production infrastructure. Do not expose it publicly without authentication, quotas and deployment review.
* Network particle motion visualises steady-state flux; it is not travel time, velocity or transient physical simulation. Scenario browsing does not constitute a simulation timeline.


## Phase-3 update

Hydraulic V2 is now coupled and analytically validated, but fixed Darcy factors, geometry and cost remain uncalibrated. Source limits are checked rather than pressure-regulated. The optional operational valve cascade is not physical rupture. Formal evidence covers bounded topology only. See HYDRAULIC_MODEL_V2.md, HYDRAULIC_VALIDATION.md and CASCADE_MODEL.md.
