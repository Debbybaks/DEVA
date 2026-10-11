# Calibration uncertainty in frozen failure cases

`deva.calibration_risk` propagates the existing local calibration covariance through actual audited hydraulic solves for the four frozen hospital failures. The same parameter vector is shared across cases in each draw. This represents common estimation uncertainty; it does not create physical outage correlation.

The distribution is a local Gaussian estimation-error approximation around the synthetic fit. Parameter bounds are enforced by rejection, never clipping. Invalid covariance, unidentified/active-bound fits, parameter-order mismatch and mismatch between the agent model and calibration estimate are rejected. Unknown solver states remain explicit. No new candidate is selected and no new population reliability estimate is produced.

The reproducible 64-draw ensemble (seed 20261031) retains every parameter vector and full hydraulic result. All four cases fail in all 64 draws; no unknown states or out-of-bound rejected draws occurred. Hospital pressure 2.5–97.5 percentile ranges are approximately:

| Frozen case index | Pressure range (m) |
|---|---|
| 0 | 14.0977–14.2356 |
| 9 | 11.3164–11.4668 |
| 18 | 9.9965–10.1334 |
| 36 | 10.2616–10.3955 |

All ranges lie below the 15 m requirement. Under this limited local covariance model, the observed deficits are substantially larger than the calibration-estimation spread. This does not exclude structural model error, sensor bias, unknown demand distribution or field parameter uncertainty; those remain unmodelled. Percentiles are finite ensemble summaries, not guaranteed intervals or a Bayesian posterior.

```bash
.venv/bin/python -m deva.calibration_risk artifacts/digital-twin-evidence.json --samples 64 --seed 20261031 --output /tmp/calibration-risk.json
.venv/bin/python -m unittest discover -s tests -p test_calibration_risk.py -v
```

Machine-readable evidence: `artifacts/calibration-failure-uncertainty.json`, linked to the unchanged source experiment by full SHA256. A zero-covariance test independently checks that this propagation path exactly recovers stored point predictions. Future redesigns need newly sealed held-out scenarios; these four cases are now diagnostic data.
