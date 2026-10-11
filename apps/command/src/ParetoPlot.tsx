import type { View } from "./contracts";
export default function ParetoPlot({
  view,
  selected,
  choose,
}: {
  view: View;
  selected: string;
  choose: (id: string) => void;
}) {
  const points = view.candidates.filter((c) => c.splits.training?.metrics);
  const maxCost = Math.max(...points.map((c) => c.cost), 1);
  return (
    <svg
      viewBox="0 0 480 175"
      className="pareto"
      role="group"
      aria-label="Empirical cost versus training failure rate Pareto comparison"
    >
      <path d="M35,10 V140 H460" />
      <text x="35" y="163">
        CAPACITY COST →
      </text>
      <text x="42" y="20">
        TRAINING FAILURE RATE
      </text>
      {[0, 0.25, 0.5, 0.75, 1].map((t) => (
        <g key={t}>
          <line x1="35" x2="460" y1={140 - t * 110} y2={140 - t * 110} />
          <text x="3" y={144 - t * 110}>
            {Math.round(t * 100)}%
          </text>
        </g>
      ))}
      {points.map((c) => (
        <g
          key={c.id}
          role="button"
          tabIndex={0}
          aria-label={`Pareto candidate ${c.id}`}
          onClick={() => choose(c.id)}
          onKeyDown={(e) => {
            if (e.key === "Enter") choose(c.id);
          }}
        >
          <circle
            cx={35 + (c.cost / maxCost) * 410}
            cy={140 - c.splits.training.metrics!.failure_rate * 110}
            r={selected === c.id ? 6 : 4}
            className={
              view.pareto_frontier.includes(c.id)
                ? "frontier-dot"
                : "dominated-dot"
            }
          />
          <title>
            {c.id}: cost {c.cost.toFixed(1)}, training failure{" "}
            {(c.splits.training.metrics!.failure_rate * 100).toFixed(1)}%
          </title>
        </g>
      ))}
    </svg>
  );
}
