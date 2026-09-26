(() => {
  const baseFoods = (window.CATFOOD_DATA || []).map(x => ({...x, dataset:x.dataset || 'pierson_2017'}));
  const meta = window.CATFOOD_META || {};
  const aliasRows = (window.CATFOOD_ALIASES || []).filter(a=>a&&a.source_id&&a.verified===true);
  const aliasById = new Map(aliasRows.map(a=>[a.source_id,a]));
  const brandCatalogSpecs = [
    {key:'tiki', label:'Tiki Cat', source:'Tiki Pets current catalog', db:window.TIKI_CAT_DB || {current_products:[],reconciliation:[],meta:{}}},
    {key:'fancy_feast', label:'Fancy Feast', source:'Purina Fancy Feast current catalog', db:window.FANCY_FEAST_DB || {current_products:[],reconciliation:[],meta:{}}},
    {key:'friskies', label:'Friskies', source:'Purina Friskies current catalog', db:window.FRISKIES_DB || {current_products:[],reconciliation:[],meta:{}}}
  ];
  const currentCatalogMatchBySourceId = new Map();
  for(const spec of brandCatalogSpecs){
    const productById=new Map((spec.db.current_products||[]).map(p=>[p.id,p]));
    for(const link of (spec.db.reconciliation||[])){
      if(!link?.source_id || !link?.current_product_id || !String(link.status||'').startsWith('verified_')) continue;
      const product=productById.get(link.current_product_id);
      if(product) currentCatalogMatchBySourceId.set(link.source_id,{spec,link,product});
    }
  }
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const readJSON = (k, fallback) => { try { return JSON.parse(localStorage.getItem(k)) ?? fallback; } catch { return fallback; } };
  const state = {
    view:'browse', query:'', visible:48,
    favorites:new Set(readJSON('cfc_favorites',[])),
    compare:readJSON('cfc_compare',[]).slice(0,4),
    custom:readJSON('cfc_custom',[]),
    settings:{profile:'normal',carbTarget:10,phosTarget:null,kidneySodiumMax:null,kidneyProteinMin:null,kidneyProteinMax:null,urinaryMagnesiumMax:null,urinaryPhosMax:null,urinarySodiumMax:null,urinaryCalciumMax:null,weightKcalMax:null,weightProteinMin:null,oncologyCarbMax:null,oncologyProteinMin:null,oncologyKcalMin:null,customCarbMax:null,customProteinMin:null,customFatMax:null,customPhosMax:null,customMagnesiumMax:null,customCalciumMax:null,customSodiumMax:null,customKcalMin:null,customKcalMax:null,storeMode:false,theme:'forest',...readJSON('cfc_settings',{})},
    quick:{profile:false,carb:false,complete:false,favorites:false,wet:false,seafood:false},
    filters:{brand:'',carbMax:null,proteinMin:null,phosMax:null,fatMax:null,source:'',form:'',texture:'',hideRx:false,excludeSeafood:false,completeOnly:false},
    sort:'relevance'
  };

  const persist = () => {
    localStorage.setItem('cfc_favorites',JSON.stringify([...state.favorites]));
    localStorage.setItem('cfc_compare',JSON.stringify(state.compare));
    localStorage.setItem('cfc_custom',JSON.stringify(state.custom));
    localStorage.setItem('cfc_settings',JSON.stringify(state.settings));
  };
  const customNormalized = () => state.custom.map(x=>({...x,dataset:'custom',verification_status:'user',source_year:new Date().getFullYear(),prescription:!!x.prescription,form:x.form||'wet',data_complete:x.protein_cal_pct!=null&&x.fat_cal_pct!=null&&x.carb_cal_pct!=null&&x.phosphorus_mg_per_100kcal!=null}));
  const currentCatalogMatchFor = f => {
    const match=currentCatalogMatchBySourceId.get(f.id); if(!match) return null;
    const {spec,link,product}=match;
    const nameNorm=normalizeSearch(product.current_name||'');
    const lineNorm=normalizeSearch(product.line||'');
    const familyNorm=normalizeSearch(product.family||'');
    const parts=[];
    if(product.line && !(lineNorm && nameNorm.startsWith(lineNorm))) parts.push(product.line);
    if(product.family && !(familyNorm && nameNorm.startsWith(familyNorm)) && normalizeSearch(product.family)!==lineNorm) parts.push(product.family);
    parts.push(product.current_name);
    return {spec,link,product,label:parts.filter(Boolean).join(' · ')};
  };
  const aliasFor = f => {
    const base=aliasById.get(f.id)||null, catalog=currentCatalogMatchFor(f);
    if(!catalog) return base;
    return {
      ...(base||{}), source_id:f.id, verified:true,
      current_name:catalog.label,
      aliases:[...(base?.aliases||[]),...(catalog.product.aliases||[]),catalog.product.raw_title].filter(Boolean),
      verified_on:catalog.product.verified_on||catalog.spec.db.meta?.verified_on,
      verified_source:catalog.spec.source, catalog_match:catalog
    };
  };
  const aliasSearchValues = f => { const a=aliasFor(f); return a ? [a.current_name,...(a.aliases||[])].filter(Boolean) : []; };
  const seafoodText = f => `${f.line||''} ${f.product||''} ${f.style||''}`.toLowerCase().replace(/fish[-\s]?free/g,'');
  const isSeafood = f => /seafood|fish|tuna|salmon|trout|mackerel|sardine|shrimp|crab|lobster|clam|mussel|prawn|tilapia|cod|sole|whitefish|oceanfish|herring|pollock|haddock|hoki|anchov|bonito|seabass|sea bass|halibut|snapper|krill|calamari|squid|oyster|scallop/.test(seafoodText(f));
  const textureText = f => `${f.style||''} ${f.line||''} ${f.product||''}`.toLowerCase();
  const textureMatches = (f,t) => { const x=textureText(f); const pats={pate:/p[âa]t[eé]|\bpate\b|\bloaf\b/,shreds:/shred|flake/,pieces:/minc|\bbit(s)?\b|chunk|morsel|\bcut(s)?\b|slice/,gravy:/gravy|sauce|stew/,broth:/broth|consomm|aspic/,mousse:/mousse/}; return !t || !!pats[t]?.test(x); };
  const THEMES={forest:{color:'#12211b'},midnight:{color:'#0a1210'},ocean:{color:'#123b4c'},berry:{color:'#4d1f38'},sunset:{color:'#5b2c1c'},lavender:{color:'#31274d'}};
  const applyTheme = () => { const theme=THEMES[state.settings.theme]?state.settings.theme:'forest'; state.settings.theme=theme; document.documentElement.dataset.theme=theme; const m=document.querySelector('meta[name=\"theme-color\"]'); if(m)m.content=THEMES[theme].color; };
  const applyStoreMode = () => { const on=!!state.settings.storeMode; document.body.classList.toggle('store-mode',on); document.documentElement.classList.toggle('store-mode-preload',on); const b=$('#storeModeBtn'); if(b){b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.textContent=on?'✓ Store mode':'🛒 Store mode';} }; 
  const allFoods = () => [...new Map([...baseFoods,...customNormalized()].map(x=>[x.id,x])).values()];
  const esc = s => String(s ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const fmt = (v,d=0) => v == null || Number.isNaN(v) ? '—' : Number(v).toFixed(d).replace(/\.0$/,'');
  const normalizeSearch = value => String(value ?? '')
    .normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
    .toLowerCase().replace(/&/g,' and ').replace(/[’']/g,'')
    .replace(/[^a-z0-9]+/g,' ').replace(/\s+/g,' ').trim();
  const searchTokens = query => normalizeSearch(query).split(' ').filter(Boolean);
  const fieldSearchValues = f => [
    ['brand', f.brand, 60], ['line', f.line, 50], ['product', f.product, 42], ['style', f.style, 24],
    ...aliasSearchValues(f).map(v=>['alias',v,46]), ['form', f.form, 8], ['source', f.source_name, 4]
  ].filter(([,v])=>v);
  const foodSearchText = f => normalizeSearch(fieldSearchValues(f).map(([,v])=>v).join(' '));

  const oneEditApart = (a,b) => {
    if(a===b) return true;
    if(Math.abs(a.length-b.length)>1) return false;
    if(a.length===b.length){
      const diffs=[];
      for(let i=0;i<a.length;i++) if(a[i]!==b[i]) diffs.push(i);
      if(diffs.length===1) return true;
      return diffs.length===2 && diffs[1]===diffs[0]+1 && a[diffs[0]]===b[diffs[1]] && a[diffs[1]]===b[diffs[0]];
    }
    if(a.length>b.length) [a,b]=[b,a];
    let i=0,j=0,edits=0;
    while(i<a.length&&j<b.length){
      if(a[i]===b[j]){i++;j++;continue;}
      if(++edits>1) return false;
      j++;
    }
    return true;
  };
  const tokenQuality = (token, value) => {
    const norm=normalizeSearch(value);
    if(!norm) return 0;
    const words=norm.split(' ');
    if(words.includes(token)) return 10;
    if(words.some(w=>w.startsWith(token))) return 8;
    if(norm.includes(token)) return 6;
    if(token.length>=4 && words.some(w=>w.length>=4 && oneEditApart(token,w))) return 3;
    return 0;
  };
  const searchScore = (f, query) => {
    const q=normalizeSearch(query), tokens=searchTokens(query);
    if(!tokens.length) return 0;
    const fields=fieldSearchValues(f);
    let score=0;
    for(const token of tokens){
      let best=0;
      for(const [,value,weight] of fields){
        const quality=tokenQuality(token,value);
        if(quality) best=Math.max(best,weight+quality);
      }
      if(!best) return null;
      score+=best;
    }
    const identity=normalizeSearch([f.brand,f.line,f.product].filter(Boolean).join(' '));
    const brand=normalizeSearch(f.brand), line=normalizeSearch(f.line), product=normalizeSearch(f.product);
    if(identity===q) score+=320;
    else if(identity.includes(q)) score+=180;
    if(brand===q) score+=260;
    if(line===q) score+=220;
    if(product===q) score+=180;
    if(brand && q.startsWith(brand+' ')) score+=80;
    return score;
  };
  const matchesSearch = (f, query) => searchScore(f,query)!=null;
  const suggestionLabel = (f,level) => level==='brand' ? f.brand : level==='line' ? [f.brand,f.line].filter(Boolean).join(' · ') : [f.brand,f.line,f.product].filter(Boolean).join(' · ');
  const suggestionQuery = label => label.replace(/ · /g,' ');
  const buildSuggestions = query => {
    const q=normalizeSearch(query);
    if(q.length<2) return [];
    const ranked=allFoods().map(f=>({f,score:searchScore(f,query)})).filter(x=>x.score!=null).sort((a,b)=>b.score-a.score).slice(0,80);
    const seen=new Set(), out=[];
    for(const {f,score} of ranked){
      for(const level of ['brand','line','product']){
        if(level==='line'&&!f.line) continue;
        const label=suggestionLabel(f,level), key=normalizeSearch(label);
        if(!key||seen.has(key)) continue;
        seen.add(key);out.push({label,query:suggestionQuery(label),score:score+(level==='brand'?30:level==='line'?20:10)});
      }
    }
    return out.sort((a,b)=>b.score-a.score||a.label.localeCompare(b.label)).slice(0,6);
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
  const PROFILE_DEFS={
    normal:{label:'Normal',hint:'General nutrition view with no condition-specific target filtering.'},
    diabetes:{label:'Diabetes',hint:'Carbohydrate-focused screening. The starting target is ≤10% of metabolizable calories.'},
    kidney:{label:'Kidney',hint:'Phosphorus-first view with optional sodium and protein limits you configure.'},
    urinary:{label:'Urinary',hint:'Mineral-focused view using magnesium, phosphorus, sodium, and calcium when source data exist.'},
    weight:{label:'Weight management',hint:'Calorie-density and protein-focused view when comparable kcal/100 g data are available.'},
    oncology:{label:'Cancer / oncology',hint:'Configurable energy, protein, and carbohydrate lens; no universal cancer-food cutoff is assumed.'},
    custom:{label:'Custom / Vet',hint:'Use your own nutrient limits from a veterinary or personal nutrition plan.'}
  };
  if(!PROFILE_DEFS[state.settings.profile]) state.settings.profile='normal';
  const currentProfile = () => PROFILE_DEFS[state.settings.profile] || PROFILE_DEFS.normal;
  const finiteOrNull = v => v==null || v==='' || !Number.isFinite(Number(v)) ? null : Number(v);
  const profileRules = (profile=state.settings.profile) => {
    const s=state.settings, out=[];
    const add=(key,op,value,label,unit='')=>{value=finiteOrNull(value);if(value!=null)out.push({key,op,value,label,unit});};
    if(profile==='diabetes') add('carb_cal_pct','max',s.carbTarget,'Carbs','% cal');
    if(profile==='kidney'){
      add('phosphorus_mg_per_100kcal','max',s.phosTarget,'Phosphorus','mg/100 kcal');
      add('sodium_mg_per_100kcal','max',s.kidneySodiumMax,'Sodium','mg/100 kcal');
      add('protein_cal_pct','min',s.kidneyProteinMin,'Protein','% cal');
      add('protein_cal_pct','max',s.kidneyProteinMax,'Protein','% cal');
    }
    if(profile==='urinary'){
      add('magnesium_mg_per_100kcal','max',s.urinaryMagnesiumMax,'Magnesium','mg/100 kcal');
      add('phosphorus_mg_per_100kcal','max',s.urinaryPhosMax,'Phosphorus','mg/100 kcal');
      add('sodium_mg_per_100kcal','max',s.urinarySodiumMax,'Sodium','mg/100 kcal');
      add('calcium_mg_per_100kcal','max',s.urinaryCalciumMax,'Calcium','mg/100 kcal');
    }
    if(profile==='weight'){
      add('kcal_per_100g','max',s.weightKcalMax,'Calories','kcal/100 g');
      add('protein_cal_pct','min',s.weightProteinMin,'Protein','% cal');
    }
    if(profile==='oncology'){
      add('carb_cal_pct','max',s.oncologyCarbMax,'Carbs','% cal');
      add('protein_cal_pct','min',s.oncologyProteinMin,'Protein','% cal');
      add('kcal_per_100g','min',s.oncologyKcalMin,'Calories','kcal/100 g');
    }
    if(profile==='custom'){
      add('carb_cal_pct','max',s.customCarbMax,'Carbs','% cal');
      add('protein_cal_pct','min',s.customProteinMin,'Protein','% cal');
      add('fat_cal_pct','max',s.customFatMax,'Fat','% cal');
      add('phosphorus_mg_per_100kcal','max',s.customPhosMax,'Phosphorus','mg/100 kcal');
      add('magnesium_mg_per_100kcal','max',s.customMagnesiumMax,'Magnesium','mg/100 kcal');
      add('calcium_mg_per_100kcal','max',s.customCalciumMax,'Calcium','mg/100 kcal');
      add('sodium_mg_per_100kcal','max',s.customSodiumMax,'Sodium','mg/100 kcal');
      add('kcal_per_100g','min',s.customKcalMin,'Calories','kcal/100 g');
      add('kcal_per_100g','max',s.customKcalMax,'Calories','kcal/100 g');
    }
    return out;
  };
  const profileValue = (f,key) => key==='carb_cal_pct' ? carbFilterValue(f) : finiteOrNull(f[key]);
  const rulePasses = (f,rule) => { const v=profileValue(f,rule.key); return v!=null && (rule.op==='max' ? v<=rule.value : v>=rule.value); };
  const evaluateProfile = (f,profile=state.settings.profile) => {
    const rules=profileRules(profile); if(!rules.length) return {configured:false,pass:null,missing:[],failed:[],rules};
    const missing=rules.filter(r=>profileValue(f,r.key)==null), failed=rules.filter(r=>profileValue(f,r.key)!=null&&!rulePasses(f,r));
    return {configured:true,pass:missing.length||failed.length?false:true,missing,failed,rules};
  };
  const profileHasTargets = (profile=state.settings.profile) => profileRules(profile).length>0;
  const profileMatches = f => { const e=evaluateProfile(f); return e.configured && e.pass===true; };
  const ruleText = r => { const unit=r.unit?(String(r.unit).startsWith('%')?String(r.unit):` ${r.unit}`):''; return `${r.label} ${r.op==='max'?'≤':'≥'} ${fmt(r.value, r.value%1?1:0)}${unit}`; };
  const profileTargetSummary = (profile=state.settings.profile) => profileRules(profile).map(ruleText).join(' · ');
  const metricValue = (f,key) => {
    if(key==='calories_package') return calorieText(f);
    if(key==='kcal_per_100g') return rangeFmt(f,'kcal_per_100g',' kcal/100g');
    if(key==='protein_cal_pct') return rangeFmt(f,key,'%');
    if(key==='fat_cal_pct') return rangeFmt(f,key,'%');
    if(key==='carb_cal_pct') return rangeFmt(f,key,'%');
    if(key==='phosphorus_mg_per_100kcal') return rangeFmt(f,key,' mg/100 kcal');
    if(key==='magnesium_mg_per_100kcal') return rangeFmt(f,key,' mg/100 kcal');
    if(key==='calcium_mg_per_100kcal') return rangeFmt(f,key,' mg/100 kcal');
    if(key==='sodium_mg_per_100kcal') return rangeFmt(f,key,' mg/100 kcal');
    return '—';
  };
  const profileMetricSpecs = (profile=state.settings.profile) => {
    if(profile==='diabetes') return [['Carbs','carb_cal_pct'],['Protein','protein_cal_pct'],['Fat','fat_cal_pct']];
    if(profile==='kidney') return [['Phosphorus','phosphorus_mg_per_100kcal'],['Protein','protein_cal_pct'],['Sodium','sodium_mg_per_100kcal']];
    if(profile==='urinary') return [['Magnesium','magnesium_mg_per_100kcal'],['Phosphorus','phosphorus_mg_per_100kcal'],['Sodium','sodium_mg_per_100kcal']];
    if(profile==='weight') return [['Calories','kcal_per_100g'],['Protein','protein_cal_pct'],['Fat','fat_cal_pct']];
    if(profile==='oncology') return [['Calories','kcal_per_100g'],['Protein','protein_cal_pct'],['Carbs','carb_cal_pct']];
    if(profile==='custom'){
      const targeted=[...new Set(profileRules('custom').map(r=>r.key))];
      const fallbacks=['carb_cal_pct','phosphorus_mg_per_100kcal','protein_cal_pct','fat_cal_pct','kcal_per_100g'];
      const keys=[...targeted,...fallbacks.filter(k=>!targeted.includes(k))].slice(0,3);
      const labels={carb_cal_pct:'Carbs',phosphorus_mg_per_100kcal:'Phosphorus',protein_cal_pct:'Protein',fat_cal_pct:'Fat',kcal_per_100g:'Calories',magnesium_mg_per_100kcal:'Magnesium',calcium_mg_per_100kcal:'Calcium',sodium_mg_per_100kcal:'Sodium'};
      return keys.map(k=>[labels[k]||k,k]);
    }
    return [['Protein','protein_cal_pct'],['Fat','fat_cal_pct'],['Carbs','carb_cal_pct']];
  };
  const profileDetailSpecs = (profile=state.settings.profile) => {
    if(profile==='kidney') return [['Calories','calories_package'],['Carbs','carb_cal_pct']];
    if(profile==='urinary') return [['Calcium','calcium_mg_per_100kcal'],['Calories','calories_package']];
    if(profile==='weight') return [['Carbs','carb_cal_pct'],['Package calories','calories_package']];
    if(profile==='oncology') return [['Phosphorus','phosphorus_mg_per_100kcal'],['Package calories','calories_package']];
    if(profile==='custom') return [['Package calories','calories_package'],['Sodium','sodium_mg_per_100kcal']];
    return [['Phosphorus','phosphorus_mg_per_100kcal'],['Calories','calories_package']];
  };
  const targetClassForMetric = (f,key) => {
    let rules=profileRules().filter(r=>r.key===key);
    if(key==='carb_cal_pct'&&state.quick.carb&&!rules.length) rules=[{key,op:'max',value:state.settings.carbTarget}];
    if(!rules.length) return '';
    const v=profileValue(f,key); if(v==null) return ' target-missing';
    return rules.every(r=>rulePasses(f,r)) ? ' target-pass' : ' target-fail';
  };
  const profileStatusText = f => {
    if(state.settings.profile==='normal') return '';
    const e=evaluateProfile(f); if(!e.configured) return 'No numeric profile targets set';
    if(e.missing.length) return `Target data incomplete · ${e.missing.map(r=>r.label).join(', ')} missing`;
    return e.failed.length ? 'Outside selected targets' : 'Meets selected targets';
  };
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
  const profileComparator = (a,b) => {
    const p=state.settings.profile, missing=999999;
    if(p==='diabetes') return (carbFilterValue(a)??missing)-(carbFilterValue(b)??missing)||sourceDateValue(b)-sourceDateValue(a);
    if(p==='kidney') return (a.phosphorus_mg_per_100kcal??missing)-(b.phosphorus_mg_per_100kcal??missing)||sourceDateValue(b)-sourceDateValue(a);
    if(p==='urinary') return (a.magnesium_mg_per_100kcal??missing)-(b.magnesium_mg_per_100kcal??missing)||(a.phosphorus_mg_per_100kcal??missing)-(b.phosphorus_mg_per_100kcal??missing)||sourceDateValue(b)-sourceDateValue(a);
    if(p==='weight') return (a.kcal_per_100g??missing)-(b.kcal_per_100g??missing)||sourceDateValue(b)-sourceDateValue(a);
    if(p==='custom'&&profileHasTargets()){
      const ap=profileMatches(a)?0:1,bp=profileMatches(b)?0:1; if(ap!==bp)return ap-bp;
    }
    return sourceDateValue(b)-sourceDateValue(a)||a.brand.localeCompare(b.brand)||a.product.localeCompare(b.product);
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
    const fav=state.favorites.has(f.id), cmp=state.compare.includes(f.id), alias=aliasFor(f);
    const metrics=profileMetricSpecs().map(([label,key])=>`<div class="metric${targetClassForMetric(f,key)}"><span>${esc(label)}</span><strong>${esc(metricValue(f,key))}</strong></div>`).join('');
    const details=profileDetailSpecs().map(([label,key])=>`<div class="mini-stat"><span>${esc(label)}</span><strong>${esc(metricValue(f,key))}</strong></div>`).join('');
    const status=profileStatusText(f);
    return `<article class="food-card" data-id="${esc(f.id)}">
      <div class="card-top"><div class="card-title"><div class="brand-name">${esc(f.brand)}</div><div class="food-name">${esc(f.product)}</div>${f.line?`<div class="line-name">${esc(f.line)}</div>`:''}${f.style?`<div class="style-name">${esc(f.style)}</div>`:''}${alias?.current_name?`<div class="shelf-name">Shelf: ${esc(alias.current_name)}</div>`:''}</div><button class="star-btn ${fav?'saved':''}" data-action="fav" aria-label="${fav?'Remove from':'Add to'} favorites">★</button></div>
      <div class="badge-row">${badges(f)}</div>
      ${status?`<div class="profile-status ${evaluateProfile(f).configured?(evaluateProfile(f).pass?'profile-pass':'profile-caution'):'profile-neutral'}">${esc(status)}</div>`:''}
      <div class="macros profile-metrics">${metrics}</div>
      <div class="details-row">${details}</div>
      <div class="card-actions"><button data-action="details">Details</button><button data-action="compare" class="${cmp?'compare-selected':''}">${cmp?'✓ Comparing':'Compare'}</button></div>
    </article>`;
  }

  function filterFoods(){
    let foods=allFoods(); const q=state.query.trim(); const fl=state.filters;
    const scores=new Map();
    if(q) foods=foods.filter(f=>{const score=searchScore(f,q);if(score==null)return false;scores.set(f.id,score);return true;});
    if(state.quick.profile && profileHasTargets()) foods=foods.filter(profileMatches);
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
      relevance:(a,b)=>q?((scores.get(b.id)??0)-(scores.get(a.id)??0)||profileComparator(a,b)):profileComparator(a,b),
      carb_asc:(a,b)=>(carbFilterValue(a)??999)-(carbFilterValue(b)??999)||sourceDateValue(b)-sourceDateValue(a)||a.brand.localeCompare(b.brand),
      phos_asc:(a,b)=>(a.phosphorus_mg_per_100kcal??99999)-(b.phosphorus_mg_per_100kcal??99999),
      protein_desc:(a,b)=>(b.protein_cal_pct??-1)-(a.protein_cal_pct??-1),
      fat_asc:(a,b)=>(a.fat_cal_pct??999)-(b.fat_cal_pct??999),
      magnesium_asc:(a,b)=>(a.magnesium_mg_per_100kcal??99999)-(b.magnesium_mg_per_100kcal??99999),
      sodium_asc:(a,b)=>(a.sodium_mg_per_100kcal??99999)-(b.sodium_mg_per_100kcal??99999),
      calories_asc:(a,b)=>(a.kcal_per_100g??99999)-(b.kcal_per_100g??99999),
      updated_desc:(a,b)=>sourceDateValue(b)-sourceDateValue(a)||a.brand.localeCompare(b.brand),
      brand_asc:(a,b)=>a.brand.localeCompare(b.brand)||a.product.localeCompare(b.product)
    };
    const chosen=(q&&state.sort==='carb_asc')?'relevance':state.sort;
    foods.sort(sorters[chosen]||sorters.relevance); return foods;
  }

  const anyActiveFoodFilter = () => {
    const fl=state.filters;
    return state.quick.profile||state.quick.carb||state.quick.complete||state.quick.favorites||state.quick.wet||state.quick.seafood||Object.entries(fl).some(([,v])=>(typeof v==='boolean'&&v)||(typeof v!=='boolean'&&v!==null&&v!==''));
  };
  const searchMatchCountBeforeFilters = query => query ? allFoods().filter(f=>matchesSearch(f,query)).length : 0;
  function renderSuggestions(){
    const box=$('#searchSuggestions');if(!box)return;
    const suggestions=buildSuggestions(state.query);
    if(!suggestions.length||document.activeElement!==$('#searchInput')){box.classList.add('hidden');box.innerHTML='';return;}
    box.innerHTML=suggestions.map((s,i)=>`<button type="button" class="search-suggestion" role="option" data-search-suggestion="${esc(s.query)}"><span>${esc(s.label)}</span>${i===0?'<small>Best match</small>':''}</button>`).join('');
    box.classList.remove('hidden');
  }

  function renderProfileUI(){
    const profile=state.settings.profile, def=currentProfile(), rules=profileRules();
    document.body.dataset.profile=profile;
    const browseSelect=$('#profileSelect'); if(browseSelect) browseSelect.value=profile;
    if($('#profileName')) $('#profileName').textContent=def.label;
    if($('#profileHint')) $('#profileHint').textContent=def.hint;
    const carbChip=$('#quickCarbChip'); if(carbChip) carbChip.classList.toggle('hidden',profile==='diabetes');
    const chip=$('#profileTargetChip');
    if(chip){
      const show=profile!=='normal'; chip.classList.toggle('hidden',!show);
      chip.classList.toggle('active',!!state.quick.profile&&rules.length>0);
      chip.classList.toggle('needs-targets',show&&!rules.length);
      chip.textContent=rules.length ? `Profile targets · ${profileTargetSummary()}` : 'Set profile targets';
      chip.setAttribute('aria-pressed',String(!!state.quick.profile&&rules.length>0));
    }
  }
  function showSettingsTargetGroup(profile=$('#settingProfileSelect')?.value||state.settings.profile){
    $$('.profile-target-group').forEach(g=>g.classList.toggle('hidden',g.dataset.profileTargets!==profile));
  }
  function renderBrowse(){
    const foods=filterFoods(), query=state.query.trim(); $('#recordCount').textContent=allFoods().length.toLocaleString(); $('#resultCount').textContent=`${foods.length.toLocaleString()} foods`;
    if(!foods.length&&query&&anyActiveFoodFilter()){
      const raw=searchMatchCountBeforeFilters(query);
      $('#foodGrid').innerHTML=raw?`<div class="empty-state"><div class="empty-icon">⌕</div><h3>${raw.toLocaleString()} search ${raw===1?'match is':'matches are'} hidden</h3><p>Your search works, but one or more nutrition/quick filters remove the results.</p><button class="primary-btn" data-clear-food-filters>Clear food filters</button></div>`:`<div class="empty-state"><div class="empty-icon">⌕</div><h3>No matches</h3><p>Try fewer words or a slightly different spelling.</p></div>`;
    } else $('#foodGrid').innerHTML=foods.slice(0,state.visible).map(card).join('') || `<div class="empty-state"><div class="empty-icon">⌕</div><h3>No matches</h3><p>Try widening a target or clearing a quick filter.</p></div>`;
    $('#loadMoreBtn').classList.toggle('hidden',foods.length<=state.visible);
    $('#quickCarbValue').textContent=state.settings.carbTarget;
    renderProfileUI();
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
      ['Protein (% calories)','protein_cal_pct',f=>rangeFmt(f,'protein_cal_pct','%')],['Fat (% calories)','fat_cal_pct',f=>rangeFmt(f,'fat_cal_pct','%')],['Carbs (% calories)','carb_cal_pct',f=>rangeFmt(f,'carb_cal_pct','%')],
      ['Phosphorus','phosphorus_mg_per_100kcal',f=>rangeFmt(f,'phosphorus_mg_per_100kcal',' mg/100 kcal')],['Magnesium','magnesium_mg_per_100kcal',f=>rangeFmt(f,'magnesium_mg_per_100kcal',' mg/100 kcal')],['Calcium','calcium_mg_per_100kcal',f=>rangeFmt(f,'calcium_mg_per_100kcal',' mg/100 kcal')],['Sodium','sodium_mg_per_100kcal',f=>rangeFmt(f,'sodium_mg_per_100kcal',' mg/100 kcal')],
      ['Calories / 100 g','kcal_per_100g',f=>rangeFmt(f,'kcal_per_100g',' kcal/100g')],['Calories / package','calories_package',f=>calorieText(f)],['Form',null,f=>formLabel(f)||'—'],['Source',null,f=>sourceLabel(f)+(f.updated?` · ${f.updated}`:'')]
    ];
    const profileLabel=state.settings.profile==='normal'?'Normal':`${currentProfile().label}${profileHasTargets()?` · ${profileTargetSummary()}`:' · no numeric targets set'}`;
    $('#compareTableWrap').innerHTML=`<div class="compare-profile-note"><strong>Profile:</strong> ${esc(profileLabel)}</div><table class="compare-table"><thead><tr><th>Metric</th>${foods.map(f=>`<th><div class="brand-name">${esc(f.brand)}</div>${esc(f.product)}<br><button class="text-btn" data-remove-compare="${esc(f.id)}">Remove</button></th>`).join('')}</tr></thead><tbody>${rows.map(([label,key,fn])=>`<tr><td><strong>${label}</strong></td>${foods.map(f=>`<td class="${key?targetClassForMetric(f,key).trim():''}">${esc(fn(f))}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
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
    const cm=currentCatalogMatchFor(f); if(cm) p.push(`<p><strong>Current catalog reconciliation:</strong> this source record is linked to the ${esc(cm.spec.label)} manufacturer catalog entry <em>${esc(cm.label)}</em>${cm.product.catalog_status==='discontinued'?' (manufacturer listing marked discontinued)':''}. The nutrition values shown above still come from the original ${esc(sourceLabel(f))} record and are not overwritten by the current catalog.</p>`);
    return p.join('');
  }

  function showDetails(f){
    const extraMinerals = [
      ['Magnesium',rangeFmt(f,'magnesium_mg_per_100kcal',' mg/100 kcal')],
      ['Calcium',rangeFmt(f,'calcium_mg_per_100kcal',' mg/100 kcal')],
      ['Sodium',rangeFmt(f,'sodium_mg_per_100kcal',' mg/100 kcal')],
      ['Calories / 100 g',rangeFmt(f,'kcal_per_100g',' kcal/100g')]
    ].filter(([,v])=>v!=='—');
    const alias=aliasFor(f), pe=evaluateProfile(f), p=currentProfile();
    const profileText=state.settings.profile==='normal'?'Neutral general-nutrition view':pe.configured?`${profileStatusText(f)} · ${profileTargetSummary()}`:'No numeric targets set for this profile';
    $('#detailContent').innerHTML=`<div class="detail-card"><div class="detail-head"><div><div class="brand-name">${esc(f.brand)}</div><h2>${esc(f.product)}</h2>${f.line?`<div class="line-name">${esc(f.line)}</div>`:''}${f.style?`<div class="style-name">${esc(f.style)}</div>`:''}${alias?.current_name?`<div class="shelf-name detail-shelf">Current shelf name: ${esc(alias.current_name)}</div>`:''}</div><button class="icon-btn close-btn" data-close-detail aria-label="Close details" title="Close"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
      <div class="badge-row">${badges(f)}</div>
      <div class="detail-profile"><strong>${esc(p.label)} profile</strong><span>${esc(profileText)}</span></div>
      <div class="detail-grid"><div class="detail-value${targetClassForMetric(f,'protein_cal_pct')}"><span>Protein</span><strong>${rangeFmt(f,'protein_cal_pct','% calories')}</strong></div><div class="detail-value${targetClassForMetric(f,'fat_cal_pct')}"><span>Fat</span><strong>${rangeFmt(f,'fat_cal_pct','% calories')}</strong></div><div class="detail-value${targetClassForMetric(f,'carb_cal_pct')}"><span>Carbohydrate</span><strong>${rangeFmt(f,'carb_cal_pct','% calories')}</strong></div><div class="detail-value${targetClassForMetric(f,'phosphorus_mg_per_100kcal')}"><span>Phosphorus</span><strong>${rangeFmt(f,'phosphorus_mg_per_100kcal',' mg/100 kcal')}</strong></div><div class="detail-value"><span>Calories</span><strong>${esc(calorieText(f))}</strong></div><div class="detail-value"><span>Active profile</span><strong>${esc(p.label)}</strong></div>${extraMinerals.map(([k,v])=>`<div class="detail-value"><span>${k}</span><strong>${esc(v)}</strong></div>`).join('')}</div>
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
    const set=(id,v)=>{const el=$(id);if(el)el.value=v??'';};
    set('#settingProfileSelect',state.settings.profile);
    set('#settingCarbTarget',state.settings.carbTarget);
    set('#settingPhosTarget',state.settings.phosTarget);
    set('#settingKidneySodiumMax',state.settings.kidneySodiumMax);set('#settingKidneyProteinMin',state.settings.kidneyProteinMin);set('#settingKidneyProteinMax',state.settings.kidneyProteinMax);
    set('#settingUrinaryMagnesiumMax',state.settings.urinaryMagnesiumMax);set('#settingUrinaryPhosMax',state.settings.urinaryPhosMax);set('#settingUrinarySodiumMax',state.settings.urinarySodiumMax);set('#settingUrinaryCalciumMax',state.settings.urinaryCalciumMax);
    set('#settingWeightKcalMax',state.settings.weightKcalMax);set('#settingWeightProteinMin',state.settings.weightProteinMin);
    set('#settingOncologyCarbMax',state.settings.oncologyCarbMax);set('#settingOncologyProteinMin',state.settings.oncologyProteinMin);set('#settingOncologyKcalMin',state.settings.oncologyKcalMin);
    set('#settingCustomCarbMax',state.settings.customCarbMax);set('#settingCustomProteinMin',state.settings.customProteinMin);set('#settingCustomFatMax',state.settings.customFatMax);set('#settingCustomPhosMax',state.settings.customPhosMax);set('#settingCustomMagnesiumMax',state.settings.customMagnesiumMax);set('#settingCustomCalciumMax',state.settings.customCalciumMax);set('#settingCustomSodiumMax',state.settings.customSodiumMax);set('#settingCustomKcalMin',state.settings.customKcalMin);set('#settingCustomKcalMax',state.settings.customKcalMax);
    const theme=$(`input[name="theme"][value="${state.settings.theme||'forest'}"]`);if(theme)theme.checked=true;
    showSettingsTargetGroup(state.settings.profile);
  }

  function initEvents(){
    document.addEventListener('click',e=>{
      const navBtn=e.target.closest('[data-nav]');if(navBtn){nav(navBtn.dataset.nav);return;}
      const cardEl=e.target.closest('.food-card');const act=e.target.closest('[data-action]');
      if(cardEl&&act){const f=foodById(cardEl.dataset.id);if(!f)return;if(act.dataset.action==='fav'){state.favorites.has(f.id)?state.favorites.delete(f.id):state.favorites.add(f.id);persist();renderBrowse();}if(act.dataset.action==='compare'){if(state.compare.includes(f.id))state.compare=state.compare.filter(x=>x!==f.id);else if(state.compare.length<4)state.compare.push(f.id);else return toast('Compare is limited to 4 foods');persist();renderBrowse();renderCompare();}if(act.dataset.action==='details')showDetails(f);return;}
      const rm=e.target.closest('[data-remove-compare]');if(rm){state.compare=state.compare.filter(x=>x!==rm.dataset.removeCompare);persist();renderCompare();renderBrowse();}
      if(e.target.closest('[data-close-detail]'))$('#detailDialog').close();
      const del=e.target.closest('[data-delete-custom]');if(del){state.custom=state.custom.filter(x=>x.id!==del.dataset.deleteCustom);persist();populateBrands();renderCustom();renderBrowse();toast('Deleted');}
      const sug=e.target.closest('[data-search-suggestion]');if(sug){state.query=sug.dataset.searchSuggestion;$('#searchInput').value=state.query;$('#clearSearchBtn')?.classList.toggle('hidden',!state.query);state.visible=48;$('#searchSuggestions').classList.add('hidden');renderBrowse();$('#searchInput').focus();}
      if(e.target.closest('[data-clear-food-filters]')){state.quick={profile:false,carb:false,complete:false,favorites:false,wet:false,seafood:false};state.filters={brand:'',carbMax:null,proteinMin:null,phosMax:null,fatMax:null,source:'',form:'',texture:'',hideRx:false,excludeSeafood:false,completeOnly:false};$$('.chip[data-quick]').forEach(b=>b.classList.toggle('active',!!state.quick[b.dataset.quick]));syncDialogs();renderBrowse();}
    });
    $('#searchInput').addEventListener('input',e=>{state.query=e.target.value;$('#clearSearchBtn')?.classList.toggle('hidden',!state.query);state.visible=48;renderBrowse();renderSuggestions();});
    $('#clearSearchBtn').addEventListener('click',()=>{state.query='';$('#searchInput').value='';$('#clearSearchBtn').classList.add('hidden');$('#searchSuggestions').classList.add('hidden');state.visible=48;renderBrowse();$('#searchInput').focus();});
    $('#searchInput').addEventListener('focus',renderSuggestions);
    $('#searchInput').addEventListener('blur',()=>setTimeout(()=>{$('#searchSuggestions')?.classList.add('hidden');},140));
    $('#searchInput').addEventListener('keydown',e=>{if(e.key==='Escape'){$('#searchSuggestions')?.classList.add('hidden');e.currentTarget.blur();}});
    $('#sortSelect').addEventListener('change',e=>{state.sort=e.target.value;renderBrowse();});
    $('#loadMoreBtn').addEventListener('click',()=>{state.visible+=48;renderBrowse();});
    $('#storeModeBtn').addEventListener('click',()=>{state.settings.storeMode=!state.settings.storeMode;persist();applyStoreMode();});
    $('#profileSelect').addEventListener('change',e=>{state.settings.profile=PROFILE_DEFS[e.target.value]?e.target.value:'normal';state.quick.profile=state.settings.profile!=='normal'&&profileHasTargets();state.visible=48;persist();syncDialogs();renderBrowse();renderCompare();toast(`${currentProfile().label} profile`);});
    $('#profileSettingsBtn').addEventListener('click',()=>{syncDialogs();$('#settingsDialog').showModal();showSettingsTargetGroup(state.settings.profile);});
    $$('.chip[data-quick]').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.quick;if(k==='profile'&&!profileHasTargets()){syncDialogs();$('#settingsDialog').showModal();showSettingsTargetGroup(state.settings.profile);return;}state.quick[k]=!state.quick[k];b.classList.toggle('active',state.quick[k]);state.visible=48;renderBrowse();}));
    $('#filterBtn').addEventListener('click',()=>{populateBrands();syncDialogs();$('#filterDialog').showModal();});
    $('#settingsBtn').addEventListener('click',()=>{syncDialogs();$('#settingsDialog').showModal();});
    $('#settingProfileSelect').addEventListener('change',e=>showSettingsTargetGroup(e.target.value));
    $('#applyFiltersBtn').addEventListener('click',()=>{const n=id=>{const v=$(id).value;return v===''?null:Number(v)};state.filters={brand:$('#brandFilter').value,carbMax:n('#carbMaxFilter'),proteinMin:n('#proteinMinFilter'),phosMax:n('#phosMaxFilter'),fatMax:n('#fatMaxFilter'),source:$('#sourceFilter').value,form:$('#formFilter').value,texture:$('#textureFilter').value,hideRx:$('#hideRxFilter').checked,excludeSeafood:$('#excludeSeafoodFilter').checked,completeOnly:$('#completeOnlyFilter').checked};state.visible=48;renderBrowse();});
    $('#resetFiltersBtn').addEventListener('click',()=>{state.filters={brand:'',carbMax:null,proteinMin:null,phosMax:null,fatMax:null,source:'',form:'',texture:'',hideRx:false,excludeSeafood:false,completeOnly:false};syncDialogs();});
    $('#saveSettingsBtn').addEventListener('click',()=>{
      const opt=id=>{const el=$(id);if(!el||el.value==='')return null;const n=Number(el.value);return Number.isFinite(n)?n:null;};
      const priorProfile=state.settings.profile, candidate=$('#settingProfileSelect').value, newProfile=PROFILE_DEFS[candidate]?candidate:'normal';
      state.settings.profile=newProfile;
      state.settings.carbTarget=opt('#settingCarbTarget')??10;state.settings.phosTarget=opt('#settingPhosTarget');
      state.settings.kidneySodiumMax=opt('#settingKidneySodiumMax');state.settings.kidneyProteinMin=opt('#settingKidneyProteinMin');state.settings.kidneyProteinMax=opt('#settingKidneyProteinMax');
      state.settings.urinaryMagnesiumMax=opt('#settingUrinaryMagnesiumMax');state.settings.urinaryPhosMax=opt('#settingUrinaryPhosMax');state.settings.urinarySodiumMax=opt('#settingUrinarySodiumMax');state.settings.urinaryCalciumMax=opt('#settingUrinaryCalciumMax');
      state.settings.weightKcalMax=opt('#settingWeightKcalMax');state.settings.weightProteinMin=opt('#settingWeightProteinMin');
      state.settings.oncologyCarbMax=opt('#settingOncologyCarbMax');state.settings.oncologyProteinMin=opt('#settingOncologyProteinMin');state.settings.oncologyKcalMin=opt('#settingOncologyKcalMin');
      state.settings.customCarbMax=opt('#settingCustomCarbMax');state.settings.customProteinMin=opt('#settingCustomProteinMin');state.settings.customFatMax=opt('#settingCustomFatMax');state.settings.customPhosMax=opt('#settingCustomPhosMax');state.settings.customMagnesiumMax=opt('#settingCustomMagnesiumMax');state.settings.customCalciumMax=opt('#settingCustomCalciumMax');state.settings.customSodiumMax=opt('#settingCustomSodiumMax');state.settings.customKcalMin=opt('#settingCustomKcalMin');state.settings.customKcalMax=opt('#settingCustomKcalMax');
      state.settings.theme=$('input[name="theme"]:checked')?.value||'forest';
      if(newProfile==='normal'||!profileHasTargets()) state.quick.profile=false; else if(priorProfile!==newProfile) state.quick.profile=true;
      persist();applyTheme();renderBrowse();renderCompare();toast('Settings saved');
    });
    $('#resetSettingsBtn').addEventListener('click',()=>{
      $('#settingProfileSelect').value='normal';showSettingsTargetGroup('normal');
      const defaults={settingCarbTarget:10,settingPhosTarget:'',settingKidneySodiumMax:'',settingKidneyProteinMin:'',settingKidneyProteinMax:'',settingUrinaryMagnesiumMax:'',settingUrinaryPhosMax:'',settingUrinarySodiumMax:'',settingUrinaryCalciumMax:'',settingWeightKcalMax:'',settingWeightProteinMin:'',settingOncologyCarbMax:'',settingOncologyProteinMin:'',settingOncologyKcalMin:'',settingCustomCarbMax:'',settingCustomProteinMin:'',settingCustomFatMax:'',settingCustomPhosMax:'',settingCustomMagnesiumMax:'',settingCustomCalciumMax:'',settingCustomSodiumMax:'',settingCustomKcalMin:'',settingCustomKcalMax:''};
      Object.entries(defaults).forEach(([id,v])=>{const el=document.getElementById(id);if(el)el.value=v;});
      const t=$('input[name="theme"][value="forest"]');if(t)t.checked=true;
    });
    $('#clearCompareBtn').addEventListener('click',()=>{state.compare=[];persist();renderCompare();renderBrowse();});
    $('#customFoodForm').addEventListener('input',e=>{const fd=new FormData(e.currentTarget);const vals=['protein','fat','carb'].map(k=>Number(fd.get(k)||0));const sum=vals.reduce((a,b)=>a+b,0);const box=$('#macroSumNote');if(vals.some(v=>v>0)){box.classList.remove('hidden');box.textContent=`Macro calories sum to ${fmt(sum,1)}%. ${Math.abs(sum-100)<=3?'Looks consistent with rounding.':'Check the three values; they should be near 100%.'}`;}else box.classList.add('hidden');});
    $('#customFoodForm').addEventListener('submit',e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const g=k=>Number(fd.get(k));const p=g('protein'),fat=g('fat'),carb=g('carb');if(Math.abs((p+fat+carb)-100)>5){toast('Macro percentages should add to about 100%');return;}const id='custom-'+Date.now();state.custom.push({id,brand:String(fd.get('brand')).trim(),line:null,product:String(fd.get('product')).trim(),form:String(fd.get('form')||'wet'),protein_cal_pct:p,protein_cal_pct_min:p,protein_cal_pct_max:p,fat_cal_pct:fat,fat_cal_pct_min:fat,fat_cal_pct_max:fat,carb_cal_pct:carb,carb_cal_pct_min:carb,carb_cal_pct_max:carb,phosphorus_mg_per_100kcal:fd.get('phos')?g('phos'):null,phosphorus_mg_per_100kcal_min:fd.get('phos')?g('phos'):null,phosphorus_mg_per_100kcal_max:fd.get('phos')?g('phos'):null,calories:fd.get('calories')?g('calories'):null,calories_min:fd.get('calories')?g('calories'):null,calories_max:fd.get('calories')?g('calories'):null,calories_display:fd.get('calories')?String(fd.get('calories')):null,section_calorie_note:String(fd.get('package')||''),user_source:String(fd.get('source')||''),verification_status:'user'});persist();e.currentTarget.reset();$('#macroSumNote').classList.add('hidden');populateBrands();renderCustom();renderBrowse();toast('Food saved on this device');});
    $('#gaCalcForm').addEventListener('submit',e=>{e.preventDefault();const fd=new FormData(e.currentTarget),n=k=>Number(fd.get(k));const p=n('protein'),f=n('fat'),fiber=n('fiber'),m=n('moisture'),ash=n('ash');const carb=100-p-f-fiber-m-ash;if(carb<0){$('#gaResult').classList.remove('hidden');$('#gaResult').textContent='Those values add to more than 100%. Check the label entries.';return;}const pk=3.5*p,fk=8.5*f,ck=3.5*carb,total=pk+fk+ck;const pp=total?100*pk/total:0,fp=total?100*fk/total:0,cp=total?100*ck/total:0;$('#gaResult').classList.remove('hidden');$('#gaResult').innerHTML=`<strong>Rough estimate:</strong><br>Protein ${fmt(pp,1)}% · Fat ${fmt(fp,1)}% · Carbs ${fmt(cp,1)}% of estimated metabolizable calories<br><span class="subtle">Estimated carbohydrate by difference: ${fmt(carb,1)}% as-fed. Guaranteed Analysis values are minima/maxima, so treat this as a screening estimate rather than a precise TNA result.</span>`;});
    $('#exportCustomBtn').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(state.custom,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='catfood-compass-my-foods.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
  }

  function registerSW(){if('serviceWorker' in navigator && location.protocol.startsWith('http'))navigator.serviceWorker.register('./service-worker.js').catch(()=>{});}
  state.quick.profile=state.settings.profile!=='normal'&&profileHasTargets();
  populateBrands();syncDialogs();initEvents();applyTheme();applyStoreMode();$('#clearSearchBtn')?.classList.toggle('hidden',!state.query);renderBrowse();renderCompare();renderCustom();registerSW();
})();
