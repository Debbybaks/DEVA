# Hydraulic Model V2 — coupled research model

`deva.hydraulic_v2` is the primary new scientific model, `hydraulic-pdd-darcy-0.3.0`. Historical directed transport experiments remain untouched. The new input is `examples/emergency_water_hydraulic.json`: explicitly synthetic pipe geometry, elevations, reservoir heads, a diameter catalogue and an illustrative construction-cost model. It is not surveyed infrastructure.

| Variable | Meaning | Canonical unit | Domain/assumption |
|---|---|---|---|
| H | Hydraulic head at node | m | Real; reservoir prescribed, isolated absolute head unknown |
| z | Node elevation | m | Real datum-relative height |
| p-head = H−z | Pressure head | m | May be negative; zero service at nonpositive pressure |
| Q | Signed pipe flow | m³/s | Either direction; pipe list orientation is reference only |
| d, y | Requested and delivered withdrawal | m³/s | d≥0, 0≤y≤d |
| D, L | Internal diameter and pipe length | m | Positive; catalogue D for synthesis |
| f | Darcy friction factor | dimensionless | Positive fixed parameter, not Reynolds-calibrated |
| g | Gravitational acceleration | m/s² | 9.80665 |
| v | Signed mean pipe velocity | m/s | 4Q/(πD²) |
| V, A | Mixed tank volume and horizontal area | m³, m² | 0≤V≤Vmax, A>0 |
| t | Extended-period integration time | s | Nonnegative; explicit integration boundaries |
| q-in | External tank inflow | m³/s | Nonnegative prescribed rate |
| c | Illustrative construction cost | synthetic units | Σ L rate100mm (D/0.1m)^1.5; uncalibrated |

Every dimensional input uses `{value, unit}`; `deva.units` checks dimension and converts at the parser boundary. Pressure in Pa cannot silently replace pressure head in m. The kernel uses SI exclusively; display projection converts flow to m³/h explicitly in Python. Numerical multipliers are dimensionless; scenario head offsets carry an explicit `_m` suffix.

Continuity: BQ=y at each non-boundary node. Darcy–Weisbach: H_i−H_j = r Q|Q|, r=8fL/(gπ²D⁵). Pressure-dependent delivery uses a Wagner-style square-root relation: y=d sqrt(clip((H−z)/p_full,0,1)). The service cut-off is zero pressure; minimum required pressure is a separate operating constraint, not the cut-off. See the EPA EPANET 2.2 documentation for established pressure-dependent network formulations: https://www.epa.gov/water-research/epanet. This implementation does not reproduce all EPANET friction, valve or pump semantics.

Sources are prescribed-head reservoirs. Source withdrawals and reverse absorption are computed; operating requirements reject excess supply or backflow. The solver does **not** enforce a pump curve or magically regulate a source at its supply bound. A computed bound violation therefore fails the design and invalidates the source operating assumption. Closed pipes carry zero flow. Unanchored islands receive zero service and unknown absolute pressure; no arbitrary datum is shown as measured pressure.

The dimensionlessly scaled coupled flow/head nonlinear residual is solved with SciPy least_squares. Accept only successful solves whose independently recomputed continuity residual is ≤1e-8 m³/s and energy residual ≤1e-6 m. PDD, boundary heads, velocities and requirement flags are independently recomputed. Solver failure is preserved as an unknown physical state and conservative failed evaluation.

A design passes only when per-demand service reaches the target, minimum pressure is met, pipe velocity is within its limit, source withdrawals obey their operating bounds, and cost is within budget. A successful topology proof does not promote any of these requirements. Catalogue evolution evaluates real hydraulic states before selecting; the training recommendation is frozen before validation/held-out streams are generated.

Extended-period storage: H_tank=H_base+V/A and dV/dt=q_in−q_out. A first-order conservative explicit integrator re-solves hydraulics at each stored state. Steps shorten at empty volume; tank outlet closes until refill. Overflow is recorded and conservation includes it. Events occur at specified integration-step boundaries; they are not falsely labelled as fixed physical timestamps if a preceding interval shortened. No interpolated frames, pipe inertia, water hammer, contaminants or calibrated recovery process exists.
