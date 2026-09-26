#!/usr/bin/env python3
"""Refresh CatFood Compass FDA recall data for brands in its food catalog.

CatFood Compass is a static GitHub Pages app. A scheduled GitHub Action runs
this script, queries FDA Food Enforcement data through openFDA, and writes a
bundled JSON/JS snapshot.

Machine-imported records are intentionally narrow: a record must (1) contain a
feline context term and (2) match one or more explicit brand aliases generated
from the CatFood Compass nutrition catalog. This prevents lexical false
positives such as cat-shaped chocolate or "Black Cat" coffee and also keeps the
recall tab focused on brands represented in the app.

No third-party Python packages are required.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OPENFDA = "https://api.fda.gov/food/enforcement.json"
FDA_RECALLS = "https://www.fda.gov/animal-veterinary/safety-health/recalls-withdrawals"
QUERY_TERMS = ["cat", "feline", "kitten", "kitty"]
UA = "CatFood-Compass-recall-updater/0.3.5 (+GitHub Pages data refresh)"


def read_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def normalize(value: str | None) -> str:
    s = (value or "").lower().replace("&", " and ").replace("’", "'")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_brand_rules() -> dict:
    payload = read_json(DATA / "recall_brands.json", {})
    if payload.get("strategy") != "catalog_brand_whitelist" or not payload.get("rules"):
        raise RuntimeError(
            "data/recall_brands.json is missing or invalid; run tools/build_recall_brands.py first"
        )
    return payload


def phrase_in_text(normalized_text: str, normalized_phrase: str) -> bool:
    if not normalized_text or not normalized_phrase:
        return False
    return f" {normalized_phrase} " in f" {normalized_text} "


def match_brand_rules(text: str | None, rules: list[dict]) -> list[dict]:
    """Return catalog rules explicitly matched in an FDA product description."""
    n = normalize(text)
    matches = []
    for rule in rules:
        aliases = rule.get("normalized_aliases") or [normalize(a) for a in rule.get("aliases", [])]
        hit = next((alias for alias in aliases if phrase_in_text(n, alias)), None)
        if hit:
            matches.append({
                "id": rule.get("id"),
                "canonical": rule.get("canonical"),
                "alias": hit,
            })
    return matches


def match_curated_record(record: dict, rules: list[dict]) -> list[dict]:
    """Match a manually curated record to the same catalog-brand whitelist."""
    # Prefer the explicitly curated brand names; fall back to the product text.
    joined = " ".join(str(x) for x in (record.get("brand_names") or []) if x)
    matches = match_brand_rules(joined, rules)
    if matches:
        return matches
    return match_brand_rules(record.get("product_description"), rules)


def has_feline_context(value: str | None) -> bool:
    n = normalize(value)
    return bool(re.search(r"\b(cat|cats|feline|felines|kitten|kittens|kitty|kitties)\b", n))


def fetch_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def fetch_query(term: str, max_records: int = 5000) -> list[dict]:
    """Fetch practical openFDA matches for one feline term."""
    out: list[dict] = []
    limit = 100
    skip = 0
    search = f'product_description:"{term}"'
    while skip < max_records:
        params = urllib.parse.urlencode({
            "search": search,
            "sort": "report_date:desc",
            "limit": limit,
            "skip": skip,
        })
        url = f"{OPENFDA}?{params}"
        try:
            payload = fetch_json(url)
        except urllib.error.HTTPError as e:
            # openFDA returns 404 when a query has no results.
            if e.code == 404:
                break
            raise
        rows = payload.get("results") or []
        if not rows:
            break
        out.extend(rows)
        if len(rows) < limit:
            break
        skip += len(rows)
        time.sleep(0.15)
    return out


def parse_yyyymmdd(value: str | None) -> str | None:
    if not value:
        return None
    s = re.sub(r"\D", "", str(value))
    if len(s) != 8:
        return None
    try:
        d = dt.datetime.strptime(s, "%Y%m%d").date()
        return d.isoformat()
    except ValueError:
        return None


def classify_species(text: str) -> list[str]:
    n = normalize(text)
    species = []
    if re.search(r"\b(cat|cats|feline|felines|kitten|kittens|kitty|kitties)\b", n):
        species.append("cat")
    if re.search(r"\b(dog|dogs|canine|canines|puppy|puppies)\b", n):
        species.append("dog")
    return species


def apply_catalog_match(record: dict, matches: list[dict]) -> dict:
    out = dict(record)
    out["brand_names"] = sorted(
        {m.get("canonical") for m in matches if m.get("canonical")}, key=str.casefold
    )
    out["catalog_brand_ids"] = sorted({m.get("id") for m in matches if m.get("id")})
    out["brand_match_aliases"] = sorted({m.get("alias") for m in matches if m.get("alias")})
    out["catalog_match"] = "brand_whitelist"
    return out


def enforcement_to_record(row: dict, matches: list[dict]) -> dict:
    recall_no = str(row.get("recall_number") or "").strip()
    event_id = str(row.get("event_id") or "").strip()
    product = str(row.get("product_description") or "").strip()
    rid_seed = recall_no or event_id or (product + str(row.get("report_date") or ""))
    rid = "openfda-" + re.sub(r"[^a-z0-9]+", "-", rid_seed.lower()).strip("-")[:80]
    if rid == "openfda-":
        rid = "openfda-" + hashlib.sha1(json.dumps(row, sort_keys=True).encode()).hexdigest()[:14]
    status = str(row.get("status") or "").strip() or "FDA enforcement record"
    term = parse_yyyymmdd(row.get("termination_date"))
    if term:
        status_label = f"Terminated {term}"
    else:
        status_label = status + " (openFDA status is not a live lifecycle tracker)"

    record = {
        "id": rid,
        "record_type": "enforcement",
        "source": "FDA Recall Enterprise System via openFDA",
        "source_url": FDA_RECALLS,
        "api_record": True,
        "announcement_date": parse_yyyymmdd(row.get("recall_initiation_date")),
        "report_date": parse_yyyymmdd(row.get("report_date")),
        "termination_date": term,
        "brand_names": [],
        "recalling_firm": row.get("recalling_firm"),
        "species": classify_species(product),
        "product_description": product,
        "reason": row.get("reason_for_recall"),
        "status_label": status_label,
        "classification": row.get("classification"),
        "recall_number": recall_no or None,
        "event_id": event_id or None,
        "lot_codes": [str(row.get("code_info"))] if row.get("code_info") else [],
        "upcs": [],
        "best_by": [],
        "distribution_pattern": row.get("distribution_pattern"),
        "product_quantity": row.get("product_quantity"),
        "voluntary_mandated": row.get("voluntary_mandated"),
        "consumer_action": None,
        "notes": "Machine-normalized enforcement record matched to a CatFood Compass catalog brand. Verify lot/package details against FDA before acting.",
    }
    return apply_catalog_match(record, matches)


def dedupe(records: list[dict]) -> list[dict]:
    by_key: dict[tuple, dict] = {}
    for r in records:
        key = (
            normalize(r.get("recall_number")),
            normalize(r.get("product_description")),
            r.get("report_date") or r.get("announcement_date") or "",
        )
        # Curated records win if a machine record overlaps the same product/date.
        prior = by_key.get(key)
        if prior is None or (prior.get("api_record") and not r.get("api_record")):
            by_key[key] = r
    return sorted(
        by_key.values(),
        key=lambda r: (r.get("report_date") or r.get("announcement_date") or "", r.get("product_description") or ""),
        reverse=True,
    )


def build(live: bool = True) -> dict:
    brand_payload = load_brand_rules()
    rules = brand_payload.get("rules") or []
    curated_all = read_json(DATA / "recalls_curated.json", {"records": []}).get("records") or []

    curated_kept = []
    for record in curated_all:
        matches = match_curated_record(record, rules)
        if matches:
            curated_kept.append(apply_catalog_match(record, matches))

    records = list(curated_kept)
    live_ok = False
    error = None
    raw_count = 0
    live_catalog_matches = 0

    if live:
        try:
            raw = []
            seen = set()
            for term in QUERY_TERMS:
                for row in fetch_query(term):
                    key = row.get("recall_number") or json.dumps(row, sort_keys=True)
                    if key in seen:
                        continue
                    seen.add(key)
                    raw.append(row)
            raw_count = len(raw)

            for row in raw:
                product = row.get("product_description")
                if not has_feline_context(product):
                    continue
                matches = match_brand_rules(product, rules)
                if not matches:
                    continue
                records.append(enforcement_to_record(row, matches))
                live_catalog_matches += 1

            print(
                f"Catalog-brand filter retained {live_catalog_matches} of {raw_count} "
                "deduplicated feline-term openFDA records."
            )
            live_ok = True
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            print(f"WARNING: live FDA refresh failed: {error}", file=sys.stderr)

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 2,
        "generated_at": now,
        "snapshot_label": "FDA recalls matched to CatFood Compass catalog brands",
        "source_notes": [
            "CatFood Compass only retains machine-imported FDA enforcement records that match a brand represented in its nutrition catalog.",
            "Machine records must also contain a feline context term; unrelated human foods and dog-only products are excluded.",
            "Curated FDA animal/veterinary notices are subjected to the same catalog-brand whitelist before appearing in the app.",
            "A record not appearing here is not proof that a product has never been recalled; this is intentionally not a complete FDA animal-recall index.",
            "openFDA states that enforcement status should not be treated as a live recall-lifecycle tracker.",
        ],
        "catalog_filter": {
            "strategy": "catalog_brand_whitelist",
            "brand_rule_count": brand_payload.get("rule_count"),
            "source_brand_count": brand_payload.get("source_brand_count"),
            "source_brand_hash": brand_payload.get("source_brand_hash"),
            "curated_input_count": len(curated_all),
            "curated_catalog_matches": len(curated_kept),
            "live_raw_feline_term_records": raw_count if live_ok else None,
            "live_catalog_matches": live_catalog_matches if live_ok else None,
        },
        "openfda": {
            "endpoint": OPENFDA,
            "coverage": "2004-present",
            "update_frequency": "weekly",
            "last_live_refresh": now if live_ok else None,
            "refresh_error": error,
        },
        "records": dedupe(records),
    }


def write_outputs(payload: dict) -> None:
    (DATA / "recalls.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (DATA / "recalls.js").write_text(f"window.CATFOOD_RECALLS = {compact};\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="Rebuild from curated records only; do not contact openFDA")
    args = ap.parse_args()
    existing = read_json(DATA / "recalls.json", {})
    payload = build(live=not args.offline)

    # Never replace a previously good generated snapshot with a curated-only
    # fallback because of a transient FDA/network failure. Let CI report the
    # failure and keep the last known-good static snapshot intact.
    if not args.offline and payload.get("openfda", {}).get("refresh_error"):
        print("ERROR: FDA refresh failed; existing recall snapshot was left unchanged.", file=sys.stderr)
        return 2

    # A scheduled check should not create a meaningless daily Git commit just
    # because the clock changed. If the normalized record set and catalog rule
    # hash are unchanged, preserve the prior successful refresh timestamps.
    same_filter = (
        existing.get("catalog_filter", {}).get("source_brand_hash")
        == payload.get("catalog_filter", {}).get("source_brand_hash")
    )
    if (
        not args.offline
        and existing
        and existing.get("records") == payload.get("records")
        and same_filter
        and existing.get("openfda", {}).get("last_live_refresh")
    ):
        payload["generated_at"] = existing.get("generated_at")
        payload["openfda"]["last_live_refresh"] = existing["openfda"].get("last_live_refresh")

    write_outputs(payload)
    print(f"Wrote {len(payload['records'])} catalog-matched recall/advisory records to data/recalls.json and data/recalls.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
