"""Static token/markup checks. Runtime interaction proof lives in browser_check.cjs."""
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
tokens = json.loads((ROOT/'core/static/core/tokens.json').read_text(encoding='utf-8'))
css = (ROOT/'core/static/core/tokens.css').read_text(encoding='utf-8')
design = (ROOT.parent/'DESIGN.md').read_text(encoding='utf-8')
for key,value in tokens['colors'].items():
    assert f'--color-{key}: {value};' in css, key+' token drift'
    assert f'{key}: "{value}"' in design, key+' DESIGN.md drift'
for path in (ROOT/'core/templates').rglob('*.html'):
    text = path.read_text(encoding='utf-8')
    assert not re.search(r'href=["\']#["\']',text),str(path)+' empty link'
    for tag in re.findall(r'<form\b[^>]*>',text):
        assert 'novalidate' in tag, str(path)+' missing form owner'
js = (ROOT/'core/static/core/app.js').read_text()
assert not re.search(r'\b(?:alert|confirm|prompt)\s*\(',js),'Native blocking dialog'
assert 'prefers-reduced-motion' in (ROOT/'core/static/core/app.css').read_text()
print('PASS: token and DESIGN.md mapping, forms, links, dialogs, reduced motion.')
