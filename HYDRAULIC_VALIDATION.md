# Hydraulic validation strength

Tests derive reference results independently of the nonlinear implementation. For a one-pipe, partially served demand with zero elevation, requested d and source Hs, PDD implies y²=d² H/p_full and energy implies Hs−H=r y². Thus H=Hs/(1+r d²/p_full). For full service, H=Hs−r d². Parallel pipes satisfy Q1/Q2=sqrt(r2/r1); equivalent r is (Σ 1/sqrt(r_e))^-2. Prescribed reservoir heads give signed flow Q=sign(ΔH)sqrt(|ΔH|/r). Tests check these expressions, pressure, direction, continuity and the independent audit.

The zero-head case exposed a convergence error with nonzero initial flow. The correction initializes the exact dry zero-flow equilibrium when equal reservoir heads are below all elevations. Tolerances were not loosened. This is retained as an analytical regression test. Disconnections expose unknown absolute heads, not invented zero pressure measurements.

Temporal tests compare constant-demand storage depletion/refill to exact volume balance, inspect imposed-event states and verify exact shortening at storage exhaustion. A variable-flow partial-service case tests the closed-form tank ODE and decreasing first-order discretisation error under step refinement. Global volume accounting includes spill and truncation.

Operating-bound tests preserve reverse source injection and reject supply-limit violations. More diameter is explicitly tested as potentially unsafe: unequal reservoir heads can increase reverse flow. Numerical output tampering is rejected even if a claimed pass flag or pressure datum is forged.

The Z3 bounded reachability result is replayed from its stored SMT-LIB; the encoding is compared to exhaustive outage enumeration. That validates the Boolean model scope, not hydraulic reality.

Acceptance tolerances: continuity 1e-8 m³/s; Darcy energy 1e-6 m; service fraction comparisons 1e-7. Analytical comparisons are generally six decimal places for head, eight for flow. Exact symbolic evidence is kept separate from floating-point numerical validation.

No independent EPANET run, published full-network benchmark, field calibration, viscosity/Reynolds-friction validation or hardware-in-the-loop experiment has been completed. Analytical references and conservation are substantial validation of the implemented equations, not certification that the equations adequately describe any particular real network.
