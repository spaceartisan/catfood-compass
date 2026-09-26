#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
import pdfplumber

PDF = Path(sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/Known values for Cat Foods-4 - Wet.pdf')
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else '/mnt/data/catfood-compass/data/fdsg_wet.json')

BINS = [
    ('brand',49.5,90),('collection',90,140),('flavor',140,195),('style',195,228),
    ('protein',228,250.5),('fat',250.5,273.5),('carb',273.5,295.5),('kcal',295.5,327),
    ('phos',327,354),('mg',354,380),('ca',380,405),('na',405,431),('updated',431,500),
]

def boundaries(page):
    ys=[]
    for line in page.lines:
        if abs(line['top']-line['bottom']) < 0.5 and line['width'] > 100 and 145 < line['top'] < 760:
            ys.append(float(line['top']))
    result=[]
    for y in sorted(ys):
        if not result or abs(y-result[-1]) > 1.5:
            result.append(y)
    return result

def cell(words, x0, x1, y0, y1):
    selected=[]
    for w in words:
        cx=(w['x0']+w['x1'])/2
        cy=(w['top']+w['bottom'])/2
        if x0 <= cx < x1 and y0 < cy < y1:
            selected.append(w)
    selected.sort(key=lambda w:(w['top'],w['x0']))
    lines=[]
    for w in selected:
        if not lines or abs(w['top']-lines[-1][0]) > 2.2:
            lines.append([w['top'],[w]])
        else:
            lines[-1][1].append(w)
    return ' '.join(' '.join(x['text'] for x in line[1]) for line in lines).strip()

def numbers(text):
    if not text: return []
    return [float(x.replace(',','')) for x in re.findall(r'(?<!\d)-?\d+(?:\.\d+)?', text.replace('–','-').replace('—','-'))]

def first(text):
    ns=numbers(text)
    return ns[0] if ns else None

def exact_year(date):
    m=re.fullmatch(r'\d{1,2}/\d{1,2}/(\d{2})', date or '')
    return 2000+int(m.group(1)) if m else None

records=[]
with pdfplumber.open(PDF) as pdf:
    for page_num,page in enumerate(pdf.pages,1):
        ys=boundaries(page)
        words=page.extract_words(x_tolerance=1,y_tolerance=2,use_text_flow=False)
        for row_num,(y0,y1) in enumerate(zip(ys[:-1],ys[1:]),1):
            raw={name:cell(words,x0,x1,y0,y1) for name,x0,x1 in BINS}
            if not raw['brand'] or not (raw['flavor'] or raw['collection'] or raw['style']):
                continue
            protein,fat,carb=first(raw['protein']),first(raw['fat']),first(raw['carb'])
            kcal,phos,mg,ca,na=(numbers(raw[x]) for x in ('kcal','phos','mg','ca','na'))
            # Preserve every source product row, even when the source leaves all nutrition cells blank.
            # Those rows remain searchable catalog entries and are explicitly marked as source-no-values.
            has_numeric = any(v is not None for v in (protein,fat,carb)) or bool(kcal) or bool(phos)
            macro_sum=sum((protein,fat,carb)) if None not in (protein,fat,carb) else None
            text=' '.join((raw['brand'],raw['collection'],raw['flavor'],raw['style']))
            rec={
                'id':f'fdsgw-p{page_num:02d}r{row_num:02d}',
                'dataset':'fdsg_wet','brand':raw['brand'],'line':raw['collection'] or None,
                'product':raw['flavor'] or raw['collection'] or raw['style'],'style':raw['style'] or None,
                'protein_cal_pct':protein,'protein_cal_pct_min':protein,'protein_cal_pct_max':protein,'protein_display':raw['protein'] or None,
                'fat_cal_pct':fat,'fat_cal_pct_min':fat,'fat_cal_pct_max':fat,'fat_display':raw['fat'] or None,
                'carb_cal_pct':carb,'carb_cal_pct_min':carb,'carb_cal_pct_max':carb,'carb_display':raw['carb'] or None,
                'kcal_per_100g':kcal[0] if kcal else None,'kcal_per_100g_min':min(kcal) if kcal else None,'kcal_per_100g_max':max(kcal) if kcal else None,'kcal_per_100g_display':raw['kcal'] or None,
                'phosphorus_mg_per_100kcal':phos[0] if phos else None,'phosphorus_mg_per_100kcal_min':min(phos) if phos else None,'phosphorus_mg_per_100kcal_max':max(phos) if phos else None,'phosphorus_display':raw['phos'] or None,
                'magnesium_mg_per_100kcal':mg[0] if mg else None,'magnesium_display':raw['mg'] or None,
                'calcium_mg_per_100kcal':ca[0] if ca else None,'calcium_display':raw['ca'] or None,
                'sodium_mg_per_100kcal':na[0] if na else None,'sodium_display':raw['na'] or None,
                'updated':raw['updated'] or None,'source_page':page_num,'source_row':row_num,'source_year':exact_year(raw['updated']),
                'source_type':'FDSG compilation from manufacturer emails/websites; typical analysis where provided',
                'source_name':'Known values for Cat Foods - Wet (FDSG)','verification_status':'source-dated' if raw['updated'] else 'source-undated',
                'source_personal_use_only':True,
                'source_has_numeric_values':has_numeric,
                'prescription':bool(re.search(r'\b(rx|theradiet|veterinary|diabetic support|renal support|urinary support|\bdm\b)',text,re.I)),
                'form':'wet','macro_sum':macro_sum,'macro_sum_ok':macro_sum is not None and 95<=macro_sum<=105,
                'source_anomaly':bool((carb is not None and carb<0) or (macro_sum is not None and not 95<=macro_sum<=105)),
                'data_complete':None not in (protein,fat,carb) and bool(phos),
            }
            records.append(rec)

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'wrote {len(records)} source product rows to {OUT}')
print(f'with full macros: {sum(None not in (r["protein_cal_pct"],r["fat_cal_pct"],r["carb_cal_pct"]) for r in records)}')
print(f'with phosphorus: {sum(r["phosphorus_mg_per_100kcal"] is not None for r in records)}')
print(f'source anomalies preserved/flagged: {sum(r["source_anomaly"] for r in records)}')
