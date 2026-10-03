"""Designed README header (Global Generation style, as in Infra-Core / Infra-IaC) on top of the existing README.
usage: build_readme.py <spec.json> <repo-dir>
spec: {
  "title": "SAT Prep Platform",
  "tagline": "one line",
  "badges": [{"label": "Next.js", "message": "16", "color": "000000", "logo": "nextdotjs", "href": optional}],
  "body": "keep" | "replace",          # keep = existing README minus its first H1; replace = use body_md
  "body_md": "...",                    # when body == replace
  "drop_lead_lines": 0                 # optional: drop N non-empty lines after the H1 (moved into the header)
}
Writes <repo-dir>/README.md and <repo-dir>/.github/assets/global-generation-{navy,white}.svg.
Idempotent: an existing header (marker comment) is replaced, not duplicated.
"""
import json
import os
import re
import shutil
import sys
import urllib.parse

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
BRANDS = {  # light / dark logo, width in README (GG 4x smaller than 460; Aura same visual height ~29px)
    'gg': ('global-generation-navy.svg', 'global-generation-white.svg', 'Global Generation', 115),
    'aura': ('aura-logo-ink.svg', 'aura-logo-white.svg', 'Aura Ecosystem', 160),
}
MARK_START = '<!-- gg-readme-header:start -->'
MARK_END = '<!-- gg-readme-header:end -->'

spec = json.load(open(sys.argv[1], encoding='utf-8'))
repo = sys.argv[2]
import subprocess
remote = subprocess.run(['git', '-C', repo, 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout
brand = spec.get('brand') or ('aura' if '/Aura-' in remote else 'gg')
LIGHT, DARK, ALT, WIDTH = BRANDS[brand]
readme = os.path.join(repo, 'README.md')
old = open(readme, encoding='utf-8').read() if os.path.exists(readme) else ''

# strip a previous generated header
if MARK_START in old:
    old = old.split(MARK_END, 1)[1].lstrip('\n')
    if old.startswith('---'):
        old = old[3:].lstrip('\n')

# ---- body ----
if spec.get('body', 'keep') == 'replace':
    body = spec['body_md'].strip('\n') + '\n'
else:
    lines = old.split('\n')
    # drop the first H1 (title moves into the header); lead lines go only together with it (first run)
    had_h1 = False
    for i, l in enumerate(lines):
        if l.strip():
            if re.match(r'^#\s', l):
                lines = lines[i + 1:]
                had_h1 = True
            break
    n = spec.get('drop_lead_lines', 0) if had_h1 else 0
    while n and lines:
        if lines[0].strip():
            n -= 1
        lines.pop(0)
    body = '\n'.join(lines).strip('\n') + '\n'

# house rules: no em-dash, no emoji (code blocks untouched)
EMOJI = re.compile('[\U0001F300-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF\U0001F000-\U0001F2FF️‍]')


def clean(text):
    out, in_code = [], False
    for l in text.split('\n'):
        if l.lstrip().startswith('```'):
            in_code = not in_code
            out.append(l)
            continue
        if not in_code:
            l = l.replace(' — ', ' - ').replace('—', '-')
            l = EMOJI.sub('', l).replace('  ', ' ') if EMOJI.search(l) else l
        out.append(l)
    return '\n'.join(out)


body = clean(body)

# ---- nav from ## headings ----
def anchor(h):
    a = h.strip().lower()
    a = re.sub(r'[^\w\- ]', '', a, flags=re.U)
    return a.replace(' ', '-')


heads, in_code = [], False
for l in body.split('\n'):
    if l.lstrip().startswith('```'):
        in_code = not in_code
    elif not in_code and re.match(r'^##\s+\S', l):
        heads.append(re.sub(r'^##\s+', '', l).strip())
nav = heads[:6]


def badge(b):
    q = lambda x: urllib.parse.quote(str(x).replace('-', '--').replace('_', '__'), safe='')
    url = 'https://img.shields.io/badge/%s-%s-%s' % (q(b['label']), q(b['message']), b.get('color', '13445d'))
    if b.get('logo'):
        url += '?logo=%s&logoColor=white' % b['logo']
    img = '<img src="%s" alt="%s %s">' % (url, b['label'], b['message'])
    return '<a href="%s">%s</a>' % (b['href'], img) if b.get('href') else img


header = [MARK_START, '<div align="center">', '  <picture>',
          '    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/%s">' % DARK,
          '    <img src=".github/assets/%s" alt="%s" width="%d">' % (LIGHT, ALT, WIDTH),
          '  </picture>', '', '  <h1>%s</h1>' % spec['title'], '', '  <p>%s</p>' % clean(spec['tagline'])]
if spec.get('badges'):
    header += ['', '  <p>'] + ['    ' + badge(b) for b in spec['badges']] + ['  </p>']
if nav:
    header += ['', '  <p>', '    ' + ' ·\n    '.join('<a href="#%s">%s</a>' % (anchor(h), h) for h in nav), '  </p>']
header += ['</div>', MARK_END, '', '---', '']

open(readme, 'w', encoding='utf-8').write('\n'.join(header) + '\n' + body)
adir = os.path.join(repo, '.github', 'assets')
os.makedirs(adir, exist_ok=True)
for b, (l, d, _, _) in BRANDS.items():  # only this brand's logos; drop the other brand's generated ones
    for f in (l, d):
        dst = os.path.join(adir, f)
        if b == brand:
            shutil.copyfile(os.path.join(ASSETS, f), dst)
        elif os.path.exists(dst):
            os.remove(dst)
print('README written', readme, '| brand', brand, '| sections in nav:', len(nav))
