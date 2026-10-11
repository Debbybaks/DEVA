# DEVA synthetic digital-twin Engineering Evidence Package

Select explicit pipe diameters for pressure-dependent emergency service under reservoir-head and outage uncertainty, exposing construction-cost tradeoffs.

Experiment: `deva-twin-882834fc7dd2ec29`
Scientific SHA256: `882834fc7dd2ec29dea5e232f1720c175d8cc817dc194fbf65662e274f8e210c`

## Scientific scope

Synthetic hidden-parameter recovery with held-out observation validation. No field calibration or real-world rupture prediction claimed. Historical 38/200 and 44/200 → 13/200 experiments remain separate and immutable.

## Observations and mathematical model

Pressure-dependent service, fixed-friction Darcy–Weisbach head loss, signed flow, conservation, prescribed source heads and independent numerical audits. Observation units: pressure head m; signed flow m³/s; known independent Gaussian noise. Five calibration epochs / 20 measurements, four withheld epochs / 16 measurements.

## Calibration and identifiability

Status: BENCHMARK CALIBRATED; local sensitivity rank 3/3.

- west-resistance: initial 1.0, estimate 1.24286645, ground truth 1.25, local standard error 0.006447093648120853; unit 1.
- east-resistance: initial 1.0, estimate 0.84154370, ground truth 0.85, local standard error 0.008143041991949769; unit 1.
- demand-coefficient: initial 1.0, estimate 1.08198425, ground truth 1.08, local standard error 0.0012273502037365702; unit 1.

```json
{
  "calibration": {
    "weighted_rmse": 0.82921272991071,
    "initial_weighted_rmse": 28.89567521944378,
    "rmse_by_quantity": {
      "flow": 2.4215311982612675e-05,
      "pressure": 0.08034721327368725
    },
    "interval_coverage_95": 1.0
  },
  "validation": {
    "weighted_rmse": 1.1408342840624806,
    "initial_weighted_rmse": 28.122041146042577,
    "rmse_by_quantity": {
      "flow": 4.639895783176541e-05,
      "pressure": 0.08970943932366501
    },
    "interval_coverage_95": 0.9375
  }
}
```

Known independent Gaussian measurement noise; local linearised covariance. No field/model-discrepancy calibration, global uniqueness or Bayesian posterior claimed.

## Observation design

Recommended two-sensor layout: east-meter, west-meter.
Local information proxy with identity regularisation, independent known noise and fixed excitation; not monetary value or global identification guarantee

Given ['west-meter'], highest conditional information-gain recommendation: {'sensor': 'east-meter', 'information_score': 30.994422201264832, 'information_gain': 12.956104165763165}.

## Research-hazard cascade

λ = λ₀(1+d) + λs(1+d)[max(0,p/pref−1)² + max(0,|v|/vref−1)²]. Interval event probability = 1−exp(−λΔt). Coefficients uncalibrated; closure approximates isolation, not leakage/fracture physics.
- 360.0 s: west-trunk failure; probability 0.18203550, recorded draw 0.13566807, hazard change 0.00322913 s⁻¹; resulting service 0.000000.

## Autonomous engineering investigation

Stopping reason: BOUNDED CATALOGUE EXHAUSTED / INSUFFICIENT TARGET EVIDENCE
Selected candidate: agent:c002; requested target achieved: False.

- agent:c000: cost 368.951216; training failures 4/12; rejection None; mutation baseline.
- agent:c001: cost 395.325706; training failures 3/12; rejection None; mutation {'pipe': 'west-trunk', 'diameter_before_m': 0.125, 'diameter_after_m': 0.15}.
- agent:c002: cost 395.325706; training failures 2/12; rejection None; mutation {'pipe': 'east-trunk', 'diameter_before_m': 0.125, 'diameter_after_m': 0.15}.
- agent:c003: cost 384.775910; training failures 3/12; rejection None; mutation {'pipe': 'west-hospital', 'diameter_before_m': 0.125, 'diameter_after_m': 0.15}.
- agent:c004: cost 384.775910; training failures 4/12; rejection None; mutation {'pipe': 'east-hospital', 'diameter_before_m': 0.125, 'diameter_after_m': 0.15}.
- agent:c005: cost 384.775910; training failures 3/12; rejection None; mutation {'pipe': 'east-shelter', 'diameter_before_m': 0.125, 'diameter_after_m': 0.15}.
- agent:c006: cost 384.775910; training failures 4/12; rejection None; mutation {'pipe': 'west-shelter', 'diameter_before_m': 0.125, 'diameter_after_m': 0.15}.

calibrate_model completed; recorded authoritative scientific output.
recommend_observations completed; recorded authoritative scientific output.
inspect_baseline completed; recorded authoritative scientific output.
run_sensitivity_analysis completed; recorded authoritative scientific output.
generate_candidates completed; recorded authoritative scientific output.
simulate_training completed; recorded authoritative scientific output.
search_adversarial_scenarios completed; recorded authoritative scientific output.
validate_selected completed; recorded authoritative scientific output.
verify_property completed; recorded authoritative scientific output.
Candidate agent:c002: 4/40 held-out hospital service/pressure failures; Wilson upper bound 0.230518.

## Property-specific proof scope

- R-TOPOLOGY-BOUNDED: FORMALLY VERIFIED / unsat; Every demand node connects to an active source after at most 1 pipe outages; Only bounded Boolean connectivity; no promotion of hydraulic service or entire design. Proof SHA256 5a48f710d070a1a401adcb639fbc73011b8c0ec17e7e9c3330104ba8a79677cb; counterexample None.
- R-TOPOLOGY-BOUNDED: COUNTEREXAMPLE / sat; Every demand node connects to an active source after at most 2 pipe outages; Only bounded Boolean connectivity; no promotion of hydraulic service or entire design. Proof SHA256 None; counterexample ['west-trunk', 'east-trunk'].

## Scientific claim ledger

- Held-out pressure RMSE 0.089709 m under the synthetic benchmark. Evidence: science/calibration/rows/validation; status BENCHMARK CALIBRATED; limitations: Not field calibration or external validation.
- Local sensitivity rank 3/3. Evidence: science/calibration/fitted_identifiability; status NUMERICAL IDENTIFIABILITY; limitations: Not a global uniqueness proof.
- 1 research-hazard failures in the selected seeded trajectory. Evidence: science/cascade/events; status UNCALIBRATED RESEARCH HAZARD; limitations: Uncalibrated hazard coefficients; no field rupture reliability claim. Quasi-steady hydraulic solves; no transient pressure waves or physical propagation timing. Interval-end Bernoulli failures use pre-interval hazards; step-size dependence must be examined. Pipe closure approximation omits leakage before isolation and repair resources. Simultaneous consequences are jointly computed, not unique causal attribution.

## Limitations

- Synthetic data generated with same equations; no field calibration or independent physical validity established.
- Local sensitivity rank does not prove global parameter uniqueness.
- Gaussian independent noise and known excitation assumed; sensor bias and correlated noise unmodelled.
- Local linearised prediction intervals exclude structural model error.
- Research rupture hazard, if evaluated separately, is uncalibrated; real-world rupture prediction remains unmodelled.
- Uncalibrated hazard coefficients; no field rupture reliability claim.
- Quasi-steady hydraulic solves; no transient pressure waves or physical propagation timing.
- Interval-end Bernoulli failures use pre-interval hazards; step-size dependence must be examined.
- Pipe closure approximation omits leakage before isolation and repair resources.
- Simultaneous consequences are jointly computed, not unique causal attribution.

## Reproduction

```bash
.venv/bin/python -m deva.digital_twin examples/emergency_water_hydraulic.json --seed 20261030 --output /tmp/twin-replay.json
.venv/bin/python scripts/replay_history.py
```

Use scientific source revision `b780be432e9f8275125c5ecfefb9d77a00863ba6`; source fingerprint `b7a6129a677bd1105b2f7b26064dc86bfcccbcdaf5a795dc7bf59f26eead22a2`.
Software: {"python": "3.12.14", "numpy": "2.3.5", "scipy": "1.17.0"}
Compare science payload and SHA256; timestamps/performance measurements are excluded. Independent seeds, all observations, rejected candidates, solver evaluations, policies, draws, cascade frames and proof objects are in the JSON package.
