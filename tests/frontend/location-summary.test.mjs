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
