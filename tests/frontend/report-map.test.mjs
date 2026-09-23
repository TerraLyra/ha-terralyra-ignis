import {test} from 'node:test';
import assert from 'node:assert/strict';
import {reportView,safeLink} from '../../frontend/ignis-report-map.js';

const state = {entity_id:'geo_location.example',state:'12.3',attributes:{
  source:'terralyra_ignis_canada_reports',friendly_name:'Report <script>',
  distance_reference_name:'Canada',unit_of_measurement:'km',
  source_times:{status_date:'2026-06-12T07:30:00+00:00'},
  source_status:'UC',source_url:'https://cwfis.cfs.nrcan.gc.ca/'}};
test('only supported official map sources are intercepted',()=>{
  assert.equal(reportView({...state,attributes:{source:'terralyra_ignis'}}),null);
  assert.equal(reportView({...state,entity_id:'sensor.example'}),null);
  assert.equal(reportView(null),null);
});
test('keeps source time and selected location; does not invent a receipt time',()=>{
  const view=reportView(state,'hu');
  assert.equal(view.rows[0][1],'Canada');
  assert.equal(view.rows[1][1],'12.3 km');
  assert.match(view.rows[4][1],/2026-06-12T07:30:00\+00:00/);
  assert.equal(view.rows[6][1],'Nincs megadva');
  assert.equal(view.title,'Report <script>');
});
test('timezone-less timestamps never become browser-local dates',()=>{
  const view=reportView({...state,attributes:{...state.attributes,source_times:{status_date:'2026-06-12T07:30:00'}}});
  assert.equal(view.rows[4][1],'Not provided');
});
test('unsafe or credential-bearing links are not navigable',()=>{
  for(const url of ['javascript:alert(1)','data:text/html,test','http://example.com','https://user:secret@example.com','/relative']) assert.equal(safeLink(url),null);
  assert.equal(safeLink('https://example.com/report'),'https://example.com/report');
});
test('unavailable reports are explicit, not a zero-distance report',()=>{
  const view=reportView({...state,state:'unavailable'});
  assert.equal(view.unavailable,true);
  assert.equal(view.rows[1][1],'Not provided');
});
test('NIFC uses its actual modification and discovery clocks',()=>{
  const view=reportView({...state,attributes:{source:'terralyra_ignis_nifc_reports',source_modified_at:'2026-09-22T12:00:00Z',source_discovered_at:'2026-09-01T11:00:00Z'}});
  assert.match(view.rows[4][1],/2026-09-22T12:00:00Z/);
  assert.match(view.rows[5][1],/2026-09-01T11:00:00Z/);
});

test('age filter hides only old official reports; unknown and satellite records survive',async()=>{
  const {filterMapStates,reportAge}=await import('../../frontend/ignis-report-map.js');
  const now=Date.parse('2026-09-22T12:00:00Z');
  const old={...state,attributes:{...state.attributes,source_times:{status_date:'2026-09-01T12:00:00Z'}}};
  const unknown={...state,attributes:{...state.attributes,source_times:{}}};
  const satellite={...state,attributes:{source:'terralyra_ignis'}};
  const future={...state,attributes:{...state.attributes,source_times:{status_date:'2026-09-23T12:00:00Z'}}};
  const states={old,unknown,satellite,future};
  assert.equal(reportAge(old,now),21);
  assert.deepEqual(Object.keys(filterMapStates(states,{},7,now)),['unknown','satellite','future']);
  assert.deepEqual(Object.keys(filterMapStates(states,{},0,now)),Object.keys(states));
  assert.deepEqual(Object.keys(filterMapStates(states,{terralyra_ignis_canada_reports:false},0,now)),['satellite']);
  assert.equal(states.old,old);
});

 test('NIFC title uses a supplied name and falls back for absent or invalid names',()=>{
  const attributes={...state.attributes,source:'terralyra_ignis_nifc_reports'};
  assert.equal(reportView({...state,attributes:{...attributes,incident_name:' SEVEN OAKS VMP RX '}}).title,'NIFC · SEVEN OAKS VMP RX');
  for (const incident_name of [undefined,null,'','   ',42,{}]) {
    assert.equal(reportView({...state,attributes:{...attributes,incident_name}}).title,state.attributes.friendly_name);
  }
  assert.equal(reportView({...state,attributes:{...state.attributes,incident_name:'Unrelated'}}).title,state.attributes.friendly_name);
});
