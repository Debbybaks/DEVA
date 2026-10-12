import { chromium, expect } from '@playwright/test';
import fs from 'node:fs/promises';
const base = process.argv[2] ?? 'http://127.0.0.1:8010';
const output = process.argv[3] ?? '../../artifacts/release';
await fs.mkdir(`${output}/screenshots`, {recursive: true});
const browser = await chromium.launch({executablePath: process.env.DEVA_CHROMIUM_PATH ?? '/usr/bin/chromium',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page = await browser.newPage({viewport:{width:1600,height:1000},reducedMotion:'reduce'});
const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
const timings={};
try {
 const start=performance.now(); await page.goto(base);
 await expect(page.getByRole('img',{name:'Chronological microgrid power and stored energy'})).toBeVisible();
 timings.world_startup_ms=performance.now()-start;
 await expect(page.getByText(/Public research archive/)).toBeVisible();
 await expect(page.getByText('Run a registered scientific investigation',{exact:true})).toHaveCount(0);
 await page.screenshot({path:`${output}/screenshots/microgrid.png`,fullPage:true});
 await page.getByRole('button',{name:/01 \/ WATER RESILIENCE/}).click();
 await expect(page.getByRole('img',{name:'Water network signed flow and pressure'})).toBeVisible();
 await page.screenshot({path:`${output}/screenshots/water.png`,fullPage:true});
 for(const lens of ['Evidence lens','Uncertainty lens','Engineering X-ray']){
  await page.getByRole('button',{name:lens,exact:true}).click();
  await page.screenshot({path:`${output}/screenshots/${lens.replaceAll(' ','-')}.png`,fullPage:true});
 }
 for(const audience of ['judge','portfolio','researcher']) await page.getByLabel('World audience').selectOption(audience);
 await page.getByRole('button',{name:'Demonstration 3.0'}).click();
 for(let n=0;n<8;n++) await page.getByRole('button',{name:'Next act'}).click();
 await expect(page.getByRole('img',{name:'Chronological microgrid power and stored energy'})).toBeVisible();
 await page.setViewportSize({width:390,height:844});
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
 await page.keyboard.press('Tab');
 if(await page.evaluate(()=>document.activeElement===document.body)) throw Error('Keyboard focus unavailable');
 const h=await page.request.get(`${base}/api/health`);if(!(await h.json()).public_read_only)throw Error('Public mode missing');
 for(const path of ['/api/domain/jobs','/api/jobs','/api/hydraulic/lab']) if((await page.request.post(`${base}${path}`,{data:{}})).status()!==403)throw Error('Public write allowed');
 if((await page.request.get(`${base}/api/not-a-route`)).status()!==404)throw Error('API error route missing');
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(`${output}/production-smoke.json`,JSON.stringify({base,status:'PASS',public:!base.includes('127.0.0.1')&&!base.includes('localhost'),timings,checks:['both physical domains','evidence/uncertainty/xray','judge/portfolio/researcher','stored demonstration','mobile width','keyboard focus','reduced motion','read-only compute','404 recovery'],page_errors:errors},null,2));
}finally{await browser.close()}
