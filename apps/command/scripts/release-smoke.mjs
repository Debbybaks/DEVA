import { chromium, expect } from '@playwright/test';
import fs from 'node:fs/promises';
import { X509Certificate, createHash } from 'node:crypto';
const proxyCA = process.env.DEVA_BROWSER_PROXY_CA;
const proxySPKI = proxyCA ? createHash('sha256').update(new X509Certificate(await fs.readFile(proxyCA)).publicKey.export({type:'spki',format:'der'})).digest('base64') : null;
const base = process.argv[2] ?? 'http://127.0.0.1:8010';
const output = process.argv[3] ?? '../../artifacts/release';
await fs.mkdir(`${output}/screenshots`, {recursive: true});
const browser = await chromium.launch({executablePath: process.env.DEVA_CHROMIUM_PATH ?? '/usr/bin/chromium',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader', ...(proxySPKI ? [`--ignore-certificate-errors-spki-list=${proxySPKI}`] : [])]});
const proxyURL = process.env.DEVA_SMOKE_PROXY ? new URL(process.env.DEVA_SMOKE_PROXY) : null;
const page = await browser.newPage({...(proxyURL ? {proxy:{server:proxyURL.origin,username:decodeURIComponent(proxyURL.username),password:decodeURIComponent(proxyURL.password)}} : {}),viewport:{width:1600,height:1000},reducedMotion:'reduce'});
const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
const timings={};
try {
 const start=performance.now(); await page.goto(base);
 await expect(page.getByRole('link',{name:'GitHub / Source code'})).toHaveAttribute('href','https://github.com/Debbybaks/DEVA');
 await expect(page.getByRole('heading',{name:'Different physics. One investigation engine.'})).toBeVisible();
 await expect(page.locator('pre:visible')).toHaveCount(0);
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
 for(const audience of ['judge','portfolio','researcher']) {
  await page.getByLabel('World audience').selectOption(audience);
  await expect(page.getByLabel('World audience')).toHaveValue(audience);
  await expect(page.locator('pre:visible')).toHaveCount(0);
 }
 await page.getByRole('button',{name:'Evidence lens',exact:true}).click();
 await page.getByText('Claim ledger / domain-scoped',{exact:true}).click();
 await expect(page.locator('pre:visible')).toHaveCount(0);
 await page.getByText('View raw evidence',{exact:true}).first().click();
 await expect(page.locator('pre:visible').first()).toBeVisible();
 await page.getByRole('button',{name:'Demonstration 3.0'}).click();
 for(let n=0;n<8;n++) await page.getByRole('button',{name:'Next act'}).click();
 await expect(page.getByRole('img',{name:'Chronological microgrid power and stored energy'})).toBeVisible();
 await page.setViewportSize({width:390,height:844});
 await page.goto(base);
 await expect(page.getByRole('heading',{name:'Different physics. One investigation engine.'})).toBeVisible();
 await expect(page.getByRole('img',{name:'Chronological microgrid power and stored energy'})).toBeVisible();
 await expect(page.locator('pre:visible')).toHaveCount(0);
 await page.screenshot({path:`${output}/screenshots/mobile-root.png`,fullPage:true});
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
 await page.keyboard.press('Tab');
 if(await page.evaluate(()=>document.activeElement===document.body)) throw Error('Keyboard focus unavailable');
 const h=await page.request.get(`${base}/api/health`);if(!(await h.json()).public_read_only)throw Error('Public mode missing');
 for(const path of ['/api/domain/jobs','/api/jobs','/api/hydraulic/lab']) if((await page.request.post(`${base}${path}`,{data:{}})).status()!==403)throw Error('Public write allowed');
 if((await page.request.get(`${base}/api/not-a-route`)).status()!==404)throw Error('API error route missing');
 await page.setViewportSize({width:1600,height:1000});
 await page.getByRole('link',{name:'Research archive'}).click();
 await expect(page).toHaveURL(`${base}/archive`);
 await expect(page.getByText('Try to break it.')).toBeVisible();
 await expect(page.getByText('38 / 200 held-out failures')).toBeVisible();
 await page.screenshot({path:`${output}/screenshots/archive.png`,fullPage:true});
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(`${output}/production-smoke.json`,JSON.stringify({base,status:'PASS',public:!base.includes('127.0.0.1')&&!base.includes('localhost'),timings,checks:['both physical domains','evidence/uncertainty/xray','judge/portfolio/researcher','stored demonstration','mobile width','keyboard focus','reduced motion','read-only compute','404 recovery'],page_errors:errors},null,2));
}finally{await browser.close()}
