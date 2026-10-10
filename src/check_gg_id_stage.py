"""GG ID kit: the scene of the sign-in screen, gg-id/gg-id-stage.css (rule of Lev, 10.10.2026: «после первого клика экран меняется, фон и геометрия ломаются»).

One geometry of the sign-in screen for the hub, the gates and every GG service: on a computer the title stands at y = max(28 px, (window height - 560 px) / 2)
whatever the view and whatever the service, the card and the panel and the background do not move, the footer (two lines, with the link «Как войти: инструкция»)
is pressed to the bottom of the window. The file is a contract: every service keeps a copy byte for byte and checks the sha256 in its own tests.

Static part (no browser, runs in CI):  python3 src/check_gg_id_stage.py
  1. gg-id/gg-id-stage.css is the file of the contract: size, sha256 (the same constant is pinned in src/build_gg_id.py and written in gg-id/README.md), the rules of the contract;
  2. every page gg-id/screens/*.html links gg-id.css and, right after it and last, gg-id-stage.css; the page has no own rule that moves the card (margin-block:auto, a margin,
     animation on .gid-card; padding-top on .gid-main; background or scrollbar-gutter on html); the showcase gg-id.html carries the file as is, after the kit CSS and before its own rules;
  3. markup: .gid > .gid-frame > aside + main.gid-main > (section.gid-card + footer.gid-foot), the card and the footer are DIRECT children of the main; the footer has two lines:
     the caption and the link «Как войти: инструкция» to https://id.global-generations-edu.com/instructions/;
  4. gg-id.css does not know the scene (the pinned copies of the kit in the services stay as they are; the scene lives in one file).
Browser part (--browser, Chromium, also runs inside src/check_gg_id.py):
  5. the five screens login, password, forgot, error, noaccess in the four windows of the contract, light and dark: the title stands on the formula and on the same y on every
     screen (the jump between screens is 0 px), the card, the panel and the first line of the footer stand on the numbers of the sign-in page of the hub (1 px), html has
     the gutter and the background from 975 px, the card has no animation, the hint of the e-mail field is out of the flow; the other screens in 1440 x 900;
  6. the showcase: switching the tabs changes the screen in place, the title does not move inside the frame; the scene does not paint the html of the showcase;
  7. the rules on html live only while there is a split sign-in screen on the page (a single page app that keeps the kit in its bundle gets its html back after the sign-in).
Run: uv run --with playwright python src/check_gg_id_stage.py --browser
"""
import hashlib
import html as htmlmod
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'gg-id')
SCREENS = os.path.join(KIT, 'screens')
STAGE_FILE = 'gg-id-stage.css'
STAGE_SHA256 = '451ecc726041580570e0d11c6951c271519ae734fddeeee44d650044e65ffbf0'   # the same in src/build_gg_id.py and gg-id/README.md: a new file needs all three
STAGE_BYTES = 6811
GUIDE_URL = 'https://id.global-generations-edu.com/instructions/'

# The sign-in page of the hub, measured in headless Chromium (tolerance 1 px): window -> title y, card x, card width, panel width, first line of the footer y.
# Desktop: title y = max(28, (H - 560) / 2); panel = client width x 1.08 / 2.08; the card (384) is centred in the rest; the footer of two lines ends 22 px above the bottom.
# Phone (390 x 844): the panel is a strip 390 x 90, the title stands on 110, the card is 16 px from the edge; the footer ends 18 px above the bottom.
CONTRACT = {
    (1440, 900): {'h1': 170, 'card_x': 901.84, 'card_w': 384, 'aside_w': 747.69, 'foot1': 825.75},
    (1280, 720): {'h1': 80, 'card_x': 780.30, 'card_w': 384, 'aside_w': 664.61, 'foot1': 645.75},
    (1920, 1080): {'h1': 260, 'card_x': 1266.45, 'card_w': 384, 'aside_w': 996.92, 'foot1': 1005.75},
    (390, 844): {'h1': 110, 'card_x': 16, 'card_w': 358, 'aside_w': 390, 'aside_h': 90, 'foot1': 773.75},
}
TOL = 1.0
SCREENS5 = ('login', 'password', 'forgot', 'error', 'noaccess')
GUTTER_FROM = 975          # from this window width html keeps the place of the scroll bar and gets the colour of the column
DARK_BG = 'rgb(10, 31, 44)'
LIGHT_BG = 'rgb(255, 255, 255)'
TRANSPARENT = 'rgba(0, 0, 0, 0)'
SHOWCASE_RULES = '/* ---------- витрина ---------- */'

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.children, self.text = tag, attrs, parent, [], []

    def classes(self):
        return set((self.attrs.get('class') or '').split())

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def inner_text(self):
        return ''.join(self.text) + ''.join(c.inner_text() for c in self.children)


class Tree(HTMLParser):
    """A small tolerant DOM: enough to ask who is a direct child of whom in the generated pages."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root', {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, dict(attrs), self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, dict(attrs), self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.text.append(data)


def parse(text):
    t = Tree()
    t.feed(text)
    t.close()
    return t.root


def scene_conflicts(css, strict):
    """Rules in `css` (what a page adds after the scene) that would move the card again. strict: also the padding of .gid-main and the paint of html (a sign-in page of a service
    has none; the showcase has two documented ones)."""
    found = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel, decls = m.group(1).strip(), m.group(2)
        for s in (x.strip() for x in sel.split(',')):
            if '.gid-card' in s and re.search(r'(^|;)\s*(margin|margin-block(-start|-end)?|margin-(top|bottom)|animation(-name)?)\s*:', decls):
                found.append(f'{s}{{{decls.strip()[:60]}}}: moves or animates the card')
            if strict and '.gid-main' in s and re.search(r'(^|;)\s*padding(-block(-start)?|-top)?\s*:', decls):
                found.append(f'{s}{{{decls.strip()[:60]}}}: own top of the column')
            if strict and re.match(r'^html\b', s) and re.search(r'(^|;)\s*(background(-color)?|scrollbar-gutter)\s*:', decls):
                found.append(f'{s}{{{decls.strip()[:60]}}}: own paint or gutter of html')
    return found


def expected(w, h, cw):
    """The numbers of the contract; on a desktop with a classic scroll bar (the scene keeps its place from 975 px) the widths follow the client width."""
    c = dict(CONTRACT[(w, h)])
    if w >= GUTTER_FROM and abs(cw - w) > 0.5:
        aside = cw * 1.08 / 2.08
        c['aside_w'], c['card_x'] = aside, aside + (cw - aside - 384) / 2
    return c


def static(problems, counts):
    counts.setdefault('stage', 0)

    def ok(name, cond, got=None):
        counts['stage'] += 1
        if not cond:
            problems.append(f'stage: {name}' + (f' (got {str(got)[:200]})' if got is not None else ''))

    # ---- 1. the file of the contract ----
    path = os.path.join(KIT, STAGE_FILE)
    raw = open(path, 'rb').read() if os.path.exists(path) else b''
    ok(f'gg-id/{STAGE_FILE} exists and is {STAGE_BYTES} bytes', len(raw) == STAGE_BYTES, len(raw))
    ok(f'gg-id/{STAGE_FILE} sha256 is the one of the contract (a new file = new sha256 here, in src/build_gg_id.py, in gg-id/README.md and in every copy)',
       hashlib.sha256(raw).hexdigest() == STAGE_SHA256, hashlib.sha256(raw).hexdigest())
    stage = raw.decode('utf-8', 'replace')
    for rule in ('.gid[data-layout="split"] .gid-main > .gid-card{animation:none}',
                 '.gid-label-row > .gid-hint{position:absolute;right:0;bottom:0;',
                 'html:has(.gid[data-layout="split"]){scrollbar-gutter:stable;background:#ffffff}',
                 'html:has(.gid[data-layout="split"]){background:#0a1f2c}',
                 '@container gid (min-width:960px){',
                 'padding-top:max(28px,calc((100vh - 560px) / 2));padding-top:max(28px,calc((100dvh - 560px) / 2))',
                 '.gid[data-layout="split"] .gid-main > .gid-card{margin-block:0 28px}',
                 '.gid[data-layout="split"] .gid-main > .gid-foot{margin-top:auto}',
                 '@keyframes gidStageFade'):
        ok(f'the scene carries «{rule[:70]}»', rule in stage)
    ok('the scene has no dashes and no external addresses', not re.search('[\u2013\u2014]|https?://|@import', stage))
    build = open(os.path.join(ROOT, 'src', 'build_gg_id.py'), encoding='utf-8').read()
    ok('src/build_gg_id.py pins the same sha256', re.findall(r"STAGE_SHA256 = '([0-9a-f]{64})'", build) == [STAGE_SHA256])
    readme = open(os.path.join(KIT, 'README.md'), encoding='utf-8').read()
    ok('gg-id/README.md names the file and its sha256 in «Сцена экрана входа»', '## Сцена экрана входа' in readme and STAGE_SHA256 in readme)
    kit_css = open(os.path.join(KIT, 'gg-id.css'), encoding='utf-8').read()
    ok('gg-id.css does not know the scene: the pinned copies of the kit in the services stay as they are', 'gidStageFade' not in kit_css and 'scrollbar-gutter' not in kit_css)
    # the numbers of the contract follow the formulas (a typo in a constant would pass the browser part on one machine and fail on another)
    for (w, h), c in CONTRACT.items():
        if w >= 960:
            aside = round(w * 1.08 / 2.08, 2)
            ok(f'contract {w}x{h}: title y is max(28, (H - 560) / 2)', abs(c['h1'] - max(28, (h - 560) / 2)) < 0.01, c['h1'])
            ok(f'contract {w}x{h}: panel is 1.08 / 2.08 of the width', abs(c['aside_w'] - aside) < 0.01, c['aside_w'])
            ok(f'contract {w}x{h}: the card (384) is centred in the column', abs(c['card_x'] - round(aside + (w - aside - 384) / 2, 2)) < 0.02, c['card_x'])
            ok(f'contract {w}x{h}: the footer of two lines ends 22 px above the bottom', abs(c['foot1'] - (h - 74.25)) < 0.01, c['foot1'])
        else:
            ok(f'contract {w}x{h}: the card is the width of the column minus 2 x 16', c['card_x'] == 16 and c['card_w'] == w - 32, c)
            ok(f'contract {w}x{h}: the footer of two lines ends 18 px above the bottom', abs(c['foot1'] - (h - 70.25)) < 0.01, c['foot1'])

    # ---- 2, 3. the pages ----
    pages = sorted(n for n in os.listdir(SCREENS) if n.endswith('.html'))
    ok('screens/ has the pages', len(pages) >= 15, len(pages))
    for name in pages:
        text = open(os.path.join(SCREENS, name), encoding='utf-8').read()
        tree = parse(text)
        links = [n.attrs.get('href') for n in tree.walk() if n.tag == 'link' and n.attrs.get('rel') == 'stylesheet']
        ok(f'screens/{name}: stylesheets are gg-id.css, then gg-id-stage.css and nothing after it', links == ['../gg-id.css', '../' + STAGE_FILE], links)
        own = '\n'.join(''.join(n.text) for n in tree.walk() if n.tag == 'style')
        ok(f'screens/{name}: no own rule that moves the card, the column or html', not scene_conflicts(own, True), scene_conflicts(own, True))
        gid = [n for n in tree.walk() if n.tag == 'div' and 'gid' in n.classes()]
        ok(f'screens/{name}: one .gid, layout split', len(gid) == 1 and gid[0].attrs.get('data-layout') == 'split', [g.attrs for g in gid])
        mains = [n for n in tree.walk() if n.tag == 'main' and 'gid-main' in n.classes()]
        ok(f'screens/{name}: one main.gid-main', len(mains) == 1)
        if len(mains) != 1:
            continue
        kids = mains[0].children
        ok(f'screens/{name}: the card and the footer are the direct children of .gid-main, in this order',
           len(kids) == 2 and kids[0].tag == 'section' and 'gid-card' in kids[0].classes() and kids[1].tag == 'footer' and 'gid-foot' in kids[1].classes(),
           [(k.tag, sorted(k.classes())) for k in kids])
        foot = next((k for k in kids if k.tag == 'footer'), None)
        if foot is None:
            continue
        parts = [k.tag for k in foot.children]
        ok(f'screens/{name}: the footer has the caption and the link, two lines', parts == ['span', 'a'], parts)
        a = next((k for k in foot.children if k.tag == 'a'), None)
        if a is not None:
            ok(f'screens/{name}: the footer link goes to the instruction, in a new tab, with noopener',
               a.attrs.get('href') == GUIDE_URL and a.attrs.get('target') == '_blank' and 'noopener' in (a.attrs.get('rel') or ''), a.attrs)
            ok(f'screens/{name}: the footer link says «Как войти: инструкция»', 'Как войти: инструкция' in htmlmod.unescape(a.inner_text()), a.inner_text())
            ok(f'screens/{name}: the footer link has the book of the sprite', any(n.tag == 'use' and n.attrs.get('href') == '#gi-book-open' for n in a.walk()))

    # ---- 2. the showcase carries the file as it is ----
    showcase = open(os.path.join(ROOT, 'gg-id.html'), encoding='utf-8').read()
    first_line = kit_css.split('\n', 1)[0]
    at_kit, at_stage, at_own = showcase.find(first_line), showcase.find(stage), showcase.find(SHOWCASE_RULES)
    ok('gg-id.html carries gg-id-stage.css once, as it is', showcase.count(stage) == 1 and stage != '')
    ok('gg-id.html: the kit CSS, then the scene, then the rules of the showcase', 0 <= at_kit < at_stage < at_own, (at_kit, at_stage, at_own))
    if 0 <= at_stage < at_own:
        own = showcase[at_own:showcase.find('</style>', at_own)]
        ok('gg-id.html: the rules of the showcase do not move or animate the card', not scene_conflicts(own, False), scene_conflicts(own, False))


# ---- the browser part ----
READ = '''() => {
  const r = (el) => { if (!el) return null; const b = el.getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height }; };
  const cs = (el, p) => (el ? getComputedStyle(el)[p] : null);
  const card = document.querySelector('.gid-card'), de = document.documentElement, foot = document.querySelector('.gid-foot'), main = document.querySelector('.gid-main');
  const h1 = card && card.querySelector('h1,.gid-h');
  return { h1: r(h1), card: r(card), aside: r(document.querySelector('.gid-aside')), foot: r(foot), footFirst: r(foot && foot.firstElementChild), link: r(foot && foot.querySelector('a')),
    cw: de.clientWidth, over: de.scrollWidth - de.clientWidth, scrollH: de.scrollHeight, innerH: window.innerHeight,
    gutter: cs(de, 'scrollbarGutter'), htmlBg: cs(de, 'backgroundColor'), cardAnim: cs(card, 'animationName'), mainAnim: cs(main, 'animationName'),
    hint: [...document.querySelectorAll('.gid-label-row > .gid-hint')].map((e) => cs(e, 'position')) };
}'''
HTML_PAINT = '''() => { const cs = getComputedStyle(document.documentElement); return [cs.scrollbarGutter, cs.backgroundColor]; }'''
SHOWCASE_READ = '''() => {
  const scr = document.querySelector('.sc-screen'); if (!scr) return null;
  const s = scr.getBoundingClientRect().width / 1280, h1 = scr.querySelector('.gid-card h1,.gid-card .gid-h'), top = scr.getBoundingClientRect().top;
  const card = scr.querySelector('.gid-card'), aside = scr.querySelector('.gid-aside');
  return { scale: s, h1: h1 ? (h1.getBoundingClientRect().top - top) / s : null, cardX: card ? (card.getBoundingClientRect().left - scr.getBoundingClientRect().left) / s : null,
    asideW: aside ? aside.getBoundingClientRect().width / s : null, key: card && card.getAttribute('data-gid-screen') };
}'''


def browser(b, problems, counts):
    counts.setdefault('stage', 0)

    def ok(name, cond, got=None):
        counts['stage'] += 1
        if not cond:
            problems.append(f'stage: {name}' + (f' (got {str(got)[:240]})' if got is not None else ''))

    def near(name, got, want, tol=TOL):
        ok(name, got is not None and abs(got - want) <= tol, f'{got}, expected {want}')

    def load(pg, key):
        pg.goto('file://' + os.path.join(SCREENS, key + '.html') + '?layout=split')
        pg.evaluate('async () => { await document.fonts.ready; return true; }')
        pg.wait_for_timeout(120)
        return pg.evaluate(READ)

    # ---- 5. the five screens in the four windows, light and dark ----
    for scheme in ('light', 'dark'):
        for (w, h), c0 in CONTRACT.items():
            ctx = b.new_context(viewport={'width': w, 'height': h}, color_scheme=scheme, locale='ru-RU', reduced_motion='reduce')
            pg = ctx.new_page()
            errs = []
            pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
            rows = {key: load(pg, key) for key in SCREENS5}
            tag = f'{scheme} {w}x{h}'
            for key, r in rows.items():
                t = f'{tag} [{key}]'
                c = expected(w, h, r['cw'])
                near(f'title y {t}', r['h1']['y'], c['h1'])
                near(f'card x {t}', r['card']['x'], c['card_x'])
                near(f'card width {t}', r['card']['w'], c['card_w'])
                near(f'panel width {t}', r['aside']['w'], c['aside_w'])
                if 'aside_h' in c:
                    near(f'panel strip height {t}', r['aside']['h'], c['aside_h'])
                ok(f'no horizontal scroll {t}', r['over'] <= 0, r['over'])
                ok(f'the card has no animation {t}', r['cardAnim'] == 'none', r['cardAnim'])
                ok(f'the footer is two lines: the link under the caption {t}', r['link'] is not None and r['link']['y'] > r['footFirst']['y'] + 10, [r['footFirst'], r['link']])
                if r['scrollH'] <= r['innerH'] + 0.5:       # a view taller than the window grows downwards and scrolls: the footer follows it
                    near(f'first line of the footer {t}', r['footFirst']['y'], c['foot1'])
                gut, bg = r['gutter'], r['htmlBg']
                if w >= GUTTER_FROM:
                    ok(f'html keeps the place of the scroll bar {t}', gut == 'stable', gut)
                    ok(f'html has the colour of the column {t}', bg == (DARK_BG if scheme == 'dark' else LIGHT_BG), bg)
                else:
                    ok(f'html is left alone on a phone {t}', gut == 'auto' and bg == TRANSPARENT, [gut, bg])
                if key in ('password', 'forgot'):
                    ok(f'the hint of the e-mail field is out of the flow, in the row of the caption {t}', r['hint'] == ['absolute'], r['hint'])
            ys = [r['h1']['y'] for r in rows.values()]
            ok(f'the title does not move between the screens {tag} (spread {max(ys) - min(ys):.2f} px)', max(ys) - min(ys) <= 0.5, ys)
            xs = [(r['card']['x'], r['card']['w'], r['aside']['w']) for r in rows.values()]
            ok(f'the card and the panel do not move between the screens {tag}', all(max(abs(a - b2) for a, b2 in zip(x, xs[0])) <= 0.5 for x in xs), xs)
            ok(f'console and exceptions clean {tag}', not errs, errs[:3])
            ctx.close()

    # the other screens: the title is the first thing of the card on all of them but «Готово» (the sign of the brand stands above its title)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme='light', locale='ru-RU', reduced_motion='reduce')
    pg = ctx.new_page()
    others = sorted(n[:-5] for n in os.listdir(SCREENS) if n.endswith('.html') and n[:-5] not in SCREENS5 and n[:-5] != 'done')
    for key in others:
        r = load(pg, key)
        near(f'1440x900 [{key}] title y', r['h1']['y'], 170)
        near(f'1440x900 [{key}] card x', r['card']['x'], 901.84)
    ctx.close()

    # ---- 5b. the fade of the right column opens the page once, unless the person asks for less motion ----
    for motion, want in (('no-preference', 'gidStageFade'), ('reduce', 'none')):
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion=motion)
        pg = ctx.new_page()
        r = load(pg, 'password')
        ok(f'the right column fades in once with motion «{motion}»', r['mainAnim'] == want and r['cardAnim'] == 'none', [r['mainAnim'], r['cardAnim']])
        ctx.close()

    # ---- 6. the showcase: the tabs change the screen in place ----
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme='light', locale='ru-RU', reduced_motion='reduce')
    pg = ctx.new_page()
    errs = []
    pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
    pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#s=login&l=split&t=light&d=desktop')
    pg.reload()
    pg.wait_for_timeout(500)
    seen = []
    for key in SCREENS5:
        pg.click(f'.sc-tab[data-key="{key}"]')
        pg.wait_for_timeout(120)
        seen.append(pg.evaluate(SHOWCASE_READ))
    ok('showcase: every tab shows its screen', [s and s['key'] for s in seen] == list(SCREENS5), [s and s['key'] for s in seen])
    ys = [s['h1'] for s in seen if s]
    near('showcase: the title stands on (frame height - 560) / 2 = 120 px inside the frame 1280 x 800', ys[0], 120, 1.5)
    ok(f'showcase: the title does not move between the tabs (spread {max(ys) - min(ys):.2f} px)', max(ys) - min(ys) <= 0.5, ys)
    ok('showcase: the card and the panel do not move between the tabs', len({(round(s['cardX'], 1), round(s['asideW'], 1)) for s in seen}) == 1, [(s['cardX'], s['asideW']) for s in seen])
    gut, bg = pg.evaluate(HTML_PAINT)
    ok('showcase: the scene does not paint the html of the page and does not keep a place for a scroll bar', gut == 'auto' and bg == TRANSPARENT, [gut, bg])
    ok('showcase: console and exceptions clean', not errs, errs[:3])
    ctx.close()

    # ---- 7. the rules on html live only while there is a split sign-in screen on the page ----
    kit = re.sub(r'url\(fonts/[^)]*\)', 'url(data:,)', open(os.path.join(KIT, 'gg-id.css'), encoding='utf-8').read())
    stage = open(os.path.join(KIT, STAGE_FILE), encoding='utf-8').read()
    shell = lambda layout: ('<div class="gid" data-layout="' + layout + '"><div class="gid-frame"><main class="gid-main"><section class="gid-card"><h1>x</h1></section></main></div></div>')
    for scheme, bg in (('light', LIGHT_BG), ('dark', DARK_BG)):
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme=scheme)
        pg = ctx.new_page()
        pg.set_content('<!doctype html><html><head><meta charset="utf-8"><style>' + kit + '</style><style>' + stage + '</style></head><body><div id="app"><p>app shell</p></div></body></html>')
        ok(f'{scheme}: an app shell without a sign-in screen keeps its html', pg.evaluate(HTML_PAINT) == ['auto', TRANSPARENT], pg.evaluate(HTML_PAINT))
        pg.evaluate('(h) => { document.getElementById("app").innerHTML = h; }', shell('split'))
        ok(f'{scheme}: the split sign-in screen mounted: the gutter and the colour of the column', pg.evaluate(HTML_PAINT) == ['stable', bg], pg.evaluate(HTML_PAINT))
        pg.evaluate('() => { document.getElementById("app").innerHTML = "<p>signed in</p>"; }')
        ok(f'{scheme}: after the sign-in the html is back', pg.evaluate(HTML_PAINT) == ['auto', TRANSPARENT], pg.evaluate(HTML_PAINT))
        for layout in ('card', 'minimal'):
            pg.evaluate('(h) => { document.getElementById("app").innerHTML = h; }', shell(layout))
            ok(f'{scheme}: the {layout} layout is not touched', pg.evaluate(HTML_PAINT) == ['auto', TRANSPARENT], pg.evaluate(HTML_PAINT))
        pg.set_viewport_size({'width': 800, 'height': 900})
        pg.evaluate('(h) => { document.getElementById("app").innerHTML = h; }', shell('split'))
        ok(f'{scheme}: under 975 px the html is left alone', pg.evaluate(HTML_PAINT) == ['auto', TRANSPARENT], pg.evaluate(HTML_PAINT))
        ctx.close()


def run(b, problems, counts):
    """From src/check_gg_id.py: the static part and the browser part on the Chromium `b`."""
    static(problems, counts)
    try:
        browser(b, problems, counts)
    except Exception as e:      # a crash is one failure, the rest of the check still runs
        counts['stage'] += 1
        problems.append(f'stage: the browser part crashed: {str(e).splitlines()[0][:300] if str(e) else repr(e)}')


if __name__ == '__main__':
    problems, counts = [], {}
    if '--browser' in sys.argv:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            chrome = p.chromium.launch()
            _new_context = chrome.new_context

            def new_context(**kw):
                c = _new_context(**kw)
                c.set_default_timeout(60000)
                c.set_default_navigation_timeout(60000)
                return c
            chrome.new_context = new_context
            run(chrome, problems, counts)
            chrome.close()
    else:
        static(problems, counts)
    if problems:
        print('GG ID STAGE FAILED |', counts.get('stage', 0), 'checks')
        for x in problems:
            print(' -', x)
        sys.exit(1)
    print('ok:', counts.get('stage', 0), 'stage checks' + (' (static and browser)' if '--browser' in sys.argv else ' (static; --browser for the windows)'))
