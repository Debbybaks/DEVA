# DEVA architecture — Phase 2

Python owns scientific truth. The original `schema`, `model`, `scenarios`, `verification` and `experiment` modules remain the validated Phase-1 baseline. NumPy/SciPy provide dense numerical work and HiGHS LPs; no dependency is added for prestige.

## Scientific modules

`analysis`: reachability, counterfactual taxonomy, paired uncertainty interventions and factorial sweeps.
`hydraulics`: independent passive Darcy–Weisbach head/flow solve with explicit physical geometry. It does not infer diameters from capacity budgets.
`evolution`: seeded bounded Pareto evolution, full archive, split separation, frozen recommendation, audits and provenance.
`adversary`: bounded combinatorial attacks, integer graph min-cut witnesses, monotone demand thresholds.
`audit`: independently recompute primal feasibility and verify scientific hashes. This is numerical checking, not a formal proof.
`report`: render recorded evidence as Markdown without generating invented results.

## Runtime and persistence

FastAPI validates strict request models before a two-process spawn worker pool. Expensive evolution and interactive LP solves run outside the HTTP event loop. A local SQLite WAL database stores job configuration, statuses, cancellation flags and ordered progress events. Full evidence is written atomically before completion. Source hash, Python/NumPy/SciPy versions, model version and complete input form cache identity. SSE has heartbeats, sequence IDs, `after`/Last-Event-ID resumption and terminal-event drain. Cancellation is cooperative at progress checkpoints; it is not immediate interruption of native solver work. Restarted unfinished jobs become failed records with a reason. Multi-server coordination, authentication and production quotas remain future work.

Immutable scientific payloads retain all candidates, scenarios, results and failures. The timestamp is execution metadata; the scientific SHA-256 is canonical finite JSON. Interactive Lab requests also receive a content-derived identity, full configuration, software metadata and a downloadable package. Runtime records live in ignored `.runtime`; baseline and demonstration artifacts are versioned in Git.

Data entities remain Project, Requirement, Candidate, Scenario, Experiment, Simulation, Verification and Provenance. Scientific entities are presently immutable JSON relationships, not separate editable database rows. SQLite stores orchestration entities. Public request contracts are in `contracts/api.openapi.json`; client Zod schemas reject invented verification levels, malformed vector dimensions and mismatched scenario identities. The read-only `view` adapter projects both baseline and evolution packages into one UI shape. Direct JSON response serialization avoids expensive recursive API encoding of large histories.

## Application boundary

`apps/command`: React, Vite, strict TypeScript, Zod contracts, a reducer for command state, React Three Fiber/Three.js and custom GLSL. Vite is appropriate for a local scientific workstation with a separate Python server; Next.js server rendering would not improve the solver boundary. The UI never independently solves or awards scientific verification. It maps supplied numerical states into geometry, labels and colour. Camera/layer controls and provenance graph traversal are application logic.

The shader encodes flux along pipe orientation, transitions encoded layer colour, displays interval hatching, and interpolates capacity width between candidate selections. It does not simulate water dynamics. SVG presents ancestry, a Pareto projection and a low-load topology. The WebGL renderer is lazy-loaded. Fonts are self-hosted. A scalar sampler measures rendered-frame time; slow rendering during worker computation switches to 2D to preserve compute resources.

Progress streams report real stages and candidate completions, not partial unvalidated hydraulic fields. The interface labels its displayed network as the last completed state while a solver job is active. Matched-scenario comparison shares layers, selection and camera pose after orbit gestures. Physical simulation time is unavailable.

## Security and extensibility

Input is bounded structured JSON; there is no arbitrary generated code execution. Local API caps graphs, scenario counts, generations and queued evolution jobs. It is not authenticated, hardened multi-tenant infrastructure or a denial-of-service guarantee. Domain adapters must bring their own units, equations and validation; only transport evolution and the independent passive hydraulic research module exist. Natural-language interpretation, durable multi-domain projects, calibrated hydraulic evolution and internet hosting are not claimed.


## Phase-3 update

Phase 3 adds a schema-3.0 pressure-dependent hydraulic engine, explicit unit boundary, source fingerprint, bounded Z3 proof objects and the same durable workers. `hydraulic_view` projects SI truth for the extended scene; historical schemas and payloads are unchanged.
