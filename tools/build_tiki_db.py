#!/usr/bin/env python3
import json,re,unicodedata
from pathlib import Path
from difflib import SequenceMatcher

ROOT=Path(__file__).resolve().parents[1]
FOODS=ROOT/'data'/'foods.js'
OUT_JSON=ROOT/'data'/'tiki_cat.json'
OUT_JS=ROOT/'data'/'tiki_cat.js'
VERIFIED_ON='2026-09-26'

SOURCES={
 'catalog':'https://tikipets.com/product-category/tiki-cat/tiki-cat-wet-food/',
 'after_dark':'https://tikipets.com/product-category/tiki-cat/after-dark/',
 'friends':'https://tikipets.com/cat/friends/',
 'grill':'https://tikipets.com/product-category/tiki-cat/tiki-cat-wet-food/shredded-cat/grill/',
 'gelee':'https://tikipets.com/product-category/tiki-cat/tiki-cat-wet-food/lean-gelee/',
 'luau':'https://tikipets.com/product-category/tiki-cat/tiki-cat-wet-food/shredded-cat/luau/',
 'mega_packs':'https://tikipets.com/product-category/tiki-cat/tiki-cat-wet-food/shredded-cat/mega-packs/',
 'silver':'https://tikipets.com/cat/silver/',
 'solutions':'https://tikipets.com/cat/solutions/',
 'velvet_mousse':'https://tikipets.com/product-category/tiki-cat/tiki-cat-wet-food/mousse-cat/velvet-mousse/',
 'baby':'https://tikipets.com/cat/baby/',
 'born_carnivore':'https://tikipets.com/product-category/tiki-cat/tiki-cat-dry-food/born-carnivore/'
}

PRODUCTS=[]
def add(line,family,name,*,role='complete_meal',source_key=None,aliases=None):
    source_key=source_key or re.sub(r'[^a-z]+','_',line.lower()).strip('_')
    PRODUCTS.append({'brand':'Tiki Cat','line':line,'family':family,'current_name':name,'role':role,
                     'manufacturer_category_url':SOURCES[source_key],'verified_on':VERIFIED_ON,
                     'aliases':aliases or []})

# Current official catalog entries verified from Tiki Pets category/line pages on 2026-09-26.
# After Dark
for fam,names in {
 'Shreds':[
  'Shreds Chicken, Quail & Chicken Liver Recipe in Broth','Shreds Turkey & Turkey Liver Recipe in Broth',
  'Shreds With Rabbit & Chicken Liver in Broth','Shreds With Venison & Beef Liver Recipe in Broth'],
 'Soft Pâté':[
  'Pâté Lamb & Beef Liver Recipe','Pâté Duck & Chicken Liver Recipe','Pâté Venison & Beef Liver Recipe',
  'Pâté Rabbit & Chicken Liver Recipe','Pâté Chicken, Chicken Liver & Quail Recipe','Pâté Turkey & Turkey Liver Recipe','Pâté Beef & Beef Liver Recipe'],
 'Pâté+':[
  'Pâté Chicken & Quail Egg Recipe in Chicken Broth','Pâté Chicken Recipe in Chicken Broth',
  'Pâté Chicken & Beef Recipe in Chicken Broth','Pâté Chicken & Duck Recipe in Chicken Broth'],
 'Whole Foods':[
  'Whole Foods Chicken Recipe in Broth','Whole Foods Chicken & Beef Recipe in Broth','Whole Foods Chicken & Duck Recipe in Broth',
  'Whole Foods Chicken & Lamb Recipe in Broth','Whole Foods Chicken & Pork Recipe in Broth','Whole Foods Chicken & Quail Egg Recipe in Broth'],
 'Velvet Mousse':[
  'Velvet Mousse Chicken Recipe in Chicken Broth','Velvet Mousse Chicken & Beef Recipe in Chicken Broth',
  'Velvet Mousse Chicken & Duck Recipe in Chicken Broth','Velvet Mousse Chicken & Quail Egg Recipe in Chicken Broth']}.items():
    for n in names:add('After Dark',fam,n,source_key='after_dark')
for fam,n in [('Shreds','Shreds Variety Pack'),('Velvet Mousse','Velvet Mousse Variety Pack'),('Pâté','Pâté Variety Pack'),('Mixed','After Dark Variety Pack')]:
    add('After Dark',fam,n,role='variety_pack',source_key='after_dark')

# Friends
for fam,names in {
 'Minced':['Tuna & Pumpkin Recipe in Broth','Tuna, Ocean Whitefish & Pumpkin Recipe in Broth','Tuna, Shrimp & Pumpkin Recipe in Broth','Tuna, Tilapia & Pumpkin Recipe in Broth','Chicken & Pumpkin Recipe in Broth','Chicken, Pumpkin & Duck Recipe in Broth','Chicken, Pumpkin & Lamb Recipe in Broth','Chicken, Pumpkin & Tuna Recipe in Broth'],
 'Mousse':['Tuna & Pumpkin Recipe in Broth','Tuna, Pumpkin & Ocean Whitefish Recipe in Broth','Tuna, Pumpkin & Shrimp Recipe in Broth','Tuna, Pumpkin & Tilapia Recipe in Broth','Chicken & Pumpkin Recipe in Broth','Chicken, Pumpkin & Duck Recipe in Broth','Chicken, Pumpkin & Lamb Recipe in Broth','Chicken, Pumpkin & Tuna Recipe in Broth']}.items():
    for n in names:add('Friends',fam,n,source_key='friends')
for n in ['Minced: Tuna Variety Pack','Minced: Chicken Variety Pack','Mousse: Tuna Variety Pack','Mousse: Chicken Variety Pack','Minced: Tuna Mega Pack']:
    add('Friends','Variety Pack',n,role='variety_pack',source_key='friends')

# Grill
for n in ['Mackerel & Sardines Pate','Sardines Pate','Tuna & Crab Surimi Pate','Sardines & Lobster Consomme Pate','Tuna & Prawn Pate','Tuna & Crab Pate']:
    add('Grill','Pâté',n,source_key='grill')
for n in ['Hawaiian Grill Ahi Tuna','Hana Grill Ahi Tuna & Crab in Broth in Tuna Consommé','Manana Grill Ahi Tuna & Prawns in Broth in Tuna Consommé','Makaha Grill Mackerel & Sardines in Calamari Consommé','Tahitian Grill Sardine Cutlets in Sardine Consomme','Bora Bora Grill Sardine Cutlets in Lobster Consomme in Lobster Consommé','Lanai Grill Tuna & Crab Surimi in Crab Surimi Consommé']:
    add('Grill','Whole Foods',n,source_key='grill')

# Gelée
for n in ['Gelée Stix Chicken Recipe in Gelée','Gelée Tuna & Crab Recipe in Gelée']:
    add('Gelée','Gelée',n,source_key='gelee')

# Luau
for fam,names in {
 'Whole Foods':['Hookena Luau Ahi Tuna & Chicken Chicken in Chicken Consommé','Papeekeo Luau Ahi Tuna & Mackerel in Tuna Consommé','Koolina Luau Chicken & Egg in Chicken Consommé','Oahu Luau Seabass in Seabass Consommé','Puka Puka Luau Succulent Chicken in Chicken Consommé',"Kapi'Olani Luau Tilapia in Tilapia Consommé",'Hanalei Luau Wild Salmon in Salmon Consommé','Napili Luau Wild Salmon & Chicken in Chicken Consommé'],
 'Pâté':['Pate Tuna & Chicken Pate Recipe in Tuna Broth','Pate Tuna & Mackerel Pate in Tuna Broth','Pate Chicken & Egg Pate in Chicken Broth','Pate Seabass Pate in Seabass Broth','Pate Succulent Chicken Pate in Broth','Pate Tilapia Pate in Tilapia Consommé','Pate Wild Salmon Pate in Salmon Broth','Pate Wild Salmon & Chicken Pate in Salmon Broth']}.items():
    for n in names:add('Luau',fam,n,source_key='luau')

# Velvet Mousse (non-After-Dark)
for n in ['Velvet Mousse Hairball Control: Chicken & Tuna Recipe in Broth','Velvet Mousse Chicken in Broth','Velvet Mousse Chicken & Salmon in Broth','Velvet Mousse Chicken & Egg in Broth','Velvet Mousse Tuna & Chicken in Broth','Velvet Mousse Tuna & Mackerel in Broth','Velvet Mousse Salmon in Broth']:
    add('Velvet Mousse','Mousse',n,source_key='velvet_mousse')
add('Velvet Mousse','Variety Pack','Velvet Mousse Variety Pack',role='variety_pack',source_key='velvet_mousse')

# Baby wet products (including supportive wet products; role distinguishes non-meals)
for n in ['Pâté Chicken & Chicken Liver Recipe','Pâté Chicken, Duck & Duck Liver Recipe','Pâté Chicken, Salmon & Chicken Liver Recipe','Pâté Chicken, Tuna & Chicken Liver Recipe']:
    add('Baby','Pâté',n,source_key='baby')
for n in ['Mousse Salmon & Chicken in Broth','Mousse Chicken & Chicken Liver in Broth','Mousse Chicken, Tuna & Chicken Liver Recipe']:
    add('Baby','Mousse',n,source_key='baby')
for n in ['Mousse & Shreds Chicken, Duck & Duck Liver Recipe','Mousse & Shreds Chicken, Salmon & Chicken Liver Recipe','Mousse & Shreds Chicken, Tuna & Chicken Liver Recipe']:
    add('Baby','Mousse & Shreds',n,source_key='baby')
for n in ['Whole Foods Chicken & Egg Recipe','Whole Foods Chicken, Duck & Duck Liver Recipe','Whole Foods Chicken & Salmon Recipe','Whole Foods Chicken, Tuna, & Chicken Liver Recipe']:
    add('Baby','Whole Foods',n,source_key='baby')
for n in ['Pâté Variety Pack','Whole Foods Variety Pack','Favorites Mega Pack Whole Foods For Kittens']:
    add('Baby','Variety Pack',n,role='variety_pack',source_key='baby')
add('Baby','Purée','Weaning Purée: Chicken & Chicken Liver Recipe in Broth',role='transitional_food',source_key='baby')
add('Baby','Liquid','Milk Replacer With Goat\'s Milk',role='milk_replacer',source_key='baby')
add('Baby','Supplement','Thrive: Chicken & Chicken Liver Recipe Supplement',role='supplement',source_key='baby')

# Silver
add('Silver','Comfort Purée','Purée with Chicken, Chicken Liver & Pumpkin Recipe in Broth',source_key='silver')
add('Silver','Supplement','Supplement with Chicken & Chicken Liver Recipe',role='supplement',source_key='silver')
for n in ['Mousse with Salmon & Pumpkin in Broth','Mousse with Chicken, Duck & Duck Liver in Broth','Mousse with Chicken & Pumpkin in Broth','Mousse with Tuna, Mackerel & Pumpkin in Broth']:
    add('Silver','Mousse',n,source_key='silver')
for n in ['Mousse & Shreds Chicken, Salmon & Chicken Liver Recipe','Mousse & Shreds with Chicken, Duck & Duck Liver Recipe']:
    add('Silver','Mousse & Shreds',n,source_key='silver')
for n in ['Pâté: Chicken Recipe in Broth','Pâté: Chicken, Duck & Duck Liver Recipe in Broth','Pâté: Chicken, Salmon & Chicken Liver Recipe in Broth','Pâté: Tuna & Mackerel Recipe in Broth']:
    add('Silver','Pâté',n,source_key='silver')
for n in ['Whole Foods with Tuna & Mackerel Recipe','Whole Foods with Chicken Recipe']:
    add('Silver','Whole Foods',n,source_key='silver')

# Solutions wet foods only (not dry kibble/topper/supplement except complete liquid meal replacer)
for function,n in [
 ('Mineral Balance','Mousse: Tuna & Salmon Recipe'),('Dental','Mousse: Chicken Recipe in Broth'),('Skin & Coat','Mousse: Salmon Recipe in Broth'),
 ('Mobility','Mousse: Chicken & Tuna Recipe in Broth'),('Digestion','Mousse: Chicken & Egg Recipe in Broth'),
 ('Light','Mousse: Chicken, Turkey & Pumpkin Recipe in Broth'),('Fussy','Mousse: With Duck Liver & Egg Recipe in Broth')]:
    add('Solutions',function,n,source_key='solutions')
add('Solutions','Liquid Meal Replacer','With Tuna in Goat\'s Milk',role='complete_liquid_meal',source_key='solutions')

# Mega packs
for n in ['Friends Minced: Tuna Mega Pack','Baby Favorites Mega Pack Whole Foods For Kittens','Chicken Craves','Chicken Craves Paté','Fish Favorites Paté','Seafood Selects – 24 ct.','Seafood Selects – 36 ct.']:
    add('Mega Packs','Variety Pack',n,role='variety_pack',source_key='mega_packs')

# Born Carnivore wet entries; official line page mixes wet and dry, so only wet entries are included here.
for n in ['Chicken Breast & Chicken Liver Recipe in Chicken Broth','Chicken Breast & Duck Recipe in Chicken Broth','Chicken Breast & Egg Recipe in Chicken Broth','Chicken Breast & Salmon Recipe in Chicken Broth','Chicken Breast & Tuna Recipe in Chicken Broth','Chicken Breast & Turkey Recipe in Chicken Broth','Chicken Breast Recipe in Chicken Broth','Sardine Cutlets & Mackerel Recipe in Broth','Sardine Cutlets Recipe in Broth','Tuna & Crab Recipe in Tuna Broth','Tuna & Pollock Recipe in Tuna Broth','Tuna & Salmon Recipe in Tuna Broth','Tuna & Seabass Recipe in Tuna Broth','Tuna & Shrimp Recipe in Tuna Broth','Tuna Recipe in Tuna Broth']:
    add('Born Carnivore','Whole Foods',n,source_key='born_carnivore')
for n in ['Mousse: Chicken & Chicken Liver Recipe in Chicken Broth','Mousse: Chicken Recipe in Chicken Broth','Mousse: Tuna & Salmon Recipe in Tuna Broth','Mousse: Tuna & Shrimp Recipe in Tuna Broth','Mousse: Tuna Recipe in Tuna Broth']:
    add('Born Carnivore','Mousse',n,source_key='born_carnivore')
for n in ['Chicken Variety Pack','Tuna Variety Pack','Mousse: Tuna Variety Pack']:
    add('Born Carnivore','Variety Pack',n,role='variety_pack',source_key='born_carnivore')

# Stable IDs.
def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().lower()
    s=s.replace('&',' and ').replace("'",'')
    s=re.sub(r'\b(tiki cat|recipe|in broth|in chicken broth|in tuna broth|in salmon broth|in seabass broth|in tilapia consomme|consomme|consomme|pate|whole foods|velvet mousse|mousse|shreds|soft|with)\b',' ',s)
    s=re.sub(r'[^a-z0-9]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()
def slug(s):
    raw=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().lower().replace('&',' and ')
    return re.sub(r'[^a-z0-9]+','-',raw).strip('-')[:72]
seen={}
for p in PRODUCTS:
    base='tiki-'+slug(p['line'])+'-'+slug(p['family'])+'-'+slug(p['current_name'])
    n=seen.get(base,0)+1;seen[base]=n
    p['id']=base if n==1 else f'{base}-{n}'

# Read existing immutable source data.
txt=FOODS.read_text(encoding='utf-8')
m=re.search(r'window\.CATFOOD_DATA\s*=\s*(\[.*?\]);\s*window\.CATFOOD_META',txt,re.S)
foods=json.loads(m.group(1))
source_records=[]
for f in foods:
    if str(f.get('brand','')).lower() in {'tiki cat','tiki cat '} or 'tiki cat' in str(f.get('brand','')).lower():
        source_records.append({
            'source_id':f['id'],'dataset':f.get('dataset'),'brand':f.get('brand'),'line':f.get('line'),'product':f.get('product'),'style':f.get('style'),
            'source_page':f.get('source_page'),'updated':f.get('updated'),'fpuo':bool(f.get('source_personal_use_only'))
        })

# Candidate-line mapping: conservative; unresolved is preferable to a false match.
LINE_MAP={
 'after dark':['After Dark'],'after dark pate+':['After Dark'],'after dark soft pate':['After Dark'],'after dark velvet mousse':['After Dark'],
 'aloha friends':['Friends'],'grill':['Grill'],'luau':['Luau'],'luau pate':['Luau'],'luau velvet':['Velvet Mousse'],
 'baby':['Baby'],'silver, 11+':['Silver'],'special, fussy':['Solutions'],'special, light':['Solutions'],'special, skin & coat':['Solutions'],
 'velvet, kitten':['Baby'],'velvet, senior':['Silver'],
 'chicken (no fish)':['Luau'],'chicken/fish':['Luau'],'fish/seafood':['Luau','Grill'],
}

# Exact legacy name associations from official current catalog pages.
LEGACY_OVERRIDES={
 'p53r20':('Luau','Puka Puka Luau'), 'p53r21':('Luau','Koolina Luau'), 'p53r24':('Luau','Hookena Luau'), 'p53r25':('Luau','Napili Luau'),
 'p54r04':('Luau','Hanalei Luau'), 'p54r08':('Grill','Manana Grill'), 'p54r10':('Luau','Papeekeo Luau'), 'p54r11':('Grill','Tahitian Grill'),
 'p53r28':('Grill','Bora Bora Grill'), 'p53r29':('Grill','Hana Grill'), 'p54r07':('Grill','Lanai Grill'), 'p54r07':('Grill','Lanai Grill'),
}

# Product-specific old->current equivalences that wording alone can miss.
PRODUCT_OVERRIDES={
 # After Dark whole foods/shreds
 'fdsgw-p36r10':'Whole Foods Chicken & Beef Recipe in Broth', 'fdsgw-p36r11':'Whole Foods Chicken & Duck Recipe in Broth',
 'fdsgw-p36r12':'Whole Foods Chicken & Lamb Recipe in Broth','fdsgw-p37r01':'Whole Foods Chicken & Pork Recipe in Broth',
 'fdsgw-p37r02':'Whole Foods Chicken & Quail Egg Recipe in Broth','fdsgw-p37r03':'Whole Foods Chicken Recipe in Broth',
 # Pate+
 'fdsgw-p37r07':'Pâté Chicken & Beef Recipe in Chicken Broth','fdsgw-p37r08':'Pâté Chicken & Duck Recipe in Chicken Broth',
 'fdsgw-p37r09':'Pâté Chicken & Quail Egg Recipe in Chicken Broth','fdsgw-p37r10':'Pâté Chicken Recipe in Chicken Broth',
 # Soft pate
 'fdsgw-p36r08':'Pâté Beef & Beef Liver Recipe','fdsgw-p36r09':'Pâté Beef & Beef Liver Recipe',
 'fdsgw-p37r04':'Pâté Duck & Chicken Liver Recipe','fdsgw-p37r05':'Pâté Rabbit & Chicken Liver Recipe','fdsgw-p37r06':'Pâté Venison & Beef Liver Recipe',
 'fdsgw-p37r11':'Pâté Beef & Beef Liver Recipe','fdsgw-p37r12':'Pâté Chicken, Chicken Liver & Quail Recipe',
 'fdsgw-p38r01':'Pâté Duck & Chicken Liver Recipe','fdsgw-p38r02':'Pâté Lamb & Beef Liver Recipe','fdsgw-p38r03':'Pâté Rabbit & Chicken Liver Recipe',
 'fdsgw-p38r04':'Pâté Turkey & Turkey Liver Recipe','fdsgw-p38r05':'Pâté Venison & Beef Liver Recipe',
 # After Dark mousse
 'fdsgw-p38r06':'Velvet Mousse Chicken & Beef Recipe in Chicken Broth','fdsgw-p38r07':'Velvet Mousse Chicken & Duck Recipe in Chicken Broth',
 'fdsgw-p38r08':'Velvet Mousse Chicken & Quail Egg Recipe in Chicken Broth','fdsgw-p38r09':'Velvet Mousse Chicken Recipe in Chicken Broth',
 # Friends legacy Aloha
 'fdsgw-p38r10':'Chicken & Pumpkin Recipe in Broth','fdsgw-p38r12':'Chicken, Pumpkin & Duck Recipe in Broth','fdsgw-p39r02':'Chicken, Pumpkin & Lamb Recipe in Broth',
 'fdsgw-p39r03':'Tuna & Pumpkin Recipe in Broth','fdsgw-p39r05':'Tuna, Ocean Whitefish & Pumpkin Recipe in Broth','fdsgw-p39r06':'Tuna, Shrimp & Pumpkin Recipe in Broth','fdsgw-p39r07':'Tuna, Tilapia & Pumpkin Recipe in Broth',
 # Grill
 'fdsgw-p39r12':'Hawaiian Grill Ahi Tuna','fdsgw-p40r01':'Hana Grill Ahi Tuna & Crab in Broth in Tuna Consommé','fdsgw-p40r02':'Manana Grill Ahi Tuna & Prawns in Broth in Tuna Consommé',
 'fdsgw-p40r03':'Makaha Grill Mackerel & Sardines in Calamari Consommé','fdsgw-p40r05':'Bora Bora Grill Sardine Cutlets in Lobster Consomme in Lobster Consommé','fdsgw-p40r06':'Tahitian Grill Sardine Cutlets in Sardine Consomme','fdsgw-p40r10':'Lanai Grill Tuna & Crab Surimi in Crab Surimi Consommé',
 'fdsgw-p40r04':'Mackerel & Sardines Pate','fdsgw-p40r07':'Sardines & Lobster Consomme Pate','fdsgw-p40r08':'Sardines Pate','fdsgw-p40r09':'Tuna & Crab Pate','fdsgw-p40r11':'Tuna & Crab Surimi Pate','fdsgw-p40r12':'Tuna & Prawn Pate',
 # Luau
 'fdsgw-p41r01':'Hookena Luau Ahi Tuna & Chicken Chicken in Chicken Consommé','fdsgw-p41r02':'Papeekeo Luau Ahi Tuna & Mackerel in Tuna Consommé','fdsgw-p41r03':'Koolina Luau Chicken & Egg in Chicken Consommé','fdsgw-p41r04':'Oahu Luau Seabass in Seabass Consommé','fdsgw-p41r05':'Puka Puka Luau Succulent Chicken in Chicken Consommé',"fdsgw-p41r06":"Kapi'Olani Luau Tilapia in Tilapia Consommé",'fdsgw-p41r07':'Hanalei Luau Wild Salmon in Salmon Consommé','fdsgw-p41r08':'Napili Luau Wild Salmon & Chicken in Chicken Consommé',
 'fdsgw-p41r09':'Pate Chicken & Egg Pate in Chicken Broth','fdsgw-p41r10':'Pate Seabass Pate in Seabass Broth','fdsgw-p41r11':'Pate Succulent Chicken Pate in Broth','fdsgw-p41r12':'Pate Tilapia Pate in Tilapia Consommé','fdsgw-p42r01':'Pate Tuna & Chicken Pate Recipe in Tuna Broth','fdsgw-p42r02':'Pate Tuna & Mackerel Pate in Tuna Broth','fdsgw-p42r03':'Pate Wild Salmon & Chicken Pate in Salmon Broth','fdsgw-p42r04':'Pate Wild Salmon Pate in Salmon Broth',
 # Velvet Mousse formerly Luau Velvet
 'fdsgw-p42r05':'Velvet Mousse Chicken & Egg in Broth','fdsgw-p42r06':'Velvet Mousse Chicken & Salmon in Broth','fdsgw-p42r07':'Velvet Mousse Chicken in Broth','fdsgw-p42r08':'Velvet Mousse Salmon in Broth','fdsgw-p42r09':'Velvet Mousse Tuna & Chicken in Broth','fdsgw-p42r10':'Velvet Mousse Tuna & Mackerel in Broth',
 # Baby
 'fdsgw-p39r08':'Whole Foods Chicken & Egg Recipe','fdsgw-p39r09':'Whole Foods Chicken & Salmon Recipe','fdsgw-p39r10':'Mousse & Shreds Chicken, Salmon & Chicken Liver Recipe',
 'fdsgw-p43r08':'Mousse Chicken & Chicken Liver in Broth','fdsgw-p43r09':'Mousse Salmon & Chicken in Broth',
 # Silver
 'fdsgw-p42r11':'Mousse with Chicken & Pumpkin in Broth','fdsgw-p42r12':'Whole Foods with Chicken Recipe',
 'fdsgw-p43r01':'Mousse & Shreds with Chicken, Duck & Duck Liver Recipe','fdsgw-p43r02':'Mousse & Shreds Chicken, Salmon & Chicken Liver Recipe',
 'fdsgw-p43r03':'Mousse with Salmon & Pumpkin in Broth','fdsgw-p43r04':'Whole Foods with Tuna & Mackerel Recipe',
 'fdsgw-p43r10':'Mousse with Chicken & Pumpkin in Broth','fdsgw-p43r11':'Mousse with Salmon & Pumpkin in Broth',
 # Solutions
 'fdsgw-p43r05':'Mousse: With Duck Liver & Egg Recipe in Broth','fdsgw-p43r06':'Mousse: Chicken, Turkey & Pumpkin Recipe in Broth','fdsgw-p43r07':'Mousse: Salmon Recipe in Broth',
}

# A few current products are represented in source data but have not yet appeared in the current category list used above.
# Keep these unresolved rather than inventing an equivalence.

def score(src,p):
    a=norm((src.get('product') or '')+' '+(src.get('style') or ''))
    b=norm(p['current_name'])
    if not a or not b:return 0
    ta=set(a.split());tb=set(b.split())
    jac=len(ta&tb)/max(1,len(ta|tb))
    seq=SequenceMatcher(None,a,b).ratio()
    return .62*jac+.38*seq

links=[]
by_name={p['current_name']:p for p in PRODUCTS}
for src in source_records:
    sid=src['source_id']
    if sid in PRODUCT_OVERRIDES and PRODUCT_OVERRIDES[sid] in by_name:
        p=by_name[PRODUCT_OVERRIDES[sid]];links.append({'source_id':sid,'current_product_id':p['id'],'status':'verified_name_match','confidence':1.0,'basis':'manual reconciliation against current Tiki Pets catalog'});continue
    if sid in LEGACY_OVERRIDES:
        line,needle=LEGACY_OVERRIDES[sid]
        cands=[p for p in PRODUCTS if p['line']==line and needle.lower() in p['current_name'].lower()]
        if cands:
            links.append({'source_id':sid,'current_product_id':cands[0]['id'],'status':'verified_legacy_match','confidence':.98,'basis':'legacy Tiki product name retained on current official catalog'});continue
    allowed=LINE_MAP.get(str(src.get('line') or '').lower())
    if not allowed:
        links.append({'source_id':sid,'current_product_id':None,'status':'unresolved','confidence':0.0,'basis':'no conservative line-level reconciliation rule'});continue
    cands=[p for p in PRODUCTS if p['line'] in allowed]
    ranked=sorted(((score(src,p),p) for p in cands),reverse=True,key=lambda x:x[0])
    if ranked and ranked[0][0]>=0.90:
        links.append({'source_id':sid,'current_product_id':ranked[0][1]['id'],'status':'probable_name_match','confidence':round(ranked[0][0],3),'basis':'normalized product-name similarity; retained as non-destructive reconciliation'})
    else:
        links.append({'source_id':sid,'current_product_id':None,'status':'unresolved','confidence':round(ranked[0][0],3) if ranked else 0.0,'basis':'no sufficiently strong current-catalog match'})

# Attach legacy/source aliases to canonical current records, without changing foods.js.
prod_by_id={p['id']:p for p in PRODUCTS}
for l in links:
    if not l['current_product_id'] or not l['status'].startswith('verified_'):continue
    src=next(s for s in source_records if s['source_id']==l['source_id'])
    legacy=' · '.join(str(x) for x in [src.get('line'),src.get('product'),src.get('style')] if x)
    if legacy and legacy not in prod_by_id[l['current_product_id']]['aliases']:
        prod_by_id[l['current_product_id']]['aliases'].append(legacy)

# Catalog stats.
from collections import Counter
status_counts=Counter(l['status'] for l in links)
line_counts=Counter(p['line'] for p in PRODUCTS)
obj={
 'meta':{
   'database':'Tiki Cat reconciliation database','schema_version':'1.0','verified_on':VERIFIED_ON,
   'scope':'Tiki Cat wet-food current catalog plus non-destructive links to existing CatFood Compass source records',
   'source_of_current_catalog':'Tiki Pets official website','current_catalog_url':SOURCES['catalog'],
   'preservation_rule':'Existing Pierson/FDSG records remain immutable source observations. This database links to them; it does not overwrite them.',
   'current_product_count':len(PRODUCTS),'source_record_count':len(source_records),'reconciliation_counts':dict(status_counts),
   'current_line_counts':dict(sorted(line_counts.items())),
   'notes':['Current manufacturer catalog names are stored separately from historical/source names.','A missing current match means unresolved, not discontinued, unless separately verified.','FDSG wet source restrictions remain attached to the original records.']
 },
 'sources':SOURCES,
 'current_products':PRODUCTS,
 'source_records':source_records,
 'reconciliation':links
}
OUT_JSON.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
OUT_JS.write_text('window.TIKI_CAT_DB = '+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
print(json.dumps(obj['meta'],indent=2,ensure_ascii=False))
# concise unresolved report
un=[l for l in links if l['status']=='unresolved']
print('\nUnresolved:',len(un))
for l in un:
    s=next(s for s in source_records if s['source_id']==l['source_id'])
    print(l['source_id'], '|',s.get('line'),'|',s.get('product'),'|',s.get('style'),'| best',l['confidence'])
