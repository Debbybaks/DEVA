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
