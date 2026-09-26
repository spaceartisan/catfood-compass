#!/usr/bin/env python3
"""Build the catalog-brand whitelist used by the FDA recall layer.

The recall updater intentionally does not try to discover every feline recall in
openFDA.  CatFood Compass only surfaces machine-imported enforcement records
that can be tied to a brand already present in the app's food catalog.

This script reads the brand labels already present in data/foods.js, folds known
historical/current naming variants into a stable canonical rule, and emits the
same rules as JSON (for Python/GitHub Actions) and JavaScript (for the static
browser app).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def normalize(value: str | None) -> str:
    s = (value or "").lower().replace("&", " and ")
    s = s.replace("’", "'")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(value)).strip("-") or "brand"


def read_food_brands() -> list[str]:
    text = (DATA / "foods.js").read_text(encoding="utf-8")
    prefix = "window.CATFOOD_DATA = "
    start = text.find(prefix)
    if start < 0:
        raise RuntimeError("Could not locate CATFOOD_DATA in data/foods.js")
    start += len(prefix)
    end = text.find(";\nwindow.CATFOOD_META", start)
    if end < 0:
        raise RuntimeError("Could not locate CATFOOD_META boundary in data/foods.js")
    rows = json.loads(text[start:end])
    return sorted({str(r.get("brand") or "").strip() for r in rows if r.get("brand")}, key=lambda s: (s.casefold(), s))


# Map source labels that are really the same brand/family to one rule key.
GROUP_KEY = {
    "fancy feast purina": "fancy feast",
    "friskies purina": "friskies",
    "ziwipeak": "ziwi peak",
    "science diet": "hill s",
    "nature s variety": "instinct",
    "raynenutriti on rxtheradiet": "rayne nutrition",
    "blue": "blue buffalo",
    "beyond": "purina beyond",
    "pro plan": "purina pro plan",
    "nutrish": "rachael ray nutrish",
    "organix": "castor and pollux organix",
    "go": "go solutions",
}


# Canonical display names for rules where the source chart uses an abbreviation,
# legacy name, parenthetical label, or a generic-looking shorthand.
CANONICAL = {
    "blue buffalo": "Blue Buffalo",
    "b f f weruva": "Weruva B.F.F.",
    "castor and pollux organix": "Castor & Pollux Organix",
    "dave s": "Dave's Pet Food",
    "dr elsey s": "Dr. Elsey's",
    "fancy feast": "Fancy Feast",
    "friskies": "Friskies",
    "go solutions": "GO! Solutions",
    "hill s": "Hill's",
    "instinct": "Instinct",
    "purina beyond": "Purina Beyond",
    "purina pro plan": "Purina Pro Plan",
    "rachael ray nutrish": "Rachael Ray Nutrish",
    "rayne nutrition": "Rayne Nutrition",
    "tiki cat": "Tiki Cat",
    "ziwi peak": "Ziwi Peak",
}


# Extra spellings that FDA product descriptions may use.  Matching is done on
# normalized token boundaries, so punctuation/case variants do not need to be
# duplicated here unless the wording itself changes.
EXTRA_ALIASES = {
    "b f f weruva": ["Weruva BFF", "BFF by Weruva", "B.F.F. by Weruva"],
    "blue buffalo": ["Blue Buffalo"],
    "castor and pollux organix": ["Castor & Pollux Organix", "Castor Pollux Organix"],
    "dave s": ["Dave's Pet Food", "Daves Pet Food", "Dave's Naturally Healthy"],
    "dr elsey s": ["Dr. Elsey's", "Dr Elseys"],
    "fancy feast": ["Fancy Feast", "Purina Fancy Feast"],
    "friskies": ["Friskies", "Purina Friskies"],
    "go solutions": ["GO! Solutions", "GO Solutions", "Petcurean GO Solutions"],
    "hill s": ["Hill's", "Hills", "Hill's Science Diet", "Hills Science Diet", "Science Diet"],
    "instinct": ["Instinct", "Nature's Variety", "Natures Variety", "Nature's Variety Instinct"],
    "open farms": ["Open Farm", "Open Farms"],
    "purina beyond": ["Purina Beyond", "Beyond by Purina"],
    "purina pro plan": ["Purina Pro Plan", "Pro Plan"],
    "rachael ray nutrish": ["Rachael Ray Nutrish", "Nutrish"],
    "rayne nutrition": ["Rayne Nutrition", "Rayne Clinical Nutrition"],
    "tiki cat": ["Tiki Cat", "Tiki Pets"],
    "ziwi peak": ["Ziwi Peak", "ZIWI Peak", "ZIWIPEAK"],
}


# Some source labels are too ambiguous to be safe FDA aliases by themselves.
# They still map foods to the rule through source_labels; they simply are not
# used as text matches against FDA product descriptions.
UNSAFE_SOURCE_ALIASES = {
    "blue",       # e.g. Blue Bunny / blue cheese
    "beyond",     # ordinary English word
    "go",         # e.g. Go Raw, LLC
    "dave s",     # e.g. Dave's Coffee
}


def preferred_name(group_key: str, labels: list[str]) -> str:
    if group_key in CANONICAL:
        return CANONICAL[group_key]
    # Prefer a mixed/title-case label over all-caps when one exists.
    ranked = sorted(
        labels,
        key=lambda s: (
            1 if s.isupper() else 0,
            1 if "/" in s else 0,
            len(s),
            s.casefold(),
        ),
    )
    return ranked[0]


def build_rules() -> dict:
    source_labels = read_food_brands()
    grouped: dict[str, list[str]] = {}
    for label in source_labels:
        nk = normalize(label)
        key = GROUP_KEY.get(nk, nk)
        grouped.setdefault(key, []).append(label)

    rules = []
    for key in sorted(grouped):
        labels = sorted(set(grouped[key]), key=lambda s: (s.casefold(), s))
        canonical = preferred_name(key, labels)
        aliases: list[str] = []

        # Canonical wording is always a valid alias.
        aliases.append(canonical)

        # Source labels are usually the best recall aliases unless explicitly
        # blocked as too generic/ambiguous.
        for label in labels:
            if normalize(label) not in UNSAFE_SOURCE_ALIASES:
                aliases.append(label)

        aliases.extend(EXTRA_ALIASES.get(key, []))

        # Dedupe by normalized spelling while preserving useful display text.
        dedup: dict[str, str] = {}
        for alias in aliases:
            n = normalize(alias)
            if n and len(n) >= 3:
                dedup.setdefault(n, alias)

        rules.append({
            "id": slug(canonical),
            "canonical": canonical,
            "source_labels": labels,
            "aliases": list(dedup.values()),
            "normalized_aliases": sorted(dedup.keys()),
        })

    source_hash = hashlib.sha256(
        json.dumps(source_labels, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]

    return {
        "schema_version": 1,
        "strategy": "catalog_brand_whitelist",
        "source": "data/foods.js",
        "source_brand_count": len(source_labels),
        "rule_count": len(rules),
        "source_brand_hash": source_hash,
        "notes": [
            "Only machine-imported FDA enforcement records matching one or more of these catalog brand rules are retained.",
            "Aliases are matched on normalized token boundaries; ambiguous source shorthands such as BLUE, GO, and DAVE'S are not used as bare FDA aliases.",
            "This whitelist limits CatFood Compass to recalls relevant to brands already represented in its nutrition catalog; it is not a complete FDA animal-recall index."
        ],
        "rules": rules,
    }


def write_outputs(payload: dict) -> None:
    (DATA / "recall_brands.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (DATA / "recall_brands.js").write_text(
        f"window.CATFOOD_RECALL_BRANDS = {compact};\n", encoding="utf-8"
    )


def main() -> int:
    payload = build_rules()
    write_outputs(payload)
    print(
        f"Wrote {payload['rule_count']} recall brand rules covering "
        f"{payload['source_brand_count']} source brand labels"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
