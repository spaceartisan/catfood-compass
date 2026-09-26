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
assert len(obs)>=24
ids=[o.get('food_id') for o in obs]
assert all(ids) and len(ids)==len(set(ids)), 'manufacturer observation food_id values must be unique'
assert set(ids)<=food_ids, f'Unknown food IDs: {sorted(set(ids)-food_ids)}'

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
            assert value>=0, (o.get('food_id'),group,key,value)

js=(DATA/'manufacturer_nutrition.js').read_text(encoding='utf-8').strip()
wrapper='window.CATFOOD_MANUFACTURER_NUTRITION = '
assert js.startswith(wrapper) and js.endswith(';')
assert json.loads(js[len(wrapper):-1])==bundle

# Basis guardrails: current manufacturer observations are a display/provenance layer.
app=(ROOT/'app.js').read_text(encoding='utf-8')
assert 'manufacturerNutritionFor' in app and 'manufacturerNutritionHtml' in app
assert 'does <strong>not</strong> overwrite' in app
assert 'manufacturerNutritionFor(f)' not in app[app.index('function filterFoods'):app.index('function renderSuggestions')], 'Manufacturer layer must not silently drive filters'

print(f"PASS: {len(obs)} exact manufacturer observations across {len(bundle['brand_sources'])} researched source families; existing source records remain separate")
