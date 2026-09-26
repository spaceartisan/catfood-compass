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
