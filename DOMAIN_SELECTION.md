# Version 1 domain selection

Decision: budget-constrained emergency water-distribution capacity planning. Select continuous pipe delivery capacities on a fixed directed network serving hospitals and shelters from multiple sources. Evaluate nominal service, individual pipe losses, loss of a shared supply corridor, source shortage, demand surge, and combined events.

| Domain | Depth | Feasibility | Outputs | Visual opportunity | Model defensibility |
|---|---|---|---|---|---|
| Water delivery capacity | Graph cuts, LP, reliability | High for capacity abstraction | Delivered volume, service, cost | Flow, bottlenecks, outages | Conservation and capacity bounds |
| Full hydraulic water twin | Nonlinear hydraulics | Lower without calibrated data | Pressure and flow | Strong | Requires roughness, elevations, pump data |
| Microgrid | Dispatch and storage optimisation | Medium | Energy, unmet load | Strong | Requires temporal weather and device models |
| Bridge geometry | Structural mechanics | Low for first complete core | Stress and deflection | Strong | Meshing and material validation required |

This is a capacity planning abstraction, not a hydraulic digital twin. A feasible flow does not establish adequate pressure or potable delivery. Directed pipes encode permitted transport direction; real bidirectional networks need a shared-capacity formulation.

Exact demonstration: minimise installed capacity cost subject to a 95% minimum demand fraction at every demand node across a declared finite scenario set. Starting alternatives are a nominally sized network and uniform allocations. Robust LP synthesis competes with them. Then independently test seeded random combined failures and demand/supply uncertainty. The first implementation assumes known topology and continuous capacities. Construction discreteness and topology search are later phases.

Acceptance: known chain/parallel cases within 1e-7; conservation and capacity residuals below 1e-7; no robust designation if any required scenario fails; byte-identical scientific outputs under identical seed/configuration/software; all rejected alternatives retained; held-out sampling cannot certify safety.
