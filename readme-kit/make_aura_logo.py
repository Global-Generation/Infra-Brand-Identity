"""Aura lockup as a self-contained SVG (text converted to paths), per Aura-Marketing-Ecosystem IDENTITY.md «Вордмарк»:
.logo gap 13px; mark 42x42 = globe «три кольца и планета» (brand/globe/aura-globe-light.svg, on dark aura-globe-white.svg);
wordmark Tenor Sans 400 24px, letter-spacing -.6px, «Aura» ink + « Ecosystem» muted (#93928e, on dark #9a9a9a).
usage: make_aura_logo.py <out-dir> <Aura-Marketing-Ecosystem checkout>
Needs fonttools + brotli (woff2): uv run --with fonttools --with brotli python make_aura_logo.py ...
"""
import os
import re
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

out, eco = sys.argv[1], sys.argv[2]
SIZE, TRACK, GAP, MARK = 24.0, -0.6, 13.0, 42.0
font = TTFont(os.path.join(eco, 'fonts', 'TenorSans-latin.woff2'))


def run(text, x, baseline):
    upm = font['head'].unitsPerEm
    s = SIZE / upm
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font['hmtx']
    d = []
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        d.append(pen.getCommands())
        x += hmtx[g][0] * s + TRACK
    return ' '.join(p for p in d if p), x


def mark(name):
    # globe as a nested <svg> scaled into the 42x42 mark box; ids prefixed so the two files never collide
    src = open(os.path.join(eco, 'brand', 'globe', name)).read()
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    body = re.sub(r'^<svg[^>]*>|</svg>\s*$', '', src.strip())
    body = re.sub(r'id="([^"]+)"', r'id="m-\1"', body)
    body = re.sub(r'url\(#([^)]+)\)', r'url(#m-\1)', body)
    return f'<svg x="0" y="0" width="{MARK:g}" height="{MARK:g}" viewBox="{vb}">{body}</svg>'


cap = font['OS/2'].sCapHeight * SIZE / font['head'].unitsPerEm
baseline = MARK / 2 + cap / 2          # cap height centred on the mark, like align-items:center
p1, x1 = run('Aura', MARK + GAP, baseline)
p2, x2 = run(' Ecosystem', x1, baseline)
W = round(x2 + 2, 1)

for name, globe, ink, muted in (('aura-logo-ink.svg', 'aura-globe-light.svg', '#0a0a0a', '#93928e'),
                                ('aura-logo-white.svg', 'aura-globe-white.svg', '#ffffff', '#9a9a9a')):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {MARK:g}" width="{W}" height="{MARK:g}" role="img" aria-label="Aura Ecosystem">'
           f'{mark(globe)}<path fill="{ink}" d="{p1}"/><path fill="{muted}" d="{p2}"/></svg>\n')
    open(os.path.join(out, name), 'w').write(svg)
print('aura lockup', W, 'x', MARK, 'cap', round(cap, 2))
