# Synthetic hidden-parameter benchmark

`python -m deva.digital_twin examples/emergency_water_hydraulic.json --seed 20261030 --output /tmp/twin.json` generates five calibration operating conditions and four disjoint validation conditions from independent SeedSequence streams. Each condition observes hospital/shelter pressure and west/east trunk signed flow. Noise standard deviations are 0.08 m and 0.00004 m³/s.

Ground truth uses west friction multiplier 1.25, east multiplier 0.85 and demand multiplier 1.08. The estimator receives initial values 1, bounds, observations and base model; it does not receive ground truth. Ground truth is unsealed only for parameter-error evaluation. This same-equation benchmark validates recovery and prediction under controlled noise, not model fidelity to reality.

Initial validation standardised RMSE was 28.122; fitted validation RMSE was 1.141, with pressure RMSE 0.0897 m, flow RMSE 0.0000464 m³/s and prediction interval coverage 15/16. These are computed preliminary results preserved in `artifacts/development`; final scientific packages record code revision and source fingerprint.

Tests cover noiseless recovery, noisy recovery, dimensions, disjoint splits, rank deficiency, deterministic generation and rejection of altered validation observations. Increasing validation measurements by 100 standard deviations leaves fitted parameters exactly unchanged and revokes accepted calibration status.
