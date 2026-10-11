# Multi-objective optimisation

The continuous design LP remains the exact numerical optimiser for cost across specified constraints; its mathematical scope is unchanged. Evolution explores competing objectives with constrained Pareto dominance: cost, empirical training failure rate, and mean unmet demand (m³/h), all minimised. Candidates that fail any declared service/budget constraint cannot parent the next generation. Equal objective points may coexist with different ancestry.

An empirical Pareto frontier means no other evaluated feasible candidate is better in all objectives and strictly better in at least one. It is not the global frontier over all capacities, and confidence intervals can overlap. No environmental-impact objective is invented without lifecycle data. No Bayesian optimiser, gradient surrogate, JAX or deep learning is needed for the present six-pipe problem.

Recommendation policy is explicit: among declared-feasible training frontier candidates, minimise training failure rate, then unmet demand, then cost and stable ID. This is one policy, not a universal best design. Held-out comparisons remain visible and do not retroactively redefine selection.

Adversary: enumerate up to two pipe outages crossed with nominal and adverse demand/supply corners, bounded by a recorded evaluation limit. Find the smallest disturbance lexicographically within that family. It is not calibrated plausibility. Unit-edge min-cut gives the exact fewest installed-pipe deletions disconnecting each demand node from sources in the abstract graph, checked by reachability. Demand bisection brackets the largest passing multiplier under each single outage. The adaptive dispatcher has no temporal cascade; red-team outcomes are deliberately selected, not IID samples.
