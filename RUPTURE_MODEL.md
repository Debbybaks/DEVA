# Bounded research failure hazard

`deva.rupture` evaluates a deliberately uncalibrated phenomenological hypothesis:

λ = λ₀(1+d) + λ_s(1+d)[max(0,p/p_ref − 1)² + max(0,|v|/v_ref − 1)²].

Here λ, λ₀ and λ_s are rates in s⁻¹, d is a dimensionless degradation multiplier, p is the maximum known endpoint pressure head in metres and v is the signed solver velocity in m/s. Reference quantities and coefficients are explicit per-pipe inputs with bounded domains. Unknown pressure is recorded as unknown and contributes no pressure stress; this is a model assumption, not evidence of safety.

For an interval Δt, probability of at least one failure is 1 − exp(−λΔt). A recorded seeded uniform draw determines the event. Closure at the interval end represents immediate isolation after a hypothesised break. Coefficients are chosen to explore failure mechanisms, not inferred from material/fatigue data. No leakage, fracture mechanics, ageing calibration, corrosion law or transient pressure wave is modelled. Real-world physical rupture prediction remains unmodelled.

Increasing stress increases hazard rather than deterministically guaranteeing failure. Pressure state and hazard are separate objects. Tests check rate monotonicity, signed-velocity symmetry and probability calculations.
