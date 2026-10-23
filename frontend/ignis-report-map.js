// Optional local dashboard resource. No external libraries or report-page requests.
const SOURCES = new Set(['terralyra_ignis_canada_reports', 'terralyra_ignis_nifc_reports', 'terralyra_ignis_tasalert_reports', 'terralyra_ignis_inpe_reports']);
// Explicit map-switch entity associations; never infer opt-in from report count.
export function visibleMapSources(states = {}, switches = {}) {
  return {terralyra_ignis:true, ...Object.fromEntries([...SOURCES].map(source => {
    const id = switches[source];
    return [source, mapBindingStatus(states,id,source) === 'on'];
  }))};
}
// Stable backend contract, independent of entity IDs and translated names.
export function mapSwitchChoices(states={},source) {
  return Object.entries(states).filter(([id,state])=>id.startsWith('switch.') &&
    SOURCES.has(state?.attributes?.ignis_map_source) &&
    (!source || state.attributes.ignis_map_source===source))
    .map(([id,state])=>[id,String(state.attributes.friendly_name||id)])
    .sort((a,b)=>a[1].localeCompare(b[1])||a[0].localeCompare(b[0]));
}
const MONITORING_AREAS='terralyra_ignis_monitoring_areas';
export function hasMonitoringAreas(config) {
  return Boolean(config.show_all || config.geo_location_sources?.some(item=>(typeof item==='string'?item:item?.source)===MONITORING_AREAS));
}
// Review only IGNIS monitoring entities; inner alert circles are not extra places.
export function monitoringAreaReview(states, config) {
  if(!hasMonitoringAreas(config))return {status:'hidden',ready:0,unavailable:0};
  if(!states)return {status:'loading',ready:0,unavailable:0};
  const areas=Object.entries(states).filter(([id,state])=>id.startsWith('geo_location.') &&
    state?.attributes?.source===MONITORING_AREAS &&
    state.attributes.map_circle_meaning==='active_fire_monitoring_area');
  const ready=areas.filter(([,state])=>{
    const a=state.attributes;
    return !['unknown','unavailable'].includes(state.state) &&
      Number.isFinite(a.latitude)&&Math.abs(a.latitude)<=90 &&
      Number.isFinite(a.longitude)&&Math.abs(a.longitude)<=180 &&
      Number.isFinite(a.monitoring_radius_km)&&a.monitoring_radius_km>0 &&
      Number.isFinite(a.gps_accuracy)&&a.gps_accuracy>0;
  }).length;
  return {status:areas.length?(ready===areas.length?'ready':'partial'):'missing',ready,unavailable:areas.length-ready};
}
// Preserve all unrelated source options and native map settings.
export function withMonitoringAreas(config, enabled) {
  if(config.show_all)return {...config};
  const sources=[...(config.geo_location_sources||[])];
  if(enabled){
    if(!hasMonitoringAreas(config))sources.push({source:MONITORING_AREAS,label_mode:'icon',focus:false});
  } else {
    return {...config,geo_location_sources:sources.filter(item=>(typeof item==='string'?item:item?.source)!==MONITORING_AREAS)};
  }
  return {...config,geo_location_sources:sources,...(config.cluster===undefined?{cluster:false}:{})};
}
export function mapBindingStatus(states, id, source) {
  if(!id)return 'unbound';
  if(typeof id!=='string'||!id.startsWith('switch.'))return 'invalid';
  if(!states)return 'loading';
  if(!states[id])return 'missing';
  const declared=states[id].attributes?.ignis_map_source;
  if(source && declared!==undefined && declared!==source)return 'wrong_source';
  return ['on','off'].includes(states[id].state)?states[id].state:'unavailable';
}
// Setup guidance does not change runtime visibility or enable a source.
export function mapSetupStatus(states, id, source) {
  const status=mapBindingStatus(states,id,source);
  if(status!=='unbound')return status;
  if(!states)return 'loading';
  return mapSwitchChoices(states,source).length?'select_switch':'no_switch';
}
const WORDS = {
  en: {close:'Close', details:'Home Assistant details', source:'Source information',
    absent:'No incident text has been loaded for this report.',
    unavailable:'This report is no longer available in the current display.',
    warning:'Official source report, not a satellite detection. Current fire activity and complete coverage are not established.',
    location:'Distance reference', distance:'Distance', status:'Reported status',
    category:'Report category', updated:'Source status / update time', discovered:'Reported discovery time',
    created:'Source record creation time', received:'Last successful retrieval', response:'Retrieval status', unknown:'Not provided'},
  hu: {close:'Bezárás', details:'Home Assistant részletek', source:'Forrásadatok megnyitása',
    absent:'Ehhez a jelentéshez nincs betöltött eseményleírás.',
    unavailable:'Ez a jelentés már nem érhető el az aktuális megjelenítésben.',
    warning:'Hivatalos forrásjelentés, nem műholdas észlelés. A jelenlegi tűzaktivitás és a teljes lefedettség nem igazolt.',
    location:'Viszonyítási helyszín', distance:'Távolság', status:'Jelentett állapot',
    category:'Jelentés típusa', updated:'Forrás szerinti státusz / frissítés időpontja', discovered:'Jelentett felfedezés ideje',
    created:'Forrásrekord létrehozása', received:'Legutóbbi sikeres lekérés', response:'Lekérés állapota', unknown:'Nincs megadva'}
};

export function satelliteContextRequest(state) {
  const a=state?.attributes;
  if(a?.source !== 'terralyra_ignis' || typeof a.context_entry_id !== 'string' || typeof a.context_incident_id !== 'string') return null;
  return {config_entry_id:a.context_entry_id,incident_id:a.context_incident_id};
}

// Display observations, never infer ignition, extinction or official confirmation.
export function satelliteSummary(state, language='en') {
  const a=state?.attributes||{},hu=language.startsWith('hu'),unknown=hu?'Nincs adat':'Not provided';
  const date=value=>typeof value==='string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value))
    ?new Date(value).toLocaleString(hu?'hu-HU':'en-GB'):unknown;
  const finite=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0;
  const place=typeof a.nearest_settlement==='string'&&a.nearest_settlement.trim()?a.nearest_settlement:(hu?'Ismeretlen helyszín':'Unknown location');
  const providers=[...new Set((Array.isArray(a.source_observations)?a.source_observations.flatMap(o=>Array.isArray(o.providers)?o.providers:[]):[]).concat(Array.isArray(a.providers)?a.providers:[]).filter(p=>typeof p==='string'&&p.trim()))];
  return {title:`${place} · ${hu?'Tűzészlelés':'Fire detection'}`,
    distance:finite(a.distance_km)?`${a.distance_km.toLocaleString(hu?'hu-HU':'en-GB',{maximumFractionDigits:1})} km`:unknown,
    location:typeof a.location_name==='string'?a.location_name:null,direction:typeof a.direction==='string'?a.direction:null,
    first:date(a.first_seen),last:date(a.last_seen||a.acquired),providers,
    singleObservation:date(a.first_seen)!==unknown && date(a.last_seen||a.acquired)!==unknown && Date.parse(a.first_seen)===Date.parse(a.last_seen||a.acquired),
    multiple:providers.length>1,unavailable:['unknown','unavailable'].includes(state?.state),
    technical:[['Latitude',a.latitude],['Longitude',a.longitude],['FRP (MW)',finite(a.frp_mw)?a.frp_mw:null],['Pixels',finite(a.pixel_count)?a.pixel_count:null],['Satellites',Array.isArray(a.satellites)?a.satellites.join(', '):null]]
      .filter(([,value])=>value!==null&&value!==undefined).map(([key,value])=>[key,String(value)])};
}

export function safeLink(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

// Original source text only; absence must not promise a later article download.
export function reportDescription(attributes = {}, language = 'en') {
  const hu = language.startsWith('hu');
  const body = attributes.incident_text;
  const supplied = typeof body === 'string' && body.trim().length > 0;
  const messages = hu ? {
    not_in_feed:'Ez az adatfolyam eseményadatokat ad, szöveges leírásmezőt nem tartalmaz.',
    not_provided:'A forrás ennél az eseménynél nem adott meg leírást.',
    not_requested:'A tárolt jelentés nem tartalmaz lekért leírásmezőt. Ez nem jelenti azt, hogy a forrásnál nincs leírás.'
  } : {
    not_in_feed:'This feed supplies incident data without a narrative description field.',
    not_provided:'The source did not provide a description for this incident.',
    not_requested:'The stored report has no requested description field. This does not establish whether the source has a description.'
  };
  return {
    heading:hu ? 'Forrás szerinti leírás' : 'Source description',
    content:supplied ? body.slice(0,4000) :
      (Object.hasOwn(messages, attributes.incident_text_status) ? messages[attributes.incident_text_status] :
        (hu ? 'A leírás elérhetősége ennél a tárolt jelentésnél nem ismert.' : 'Description availability is unknown for this stored report.')),
    notice:supplied && body.length > 4000 ?
      (hu ? 'A megjelenített leírás rövidítve van.' : 'The displayed description has been shortened.') : null
  };
}

// Retrieval state is not a statement about the fire's activity or freshness.
export function retrievalView(attributes = {}, language = 'en') {
  const hu = language.startsWith('hu');
  const status = attributes.response_status;
  const source = attributes.source;
  const inpe = source === 'terralyra_ignis_inpe_reports';
  const tasalert = source === 'terralyra_ignis_tasalert_reports';
  const canada = source === 'terralyra_ignis_canada_reports';
  const nifc = source === 'terralyra_ignis_nifc_reports';
  const labels = {
    success:['Sikeres adatátvétel','Successful retrieval'],
    error:['Sikertelen lekérés','Retrieval failed'],
    accepted:['Sikeres adatátvétel','Successful retrieval'],
    not_modified:['A forrás nem változott','Source unchanged'],
    retrieval_failed:['Sikertelen lekérés','Retrieval failed'],
    empty_snapshot_review:['Üres forrásválasz; ellenőrzést igényel','Empty source response; review required'],
    unexpected_304:['Váratlan változatlansági válasz','Unexpected unchanged response'],
    invalid_snapshot:['Érvénytelen forrásválasz','Invalid source response'],
    replacement_review:['A változások ellenőrzést igényelnek','Changes require review'],
    not_requested:['Még nincs lekérés','Not yet requested'],
    initializing:['Inicializálás','Initializing'],
    never_fetched:['Még nincs sikeres lekérés','Not yet retrieved'],
    available:['Sikeres adatátvétel','Successful retrieval'],
    retrieved:['Sikeres adatátvétel','Successful retrieval'],
    rate_limited:['Lekérési korlátozás','Request rate limited'],
    unavailable:['Sikertelen lekérés','Retrieval failed'],
    invalid_response:['Érvénytelen forrásválasz','Invalid source response'],
    review_required:['Ellenőrzést igényel','Review required'],
    storage_error:['Tárolási hiba','Storage error'],
    restored_cooldown:['Visszaállított várakozási idő','Restored request cooldown'],
    persistence_review_required:['A tárolás ellenőrzést igényel','Storage review required'],
    refresh_failed_transient:['Átmeneti lekérési hiba','Temporary retrieval failure'],
    refresh_failed_rate_limited:['Lekérési korlátozás','Request rate limited'],
    refresh_failed_invalid_data:['Érvénytelen forrásválasz','Invalid source response'],
    refresh_failed_access_denied:['Hozzáférési hiba','Access denied']
  };
  const valid = inpe ? ['not_requested','success','error'] : tasalert ? ['not_requested','accepted','not_modified','retrieval_failed','empty_snapshot_review','unexpected_304','invalid_snapshot','replacement_review','review_required'] : canada ? ['not_requested','initializing','available','rate_limited','unavailable','invalid_response','review_required','storage_error'] :
    nifc ? ['not_requested','never_fetched','retrieved','restored_cooldown','persistence_review_required','refresh_failed_transient','refresh_failed_rate_limited','refresh_failed_invalid_data','refresh_failed_access_denied'] : [];
  const known = valid.includes(status);
  const success = (inpe && status === 'success') || (tasalert && ['accepted','not_modified'].includes(status)) || (canada && status === 'available') || (nifc && status === 'retrieved');
  const retained = known && !success && !['not_requested','initializing','never_fetched'].includes(status);
  return {
    label:known ? `${labels[status][hu ? 0 : 1]} (${status})` :
      (typeof status === 'string' && status.trim() ? `${hu ? 'Ismeretlen lekérési állapot' : 'Unknown retrieval status'} (${status.slice(0,200)})` : (hu ? 'Nincs megadva' : 'Not provided')),
    notice:retained ? (hu ? 'Megőrzött korábbi jelentés látható. A legutóbbi lekérési állapot nem igazolja az adat frissességét.' : 'A retained earlier report is displayed. The latest retrieval status does not establish its freshness.') : null
  };
}

export function reportView(state, language = 'en') {
  const a = state?.attributes;
  if (!state?.entity_id?.startsWith('geo_location.') || !SOURCES.has(a?.source)) return null;
  const lang = language.split('-')[0] === 'hu' ? 'hu' : 'en';
  const w = a.source === 'terralyra_ignis_inpe_reports' ? {...WORDS[lang], warning:lang === 'hu'
    ? 'INPE műholdas eredetű, előzetes eseménytermék. A jelölő közelítő középpont, nem tűzhatár. A geometria az előző nap adataira épül; a jelenlegi aktivitás és a teljes lefedettség nem igazolt. Nem független megerősítés más műholdas forrás mellett.'
    : 'Provisional INPE satellite-derived event product. Marker is a representative centroid, not a fire perimeter. Geometry is based on the previous day; current activity and complete coverage are not established. Not independent confirmation of other satellite sources.'} : WORDS[lang];
  const text = value => typeof value === 'string' && value ? value.slice(0, 4000) : w.unknown;
  const time = value => {
    // Never reinterpret a timezone-less source timestamp using browser timezone.
    if (typeof value !== 'string' || !/(Z|[+-]\d\d:\d\d)$/.test(value)) return w.unknown;
    const date = new Date(value);
    return Number.isNaN(date.valueOf()) ? w.unknown : date.toLocaleString(lang) + ' (' + value + ')';
  };
  const distance = Number(state.state);
  const incidentName = a.source === 'terralyra_ignis_nifc_reports'
    && typeof a.incident_name === 'string' ? a.incident_name.trim() : '';
  return {w, title:incidentName ? `NIFC · ${text(incidentName)}` : text(a.friendly_name), attribution:text(a.attribution),
    unavailable: ['unavailable','unknown'].includes(state.state),
    source:safeLink(a.source_url), license:safeLink(a.license_url), licenseLabel:a.source === 'terralyra_ignis_inpe_reports' ? 'CC BY-SA 4.0' : 'CC BY 4.0', transformation:text(a.transformation),
    retrievalNotice:retrievalView(a,language).notice,
    rows:[
      [w.location,text(a.distance_reference_name)],
      [w.distance,Number.isFinite(distance) && state.state.trim() !== '' ? `${distance} ${text(a.unit_of_measurement)}` : w.unknown],
      [w.status,text(a.source_status || a.stage_of_control)],
      [w.category,text(a.report_category || a.prescribed_status)],
      [w.updated,time(a.source_times?.status_date || a.source_modified_at)],
      ...(a.source === 'terralyra_ignis_tasalert_reports' ? [[w.created,time(a.source_created_at)]] : [[w.discovered,time(a.source_discovered_at)]]),
      [w.received,time(a.last_success_at)],
      [w.response,retrievalView(a,language).label]
    ]};
}

export function reportAge(state, now = Date.now()) {
  const a = state?.attributes || {};
  const stamp = a.source_times?.status_date || a.source_modified_at;
  if (typeof stamp !== 'string' || !/(Z|[+-]\d\d:\d\d)$/.test(stamp)) return null;
  const age = (now - Date.parse(stamp)) / 86400000;
  return Number.isFinite(age) && age >= 0 ? age : null;
}

export function reportAgeLabel(state, language = 'en', now = Date.now()) {
  const hu = language.startsWith('hu');
  const a = state?.attributes || {};
  const stamp = a.source_times?.status_date || a.source_modified_at;
  if (stamp === undefined || stamp === null || stamp === '') {
    return hu ? 'A forrás nem ad meg frissítési időpontot; a jelentés kora nem állapítható meg.'
      : 'The source does not provide an update time; the report age cannot be determined.';
  }
  if (typeof stamp !== 'string' || !/(Z|[+-]\d\d:\d\d)$/.test(stamp) || !Number.isFinite(Date.parse(stamp))) {
    return hu ? 'A forrás frissítési időpontja nem értelmezhető; a jelentés kora nem állapítható meg.'
      : 'The source update time cannot be interpreted; the report age cannot be determined.';
  }
  const age = reportAge(state, now);
  if (age === null) {
    return hu ? 'A forrás frissítési időpontja a jövőben van; a jelentés kora nem állapítható meg.'
      : 'The source update time is in the future; the report age cannot be determined.';
  }
  return hu ? `Jelentés kora: ${Math.floor(age)} nap (forrás szerinti frissítés)`
    : `Report age: ${Math.floor(age)} days (source update)`;
}

export function filterMapStates(states, enabled, maxDays, now = Date.now()) {
  return Object.fromEntries(Object.entries(states).filter(([, state]) => {
    const source = state.attributes?.source;
    if (Object.hasOwn(enabled, source) && !enabled[source]) return false;
    if (!SOURCES.has(source) || !maxDays) return true;
    const age = reportAge(state, now);
    // Unknown/future timestamps remain visible rather than silently disappearing.
    return age === null || age <= maxDays;
  }));
}

// Guard permits dependency-free model tests in Node without a browser DOM.
if (typeof customElements !== 'undefined' && !customElements.get('ignis-report-map')) {
  class IgnisReportMapEditor extends HTMLElement {
    setConfig(config){this.config={...config};this.render();}
    set hass(value){
      this._hass=value;
      const signature=JSON.stringify([value?.language,[...SOURCES].map(source=>[source,this.choices(source)])]);
      if(signature!==this.signature){this.signature=signature;this.render();}else this.renderStatus();
    }
    choices(source){return mapSwitchChoices(this._hass?.states,source);}
    node(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;}
    update(patch){this.config={...this.config,...patch};this.renderStatus();this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:this.config},bubbles:true,composed:true}));}
    renderStatus(){
      if(!this.statusHost)return;
      const hu=this._hass?.language?.startsWith('hu');
      const messages=hu?{
        wrong_source:'A kapcsoló másik forráshoz tartozik; válaszd ki a megfelelő kapcsolót. A riportvezérlő rejtve marad.',
        select_switch:'Van választható IGNIS kapcsoló. Ha szeretnéd ezt a forrást megjeleníteni, válaszd ki fent.',
        no_switch:'Nem található ehhez a forráshoz IGNIS térképkapcsoló. Ha szükséged van rá, ellenőrizd a forrás engedélyezését és az entitásokat az integráció beállításaiban. A forrás használata nem kötelező.',
        invalid:'Kapcsolóentitást válassz; a jelenlegi hozzárendelés nem használható.',
        loading:'Várakozás a Home Assistant állapotadataira.',
        missing:'A hozzárendelt kapcsoló nem található. Ellenőrizd a kiválasztást.',
        unavailable:'A kapcsoló állapota nem elérhető; a riportvezérlő rejtve marad.',
        off:'A térképkapcsoló ki van kapcsolva; a riportvezérlő rejtve marad.',
        on:'A térképkapcsoló be van kapcsolva. Ez nem igazolja friss riportok meglétét.'
      }:{
        wrong_source:'The switch belongs to a different source; select the matching switch. The report control stays hidden.',
        select_switch:'An IGNIS switch is available. Select it above if you want to display this source.',
        no_switch:'No IGNIS map switch was found for this source. If needed, check source enablement and entities in the integration settings. This source is optional.',
        invalid:'Select a switch entity; the current binding cannot be used.',
        loading:'Waiting for Home Assistant state data.',
        missing:'The bound switch was not found. Check the selection.',
        unavailable:'Switch state unavailable; the report control stays hidden.',
        off:'The map switch is off; the report control stays hidden.',
        on:'The map switch is on. This does not establish that fresh reports exist.'
      };
      this.statusHost.replaceChildren(this.node('h3',hu?'Hozzárendelések állapota':'Binding status'));
      const areas=monitoringAreaReview(this._hass?.states,this.config);
      const areaMessages=hu?{
        hidden:'A megfigyelési körök megjelenítése nincs bekapcsolva ezen a kártyán.',
        loading:'A megfigyelési körök ellenőrzése az állapotadatokra vár.',
        missing:'Még nincs elérhető IGNIS megfigyelési terület. Ellenőrizd a helyszíneket és a területentitásokat az integráció beállításaiban.',
        ready:`${areas.ready} megfigyelt helyszín köradata elérhető. A tényleges megjelenést a térkép szűrése és csoportosítása is befolyásolja.`,
        partial:`${areas.ready} helyszín köradata elérhető, ${areas.unavailable} terület adata hiányos vagy nem elérhető. Ellenőrizd az integráció területentitásait.`
      }:{
        hidden:'Monitoring circles are not enabled on this card.',
        loading:'Waiting for state data to check monitoring circles.',
        missing:'No IGNIS monitoring area is available yet. Check locations and area entities in the integration settings.',
        ready:`Circle data is available for ${areas.ready} monitored locations. Map filters and clustering also affect actual visibility.`,
        partial:`Circle data is available for ${areas.ready} locations; ${areas.unavailable} areas have incomplete or unavailable data. Check the integration area entities.`
      };
      this.statusHost.append(this.node('p',areaMessages[areas.status]));
      for(const [source,name] of [['terralyra_ignis_canada_reports','Canada'],['terralyra_ignis_nifc_reports','NIFC'],['terralyra_ignis_tasalert_reports','TasALERT'],['terralyra_ignis_inpe_reports','INPE']])this.statusHost.append(this.node('p',name+': '+messages[mapSetupStatus(this._hass?.states,this.config.report_switches?.[source],source)]));
    }
    render(){
      if(!this.config)return;
      if(!this.shadowRoot)this.attachShadow({mode:'open'});
      const root=this.shadowRoot;root.replaceChildren();
      const hu=this._hass?.language?.startsWith('hu');
      root.append(this.node('style',`:host{display:block;color:var(--primary-text-color);overflow-wrap:anywhere}label{display:block;margin:16px 0}input,select{box-sizing:border-box;width:100%;min-width:0;padding:12px;margin-top:8px;font:inherit;color:inherit;background:var(--card-background-color,white);border:1px solid var(--divider-color,#999);border-radius:8px}p{line-height:1.5}`));
      const help=this.node('nav');help.setAttribute('aria-label',hu?'Beállítási segítség':'Setup help');
      for(const [caption,url] of [
        [hu?'Helyszínek és adatforrások beállítása':'Configure locations and sources','/config/integrations/integration/terralyra_ignis'],
        [hu?'Első lépések útmutató':'First setup guide','https://github.com/TerraLyra/ha-terralyra-ignis/blob/main/docs/FIRST_STEPS.md'+(hu?'#magyar':'#english')]
      ]){
        const link=this.node('a',caption);link.href=url;link.target='_blank';link.rel='noopener noreferrer';link.style.color='var(--primary-color,#007a8a)';
        const line=this.node('p');line.append(link);help.append(line);
      }
      root.append(help);
      const titleText=hu?'Térkép címe (nem kötelező)':'Map title (optional)';
      const label=this.node('label',titleText),input=this.node('input');input.type='text';input.value=this.config.title||'';input.setAttribute('aria-label',titleText);input.onchange=()=>this.update({title:input.value});label.append(input);root.append(label);
      root.append(this.node('p',hu?'Válaszd ki az adott forrás IGNIS térképes megjelenítési kapcsolóját. Ez csak hozzárendelés: nem engedélyez adatforrást, és nem kapcsol át entitást.':'Select each source’s IGNIS map visibility switch. This only creates a binding: it does not enable a provider or toggle an entity.'));
      for(const [source,name] of [['terralyra_ignis_canada_reports','Canada'],['terralyra_ignis_nifc_reports','NIFC'],['terralyra_ignis_tasalert_reports','TasALERT'],['terralyra_ignis_inpe_reports','INPE']]){
        const caption=name+(hu?' térképkapcsoló':' map switch'),label=this.node('label',caption),select=this.node('select');select.setAttribute('aria-label',caption);
        const empty=this.node('option',hu?'Nincs hozzárendelés':'No binding');empty.value='';select.append(empty);
        const choices=this.choices(source),current=this.config.report_switches?.[source]||'';
        for(const [id,name] of choices){const option=this.node('option',`${name} — ${id}`);option.value=id;select.append(option);}
        if(current&&!choices.some(([id])=>id===current)){const option=this.node('option',(hu?'Megőrzött, ellenőrizendő: ':'Saved; check binding: ')+current);option.value=current;select.append(option);}
        select.value=current;select.onchange=()=>{const bindings={...this.config.report_switches};if(select.value)bindings[source]=select.value;else delete bindings[source];this.update({report_switches:bindings});};label.append(select);root.append(label);
      }
      for(const [key,caption,options] of [
        ['aspect_ratio',hu?'Térkép képaránya':'Map aspect ratio',[
          ['',hu?'Alapértelmezett':'Default'],['16:9',hu?'Széles (16:9)':'Wide (16:9)'],['4:3','4:3'],['1:1',hu?'Négyzet (1:1)':'Square (1:1)']]],
        ['scale_ruler',hu?'Méretarány-vonalzó':'Scale ruler',[
          ['',hu?'Alapértelmezett':'Default'],['true',hu?'Bekapcsolva':'On'],['false',hu?'Kikapcsolva':'Off']]]
      ]){
        const label=this.node('label',caption),select=this.node('select');select.setAttribute('aria-label',caption);
        const current=this.config[key]===undefined?'':String(this.config[key]);
        for(const [value,title] of options){const option=this.node('option',title);option.value=value;select.append(option);}
        if(!options.some(([value])=>value===current)){
          const option=this.node('option',(hu?'Egyedi, megőrzött: ':'Custom, preserved: ')+current);option.value=current;select.append(option);
        }
        select.value=current;
        select.onchange=()=>{
          const next={...this.config};
          if(select.value==='')delete next[key];
          else next[key]=key==='scale_ruler'?select.value==='true':select.value;
          this.config=next;this.update({});
        };
        label.append(select);root.append(label);
      }
      root.append(this.node('p',hu?'A képarány a kártya alakját szabályozza; szakaszos dashboardon az Elrendezés beállítása is befolyásolhatja a méretét. A vonalzó a térkép aktuális léptékét mutatja.':'Aspect ratio controls the card shape; on a sections dashboard, Layout settings can also affect its size. The ruler shows the current map scale.'));
      const clusterCaption=hu?'Jelölők csoportosítása':'Marker clustering';
      const clusterLabel=this.node('label',clusterCaption),clusterSelect=this.node('select');clusterSelect.setAttribute('aria-label',clusterCaption);
      for(const [value,caption] of [['default',hu?'Alapértelmezett':'Default'],['on',hu?'Bekapcsolva':'On'],['off',hu?'Kikapcsolva':'Off']]){
        const option=this.node('option',caption);option.value=value;clusterSelect.append(option);
      }
      clusterSelect.value=this.config.cluster===true?'on':this.config.cluster===false?'off':'default';
      clusterSelect.onchange=()=>{
        if(clusterSelect.value==='default'){
          const next={...this.config};delete next.cluster;this.config=next;this.update({});
        }else this.update({cluster:clusterSelect.value==='on'});
        this.render();
      };
      clusterLabel.append(clusterSelect);root.append(clusterLabel);
      const circlesLabel=this.node('label',hu?'Megfigyelési és riasztási körök':'Monitoring and alert circles'),circles=this.node('input');
      circles.type='checkbox';circles.style.cssText='width:auto;margin-right:8px';circles.checked=hasMonitoringAreas(this.config);circles.disabled=Boolean(this.config.show_all);
      circles.setAttribute('aria-label',hu?'Megfigyelési és riasztási körök':'Monitoring and alert circles');
      circles.onchange=()=>{this.update(withMonitoringAreas(this.config,circles.checked));this.render();};circlesLabel.prepend(circles);root.append(circlesLabel);
      root.append(this.node('p',hu?'A körök a megfigyelt helyszínek beállított sugarait mutatják. Egyenlő sugaraknál egy kör jelenik meg. Nem a tűz kiterjedését jelölik.':'Circles show the configured radii of monitored locations. Equal radii use one circle. They do not represent fire perimeters.'));
      if(this.config.show_all)root.append(this.node('p',hu?'Az összes entitás megjelenítése aktív; a körök külön szűréséhez előbb kapcsold ki a show_all beállítást a kódszerkesztőben.':'Show all entities is active; turn off show_all in the code editor before filtering circles separately.'));
      if(this.config.cluster===true)root.append(this.node('p',hu?'A jelölők csoportosítása aktív; a köröket elrejtheti. A körök láthatóságához válaszd a Kikapcsolva lehetőséget.':'Marker clustering is active and may hide circles. Choose Off to keep circle centres separate.'));
      this.statusHost=this.node('section');this.statusHost.setAttribute('aria-live','polite');root.append(this.statusHost);this.renderStatus();
      root.append(this.node('p',hu?'A hozzárendelés nélküli vagy kikapcsolt riportforrás vezérlője rejtve marad. Az egyéb haladó térképbeállítások a kódszerkesztőben módosíthatók; a meglévő értékeket megőrizzük.':'Report controls stay hidden without a binding or when their switch is off. Other advanced map options remain available in the code editor; existing values are preserved.'));
    }
  }
  customElements.define('ignis-report-map-editor',IgnisReportMapEditor);
  class IgnisReportMap extends HTMLElement {
    static getConfigElement(){return document.createElement('ignis-report-map-editor');}
    static getStubConfig(){return withMonitoringAreas({type:'custom:ignis-report-map'},true);}

    constructor() {
      super();
      this.attachShadow({mode:'open'});
      const style = document.createElement('style');
      style.textContent = `:host{display:block}dialog{box-sizing:border-box;width:min(640px,calc(100vw - 24px));max-height:85dvh;overflow:auto;border:0;border-radius:20px;padding:24px;background:var(--card-background-color,#fff);color:var(--primary-text-color,#172b39);font:inherit}dialog::backdrop{background:#0008}.satellite-summary header{padding:18px;border-radius:14px;background:var(--secondary-background-color,#eef5f6);border-left:4px solid var(--primary-color,#007f91)}.satellite-summary header>span{font-size:.72rem;letter-spacing:.12em;color:var(--secondary-text-color)}.satellite-summary h2{margin:10px 0}.satellite-summary section{padding:12px 0;border-bottom:1px solid var(--divider-color,#ddd)}.satellite-summary h3{font-size:1rem}.satellite-summary small{color:var(--secondary-text-color);line-height:1.5;display:block}.satellite-summary details{padding-top:20px}.satellite-summary summary{cursor:pointer;font-weight:600}.sat-close{margin-bottom:14px}h2{font-size:1.3rem;overflow-wrap:anywhere}p{line-height:1.5}dl{display:grid;grid-template-columns:1fr 1fr;gap:14px}dt{color:var(--secondary-text-color,#596975)}dd{margin:0;overflow-wrap:anywhere}button,a{font:inherit;padding:10px;color:var(--primary-color,#007f91)}button{cursor:pointer;background:transparent;border:1px solid currentColor;border-radius:8px}footer{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px}@media(max-width:440px){dl{grid-template-columns:1fr;gap:6px}dd{margin-bottom:12px}}`;
      this.enabled = {terralyra_ignis:true, terralyra_ignis_canada_reports:true, terralyra_ignis_nifc_reports:true, terralyra_ignis_tasalert_reports:true, terralyra_ignis_inpe_reports:true};
      this.maxDays = 0;
      this.controls = document.createElement('div');
      this.controls.style.cssText='display:flex;flex-wrap:wrap;gap:12px;padding:12px;background:var(--card-background-color,#fff)';
      this.mapHost = document.createElement('div');
      this.dialog = document.createElement('dialog');
      this.dialog.setAttribute('aria-labelledby','report-title');
      this.shadowRoot.append(style,this.controls,this.mapHost,this.dialog);
      this.mapHost.addEventListener('hass-more-info', event => {
        const id = event.detail?.entityId;
        const context=satelliteContextRequest(this._hass?.states[id]);
        if (!context && !reportView(this._hass?.states[id],this._hass?.language)) return;
        event.stopPropagation();
        delete this.dialog.dataset.satelliteId;
        this.selected = id;
        this.satelliteResult = null;
        if(context) this.loadSatelliteContext(id,context);
        this.renderReport();
        this.dialog.showModal();
      });
      // A queued close event may arrive after another report has opened.
      this.dialog.addEventListener('close',()=>{if (!this.dialog.open) this.selected = null;});
    }
    setConfig(config) {
      this.config = {...config, type:'map'};
      const sources = config.geo_location_sources || [];
      this.config.geo_location_sources = [...sources];
      for (const source of config.show_all ? [] : Object.keys(this.enabled)) {
        if (!sources.some(item => (typeof item === 'string' ? item : item.source) === source)) this.config.geo_location_sources.push(source);
      }
      if (config.show_all) delete this.config.geo_location_sources;
      this.renderControls();
      this.buildMap();
    }
    async buildMap() {
      const config = this.config;
      const attempt = this.mapAttempt = (this.mapAttempt || 0) + 1;
      try {
        const helpers = await window.loadCardHelpers();
        if (config !== this.config || attempt !== this.mapAttempt) return;
        this.map = helpers.createCardElement(config);
        this.updateMap();
        this.mapHost.replaceChildren(this.map);
      } catch {
        if (config !== this.config || attempt !== this.mapAttempt) return;
        const hu = this._hass?.language?.startsWith('hu');
        const message = document.createElement('p');
        message.setAttribute('role','status');
        message.textContent = hu
          ? 'A térkép nem tölthető be. Próbáld újra; ha továbbra sem sikerül, töltsd újra a böngészőt.'
          : 'The map could not be loaded. Try again; if it still fails, reload the browser.';
        const retry = document.createElement('button');
        retry.type = 'button';
        retry.textContent = hu ? 'Újrapróbálás' : 'Try again';
        retry.addEventListener('click', () => {
          retry.disabled = true;
          message.textContent = hu ? 'Térkép betöltése…' : 'Loading map…';
          void this.buildMap();
        });
        this.mapHost.replaceChildren(message,retry);
      }
    }
    set hass(value) {
      this._hass = value;
      this.renderControls();
      this.updateMap();
      if (this.selected) {
        const next = value.states[this.selected];
        if (next !== this.selectedState) this.renderReport();
      }
    }
    renderControls() {
      const hu = this._hass?.language?.startsWith('hu');
      const visibility = visibleMapSources(this._hass?.states, this.config?.report_switches);
      const key = JSON.stringify([hu, visibility]);
      if (this.controlsKey === key) return;
      this.controlsKey = key;
      this.controls.replaceChildren();
      const labels = hu ? ['Műholdas észlelések','Kanadai jelentések','NIFC jelentések','TasALERT jelentések','INPE események'] : ['Satellite detections','Canada reports','NIFC reports','TasALERT reports','INPE events'];
      Object.keys(this.enabled).forEach((source,index)=>{
        if (!visibility[source]) return;
        const label=document.createElement('label');
        const input=document.createElement('input');input.type='checkbox';input.checked=this.enabled[source];
        input.onchange=()=>{this.enabled[source]=input.checked;this.updateMap();};
        label.append(input,document.createTextNode(labels[index]));this.controls.append(label);
      });
      if (![...SOURCES].some(source=>visibility[source])) return;
      const label=document.createElement('label');
      label.append(document.createTextNode(hu ? 'Jelentés frissítése: ' : 'Report updated: '));
      const select=document.createElement('select');
      for (const days of [0,1,7,30]) {
        const option=document.createElement('option');option.value=days;
        option.textContent=days ? (hu ? `Legfeljebb ${days} napja` : `Within ${days} ${days === 1 ? 'day' : 'days'}`) : (hu ? 'Bármikor' : 'Any time');
        select.append(option);
      }
      select.value=this.maxDays;
      select.onchange=()=>{this.maxDays=Number(select.value);this.updateMap();};
      label.append(select);this.controls.append(label);
      const note=document.createElement('small');
      note.textContent=hu ? 'Az ismeretlen idejű jelentések láthatók maradnak. A szűrés csak a megjelenítést érinti.' : 'Reports with unknown times remain visible. Filters affect display only.';
      this.controls.append(note);
    }
    updateMap() {
      if (this.map && this._hass) this.map.hass = {...this._hass,states:filterMapStates(this._hass.states,Object.fromEntries(Object.entries(this.enabled).map(([source, checked]) => [source, checked && visibleMapSources(this._hass.states,this.config?.report_switches)[source]])),this.maxDays)};
    }
    getCardSize() {return this.map?.getCardSize?.() ?? 7;}
    disconnectedCallback() {if(this.dialog.open) this.dialog.close();}
    async loadSatelliteContext(id, data) {
      const token={}; this.contextToken=token;
      try {
        const response=await this._hass.callWS({type:'call_service',domain:'terralyra_ignis',service:'get_satellite_report_context',service_data:data,return_response:true});
        if(this.selected!==id || this.contextToken!==token)return;
        this.satelliteResult=response.response || {reports:[]};
      } catch {
        if(this.selected!==id || this.contextToken!==token)return;
        this.satelliteResult={error:true};
      }
      this.renderReport();
    }
    renderSatellite(state) {
      this.selectedState=state;
      const hu=this._hass.language?.startsWith('hu'),v=satelliteSummary(state,this._hass.language||'en');
      const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
      const sameIncident=this.dialog.dataset.satelliteId===this.selected;
      const expandedKeys=new Set(sameIncident?Array.from(this.dialog.querySelectorAll('details[open]')).map(n=>n.dataset.expandKey):[]);
      const focused=sameIncident?this.shadowRoot.activeElement?.dataset.focusKey:null;
      const scrollTop=sameIncident?this.dialog.scrollTop:0;
      const close=el('button',hu?'Bezárás':'Close');close.onclick=()=>this.dialog.close();close.className='sat-close';close.dataset.focusKey='close';
      const heading=el('h2',v.title);heading.id='report-title';
      const card=el('article');card.className='satellite-summary';
      const header=el('header');header.append(el('span',hu?'MŰHOLDAS ÉSZLELÉS':'SATELLITE OBSERVATION'),heading);
      header.append(el('p',[v.distance,v.direction,v.location].filter(Boolean).join(' · ')));
      card.append(header);
      const section=(title)=>{const n=el('section');n.append(el('h3',title));card.append(n);return n;};
      const times=section(hu?'◷ Észlelési időszak':'◷ Observation period');
      const clocks=el('dl');
      if(v.singleObservation)clocks.append(el('dt',hu?'Észlelés időpontja':'Observation time'),el('dd',v.first));
      else clocks.append(el('dt',hu?'Első észlelés':'First observation'),el('dd',v.first),el('dt',hu?'Legutóbbi észlelés':'Latest observation'),el('dd',v.last));times.append(clocks);
      times.append(el('small',hu?'Észlelési időpontok, nem a tűz keletkezésének vagy eloltásának ideje.':'Observation times, not ignition or extinction times.'));
      if(v.unavailable)times.append(el('p',hu?'Az észlelés adatai jelenleg nem érhetők el.':'Observation data is currently unavailable.'));
      const news=section(hu?'▤ Kapcsolódó hír':'▤ Related report'),result=this.satelliteResult;
      if(!result||result.error)news.append(el('p',hu?(!result?'Kapcsolódó hírek ellenőrzése…':'A kapcsolódó hírek most nem ellenőrizhetők.'):(!result?'Checking related reports…':'Related reports could not be checked.')));
      else if(!result.reports?.length)news.append(el('p',hu?'A helyben tárolt hírek között nem találtunk kapcsolódó BM-hírt.':'No related BM report was found in the local archive.'));
      for(const report of result?.reports || []) {
        news.append(el('span',hu?'Valószínűleg kapcsolódó BM-hír':'Probably related BM report'),el('h4',report.title));
        const content=typeof report.description==='string'?report.description.slice(0,4000):'';
        const body=el('p',content.length>280?content.slice(0,280)+'…':content);body.style.whiteSpace='pre-wrap';news.append(body);
        if(content.length>280){const full=el('details');full.dataset.expandKey=`news:${report.report_url||report.title}`;full.open=expandedKeys.has(full.dataset.expandKey);const summary=el('summary',hu?'Teljes hírszöveg':'Full report text');summary.dataset.focusKey=full.dataset.expandKey;const text=el('p',content);text.style.whiteSpace='pre-wrap';full.append(summary,text);news.append(full);}
        news.append(el('small',`BM OKF · ${report.published_at}`));
        if(report.ambiguous)news.append(el('p',hu?'Több műholdas észleléshez is illeszkedhet.':'May relate to multiple satellite observations.'));
        const url=safeLink(report.report_url);if(url){const link=el('a',hu?'Eredeti hír':'Original report');link.href=url;link.target='_blank';link.rel='noopener noreferrer';link.dataset.focusKey=`report:${url}`;news.append(link);}
      }
      const sources=section(hu?'⌁ Észlelő források':'⌁ Observing sources');
      sources.append(el('p',v.multiple?(hu?'Több forrás észlelése · valószínűleg ugyanaz az esemény':'Multiple sources · probably the same event'):(hu?'Több forrás egyezése nem igazolt.':'Agreement between multiple sources is not established.')));
      sources.append(el('p',state.attributes.provider_attribution||v.providers.join(' · ')||(hu?'Nincs forrásadat':'No source information')));
      sources.append(el('small',hu?'A műholdas egyezés nem hivatalos megerősítés. A források időpontjai eltérhetnek.':'Satellite agreement is not official confirmation. Source observation times may differ.'));
      const technical=el('details');technical.dataset.expandKey='technical';technical.open=expandedKeys.has('technical');const toggle=el('summary',hu?'Technikai részletek':'Technical details');toggle.dataset.focusKey='technical';technical.append(toggle);
      const list=el('dl');for(const [key,value] of v.technical)list.append(el('dt',hu?({Latitude:'Szélesség',Longitude:'Hosszúság',Pixels:'Pixelszám',Satellites:'Műholdak'}[key]||key):key),el('dd',value));technical.append(list);
      technical.append(el('small',hu?'Az FRP sugárzási teljesítmény; a pixelszám nem a tűz területe.':'FRP is radiative power; pixel count is not fire area.'));
      for(const o of state.attributes.source_observations||[])technical.append(el('p',`${o.provider_attribution||(o.providers||[]).join(', ')} · ${o.acquired||'—'} · ${o.evidence_role||'—'}`));
      card.append(technical);
      const footer=el('footer'),details=el('button',hu?'Home Assistant részletek':'Home Assistant details');
      details.dataset.focusKey='native-details';
      details.onclick=()=>{const entityId=this.selected;this.dialog.close();this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId},bubbles:true,composed:true}));};footer.append(details);card.append(footer);
      this.dialog.replaceChildren(close,card);
      this.dialog.dataset.satelliteId=this.selected;
      if(focused)Array.from(this.dialog.querySelectorAll('[data-focus-key]')).find(n=>n.dataset.focusKey===focused)?.focus({preventScroll:true});
      this.dialog.scrollTop=scrollTop;
    }
    renderReport() {
      if(satelliteContextRequest(this._hass?.states[this.selected])) {this.renderSatellite(this._hass.states[this.selected]);return;}
      const state = this._hass.states[this.selected];
      this.selectedState = state;
      const view = reportView(state,this._hass.language);
      const w = view?.w || WORDS[this._hass.language?.startsWith('hu') ? 'hu' : 'en'];
      const focused = this.shadowRoot.activeElement?.dataset?.action;
      const element = (tag,text) => {const el=document.createElement(tag);el.textContent=text;return el;};
      const close = element('button',w.close);
      close.dataset.action='close';
      close.onclick=()=>this.dialog.close();
      const heading=element('h2',view?.title || w.unavailable);
      heading.id='report-title';
      this.dialog.replaceChildren(close,heading);
      if (!view || view.unavailable) {this.dialog.append(element('p',w.unavailable));return;}
      const description = reportDescription(state.attributes,this._hass.language || 'en');
      const paragraph=element('p',description.content);paragraph.style.whiteSpace='pre-wrap';
      const inpe=state.attributes.source==='terralyra_ignis_inpe_reports';
      if(inpe){const keyFacts=element('dl','');for(const [label,value] of view.rows.slice(0,4))keyFacts.append(element('dt',label),element('dd',value));this.dialog.append(keyFacts);}
      this.dialog.append(element('p',view.attribution));
      if(!inpe || (typeof state.attributes.incident_text==='string' && state.attributes.incident_text.trim()))this.dialog.append(element('h3',description.heading));
      this.dialog.append(paragraph);
      if(description.notice) this.dialog.append(element('p',description.notice));
      if(view.retrievalNotice) this.dialog.append(element('p',view.retrievalNotice));
      this.dialog.append(element('p',reportAgeLabel(state,this._hass.language || 'en')));
      const list=document.createElement('dl');
      for(const [label,value] of (inpe?view.rows.slice(4):view.rows)) list.append(element('dt',label),element('dd',value));
      this.dialog.append(list,element('p',w.warning));
      const footer=document.createElement('footer');
      if(view.source) {
        const link=element('a',w.source);
        link.href=view.source;link.target='_blank';link.rel='noopener noreferrer';link.dataset.action='source';
        footer.append(link);
      }
      if(view.license){const link=element('a',view.licenseLabel);link.href=view.license;link.target='_blank';link.rel='noopener noreferrer';footer.append(link);this.dialog.append(element('p',view.transformation));}
      const details=element('button',w.details);
      details.dataset.action='details';
      details.onclick=()=>{
        const entityId=this.selected;
        this.dialog.close();
        this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId},bubbles:true,composed:true}));
      };
      footer.append(details);this.dialog.append(footer);
      if(focused) this.dialog.querySelector(`[data-action="${focused}"]`)?.focus();
    }
  }
  customElements.define('ignis-report-map',IgnisReportMap);
  window.customCards=window.customCards || [];
  window.customCards.push({type:'ignis-report-map',name:'IGNIS report map',description:'Map with readable official report details, including TasALERT.'});
}
