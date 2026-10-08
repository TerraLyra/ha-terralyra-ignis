import {test} from 'node:test';
import assert from 'node:assert/strict';
globalThis.HTMLElement=class {};
globalThis.customElements={define(){}};
globalThis.window={};
const {summarizeLocation}=await import('../../frontend/ignis-location-summary.js');
const entity={state:'available',attributes:{location_id:'ca',location_name:'Canada',operational_status:'available',source_health:[],active_incidents:3,multi_source_incidents:1}};
test('requires explicit matching location identity',()=>{
 assert.ok(summarizeLocation(entity,'home').error);
 assert.ok(summarizeLocation(null,'ca').error);
 assert.ok(summarizeLocation({attributes:{location_id:'ca'}},'ca').error);
});
test('unavailable or restoring data does not become zero or retain old counts',()=>{
 for(const state of ['unknown','unavailable'])assert.equal(summarizeLocation({...entity,state},'ca').active,null);
 for(const operational_status of ['initializing','unavailable','no_coverage','unexpected'])assert.equal(summarizeLocation({...entity,attributes:{...entity.attributes,operational_status}},'ca').active,null);
});
test('partial snapshot retains numeric meaning and visible status',()=>{
 const m=summarizeLocation({...entity,attributes:{...entity.attributes,operational_status:'partial',active_incidents:0}},'ca');
 assert.equal(m.active,0);assert.equal(m.status,'Részleges adatellátás');
});
test('invalid count cannot be shown as real observation',()=>{
 for(const active_incidents of [-1,1.5,'3',NaN,Infinity,null])assert.equal(summarizeLocation({...entity,attributes:{...entity.attributes,active_incidents}},'ca').active,null);
 assert.equal(summarizeLocation(entity,'ca').active,3);
});

const {summarizeForecast}=await import('../../frontend/ignis-location-summary.js');
const binding={entity:'sensor.risk',location_id:'home',latitude:47,longitude:19};
const now=new Date('2026-09-29T12:00:00Z');
const forecast={state:'high',attributes:{scope:'near_home',sample_latitude:47,sample_longitude:19,generated_at:'2026-09-29T06:00:00Z',forecast:[{date:'2026-09-29',risk:'low'}],attribution:'LSA SAF'}};
const review=(e=forecast,b=binding)=>summarizeForecast(e,b,'home',now);
test('forecast uses dated product entry, not potentially stale sensor state',()=>{
 assert.equal(review().risk,'Alacsony'); assert.equal(review().validDate,'2026-09-29');
 assert.equal(review().received,'2026-09-29T06:00:00.000Z');
});
test('forecast fails closed on wrong location, coordinates, scope or unavailable entity',()=>{
 for(const b of [{...binding,location_id:'ca'},{...binding,latitude:'47'},{...binding,latitude:91}])assert.ok(review(forecast,b).message);
 for(const attributes of [{...forecast.attributes,sample_latitude:48},{...forecast.attributes,scope:'monitoring_area'}])assert.ok(review({...forecast,attributes}).message);
 for(const state of ['unknown','unavailable'])assert.ok(review({...forecast,state}).message);
 assert.ok(review(null).message);
});
test('expired, missing, duplicate and unknown forecast dates never appear as current risk',()=>{
 for(const days of [[],[{date:'2026-09-28',risk:'high'}],[{date:'2026-09-30',risk:'high'}],[{date:'2026-09-29',risk:'unknown'}],[{date:'2026-09-29',risk:'high'},{date:'2026-09-29',risk:'low'}]])assert.ok(review({...forecast,attributes:{...forecast.attributes,forecast:days}}).message);
});
test('UTC product day is independent of local DST date; offsetless receipt stays unknown',()=>{
 assert.ok(summarizeForecast(forecast,binding,'home',new Date('2026-09-30T00:30:00+02:00')).risk);
 for(const generated_at of ['2026-09-29T06:00:00','garbage','2026-09-30T06:00:00Z'])assert.equal(review({...forecast,attributes:{...forecast.attributes,generated_at}}).received,null);
 assert.match(review({...forecast,attributes:{...forecast.attributes,generated_at:'2026-09-28T06:00:00Z'}}).freshness,/12 órás/);
});

test('nearest distance is exact-location, finite and suppressed for unavailable data',()=>{
 const located={...entity,attributes:{...entity.attributes,nearest_incident_distance_km:0}};
 assert.equal(summarizeLocation(located,'ca').nearest,0);
 assert.equal(summarizeLocation({...located,state:'unavailable'},'ca').nearest,null);
 assert.ok(summarizeLocation(located,'home').error);
 for(const v of [undefined,null,-1,Infinity,'2',true])assert.equal(summarizeLocation({...entity,attributes:{...entity.attributes,nearest_incident_distance_km:v}},'ca').nearest,null);
});

test('location forecast binds requested geometry independently of sampled pixel',()=>{
 const b={...binding,radius_km:50};
 const e={...forecast,attributes:{...forecast.attributes,scope:'monitored_location',location_id:'home',latitude:47,longitude:19,forecast_radius_km:50,provider:'eumetsat_lsa_saf_frmv3',product:'FRMv3',sample_latitude:47.05,sample_longitude:19.05}};
 assert.equal(review(e,b).risk,'Alacsony');
 for(const changes of [{location_id:'other'},{latitude:47.000001},{longitude:20},{forecast_radius_km:51},{provider:'other'},{product:'other'}])assert.ok(review({...e,attributes:{...e.attributes,...changes}},b).message);
 for(const radius_km of [undefined,0,501,'50',true])assert.ok(review(e,{...b,radius_km}).message);
});

test('summary exposes both radii belonging to the selected location',()=>{
 const e={...entity,attributes:{...entity.attributes,monitoring_radius_km:100,alert_radius_km:25}};
 const m=summarizeLocation(e,'ca');
 assert.equal(m.monitoringRadius,100);assert.equal(m.alertRadius,25);
 assert.ok(summarizeLocation(e,'other').error);
});

const {locationChoices}=await import('../../frontend/ignis-location-summary.js');
test('editor lists explicit location-status sensors only, including unavailable existing locations',()=>{
 const states={
  'sensor.place':entity,
  'sensor.unavailable':{...entity,state:'unavailable',attributes:{...entity.attributes,location_id:'other',location_name:'Other'}},
  'sensor.forecast':{attributes:{location_id:'ca',scope:'monitored_location'}},
  'sensor.global':{attributes:{operational_status:'available',source_health:[]}},
  'binary_sensor.place':entity,
  'sensor.blank':{attributes:{...entity.attributes,location_id:' '}},
 };
 assert.deepEqual(locationChoices(states).map(c=>[c.entity,c.location_id]),[['sensor.place','ca'],['sensor.unavailable','other']]);
 assert.deepEqual(locationChoices(),[]);
});

const {sourceGuidance}=await import('../../frontend/ignis-location-summary.js');
test('source guidance prioritizes authentication and failed retrieval over cached freshness',()=>{
 assert.match(sourceGuidance({status:'auth_error',retrieval_status:'failed'}),/hozzáférési/);
 assert.match(sourceGuidance({status:'available',retrieval_status:'failed'}),/sikertelen/);
 assert.match(sourceGuidance({status:'delayed',retrieval_status:'failed'}),/sikertelen/);
 assert.match(sourceGuidance({status:'delayed',retrieval_status:'successful'}),/nem jelent friss/);
 assert.match(sourceGuidance({status:'no_product'}),/nem következik/);
 assert.match(sourceGuidance({status:'initializing'}),/első lekérés/);
 for(const source of [null,{}, {status:'available'}, {status:'future_status'}])assert.equal(sourceGuidance(source),'');
});

const {setupReview}=await import('../../frontend/ignis-location-summary.js');
test('setup review never claims notifications are configured and respects identity',()=>{
 assert.equal(setupReview(entity,'wrong').length,1);
 const configured={...entity,attributes:{...entity.attributes,monitoring_radius_km:100,alert_radius_km:100}};
 assert.match(setupReview(configured,'ca').join(' '),/Megfigyelés: 100 km/);
 assert.match(setupReview(configured,'ca').join(' '),/nem ellenőrzi/);
 assert.match(setupReview({...configured,state:'unavailable'},'ca').join(' '),/adatellátás jelenleg nem ellenőrizhető/);
 for(const alert_radius_km of [101,0,-1,'50',NaN])assert.match(setupReview({...configured,attributes:{...configured.attributes,alert_radius_km}},'ca')[1],/Ellenőrizd/);
});

test('visual forecasts require exact location and valid source geometry',async()=>{
 const {forecastChoices}=await import('../../frontend/ignis-location-summary.js');
 const good={state:'unavailable',attributes:{scope:'monitored_location',location_id:'home',provider:'eumetsat_lsa_saf_frmv3',product:'FRMv3',latitude:47,longitude:19,forecast_radius_km:25}};
 assert.deepEqual(forecastChoices({'sensor.risk':good},'home')[0],{entity:'sensor.risk',name:'sensor.risk',location_id:'home',latitude:47,longitude:19,radius_km:25});
 for(const patch of [{scope:'near_home'},{location_id:'other'},{provider:'other'},{latitude:NaN},{longitude:190},{forecast_radius_km:0}])assert.equal(forecastChoices({'sensor.risk':{...good,attributes:{...good.attributes,...patch}}},'home').length,0);
 assert.equal(forecastChoices({'sensor.risk':good},undefined).length,0);
});

test('setup review distinguishes optional missing forecast from mismatched binding',async()=>{
 const {forecastSetupReview}=await import('../../frontend/ignis-location-summary.js');
 assert.match(forecastSetupReview({}, {location_id:'home'}),/nem kötelező/);
 assert.match(forecastSetupReview({}, {location_id:'home',forecast:{entity:'sensor.risk',location_id:'other',latitude:47,longitude:19}}),/eltérő/);
 assert.match(forecastSetupReview({}, {location_id:'home',forecast:{entity:'sensor.risk',location_id:'home',latitude:47,longitude:19}}),/nem érhető el/);
});

test('English summary retains data meaning and source text',async()=>{
 const {summaryLanguage,sourceGuidance,setupReview,forecastSetupReview}=await import('../../frontend/ignis-location-summary.js');
 assert.equal(summaryLanguage({language:'hu-HU'}),'hu');
 assert.equal(summaryLanguage({language:'de'}),'en');
 assert.equal(summaryLanguage({locale:{language:'en-US'}}),'en');
 assert.equal(summaryLanguage({}),'hu');
 const e={...entity,attributes:{...entity.attributes,location_name:'Magas',monitoring_radius_km:100,alert_radius_km:25}};
 assert.equal(summarizeLocation(e,'ca','en').name,'Magas');
 assert.equal(summarizeLocation(e,'ca','en').status,'Sources available');
 assert.equal(summarizeLocation({...e,state:'unavailable'},'ca','en').active,null);
 assert.match(sourceGuidance({status:'no_product'},'en'),/does not mean there is no fire/);
 assert.match(setupReview(e,'ca','en').join(' '),/Monitoring: 100 km · Alert: 25 km/);
 assert.match(setupReview(e,'ca','en').join(' '),/does not verify existing automations or delivery/);
 assert.equal(summarizeForecast(forecast,binding,'home',now,'en').risk,'Low');
 assert.match(summarizeForecast({...forecast,state:'unavailable'},binding,'home',now,'en').message,/unavailable/);
 assert.match(forecastSetupReview({}, {},now,'en'),/not linked/);
});
