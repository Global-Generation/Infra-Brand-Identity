"""Check GG ID: every screen in gg-id/screens at 1440 and 390 px, 3 layouts x 2 themes, the GG ID card,
the e-mail card gg-id/email-card.html and the showcase gg-id.html.

Fails on horizontal scroll, elements sticking out of the screen, missing Montserrat, console errors, dashes in text;
for the card also on text outside the card padding, wrong proportions, more than one accent, proportional digits;
for the e-mail card on low contrast in light, dark (Apple Mail) and inverted (Gmail on iPhone) modes.
Screenshots: shots/gg-id/. Run: uv run --with playwright python src/check_gg_id.py
With --preview it also refreshes the card pictures in gg-id/preview/ (README and PR).
"""
import html
import os
import re
import shutil
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

# GG ID card: everything inside the padding, one accent (the status dot), monospaced digits, Montserrat
CARD_PROBE = '''async (sel) => {
  await document.fonts.ready;
  const ACCENT = '92, 195, 236', LIGHT_ACCENT = '0, 156, 220';
  const name = e => (e.className && e.className.baseVal === undefined && e.className) || e.tagName;
  const res = [];
  document.querySelectorAll(sel).forEach(c => {
    const r = c.getBoundingClientRect(), cs = getComputedStyle(c);
    const pl = parseFloat(cs.paddingLeft), pr = parseFloat(cs.paddingRight), pt = parseFloat(cs.paddingTop), pb = parseFloat(cs.paddingBottom);
    const outside = [], accents = [];
    c.querySelectorAll('*').forEach(e => {
      const q = e.getBoundingClientRect();
      if (!q.width || !q.height) return;
      if (q.left < r.left + pl - 1 || q.right > r.right - pr + 1 || q.top < r.top + pt - 1 || q.bottom > r.bottom - pb + 1)
        outside.push(name(e) + ' @' + Math.round(q.left - r.left) + ',' + Math.round(q.top - r.top) + ' ' + Math.round(q.width) + 'x' + Math.round(q.height));
    });
    [c, ...c.querySelectorAll('*')].forEach(e => {
      if (!e.getClientRects().length) return;
      [null, '::before', '::after'].forEach(ps => {
        const s = getComputedStyle(e, ps);
        if (ps && s.content === 'none') return;
        if ([s.color, s.backgroundColor, s.borderTopColor].some(v => v.includes(ACCENT) || v.includes(LIGHT_ACCENT))) accents.push(name(e) + (ps || ''));
      });
    });
    const num = c.querySelector('[data-gid-field="id"]');
    let tnum = null;
    if (num) {
      const pr2 = document.createElement('span');
      pr2.className = num.className; pr2.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap';
      num.parentNode.appendChild(pr2);
      pr2.textContent = '1111111111'; const w1 = pr2.getBoundingClientRect().width;
      pr2.textContent = '0000000000'; const w0 = pr2.getBoundingClientRect().width;
      pr2.remove();
      tnum = Math.abs(w1 - w0) < 0.5;
    }
    const nm = c.querySelector('[data-gid-field="name"]');
    res.push({w: r.width, h: r.height, ratio: r.width / r.height, parentW: c.parentElement.getBoundingClientRect().width,
      parentPad: parseFloat(getComputedStyle(c.parentElement).paddingLeft) + parseFloat(getComputedStyle(c.parentElement).paddingRight),
      outside: outside.slice(0, 6), accents, tnum, font: nm ? getComputedStyle(nm).fontFamily : getComputedStyle(c).fontFamily});
  });
  return {cards: res, fontOk: document.fonts.check('700 16px Montserrat') && document.fonts.check('600 16px Montserrat'),
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
    dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length};
}'''

RATIO = 85.6 / 54
LONG = {'name': 'Александра Образцова-Константинопольская',
        'positions': ['Ментор', 'Руководитель направления «Магистратура в Европе»', 'Ведущая роликов YouTube-канала'],
        'email': 'aleksandra.obraztsova-konstantinopolskaya@global-generations.com', 'id': 'GG 9031-55C0E7', 'since': '2025-09',
        'status': 'active', 'passkey': True}
EMPTY = {'name': 'Лёв', 'positions': [], 'email': 'lev.demo@global-generations.com', 'id': 'GG 1', 'since': '2026-10',
         'status': 'disabled', 'passkey': False}

# e-mail card: the hub fills the placeholders (escaped), Gmail on iPhone inverts colours but not images
EMAIL = os.path.join(ROOT, 'gg-id', 'email-card.html')
EMAIL_PNG = os.path.join(ROOT, 'gg-id', 'email', 'gg-id-lockup-2x.png')
EMAIL_PNG_URL = 'https://levauth.global-generations-edu.com/assets/gg-id/email/gg-id-lockup-2x.png'
EMAIL_DEMO = {'name': 'Иван Образцов', 'initials': 'ИО', 'positions': 'Ментор · Продажи',
              'email': 'ivan.obraztsov@global-generations.com', 'id': 'GG 0042-7F3A', 'since': 'марта 2024'}
EMAIL_LONG = {'name': 'Александра Образцова-Константинопольская', 'initials': 'АО',
              'positions': 'Ментор · Руководитель направления «Магистратура в Европе» · Ведущая роликов YouTube-канала',
              'email': 'aleksandra.obraztsova-konstantinopolskaya@global-generations.com', 'id': 'GG 9031-55C0E7', 'since': 'сентября 2025'}
INVERT = '''() => {   // like Gmail on iPhone in dark mode: lightness of every colour flipped, images untouched
  const parse = v => { const m = v.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(',').map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const flip = c => { let r = c.r / 255, g = c.g / 255, b = c.b / 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b); let h = 0, s = 0, l = (mx + mn) / 2;
    if (mx !== mn) { const d = mx - mn; s = l > .5 ? d / (2 - mx - mn) : d / (mx + mn);
      h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h /= 6; }
    l = 1 - l;
    const q = l < .5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
    const hue = t => { t = (t + 1) % 1; return t < 1 / 6 ? p + (q - p) * 6 * t : t < 1 / 2 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
    const to = x => Math.round(x * 255);
    return s === 0 ? `rgba(${to(l)}, ${to(l)}, ${to(l)}, ${c.a})` : `rgba(${to(hue(h + 1 / 3))}, ${to(hue(h))}, ${to(hue(h - 1 / 3))}, ${c.a})`; };
  const plan = [];
  document.querySelectorAll('body, body *').forEach(e => {
    if (e.tagName === 'IMG') return;
    const s = getComputedStyle(e);
    ['color', 'background-color', 'border-top-color', 'border-left-color'].forEach(prop => { const c = parse(s.getPropertyValue(prop)); if (c && c.a > 0) plan.push([e, prop, flip(c)]); });
  });
  plan.forEach(([e, prop, v]) => e.style.setProperty(prop, v, 'important'));
}'''
CONTRAST = '''() => {
  const parse = v => { const m = v.match(/rgba?\\(([^)]+)\\)/); const p = m[1].split(',').map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = c => { const f = x => { x /= 255; return x <= .03928 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const bgOf = e => { for (let p = e; p; p = p.parentElement) { const c = parse(getComputedStyle(p).backgroundColor); if (c.a > 0) return c; } return {r: 255, g: 255, b: 255, a: 1}; };
  const low = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walk.nextNode(); n; n = walk.nextNode()) {
    const t = n.nodeValue.trim(); if (!t) continue;
    const e = n.parentElement; if (!e.getClientRects().length || getComputedStyle(e).display === 'none') continue;
    const cr = ratio(parse(getComputedStyle(e).color), bgOf(e));
    if (cr < 4.5) low.push(t.slice(0, 24) + ' ' + cr.toFixed(2));
  }
  const img = document.querySelector('img'), card = document.querySelector('.gidm-card');
  const plate = {r: 19, g: 68, b: 93, a: 1};   // the navy plate baked into the PNG
  const cb = card.getBoundingClientRect();
  return {low, img: img.complete && img.naturalWidth > 0, plate: ratio(plate, bgOf(card)), bodyLum: lum(bgOf(document.body)),
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth, cardW: cb.width,
    left: (document.body.innerText.match(/\\{\\{|\\}\\}/g) || []).length,
    dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length};
}'''


def email_page(values):
    src = open(EMAIL, encoding='utf-8').read()
    return re.sub(r'\{\{([a-z_]+)\}\}', lambda m: html.escape(values[m.group(1)], quote=True), src)


problems = []
counts = {'screens': 0, 'card': 0, 'email': 0, 'showcase': 0}
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
                    counts['screens'] += 1
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
                    shot = (theme == 'light' and layout == 'split') or key in ('login', 'setpass', 'done', 'pin', 'card')
                    if shot:
                        pg.wait_for_timeout(900 if key == 'done' else 150)
                        pg.screenshot(path=os.path.join(OUT, f'{tag}-{theme}-{layout}-{key}.png'))

            # GG ID card on its screen (minimal layout = the plain column of the hub): demo, long and empty data
            for data_name, data in (('demo', None), ('long', LONG), ('empty', EMPTY)):
                errs.clear()
                pg.goto('file://' + os.path.join(SCREENS, 'card.html') + '?layout=minimal')
                pg.wait_for_timeout(250)
                if data:
                    pg.evaluate('(d) => GGID.card(document.querySelector(".gid-idcard"), d)', data)
                r = pg.evaluate(CARD_PROBE, '.gid-idcard')
                counts['card'] += 1
                label = f'card/{tag}/{theme}/{data_name}'
                c = r['cards'][0]
                if r['scrollW'] > r['clientW']:
                    problems.append(f'{label}: horizontal scroll {r["scrollW"]} > {r["clientW"]}')
                if c['outside']:
                    problems.append(f'{label}: outside the card padding {c["outside"]}')
                if not r['fontOk'] or 'Montserrat' not in c['font']:
                    problems.append(f'{label}: font {c["font"]}')
                if r['dashes']:
                    problems.append(f'{label}: dashes in text {r["dashes"]}')
                if errs:
                    problems.append(f'{label}: console {errs[:3]}')
                if c['tnum'] is not True:
                    problems.append(f'{label}: digits of the GG ID number are not monospaced')
                expect_accents = [] if data_name == 'empty' else ['gid-idcard-status::before']
                if c['accents'] != expect_accents:
                    problems.append(f'{label}: accent colour on {c["accents"]}, expected {expect_accents}')
                if c['h'] < c['w'] / RATIO - 1:
                    problems.append(f'{label}: card shorter than 85.6 x 54 ({c["w"]:.0f}x{c["h"]:.0f})')
                if data_name == 'demo' and tag == 'desktop' and abs(c['ratio'] - RATIO) > 0.01:
                    problems.append(f'{label}: proportions {c["ratio"]:.3f}, a real card is {RATIO:.3f}')
                if tag == 'phone' and c['w'] < c['parentW'] - c['parentPad'] - 1:
                    problems.append(f'{label}: not full width on the phone ({c["w"]:.0f} of {c["parentW"]:.0f})')
                if data_name == 'long':
                    if pg.evaluate('document.querySelectorAll(".gid-idcard-roles li").length') != 3:
                        problems.append(f'{label}: three positions expected')
                if data_name == 'empty':
                    hid = pg.evaluate('[...document.querySelectorAll(\'[data-gid-field="positions"],[data-gid-field="passkey"]\')].map(e => getComputedStyle(e).display)')
                    if hid != ['none', 'none']:
                        problems.append(f'{label}: empty positions and passkey must be hidden ({hid})')
                pg.locator('.gid-idcard').screenshot(path=os.path.join(OUT, f'card-{tag}-{theme}-{data_name}.png'))
            # GGID.card never parses markup from the data
            pg.evaluate('() => GGID.card(document.querySelector(".gid-idcard"), {name: "<img src=x onerror=alert(1)>", positions: ["<b>x</b>"], email: "a<i>@global-generations.com", id: "<s>", since: "<u>"})')
            if pg.evaluate('document.querySelector(".gid-idcard").querySelectorAll("img,b,i,s,u").length'):
                problems.append(f'card/{tag}/{theme}: GGID.card inserted markup from data')
            ctx.close()

    # e-mail card: 600 and 375 px; light, dark (Apple Mail honours color-scheme), inverted (Gmail on iPhone)
    for vw, vh, tag in [(600, 900, 'wide'), (375, 812, 'phone')]:
        for mode in ('light', 'dark', 'gmail-ios'):
            for data_name, data in (('demo', EMAIL_DEMO), ('long', EMAIL_LONG)):
                ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2,
                                    color_scheme='dark' if mode == 'dark' else 'light')
                pg = ctx.new_page()
                errs = []
                pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
                pg.route(EMAIL_PNG_URL, lambda route: route.fulfill(path=EMAIL_PNG, content_type='image/png'))
                pg.route(re.compile(r'^https?://(?!levauth\.global-generations-edu\.com/assets/gg-id/email/).*'),
                         lambda route: (errs.append(f'network: {route.request.url}'), route.abort()))
                pg.set_content(email_page(data), wait_until='load')
                if mode == 'gmail-ios':
                    pg.evaluate(INVERT)
                r = pg.evaluate(CONTRAST)
                counts['email'] += 1
                label = f'email/{tag}/{mode}/{data_name}'
                if r['scrollW'] > r['clientW']:
                    problems.append(f'{label}: horizontal scroll {r["scrollW"]} > {r["clientW"]}')
                if r['low']:
                    problems.append(f'{label}: low contrast {r["low"][:4]}')
                if not r['img']:
                    problems.append(f'{label}: lockup image did not load')
                if mode == 'gmail-ios' and r['plate'] < 3:     # inverted card: the navy plate keeps the white logo readable
                    problems.append(f'{label}: lockup plate lost on the inverted card ({r["plate"]:.2f})')
                if mode != 'gmail-ios' and r['plate'] > 1.05:  # normal card: the plate is the card colour, no visible box
                    problems.append(f'{label}: lockup plate differs from the card colour ({r["plate"]:.2f})')
                if mode == 'dark' and r['bodyLum'] > 0.1:
                    problems.append(f'{label}: light page around the card in dark mode (luminance {r["bodyLum"]:.2f})')
                if r['left']:
                    problems.append(f'{label}: placeholders left in text')
                if r['dashes']:
                    problems.append(f'{label}: dashes {r["dashes"]}')
                if r['cardW'] > 440.5:
                    problems.append(f'{label}: card wider than 440 px ({r["cardW"]})')
                if errs:
                    problems.append(f'{label}: console {errs[:3]}')
                if data_name == 'demo':
                    pg.screenshot(path=os.path.join(OUT, f'email-{tag}-{mode}.png'), full_page=True)
                    pg.locator('.gidm-card').screenshot(path=os.path.join(OUT, f'email-{tag}-{mode}-card.png'))
                ctx.close()

    # showcase: page width, all modes render, console clean
    for vw, vh, tag in [(1440, 900, 'desktop'), (390, 844, 'phone')]:
        ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2 if vw < 500 else 1)
        pg = ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        for h in ('s=login&l=split&t=light&d=desktop', 's=setpass&l=card&t=dark&d=phone', 's=login&l=minimal&t=light&d=all',
                  's=error&l=split&t=dark&d=desktop', 's=card&l=split&t=light&d=desktop', 's=card&l=minimal&t=dark&d=phone'):
            pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#' + h)
            pg.reload()
            pg.wait_for_timeout(700)
            r = pg.evaluate('''() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
              gids: document.querySelectorAll('#stage .gid').length, thumbs: document.querySelectorAll('.sc-thumb').length,
              tabs: document.querySelectorAll('.sc-tab').length, rows: document.querySelectorAll('.sc-api tbody tr').length,
              idcard: document.querySelectorAll('#stage .gid-idcard').length,
              dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length})''')
            counts['showcase'] += 1
            label = f'showcase/{tag}/{h}'
            if r['sw'] > r['cw']:
                problems.append(f'{label}: horizontal scroll {r["sw"]} > {r["cw"]}')
            if r['gids'] < 1 or r['tabs'] < 18 or r['rows'] < 18:
                problems.append(f'{label}: not rendered {r}')
            if h.startswith('s=card') and r['idcard'] != 1:
                problems.append(f'{label}: the card screen did not open ({r["idcard"]} cards on stage)')
            if r['dashes']:
                problems.append(f'{label}: dashes {r["dashes"]}')
            pg.screenshot(path=os.path.join(OUT, f'showcase-{tag}-{h.split("&")[0][2:]}-{h.split("&")[3][2:]}.png'),
                          full_page=(h.endswith('d=all')))
        # section «Карточка GG ID»: cards and rows inside their padding, the e-mail preview loaded and fitted
        r = pg.evaluate(CARD_PROBE, '#idcard .gid-idcard')
        counts['showcase'] += 1
        for i, c in enumerate(r['cards']):
            if c['outside']:
                problems.append(f'showcase/{tag}/idcard {i}: outside the card padding {c["outside"]}')
            if c['accents'] != ['gid-idcard-status::before']:
                problems.append(f'showcase/{tag}/idcard {i}: accent colour on {c["accents"]}')
        rows = pg.evaluate('''() => [...document.querySelectorAll('#idcard .gid-idrow')].map(row => { const r = row.getBoundingClientRect();
            return [...row.querySelectorAll('*')].filter(e => { const q = e.getBoundingClientRect(); return q.width && (q.right > r.right + 1 || q.left < r.left - 1); }).length; })''')
        if len(rows) != 2 or any(rows):
            problems.append(f'showcase/{tag}: compact rows {rows}')
        mail = pg.evaluate('''() => { const f = document.getElementById('mailFrame'), d = f.contentDocument;
            return {card: !!(d && d.querySelector('.gidm-card')), fit: d ? f.getBoundingClientRect().height - d.body.offsetHeight : -1}; }''')
        if not mail['card'] or abs(mail['fit']) > 2:
            problems.append(f'showcase/{tag}: e-mail preview {mail}')
        if r['cards'] and len(r['cards']) != 3:
            problems.append(f'showcase/{tag}: 3 cards expected in the section, got {len(r["cards"])}')
        pg.locator('#idcard').screenshot(path=os.path.join(OUT, f'showcase-{tag}-idcard-section.png'))
        for i in (0, 1):
            pg.locator('#idcard .sc-idc').nth(i).screenshot(path=os.path.join(OUT, f'showcase-{tag}-idcard-row{i + 1}.png'))
        # the link in the section opens the card screen in the stage
        pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#s=login&l=split&t=light&d=desktop')
        pg.reload()
        pg.wait_for_timeout(400)
        pg.click('#toCard')
        pg.wait_for_timeout(300)
        if pg.evaluate('document.querySelectorAll("#stage .gid-idcard").length') != 1:
            problems.append(f'showcase/{tag}: the link in «Карточка GG ID» did not open the card screen')
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

summary = (f'{counts["screens"]} screen renders, {counts["card"]} card renders, {counts["email"]} e-mail renders, '
           f'{counts["showcase"]} showcase states')
if problems:
    print('GG ID CHECK FAILED', '|', summary)
    for x in problems:
        print(' -', x)
    sys.exit(1)
print('ok:', summary, '| shots in', OUT)

if '--preview' in sys.argv:   # pictures for gg-id/README.md and the PR, only after a green run
    PREVIEW = os.path.join(ROOT, 'gg-id', 'preview')
    os.makedirs(PREVIEW, exist_ok=True)
    for src_name, dst_name in [('showcase-desktop-idcard-row1.png', 'card-light-dark.png'),
                               ('showcase-desktop-idcard-row2.png', 'card-long-and-row.png'),
                               ('card-phone-light-demo.png', 'card-phone.png'),
                               ('email-wide-light-card.png', 'email-light.png'),
                               ('email-wide-gmail-ios-card.png', 'email-gmail-ios-dark.png')]:
        shutil.copyfile(os.path.join(OUT, src_name), os.path.join(PREVIEW, dst_name))
    print('preview pictures in', PREVIEW)
