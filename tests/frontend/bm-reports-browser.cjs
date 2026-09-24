const assert=require('node:assert/strict');const fs=require('node:fs');const {chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||undefined});try{
const page=await browser.newPage({viewport:{width:390,height:844}});await page.setContent('<main></main>');
await page.addScriptTag({type:'module',content:fs.readFileSync('frontend/ignis-bm-reports.js','utf8')});
await page.evaluate(async()=>{await customElements.whenDefined('ignis-bm-reports');window.calls=[];window.card=document.createElement('ignis-bm-reports');card.setConfig({});card.hass={callWS:async req=>{calls.push(req);if(window.fail)throw Error('offline');return {response:{status:'available',notices:[{title:'<img src=x onerror=alert(1)>',description:'Ég a tarló.',url:'https://www.katasztrofavedelem.hu/modules/vesz/esemeny/1',fire_scope:{category:'vegetation_fire_candidate'}},{title:'Lakástűz',url:'javascript:alert(1)',fire_scope:{category:'local_asset_fire_candidate'}},{title:'Baleseti hír',url:'https://www.katasztrofavedelem.hu/modules/vesz/esemeny/4',fire_scope:{category:'non_fire_report_candidate'}},{title:'Ismeretlen',url:'https://www.katasztrofavedelem.hu/modules/vesz/esemeny/3'}]}}}};document.querySelector('main').append(card)});
assert.equal(await page.evaluate(()=>calls.length),0);
await page.getByRole('button',{name:'Jelentések lekérése'}).click();await page.locator('.entry').first().waitFor();assert.equal(await page.locator('.entry').count(),2);assert.equal(await page.locator('img').count(),0);
assert.equal((await page.evaluate(()=>calls[0])).return_response,true);
await page.getByRole('combobox').selectOption('all');assert.equal(await page.locator('.entry').count(),4);await page.getByRole('button',{name:/Lakástűz/}).click();assert.equal(await page.locator('a').count(),0);
await page.getByRole('combobox').selectOption('veg');assert.equal(await page.locator('.entry').count(),1);assert.equal(await page.locator('a').count(),1);
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
await page.evaluate(()=>window.fail=true);await page.getByRole('button',{name:'Jelentések lekérése'}).click();await page.getByRole('alert').waitFor();assert.equal(await page.locator('.entry').count(),0);
console.log('BM card: explicit fetch, filters, safe text/links, mobile and failure checks passed');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
