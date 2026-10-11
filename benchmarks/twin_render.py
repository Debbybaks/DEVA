"""Real WebGL shader workload, numerical fallback and WebGPU availability probe."""
import asyncio,json,statistics
from pathlib import Path
import numpy as np
from playwright.async_api import async_playwright

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport=dict(width=1600,height=1000))
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto('http://127.0.0.1:5173/?model=twin');await page.get_by_text('Make the model answer to evidence.').wait_for(timeout=30000)
  data=await (await page.request.get('http://127.0.0.1:5173/api/twin/view')).json()
  capability=await page.evaluate("""async()=>{if(!navigator.gpu)return {available:false,reason:'navigator.gpu absent'};try{const a=await Promise.race([navigator.gpu.requestAdapter(),new Promise(r=>setTimeout(()=>r(null),3000))]);return {available:!!a,reason:a?'adapter returned':'No adapter returned',info:a?{vendor:a.info?.vendor,architecture:a.info?.architecture,description:a.info?.description}:null};}catch(e){return {available:false,reason:String(e)}}}""")
  samples=[]
  for mode in ['standard','high','2d']:
   await page.get_by_label('Twin rendering').select_option(mode)
   for layer in ['pressure','flow']:
    await page.get_by_role('button',name=layer,exact=True).click();await page.wait_for_timeout(500)
    times=await page.evaluate("""()=>new Promise(resolve=>{const a=[];let prev=performance.now();function tick(t){a.push(t-prev);prev=t;if(a.length===60)resolve(a);else requestAnimationFrame(tick);}requestAnimationFrame(tick);})""")
    heap=await page.evaluate('()=>performance.memory?performance.memory.usedJSHeapSize:null')
    resolution=await page.evaluate('()=>{const c=document.querySelector("canvas");return c?{width:c.width,height:c.height,css_width:c.clientWidth,css_height:c.clientHeight}:null;}')
    count=sum(g['particle_count'] if mode=='high' else int(np.ceil(g['particle_count']*.5)) for g in data['frames'][0]['baseline_gpu']) if layer=='flow' and mode!='2d' else 0
    samples.append(dict(mode=mode,layer=layer,particle_count=count,particle_attribute_bytes=count*24,mean_frame_ms=statistics.mean(times),p95_frame_ms=float(np.quantile(times,.95)),samples=len(times),javascript_heap_bytes=heap,render_resolution=resolution))
  latency=[]
  for _ in range(10):
   a=await page.evaluate('async()=>{const t=performance.now();const r=await fetch("/api/twin/view");await r.arrayBuffer();return performance.now()-t;}');latency.append(a)
  await browser.close()
 report=dict(renderer='Chromium requested software ANGLE SwiftShader',viewport=[1600,1000],webgpu=capability,workloads=samples,api_latency_ms=dict(mean=float(np.mean(latency)),p95=float(np.quantile(latency,.95)),samples=latency),page_errors=errors,scope='Same stored initial model state. Frame timing is browser rAF, not GPU kernel timing. Attribute bytes exclude driver overhead; JS heap is not GPU memory. No WGSL before/after benchmark without an available WebGPU adapter; no claimed GPU-compute acceleration.')
 Path('artifacts/twin-render-performance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
asyncio.run(main())
