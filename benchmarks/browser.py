"""Actual browser frame sampling and live API latency under worker load."""

import asyncio
import json
from pathlib import Path
import statistics
import time
import httpx
import numpy as np
from playwright.async_api import async_playwright


async def main():
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000", timeout=60, trust_env=False
    ) as client:
        raw = (await client.get("/api/problem")).json()
        submission = await client.post(
            "/api/jobs",
            json=dict(
                raw=raw,
                seed=20261100,
                generations=1,
                train_samples=60,
                validation_samples=60,
                test_samples=100,
            ),
        )
        submission.raise_for_status()
        jid = submission.json()["job_id"]
        cached = submission.json()["cached"]
        latencies = []
        for _ in range(30):
            start = time.perf_counter()
            response = await client.get("/api/health")
            response.raise_for_status()
            latencies.append(time.perf_counter() - start)
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
            page = await browser.new_page(viewport={"width": 1600, "height": 1000})
            await page.goto("http://127.0.0.1:5173")
            await page.get_by_text("Try to break it.").wait_for()
            await page.locator("canvas").wait_for()
            await page.wait_for_timeout(1000)
            renderer = await page.locator("canvas").evaluate(
                "c=>{const gl=c.getContext('webgl2');const ext=gl.getExtension('WEBGL_debug_renderer_info');return ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'Unknown WebGL2 renderer';}"
            )
            frames = await page.evaluate(
                "()=>new Promise(resolve=>{const samples=[];let last=performance.now();function step(now){samples.push(now-last);last=now;if(samples.length>=180)resolve(samples);else requestAnimationFrame(step);}requestAnimationFrame(step);})"
            )
            await browser.close()
        status = (await client.get(f"/api/jobs/{jid}")).json()
    report = dict(
        browser=dict(
            renderer=renderer,
            viewport=[1600, 1000],
            frame_samples=len(frames),
            median_frame_ms=statistics.median(frames),
            p95_frame_ms=float(np.quantile(frames, 0.95)),
            mean_frame_ms=statistics.mean(frames),
        ),
        api_under_worker_load=dict(
            requests=len(latencies),
            submission_cached=cached,
            median_seconds=statistics.median(latencies),
            p95_seconds=float(np.quantile(latencies, 0.95)),
            job_status_at_end=status["status"],
        ),
        caveat="Measured local Chromium software rasterisation, not hardware GPU performance. Warm API endpoints; no WAN latency claim.",
    )
    Path("artifacts/browser-performance.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    asyncio.run(main())
