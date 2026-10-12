import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import WorldsWorkspace from "./WorldsWorkspace";
import { worldSchema } from "./worldContracts";
const raw = JSON.parse(
  readFileSync(
    resolve(process.cwd(), "../../artifacts/phase5-worlds-view.json"),
    "utf8",
  ),
);
beforeEach(() => {
  cleanup();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url) => {
      const body = structuredClone(raw);
      if (String(url).includes("/experiment/")) {
        body.science.experiments = body.science.experiments.filter(
          (e: { id: string }) => String(url).endsWith(e.id),
        );
      } else {
        for (const e of body.science.experiments)
          for (const c of e.candidates) c.frames = [];
      }
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );
});
it("validates domain isolation and chronological dimensions", () => {
  const parsed = worldSchema.parse(raw);
  expect(parsed.science.experiments.length).toBe(30);
  const bad = structuredClone(raw);
  bad.science.experiments[0].descriptor.id = "microgrid";
  expect(() => worldSchema.parse(bad)).toThrow();
  const dimensions = structuredClone(raw),
    e = dimensions.science.experiments.find(
      (e: { domain: string }) => e.domain === "microgrid",
    );
  e.candidates[0].frames[0].outcome.state.energy_J.pop();
  expect(() => worldSchema.parse(dimensions)).toThrow();
});
it("opens different physical worlds and preserves local evidence", async () => {
  render(<WorldsWorkspace onBack={() => {}} />);
  await screen.findByText("Different physics. One investigation engine.");
  const user = userEvent.setup();
  expect(
    await screen.findByRole("img", {
      name: "Chronological microgrid power and stored energy",
    }),
  ).toBeVisible();
  await user.click(
    screen.getByRole("button", { name: /01 \/ WATER RESILIENCE/ }),
  );
  await screen.findByRole("img", {
    name: "Water network signed flow and pressure",
  });
  await user.click(screen.getByRole("button", { name: "Evidence lens" }));
  expect(screen.getByText("Evidence remains local")).toBeVisible();
  expect(screen.getByText(/4\/40 hospital failures/)).toBeVisible();
});
