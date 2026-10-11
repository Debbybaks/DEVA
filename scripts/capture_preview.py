import asyncio
from pathlib import Path
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
        page = await browser.new_page(
            viewport={"width": 1600, "height": 1000}, device_scale_factor=1
        )
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto("http://127.0.0.1:5173", wait_until="domcontentloaded")
        await page.get_by_text("Try to break it.").wait_for(timeout=30000)
        await page.locator("canvas").wait_for(timeout=30000)
        await page.wait_for_timeout(2000)
        await page.screenshot(path="artifacts/command-environment.png", full_page=True)
        print("page errors", errors)
        print("rendered canvases", await page.locator("canvas").count())
        print("screenshot artifacts/command-environment.png")
        await browser.close()


asyncio.run(main())
