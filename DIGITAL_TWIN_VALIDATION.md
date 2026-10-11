# Digital-twin validation route

The immutable Phase-3 baseline was locked before development: 67 Python tests, 8 frontend tests, 4 browser tests and the production build passed. All three historical scientific payloads replayed exactly. The original artifact byte hash remains `14e632693c8f4b9549bb326310715f719b068da373a2feeae1c9d641378ecd5e`. Bounded Z3 topology results remain UNSAT for single outages and SAT for a two-outage counterexample; hydraulic service is not formally proved.

Phase-4 scientific tests validate observation dimensions/provenance, hidden/noiseless parameter recovery, held-out separation, altered-validation rejection, local rank deficiency, sensor information weighting, conditional value of information, explicit knowledge state, hazard probability/monotonicity, seeded cascade replay, independent frame audits, causal reference integrity, scheduled repair, ensembles, tool budgets, sealed agent validation, stored claim references, counterexample conversion, process jobs and GPU projection consistency. Full benchmark replay compares scientific payloads, not volatile timestamps or performance measurements.

Frontend and live-browser tests use actual Python projections. They inspect measured versus estimated values, shared-world comparison, stored event time, proof scope, agent stopping, responsive controls during worker jobs and numerical fallback. Shader movement is a representation of solved steady flow, not an independently validated transient simulation.

The synthetic truth and estimator use the same equations. This validates controlled parameter inference but cannot establish external physical fidelity. Existing analytical hydraulic validation remains necessary and does not become field validation because calibration residuals are low. Local covariance/prediction intervals exclude model discrepancy. Research hazard coefficients remain uncalibrated.

See `artifacts/phase4-validation.json` for final counts, replay identities, validation scope and retained development failures. No existing test assertion or timeout was weakened.

Resumed milestone: 96 complete Python tests, 12 frontend tests, six complete browser tests and production build pass. Provenance-only calibration-risk output metadata was subsequently checked with its three targeted tests. Both pinned replay helpers now pass: three historical payloads plus the complete immutable twin package. Original 38/200 artifact bytes remain unchanged. The diagnosis and local covariance ensemble add conditional evidence, not a new reliability target claim.
