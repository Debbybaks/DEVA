# Hydraulic calibration

`deva.calibration` estimates declared friction multipliers, demand multipliers and prescribed-source head offsets. Parameters have explicit component ownership, finite bounds and units. Overlapping ownership is rejected. Observation records carry timezone-aware timestamps, component/sensor IDs, measured quantities with units, positive one-standard-deviation uncertainty, known operating conditions and explicit SYNTHETIC / REFERENCE / FIELD provenance. FIELD is a provenance category, not a claim that field data currently exist.

The estimator minimises sum_i ((prediction_i(theta) - observation_i) / sigma_i)^2 using bounded SciPy nonlinear least squares. Multiple seeded starts compete only on calibration residuals. Every evaluated operating condition uses the authoritative pressure-dependent hydraulic solver and independent conservation/energy audit. Validation observations cannot influence the estimated parameters. Solver errors stop fitting rather than turning unknown state into a fabricated measurement.

Supported quantities are pressure head (m), signed pipe flow (m³/s), source output (m³/s) and demand service fraction (dimensionless). Storage-level inference is not implemented. Known excitation is assumed; estimating unknown inputs and resistance simultaneously would require further identifiability analysis.

Local covariance is (JᵀJ)^−1 for known independent Gaussian observation noise, where J is the noise-standardised prediction sensitivity. Covariance and standard errors are withheld for rank deficiency or active bounds. Prediction intervals combine measurement variance and local propagated parameter variance. They exclude model discrepancy, input uncertainty, sensor bias and correlated noise; they are not Bayesian credible intervals.

Calibration status requires solver convergence, full local sensitivity rank, no active bounds, held-out standardised RMSE ≤ 2 and held-out prediction interval coverage ≥ 80%. This is a predeclared small synthetic-benchmark acceptance gate, not a field certification or universal calibration standard. A failed gate remains visible as INSUFFICIENT CALIBRATION EVIDENCE.
