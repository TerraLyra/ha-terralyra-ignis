// Optional BM publication list. Explicit refresh only; no map coordinates or history writes.
export function visibleNotices(notices, filter) {
  return notices.filter(n => filter === 'all' || (filter === 'veg'
    ? n.fire_scope?.category === 'vegetation_fire_candidate'
    : n.fire_scope?.category !== 'local_asset_fire_candidate'));
}
const labels = {vegetation_fire_candidate:'Növényzettűz-jelölt',local_asset_fire_candidate:'Helyi épület- vagy járműtűz-jelölt',mixed_fire_candidate:'Vegyes tűzeset-jelölt',unknown:'Bizonytalan besorolás'};
class IgnisBmReports extends HTMLElement {
  setConfig(config) { this.config = config; this.filter = 'focus'; this.notices = []; this.attach(); this.render(); }
  set hass(value) { this._hass = value; }
  getCardSize() { return 7; }
  attach() { if (!this.shadowRoot) this.attachShadow({mode:'open'}); }
  node(tag,text,cls) { const n=document.createElement(tag); if(text)n.textContent=text;if(cls)n.className=cls;return n; }
  async refresh() {
    if(this.loading || !this._hass)return;
    this.loading=true;this.error='';this.render();
    try {
      const result=await this._hass.callWS({type:'call_service',domain:'terralyra_ignis',service:'get_official_reports',service_data:{},return_response:true});
      const response=result?.response;
      if(response?.status!=='available' || !Array.isArray(response.notices))throw Error('unavailable');
      this.notices=response.notices;this.fetched=response.fetched_at;this.loaded=true;
    } catch {this.notices=[];this.error='A BM OKF jelentései most nem kérhetők le. Próbáld újra később.';}
    finally {this.loading=false;this.render();}
  }
  render() {
    this.attach();const root=this.shadowRoot;root.replaceChildren();
    const style=this.node('style');style.textContent=`:host{display:block}*{box-sizing:border-box}ha-card{display:block;padding:20px;color:var(--primary-text-color,#183042);background:var(--card-background-color,white);border-radius:14px}h2{margin:0 0 12px}h3{font-size:18px}.bar{display:flex;gap:12px;flex-wrap:wrap}button,select{font:inherit;padding:10px;border:1px solid #8ba7b5;border-radius:8px;background:var(--card-background-color,white);color:inherit}button{cursor:pointer}.entry{display:block;width:100%;text-align:left;margin:10px 0}.entry[aria-pressed=true]{border:2px solid #00838f}.muted{opacity:.75;font-size:13px}.tag{font-size:13px;color:var(--primary-color,#007c85)}.detail{border-top:1px solid #b5c5ce;margin-top:16px;padding-top:12px}.text{white-space:pre-wrap;overflow-wrap:anywhere}.note{padding:12px;border-left:3px solid #c69c45}.title{display:block;margin-top:5px}a{color:var(--primary-color,#007c85)}strong{overflow-wrap:anywhere}`;root.append(style);
    const card=this.node('ha-card');root.append(card);card.append(this.node('h2','BM OKF jelentések'));
    const bar=this.node('div',null,'bar'),select=this.node('select');select.setAttribute('aria-label','Jelentések szűrése');
    for(const [v,t] of [['focus','Növényzettüzek és bizonytalan hírek'],['all','Minden jelentés'],['veg','Csak növényzettűz-jelöltek']]){const o=this.node('option',t);o.value=v;select.append(o)}
    select.value=this.filter;select.onchange=()=>{this.filter=select.value;this.render()};
    const refresh=this.node('button',this.loading?'Lekérés…':'Jelentések lekérése');refresh.disabled=this.loading;refresh.onclick=()=>this.refresh();bar.append(select,refresh);card.append(bar);
    card.append(this.node('p','Automatikus szöveges jelölés, nem hivatalos besorolás. A bizonytalan és vegyes esetek az alapnézetben megmaradnak.','muted'));
    if(this.error){const err=this.node('p',this.error,'note');err.setAttribute('role','alert');card.append(err);return;}
    if(!this.loaded){card.append(this.node('p','A lekéréshez nyomd meg a fenti gombot. A kártya az aktuális RSS-jelentéseket mutatja.','muted'));return;}
    const items=visibleNotices(this.notices,this.filter);
    if(!items.some(n=>n.url===this.selected))this.selected=items[0]?.url;
    const count=this.node('p',`${items.length} megjelenítve · ${this.notices.length-items.length} elrejtve a nézetben`,'muted');count.setAttribute('aria-live','polite');card.append(count);
    if(!items.length)card.append(this.node('p',this.notices.length?'Ebben a nézetben nincs megjeleníthető hír.':'Az aktuális feed nem tartalmaz jelentést.'));
    for(const n of items){const b=this.node('button',null,'entry');b.setAttribute('aria-pressed',String(n.url===this.selected));b.append(this.node('span',labels[n.fire_scope?.category]||labels.unknown,'tag'),this.node('strong',n.title,'title'));b.onclick=()=>{this.selected=n.url;this.render()};card.append(b)}
    const n=items.find(n=>n.url===this.selected);if(!n)return;
    const detail=this.node('section',null,'detail');detail.setAttribute('aria-label','Jelentés részletei');card.append(detail);
    detail.append(this.node('h3',n.title),this.node('p',`Közzétéve: ${n.published_at||'Nincs adat'}`,'muted'),this.node('p',n.description||'A forrás nem közölt leírást.','text'));
    if(n.description_status==='truncated')detail.append(this.node('p','A forrásszöveg a méretkorlát miatt rövidítve jelenik meg.','note'));
    const areas=n.fire_scope?.evidence?.filter(e=>e.kind==='area').map(e=>e.evidence)||[];
    detail.append(this.node('p',areas.length?`Területre utaló szöveg: ${areas.join('; ')}. Nem igazolt égett terület.`:'A kiterjedés nincs igazolva.'));
    detail.append(this.node('p','Nincs igazolt eseménykoordináta. A település középpontját nem jelöljük tűzhelyszínként. A jelentés nem műholdas észlelés.','note'));
    if(/^https:\/\/www\.katasztrofavedelem\.hu\/modules\/vesz\/esemeny\/[0-9]+$/.test(n.url)){const a=this.node('a','Eredeti jelentés ↗');a.href=n.url;a.target='_blank';a.rel='noopener noreferrer';detail.append(a)}
    detail.append(this.node('p',n.publisher||'BM OKF','muted'),this.node('p','A közzététel ideje nem feltétlenül az esemény kezdete. A feed nem teljes tűzeseti archívum.','muted'));
  }
}
customElements.define('ignis-bm-reports',IgnisBmReports);
window.customCards=window.customCards||[];
window.customCards.push({type:'ignis-bm-reports',name:'IGNIS BM OKF jelentések',description:'BM OKF hírek, szöveg és választható növényzettűz-fókusz.'});
