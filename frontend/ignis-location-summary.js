// Optional read-only card. Explicit entity/location association; no service calls.
const statusLabels = {available:'Adatforrások elérhetők',degraded:'Késleltetett adatellátás',partial:'Részleges adatellátás',initializing:'Első adatokra vár',unavailable:'Adatok nem érhetők el',no_coverage:'Nincs megfelelő forrás'};
// Describe only the reported state; never infer an all-clear or a scheduled retry.
export function sourceGuidance(source) {
  if(!source || typeof source!=='object')return '';
  if(source.status==='auth_error')return 'Ellenőrizd a forrás hozzáférési adatait az IGNIS beállításaiban.';
  if(source.retrieval_status==='failed'||source.status==='outage')return 'A lekérés sikertelen. Ha tartósan fennáll, ellenőrizd az IGNIS diagnosztikáját és a hálózati kapcsolatot.';
  return ({
    delayed:'Az adatok késnek. A sikeres lekérés önmagában nem jelent friss műholdas megfigyelést.',
    no_product:'Jelenleg nincs elérhető adatcsomag; ebből nem következik, hogy nincs tűz.',
    initializing:'Várd meg az első lekérés eredményét. Ha ez az állapot tartós, ellenőrizd az IGNIS diagnosztikáját.'
  })[source.status]||'';
}
export function summarizeLocation(entity, locationId) {
  const a=entity?.attributes;
  if(!a || a.location_id!==locationId || !Array.isArray(a.source_health))return {error:'A kiválasztott érzékelő nem ehhez a helyszínhez tartozik, vagy nem támogatott.'};
  const status=['unknown','unavailable'].includes(entity.state)?'unavailable':a.operational_status;
  const usable=['available','degraded','partial'].includes(status);
  const count=v=>usable && Number.isSafeInteger(v) && v>=0?v:null;
  return {name:a.location_name||locationId,status:statusLabels[status]||'Ismeretlen adatellátás',active:count(a.active_incidents),multi:count(a.multi_source_incidents),nearest:usable&&Number.isFinite(a.nearest_incident_distance_km)&&a.nearest_incident_distance_km>=0?a.nearest_incident_distance_km:null,sources:a.source_health,received:a.last_received_at,monitoringRadius:a.monitoring_radius_km,alertRadius:a.alert_radius_km};
}
// FRMv3 validity dates are UTC product dates; generated_at is retrieval time.
const riskLabels={low:'Alacsony',moderate:'Mérsékelt',high:'Magas',very_high:'Nagyon magas',extreme:'Szélsőséges'};
export function summarizeForecast(entity, binding, locationId, now=new Date()) {
  if(!binding)return {message:'Ehhez a kártyához nincs kapcsolt előrejelzés.'};
  const a=entity?.attributes;
  const number=v=>typeof v==='number'&&Number.isFinite(v);
  if(binding.location_id!==locationId || !number(binding.latitude) || !number(binding.longitude) || Math.abs(binding.latitude)>90 || Math.abs(binding.longitude)>180)
    return {message:'Az előrejelzés helyszín-hozzárendelése hiányos vagy eltérő.'};
  if(!a || ['unknown','unavailable'].includes(entity.state))return {message:'Az előrejelzés jelenleg nem érhető el.'};
  if(a.scope==='monitored_location') {
    if(a.location_id!==locationId || a.provider!=='eumetsat_lsa_saf_frmv3' || a.product!=='FRMv3' ||
       !number(a.latitude)||!number(a.longitude)||a.latitude!==binding.latitude||a.longitude!==binding.longitude||
       !number(binding.radius_km)||binding.radius_km<1||binding.radius_km>500||a.forecast_radius_km!==binding.radius_km)
      return {message:'Az előrejelzés helyszíne vagy sugara nem egyezik a hozzárendeléssel.'};
  } else if(a.scope!=='near_home'||!number(a.sample_latitude)||!number(a.sample_longitude)||Math.abs(a.sample_latitude-binding.latitude)>0.000001||Math.abs(a.sample_longitude-binding.longitude)>0.000001)
    return {message:'Az előrejelzés mintavételi pontja nem egyezik a hozzárendelt helyszínnel.'};
  if(!Array.isArray(a.forecast)||!Number.isFinite(now.getTime()))return {message:'Az előrejelzés érvényessége nem ellenőrizhető.'};
  const today=now.toISOString().slice(0,10);
  const days=a.forecast.filter(d=>d&&typeof d.date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d.date)&&Number.isFinite(Date.parse(d.date))&&new Date(d.date).toISOString().slice(0,10)===d.date);
  const matches=days.filter(d=>d.date===today);
  if(matches.length!==1)return {message:days.length&&days.every(d=>d.date<today)?'Az előrejelzés lejárt; mai érték nem jeleníthető meg.':'A mai UTC terméknapra nincs egyértelmű előrejelzés.'};
  const day=matches[0];
  if(!Object.hasOwn(riskLabels,day.risk))return {message:'A mai kockázati kategória ismeretlen.'};
  const stamp=typeof a.generated_at==='string'&&/(Z|[+-]\d{2}:\d{2})$/.test(a.generated_at)?Date.parse(a.generated_at):NaN;
  const age=now.getTime()-stamp;
  return {scope:a.scope,risk:riskLabels[day.risk],validDate:day.date,received:Number.isFinite(stamp)&&age>=0?new Date(stamp).toISOString():null,
    freshness:!Number.isFinite(stamp)||age<0?'Az adatátvétel ideje nem ellenőrizhető.':age>12*3600000?'Az adatátvétel több mint 12 órás; a frissítés késhet.':'Az adatátvétel 12 órán belüli.',
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
// Setup review is descriptive: it cannot inspect notification automation delivery.
export function setupReview(entity, locationId) {
  const a=entity?.attributes;
  if(!a || a.location_id!==locationId)return ['A helyszín hozzárendelése még nem ellenőrizhető.'];
  const valid=Number.isFinite(a.monitoring_radius_km)&&Number.isFinite(a.alert_radius_km)&&a.alert_radius_km>0&&a.alert_radius_km<=a.monitoring_radius_km;
  return [
    `Helyszín: ${a.location_name||locationId}`,
    valid?`Megfigyelés: ${a.monitoring_radius_km} km · Riasztás: ${a.alert_radius_km} km`:'Ellenőrizd a sugarakat az IGNIS beállításaiban: a riasztási sugár legyen pozitív és legfeljebb a megfigyelési sugár.',
    ['unknown','unavailable'].includes(entity.state)?'Az adatellátás jelenleg nem ellenőrizhető.':(statusLabels[a.operational_status]||'Ismeretlen adatellátás'),
    'Telefonos értesítés: külön blueprint és értesítési cél szükséges. A kártya nem ellenőrzi a meglévő automatizálást vagy a kézbesítést.'
  ];
}
class IgnisLocationSummaryEditor extends HTMLElement {
  setConfig(config){this.config={...config};this.render();}
  set hass(value){
    this._hass=value;
    const signature=JSON.stringify(locationChoices(value?.states));
    if(signature!==this._choicesSignature){this._choicesSignature=signature;this.render();}
    else this.refreshReview();
  }
  node(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;}
  update(patch){
    this.config={...this.config,...patch};
    this.refreshReview();
    this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:{...this.config}},bubbles:true,composed:true}));
  }
  refreshReview(){
    if(!this.reviewHost||!this.config)return;
    this.reviewHost.replaceChildren(this.node('h3','Beállítások áttekintése'));
    for(const text of setupReview(this._hass?.states?.[this.config.entity],this.config.location_id))this.reviewHost.append(this.node('p',text));
  }
  render(){
    if(!this.config)return;
    if(!this.shadowRoot)this.attachShadow({mode:'open'});
    const root=this.shadowRoot;root.replaceChildren();
    root.append(this.node('style',`:host{display:block;color:var(--primary-text-color);overflow-wrap:anywhere}label{display:block;margin:16px 0}select,input{display:block;box-sizing:border-box;width:100%;min-width:0;font:inherit;padding:12px;margin-top:8px;color:inherit;background:var(--card-background-color,white);border:1px solid var(--divider-color,#999);border-radius:8px}p{line-height:1.5}`));
    const choices=locationChoices(this._hass?.states);
    const label=this.node('label','Megfigyelt helyszín'),select=this.node('select');
    select.setAttribute('aria-label','Megfigyelt helyszín');
    const placeholder=this.node('option','Válassz helyszínt…');placeholder.value='';placeholder.disabled=true;select.append(placeholder);
    for(const choice of choices){const option=this.node('option',`${choice.name} — ${choice.entity}`);option.value=choice.entity;select.append(option);}
    if(this.config.entity&&!choices.some(c=>c.entity===this.config.entity)){
      const missing=this.node('option',`Jelenleg nem elérhető: ${this.config.entity}`);missing.value=this.config.entity;missing.disabled=true;select.append(missing);
    }
    select.value=this.config.entity||'';
    select.onchange=()=>{
      const choice=locationChoices(this._hass?.states).find(c=>c.entity===select.value);
      if(choice)this.update({entity:choice.entity,location_id:choice.location_id});
    };
    label.append(select);root.append(label);
    if(!choices.length){const empty=this.node('p',this._hass?'Még nincs választható helyszínérzékelő. Engedélyezz egy megfigyelt helyszínt az IGNIS beállításaiban, majd várd meg az érzékelő létrejöttét.':'Kapcsolódás a Home Assistanthoz…');empty.setAttribute('role','status');root.append(empty);}
    root.append(this.node('p','A helyszínazonosítót a kiválasztott érzékelőből vesszük át. A sugarakat az IGNIS beállításaiban módosíthatod.'));
    const titleLabel=this.node('label','Egyéni cím (nem kötelező)'),title=this.node('input');title.type='text';title.value=this.config.title||'';title.setAttribute('aria-label','Egyéni cím (nem kötelező)');
    title.onchange=()=>this.update({title:title.value});titleLabel.append(title);root.append(titleLabel);
    const review=this.node('section');review.setAttribute('aria-label','Beállítások áttekintése');this.reviewHost=review;this.refreshReview();
    root.append(review);
    root.append(this.node('p','Az opcionális előrejelzés hozzárendelését a kódszerkesztőben állíthatod be. A meglévő hozzárendelés megmarad; helyszínváltás után ellenőrizd, hogy az új helyszínhez tartozik-e.'));
  }
}
customElements.define('ignis-location-summary-editor',IgnisLocationSummaryEditor);
class IgnisLocationSummary extends HTMLElement {
  static getConfigElement(){return document.createElement('ignis-location-summary-editor');}
  static getStubConfig(){return {type:'custom:ignis-location-summary'};}

  setConfig(config) {
    const unconfigured=config.entity===undefined&&config.location_id===undefined;
    if(!unconfigured&&(typeof config.entity!=='string'||!config.entity.startsWith('sensor.')||typeof config.location_id!=='string'||!config.location_id.trim()))throw Error('Add meg az entity és location_id értékét.');
    if(config.forecast && (typeof config.forecast.entity!=='string'||!config.forecast.entity.startsWith('sensor.')))throw Error('Adj meg egy forecast.entity érzékelőt.');
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
    if(!this.config||!this.shadowRoot)return;
    const root=this.shadowRoot;root.replaceChildren();
    const style=this.node('style',`:host{display:block}ha-card{display:block;padding:22px;background:var(--card-background-color,white);color:var(--primary-text-color,#183238);border-radius:16px;overflow-wrap:anywhere}h2{margin:0 0 12px;font-size:24px}h3{font-size:16px;margin-top:22px}.with-icon{display:flex;align-items:baseline;gap:8px}.with-icon ha-icon{--mdc-icon-size:18px;width:18px;height:18px;flex:0 0 18px;align-self:flex-start;margin-top:2px;color:var(--secondary-text-color,#596e73)}.with-icon>span{min-width:0}.status{padding:12px;background:var(--secondary-background-color,#eef4f4);border-radius:8px}.counts{display:flex;gap:24px;flex-wrap:wrap}.counts p{flex:1;min-width:120px}.number{display:block;font-size:36px;font-weight:600}.muted{font-size:13px;color:var(--secondary-text-color,#596e73)}li{margin:8px 0}button{font:inherit;padding:9px;border:1px solid var(--divider-color,#aaa);border-radius:8px;background:transparent;color:inherit;cursor:pointer}`);root.append(style);
    const card=this.node('ha-card');root.append(card);
    if(!this.config.entity){card.append(this.node('h2','Helyszínösszefoglaló'),this.node('p','Válassz egy megfigyelt helyszínt a kártya szerkesztőjében.'));return;}
    const model=summarizeLocation(this._hass?.states?.[this.config.entity],this.config.location_id);
    card.append(this.labelled('h2',this.config.title||model.name||'Helyszínösszefoglaló','mdi:map-marker-outline'));
    if(model.error){const p=this.node('p',this._hass?model.error:'Kapcsolódás a Home Assistanthoz…');p.setAttribute('role','status');card.append(p);return;}
    const state=this.node('p',model.status);state.className='status';card.append(state);
    const counts=this.node('div');counts.className='counts';
    for(const [n,label,icon] of [[model.active,'aktívként követett műholdas esemény','mdi:fire'],[model.multi,'több forrás által észlelt esemény','mdi:layers-outline']]){const p=this.node('p'),number=this.node('span',n??'—');number.className='number';p.append(number,this.labelled('span',label,icon));counts.append(p);}card.append(counts);
    if(model.active===null)card.append(this.node('p','A jelenlegi eseményszám nem állapítható meg.'));
    card.append(this.node('p',model.nearest===null?'Nincs ellenőrizhető távolságadat ehhez a helyszínhez.':`Legközelebbi követett műholdas esemény a helyszín sugarán belül: ${model.nearest.toLocaleString(this._hass?.locale?.language||'hu',{maximumFractionDigits:2})} km`));
    if(Number.isFinite(model.monitoringRadius)&&Number.isFinite(model.alertRadius)&&model.alertRadius>0&&model.alertRadius<=model.monitoringRadius)
      card.append(this.labelled('p',`Megfigyelés: ${model.monitoringRadius} km · Riasztás: ${model.alertRadius} km`,'mdi:radar'));
    card.append(this.labelled('h3','Adatforrások','mdi:satellite-variant'));
    const list=this.node('ul');for(const source of model.sources){if(!source||typeof source!=='object')continue;const row=this.node('li',`${source.name||source.provider||'Ismeretlen forrás'}${source.satellite?' · '+source.satellite:''}: ${statusLabels[source.status]||({delayed:'Késleltetett',outage:'Forráskiesés',auth_error:'Hozzáférési hiba',no_product:'Nincs termék'}[source.status])||'Ismeretlen állapot'}`);const guidance=sourceGuidance(source);if(guidance){const hint=this.node('div',guidance);hint.className='muted';row.append(hint);}list.append(row);}card.append(list);
    const date=typeof model.received==='string'?new Date(model.received):null;
    const stamp=this.node('p',date&&!Number.isNaN(date.getTime())?`Legutóbbi sikeres adatátvétel: ${date.toLocaleString(this._hass?.locale?.language||'hu')}`:'Nincs adatátvételi időpont.');stamp.className='muted';card.append(stamp);
    card.append(this.labelled('h3','Tűzveszély-előrejelzés','mdi:chart-line'));
    const forecast=summarizeForecast(this._hass?.states?.[this.config.forecast?.entity],this.config.forecast,this.config.location_id);
    if(forecast.message)card.append(this.node('p',forecast.message));
    else {
      card.append(this.node('p',`${forecast.risk} · Érvényesség: ${forecast.validDate} (UTC terméknap)`));
      card.append(this.node('p',forecast.freshness));
      if(forecast.received)card.append(this.node('p',`Sikeres lekérés: ${new Date(forecast.received).toLocaleString(this._hass?.locale?.language||'hu',{timeZone:this._hass?.config?.time_zone||'UTC'})}`));
      card.append(this.node('p',forecast.attribution),this.node('p',forecast.scope==='monitored_location'?'Modell-előrejelzés a kijelölt helyszín közelére; nem hatósági riasztás. A lekérés ideje nem a modell kiadási ideje.':'Modell-előrejelzés az otthonpont közelére; nem hatósági riasztás. A lekérés ideje nem a modell kiadási ideje.'));
    }
    card.append(this.labelled('h3','Hivatalos tűzgyújtási korlátozás','mdi:information-outline'),this.node('p','Nincs kapcsolt adat; ebből a tilalom fennállása nem állapítható meg.'));
    const note=this.node('p','Az észlelések hiánya nem jelent tűzmentességet. A legutóbbi adatátvétel nem minden forrás frissessége és nem az esemény kezdete. A műholdas események nem hatóságilag igazolt tűzesetek.');note.className='muted';card.append(note);
    const button=this.node('button','Érzékelő részletei');button.onclick=()=>this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:this.config.entity},bubbles:true,composed:true}));card.append(button);
  }
}
customElements.define('ignis-location-summary',IgnisLocationSummary);
window.customCards=window.customCards||[];
window.customCards.push({type:'ignis-location-summary',name:'IGNIS helyszínösszefoglaló',description:'Egy kijelölt helyszín műholdas eseményei és forrásállapota.'});
