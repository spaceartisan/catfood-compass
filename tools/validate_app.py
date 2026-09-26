from pathlib import Path
root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text(encoding='utf-8')
js=(root/'app.js').read_text(encoding='utf-8')
css=(root/'styles.css').read_text(encoding='utf-8')
alias=(root/'data'/'aliases.js').read_text(encoding='utf-8')
assert 'id="storeModeBtn"' in html
assert 'data-quick="seafood"' in html
assert 'id="textureFilter"' in html
assert 'id="excludeSeafoodFilter"' in html
assert './data/aliases.js' in html
assert 'const isSeafood' in js and 'const textureMatches' in js
assert 'aliasById' in js and 'verified===true' in js
assert 'store-mode' in css
assert 'window.CATFOOD_ALIASES = []' in alias
print('PASS: Store Mode, seafood exclusion, texture filtering, and separate verified-alias layer are wired')

# Search UX regression checks (v0.2.4)
assert 'const searchScore' in js, 'ranked search missing'
assert 'oneEditApart' in js, 'typo tolerance missing'
assert 'searchSuggestions' in html and 'search-suggestion' in css, 'search suggestions missing'
assert 'data-clear-food-filters' in js, 'hidden-by-filter recovery missing'
assert '<option value="relevance">Best match</option>' in html, 'best-match sort missing'
print('PASS: ranked typo-tolerant search, suggestions, and filter-conflict recovery are wired')


# Theme regression checks (v0.2.5+)
for theme in ['forest','midnight','ocean','berry','sunset','lavender']:
    assert f'value="{theme}"' in html, f'{theme} theme control missing'
    if theme != 'forest':
        assert f'html[data-theme="{theme}"]' in css, f'{theme} theme CSS missing'
assert 'const applyTheme' in js and "theme:'forest'" in js, 'theme persistence/application missing'
assert 'theme-color' in html and 'localStorage.getItem' in html, 'pre-paint theme bootstrap missing'
print('PASS: six persistent themes and pre-paint theme bootstrap are wired')

# Sharper UI regression checks (v0.2.6+)
assert 'v0.2.6 — sharper, less rounded visual language' in css
assert '.food-card,.panel,.compare-wrap{border-radius:10px;box-shadow:none}' in css
assert '.badge{border-radius:4px' in css
print('PASS: sharper, flatter visual language is present')

# Real-device mobile layout regression checks (v0.2.7)
assert 'v0.2.7 — mobile layout repair from real-device screenshot' in css
assert 'class="search-stick"' in html
assert 'store-mode-preload' in html and 'store-mode-preload' in js
assert '.search-stick{position:sticky' in css
assert 'scroll-snap-type:x proximity' in css
assert 'bottom:calc(7px + var(--safe-bottom))' in css
print('PASS: v0.2.7 mobile Store Mode layout repairs are wired')

# Theme contrast / dismiss-control regression checks (v0.2.8)
assert 'v0.2.8 — theme contrast and dismiss-control hardening' in css
assert css.count('.close-btn') >= 1, 'close button styling missing'
assert 'stroke:currentColor' in css, 'SVG close icon does not follow themed foreground'
assert 'id="clearSearchBtn"' in html, 'app-owned search clear button missing'
assert '::-webkit-search-cancel-button' in css, 'native search clear suppression missing'
assert js.count('clearSearchBtn') >= 3, 'search clear behavior missing'
assert html.count('class="icon-btn close-btn"') >= 2, 'dialog close buttons not hardened'
assert 'class="icon-btn close-btn" data-close-detail' in js, 'detail close button not hardened'
assert '.sheet-head h2,' in css and '.theme-option strong,' in css, 'dialog/theme label foreground hardening missing'
print('PASS: v0.2.8 dialog, theme-label, and X/clear contrast hardening is wired')


# Current-manufacturer reconciliation layer regression checks (v0.3.0)
tiki_js=(root/'data'/'tiki_cat.js').read_text(encoding='utf-8')
fancy_js=(root/'data'/'fancy_feast.js').read_text(encoding='utf-8')
friskies_js=(root/'data'/'friskies.js').read_text(encoding='utf-8')
for rel,var,label in [('./data/tiki_cat.js','window.TIKI_CAT_DB','Tiki'),('./data/fancy_feast.js','window.FANCY_FEAST_DB','Fancy Feast'),('./data/friskies.js','window.FRISKIES_DB','Friskies')]:
    assert rel in html, f'{label} database script missing'
for blob,var,label in [(tiki_js,'window.TIKI_CAT_DB','Tiki'),(fancy_js,'window.FANCY_FEAST_DB','Fancy Feast'),(friskies_js,'window.FRISKIES_DB','Friskies')]:
    assert var in blob, f'{label} JS database wrapper missing'
assert 'brandCatalogSpecs' in js and 'currentCatalogMatchBySourceId' in js and 'currentCatalogMatchFor' in js, 'generic manufacturer reconciliation registry missing'
assert "startsWith('verified_')" in js, 'tentative manufacturer matches must not be exposed as verified aliases'
assert 'Current catalog reconciliation:' in js, 'generic reconciliation provenance note missing'
print('PASS: v0.3.0 Tiki, Fancy Feast, and Friskies non-destructive catalog reconciliation layers are wired')

# Nutrition profile regression checks (v0.3.1)
for profile in ['normal','diabetes','kidney','urinary','weight','oncology','custom']:
    assert f'value="{profile}"' in html, f'{profile} profile option missing'
assert 'id="profileSelect"' in html and 'id="profileTargetChip"' in html, 'browse profile controls missing'
assert "profile:'normal'" in js and 'const PROFILE_DEFS' in js, 'Normal default/profile registry missing'
assert 'const profileRules' in js and 'const profileMatches' in js and 'const evaluateProfile' in js, 'profile target engine missing'
assert 'settingUrinaryMagnesiumMax' in html and 'settingCustomSodiumMax' in html and 'settingOncologyKcalMin' in html, 'specialized/custom profile target controls missing'
assert 'v0.3.1 — nutrition profiles' in css, 'profile UI CSS missing'
assert 'Profile targets' in html and 'no universal cancer-food cutoff is assumed' in js, 'profile target UX/caution text missing'
print('PASS: v0.3.1 Normal-default multi-condition nutrition profile system is wired')

# FDA recall/advisory layer regression checks (v0.3.2)
recalls_js=(root/'data'/'recalls.js').read_text(encoding='utf-8')
assert 'id="recallsView"' in html and 'data-nav="recalls"' in html, 'Recalls view/navigation missing'
assert 'id="refreshRecallsBtn"' in html and 'id="recallSearchInput"' in html and 'id="recallStatusFilter"' in html, 'Recall controls missing'
assert './data/recalls.js' in html and 'window.CATFOOD_RECALLS' in recalls_js, 'Bundled recall data missing'
for symbol in ['recallBundle','foodRecallDetailHtml','renderRecalls','refreshRecallsLive','updateRecallNavCount']:
    assert symbol in js, f'Recall helper missing: {symbol}'
assert 'v0.3.2 — FDA recall/advisory layer' in css, 'Recall UI CSS marker missing'
assert (root/'tools'/'update_recalls.py').exists(), 'Recall updater missing'
assert (root/'.github'/'workflows'/'update-recalls.yml').exists(), 'Scheduled recall workflow missing'
assert 'A missing match is <strong>not proof that a product has never been recalled</strong>' in html, 'Recall absence disclaimer missing'
print('PASS: v0.3.2 bundled FDA recall/advisory view, live check, product matching, and scheduled updater are wired')
