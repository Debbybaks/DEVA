# Frozen autonomous investigation: remaining failure analysis

Source: `deva-twin-882834fc7dd2ec29`, selected `agent:c002`, 4 hospital service/pressure failures in 40 independently held-out scenarios. Observed failure rate 10%; Wilson 95% interval approximately [3.958%, 23.052%]. Requested 2% target remains unestablished. Even zero failures in 40 samples would not establish a 2% upper bound at this confidence level.

`deva.agent_diagnosis` validates both source hashes, independently audits new hydraulic states and requires original failed states to replay exactly. It retains every failure, four controlled counterfactuals per case, single-outage probes and every single-pipe catalogue upgrade, including unsuccessful upgrades. Reproduce:

```bash
.venv/bin/python -m deva.agent_diagnosis artifacts/digital-twin-evidence.json --output /tmp/agent-diagnosis.json
.venv/bin/python -m unittest discover -s tests -p test_agent_diagnosis.py -v
```

## Conditional mechanism

All four cases include east-trunk loss; one additionally closes east-hospital and east-shelter. None disconnects hospital from all sources. The east-trunk outage alone, retaining each case's demand/head conditions, already fails in all four. These are connected hydraulic deficits, not topological isolation and not an observed temporal cascade.

Hospital pressure margins below the 15 m minimum are 0.8343, 3.6096, 4.9361 and 4.6725 m. Service deficits below the specified target are 0.1084, 0.1953, 0.2406 and 0.2314. Demand factors are approximately 1.0046, 1.3654, 1.3939 and 1.3159; source-head shifts are −5.1445, −0.7772, −3.4536 and −4.3787 m. Restoring all outages resolves every case; restoring nominal demand, nominal source head, or both while retaining outages does not. Thus high demand/source depression worsen these cases but are not necessary for failure under the retained outage patterns.

A common mechanism does not establish stochastic correlation. The input trials are sampled independently under the declared synthetic generator; shared outage exposure explains clustering. No field frequency or temporal failure dependence is inferred.

## Diagnostic engineering cost

Selected synthetic construction cost is 395.325706, versus baseline 368.951216 (~7.15% increase), allowed maximum 413.225362 (+12%). A west-trunk 150 mm diagnostic upgrade adds 26.374489 and resolves one of these four cases; 175 mm adds 55.049395 and resolves all four. Total cost of the latter is 450.375100 (~22.06% above baseline), outside the requested bound. Increasing the already-selected east trunk resolves none while it is closed. Other single-pipe upgrades resolve none of the four.

These probes do not exhaust joint substitutions, topology changes or operational controls. They do not prove the target infeasible under the budget. Cost per resolved stored case is a diagnostic metric, not marginal cost per unit population reliability. No candidate was selected or promoted using these reused held-out cases.

## Uncertainty and next experiment

Calibration covariance and structural discrepancy have not been propagated into this failure diagnosis. Parameter inference remains a same-model synthetic benchmark, not field calibration. The next scientific step is a bounded uncertainty propagation study around these cases, distinguishing known measurement-induced local covariance from unmodelled discrepancy. Any subsequent design-search use of these cases converts them into training/diagnostic evidence; generalisation requires a newly generated sealed validation split and sufficient sample size for the intended confidence claim.

Full machine-readable states and negative probes: `artifacts/agent-remaining-failure-diagnosis.json`. Numerical audits and conditional counterfactuals are not formal causal proof.
