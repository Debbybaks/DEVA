# DEVA
**Design, Engineering & Verification Autonomy** — named after Deborah.

Design. Simulate. Break. Verify.

Phase 0 foundations and a validated Phase 1 scientific core are implemented. DEVA currently solves continuous capacity design for a directed emergency-water delivery network. It generates nominal, uniform and scenario-robust alternatives, checks per-node service through linear programming, attacks them with outages and seeded combined events, and exports complete JSON evidence. It has no frontend, hydraulic pressure model, language-model interpreter, background service or formal proof engine yet.

## Run
Python 3.11+ with NumPy and SciPy. From this directory:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/deva examples/emergency_water.json --seed 20261011 --samples 200 --output artifacts/my-experiment.json
.venv/bin/python -m unittest discover -s tests -v
```

If dependencies are already installed, `PYTHONPATH=src python -m deva.cli ...` runs without installation. No API credentials are needed. Computation is local. The supplied example takes seconds, not hours. Sampling supports up to 10,000 scenarios; large dense synthesis problems are rejected before allocation. This bound does not provide server-grade denial-of-service protection.

## Demonstration findings
The committed 200-sample experiment uses seed 20261011, NumPy 2.3.5 and SciPy 1.17.0. There are 11 declared scenarios: nominal, six pipe outages, two corridor outages, demand surge and supply shortage.

| Candidate | Capacity cost | Declared requirements | Held-out failures |
|---|---:|---|---:|
| Nominal LP | 199.5 | Fails | 165 / 200 |
| Uniform allocation | 570 | Passes | 7 / 200 |
| Robust LP | 399 | Passes | 38 / 200 |

Robust LP wins by minimum cost among candidates meeting **declared** constraints. Uniform capacity has lower failure under this synthetic held-out distribution. This tradeoff is preserved rather than hidden. Held-out failures prevent a general safety claim. The robust LP's conditional failure interval is approximately 14.2–25.0%; this is not a real-world failure estimate.

## Claims and limits
The solver provides a numerically checked optimum for a continuous linear model over a finite synthesis scenario set. Tests validate implementation against analytical cases. Passing the declared suite earns `ROBUST UNDER TESTED CONDITIONS`, always scoped to that suite. No output is `FORMALLY VERIFIED`. Conservation and delivery capacities do not establish water pressure, quality, constructability or infrastructure safety.

The complete evidence includes configuration, scenarios, flows, deliveries, residuals, parent relationships, rejected candidates, local sensitivities, uncertainty, versions, seed, timestamp and SHA-256 of the scientific payload. Re-running the same configuration and software produces identical scientific payloads; the execution timestamp changes.

## Foundations
Read [VISION.md](VISION.md), [DOMAIN_SELECTION.md](DOMAIN_SELECTION.md), [MATHEMATICAL_MODEL.md](MATHEMATICAL_MODEL.md), [ARCHITECTURE.md](ARCHITECTURE.md), [VERIFICATION_STRATEGY.md](VERIFICATION_STRATEGY.md) and [ROADMAP.md](ROADMAP.md). UX and visual specifications describe the future command environment. [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md) defines validation scope. [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md) records current evidence and remaining gates.
