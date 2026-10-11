# Second-domain selection

Selected: islanded microgrid **energy adequacy**, with chronological renewable/generator dispatch and battery storage. Its different temporal state equations test whether the same engine works beyond static water transport without embedding physics in the agent.

| Candidate | Depth / feasibility / validation | Decision |
|---|---|---|
| AC distribution | Strong physics, but nonlinear voltage/protection and independent benchmark integration significantly widen validation scope | Defer |
| DC transmission | Defensible linear network physics; similar graph structure offers a less decisive contrast to water | Defer |
| Transportation flow | Feasible and visual; too close to the existing capacity-flow foundation for this first generalisation test | Defer |
| Microgrid energy adequacy | Time-coupled storage, losses, outages, power/energy limits; analytically testable LP and clear optimisation variables | Select |

This is not an electrical digital twin or industrial microgrid controller. Perfect-foresight dispatch is an optimistic planning bound; no AC voltage/frequency, protection, stochastic rupture, converter dynamics, tariffs, lifecycle pricing or field calibration is claimed. Public-reference integration remains future work; validation currently rests on independently derived analytical cases and conservation, not DEVA-generated truth alone.
