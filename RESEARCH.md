# Research programme

RQ1: How much capacity cost buys resistance to declared single and correlated failures? Compare nominal LP, uniform capacities, and scenario-constrained LP under the same budget.
RQ2: Does robustness to enumerated outages generalise to combined events? Evaluate all candidates on the same independent seeded samples; preserve adversarial counterexamples.
RQ3: Which constraints drive the design? Inspect edge utilisation, per-node service, scenario margins, and paired demand/supply perturbations.
RQ4: Can the interface make the distinction between sampled confidence and bounded guarantees understandable? Later user studies measure correct classification of evidence and time to locate a failure.

Hypotheses are unconfirmed until measured. Synthetic examples validate implementation, not field realism. No field data or literature review has yet established practical calibration. Relevant mathematical foundations: network flow conservation and max-flow/min-cut; linear programming; binomial Wilson intervals. Primary references: Ford & Fulkerson, Flows in Networks (1962); Wilson, Probable Inference, the Law of Succession, and Statistical Inference (1927); SciPy linprog/HiGHS documentation. These are model foundations, not evidence of real-world applicability.

Protocol: freeze configuration and scenario distribution before evaluation; isolate synthesis scenarios from held-out draws; report every candidate and every failure; compare paired samples; log solver/version/tolerance. Future benchmark datasets require provenance and licences. Research risks include simplistic failure distributions and overfitting to the scenario family.

## Phase-2 implementation status

The first new three-generation experiment retains 26 candidates. On one fresh common held-out set, the training-selected design has 13/200 failures versus 44/200 for the original robust capacities, at greater cost. This is a single synthetic experiment; no cross-seed or field generalisation claim is earned. Counterfactual diagnosis establishes 36 original outage–demand interactions and two topology disconnections.
