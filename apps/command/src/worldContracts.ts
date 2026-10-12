import { z } from "zod";
const number = z.number().finite();
const state = z.discriminatedUnion("domain", [
  z.object({
    domain: z.literal("water"),
    service: number.nullable(),
    passes: z.boolean(),
    violations: z.array(z.string()),
    state: z
      .object({
        pressure_head_m: z.record(z.string(), number.nullable()),
        flow_m3s: z.array(number),
        velocity_ms: z.array(number),
      })
      .passthrough()
      .nullable(),
  }),
  z.object({
    domain: z.literal("microgrid"),
    service: number.nullable(),
    passes: z.boolean(),
    violations: z.array(z.string()),
    state: z
      .object({
        time_s: z.array(number),
        solar_W: z.array(number),
        generator_W: z.array(number),
        charge_W: z.array(number),
        discharge_W: z.array(number),
        served_W: z.array(number),
        demand_W: z.array(number),
        energy_J: z.array(number),
        unserved_energy_J: number,
        scope: z.string(),
      })
      .nullable(),
  }),
]);
const frame = z.object({
  component_passes: z.record(z.string(), z.array(z.boolean())).optional(),
  scenario: z.record(z.string(), z.unknown()),
  outcome: state,
});
const result = z
  .object({
    failures: number,
    samples: number,
    failure_rate: number,
    failure_rate_wilson_95: z.array(number),
    records: z.array(frame),
  })
  .nullable();
export const worldSchema = z
  .object({
    science: z.object({
      source_experiment: z.string(),
      source_sha256: z.string(),
      label: z.string(),
      experiments: z.array(
        z.object({
          id: z.string(),
          view_url: z.string().optional(),
          scientific_sha256: z.string().optional(),
          domain: z.enum(["water", "microgrid"]),
          strategy: z.string(),
          seed: number,
          selection: z.string().nullable(),
          frontier: z.array(z.string()),
          descriptor: z
            .object({
              id: z.string(),
              model_version: z.string(),
              equations: z.array(z.string()),
              validity_envelope: z.record(z.string(), z.string()),
            })
            .passthrough(),
          configuration: z.record(z.string(), z.unknown()),
          variables: z.array(
            z.object({
              id: z.string(),
              unit: z.string(),
              options: z.array(number),
            }),
          ),
          plan: z.record(z.string(), z.unknown()),
          stop: z.string(),
          target_achieved: z.boolean(),
          candidates: z.array(
            z.object({
              id: z.string(),
              parent: z.string().nullable(),
              generation: number,
              design: z.array(number),
              cost: number,
              counterexample: z.string().nullable(),
              rejection_reason: z.string().nullable(),
              training_failures: number.nullable(),
              frames: z.array(frame),
            }),
          ),
          heldout: result,
          adversarial: result,
          verification: z.array(z.unknown()),
          claim_ledger: z.array(z.unknown()),
          solver_calls: number,
          diversity: number,
        }),
      ),
      ablation: z.array(z.unknown()),
      curves: z.array(z.unknown()),
      decision: z.record(z.string(), z.unknown()),
      decision_candidates: z.array(z.unknown()),
      limitations: z.array(z.string()),
    }),
    scientific_sha256: z.string(),
  })
  .superRefine((v, c) => {
    for (const e of v.science.experiments) {
      if (e.domain !== e.descriptor.id)
        c.addIssue({ code: "custom", message: "Domain evidence mismatch" });
      for (const candidate of e.candidates)
        for (const f of candidate.frames) {
          if (f.outcome.domain !== e.domain)
            c.addIssue({
              code: "custom",
              message: "Cross-domain physics rejected",
            });
          if (f.outcome.domain === "microgrid" && f.outcome.state) {
            const s = f.outcome.state,
              n = s.demand_W.length;
            if (
              [
                s.solar_W,
                s.generator_W,
                s.charge_W,
                s.discharge_W,
                s.served_W,
              ].some((a) => a.length !== n) ||
              s.energy_J.length !== n + 1 ||
              s.time_s.length !== n + 1
            )
              c.addIssue({
                code: "custom",
                message: "Temporal state dimensions mismatch",
              });
          }
        }
    }
  });
export type WorldView = z.infer<typeof worldSchema>["science"];
export type WorldExperiment = WorldView["experiments"][number];
export type WorldFrame = z.infer<typeof frame>;
