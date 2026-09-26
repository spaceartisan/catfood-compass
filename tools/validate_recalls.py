#!/usr/bin/env python3
"""Validate CatFood Compass recall/advisory bundle structure and provenance."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'

bundle=json.loads((DATA/'recalls.json').read_text(encoding='utf-8'))
curated=json.loads((DATA/'recalls_curated.json').read_text(encoding='utf-8'))
assert bundle.get('schema_version')==1
assert isinstance(bundle.get('generated_at'),str) and bundle['generated_at']
assert bundle.get('snapshot_label')
assert bundle.get('openfda',{}).get('endpoint')=='https://api.fda.gov/food/enforcement.json'
assert bundle.get('openfda',{}).get('coverage')=='2004-present'
assert bundle.get('openfda',{}).get('update_frequency')=='weekly'
assert len(bundle.get('source_notes',[]))>=3

records=bundle.get('records') or []
curated_records=curated.get('records') or []
assert len(records)>=len(curated_records)>=6
ids=[r.get('id') for r in records]
assert all(ids) and len(ids)==len(set(ids)), 'Duplicate or missing recall IDs'
valid_types={'recall','advisory','enforcement'}
for r in records:
    assert r.get('record_type') in valid_types, (r.get('id'),r.get('record_type'))
    assert r.get('source') and r.get('source_url','').startswith('https://www.fda.gov/'), r.get('id')
    assert r.get('product_description') and r.get('reason'), r.get('id')
    assert isinstance(r.get('brand_names',[]),list) and isinstance(r.get('species',[]),list), r.get('id')
    assert 'cat' in r.get('species',[]), f"Non-feline record in feline bundle: {r.get('id')}"

# Curated records are never lost when rebuilding the generated bundle.
bundle_ids=set(ids)
for r in curated_records:
    assert r['id'] in bundle_ids, f"Curated record missing from bundle: {r['id']}"

# JavaScript wrapper must contain the same generated payload.
js=(DATA/'recalls.js').read_text(encoding='utf-8').strip()
prefix='window.CATFOOD_RECALLS = '
assert js.startswith(prefix) and js.endswith(';')
wrapped=json.loads(js[len(prefix):-1])
assert wrapped==bundle, 'recalls.js and recalls.json differ'

# The updater and workflow must remain static-site friendly.
updater=(ROOT/'tools'/'update_recalls.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'update-recalls.yml').read_text(encoding='utf-8')
assert 'urllib.request' in updater and 'requests' not in updater, 'Updater should require no third-party HTTP package'
assert '--offline' in updater
assert 'schedule:' in workflow and 'workflow_dispatch:' in workflow
assert 'python tools/update_recalls.py' in workflow
assert 'git push' in workflow

print(f"PASS: {len(records)} feline-relevant FDA recall/advisory records validated; {len(curated_records)} curated offline records preserved")

sw=(ROOT/'service-worker.js').read_text(encoding='utf-8')
assert 'isRecallSnapshot' in sw and 'fetch(e.request).then' in sw and 'caches.match(e.request)' in sw, 'Recall snapshot must be network-first with cached offline fallback'
assert 'existing recall snapshot was left unchanged' in updater, 'Updater must preserve prior snapshot on live refresh failure'
assert 'meaningless daily Git commit' in updater, 'Updater must suppress timestamp-only scheduled commits'
print('PASS: recall refresh is failure-safe and service worker uses network-first recall snapshot caching')
