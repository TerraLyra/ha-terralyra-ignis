// Run with NODE_PATH pointing to a Playwright installation. No live HA access.
const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL || undefined});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.setContent('<main></main>');
  await page.evaluate(()=>{
   window.loadCardHelpers=async()=>({createCardElement:()=>document.createElement('div')});
   window.nativeClicks=[];
   document.addEventListener('hass-more-info',e=>window.nativeClicks.push(e.detail.entityId));
  });
  await page.addScriptTag({type:'module',content:fs.readFileSync('frontend/ignis-report-map.js','utf8')});
  await page.evaluate(async()=>{
   await customElements.whenDefined('ignis-report-map');
   window.card=document.createElement('ignis-report-map');
   document.querySelector('main').append(card);
   card.setConfig({type:'custom:ignis-report-map',geo_location_sources:['terralyra_ignis_canada_reports']});
   window.report={entity_id:'geo_location.report',state:'186.1',attributes:{source:'terralyra_ignis_canada_reports',friendly_name:'Canada · <img src=x onerror=alert(1)>',distance_reference_name:'Canada',unit_of_measurement:'km',source_url:'javascript:alert(1)',source_times:{status_date:'2026-06-12T07:30:00Z'}}};
   card.hass={language:'hu',states:{[report.entity_id]:report}};
  });
  await page.evaluate(()=>card.mapHost.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:report.entity_id},bubbles:true,composed:true})));
  assert.equal(await page.locator('dialog').isVisible(),true);
  assert.equal(await page.getByRole('checkbox').count(),3);
  assert.equal(await page.locator('dialog img').count(),0);
  assert.equal(await page.locator('dialog a').count(),0);
  assert.match(await page.locator('dialog').innerText(),/Canada/);
  assert.deepEqual(await page.evaluate(()=>nativeClicks),[]);
  const box=await page.locator('dialog').boundingBox();
  assert.ok(box.width<=390 && box.x>=0);
  await page.getByRole('button',{name:'Home Assistant részletek'}).click();
  assert.deepEqual(await page.evaluate(()=>nativeClicks),['geo_location.report']);
  await page.evaluate(()=>card.mapHost.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:'geo_location.satellite'},bubbles:true,composed:true})));
  assert.deepEqual(await page.evaluate(()=>nativeClicks),['geo_location.report','geo_location.satellite']);
  await page.evaluate(()=>card.mapHost.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:report.entity_id},bubbles:true,composed:true})));
  // Reproduce a delayed close event from the previous dialog deterministically.
  await page.evaluate(()=>card.dialog.dispatchEvent(new Event('close')));
  assert.equal(await page.evaluate(()=>card.selected), 'geo_location.report');
  await page.evaluate(()=>{card.hass={language:'hu',states:{}};});
  assert.match(await page.locator('dialog').innerText(),/már nem érhető el/);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog').isVisible(),false);
  await page.evaluate(()=>{card.hass={language:'hu',states:{[report.entity_id]:report}};});
  assert.equal(await page.evaluate(()=>Object.hasOwn(card.map.hass.states,'geo_location.report')),true);
  await page.getByRole('checkbox',{name:'Kanadai jelentések'}).uncheck();
  assert.equal(await page.evaluate(()=>Object.hasOwn(card.map.hass.states,'geo_location.report')),false);
  await page.getByRole('checkbox',{name:'Kanadai jelentések'}).check();
  await page.getByRole('combobox').selectOption('7');
  assert.equal(await page.evaluate(()=>Object.hasOwn(card.map.hass.states,'geo_location.report')),false);
  assert.equal(await page.evaluate(()=>Object.hasOwn(card._hass.states,'geo_location.report')),true);
  await page.getByRole('combobox').selectOption('0');
  assert.equal(await page.evaluate(()=>Object.hasOwn(card.map.hass.states,'geo_location.report')),true);
  await page.evaluate(()=>{
    report={...report,attributes:{...report.attributes,incident_text:'Official <script>alert(1)</script> description'}};
    card.hass={language:'hu',states:{[report.entity_id]:report}};
    card.mapHost.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:report.entity_id},bubbles:true,composed:true}));
  });
  assert.match(await page.locator('dialog').innerText(),/Official <script>alert\(1\)<\/script> description/);
  assert.equal(await page.locator('dialog script').count(),0);
  console.log('Browser checks passed: safe text/links, scoped clicks, native fallback, mobile fit, report removal, Escape.');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
