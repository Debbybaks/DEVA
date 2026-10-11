# Command-environment UX

Opening: DEVA / Design. Simulate. Break. Verify. The primary object is the engineering network; the objective and current earned evidence level sit beside it. No wall of metric cards. The user edits a problem, inspects formalisation and assumptions, starts an experiment, then follows candidate branches and failed scenarios.

Spatial layout: central topology canvas; narrow requirement rail; bottom evolution/history strip; contextual inspection panel. Sources, hospitals and shelters have distinct shapes and text labels. Selecting an edge reveals installed capacity, scenario flow, utilisation and constraints. Selecting a dead branch reveals its counterexample and rationale. All simulation numbers come from identified experiment records.

Switchable layers: physical topology, dependency/corridor groups, flow utilisation, risk across sampled scenarios, uncertainty distribution, verification requirements and evolutionary branches. Preserve camera/selection across smooth transitions. Empty layers explain missing evidence. Failure Lab shows how an event changes source availability and disconnected routes; graph reachability is distinct from dynamic hydraulic cascading.

Current core is static. Scenario browsing has an index control, not a time scrubber. Physical timeline/play/speed controls become available only with a dynamic model. Future motion represents worker progress and computed flows, not invented time dynamics.

Accessibility: keyboard selectable nodes/edges, equivalent textual evidence, colour-independent failure markers, reduced motion, high contrast, screen-reader summaries. Users can download JSON evidence immediately; professional report rendering is later work.

## Phase-2 implementation status

The command environment is implemented in apps/command. It includes the network canvas, layers, matched-scenario comparisons, camera focus, candidate ancestry, interactive outage/source/degradation controls, equations and Evidence Mode. Scenario index is explicitly not physical time. Low-load 2D view retains flows and inspection; physical recovery, temporal cascades and sensor layers remain unavailable.


## Phase-3 update

Hydraulic V2 extends the same central world with pressure, velocity, real tank frames, operational isolation rounds, component equations and guided stored evidence. The transport archive remains accessible.
