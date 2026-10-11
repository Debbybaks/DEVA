"""Actual same-state rendering modes; WebGPU capability, not invented speedups."""

import asyncio, json, statistics
from pathlib import Path
import numpy as np
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=[
                "--no-sandbox",
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ],
        )
        page = await b.new_page(viewport=dict(width=1600, height=1000))
        await page.goto("http://127.0.0.1:5173/?model=hydraulic")
        await page.get_by_text("Design against pressure. Trust the evidence.").wait_for(
            timeout=30000
        )
        gpu = await page.evaluate(
            """async()=>{if(!navigator.gpu)return {available:false,reason:'navigator.gpu absent'};try{const a=await Promise.race([navigator.gpu.requestAdapter(),new Promise(r=>setTimeout(()=>r(null),3000))]);return {available:!!a,info:a?{vendor:a.info?.vendor,architecture:a.info?.architecture,description:a.info?.description}:null};}catch(e){return {available:false,reason:String(e)}}}"""
        )
        modes = []
        for mode in ["standard", "high", "2d"]:
            await page.get_by_label("Visual performance").select_option(mode)
            await page.wait_for_timeout(500)
            frames = await page.evaluate(
                """()=>new Promise(resolve=>{const values=[];let last=performance.now();function step(t){values.push(t-last);last=t;if(values.length===60)resolve(values);else requestAnimationFrame(step);}requestAnimationFrame(step);})"""
            )
            resolution = await page.evaluate(
                "()=>{const c=document.querySelector('canvas');return c?{width:c.width,height:c.height,css_width:c.clientWidth,css_height:c.clientHeight,device_pixel_ratio:devicePixelRatio}:null;}"
            )
            modes.append(
                dict(
                    render_resolution=resolution,
                    mode=mode,
                    samples=len(frames),
                    median_frame_ms=statistics.median(frames),
                    p95_frame_ms=float(np.quantile(frames, 0.95)),
                    mean_frame_ms=statistics.mean(frames),
                )
            )
        await b.close()
    report = dict(
        viewport=[1600, 1000],
        renderer="Chromium requested ANGLE SwiftShader software rendering",
        webgpu_capability=gpu,
        mode_samples=modes,
        scope="Same stored hydraulic state and values. Capability probe is not a WebGPU implementation benchmark. No claimed WebGPU/Rust speedup. Software-only frame measurements.",
    )
    Path("artifacts/render-mode-performance.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))


asyncio.run(main())
