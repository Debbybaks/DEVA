import { z } from "zod";
const finite = z.number().finite();
export const problemSchema = z.object({
  id: z.string(),
  objective: z.string(),
  nodes: z.array(z.string()),
  supply: z.record(z.string(), finite),
  demand: z.record(z.string(), finite),
  budget: finite,
  target: finite,
  edges: z.array(
    z.object({
      id: z.string(),
      tail: z.string(),
      head: z.string(),
      unit_cost: finite,
      max_capacity: finite,
      corridor: z.string(),
    }),
  ),
});
export const scenarioSchema = z.object({
  id: z.string(),
  availability: z.array(finite),
  supply_factor: finite,
  demand_factor: finite,
});
export const resultSchema = z.object({
  scenario_id: z.string(),
  service_fraction: finite,
  flow: z.array(finite),
  injection: z.array(finite),
  delivered: z.array(finite),
  demand: z.array(finite),
  max_residual: finite,
  passes: z.boolean(),
});
const metricsSchema = z.object({
  failures: z.number(),
  samples: z.number(),
  failure_rate: finite,
  failure_rate_wilson_95: z.tuple([finite, finite]),
  mean_unmet_m3h: finite,
  mean_service: finite,
});
const verificationSchema = z.object({
  level: z.enum([
    "UNTESTED",
    "SIMULATED",
    "STRESS TESTED",
    "ROBUST UNDER TESTED CONDITIONS",
  ]),
  requirements_pass: z.boolean(),
  formal_verification: z.literal(false),
  scope: z.string(),
  budget_margin: finite,
});
export const candidateSchema = z.object({
  id: z.string(),
  parents: z.array(z.string()),
  generation: z.number(),
  mutations: z.array(z.object({ operator: z.string() }).passthrough()),
  capacities: z.array(finite),
  cost: finite,
  disposition: z.string(),
  rejection_reason: z.string().nullable(),
  verification: verificationSchema,
  splits: z.record(
    z.string(),
    z.object({
      results: z.array(resultSchema),
      metrics: metricsSchema.optional(),
    }),
  ),
  visual_fields: z.array(
    z.object({
      edge_id: z.string(),
      outage_trials: z.number(),
      outage_failures: z.number(),
      conditional_failure_rate: finite.nullable(),
      conditional_wilson_95: z.tuple([finite, finite]).nullable(),
      scope: z.string(),
    }),
  ),
});
const provenanceSchema = z.object({
  nodes: z.array(
    z.object({ id: z.string(), kind: z.string(), label: z.string() }),
  ),
  edges: z.array(
    z.object({ source: z.string(), target: z.string(), relation: z.string() }),
  ),
});
const adversarySchema = z.object({
  tested: z.number(),
  failures: z.number(),
  enumeration_complete_within_bounds: z.boolean(),
  results: z.array(
    z.object({ scenario: scenarioSchema, result: resultSchema }),
  ),
  topology_cuts: z.array(
    z.object({
      demand_node: z.string(),
      minimum_pipe_outages: z.number().nullable(),
      edges: z.array(z.string()),
    }),
  ),
  single_outage_demand_margins: z.array(
    z.object({
      edge: z.string(),
      max_passing_demand_factor: finite.nullable(),
    }),
  ),
});
export const viewSchema = z
  .object({
    experiment_id: z.string(),
    scientific_sha256: z.string(),
    problem: problemSchema,
    recommendation: z.string().nullable(),
    candidates: z.array(candidateSchema),
    scenarios: z.record(z.string(), z.array(scenarioSchema)),
    pareto_frontier: z.array(z.string()),
    adversarial: adversarySchema.nullable(),
    provenance: provenanceSchema.nullable(),
    sensitivity: z.unknown(),
    failure_taxonomy: z.unknown(),
    limitations: z.array(z.string()),
    seeds: z.record(z.string(), z.number()),
    software: z.record(z.string(), z.string()),
    infeasible_attempts: z
      .array(
        z
          .object({ id: z.string(), operator: z.string(), status: z.string() })
          .passthrough(),
      )
      .default([]),
  })
  .superRefine((view, ctx) => {
    const m = view.problem.edges.length,
      n = view.problem.nodes.length;
    for (const [split, scenarios] of Object.entries(view.scenarios)) {
      if (scenarios.some((s) => s.availability.length !== m))
        ctx.addIssue({
          code: "custom",
          message: `Invalid ${split} availability dimension`,
        });
    }
    for (const c of view.candidates) {
      if (c.capacities.length !== m)
        ctx.addIssue({
          code: "custom",
          message: `Invalid capacities for ${c.id}`,
        });
      for (const [split, data] of Object.entries(c.splits)) {
        if (data.results.length !== view.scenarios[split]?.length)
          ctx.addIssue({
            code: "custom",
            message: `Invalid ${split} scenario count for ${c.id}`,
          });
        for (let i = 0; i < data.results.length; i++) {
          const r = data.results[i];
          if (
            r.flow.length !== m ||
            [r.injection, r.delivered, r.demand].some((v) => v.length !== n) ||
            r.scenario_id !== view.scenarios[split]?.[i]?.id
          )
            ctx.addIssue({
              code: "custom",
              message: `Invalid result dimension or scenario identity for ${c.id}`,
            });
        }
      }
    }
  });
export type Problem = z.infer<typeof problemSchema>;
export type Candidate = z.infer<typeof candidateSchema>;
export type Scenario = z.infer<typeof scenarioSchema>;
export type Result = z.infer<typeof resultSchema>;
export type View = z.infer<typeof viewSchema>;
export type Layer =
  | "physical"
  | "flow"
  | "capacity"
  | "failure"
  | "risk"
  | "uncertainty"
  | "verification"
  | "dependency";
export const layers: Layer[] = [
  "physical",
  "flow",
  "capacity",
  "failure",
  "risk",
  "uncertainty",
  "verification",
  "dependency",
];
export async function request<T>(
  url: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok)
    throw new Error(`Engine ${response.status}: ${await response.text()}`);
  return schema.parse(await response.json());
}
export const labSchema = z.object({
  experiment_id: z.string(),
  scenario: scenarioSchema,
  source_losses: z.array(z.string()),
  result: resultSchema,
  scope: z.string(),
});
export const jobSchema = z.object({
  job_id: z.string(),
  status: z.string(),
  cached: z.boolean(),
});
export const jobStatusSchema = z.object({
  job_id: z.string(),
  status: z.string(),
  error: z.string().nullable(),
  cancel_requested: z.boolean(),
});
