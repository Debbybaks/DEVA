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
