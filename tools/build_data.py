#!/usr/bin/env python3
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
foods_js=ROOT/'data'/'foods.js'
text=foods_js.read_text(encoding='utf-8')
m=re.search(r'window\.CATFOOD_DATA = (\[.*?\]);\s*window\.CATFOOD_META = ',text,re.S)
if not m: raise SystemExit('could not parse existing foods.js')
historical=json.loads(m.group(1))
for r in historical:
    r['dataset']='pierson_2017'
wet=json.loads((ROOT/'data'/'fdsg_wet.json').read_text(encoding='utf-8'))
dry=json.loads((ROOT/'data'/'fdsg_dry.json').read_text(encoding='utf-8'))
all_foods=historical+wet+dry
ids=[r['id'] for r in all_foods]
if len(ids)!=len(set(ids)): raise SystemExit('duplicate IDs')
meta={
  'app_version':'0.2.7','dataset_version':'multi-source-v2','record_count':len(all_foods),
  'counts':{'pierson_2017':len(historical),'fdsg_wet':len(wet),'fdsg_dry':len(dry)},
  'sources':[
    {'dataset':'pierson_2017','title':'Cat Food - Nutritional Composition','compiler':'Lisa A. Pierson, DVM','year':2017,'basis':'Typical Nutrient Analysis (TNA) data provided by respective companies','primary_macros':'percent of calories','phosphorus_basis':'mg per 100 kcal','historical':True},
    {'dataset':'fdsg_wet','title':'Known values for Cat Foods - Wet','compiler':'FDSG compilation','basis':'Manufacturer emails/websites; typical analysis where provided','primary_macros':'percent metabolizable energy','phosphorus_basis':'mg per 100 kcal','calorie_basis':'kcal per 100 g','personal_use_only':True},
    {'dataset':'fdsg_dry','title':'Dry Food List - Compiled for FDSG','compiler':'FDSG compilation','basis':'ME carbohydrate percent','primary_macros':'carbohydrate only for most entries'}
  ]
}
foods_js.write_text('window.CATFOOD_DATA = '+json.dumps(all_foods,ensure_ascii=False,separators=(',',':'))+';\nwindow.CATFOOD_META = '+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
print('records',len(all_foods),meta['counts'])
