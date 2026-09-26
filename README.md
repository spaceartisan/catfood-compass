# CatFood Compass v0.3.1

A mobile-first, static cat-food nutrition lookup app designed for GitHub Pages. There is **one canonical build only**. Historical and supplied nutrition records remain immutable source observations; current manufacturer catalogs and nutrition profiles are additive layers.

## Core nutrition data

The app still contains the same **2,024 source nutrition records**:

- 1,161 Lisa A. Pierson, DVM 2017 wet-food records.
- 838 FDSG wet-food records (FPUO flag preserved in the UI/data).
- 25 FDSG dry/air-dried/steam-dried records.

No source nutrition row was rewritten for v0.3.1.

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
- `tools/validate_data.py` / `tools/validate_app.py` / `tools/validate_brand_dbs.py` — regression checks.

The original PDFs are not bundled in the web app.
