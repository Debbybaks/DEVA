# Phase-4 recovery checkpoint

Scientific source commit: `b780be432e9f8275125c5ecfefb9d77a00863ba6`. This checkpoint is committed afterwards; resolve its exact containing commit with `git log -1 -- PHASE4_CHECKPOINT.md`. No baseline history was replaced.

## Completed and partial work

Calibration observations, local identifiability, bounded multistart fitting, held-out synthetic validation, digital-twin knowledge categories, conditional sensor information, seeded state-dependent research hazard cascades, scheduled recovery, causal records, bounded scientific-tool agent, counterexample simulation, observed/residual world, solver-driven GPU tracers, proof inspector and stored-data demonstration are implemented. See ROADMAP.md for COMPLETE/PARTIAL/NOT STARTED/BLOCKED scopes. Field calibration, physical rupture fidelity, global identifiability, online field operation and general autonomous search remain incomplete. Phase-4 benchmark scripts exist but are unexecuted.

## Validation and regression

90 Python tests passed in 121.215 s. 11 frontend tests and strict production build passed; production frontend has not changed since those checks. Original four browser tests passed at baseline. Expanded browser run initially passed five and failed hydraulic startup; the unchanged five-second hydraulic assertion subsequently passed after caching/prewarming scientific projection and gzip compression. SSE explicitly bypasses compression. Latest two twin browser flows passed in targeted runs. A newly added exact-text locator failed because its element includes a nested annotation; corrected locator checks the same label without changing timeout. No existing test was weakened. A complete six-test browser run after the startup fix has not yet been performed.

Three historical experiments were executed and replayed exactly before Phase-4 expansion; preserved replay payloads were rechecked afterwards. Original artifact byte SHA256: `14e632693c8f4b9549bb326310715f719b068da373a2feeae1c9d641378ecd5e`. The wrapper scripts/replay_history.py has not itself been exercised yet. See artifacts/phase4-validation.json.

## Scientific results

Historical 38/200 failures remain immutable. Fresh capacity experiment 44/200 → 13/200 costs 399 → 532.5578984864775; these costs are distinct from hydraulic geometry costs. Twin experiment `deva-twin-882834fc7dd2ec29` recovers synthetic west/east friction 1.242866/0.841544 and demand multiplier 1.081984 against 1.25/0.85/1.08 truth. Held-out pressure RMSE 0.089709 m, flow RMSE 0.000046399 m³/s, local prediction interval coverage 15/16; local rank 3/3. Same-equation synthetic truth is not external validation.

Autonomous selected agent:c002 costs 395.325706 versus 368.951216 baseline (~7.15% more). It has 4/40 held-out hospital service/pressure failures. The 2% target is NOT established; bounded catalogue exhausted. Research cascade has secondary west-trunk failure at 360 s; hazards are uncalibrated phenomenology, not real rupture predictions. Z3 proves only bounded Boolean topology, never nonlinear hydraulic reality.

## Limitations / unresolved work

No known unresolved startup cause after the targeted pass; full browser confirmation remains outstanding. Independent field/reference calibration, model discrepancy, correlated sensor errors, timestep-convergence studies, physical leak/fracture/transients and independently checked proof artifacts remain open. GPU budgets are targets, not measurements. Development gzip evidence is intentionally retained and labelled provisional.

## Files and continuation

At checkpoint preparation no scientific modules were mid-edit. Remaining working-tree changes comprised documentation, final evidence/report, benchmark scaffolds, calibration analytical test and twin browser assertions; they are committed with this checkpoint. Runtime/cache/test-results are ignored.

Exact next implementation step: independently diagnose each of the frozen four agent failures from stored scenario/result evidence, test controlled outage/demand/head counterfactuals, and quantify diagnostic design costs without claiming generalisation on reused held-out data. Then deepen causal replay/counterexample evolution, run benchmark scaffolds and improve visual inspection only from actual scientific results.

## Resume commands

```bash
cd /workspace/deva
git status --short
git log -6 --oneline
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python scripts/replay_history.py
.venv/bin/python scripts/twin_report.py artifacts/digital-twin-evidence.json --output /tmp/twin-report.md
cd apps/command
npm test
npm run build
npm run test:e2e
```

Run targeted tests after changes; avoid repeating the 90-test suite immediately without a relevant change. Browser/process tests require local networking permission. Playwright starts/reuses API8000 and Vite5173. Continue: frozen failure diagnosis → calibration uncertainty propagation → causal replay refinement → counterexample/evolution/reverification → measured performance → world inspection and demonstration → complete milestone validation.
