import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { hydraulicViewSchema } from "./hydraulicContracts";
import HydraulicWorkspace from "./HydraulicWorkspace";
const root = resolve(process.cwd(), "../..");
const raw = JSON.parse(
  execFileSync(
    resolve(root, ".venv/bin/python"),
    [
      "-c",
      "import json;from deva.hydraulic_view import project;print(json.dumps(project(json.load(open('artifacts/hydraulic-evidence.json')))))",
    ],
    { cwd: root, maxBuffer: 20_000_000 },
  ).toString(),
);
vi.mock("./NetworkCanvas", () => ({
  default: () => <div data-testid="hydraulic-renderer">Computed world</div>,
}));
beforeEach(() => {
  cleanup();
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify(raw), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    ),
  );
});
it("validates real Python hydraulic projection and rejects unsupported formal/shape claims", () => {
  expect(hydraulicViewSchema.parse(raw).verification_objects[0].status).toBe(
    "FORMALLY VERIFIED",
  );
  const bad = structuredClone(raw);
  bad.verification_objects[0].proof = null;
  expect(() => hydraulicViewSchema.parse(bad)).toThrow();
  const dimensions = structuredClone(raw);
  dimensions.candidates[0].states.heldout[0].result.flow.pop();
  expect(() => hydraulicViewSchema.parse(dimensions)).toThrow();
});
it("inspects exact pressure, replays computed tank states and preserves fallback values", async () => {
  render(<HydraulicWorkspace onBack={() => {}} />);
  await screen.findByText("Design against pressure. Trust the evidence.");
  const user = userEvent.setup();
  await user.selectOptions(screen.getByLabelText("Visual performance"), "2d");
  await user.selectOptions(
    screen.getByLabelText("Hydraulic inspect component"),
    "hospital",
  );
  const observed = raw.candidates.find(
    (c: { id: string }) => c.id === raw.recommendation,
  ).states.heldout[0].hydraulic.pressure_head_m.hospital;
  expect(
    screen.getByText(`Pressure head: ${observed.toFixed(6)} m`),
  ).toBeInTheDocument();
  await user.selectOptions(
    screen.getByLabelText("Hydraulic sequence"),
    "storage",
  );
  await user.click(screen.getByRole("button", { name: "Step forward" }));
  expect(screen.getByText(/300.0 s ·/)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Hydraulic evidence" }));
  expect(
    screen.getByText(
      "Scientific claim ledger · property-specific proof objects",
    ),
  ).toBeInTheDocument();
  expect(
    screen.getAllByText(
      "Only bounded Boolean connectivity; no promotion of hydraulic service or entire design",
    ),
  ).toHaveLength(2);
});
it("links matched comparison and real-data demonstration without inventing a simulation", async () => {
  render(<HydraulicWorkspace onBack={() => {}} />);
  await screen.findByText("Design against pressure. Trust the evidence.");
  const user = userEvent.setup();
  await user.selectOptions(
    screen.getByLabelText("Hydraulic comparison"),
    "h0-c000",
  );
  expect(screen.getAllByTestId("hydraulic-renderer")).toHaveLength(2);
  await user.click(screen.getByRole("button", { name: "Demonstration" }));
  expect(
    screen.getByText(/1 \/ 9 · Engineering objective/),
  ).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Next evidence" }));
  expect(screen.getByLabelText("Hydraulic candidate")).toHaveValue("h0-c000");
});
