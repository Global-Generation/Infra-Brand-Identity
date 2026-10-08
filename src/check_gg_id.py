"""Check GG ID: every screen in gg-id/screens at 1440 and 390 px, 3 layouts x 2 themes, plus the showcase gg-id.html.

Fails on horizontal scroll, elements sticking out of the screen, missing Montserrat, console errors, dashes in text.
Screenshots: shots/gg-id/. Run: uv run --with playwright python src/check_gg_id.py
"""
import os
import sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENS = os.path.join(ROOT, 'gg-id', 'screens')
OUT = os.path.join(ROOT, 'shots', 'gg-id')
os.makedirs(OUT, exist_ok=True)

PROBE = '''async () => {
  await document.fonts.ready;
  const de = document.documentElement, W = de.clientWidth;
  const out = [];
  document.querySelectorAll('.gid-main *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0) return;
    if (r.right > W + 1 || r.left < -1) {
      let p = el.parentElement, clipped = false;
      while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o !== 'visible') { clipped = true; break; } p = p.parentElement; }
      if (!clipped) out.push((el.className && el.className.baseVal === undefined ? el.className : el.tagName) + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
    }
  });
  const card = document.querySelector('.gid-card').getBoundingClientRect();
  return {
    scrollW: de.scrollWidth, clientW: W, height: de.scrollHeight, viewH: innerHeight,
    font: document.fonts.check('700 16px Montserrat') && document.fonts.check('500 16px Montserrat'),
    usedFont: getComputedStyle(document.querySelector('.gid-h') || document.body).fontFamily,
    dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length,
    wide: out.slice(0, 8), cardW: Math.round(card.width),
    aside: getComputedStyle(document.querySelector('.gid-aside')).display
  };
}'''

problems = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for vw, vh, tag in [(1440, 900, 'desktop'), (390, 844, 'phone')]:
        for theme in ('light', 'dark'):
            ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2 if vw < 500 else 1,
                                color_scheme=theme)
            pg = ctx.new_page()
            errs = []
            pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
            for fn in sorted(os.listdir(SCREENS)):
                key = fn[:-5]
                for layout in ('split', 'card', 'minimal'):
                    errs.clear()
                    pg.goto('file://' + os.path.join(SCREENS, fn) + f'?layout={layout}')
                    pg.wait_for_timeout(250)
                    r = pg.evaluate(PROBE)
                    label = f'{tag}/{theme}/{layout}/{key}'
                    if r['scrollW'] > r['clientW']:
                        problems.append(f'{label}: horizontal scroll {r["scrollW"]} > {r["clientW"]}')
                    if r['wide']:
                        problems.append(f'{label}: sticks out {r["wide"]}')
                    if not r['font'] or 'Montserrat' not in r['usedFont']:
                        problems.append(f'{label}: font {r["usedFont"]}')
                    if r['dashes']:
                        problems.append(f'{label}: dashes in text {r["dashes"]}')
                    if errs:
                        problems.append(f'{label}: console {errs[:3]}')
                    if layout == 'split' and tag == 'desktop' and r['aside'] != 'flex':
                        problems.append(f'{label}: split panel hidden on desktop')
                    if tag == 'phone' and r['aside'] != 'none':
                        problems.append(f'{label}: split panel visible on phone')
                    if r['height'] > r['viewH'] and tag == 'desktop':
                        problems.append(f'{label}: taller than the window {r["height"]} > {r["viewH"]}')
                    shot = (theme == 'light' and layout == 'split') or key in ('login', 'setpass', 'done', 'pin')
                    if shot:
                        pg.wait_for_timeout(900 if key == 'done' else 150)
                        pg.screenshot(path=os.path.join(OUT, f'{tag}-{theme}-{layout}-{key}.png'))
            ctx.close()

    # showcase: page width, all modes render, console clean
    for vw, vh, tag in [(1440, 900, 'desktop'), (390, 844, 'phone')]:
        ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2 if vw < 500 else 1)
        pg = ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        for h in ('s=login&l=split&t=light&d=desktop', 's=setpass&l=card&t=dark&d=phone', 's=login&l=minimal&t=light&d=all',
                  's=error&l=split&t=dark&d=desktop'):
            pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#' + h)
            pg.reload()
            pg.wait_for_timeout(700)
            r = pg.evaluate('''() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
              gids: document.querySelectorAll('#stage .gid').length, thumbs: document.querySelectorAll('.sc-thumb').length,
              tabs: document.querySelectorAll('.sc-tab').length, rows: document.querySelectorAll('.sc-api tbody tr').length,
              dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length})''')
            label = f'showcase/{tag}/{h}'
            if r['sw'] > r['cw']:
                problems.append(f'{label}: horizontal scroll {r["sw"]} > {r["cw"]}')
            if r['gids'] < 1 or r['tabs'] < 15 or r['rows'] < 15:
                problems.append(f'{label}: not rendered {r}')
            if r['dashes']:
                problems.append(f'{label}: dashes {r["dashes"]}')
            pg.screenshot(path=os.path.join(OUT, f'showcase-{tag}-{h.split("&")[0][2:]}-{h.split("&")[3][2:]}.png'),
                          full_page=(h.endswith('d=all')))
        pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#s=login&l=split&t=light&d=desktop')
        pg.reload()
        pg.wait_for_timeout(400)
        pg.click('.sc-tab[data-key="password"]')
        pg.click('#stage .gid-btn--primary[type=submit]')
        pg.wait_for_timeout(200)
        if 's=enroll' not in pg.url:
            problems.append(f'showcase/{tag}: password submit did not lead to enroll ({pg.url})')
        pg.screenshot(path=os.path.join(OUT, f'showcase-{tag}-full.png'), full_page=True)
        if errs:
            problems.append(f'showcase/{tag}: console {errs[:5]}')
        ctx.close()
    b.close()

if problems:
    print('GG ID CHECK FAILED')
    for x in problems:
        print(' -', x)
    sys.exit(1)
print('ok: all screens x 3 layouts x 2 themes x 2 widths, showcase clean; shots in', OUT)
