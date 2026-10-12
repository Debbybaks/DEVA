import { z } from "zod";
import EvidenceSummary, { RawEvidence } from "./EvidenceSummary";
const ablationSchema = z.array(
  z.object({
    domain: z.string(),
    strategy: z.string(),
    mean_failure_rate: z.number(),
    trials: z.array(
      z.object({
        experiment: z.string(),
        failure_rate: z.number(),
        cost: z.number().nullable(),
        solver_calls: z.number(),
        diversity: z.number(),
        stop: z.string(),
      }),
    ),
  }),
);
export function SearchAblation({
  value,
  allowRaw,
}: {
  value: unknown;
  allowRaw: boolean;
}) {
  const parsed = ablationSchema.safeParse(value);
  if (!parsed.success)
    return <EvidenceSummary value={value} allowRaw={allowRaw} />;
  return (
    <>
      <div className="ablation-grid">
        {parsed.data.map((group) => (
          <article
            className="ablation-card"
            key={`${group.domain}-${group.strategy}`}
          >
            <h3>
              {group.domain === "water"
                ? "Water Resilience"
                : "Microgrid Energy Adequacy"}{" "}
              · {group.strategy}
            </h3>
            <p>
              Mean held-out failure rate:{" "}
              <strong>{group.mean_failure_rate * 100}%</strong>
            </p>
            <div className="ablation-meter" aria-hidden="true">
              <span style={{ width: `${group.mean_failure_rate * 100}%` }} />
            </div>
            <details>
              <summary>{group.trials.length} recorded trials</summary>
              {group.trials.map((trial) => (
                <article className="decision-card" key={trial.experiment}>
                  <dl className="evidence-fields">
                    <div>
                      <dt>Failure rate</dt>
                      <dd>{trial.failure_rate * 100}%</dd>
                    </div>
                    <div>
                      <dt>Design cost (units)</dt>
                      <dd>{trial.cost ?? "Not available"}</dd>
                    </div>
                    <div>
                      <dt>Physical solver calls</dt>
                      <dd>{trial.solver_calls}</dd>
                    </div>
                    <div>
                      <dt>Catalogue diversity</dt>
                      <dd>{trial.diversity}</dd>
                    </div>
                    <div>
                      <dt>Stopping reason</dt>
                      <dd>{trial.stop}</dd>
                    </div>
                    <div>
                      <dt>Evidence reference</dt>
                      <dd>{trial.experiment}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </details>
          </article>
        ))}
      </div>
      {allowRaw && <RawEvidence value={value} />}
    </>
  );
}
