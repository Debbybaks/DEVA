import type { Candidate } from "./contracts";
export default function EvolutionMap({
  candidates,
  selected,
  choose,
}: {
  candidates: Candidate[];
  selected: string;
  choose: (id: string) => void;
}) {
  const maxGeneration = Math.max(...candidates.map((c) => c.generation));
  const groups = Array.from({ length: maxGeneration + 1 }, (_, g) =>
    candidates.filter((c) => c.generation === g),
  );
  const positions = new Map(
    candidates.map((c) => [
      c.id,
      {
        x: 45 + c.generation * 235,
        y: 55 + groups[c.generation].indexOf(c) * 62,
      },
    ]),
  );
  const height = Math.max(150, ...groups.map((g) => g.length * 62 + 55));
  return (
    <div className="ancestry-scroll">
      <svg
        viewBox={`0 0 ${100 + maxGeneration * 235} ${height}`}
        role="group"
        aria-label="Design evolutionary ancestry graph"
        className="ancestry"
      >
        {groups.map((_, g) => (
          <text key={g} x={45 + g * 235} y="22" className="generation-label">
            GENERATION {g}
          </text>
        ))}
        {candidates.flatMap((c) =>
          c.parents.map((parent) => {
            const a = positions.get(parent),
              b = positions.get(c.id);
            return a && b ? (
              <path
                key={parent + c.id}
                d={`M${a.x + 18},${a.y} C${a.x + 100},${a.y} ${b.x - 100},${b.y} ${b.x - 18},${b.y}`}
                className={
                  c.disposition === "rejected" ? "dead-branch" : "branch"
                }
              />
            ) : null;
          }),
        )}
        {candidates.map((c) => {
          const p = positions.get(c.id)!;
          return (
            <g
              key={c.id}
              className={`candidate-point ${c.disposition} ${selected === c.id ? "chosen" : ""}`}
              tabIndex={0}
              role="button"
              aria-label={`Inspect ${c.id}, generation ${c.generation}, ${c.disposition}`}
              onClick={() => choose(c.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  choose(c.id);
                }
              }}
              transform={`translate(${p.x},${p.y})`}
            >
              <rect
                x="-16"
                y="-19"
                width="190"
                height="40"
                fill="transparent"
                pointerEvents="all"
              />
              <circle r="10" />
              <text x="17" y="-2">
                {c.id}
              </text>
              <text x="17" y="14" className="candidate-cost">
                {c.cost.toFixed(1)} ·{" "}
                {c.splits.training?.metrics?.failures ?? "—"} training failures
              </text>
              {c.disposition === "rejected" && (
                <path d="M-5,-5 L5,5 M-5,5 L5,-5" />
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
