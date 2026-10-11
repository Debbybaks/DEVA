# Coupled scientific world

Open `/?model=hydraulic` or select Hydraulic V2 in the existing command environment. The transport archive, history and original warnings remain accessible. The hydraulic extension enlarges the existing central world and moves pressure, flow direction and diameter into that world rather than replacing it with new statistic cards.

Python `hydraulic_view` is the explicit SI-to-display boundary. It supplies typed render state and underlying hydraulic quantities. React handles selection, shared camera, layer, matched scenario index, ancestry selection, and frame replay. It never solves PDD, pressure, reliability or unit conversions. Zod rejects dimension/identity mismatches and unsupported formal labels; unknown numerical states render no invented flow.

Pressure halos and labels use computed node pressure head, with unknown isolated pressure shown separately. They are node-state encodings, not an invented continuous field over unsurveyed ground. Pipe geometry morphs between explicit catalogue diameters. Signed GLSL motion consumes computed velocity for hydraulic views, preserving reverse direction; historical transport uses its existing relative volumetric-flux scale. Layout is topology, not length-scaled surveyed geography. Camera focus transitions guide inspection and stop on user orbit.

Three fidelity modes preserve exactly the same scientific values: SVG scientific 2D, standard WebGL, and higher-resolution WebGL. Solver submission switches to 2D to release CPU in software-rendering environments. WebGL availability/context failure also retains numerical SVG rendering. Hardware performance remains unmeasured.

Storage replay visits actual re-solved states with seconds and tank volume; isolation replay visits actual policy rounds without fabricated seconds. Event markers focus the tank. Comparison shares camera, layer and matched held-out scenario; temporal comparison is disabled until separately computed paired trajectories exist. Pressure/service annotations, component equations and observed causal facts drill into the same scene. The cost–resilience plot directly selects the corresponding engineering candidate and preserves dominated designs.

Demonstration Mode guides actual stored objective, economical candidate, failure, selected lineage, adaptive probe, storage response, operational cascade, frontier and proof objects. Researcher Mode retains full controls. No video, fake intermediate state, ambient particle system or generated explanation supplies scientific evidence. Further spatial ancestry design, calibrated propagation fields and large-network instancing require additional work and benchmarks.

## Phase-4 world integration

`TwinWorkspace` shares `NetworkCanvas`, camera state, scientific 2D fallback and hydraulic state contract. The new `twinContracts` validates synthetic observation dimensions, calibration acceptance gates, proof scope, ensemble shape, graph references and GPU/CPU flow agreement. `FlowParticles` animates a stable vertex buffer in GLSL, not a JS per-particle simulation.

Observation epochs and cascade intervals are separate stored sequences. Candidate mutations and SAT-counterexample simulations are also actual Python-projected states, not inferred browser physics. Component inspection links numerical state to equations and evidence. Ten guided demonstration stages select stored data; they do not fabricate optimisation progress or intermediate pressure states. Comparison uses a shared camera and the same observed excitation. Display tracer speed is explicitly distinct from scientific replay time.
