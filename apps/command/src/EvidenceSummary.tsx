import { useState } from "react";
import "./evidence.css";

const labels: Record<string, string> = {
  verification_level: "Evidence level",
  model_version: "Model",
  status: "Verification status",
  failure_rate: "Failure rate",
  mean_failure_rate: "Mean failure rate",
  solver_calls: "Physical solver calls",
  cost: "Design cost (units)",
  scientific_sha256: "Scientific SHA256",
  stop: "Stopping reason",
  unvalidated: "Unvalidated scope",
  smtlib: "Solver input",
  proof: "Machine-readable proof",
};
function label(key: string) {
  return (
    labels[key] ??
    key.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase())
  );
}

export function EvidenceFields({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span>Not available</span>;
  if (typeof value === "boolean") return <span>{value ? "Yes" : "No"}</span>;
  if (typeof value !== "object") return <span>{String(value)}</span>;
  if (Array.isArray(value))
    return value.length ? (
      <ul className="evidence-list">
        {value.map((item, i) => (
          <li key={i}>
            <EvidenceFields value={item} />
          </li>
        ))}
      </ul>
    ) : (
      <span>No records</span>
    );
  return (
    <dl className="evidence-fields">
      {Object.entries(value).map(([key, item]) => (
        <div key={key}>
          <dt>{label(key)}</dt>
          <dd>
            {["smtlib", "proof"].includes(key) ? (
              "Available in raw evidence"
            ) : (
              <EvidenceFields value={item} />
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function RawEvidence({
  value,
  label: title = "View raw evidence",
}: {
  value: unknown;
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <details
      className="raw-evidence"
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary>{title}</summary>
      {open && (
        <pre>
          {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
        </pre>
      )}
    </details>
  );
}

export default function EvidenceSummary({
  value,
  allowRaw = true,
}: {
  value: unknown;
  allowRaw?: boolean;
}) {
  return (
    <div className="evidence-summary">
      <EvidenceFields value={value} />
      {allowRaw && <RawEvidence value={value} />}
    </div>
  );
}
