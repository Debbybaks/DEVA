# Performance and technology decisions

## Scientific core

`benchmarks/run.py` records environment, graph size, solver throughput, synthesis/evolution runtime and Linux peak resident memory in `artifacts/performance.json`. On this six-node, six-pipe example, the measured median simulation was 4.11 ms, p95 9.77 ms, throughput 199.36 scenarios/s, declared synthesis 41.5 ms and a small eight-candidate evolution 2.72 s. Peak RSS was 63.04 MiB. These are warm local measurements, not scalability guarantees.

Python remains the scientific implementation. No measured scientific bottleneck justifies Rust/WASM, JAX or GPU computation for this graph. WebGPU/WGSL is deferred until larger scientifically meaningful workloads and comparative benchmarks exist. No performance claim is based on technology branding.

## Application boundary

Two spawned worker processes run experiments outside the API event loop. Durable SQLite event sequences support reconnecting SSE clients. Scientific payloads are atomically persisted; source/software/configuration-aware cache keys avoid reusing incompatible results. Cancellation occurs at stage checkpoints. Admission bounds limit active experiments and model sizes; production authentication, multi-user isolation, hard process deadlines and distributed scheduling remain outstanding.

Large scientific views use direct JSON responses to avoid recursive framework serialization. A local 9.2 MB view request measured approximately 0.60 s; the payload remains larger than desirable. Pagination and compact progressive scientific projections are future work. The Three.js renderer is loaded separately from controls. Self-hosted fonts remove a runtime external font dependency.

## Browser measurements and degradation

`benchmarks/browser.py` samples 180 actual animation frames in Chromium and measures local health API latency following experiment submission. The report identifies cached submissions and the actual GL renderer. See `artifacts/browser-performance.json`; the first poor result remains in `artifacts/browser-performance-initial.json`.

This environment uses ANGLE/SwiftShader software rasterisation, not a hardware GPU. The initial median frame interval was 166.7 ms, p95 416.7 ms: substantially below interactive quality. After geometry/material and resolution changes, the isolated final measurement had a 116.7 ms median, 233.3 ms p95 and 132.5 ms mean frame interval. Software rendering remains a limitation. The uncached experiment submission was followed by 30 health requests with median 3.27 ms and p95 5.98 ms local latency. Do not infer hardware frame rates from these numbers. A user-selectable numerical SVG mode preserves exact Python-generated flows, topology and inspection. During an experiment, an observed mean frame interval above 80 ms automatically switches to this lower-load mode, then restores spatial rendering after computation. This frees CPU for the solver rather than masking scientific results. Flux animation and camera motion apply only to the WebGL mode; animation time is visual flux phase, not physical simulation time.

Comparison uses shared camera, scenario index and layer state. Benchmarks should run without concurrent browser tests or builds, since they otherwise compete for CPU. The browser report does not establish large-network performance, production API latency, calibrated hydraulic throughput or WebGPU superiority.

## Phase-3 measurements

`benchmarks/hydraulic.py` independently records fresh nonlinear throughput, evaluations, errors and memory in `artifacts/hydraulic-performance.json`. `benchmarks/render_modes.py` samples the same real hydraulic state across fidelity modes and probes WebGPU. The measured software medians were 116.75 ms standard, 116.65 ms high-resolution, and 16.70 ms scientific 2D. The small difference between the two 3D measurements is not evidence that higher resolution is faster; warm-up and shared-host variability matter. Effective rendering resolutions are recorded. No WebGPU adapter was obtained in this environment, and no WGSL speedup is claimed. Python, WebGL and SVG remain the justified implementations; Rust/WASM is still deferred. See GPU_BENCHMARKS.md for scope.
