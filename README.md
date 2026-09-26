# CatFood Compass v0.3.0

A mobile-first, static cat-food nutrition lookup app designed for GitHub Pages. There is **one canonical build only**. Historical and supplied nutrition records remain immutable source observations; current manufacturer catalogs are stored as separate reconciliation layers.

## Core nutrition data

The app still contains the same **2,024 source nutrition records**:

- 1,161 Lisa A. Pierson, DVM 2017 wet-food records.
- 838 FDSG wet-food records (FPUO flag preserved in the UI/data).
- 25 FDSG dry/air-dried/steam-dried records.

No source nutrition row was rewritten for v0.3.0.

## Dedicated current-manufacturer catalog databases

Three additive reconciliation databases now live in `data/`:

- `tiki_cat.json` / `tiki_cat.js` / `tiki_cat_reconciliation.csv`
- `fancy_feast.json` / `fancy_feast.js` / `fancy_feast_reconciliation.csv`
- `friskies.json` / `friskies.js` / `friskies_reconciliation.csv`

All three use the same rule: **current catalog identity and source nutrition are separate observations**. Verified current-name links improve search and appear as a secondary shelf/current-catalog name, but protein/fat/carbohydrate/phosphorus values continue to come from the original Pierson/FDSG record.

### Tiki Cat

The existing v0.2.9 database is retained unchanged: 161 catalog entries, 120 Tiki source observations, 95 verified links, 25 unresolved.

### Fancy Feast

Snapshot verified 2026-09-26 from Purina's official Fancy Feast wet-food catalog. The captured catalog contains 136 listing entries (135 currently listed plus one page explicitly marked discontinued), across Classic Paté, Grilled, Gravy Lovers, Gravy Lovers Paté in Gravy, Delights With Cheddar, Savory Centers, Flaked, Sliced, Minced, Chunky, Marinated Morsels, Medleys, Gourmet Naturals, Petites, Gems, Senior 7+, and Kitten. The broader Purina Fancy Feast product index reports 164 wet-cat-food products, so the dated reconciliation database records the catalog snapshot it actually captured rather than pretending those counts are identical.

There are 108 existing Fancy Feast source nutrition observations. Only conservative verified links are exposed to the app; uncertain historical-to-current relationships remain unresolved.

### Friskies

Snapshot verified 2026-09-26 from Purina's official Friskies wet-food catalog. The captured catalog contains 102 listing entries including individual foods and variety packs. Purina describes the line as having more than 60 wet-food varieties. Current catalog families include Paté, Shreds, Prime Filets, Tasty Treasures, Farm Favorites, Ocean Favorites, Wild Favorites Mini Bites, Indoor, Extra Gravy, Gravy Sensations, Meaty Bits, Fully Load'd, and Glaz'd & Infuz'd. Lil' Soups is explicitly stored as a **complement**, not a complete meal.

There are 74 existing Friskies source nutrition observations. Historical lines that do not have a sufficiently strong current identity match remain unresolved rather than being forced onto a modern SKU.

Purina also states that Friskies wet foods are rolling out without artificial colors or preservatives during 2026; that rollout is stored as brand-level source metadata rather than used to overwrite old nutrition/formula observations.

## Search and UI

Search remains ranked and typo-tolerant across brand, line, source recipe/style, verified shelf aliases, and now all three verified manufacturer reconciliation layers. Thus old source terminology can remain intact while current shelf terminology is searchable.

The six-theme system, Store Mode, mobile layout repairs, FPUO badges, source-anomaly behavior, favorites, compare view, and nutrition filters are unchanged.

## GitHub Pages

1. Put this folder's contents at the repository root.
2. Push to `main`.
3. In GitHub **Settings -> Pages**, deploy from `main` and `/ (root)`.
4. Relative paths make the app work at project-site URLs such as `https://username.github.io/repository/`.

For local testing:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Development tools

- `tools/extract_seed_pdf.py` — Pierson PDF extraction.
- `tools/extract_fdsg_wet.py` — FDSG wet PDF extraction.
- `tools/build_data.py` — core 2,024-record source dataset.
- `tools/build_tiki_db.py` — Tiki current catalog/reconciliation layer.
- `tools/build_purina_brand_dbs.py` — Fancy Feast + Friskies current catalog/reconciliation layers.
- `tools/validate_data.py` / `tools/validate_app.py` — regression checks.

The original PDFs are not bundled in the web app.
