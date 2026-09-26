import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'data'/'foods.js').read_text(encoding='utf-8')
m=re.search(r'window\.CATFOOD_DATA = (.*?);\nwindow\.CATFOOD_META = (.*?);\s*$',s,re.S)
if not m: raise SystemExit('Could not locate dataset')
data=json.loads(m.group(1)); meta=json.loads(m.group(2))
assert len(data)==meta['record_count']
assert len(data)>2000, len(data)
assert len({r['id'] for r in data})==len(data)
assert all(r.get('id') and r.get('brand') and r.get('product') for r in data)
counts={k:sum(r.get('dataset')==k for r in data) for k in ('pierson_2017','fdsg_wet','fdsg_dry')}
assert counts==meta['counts'], (counts,meta['counts'])
# Source anomalies are preserved, not silently corrected. Non-flagged complete macros should be close to 100.
for r in data:
    vals=[r.get(k) for k in ('protein_cal_pct','fat_cal_pct','carb_cal_pct')]
    if None not in vals and not r.get('source_anomaly'):
        total=sum(vals)
        assert 95 <= total <= 105, (r['id'],total)
# Historical regression check.
assert any(r['dataset']=='pierson_2017' and r['brand']=='FANCY FEAST' and r['product']=='Tender Liver & Chicken Feast' and r['carb_cal_pct']==2 for r in data)
# Manual spot checks across several Pierson brands/pages preserve source values.
def hit(brand, product, p, f, c, ph):
    return any(r.get('dataset')=='pierson_2017' and r.get('brand')==brand and r.get('product')==product and r.get('protein_cal_pct')==p and r.get('fat_cal_pct')==f and r.get('carb_cal_pct')==c and r.get('phosphorus_mg_per_100kcal')==ph for r in data)
assert hit('FANCY FEAST','Tender Liver & Chicken Feast',43,55,2,478)
assert hit('FRISKIES','Turkey & Giblets',37,59,5,335)
assert hit('NULO','Turkey & Chicken',35,64,1,360)
assert hit('SHEBA','All varieties - approximate values',42,56,3,236)
assert hit('HOLISTIC SELECT','Chicken',32,66,2,221)
# New wet source regression checks.
assert any(r['dataset']=='fdsg_wet' and r['brand']=='Bixbi' and r['product']=='Chicken & Pumpkin' and r['protein_cal_pct']==38.8 and r['carb_cal_pct']==8.2 and r['phosphorus_mg_per_100kcal']==260 for r in data)
assert any(r['dataset']=='fdsg_wet' and r['brand']=='Rawz' and r['product']=='Chicken Breast & Duck' and r['carb_cal_pct']==0.5 and r['updated']=='3/4/26' for r in data)
# Dry source keeps current and prior recipe values distinct.
assert any(r['dataset']=='fdsg_dry' and r['brand']=="Dr Elsey's" and r['product']=='Chicken' and r['carb_cal_pct']==0.8 and '3.72' in r['previous_carb_display'] for r in data)
assert any(r['dataset']=='fdsg_dry' and r['brand']=='Young Again' and r['product']=='ZERO Mature' and r['carb_display']=='Trace' for r in data)
print(f"PASS: {len(data)} records: {counts}; flagged source anomalies: {sum(bool(r.get('source_anomaly')) for r in data)}")
