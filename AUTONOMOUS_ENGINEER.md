# Bounded autonomous engineering investigation

`deva.engineering_agent` is a deterministic tool policy over authoritative Python computations. It accepts an exact structured objective: demand component, maximum failure probability, maximum relative construction-cost increase, training/validation samples, candidate/tool budgets and seed. It does not execute generated code or pretend to understand unrestricted natural language.

Before computation, it stores an Engineering Plan with constraints, assumptions, registered tools, success criteria and stopping conditions. Optional calibration observations trigger uncertainty-weighted fitting and experimental-design recommendations. Only accepted synthetic benchmark calibration updates the working model; original configuration and calibration data remain recorded.

The registered sequence inspects baseline, calculates local diameter sensitivity, generates bounded catalogue mutations, evaluates training scenarios, freezes a cost-feasible selection, attacks it, opens an independent validation stream and verifies bounded topology. Every invocation records an output reference and hash. Failed/over-budget candidates remain in output. Validation cannot select or mutate a candidate.

Success requires the selected design's held-out component service/pressure failure Wilson 95% interval upper endpoint to meet the requested probability bound. Zero observed failures in a small sample is insufficient for a 2% requirement. Tool-budget exhaustion, exhausted catalogue, no cost-feasible design and insufficient statistical evidence produce explicit stopping reasons.

The policy is intentionally bounded, not a global optimiser or general-purpose AI engineer. Structured critique references the weakest evidence and assumptions. SAT topology counterexamples become actual hydraulic scenarios; they are preserved rather than silently redesigning outside the budget. Claims and concise narrative statements are generated from stored tool output, not an LLM story.
