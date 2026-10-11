import { test, expect } from "@playwright/test";

test("synthetic observations → held-out calibration → emergent cascade → bounded proof", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const view = await (await request.get("/api/twin/view")).json();
  await page.goto("/?model=twin");
  await expect(
    page.getByText("Make the model answer to evidence."),
  ).toBeVisible();
  await page.getByLabel("Twin rendering").selectOption("2d");
  await page.getByLabel("Twin inspect component").selectOption("hospital");
  const row = view.frames[0].observations.find(
    (r: { observation: { component: string } }) =>
      r.observation.component === "hospital",
  );
  await expect(
    page.getByText(
      `${row.observation.value_si.toPrecision(6)} ± ${row.observation.sigma_si.toPrecision(3)} m (sensor σ)`,
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Compare residuals" }).click();
  await expect(page.getByText("ESTIMATED / SAME OBSERVATIONS")).toBeVisible();
  await page.getByRole("button", { name: "residuals", exact: true }).click();
  await expect(
    page.getByText("Δ = model − observation", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Compare residuals" }).click();
  await page
    .getByRole("button", { name: "Initial model", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Estimated model", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByLabel("Twin timeline").fill("5");
  await expect(page.getByText("VALIDATION ·", { exact: false })).toBeVisible();
  await page.getByLabel("Twin sequence").selectOption("cascade");
  const event = view.cascade_events[0];
  await page
    .getByRole("button", {
      name: `${event.simulation_time_seconds} s · ${event.component} · ${event.event}`,
    })
    .click();
  await expect(
    page.getByText(`${event.simulation_time_seconds.toFixed(0)} s · 1 events`),
  ).toBeVisible();
  await page.getByRole("button", { name: "Twin evidence" }).click();
  await page
    .getByText("Engineering Agent / plan, stopping and self-critique")
    .click();
  await expect(
    page.getByText(view.engineering_agent.stopping_reason),
  ).toBeVisible();
  await page.getByText("Proof Inspector / bounded Boolean topology").click();
  await expect(
    page.getByText("FORMALLY VERIFIED · R-TOPOLOGY-BOUNDED · UNSAT", {
      exact: true,
    }),
  ).toBeVisible();
  await page.getByLabel("Twin sequence").selectOption("counterexample");
  await page.getByLabel("Twin inspect component").selectOption("hospital");
  await expect(
    page.getByText("Pressure head: UNKNOWN m", { exact: true }),
  ).toBeVisible();
  await expect(
    page.locator(".twin-state-label").first(),
  ).toContainText("SIMULATED / FORMAL COUNTEREXAMPLE");
  await page.getByLabel("Twin sequence").selectOption("agent");
  await page.getByLabel("Agent candidate").selectOption("agent:c000");
  await expect(
    page.locator(".twin-state-label").first(),
  ).toContainText("SIMULATED / AGENT CANDIDATE");
  await page.getByRole("button", { name: "Demonstration 2.0" }).click();
  for (let n = 0; n < 9; n++)
    await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(
    page.getByText("10 / Expose remaining uncertainty"),
  ).toBeVisible();
  await expect(
    page.getByText("Real-world rupture prediction: UNMODELLED.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(391);
  expect(errors).toEqual([]);
});

test("scientific GLSL particle world and a new background twin investigation", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/?model=twin");
  await expect(
    page.getByText("Make the model answer to evidence."),
  ).toBeVisible();
  await page.getByLabel("Twin rendering").selectOption("high");
  await page.getByRole("button", { name: "flow", exact: true }).click();
  await expect(page.locator("canvas")).toHaveCount(1);
  await expect(
    page.getByText("Signed solver velocity / pipe length drives tracer phase", {
      exact: false,
    }),
  ).toBeVisible();
  await page.waitForTimeout(500);
  await page.getByLabel("Twin rendering").selectOption("2d");
  await page
    .getByLabel("Twin experiment seed")
    .fill(String(20263000 + process.pid));
  const submitted = page.waitForResponse(
    (r) => r.url().endsWith("/api/twin/jobs") && r.status() === 202,
  );
  await page
    .getByRole("button", { name: "Run synthetic investigation" })
    .click();
  const job = (await (await submitted).json()).job_id;
  await expect(
    page.getByRole("button", { name: "Run synthetic investigation" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "uncertainty", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "uncertainty", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect
    .poll(
      async () => (await (await request.get("/api/jobs/" + job)).json()).status,
      { timeout: 45000 },
    )
    .toBe("completed");
  await expect(
    page.getByRole("button", { name: "Run synthetic investigation" }),
  ).toBeEnabled();
  const evidence = await (
    await request.get("/api/jobs/" + job + "/evidence")
  ).json();
  const latest = await (await request.get("/api/jobs/" + job + "/view")).json();
  await expect(
    page.getByText(latest.experiment_id, { exact: false }),
  ).toBeVisible();
  expect(evidence.science.dataset.label).toBe(
    "SYNTHETIC HIDDEN-PARAMETER BENCHMARK",
  );
  expect(evidence.science.calibration.rows.validation.length).toBe(16);
  expect(errors).toEqual([]);
});
