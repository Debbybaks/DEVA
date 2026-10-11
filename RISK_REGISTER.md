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
