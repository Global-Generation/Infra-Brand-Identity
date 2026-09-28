"""Build index.html (brand page) from src/template.html + fonts + logo + lucide icons + Джи-джи mascot.

Run: python3 src/build.py
"""
import json
import os
import re
import sys
import urllib.parse
import base64

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.dirname(HERE)
OUT = os.path.join(OUT_DIR, 'index.html')
ICON_DIR = os.path.join(HERE, 'lucide-icons')

tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
fonts = open(os.path.join(HERE, 'fonts.css'), encoding='utf-8').read()

# ---- vector GG mark (source: Ops-Legal/frontend/public/gg-icon.svg) ----
icon_src = open(os.path.join(HERE, 'gg-icon.svg'), encoding='utf-8').read()
paths = re.findall(r'<path d="([^"]+)"', icon_src)
assert len(paths) == 4, len(paths)
MAIN = paths[2]
SEC = ' '.join([paths[0], paths[1], paths[3]])

# ---- full logo (source: Ops-Legal/frontend/public/global-logo.svg) ----
logo_src = open(os.path.join(HERE, 'global-logo.svg'), encoding='utf-8').read()
logo_paths = re.findall(r'<path d="([^"]+)"', logo_src)
assert len(logo_paths) == 20, len(logo_paths)
FULLLOGO = ''.join(f'<path d="{d}"/>' for d in logo_paths)
# paths 0-15 are the GLOBAL GENERATION letters, 16-19 the mark (checked by x origin)
LOGO_LETTERS = ''.join(f'<path d="{d}"/>' for d in logo_paths[:16])


def icon_inner(name):
    s = open(os.path.join(ICON_DIR, name + '.svg'), encoding='utf-8').read()
    body = s.split('>', 2)[2] if s.startswith('<!--') else s.split('>', 1)[1]
    body = body.rsplit('</svg>', 1)[0]
    body = re.sub(r'\s+', ' ', body).replace(' />', '/>').strip()
    return body


# icons referenced as #i-NAME in the template + service icons listed in the JS block
ui_icons = sorted(set(re.findall(r'#i-([a-z0-9-]+)', tpl)))
svc_icons = sorted(set(re.findall(r"icon:'([a-z0-9-]+)'", tpl)))
all_icons = sorted(set(ui_icons) | set(svc_icons))
sprite = ''.join(
    f'<symbol id="i-{n}" viewBox="0 0 24 24">{icon_inner(n)}</symbol>' for n in all_icons)
icons_json = json.dumps({n: icon_inner(n) for n in svc_icons}, ensure_ascii=False)

# master favicon: navy tile + white G + sky secondary
fav_svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 39 39">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1f6a90"/><stop offset="1" stop-color="#0d2f42"/></linearGradient></defs>'
    '<rect width="39" height="39" rx="9" fill="url(#g)"/>'
    f'<path d="{SEC}" fill="#ffffff"/><path d="{MAIN}" fill="#ffffff"/></svg>')
fav_uri = 'data:image/svg+xml,' + urllib.parse.quote(fav_svg, safe='')

html = (tpl
        .replace('/*@FONTS@*/', fonts)
        .replace('@MARK_MAIN@', MAIN)
        .replace('@MARK_SEC@', SEC)
        .replace('@GIGI_URI@', 'data:image/png;base64,' + base64.b64encode(open(os.path.join(HERE, 'gigi-256.png'), 'rb').read()).decode())
        .replace('@FULLLOGO@', FULLLOGO)
        .replace('@LOGO_LETTERS@', LOGO_LETTERS)
        .replace('<!--@SPRITE@-->', sprite)
        .replace('/*@ICONS_JSON@*/', icons_json)
        .replace('@FAVICON_URI@', fav_uri))

# ---- hard brand asserts ----
problems = []
leftover = re.findall(r'@[A-Z_]+@|/\*@[A-Z_]+@\*/|<!--@[A-Z]+@-->', html)
if leftover:
    problems.append(f'unfilled placeholders: {leftover[:5]}')
for bad, why in [('—', 'em-dash'), ('–', 'en-dash'), ('&mdash;', 'em-dash entity'),
                 ('&ndash;', 'en-dash entity'), ('&#8212;', 'em-dash entity'), ('&#x2014;', 'em-dash entity'),
                 ('fonts.googleapis', 'google fonts'), ('fonts.gstatic', 'google fonts'),
                 ('5b4be0', 'violet'), ('6d5cf0', 'violet'), ('9286f0', 'violet'), ('4a39c8', 'violet'),
                 ('c4b5fd', 'lilac'), ('196, 181, 253', 'lilac'), ('196,181,253', 'lilac'),
                 ('наставник', 'наставник (only allowed in the rules line)')]:
    n = html.lower().count(bad.lower())
    if bad == 'наставник':
        if n > 2:
            problems.append(f'{why}: {n}')
        continue
    if n:
        problems.append(f'{why}: {n}')
emoji = re.findall('[\U0001F000-\U0001FAFF☀-➿⬀-⯿️]', html)
if emoji:
    problems.append(f'emoji-like chars: {emoji[:10]}')
ext = [u for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
       if not (u.startswith('https://cdnjs.cloudflare.com') or u.startswith('https://cdn.jsdelivr.net/npm/'))]
if ext:
    problems.append(f'external resources: {ext}')
if problems:
    print('BRAND CHECK FAILED')
    for p in problems:
        print(' -', p)
    sys.exit(1)

os.makedirs(OUT_DIR, exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(html)
print('ok', OUT, f'{len(html)/1024:.0f} KB', 'icons:', len(all_icons))
