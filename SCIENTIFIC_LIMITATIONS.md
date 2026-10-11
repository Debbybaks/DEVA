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

## Phase-4 distinctions

Synthetic hidden-parameter calibration is implemented and held-out benchmark validation can earn BENCHMARK CALIBRATED. Field calibration remains incomplete. Local numerical rank does not prove globally unique parameter inference. Known independent Gaussian noise, accurate excitation and same-equation truth are assumptions, not measured field properties. Local prediction intervals exclude model discrepancy.

A seeded phenomenological failure-hazard model can produce emergent cascades through solved hydraulic redistribution. It is an uncalibrated research hypothesis. Real-world pipe rupture, leakage, material fatigue, corrosion and transient pressure-wave dynamics remain unmodelled. Conditional causal graphs expose calculations/draws; they do not uniquely identify real-world causal mechanisms. Scheduled repair is exogenous, not autonomous physical recovery.

The Engineering Agent uses bounded deterministic tools and declared catalogue mutations. It can stop without meeting a target and does not claim global optimality, unrestricted natural-language reasoning or real-time field control. Sensor recommendations maximise a local information proxy, not guaranteed economic value. Topology proof remains bounded Boolean connectivity; hydraulic service is numerical evidence only.
