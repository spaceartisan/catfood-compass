# CatFood Compass v0.2.6

A mobile-friendly, static cat-food shopping app designed for GitHub Pages. **There is one canonical build only; all included source records live in this app.** It compares foods primarily by **protein, fat, and carbohydrate as percent of metabolizable calories**, **phosphorus in mg/100 kcal**, and **calorie density/package calories when the source provides them**.

## Included data

The app currently contains **2,024 records** from three supplied reference sets:

- **1,161 Pierson 2017 records** from *Cat Food - Nutritional Composition* (Lisa A. Pierson, DVM). These remain clearly marked historical.
- **838 FDSG wet-food records** extracted from *Known values for Cat Foods - Wet*. These include protein/fat/carbohydrate %ME where supplied, kcal/100 g, phosphorus, magnesium, calcium, sodium, and row update dates where present.
- **25 FDSG dry / air-dried / steam-dried records** from *Dry Food List - Compiled for FDSG*. This source is mainly a carbohydrate list, so missing protein, fat, phosphorus, and calorie data remain blank.

Source anomalies are preserved and flagged rather than silently corrected. Examples include negative calculated carbohydrate values and macro totals that do not add to approximately 100% in the supplied wet-food sheet.

## What it does

- Ranked, typo-tolerant search across brand, product line/collection, recipe, style, source, and independently verified modern shelf-name aliases. Search words can match different fields, so `Fancy Feast Classic` and `Tiki Cat After Dark` work as expected. Best matches rise to the top, and the app offers mobile-friendly brand/line/product suggestions.
- Search diagnostics distinguish a true no-match from a match hidden by active nutrition/quick filters, with a one-tap option to clear those filters.
- Default quick filter: carbohydrate at or below 10% of calories (user-adjustable).
- Filter/sort by protein, fat, carbohydrate, phosphorus, brand, source dataset, food form, texture, prescription status, seafood/fish exclusion, and data completeness.
- Distinguish wet, dry, air-dried, and steam-dried foods.
- One-tap **No seafood** filtering and texture filters for pâté/loaf, shreds/flakes, minced/bits/chunks/slices, gravy/sauce/stew, broth/consommé/aspic, and mousse.
- **Store Mode** hides the large landing panel and tightens the mobile shopping cards while keeping the core nutrient values, warnings, favorites, details, and comparison controls.
- Six persistent visual themes: **Catnip**, **Midnight**, **Ocean**, **Berry**, **Sunset**, and **Lavender**. Theme selection is stored locally and applies before first paint to avoid flashing the default palette.
- Sharper visual language with tighter corner radii, flatter cards, crisper nutrient tiles, and less pill-shaped chrome while preserving touch-friendly controls.
- Show source dates on FDSG rows when the source provides them.
- Show phosphorus plus additional magnesium/calcium/sodium in details when available.
- Favorite foods locally and compare up to four side-by-side.
- Add current manufacturer/TNA values and keep them on the device using `localStorage`.
- Estimate caloric macro distribution from a complete Guaranteed Analysis entry (including ash), clearly labeled as an estimate.
- Works offline after first load through a service worker.
- No backend, accounts, tracking, build step, or external JavaScript libraries.

## FPUO source flag

The supplied **FDSG wet-food PDF is marked “For personal use only.”** CatFood Compass uses one canonical build: those records are included in the same database and carry `source_personal_use_only: true`. The UI displays an **FPUO** badge on those records so the source restriction remains visible.

## GitHub Pages deployment

1. Create a GitHub repository.
2. Put the contents of this folder in the repository root.
3. Push to `main`.
4. In **Settings -> Pages**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`.
5. Open the Pages URL. All paths are relative, so project-site URLs such as `https://username.github.io/repository/` work correctly.

## Local test

Run a small web server from this directory:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Data files and extraction

`data/foods.js` is the browser-ready merged dataset.

The development folder also contains:

- `data/fdsg_wet.json` - extracted wet-food records.
- `data/fdsg_dry.json` - structured dry-food records.
- `tools/extract_seed_pdf.py` - original Pierson chart extractor.
- `tools/extract_fdsg_wet.py` - coordinate-based FDSG wet PDF extractor.
- `tools/build_data.py` - merges all supplied datasets into `foods.js`.
- `tools/validate_data.py` - regression and integrity checks.

The original PDFs are **not** included in the app package.

Run integrity checks with:

```bash
python tools/validate_data.py
```

## Data model notes

The core nutrient fields are:

- `protein_cal_pct`
- `fat_cal_pct`
- `carb_cal_pct`
- `phosphorus_mg_per_100kcal`
- `kcal_per_100g` for newer wet-source rows where supplied
- `calories` / package metadata for historical rows where supplied

The newer wet sheet also supplies optional:

- `magnesium_mg_per_100kcal`
- `calcium_mg_per_100kcal`
- `sodium_mg_per_100kcal`
- `updated`

Qualitative dry-food entries such as **Trace** or **under 6%** remain qualitative rather than being converted into invented exact values.


### Source names and current shelf names

`data/foods.js` remains the source-of-record dataset. Historical/source product names are never overwritten. `data/aliases.js` is a separate, initially empty mapping layer for independently verified modern shelf names. The app only uses alias rows marked `verified: true`; aliases can improve search and appear as a secondary “Shelf” label while the original source name remains primary.

## Important limitation

Commercial formulas change and all of these numbers inherit the uncertainty of their source. CatFood Compass is intended to make comparison and record-keeping easier, not to declare a food medically safe or replace a veterinary plan.
