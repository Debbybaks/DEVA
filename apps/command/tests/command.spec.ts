import { test, expect } from "@playwright/test";
import { resolve } from "node:path";

test("Python → API → WebGL command environment → Failure Lab → evidence", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByText("Try to break it.")).toBeVisible();
  await expect(page.getByText("38 / 200 held-out failures")).toBeVisible();
  await expect(page.locator("canvas")).toHaveCount(1);
  await page.getByRole("button", { name: "capacity", exact: true }).click();
  await page.getByLabel("Inspect component").selectOption("west-trunk");
  await expect(page.getByText("0 ≤ fₑ ≤ aₑ cₑ")).toBeVisible();
  await page.getByLabel("Selected candidate").selectOption("g0-c001");
  await page.getByLabel("Comparison candidate").selectOption("g2-c012");
  await expect(page.locator("canvas")).toHaveCount(2);
  await page.getByLabel("Primary pipe outage").selectOption("west-trunk");
  await page.getByLabel("Demand multiplier").focus();
  await page.getByLabel("Demand multiplier").press("ArrowRight");
  await page.getByLabel("Demand multiplier").press("ArrowRight");
  await page.getByLabel("Demand multiplier").press("ArrowRight");
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/api/lab") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Apply disturbance" }).click();
  const evidence = await (await response).json();
  expect(
    evidence.result.independent_audit.independent_max_residual,
  ).toBeLessThan(1e-7);
  await expect(
    page.getByRole("button", { name: "Return to recorded scenario" }),
  ).toBeVisible();
  await expect(page.getByText(/COMMON SERVICE · FAIL/).first()).toBeVisible();
  await page.getByRole("button", { name: "evolution", exact: true }).click();
  await page.getByRole("button", { name: /Inspect g0-c000/ }).click();
  await expect(page.getByLabel("Selected candidate")).toHaveValue("g0-c000");
  await page.getByRole("button", { name: "evidence", exact: true }).click();
  await page.getByText("Trace a conclusion backwards").click();
  await page.getByRole("button", { name: "Trace supporting evidence" }).click();
  await expect(page.getByText("requirement:service")).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Full Engineering Evidence Package/ }),
  ).toHaveAttribute("href", "/api/evidence/evolution");
  expect(errors).toEqual([]);
});

test("preserved baseline and mobile layout remain inspectable", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Try to break it.")).toBeVisible();
  await page.getByLabel("Evidence dataset").selectOption("baseline");
  await expect(page.getByLabel("Selected candidate")).toHaveValue("robust-lp");
  await expect(
    page.getByText("/ 200 held-out failures", { exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText("Try to break it.")).toBeVisible();
  const sizes = await page.evaluate(() => ({
    viewport: innerWidth,
    width: document.documentElement.scrollWidth,
  }));
  expect(sizes.width).toBeLessThanOrEqual(sizes.viewport + 1);
  await page.getByLabel("Inspect component").selectOption("hospital");
  await expect(page.getByText("Bf + q − y = 0")).toBeVisible();
});

test("background evolution streams actual progress and loads computed results", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Try to break it.")).toBeVisible();
  await page.getByLabel("Experiment seed").fill(String(20261014 + process.pid));
  await page.getByLabel("Generation budget").fill("1");
  await page.getByRole("button", { name: "Run design evolution" }).click();
  await expect(
    page.getByRole("button", { name: "Evolution in progress" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "risk", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "risk", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Evidence dataset")).toHaveValue("job", {
    timeout: 60000,
  });
  await page.getByRole("button", { name: "evidence", exact: true }).click();
  await expect(
    page.getByText(/training=\d+ · validation=\d+ · heldout=\d+/),
  ).toBeVisible();
});
