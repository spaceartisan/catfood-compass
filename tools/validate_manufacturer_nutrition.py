#!/usr/bin/env python3
"""Validate additive current-manufacturer nutrition observations."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'

foods_js=(DATA/'foods.js').read_text(encoding='utf-8')
prefix='window.CATFOOD_DATA = '
start=foods_js.index(prefix)+len(prefix)
end=foods_js.index(';\nwindow.CATFOOD_META',start)
foods=json.loads(foods_js[start:end])
food_ids={r['id'] for r in foods}

bundle=json.loads((DATA/'manufacturer_nutrition.json').read_text(encoding='utf-8'))
assert bundle.get('schema_version')==1
assert bundle.get('policy')
assert len(bundle.get('brand_sources') or [])>=13
obs=bundle.get('observations') or []
assert len(obs)>=82
ids=[o.get('food_id') for o in obs]
assert all(ids) and len(ids)==len(set(ids)), 'manufacturer observation food_id values must be unique'
assert set(ids)<=food_ids, f'Unknown food IDs: {sorted(set(ids)-food_ids)}'
assert sum(1 for o in obs if str(o.get('source_type','')).startswith('manufacturer_typical_analysis') and 'ZIWI' in str(o.get('current_product_name','')).upper()) >= 15, 'ZIWI enrichment missing'
weruva_wx_ids={'fdsgw-p70r06','fdsgw-p70r07','fdsgw-p70r08','fdsgw-p70r09','fdsgw-p70r10'}
assert weruva_wx_ids <= set(ids), 'Weruva WX enrichment missing'
assert bundle.get('research_summary',{}).get('fromm_exact_matches')==12, 'Fromm enrichment count mismatch'
assert bundle.get('research_summary',{}).get('farmina_exact_matches')==3, 'Farmina enrichment count mismatch'
assert bundle.get('research_summary',{}).get('honest_kitchen_exact_matches')==8, 'Honest Kitchen enrichment count mismatch'
fromm_ids={'fdsgw-p10r02','fdsgw-p10r03','fdsgw-p10r04','fdsgw-p10r05','fdsgw-p10r08','fdsgw-p11r02','fdsgw-p11r04','fdsgw-p11r05','fdsgw-p11r06','fdsgw-p11r07','fdsgw-p11r08','fdsgw-p10r11'}
farmina_ids={'fdsgw-p07r07','fdsgw-p07r08','fdsgw-p07r09'}
honest_ids={'fdsgw-p12r07','fdsgw-p12r08','fdsgw-p12r09','fdsgw-p12r10','fdsgw-p12r11','fdsgw-p12r12','fdsgw-p13r01','fdsgw-p13r02'}
assert fromm_ids <= set(ids), 'Fromm enrichment missing'
assert farmina_ids <= set(ids), 'Farmina enrichment missing'
assert honest_ids <= set(ids), 'Honest Kitchen enrichment missing'

fancy_classic_ids={'p14r04','p14r05','p14r06','p14r07','p14r08','p14r09','p14r10','p14r11','p14r12','p14r13','p14r14','p14r15','fdsgw-p05r11','fdsgw-p05r12','fdsgw-p06r01'}
assert fancy_classic_ids <= set(ids), 'Fancy Feast Classic Paté enrichment missing'
assert bundle.get('research_summary',{}).get('fancy_feast_classic_pate_current_products')==12, 'Fancy Feast current-product count mismatch'
assert bundle.get('research_summary',{}).get('fancy_feast_classic_pate_linked_source_records')==15, 'Fancy Feast linked source-row count mismatch'
ff=[o for o in obs if o.get('food_id') in fancy_classic_ids]
assert all((o.get('energy') or {}).get('kcal_per_3oz_can') for o in ff), 'Fancy Feast current calorie data missing'
assert sum(1 for o in ff if o.get('guaranteed_analysis'))>=9, 'Fancy Feast GA coverage unexpectedly low'

numeric_groups={'guaranteed_analysis','typical_percent','as_fed_pct','dry_matter_pct','per_100_kcal','percent_ME','energy'}
for o in obs:
    assert o.get('match_status')=='verified_exact_product', o.get('food_id')
    assert str(o.get('source_url') or '').startswith('https://'), o.get('food_id')
    assert o.get('current_product_name') and o.get('source_type') and o.get('retrieved_on'), o.get('food_id')
    assert numeric_groups.intersection(o), f'No nutrient group: {o.get("food_id")}'
    for group in numeric_groups:
        for key,value in (o.get(group) or {}).items():
            if value is None: continue
            assert isinstance(value,(int,float)), (o.get('food_id'),group,key,value)
            if value < 0:
                allowed_negative = (
                    key == 'carbohydrate' and
                    group in {'as_fed_pct','dry_matter_pct','percent_ME'} and
                    o.get('source_anomaly') is True and
                    bool(o.get('anomaly_notes'))
                )
                assert allowed_negative, (o.get('food_id'),group,key,value)

js=(DATA/'manufacturer_nutrition.js').read_text(encoding='utf-8').strip()
wrapper='window.CATFOOD_MANUFACTURER_NUTRITION = '
assert js.startswith(wrapper) and js.endswith(';')
assert json.loads(js[len(wrapper):-1])==bundle

# Basis guardrails: current manufacturer observations are a display/provenance layer.
app=(ROOT/'app.js').read_text(encoding='utf-8')
assert 'manufacturerNutritionFor' in app and 'manufacturerNutritionHtml' in app
assert 'does <strong>not</strong> overwrite' in app
assert 'manufacturerNutritionFor(f)' not in app[app.index('function filterFoods'):app.index('function renderSuggestions')], 'Manufacturer layer must not silently drive filters'

print(f"PASS: {len(obs)} exact manufacturer observations; v0.3.8 Fancy Feast Classic Paté enrichment and basis guardrails validated")
