import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=[
                "--no-sandbox",
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ],
        )
        page = await browser.new_page(viewport=dict(width=1600, height=1100))
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto("http://127.0.0.1:5173/?model=hydraulic")
        await page.get_by_text("Design against pressure. Trust the evidence.").wait_for(
            timeout=30000
        )
        await page.locator("canvas").wait_for()
        await page.wait_for_timeout(1200)
        await page.screenshot(path="artifacts/hydraulic-world.png", full_page=True)
        await page.locator("summary").filter(has_text="Hydraulic Failure Lab").click()
        await page.get_by_label("Hydraulic outage").select_option("east-trunk")
        await page.get_by_label("Hydraulic demand factor").fill("1.6")
        await page.get_by_label("Source head change").fill("-10")
        await page.get_by_role("button", name="Solve hydraulic disturbance").click()
        await page.get_by_role("link", name="Download hydraulic intervention").wait_for(
            timeout=30000
        )
        await page.wait_for_timeout(1200)
        await page.screenshot(path="artifacts/hydraulic-failure.png", full_page=True)
        print("Actual hydraulic captures; page errors:", errors)
        if errors:
            raise RuntimeError("Browser error during evidence capture")
        await browser.close()


asyncio.run(main())
