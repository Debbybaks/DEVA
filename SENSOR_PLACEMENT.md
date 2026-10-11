# Bounded experimental design

`deva.calibration.sensor_placement` evaluates every layout of up to three sensors from at most twelve registered observation locations. A sensor covers its measurements over the declared excitation series. Each layout retains local rank and singular values.

The criterion log det(I + J_scaledᵀ J_scaled) uses noise-weighted sensitivities and parameter-range scaling. The identity stabilises rank-deficient layouts and sets a dimensionless design reference; it is not an inferred Bayesian prior. The selected layout maximises this local information proxy at the specified model parameters. Scores decrease as declared measurement noise increases.

Single-sensor scores are value-of-information proxies for an empty starting layout. They are not monetary value, posterior entropy reduction or guaranteed identification. Cost-sensitive placement, sensor failure, unknown operating inputs and global nonlinear design remain future work.
