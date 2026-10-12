# DEVA
**Design, Engineering & Verification Autonomy** — named after Deborah.

Design. Simulate. Break. Evolve. Verify.

DEVA is a local engineering research workbench with a Python scientific engine and a strict TypeScript spatial command environment. It designs continuous capacities for an emergency-water network, evolves competing designs, searches for counterexamples, and preserves the evidence behind every conclusion.

## What is implemented

- Original validated transport LP, unchanged baseline experiments and all original 16 tests.
- Counterfactual failure taxonomy, paired probabilistic sensitivities and factorial sweeps.
- Bounded Design Evolution Engine: ancestry, mutations, rejected branches and empirical three-objective Pareto analysis.
- Independent training, validation and held-out streams; recommendation frozen before audit data is generated.
- Adversarial outage search, unit-edge minimum cuts and demand-threshold bracketing.
- Independent numerical evidence audits and a requirement-to-conclusion provenance graph.
- Legacy passive Darcy–Weisbach research adapter (`deva.hydraulics`), alongside the now-coupled pressure-dependent Hydraulic V2 engine described below. Neither has field calibration.
- FastAPI/process workers, SQLite job/event persistence, resumable SSE progress, caching, cooperative cancellation and recorded interactive Failure Lab evidence.
- React/Three.js command canvas, meaningful GLSL flux/uncertainty encoding, scientific layers, matched-scenario design comparison, camera synchronisation, component equations, ancestry and Evidence Mode.
- JSON evidence and a portable Markdown report export; computational and browser benchmark tools.

## Start locally

From `/workspace/deva`, Python 3.11+ and Node 20.19+/22.12+:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[api,test]'
npm --prefix apps/command ci
.venv/bin/python -m uvicorn deva.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
npm --prefix apps/command run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to the Python service. No API credentials are required. This is a local research service; authentication, tenancy and internet deployment are not implemented. Fonts are bundled locally. WebGL2 renders the network; a selectable 2D low-load representation retains the exact flows and inspection controls. Slow rendering during worker computation switches to the low-load view to prioritise scientific work.

## Run the independent scientific engine

```bash
.venv/bin/python -m deva.cli examples/emergency_water.json --seed 20261011 --samples 200 --output /tmp/baseline-replay.json
.venv/bin/python -m deva.diagnose artifacts/emergency-water-evidence.json --samples 100 --output /tmp/failure-analysis.json
.venv/bin/python -m deva.evolve_cli examples/emergency_water.json --seed 20261013 --generations 3 --output /tmp/evolution.json
.venv/bin/python -m deva.report /tmp/evolution.json --output /tmp/evolution-report.md
```

The interface is unnecessary for numerical correctness or reproducibility. Experiments have content-derived scientific identities; execution timestamps are separate. Compare canonical JSON scientific payloads, rather than Python tuple/list representations after deserialisation. The committed experiment reproduces exactly in this software environment; cross-platform bitwise reproduction is not promised.

## Evidence worth investigating

The original artifact is preserved byte-for-byte: **38/200 held-out failures**, of which 36 are outage–demand interactions and 2 are topological disconnections. It is never replaced by a better-looking result. See [FAILURE_TAXONOMY.md](FAILURE_TAXONOMY.md).

The new experiment uses seed 20261013, three generations, 60 training scenarios, 80 validation scenarios and 200 independent held-out scenarios. It retains 26 candidates. On the **same new test split**, the original minimum-cost robust capacity design fails 44/200; the training-selected evolved design `g2-c012` fails 13/200. Its capacity cost is 532.558 versus 399 for the original robust design. It had zero training failures and five validation failures. This is an empirical cost/reliability tradeoff in one synthetic experiment, not a field reliability or general safety guarantee.

Inspect [artifacts/evolution-report.md](artifacts/evolution-report.md), [artifacts/evolution-evidence.json](artifacts/evolution-evidence.json), and [artifacts/baseline-failure-analysis.json](artifacts/baseline-failure-analysis.json). Evidence Mode exposes provenance, negative results, seed streams, solver versions, uncertainty and sensitivities. Interactive disturbances have downloadable content-addressed evidence records in the local runtime directory.

## Validation and performance

```bash
.venv/bin/python -m unittest discover -s tests -v
npm --prefix apps/command run test
npm --prefix apps/command run build
npm --prefix apps/command run test:e2e
.venv/bin/python benchmarks/run.py
# With the local API and UI running, Chromium and Python Playwright installed:
.venv/bin/python benchmarks/browser.py
```

Playwright uses `/usr/bin/chromium` by default; set `DEVA_CHROMIUM_PATH` for another executable. Scientific/CLI/API tests and frontend tests are distinct from real-browser end-to-end checks. Browser tests use actual Python outputs and no mock simulation data. See [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md) and [PERFORMANCE.md](PERFORMANCE.md). GPU measurements here use software SwiftShader; there is no hardware frame-rate claim.

## Scientific boundaries

Capacity-network results do not establish hydraulic pressure, potable-water delivery, construction feasibility or certified infrastructure safety. Particle motion encodes relative volumetric flux; it is not velocity or travel time. The model is steady-state, so scenario indices are not timestamps and no physical cascade/recovery timeline is shown. Full-design mathematical/formal verification, physical transients, sensor inference, discrete construction catalogues, calibration and LLM problem interpretation remain incomplete. WebGPU, Rust and WASM have not been added without measured justification.

Start with [MATHEMATICAL_MODEL.md](MATHEMATICAL_MODEL.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DESIGN_EVOLUTION.md](DESIGN_EVOLUTION.md), [OPTIMISATION.md](OPTIMISATION.md), [HYDRAULIC_MODEL.md](HYDRAULIC_MODEL.md), [SCIENTIFIC_LIMITATIONS.md](SCIENTIFIC_LIMITATIONS.md) and [ROADMAP.md](ROADMAP.md).

## Phase 3 — coupled hydraulic research

Select **Hydraulic V2**, or open `http://localhost:5173/?model=hydraulic`. This is the primary new scientific demonstration, with explicit synthetic geometry and construction-cost assumptions. The transport archive and both historical experiments remain intact.

Install the formal extra for coupled experiments: `.venv/bin/python -m pip install -e '.[api,test,formal]'`. Run:

```bash
.venv/bin/python -m deva.hydraulic_experiment examples/emergency_water_hydraulic.json --seed 20261020 --output /tmp/hydraulic.json
.venv/bin/python -m deva.remaining artifacts/evolution-evidence.json --output /tmp/remaining.json
.venv/bin/python benchmarks/hydraulic.py
# With local servers running; run browser benchmarks without concurrent work:
.venv/bin/python benchmarks/render_modes.py
```

The new model couples pressure-dependent demand, Darcy–Weisbach losses, signed flow, source operating bounds, diameter evolution, adaptive adversaries, uncertainty envelopes, computed tank states, and independent numerical audits. The optional excess-flow valve-isolation cascade is an explicit synthetic policy, not a calibrated rupture model. Demonstration Mode guides actual stored evidence; Researcher Mode preserves controls. Pressure, velocity, timeline and property-specific proof objects are inspectable.

Z3 verifies bounded connectivity after any single pipe outage and provides a two-outage counterexample. This formal status is attached **only to the topology proposition**, not hydraulic service or the full design. See [HYDRAULIC_MODEL_V2.md](HYDRAULIC_MODEL_V2.md), [HYDRAULIC_VALIDATION.md](HYDRAULIC_VALIDATION.md), [FORMAL_METHODS.md](FORMAL_METHODS.md), [RESILIENCE_FRONTIER.md](RESILIENCE_FRONTIER.md), [REMAINING_FAILURE_ANALYSIS.md](REMAINING_FAILURE_ANALYSIS.md) and [CLAIM_LEDGER.md](CLAIM_LEDGER.md).

Geometry, reservoir heads, Darcy factors and prices remain uncalibrated. The new costs and seeds differ from the old capacity experiment; no cross-model universal improvement is claimed. The pipeline retains failures and labels missing reliability levels rather than inventing a 100% design.

Phase-3 validation: **67 Python tests, eight frontend tests, four real-browser flows**, passing strict production build and exact replay of all three scientific payloads. Review [artifacts/hydraulic-report.md](artifacts/hydraulic-report.md), [artifacts/hydraulic-world.png](artifacts/hydraulic-world.png) and [artifacts/hydraulic-evidence.json](artifacts/hydraulic-evidence.json). The selected hydraulic design has 10/100 held-out failures; a higher-cost catalogue design has 4/100 on that same split. This descriptive tradeoff does not change the frozen recommendation or imply superiority to the older capacity experiment.

## Phase 4: synthetic digital-twin laboratory

Open `http://localhost:5173/?model=twin` after starting the same API and command application. The original transport and hydraulic worlds remain available. The new world attaches synthetic observation markers, residuals and local uncertainty directly to the network; shared-camera comparison shows initial versus fitted predictions. Stored stochastic cascade events, sensor layouts, agent mutations, bounded topology counterexamples and property-specific proof artifacts remain inspectable. Demonstration 2.0 guides ten real-data stages; it does not generate fake outcomes.

```bash
.venv/bin/python -m deva.digital_twin examples/emergency_water_hydraulic.json --seed 20261030 --output /tmp/twin-replay.json
.venv/bin/python scripts/twin_report.py /tmp/twin-replay.json --output /tmp/twin-report.md
.venv/bin/python scripts/replay_history.py
```

The calibration benchmark estimates west/east friction multipliers and a demand coefficient from synthetic pressure/flow observations. It checks local identifiability and disjoint held-out predictions. Accepted **BENCHMARK CALIBRATED** status does not mean field calibration. Rank-deficient problems withhold parameter covariance. See [CALIBRATION_ENGINE.md](CALIBRATION_ENGINE.md), [IDENTIFIABILITY.md](IDENTIFIABILITY.md) and [CALIBRATION_VALIDATION.md](CALIBRATION_VALIDATION.md).

The new cascade uses a state-dependent, explicitly **uncalibrated research hazard**, seeded draws and audited hydraulic redistribution. Real-world material rupture, leakage before isolation and transient pressure waves remain unmodelled. See [RUPTURE_MODEL.md](RUPTURE_MODEL.md) and [CASCADE_ENGINE.md](CASCADE_ENGINE.md).

The bounded Engineering Agent invokes registered scientific tools with a stored plan, separate scenario streams, candidate/cost limits, stopping conditions and self-critique. It does not execute generated code. A 2% failure-probability objective requires statistical evidence, not a zero-looking count. See [AUTONOMOUS_ENGINEER.md](AUTONOMOUS_ENGINEER.md).

Historical exact replay uses an isolated recorded scientific revision because current source fingerprints legitimately change when new modules are added. `scripts/replay_history.py` never overwrites historical artifacts. The new JSON/Markdown package is separate at `artifacts/digital-twin-evidence.json` and `artifacts/digital-twin-report.md`.

### Resumed Phase-4 evidence

[Checkpoint](PHASE4_CHECKPOINT.md) records current scopes and continuation. The frozen agent still fails 4/40 hospital scenarios; its 2% target is unestablished. [Failure diagnosis](AGENT_REMAINING_FAILURE_ANALYSIS.md) and [calibration uncertainty](CALIBRATION_FAILURE_UNCERTAINTY.md) expose computed mechanisms and diagnostic costs. `python scripts/replay_twin.py` replays the complete stored synthetic package at its recorded source revision. Failure-world inspection uses actual held-out states, not fabricated animation.

### Phase 5 — Engineering Worlds

Open `/?model=worlds` for Water Resilience and Microgrid Energy Adequacy, driven by one bounded domain-neutral investigator. See [Domain Contract](DOMAIN_CONTRACT.md), [microgrid model](MICROGRID_MODEL.md), [research report](RESEARCH_REPORT_PHASE5.md) and [validity scope](PHASE5_VALIDITY_AND_SCOPE.md). Run `python scripts/replay_phase5.py` for the exact stored cross-domain study. Negative results and field limitations remain visible; this is research software, not certified infrastructure design.

## DEVA v1.0

Autonomous Engineering Research Laboratory. Frozen scope: [V1_SCOPE.md](V1_SCOPE.md). Release status: [V1_RELEASE_GATES.md](V1_RELEASE_GATES.md). Engineering Worlds: water resilience and microgrid energy adequacy; same investigator, different physics. Negative results are evidence, not errors to erase.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-release-lock.txt -r requirements-build-lock.txt
.venv/bin/pip install --no-deps --no-build-isolation -e .
cd apps/command
npm ci
npm run build
cd ../..
.venv/bin/python -m uvicorn deva.release_app:app --host 127.0.0.1 --port 8000
```

Open http://localhost:8000 for the read-only public-style research archive. For trusted local new investigations run `deva.api:app` instead. Testing: `.venv/bin/python -m unittest discover -s tests -q`; frontend `npm test`; browser `npm run test:e2e` from apps/command (requires Chromium). Exact replay commands and immutable hashes: [REPLAY_MANIFEST.json](REPLAY_MANIFEST.json). Replay requires Git history, not a shallow snapshot.

Deployment: [DEPLOYMENT.md](DEPLOYMENT.md). Technical report: [DEVA_V1_TECHNICAL_REPORT.md](DEVA_V1_TECHNICAL_REPORT.md). Privacy/security/limitations: [RELEASE_AUDIT.md](RELEASE_AUDIT.md). Public release: https://deva-vert.vercel.app. Hosted mode is a read-only research archive; full investigations run locally. No field certification, universal optimum or 2% target achievement is implied.
