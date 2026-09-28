import os
import sys
from playwright.sync_api import sync_playwright

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')
OUT = os.path.join(os.path.dirname(PATH), 'shots')
URL = 'file://' + PATH

html = open(PATH, encoding='utf-8').read()
print('em-dash count:', html.count('—'), 'en-dash:', html.count('–'))

with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h, tag in [(1440, 900, 'desktop-1440'), (390, 844, 'mobile-390')]:
        ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2 if w < 500 else 1)
        pg = ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        pg.goto(URL)
        pg.wait_for_timeout(1200)
        res = pg.evaluate('''async () => {
          await document.fonts.ready;
          const de = document.documentElement;
          const wide = [];
          document.querySelectorAll('body *').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.right > de.clientWidth + 1 && getComputedStyle(el).position !== 'fixed') {
              let p = el.parentElement, clipped = false;
              while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'hidden' || o === 'scroll') { clipped = true; break; } p = p.parentElement; }
              if (!clipped) wide.push((el.className && el.className.baseVal === undefined ? el.className : el.tagName) + ' ' + Math.round(r.right));
            }
          });
          return {
            scrollW: de.scrollWidth, clientW: de.clientWidth,
            f700: document.fonts.check('700 16px Montserrat'), f500: document.fonts.check('500 16px Montserrat'),
            loaded: [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight),
            bodyFont: getComputedStyle(document.body).fontFamily,
            wide: wide.slice(0, 15),
            dashInText: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length,
            imgsBroken: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length,
            svcCards: document.querySelectorAll('#svcgrid .svc').length,
            chips: document.querySelectorAll('#switch .pchip').length,
            height: de.scrollHeight
          };
        }''')
        print(tag, res)
        print(tag, 'console:', errs[:10])
        pg.screenshot(path=os.path.join(OUT, f'screenshot-{tag}-full.png'), full_page=True)
        pg.screenshot(path=os.path.join(OUT, f'screenshot-{tag}-top.png'))
        ctx.close()
    b.close()
