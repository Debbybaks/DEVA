import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { reducer, initial } from "./state";
import { viewSchema } from "./contracts";
import App from "./App";
const root = resolve(process.cwd(), "../..");
const projection = JSON.parse(
  execFileSync(
    resolve(root, ".venv/bin/python"),
    [
      "-c",
      "import json;from deva.view import project;print(json.dumps(project(json.load(open('artifacts/evolution-evidence.json')))))",
    ],
    { cwd: root, maxBuffer: 20_000_000 },
  ).toString(),
);
vi.mock("./NetworkCanvas", () => ({
  default: () => <div data-testid="scientific-canvas">Scientific renderer</div>,
}));
beforeEach(() => {
  cleanup();
  vi.stubGlobal("matchMedia", () => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify(projection), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    ),
  );
});
describe("Typed scientific contract and command state", () => {
  it("parses Python projection and rejects invented verification", () => {
    expect(viewSchema.parse(projection).candidates.length).toBe(26);
    const copy = structuredClone(projection);
    copy.candidates[0].verification.level = "FORMALLY VERIFIED";
    expect(() => viewSchema.parse(copy)).toThrow();
  });
  it("resets scenario index on split changes and preserves layer selection", () => {
    let s = reducer(initial, { type: "scenario", index: 40 });
    s = reducer(s, { type: "layer", layer: "risk" });
    s = reducer(s, { type: "split", split: "validation" });
    expect(s.index).toBe(0);
    expect(s.layer).toBe("risk");
  });
  it("keeps baseline visible, switches layers and inspects equations", async () => {
    render(<App />);
    await screen.findByText("Try to break it.");
    expect(screen.getByText("38 / 200 held-out failures")).toBeInTheDocument();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "risk" }));
    expect(screen.getByRole("button", { name: "risk" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await user.selectOptions(
      screen.getByLabelText("Inspect component"),
      "west-trunk",
    );
    expect(screen.getByText("0 ≤ fₑ ≤ aₑ cₑ")).toBeInTheDocument();
    expect(
      screen.getByText("Untested in this capacity model"),
    ).toBeInTheDocument();
  });
  it("opens paired views, explores rejected ancestry and traces evidence", async () => {
    render(<App />);
    await screen.findByText("Try to break it.");
    const user = userEvent.setup();
    await user.selectOptions(
      screen.getByLabelText("Comparison candidate"),
      "g0-c001",
    );
    await waitFor(() =>
      expect(screen.getAllByTestId("scientific-canvas")).toHaveLength(2),
    );
    await user.click(screen.getByRole("button", { name: "evolution" }));
    await user.click(screen.getByRole("button", { name: /Inspect g0-c000/ }));
    expect(screen.getByLabelText("Selected candidate")).toHaveValue("g0-c000");
    await user.click(screen.getByRole("button", { name: "evidence" }));
    await user.click(screen.getByText("Trace a conclusion backwards"));
    await user.click(
      screen.getByRole("button", { name: "Trace supporting evidence" }),
    );
    expect(screen.getByText("requirement:service")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Full Engineering Evidence Package/ }),
    ).toHaveAttribute("href", "/api/evidence/evolution");
  });
  it("shows engine contract errors instead of substitute scientific values", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response('{"fake":true}', { status: 200 })),
    );
    render(<App />);
    await screen.findByRole("button", { name: "Reconnect to engine" });
    expect(screen.queryByTestId("scientific-canvas")).not.toBeInTheDocument();
  });
});
