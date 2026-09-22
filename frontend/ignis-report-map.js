// Optional local dashboard resource. No external libraries or report-page requests.
const SOURCES = new Set(['terralyra_ignis_canada_reports', 'terralyra_ignis_nifc_reports']);
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

export function safeLink(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
  } catch { return null; }
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
  return {w, title:text(a.friendly_name), attribution:text(a.attribution),
    unavailable: ['unavailable','unknown'].includes(state.state),
    source:safeLink(a.source_url),
    rows:[
      [w.location,text(a.distance_reference_name)],
      [w.distance,Number.isFinite(distance) && state.state.trim() !== '' ? `${distance} ${text(a.unit_of_measurement)}` : w.unknown],
      [w.status,text(a.source_status || a.stage_of_control)],
      [w.category,text(a.report_category || a.prescribed_status)],
      [w.updated,time(a.source_times?.status_date || a.source_modified_at)],
      [w.discovered,time(a.source_discovered_at)],
      [w.received,time(a.last_success_at)],
      [w.response,text(a.response_status)]
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
  class IgnisReportMap extends HTMLElement {
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
        if (!reportView(this._hass?.states[id],this._hass?.language)) return;
        event.stopPropagation();
        this.selected = id;
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
      if (this.controlsLanguage === hu) return;
      this.controlsLanguage = hu;
      this.controls.replaceChildren();
      const labels = hu ? ['Műholdas észlelések','Kanadai jelentések','NIFC jelentések'] : ['Satellite detections','Canada reports','NIFC reports'];
      Object.keys(this.enabled).forEach((source,index)=>{
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
      if (this.map && this._hass) this.map.hass = {...this._hass,states:filterMapStates(this._hass.states,this.enabled,this.maxDays)};
    }
    getCardSize() {return this.map?.getCardSize?.() ?? 7;}
    disconnectedCallback() {if(this.dialog.open) this.dialog.close();}
    renderReport() {
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
      const body = state.attributes.incident_text;
      const content = typeof body === 'string' && body.trim() ? body.slice(0,4000) :
        state.attributes.incident_text_status === 'not_in_feed'
          ? (this._hass.language?.startsWith('hu') ? 'Ez az adatfolyam eseményadatokat ad, szöveges leírásmezőt nem tartalmaz.' : 'This feed supplies incident data without a narrative description field.') :
        state.attributes.incident_text_status === 'not_provided'
          ? (this._hass.language?.startsWith('hu') ? 'A forrás ennél az eseménynél nem adott meg leírást.' : 'The source did not provide a description for this incident.') : w.absent;
      const paragraph=element('p',content);paragraph.style.whiteSpace='pre-wrap';
      this.dialog.append(element('p',view.attribution),paragraph);
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
