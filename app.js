(() => {
  const baseFoods = (window.CATFOOD_DATA || []).map(x => ({...x, dataset:x.dataset || 'pierson_2017'}));
  const meta = window.CATFOOD_META || {};
  const aliasRows = (window.CATFOOD_ALIASES || []).filter(a=>a&&a.source_id&&a.verified===true);
  const aliasById = new Map(aliasRows.map(a=>[a.source_id,a]));
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const readJSON = (k, fallback) => { try { return JSON.parse(localStorage.getItem(k)) ?? fallback; } catch { return fallback; } };
  const state = {
    view:'browse', query:'', visible:48,
    favorites:new Set(readJSON('cfc_favorites',[])),
    compare:readJSON('cfc_compare',[]).slice(0,4),
    custom:readJSON('cfc_custom',[]),
    settings:{carbTarget:10,phosTarget:null,storeMode:false,...readJSON('cfc_settings',{})},
    quick:{carb:true,complete:false,favorites:false,wet:false,seafood:false},
    filters:{brand:'',carbMax:null,proteinMin:null,phosMax:null,fatMax:null,source:'',form:'',texture:'',hideRx:false,excludeSeafood:false,completeOnly:false},
    sort:'carb_asc'
  };

  const persist = () => {
    localStorage.setItem('cfc_favorites',JSON.stringify([...state.favorites]));
    localStorage.setItem('cfc_compare',JSON.stringify(state.compare));
    localStorage.setItem('cfc_custom',JSON.stringify(state.custom));
    localStorage.setItem('cfc_settings',JSON.stringify(state.settings));
  };
  const customNormalized = () => state.custom.map(x=>({...x,dataset:'custom',verification_status:'user',source_year:new Date().getFullYear(),prescription:!!x.prescription,form:x.form||'wet',data_complete:x.protein_cal_pct!=null&&x.fat_cal_pct!=null&&x.carb_cal_pct!=null&&x.phosphorus_mg_per_100kcal!=null}));
  const aliasFor = f => aliasById.get(f.id) || null;
  const aliasSearchValues = f => { const a=aliasFor(f); return a ? [a.current_name,...(a.aliases||[])].filter(Boolean) : []; };
  const seafoodText = f => `${f.line||''} ${f.product||''} ${f.style||''}`.toLowerCase().replace(/fish[-\s]?free/g,'');
  const isSeafood = f => /seafood|fish|tuna|salmon|trout|mackerel|sardine|shrimp|crab|lobster|clam|mussel|prawn|tilapia|cod|sole|whitefish|oceanfish|herring|pollock|haddock|hoki|anchov|bonito|seabass|sea bass|halibut|snapper|krill|calamari|squid|oyster|scallop/.test(seafoodText(f));
  const textureText = f => `${f.style||''} ${f.line||''} ${f.product||''}`.toLowerCase();
  const textureMatches = (f,t) => { const x=textureText(f); const pats={pate:/p[âa]t[eé]|\bpate\b|\bloaf\b/,shreds:/shred|flake/,pieces:/minc|\bbit(s)?\b|chunk|morsel|\bcut(s)?\b|slice/,gravy:/gravy|sauce|stew/,broth:/broth|consomm|aspic/,mousse:/mousse/}; return !t || !!pats[t]?.test(x); };
  const applyStoreMode = () => { document.body.classList.toggle('store-mode',!!state.settings.storeMode); const b=$('#storeModeBtn'); if(b){b.classList.toggle('active',!!state.settings.storeMode);b.setAttribute('aria-pressed',String(!!state.settings.storeMode));b.textContent=state.settings.storeMode?'✓ Store mode':'🛒 Store mode';} }; 
  const allFoods = () => [...new Map([...baseFoods,...customNormalized()].map(x=>[x.id,x])).values()];
  const esc = s => String(s ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const fmt = (v,d=0) => v == null || Number.isNaN(v) ? '—' : Number(v).toFixed(d).replace(/\.0$/,'');
  const normalizeSearch = value => String(value ?? '')
    .normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
    .toLowerCase().replace(/&/g,' and ').replace(/[’']/g,'')
    .replace(/[^a-z0-9]+/g,' ').replace(/\s+/g,' ').trim();
  const searchTokens = query => normalizeSearch(query).split(' ').filter(Boolean);
  const foodSearchText = f => normalizeSearch([
    f.brand, f.line, f.product, f.style, f.source_name, f.dataset, f.form,
    ...aliasSearchValues(f)
  ].filter(Boolean).join(' '));
  const matchesSearch = (f, query) => {
    const tokens = searchTokens(query);
    if(!tokens.length) return true;
    const haystack = foodSearchText(f);
    return tokens.every(token => haystack.includes(token));
  };

  const displayProp = key => ({
    protein_cal_pct:'protein_display', fat_cal_pct:'fat_display', carb_cal_pct:'carb_display',
    phosphorus_mg_per_100kcal:'phosphorus_display', magnesium_mg_per_100kcal:'magnesium_display',
    calcium_mg_per_100kcal:'calcium_display', sodium_mg_per_100kcal:'sodium_display', kcal_per_100g:'kcal_per_100g_display'
  }[key]);
  const rangeFmt = (f,key,suffix='') => {
    const raw = displayProp(key) ? f[displayProp(key)] : null;
    if(raw && /[A-Za-z<>/]|%|Trace|trace/.test(String(raw))) return String(raw);
    const min=f[key+'_min'], max=f[key+'_max'], val=f[key];
    if(val==null){ if(raw) return String(raw); return '—'; }
    if(min!=null&&max!=null&&min!==max)return `${fmt(min,1)}–${fmt(max,1)}${suffix}`;
    return `${fmt(val,1)}${suffix}`;
  };
  const sourceLabel = f => ({
    pierson_2017:'Historical 2017', fdsg_wet:'FDSG wet', fdsg_dry:'FDSG dry', custom:'My data'
  }[f.dataset] || f.dataset || 'Unknown');
  const formLabel = f => ({wet:'Wet',dry:'Dry', 'air-dried':'Air-dried', 'steam-dried':'Steam & dried'}[f.form] || f.form || '');
  const sourceBadgeClass = f => f.dataset==='pierson_2017' ? 'warning' : f.dataset==='custom' ? 'good' : 'source';
  const carbFilterValue = f => {
    if(f.carb_upper_bound!=null) return f.carb_upper_bound;
    if(f.carb_qualifier==='trace') return 0.01;
    if(f.carb_cal_pct!=null) return Math.max(0,Number(f.carb_cal_pct));
    return null;
  };
  const carbFits = (f,max) => { const v=carbFilterValue(f); return v!=null && v<=max; };
  const foodById = id => allFoods().find(f=>f.id===id);
  const toast = msg => { const t=$('#toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(()=>t.classList.remove('show'),1800); };
  const calorieText = f => {
    if(f.kcal_per_100g!=null || f.kcal_per_100g_display){
      const v=rangeFmt(f,'kcal_per_100g','');
      return v==='—' ? '—' : `${v} kcal/100g`;
    }
    if(f.calorie_options?.length) return f.calorie_options.map(o=>`${fmt(o.kcal,0)} kcal / ${fmt(o.amount,1)} ${o.unit}`).join(' · ');
    if(f.calories_display && f.calories_ambiguous) return `${f.calories_display}${f.section_calorie_note ? ` (${f.section_calorie_note})` : ''}`;
    if(f.calories!=null){ const size=f.calorie_amount ? ` / ${fmt(f.calorie_amount,1)} ${f.calorie_unit||''}` : f.section_calorie_note ? ` · ${f.section_calorie_note}`:''; return `${rangeFmt(f,'calories',' kcal')}${size}`; }
    return f.calories_display || '—';
  };
  const sourceDateValue = f => {
    if(f.updated){ const m=String(f.updated).match(/^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/); if(m){let y=+m[3];if(y<100)y+=2000;return y*10000+(+m[1])*100+(+m[2]);} }
    return (f.source_year||0)*10000;
  };

  function badges(f){
    let b=`<span class="badge ${sourceBadgeClass(f)}">${esc(sourceLabel(f))}</span>`;
    if(f.updated) b+=`<span class="badge">Updated ${esc(f.updated)}</span>`;
    if(f.form) b+=`<span class="badge">${esc(formLabel(f))}</span>`;
    if(f.prescription) b+='<span class="badge rx">Veterinary</span>';
    if(f.source_personal_use_only) b+='<span class="badge warning" title="Source marked For Personal Use Only">FPUO</span>';
    if(!f.data_complete) b+='<span class="badge missing">Partial data</span>';
    if(f.source_anomaly) b+='<span class="badge danger">Source anomaly</span>';
    if(f.analysis_shared) b+='<span class="badge">Shared analysis</span>';
    return b;
  }

  function card(f){
    const fav=state.favorites.has(f.id), cmp=state.compare.includes(f.id), within=carbFits(f,state.settings.carbTarget), alias=aliasFor(f);
    return `<article class="food-card" data-id="${esc(f.id)}">
      <div class="card-top"><div class="card-title"><div class="brand-name">${esc(f.brand)}</div><div class="food-name">${esc(f.product)}</div>${f.line?`<div class="line-name">${esc(f.line)}</div>`:''}${f.style?`<div class="style-name">${esc(f.style)}</div>`:''}${alias?.current_name?`<div class="shelf-name">Shelf: ${esc(alias.current_name)}</div>`:''}</div><button class="star-btn ${fav?'saved':''}" data-action="fav" aria-label="${fav?'Remove from':'Add to'} favorites">★</button></div>
      <div class="badge-row">${badges(f)}</div>
      <div class="macros"><div class="metric"><span>Protein</span><strong>${rangeFmt(f,'protein_cal_pct','%')}</strong></div><div class="metric"><span>Fat</span><strong>${rangeFmt(f,'fat_cal_pct','%')}</strong></div><div class="metric carb ${within?'within':'over'}"><span>Carbs</span><strong>${rangeFmt(f,'carb_cal_pct','%')}</strong></div></div>
      <div class="details-row"><div class="mini-stat"><span>Phosphorus</span><strong>${rangeFmt(f,'phosphorus_mg_per_100kcal',' mg/100 kcal')}</strong></div><div class="mini-stat"><span>Calories</span><strong>${esc(calorieText(f))}</strong></div></div>
      <div class="card-actions"><button data-action="details">Details</button><button data-action="compare" class="${cmp?'compare-selected':''}">${cmp?'✓ Comparing':'Compare'}</button></div>
    </article>`;
  }

  function filterFoods(){
    let foods=allFoods(); const q=state.query.trim().toLowerCase(); const fl=state.filters;
    if(q) foods=foods.filter(f=>matchesSearch(f,q));
    const carbMax = fl.carbMax ?? (state.quick.carb ? state.settings.carbTarget : null);
    if(carbMax!=null) foods=foods.filter(f=>carbFits(f,carbMax));
    if(fl.proteinMin!=null) foods=foods.filter(f=>f.protein_cal_pct!=null && f.protein_cal_pct>=fl.proteinMin);
    if(fl.phosMax!=null) foods=foods.filter(f=>f.phosphorus_mg_per_100kcal!=null && f.phosphorus_mg_per_100kcal<=fl.phosMax);
    if(fl.fatMax!=null) foods=foods.filter(f=>f.fat_cal_pct!=null && f.fat_cal_pct<=fl.fatMax);
    if(fl.brand) foods=foods.filter(f=>f.brand===fl.brand);
    if(fl.source) foods=foods.filter(f=>f.dataset===fl.source);
    if(fl.form) foods=foods.filter(f=>fl.form==='dryish' ? f.form!=='wet' : f.form===fl.form);
    if(fl.texture) foods=foods.filter(f=>textureMatches(f,fl.texture));
    if(fl.hideRx) foods=foods.filter(f=>!f.prescription);
    if(fl.excludeSeafood||state.quick.seafood) foods=foods.filter(f=>!isSeafood(f));
    if(fl.completeOnly||state.quick.complete) foods=foods.filter(f=>f.data_complete);
    if(state.quick.favorites) foods=foods.filter(f=>state.favorites.has(f.id));
    if(state.quick.wet) foods=foods.filter(f=>f.form==='wet');
    const sorters={
      carb_asc:(a,b)=>(carbFilterValue(a)??999)-(carbFilterValue(b)??999)||sourceDateValue(b)-sourceDateValue(a)||a.brand.localeCompare(b.brand),
      phos_asc:(a,b)=>(a.phosphorus_mg_per_100kcal??99999)-(b.phosphorus_mg_per_100kcal??99999),
      protein_desc:(a,b)=>(b.protein_cal_pct??-1)-(a.protein_cal_pct??-1),
      fat_asc:(a,b)=>(a.fat_cal_pct??999)-(b.fat_cal_pct??999),
      updated_desc:(a,b)=>sourceDateValue(b)-sourceDateValue(a)||a.brand.localeCompare(b.brand),
      brand_asc:(a,b)=>a.brand.localeCompare(b.brand)||a.product.localeCompare(b.product)
    };
    foods.sort(sorters[state.sort]||sorters.carb_asc); return foods;
  }

  function renderBrowse(){
    const foods=filterFoods(); $('#recordCount').textContent=allFoods().length.toLocaleString(); $('#resultCount').textContent=`${foods.length.toLocaleString()} foods`;
    $('#foodGrid').innerHTML=foods.slice(0,state.visible).map(card).join('') || `<div class="empty-state"><div class="empty-icon">⌕</div><h3>No matches</h3><p>Try widening a target or clearing a quick filter.</p></div>`;
    $('#loadMoreBtn').classList.toggle('hidden',foods.length<=state.visible);
    $('#quickCarbValue').textContent=state.settings.carbTarget;
    applyStoreMode();
    updateFilterCount();
  }
  function updateFilterCount(){
    const f=state.filters;let n=Object.entries(f).filter(([k,v])=>k!=='completeOnly' && ((typeof v==='boolean'&&v)||(typeof v!=='boolean'&&v!==null&&v!==''))).length+(f.completeOnly?1:0);
    $('#filterCount').textContent=n;$('#filterCount').classList.toggle('hidden',n===0);
  }

  function renderCompare(){
    state.compare=state.compare.filter(id=>foodById(id));persist(); const foods=state.compare.map(foodById).filter(Boolean);
    $('#compareNavCount').textContent=foods.length;$('#compareNavCount').classList.toggle('hidden',!foods.length);
    $('#compareEmpty').classList.toggle('hidden',!!foods.length);$('#compareTableWrap').classList.toggle('hidden',!foods.length);
    if(!foods.length){$('#compareTableWrap').innerHTML='';return;}
    const rows=[
      ['Protein (% calories)',f=>rangeFmt(f,'protein_cal_pct','%')],['Fat (% calories)',f=>rangeFmt(f,'fat_cal_pct','%')],['Carbs (% calories)',f=>rangeFmt(f,'carb_cal_pct','%')],
      ['Phosphorus',f=>rangeFmt(f,'phosphorus_mg_per_100kcal',' mg/100 kcal')],['Calories',f=>calorieText(f)],['Form',f=>formLabel(f)||'—'],['Source',f=>sourceLabel(f)+(f.updated?` · ${f.updated}`:'')]
    ];
    $('#compareTableWrap').innerHTML=`<table class="compare-table"><thead><tr><th>Metric</th>${foods.map(f=>`<th><div class="brand-name">${esc(f.brand)}</div>${esc(f.product)}<br><button class="text-btn" data-remove-compare="${esc(f.id)}">Remove</button></th>`).join('')}</tr></thead><tbody>${rows.map(([label,fn])=>`<tr><td><strong>${label}</strong></td>${foods.map(f=>{let cls='';if(label.startsWith('Carbs'))cls=carbFits(f,state.settings.carbTarget)?'value-good':'value-warn';return `<td class="${cls}">${esc(fn(f))}</td>`}).join('')}</tr>`).join('')}</tbody></table>`;
  }

  function sourceNotes(f){
    const p=[];
    if(f.dataset==='pierson_2017') p.push(`<p><strong>Source:</strong> ${esc(f.source_name)}, page ${esc(f.source_page)}. ${esc(f.source_type)}.</p><p>This record is historical. Verify the current formula with the manufacturer before relying on it.</p>`);
    else if(f.dataset==='fdsg_wet') p.push(`<p><strong>Source:</strong> ${esc(f.source_name)}, page ${esc(f.source_page)}. ${esc(f.source_type)}.</p>${f.updated?`<p><strong>Row update:</strong> ${esc(f.updated)}</p>`:''}<p>The source describes typical-analysis values as more detailed than Guaranteed Analysis but not absolute.</p>${f.source_personal_use_only?'<p><strong>Source restriction:</strong> the supplied compilation is marked “For personal use only.”</p>':''}`);
    else if(f.dataset==='fdsg_dry') p.push(`<p><strong>Source:</strong> ${esc(f.source_name)}, page ${esc(f.source_page)}. This source primarily provides ME carbohydrate percentages, so missing protein, fat, phosphorus, and calories are intentionally left blank.</p>${f.previous_carb_display?`<p><strong>Previous recipe carb:</strong> ${esc(f.previous_carb_display)}</p>`:''}`);
    else p.push(`<p><strong>Source/note:</strong> ${esc(f.user_source||'User-entered')}</p>`);
    if(f.source_anomaly) p.push(`<p><strong>Source anomaly:</strong> the source value is preserved as printed even though its macro arithmetic is unusual${f.macro_sum!=null?` (sum ${fmt(f.macro_sum,1)}%)`:''}. It has not been silently corrected.</p>`);
    if(f.section_calorie_note) p.push(`<p><strong>Source package note:</strong> ${esc(f.section_calorie_note)}</p>`);
    if(f.analysis_shared) p.push('<p>The original PDF visually shared this analysis across multiple product rows. The app preserves that relationship.</p>');
    const a=aliasFor(f); if(a?.current_name) p.push(`<p><strong>Verified shelf alias:</strong> ${esc(a.current_name)}${a.verified_on?` · checked ${esc(a.verified_on)}`:''}${a.verified_source?` · ${esc(a.verified_source)}`:''}. The source product name above remains unchanged.</p>`);
    return p.join('');
  }

  function showDetails(f){
    const extraMinerals = [
      ['Magnesium',rangeFmt(f,'magnesium_mg_per_100kcal',' mg/100 kcal')],
      ['Calcium',rangeFmt(f,'calcium_mg_per_100kcal',' mg/100 kcal')],
      ['Sodium',rangeFmt(f,'sodium_mg_per_100kcal',' mg/100 kcal')]
    ].filter(([,v])=>v!=='—');
    const alias=aliasFor(f);
    $('#detailContent').innerHTML=`<div class="detail-card"><div class="detail-head"><div><div class="brand-name">${esc(f.brand)}</div><h2>${esc(f.product)}</h2>${f.line?`<div class="line-name">${esc(f.line)}</div>`:''}${f.style?`<div class="style-name">${esc(f.style)}</div>`:''}${alias?.current_name?`<div class="shelf-name detail-shelf">Current shelf name: ${esc(alias.current_name)}</div>`:''}</div><button class="icon-btn" data-close-detail>✕</button></div>
      <div class="badge-row">${badges(f)}</div>
      <div class="detail-grid"><div class="detail-value"><span>Protein</span><strong>${rangeFmt(f,'protein_cal_pct','% calories')}</strong></div><div class="detail-value"><span>Fat</span><strong>${rangeFmt(f,'fat_cal_pct','% calories')}</strong></div><div class="detail-value"><span>Carbohydrate</span><strong>${rangeFmt(f,'carb_cal_pct','% calories')}</strong></div><div class="detail-value"><span>Phosphorus</span><strong>${rangeFmt(f,'phosphorus_mg_per_100kcal',' mg/100 kcal')}</strong></div><div class="detail-value"><span>Calories</span><strong>${esc(calorieText(f))}</strong></div><div class="detail-value"><span>Carb target</span><strong>≤ ${fmt(state.settings.carbTarget)}%</strong></div>${extraMinerals.map(([k,v])=>`<div class="detail-value"><span>${k}</span><strong>${esc(v)}</strong></div>`).join('')}</div>
      <div class="detail-notes">${sourceNotes(f)}</div>
      <button class="primary-btn" data-close-detail>Done</button></div>`;
    $('#detailDialog').showModal();
  }

  function renderCustom(){
    const wrap=$('#customFoodsList'); if(!state.custom.length){wrap.innerHTML='<p class="subtle">Nothing saved yet.</p>';return;}
    wrap.innerHTML=state.custom.map(f=>`<div class="custom-item"><div><strong>${esc(f.brand)} — ${esc(f.product)}</strong><div class="subtle">P ${fmt(f.protein_cal_pct)}% · F ${fmt(f.fat_cal_pct)}% · C ${fmt(f.carb_cal_pct)}% · Phos ${fmt(f.phosphorus_mg_per_100kcal)} mg/100 kcal</div></div><button class="text-btn" data-delete-custom="${esc(f.id)}">Delete</button></div>`).join('');
  }
  function nav(view){state.view=view;$$('.view').forEach(v=>v.classList.toggle('active',v.id===view+'View'));$$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.nav===view));if(view==='browse')renderBrowse();if(view==='compare')renderCompare();if(view==='add'){renderCustom();}window.scrollTo({top:0,behavior:'instant'});}
  function populateBrands(){const brands=[...new Set(allFoods().map(f=>f.brand).filter(Boolean))].sort((a,b)=>a.localeCompare(b));$('#brandFilter').innerHTML='<option value="">All brands</option>'+brands.map(b=>`<option>${esc(b)}</option>`).join('');}
  function syncDialogs(){
    $('#brandFilter').value=state.filters.brand;$('#carbMaxFilter').value=state.filters.carbMax??'';$('#proteinMinFilter').value=state.filters.proteinMin??'';$('#phosMaxFilter').value=state.filters.phosMax??'';$('#fatMaxFilter').value=state.filters.fatMax??'';$('#sourceFilter').value=state.filters.source;$('#formFilter').value=state.filters.form;$('#textureFilter').value=state.filters.texture;$('#hideRxFilter').checked=state.filters.hideRx;$('#excludeSeafoodFilter').checked=state.filters.excludeSeafood;$('#completeOnlyFilter').checked=state.filters.completeOnly;
    $('#settingCarbTarget').value=state.settings.carbTarget;$('#settingPhosTarget').value=state.settings.phosTarget??'';
  }

  function initEvents(){
    document.addEventListener('click',e=>{
      const navBtn=e.target.closest('[data-nav]');if(navBtn){nav(navBtn.dataset.nav);return;}
      const cardEl=e.target.closest('.food-card');const act=e.target.closest('[data-action]');
      if(cardEl&&act){const f=foodById(cardEl.dataset.id);if(!f)return;if(act.dataset.action==='fav'){state.favorites.has(f.id)?state.favorites.delete(f.id):state.favorites.add(f.id);persist();renderBrowse();}if(act.dataset.action==='compare'){if(state.compare.includes(f.id))state.compare=state.compare.filter(x=>x!==f.id);else if(state.compare.length<4)state.compare.push(f.id);else return toast('Compare is limited to 4 foods');persist();renderBrowse();renderCompare();}if(act.dataset.action==='details')showDetails(f);return;}
      const rm=e.target.closest('[data-remove-compare]');if(rm){state.compare=state.compare.filter(x=>x!==rm.dataset.removeCompare);persist();renderCompare();renderBrowse();}
      if(e.target.closest('[data-close-detail]'))$('#detailDialog').close();
      const del=e.target.closest('[data-delete-custom]');if(del){state.custom=state.custom.filter(x=>x.id!==del.dataset.deleteCustom);persist();populateBrands();renderCustom();renderBrowse();toast('Deleted');}
    });
    $('#searchInput').addEventListener('input',e=>{state.query=e.target.value;state.visible=48;renderBrowse();});
    $('#sortSelect').addEventListener('change',e=>{state.sort=e.target.value;renderBrowse();});
    $('#loadMoreBtn').addEventListener('click',()=>{state.visible+=48;renderBrowse();});
    $('#storeModeBtn').addEventListener('click',()=>{state.settings.storeMode=!state.settings.storeMode;persist();applyStoreMode();});
    $$('.chip[data-quick]').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.quick;state.quick[k]=!state.quick[k];b.classList.toggle('active',state.quick[k]);state.visible=48;renderBrowse();}));
    $('#filterBtn').addEventListener('click',()=>{populateBrands();syncDialogs();$('#filterDialog').showModal();});
    $('#settingsBtn').addEventListener('click',()=>{syncDialogs();$('#settingsDialog').showModal();});
    $('#applyFiltersBtn').addEventListener('click',()=>{const n=id=>{const v=$(id).value;return v===''?null:Number(v)};state.filters={brand:$('#brandFilter').value,carbMax:n('#carbMaxFilter'),proteinMin:n('#proteinMinFilter'),phosMax:n('#phosMaxFilter'),fatMax:n('#fatMaxFilter'),source:$('#sourceFilter').value,form:$('#formFilter').value,texture:$('#textureFilter').value,hideRx:$('#hideRxFilter').checked,excludeSeafood:$('#excludeSeafoodFilter').checked,completeOnly:$('#completeOnlyFilter').checked};state.visible=48;renderBrowse();});
    $('#resetFiltersBtn').addEventListener('click',()=>{state.filters={brand:'',carbMax:null,proteinMin:null,phosMax:null,fatMax:null,source:'',form:'',texture:'',hideRx:false,excludeSeafood:false,completeOnly:false};syncDialogs();});
    $('#saveSettingsBtn').addEventListener('click',()=>{state.settings.carbTarget=Number($('#settingCarbTarget').value)||10;state.settings.phosTarget=$('#settingPhosTarget').value===''?null:Number($('#settingPhosTarget').value);persist();renderBrowse();renderCompare();});
    $('#resetSettingsBtn').addEventListener('click',()=>{$('#settingCarbTarget').value=10;$('#settingPhosTarget').value='';});
    $('#clearCompareBtn').addEventListener('click',()=>{state.compare=[];persist();renderCompare();renderBrowse();});
    $('#customFoodForm').addEventListener('input',e=>{const fd=new FormData(e.currentTarget);const vals=['protein','fat','carb'].map(k=>Number(fd.get(k)||0));const sum=vals.reduce((a,b)=>a+b,0);const box=$('#macroSumNote');if(vals.some(v=>v>0)){box.classList.remove('hidden');box.textContent=`Macro calories sum to ${fmt(sum,1)}%. ${Math.abs(sum-100)<=3?'Looks consistent with rounding.':'Check the three values; they should be near 100%.'}`;}else box.classList.add('hidden');});
    $('#customFoodForm').addEventListener('submit',e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const g=k=>Number(fd.get(k));const p=g('protein'),fat=g('fat'),carb=g('carb');if(Math.abs((p+fat+carb)-100)>5){toast('Macro percentages should add to about 100%');return;}const id='custom-'+Date.now();state.custom.push({id,brand:String(fd.get('brand')).trim(),line:null,product:String(fd.get('product')).trim(),form:String(fd.get('form')||'wet'),protein_cal_pct:p,protein_cal_pct_min:p,protein_cal_pct_max:p,fat_cal_pct:fat,fat_cal_pct_min:fat,fat_cal_pct_max:fat,carb_cal_pct:carb,carb_cal_pct_min:carb,carb_cal_pct_max:carb,phosphorus_mg_per_100kcal:fd.get('phos')?g('phos'):null,phosphorus_mg_per_100kcal_min:fd.get('phos')?g('phos'):null,phosphorus_mg_per_100kcal_max:fd.get('phos')?g('phos'):null,calories:fd.get('calories')?g('calories'):null,calories_min:fd.get('calories')?g('calories'):null,calories_max:fd.get('calories')?g('calories'):null,calories_display:fd.get('calories')?String(fd.get('calories')):null,section_calorie_note:String(fd.get('package')||''),user_source:String(fd.get('source')||''),verification_status:'user'});persist();e.currentTarget.reset();$('#macroSumNote').classList.add('hidden');populateBrands();renderCustom();renderBrowse();toast('Food saved on this device');});
    $('#gaCalcForm').addEventListener('submit',e=>{e.preventDefault();const fd=new FormData(e.currentTarget),n=k=>Number(fd.get(k));const p=n('protein'),f=n('fat'),fiber=n('fiber'),m=n('moisture'),ash=n('ash');const carb=100-p-f-fiber-m-ash;if(carb<0){$('#gaResult').classList.remove('hidden');$('#gaResult').textContent='Those values add to more than 100%. Check the label entries.';return;}const pk=3.5*p,fk=8.5*f,ck=3.5*carb,total=pk+fk+ck;const pp=total?100*pk/total:0,fp=total?100*fk/total:0,cp=total?100*ck/total:0;$('#gaResult').classList.remove('hidden');$('#gaResult').innerHTML=`<strong>Rough estimate:</strong><br>Protein ${fmt(pp,1)}% · Fat ${fmt(fp,1)}% · Carbs ${fmt(cp,1)}% of estimated metabolizable calories<br><span class="subtle">Estimated carbohydrate by difference: ${fmt(carb,1)}% as-fed. Guaranteed Analysis values are minima/maxima, so treat this as a screening estimate rather than a precise TNA result.</span>`;});
    $('#exportCustomBtn').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(state.custom,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='catfood-compass-my-foods.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
  }
  function registerSW(){if('serviceWorker' in navigator && location.protocol.startsWith('http'))navigator.serviceWorker.register('./service-worker.js').catch(()=>{});}
  populateBrands();syncDialogs();initEvents();applyStoreMode();renderBrowse();renderCompare();renderCustom();registerSW();
})();
