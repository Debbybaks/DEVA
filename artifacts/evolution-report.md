# DEVA Engineering Evidence Report

Experiment: `deva-evolution-0bea3589cd34a9d0`

Deliver at least 95% of hospital and shelter demand despite each declared outage within a 700-unit capacity budget.

Scientific SHA-256: `0bea3589cd34a9d0c7b2800925037c63de6a0daddacc93b90943515efee0bce4`

## Candidate evidence

| Candidate | Generation | Cost | Training failures | Validation failures | Held-out failures | Evidence |
|---|---:|---:|---:|---:|---:|---|
| g0-c000 | 0 | 199.500 | 47/60 | 65/80 | 163/200 | STRESS TESTED |
| g0-c001 | 0 | 399.000 | 7/60 | 11/80 | 44/200 | ROBUST UNDER TESTED CONDITIONS |
| g0-c002 | 0 | 570.000 | 0/60 | 5/80 | 10/200 | ROBUST UNDER TESTED CONDITIONS |
| g0-c003 | 0 | 498.750 | 1/60 | 5/80 | 17/200 | ROBUST UNDER TESTED CONDITIONS |
| g1-c004 | 1 | 604.367 | 0/60 | 5/80 | 10/200 | ROBUST UNDER TESTED CONDITIONS |
| g1-c005 | 1 | 595.000 | 0/60 | 5/80 | 10/200 | ROBUST UNDER TESTED CONDITIONS |
| g1-c006 | 1 | 549.288 | 0/60 | 5/80 | 13/200 | ROBUST UNDER TESTED CONDITIONS |
| g1-c007 | 1 | 503.796 | 1/60 | 5/80 | 17/200 | ROBUST UNDER TESTED CONDITIONS |
| g1-c008 | 1 | 429.731 | 5/60 | 9/80 | 35/200 | ROBUST UNDER TESTED CONDITIONS |
| g1-c009 | 1 | 402.800 | 7/60 | 11/80 | 42/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c010 | 2 | 612.982 | 0/60 | 5/80 | 10/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c011 | 2 | 549.346 | 0/60 | 5/80 | 13/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c012 | 2 | 532.558 | 0/60 | 5/80 | 13/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c013 | 2 | 510.085 | 1/60 | 5/80 | 15/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c014 | 2 | 451.552 | 2/60 | 7/80 | 30/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c015 | 2 | 434.582 | 5/60 | 9/80 | 33/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c016 | 2 | 439.188 | 4/60 | 9/80 | 34/200 | ROBUST UNDER TESTED CONDITIONS |
| g2-c017 | 2 | 382.318 | 8/60 | 11/80 | 45/200 | STRESS TESTED |
| g3-c018 | 3 | 614.543 | 0/60 | 5/80 | 10/200 | ROBUST UNDER TESTED CONDITIONS |
| g3-c019 | 3 | 527.702 | 2/60 | 6/80 | 22/200 | ROBUST UNDER TESTED CONDITIONS |
| g3-c020 | 3 | 555.288 | 0/60 | 5/80 | 13/200 | ROBUST UNDER TESTED CONDITIONS |
| g3-c021 | 3 | 532.500 | 1/60 | 5/80 | 17/200 | ROBUST UNDER TESTED CONDITIONS |
| g3-c022 | 3 | 477.863 | 0/60 | 6/80 | 24/200 | ROBUST UNDER TESTED CONDITIONS |
| g3-c023 | 3 | 441.363 | 5/60 | 10/80 | 42/200 | STRESS TESTED |
| g3-c024 | 3 | 459.406 | 2/60 | 7/80 | 29/200 | ROBUST UNDER TESTED CONDITIONS |
| g3-c025 | 3 | 436.814 | 5/60 | 9/80 | 37/200 | ROBUST UNDER TESTED CONDITIONS |

## Scope and limitations

- Numerical steady-state capacity model, not hydraulics
- Synthetic hazards, not field probabilities
- Training frontier is empirical, not a global Pareto guarantee
- Adversarial search bounded and non-IID
- No temporal cascade or recovery
- No mathematical or formal verification

No numerical simulation or Monte Carlo result is mathematical or formal verification. Negative results are retained in the full JSON package.

## Reproduction

Software: `{"numpy": "2.3.5", "python": "3.12.14", "scipy": "1.17.0", "solver": "HiGHS"}`

```bash
python -m deva.evolve_cli examples/emergency_water.json --seed 20261013 --generations 3 --train-samples 60 --validation-samples 80 --test-samples 200 --output replay.json
```

Use the exact `science.configuration` from the package when it differs from the example. Seed streams, every failure, sensitivities, attack witnesses and provenance are preserved in the JSON.
