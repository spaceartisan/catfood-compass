#!/usr/bin/env python3
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(stem): return json.loads((ROOT/'data'/f'{stem}.json').read_text(encoding='utf-8'))

def assert_db(stem, brand, min_products, expected_sources):
    d=load(stem); prods=d['current_products']; links=d['reconciliation']; sources=d['source_records']
    assert len(prods)>=min_products,(stem,len(prods))
    assert len(sources)==expected_sources,(stem,len(sources))
    ids=[p['id'] for p in prods]; assert len(ids)==len(set(ids)),f'{stem}: duplicate product ids'
    pids=set(ids); sids={s['source_id'] for s in sources}
    assert len(links)==len(sources)
    for l in links:
        assert l['source_id'] in sids
        if l.get('current_product_id'): assert l['current_product_id'] in pids
        if str(l.get('status','')).startswith('verified_'): assert l.get('current_product_id')
    assert d['meta']['preservation_rule'].startswith('Existing Pierson/FDSG records remain immutable')
    return d

f=assert_db('fancy_feast','Fancy Feast',130,108)
r=assert_db('friskies','Friskies',100,74)

# Regression identities.
def link_for(d,sid):
    l=next(x for x in d['reconciliation'] if x['source_id']==sid)
    p=next((x for x in d['current_products'] if x['id']==l.get('current_product_id')),None)
    return l,p
l,p=link_for(f,'p14r04'); assert l['status'].startswith('verified_') and 'Classic Paté Chicken Feast' in p['current_name']
l,p=link_for(f,'p16r07'); assert l['status'].startswith('verified_') and 'Gravy Lovers Beef Feast' in p['current_name']
l,p=link_for(r,'p20r19'); assert l['status'].startswith('verified_') and 'Turkey & Giblets' in p['current_name']
l,p=link_for(r,'p21r13'); assert l['status'].startswith('verified_') and 'Chicken & Salmon' in p['current_name']
# Historical Bacon/Cheese Tasty Treasures are not silently equated to current differently-named products.
for sid in ['p22r06','p22r07','p22r08','p22r12','p22r13']:
    l,_=link_for(r,sid); assert not l['status'].startswith('verified_'),(sid,l)
# Complement is explicitly not a meal.
soups=[p for p in r['current_products'] if "Lil' Soups" in p['current_name']]
assert len(soups)==1 and soups[0]['role']=='complement'
# Source record database itself stays at 2,024 rows.
txt=(ROOT/'data'/'foods.js').read_text(encoding='utf-8')
m=re.search(r'window\.CATFOOD_DATA\s*=\s*(\[.*?\]);\s*window\.CATFOOD_META',txt,re.S)
foods=json.loads(m.group(1)); assert len(foods)==2024
print('PASS: Fancy Feast and Friskies catalog DB structure, conservative reconciliation, and 2,024 source records validated')
print('Fancy Feast:',f['meta']['catalog_entry_count'],'catalog entries,',f['meta']['reconciliation_counts'])
print('Friskies:',r['meta']['catalog_entry_count'],'catalog entries,',r['meta']['reconciliation_counts'])
