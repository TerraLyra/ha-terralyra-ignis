const assert=require('node:assert/strict'),fs=require('node:fs'),{chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||undefined});try{
 const page=await browser.newPage({viewport:{width:390,height:844}});await page.setContent('<main></main>');
 await page.addScriptTag({type:'module',content:fs.readFileSync('frontend/ignis-location-summary.js','utf8')});
 await page.evaluate(async()=>{await customElements.whenDefined('ignis-location-summary');window.card=document.createElement('ignis-location-summary');card.setConfig({entity:'sensor.place',location_id:'ca'});window.entity={state:'available',attributes:{location_id:'ca',location_name:'<img src=x onerror=alert(1)>',operational_status:'available',active_incidents:3,multi_source_incidents:1,source_health:[{provider:'NASA FIRMS',status:'available'}]}};card.hass={states:{'sensor.place':entity}};document.querySelector('main').append(card);window.info=null;card.addEventListener('hass-more-info',e=>window.info=e.detail.entityId);});
 assert.equal(await page.locator('.number').first().textContent(),'3');assert.equal(await page.locator('img').count(),0);
 await page.getByRole('button',{name:'Érzékelő részletei'}).click();assert.equal(await page.evaluate(()=>info),'sensor.place');
 await page.evaluate(()=>{entity={...entity,state:'unavailable'};card.hass={states:{'sensor.place':entity}}});assert.equal(await page.locator('.number').first().textContent(),'—');
 await page.evaluate(()=>card.setConfig({entity:'sensor.place',location_id:'home'}));assert.equal(await page.locator('.number').count(),0);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 console.log('Location summary browser checks passed');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
