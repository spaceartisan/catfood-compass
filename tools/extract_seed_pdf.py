import pdfplumber, re, json
from pathlib import Path
PDF=Path('/mnt/data/CatFoodProteinFatCarbPhosphorusChart-1.pdf')
OUT=Path('/mnt/data/catfood_records_v2.json')

BRANDS=[
'AGAINST the GRAIN','ARTEMIS','AVODERM','B.F.F. (Weruva)','BEYOND','BLUE','CANIDAE','CHICKEN SOUP FOR the SOUL',
'DAVE’s','DAVE\'s','DR. TIM’S','DRS. FOSTER & SMITH','EARTHBORN','EVO','EVOLVE','FANCY FEAST','FIRST MATE','4HEALTH',
'FRESHPET','FRISKIES','FROMM','FUSSIE CAT','GO','HALO','HILL’s','HILL’S','HILL\'S','HI-TOR','HOLISTIC SELECT','HOUNDS & GATOS',
'IAMS','I and Love and You','KASIKS','KOHA','LOTUS','MEOW MIX','MERRICK','NATURAL BALANCE','NATURAL PLANET','NATURE’S LOGIC',
'NATURE’S RECIPE','NATURE’S VARIETY','NEWMAN’S OWN','9Lives','NULO','NUTRISH','NUTRI SOURCE','NUTRO','ORGANIX','PINNACLE',
'PRECISE','PRO PLAN','PURE-VITA','PURINA ONE','ROYAL CANIN','SCIENCE DIET','SHEBA','SOULISTIC','TENDER and TRUE','TIKI CAT',
'TRIUMPH','VeRUS','WELLNESS','WERUVA','WHOLE EARTH FARMS','WILD CALLING','ZIWIPEAK','PURINA'
]
# longest first to avoid prefix ambiguity
BRANDS=sorted(BRANDS,key=len,reverse=True)

def clean(s):
    if s is None:return None
    s=s.replace('\u00ad','').replace('\x00','').replace('ﬁ','fi').replace('ﬂ','fl')
    s=re.sub(r'\s+',' ',s.strip())
    return s

def parse_num_range(s):
    s=clean(s)
    if not s:return None
    m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)',s)
    if m:
        a,b=map(float,m.groups());return {'min':a,'max':b,'value':(a+b)/2,'display':s}
    m=re.fullmatch(r'\d+(?:\.\d+)?',s)
    if m:
        v=float(s);return {'min':v,'max':v,'value':v,'display':s}
    return None

def canonical_brand(b):
    b=clean(b) or ''
    b=b.replace('HILL’s',"HILL'S").replace('HILL’S',"HILL'S")
    b=b.replace('DAVE’s',"DAVE'S")
    return b

def parse_header(raw):
    if not raw:return None
    flat=clean(raw)
    for b in BRANDS:
        if flat.lower().startswith(b.lower()):
            cb=canonical_brand(b)
            rest=flat[len(b):].strip(' -')
            # BEYOND appears as "BEYOND - GRAVY Grain Free"
            return cb, (rest or None)
    return None

def parse_section_amount(note):
    note=clean(note)
    if not note:return []
    low=note.lower().replace('0z','oz')
    # ordered ounce amounts; handles 3 oz/5.5 oz and 2.8 oz/6.0 oz
    nums=[]
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(oz|ounce|ounces|g|gram|grams)',low):
        nums.append((float(m.group(1)),m.group(2)))
    if len(nums)==1 and '/' in low:
        # e.g. "3.2/6.0 oz" first amount lacks unit
        m=re.search(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*(oz|g)',low)
        if m:
            nums=[(float(m.group(1)),m.group(3)),(float(m.group(2)),m.group(3))]
    return nums

def parse_calories(raw,section_note):
    s=clean(raw); note=clean(section_note)
    out={'value':None,'min':None,'max':None,'package_amount':None,'package_unit':None,'display':s,'options':None,'ambiguous':False}
    if not s:return out
    if '=' in s:
        out['ambiguous']=True;return out
    # labeled multi-size values like "3 oz: 104-114 5.5 oz: 191-210"
    labeled=[]
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*oz\s*:\s*(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?',s,re.I):
        amt=float(m.group(1)); a=float(m.group(2)); b=float(m.group(3)) if m.group(3) else a
        labeled.append({'kcal_min':a,'kcal_max':b,'kcal':(a+b)/2,'amount':amt,'unit':'oz'})
    if labeled:
        out['options']=labeled
        if len(labeled)==1:
            o=labeled[0];out.update(value=o['kcal'],min=o['kcal_min'],max=o['kcal_max'],package_amount=o['amount'],package_unit=o['unit'])
        else: out['ambiguous']=True
        return out
    # kcal/size explicit
    m=re.fullmatch(r'(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?\s*/\s*(\d+(?:\.\d+)?)\s*(oz|g|cup|container|pouch|can)?',s,re.I)
    if m:
        a=float(m.group(1));b=float(m.group(2)) if m.group(2) else a;amt=float(m.group(3));unit=m.group(4)
        out.update(value=(a+b)/2,min=a,max=b,package_amount=amt,package_unit=(unit.lower() if unit else None))
        return out
    # a/b paired kcal with a section note that defines paired sizes
    m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)',s)
    if m:
        sizes=parse_section_amount(note)
        if len(sizes)>=2:
            vals=[float(m.group(1)),float(m.group(2))]
            out['options']=[{'kcal':vals[i],'kcal_min':vals[i],'kcal_max':vals[i],'amount':sizes[i][0],'unit':sizes[i][1]} for i in range(2)]
            out['ambiguous']=True
        else: out['ambiguous']=True
        return out
    # simple number/range, use section package if a single size is specified
    m=re.fullmatch(r'(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?',s)
    if m:
        a=float(m.group(1));b=float(m.group(2)) if m.group(2) else a
        out.update(value=(a+b)/2,min=a,max=b)
        sizes=parse_section_amount(note)
        if len(sizes)==1:
            out['package_amount'],out['package_unit']=sizes[0]
        elif note:
            low=note.lower()
            for u in ['pouch','can','container','cup','nugget','medallion']:
                if u in low:out['package_unit']=u;break
        return out
    out['ambiguous']=True;return out

def likely_note(name,row):
    n=clean(name) or ''
    if len(n)>110:return True
    if n.lower().startswith(('please note','this company','petsmart brand','purchase is not recommended')):return True
    # long prose in second column indicates a section note, but c0 may still be a brand header handled before this
    c1=clean(row[1])
    if c1 and len(c1)>80:return True
    return False

records=[]
current_brand=None;current_line=None;section_cal_note=None;section_note=None;last_group=None
with pdfplumber.open(PDF) as pdf:
    for pageno in range(5,65):
        table=pdf.pages[pageno-1].extract_table()
        if not table:continue
        for ridx,row in enumerate(table[3:],start=4):
            row=(row or [])+[None]*9
            raw_name=row[0];name=clean(raw_name)
            if not name:continue
            # First detect true section header by known brand prefix
            h=parse_header(raw_name)
            if h:
                current_brand,current_line=h
                section_cal_note=clean(row[7])
                section_note=clean(row[1]) if row[1] and len(clean(row[1]))>40 else None
                last_group=None
                continue
            if name in {'COMPANY Flavor/Style','Print','Caloric Distribution'} or name.isdigit():continue
            if not current_brand:continue
            p=parse_num_range(row[1]);f=parse_num_range(row[2]);c=parse_num_range(row[3]);ph=parse_num_range(row[5])
            has_any=any(x is not None for x in [p,f,c,ph])
            merged=all(row[i] is None for i in [1,2,3,5]) and last_group is not None
            # ignore prose notes; preserve product rows with blank values
            if likely_note(name,row) and not has_any and not merged:
                # if this is a long line name with numeric calories it may still be product, but long c1 prose means note
                continue
            if merged:
                p,f,c,ph=last_group['p'],last_group['f'],last_group['c'],last_group['ph']
                inherited=True
                cal_raw=last_group['cal_raw'] if row[7] is None else clean(row[7])
            else:
                inherited=False
                cal_raw=clean(row[7])
                if has_any:
                    last_group={'p':p,'f':f,'c':c,'ph':ph,'cal_raw':cal_raw}
                else:
                    last_group=None
            cal=parse_calories(cal_raw,section_cal_note)
            # include blank-data product rows too (historical chart explicitly has blanks)
            rec={
                'id':f'p{pageno:02d}r{ridx:02d}',
                'brand':current_brand,'line':current_line,'product':name,
                'protein_cal_pct':p['value'] if p else None,'protein_cal_pct_min':p['min'] if p else None,'protein_cal_pct_max':p['max'] if p else None,'protein_display':p['display'] if p else None,
                'fat_cal_pct':f['value'] if f else None,'fat_cal_pct_min':f['min'] if f else None,'fat_cal_pct_max':f['max'] if f else None,'fat_display':f['display'] if f else None,
                'carb_cal_pct':c['value'] if c else None,'carb_cal_pct_min':c['min'] if c else None,'carb_cal_pct_max':c['max'] if c else None,'carb_display':c['display'] if c else None,
                'phosphorus_mg_per_100kcal':ph['value'] if ph else None,'phosphorus_mg_per_100kcal_min':ph['min'] if ph else None,'phosphorus_mg_per_100kcal_max':ph['max'] if ph else None,'phosphorus_display':ph['display'] if ph else None,
                'calories':cal['value'],'calories_min':cal['min'],'calories_max':cal['max'],'calorie_amount':cal['package_amount'],'calorie_unit':cal['package_unit'],'calories_display':cal['display'],'calorie_options':cal['options'],'calories_ambiguous':cal['ambiguous'],
                'section_calorie_note':section_cal_note,'section_note':section_note,
                'analysis_shared':inherited,
                'source_page':pageno,'source_row':ridx,'source_year':2017,'source_type':'Typical Nutrient Analysis (TNA)','source_name':'Cat Food - Nutritional Composition (Lisa A. Pierson, DVM)','verification_status':'historical',
                'prescription': pageno>=61,
                'form':'dry' if ('(DRY)' in name.upper() or (cal['package_unit']=='cup' and pageno>=61)) else 'wet'
            }
            vals=[rec['protein_cal_pct'],rec['fat_cal_pct'],rec['carb_cal_pct']]
            rec['macro_sum']=sum(vals) if all(v is not None for v in vals) else None
            rec['macro_sum_ok']=(97<=rec['macro_sum']<=103) if rec['macro_sum'] is not None else None
            rec['data_complete']=all(rec[k] is not None for k in ['protein_cal_pct','fat_cal_pct','carb_cal_pct','phosphorus_mg_per_100kcal'])
            records.append(rec)

# light normalization of obvious OCR/typo display only; preserve product wording otherwise
for r in records:
    r['brand']=canonical_brand(r['brand'])
    if r['line']:r['line']=r['line'].replace('WIth','With').replace('calries','calories')

OUT.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('records',len(records),'brands',len(set(r['brand'] for r in records)))
from collections import Counter
for b,n in Counter(r['brand'] for r in records).most_common():print(n,b)
print('complete macros',sum(all(r[k] is not None for k in ['protein_cal_pct','fat_cal_pct','carb_cal_pct']) for r in records))
print('phos',sum(r['phosphorus_mg_per_100kcal'] is not None for r in records),'cal',sum(r['calories'] is not None for r in records))
print('bad macro sums',sum(r['macro_sum_ok'] is False for r in records))
