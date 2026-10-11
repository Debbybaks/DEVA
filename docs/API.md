# Local scientific API

`uvicorn deva.api:app --host 127.0.0.1 --port 8000`. OpenAPI: `/docs`; saved request schema: `contracts/api.openapi.json`.

- GET `/api/health`, `/api/problem`: local readiness and structured example.
- GET `/api/evidence/{baseline|evolution|diagnosis}`: full preserved scientific artifacts.
- GET `/api/view/{baseline|evolution}`: typed read-only command projection; no new scientific claims.
- POST `/api/jobs`: strict evolution config; returns 202, job ID and cache flag.
- GET `/api/jobs/{id}`: durable queued/running/completed/failed/cancelled state.
- GET `/api/jobs/{id}/events`: SSE sequence events, heartbeat and terminal drain; supports `after` and Last-Event-ID.
- DELETE `/api/jobs/{id}`: cancellation request, checked at stage/candidate checkpoints.
- GET `/api/jobs/{id}/evidence` and `/view`: available only after atomic result persistence.
- POST `/api/lab`: capacities, availability, demand/supply factors and explicit source losses. Solved in a process; independent audit and complete content-addressed evidence returned.
- GET `/api/lab/{experiment_id}`: recorded interactive evidence download.
- GET `/api/provenance/evolution?node=...`: backwards evidence ancestry for the committed evolution package.

Limits: 30 API nodes, 60 pipes, four generations, 120 training/validation samples, 300 held-out samples, four outstanding evolution jobs. Independent CLI limits differ and are documented in code. Native LP work cannot be instantly cancelled. WebSocket/partial-field streaming is not implemented; SSE streams real orchestration progress. No authentication or external publication is configured.

## Coupled hydraulic routes

GET `/api/hydraulic/evidence` and `/api/hydraulic/view` expose the stored schema-3.0 experiment and explicit display projection. POST `/api/hydraulic/jobs` accepts strict quantity-aware raw geometry, seed, bounded generations and three split sizes; it uses the same durable jobs, events, cache, cancellation and full-evidence routes. Completed job views dispatch by scientific schema. No-budget-feasible experiments retain candidates and full evidence rather than selecting a fake design.

POST `/api/hydraulic/lab` accepts SI diameters, closed pipe IDs, demand multiplier, head offset in m, friction multiplier and source losses. It performs a real process-backed solve, independent audit and observed causal trace. GET `/api/hydraulic/lab/{experiment_id}` downloads the content-addressed intervention with configuration, source revision, solver versions and all results. Unit-incompatible inputs are rejected. Solver nonconvergence remains an explicit failed/unknown evaluation, never a substituted state.

## Phase-4 synthetic twin

- `GET /api/twin/view`: hash-validated projection, observation/model pairs, cascade frames, GPU quantities, sensor layouts, agent outputs, proof/counterexample state and limits.
- `GET /api/twin/evidence`: complete schema-4.0 package.
- `POST /api/twin/jobs`: strict `{raw, diameters, seed}`; diameters are explicit SI metres. Runs the bounded named-component synthetic benchmark through existing workers.
- Existing `/api/jobs/{id}`, `/events`, `/view`, `/evidence` and cancellation routes support twin jobs. Progress stages correspond to actual observations/calibration/cascade/agent/persistence work.

Custom field ingestion, free-form agent code, arbitrary simulation plugins and authenticated multi-user operation are not exposed. Python APIs support explicit observation/parameter calibration separately; HTTP twin jobs currently use the reproducible synthetic benchmark, not uploaded field observations. Cooperative cancellation checkpoints occur between stages, not inside each nonlinear fit.

Twin projections include `failed_cases` with stored validation indices, original scenarios, exact solved state and GPU values; `unknown_cases` remain separately identified. These independent scenarios are not a temporal trajectory. The frontend disables Play for this collection while allowing discrete inspection. No new hydraulic solver is introduced in the browser.
