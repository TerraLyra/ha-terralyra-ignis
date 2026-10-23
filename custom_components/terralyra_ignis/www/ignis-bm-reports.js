// Optional BM publication list. Explicit refresh only; no map coordinates or history writes.
export function visibleNotices(notices, filter) {
  return notices.filter(n => filter === 'all' || (filter === 'veg'
    ? n.fire_scope?.category === 'vegetation_fire_candidate'
    : !['local_asset_fire_candidate', 'non_fire_report_candidate'].includes(n.fire_scope?.category)));
}
const labels = {non_fire_report_candidate:'Baleseti jelentés · tűz nincs említve',vegetation_fire_candidate:'Növényzettűz-jelölt',local_asset_fire_candidate:'Helyi épület- vagy járműtűz-jelölt',mixed_fire_candidate:'Vegyes tűzeset-jelölt',unknown:'Bizonytalan besorolás'};
const english={"BM OKF jelentések": "BM OKF reports", "Jelentések szűrése": "Filter reports", "Növényzettüzek és bizonytalan hírek": "Vegetation fires and uncertain reports", "Minden jelentés": "All reports", "Csak növényzettűz-jelöltek": "Vegetation fire candidates only", "Lekérés…": "Fetching…", "Jelentések lekérése": "Fetch reports", "Automatikus szöveges jelölés, nem hivatalos besorolás. A bizonytalan és vegyes esetek az alapnézetben megmaradnak.": "Automatic text classification, not an official category. Uncertain and mixed reports remain in the default view.", "A lekéréshez nyomd meg a fenti gombot. A kártya az aktuális RSS-jelentéseket mutatja.": "Use the button above to fetch current RSS reports.", "A BM OKF jelentései most nem kérhetők le. Próbáld újra később.": "BM OKF reports could not be retrieved. Try again later.", "Ebben a nézetben nincs megjeleníthető hír.": "No reports match this view.", "Az aktuális feed nem tartalmaz jelentést.": "The current feed contains no reports.", "Jelentés részletei": "Report details", "A forrás nem közölt leírást.": "The source did not provide a description.", "A forrásszöveg a méretkorlát miatt rövidítve jelenik meg.": "Source text is shortened because of the size limit.", "A kiterjedés nincs igazolva.": "The affected area is not verified.", "Nincs igazolt eseménykoordináta. A település középpontját nem jelöljük tűzhelyszínként. A jelentés nem műholdas észlelés.": "No verified incident coordinates. Settlement centres are not used as fire locations. This report is not a satellite observation.", "Eredeti jelentés ↗": "Original report ↗", "A közzététel ideje nem feltétlenül az esemény kezdete. A feed nem teljes tűzeseti archívum.": "Publication time is not necessarily the incident start. This feed is not a complete fire archive.", "Baleseti jelentés · tűz nincs említve": "Accident report · no fire mentioned", "Növényzettűz-jelölt": "Vegetation fire candidate", "Helyi épület- vagy járműtűz-jelölt": "Local building or vehicle fire candidate", "Vegyes tűzeset-jelölt": "Mixed fire candidate", "Bizonytalan besorolás": "Uncertain classification"};
class IgnisBmReports extends HTMLElement {
  setConfig(config) { this.config = config; this.filter = 'focus'; this.notices = []; this.attach(); this.render(); }
  set hass(value) { const previous=this._hass?.language;this._hass = value;if(previous!==value?.language)this.render(); }
  get hu(){return !this._hass?.language||this._hass.language.startsWith('hu');}
  t(value){return this.hu?value:(english[value]||value);}
  getCardSize() { return 7; }
  attach() { if (!this.shadowRoot) this.attachShadow({mode:'open'}); }
  node(tag,text,cls) { const n=document.createElement(tag); if(text)n.textContent=this.t(text);if(cls)n.className=cls;return n; }
  formatTime(value) {if(typeof value!=='string'||!/(Z|[+-]\d\d:\d\d)$/.test(value)||!Number.isFinite(Date.parse(value)))return this.hu?'Nincs adat':'Not provided';return new Intl.DateTimeFormat(this.hu?'hu-HU':'en-GB',{dateStyle:'short',timeStyle:'long',timeZone:this._hass?.config?.time_zone||'UTC'}).format(new Date(value));}
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
    const focused=this.shadowRoot?.activeElement?.dataset.focusKey;
    this.renderContent();
    if(focused)Array.from(this.shadowRoot.querySelectorAll('[data-focus-key]')).find(n=>n.dataset.focusKey===focused)?.focus({preventScroll:true});
  }
  renderContent() {
    this.attach();const root=this.shadowRoot;root.replaceChildren();
    const style=this.node('style');style.textContent=`:host{display:block}*{box-sizing:border-box}ha-card{display:block;padding:20px;color:var(--primary-text-color,#183042);background:var(--card-background-color,white);border-radius:14px}h2{margin:0 0 12px}h3{font-size:18px}.bar{display:flex;gap:12px;flex-wrap:wrap}button,select{min-height:44px;font:inherit;padding:10px;border:1px solid #8ba7b5;border-radius:8px;background:var(--card-background-color,white);color:inherit}button{cursor:pointer}button:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid var(--primary-color,#007c85);outline-offset:3px}.entry{display:block;width:100%;text-align:left;margin:10px 0}.entry[aria-pressed=true]{border:2px solid #00838f}.muted{color:var(--secondary-text-color,#526471);font-size:13px}.tag{font-size:13px;color:var(--primary-color,#007c85)}.detail{border-top:1px solid #b5c5ce;margin-top:16px;padding-top:12px}.text{white-space:pre-wrap;overflow-wrap:anywhere}.note{padding:12px;border-left:3px solid #c69c45}.title{display:block;margin-top:5px}a{color:var(--primary-color,#007c85)}strong{overflow-wrap:anywhere}`;root.append(style);
    const card=this.node('ha-card');root.append(card);card.append(this.node('h2','BM OKF jelentések'));
    const bar=this.node('div',null,'bar'),select=this.node('select');select.setAttribute('aria-label',this.t('Jelentések szűrése'));select.dataset.focusKey='filter';
    for(const [v,t] of [['focus','Növényzettüzek és bizonytalan hírek'],['all','Minden jelentés'],['veg','Csak növényzettűz-jelöltek']]){const o=this.node('option',t);o.value=v;select.append(o)}
    select.value=this.filter;select.onchange=()=>{this.filter=select.value;this.render()};
    const refresh=this.node('button',this.loading?'Lekérés…':'Jelentések lekérése');refresh.dataset.focusKey='refresh';refresh.setAttribute('aria-disabled',String(Boolean(this.loading)));refresh.onclick=()=>this.refresh();bar.append(select,refresh);card.append(bar);
    card.append(this.node('p','Automatikus szöveges jelölés, nem hivatalos besorolás. A bizonytalan és vegyes esetek az alapnézetben megmaradnak.','muted'));
    if(this.error){const err=this.node('p',this.error,'note');err.setAttribute('role','alert');card.append(err);return;}
    if(!this.loaded){card.append(this.node('p','A lekéréshez nyomd meg a fenti gombot. A kártya az aktuális RSS-jelentéseket mutatja.','muted'));return;}
    const items=visibleNotices(this.notices,this.filter);
    if(!items.some(n=>n.url===this.selected))this.selected=items[0]?.url;
    const count=this.node('p',this.hu?`${items.length} megjelenítve · ${this.notices.length-items.length} elrejtve a nézetben`:`${items.length} shown · ${this.notices.length-items.length} hidden in this view`,'muted');count.setAttribute('aria-live','polite');card.append(count);
    if(!items.length)card.append(this.node('p',this.notices.length?'Ebben a nézetben nincs megjeleníthető hír.':'Az aktuális feed nem tartalmaz jelentést.'));
    for(const n of items){const b=this.node('button',null,'entry');b.dataset.focusKey=`notice:${n.url}`;b.setAttribute('aria-expanded',String(n.url===this.selected));b.setAttribute('aria-controls','notice-detail');b.setAttribute('aria-pressed',String(n.url===this.selected));b.append(this.node('span',labels[n.fire_scope?.category]||labels.unknown,'tag'),this.node('strong',n.title,'title'));b.onclick=()=>{this.selected=n.url;this.render()};card.append(b)}
    const n=items.find(n=>n.url===this.selected);if(!n)return;
    const detail=this.node('section',null,'detail');detail.id='notice-detail';detail.setAttribute('aria-label',this.t('Jelentés részletei'));Array.from(card.querySelectorAll('.entry')).find(b=>b.dataset.focusKey===`notice:${n.url}`)?.after(detail);
    detail.append(this.node('h3',n.title),this.node('p',`${this.hu?'Közzétéve':'Published'}: ${this.formatTime(n.published_at)}`,'muted'),this.node('p',n.description||'A forrás nem közölt leírást.','text'));
    if(n.description_status==='truncated')detail.append(this.node('p','A forrásszöveg a méretkorlát miatt rövidítve jelenik meg.','note'));
    const areas=n.fire_scope?.evidence?.filter(e=>e.kind==='area').map(e=>e.evidence)||[];
    detail.append(this.node('p',areas.length?(this.hu?`Területre utaló szöveg: ${areas.join('; ')}. Nem igazolt égett terület.`:`Source area wording: ${areas.join('; ')}. Not a verified burned area.`):'A kiterjedés nincs igazolva.'));
    detail.append(this.node('p','Nincs igazolt eseménykoordináta. A település középpontját nem jelöljük tűzhelyszínként. A jelentés nem műholdas észlelés.','note'));
    if(/^https:\/\/www\.katasztrofavedelem\.hu\/modules\/vesz\/esemeny\/[0-9]+$/.test(n.url)){const a=this.node('a','Eredeti jelentés ↗');a.href=n.url;a.target='_blank';a.rel='noopener noreferrer';detail.append(a)}
    detail.append(this.node('p',n.publisher||'BM OKF','muted'),this.node('p','A közzététel ideje nem feltétlenül az esemény kezdete. A feed nem teljes tűzeseti archívum.','muted'));
  }
}
customElements.define('ignis-bm-reports',IgnisBmReports);
window.customCards=window.customCards||[];
window.customCards.push({type:'ignis-bm-reports',name:'IGNIS BM OKF jelentések',description:'BM OKF hírek, szöveg és választható növényzettűz-fókusz.'});
