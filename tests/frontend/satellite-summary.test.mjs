import {test} from 'node:test';
import assert from 'node:assert/strict';
const {satelliteSummary}=await import('../../frontend/ignis-report-map.js');
test('satellite summary leads with settlement and retains distinct observation clocks',()=>{
 const v=satelliteSummary({state:'49',attributes:{nearest_settlement:'Ercsi',first_seen:'2026-10-14T12:00:00Z',last_seen:'2026-10-14T13:00:00Z',distance_km:49.2,location_name:'Home',providers:['firms','firms'],source_observations:[{providers:['lsa_saf']}],pixel_count:0}},'hu');
 assert.equal(v.title,'Ercsi · Tűzészlelés');assert.notEqual(v.first,v.last);assert.equal(v.multiple,true);assert.equal(v.providers.length,2);assert.equal(v.distance,'49,2 km');
 assert.ok(v.technical.some(([k,v])=>k==='Pixels'&&v==='0'));
});
test('missing and offsetless timestamps do not become observation times',()=>{
 const v=satelliteSummary({state:'unavailable',attributes:{first_seen:'2026-10-14T12:00:00',distance_km:null,providers:[]}},'en');
 assert.equal(v.first,'Not provided');assert.equal(v.last,'Not provided');assert.equal(v.distance,'Not provided');assert.equal(v.multiple,false);assert.equal(v.unavailable,true);
});
