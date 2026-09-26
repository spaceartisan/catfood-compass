#!/usr/bin/env python3
"""Refresh CatFood Compass feline-relevant FDA recall data.

This keeps the GitHub Pages app static while allowing a scheduled GitHub Action
to refresh a bundled JSON/JS snapshot. It supplements a small curated set of
FDA recall/advisory records with FDA Food Enforcement (openFDA) records whose
product descriptions are cat/feline/kitten relevant.

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
QUERY_TERMS = ["cat", "feline", "kitten"]
UA = "CatFood-Compass-recall-updater/0.3.2 (+GitHub Pages data refresh)"


def read_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def normalize(value: str | None) -> str:
    s = (value or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_known_brands() -> list[str]:
    """Read brands from foods.js without executing JavaScript."""
    path = DATA / "foods.js"
    text = path.read_text(encoding="utf-8")
    prefix = "window.CATFOOD_DATA = "
    start = text.find(prefix)
    if start < 0:
        return []
    start += len(prefix)
    end = text.find(";\nwindow.CATFOOD_META", start)
    if end < 0:
        return []
    rows = json.loads(text[start:end])
    brands = sorted({str(r.get("brand") or "").strip() for r in rows if r.get("brand")})
    # Avoid tiny/generic names that can create false substring matches.
    return [b for b in brands if len(normalize(b)) >= 4]


def fetch_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def fetch_query(term: str, max_records: int = 5000) -> list[dict]:
    """Fetch all practical matches for one feline term from openFDA."""
    out: list[dict] = []
    limit = 100
    skip = 0
    # Query syntax intentionally kept simple; terms are run separately and deduped.
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
    if re.search(r"\b(cat|cats|feline|felines|kitten|kittens)\b", n):
        species.append("cat")
    if re.search(r"\b(dog|dogs|canine|canines|puppy|puppies)\b", n):
        species.append("dog")
    return species or ["cat"]  # Query itself was feline-oriented.


def match_known_brands(product_description: str, known_brands: list[str]) -> list[str]:
    n = f" {normalize(product_description)} "
    matched = []
    for brand in known_brands:
        bn = normalize(brand)
        if bn and f" {bn} " in n:
            matched.append(brand)
    return sorted(set(matched), key=str.lower)


def enforcement_to_record(row: dict, known_brands: list[str]) -> dict:
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
    return {
        "id": rid,
        "record_type": "enforcement",
        "source": "FDA Recall Enterprise System via openFDA",
        "source_url": FDA_RECALLS,
        "api_record": True,
        "announcement_date": parse_yyyymmdd(row.get("recall_initiation_date")),
        "report_date": parse_yyyymmdd(row.get("report_date")),
        "termination_date": term,
        "brand_names": match_known_brands(product, known_brands),
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
        "notes": "Machine-normalized enforcement record. Verify lot/package details against FDA before acting."
    }


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
    curated = read_json(DATA / "recalls_curated.json", {"records": []}).get("records") or []
    records = list(curated)
    live_ok = False
    error = None
    if live:
        try:
            known_brands = load_known_brands()
            raw = []
            seen = set()
            for term in QUERY_TERMS:
                for row in fetch_query(term):
                    key = row.get("recall_number") or json.dumps(row, sort_keys=True)
                    if key in seen:
                        continue
                    seen.add(key)
                    raw.append(row)
            records.extend(enforcement_to_record(r, known_brands) for r in raw)
            live_ok = True
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            print(f"WARNING: live FDA refresh failed: {error}", file=sys.stderr)

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "generated_at": now,
        "snapshot_label": "Bundled FDA feline-relevant recall/advisory snapshot",
        "source_notes": [
            "Curated FDA animal/veterinary recall announcements and advisories are bundled for offline use.",
            "The scheduled updater supplements this file with feline-relevant FDA Food Enforcement records from openFDA.",
            "A record not appearing here is not proof that a product has never been recalled.",
            "openFDA states that enforcement status should not be treated as a live recall-lifecycle tracker."
        ],
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
    # because the clock changed. If the normalized record set is unchanged and
    # this repository already has a successful live snapshot, preserve its
    # snapshot timestamps so git diff remains clean.
    if (not args.offline and existing and
            existing.get("records") == payload.get("records") and
            existing.get("openfda", {}).get("last_live_refresh")):
        payload["generated_at"] = existing.get("generated_at")
        payload["openfda"]["last_live_refresh"] = existing["openfda"].get("last_live_refresh")

    write_outputs(payload)
    print(f"Wrote {len(payload['records'])} recall/advisory records to data/recalls.json and data/recalls.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
