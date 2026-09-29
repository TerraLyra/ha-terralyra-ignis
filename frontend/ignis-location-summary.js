// Optional read-only card. Explicit entity/location association; no service calls.
const statusLabels = {available:'Adatforrások elérhetők',degraded:'Késleltetett adatellátás',partial:'Részleges adatellátás',initializing:'Első adatokra vár',unavailable:'Adatok nem érhetők el',no_coverage:'Nincs megfelelő forrás'};
export function summarizeLocation(entity, locationId) {
  const a=entity?.attributes;
  if(!a || a.location_id!==locationId || !Array.isArray(a.source_health))return {error:'A kiválasztott érzékelő nem ehhez a helyszínhez tartozik, vagy nem támogatott.'};
  const status=['unknown','unavailable'].includes(entity.state)?'unavailable':a.operational_status;
  const usable=['available','degraded','partial'].includes(status);
  const count=v=>usable && Number.isSafeInteger(v) && v>=0?v:null;
  return {name:a.location_name||locationId,status:statusLabels[status]||'Ismeretlen adatellátás',active:count(a.active_incidents),multi:count(a.multi_source_incidents),nearest:usable&&Number.isFinite(a.nearest_incident_distance_km)&&a.nearest_incident_distance_km>=0?a.nearest_incident_distance_km:null,sources:a.source_health,received:a.last_received_at};
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
  if(a.scope!=='near_home'||!number(a.sample_latitude)||!number(a.sample_longitude)||Math.abs(a.sample_latitude-binding.latitude)>0.000001||Math.abs(a.sample_longitude-binding.longitude)>0.000001)
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
  return {risk:riskLabels[day.risk],validDate:day.date,received:Number.isFinite(stamp)&&age>=0?new Date(stamp).toISOString():null,
    freshness:!Number.isFinite(stamp)||age<0?'Az adatátvétel ideje nem ellenőrizhető.':age>12*3600000?'Az adatátvétel több mint 12 órás; a frissítés késhet.':'Az adatátvétel 12 órán belüli.',
    attribution:typeof a.attribution==='string'?a.attribution:'EUMETSAT / LSA SAF'};
}
class IgnisLocationSummary extends HTMLElement {
  setConfig(config) {
    if(typeof config.entity!=='string'||!config.entity.startsWith('sensor.')||typeof config.location_id!=='string'||!config.location_id.trim())throw Error('Add meg az entity és location_id értékét.');
    if(config.forecast && (typeof config.forecast.entity!=='string'||!config.forecast.entity.startsWith('sensor.')))throw Error('Adj meg egy forecast.entity érzékelőt.');
    this.config={...config};if(!this.shadowRoot)this.attachShadow({mode:'open'});this.render();
  }
  set hass(value){this._hass=value;this.render();}
  getCardSize(){return 5;}
  node(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;}
  render(){
    if(!this.config||!this.shadowRoot)return;
    const root=this.shadowRoot;root.replaceChildren();
    const style=this.node('style',`:host{display:block}ha-card{display:block;padding:22px;background:var(--card-background-color,white);color:var(--primary-text-color,#183238);border-radius:16px;overflow-wrap:anywhere}h2{margin:0 0 12px;font-size:24px}h3{font-size:16px;margin-top:22px}.status{padding:12px;background:var(--secondary-background-color,#eef4f4);border-radius:8px}.counts{display:flex;gap:24px;flex-wrap:wrap}.counts p{flex:1;min-width:120px}.number{display:block;font-size:36px;font-weight:600}.muted{font-size:13px;color:var(--secondary-text-color,#596e73)}li{margin:8px 0}button{font:inherit;padding:9px;border:1px solid var(--divider-color,#aaa);border-radius:8px;background:transparent;color:inherit;cursor:pointer}`);root.append(style);
    const card=this.node('ha-card');root.append(card);
    const model=summarizeLocation(this._hass?.states?.[this.config.entity],this.config.location_id);
    card.append(this.node('h2',this.config.title||model.name||'Helyszínösszefoglaló'));
    if(model.error){const p=this.node('p',this._hass?model.error:'Kapcsolódás a Home Assistanthoz…');p.setAttribute('role','status');card.append(p);return;}
    const state=this.node('p',model.status);state.className='status';card.append(state);
    const counts=this.node('div');counts.className='counts';
    for(const [n,label] of [[model.active,'aktívként követett műholdas esemény'],[model.multi,'több forrás által észlelt esemény']]){const p=this.node('p'),number=this.node('span',n??'—');number.className='number';p.append(number,this.node('span',label));counts.append(p);}card.append(counts);
    if(model.active===null)card.append(this.node('p','A jelenlegi eseményszám nem állapítható meg.'));
    card.append(this.node('p',model.nearest===null?'Nincs ellenőrizhető távolságadat ehhez a helyszínhez.':`Legközelebbi követett műholdas esemény a helyszín sugarán belül: ${model.nearest.toLocaleString(this._hass?.locale?.language||'hu',{maximumFractionDigits:2})} km`));
    card.append(this.node('h3','Adatforrások'));
    const list=this.node('ul');for(const source of model.sources){if(!source||typeof source!=='object')continue;list.append(this.node('li',`${source.name||source.provider||'Ismeretlen forrás'}${source.satellite?' · '+source.satellite:''}: ${statusLabels[source.status]||({delayed:'Késleltetett',outage:'Forráskiesés',auth_error:'Hozzáférési hiba',no_product:'Nincs termék'}[source.status])||'Ismeretlen állapot'}`));}card.append(list);
    const date=typeof model.received==='string'?new Date(model.received):null;
    const stamp=this.node('p',date&&!Number.isNaN(date.getTime())?`Legutóbbi sikeres adatátvétel: ${date.toLocaleString(this._hass?.locale?.language||'hu')}`:'Nincs adatátvételi időpont.');stamp.className='muted';card.append(stamp);
    card.append(this.node('h3','Tűzveszély-előrejelzés'));
    const forecast=summarizeForecast(this._hass?.states?.[this.config.forecast?.entity],this.config.forecast,this.config.location_id);
    if(forecast.message)card.append(this.node('p',forecast.message));
    else {
      card.append(this.node('p',`${forecast.risk} · Érvényesség: ${forecast.validDate} (UTC terméknap)`));
      card.append(this.node('p',forecast.freshness));
      if(forecast.received)card.append(this.node('p',`Sikeres lekérés: ${new Date(forecast.received).toLocaleString(this._hass?.locale?.language||'hu',{timeZone:this._hass?.config?.time_zone||'UTC'})}`));
      card.append(this.node('p',forecast.attribution),this.node('p','Modell-előrejelzés az otthonpont közelére; nem hatósági riasztás. A lekérés ideje nem a modell kiadási ideje.'));
    }
    card.append(this.node('h3','Hivatalos tűzgyújtási korlátozás'),this.node('p','Nincs kapcsolt adat; ebből a tilalom fennállása nem állapítható meg.'));
    const note=this.node('p','Az észlelések hiánya nem jelent tűzmentességet. A legutóbbi adatátvétel nem minden forrás frissessége és nem az esemény kezdete. A műholdas események nem hatóságilag igazolt tűzesetek.');note.className='muted';card.append(note);
    const button=this.node('button','Érzékelő részletei');button.onclick=()=>this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:this.config.entity},bubbles:true,composed:true}));card.append(button);
  }
}
customElements.define('ignis-location-summary',IgnisLocationSummary);
window.customCards=window.customCards||[];
window.customCards.push({type:'ignis-location-summary',name:'IGNIS helyszínösszefoglaló',description:'Egy kijelölt helyszín műholdas eseményei és forrásállapota.'});
