import { z } from "zod";
import {
  problemSchema,
  candidateSchema,
  resultSchema,
  scenarioSchema,
} from "./contracts";
const finite = z.number().finite();
export const hydraulicStateSchema = z
  .object({
    scenario: scenarioSchema,
    result: resultSchema,
    candidate: candidateSchema,
    hydraulic: z.object({
      pressure_head_m: z.record(z.string(), finite.nullable()),
      head_m: z.record(z.string(), finite.nullable()),
      diameters_m: z.array(finite.positive()),
      velocity_ms: z.array(finite),
      requirements: z.record(z.string(), z.boolean()),
      requested_m3s: z.record(z.string(), finite),
      delivered_m3s: z.record(z.string(), finite),
      minimum_pressure_m: finite,
      full_service_pressure_m: finite,
      energy_residual_m: finite,
      mass_residual_m3s: finite,
    }),
  })
  .superRefine((s, c) => {
    if (s.result.scenario_id !== s.scenario.id)
      c.addIssue({
        code: "custom",
        message: "Hydraulic scenario identity mismatch",
      });
    const n = s.hydraulic.diameters_m.length;
    if (
      [
        s.result.flow,
        s.scenario.availability,
        s.candidate.capacities,
        s.hydraulic.velocity_ms,
      ].some((a) => a.length !== n)
    )
      c.addIssue({
        code: "custom",
        message: "Hydraulic pipe dimensions mismatch",
      });
    if (
      s.result.passes !== Object.values(s.hydraulic.requirements).every(Boolean)
    )
      c.addIssue({
        code: "custom",
        message: "Hydraulic requirement result mismatch",
      });
  });
const metric = z.object({
  failures: z.number().int(),
  samples: z.number().int(),
  failure_rate: finite,
  failure_rate_wilson_95: z.tuple([finite, finite]),
  mean_service: finite.nullable(),
  unknown_solver_states: z.number(),
});
const candidate = z.object({
  id: z.string(),
  parents: z.array(z.string()),
  generation: z.number(),
  mutation: z.unknown(),
  cost: finite,
  diameters_m: z.array(finite),
  rejection_reason: z.string().nullable(),
  states: z.record(z.string(), z.array(hydraulicStateSchema.nullable())),
  metrics: z.record(z.string(), metric),
});
const fact = z.object({
  component: z.string(),
  event: z.string(),
  evidence: z.string(),
  value: finite.nullable(),
  unit: z.string().nullable(),
});
const trace = z.object({ facts: z.array(fact), scope: z.string() });
export const hydraulicViewSchema = z
  .object({
    experiment_id: z.string(),
    scientific_sha256: z.string(),
    problem: problemSchema,
    configuration: z.record(z.string(), z.unknown()),
    recommendation: z.string(),
    candidates: z.array(candidate),
    frames: z.array(
      z.object({
        index: z.number(),
        time_seconds: finite,
        volume_m3: finite,
        head_m: finite,
        events: z.array(z.string()),
        state: hydraulicStateSchema,
      }),
    ),
    cascade: z.array(
      z.object({
        round: z.number(),
        newly_closed: z.array(z.string()),
        causes: z.array(z.unknown()),
        state: hydraulicStateSchema,
      }),
    ),
    frontier: z.object({
      heldout_frontier: z.array(z.string()),
      marginal_segments: z.array(z.unknown()),
      requested_levels: z.array(z.unknown()),
      scope: z.string(),
    }),
    verification_objects: z.array(
      z
        .object({
          requirement_id: z.string(),
          property: z.string(),
          status: z.enum(["FORMALLY VERIFIED", "COUNTEREXAMPLE", "UNKNOWN"]),
          result: z.enum(["unsat", "sat", "unknown"]),
          assumptions: z.array(z.string()),
          scope: z.string(),
          smtlib: z.string(),
          proof: z.string().nullable(),
          proof_sha256: z.string().nullable(),
          limitations: z.array(z.string()),
        })
        .passthrough(),
    ),
    claim_ledger: z.array(
      z
        .object({
          id: z.string(),
          claim: z.string(),
          status: z.string(),
          evidence: z.array(z.string()),
          assumptions: z.array(z.string()),
          limitations: z.array(z.string()),
          reproduction: z.string(),
        })
        .passthrough(),
    ),
    uncertainty: z.unknown(),
    code: z.unknown(),
    seeds: z.unknown(),
    limitations: z.array(z.string()),
    adversarial_scenario: z.object({
      id: z.string(),
      closed: z.array(z.string()),
      demand_factor: finite,
      source_head_delta_m: finite,
      friction_factor: finite,
    }),
    causal_trace: trace,
  })
  .superRefine((v, c) => {
    for (const p of v.verification_objects) {
      if (
        p.status === "FORMALLY VERIFIED" &&
        (p.result !== "unsat" ||
          !p.proof ||
          !p.proof_sha256 ||
          p.proof_sha256.length !== 64)
      )
        c.addIssue({
          code: "custom",
          message: "Formal property lacks UNSAT proof evidence",
        });
    }
    for (const candidate of v.candidates)
      for (const states of Object.values(candidate.states))
        for (const s of states) {
          if (
            s &&
            (s.result.flow.length !== v.problem.edges.length ||
              s.result.delivered.length !== v.problem.nodes.length ||
              Object.keys(s.hydraulic.pressure_head_m).length !==
                v.problem.nodes.length)
          )
            c.addIssue({
              code: "custom",
              message: "Hydraulic network/state dimensions disagree",
            });
        }
  });
export const hydraulicLabSchema = z.object({
  experiment_id: z.string(),
  scientific_sha256: z.string(),
  state: hydraulicStateSchema,
  causal_trace: trace,
});
export type HydraulicView = z.infer<typeof hydraulicViewSchema>;
export type HydraulicState = z.infer<typeof hydraulicStateSchema>;
