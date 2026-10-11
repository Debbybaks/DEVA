# Capacity-network model v0.1

Units: demand, supply, flow, and capacity in m³/h. Cost is arbitrary demonstration currency; edge coefficient is currency/(m³/h). Graph G=(V,E), directed incidence matrix B with +1 at head and -1 at tail. Demand d_v≥0 and source limit s_v≥0. Scenario multipliers modify demand, supply, and usable pipe fraction a_e∈[0,1].

Operational variables f_e≥0, injection q_v≥0, delivery y_v≥0, and common service fraction t∈[0,1]. Conservation Bf+q−y=0. Bounds: f_e≤a_e c_e, q_v≤s_v, y_v≤d_v. Require y_v≥t d_v. Maximise t using a linear program. This max-min objective avoids sacrificing a shelter for higher aggregate delivery; t is the guaranteed common fraction, not a unique dispatch. After computing t, maximise total delivery while preserving that service within numerical tolerance. Non-unique edge flows are not unique physical predictions.

Design LP: minimise Σ k_e c_e, with 0≤c_e≤cmax_e and budget Σ k_e c_e≤budget. For each declared scenario include separate f,q,y variables, conservation and capacity inequalities, and y_v≥τd_v. Installed capacities are shared between scenarios; dispatch can adapt after the event (perfect recourse). This assumption needs operational validation. Infeasibility is preserved, never converted into a design. This global optimum applies only to the continuous linear model and declared scenarios, within solver tolerances.

Monte Carlo: independently draw correlated corridor failure, individual outages, global demand multiplier, and global supply multiplier from a documented synthetic distribution. Scenario passes when t≥τ−ε. Estimate p_failure=k/n with a 95% Wilson binomial interval using z=1.959963984540054. Interval validity assumes IID samples from that generator and says nothing about omitted hazards. Seeds and full scenarios are exported.

Numerical validation: check conservation, nonnegative variables, capacities, source limits, demand limits, and common-service inequalities after solver success. No floating-point solver output earns FORMALLY VERIFIED. A future formal certificate must define its scope and independently check a rational primal/dual certificate or another proof artefact.

Exclusions: pressure, friction, elevation, pumps, storage, transients, contamination, repairs, cascading hydraulic failure, sensor state estimation. The current model is steady-state. Sample ordering is not physical time.

## Phase-2 implementation status

The original equations and solver are unchanged. Phase-2 adds constrained empirical Pareto evolution, IID split audits, independent primal checks and unit-edge topological min cuts. See DESIGN_EVOLUTION.md, OPTIMISATION.md, HYDRAULIC_MODEL.md and UNCERTAINTY_MODEL.md. No physical time or formal certificate has been added.


## Phase-3 update

The hydraulic V2 governing equations, units, source operating constraints and storage integration are specified in HYDRAULIC_MODEL_V2.md. Historical capacity mathematics is unchanged; the models do not share a calibrated cost scale.
