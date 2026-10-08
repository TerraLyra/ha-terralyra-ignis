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
 await page.evaluate(()=>{card.setConfig({entity:'sensor.place',location_id:'ca',forecast:{entity:'sensor.forecast',location_id:'ca',latitude:47,longitude:19}});entity.state='available';window.forecast={state:'high',attributes:{scope:'near_home',sample_latitude:47,sample_longitude:19,generated_at:new Date().toISOString(),forecast:[{date:new Date().toISOString().slice(0,10),risk:'high'}],attribution:'<img src=x onerror=alert(1)>'}};card.hass={states:{'sensor.place':entity,'sensor.forecast':forecast}};});
 assert.match(await page.locator('ha-card').innerText(),/Magas · Érvényesség/);
 assert.equal(await page.locator('img').count(),0);
 await page.evaluate(()=>{forecast.state='unavailable';card.hass={states:{'sensor.place':entity,'sensor.forecast':forecast}};});
 assert.match(await page.locator('ha-card').innerText(),/előrejelzés jelenleg nem érhető el/);
 assert.doesNotMatch(await page.locator('ha-card').innerText(),/Magas · Érvényesség/);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.evaluate(()=>{
   card.setConfig({entity:'sensor.place',location_id:'ca',forecast:{entity:'sensor.forecast',location_id:'ca',latitude:47,longitude:19,radius_km:50}});
   forecast.state='high';Object.assign(forecast.attributes,{scope:'monitored_location',location_id:'ca',latitude:47,longitude:19,forecast_radius_km:50,provider:'eumetsat_lsa_saf_frmv3',product:'FRMv3',sample_latitude:47.05});
   card.hass={states:{'sensor.place':entity,'sensor.forecast':forecast}};
 });
 assert.match(await page.locator('ha-card').innerText(),/kijelölt helyszín közelére/);
 assert.match(await page.locator('ha-card').innerText(),/Magas · Érvényesség/);
 await page.evaluate(()=>{forecast.attributes.forecast_radius_km=100;card.hass={states:{'sensor.place':entity,'sensor.forecast':forecast}}});
 assert.doesNotMatch(await page.locator('ha-card').innerText(),/Magas · Érvényesség/);
 // Editor requires an explicit selection and preserves advanced configuration.
 await page.evaluate(()=>{
   document.querySelector('main').replaceChildren();
   const Card=customElements.get('ignis-location-summary');
   window.editor=Card.getConfigElement();window.changes=[];
   editor.addEventListener('config-changed',event=>changes.push(event.detail.config));
   editor.setConfig(Card.getStubConfig());editor.hass={states:{}};
   document.querySelector('main').append(editor);
   const preview=new Card();preview.setConfig(Card.getStubConfig());document.querySelector('main').append(preview);
 });
 assert.match(await page.locator('ha-card').innerText(),/Válassz egy megfigyelt helyszínt/);
 assert.match(await page.getByRole('status').innerText(),/Még nincs választható/);
 assert.equal(await page.evaluate(()=>changes.length),0);
 await page.evaluate(()=>{
   window.editorStates={'sensor.place':entity,'sensor.forecast':forecast,
    'sensor.other':{...entity,attributes:{...entity.attributes,location_id:'other',location_name:'Other'}}};
   editor.hass={states:editorStates};
 });
 assert.equal(await page.getByRole('combobox',{name:'Megfigyelt helyszín',exact:true}).inputValue(),'');
 assert.equal(await page.getByRole('combobox',{name:'Megfigyelt helyszín',exact:true}).locator('option').count(),3);
 assert.equal(await page.locator('img').count(),0);
 await page.getByRole('combobox',{name:'Megfigyelt helyszín',exact:true}).selectOption('sensor.place');
 assert.deepEqual(await page.evaluate(()=>changes.at(-1)),{type:'custom:ignis-location-summary',entity:'sensor.place',location_id:'ca'});
 await page.evaluate(()=>editor.setConfig({...changes.at(-1),forecast:{entity:'sensor.forecast',location_id:'ca',latitude:47,longitude:19},custom_option:true}));
 await page.getByRole('textbox').fill('My place');
 // A HA state update must not discard a title currently being typed.
 await page.evaluate(()=>{editorStates['sensor.place'].attributes.monitoring_radius_km=100;editorStates['sensor.place'].attributes.alert_radius_km=50;editor.hass={states:editorStates}});
 assert.match(await page.getByRole('region',{name:'Beállítások áttekintése'}).innerText(),/Megfigyelés: 100 km/);
 assert.equal(await page.getByRole('textbox').inputValue(),'My place');
 await page.getByRole('textbox').press('Tab');
 assert.equal(await page.evaluate(()=>changes.at(-1).title),'My place');
 assert.equal(await page.evaluate(()=>changes.at(-1).custom_option),true);
 await page.getByRole('combobox',{name:'Megfigyelt helyszín',exact:true}).selectOption('sensor.other');
 assert.equal(await page.evaluate(()=>changes.at(-1).location_id),'other');
 assert.equal(await page.evaluate(()=>changes.at(-1).forecast.location_id),'ca');
 // The existing card rejects that old forecast association; editor never rewrites it.
 await page.evaluate(()=>{card.setConfig(changes.at(-1));card.hass={states:editorStates};document.querySelector('main').append(card)});
 assert.match(await page.locator('ha-card').last().innerText(),/helyszín-hozzárendelése hiányos vagy eltérő/);
 await page.evaluate(()=>{editor.setConfig(changes.at(-1));editor.hass={states:{}}});
 assert.equal(await page.getByRole('combobox',{name:'Megfigyelt helyszín',exact:true}).inputValue(),'sensor.other');
 assert.equal(await page.evaluate(()=>changes.at(-1).entity),'sensor.other');
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.evaluate(()=>{
   editor.setConfig({type:'custom:ignis-location-summary',entity:'sensor.place',location_id:'ca',custom_option:true});
   editor.hass={states:{...editorStates,'sensor.risk':{state:'available',attributes:{scope:'monitored_location',location_id:'ca',provider:'eumetsat_lsa_saf_frmv3',product:'FRMv3',latitude:47,longitude:19,forecast_radius_km:25}}}};
 });
 await page.getByRole('combobox',{name:'Előrejelzés (nem kötelező)',exact:true}).selectOption('sensor.risk');
 assert.deepEqual(await page.evaluate(()=>changes.at(-1).forecast),{entity:'sensor.risk',location_id:'ca',latitude:47,longitude:19,radius_km:25});
 assert.equal(await page.evaluate(()=>changes.at(-1).custom_option),true);
 await page.evaluate(()=>{editor.hass={states:{...editor._hass.states,'sensor.risk':{state:'available',attributes:{...editor._hass.states['sensor.risk'].attributes,forecast_radius_km:40,latitude:48}}}}});
 assert.equal(await page.evaluate(()=>changes.at(-1).forecast.radius_km),25);
 await page.getByRole('button',{name:'Előrejelzés hozzárendelésének frissítése',exact:true}).click();
 assert.deepEqual(await page.evaluate(()=>changes.at(-1).forecast),{entity:'sensor.risk',location_id:'ca',latitude:48,longitude:19,radius_km:40});
 assert.equal(await page.evaluate(()=>changes.at(-1).custom_option),true);
 assert.equal(await page.getByRole('button',{name:'Előrejelzés hozzárendelésének frissítése',exact:true}).count(),0);
 await page.getByRole('combobox',{name:'Előrejelzés (nem kötelező)',exact:true}).selectOption('');
 assert.equal(await page.evaluate(()=>Object.hasOwn(changes.at(-1),'forecast')),false);
 await page.evaluate(()=>{
   editor.setConfig({...editor.config,forecast:{entity:'sensor.risk',location_id:'ca',latitude:47,longitude:19,radius_km:25}});
   editor.hass={states:{...editor._hass.states,'sensor.risk':{state:'available',attributes:{...editor._hass.states['sensor.risk'].attributes,location_id:'different-place'}}}};
 });
 assert.equal(await page.getByRole('button',{name:'Előrejelzés hozzárendelésének frissítése',exact:true}).count(),0);
 assert.equal(await page.getByRole('combobox',{name:'Előrejelzés (nem kötelező)',exact:true}).inputValue(),'sensor.risk');
 assert.equal(await page.evaluate(()=>editor.config.forecast.radius_km),25);

 if(process.env.IGNIS_SCREENSHOT){
   await page.evaluate(()=>{document.querySelector('main').replaceChildren(editor);editor.setConfig({type:'custom:ignis-location-summary',entity:'sensor.place',location_id:'ca'});entity.attributes.location_name='Home';editor.hass={states:{'sensor.place':entity}}});
   await page.screenshot({path:process.env.IGNIS_SCREENSHOT,fullPage:true});
 }
 console.log('Location summary browser checks passed');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
