#!/usr/bin/env python3
"""Validate CatFood Compass catalog-matched FDA recall data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
sys.path.insert(0, str(ROOT / 'tools'))

from build_recall_brands import build_rules
from update_recalls import (
    has_feline_context,
    match_brand_rules,
    match_curated_record,
)

bundle = json.loads((DATA / 'recalls.json').read_text(encoding='utf-8'))
curated = json.loads((DATA / 'recalls_curated.json').read_text(encoding='utf-8'))
brands = json.loads((DATA / 'recall_brands.json').read_text(encoding='utf-8'))

assert bundle.get('schema_version') == 2
assert bundle.get('snapshot_label')
assert bundle.get('catalog_filter', {}).get('strategy') == 'catalog_brand_whitelist'
assert bundle.get('openfda', {}).get('endpoint') == 'https://api.fda.gov/food/enforcement.json'
assert bundle.get('openfda', {}).get('coverage') == '2004-present'
assert bundle.get('openfda', {}).get('update_frequency') == 'weekly'
assert len(bundle.get('source_notes', [])) >= 4

assert brands.get('schema_version') == 1
assert brands.get('strategy') == 'catalog_brand_whitelist'
assert brands.get('source_brand_count') == 107
assert brands.get('rule_count') > 0
rules = brands.get('rules') or []

# The checked-in whitelist must exactly match what the current food catalog generates.
rebuilt = build_rules()
assert rebuilt == brands, 'recall_brands.json is stale; run tools/build_recall_brands.py'
assert bundle['catalog_filter']['source_brand_hash'] == brands['source_brand_hash']
assert bundle['catalog_filter']['brand_rule_count'] == brands['rule_count']
assert bundle['catalog_filter']['source_brand_count'] == brands['source_brand_count']

records = bundle.get('records') or []
ids = [r.get('id') for r in records]
assert all(ids) and len(ids) == len(set(ids)), 'Duplicate or missing recall IDs'

valid_types = {'recall', 'advisory', 'enforcement'}
known_rule_ids = {r['id'] for r in rules}
for r in records:
    assert r.get('record_type') in valid_types, (r.get('id'), r.get('record_type'))
    assert r.get('source') and r.get('source_url', '').startswith('https://www.fda.gov/'), r.get('id')
    assert r.get('product_description') and r.get('reason'), r.get('id')
    assert isinstance(r.get('brand_names', []), list), r.get('id')
    assert r.get('catalog_match') == 'brand_whitelist', r.get('id')
    ids_for_record = set(r.get('catalog_brand_ids') or [])
    assert ids_for_record and ids_for_record <= known_rule_ids, f"Invalid catalog brand IDs: {r.get('id')}"
    if r.get('api_record'):
        assert has_feline_context(r.get('product_description')), f"Missing feline context: {r.get('id')}"
        matches = match_brand_rules(r.get('product_description'), rules)
        assert ids_for_record <= {m['id'] for m in matches}, f"Machine record no longer matches whitelist: {r.get('id')}"

# Real false positives from the first implementation must never match a catalog brand.
false_positive_descriptions = [
    "Winfield's chocolate bar, Cat shape, net wt 8 oz",
    "Intelligentsia Black Cat Espresso Ice Cream Pint",
    "Purity Organic Mango Tommy Atkins CAT 1, Size 10",
    "BIO-CAT enzyme blend, bulk ingredient",
    "Fat Cat Purry-Purry Sauce, 5 oz",
    "Dave's Coffee Falcon Iced Coffee, Wizard Cat roast, 12 oz",
]
for desc in false_positive_descriptions:
    assert not match_brand_rules(desc, rules), f"False-positive catalog brand match: {desc}"

# Known catalog brands must match through canonical and manufacturer-style aliases.
expected = {
    "Fancy Feast Classic Chicken Feast Cat Food": 'fancy-feast',
    "Purina Fancy Feast Gourmet Cat Food": 'fancy-feast',
    "Tiki Cat After Dark Cat Food": 'tiki-cat',
    "Dave's Pet Food Chicken Formula for Cats": 'dave-s-pet-food',
    "Blue Buffalo Wilderness Cat Food": 'blue-buffalo',
    "Hill's Science Diet Adult Cat Food": 'hill-s',
}
for desc, rule_id in expected.items():
    hits = {m['id'] for m in match_brand_rules(desc, rules)}
    assert rule_id in hits, f"Expected brand rule {rule_id} not found for {desc}"
    assert has_feline_context(desc), f"Expected feline context missing for {desc}"

# Curated inputs outside the catalog are intentionally not surfaced.
curated_records = curated.get('records') or []
curated_kept = [r for r in curated_records if match_curated_record(r, rules)]
assert bundle['catalog_filter']['curated_input_count'] == len(curated_records)
assert bundle['catalog_filter']['curated_catalog_matches'] == len(curated_kept)
for r in curated_kept:
    assert r['id'] in set(ids), f"Catalog-matched curated record missing: {r['id']}"

# JavaScript wrappers must contain exactly the same payloads as JSON.
for json_name, js_name, prefix in [
    ('recalls.json', 'recalls.js', 'window.CATFOOD_RECALLS = '),
    ('recall_brands.json', 'recall_brands.js', 'window.CATFOOD_RECALL_BRANDS = '),
]:
    payload = json.loads((DATA / json_name).read_text(encoding='utf-8'))
    js = (DATA / js_name).read_text(encoding='utf-8').strip()
    assert js.startswith(prefix) and js.endswith(';')
    wrapped = json.loads(js[len(prefix):-1])
    assert wrapped == payload, f'{js_name} and {json_name} differ'

# The updater/workflow must remain static-site friendly and rebuild the whitelist.
updater = (ROOT / 'tools' / 'update_recalls.py').read_text(encoding='utf-8')
workflow = (ROOT / '.github' / 'workflows' / 'update-recalls.yml').read_text(encoding='utf-8')
assert 'urllib.request' in updater and 'requests' not in updater
assert '--offline' in updater
assert 'schedule:' in workflow and 'workflow_dispatch:' in workflow
assert 'python tools/build_recall_brands.py' in workflow
assert 'python tools/update_recalls.py' in workflow
assert 'python tools/validate_recalls.py' in workflow
assert 'git push' in workflow

sw = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
assert 'recall_brands' in sw and 'recalls' in sw
assert 'fetch(e.request).then' in sw and 'caches.match(e.request)' in sw
assert 'existing recall snapshot was left unchanged' in updater
assert 'meaningless daily Git commit' in updater

print(
    f"PASS: {brands['rule_count']} catalog brand rules cover "
    f"{brands['source_brand_count']} source brand labels"
)
print(
    f"PASS: {len(records)} catalog-matched FDA recall/advisory records validated; "
    f"{len(curated_kept)} of {len(curated_records)} curated inputs currently match the catalog"
)
print('PASS: recall refresh is catalog-whitelisted, failure-safe, and network-first cached')
