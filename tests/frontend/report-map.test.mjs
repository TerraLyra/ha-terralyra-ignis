import {test} from 'node:test';
import assert from 'node:assert/strict';
import {reportView,safeLink,visibleMapSources,reportDescription,retrievalView} from '../../frontend/ignis-report-map.js';

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

test('report controls follow explicit map switches, not marker availability',()=>{
 const source='terralyra_ignis_canada_reports';
 const mapping={[source]:'switch.canada'};
 assert.equal(visibleMapSources({'switch.canada':{state:'on'}},mapping)[source],true);
 for(const state of ['off','unknown','unavailable'])assert.equal(visibleMapSources({'switch.canada':{state}},mapping)[source],false);
 assert.equal(visibleMapSources({},mapping)[source],false);
 assert.equal(visibleMapSources({'geo_location.report':{attributes:{source}}})[source],false);
 assert.equal(visibleMapSources().terralyra_ignis,true);
});


test('description absence distinguishes schema, empty source and unrequested field',()=>{
  assert.match(reportDescription({incident_text_status:'not_in_feed'},'hu').content,/nem tartalmaz/);
  assert.match(reportDescription({incident_text:'  ',incident_text_status:'not_provided'}).content,/did not provide/);
  assert.match(reportDescription({incident_text_status:'not_requested'}).content,/does not establish/);
  for(const status of [undefined,'available','unrecognised','toString']) {
    assert.match(reportDescription({incident_text_status:status}).content,/unknown/);
  }
});
test('supplied source text wins over stale status and truncation is disclosed',()=>{
  const text='Original <b>text</b>\nsecond line';
  const view=reportDescription({incident_text:text,incident_text_status:'not_provided'});
  assert.equal(view.content,text);
  assert.equal(view.notice,null);
  const long=reportDescription({incident_text:'x'.repeat(4001)},'hu');
  assert.equal(long.content.length,4000);
  assert.match(long.notice,/rövidítve/);
  assert.equal(reportDescription({incident_text:'x'.repeat(4000)}).notice,null);
});


test('retrieval errors explain retained reports without changing source status',()=>{
  for(const [source,status] of [
    ['terralyra_ignis_canada_reports','review_required'],
    ['terralyra_ignis_canada_reports','rate_limited'],
    ['terralyra_ignis_nifc_reports','refresh_failed_invalid_data'],
    ['terralyra_ignis_nifc_reports','restored_cooldown']]) {
    const attributes={...state.attributes,source,response_status:status};
    const view=reportView({...state,attributes},'hu');
    assert.match(view.retrievalNotice,/Megőrzött korábbi jelentés/);
    assert.ok(view.rows[7][1].includes(status));
    assert.equal(view.rows[2][1],'UC');
    assert.equal(attributes.response_status,status);
  }
});
test('success and unknown retrieval states never invent retention or freshness',()=>{
  for(const [source,status] of [
    ['terralyra_ignis_canada_reports','available'],
    ['terralyra_ignis_nifc_reports','retrieved']]) {
    const view=retrievalView({source,response_status:status});
    assert.match(view.label,/Successful retrieval/);
    assert.equal(view.notice,null);
  }
  for(const status of ['retrieved','future_status','toString',undefined]) {
    const view=retrievalView({source:'terralyra_ignis_canada_reports',response_status:status});
    assert.equal(view.notice,null);
    assert.doesNotMatch(view.label,/Successful/);
  }
});

const {mapBindingStatus}=await import('../../frontend/ignis-report-map.js');
test('binding readiness distinguishes absent, loading, missing and unavailable states',()=>{
 assert.equal(mapBindingStatus(undefined,''),'unbound');
 assert.equal(mapBindingStatus({},'sensor.other'),'invalid');
 assert.equal(mapBindingStatus(undefined,'switch.test'),'loading');
 assert.equal(mapBindingStatus({},'switch.test'),'missing');
 for(const state of ['on','off'])assert.equal(mapBindingStatus({'switch.test':{state}},'switch.test'),state);
 for(const state of ['unknown','unavailable','unexpected'])assert.equal(mapBindingStatus({'switch.test':{state}},'switch.test'),'unavailable');
});
