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
