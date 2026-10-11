# Evidence hierarchy

UNTESTED: no successful model evaluation. SIMULATED: nominal model ran and residuals passed. STRESS TESTED: declared stress scenarios ran with valid numerical solutions, regardless of requirement failure. ROBUST UNDER TESTED CONDITIONS: cost/capacity constraints and every declared scenario meet the specified minimum per-node fraction. FORMALLY VERIFIED: unavailable in this implementation.

Stage labels describe earned evidence, not safety certification. Failed requirements appear alongside stress-tested status. Held-out failures do not erase the fact that declared scenarios passed, but prohibit broad robustness claims; each status must state its scope. A solver error is an invalid experiment, never a passing scenario.

Verification independently recomputes cost, capacity bounds and scenario service margins from outputs. Operational residuals are checked after each solve. A numerical feasible solution remains numerical evidence. Future exact certificates can prove feasibility in a finite abstract model but cannot prove the model matches reality.

Success gates: analytical and invariant tests pass; nominal and scenario outputs are retained; rejected designs remain visible; infeasible synthesis returns explicit failure; confidence intervals identify sampling assumptions; replays match science outputs; fresh experiment timestamps do not affect deterministic experiment identity.
