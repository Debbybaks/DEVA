# Validation report — 2026-10-11

## Historical baseline preserved

The original 16 tests and scientific implementation are unchanged. The original 200-scenario evidence artifact remains byte-for-byte SHA-256 `14e632693c8f4b9549bb326310715f719b068da373a2feeae1c9d641378ecd5e`. Its scientific hash is `9a473107d6fcb70fc45a4b1a756e09ed4db5f3a64a5462513711a07323b82eaf`. Canonical scientific replay reproduces all results: the cost-399 robust design passes 11 declared scenarios and fails 38/200 held-out trials. Python in-memory tuples serialize to JSON arrays; compare canonical JSON, not heterogeneous in-memory container types.

Counterfactual reruns classify 36 failures as combined outage–demand interactions and two as topological disconnections. These are observations under this model; there is no temporal cascade or heterogeneous spatial-demand process to infer.

## Evolution experiment

Experiment `deva-evolution-415e051c31e3bded` uses model `capacity-evolution-0.2.1`, seed 20261013, three generations, 60 training, 80 validation and 200 independently generated held-out scenarios. It retains 26 candidates and all outcomes. Canonical scientific JSON replay matches exactly. Training-selected `g2-c012` costs 532.5578984864775, with 0/60 training, 5/80 validation and 13/200 held-out failures. The original robust design on this **same new held-out split** fails 44/200. The historical 38/200 experiment uses different scenarios and remains separate.

This is one synthetic out-of-sample experiment, not evidence of universal optimality or calibrated field failure probability. Every result is independently audited for conservation, bounds and service; this is numerical verification, not proof.

## Software and numerical checks

The Python suite contains 43 tests including the unchanged original 16. It covers analytical and seeded network cases, counterfactual classification, paired sensitivity, analytical passive hydraulics, graph-cut witnesses, bounded adversarial search, ancestry, deterministic evolution, split isolation, independent residual recomputation, tamper rejection, infeasible attempts, job lifecycle, contracts and evidence export.

Five frontend interaction tests use actual Python scientific projections. Three live Playwright end-to-end tests passed: Python/API/WebGL comparison and failure intervention with independent audit; historical baseline and mobile inspection; fresh asynchronous evolution with real progress and completed evidence. Background experiments use a fresh recorded fixture seed to avoid cache reuse.

Strict TypeScript compilation and production bundling are checked separately. Browser rendering is tested with Chromium software ANGLE/SwiftShader. This environment is too slow to establish premium hardware-GPU interaction quality; measurements and retained initial results are in PERFORMANCE.md and the browser artifacts. The numerical 2D mode provides graceful degradation.

## Limits

No physical calibration, pressure-coupled optimization, transient hydraulics, storage/recovery model, causal cascade, LLM interpreter, proof certificate or formal verification is claimed. The passive hydraulic solver is separately validated and intentionally not assigned invented physical properties from capacity values. No hardware-GPU, large-network, distributed multi-user or production-security validation has been completed. Locked browser dependencies and reproduction environment snapshots improve local repeatability but do not establish cross-platform bitwise guarantees.

## Phase-3 validation and scope

The original two scientific payloads replay exactly during Phase 3 and their committed bytes are untouched. The new clean-source hydraulic experiment `deva-hydraulic-065f46bd63838ed5` also replays with identical canonical scientific JSON. Scientific revision `118b7128d19805bcfe5b7c0da61cb76d90bd55ae`, Python-source fingerprint `d64e4d01908d1ce2a176b25f78e94c8063ea56f37b95cd9d4f294978f76732ec`, seed 20261020: 18 candidates, selected `h1-c008`, cost 395.3257055564662, 0/24 training failures, 2/24 validation, 10/100 held-out and 0/7 declared. These are new geometry, cost and scenario assumptions; no improvement over historical capacity failures is inferred.

Single-outage topology query: UNSAT with stored Z3 proof. Two-outage query: SAT with both trunks closed. The formal scope is bounded undirected connectivity with active sources, not hydraulic delivery. Numerical acceptance stays at 1e-8 m³/s mass and 1e-6 m head-loss residuals. Variable-demand tank tests independently validate first-order refinement against a closed-form ODE. No external EPANET/field validation was performed.

Development history: the first baseline browser rerun had startup timeouts while competing with numerical replay, then all three passed when isolated. A zero-head hydraulic solver residual failure was corrected without relaxing tolerance and retained as regression. A new browser test discovered an HTML-label cleanup error during renderer switching; a dedicated portal fixed it and the zero-page-errors assertion remains. Two new frontend selectors were made precise after ambiguously matching legend/evidence text; no original assertions were changed. Development scientific snapshots retain their full outputs in compressed artifacts.

Current software-rendering limits and WebGPU capability are recorded in GPU_BENCHMARKS.md. The optional cascade is an explicit synthetic protective-valve control model, not calibrated physical rupture. Nonconvergence outside the candidate evaluator can still abort a job; its configuration/error/progress remain durable, but partial probe-state checkpointing is not yet implemented. Full field reliability, all-model formal verification, mechanical stress and transient safety remain unclaimed.

Final checks: **67 Python tests, eight frontend tests, four live-browser tests**, strict TypeScript and production bundle pass. All original assertions remain. All three scientific payload replays match exactly, the two historical files are unchanged, and the new source fingerprint is clean. Actual world/failure screenshots captured without page errors are stored alongside `artifacts/phase3-validation.json`; development validation events remain separately recorded.
