import { test, expect } from "@playwright/test";

for (const viewport of [
  { width: 1600, height: 1000 },
  { width: 390, height: 844 },
]) {
  test(`root opens visual worlds with and without tracking at ${viewport.width}px`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    for (const path of ["/", "/?utm_source=chatgpt.com"]) {
      await page.goto(path);
      await expect(
        page.getByRole("heading", {
          name: "Different physics. One investigation engine.",
        }),
      ).toBeVisible();
      await expect(
        page.getByRole("img", {
          name: "Chronological microgrid power and stored energy",
        }),
      ).toBeVisible();
      await expect(
        page.getByRole("navigation", { name: "Engineering worlds" }),
      ).toBeVisible();
      await expect(page.locator("pre:visible")).toHaveCount(0);
      await expect
        .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
        .toBeLessThanOrEqual(viewport.width + 1);
      await expect(
        page.getByRole("link", { name: "Research archive" }),
      ).toHaveAttribute("href", "/archive");
    }
  });
}
