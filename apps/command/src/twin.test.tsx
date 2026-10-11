import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { twinViewSchema } from "./twinContracts";
import TwinWorkspace from "./TwinWorkspace";
const root = resolve(process.cwd(), "../..");
const raw = JSON.parse(
  execFileSync(
    resolve(root, ".venv/bin/python"),
    [
      "-c",
      "import json;from deva.twin_view import project;print(json.dumps(project(json.load(open('artifacts/digital-twin-evidence.json')))))",
    ],
    { cwd: root, maxBuffer: 20_000_000 },
  ).toString(),
);
vi.mock("./NetworkCanvas", () => ({
  default: () => <div data-testid="twin-renderer">Scientific world</div>,
}));
beforeEach(() => {
  cleanup();
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
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
it("validates stored twin and rejects unearned calibration, formal badges and GPU values", () => {
  expect(twinViewSchema.parse(raw).calibration.status).toBe(
    "BENCHMARK CALIBRATED",
  );
  const bad = structuredClone(raw);
  bad.calibration.metrics.validation.weighted_rmse = 5;
  expect(() => twinViewSchema.parse(bad)).toThrow();
  const units = structuredClone(raw);
  units.frames[0].observations[0].observation.canonical_unit = "m3/s";
  expect(() => twinViewSchema.parse(units)).toThrow();
  const gpu = structuredClone(raw);
  gpu.frames[0].estimated_gpu[0].signed_velocity_ms += 1;
  expect(() => twinViewSchema.parse(gpu)).toThrow();
  const proof = structuredClone(raw);
  proof.verification.objects[0].proof = null;
  expect(() => twinViewSchema.parse(proof)).toThrow();
});
it("keeps observed and estimated values separate across residual comparison", async () => {
  render(<TwinWorkspace onBack={() => {}} />);
  await screen.findByText("Make the model answer to evidence.");
  const user = userEvent.setup();
  await user.selectOptions(
    screen.getByLabelText("Twin inspect component"),
    "hospital",
  );
  expect(screen.getByText("OBSERVED / SYNTHETIC")).toBeVisible();
  const row = raw.frames[0].observations.find(
    (r: { observation: { component: string } }) =>
      r.observation.component === "hospital",
  );
  expect(
    screen.getByText(
      `${row.observation.value_si.toPrecision(6)} ± ${row.observation.sigma_si.toPrecision(3)} m (sensor σ)`,
    ),
  ).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Compare residuals" }));
  expect(screen.getAllByTestId("twin-renderer")).toHaveLength(2);
  await user.click(screen.getByRole("button", { name: "Initial model" }));
  expect(
    screen.getByRole("button", { name: "Estimated model" }),
  ).toHaveAttribute("aria-pressed", "true");
});
it("replays stored cascade events and reveals real agent stopping and bounded proof", async () => {
  render(<TwinWorkspace onBack={() => {}} />);
  await screen.findByText("Make the model answer to evidence.");
  const user = userEvent.setup();
  await user.selectOptions(screen.getByLabelText("Twin sequence"), "cascade");
  const event = raw.cascade_events[0];
  await user.click(
    screen.getByRole("button", {
      name: `${event.simulation_time_seconds} s · ${event.component} · ${event.event}`,
    }),
  );
  expect(
    screen.getByText(
      `${event.simulation_time_seconds.toFixed(0)} s · 1 events`,
    ),
  ).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Twin evidence" }));
  expect(screen.getByLabelText("Traceable evidence graph")).toBeVisible();
  await user.click(
    screen.getByText("Engineering Agent / plan, stopping and self-critique"),
  );
  expect(screen.getByText(raw.engineering_agent.stopping_reason)).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Demonstration 2.0" }));
  expect(screen.getByText("01 / Observe synthetic truth")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Next" }));
  expect(screen.getByText("02 / Reveal model mismatch")).toBeVisible();
});
