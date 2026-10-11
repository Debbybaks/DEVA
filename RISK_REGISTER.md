# Risk register

| Risk | Impact | Mitigation / evidence required | State |
|---|---|---|---|
| Capacity abstraction mistaken for hydraulics | Unsafe real-world interpretation | Prominent scope in every evidence package; calibrated hydraulic adapter | Open |
| Perfect adaptive dispatch unrealistic | Overstated resilience | Document recourse; future operational policy simulation | Open |
| Synthetic hazard distribution | Invalid real-world probabilities | Label intervals conditional; calibrated data needed | Open |
| Scenario overfitting | Combined failures escape synthesis | Separate declared and held-out samples; retain failures | Controlled within demo |
| Floating point tolerances | False pass | Independent residual checks, margin threshold, analytical cases | Tested numerically |
| Unbounded input computation | Resource exhaustion | Graph/sample caps; future worker quotas | Local caps implemented |
| Continuous capacities not buildable | Unrealistic design | Discrete catalogue/MILP later | Open |
| Multiple optimal flows | Misleading geometry | State nonuniqueness; do not treat flow as physical prediction | Documented |
| Seeds across library versions | Replay drift | Record software versions; replay scientific payload comparison | Same-environment tested |
| Visual spectacle hides limitations | Loss of scientific credibility | Earned labels and direct evidence navigation | UI acceptance gate |
| No field validation | Research extrapolation | Independent hydraulic/field comparisons before deployment | Open |

## Phase-2 implementation status

Additional Phase-2 risks: training Pareto overfitting (sealed held-out audits); software-GPU frame cost (measured, reduced DPR, selectable/automatic low-load mode); large evidence views (direct JSON response serialization, future paging); native solver cancellation latency (cooperative checkpoints); local API lacks authentication (loopback-only research use). Hydraulic calibration and independent physical validation remain open.

## Phase-4 research risks

- Same-equation synthetic calibration can conceal structural model error. Mitigation: explicit SYNTHETIC labels, held-out excitation and no field-validity claim; obtain independent reference/field data before certification.
- Local sensitivity rank can imply false global uniqueness. Mitigation: retain singular values/condition/correlations, label local scope and withhold covariance for rank deficiency/bounds.
- Phenomenological hazard can be mistaken for material rupture prediction. Mitigation: separate hazard/state, expose coefficients and draws, preserve UNMODELLED field-rupture limitation and no CFD/transient claims.
- Interval-end stochastic cascades depend on timestep. Mitigation: retain timestep and full pre/post states; convergence of cascade statistics is an outstanding gate.
- Reusing audit data to design future candidates biases generalisation. Mitigation: frozen training selection, disjoint streams and explicit post-hoc labels; new investigations require new sealed seeds.
- Software GPU rendering can impede interaction. Mitigation: measured adaptive 2D fallback and unchanged scientific values; no unsupported WebGPU speedup claim.
