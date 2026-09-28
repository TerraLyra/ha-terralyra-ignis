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
