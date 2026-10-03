"""Aura lockup as a self-contained SVG (text converted to paths), per Aura-Marketing-Ecosystem brand/tokens.css:
.logo gap 13px; mark 42x42 (3 concentric circles); wordmark BLK Fort 24px, letter-spacing -.6px,
«Aura» Bold 700 + « Ecosystem» Book 400; ink #0a0a0a, on dark #fff.
usage: make_aura_logo.py <out-dir>
Fonts: put BLKFort-Bold.ttf and BLKFort-Book.ttf next to this script (from Global-Generation/Aura-Portal public/fonts, not committed here).
"""
import os
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
SIZE, TRACK, GAP, MARK = 24.0, -0.6, 13.0, 42.0


def run(font_path, text, x, baseline):
    f = TTFont(font_path)
    upm = f['head'].unitsPerEm
    s = SIZE / upm
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    hmtx = f['hmtx']
    d = []
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        d.append(pen.getCommands())
        x += hmtx[g][0] * s + TRACK
    asc = f['OS/2'].sCapHeight * s if getattr(f['OS/2'], 'sCapHeight', 0) else 0.7 * SIZE
    return ' '.join(p for p in d if p), x, asc


bold = os.path.join(HERE, 'BLKFort-Bold.ttf')
book = os.path.join(HERE, 'BLKFort-Book.ttf')
cap = TTFont(bold)['OS/2'].sCapHeight * SIZE / TTFont(bold)['head'].unitsPerEm
baseline = MARK / 2 + cap / 2          # cap height centred on the mark, like align-items:center
x0 = MARK + GAP
p1, x1, _ = run(bold, 'Aura', x0, baseline)
p2, x2, _ = run(book, ' Ecosystem', x1, baseline)
W = round(x2 + 2, 1)

for name, ink in (('aura-logo-ink.svg', '#0a0a0a'), ('aura-logo-white.svg', '#ffffff')):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {MARK:g}" width="{W}" height="{MARK:g}" role="img" aria-label="Aura Ecosystem">'
           f'<circle cx="21" cy="21" r="19" fill="none" stroke="{ink}" stroke-width="1.4" opacity=".16"/>'
           f'<circle cx="21" cy="21" r="13" fill="none" stroke="{ink}" stroke-width="1.6" opacity=".42"/>'
           f'<circle cx="21" cy="21" r="7" fill="{ink}"/>'
           f'<path fill="{ink}" d="{p1}"/><path fill="{ink}" d="{p2}"/></svg>\n')
    open(os.path.join(out, name), 'w').write(svg)
print('aura lockup', W, 'x', MARK, 'cap', round(cap, 2))
