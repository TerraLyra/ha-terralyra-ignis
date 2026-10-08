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
   card.setConfig({type:'custom:ignis-report-map',geo_location_sources:['terralyra_ignis_canada_reports'],report_switches:{terralyra_ignis_canada_reports:'switch.canada',terralyra_ignis_nifc_reports:'switch.nifc'}});
   window.report={entity_id:'geo_location.report',state:'186.1',attributes:{source:'terralyra_ignis_canada_reports',friendly_name:'Canada · <img src=x onerror=alert(1)>',distance_reference_name:'Canada',unit_of_measurement:'km',source_url:'javascript:alert(1)',source_times:{status_date:'2026-06-12T07:30:00Z'}}};
   card.hass={language:'hu',states:{'switch.canada':{state:'on'},'switch.nifc':{state:'on'},[report.entity_id]:report}};
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
  await page.evaluate(()=>{card.hass={language:'hu',states:{'switch.canada':{state:'on'},'switch.nifc':{state:'on'},[report.entity_id]:report}};});
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
    report={...report,attributes:{...report.attributes,source:'terralyra_ignis_nifc_reports',incident_name:'Named <img src=x onerror=alert(1)> fire',incident_text:'Official <script>alert(1)</script> description'}};
    card.hass={language:'hu',states:{'switch.canada':{state:'on'},'switch.nifc':{state:'on'},[report.entity_id]:report}};
    card.mapHost.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:report.entity_id},bubbles:true,composed:true}));
  });
  assert.match(await page.locator('dialog').innerText(),/Official <script>alert\(1\)<\/script> description/);
  assert.equal(await page.locator('dialog script').count(),0);
  assert.equal(await page.locator('dialog h3').innerText(),'Forrás szerinti leírás');
  await page.evaluate(()=>{
    report={...report,attributes:{...report.attributes,incident_text:null,incident_text_status:'not_requested',response_status:'refresh_failed_invalid_data'}};
    card.hass={language:'hu',states:{'switch.nifc':{state:'on'},[report.entity_id]:report}};
  });
  assert.match(await page.locator('dialog').innerText(),/nem tartalmaz lekért leírásmezőt/);
  assert.match(await page.locator('dialog').innerText(),/Megőrzött korábbi jelentés/);
  assert.match(await page.locator('dialog').innerText(),/Érvénytelen forrásválasz/);

  assert.equal(await page.locator('dialog h2').innerText(),'NIFC · Named <img src=x onerror=alert(1)> fire');
  assert.equal(await page.locator('dialog img').count(),0);
  await page.evaluate(()=>{card.hass={language:'hu',states:{'switch.canada':{state:'on'}}};});
  assert.equal(await page.getByRole('checkbox').count(),2);
  assert.equal(await page.getByRole('checkbox',{name:'Kanadai jelentések'}).count(),1);
  await page.evaluate(()=>{card.hass={language:'hu',states:{'switch.canada':{state:'off'}}};});
  assert.equal(await page.getByRole('checkbox').count(),1);
  await page.evaluate(()=>{
    document.querySelector('main').replaceChildren();
    window.editor=customElements.get('ignis-report-map').getConfigElement();
    window.edits=[];editor.addEventListener('config-changed',e=>edits.push(e.detail.config));
    editor.setConfig({type:'custom:ignis-report-map',entities:['zone.home'],default_zoom:7,report_switches:{terralyra_ignis_nifc_reports:'switch.missing'}});
    window.editorHass={language:'hu',states:{'switch.light':{state:'on',attributes:{friendly_name:'NIFC Canada lamp'}},'switch.canada':{state:'off',attributes:{friendly_name:'Canada <img src=x>',ignis_map_source:'terralyra_ignis_canada_reports'}}}};
    editor.hass=editorHass;document.querySelector('main').append(editor);
  });
  assert.equal(await page.evaluate(()=>edits.length),0);
  assert.equal(await page.getByRole('combobox',{name:'NIFC térképkapcsoló'}).inputValue(),'switch.missing');
  assert.equal(await page.locator('img').count(),0);
  assert.equal(await page.getByRole('combobox',{name:'Canada térképkapcsoló'}).locator('option').count(),2);
  assert.equal(await page.getByRole('combobox',{name:'NIFC térképkapcsoló'}).locator('option').count(),2);
  await page.getByRole('combobox',{name:'Canada térképkapcsoló'}).selectOption('switch.canada');
  assert.equal(await page.evaluate(()=>edits.at(-1).report_switches.terralyra_ignis_nifc_reports),'switch.missing');
  assert.deepEqual(await page.evaluate(()=>edits.at(-1).entities),['zone.home']);
  assert.equal(await page.evaluate(()=>edits.at(-1).default_zoom),7);
  assert.equal(await page.evaluate(()=>editorHass.states['switch.canada'].state),'off');
  await page.getByRole('textbox').fill('New title');
  await page.evaluate(()=>editor.hass=editorHass);
  assert.equal(await page.getByRole('textbox').inputValue(),'New title');
  await page.evaluate(()=>{editorHass.states['switch.canada'].state='on';editor.hass=editorHass});
  assert.match(await page.locator('section').innerText(),/nem igazolja friss/);
  assert.equal(await page.getByRole('textbox').inputValue(),'New title');
  await page.getByRole('textbox').press('Tab');
  assert.equal(await page.evaluate(()=>edits.at(-1).title),'New title');
  await page.getByRole('combobox',{name:'Canada térképkapcsoló'}).selectOption('');
  assert.equal(await page.evaluate(()=>Object.hasOwn(edits.at(-1).report_switches,'terralyra_ignis_canada_reports')),false);
  await page.evaluate(()=>{
    editor.setConfig({...editor.config,report_switches:{terralyra_ignis_nifc_reports:'switch.canada'}});
    editor.hass=editorHass;
  });
  assert.match(await page.locator('section').innerText(),/másik forráshoz tartozik/);
  assert.equal(await page.getByRole('combobox',{name:'NIFC térképkapcsoló'}).inputValue(),'switch.canada');
  await page.evaluate(()=>editor.hass={...editorHass,language:'en'});
  assert.equal(await page.getByRole('combobox',{name:'Canada map switch'}).count(),1);
  await page.getByRole('checkbox',{name:'Monitoring and alert circles',exact:true}).check();
  assert.deepEqual(await page.evaluate(()=>edits.at(-1).geo_location_sources),[{source:'terralyra_ignis_monitoring_areas',label_mode:'icon',focus:false}]);
  assert.deepEqual(await page.evaluate(()=>edits.at(-1).entities),['zone.home']);
  assert.equal(await page.evaluate(()=>edits.at(-1).default_zoom),7);
  assert.equal(await page.evaluate(()=>edits.at(-1).cluster),false);
  await page.getByRole('checkbox',{name:'Monitoring and alert circles',exact:true}).uncheck();
  assert.deepEqual(await page.evaluate(()=>edits.at(-1).geo_location_sources),[]);
  await page.evaluate(()=>editor.setConfig({...editor.config,show_all:true}));
  assert.equal(await page.getByRole('checkbox',{name:'Monitoring and alert circles',exact:true}).isDisabled(),true);
  assert.equal(await page.getByRole('checkbox',{name:'Monitoring and alert circles',exact:true}).isChecked(),true);

  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await page.evaluate(()=>{
    card.dialog.close(); card.selected=null;
    document.querySelector('main').replaceChildren(card);
    const satellite={entity_id:'geo_location.satellite',state:'3',attributes:{source:'terralyra_ignis',friendly_name:'Műholdas észlelés',context_entry_id:'entry',context_incident_id:'a'}};
    card.hass={language:'hu',states:{[satellite.entity_id]:satellite},callWS:async request=>{
      window.contextRequest=request;
      return {response:{reports:[{title:'Teszt hír',description:'<img src=x onerror=alert(1)>',published_at:'2026-10-07T12:00:00Z',report_url:'https://www.katasztrofavedelem.hu/modules/vesz/esemeny/1',ambiguous:true}]}};
    }};
    card.mapHost.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:satellite.entity_id},bubbles:true,composed:true}));
  });
  await page.getByRole('heading',{name:'Teszt hír'}).waitFor();
  assert.match(await page.locator('dialog').innerText(),/Valószínűleg/);
  assert.equal(await page.locator('dialog img').count(),0);
  assert.equal(await page.evaluate(()=>contextRequest.service),'get_satellite_report_context');
  assert.equal(await page.evaluate(()=>contextRequest.service_data.incident_id),'a');
  await page.getByRole('button',{name:'Home Assistant részletek'}).click();
  assert.equal(await page.evaluate(()=>nativeClicks.at(-1)),'geo_location.satellite');
  console.log('Browser checks passed: safe text/links, scoped clicks, native fallback, mobile fit, report removal, Escape.');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
