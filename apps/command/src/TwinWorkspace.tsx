import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { request } from "./contracts";
import { twinViewSchema, type TwinView } from "./twinContracts";
import { overview, positions, type Pose } from "./geometry";
const NetworkCanvas = lazy(() => import("./NetworkCanvas"));
const layers = [
  "observations",
  "residuals",
  "uncertainty",
  "pressure",
  "flow",
  "hazard",
] as const;
type Layer = (typeof layers)[number];
const pct = (v: number) => `${(100 * v).toFixed(1)}%`;
const stages = [
  "Observe synthetic truth",
  "Reveal model mismatch",
  "Calibrate parameters",
  "Validate withheld measurements",
  "Initiate research cascade",
  "Inspect secondary failure",
  "Choose useful sensors",
  "Review autonomous investigation",
  "Inspect bounded proof",
  "Expose remaining uncertainty",
];
export default function TwinWorkspace({ onBack }: { onBack: () => void }) {
  const sampleTimes = useRef<number[]>([]),
    adaptive = useRef(true),
    runController = useRef<AbortController | null>(null);
  const [renderNotice, setRenderNotice] = useState(""),
    [reduced, setReduced] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const change = () => setReduced(media.matches);
    change();
    media.addEventListener("change", change);
    return () => {
      media.removeEventListener("change", change);
      runController.current?.abort();
    };
  }, []);
  const [view, setView] = useState<TwinView | null>(null),
    [error, setError] = useState(""),
    [url, setUrl] = useState("/api/twin/view");
  const [mode, setMode] = useState<
      "observations" | "cascade" | "agent" | "counterexample" | "failures"
    >("observations"),
    [index, setIndex] = useState(0),
    [layer, setLayer] = useState<Layer>("observations");
  const [agentCandidate, setAgentCandidate] = useState("");
  const [fitted, setFitted] = useState(false),
    [compare, setCompare] = useState(false),
    [quality, setQuality] = useState<"2d" | "standard" | "high">("standard"),
    [selection, setSelection] = useState<string | null>(null),
    [pose, setPose] = useState<Pose>(overview);
  const [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(1),
    [camera, setCamera] = useState(false),
    [evidence, setEvidence] = useState(false),
    [demo, setDemo] = useState<number | null>(null),
    [evidenceNode, setEvidenceNode] = useState("observations");
  const [job, setJob] = useState<string | null>(null),
    [status, setStatus] = useState(""),
    [seed, setSeed] = useState(20261031),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setView(null);
    request(url, twinViewSchema, { signal: controller.signal })
      .then((v) => {
        setView(v);
        setError("");
        setIndex(0);
        setSelection(null);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(String(e));
      });
    return () => controller.abort();
  }, [url]);
  useEffect(() => {
    if (!job) return;
    const stream = new EventSource(`/api/jobs/${job}/events`);
    stream.onmessage = (event) => {
      try {
        const value = JSON.parse(event.data) as {
          stage: string;
          error?: string;
        };
        setStatus(value.stage);
        if (value.stage === "completed") {
          setUrl(`/api/jobs/${job}/view`);
          setJob(null);
          stream.close();
        }
        if (["failed", "cancelled"].includes(value.stage)) {
          setError(value.error ?? value.stage);
          setJob(null);
          stream.close();
        }
      } catch {
        setError("Invalid scientific progress event");
      }
    };
    return () => stream.close();
  }, [job]);
  const count =
    mode === "failures"
      ? (view?.failed_cases.length ?? 0)
      : mode === "cascade"
        ? (view?.cascade.length ?? 0)
        : mode === "observations"
          ? (view?.frames.length ?? 0)
          : 1;
  useEffect(() => {
    if (!playing || !count) return;
    const timer = setInterval(() => {
      setIndex((i) => {
        if (i + 1 >= count) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, 900 / speed);
    return () => clearInterval(timer);
  }, [playing, speed, count]);
  const frame = view?.frames[Math.min(index, (view?.frames.length ?? 1) - 1)],
    cascadeFrame =
      view?.cascade[Math.min(index, (view?.cascade.length ?? 1) - 1)];
  const agentState = view?.agent_candidates.find(
    (c) => c.id === (agentCandidate || view.engineering_agent.selection),
  );
  const failedCase =
    view?.failed_cases[Math.min(index, (view?.failed_cases.length ?? 1) - 1)];
  const state =
    mode === "failures"
      ? failedCase?.state
      : mode === "cascade"
        ? cascadeFrame?.state
        : mode === "agent"
          ? agentState?.state
          : mode === "counterexample"
            ? view?.counterexample?.state
            : fitted
              ? frame?.estimated
              : frame?.baseline;
  const gpu =
    mode === "failures"
      ? failedCase?.gpu
      : mode === "cascade"
        ? cascadeFrame?.gpu
        : mode === "agent"
          ? agentState?.gpu
          : mode === "counterexample"
            ? view?.counterexample?.gpu
            : fitted
              ? frame?.estimated_gpu
              : frame?.baseline_gpu;
  const measurements = useMemo(
    () =>
      Object.fromEntries(
        (mode === "observations" ? (frame?.observations ?? []) : []).map(
          (r) => [
            r.observation.component,
            {
              value: r.observation.value_si,
              prediction: fitted ? r.prediction : r.initial_prediction,
              residual:
                (fitted ? r.prediction : r.initial_prediction) -
                r.observation.value_si,
              sigma: r.observation.sigma_si,
              unit: r.observation.canonical_unit,
              standardized:
                ((fitted ? r.prediction : r.initial_prediction) -
                  r.observation.value_si) /
                r.observation.sigma_si,
              parameterRatio:
                r.parameter_variance === null
                  ? null
                  : Math.sqrt(r.parameter_variance) / r.observation.sigma_si,
            },
          ],
        ),
      ),
    [mode, frame, fitted],
  );
  const focus = useCallback(
    (component: string) => {
      if (!view) return;
      setSelection(component);
      const p = positions(view.problem);
      const pipe = view.problem.edges.find((e) => e.id === component);
      const target = p[component] ?? (pipe ? p[pipe.head] : null);
      if (target)
        setPose({ target, position: [target[0] + 2.5, 4.5, target[2] + 5.5] });
    },
    [view],
  );
  useEffect(() => {
    if (!camera || mode !== "cascade" || !cascadeFrame) return;
    const component =
      cascadeFrame.newly_failed[0] ?? (index === 0 ? "east-trunk" : null);
    if (component) focus(component);
  }, [camera, mode, index, cascadeFrame, focus]);
  function stage(n: number) {
    if (!view) return;
    setDemo(n);
    setPlaying(false);
    setCompare(false);
    setEvidence(false);
    setMode("observations");
    setIndex(0);
    setFitted(n >= 2);
    setLayer(n === 1 ? "residuals" : "observations");
    setPose(overview);
    if (n === 1) setCompare(true);
    if (n === 3) {
      setIndex(view.frames.findIndex((f) => f.split === "validation"));
      setLayer("residuals");
    }
    if (n === 4 || n === 5) {
      setMode("cascade");
      setLayer(n === 4 ? "flow" : "hazard");
      setIndex(
        n === 4
          ? 0
          : (view.cascade.find((f) => f.newly_failed.length)?.index ?? 0),
      );
      setCamera(true);
    }
    if (n === 6) {
      setLayer("uncertainty");
      const sensor = view.sensor_placement.recommendation[0];
      const r = view.frames[0].observations.find(
        (r) => r.observation.sensor_id === sensor,
      );
      if (r) focus(r.observation.component);
    }
    if (n === 7) {
      setMode("agent");
      setAgentCandidate(view.engineering_agent.selection ?? "");
      setLayer("pressure");
    }
    if (n >= 7) {
      setEvidence(true);
      setEvidenceNode(n === 7 ? "agent" : n === 8 ? "proof" : "limitations");
    }
  }
  async function run() {
    if (!view) return;
    setBusy(true);
    runController.current?.abort();
    const controller = new AbortController();
    runController.current = controller;
    try {
      const response = await fetch("/api/twin/evidence", {
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`Evidence HTTP ${response.status}`);
      const record = (await response.json()) as {
        science: { configuration: unknown; diameters_m: number[] };
      };
      const submitted = await fetch("/api/twin/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          raw: record.science.configuration,
          diameters: record.science.diameters_m,
          seed,
        }),
      });
      if (!submitted.ok) throw new Error(`Twin job HTTP ${submitted.status}`);
      const data = (await submitted.json()) as { job_id: string };
      setQuality("2d");
      setJob(data.job_id);
      setStatus("queued");
    } catch (e) {
      if (!controller.signal.aborted) setError(String(e));
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  if (!view || !state || !frame || !gpu || !cascadeFrame)
    return (
      <main className="twin-loading">
        <h1>DEVA / Digital-twin laboratory</h1>
        <p>{error || "Loading hash-validated synthetic computation…"}</p>
        <button onClick={onBack}>Hydraulic world</button>
      </main>
    );
  const annotation = measurements[selection ?? ""];
  const selectedPipe = view.problem.edges.findIndex((p) => p.id === selection);
  const hazard =
    mode === "cascade" && selection
      ? cascadeFrame.hazards[selection]
      : undefined;
  function world(estimated = false) {
    if (!view || !state || !frame || !gpu || !cascadeFrame) return null;
    const current = estimated ? frame.estimated : state,
      fields = estimated ? frame.estimated_gpu : gpu;
    return (
      <Suspense fallback={<p>Loading scientific renderer…</p>}>
        <NetworkCanvas
          problem={view.problem}
          candidate={current.candidate}
          result={current.result}
          scenario={current.scenario}
          layer={
            mode === "cascade" && layer === "hazard"
              ? "failure"
              : layer === "flow"
                ? "flow"
                : "physical"
          }
          selection={selection}
          select={focus}
          animate={!reduced}
          speed={50}
          pose={pose}
          setPose={setPose}
          onFrame={(ms) => {
            if (!adaptive.current) return;
            sampleTimes.current.push(ms);
            if (sampleTimes.current.length === 60) {
              adaptive.current = false;
              const samples = [...sampleTimes.current].sort((a, b) => a - b),
                p95 = samples[56];
              if (p95 > 80) {
                setQuality("2d");
                setRenderNotice(
                  `Measured p95 ${p95.toFixed(1)} ms; rendering changed to Scientific 2D. Scientific values are unchanged.`,
                );
              }
            }
          }}
          diagram={quality === "2d"}
          quality={quality === "high" ? "high" : "standard"}
          hydraulic={{
            ...current.hydraulic,
            showPressure: layer === "pressure",
          }}
          twin={{
            layer,
            measurements: estimated
              ? Object.fromEntries(
                  frame.observations.map((r) => [
                    r.observation.component,
                    {
                      value: r.observation.value_si,
                      prediction: r.prediction,
                      residual: r.residual,
                      sigma: r.observation.sigma_si,
                      unit: r.observation.canonical_unit,
                      standardized: r.standardized_residual,
                      parameterRatio:
                        r.parameter_variance === null
                          ? null
                          : Math.sqrt(r.parameter_variance) /
                            r.observation.sigma_si,
                    },
                  ]),
                )
              : measurements,
            hazards: mode === "cascade" ? cascadeFrame.hazards : {},
            gpu: fields,
          }}
        />
      </Suspense>
    );
  }
  const selectedGraph = view.provenance_graph.nodes.find(
    (n) => n.id === evidenceNode,
  );
  return (
    <div className="twin-shell">
      <header className="masthead">
        <div className="wordmark">
          DEVA<span>DIGITAL-TWIN LABORATORY</span>
        </div>
        <nav>
          <button onClick={onBack}>Hydraulic world</button>
          <button
            onClick={() => {
              setDemo(null);
              setEvidence(false);
            }}
          >
            Researcher
          </button>
          <button onClick={() => stage(0)}>Demonstration 2.0</button>
          <button
            aria-pressed={evidence}
            onClick={() => setEvidence(!evidence)}
          >
            Twin evidence
          </button>
        </nav>
        <span className="engine-indicator">
          SYNTHETIC · NOT FIELD CERTIFIED
        </span>
      </header>
      <div className="baseline-strip">
        <b>IMMUTABLE HISTORY</b>
        <span>38/200 · 44/200 → 13/200 at increased capacity cost</span>
        <a href="/api/twin/evidence" download>
          Engineering Evidence Package ↗
        </a>
      </div>
      <div className="twin-world-header">
        <div>
          <small>OBSERVE → CALIBRATE → ATTACK → EXPLAIN</small>
          <h1>Make the model answer to evidence.</h1>
        </div>
        <label>
          Rendering
          <select
            aria-label="Twin rendering"
            value={quality}
            onChange={(e) => {
              adaptive.current = false;
              setQuality(e.target.value as typeof quality);
            }}
          >
            <option value="2d">Scientific 2D</option>
            <option value="standard">Standard 3D</option>
            <option value="high">High-fidelity 3D</option>
          </select>
        </label>
      </div>
      {renderNotice && (
        <p role="status" className="twin-render-notice">
          {renderNotice}
        </p>
      )}
      {demo !== null && (
        <div className="twin-guidance">
          <b>
            {String(demo + 1).padStart(2, "0")} / {stages[demo]}
          </b>
          <span>
            {demo === 2
              ? view.calibration.status
              : demo === 5
                ? "Stored stochastic event; uncalibrated research hypothesis."
                : demo === 7
                  ? view.engineering_agent.stopping_reason
                  : "Actual stored benchmark states; no fabricated intermediate computation."}
          </span>
          <button disabled={demo === 0} onClick={() => stage(demo - 1)}>
            Previous
          </button>
          <button
            disabled={demo === stages.length - 1}
            onClick={() => stage(demo + 1)}
          >
            Next
          </button>
        </div>
      )}
      <section
        className={`twin-world ${compare && mode === "observations" ? "paired" : ""}`}
        aria-label="Digital twin engineering world"
      >
        <div className="twin-layer-rail" aria-label="Twin scientific layers">
          {layers.map((l) => (
            <button
              key={l}
              aria-pressed={layer === l}
              onClick={() => setLayer(l)}
            >
              {l}
            </button>
          ))}
        </div>
        <div className="twin-scene">
          <div className="twin-state-label">
            {mode === "failures"
              ? "SIMULATED / HELD-OUT FAILURE"
              : mode === "cascade"
                ? "SIMULATED / RESEARCH HAZARD"
                : mode === "agent"
                  ? "SIMULATED / AGENT CANDIDATE"
                  : mode === "counterexample"
                    ? "SIMULATED / FORMAL COUNTEREXAMPLE"
                    : fitted
                      ? "ESTIMATED / BENCHMARK CALIBRATION"
                      : "SIMULATED / INITIAL MODEL"}
            <small>
              {mode === "failures"
                ? `Independent scenario ${failedCase?.index}: ${String(failedCase?.scenario.id)} · not a temporal trajectory`
                : mode === "cascade"
                  ? `${cascadeFrame.time_seconds.toFixed(0)} s · ${cascadeFrame.events.length} events`
                  : mode === "agent"
                    ? `${agentState?.id} · synthetic cost ${agentState?.cost.toFixed(3)} · ${agentState?.rejection_reason ?? "Within requested budget"}`
                    : mode === "counterexample"
                      ? "Bounded graph counterexample → actual hydraulic evaluation"
                      : `${frame.split.toUpperCase()} · ${frame.timestamp}`}
            </small>
          </div>
          {world()}
        </div>
        {compare && mode === "observations" && (
          <div className="twin-scene">
            <div className="twin-state-label">
              ESTIMATED / SAME OBSERVATIONS
            </div>
            {world(true)}
          </div>
        )}
        <div className="twin-world-legend">
          {layer === "flow"
            ? "Signed solver velocity / pipe length drives tracer phase · 50× display speed · schematic geometry"
            : layer === "uncertainty"
              ? "Opacity encodes local parameter σ / sensor σ · excludes model error"
              : layer === "hazard"
                ? "Pre-interval probability from uncalibrated hazard law · not field rupture risk"
                : layer === "residuals"
                  ? "Δ = model − observation · colour saturates at |Δ| ≥ 3 sensor σ"
                  : "Blue markers: synthetic observations · values remain separate from estimates"}
        </div>
      </section>
      <div className="twin-controls">
        <label>
          Stored sequence
          <select
            aria-label="Twin sequence"
            value={mode}
            onChange={(e) => {
              setMode(e.target.value as typeof mode);
              setIndex(0);
              setPlaying(false);
            }}
          >
            <option value="observations">
              Observation / validation epochs
            </option>
            <option value="cascade">Computed research cascade</option>
            <option value="agent">Agent candidate mutations</option>
            <option value="failures" disabled={!view.failed_cases.length}>
              Frozen held-out failures
            </option>
            <option value="counterexample" disabled={!view.counterexample}>
              Formal counterexample simulation
            </option>
          </select>
        </label>
        {mode === "agent" && (
          <label>
            Agent candidate
            <select
              aria-label="Agent candidate"
              value={agentState?.id ?? ""}
              onChange={(e) => setAgentCandidate(e.target.value)}
            >
              {view.agent_candidates.map((c) => (
                <option key={c.id} value={c.id} disabled={!c.state}>
                  {c.id} · {c.cost.toFixed(2)} cost · {c.training_failures}/
                  {c.training_samples} training failures
                </option>
              ))}
            </select>
          </label>
        )}
        <button
          aria-pressed={fitted}
          disabled={mode !== "observations"}
          onClick={() => {
            setFitted(!fitted);
            setCompare(false);
          }}
        >
          {fitted ? "Estimated model" : "Initial model"}
        </button>
        <button
          aria-pressed={compare}
          disabled={mode !== "observations"}
          onClick={() => {
            setCompare(!compare);
            setFitted(false);
          }}
        >
          Compare residuals
        </button>
        <button onClick={() => setIndex(0)}>Restart</button>
        <button disabled={index === 0} onClick={() => setIndex((i) => i - 1)}>
          Step back
        </button>
        <button
          disabled={mode === "failures"}
          onClick={() => setPlaying(!playing)}
        >
          {playing ? "Pause" : "Play"}
        </button>
        <button
          disabled={index + 1 >= count}
          onClick={() => setIndex((i) => i + 1)}
        >
          Step forward
        </button>
        <label>
          Replay speed
          <select
            aria-label="Twin replay speed"
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
          >
            {[1, 5, 10, 50].map((s) => (
              <option key={s} value={s}>
                {s}×
              </option>
            ))}
          </select>
        </label>
        <label className="twin-scrub">
          {mode === "failures" ? "Independent failed case" : "Stored frame"}{" "}
          {index + 1}/{count}
          <input
            type="range"
            aria-label="Twin timeline"
            min={0}
            max={count - 1}
            value={index}
            onChange={(e) => {
              setPlaying(false);
              setIndex(Number(e.target.value));
            }}
          />
        </label>
        <button aria-pressed={camera} onClick={() => setCamera(!camera)}>
          Causal camera
        </button>
        <button
          onClick={() => {
            setPose(overview);
            setSelection(null);
          }}
        >
          Overview
        </button>
      </div>
      {mode === "cascade" && (
        <div className="twin-events" aria-label="Computed cascade events">
          {view.cascade_events.map((e) => (
            <button
              key={e.id}
              onClick={() => {
                setIndex(
                  view.cascade.findIndex(
                    (f) => f.time_seconds === e.simulation_time_seconds,
                  ),
                );
                focus(e.component);
              }}
            >
              {e.simulation_time_seconds} s · {e.component} · {e.event}
            </button>
          ))}
          <span>No interpolated physical states · interval-end failures</span>
        </div>
      )}
      <div className="twin-inspection">
        <section className="twin-component">
          <small>COMPONENT → EQUATION → EVIDENCE</small>
          <h2>{selection ?? "Inspect the engineering world"}</h2>
          <label>
            Inspect component
            <select
              aria-label="Twin inspect component"
              value={selection ?? ""}
              onChange={(e) => focus(e.target.value)}
            >
              <option value="">Choose component</option>
              {[
                ...view.problem.nodes,
                ...view.problem.edges.map((e) => e.id),
              ].map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </label>
          {selection ? (
            <>
              <p>
                Pressure head:{" "}
                {state.hydraulic.pressure_head_m[selection] === null
                  ? "UNKNOWN"
                  : (state.hydraulic.pressure_head_m[selection]?.toFixed(4) ??
                    "Pipe endpoints; inspect a junction")}{" "}
                m
              </p>
              {selectedPipe >= 0 && (
                <p>
                  Signed velocity:{" "}
                  {state.hydraulic.velocity_ms[selectedPipe].toFixed(5)} m/s ·
                  flow:{" "}
                  {(state.result.flow[selectedPipe] / 3600).toPrecision(5)} m³/s
                </p>
              )}
              {annotation && (
                <dl>
                  <dt>OBSERVED / SYNTHETIC</dt>
                  <dd>
                    {annotation.value.toPrecision(6)} ±{" "}
                    {annotation.sigma.toPrecision(3)} {annotation.unit} (sensor
                    σ)
                  </dd>
                  <dt>{fitted ? "ESTIMATED" : "SIMULATED"}</dt>
                  <dd>
                    {annotation.prediction.toPrecision(6)} {annotation.unit}
                  </dd>
                  <dt>Model − observation</dt>
                  <dd>
                    {annotation.residual.toPrecision(5)} {annotation.unit} ·{" "}
                    {annotation.standardized.toFixed(2)} σ
                  </dd>
                </dl>
              )}
              {hazard && (
                <p>
                  RESEARCH HAZARD: {hazard.rate_per_second.toExponential(4)} s⁻¹
                  · {pct(hazard.probability)} per 60 s interval
                </p>
              )}
              <details>
                <summary>Equations, units and assumptions</summary>
                <p>
                  Continuity: ΣQ_in − ΣQ_out = delivered demand (m³/s). Head
                  loss: ΔH = 8fLQ|Q| / (gπ²D⁵) (m). Pressure head p = H −
                  elevation (m). Service y = d√clip(p/p_full, 0, 1).
                </p>
                <p>
                  Hazard probability = 1 − exp(−λΔt), λ in s⁻¹; phenomenological
                  coefficients are uncalibrated. Static redistribution is not
                  pressure-wave propagation.
                </p>
              </details>
            </>
          ) : (
            <p>
              Select a node, pipe or observation marker. Synthetic measurements,
              model predictions and unknown quantities remain distinct.
            </p>
          )}
        </section>
        <section className="twin-calibration-summary">
          <small>WITHHELD OBSERVATIONS / {view.calibration.status}</small>
          <p className="twin-result">
            {view.calibration.metrics.validation.rmse_by_quantity.pressure.toFixed(
              4,
            )}{" "}
            <span>m pressure RMSE</span>
          </p>
          <p>
            Initial standardised error{" "}
            {view.calibration.metrics.validation.initial_weighted_rmse.toFixed(
              2,
            )}{" "}
            → fitted{" "}
            {view.calibration.metrics.validation.weighted_rmse.toFixed(2)} ·
            interval coverage{" "}
            {pct(view.calibration.metrics.validation.interval_coverage_95 ?? 0)}
          </p>
          <p>
            Local rank {view.calibration.fitted_identifiability.rank}/
            {view.calibration.fitted_identifiability.parameters} · not global
            uniqueness or field calibration
          </p>
          <details>
            <summary>Parameter search and incremental evidence</summary>
            {view.calibration.parameters.map((p) => (
              <p key={p.id}>
                {p.id}: {p.initial} → {p.estimate.toFixed(5)} ±{" "}
                {p.standard_error?.toFixed(5) ?? "UNKNOWN"} {p.unit} (local σ)
              </p>
            ))}
            <svg
              viewBox="0 0 600 100"
              role="img"
              aria-label="Stored calibration objective evaluations"
            >
              {view.calibration.searches.map((search, n) => {
                const values = search.history.map((h) =>
                  Math.log10(1 + h.weighted_sum_squares),
                );
                const max = Math.max(...values, 1);
                return (
                  <polyline
                    key={n}
                    fill="none"
                    stroke={["#66b8ac", "#d1aa62", "#88b8cc"][n % 3]}
                    points={values
                      .map(
                        (v, i) =>
                          `${(i / Math.max(1, values.length - 1)) * 590},${95 - (v / max) * 85}`,
                      )
                      .join(" ")}
                  />
                );
              })}
            </svg>
            <p>
              Log objective evaluations include finite-difference probes; not
              monotonic accepted iterations.
            </p>
            {view.incremental_calibration.map((p) => (
              <p key={p.timestamp}>
                {p.observation_count} observations · rank{" "}
                {p.identifiability.rank} · {p.status}
              </p>
            ))}
            <p>{view.calibration.uncertainty_scope}</p>
          </details>
        </section>
      </div>
      <details className="twin-research">
        <summary>Possible futures / research-hazard ensemble</summary>
        <svg
          viewBox="0 0 700 180"
          role="img"
          aria-label="Computed service ensemble"
        >
          {view.ensemble.trajectories.map((a, i) => (
            <polyline
              key={i}
              points={a
                .map((v, j) => `${(j / (a.length - 1)) * 690},${170 - v * 150}`)
                .join(" ")}
              fill="none"
              stroke="#88b8cc"
              opacity=".25"
            />
          ))}
          {Object.entries(view.ensemble.service_percentiles).map(([p, a]) => (
            <polyline
              key={p}
              points={a
                .map((v, j) => `${(j / (a.length - 1)) * 690},${170 - v * 150}`)
                .join(" ")}
              fill="none"
              stroke={p === "50" ? "#66b8ac" : "#d1aa62"}
            />
          ))}
        </svg>
        <p>
          5th / 50th / 95th service percentiles ·{" "}
          {view.ensemble.terminal_failures}/{view.ensemble.samples} terminal
          requirement failures · {view.ensemble.scope}
        </p>
      </details>
      <details className="twin-research">
        <summary>What should we measure next? / sensor placement</summary>
        <p>
          Given {view.next_observation.current_sensors.join(" + ")}, the next
          observation recommendation is{" "}
          {view.next_observation.value_of_information[0].sensor}; local
          information gain{" "}
          {view.next_observation.value_of_information[0].information_gain.toFixed(
            3,
          )}
          . This is a sensitivity-based proxy.
        </p>
        <p>{view.sensor_placement.scope}</p>
        {view.sensor_placement.layouts.map((layout) => (
          <button
            className="sensor-layout"
            key={layout.sensors.join(":")}
            onClick={() => {
              setMode("observations");
              setIndex(0);
              setLayer("uncertainty");
              const row = view.frames[0].observations.find(
                (r) => r.observation.sensor_id === layout.sensors[0],
              );
              if (row) focus(row.observation.component);
            }}
          >
            {layout.sensors.join(" + ")} · information{" "}
            {layout.information_score.toFixed(3)} · rank{" "}
            {layout.identifiability.rank}
          </button>
        ))}
        <p>
          Recommended: {view.sensor_placement.recommendation.join(" + ")}.
          Criterion: {view.sensor_placement.criterion}; not economic value.
        </p>
      </details>
      {evidence && (
        <section className="twin-evidence" aria-label="Twin evidence graph">
          <h2>Follow the scientific claim.</h2>
          <svg
            viewBox="0 0 1000 210"
            role="img"
            aria-label="Traceable evidence graph"
          >
            {view.provenance_graph.edges.map((e, i) => {
              const a = view.provenance_graph.nodes.findIndex(
                  (n) => n.id === e.source,
                ),
                b = view.provenance_graph.nodes.findIndex(
                  (n) => n.id === e.target,
                );
              return (
                <line
                  key={i}
                  x1={65 + (a % 4) * 260}
                  y1={45 + Math.floor(a / 4) * 100}
                  x2={65 + (b % 4) * 260}
                  y2={45 + Math.floor(b / 4) * 100}
                  stroke="#42555e"
                />
              );
            })}
            {view.provenance_graph.nodes.map((n, i) => (
              <g
                key={n.id}
                role="button"
                tabIndex={0}
                aria-label={`${n.kind}: ${n.id}`}
                onClick={() => setEvidenceNode(n.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") setEvidenceNode(n.id);
                }}
              >
                <circle
                  cx={65 + (i % 4) * 260}
                  cy={45 + Math.floor(i / 4) * 100}
                  r={evidenceNode === n.id ? 12 : 8}
                  fill={evidenceNode === n.id ? "#d1aa62" : "#66b8ac"}
                />
                <text
                  x={85 + (i % 4) * 260}
                  y={49 + Math.floor(i / 4) * 100}
                  fill="#c5d1d4"
                  fontSize="12"
                >
                  {n.kind}
                </text>
              </g>
            ))}
          </svg>
          {selectedGraph && (
            <p>
              {selectedGraph.id} → science/{selectedGraph.reference}
            </p>
          )}
          {view.claim_ledger
            .filter((c) => c.id === evidenceNode)
            .map((c) => (
              <div key={c.id}>
                <p>{c.claim}</p>
                <p>
                  {c.status} · {c.evidence}
                </p>
                <p>{c.limitations.join(" ")}</p>
                <code>{c.reproduction_route}</code>
              </div>
            ))}
          <details open={evidenceNode === "agent"}>
            <summary>
              Engineering Agent / plan, stopping and self-critique
            </summary>
            <p>{view.engineering_agent.stopping_reason}</p>
            <button
              disabled={!view.failed_cases.length}
              onClick={() => {
                setMode("failures");
                setIndex(0);
                setPlaying(false);
                setCompare(false);
                setLayer("pressure");
                focus("hospital");
              }}
            >
              Inspect frozen held-out failures
            </button>
            {view.unknown_cases.length > 0 && (
              <p>
                {view.unknown_cases.length} unknown solver states retained
                separately; see full evidence.
              </p>
            )}
            <pre>{JSON.stringify(view.engineering_agent.plan, null, 2)}</pre>
            {view.engineering_agent.research_narrative.map((n, i) => (
              <p key={i}>
                {n.text} <code>{n.evidence}</code>
              </p>
            ))}
            {view.engineering_agent.self_critique.map((c, i) => (
              <p key={i}>
                {c.issue} · {c.evidence}
              </p>
            ))}
          </details>
          <details open={evidenceNode === "proof"}>
            <summary>Proof Inspector / bounded Boolean topology</summary>
            {view.verification.objects.map((p, i) => (
              <details key={i}>
                <summary>
                  {p.status} · {p.requirement_id} · {p.result.toUpperCase()}
                </summary>
                <p>{p.property}</p>
                <p>{p.scope}</p>
                <p>{p.assumptions.join(" ")}</p>
                <p>{p.tool}</p>
                <pre>{p.smtlib}</pre>
                {p.proof && (
                  <details>
                    <summary>Z3 proof artifact / {p.proof_sha256}</summary>
                    <pre>{p.proof}</pre>
                  </details>
                )}
                {p.counterexample_closed && (
                  <p>
                    Counterexample: {p.counterexample_closed.join(" + ")}. Its
                    hydraulic simulation is retained in the agent evidence.
                    {view.counterexample && (
                      <button
                        onClick={() => {
                          setMode("counterexample");
                          setIndex(0);
                          setLayer("pressure");
                          setEvidence(false);
                          focus("hospital");
                        }}
                      >
                        Simulate stored counterexample
                      </button>
                    )}
                  </p>
                )}
                <p>{p.limitations.join(" ")}</p>
              </details>
            ))}
          </details>
          <details>
            <summary>Computed cascade causal graph</summary>
            {view.causal_graph.edges.map((e, i) => (
              <button
                key={i}
                onClick={() => {
                  const event = view.cascade_events.find(
                    (x) => x.id === e.source || x.id === e.target,
                  );
                  if (event) {
                    setMode("cascade");
                    setIndex(
                      view.cascade.findIndex(
                        (f) => f.time_seconds === event.simulation_time_seconds,
                      ),
                    );
                    focus(event.component);
                  }
                }}
              >
                {e.source} → {e.target} · {e.evidence}
              </button>
            ))}
          </details>
          <details open={evidenceNode === "limitations"}>
            <summary>Uncertainty and scientific limitations</summary>
            {view.limitations.map((l) => (
              <p key={l}>{l}</p>
            ))}
            <p>
              Real-world rupture prediction: UNMODELLED. Field calibration:
              INCOMPLETE. Hydraulic service: NUMERICALLY VALIDATED, not formally
              proven.
            </p>
            <pre>
              {JSON.stringify(
                {
                  seed: view.seed,
                  code: view.code,
                  experiment_id: view.experiment_id,
                  scientific_sha256: view.scientific_sha256,
                },
                null,
                2,
              )}
            </pre>
          </details>
        </section>
      )}
      <div className="twin-run">
        <label>
          New independent benchmark seed
          <input
            type="number"
            aria-label="Twin experiment seed"
            min={0}
            max={2 ** 32 - 22}
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
          />
        </label>
        <button disabled={busy || !!job} onClick={run}>
          Run synthetic investigation
        </button>
        {status && <span role="status">{status}</span>}
        {error && <p role="alert">{error}</p>}
      </div>
      <footer className="twin-footer">
        {view.experiment_id} · Synthetic digital twin · conditional research
        hazard · field rupture unmodelled · topology proof bounded
      </footer>
    </div>
  );
}
