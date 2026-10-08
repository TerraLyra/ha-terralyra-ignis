// Optional local dashboard resource. No external libraries or report-page requests.
const SOURCES = new Set(['terralyra_ignis_canada_reports', 'terralyra_ignis_nifc_reports']);
// Explicit map-switch entity associations; never infer opt-in from report count.
export function visibleMapSources(states = {}, switches = {}) {
  return {terralyra_ignis:true, ...Object.fromEntries([...SOURCES].map(source => {
    const id = switches[source];
    return [source, typeof id === 'string' && id.startsWith('switch.') && states[id]?.state === 'on'];
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
export function mapBindingStatus(states, id) {
  if(!id)return 'unbound';
  if(typeof id!=='string'||!id.startsWith('switch.'))return 'invalid';
  if(!states)return 'loading';
  if(!states[id])return 'missing';
  return ['on','off'].includes(states[id].state)?states[id].state:'unavailable';
}
const WORDS = {
  en: {close:'Close', details:'Home Assistant details', source:'Source information',
    absent:'No incident text has been loaded for this report.',
    unavailable:'This report is no longer available in the current display.',
    warning:'Official source report, not a satellite detection. Current fire activity and complete coverage are not established.',
    location:'Distance reference', distance:'Distance', status:'Reported status',
    category:'Report category', updated:'Source status / update time', discovered:'Reported discovery time',
    received:'Last successful retrieval', response:'Retrieval status', unknown:'Not provided'},
  hu: {close:'Bezárás', details:'Home Assistant részletek', source:'Forrásadatok megnyitása',
    absent:'Ehhez a jelentéshez nincs betöltött eseményleírás.',
    unavailable:'Ez a jelentés már nem érhető el az aktuális megjelenítésben.',
    warning:'Hivatalos forrásjelentés, nem műholdas észlelés. A jelenlegi tűzaktivitás és a teljes lefedettség nem igazolt.',
    location:'Viszonyítási helyszín', distance:'Távolság', status:'Jelentett állapot',
    category:'Jelentés típusa', updated:'Forrás szerinti státusz / frissítés időpontja', discovered:'Jelentett felfedezés ideje',
    received:'Legutóbbi sikeres lekérés', response:'Lekérés állapota', unknown:'Nincs megadva'}
};

export function satelliteContextRequest(state) {
  const a=state?.attributes;
  if(a?.source !== 'terralyra_ignis' || typeof a.context_entry_id !== 'string' || typeof a.context_incident_id !== 'string') return null;
  return {config_entry_id:a.context_entry_id,incident_id:a.context_incident_id};
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
  const canada = source === 'terralyra_ignis_canada_reports';
  const nifc = source === 'terralyra_ignis_nifc_reports';
  const labels = {
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
  const valid = canada ? ['not_requested','initializing','available','rate_limited','unavailable','invalid_response','review_required','storage_error'] :
    nifc ? ['not_requested','never_fetched','retrieved','restored_cooldown','persistence_review_required','refresh_failed_transient','refresh_failed_rate_limited','refresh_failed_invalid_data','refresh_failed_access_denied'] : [];
  const known = valid.includes(status);
  const success = (canada && status === 'available') || (nifc && status === 'retrieved');
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
  const w = WORDS[lang];
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
    source:safeLink(a.source_url),
    retrievalNotice:retrievalView(a,language).notice,
    rows:[
      [w.location,text(a.distance_reference_name)],
      [w.distance,Number.isFinite(distance) && state.state.trim() !== '' ? `${distance} ${text(a.unit_of_measurement)}` : w.unknown],
      [w.status,text(a.source_status || a.stage_of_control)],
      [w.category,text(a.report_category || a.prescribed_status)],
      [w.updated,time(a.source_times?.status_date || a.source_modified_at)],
      [w.discovered,time(a.source_discovered_at)],
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
        unbound:'Nincs hozzárendelés; a riportvezérlő rejtve marad.',
        invalid:'Kapcsolóentitást válassz; a jelenlegi hozzárendelés nem használható.',
        loading:'Várakozás a Home Assistant állapotadataira.',
        missing:'A hozzárendelt kapcsoló nem található. Ellenőrizd a kiválasztást.',
        unavailable:'A kapcsoló állapota nem elérhető; a riportvezérlő rejtve marad.',
        off:'A térképkapcsoló ki van kapcsolva; a riportvezérlő rejtve marad.',
        on:'A térképkapcsoló be van kapcsolva. Ez nem igazolja friss riportok meglétét.'
      }:{
        unbound:'No binding; the report control stays hidden.',
        invalid:'Select a switch entity; the current binding cannot be used.',
        loading:'Waiting for Home Assistant state data.',
        missing:'The bound switch was not found. Check the selection.',
        unavailable:'Switch state unavailable; the report control stays hidden.',
        off:'The map switch is off; the report control stays hidden.',
        on:'The map switch is on. This does not establish that fresh reports exist.'
      };
      this.statusHost.replaceChildren(this.node('h3',hu?'Hozzárendelések állapota':'Binding status'));
      for(const [source,name] of [['terralyra_ignis_canada_reports','Canada'],['terralyra_ignis_nifc_reports','NIFC']])this.statusHost.append(this.node('p',name+': '+messages[mapBindingStatus(this._hass?.states,this.config.report_switches?.[source])]));
    }
    render(){
      if(!this.config)return;
      if(!this.shadowRoot)this.attachShadow({mode:'open'});
      const root=this.shadowRoot;root.replaceChildren();
      const hu=this._hass?.language?.startsWith('hu');
      root.append(this.node('style',`:host{display:block;color:var(--primary-text-color);overflow-wrap:anywhere}label{display:block;margin:16px 0}input,select{box-sizing:border-box;width:100%;min-width:0;padding:12px;margin-top:8px;font:inherit;color:inherit;background:var(--card-background-color,white);border:1px solid var(--divider-color,#999);border-radius:8px}p{line-height:1.5}`));
      const titleText=hu?'Térkép címe (nem kötelező)':'Map title (optional)';
      const label=this.node('label',titleText),input=this.node('input');input.type='text';input.value=this.config.title||'';input.setAttribute('aria-label',titleText);input.onchange=()=>this.update({title:input.value});label.append(input);root.append(label);
      root.append(this.node('p',hu?'Válaszd ki az adott forrás IGNIS térképes megjelenítési kapcsolóját. Ez csak hozzárendelés: nem engedélyez adatforrást, és nem kapcsol át entitást.':'Select each source’s IGNIS map visibility switch. This only creates a binding: it does not enable a provider or toggle an entity.'));
      for(const [source,name] of [['terralyra_ignis_canada_reports','Canada'],['terralyra_ignis_nifc_reports','NIFC']]){
        const caption=name+(hu?' térképkapcsoló':' map switch'),label=this.node('label',caption),select=this.node('select');select.setAttribute('aria-label',caption);
        const empty=this.node('option',hu?'Nincs hozzárendelés':'No binding');empty.value='';select.append(empty);
        const choices=this.choices(source),current=this.config.report_switches?.[source]||'';
        for(const [id,name] of choices){const option=this.node('option',`${name} — ${id}`);option.value=id;select.append(option);}
        if(current&&!choices.some(([id])=>id===current)){const option=this.node('option',(hu?'Megőrzött, ellenőrizendő: ':'Saved; check binding: ')+current);option.value=current;select.append(option);}
        select.value=current;select.onchange=()=>{const bindings={...this.config.report_switches};if(select.value)bindings[source]=select.value;else delete bindings[source];this.update({report_switches:bindings});};label.append(select);root.append(label);
      }
      const circlesLabel=this.node('label',hu?'Megfigyelési és riasztási körök':'Monitoring and alert circles'),circles=this.node('input');
      circles.type='checkbox';circles.style.cssText='width:auto;margin-right:8px';circles.checked=hasMonitoringAreas(this.config);circles.disabled=Boolean(this.config.show_all);
      circles.setAttribute('aria-label',hu?'Megfigyelési és riasztási körök':'Monitoring and alert circles');
      circles.onchange=()=>{this.update(withMonitoringAreas(this.config,circles.checked));this.render();};circlesLabel.prepend(circles);root.append(circlesLabel);
      root.append(this.node('p',hu?'A körök a megfigyelt helyszínek beállított sugarait mutatják. Egyenlő sugaraknál egy kör jelenik meg. Nem a tűz kiterjedését jelölik.':'Circles show the configured radii of monitored locations. Equal radii use one circle. They do not represent fire perimeters.'));
      if(this.config.show_all)root.append(this.node('p',hu?'Az összes entitás megjelenítése aktív; a körök külön szűréséhez előbb kapcsold ki a show_all beállítást a kódszerkesztőben.':'Show all entities is active; turn off show_all in the code editor before filtering circles separately.'));
      if(this.config.cluster===true)root.append(this.node('p',hu?'A jelölők csoportosítása aktív; a köröket elrejtheti. Ha szükséges, állítsd a cluster értékét false-ra a kódszerkesztőben.':'Marker clustering is active and may hide circles. If needed, set cluster to false in the code editor.'));
      this.statusHost=this.node('section');this.statusHost.setAttribute('aria-live','polite');root.append(this.statusHost);this.renderStatus();
      root.append(this.node('p',hu?'A hozzárendelés nélküli vagy kikapcsolt riportforrás vezérlője rejtve marad. Az egyéb haladó térképbeállítások a kódszerkesztőben módosíthatók; a meglévő értékeket megőrizzük.':'Report controls stay hidden without a binding or when their switch is off. Other advanced map options remain available in the code editor; existing values are preserved.'));
    }
  }
  customElements.define('ignis-report-map-editor',IgnisReportMapEditor);
  class IgnisReportMap extends HTMLElement {
    static getConfigElement(){return document.createElement('ignis-report-map-editor');}
    static getStubConfig(){return {type:'custom:ignis-report-map'};}

    constructor() {
      super();
      this.attachShadow({mode:'open'});
      const style = document.createElement('style');
      style.textContent = `:host{display:block}dialog{box-sizing:border-box;width:min(640px,calc(100vw - 24px));max-height:85dvh;overflow:auto;border:0;border-radius:20px;padding:24px;background:var(--card-background-color,#fff);color:var(--primary-text-color,#172b39);font:inherit}dialog::backdrop{background:#0008}h2{font-size:1.3rem;overflow-wrap:anywhere}p{line-height:1.5}dl{display:grid;grid-template-columns:1fr 1fr;gap:14px}dt{color:var(--secondary-text-color,#596975)}dd{margin:0;overflow-wrap:anywhere}button,a{font:inherit;padding:10px;color:var(--primary-color,#007f91)}button{cursor:pointer;background:transparent;border:1px solid currentColor;border-radius:8px}footer{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px}@media(max-width:440px){dl{grid-template-columns:1fr;gap:6px}dd{margin-bottom:12px}}`;
      this.enabled = {terralyra_ignis:true, terralyra_ignis_canada_reports:true, terralyra_ignis_nifc_reports:true};
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
      try {
        const helpers = await window.loadCardHelpers();
        if (config !== this.config) return;
        this.map = helpers.createCardElement(config);
        this.updateMap();
        this.mapHost.replaceChildren(this.map);
      } catch {
        this.mapHost.textContent = 'IGNIS: the Home Assistant map could not be loaded. Reload the dashboard or use the standard map card.';
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
      const labels = hu ? ['Műholdas észlelések','Kanadai jelentések','NIFC jelentések'] : ['Satellite detections','Canada reports','NIFC reports'];
      Object.keys(this.enabled).forEach((source,index)=>{
        if (!visibility[source]) return;
        const label=document.createElement('label');
        const input=document.createElement('input');input.type='checkbox';input.checked=this.enabled[source];
        input.onchange=()=>{this.enabled[source]=input.checked;this.updateMap();};
        label.append(input,document.createTextNode(labels[index]));this.controls.append(label);
      });
      const label=document.createElement('label');
      label.append(document.createTextNode(hu ? 'Jelentés frissítése: ' : 'Report updated: '));
      const select=document.createElement('select');
      for (const days of [0,1,7,30]) {
        const option=document.createElement('option');option.value=days;
        option.textContent=days ? (hu ? `Legfeljebb ${days} napja` : `Within ${days} days`) : (hu ? 'Bármikor' : 'Any time');
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
      const hu=this._hass.language?.startsWith('hu');
      const el=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
      const close=el('button',hu?'Bezárás':'Close');close.onclick=()=>this.dialog.close();
      const heading=el('h2',state.attributes.friendly_name || this.selected);heading.id='report-title';
      const details=el('button',hu?'Home Assistant részletek':'Home Assistant details');
      details.onclick=()=>{const entityId=this.selected;this.dialog.close();this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId},bubbles:true,composed:true}));};
      this.dialog.replaceChildren(close,heading,details);
      const result=this.satelliteResult;
      if(!result || result.error){this.dialog.append(el('p',hu?(!result?'Kapcsolódó hírek ellenőrzése…':'A kapcsolódó hírek most nem ellenőrizhetők.'):(!result?'Checking related reports…':'Related reports could not be checked.')));return;}
      if(!result.reports?.length)this.dialog.append(el('p',hu?'A helyben tárolt hírek között nem találtunk kapcsolódó BM-hírt.':'No related BM report was found in the local archive.'));
      for(const report of result.reports || []) {
        this.dialog.append(el('h3',hu?'Valószínűleg ehhez az észleléshez kapcsolódó BM-hír':'BM report probably related to this observation'),el('h4',report.title));
        const body=el('p',report.description);body.style.whiteSpace='pre-wrap';this.dialog.append(body);
        this.dialog.append(el('p',`BM OKF · ${report.published_at}`));
        if(report.ambiguous)this.dialog.append(el('p',hu?'Több műholdas észleléshez is illeszkedhet.':'May relate to multiple satellite observations.'));
        const url=safeLink(report.report_url);if(url){const link=el('a',hu?'Eredeti hír':'Original report');link.href=url;link.target='_blank';link.rel='noopener noreferrer';this.dialog.append(link);}
      }
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
      this.dialog.append(element('p',view.attribution),element('h3',description.heading),paragraph);
      if(description.notice) this.dialog.append(element('p',description.notice));
      if(view.retrievalNotice) this.dialog.append(element('p',view.retrievalNotice));
      const age=reportAge(state);
      this.dialog.append(element('p',this._hass.language?.startsWith('hu')
        ? (age === null ? 'Jelentés kora: ismeretlen vagy jövőbeli időpont' : `Jelentés kora: ${Math.floor(age)} nap (forrás szerinti frissítés)`)
        : (age === null ? 'Report age: unknown or future timestamp' : `Report age: ${Math.floor(age)} days (source update)`)));
      const list=document.createElement('dl');
      for(const [label,value] of view.rows) list.append(element('dt',label),element('dd',value));
      this.dialog.append(list,element('p',w.warning));
      const footer=document.createElement('footer');
      if(view.source) {
        const link=element('a',w.source);
        link.href=view.source;link.target='_blank';link.rel='noopener noreferrer';link.dataset.action='source';
        footer.append(link);
      }
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
  window.customCards.push({type:'ignis-report-map',name:'IGNIS report map',description:'Map with readable Canada and NIFC official report details.'});
}
