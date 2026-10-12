import { test, expect } from "@playwright/test";
for (const width of [1600, 390]) {
  test(`public modes preserve readable evidence and explicit inspection at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
    await page.goto("/");
    await expect(
      page.getByRole("img", {
        name: "Chronological microgrid power and stored energy",
      }),
    ).toBeVisible();
    const noRaw = async () => {
      await expect(page.locator("pre:visible")).toHaveCount(0);
      await expect(page.locator("body")).not.toContainText(
        /"(?:failure_rate|solver_calls|experiment|cost)"\s*:/,
      );
      await expect
        .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
        .toBeLessThanOrEqual(width + 1);
    };
    for (const mode of ["judge", "portfolio", "researcher"]) {
      await page.getByLabel("World audience").selectOption(mode);
      await page
        .getByRole("button", { name: "Physical world", exact: true })
        .click();
      await page
        .getByText("Search ablation / preserve negative results", {
          exact: true,
        })
        .click();
      await expect(page.getByText(/random search was stronger/)).toBeVisible();
      await expect(page.locator(".ablation-card")).toHaveCount(10);
      await page
        .getByText("3 recorded trials", { exact: true })
        .first()
        .click();
      await noRaw();
      await page
        .getByText("Search ablation / preserve negative results", {
          exact: true,
        })
        .click();
    }
    await page.getByRole("button", { name: /01 \/ WATER RESILIENCE/ }).click();
    await expect(
      page.getByRole("img", { name: "Water network signed flow and pressure" }),
    ).toBeVisible();
    await noRaw();
    if (width === 390) {
      const cards = await page
        .locator(".world-lineage button")
        .evaluateAll((nodes) =>
          nodes.map((n) => ({
            width: n.getBoundingClientRect().width,
            right: n.getBoundingClientRect().right,
            left: n.getBoundingClientRect().left,
          })),
        );
      expect(
        cards.every((c) => c.width > 200 && c.left >= 0 && c.right <= 390),
      ).toBeTruthy();
    }
    await page
      .getByRole("button", { name: "Uncertainty lens", exact: true })
      .click();
    await noRaw();
    await page
      .getByRole("button", { name: "Evidence lens", exact: true })
      .click();
    await page
      .getByText("Claim ledger / domain-scoped", { exact: true })
      .click();
    await noRaw();
    await expect(
      page.getByText("Evidence level", { exact: true }).first(),
    ).toBeVisible();
    await page.getByText("View raw evidence", { exact: true }).first().click();
    await expect(page.locator("pre:visible")).toHaveCount(1);
    await expect(page.locator("pre:visible")).toContainText("model_version");
    await page.getByLabel("World audience").selectOption("judge");
    await noRaw();
    await page
      .getByRole("button", { name: "Demonstration 3.0", exact: true })
      .click();
    for (let n = 0; n < 10; n++) {
      await noRaw();
      if (n < 9) await page.getByRole("button", { name: "Next act" }).click();
    }
    await expect(
      page.getByRole("link", { name: "GitHub / Source code" }),
    ).toHaveAttribute("href", "https://github.com/Debbybaks/DEVA");
    await page.getByRole("link", { name: "Research archive" }).click();
    await expect(page).toHaveURL(/\/archive$/);
    await expect(page.getByText("Try to break it.")).toBeVisible();
    await expect(
      page.getByRole("link", { name: "GitHub / Source code" }),
    ).toHaveAttribute("href", "https://github.com/Debbybaks/DEVA");
  });
}
