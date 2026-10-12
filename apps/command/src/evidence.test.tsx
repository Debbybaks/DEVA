import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import EvidenceSummary from "./EvidenceSummary";
import { SearchAblation } from "./WorldEvidence";
afterEach(cleanup);
it("presents scientific fields without mounting raw evidence until explicitly opened", async () => {
  const value = {
    failure_rate: 0.15,
    cost: 492.0046121193669,
    solver_calls: 172,
    assumptions: { calibration: "Synthetic only" },
    smtlib: "(assert debug)",
  };
  const { container } = render(<EvidenceSummary value={value} />);
  expect(screen.getByText("Design cost (units)")).toBeVisible();
  expect(screen.getByText("492.0046121193669")).toBeVisible();
  expect(container.querySelector("pre")).toBeNull();
  expect(screen.queryByText("(assert debug)")).toBeNull();
  await userEvent.click(screen.getByText("View raw evidence"));
  expect(container.querySelector("pre")?.textContent).toBe(
    JSON.stringify(value, null, 2),
  );
});
it("keeps all 30 ablation trials and negative results in readable cards", () => {
  const value = JSON.parse(
    readFileSync("../../artifacts/phase5-worlds-view.json", "utf8"),
  ).science.ablation;
  const { container } = render(
    <SearchAblation value={value} allowRaw={false} />,
  );
  expect(container.querySelectorAll(".decision-card")).toHaveLength(30);
  expect(container.querySelector("pre")).toBeNull();
  expect(screen.queryByText("View raw evidence")).toBeNull();
});
it("links README to the canonical live application and repository root", () => {
  const readme = readFileSync("../../README.md", "utf8");
  expect(readme).toContain(
    "**Live DEVA:** [https://deva-vert.vercel.app](https://deva-vert.vercel.app)",
  );
  expect(readme).toContain(
    "[Debbybaks/DEVA](https://github.com/Debbybaks/DEVA)",
  );
  expect(readme).not.toContain("/blob/main/README.md");
});
