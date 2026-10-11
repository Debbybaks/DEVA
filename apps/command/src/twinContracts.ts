import { z } from "zod";
import { problemSchema } from "./contracts";
import { hydraulicStateSchema } from "./hydraulicContracts";
const finite = z.number().finite();
const observation = z
  .object({
    id: z.string(),
    timestamp: z.string(),
    sensor_id: z.string(),
    component: z.string(),
    measurement_type: z.enum(["pressure", "flow", "source_output", "service"]),
    value_si: finite,
    sigma_si: finite.positive(),
    canonical_unit: z.enum(["m", "m3/s", "1"]),
    scenario: z.record(z.string(), z.unknown()),
    provenance: z.object({
      kind: z.enum(["SYNTHETIC", "REFERENCE", "FIELD"]),
      source: z.string(),
    }),
  })
  .superRefine((r, c) => {
    const unit =
      r.measurement_type === "pressure"
        ? "m"
        : r.measurement_type === "service"
          ? "1"
          : "m3/s";
    if (r.canonical_unit !== unit)
      c.addIssue({
        code: "custom",
        message: "Observation dimensional mismatch",
      });
  });
const row = z.object({
  observation,
  prediction: finite,
  initial_prediction: finite,
  residual: finite,
  standardized_residual: finite,
  parameter_variance: finite.nonnegative().nullable(),
  measurement_variance: finite.nonnegative(),
  prediction_interval_95: z.tuple([finite, finite]).nullable(),
  covered: z.boolean().nullable(),
});
const metric = z.object({
  weighted_rmse: finite.nonnegative(),
  initial_weighted_rmse: finite.nonnegative(),
  rmse_by_quantity: z.record(z.string(), finite),
  interval_coverage_95: finite.min(0).max(1).nullable(),
});
const ident = z.object({
  rank: z.number().int(),
  parameters: z.number().int(),
  locally_identifiable: z.boolean(),
  singular_values: z.array(finite),
  condition_number: finite.nullable(),
  scope: z.string(),
});
const hazard = z.object({
  rate_per_second: finite.nonnegative(),
  probability: finite.min(0).max(1),
  uniform_draw: finite.min(0).max(1),
  hazard_change: finite,
  velocity_ms: finite,
  pressure_m: finite.nullable(),
  scope: z.string(),
});
const gpu = z.array(
  z.object({
    pipe_id: z.string(),
    length_m: finite.positive(),
    signed_velocity_ms: finite,
    flow_m3s: finite,
    particle_count: z.number().int().min(0).max(2048),
  }),
);
const graph = z.object({
  nodes: z.array(
    z.object({
      id: z.string(),
      kind: z.string(),
      reference: z.string().optional(),
    }),
  ),
  edges: z.array(
    z.object({
      source: z.string(),
      target: z.string(),
      evidence: z.string().optional(),
      scope: z.string().optional(),
    }),
  ),
});
const claim = z.object({
  id: z.string(),
  claim: z.string(),
  evidence: z.string(),
  status: z.string(),
  assumptions: z.array(z.string()),
  limitations: z.array(z.string()),
  reproduction_route: z.string(),
});
const proof = z.object({
  requirement_id: z.string(),
  property: z.string(),
  assumptions: z.array(z.string()),
  tool: z.string(),
  result: z.enum(["sat", "unsat", "unknown"]),
  status: z.string(),
  scope: z.string(),
  smtlib: z.string(),
  proof: z.string().nullable().optional(),
  proof_sha256: z.string().nullable().optional(),
  counterexample_closed: z.array(z.string()).nullable().optional(),
  limitations: z.array(z.string()),
});
export const twinViewSchema = z
  .object({
    experiment_id: z.string(),
    scientific_sha256: z.string(),
    label: z.literal("SYNTHETIC HIDDEN-PARAMETER BENCHMARK"),
    problem: problemSchema,
    frames: z
      .array(
        z.object({
          id: z.string(),
          split: z.enum(["calibration", "validation"]),
          timestamp: z.string(),
          baseline: hydraulicStateSchema,
          estimated: hydraulicStateSchema,
          baseline_gpu: gpu,
          estimated_gpu: gpu,
          observations: z.array(row),
        }),
      )
      .min(1),
    cascade: z
      .array(
        z.object({
          index: z.number().int(),
          time_seconds: finite.nonnegative(),
          state: hydraulicStateSchema,
          gpu,
          hazards: z.record(z.string(), hazard),
          events: z.array(z.string()),
          newly_failed: z.array(z.string()),
          restored: z.array(z.string()),
        }),
      )
      .min(1),
    causal_graph: graph,
    cascade_events: z.array(
      z.object({
        id: z.string(),
        simulation_time_seconds: finite,
        component: z.string(),
        event: z.string(),
        pre_event_state: z.record(z.string(), finite.nullable()).optional(),
        trigger: hazard.optional(),
        scope: z.string(),
      }),
    ),
    ensemble: z.object({
      time_seconds: z.array(finite),
      service_percentiles: z.object({
        "5": z.array(finite),
        "50": z.array(finite),
        "95": z.array(finite),
      }),
      terminal_failures: z.number().int(),
      samples: z.number().int(),
      trajectories: z.array(z.array(finite)),
      scope: z.string(),
    }),
    calibration: z.object({
      status: z.enum([
        "BENCHMARK CALIBRATED",
        "INSUFFICIENT CALIBRATION EVIDENCE",
      ]),
      parameters: z.array(
        z.object({
          id: z.string(),
          kind: z.string(),
          components: z.array(z.string()),
          initial: finite,
          lower: finite,
          upper: finite,
          estimate: finite,
          standard_error: finite.nullable(),
          unit: z.string(),
        }),
      ),
      metrics: z.object({ calibration: metric, validation: metric }),
      initial_identifiability: ident,
      fitted_identifiability: ident,
      covariance: z.array(z.array(finite)).nullable(),
      searches: z.array(
        z.object({
          start: z.number(),
          success: z.boolean(),
          history: z.array(
            z.object({
              parameters: z.array(finite),
              weighted_sum_squares: finite,
            }),
          ),
          weighted_sum_squares: finite,
        }),
      ),
      acceptance_criteria: z.object({
        heldout_weighted_rmse_max: finite,
        heldout_prediction_coverage_min: finite,
      }),
      uncertainty_scope: z.string(),
    }),
    incremental_calibration: z.array(
      z.object({
        observation_count: z.number(),
        timestamp: z.string(),
        status: z.string(),
        parameters: z.array(z.object({ id: z.string(), estimate: finite })),
        identifiability: ident,
      }),
    ),
    sensor_placement: z.object({
      budget: z.number(),
      recommendation: z.array(z.string()),
      layouts: z.array(
        z.object({
          sensors: z.array(z.string()),
          information_score: finite,
          identifiability: ident,
        }),
      ),
      value_of_information: z.array(
        z.object({ sensor: z.string(), information_score: finite }),
      ),
      criterion: z.string(),
      scope: z.string(),
    }),
    claim_ledger: z.array(claim),
    provenance_graph: graph,
    engineering_agent: z.object({
      plan: z.object({
        objective: z.record(z.string(), z.unknown()),
        tools: z.array(z.string()),
        constraints: z.record(z.string(), z.unknown()),
        assumptions: z.array(z.string()),
        stopping_conditions: z.array(z.string()),
      }),
      selection: z.string().nullable(),
      stopping_reason: z.string(),
      target_achieved: z.boolean(),
      invocations: z.array(
        z.object({
          index: z.number(),
          tool: z.string(),
          output_reference: z.string(),
          output_sha256: z.string(),
        }),
      ),
      self_critique: z.array(
        z.object({ issue: z.string(), evidence: z.string() }),
      ),
      research_narrative: z.array(
        z.object({ text: z.string(), evidence: z.string() }),
      ),
      outputs: z.record(z.string(), z.unknown()),
    }),
    next_observation: z.object({
      current_sensors: z.array(z.string()),
      value_of_information: z.array(
        z.object({
          sensor: z.string(),
          information_score: finite,
          information_gain: finite,
        }),
      ),
      scope: z.string(),
    }),
    counterexample: z
      .object({ state: hydraulicStateSchema, gpu, scope: z.string() })
      .nullable(),
    agent_candidates: z.array(
      z.object({
        id: z.string(),
        parents: z.array(z.string()),
        mutation: z.unknown(),
        cost: finite,
        rejection_reason: z.string().nullable(),
        training_failures: z.number().int(),
        training_samples: z.number().int(),
        state: hydraulicStateSchema.nullable(),
        gpu: gpu.nullable(),
      }),
    ),
    verification: z.object({
      objects: z.array(proof),
      counterexample_scenario: z.record(z.string(), z.unknown()).nullable(),
      counterexample_simulation: z.unknown(),
      scope: z.string(),
    }),
    knowledge_states: z.array(
      z.object({
        component: z.string(),
        quantity: z.string(),
        unit: z.string(),
        category: z.enum([
          "OBSERVED",
          "ESTIMATED",
          "SIMULATED",
          "FORECAST",
          "UNKNOWN",
        ]),
        value: finite.nullable(),
        uncertainty: finite.nullable(),
        provenance: z.record(z.string(), z.unknown()),
      }),
    ),
    limitations: z.array(z.string()),
    code: z.record(z.string(), z.unknown()),
    seed: z.number().int(),
  })
  .superRefine((v, c) => {
    for (const f of [
      ...v.frames.map((f) => ({ state: f.estimated, gpu: f.estimated_gpu })),
      ...v.frames.map((f) => ({ state: f.baseline, gpu: f.baseline_gpu })),
      ...v.cascade,
    ])
      if (
        f.gpu.length !== v.problem.edges.length ||
        f.gpu.some(
          (g, i) =>
            g.pipe_id !== v.problem.edges[i].id ||
            Math.abs(g.signed_velocity_ms - f.state.hydraulic.velocity_ms[i]) >
              1e-10 ||
            Math.abs(g.flow_m3s * 3600 - f.state.result.flow[i]) > 1e-8,
        )
      )
        c.addIssue({
          code: "custom",
          message: "GPU scientific state mismatch",
        });
    const cal = v.calibration,
      m = cal.metrics.validation,
      gate = cal.acceptance_criteria;
    if (
      cal.status === "BENCHMARK CALIBRATED" &&
      (!cal.fitted_identifiability.locally_identifiable ||
        cal.covariance === null ||
        m.weighted_rmse > gate.heldout_weighted_rmse_max ||
        (m.interval_coverage_95 ?? 0) < gate.heldout_prediction_coverage_min)
    )
      c.addIssue({ code: "custom", message: "Unsupported calibration badge" });
    for (const p of v.verification.objects)
      if (
        p.status === "FORMALLY VERIFIED" &&
        (p.result !== "unsat" ||
          !p.proof ||
          !p.proof_sha256 ||
          p.proof_sha256.length !== 64)
      )
        c.addIssue({ code: "custom", message: "Unsupported formal badge" });
    for (const g of [v.provenance_graph, v.causal_graph]) {
      const ids = new Set(g.nodes.map((n) => n.id));
      if (g.edges.some((e) => !ids.has(e.source) || !ids.has(e.target)))
        c.addIssue({ code: "custom", message: "Broken evidence graph" });
    }
    if (
      v.ensemble.trajectories.length !== v.ensemble.samples ||
      Object.values(v.ensemble.service_percentiles).some(
        (p) => p.length !== v.ensemble.time_seconds.length,
      )
    )
      c.addIssue({ code: "custom", message: "Ensemble dimensional mismatch" });
  });
export type TwinView = z.infer<typeof twinViewSchema>;
