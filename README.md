# CatFood Compass v0.3.7

## Current manufacturer nutrition layer

v0.3.7 expands the **separate current-manufacturer nutrient observation layer**. It remains deliberately additive: none of the 2,024 Pierson/FDSG source records are rewritten, and unlike nutrient bases are not silently merged into the profile filters.

The manufacturer layer now links **67 exact current products across 12 brands**. This release adds **23 exact matches**: **12 Fromm** current wet foods from Fromm's official 2026 Nutrition Reference Guide, **3 Farmina N&D Quinoa** wet formulas from current manufacturer product pages, and **8 The Honest Kitchen** wet foods from current manufacturer product pages. The prior ACANA, ORIJEN, RAWZ, Young Again, FirstMate, Hill's Science Diet, Dr. Elsey's, ZIWI Peak, and Weruva observations remain. Royal Canin's current US catalog has also been reviewed, but legacy-to-current product reconciliation remains intentionally pending rather than forcing uncertain identity matches.

Where a manufacturer publishes mathematically unusual calculated values, CatFood Compass preserves the source rather than silently correcting it. In particular, several current Weruva WX laboratory rows report negative calculated carbohydrate values; those observations are flagged as **Source anomaly preserved**, retain the raw values, and remain display/provenance data rather than inputs to profile filtering.

`data/manufacturer_nutrition.json` / `data/manufacturer_nutrition.js` preserve the manufacturer's own basis and source URL. Depending on the manufacturer, a record may contain % metabolizable energy, as-fed %, dry-matter %, per-100-kcal values, typical mineral percentages, Guaranteed Analysis, or calculated energy. Food cards receive a **Manufacturer data** badge when an exact link exists; the Details screen shows each basis in a separately labeled section alongside a direct manufacturer-source link.

Manufacturer data is currently a **comparison and provenance layer only**. For example, a dry-matter carbohydrate value is not substituted into a `% ME` carbohydrate filter. A later release can selectively promote directly compatible manufacturer fields after basis-specific validation.

## Catalog-brand recall matching

v0.3.4 changed the recall updater from broad feline-text matching to a **catalog-brand whitelist**. Machine-imported openFDA records are retained only when the product description both has feline context and matches a brand already represented in CatFood Compass.

`tools/build_recall_brands.py` derives a stable whitelist from the 107 source brand labels in `data/foods.js`, collapses known historical/current duplicates, and writes 89 canonical brand rules to `data/recall_brands.json` / `data/recall_brands.js`. Ambiguous shorthand labels such as `BLUE`, `GO`, and `DAVE'S` are not used as bare FDA aliases; they map to safer names such as `Blue Buffalo`, `GO! Solutions`, and `Dave's Pet Food`.

This directly guards against the false positives seen in the first recall implementation, including cat-shaped chocolate, Black Cat espresso ice cream, CAT 1 mangoes, Bio-Cat enzymes, Fat Cat sauce, and Dave's Coffee. Curated FDA notices are subjected to the same catalog-brand whitelist before they appear in the app. Nutrition data remains unchanged.

A mobile-first, static cat-food nutrition lookup app designed for GitHub Pages. There is **one canonical build only**. Historical and supplied nutrition records remain immutable source observations; current manufacturer catalogs and nutrition profiles are additive layers.

## Core nutrition data

The app still contains the same **2,024 source nutrition records**:

- 1,161 Lisa A. Pierson, DVM 2017 wet-food records.
- 838 FDSG wet-food records (FPUO flag preserved in the UI/data).
- 25 FDSG dry/air-dried/steam-dried records.

No source nutrition row was rewritten for v0.3.7.

## Nutrition profiles

**Normal is the default profile.** It is intentionally condition-neutral: no profile target is automatically applied and the cards show the general protein/fat/carbohydrate view.

Specialized profiles change the nutrient emphasis without changing the underlying food record:

- **Diabetes** — carbohydrate first. The starting carb target remains ≤10% of metabolizable calories, based on the supplied source material. The target can be changed.
- **Kidney** — phosphorus-first display, with optional user-entered phosphorus, sodium, and protein limits.
- **Urinary** — magnesium/phosphorus/sodium emphasis, with optional mineral limits.
- **Weight management** — kcal/100 g and protein emphasis, with optional calorie-density and protein targets.
- **Cancer / oncology** — deliberately has **no universal preset**. Optional calorie-density, protein, and carbohydrate targets can be entered for an individual plan.
- **Custom / Vet** — configurable carbohydrate, protein, fat, phosphorus, magnesium, calcium, sodium, and kcal/100 g targets.

For specialized profiles, a **Profile targets** quick filter appears. If numeric targets exist it can filter to records that have all required target data and meet the selected numbers. If no targets are configured, the button opens Settings rather than pretending there is a default medical cutoff.

Cards, details, compare view, and sorting adapt to the selected profile. Target language is intentionally descriptive (for example, “Meets selected targets” or “Outside selected targets”) rather than declaring a food medically safe or appropriate.


## FDA recall and advisory layer

The FDA safety layer is separate and non-destructive; it does **not** alter any nutrition observation.

- `data/recall_brands.json` / `data/recall_brands.js` are the catalog-derived recall whitelist shared by GitHub Actions and the browser.
- `data/recalls.json` / `data/recalls.js` provide the bundled offline snapshot used by the app.
- `data/recalls_curated.json` remains a source file for manually curated feline FDA notices, but only records matching a catalog brand are surfaced.
- `tools/build_recall_brands.py` rebuilds the whitelist from `data/foods.js`; all 107 source brand labels are covered by 89 canonical rules in this release.
- `tools/update_recalls.py` queries the FDA Recall Enterprise System through openFDA and retains only records with feline context plus an explicit catalog-brand alias match. The updater uses only the Python standard library.
- `.github/workflows/update-recalls.yml` rebuilds the brand whitelist, refreshes openFDA data, validates the result, and commits only when recall data changes. It runs daily, can be started manually, and also runs when the catalog/recall-matching code changes.
- The **Recalls** tab works offline from the bundled snapshot. **Check openFDA now** applies the same catalog-brand whitelist for a session-only live check.
- The service worker uses **network-first caching** for both the recall snapshot and brand-whitelist files, so installed/offline-capable copies can receive scheduled GitHub Pages updates while keeping the last successful copy offline.
- If a scheduled FDA refresh fails, the updater leaves the last known-good snapshot untouched; unchanged normalized records do not create timestamp-only daily commits.
- Food detail screens match by stable catalog brand IDs. A brand match means “check the exact FDA lot/package details,” not that every product from that brand is recalled. A missing match is explicitly **not** presented as proof that a product has never been recalled.

This is intentionally **not a complete FDA animal-recall index**: a recall for a brand that is not represented in CatFood Compass is outside the app's scope. FDA company recalls, FDA advisories, and machine-normalized openFDA enforcement records remain distinct record types.

## Dedicated current-manufacturer catalog databases

Three additive reconciliation databases remain in `data/`:

- `tiki_cat.json` / `tiki_cat.js` / `tiki_cat_reconciliation.csv`
- `fancy_feast.json` / `fancy_feast.js` / `fancy_feast_reconciliation.csv`
- `friskies.json` / `friskies.js` / `friskies_reconciliation.csv`

Current catalog identity and source nutrition remain separate observations. Verified current-name links improve search and appear as a secondary shelf/current-catalog name, but protein/fat/carbohydrate/phosphorus values continue to come from the original Pierson/FDSG record.

## Search and shopping UI

Search remains ranked and typo-tolerant across brand, line, source recipe/style, verified shelf aliases, and the manufacturer reconciliation layers. Store Mode, the six-theme system, FPUO badges, source-anomaly behavior, favorites, compare view, and advanced nutrition filters remain available.

Additional sort options now include magnesium, sodium, and kcal/100 g for the new profile workflows.

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
- `tools/build_recall_brands.py` — builds the catalog-brand recall whitelist from the food database.
- `tools/update_recalls.py` — FDA/openFDA recall snapshot updater.
- `tools/validate_manufacturer_nutrition.py` — verifies exact product links, source provenance, numeric sanity, JS/JSON parity, and basis-isolation guardrails.
- `tools/validate_data.py` / `tools/validate_app.py` / `tools/validate_brand_dbs.py` / `tools/validate_recalls.py` — regression checks.

The original PDFs are not bundled in the web app.