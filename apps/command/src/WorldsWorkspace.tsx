import EvidenceSummary from "./EvidenceSummary";
import { SearchAblation } from "./WorldEvidence";
import { z } from "zod";
import { useEffect, useState } from "react";
import { request } from "./contracts";
import {
  worldSchema,
  type WorldView,
  type WorldExperiment,
  type WorldFrame,
} from "./worldContracts";
import "./worlds.css";

const pct = (v: number | null) =>
  v === null ? "UNKNOWN" : `${(v * 100).toFixed(1)}%`;
function PhysicalWorld({
  experiment,
  frame,
  time,
  onSelect,
}: {
  experiment: WorldExperiment;
  frame: WorldFrame | undefined;
  time: number;
  onSelect: (id: string) => void;
}) {
  if (!frame)
    return (
      <p role="status">
        {experiment.selection === null
          ? "No fully evaluated budget-feasible design. Rejections remain in the evidence."
          : "Loading stored physical states…"}
      </p>
    );
  if (!frame.outcome.state)
    return (
      <p role="status">UNKNOWN SOLVER STATE / inspect preserved evidence</p>
    );
  if (frame.outcome.domain === "microgrid") {
    const s = frame.outcome.state,
      t = Math.min(time, s.demand_W.length - 1);
    const components = [
      { id: "solar", x: 110, y: 110, value: s.solar_W[t], label: "SOLAR" },
      {
        id: "generator",
        x: 110,
        y: 300,
        value: s.generator_W[t],
        label: "GENERATOR",
      },
      {
        id: "battery",
        x: 390,
        y: 300,
        value: s.discharge_W[t] - s.charge_W[t],
        label: "STORAGE",
      },
      {
        id: "critical-load",
        x: 660,
        y: 150,
        value: s.served_W[t],
        label: "CRITICAL LOAD",
      },
    ];
    return (
      <>
        <svg
          viewBox="0 0 850 450"
          role="img"
          aria-label="Chronological microgrid power and stored energy"
        >
          <defs>
            <marker
              id="world-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="5"
              markerHeight="5"
              orient="auto-start-reverse"
            >
              <path d="M0 0L10 5L0 10" fill="currentColor" />
            </marker>
          </defs>
          {[
            { id: "solar", path: "M160 110H390V150H610", power: s.solar_W[t] },
            {
              id: "generator",
              path: "M160 300H280V150H610",
              power: s.generator_W[t],
            },
            {
              id: "battery",
              path: "M440 300H530V150H610",
              power: s.discharge_W[t] - s.charge_W[t],
            },
          ].map((link) => (
            <path
              key={link.id}
              d={link.path}
              className="energy-path"
              strokeWidth={Math.max(
                1,
                Math.min(7, Math.abs(link.power) / 2000),
              )}
              opacity={Math.abs(link.power) > 0.001 ? 1 : 0.25}
              markerEnd={link.power > 0.001 ? "url(#world-arrow)" : undefined}
              markerStart={
                link.power < -0.001 ? "url(#world-arrow)" : undefined
              }
            />
          ))}
          {components.map((c) => (
            <g
              key={c.id}
              role="button"
              tabIndex={0}
              aria-label={`Inspect ${c.id}`}
              onClick={() => onSelect(c.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") onSelect(c.id);
              }}
              transform={`translate(${c.x},${c.y})`}
            >
              <rect
                x="-50"
                y="-35"
                width="100"
                height="70"
                rx={c.id === "battery" ? 5 : 0}
                className={
                  frame.component_passes?.[c.id]?.[t] === false
                    ? "world-component violated"
                    : "world-component"
                }
              />
              <text y="-50" textAnchor="middle">
                {c.label}
              </text>
              <text y="5" textAnchor="middle">
                {(c.value / 1000).toFixed(2)} kW
              </text>
            </g>
          ))}
          <text x="610" y="240">
            Demand {(s.demand_W[t] / 1000).toFixed(2)} kW
          </text>
          <text x="330" y="370">
            Stored energy {(s.energy_J[t] / 3600000).toFixed(2)} kWh
          </text>
          <text x="330" y="395">
            Computed time {(s.time_s[t] / 3600).toFixed(1)} h / signed battery
            power
          </text>
          <path
            d={s.energy_J
              .map(
                (v, i) =>
                  `${i ? "L" : "M"}${110 + i * 75},${430 - (v / Math.max(...s.energy_J, 1)) * 25}`,
              )
              .join(" ")}
            className="energy-envelope"
          />
        </svg>
        <dl className="world-readout" aria-label="Microgrid computed state">
          <div>
            <dt>Demand</dt>
            <dd>{s.demand_W[t]} W</dd>
          </div>
          <div>
            <dt>Served power</dt>
            <dd>{s.served_W[t]} W</dd>
          </div>
          <div>
            <dt>Stored energy</dt>
            <dd>{s.energy_J[t]} J</dd>
          </div>
          <div>
            <dt>Computed time</dt>
            <dd>{s.time_s[t]} s</dd>
          </div>
        </dl>
      </>
    );
  }
  const s = frame.outcome.state;
  const config = experiment.configuration as {
    nodes: { id: string }[];
    pipes: { id: string; tail: string; head: string }[];
  };
  const positions = Object.fromEntries(
    config.nodes.map((n, i) => [
      n.id,
      [130 + (i % 2) * 500, 65 + Math.floor(i / 2) * 150],
    ]),
  );
  return (
    <>
      <svg
        viewBox="0 0 850 450"
        role="img"
        aria-label="Water network signed flow and pressure"
      >
        {config.pipes.map((p, i) => {
          const a = positions[p.tail],
            b = positions[p.head];
          return (
            <g
              key={p.id}
              role="button"
              tabIndex={0}
              aria-label={`Inspect ${p.id}`}
              onClick={() => onSelect(p.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter") onSelect(p.id);
              }}
            >
              <line
                x1={a[0]}
                y1={a[1]}
                x2={b[0]}
                y2={b[1]}
                className="water-edge"
                strokeWidth={Math.max(
                  1,
                  Math.min(8, Math.abs(s.flow_m3s[i]) * 250),
                )}
              />
              <text x={(a[0] + b[0]) / 2} y={(a[1] + b[1]) / 2 - 6}>
                {p.id} · {(s.flow_m3s[i] * 1000).toFixed(2)} L/s
              </text>
            </g>
          );
        })}
        {config.nodes.map((n) => {
          const [x, y] = positions[n.id],
            p = s.pressure_head_m[n.id];
          return (
            <g
              key={n.id}
              transform={`translate(${x},${y})`}
              role="button"
              tabIndex={0}
              aria-label={`Inspect ${n.id}`}
              onClick={() => onSelect(n.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter") onSelect(n.id);
              }}
            >
              <circle
                r="23"
                className={
                  frame.component_passes?.[n.id]?.[0] === false
                    ? "world-node violated"
                    : "world-node"
                }
              />
              <text x="32" y="-5">
                {n.id}
              </text>
              <text x="32" y="16">
                {p === null ? "UNKNOWN" : p.toFixed(2)} m head
              </text>
            </g>
          );
        })}
      </svg>
      <dl className="world-readout" aria-label="Water computed pressure heads">
        {config.nodes.map((n) => (
          <div key={n.id}>
            <dt>{n.id.replaceAll("-", " ")}</dt>
            <dd>{s.pressure_head_m[n.id] ?? "Unknown"} m head</dd>
          </div>
        ))}
      </dl>
    </>
  );
}
export default function WorldsWorkspace({ onBack }: { onBack: () => void }) {
  const [publicArchive, setPublicArchive] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((r) => r.json())
      .then((r) => setPublicArchive(r.public_read_only === true))
      .catch(() => {});
    return () => controller.abort();
  }, []);
  const [job, setJob] = useState<string | null>(null),
    [liveStatus, setLiveStatus] = useState("");
  const [researchSeed, setResearchSeed] = useState(20261220),
    [costLimit, setCostLimit] = useState(300),
    [simulationLimit, setSimulationLimit] = useState(400),
    [candidateLimit, setCandidateLimit] = useState(16),
    [generationLimit, setGenerationLimit] = useState(4),
    [trainCount, setTrainCount] = useState(8),
    [validationCount, setValidationCount] = useState(12),
    [heldCount, setHeldCount] = useState(40),
    [failureTarget, setFailureTarget] = useState(0.02);
  const [view, setView] = useState<WorldView | null>(null),
    [error, setError] = useState("");
  const [domain, setDomain] = useState<"water" | "microgrid">("microgrid"),
    [strategy, setStrategy] = useState("hybrid"),
    [seedIndex, setSeedIndex] = useState(0),
    [candidateId, setCandidateId] = useState("");
  const [scenario, setScenario] = useState(0),
    [time, setTime] = useState(0),
    [compare, setCompare] = useState(false),
    [lens, setLens] = useState<
      "physical" | "xray" | "evidence" | "uncertainty"
    >("physical"),
    [selected, setSelected] = useState("");
  const [audience, setAudience] = useState<
      "researcher" | "judge" | "portfolio"
    >("researcher"),
    [act, setAct] = useState<number | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    request("/api/worlds/view", worldSchema, { signal: controller.signal })
      .then((r) => setView(r.science))
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(
            "Scientific data could not be loaded. Please try again; the stored evidence remains available in the research archive.",
          );
      });
    return () => controller.abort();
  }, []);
  const group =
      view?.experiments.filter(
        (e) => e.domain === domain && e.strategy === strategy,
      ) ?? [],
    summary = group[seedIndex] ?? group[0];
  const [loaded, setLoaded] = useState<WorldExperiment | null>(null);
  const experiment = loaded?.id === summary?.id ? loaded : summary;
  useEffect(() => {
    if (!summary) return;
    const controller = new AbortController();
    setLoaded(null);
    request(
      summary.view_url ?? `/api/worlds/experiment/${summary.id}`,
      worldSchema,
      {
        signal: controller.signal,
      },
    )
      .then((r) => {
        setLoaded(r.science.experiments[0]);
        setError("");
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(
            "Scientific data could not be loaded. Please try again; the stored evidence remains available in the research archive.",
          );
      });
    return () => controller.abort();
  }, [summary?.id]);
  async function runResearch() {
    if (!experiment || job) return;
    try {
      const result = await request(
        "/api/domain/jobs",
        z.object({ job_id: z.string(), cached: z.boolean() }),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            domain,
            raw: experiment.configuration,
            seed: researchSeed,
            strategy,
            maximum_cost: costLimit,
            maximum_simulations: simulationLimit,
            maximum_candidates: candidateLimit,
            maximum_generations: generationLimit,
            training_samples: trainCount,
            validation_samples: validationCount,
            heldout_samples: heldCount,
            target_failure_probability: failureTarget,
          }),
        },
      );
      setJob(result.job_id);
      setLiveStatus("Queued registered scientific investigation");
      setError("");
    } catch (e) {
      setError(
        "Scientific data could not be loaded. Please try again; the stored evidence remains available in the research archive.",
      );
    }
  }
  useEffect(() => {
    if (!job) return;
    const stream = new EventSource(`/api/jobs/${job}/events`);
    stream.onmessage = (event) => {
      const data = JSON.parse(event.data) as {
        stage: string;
        domain?: string;
        phase?: string;
        simulations?: number;
        error?: string;
      };
      setLiveStatus(
        `${data.stage} / ${data.phase ?? ""} / ${data.simulations ?? 0} solver calls`,
      );
      if (data.stage === "completed") {
        stream.close();
        request(`/api/domain/jobs/${job}/view`, worldSchema)
          .then((r) => {
            const e = r.science.experiments[0];
            e.view_url = `/api/domain/jobs/${job}/view`;
            setView((v) =>
              v
                ? {
                    ...v,
                    experiments: [
                      e,
                      ...v.experiments.filter((old) => old.id !== e.id),
                    ],
                  }
                : r.science,
            );
            setDomain(e.domain);
            setStrategy(e.strategy);
            setSeedIndex(0);
            setCandidateId(e.selection ?? "");
            setScenario(0);
            setTime(0);
            setJob(null);
            setLoaded(e);
          })
          .catch((e) => {
            setError(
              "Scientific data could not be loaded. Please try again; the stored evidence remains available in the research archive.",
            );
            setJob(null);
          });
      }
      if (data.stage === "failed" || data.stage === "cancelled") {
        setError(
          "The investigation stopped. Inspect its retained evidence in Researcher Mode.",
        );
        setJob(null);
        stream.close();
      }
    };
    return () => stream.close();
  }, [job]);
  const candidate =
    experiment?.candidates.find(
      (c) => c.id === (candidateId || experiment.selection),
    ) ?? experiment?.candidates.find((c) => c.frames.length);
  const frame = candidate?.frames[scenario],
    parent = experiment?.candidates.find((c) => c.id === candidate?.parent),
    before = parent?.frames[scenario];
  function switchWorld(d: "water" | "microgrid") {
    setDomain(d);
    setCandidateId("");
    setScenario(0);
    setTime(0);
    setSelected("");
    setCompare(false);
    setCostLimit(d === "water" ? 500 : 300);
  }
  function counterexample() {
    const witness = [candidate, ...(experiment?.candidates ?? [])].find((c) =>
      c?.frames.some((f) => !f.outcome.passes),
    );
    const i = witness?.frames.findIndex((f) => !f.outcome.passes) ?? -1;
    if (witness && i >= 0) {
      setCandidateId(witness.id);
      setScenario(i);
      setTime(0);
      setError("");
    } else
      setError(
        "No failure witness in the stored training scenarios; inspect held-out evidence.",
      );
  }
  function demonstrate(n: number) {
    setAct(n);
    if (n === 0) {
      switchWorld("water");
      setStrategy("hybrid");
      setSeedIndex(0);
      const archived =
        view?.experiments.filter(
          (e) => e.domain === "water" && e.strategy === "hybrid",
        ) ?? [];
      const archiveIndex = Math.max(
        0,
        archived.findIndex((e) => !e.view_url),
      );
      setSeedIndex(archiveIndex);
      const first = archived[archiveIndex];
      setCandidateId(first?.candidates[0]?.id ?? "");
    }
    if (n === 2) counterexample();
    if (n === 3) setLens("xray");
    if (n === 4) {
      setCandidateId(experiment?.selection ?? "");
    }
    if (n === 5) setCompare(true);
    if (n === 7) setLens("evidence");
    if (n === 8) switchWorld("microgrid");
  }
  if (!view || !experiment)
    return (
      <main className="worlds-shell">
        <h1>DEVA / Engineering worlds</h1>
        <p>{error || "Loading stored cross-domain evidence…"}</p>
        <button onClick={onBack}>Return to water laboratory</button>
      </main>
    );
  const acts = [
    "The problem",
    "The digital world",
    "Break it",
    "Understand the mechanism",
    "Competing designs",
    "The trade-off",
    "Decision frontier",
    "Scoped verification",
    "A second physical domain",
    "What remains unestablished",
  ];
  return (
    <main className="worlds-shell">
      <header className="worlds-header">
        <a href="/">DEVA</a>
        <nav aria-label="Project links">
          <a href="/archive">Research archive</a>
          <a href="https://github.com/Debbybaks/DEVA">GitHub / Source code</a>
        </nav>
        <span>
          DEVA v1.0 · RESEARCH LABORATORY · DESIGN. SIMULATE. BREAK. EVOLVE.
          VERIFY.
        </span>
        <button onClick={onBack}>Water reference laboratory</button>
      </header>
      <section className="worlds-title">
        <p>DEVA v1.0 · Design. Simulate. Break. Evolve. Verify.</p>
        <p>ENGINEERING WORLDS / {view.label}</p>
        <h1>Different physics. One investigation engine.</h1>
        <p>Designs earn evidence. Failure remains visible.</p>
      </section>
      <nav aria-label="Engineering worlds" className="world-choice">
        <button
          aria-pressed={domain === "water"}
          onClick={() => switchWorld("water")}
        >
          01 / WATER RESILIENCE<span>Pressure · signed flow · service</span>
        </button>
        <button
          aria-pressed={domain === "microgrid"}
          onClick={() => switchWorld("microgrid")}
        >
          02 / MICROGRID ADEQUACY
          <span>Power · stored energy · chronological dispatch</span>
        </button>
      </nav>
      <div className="world-toolbar">
        <label>
          Audience
          <select
            aria-label="World audience"
            value={audience}
            onChange={(e) => setAudience(e.target.value as typeof audience)}
          >
            <option value="researcher">Researcher</option>
            <option value="judge">Judge</option>
            <option value="portfolio">Portfolio</option>
          </select>
        </label>
        <button onClick={() => demonstrate(0)}>Demonstration 3.0</button>
        {(["physical", "xray", "evidence", "uncertainty"] as const).map((l) => (
          <button key={l} aria-pressed={lens === l} onClick={() => setLens(l)}>
            {l === "xray"
              ? "Engineering X-ray"
              : l === "evidence"
                ? "Evidence lens"
                : l === "uncertainty"
                  ? "Uncertainty lens"
                  : "Physical world"}
          </button>
        ))}
      </div>
      {act !== null && (
        <section className="world-act" aria-live="polite">
          <strong>
            ACT {act + 1} / {acts[act]}
          </strong>
          <button disabled={act === 0} onClick={() => demonstrate(act - 1)}>
            Previous act
          </button>
          <button disabled={act === 9} onClick={() => demonstrate(act + 1)}>
            Next act
          </button>
          <button onClick={() => setAct(null)}>Exit guide</button>
          <p>
            Stored experiments only · {view.source_experiment} · no live outcome
            is scripted.
          </p>
        </section>
      )}
      {audience === "portfolio" && (
        <p>
          Python owns physical simulation and evidence. Strict TypeScript
          consumes stored states. The shared engine provides bounded search,
          Pareto competition, counterexample interventions and sealed
          generalisation. Two-domain operation is demonstrated; general
          engineering intelligence remains a research hypothesis.
        </p>
      )}
      {error && <p role="status">{error}</p>}
      {lens === "uncertainty" && (
        <section
          className="world-depth"
          aria-label="Local uncertainty evidence"
        >
          <h2>Finite-sample reliability / local evidence</h2>
          <p>
            Frozen candidate: {experiment.heldout?.failures}/
            {experiment.heldout?.samples} held-out failures; 95% Wilson interval{" "}
            {experiment.heldout?.failure_rate_wilson_95
              .map((v) => `${(v * 100).toFixed(2)}%`)
              .join("–") ?? "UNTESTED"}
            .
          </p>
          <p>
            Conditional on the declared synthetic distribution. This is not
            field confidence, parameter certainty or formal proof. Microgrid
            parameter calibration remains untested; water calibration is
            synthetic.
          </p>
        </section>
      )}
      {publicArchive && (
        <p role="status">
          Public research archive · stored reproducible investigations. Run new
          scientific jobs in the trusted local research environment.
        </p>
      )}
      {audience === "researcher" && !publicArchive && (
        <details className="world-depth">
          <summary>Run a registered scientific investigation</summary>
          <p>
            Explicit Python tools; separate training/validation/held-out
            streams. No generated code. Field validity remains unestablished.
          </p>
          <div className="world-toolbar">
            {[
              {
                label: "Research seed",
                value: researchSeed,
                set: setResearchSeed,
                min: 0,
                max: 4294967295,
              },
              {
                label: "Engineering cost limit",
                value: costLimit,
                set: setCostLimit,
                min: 1,
                max: 100000,
              },
              {
                label: "Simulation budget",
                value: simulationLimit,
                set: setSimulationLimit,
                min: 1,
                max: 1500,
              },
              {
                label: "Candidate budget",
                value: candidateLimit,
                set: setCandidateLimit,
                min: 1,
                max: 64,
              },
              {
                label: "Generation budget",
                value: generationLimit,
                set: setGenerationLimit,
                min: 0,
                max: 8,
              },
              {
                label: "Training samples",
                value: trainCount,
                set: setTrainCount,
                min: 2,
                max: 32,
              },
              {
                label: "Validation samples",
                value: validationCount,
                set: setValidationCount,
                min: 2,
                max: 64,
              },
              {
                label: "Held-out samples",
                value: heldCount,
                set: setHeldCount,
                min: 2,
                max: 256,
              },
            ].map((c) => (
              <label key={c.label}>
                {c.label}
                <input
                  type="number"
                  aria-label={c.label}
                  value={c.value}
                  min={c.min}
                  max={c.max}
                  onChange={(e) => c.set(Number(e.target.value))}
                />
              </label>
            ))}
            <label>
              Failure probability target
              <input
                aria-label="Failure probability target"
                type="number"
                min="0"
                max="1"
                step=".01"
                value={failureTarget}
                onChange={(e) => setFailureTarget(Number(e.target.value))}
              />
            </label>
            <button onClick={runResearch} disabled={!!job}>
              Run domain investigation
            </button>
            {job && (
              <button
                onClick={() => fetch(`/api/jobs/${job}`, { method: "DELETE" })}
              >
                Cancel domain investigation
              </button>
            )}
          </div>
          <p role="status">{liveStatus}</p>
        </details>
      )}
      <section className="engineering-world">
        <div className="world-annotation">
          <span>
            {domain.toUpperCase()} /{" "}
            {!frame
              ? experiment.selection === null
                ? "UNTESTED / NO FULLY EVALUATED DESIGN"
                : "LOADING / NO REQUIREMENT CLAIM"
              : frame.outcome.passes
                ? "REQUIREMENTS SATISFIED IN THIS STATE"
                : "REQUIREMENT FAILURE / INSPECT EVIDENCE"}
          </span>
          <span>
            {frame?.scenario.id as string} · service{" "}
            {pct(frame?.outcome.service ?? null)}
          </span>
        </div>
        <PhysicalWorld
          experiment={experiment}
          frame={frame}
          time={time}
          onSelect={setSelected}
        />
        {compare && before && (
          <div className="parent-world">
            <p>PARENT / SAME SCENARIO AND COMPUTED INTERVAL</p>
            <PhysicalWorld
              experiment={experiment}
              frame={before}
              time={time}
              onSelect={setSelected}
            />
          </div>
        )}
      </section>
      <div className="world-toolbar">
        <label>
          Search strategy
          <select
            aria-label="World search strategy"
            value={strategy}
            onChange={(e) => {
              setStrategy(e.target.value);
              setCandidateId("");
              setScenario(0);
            }}
          >
            {["random", "evolutionary", "guided", "pareto", "hybrid"].map(
              (s) => (
                <option key={s}>{s}</option>
              ),
            )}
          </select>
        </label>
        <label>
          Predeclared seed
          <select
            aria-label="World experiment seed"
            value={seedIndex}
            onChange={(e) => {
              setSeedIndex(Number(e.target.value));
              setCandidateId("");
              setScenario(0);
            }}
          >
            {group.map((e, i) => (
              <option value={i} key={e.id}>
                {e.seed}
              </option>
            ))}
          </select>
        </label>
        <button onClick={counterexample}>Load training counterexample</button>
        <button onClick={() => setCompare(!compare)} disabled={!parent}>
          Compare parent / child
        </button>
        <label>
          Independent training scenario
          <input
            aria-label="World scenario"
            type="range"
            min="0"
            max={Math.max(0, (candidate?.frames.length ?? 1) - 1)}
            value={scenario}
            onChange={(e) => {
              setScenario(Number(e.target.value));
              setTime(0);
            }}
          />
        </label>
        {domain === "microgrid" &&
          frame?.outcome.domain === "microgrid" &&
          frame.outcome.state && (
            <label>
              Computed interval
              <input
                aria-label="Microgrid interval"
                type="range"
                min="0"
                max={frame.outcome.state.demand_W.length - 1}
                value={time}
                onChange={(e) => setTime(Number(e.target.value))}
              />
            </label>
          )}
      </div>
      <section className="world-lineage" aria-label="Candidate evolution">
        {experiment.candidates.map((c) => (
          <button
            key={c.id}
            disabled={!c.frames.length}
            aria-pressed={candidate?.id === c.id}
            onClick={() => {
              setCandidateId(c.id);
              setScenario(0);
              setTime(0);
            }}
            className={c.rejection_reason ? "rejected" : ""}
          >
            <span>
              G{c.generation} / {c.id.split(":").at(-1)}
            </span>
            <strong>{c.cost.toFixed(2)} cost</strong>
            <small>
              {c.rejection_reason ?? `${c.training_failures} training failures`}
            </small>
            {experiment.frontier.includes(c.id) && <small>NON-DOMINATED</small>}
          </button>
        ))}
      </section>
      <p className="world-verdict">
        Frozen selection {experiment.selection}: {experiment.heldout?.failures}/
        {experiment.heldout?.samples} held-out failures. Target{" "}
        {experiment.target_achieved
          ? "ESTABLISHED UNDER SPECIFIED DISTRIBUTION"
          : "UNESTABLISHED"}
        . {experiment.stop}. {experiment.solver_calls} physical solver calls.
      </p>
      {(lens !== "physical" || audience !== "researcher") && (
        <section className="world-depth" key={`${audience}-${lens}-${act}`}>
          <h2>
            {lens === "xray"
              ? "Equation → constraint → consequence"
              : "Evidence remains local"}
          </h2>
          {selected && <p>Selected component: {selected}</p>}
          {experiment.descriptor.equations.map((eq) => (
            <p key={eq}>
              <code>{eq}</code>
            </p>
          ))}
          <p>
            Current violations:{" "}
            {frame?.outcome.violations.join(", ") ||
              "none in this computed state"}
          </p>
          <EvidenceSummary
            value={experiment.descriptor.validity_envelope}
            allowRaw={false}
          />
          <details>
            <summary>Claim ledger / domain-scoped</summary>
            <EvidenceSummary
              value={experiment.claim_ledger}
              allowRaw={
                act === null &&
                (audience === "researcher" || lens === "evidence")
              }
            />
          </details>
          <details>
            <summary>
              Bounded verification / assumptions and proof scope
            </summary>
            <EvidenceSummary
              value={experiment.verification}
              allowRaw={
                act === null &&
                (audience === "researcher" || lens === "evidence")
              }
            />
          </details>
          <details>
            <summary>Plan / budgets / stopping</summary>
            <EvidenceSummary
              value={experiment.plan}
              allowRaw={
                act === null &&
                (audience === "researcher" || lens === "evidence")
              }
            />
          </details>
        </section>
      )}
      <p className="world-verdict">
        Three seeds are exploratory. Guided search is not established as
        superior; random search was stronger on this microgrid benchmark.
      </p>
      <details className="world-depth">
        <summary>Search ablation / preserve negative results</summary>
        <SearchAblation
          key={`${audience}-${lens}-${act}`}
          value={view.ablation}
          allowRaw={
            act === null && (audience === "researcher" || lens === "evidence")
          }
        />
      </details>
      <details className="world-depth">
        <summary>Water constraint negotiation / fresh test population</summary>
        <EvidenceSummary
          key={`${audience}-${lens}-${act}`}
          allowRaw={
            act === null && (audience === "researcher" || lens === "evidence")
          }
          value={{
            candidates: view.decision_candidates,
            negotiation: view.decision,
          }}
        />
        <p>
          Smallest known relaxation among tested designs is not a global optimum
          or infeasibility certificate.
        </p>
      </details>
      <footer>
        <p>
          Historical evidence unchanged: 38/200 · 44/200 → 13/200 at increased
          cost · 4/40 hospital failures; 2% target unestablished.
        </p>
        <p>
          Microgrid: energy adequacy, not AC physics. Water: field calibration
          and rupture validation incomplete. Numerical evidence is not formal
          proof. Scientific 2D retains exact stored values.
        </p>
        <p>Selected investigation: {experiment.id}</p>
        <code>{experiment.scientific_sha256 ?? view.source_sha256}</code>
      </footer>
    </main>
  );
}
