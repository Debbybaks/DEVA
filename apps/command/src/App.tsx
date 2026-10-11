import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { z } from "zod";
import { overview, positions, type Pose } from "./geometry";
const HydraulicWorkspace = lazy(() => import("./HydraulicWorkspace"));
const NetworkCanvas = lazy(() => import("./NetworkCanvas"));
import EvolutionMap from "./EvolutionMap";
import ParetoPlot from "./ParetoPlot";
import { useCommandState } from "./state";
import {
  layers,
  request,
  viewSchema,
  labSchema,
  jobSchema,
  jobStatusSchema,
  type View,
  type Result,
  type Scenario,
} from "./contracts";
const progressSchema = z.object({
  stage: z.string(),
  candidate_id: z.string().optional(),
  generation: z.number().optional(),
  experiment_id: z.string().optional(),
  error: z.string().optional(),
});
const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

export default function App() {
  const [physics, setPhysics] = useState(
    new URLSearchParams(window.location.search).get("model") === "hydraulic",
  );
  const [state, dispatch] = useCommandState();
  const [view, setView] = useState<View | null>(null);
  const [dataUrl, setDataUrl] = useState("/api/view/evolution");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [pose, setPose] = useState<Pose>(overview);
  const [diagram, setDiagram] = useState(false);
  const [seed, setSeed] = useState(20261013);
  const [generations, setGenerations] = useState(3);
  const [budget, setBudget] = useState(700);
  const [job, setJob] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<string[]>([]);
  const [pipe, setPipe] = useState("");
  const [secondPipe, setSecondPipe] = useState("");
  const [degradation, setDegradation] = useState(0);
  const [demand, setDemand] = useState(1.2);
  const [supply, setSupply] = useState(1);
  const [sourceLoss, setSourceLoss] = useState("");
  const [lab, setLab] = useState<{
    scenario: Scenario;
    result: Result;
    comparison: Result | null;
    source_losses: string[];
    experiment_id?: string;
  } | null>(null);
  const [labBusy, setLabBusy] = useState(false);
  const [traceNode, setTraceNode] = useState("conclusion:recommendation");
  const [trace, setTrace] = useState<string[]>([]);
  const labContext = useRef("");
  labContext.current = `${dataUrl}:${state.candidate}:${state.compare}:${state.split}:${state.index}`;
  const [reduced, setReduced] = useState(false);
  const frameRef = useRef<number[]>([]);
  const workerQualityFallback = useRef(false);
  useEffect(() => {
    frameRef.current = [];
    if (!running && workerQualityFallback.current) {
      setDiagram(false);
      workerQualityFallback.current = false;
    }
  }, [running]);
  const [frameMs, setFrameMs] = useState<number | null>(null);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(media.matches);
    const change = () => setReduced(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    if (physics) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setLab(null);
    request(dataUrl, viewSchema, { signal: controller.signal })
      .then((v) => {
        setView(v);
        dispatch({
          type: "candidate",
          id: v.recommendation ?? v.candidates[0].id,
        });
        dispatch({ type: "compare", id: null });
        dispatch({ type: "split", split: "heldout" });
        setBudget(v.problem.budget);
        setLoading(false);
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setError(String(e));
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [dataUrl, physics]);
  useEffect(() => {
    setLab(null);
  }, [state.candidate, state.compare, state.split, state.index]);
  useEffect(() => {
    if (!job) return;
    const connection = new EventSource(`/api/jobs/${job}/events`);
    const finish = (status: string, message?: string) => {
      if (status === "completed") {
        setDataUrl(`/api/jobs/${job}/view`);
        setRunning(false);
        connection.close();
      } else if (status === "failed" || status === "cancelled") {
        setRunning(false);
        connection.close();
        if (message) setError(message);
      }
    };
    connection.onmessage = (event) => {
      let data: unknown;
      try {
        data = JSON.parse(event.data);
      } catch {
        setError("Invalid engine progress JSON");
        return;
      }
      const parsed = progressSchema.safeParse(data);
      if (!parsed.success) {
        setError("Invalid engine progress contract");
        return;
      }
      const p = parsed.data;
      setEvents((current) =>
        [
          ...current,
          `${p.stage.replaceAll("_", " ")}${p.candidate_id ? ` · ${p.candidate_id}` : ""}`,
        ].slice(-100),
      );
      finish(p.stage, p.error);
    };
    connection.onerror = () => {
      request(`/api/jobs/${job}`, jobStatusSchema)
        .then((s) => finish(s.status, s.error ?? undefined))
        .catch((e) => setError(String(e)));
    };
    return () => connection.close();
  }, [job]);
  const observeFrame = useCallback(
    (ms: number) => {
      const samples = frameRef.current;
      samples.push(ms);
      if (samples.length === 30) {
        const mean = samples.reduce((a, b) => a + b, 0) / samples.length;
        setFrameMs(mean);
        if (running && mean > 80 && !workerQualityFallback.current) {
          workerQualityFallback.current = true;
          setDiagram(true);
        }
        samples.length = 0;
      }
    },
    [running],
  );
  const choose = useCallback(
    (id: string) => dispatch({ type: "candidate", id }),
    [dispatch],
  );
  const select = useCallback(
    (id: string) => dispatch({ type: "selection", id }),
    [dispatch],
  );
  const candidate =
    view?.candidates.find((c) => c.id === state.candidate) ??
    view?.candidates[0];
  const comparison = view?.candidates.find((c) => c.id === state.compare);
  const scenarios = view?.scenarios[state.split] ?? [];
  const index = Math.min(state.index, Math.max(0, scenarios.length - 1));
  const scenario = lab?.scenario ?? scenarios[index];
  const result = lab?.result ?? candidate?.splits[state.split]?.results[index];
  const comparisonResult =
    lab?.comparison ?? comparison?.splits[state.split]?.results[index];
  const selectedEdge =
    view?.problem.edges.findIndex((e) => e.id === state.selection) ?? -1;
  const selectedNode = view?.problem.nodes.indexOf(state.selection ?? "") ?? -1;
  const metrics = candidate?.splits.heldout?.metrics;
  const runEvolution = async () => {
    if (!view) return;
    setRunning(true);
    setError("");
    setEvents([]);
    try {
      const raw = {
        ...view.problem,
        budget,
        objective: `Provide at least ${pct(view.problem.target)} per-node service within a ${budget}-unit capacity budget; evolve resilience under declared and synthetic scenarios.`,
      };
      const response = await request("/api/jobs", jobSchema, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw,
          seed,
          generations,
          train_samples: 60,
          validation_samples: 80,
          test_samples: 200,
        }),
      });
      if (response.status === "completed") {
        setDataUrl(`/api/jobs/${response.job_id}/view`);
        setRunning(false);
      } else setJob(response.job_id);
    } catch (e) {
      setError(String(e));
      setRunning(false);
    }
  };
  const runLab = async () => {
    if (!view || !candidate) return;
    const context = labContext.current;
    setLabBusy(true);
    setError("");
    const availability = view.problem.edges.map((e) =>
      e.id === pipe || e.id === secondPipe ? degradation : 1,
    );
    const body = {
      raw: view.problem,
      capacities: candidate.capacities,
      availability,
      supply_factor: supply,
      demand_factor: demand,
      source_losses: sourceLoss ? [sourceLoss] : [],
    };
    try {
      const [a, b] = await Promise.all([
        request("/api/lab", labSchema, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }),
        comparison
          ? request("/api/lab", labSchema, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                ...body,
                capacities: comparison.capacities,
              }),
            })
          : Promise.resolve(null),
      ]);
      if (context === labContext.current) {
        setLab({
          scenario: a.scenario,
          result: a.result,
          comparison: b?.result ?? null,
          source_losses: a.source_losses,
          experiment_id: a.experiment_id,
        });
        dispatch({ type: "layer", layer: "failure" });
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLabBusy(false);
    }
  };
  const focus = () => {
    if (!view) return;
    const coordinates = positions(view.problem);
    const e = view.problem.edges[selectedEdge];
    const target = e
      ? coordinates[e.tail].map((v, i) => (v + coordinates[e.head][i]) / 2)
      : (coordinates[state.selection ?? ""] ?? [0, 0, 0]);
    setPose({
      position: [target[0], 6, 6],
      target: target as [number, number, number],
    });
  };
  const traceEvidence = () => {
    const graph = view?.provenance;
    if (!graph) return;
    const seen = new Set([traceNode]);
    let changed = true;
    while (changed) {
      changed = false;
      for (const edge of graph.edges)
        if (seen.has(edge.target) && !seen.has(edge.source)) {
          seen.add(edge.source);
          changed = true;
        }
    }
    setTrace([...seen]);
  };
  const evidenceUrl = dataUrl.startsWith("/api/jobs/")
    ? dataUrl.replace("/view", "/evidence")
    : dataUrl.includes("baseline")
      ? "/api/evidence/baseline"
      : "/api/evidence/evolution";
  if (physics)
    return (
      <Suspense
        fallback={<main className="boot">Loading hydraulic world…</main>}
      >
        <HydraulicWorkspace onBack={() => setPhysics(false)} />
      </Suspense>
    );
  if (!view)
    return (
      <main className="boot">
        <div className="wordmark">
          DEVA<span>DESIGN · ENGINEERING · VERIFICATION · AUTONOMY</span>
        </div>
        <h1>
          Design. Simulate. Break.
          <br />
          Evolve. Verify.
        </h1>
        <p>{error || "Connecting to the scientific engine…"}</p>
        {error && (
          <>
            <p>
              Start the Python API on port 8000. No substitute simulation data
              is displayed.
            </p>
            <button onClick={() => window.location.reload()}>
              Reconnect to engine
            </button>
          </>
        )}
      </main>
    );
  return (
    <div className="command-shell">
      <header className="masthead">
        <a
          className="wordmark"
          href="#main-canvas"
          aria-label="DEVA engineering command environment"
        >
          DEVA<span>DESIGN, ENGINEERING & VERIFICATION AUTONOMY</span>
        </a>
        <nav aria-label="Command modes">
          <button onClick={() => setPhysics(true)}>Hydraulic V2</button>
          {(["laboratory", "evolution", "evidence"] as const).map((mode) => (
            <button
              key={mode}
              className={state.mode === mode ? "active" : ""}
              aria-pressed={state.mode === mode}
              onClick={() => dispatch({ type: "mode", mode })}
            >
              {mode}
            </button>
          ))}
        </nav>
        <div className="engine-indicator">
          <i className={running ? "working" : ""} />
          {running ? "COMPUTING" : "SCIENTIFIC ENGINE"}
          <span>PYTHON / HIGHS</span>
        </div>
      </header>
      <div className="baseline-strip">
        <b>IMMUTABLE BASELINE</b>
        <span>38 / 200 held-out failures</span>
        <span>
          36 outage–demand interactions · 2 topological disconnections
        </span>
        <a href="/api/evidence/diagnosis" target="_blank" rel="noreferrer">
          Inspect diagnosis ↗
        </a>
      </div>
      <div className="workspace">
        <aside className="study-rail">
          <div className="rail-heading">
            <span>01 / RESEARCH STUDY</span>
            <select
              aria-label="Evidence dataset"
              value={
                dataUrl.startsWith("/api/jobs/")
                  ? "job"
                  : dataUrl.includes("baseline")
                    ? "baseline"
                    : "evolution"
              }
              onChange={(e) => {
                if (e.target.value !== "job")
                  setDataUrl(`/api/view/${e.target.value}`);
              }}
            >
              <option value="evolution">Evolution experiment</option>
              <option value="baseline">Preserved baseline</option>
              {dataUrl.startsWith("/api/jobs/") && (
                <option value="job">Current experiment</option>
              )}
            </select>
          </div>
          <h1>
            Design. Simulate.
            <br />
            Break. Evolve.
            <br />
            <em>Verify.</em>
          </h1>
          <p className="objective">{view.problem.objective}</p>
          <div className="requirement">
            <span>REQUIRED SERVICE</span>
            <strong>{pct(view.problem.target)}</strong>
            <small>at every demand node</small>
          </div>
          <div className="constraint-line">
            <span>Capacity budget</span>
            <b>{view.problem.budget.toFixed(0)} units</b>
          </div>
          <div className="constraint-line">
            <span>Model scope</span>
            <b>Static transport</b>
          </div>
          <section className="candidate-selector">
            <h2>
              Candidate archive <span>{view.candidates.length}</span>
            </h2>
            <select
              aria-label="Selected candidate"
              value={candidate?.id ?? ""}
              onChange={(e) => choose(e.target.value)}
            >
              {view.candidates.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} · G{c.generation} · {c.disposition}
                </option>
              ))}
            </select>
            {candidate && (
              <>
                <div className="candidate-title">
                  {candidate.id}
                  <span>GENERATION {candidate.generation}</span>
                </div>
                <p className="mutation">
                  {candidate.mutations
                    .map((m) => m.operator.replaceAll("_", " "))
                    .join(" / ")}
                </p>
                <p className="verdict">
                  {candidate.rejection_reason ??
                    "Survives on the empirical training frontier"}
                </p>
                <div className="constraint-line">
                  <span>Capacity cost</span>
                  <b>{candidate.cost.toFixed(2)}</b>
                </div>
              </>
            )}
            <label>
              Compare with
              <select
                aria-label="Comparison candidate"
                value={state.compare ?? ""}
                onChange={(e) =>
                  dispatch({ type: "compare", id: e.target.value || null })
                }
              >
                <option value="">Single design</option>
                {view.candidates
                  .filter((c) => c.id !== candidate?.id)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id}
                    </option>
                  ))}
              </select>
            </label>
          </section>
          <section className="experiment-controls">
            <h2>Evolve a new experiment</h2>
            <div className="config-grid">
              <label>
                Seed
                <input
                  aria-label="Experiment seed"
                  type="number"
                  min="0"
                  max="4294967295"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                />
              </label>
              <label>
                Generations
                <input
                  aria-label="Generation budget"
                  type="number"
                  min="1"
                  max="4"
                  value={generations}
                  onChange={(e) => setGenerations(Number(e.target.value))}
                />
              </label>
            </div>
            <label>
              Budget
              <input
                aria-label="Capacity budget"
                type="number"
                min="1"
                max="100000"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
              />
            </label>
            <button
              className="primary"
              onClick={runEvolution}
              disabled={running || loading}
            >
              ↗ {running ? "Evolution in progress" : "Run design evolution"}
            </button>
            {running && job && (
              <button
                className="quiet"
                onClick={() =>
                  fetch(`/api/jobs/${job}`, { method: "DELETE" }).catch((e) =>
                    setError(String(e)),
                  )
                }
              >
                Request cancellation
              </button>
            )}
            <small>
              60 training / 80 validation / 200 held-out.
              <br />
              Selection freezes before validation and test.
            </small>
          </section>
        </aside>
        <main id="main-canvas" className="engineering-main">
          <div className="canvas-title">
            <div>
              <span>EMERGENCY WATER NETWORK / CAPACITY MODEL</span>
              <h2>
                {state.mode === "evidence"
                  ? "Engineering Evidence"
                  : state.mode === "evolution"
                    ? "Design Evolution Engine"
                    : "Engineering Command Environment"}
              </h2>
            </div>
            <span className="model-tag">
              6-Pipe demonstration · topology layout
            </span>
          </div>
          <div
            className="layer-bar"
            role="group"
            aria-label="Scientific layers"
          >
            {layers.map((layer) => (
              <button
                key={layer}
                aria-pressed={state.layer === layer}
                className={state.layer === layer ? "active" : ""}
                onClick={() => dispatch({ type: "layer", layer })}
              >
                {layer}
              </button>
            ))}
          </div>
          {error && (
            <div className="error-banner" role="alert">
              {error}
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                ×
              </button>
            </div>
          )}
          {loading && (
            <p className="loading-note" role="status">
              Loading engine evidence…
            </p>
          )}
          {candidate && result && scenario && (
            <div className={`canvas-area ${comparison ? "paired" : ""}`}>
              <div className="canvas-pane">
                <div className="canvas-overlay">
                  <b>
                    {candidate.id}
                    {running ? " · SOLVER ACTIVE / LAST COMPLETED STATE" : ""}
                  </b>
                  <span className={result.passes ? "pass" : "fail"}>
                    {pct(result.service_fraction)} COMMON SERVICE ·{" "}
                    {result.passes ? "PASS" : "FAIL"}
                  </span>
                </div>
                <Suspense
                  fallback={
                    <div className="canvas-loading">
                      Loading scientific renderer…
                    </div>
                  }
                >
                  <NetworkCanvas
                    problem={view.problem}
                    diagram={diagram}
                    candidate={candidate}
                    result={result}
                    scenario={scenario}
                    layer={state.layer}
                    selection={state.selection}
                    select={select}
                    animate={state.animate && !reduced}
                    speed={state.speed}
                    pose={pose}
                    setPose={setPose}
                    sourceLosses={lab?.source_losses}
                    onFrame={observeFrame}
                  />
                </Suspense>
              </div>
              {comparison && comparisonResult && (
                <div className="canvas-pane">
                  <div className="canvas-overlay">
                    <b>{comparison.id}</b>
                    <span className={comparisonResult.passes ? "pass" : "fail"}>
                      {pct(comparisonResult.service_fraction)} COMMON SERVICE ·{" "}
                      {comparisonResult.passes ? "PASS" : "FAIL"}
                    </span>
                  </div>
                  <Suspense
                    fallback={
                      <div className="canvas-loading">
                        Loading scientific renderer…
                      </div>
                    }
                  >
                    <NetworkCanvas
                      problem={view.problem}
                      diagram={diagram}
                      candidate={comparison}
                      result={comparisonResult}
                      scenario={scenario}
                      layer={state.layer}
                      selection={state.selection}
                      select={select}
                      animate={state.animate && !reduced}
                      speed={state.speed}
                      pose={pose}
                      setPose={setPose}
                      sourceLosses={lab?.source_losses}
                    />
                  </Suspense>
                </div>
              )}
              <div className="canvas-tools">
                <select
                  aria-label="Rendering mode"
                  value={diagram ? "diagram" : "webgl"}
                  onChange={(e) => setDiagram(e.target.value === "diagram")}
                >
                  <option value="webgl">WebGL / spatial</option>
                  <option value="diagram">2D / low-load</option>
                </select>
                <button onClick={() => setPose(overview)} disabled={diagram}>
                  Overview
                </button>
                <button onClick={focus} disabled={diagram || !state.selection}>
                  Focus selection
                </button>
                <button
                  disabled={diagram}
                  aria-pressed={state.animate}
                  onClick={() => dispatch({ type: "animation" })}
                >
                  {state.animate ? "Ⅱ Pause flux" : "▶ Animate flux"}
                </button>
                <select
                  disabled={diagram}
                  aria-label="Flux animation speed"
                  value={state.speed}
                  onChange={(e) =>
                    dispatch({ type: "speed", speed: Number(e.target.value) })
                  }
                >
                  {[1, 5, 10, 50].map((n) => (
                    <option key={n} value={n}>
                      {n}× visual flux
                    </option>
                  ))}
                </select>
              </div>
              <div className="canvas-legend">
                <span>
                  <i />
                  Capacity encoded by width · motion encodes relative volumetric
                  flux
                </span>
                <span>
                  {state.layer === "risk"
                    ? "Colour: held-out failure conditional on this pipe outage; co-occurring hazards included"
                    : state.layer === "uncertainty"
                      ? "Hatching: width of conditional Wilson interval; untested when no observations"
                      : state.layer === "verification"
                        ? "Declared-suite evidence only; scenario failures remain visible"
                        : state.layer === "dependency"
                          ? "Colour groups shared corridors; no temporal cascade model"
                          : "Orbit to inspect · scroll to zoom · click a component"}
                </span>
                <b>
                  {diagram
                    ? "2D NUMERICAL TOPOLOGY · EXACT FLOWS / OTHER LAYERS IN INSPECTOR"
                    : "STEADY STATE — NO TRAVEL-TIME OR HYDRAULIC ANIMATION"}
                </b>
              </div>
            </div>
          )}
          <div className="scenario-browser">
            <div>
              <span>
                SCENARIO INDEX ·{" "}
                {lab ? "INTERACTIVE DISTURBANCE" : state.split.toUpperCase()}
              </span>
              <strong>{lab ? "interactive-lab" : scenario?.id}</strong>
            </div>
            <select
              aria-label="Scenario split"
              value={state.split}
              onChange={(e) =>
                dispatch({ type: "split", split: e.target.value })
              }
            >
              {Object.keys(view.scenarios).map((split) => (
                <option key={split}>{split}</option>
              ))}
            </select>
            <button
              aria-label="Previous scenario"
              disabled={index === 0}
              onClick={() => dispatch({ type: "scenario", index: index - 1 })}
            >
              ←
            </button>
            <input
              aria-label="Scenario index"
              type="range"
              min="0"
              max={Math.max(0, scenarios.length - 1)}
              value={index}
              onChange={(e) =>
                dispatch({ type: "scenario", index: Number(e.target.value) })
              }
            />
            <button
              aria-label="Next scenario"
              disabled={index === scenarios.length - 1}
              onClick={() => dispatch({ type: "scenario", index: index + 1 })}
            >
              →
            </button>
            <span>
              {index + 1}/{scenarios.length}
            </span>
            {lab && (
              <button onClick={() => setLab(null)}>
                Return to recorded scenario
              </button>
            )}
            {lab?.experiment_id && (
              <a href={`/api/lab/${lab.experiment_id}`} download>
                ↓ Disturbance evidence
              </a>
            )}
          </div>
          <div
            className={`analysis-floor ${state.mode === "evolution" ? "expanded" : ""}`}
          >
            {state.mode === "evidence" ? (
              <section className="evidence-mode">
                <div className="section-label">EVIDENCE / REPRODUCIBILITY</div>
                <h3>{view.experiment_id}</h3>
                <dl>
                  <dt>Scientific SHA-256</dt>
                  <dd className="hash">{view.scientific_sha256}</dd>
                  <dt>Solver / software</dt>
                  <dd>
                    {Object.entries(view.software)
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(" · ")}
                  </dd>
                  <dt>Independent streams</dt>
                  <dd>
                    {Object.entries(view.seeds)
                      .map(([k, v]) => `${k}=${v}`)
                      .join(" · ")}
                  </dd>
                </dl>
                <a className="download" href={evidenceUrl} download>
                  ↓ Full Engineering Evidence Package
                </a>
                <details>
                  <summary>
                    Assumptions, uncertainty and scientific limits
                  </summary>
                  {view.limitations.map((l) => (
                    <p key={l}>{l}</p>
                  ))}
                </details>
                <details>
                  <summary>Trace a conclusion backwards</summary>
                  {view.provenance ? (
                    <>
                      <label>
                        Conclusion or evidence node
                        <select
                          aria-label="Provenance node"
                          value={traceNode}
                          onChange={(e) => setTraceNode(e.target.value)}
                        >
                          {view.provenance.nodes
                            .filter(
                              (n) =>
                                n.kind === "conclusion" ||
                                n.kind === "verification" ||
                                n.kind === "candidate",
                            )
                            .map((n) => (
                              <option key={n.id} value={n.id}>
                                {n.id}
                              </option>
                            ))}
                        </select>
                      </label>
                      <button onClick={traceEvidence}>
                        Trace supporting evidence
                      </button>
                      <p>
                        {trace.length} linked requirements, assumptions,
                        candidates and results.
                      </p>
                      <ul className="trace-list">
                        {trace.slice(0, 80).map((id) => (
                          <li key={id}>{id}</li>
                        ))}
                      </ul>
                      {trace.length > 80 && (
                        <p>
                          First 80 nodes shown; full graph is in the export.
                        </p>
                      )}
                    </>
                  ) : (
                    <p>
                      The preserved Phase-1 package has an event trace. A
                      provenance graph is available in evolution experiments.
                    </p>
                  )}
                </details>
                <details>
                  <summary>
                    Infeasible synthesis attempts (
                    {view.infeasible_attempts.length})
                  </summary>
                  <pre>{JSON.stringify(view.infeasible_attempts, null, 2)}</pre>
                </details>
                <details>
                  <summary>Failure taxonomy / sensitivity</summary>
                  <pre>
                    {JSON.stringify(
                      {
                        failure_taxonomy: view.failure_taxonomy,
                        sensitivity: view.sensitivity,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
              </section>
            ) : (
              <>
                <section className="evolution-section">
                  <div className="section-label">
                    DESIGN ANCESTRY{" "}
                    <span>Every rejected branch remains inspectable</span>
                  </div>
                  {candidate && (
                    <EvolutionMap
                      candidates={view.candidates}
                      selected={candidate.id}
                      choose={choose}
                    />
                  )}
                </section>
                <section className="frontier-section">
                  <div className="section-label">EMPIRICAL PARETO FRONTIER</div>
                  {candidate && view.pareto_frontier.length > 0 ? (
                    <ParetoPlot
                      view={view}
                      selected={candidate.id}
                      choose={choose}
                    />
                  ) : (
                    <p>
                      Training Pareto analysis is available in evolution
                      experiments.
                    </p>
                  )}
                  <p>
                    Three objectives: cost, training failure rate, unmet demand.
                    <br />
                    The 2D projection shows cost and failure rate.
                  </p>
                </section>
              </>
            )}
          </div>
        </main>
        <aside className="inspection-rail">
          <section className="failure-lab">
            <div className="rail-heading">02 / FAILURE LAB</div>
            <h2>Try to break it.</h2>
            <p>Controlled disturbances. Recomputed by Python.</p>
            <label>
              Primary pipe
              <select
                aria-label="Primary pipe outage"
                value={pipe}
                onChange={(e) => setPipe(e.target.value)}
              >
                <option value="">No pipe outage</option>
                {view.problem.edges.map((e) => (
                  <option key={e.id}>{e.id}</option>
                ))}
              </select>
            </label>
            <label>
              Simultaneous pipe
              <select
                aria-label="Second pipe outage"
                value={secondPipe}
                onChange={(e) => setSecondPipe(e.target.value)}
              >
                <option value="">No second outage</option>
                {view.problem.edges.map((e) => (
                  <option key={e.id}>{e.id}</option>
                ))}
              </select>
            </label>
            <label>
              Remaining pipe capacity <b>{pct(degradation)}</b>
              <input
                aria-label="Remaining pipe capacity"
                type="range"
                min="0"
                max="1"
                step=".05"
                value={degradation}
                onChange={(e) => setDegradation(Number(e.target.value))}
              />
            </label>
            <label>
              Demand multiplier <b>{demand.toFixed(2)}×</b>
              <input
                aria-label="Demand multiplier"
                type="range"
                min=".5"
                max="2"
                step=".05"
                value={demand}
                onChange={(e) => setDemand(Number(e.target.value))}
              />
            </label>
            <label>
              Supply multiplier <b>{supply.toFixed(2)}×</b>
              <input
                aria-label="Supply multiplier"
                type="range"
                min="0"
                max="1"
                step=".05"
                value={supply}
                onChange={(e) => setSupply(Number(e.target.value))}
              />
            </label>
            <label>
              Source loss
              <select
                aria-label="Source loss"
                value={sourceLoss}
                onChange={(e) => setSourceLoss(e.target.value)}
              >
                <option value="">No source loss</option>
                {view.problem.nodes
                  .filter((n) => view.problem.supply[n] > 0)
                  .map((n) => (
                    <option key={n}>{n}</option>
                  ))}
              </select>
            </label>
            <button
              className="attack-button"
              onClick={runLab}
              disabled={labBusy}
            >
              {labBusy ? "Solving disturbance…" : "↗ Apply disturbance"}
            </button>
            {view.adversarial && (
              <details>
                <summary>Adversarial discoveries</summary>
                <p>
                  Select the recommended candidate in single-design mode to
                  replay its attacks.
                </p>
                <p>
                  {view.adversarial.failures} failures in{" "}
                  {view.adversarial.tested} deliberately selected attacks.
                </p>
                <select
                  aria-label="Discovered adversarial scenario"
                  disabled={
                    candidate?.id !== view.recommendation || Boolean(comparison)
                  }
                  defaultValue=""
                  onChange={(e) => {
                    const r = view.adversarial?.results[Number(e.target.value)];
                    if (r) {
                      setLab({
                        scenario: r.scenario,
                        result: r.result,
                        comparison: null,
                        source_losses: [],
                      });
                      dispatch({ type: "layer", layer: "failure" });
                    }
                  }}
                >
                  <option value="" disabled>
                    Select a discovered attack
                  </option>
                  {view.adversarial.results
                    .filter((r) => !r.result.passes)
                    .map((r) => (
                      <option
                        key={r.scenario.id}
                        value={view.adversarial!.results.indexOf(r)}
                      >
                        {r.scenario.id} · {pct(r.result.service_fraction)}{" "}
                        service
                      </option>
                    ))}
                </select>
                {view.adversarial.topology_cuts.map((c) => (
                  <p key={c.demand_node}>
                    {c.demand_node}: {c.minimum_pipe_outages}-pipe topological
                    cut ({c.edges.join(", ")}).
                  </p>
                ))}
              </details>
            )}
          </section>
          <section className="inspector">
            <div className="rail-heading">03 / EQUATION INSPECTOR</div>
            <select
              aria-label="Inspect component"
              value={state.selection ?? ""}
              onChange={(e) => select(e.target.value)}
            >
              <option value="">Select a component</option>
              {view.problem.nodes.map((n) => (
                <option key={n}>{n}</option>
              ))}
              {view.problem.edges.map((e) => (
                <option key={e.id}>{e.id}</option>
              ))}
            </select>
            {selectedEdge >= 0 && candidate && result && scenario ? (
              <>
                <h3>{state.selection}</h3>
                <div className="equation">0 ≤ fₑ ≤ aₑ cₑ</div>
                <dl>
                  <dt>Installed capacity cₑ</dt>
                  <dd>{candidate.capacities[selectedEdge].toFixed(3)} m³/h</dd>
                  <dt>Available fraction aₑ</dt>
                  <dd>{scenario.availability[selectedEdge].toFixed(2)}</dd>
                  <dt>Computed flow fₑ</dt>
                  <dd>{result.flow[selectedEdge].toFixed(3)} m³/h</dd>
                  <dt>Capacity unit cost</dt>
                  <dd>
                    {view.problem.edges[selectedEdge].unit_cost} units/(m³/h)
                  </dd>
                  <dt>Dependency corridor</dt>
                  <dd>{view.problem.edges[selectedEdge].corridor}</dd>
                  <dt>Held-out failure conditional on outage</dt>
                  <dd>
                    {candidate.visual_fields[selectedEdge]
                      ?.conditional_failure_rate == null
                      ? "Untested"
                      : `${(100 * candidate.visual_fields[selectedEdge].conditional_failure_rate!).toFixed(1)}% (${candidate.visual_fields[selectedEdge].outage_failures}/${candidate.visual_fields[selectedEdge].outage_trials} trials)`}
                  </dd>
                  <dt>Conditional Wilson 95% interval</dt>
                  <dd>
                    {candidate.visual_fields[selectedEdge]
                      ?.conditional_wilson_95
                      ? candidate.visual_fields[selectedEdge]
                          .conditional_wilson_95!.map(
                            (v) => `${(100 * v).toFixed(1)}%`,
                          )
                          .join("–")
                      : "Untested"}
                  </dd>
                  <dt>Pressure</dt>
                  <dd>Untested in this capacity model</dd>
                </dl>
              </>
            ) : selectedNode >= 0 && result ? (
              <>
                <h3>{state.selection}</h3>
                <div className="equation">Bf + q − y = 0</div>
                <dl>
                  <dt>Injection q</dt>
                  <dd>{result.injection[selectedNode].toFixed(3)} m³/h</dd>
                  <dt>Delivery y</dt>
                  <dd>{result.delivered[selectedNode].toFixed(3)} m³/h</dd>
                  <dt>Demand d</dt>
                  <dd>{result.demand[selectedNode].toFixed(3)} m³/h</dd>
                </dl>
              </>
            ) : (
              <p>
                Select a pipe or node to inspect the variables, units and
                constraints.
              </p>
            )}
          </section>
          {candidate && (
            <section className="earned-evidence">
              <div className="rail-heading">04 / EARNED EVIDENCE</div>
              <strong>{candidate.verification.level}</strong>
              <p>Scope: declared finite capacity-network suite.</p>
              {metrics && (
                <>
                  <div className="failure-count">
                    {metrics.failures}
                    <span>/ {metrics.samples} held-out failures</span>
                  </div>
                  <p>
                    Conditional Wilson 95% interval:
                    <br />
                    {pct(metrics.failure_rate_wilson_95[0])}–
                    {pct(metrics.failure_rate_wilson_95[1])}
                  </p>
                </>
              )}
              <p className="integrity">
                Numerical evidence. No mathematical or formal verification.
                Synthetic hazards.
              </p>
            </section>
          )}
        </aside>
      </div>
      <footer className="status-bar">
        <span>
          <i />
          {running ? (events.at(-1) ?? "Queued") : view.experiment_id}
        </span>
        <span>PRESSURE: UNTESTED · CASCADE: UNMODELLED</span>
        <span>
          {frameMs ? `${frameMs.toFixed(1)} ms mean rendered frame · ` : ""}
          LOCAL RESEARCH SYSTEM
        </span>
      </footer>
    </div>
  );
}
