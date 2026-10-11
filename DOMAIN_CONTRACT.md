# Engineering Domain Contract

The domain-neutral engine in `general_engineer.py` owns budgets, plans, scenario splits, candidate ancestry, Pareto dominance, intervention ranking, evidence, memory and stopping. `EngineeringDomain` supplies a descriptor, construction catalogue, baseline, cost, simulation, scenarios, mutations and bounded verification. The agent contains no water/microgrid branches.

Descriptors declare identity/version, component types, state variables and units, equations, constraints, failure mechanisms, uncertainty, observables, verifiable properties, visual adapter, evidence adapter and validity envelope. Every outcome carries domain/model IDs; cross-domain results are rejected. Physical service is a dimensionless domain-defined critical requirement measure; equal values across domains do not imply equivalent physical risk or economic costs.

Water is a wrapper around the existing solver/audit and unchanged legacy orchestration. Scenario provenance is metadata removed only at the strict legacy physics boundary. Historical evidence is never migrated or rewritten; pinned replay scripts retain exact original source identity. New recursive source fingerprints cover nested domain modules while legacy fingerprints remain unchanged.

Catalogue search failure is not infeasibility proof. Wall time is checked between authoritative tools and can overrun by one bounded tool call; it is not a preemptive hard deadline. Candidate and simulation budgets are strict. Validation and held-out sets are frozen and never used to choose a design. Budget exhaustion preserves partial invocations and unknown states.
