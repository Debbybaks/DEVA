# Microgrid energy-adequacy model

Boundary quantities use dimension-checked W, J and s. LP coordinates use explicit kW/kWh/hour conversion to improve conditioning. Solar construction W, battery energy J and converter power W are separate design variables; synthetic cost coefficients are cost units per corresponding canonical quantity.

For every interval t:

- PV_t + G_t + D_t = L_served,t + C_t (W).
- E_(t+1) = E_t + Δt(η_c C_t − D_t/η_d) (J).
- 0 ≤ E_t ≤ installed energy; 0 ≤ C_t,D_t ≤ converter power.
- Available PV follows a prescribed solar profile; generator availability is zero during explicit outage intervals.
- L_served,t ≥ z L_requested,t; first maximise worst-interval service z, then fix its optimum and minimise generator output plus a positive throughput tie-break.

All flows are nonnegative. Initial SOC is prescribed; terminal depletion is allowed, so this is finite-horizon adequacy, not sustainable cyclic dispatch. Perfect foresight is assumed. Charging/discharging are LP-relaxed; losses and a positive throughput tie-break discourage pointless simultaneous cycles, but no mixed-integer exclusive-mode guarantee is claimed. Independently recomputed balances and bounds audit every result.

Analytical reference: with constant 10 kW load for two hours, no generation, 10 kWh initially stored and η_d=1, maximum uniform service is 0.5. With η_d=0.8 it is 0.4. A 2 kW converter limits service to 0.2 even with 100 kWh storage. These independent results test different physical constraints.

A necessary energy-availability inequality is recorded, not promoted into a sufficient guarantee. HiGHS numerical optimisation does not constitute formal proof. No full AC, frequency, protection or field-validity claim exists.
