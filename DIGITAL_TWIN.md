# Digital-twin knowledge state

Every component quantity is categorised independently:

- OBSERVED: measured synthetic/reference/field quantity with timestamp, noise uncertainty and provenance.
- ESTIMATED: prediction from parameters inferred from calibration observations; records model status, residual and local parameter uncertainty.
- SIMULATED: prediction from the original model under a declared condition.
- FORECAST: conditional prediction for an unobserved future operating condition, never a measurement.
- UNKNOWN: disconnected or unavailable quantity; not zero pressure.

`deva.digital_twin` preserves these categories in machine-readable state. Synthetic data remain labelled synthetic after successful calibration. Prefix refits show how estimates change as dated synthetic observations accumulate; this is offline incremental architecture, not online field operation or a Kalman state estimator. Withheld observations are never used to update parameters.
