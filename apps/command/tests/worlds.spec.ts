import { test, expect } from "@playwright/test";
test("cross-domain stored worlds → scoped evidence → reproducible demonstration", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/?model=worlds");
  await expect(
    page.getByText("Different physics. One investigation engine."),
  ).toBeVisible();
  await expect(
    page.getByRole("img", {
      name: "Chronological microgrid power and stored energy",
    }),
  ).toBeVisible();
  await page.getByLabel("Microgrid interval").fill("3");
  await page.getByRole("button", { name: /01 \/ WATER RESILIENCE/ }).click();
  await expect(
    page.getByRole("img", { name: "Water network signed flow and pressure" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Evidence lens" }).click();
  await expect(page.getByText("Evidence remains local")).toBeVisible();
  await page.getByRole("button", { name: "Demonstration 3.0" }).click();
  for (let n = 0; n < 8; n++)
    await page.getByRole("button", { name: "Next act" }).click();
  await expect(
    page.getByText("ACT 9 / A second physical domain"),
  ).toBeVisible();
  await expect(
    page.getByRole("img", {
      name: "Chronological microgrid power and stored energy",
    }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(391);
  expect(errors).toEqual([]);
});

test("registered domain investigation streams scientific actions and opens real worker output", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/?model=worlds");
  await expect(
    page.getByRole("img", {
      name: "Chronological microgrid power and stored energy",
    }),
  ).toBeVisible();
  await page
    .getByText("Run a registered scientific investigation", { exact: true })
    .click();
  await page.getByLabel("Research seed").fill(String(20261230 + process.pid));
  await page.getByLabel("Candidate budget").fill("3");
  await page.getByLabel("Generation budget").fill("1");
  await page.getByLabel("Training samples").fill("2");
  await page.getByLabel("Validation samples").fill("2");
  await page.getByLabel("Held-out samples").fill("4");
  const submitted = page.waitForResponse(
    (r) => r.url().endsWith("/api/domain/jobs") && r.status() === 202,
  );
  await page
    .getByRole("button", { name: "Run domain investigation", exact: true })
    .click();
  const job = (await (await submitted).json()).job_id;
  await expect
    .poll(
      async () => (await (await request.get("/api/jobs/" + job)).json()).status,
      { timeout: 45000 },
    )
    .toBe("completed");
  const evidence = await (
    await request.get("/api/jobs/" + job + "/evidence")
  ).json();
  expect(evidence.science.domain.id).toBe("microgrid");
  expect(evidence.science.heldout.samples).toBe(4);
  await expect(
    page.getByText("Selected investigation: " + evidence.experiment_id, {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Run domain investigation", exact: true }),
  ).toBeEnabled();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(391);
  expect(errors).toEqual([]);
});
