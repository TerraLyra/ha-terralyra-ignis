// UI language follows HA; preserve the historical Hungarian default before HA connects.
export function summaryLanguage(hass) {
  const language=hass?.language||hass?.locale?.language;
  return !language||language.toLowerCase().startsWith('hu')?'hu':'en';
}
const english = {
  "Adatforrások elérhetők": "Sources available",
  "Késleltetett adatellátás": "Delayed data",
  "Részleges adatellátás": "Partial data",
  "Első adatokra vár": "Waiting for first data",
  "Adatok nem érhetők el": "Data unavailable",
  "Nincs megfelelő forrás": "No suitable source",
  "Ellenőrizd a forrás hozzáférési adatait az IGNIS beállításaiban.": "Check source credentials in IGNIS settings.",
  "A lekérés sikertelen. Ha tartósan fennáll, ellenőrizd az IGNIS diagnosztikáját és a hálózati kapcsolatot.": "Retrieval failed. If this persists, check IGNIS diagnostics and the network connection.",
  "Az adatok késnek. A sikeres lekérés önmagában nem jelent friss műholdas megfigyelést.": "Data is delayed. Successful retrieval alone does not mean a fresh satellite observation.",
  "Jelenleg nincs elérhető adatcsomag; ebből nem következik, hogy nincs tűz.": "No data product is currently available; this does not mean there is no fire.",
  "Várd meg az első lekérés eredményét. Ha ez az állapot tartós, ellenőrizd az IGNIS diagnosztikáját.": "Wait for the first retrieval. If this persists, check IGNIS diagnostics.",
  "A kiválasztott érzékelő nem ehhez a helyszínhez tartozik, vagy nem támogatott.": "The selected sensor does not belong to this location or is unsupported.",
  "Ismeretlen adatellátás": "Unknown data availability",
  "Alacsony": "Low",
  "Mérsékelt": "Moderate",
  "Magas": "High",
  "Nagyon magas": "Very high",
  "Szélsőséges": "Extreme",
  "Ehhez a kártyához nincs kapcsolt előrejelzés.": "No forecast is linked to this card.",
  "Az előrejelzés helyszín-hozzárendelése hiányos vagy eltérő.": "The forecast location binding is incomplete or does not match.",
  "Az előrejelzés jelenleg nem érhető el.": "The forecast is currently unavailable.",
  "Az előrejelzés helyszíne vagy sugara nem egyezik a hozzárendeléssel.": "The forecast location or radius does not match the binding.",
  "Az előrejelzés mintavételi pontja nem egyezik a hozzárendelt helyszínnel.": "The forecast sample point does not match the bound location.",
  "Az előrejelzés érvényessége nem ellenőrizhető.": "Forecast validity cannot be verified.",
  "Az előrejelzés lejárt; mai érték nem jeleníthető meg.": "The forecast has expired; no current value can be displayed.",
  "A mai UTC terméknapra nincs egyértelmű előrejelzés.": "There is no unambiguous forecast for today's UTC product date.",
  "A mai kockázati kategória ismeretlen.": "Today's risk category is unknown.",
  "Az adatátvétel ideje nem ellenőrizhető.": "The data receipt time cannot be verified.",
  "Az adatátvétel több mint 12 órás; a frissítés késhet.": "Data was received more than 12 hours ago; updates may be delayed.",
  "Az adatátvétel 12 órán belüli.": "Data was received within the last 12 hours.",
  "Előrejelzés: nincs hozzárendelve (nem kötelező).": "Forecast: not linked (optional).",
  "A helyszín hozzárendelése még nem ellenőrizhető.": "The location binding cannot yet be verified.",
  "Ellenőrizd a sugarakat az IGNIS beállításaiban: a riasztási sugár legyen pozitív és legfeljebb a megfigyelési sugár.": "Check the radii in IGNIS settings: the alert radius must be positive and no larger than the monitoring radius.",
  "Az adatellátás jelenleg nem ellenőrizhető.": "Data availability cannot currently be verified.",
  "Telefonos értesítés: külön blueprint és értesítési cél szükséges. A kártya nem ellenőrzi a meglévő automatizálást vagy a kézbesítést.": "Phone notifications require a separate blueprint and notification target. This card does not verify existing automations or delivery.",
  "Előrejelzés (nem kötelező)": "Forecast (optional)",
  "Nincs hozzárendelve": "Not linked",
  "Előrejelzés hozzárendelésének frissítése": "Update forecast binding",
  "Csak a kiválasztott helyhez tartozó előrejelzések választhatók. A hozzárendelés nem kapcsol be adatforrást.": "Only forecasts for the selected location are offered. Linking does not enable a source.",
  "Ehhez a helyhez még nincs választható előrejelzés. Az IGNIS beállításaiban engedélyezheted, ahol elérhető.": "No forecast is available to select for this location yet. Enable it in IGNIS settings where supported.",
  "Beállítások áttekintése": "Setup review",
  "Megfigyelt helyszín": "Monitored location",
  "Válassz helyszínt…": "Choose a location…",
  "Még nincs választható helyszínérzékelő. Engedélyezz egy megfigyelt helyszínt az IGNIS beállításaiban, majd várd meg az érzékelő létrejöttét.": "No location sensor is available to select yet. Enable a monitored location in IGNIS settings, then wait for its sensor to appear.",
  "Kapcsolódás a Home Assistanthoz…": "Connecting to Home Assistant…",
  "A helyszínazonosítót a kiválasztott érzékelőből vesszük át. A sugarakat az IGNIS beállításaiban módosíthatod.": "The location ID comes from the selected sensor. Change radii in IGNIS settings.",
  "Egyéni cím (nem kötelező)": "Custom title (optional)",
  "Add meg az entity és location_id értékét.": "Provide entity and location_id values.",
  "Adj meg egy forecast.entity érzékelőt.": "Provide a forecast.entity sensor.",
  "Helyszínösszefoglaló": "Location summary",
  "Válassz egy megfigyelt helyszínt a kártya szerkesztőjében.": "Choose a monitored location in the card editor.",
  "aktívként követett műholdas esemény": "satellite incidents tracked as active",
  "több forrás által észlelt esemény": "incidents detected by multiple sources",
  "A jelenlegi eseményszám nem állapítható meg.": "The current incident count cannot be determined.",
  "Nincs ellenőrizhető távolságadat ehhez a helyszínhez.": "No verifiable distance data is available for this location.",
  "Adatforrások": "Sources",
  "Ismeretlen forrás": "Unknown source",
  "Késleltetett": "Delayed",
  "Forráskiesés": "Source outage",
  "Hozzáférési hiba": "Access error",
  "Nincs termék": "No product",
  "Ismeretlen állapot": "Unknown status",
  "Nincs adatátvételi időpont.": "No data receipt time is available.",
  "Tűzveszély-előrejelzés": "Fire-risk forecast",
  "Modell-előrejelzés a kijelölt helyszín közelére; nem hatósági riasztás. A lekérés ideje nem a modell kiadási ideje.": "Model forecast near the selected location; not an official warning. Retrieval time is not model issuance time.",
  "Modell-előrejelzés az otthonpont közelére; nem hatósági riasztás. A lekérés ideje nem a modell kiadási ideje.": "Model forecast near Home; not an official warning. Retrieval time is not model issuance time.",
  "Hivatalos tűzgyújtási korlátozás": "Official fire restrictions",
  "Nincs kapcsolt adat; ebből a tilalom fennállása nem állapítható meg.": "No linked data; whether a restriction is in force cannot be determined.",
  "Az észlelések hiánya nem jelent tűzmentességet. A legutóbbi adatátvétel nem minden forrás frissessége és nem az esemény kezdete. A műholdas események nem hatóságilag igazolt tűzesetek.": "No detections does not mean no fire. The latest data receipt does not establish freshness of every source or when an incident began. Satellite incidents are not officially confirmed fires.",
  "Érzékelő részletei": "Sensor details"
};
function text(hungarian, language) { return language==='hu'?hungarian:(english[hungarian]??hungarian); }
// Optional read-only card. Explicit entity/location association; no service calls.
const statusLabels = language => ({available:text("Adatforrások elérhetők",language),degraded:text("Késleltetett adatellátás",language),partial:text("Részleges adatellátás",language),initializing:text("Első adatokra vár",language),unavailable:text("Adatok nem érhetők el",language),no_coverage:text("Nincs megfelelő forrás",language)});
// Describe only the reported state; never infer an all-clear or a scheduled retry.
export function sourceGuidance(source, language='hu') {
  if(!source || typeof source!=='object')return '';
  if(source.status==='auth_error')return text("Ellenőrizd a forrás hozzáférési adatait az IGNIS beállításaiban.",language);
  if(source.retrieval_status==='failed'||source.status==='outage')return text("A lekérés sikertelen. Ha tartósan fennáll, ellenőrizd az IGNIS diagnosztikáját és a hálózati kapcsolatot.",language);
  return ({
    delayed:text("Az adatok késnek. A sikeres lekérés önmagában nem jelent friss műholdas megfigyelést.",language),
    no_product:text("Jelenleg nincs elérhető adatcsomag; ebből nem következik, hogy nincs tűz.",language),
    initializing:text("Várd meg az első lekérés eredményét. Ha ez az állapot tartós, ellenőrizd az IGNIS diagnosztikáját.",language)
  })[source.status]||'';
}
export function summarizeLocation(entity, locationId, language='hu') {
  const a=entity?.attributes;
  if(!a || a.location_id!==locationId || !Array.isArray(a.source_health))return {error:text("A kiválasztott érzékelő nem ehhez a helyszínhez tartozik, vagy nem támogatott.",language)};
  const status=['unknown','unavailable'].includes(entity.state)?'unavailable':a.operational_status;
  const usable=['available','degraded','partial'].includes(status);
  const count=v=>usable && Number.isSafeInteger(v) && v>=0?v:null;
  return {name:a.location_name||locationId,status:statusLabels(language)[status]||text("Ismeretlen adatellátás",language),active:count(a.active_incidents),multi:count(a.multi_source_incidents),nearest:usable&&Number.isFinite(a.nearest_incident_distance_km)&&a.nearest_incident_distance_km>=0?a.nearest_incident_distance_km:null,sources:a.source_health,received:a.last_received_at,monitoringRadius:a.monitoring_radius_km,alertRadius:a.alert_radius_km};
}
// FRMv3 validity dates are UTC product dates; generated_at is retrieval time.
const riskLabels=language=>({low:text("Alacsony",language),moderate:text("Mérsékelt",language),high:text("Magas",language),very_high:text("Nagyon magas",language),extreme:text("Szélsőséges",language)});
export function summarizeForecast(entity, binding, locationId, now=new Date(), language='hu') {
  if(!binding)return {message:text("Ehhez a kártyához nincs kapcsolt előrejelzés.",language)};
  const a=entity?.attributes;
  const number=v=>typeof v==='number'&&Number.isFinite(v);
  if(binding.location_id!==locationId || !number(binding.latitude) || !number(binding.longitude) || Math.abs(binding.latitude)>90 || Math.abs(binding.longitude)>180)
    return {message:text("Az előrejelzés helyszín-hozzárendelése hiányos vagy eltérő.",language)};
  if(!a || ['unknown','unavailable'].includes(entity.state))return {message:text("Az előrejelzés jelenleg nem érhető el.",language)};
  if(a.scope==='monitored_location') {
    if(a.location_id!==locationId || a.provider!=='eumetsat_lsa_saf_frmv3' || a.product!=='FRMv3' ||
       !number(a.latitude)||!number(a.longitude)||a.latitude!==binding.latitude||a.longitude!==binding.longitude||
       !number(binding.radius_km)||binding.radius_km<1||binding.radius_km>500||a.forecast_radius_km!==binding.radius_km)
      return {message:text("Az előrejelzés helyszíne vagy sugara nem egyezik a hozzárendeléssel.",language)};
  } else if(a.scope!=='near_home'||!number(a.sample_latitude)||!number(a.sample_longitude)||Math.abs(a.sample_latitude-binding.latitude)>0.000001||Math.abs(a.sample_longitude-binding.longitude)>0.000001)
    return {message:text("Az előrejelzés mintavételi pontja nem egyezik a hozzárendelt helyszínnel.",language)};
  if(!Array.isArray(a.forecast)||!Number.isFinite(now.getTime()))return {message:text("Az előrejelzés érvényessége nem ellenőrizhető.",language)};
  const today=now.toISOString().slice(0,10);
  const days=a.forecast.filter(d=>d&&typeof d.date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d.date)&&Number.isFinite(Date.parse(d.date))&&new Date(d.date).toISOString().slice(0,10)===d.date);
  const matches=days.filter(d=>d.date===today);
  if(matches.length!==1)return {message:days.length&&days.every(d=>d.date<today)?text("Az előrejelzés lejárt; mai érték nem jeleníthető meg.",language):text("A mai UTC terméknapra nincs egyértelmű előrejelzés.",language)};
  const day=matches[0];
  if(!Object.hasOwn(riskLabels(language),day.risk))return {message:text("A mai kockázati kategória ismeretlen.",language)};
  const stamp=typeof a.generated_at==='string'&&/(Z|[+-]\d{2}:\d{2})$/.test(a.generated_at)?Date.parse(a.generated_at):NaN;
  const age=now.getTime()-stamp;
  return {scope:a.scope,risk:riskLabels(language)[day.risk],validDate:day.date,received:Number.isFinite(stamp)&&age>=0?new Date(stamp).toISOString():null,
    freshness:!Number.isFinite(stamp)||age<0?text("Az adatátvétel ideje nem ellenőrizhető.",language):age>12*3600000?text("Az adatátvétel több mint 12 órás; a frissítés késhet.",language):text("Az adatátvétel 12 órán belüli.",language),
    attribution:typeof a.attribution==='string'?a.attribution:'EUMETSAT / LSA SAF'};
}
// Only offer states carrying the location-status contract, never forecast/global sensors.
export function locationChoices(states={}) {
  return Object.entries(states).filter(([id,state])=>id.startsWith('sensor.') &&
    typeof state?.attributes?.location_id==='string' && state.attributes.location_id.trim() &&
    typeof state.attributes.operational_status==='string' && Array.isArray(state.attributes.source_health))
    .map(([entity,state])=>({entity,location_id:state.attributes.location_id,
      name:String(state.attributes.location_name||state.attributes.friendly_name||entity)}))
    .sort((a,b)=>a.name.localeCompare(b.name)||a.entity.localeCompare(b.entity));
}
// Offer explicit monitored-location forecasts only; legacy bindings remain intact.
export function forecastChoices(states={},locationId) {
  return Object.entries(states).filter(([id,state])=>{
    const a=state?.attributes;
    return id.startsWith('sensor.') && a?.scope==='monitored_location' &&
      typeof locationId==='string' && locationId.length>0 && a.location_id===locationId &&
      a.provider==='eumetsat_lsa_saf_frmv3' && a.product==='FRMv3' &&
      Number.isFinite(a.latitude)&&Math.abs(a.latitude)<=90 &&
      Number.isFinite(a.longitude)&&Math.abs(a.longitude)<=180 &&
      Number.isFinite(a.forecast_radius_km)&&a.forecast_radius_km>=1&&a.forecast_radius_km<=500;
  }).map(([entity,state])=>({entity,name:String(state.attributes.friendly_name||entity),
    location_id:locationId,latitude:state.attributes.latitude,longitude:state.attributes.longitude,
    radius_km:state.attributes.forecast_radius_km})).sort((a,b)=>a.name.localeCompare(b.name)||a.entity.localeCompare(b.entity));
}
export function forecastSetupReview(states, config, now=new Date(), language='hu') {
  if(!config.forecast)return text("Előrejelzés: nincs hozzárendelve (nem kötelező).",language);
  const result=summarizeForecast(states?.[config.forecast.entity],config.forecast,config.location_id,now,language);
  return result.message?(language==='hu'?`Előrejelzés: ${result.message}`:`Forecast: ${result.message}`):(language==='hu'?`Előrejelzés: ${result.risk} · UTC terméknap: ${result.validDate}. ${result.freshness}`:`Forecast: ${result.risk} · UTC product date: ${result.validDate}. ${result.freshness}`);
}
// Setup review is descriptive: it cannot inspect notification automation delivery.
export function setupReview(entity, locationId, language='hu') {
  const a=entity?.attributes;
  if(!a || a.location_id!==locationId)return [text("A helyszín hozzárendelése még nem ellenőrizhető.",language)];
  const valid=Number.isFinite(a.monitoring_radius_km)&&Number.isFinite(a.alert_radius_km)&&a.alert_radius_km>0&&a.alert_radius_km<=a.monitoring_radius_km;
  return [
    (language==='hu'?`Helyszín: ${a.location_name||locationId}`:`Location: ${a.location_name||locationId}`),
    valid?(language==='hu'?`Megfigyelés: ${a.monitoring_radius_km} km · Riasztás: ${a.alert_radius_km} km`:`Monitoring: ${a.monitoring_radius_km} km · Alert: ${a.alert_radius_km} km`):text("Ellenőrizd a sugarakat az IGNIS beállításaiban: a riasztási sugár legyen pozitív és legfeljebb a megfigyelési sugár.",language),
    ['unknown','unavailable'].includes(entity.state)?text("Az adatellátás jelenleg nem ellenőrizhető.",language):(statusLabels(language)[a.operational_status]||text("Ismeretlen adatellátás",language)),
    text("Telefonos értesítés: külön blueprint és értesítési cél szükséges. A kártya nem ellenőrzi a meglévő automatizálást vagy a kézbesítést.",language)
  ];
}
class IgnisLocationSummaryEditor extends HTMLElement {
  setConfig(config){this.config={...config};this.render();}
  set hass(value){
    this._hass=value;
    const signature=JSON.stringify([summaryLanguage(value),locationChoices(value?.states),forecastChoices(value?.states,this.config?.location_id)]);
    if(signature!==this._choicesSignature){this._choicesSignature=signature;this.render();}
    else this.refreshReview();
  }
  node(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;}
  update(patch){
    this.config={...this.config,...patch};
    this.refreshReview();
    this.refreshForecast();
    this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:{...this.config}},bubbles:true,composed:true}));
  }
  refreshForecast(){
    const language=summaryLanguage(this._hass);
    if(!this.forecastHost)return;
    const host=this.forecastHost;host.replaceChildren();
    const choices=forecastChoices(this._hass?.states,this.config.location_id);
    const label=this.node('label',text("Előrejelzés (nem kötelező)",language)),select=this.node('select');
    select.setAttribute('aria-label',text("Előrejelzés (nem kötelező)",language));
    const empty=this.node('option',text("Nincs hozzárendelve",language));empty.value='';select.append(empty);
    for(const choice of choices){const option=this.node('option',`${choice.name} — ${choice.radius_km} km — ${choice.entity}`);option.value=choice.entity;select.append(option);}
    const current=this.config.forecast?.entity;
    if(current&&!choices.some(c=>c.entity===current)){const saved=this.node('option',(language==='hu'?`Megőrzött hozzárendelés, ellenőrizendő: ${current}`:`Saved binding; check: ${current}`));saved.value=current;select.append(saved);}
    select.value=current||'';
    select.onchange=()=>{
      const choice=forecastChoices(this._hass?.states,this.config.location_id).find(c=>c.entity===select.value);
      if(choice){const {name,...binding}=choice;this.update({forecast:binding});}
      else if(select.value===''){const {forecast,...rest}=this.config;this.config=rest;this.update({});}
    };
    label.append(select);host.append(label);
    const selected=choices.find(c=>c.entity===current);
    if(selected && ['location_id','latitude','longitude','radius_km'].some(key=>selected[key]!==this.config.forecast[key])){
      const refresh=this.node('button',text("Előrejelzés hozzárendelésének frissítése",language));refresh.type='button';
      refresh.onclick=()=>{
        // Re-read current metadata at click time; never reuse stale coordinates.
        const latest=forecastChoices(this._hass?.states,this.config.location_id).find(c=>c.entity===this.config.forecast?.entity);
        if(latest){const {name,...binding}=latest;this.update({forecast:binding});}
        else this.refreshForecast();
      };
      host.append(this.node('p',(language==='hu'?`A kiválasztott előrejelzés beállításai változtak. Aktuális pont: ${selected.latitude}, ${selected.longitude}; előrejelzési sugár: ${selected.radius_km} km. A gombbal átveheted ezeket a kártyához.`:`The selected forecast settings have changed. Current point: ${selected.latitude}, ${selected.longitude}; forecast radius: ${selected.radius_km} km. Use the button to apply these to the card.`)),refresh);
    }
    host.append(this.node('p',choices.length?text("Csak a kiválasztott helyhez tartozó előrejelzések választhatók. A hozzárendelés nem kapcsol be adatforrást.",language):text("Ehhez a helyhez még nincs választható előrejelzés. Az IGNIS beállításaiban engedélyezheted, ahol elérhető.",language)));
  }
  refreshReview(){
    const language=summaryLanguage(this._hass);
    if(!this.reviewHost||!this.config)return;
    this.reviewHost.replaceChildren(this.node('h3',text("Beállítások áttekintése",language)));
    for(const text of setupReview(this._hass?.states?.[this.config.entity],this.config.location_id,language))this.reviewHost.append(this.node('p',text));
    this.reviewHost.append(this.node('p',forecastSetupReview(this._hass?.states,this.config,new Date(),language)));
  }
  render(){
    const language=summaryLanguage(this._hass);
    if(!this.config)return;
    if(!this.shadowRoot)this.attachShadow({mode:'open'});
    const root=this.shadowRoot;root.replaceChildren();
    root.append(this.node('style',`:host{display:block;color:var(--primary-text-color);overflow-wrap:anywhere}label{display:block;margin:16px 0}select,input{display:block;box-sizing:border-box;width:100%;min-width:0;font:inherit;padding:12px;margin-top:8px;color:inherit;background:var(--card-background-color,white);border:1px solid var(--divider-color,#999);border-radius:8px}p{line-height:1.5}`));
    const choices=locationChoices(this._hass?.states);
    const label=this.node('label',text("Megfigyelt helyszín",language)),select=this.node('select');
    select.setAttribute('aria-label',text("Megfigyelt helyszín",language));
    const placeholder=this.node('option',text("Válassz helyszínt…",language));placeholder.value='';placeholder.disabled=true;select.append(placeholder);
    for(const choice of choices){const option=this.node('option',`${choice.name} — ${choice.entity}`);option.value=choice.entity;select.append(option);}
    if(this.config.entity&&!choices.some(c=>c.entity===this.config.entity)){
      const missing=this.node('option',(language==='hu'?`Jelenleg nem elérhető: ${this.config.entity}`:`Currently unavailable: ${this.config.entity}`));missing.value=this.config.entity;missing.disabled=true;select.append(missing);
    }
    select.value=this.config.entity||'';
    select.onchange=()=>{
      const choice=locationChoices(this._hass?.states).find(c=>c.entity===select.value);
      if(choice)this.update({entity:choice.entity,location_id:choice.location_id});
    };
    label.append(select);root.append(label);
    if(!choices.length){const empty=this.node('p',this._hass?text("Még nincs választható helyszínérzékelő. Engedélyezz egy megfigyelt helyszínt az IGNIS beállításaiban, majd várd meg az érzékelő létrejöttét.",language):text("Kapcsolódás a Home Assistanthoz…",language));empty.setAttribute('role','status');root.append(empty);}
    root.append(this.node('p',text("A helyszínazonosítót a kiválasztott érzékelőből vesszük át. A sugarakat az IGNIS beállításaiban módosíthatod.",language)));
    const titleLabel=this.node('label',text("Egyéni cím (nem kötelező)",language)),title=this.node('input');title.type='text';title.value=this.config.title||'';title.setAttribute('aria-label',text("Egyéni cím (nem kötelező)",language));
    title.onchange=()=>this.update({title:title.value});titleLabel.append(title);root.append(titleLabel);
    const review=this.node('section');review.setAttribute('aria-label',text("Beállítások áttekintése",language));this.reviewHost=review;this.refreshReview();
    root.append(review);
    this.forecastHost=this.node('section');root.append(this.forecastHost);this.refreshForecast();
  }
}
customElements.define('ignis-location-summary-editor',IgnisLocationSummaryEditor);
class IgnisLocationSummary extends HTMLElement {
  static getConfigElement(){return document.createElement('ignis-location-summary-editor');}
  static getStubConfig(){return {type:'custom:ignis-location-summary'};}

  setConfig(config) {
    const language=summaryLanguage(this._hass);
    const unconfigured=config.entity===undefined&&config.location_id===undefined;
    if(!unconfigured&&(typeof config.entity!=='string'||!config.entity.startsWith('sensor.')||typeof config.location_id!=='string'||!config.location_id.trim()))throw Error(text("Add meg az entity és location_id értékét.",language));
    if(config.forecast && (typeof config.forecast.entity!=='string'||!config.forecast.entity.startsWith('sensor.')))throw Error(text("Adj meg egy forecast.entity érzékelőt.",language));
    this.config={...config};if(!this.shadowRoot)this.attachShadow({mode:'open'});this.render();
  }
  set hass(value){this._hass=value;this.render();}
  getCardSize(){return 5;}
  node(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;}
  labelled(tag,text,icon){
    const node=this.node(tag),glyph=this.node('ha-icon');
    glyph.setAttribute('icon',icon);glyph.setAttribute('aria-hidden','true');
    node.classList.add('with-icon');node.append(glyph,this.node('span',text));return node;
  }
  render(){
    const language=summaryLanguage(this._hass);
    if(!this.config||!this.shadowRoot)return;
    const root=this.shadowRoot;root.replaceChildren();
    const style=this.node('style',`:host{display:block}ha-card{display:block;padding:22px;background:var(--card-background-color,white);color:var(--primary-text-color,#183238);border-radius:16px;overflow-wrap:anywhere}h2{margin:0 0 12px;font-size:24px}h3{font-size:16px;margin-top:22px}.with-icon{display:flex;align-items:baseline;gap:8px}.with-icon ha-icon{--mdc-icon-size:18px;width:18px;height:18px;flex:0 0 18px;align-self:flex-start;margin-top:2px;color:var(--secondary-text-color,#596e73)}.with-icon>span{min-width:0}.status{padding:12px;background:var(--secondary-background-color,#eef4f4);border-radius:8px}.counts{display:flex;gap:24px;flex-wrap:wrap}.counts p{flex:1;min-width:120px}.number{display:block;font-size:36px;font-weight:600}.muted{font-size:13px;color:var(--secondary-text-color,#596e73)}li{margin:8px 0}button{font:inherit;padding:9px;border:1px solid var(--divider-color,#aaa);border-radius:8px;background:transparent;color:inherit;cursor:pointer}`);root.append(style);
    const card=this.node('ha-card');root.append(card);
    if(!this.config.entity){card.append(this.node('h2',text("Helyszínösszefoglaló",language)),this.node('p',text("Válassz egy megfigyelt helyszínt a kártya szerkesztőjében.",language)));return;}
    const model=summarizeLocation(this._hass?.states?.[this.config.entity],this.config.location_id,language);
    card.append(this.labelled('h2',this.config.title||model.name||text("Helyszínösszefoglaló",language),'mdi:map-marker-outline'));
    if(model.error){const p=this.node('p',this._hass?model.error:text("Kapcsolódás a Home Assistanthoz…",language));p.setAttribute('role','status');card.append(p);return;}
    const state=this.node('p',model.status);state.className='status';card.append(state);
    const counts=this.node('div');counts.className='counts';
    for(const [n,label,icon] of [[model.active,text("aktívként követett műholdas esemény",language),'mdi:fire'],[model.multi,text("több forrás által észlelt esemény",language),'mdi:layers-outline']]){const p=this.node('p'),number=this.node('span',n??'—');number.className='number';p.append(number,this.labelled('span',label,icon));counts.append(p);}card.append(counts);
    if(model.active===null)card.append(this.node('p',text("A jelenlegi eseményszám nem állapítható meg.",language)));
    card.append(this.node('p',model.nearest===null?text("Nincs ellenőrizhető távolságadat ehhez a helyszínhez.",language):(language==='hu'?`Legközelebbi követett műholdas esemény a helyszín sugarán belül: ${model.nearest.toLocaleString(this._hass?.locale?.language||language,{maximumFractionDigits:2})} km`:`Nearest tracked satellite incident within this location’s radius: ${model.nearest.toLocaleString(this._hass?.locale?.language||language,{maximumFractionDigits:2})} km`)));
    if(Number.isFinite(model.monitoringRadius)&&Number.isFinite(model.alertRadius)&&model.alertRadius>0&&model.alertRadius<=model.monitoringRadius)
      card.append(this.labelled('p',(language==='hu'?`Megfigyelés: ${model.monitoringRadius} km · Riasztás: ${model.alertRadius} km`:`Monitoring: ${model.monitoringRadius} km · Alert: ${model.alertRadius} km`),'mdi:radar'));
    card.append(this.labelled('h3',text("Adatforrások",language),'mdi:satellite-variant'));
    const list=this.node('ul');for(const source of model.sources){if(!source||typeof source!=='object')continue;const row=this.node('li',`${source.name||source.provider||text("Ismeretlen forrás",language)}${source.satellite?' · '+source.satellite:''}: ${statusLabels(language)[source.status]||({delayed:text("Késleltetett",language),outage:text("Forráskiesés",language),auth_error:text("Hozzáférési hiba",language),no_product:text("Nincs termék",language)}[source.status])||text("Ismeretlen állapot",language)}`);const guidance=sourceGuidance(source,language);if(guidance){const hint=this.node('div',guidance);hint.className='muted';row.append(hint);}list.append(row);}card.append(list);
    const date=typeof model.received==='string'?new Date(model.received):null;
    const stamp=this.node('p',date&&!Number.isNaN(date.getTime())?(language==='hu'?`Legutóbbi sikeres adatátvétel: ${date.toLocaleString(this._hass?.locale?.language||language)}`:`Latest successful data receipt: ${date.toLocaleString(this._hass?.locale?.language||language)}`):text("Nincs adatátvételi időpont.",language));stamp.className='muted';card.append(stamp);
    card.append(this.labelled('h3',text("Tűzveszély-előrejelzés",language),'mdi:chart-line'));
    const forecast=summarizeForecast(this._hass?.states?.[this.config.forecast?.entity],this.config.forecast,this.config.location_id,new Date(),language);
    if(forecast.message)card.append(this.node('p',forecast.message));
    else {
      card.append(this.node('p',(language==='hu'?`${forecast.risk} · Érvényesség: ${forecast.validDate} (UTC terméknap)`:`${forecast.risk} · Valid for: ${forecast.validDate} (UTC product date)`)));
      card.append(this.node('p',forecast.freshness));
      if(forecast.received)card.append(this.node('p',(language==='hu'?`Sikeres lekérés: ${new Date(forecast.received).toLocaleString(this._hass?.locale?.language||language,{timeZone:this._hass?.config?.time_zone||'UTC'})}`:`Successful retrieval: ${new Date(forecast.received).toLocaleString(this._hass?.locale?.language||language,{timeZone:this._hass?.config?.time_zone||'UTC'})}`)));
      card.append(this.node('p',forecast.attribution),this.node('p',forecast.scope==='monitored_location'?text("Modell-előrejelzés a kijelölt helyszín közelére; nem hatósági riasztás. A lekérés ideje nem a modell kiadási ideje.",language):text("Modell-előrejelzés az otthonpont közelére; nem hatósági riasztás. A lekérés ideje nem a modell kiadási ideje.",language)));
    }
    card.append(this.labelled('h3',text("Hivatalos tűzgyújtási korlátozás",language),'mdi:information-outline'),this.node('p',text("Nincs kapcsolt adat; ebből a tilalom fennállása nem állapítható meg.",language)));
    const note=this.node('p',text("Az észlelések hiánya nem jelent tűzmentességet. A legutóbbi adatátvétel nem minden forrás frissessége és nem az esemény kezdete. A műholdas események nem hatóságilag igazolt tűzesetek.",language));note.className='muted';card.append(note);
    const button=this.node('button',text("Érzékelő részletei",language));button.onclick=()=>this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:this.config.entity},bubbles:true,composed:true}));card.append(button);
  }
}
customElements.define('ignis-location-summary',IgnisLocationSummary);
window.customCards=window.customCards||[];
window.customCards.push({type:'ignis-location-summary',name:'IGNIS helyszínösszefoglaló',description:'Egy kijelölt helyszín műholdas eseményei és forrásállapota.'});
