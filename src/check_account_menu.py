"""Check GG account menu (gg-id/account-menu: GGAccountMenu, the account chip and dropdown of every GG staff service).

What it holds (a failed line names the rule):

* sources: gg-account-menu.css is exactly what src/build_account_menu.py makes from gg-id/gg-id.css (every kit block byte for byte),
  versions agree with gg-id/VERSION, no innerHTML and friends, no storage, no cookies, no external address except the one canonical hub constant
  (the README lists the same addresses), no dashes, no emoji, no side stripes;
* look: the component and the AKB markup of the kit (.gid-acct, .gid-chip, .gid-menu ...) drawn side by side, each by its own stylesheet only:
  every element has the same box and the same computed style (light, dark, dark by the system; the menu also at 390 px);
* behaviour: open and close by mouse, touch and keyboard (Enter, Space, arrows, Home, End, Esc, Tab, click outside), roles and aria-expanded,
  one menu open at a time, the services section (arrows right and left), update, destroy, data attributes, logout (link, POST, callback, event);
* the services list against a real hub-like server on another port (real CORS with the cookie, no stubs of the browser): one request on the first
  open and never again, the cookie goes along, the list is drawn, one click goes into the service, the current service is marked; 401, 403
  without CORS headers, 503, empty, broken JSON, a foreign page, slow answer, no network = "Мои сервисы" is a plain link to the hub cabinet;
* the Apple Wallet badge (the last row of the header block): where it sits, black with the grey outline of Apple's badge and no effects, English text,
  the link to the pass of the hub, the keyboard (not the first stop, reached by the arrow up), the click (the pass is downloaded from the hub with the cookie),
  the device rule of the cabinet (iPhone, iPad, Safari on a Mac; wallet true and false override it), walletUrl, walletImage, 390 px, dark;
* the kit defaults: no hubOrigin = the production hub, every address of the menu is the canonical one (requested without leaving the machine: the
  context answers for the hub), hubOrigin false = no hub addresses, a page of the hub itself signs out through the hub (POST /api/auth/logout, then its sign-in page);
* the photo of the person (option photo, kit 2026-10-15.3): an address draws the picture in the chip and in the head of the card and asks nothing, false draws the initials and asks
  nothing, not said asks the hub once per person (real CORS with the cookie, GET /api/auth/card) and takes `photo`; every refusal of the hub is silent; addresses that are not an https address
  or an own path are dropped (data:, javascript:, http:, //host, a slash followed by a backslash, a tab, a space, a quote, < >, a backslash, over 500 characters) and nothing runs or leaves the machine; a picture that does not
  load gives the initials back; a repeated update of the same person asks nothing, another person asks once; the circle keeps its size; the picture fills the whole round shape (pixels), in both themes;
* safety: names, e-mail and titles with markup stay text, javascript: and data: addresses are dropped, nothing runs;
* 390 px: no horizontal scroll, the round initials chip, the card inside the screen, a long list scrolls inside.

Run: uv run --with playwright python src/check_account_menu.py [--preview]
GGAM_ENGINE=webkit or firefox runs the same in another engine. Screenshots: shots/account-menu/ (GGAM_SHOTS=<dir> puts them elsewhere).
With --preview the pictures of gg-id/account-menu/preview/ are refreshed.
"""
import base64
import datetime
import http.server
import json
import math
import os
import re
import struct
import sys
import threading
import time
import urllib.parse
import zlib

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_account_menu as bam   # noqa: E402

ROOT, KIT, DIR = bam.ROOT, bam.KIT, bam.OUT_DIR
OUT = os.environ.get('GGAM_SHOTS') or os.path.join(ROOT, 'shots', 'account-menu')       # shots/ is not committed
os.makedirs(OUT, exist_ok=True)
HUB_URL = 'https://id.global-generations-edu.com'    # the production hub: the kit default. Never reached from this check (every context blocks it)
ENGINE = os.environ.get('GGAM_ENGINE', 'chromium')

problems = []
counts = {}
# built from code points so that this file holds no dash and no emoji itself
DASHES = re.compile('[' + chr(0x2014) + chr(0x2013) + ']')
EMOJI = re.compile('[' + chr(0x1F000) + '-' + chr(0x1FAFF) + chr(0x2600) + '-' + chr(0x27BF) + chr(0xFE0F) + chr(0x200D) + ']')


def check(group, name, ok, got=None):
    counts[group] = counts.get(group, 0) + 1
    if not ok:
        problems.append(f'{group}: {name}' + (f' ({got})' if got is not None else ''))


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------------------------------------------- sources

def sources():
    js, css, local = read(bam.JS), read(bam.OUT), read(bam.LOCAL)
    kit_css = read(os.path.join(KIT, 'gg-id.css'))
    check('sources', 'gg-account-menu.css is what the kit makes (python3 src/build_account_menu.py)', css == bam.make())
    check('sources', 'versions agree with gg-id/VERSION', not bam.versions_agree(), bam.versions_agree())
    version = read(os.path.join(KIT, 'VERSION')).strip()
    for path in ('gg-id.js', 'gg-id-service.js'):
        check('sources', f'{path} carries the kit version', f"version: '{version}'" in read(os.path.join(KIT, path)))
    check('sources', 'gg-id.css first line carries the kit version', f'версия {version}' in kit_css.split('\n', 1)[0])
    for title, text in bam.kit_blocks(kit_css):
        check('sources', f'kit block "{title}" is in the css byte for byte', text in css)
    for pat in (r'\binnerHTML\b', r'\bouterHTML\b', r'insertAdjacentHTML', r'document\.write', r'\beval\s*\(', r'new Function', r'XMLHttpRequest',
                r'localStorage', r'sessionStorage', r'indexedDB', r'document\.cookie', r'\.postMessage', r'sendBeacon', r'WebSocket', r'importScripts'):
        check('sources', f'gg-account-menu.js has no {pat}', not re.search(pat, js))
    check('sources', 'gg-account-menu.js makes two kinds of request, both to the hub: GET (one helper: the services list and the card with the photo) and the POST sign-out of a page of the hub itself (same origin, its cookie)',
          len(re.findall(r'\bfetch\(', js)) == 2 and len(re.findall(r"method: 'POST', credentials: 'same-origin'", js)) == 1
          and len(re.findall(r"credentials: 'include', cache: 'no-store'", js)) == 1)
    check('sources', 'the photo is an img made with createElement: alt empty, no-referrer, decoding async, the address only through setAttribute (never markup)',
          all(t in js for t in ("img.setAttribute('alt', '')", "img.setAttribute('referrerpolicy', 'no-referrer')", "img.setAttribute('decoding', 'async')", "img.setAttribute('src', url)")))
    urls = [u for u in re.findall(r'https?://[^\s\'")<>]+', js + css) if u not in ('http://www.w3.org/2000/svg', HUB_URL)]
    check('sources', 'no external address in the js and css (only the svg namespace and the one canonical hub address)', not urls, urls[:3])
    hub_lits = re.findall(r'global-generations[\w.-]*', js + css, re.I)
    check('sources', 'the canonical hub address is written once, in the HUB constant, and nowhere else', hub_lits == ['global-generations-edu.com'] and js.count(HUB_URL) == 1, hub_lits)
    for name, text in (('js', js), ('css', css)):
        check('sources', f'no Aura and no levauth in the {name}', not re.search(r'aura|levauth', text, re.I))
    block = re.search(r'var HUB = \{(.*?)\n  \};', js, re.S)
    hub = dict(re.findall(r"(\w+):\s*'([^']*)'", block.group(1))) if block else {}
    check('sources', 'the HUB constant holds the origin and the seven canonical paths',
          set(hub) == {'origin', 'services', 'profile', 'servicesApi', 'wallet', 'card', 'logout', 'login'} and hub.get('origin') == HUB_URL, hub)
    readme = read(os.path.join(DIR, 'README.md'))
    for k in ('services', 'profile', 'servicesApi', 'wallet', 'card', 'logout'):
        check('sources', f'the README lists the canonical address of {k} ({hub.get("origin", "")}{hub.get(k, "")})', hub.get('origin', '') + hub.get(k, '#') in readme)
    wallet_const = re.search(r'var WALLET = \{[^}]*\};', js)
    check('sources', 'the Apple Wallet badge text is English only (no Cyrillic in the WALLET constant)', bool(wallet_const) and not re.search('[Ѐ-ӿ]', wallet_const.group(0)))
    check('sources', 'no side stripe in the css (border-left)', not re.search(r'border-left\s*:\s*[^;}]*\d', css))
    photo_rules = re.findall(r'[^{}]*\.gam-(?:photo|av--img|av--photo)[^{}]*\{[^}]*\}', re.sub(r'/\*.*?\*/', '', css, flags=re.S))      # the rules, not the comments around them
    check('sources', 'the css of the photo: the img fills the circle (absolute, object-fit cover, round), tokens only, no filter, no shadow but the ring of the avatar',
          len(photo_rules) >= 4 and any('object-fit:cover' in r and 'border-radius:50%' in r and 'position:absolute' in r for r in photo_rules)
          and not any(re.search(r'filter|#[0-9a-fA-F]{3,8}\b|rgb\(', r) for r in photo_rules)
          and all(set(re.findall(r'box-shadow:([^;}]*)', r)) <= {'inset 0 0 0 1px var(--g-avatar-line)'} for r in photo_rules), photo_rules[:2])
    table = set(re.findall(r"^    '([a-z0-9-]+)': \[\[", js, re.M))
    need = {i for _, _, i in SERVICE_BASE} | {i for _, i in GROUPS4}
    check('sources', 'the table of icons holds every icon of the services of the cabinet and of the four groups (the tile of a service is the same in the menu and in the cabinet)',
          need <= table, sorted(need - table))
    check('sources', 'the services panel has no height limit of its own: the js gives it gam-sub--all, the css lifts the limit of the panels (max-height:none, overflow visible)',
          "panelClass: 'gam-sub--all'" in js and '.gam .gam-sub--all{max-height:none;overflow:visible}' in css)
    paths = [bam.JS, bam.OUT, bam.LOCAL, os.path.join(DIR, 'demo.html'), os.path.join(DIR, 'README.md'), bam.__file__, os.path.abspath(__file__)]
    for p in paths:
        if not os.path.exists(p):
            continue
        text = read(p)
        n = os.path.relpath(p, ROOT)
        check('sources', f'{n}: no em dash or en dash', not DASHES.search(text), [text[max(0, m.start() - 20):m.end() + 10] for m in DASHES.finditer(text)][:2])
        check('sources', f'{n}: no emoji', not EMOJI.search(text))


# ---------------------------------------------------------------------------------------------------------------- servers

class Quiet(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def send(self, status, ctype, body, headers=None):
        data = body.encode('utf-8') if isinstance(body, str) else body
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def json(self, status, obj, headers=None):
        self.send(status, 'application/json', json.dumps(obj), headers)


ORIGINS = {}                 # svc, hub, evil -> http://localhost:port
PAGES = {}                   # page id -> html of /app.html?p=<id>
POSTS = []                   # what the service saw on POST /logout
HUB = {'mode': 'ok', 'delay': 0, 'calls': [], 'allowed': set(), 'wallet': [], 'logouts': [],   # calls: the services list; wallet: the pass; logouts: the sign-out of a hub page
       'cards': [], 'card_mode': 'nophoto', 'card_delay': 0, 'card_photo': '/api/auth/avatars/f-1-long-black/face-256.png', 'card_body': None}   # cards: the card with the photo
AVATARS = []                 # the requests for a picture of an avatar (either server): host, path, referer, cookie
TYPES = {'.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.html': 'text/html; charset=utf-8', '.svg': 'image/svg+xml',
         '.woff2': 'font/woff2', '.png': 'image/png', '.json': 'application/json'}


def make_png(width=160, height=80):
    """A picture that is not square on purpose, made on the spot (no binary in the repo): red on the left, green in the middle, blue on the right. The green band (36 to 124 of 160)
    is wider than the part a square circle shows (40 to 120: with object-fit cover only the middle half of a picture twice as wide as it is tall is in view), so a circle that is
    green all over has been filled by the picture and cropped, not squeezed (the red and the blue would show) and not left empty."""
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    band = lambda x: (220, 30, 30) if x < width * 9 // 40 else ((0, 170, 70) if x < width * 31 // 40 else (30, 60, 220))
    row = b'\x00' + b''.join(bytes(band(x)) for x in range(width))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(row * height)) + chunk(b'IEND', b'')


PNG = make_png()


# the services of GG ID with the titles and icons of the cabinet «Мои сервисы» (the hub: cabinet/catalog.js), in the four groups of 15.10.2026
SERVICE_BASE = [
    ('akb', 'АКБ', 'briefcase'), ('mentor-cabinet', 'Кабинет ментора', 'graduation-cap'), ('mentor-report', 'Квартальный отчёт', 'clipboard-list'),
    ('consultation-intake', 'Консультации', 'messages-square'), ('gg-notetaker', 'Notetaker', 'mic'), ('merch-store', 'Мерч', 'shopping-bag'),
    ('hr', 'Найм', 'user-plus'), ('onboarding-hub', 'Онбординг', 'map'),
    ('production', 'Production', 'clapperboard'), ('video-factory', 'Видеофабрика', 'film'), ('ai-teleprompter', 'Телесуфлёр', 'scroll-text'), ('yt', 'YouTube-трекер', 'youtube'),
]
GROUPS4 = [('Product', 'box'), ('Маркетинг', 'trending-up'), ('YouTube', 'play'), ('Infrastructure', 'server')]      # the captions and the icons of the sections of the board
GROUP_SIZES = [6, 2, 4, 1]      # the 13 services of the mock: Product 6, Маркетинг 2, YouTube 4, Infrastructure 1 (the thirteenth)


def services(n=None):
    base = SERVICE_BASE
    out = [{'key': k, 'title': t, 'url': f'{ORIGINS["svc"]}/svc/{k}', 'icon': i} for k, t, i in base]
    while n and len(out) < n:
        k = f'extra-{len(out)}'
        out.append({'key': k, 'title': f'Дополнительный сервис номер {len(out)}', 'url': f'{ORIGINS["svc"]}/svc/{k}', 'icon': 'server'})
    return out


def site_handler():
    class H(Quiet):
        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            path = urllib.parse.unquote(u.path)
            if path == '/app.html':
                pid = urllib.parse.parse_qs(u.query).get('p', ['default'])[0]
                html = PAGES.get(pid, '<!doctype html><title>none</title>')
                return self.send(200, 'text/html; charset=utf-8', html.replace('__HUB__', ORIGINS['hub']).replace('__SVC__', ORIGINS['svc']).replace('__EVIL__', ORIGINS['evil']))
            if path.startswith('/gg-id/') or path.startswith('/src/'):
                full = os.path.normpath(os.path.join(ROOT, path.lstrip('/')))
                if full.startswith(ROOT + os.sep) and os.path.isfile(full):
                    with open(full, 'rb') as f:
                        return self.send(200, TYPES.get(os.path.splitext(full)[1], 'application/octet-stream'), f.read())
                return self.send(404, 'text/plain', 'no')
            if path.startswith('/api/auth/avatars/'):          # the pictures of GG ID: /api/auth/avatars/<code>/face-256.png, open without a login, either server answers
                AVATARS.append({'host': self.headers.get('Host'), 'path': path, 'referer': self.headers.get('Referer'), 'cookie': self.headers.get('Cookie') or '',
                                'dest': self.headers.get('Sec-Fetch-Dest'), 'at': time.time()})
                if 'missing' in path:
                    return self.send(404, 'text/plain', 'no')
                if 'broken' in path:
                    return self.send(200, 'text/plain', 'this is not a picture')
                return self.send(200, 'image/png', PNG, {'Cross-Origin-Resource-Policy': 'cross-origin'})
            if path.startswith('/svc/') or path in ('/cabinet', '/cabinet/', '/profile', '/logout', '/logged-out', '/settings', '/login.html', '/after', '/pass'):
                return self.send(200, 'text/html; charset=utf-8', f'<!doctype html><meta charset="utf-8"><title>{path}</title><p id="here">{path}</p>')
            return self.send(404, 'text/plain', 'no')

        def do_POST(self):
            n = int(self.headers.get('Content-Length') or 0)
            body = self.rfile.read(n).decode('utf-8') if n else ''
            POSTS.append({'path': self.path, 'body': body, 'cookie': self.headers.get('Cookie') or '', 'ctype': self.headers.get('Content-Type') or ''})
            if self.path == '/logout':
                return self.send(303, 'text/plain', '', {'Location': '/logged-out'})
            return self.send(404, 'text/plain', 'no')
    return H


def hub_handler():
    Site = site_handler()       # the hub also serves pages and the kit files like a service does: its own pages (cabinet, admin) carry the menu too

    class H(Site):
        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path == '/api/auth/wallet/apple.pkpass':
                cookie = self.headers.get('Cookie') or ''
                HUB['wallet'].append({'origin': self.headers.get('Origin'), 'cookie': cookie, 'dest': self.headers.get('Sec-Fetch-Dest'), 'at': time.time()})
                if 'gg_portal_session=' not in cookie:
                    return self.json(401, {'error': 'unauthenticated'})
                return self.send(200, 'application/vnd.apple.pkpass', b'PK\x03\x04 a test pass, not a real one', {'Content-Disposition': 'attachment; filename="gg-id.pkpass"'})
            if path == '/api/auth/card':
                return self.card()
            if path != '/api/auth/service-links':
                return Site.do_GET(self)
            origin = self.headers.get('Origin')
            cookie = self.headers.get('Cookie') or ''
            HUB['calls'].append({'origin': origin, 'cookie': cookie, 'accept': self.headers.get('Accept'), 'at': time.time()})
            cors = {}
            if origin:
                if origin not in HUB['allowed']:                               # as the hub: a foreign Origin gets 403 and not one CORS header
                    return self.json(403, {'error': 'bad_origin'}, {'Vary': 'Origin'})
                cors = {'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Credentials': 'true', 'Vary': 'Origin'}
            if HUB['delay']:
                time.sleep(HUB['delay'])
            mode = HUB['mode']
            if 'gg_portal_session=' not in cookie or mode == 'nologin':
                return self.json(401, {'error': 'unauthenticated'}, cors)
            if mode == 'forbidden':
                return self.json(403, {'error': 'forbidden', 'level': None}, cors)
            if mode == 'error':
                return self.json(503, {'error': 'unavailable'}, cors)
            if mode == 'empty':
                return self.json(200, {'services': []}, cors)
            if mode == 'broken':
                return self.send(200, 'application/json', '{"services": [', cors)
            if mode == 'wrong':
                return self.json(200, {'items': 'nope'}, cors)
            if mode == 'no_cors':
                return self.json(200, {'services': services()}, {})
            if mode == 'array':
                return self.json(200, services()[:3], cors)
            if mode == 'many':
                return self.json(200, {'services': services(60)}, cors)
            if mode == 'thirteen':          # what the hub gives its administrator (14.10.2026: 13 services, the list showed six)
                return self.json(200, {'services': services(13)}, cors)
            if mode == 'grouped':           # the hub of 15.10.2026: the four groups with `group` and `group_icon` on every service, in the order of the groups
                grp = [g for g, size in zip(GROUPS4, GROUP_SIZES) for _ in range(size)]
                return self.json(200, {'services': [dict(e, group=grp[n][0], group_icon=grp[n][1]) for n, e in enumerate(services(13))]}, cors)
            if mode == 'grouped_evil':      # captions and icons that are not what they should be: markup, a long text, a name that is not in the set, a number, a prototype name
                grp = [('Product', 'box')] * 3 + [('Маркетинг', '"><script>window.__pwned=7</script>')] * 2 + [('YouTube', 'constructor')] * 2 \
                    + [('Infrastructure', 7)] * 2 + [('<img src=x onerror="window.__pwned=9">' + 'Я' * 60, '__proto__')] * 4
                return self.json(200, {'services': [dict(e, group=grp[n][0], group_icon=grp[n][1]) for n, e in enumerate(services(13))]}, cors)
            if mode == 'evil':
                bad = [
                    {'key': 'x1', 'title': '<img src=x onerror="window.__pwned=1">Сервис <b>один</b>', 'url': f'{ORIGINS["svc"]}/svc/x1', 'icon': 'users'},
                    {'key': 'x2', 'title': 'javascript url', 'url': 'javascript:window.__pwned=2', 'icon': 'users'},
                    {'key': 'x3', 'title': 'data url', 'url': 'data:text/html,<script>window.__pwned=3</script>', 'icon': 'users'},
                    {'key': 'x4', 'title': 'plain http to a stranger', 'url': 'http://evil.example/x', 'icon': 'users'},
                    {'key': 'x5', 'title': 'icon with a quote " onload=1', 'url': f'{ORIGINS["svc"]}/svc/x5', 'icon': '"><script>window.__pwned=5</script>'},
                    {'key': 'x6', 'title': '', 'url': f'{ORIGINS["svc"]}/svc/x6', 'icon': 'users'},
                    {'key': 'x7', 'title': 'no url', 'icon': 'users'},
                    {'key': 'x1', 'title': 'duplicate key', 'url': f'{ORIGINS["svc"]}/svc/dup', 'icon': 'users'},
                    'a string', None, 7,
                    {'key': 'x8', 'title': 'Х' * 400, 'url': f'{ORIGINS["svc"]}/svc/x8', 'icon': 'constructor'},
                    {'key': 'x9', 'title': 'fine one', 'url': f'{ORIGINS["svc"]}/svc/x9', 'icon': '__proto__'},
                ]
                return self.json(200, {'services': bad}, cors)
            return self.json(200, {'services': services()}, cors)

        def card(self):
            """GET /api/auth/card as the hub answers it (Infra-Auth docs/gg-auth-api.md): the session cookie is needed, a foreign Origin gets 403 and not one CORS header,
            `photo` is there only when the person has chosen an avatar. HUB['card_mode'] picks the answer."""
            origin = self.headers.get('Origin')
            cookie = self.headers.get('Cookie') or ''
            HUB['cards'].append({'origin': origin, 'cookie': cookie, 'accept': self.headers.get('Accept'), 'dest': self.headers.get('Sec-Fetch-Dest'), 'at': time.time()})
            cors = {}
            if origin:
                if origin not in HUB['allowed']:
                    return self.json(403, {'error': 'bad_origin'}, {'Vary': 'Origin'})
                cors = {'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Credentials': 'true', 'Vary': 'Origin'}
            if HUB['card_delay']:
                time.sleep(HUB['card_delay'])
            mode = HUB['card_mode']
            card = {'display_name': 'Лёв Авдошин', 'position_title': 'Основатель', 'positions': ['Основатель'], 'gg_number': 'GG0AAAA-0AAAA', 'qr': '/v/GG0AAAA-0AAAA'}
            if 'gg_portal_session=' not in cookie or mode == 'nologin':
                return self.json(401, {'error': 'unauthenticated'}, cors)
            if mode == 'forbidden':
                return self.json(403, {'error': 'forbidden'}, cors)
            if mode == 'notfound':
                return self.json(404, {'error': 'no_card'}, cors)
            if mode == 'error':
                return self.json(503, {'error': 'unavailable'}, cors)
            if mode == 'broken':
                return self.send(200, 'application/json', '{"photo": [', cors)
            if mode == 'array':
                return self.json(200, ['not', 'a', 'card'], cors)
            if mode == 'no_cors':
                return self.json(200, dict(card, photo=HUB['card_photo']), {})
            if mode == 'custom':
                return self.json(200, dict(card, **(HUB['card_body'] or {})), cors)
            if mode == 'ok':
                return self.json(200, dict(card, photo=HUB['card_photo']), cors)
            return self.json(200, card, cors)              # nophoto: the person has not chosen an avatar, the key is absent

        def do_POST(self):
            if urllib.parse.urlparse(self.path).path != '/api/auth/logout':
                return Site.do_POST(self)
            n = int(self.headers.get('Content-Length') or 0)
            if n:
                self.rfile.read(n)
            HUB['logouts'].append({'origin': self.headers.get('Origin'), 'cookie': self.headers.get('Cookie') or '', 'site': self.headers.get('Sec-Fetch-Site'), 'at': time.time()})
            return self.json(200, {'ok': True}, {'Set-Cookie': 'gg_portal_session=; Max-Age=0; Path=/'})
    return H


class QuietServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass     # a browser that closes a connection (an aborted fetch, a closed page) is not a failure of the check


class Server:
    def __init__(self, handler):
        self.srv = QuietServer(('127.0.0.1', 0), handler)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def stop(self):
        self.srv.shutdown()


# ---------------------------------------------------------------------------------------------------------------- pages

FONTS = ("@font-face{font-family:'Montserrat';font-style:normal;font-weight:400 700;font-display:swap;src:url(/gg-id/fonts/montserrat-cyrillic.woff2) format('woff2');"
         "unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}"
         "@font-face{font-family:'Montserrat';font-style:normal;font-weight:400 700;font-display:swap;src:url(/gg-id/fonts/montserrat-latin.woff2) format('woff2');"
         "unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}")


def page(script, body='', manual=True, head=''):
    """A page of a service on the service origin: header, the mount point #account, the component from the kit folder, `script` runs after it."""
    return ('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<style>{FONTS}*{{box-sizing:border-box}}body{{margin:0;font-family:Montserrat,system-ui,sans-serif;background:#f8fafc;color:#0f172a}}'
            'header{display:flex;align-items:center;justify-content:space-between;height:64px;padding:0 16px;background:#fff;border-bottom:1px solid #e2e8f0}'
            'main{height:1400px;padding:16px}</style>'
            f'<link rel="stylesheet" href="/gg-id/account-menu/gg-account-menu.css">{head}</head>'
            f'<body><header><b>Mentorship-AKB</b><div id="account"></div></header><main><a id="after" href="#after">after</a>{body}</main>'
            + ('<script>window.GG_ACCOUNT_MENU_MANUAL = true;</script>' if manual else '')
            + '<script src="/gg-id/account-menu/gg-account-menu.js"></script>'
            f'<script>{script}</script></body></html>')


def opts_js(extra='', logout=True):
    """The options of a service page. wallet is false unless a test says otherwise: the badge shows by itself on Apple devices (the WebKit run is one),
    and the look and the keys of the rest of the menu are not to depend on the engine."""
    base = ("name: 'Лёв Авдошин', email: 'lev.avdoshin@global-generations.com', hubOrigin: '__HUB__', currentKey: 'akb', wallet: false"
            + (", logoutUrl: '/logout'" if logout else ''))
    return '{' + base + (', ' + extra if extra else '') + '}'


MIN = "hubOrigin: false, wallet: false"      # a bare menu: no hub addresses (the default hub is never asked), no badge


def mount_js(extra='', var='menu', logout=True):
    return f"window.{var} = GGAccountMenu.mount('#account', {opts_js(extra, logout)});"


ITEMS = ("items: ["
         "{id: 'edit', label: 'Редактировать профиль', icon: 'pencil', onClick: function () { window.__clicked = 'edit'; }},"
         "{id: 'settings', label: 'Настройки', icon: 'settings', href: '/settings', title: 'Менторы'},"
         "{id: 'viewas', label: 'Открыть кабинет как ментор', icon: 'eye', panel: {load: function () { return Promise.resolve([{label: 'Анна Иванова', onClick: function () { window.__clicked = 'anna'; }}, {label: 'Борис Петров', href: '/svc/boris'}]); }}},"
         "{id: 'tz', label: 'Часовой пояс', icon: 'clock', meta: 'Москва (UTC+3)', onClick: function () { window.__clicked = 'tz'; }}"
         "]")


def goto(pg, pid, html):
    PAGES[pid] = html
    HUB['calls'].clear()
    HUB['cards'].clear()
    AVATARS.clear()
    pg.goto(f'{ORIGINS["svc"]}/app.html?p={pid}')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    pg.evaluate('document.fonts.ready.then(() => 1)')


CHIP, MENU = '#account .gid-chip', '#account .gid-menu'
STATE = '''() => { const r = document.getElementById('account'), c = r.querySelector('.gid-chip'), m = r.querySelector('.gid-menu'), a = document.activeElement,
  items = [...m.querySelectorAll('[role="menuitem"]')].filter(e => e.getClientRects().length);
  return {open: !m.hidden, expanded: c.getAttribute('aria-expanded'), focus: a === c ? 'chip' : (items.indexOf(a) >= 0 ? items.indexOf(a) : (a ? 'other:' + (a.id || a.tagName) : 'none')), count: items.length,
          labels: items.map(e => (e.textContent || '').trim())}; }'''


def state(pg):
    return pg.evaluate(STATE)


# ---------------------------------------------------------------------------------------------------------------- look parity with the kit

AKB_REFERENCE = '''
<!doctype html><html lang="ru"><head><meta charset="utf-8"><link rel="stylesheet" href="/gg-id/gg-id.css">
<style>body{margin:0;background:#f8fafc}#w{position:fixed;top:24px;right:24px}</style></head><body>
<div class="gid-kit gid-acct" __THEME__ id="w">
<button class="gid-chip" type="button" aria-expanded="true" aria-haspopup="menu" aria-controls="m"><span class="gid-avatar gid-avatar--xs" aria-hidden="true">ЛА</span><span class="gid-chip-name">Лёв</span><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></button>
<div class="gid-menu" id="m" role="menu" aria-label="Аккаунт">
 <div class="gid-menu-head"><span class="gid-avatar" aria-hidden="true">ЛА</span><div class="gid-menu-head-tx"><b>Лёв Авдошин</b><span>lev.<wbr>avdoshin<wbr><span class="gid-nowrap">@global-generations.com</span></span></div></div>
 <a class="gid-menu-item" role="menuitem" href="#"><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><rect width="7" height="7" x="3" y="3" rx="1"/></svg>Мои сервисы</a>
 <a class="gid-menu-item" role="menuitem" href="#"><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="7" r="4"/></svg>Профиль GG ID</a>
 <button class="gid-menu-item" role="menuitem" type="button"><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><path d="m15 5 4 4"/></svg>Редактировать профиль</button>
 <a class="gid-menu-item" role="menuitem" href="#"><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/></svg>Настройки</a>
 <button class="gid-menu-item" role="menuitem" type="button"><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/></svg>Открыть кабинет как ментор<svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true" style="margin-left:auto;width:14px;height:14px"><path d="m9 18 6-6-6-6"/></svg></button>
 <button class="gid-menu-item" role="menuitem" type="button"><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/></svg>Часовой пояс<span class="gid-menu-meta">Москва (UTC+3)</span></button>
 <div class="gid-menu-sep"></div>
 <button class="gid-menu-item" role="menuitem" type="button"><svg class="gid-ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12H9"/></svg>Выйти</button>
</div></div></body></html>'''

SNAP = '''() => {
  const root = document.getElementById('w') || document.getElementById('account');
  const W = root.getBoundingClientRect(), chip = root.querySelector('.gid-chip'), menu = root.querySelector('.gid-menu');
  const C = chip.getBoundingClientRect(), M = menu.getBoundingClientRect();
  const PROPS = ['display','position','box-sizing','width','height','min-width','max-width','margin-top','margin-right','margin-bottom','margin-left',
    'padding-top','padding-right','padding-bottom','padding-left','border-top-width','border-right-width','border-bottom-width','border-left-width',
    'border-top-style','border-top-color','border-right-color','border-bottom-color','border-left-color','border-radius','background-color','background-image',
    'color','font-family','font-size','font-weight','line-height','letter-spacing','text-align','white-space','overflow-x','overflow-y','text-overflow',
    'flex-grow','flex-shrink','flex-basis','flex-wrap','align-items','align-content','justify-content','column-gap','row-gap','box-shadow','opacity',
    'z-index','stroke','fill','stroke-width','vertical-align','cursor','overflow-wrap','text-indent','text-transform'];
  const SELS = ['.gid-chip', '.gid-chip > .gid-avatar', '.gid-chip-name', '.gid-chip > svg', '.gid-menu', '.gid-menu-head', '.gid-menu-head .gid-avatar',
    '.gid-menu-head-tx', '.gid-menu-head-tx > b', '.gid-menu-head-tx > span', '.gid-menu-head-tx wbr', '.gid-nowrap', '.gid-menu-item', '.gid-menu-item > svg',
    '.gid-menu-meta', '.gid-menu-sep'];
  const out = [{sel: 'wrapper', i: 0, x: 0, y: 0, w: W.width, h: W.height, s: {}, text: ''},
               {sel: 'card under the chip, right edges equal', i: 0, x: M.right - W.right, y: M.top - W.bottom, w: 0, h: 0, s: {}, text: ''}];
  SELS.forEach(sel => { let n = 0; root.querySelectorAll(sel).forEach(e => {
    if (!e.getClientRects().length && e.tagName !== 'WBR') return;
    const O = menu.contains(e) ? M : C, q = e.getBoundingClientRect(), cs = getComputedStyle(e), s = {};
    PROPS.forEach(p => { s[p] = cs.getPropertyValue(p); });
    out.push({sel, i: n++, x: q.left - O.left, y: q.top - O.top, w: q.width, h: q.height, s, text: (e.textContent || '').trim().slice(0, 40)});
  }); });
  return out;
}'''


def compare(label, a, b, skip_chip=False):
    def kept(x):
        return not (skip_chip and (x['sel'].startswith('.gid-chip') or x['sel'] == 'wrapper'))
    sa = [x for x in a if kept(x)]
    sb = [x for x in b if kept(x)]
    check('look', f'{label}: the same elements ({len(sa)} against {len(sb)})', [(x['sel'], x['i']) for x in sa] == [(x['sel'], x['i']) for x in sb],
          [(x['sel'], x['i']) for x in sa][:30] if len(sa) != len(sb) else None)
    if len(sa) != len(sb):
        return
    bad = []
    for x, y in zip(sa, sb):
        box = [k for k in 'xywh' if abs(x[k] - y[k]) > 0.51]
        style = [(p, x['s'][p], y['s'][p]) for p in x['s'] if x['s'][p] != y['s'][p]]
        if box or style:
            bad.append((x['sel'], x['i'], x['text'], {k: (round(x[k], 1), round(y[k], 1)) for k in box}, style[:4]))
    check('look', f'{label}: every box and every computed style equals the kit markup', not bad, bad[:3])


def look(b):
    for tag, w, scheme, theme, skip in (('desktop light', 1440, 'light', 'light', False), ('desktop dark', 1440, 'light', 'dark', False),
                                        ('desktop dark by the system', 1440, 'dark', 'auto', False), ('phone 390 light', 390, 'light', 'light', True)):
        ctx = b.new_context(viewport={'width': w, 'height': 900}, color_scheme=scheme)
        ref = ctx.new_page()
        PAGES['ref'] = AKB_REFERENCE.replace('__THEME__', '' if theme == 'auto' else f'data-theme="{theme}"')
        ref.goto(f'{ORIGINS["svc"]}/app.html?p=ref')
        ref.evaluate('document.fonts.ready.then(() => 1)')
        ref.wait_for_timeout(450)
        snap_ref = ref.evaluate(SNAP)
        com = ctx.new_page()
        extra = ("servicesUrl: '/cabinet', servicesApi: false, profileUrl: '/profile', "
                 f"theme: '{theme}', " + ITEMS)
        PAGES['com'] = page(f"var m = GGAccountMenu.mount('#account', {opts_js(extra)}); document.getElementById('account').style.cssText = 'position:fixed;top:24px;right:24px'; m.open();")
        com.goto(f'{ORIGINS["svc"]}/app.html?p=com')
        com.wait_for_function('window.GGAccountMenu !== undefined')
        com.evaluate('document.fonts.ready.then(() => 1)')
        com.wait_for_timeout(450)
        snap_com = com.evaluate(SNAP)
        compare(tag, snap_ref, snap_com, skip_chip=skip)
        if tag == 'desktop light':
            ref.screenshot(path=os.path.join(OUT, 'look-kit-reference.png'), clip={'x': w - 360, 'y': 0, 'width': 360, 'height': 560})
            com.screenshot(path=os.path.join(OUT, 'look-component.png'), clip={'x': w - 360, 'y': 0, 'width': 360, 'height': 560})
        ctx.close()


# ---------------------------------------------------------------------------------------------------------------- behaviour

def behaviour(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': ORIGINS['svc'] + '/'}])
    errs = []
    pg = ctx.new_page()
    pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))

    goto(pg, 'main', page(mount_js('servicesApi: false, servicesUrl: "/cabinet", profileUrl: "/profile", ' + ITEMS)))
    s = state(pg)
    check('keys', 'starts closed, aria-expanded false', s['open'] is False and s['expanded'] == 'false', s)
    roles = pg.evaluate('''() => { const r = document.getElementById('account'); return {menu: r.querySelector('.gid-menu').getAttribute('role'),
      label: r.querySelector('.gid-menu').getAttribute('aria-label'), chip: r.querySelector('.gid-chip .gam-sr').textContent, chipLabel: r.querySelector('.gid-chip').hasAttribute('aria-label'), shownHidden: r.querySelector('.gid-chip-name').getAttribute('aria-hidden'),
      haspopup: r.querySelector('.gid-chip').getAttribute('aria-haspopup'), controls: r.querySelector('.gid-chip').getAttribute('aria-controls') === r.querySelector('.gid-menu').id,
      items: [...r.querySelectorAll('.gid-menu-item')].map(e => e.getAttribute('role')), sep: r.querySelector('.gid-menu-sep').getAttribute('role'),
      wrapper: r.className, theme: r.getAttribute('data-theme')}; }''')
    check('keys', 'roles: menu, menuitems, separator, a chip named from its content (a screen-reader line, no aria-label), aria-controls', roles['menu'] == 'menu' and roles['label'] == 'Аккаунт' and roles['chip'] == 'Аккаунт: Лёв Авдошин' and not roles['chipLabel'] and roles['shownHidden'] == 'true'
          and roles['haspopup'] == 'menu' and roles['controls'] and set(roles['items']) <= {'menuitem', None} and roles['sep'] == 'separator', roles)
    check('keys', 'wrapper is .gid-kit.gam, light by default, and not .gid-acct (gg-id-service.js must not take it twice)',
          'gid-kit' in roles['wrapper'] and 'gam' in roles['wrapper'] and 'gid-acct' not in roles['wrapper'] and roles['theme'] == 'light', roles)

    pg.click(CHIP)
    s = state(pg)
    check('keys', 'click opens, focus stays on the chip (mouse)', s['open'] and s['expanded'] == 'true' and s['focus'] == 'chip', s)
    pg.keyboard.press('ArrowDown')
    check('keys', 'ArrowDown goes to the first item', state(pg)['focus'] == 0, state(pg))
    pg.keyboard.press('ArrowDown')
    check('keys', 'ArrowDown goes on', state(pg)['focus'] == 1, state(pg))
    pg.keyboard.press('End')
    last = state(pg)['count'] - 1
    check('keys', 'End goes to the last item (Выйти)', state(pg)['focus'] == last and state(pg)['labels'][last] == 'Выйти', state(pg))
    pg.keyboard.press('ArrowDown')
    check('keys', 'ArrowDown wraps to the first item', state(pg)['focus'] == 0, state(pg))
    pg.keyboard.press('ArrowUp')
    check('keys', 'ArrowUp wraps to the last item', state(pg)['focus'] == last, state(pg))
    pg.keyboard.press('Home')
    check('keys', 'Home goes to the first item', state(pg)['focus'] == 0, state(pg))
    pg.keyboard.press('Escape')
    s = state(pg)
    check('keys', 'Esc closes and returns the focus to the chip', not s['open'] and s['focus'] == 'chip' and s['expanded'] == 'false', s)
    pg.keyboard.press('ArrowDown')
    s = state(pg)
    check('keys', 'ArrowDown on the closed chip opens on the first item', s['open'] and s['focus'] == 0, s)
    pg.keyboard.press('Tab')
    check('keys', 'Tab closes the menu', not state(pg)['open'], state(pg))
    pg.focus(CHIP)
    pg.keyboard.press('ArrowUp')
    s = state(pg)
    check('keys', 'ArrowUp on the closed chip opens on the last item', s['open'] and s['focus'] == s['count'] - 1, s)
    pg.keyboard.press('Escape')
    pg.focus(CHIP)
    pg.keyboard.press('Enter')
    s = state(pg)
    check('keys', 'Enter on the chip opens with the focus on the first item', s['open'] and s['focus'] == 0, s)
    pg.keyboard.press('Escape')
    pg.focus(CHIP)
    pg.keyboard.press('Space')
    s = state(pg)
    check('keys', 'Space on the chip opens with the focus on the first item', s['open'] and s['focus'] == 0, s)
    pg.mouse.click(5, 300)
    check('keys', 'a click outside closes', not state(pg)['open'], state(pg))
    pg.click(CHIP)
    pg.evaluate('document.activeElement.blur()')
    pg.keyboard.press('Escape')
    check('keys', 'Esc closes even when the focus fell to the body (Safari, Firefox)', not state(pg)['open'], state(pg))
    pg.click(CHIP)
    pg.focus('#after')
    check('keys', 'the focus moving out of the menu closes it', not state(pg)['open'], state(pg))

    # items: callbacks, events, links, panels
    pg.evaluate("window.__events = []; document.getElementById('account').addEventListener('gam:select', e => window.__events.push(e.detail));")
    pg.click(CHIP)
    pg.click(MENU + ' [data-gam-id="edit"]')
    check('items', 'onClick runs, gam:select carries the id, the menu closes',
          pg.evaluate('window.__clicked') == 'edit' and pg.evaluate('window.__events[0].id') == 'edit' and not state(pg)['open'], pg.evaluate('window.__events'))
    pg.click(CHIP)
    pg.click(MENU + ' [data-gam-id="tz"]')
    meta = pg.evaluate('document.querySelector("#account [data-gam-id=tz] .gid-menu-meta").textContent')
    check('items', 'meta text is shown and onClick of that item runs', meta == 'Москва (UTC+3)' and pg.evaluate('window.__clicked') == 'tz', meta)
    pg.click(CHIP)
    pg.click(MENU + ' [data-gam-id="viewas"]')
    s = state(pg)
    check('items', 'an item with a panel opens its list inside the menu and the menu stays open', s['open'] and 'Анна Иванова' in s['labels'] and 'Борис Петров' in s['labels'], s)
    pg.click(MENU + ' .gam-sub .gid-menu-item >> nth=0')
    check('items', 'a row of the panel works like an item (onClick, the menu closes)', pg.evaluate('window.__clicked') == 'anna' and not state(pg)['open'], pg.evaluate('window.__clicked'))
    pg.click(CHIP)
    check('items', 'the panel is folded when the menu opens again', pg.evaluate('document.querySelector("#account [data-gam-id=viewas]").getAttribute("aria-expanded")') == 'false')
    links = pg.evaluate('''() => [...document.querySelectorAll('#account a.gid-menu-item')].filter(a => a.getClientRects().length).map(a => [a.textContent.trim(), a.getAttribute('href')])''')
    base = ORIGINS['svc']
    check('items', 'links: Мои сервисы (cabinet), Профиль GG ID, Настройки, Выйти (logout url)',
          links == [['Мои сервисы', base + '/cabinet'], ['Профиль GG ID', base + '/profile'], ['Настройки', base + '/settings'], ['Выйти', base + '/logout']], links)
    pg.keyboard.press('Escape')

    # arrows inside a section, Esc from inside it
    goto(pg, 'sec', page(mount_js('servicesApi: false, servicesUrl: "/cabinet", ' + ITEMS)))
    pg.click(CHIP)
    pg.focus(MENU + ' [data-gam-id="viewas"]')
    pg.keyboard.press('ArrowRight')
    exp = pg.evaluate('document.querySelector("#account [data-gam-id=viewas]").getAttribute("aria-expanded")')
    check('keys', 'ArrowRight opens a folded section', exp == 'true', exp)
    pg.keyboard.press('ArrowDown')
    check('keys', 'ArrowDown goes into the list of the section', state(pg)['labels'][state(pg)['focus']] == 'Анна Иванова', state(pg))
    pg.keyboard.press('ArrowLeft')
    s = state(pg)
    exp = pg.evaluate('document.querySelector("#account [data-gam-id=viewas]").getAttribute("aria-expanded")')
    check('keys', 'ArrowLeft inside the list folds it and goes back to the item', exp == 'false' and s['labels'][s['focus']] == 'Открыть кабинет как ментор', s)
    pg.keyboard.press('Enter')
    exp = pg.evaluate('document.querySelector("#account [data-gam-id=viewas]").getAttribute("aria-expanded")')
    check('keys', 'Enter on a section opens it and keeps the menu open', exp == 'true' and state(pg)['open'], exp)
    pg.keyboard.press('ArrowDown')
    pg.keyboard.press('Escape')
    s = state(pg)
    check('keys', 'Esc from inside a section closes the whole menu and the focus goes to the chip', not s['open'] and s['focus'] == 'chip', s)

    # one menu at a time, update, destroy, mount twice
    goto(pg, 'two', page(mount_js('servicesApi: false, servicesUrl: "/cabinet"')
                         + "document.getElementById('account').insertAdjacentElement('afterend', Object.assign(document.createElement('div'), {id: 'second'}));"
                         + f"window.second = GGAccountMenu.mount('#second', {{name: 'Вера Петрова', email: 'vera@global-generations.com', logoutUrl: '/logout', {MIN}}});"))
    pg.click(CHIP)
    pg.click('#second .gid-chip')
    open_now = pg.evaluate('[...document.querySelectorAll(".gid-menu")].map(m => !m.hidden)')
    check('api', 'only one menu is open at a time', open_now == [False, True], open_now)
    pg.keyboard.press('Escape')
    again = pg.evaluate("GGAccountMenu.mount('#account', {name: 'Борис Петров'}) === window.menu")
    ini = pg.evaluate("document.querySelector('#account .gid-avatar').textContent + '|' + document.querySelector('#account .gid-chip-name').textContent")
    check('api', 'mount on the same element updates and returns the same handle', again and ini == 'БП|Борис', ini)
    pg.evaluate("window.menu.update({name: 'Анна', email: ''})")
    ini = pg.evaluate("document.querySelector('#account .gid-avatar').textContent + '|' + document.querySelector('#account .gid-menu-head-tx').textContent")
    check('api', 'update re-draws: one word name, no e-mail line', ini == 'А|Анна', ini)
    pg.evaluate("window.menu.update({name: '', email: 'zoya@global-generations.com'})")
    ini = pg.evaluate("document.querySelector('#account .gid-avatar').textContent + '|' + document.querySelector('#account .gid-chip-name').textContent")
    check('api', 'no name: initials from the e-mail, the chip says Аккаунт', ini == 'Z|Аккаунт', ini)
    pg.evaluate("window.menu.open()")
    pg.evaluate("window.menu.update({name: 'Лёв Авдошин'})")
    check('api', 'update keeps an open menu open', state(pg)['open'] and pg.evaluate("window.menu.isOpen()"))
    pg.evaluate("window.menu.destroy()")
    gone = pg.evaluate("(() => { const a = document.getElementById('account'); return [a.children.length, a.className, a.hasAttribute('data-theme'), a.hasAttribute('data-gam')]; })()")
    check('api', 'destroy empties the element and takes its classes back', gone == [0, '', False, False], gone)
    pg.click('#after')
    check('api', 'no listener left after destroy (a click outside does nothing, no error)', not errs, errs)
    thrown = pg.evaluate("(() => { try { GGAccountMenu.mount('#nope', {}); return 'no error'; } catch (e) { return e.name; } })()")
    check('api', 'mount on a missing element throws TypeError', thrown == 'TypeError', thrown)
    check('api', 'GGAccountMenu.version equals gg-id/VERSION', pg.evaluate('GGAccountMenu.version') == read(os.path.join(KIT, 'VERSION')).strip())
    known = pg.evaluate("['layout-grid', 'graduation-cap', 'megaphone', 'globe', 'server', 'activity', 'message-square', 'users', 'video', 'scale', 'user', 'log-out', 'chevron-down', 'chevron-right', 'external-link', 'settings', 'eye', 'clock', 'pencil', 'box', 'trending-up', 'play'].filter(n => GGAccountMenu.icons.indexOf(n) < 0)")
    check('api', 'the icons the hub mapping names (service key to icon, section to icon) and the icons of AKB items are in the kit set', known == [], known)
    check('api', 'initials: two words, one word, empty', pg.evaluate("[GGAccountMenu.initials('лёв авдошин'), GGAccountMenu.initials('Анна'), GGAccountMenu.initials(''), GGAccountMenu.initials('a b c')]") == ['ЛА', 'А', 'U', 'AB'])

    # data attributes (no script of the service), a manual flag, the event instead of a callback
    goto(pg, 'data', page('', manual=False, body='<div id="auto" data-gg-account-menu data-name="Лёв Авдошин" data-email="lev@global-generations.com" '
                          'data-hub-origin="__HUB__" data-services-api="false" data-wallet="false" data-logout-url="/logout" data-gam-theme="dark" data-gam-placement="start" '
                          'data-gam-items=\'[{"id":"s","label":"Настройки","icon":"settings","href":"/settings"}]\'></div>'))
    auto = pg.evaluate('''() => { const a = document.getElementById('auto'); return {cls: a.className, theme: a.getAttribute('data-theme'),
      labels: [...a.querySelectorAll('.gid-menu-item')].map(e => e.textContent.trim()), name: a.querySelector('.gid-chip-name').textContent}; }''')
    check('api', 'data-gg-account-menu mounts without a script of the service (theme, placement, items from attributes)',
          auto['name'] == 'Лёв' and 'gam--start' in auto['cls'] and auto['theme'] == 'dark' and 'Настройки' in auto['labels'] and 'Выйти' in auto['labels'], auto)
    goto(pg, 'manual', page('', manual=True, body='<div id="auto" data-gg-account-menu data-name="X"></div>'))
    check('api', 'GG_ACCOUNT_MENU_MANUAL stops the automatic mounting', pg.evaluate("document.getElementById('auto').children.length") == 0)
    goto(pg, 'evt', page(mount_js('servicesApi: false, servicesUrl: "/cabinet"', logout=False)))
    pg.evaluate("window.__events = []; document.getElementById('account').addEventListener('gam:select', e => window.__events.push(e.detail.id));")
    pg.click(CHIP)
    pg.click(MENU + ' [data-gam-id="logout"]')
    check('api', 'logout without url and callback is a button that only fires gam:select (id logout)', pg.evaluate('window.__events') == ['logout'], pg.evaluate('window.__events'))
    goto(pg, 'cb', page(mount_js("servicesApi: false, servicesUrl: '/cabinet', onLogout: function (ev, h) { window.__out = typeof h.close; throw new Error('boom'); }")))
    pg.click(CHIP)
    seen_errs = len(errs)
    pg.click(MENU + ' [data-gam-id="logout"]')
    pg.wait_for_timeout(150)
    check('api', 'onLogout is called with the handle; an error inside it does not break the menu', pg.evaluate('window.__out') == 'function' and not state(pg)['open'])
    del errs[seen_errs:]          # the error the test throws on purpose (its text differs by engine: Firefox prints just "Error")
    POSTS.clear()
    goto(pg, 'post', page(mount_js("servicesApi: false, servicesUrl: '/cabinet', logoutMethod: 'POST', logoutFields: {csrf_token: 'a b&c'}")))
    pg.click(CHIP)
    with pg.expect_navigation():
        pg.click(MENU + ' [data-gam-id="logout"]')
    check('api', 'logoutMethod POST sends a real form post with the cookie and the fields, the service answers with its own redirect',
          len(POSTS) == 1 and POSTS[0]['path'] == '/logout' and 'csrf_token=a+b%26c' in POSTS[0]['body'] and 'gg_portal_session=test-session' in POSTS[0]['cookie']
          and pg.url.endswith('/logged-out'), (POSTS, pg.url))
    goto(pg, 'get', page(mount_js("servicesApi: false, servicesUrl: '/cabinet'")))
    pg.click(CHIP)
    with pg.expect_navigation():
        pg.click(MENU + ' [data-gam-id="logout"]')
    check('api', 'logoutUrl by GET is a plain link to the service logout', pg.url == ORIGINS['svc'] + '/logout', pg.url)
    check('keys', 'no console errors in the behaviour runs', not errs, errs[:3])
    ctx.close()


# ---------------------------------------------------------------------------------------------------------------- services list

ROWS = '''() => [...document.querySelectorAll('#account .gam-svc')].map(a => ({title: a.querySelector('.gam-name').textContent, href: a.getAttribute('href'), key: a.getAttribute('data-gam-key'),
    current: a.getAttribute('aria-current'), icon: !!a.querySelector('.gam-tile svg'),
    grid: (() => { const s = a.querySelector('.gam-tile svg'); return !!s && s.children.length === 4 && [...s.children].every(c => c.tagName.toLowerCase() === 'rect'); })(), tile: getComputedStyle(a.querySelector('.gam-tile')).backgroundImage, meta: (a.querySelector('.gid-menu-meta') || {}).textContent || ''}))'''
LINK = '''() => { const r = document.getElementById('account'), a = r.querySelector('a[data-gam-id="services"]'), b = r.querySelector('button[data-gam-id="services"]');
  return {link: !!a && !a.hidden, href: a && a.getAttribute('href'), btn: !!b && !b.hidden, expanded: b && b.getAttribute('aria-expanded'),
          panel: [...r.querySelectorAll('.gam-sub')].some(p => !p.hidden)}; }'''


# the open services list and the card around it: what is in view (the element at the middle of the row is the row itself, so a row clipped by a box
# that scrolls does not count), whether the list or the card scrolls, how the card sits in the window
CARD_GEO = '''() => {
  const menu = document.querySelector('#account .gid-menu'), panel = document.querySelector('#account .gam-sub:not([hidden])');
  const m = menu.getBoundingClientRect(), cs = getComputedStyle(panel), vh = innerHeight, de = document.documentElement;
  const rows = [...panel.querySelectorAll('.gam-svc')], all = panel.querySelector('.gam-all'), out = document.querySelector('#account [data-gam-id="logout"]');
  const seen = e => { if (!e) return false; const r = e.getBoundingClientRect();
    if (!(r.top >= m.top - 0.5 && r.bottom <= m.bottom + 0.5 && r.top >= -0.5 && r.bottom <= vh + 0.5)) return false;
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !!hit && e.contains(hit); };
  return {rows: rows.length, seen: rows.filter(seen).length, allSeen: seen(all), logoutSeen: seen(out),
          panelMax: cs.maxHeight, panelOverflow: cs.overflowY, panelScroll: panel.scrollHeight > panel.clientHeight + 1, panelH: Math.round(panel.getBoundingClientRect().height),
          cardScrolls: menu.scrollHeight > menu.clientHeight + 1, cardOverflow: getComputedStyle(menu).overflowY, cardH: Math.round(m.height), top: Math.round(m.top),
          bottom: Math.round(m.bottom), left: Math.round(m.left), right: Math.round(m.right), w: Math.round(m.width), vh: vh, vw: innerWidth, hscroll: de.scrollWidth > de.clientWidth};
}'''
GROUPS_PROBE = '''() => {
  const panel = document.querySelector('#account .gam-sub:not([hidden])') || document.querySelector('#account .gam-sub');
  const boxes = [...panel.querySelectorAll(':scope > .gam-grp')], caps = boxes.map(b => b.firstElementChild);
  const sig = svg => svg ? [...svg.querySelectorAll('path')].map(p => p.getAttribute('d')).join('|') + '#' + svg.children.length : '';
  const cs = getComputedStyle(caps[0]);
  return {texts: caps.map(c => (c.querySelector('span') || c).textContent), sizes: boxes.map(b => b.querySelectorAll(':scope > .gam-svc').length),
    rows: panel.querySelectorAll('.gam-svc').length, roles: boxes.map(b => b.getAttribute('role')),
    labelled: boxes.map((b, i) => !!caps[i].id && b.getAttribute('aria-labelledby') === caps[i].id), capClass: caps.map(c => c.classList.contains('gam-group')),
    icons: caps.map(c => c.querySelectorAll('svg').length), iconHidden: caps.map(c => { const v = c.querySelector('svg'); return v ? v.getAttribute('aria-hidden') : null; }),
    iconSize: caps.map(c => { const v = c.querySelector('svg'); return v ? Math.round(v.getBoundingClientRect().width) : 0; }), sig: caps.map(c => sig(c.querySelector('svg'))),
    childKinds: [...panel.children].map(c => c.classList.contains('gam-grp') ? 'grp' : (c.classList.contains('gam-all') ? 'all' : c.tagName)),
    size: cs.fontSize, weight: cs.fontWeight, transform: cs.textTransform, color: cs.color, rowColor: getComputedStyle(panel.querySelector('.gam-name')).color,
    imgs: panel.querySelectorAll('img').length, scripts: panel.querySelectorAll('script').length, pwned: window.__pwned || 0};
}'''
SCROLL_CARD_END = "(() => { const m = document.querySelector('#account .gid-menu'); m.scrollTop = m.scrollHeight; })()"


def open_services(pg):
    pg.click(CHIP)
    pg.click(MENU + ' button[data-gam-id="services"]')


def listing(b):
    svc, hub = ORIGINS['svc'], ORIGINS['hub']
    HUB['allowed'] = {svc}
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000})
    ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
    errs = []
    pg = ctx.new_page()
    # WebKit reports the answer the browser blocked on purpose (the run "without CORS headers") as a page error, other engines only log it
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}') if 'access control checks' not in str(e) else None)
    cabinet = hub + '/cabinet/'

    HUB['mode'], HUB['delay'] = 'ok', 0
    goto(pg, 'svc-ok', page(mount_js()))
    pg.wait_for_timeout(300)
    check('services', 'nothing is requested while the menu stays closed (lazy)', len(HUB['calls']) == 0, HUB['calls'])
    s = pg.evaluate(LINK)
    check('services', 'before the list is known: «Мои сервисы» is an expander button, the link is hidden', s['btn'] and not s['link'] and s['expanded'] == 'false', s)
    pg.click(CHIP)
    pg.wait_for_timeout(400)
    check('services', 'the first open makes exactly one request', len(HUB['calls']) == 1, len(HUB['calls']))
    call = HUB['calls'][0] if HUB['calls'] else {}
    check('services', 'the request is cross-origin, credentialed (the hub cookie goes along), asks for JSON', call.get('origin') == svc and 'gg_portal_session=test-session' in call.get('cookie', '')
          and 'application/json' in (call.get('accept') or ''), call)
    pg.click(MENU + ' button[data-gam-id="services"]')
    pg.wait_for_selector('#account .gam-svc')
    rows = pg.evaluate(ROWS)
    want = services()
    check('services', 'every service of the answer is a row, in the order of the answer', [r['title'] for r in rows] == [x['title'] for x in want], [r['title'] for r in rows])
    check('services', 'one click goes straight into the service: the row is a link to its address', [r['href'] for r in rows] == [x['url'] for x in want], [r['href'] for r in rows][:3])
    check('services', 'every row has an icon tile with the light gradient of the kit (rule 4a)', all(r['icon'] and 'linear-gradient' in r['tile'] and '143, 186, 221' in r['tile'] for r in rows), rows[0])
    check('services', 'the icons of the cabinet are drawn (not the grid of an unknown name): briefcase, graduation-cap, clipboard-list, messages-square, mic, shopping-bag, user-plus, map, clapperboard, film, scroll-text, youtube',
          not any(r['grid'] for r in rows), [r['key'] for r in rows if r['grid']])
    cur = [r for r in rows if r['current']]
    check('services', 'the service the page is in (currentKey) is marked: aria-current and the words «Вы здесь», and only it', len(cur) == 1 and cur[0]['key'] == 'akb' and cur[0]['meta'] == 'Вы здесь', cur)
    allrow = pg.evaluate("(() => { const a = document.querySelector('#account .gam-all'); return a && [a.textContent.trim(), a.getAttribute('href')]; })()")
    check('services', 'the last row of the list leads to the hub cabinet (Все сервисы)', allrow == ['Все сервисы', cabinet], allrow)
    exp = pg.evaluate(LINK)
    check('services', 'aria-expanded is true while the list is open', exp['expanded'] == 'true' and exp['panel'], exp)
    pg.screenshot(path=os.path.join(OUT, 'services-desktop.png'), clip={'x': 1000, 'y': 0, 'width': 440, 'height': 720})
    pg.keyboard.press('Escape')
    pg.click(CHIP)
    pg.click(MENU + ' button[data-gam-id="services"]')
    check('services', 'no second request on the next open and expand (cached for the page)', len(HUB['calls']) == 1, len(HUB['calls']))
    pg.click(MENU + ' .gam-svc[data-gam-key="production"]')
    pg.wait_for_url('**/svc/production')
    check('services', 'a click on a row opens that service in this tab', pg.url == svc + '/svc/production', pg.url)

    # a long list: the list has no box of its own (every row is in the flow), the whole card scrolls and stays on the screen
    HUB['mode'] = 'many'
    goto(pg, 'svc-many', page(mount_js()))
    open_services(pg)
    pg.wait_for_selector('#account .gam-svc')
    geo = pg.evaluate(CARD_GEO)
    check('services', '60 services: the list has no box of its own (no height limit, no scroll of its own, every row in the flow), the card is inside the window',
          geo['rows'] == 60 and geo['panelMax'] == 'none' and geo['panelOverflow'] == 'visible' and not geo['panelScroll'] and geo['panelH'] > 60 * 40 and geo['bottom'] <= geo['vh'], geo)
    check('services', '60 services: the whole card scrolls (one scroll, not a scroll inside a scroll)', geo['cardScrolls'] and geo['cardOverflow'] == 'auto', geo)
    pg.evaluate(SCROLL_CARD_END)
    end = pg.evaluate(CARD_GEO)
    check('services', '60 services: scrolled to its end the card shows the last row of the list, «Все сервисы» and «Выйти»', end['allSeen'] and end['logoutSeen'], end)
    pg.keyboard.press('Escape')

    # what the hub gives its administrator (13 services; the list used to show six): every row, «Все сервисы» and «Выйти» in view with no scroll anywhere
    HUB['mode'] = 'thirteen'
    goto(pg, 'svc-13', page(mount_js()))
    open_services(pg)
    pg.wait_for_selector('#account .gam-svc')
    geo = pg.evaluate(CARD_GEO)
    check('services', '13 services in a window of 1000 px: all 13 rows, «Все сервисы» and «Выйти» are in view, the list has no scroll of its own and the card needs none',
          geo['rows'] == 13 and geo['seen'] == 13 and geo['allSeen'] and geo['logoutSeen'] and geo['panelMax'] == 'none' and not geo['panelScroll'] and not geo['cardScrolls'], geo)
    # the same list in a low window: the list stays whole (no scroll of its own), the whole card scrolls and ends with «Все сервисы» and «Выйти»
    pg.set_viewport_size({'width': 1440, 'height': 600})
    pg.wait_for_timeout(150)
    geo = pg.evaluate(CARD_GEO)
    check('services', '13 services in a window of 600 px: the list keeps all 13 rows without a scroll of its own, the whole card scrolls and stays inside the window',
          geo['rows'] == 13 and not geo['panelScroll'] and geo['cardScrolls'] and geo['cardOverflow'] == 'auto' and geo['bottom'] <= geo['vh'], geo)
    pg.evaluate(SCROLL_CARD_END)
    end = pg.evaluate(CARD_GEO)
    check('services', '13 services in a window of 600 px: scrolled to its end the card shows «Все сервисы» and «Выйти»', end['allSeen'] and end['logoutSeen'], end)
    pg.keyboard.press('Escape')
    pg.set_viewport_size({'width': 1440, 'height': 1000})

    # the groups of 15.10.2026: the hub sends `group` and `group_icon`; the list draws a small grey caption (icon and name) before the first service of each group,
    # the services of a group stand in a group of their own; no `group` = no captions
    check('groups', 'an answer without `group` (the old hub) draws no captions', pg.evaluate("document.querySelectorAll('#account .gam-group').length") == 0)
    HUB['mode'] = 'grouped'
    goto(pg, 'svc-groups', page(mount_js()))
    open_services(pg)
    pg.wait_for_selector('#account .gam-group')
    info = pg.evaluate(GROUPS_PROBE)
    check('groups', 'four groups in the order of the cabinet: Product, Маркетинг, YouTube, Infrastructure (6, 2, 4 and 1 services), all 13 rows',
          info['texts'] == [g for g, _ in GROUPS4] and info['sizes'] == GROUP_SIZES and info['rows'] == 13, info)
    check('groups', 'a group is a box of its own: role=group named by its caption (aria-labelledby), the caption is its first child; «Все сервисы» stands after the groups, outside them',
          info['roles'] == ['group'] * 4 and all(info['labelled']) and all(info['capClass']) and info['childKinds'] == ['grp'] * 4 + ['all'], info)
    check('groups', 'every caption has its icon, the one of the section of the board (box, trending-up, play, server): a small svg 14 px, hidden from screen readers, four different drawings (3, 2, 1 and 4 shapes)',
          info['icons'] == [1] * 4 and info['iconHidden'] == ['true'] * 4 and info['iconSize'] == [14] * 4 and len(set(info['sig'])) == 4
          and [x.split('#')[1] for x in info['sig']] == ['3', '2', '1', '4'], info)
    check('groups', 'captions: 12 px, weight 600, not upper-cased, muted colour (not the colour of the service names)',
          info['size'] == '12px' and info['weight'] == '600' and info['transform'] == 'none' and info['color'] != info['rowColor'], info)
    geo = pg.evaluate(CARD_GEO)
    check('groups', 'grouped list of 13 in a window of 1000 px: all rows, «Все сервисы» and «Выйти» in view, no scroll of its own',
          geo['rows'] == 13 and geo['seen'] == 13 and geo['allSeen'] and geo['logoutSeen'] and not geo['panelScroll'], geo)
    # the keyboard walks the services of all groups in the order of the list (the captions are not stops), then «Все сервисы»
    pg.focus(MENU + ' button[data-gam-id="services"]')
    walk = []
    for _ in range(14):
        pg.keyboard.press('ArrowDown')
        walk.append(pg.evaluate("(() => { const a = document.activeElement; return a ? (a.getAttribute('data-gam-key') || (a.classList.contains('gam-all') ? 'all' : a.tagName)) : ''; })()"))
    check('groups', 'the arrow keys walk the 13 services across the groups in the order of the list and then «Все сервисы»',
          walk == [k for k, _, _ in SERVICE_BASE] + ['extra-12', 'all'], walk)
    pg.screenshot(path=os.path.join(OUT, 'groups-desktop.png'), clip={'x': 1000, 'y': 0, 'width': 440, 'height': 1000})
    pg.keyboard.press('Escape')
    # captions and icons that are not what they should be: text only, cut to 40 letters, a name that is not in the set draws no icon
    HUB['mode'] = 'grouped_evil'
    goto(pg, 'svc-groups-evil', page(mount_js()))
    open_services(pg)
    pg.wait_for_selector('#account .gam-group')
    ev = pg.evaluate(GROUPS_PROBE)
    check('groups', 'captions are text only: markup and 60 letters are cut to 40 and shown as text, nothing runs',
          len(ev['texts']) == 5 and ev['texts'][:4] == [g for g, _ in GROUPS4] and len(ev['texts'][4]) == 40 and ev['texts'][4].startswith('<img')
          and ev['imgs'] == 0 and ev['scripts'] == 0 and ev['pwned'] == 0 and ev['rows'] == 13, ev)
    check('groups', 'an icon of a group that is not in the set (markup, a prototype name, a number) draws no icon; a known one draws it',
          ev['icons'] == [1, 0, 0, 0, 0], ev['icons'])
    pg.keyboard.press('Escape')
    HUB['mode'] = 'thirteen'

    # the panel of an item of the service itself (a long list of people) keeps its own box: only «Мои сервисы» lost the limit
    people = ', '.join("{label: 'Ментор %d'}" % i for i in range(40))
    goto(pg, 'svc-people', page(mount_js("items: [{id: 'viewas', label: 'Открыть кабинет как ментор', icon: 'eye', panel: {items: [" + people + "]}}]")))
    pg.click(CHIP)
    pg.click(MENU + ' button[data-gam-id="viewas"]')
    pg.wait_for_selector('#account .gam-sub:not([hidden]) .gid-menu-item')
    own = pg.evaluate('''() => { const p = document.querySelector('#account .gam-sub:not([hidden])'), cs = getComputedStyle(p);
      return {rows: p.querySelectorAll('.gid-menu-item').length, max: cs.maxHeight, overflow: cs.overflowY, scroll: p.scrollHeight > p.clientHeight + 1, h: p.clientHeight}; }''')
    check('services', 'the panel of an item of the service itself (40 people) keeps its own box: max 272 px and a scroll of its own',
          own['rows'] == 40 and own['max'] == '272px' and own['overflow'] == 'auto' and own['scroll'] and own['h'] <= 273, own)
    pg.keyboard.press('Escape')

    # a low window: the whole menu scrolls instead of leaving the screen
    pg.set_viewport_size({'width': 1440, 'height': 240})
    pg.click(CHIP)
    geo = pg.evaluate('''() => { const m = document.querySelector('#account .gid-menu'); const r = m.getBoundingClientRect();
      return {bottom: r.bottom, vh: innerHeight, scroll: m.scrollHeight > m.clientHeight, overflow: getComputedStyle(m).overflowY}; }''')
    check('services', 'a low window (240 px): the menu keeps inside the window and scrolls inside', geo['bottom'] <= geo['vh'] and geo['scroll'] and geo['overflow'] == 'auto', geo)
    pg.keyboard.press('Escape')
    pg.set_viewport_size({'width': 1440, 'height': 1000})

    # when the list cannot be had: a plain link to the hub cabinet
    for mode, why in (('nologin', '401: no hub session'), ('forbidden', '403: no level'), ('error', '503: the hub is down'), ('empty', 'an empty list'),
                      ('broken', 'broken JSON'), ('wrong', 'an answer of another shape'), ('no_cors', 'an answer without CORS headers (the browser blocks it)')):
        HUB['mode'] = mode
        goto(pg, 'svc-' + mode, page(mount_js()))
        pg.click(CHIP)
        pg.wait_for_function('document.querySelector("#account a[data-gam-id=services]") && document.querySelector("#account a[data-gam-id=services]").getClientRects().length > 0', timeout=4000)
        s = pg.evaluate(LINK)
        check('services', f'{why}: «Мои сервисы» becomes a plain link to the cabinet, no list, no button', s['link'] and s['href'] == cabinet and not s['btn'] and not s['panel'], s)
        check('services', f'{why}: one request, no retry storm', len(HUB['calls']) == 1, len(HUB['calls']))
        if mode == 'error':
            pg.screenshot(path=os.path.join(OUT, 'services-fallback.png'), clip={'x': 1000, 'y': 0, 'width': 440, 'height': 360})
        pg.keyboard.press('Escape')

    # a page that the hub does not know (foreign origin): 403 without CORS headers, the browser refuses, the link stays
    HUB['mode'] = 'ok'
    ctx2 = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx2.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': ORIGINS['evil'] + '/'}])
    ev = ctx2.new_page()
    PAGES['evil'] = page(mount_js())
    HUB['calls'].clear()
    ev.goto(f'{ORIGINS["evil"]}/app.html?p=evil')
    ev.wait_for_function('window.GGAccountMenu !== undefined')
    ev.click(CHIP)
    ev.wait_for_function('document.querySelector("#account a[data-gam-id=services]") && document.querySelector("#account a[data-gam-id=services]").getClientRects().length > 0', timeout=4000)
    check('services', 'a foreign page: the hub answered 403 without CORS headers, the page got nothing, the link to the cabinet remains', ev.evaluate(LINK)['href'] == cabinet
          and len(HUB['calls']) == 1 and HUB['calls'][0]['origin'] == ORIGINS['evil'], HUB['calls'])
    ctx2.close()

    # slow hub: the loading line, then the list; a hub that is too slow: the link
    HUB['mode'], HUB['delay'] = 'ok', 0.9
    goto(pg, 'svc-slow', page(mount_js()))
    open_services(pg)
    loading = pg.evaluate("(() => { const n = document.querySelector('#account .gam-sub .gam-note'); return n && [n.textContent, n.getAttribute('role')]; })()")
    check('services', 'while the answer is on its way the panel says «Загружаем сервисов…» (role status)', loading == ['Загружаем сервисы…', 'status'], loading)
    pg.wait_for_selector('#account .gam-svc', timeout=4000)
    check('services', 'the list replaces the loading line', len(pg.evaluate(ROWS)) == 12)
    HUB['delay'] = 1.8
    goto(pg, 'svc-timeout', page(mount_js('servicesTimeout: 700')))
    open_services(pg)
    pg.focus(MENU + ' button[data-gam-id="services"]')       # Safari gives a button no focus on a click; the focus of a keyboard user on the expander is made explicit
    pg.wait_for_function('document.querySelector("#account a[data-gam-id=services]") && document.querySelector("#account a[data-gam-id=services]").getClientRects().length > 0', timeout=4000)
    s = pg.evaluate(LINK)
    foc = pg.evaluate("document.activeElement && document.activeElement.getAttribute('data-gam-id')")
    check('services', 'too slow (timeout): the link; the panel that was waiting folds, the focus follows to the link',
          s['link'] and not s['panel'] and not s['btn'], s)
    check('services', 'the focus that was on the expander moves to the link when the list fails', foc == 'services', foc)
    HUB['delay'] = 0

    # no hub origin, no api: no request at all
    goto(pg, 'svc-noapi', page(mount_js('servicesApi: false')))
    pg.click(CHIP)
    pg.wait_for_timeout(250)
    check('services', 'servicesApi false: no request, «Мои сервисы» is the cabinet link at once', len(HUB['calls']) == 0 and pg.evaluate(LINK)['href'] == cabinet, HUB['calls'])
    goto(pg, 'svc-nohub', page(f"window.menu = GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', email: 'lev@global-generations.com', logoutUrl: '/logout', {MIN}}});"))
    pg.click(CHIP)
    labels = state(pg)['labels']
    check('services', 'no hubOrigin and no urls: no services item and no profile item, only what the service gave and Выйти', labels == ['Выйти'] and len(HUB['calls']) == 0, labels)
    goto(pg, 'svc-static', page(mount_js("services: [{key: 'a', title: 'Один', url: '__SVC__/svc/a', icon: 'users'}, {key: 'b', title: 'Два', url: 'https://example.org/b', icon: 'nope'}]")))
    open_services(pg)
    rows = pg.evaluate(ROWS)
    check('services', 'services given by the page itself: drawn at once, not one request', [r['title'] for r in rows] == ['Один', 'Два'] and len(HUB['calls']) == 0, (rows, HUB['calls']))
    pg.keyboard.press('Escape')
    goto(pg, 'svc-off', page(mount_js('services: false')))
    pg.click(CHIP)
    check('services', 'services false removes the item (the hub cabinet itself)', 'Мои сервисы' not in state(pg)['labels'] and len(HUB['calls']) == 0, state(pg)['labels'])
    pg.keyboard.press('Escape')

    # the list can be asked again by hand after a failure
    HUB['mode'] = 'error'
    goto(pg, 'svc-refresh', page(mount_js()))
    pg.click(CHIP)
    pg.wait_for_function('document.querySelector("#account a[data-gam-id=services]") && document.querySelector("#account a[data-gam-id=services]").getClientRects().length > 0')
    HUB['mode'] = 'ok'
    pg.evaluate('window.menu.refreshServices()')
    pg.click(CHIP) if not state(pg)['open'] else None
    pg.wait_for_function('document.querySelector("#account button[data-gam-id=services]") && document.querySelector("#account button[data-gam-id=services]").getClientRects().length > 0', timeout=4000)
    pg.wait_for_timeout(300)
    check('services', 'refreshServices after a failure asks again and the expander comes back', len(HUB['calls']) == 2 and pg.evaluate(LINK)['btn'], (len(HUB['calls']), pg.evaluate(LINK)))
    pg.keyboard.press('Escape')

    # the answer as an array, a second menu on the same page shares the one answer
    HUB['mode'] = 'array'
    goto(pg, 'svc-array', page(mount_js()
                               + "document.getElementById('account').insertAdjacentElement('afterend', Object.assign(document.createElement('div'), {id: 'second'}));"
                               + "GGAccountMenu.mount('#second', {name: 'Вера Петрова', hubOrigin: '__HUB__', wallet: false, logoutUrl: '/logout'});"))
    open_services(pg)
    pg.wait_for_selector('#account .gam-svc')
    pg.keyboard.press('Escape')
    pg.click('#second .gid-chip')
    pg.click('#second button[data-gam-id="services"]')
    pg.wait_for_selector('#second .gam-svc')
    check('services', 'an answer that is a bare array is read; two menus on a page make one request', pg.evaluate("document.querySelectorAll('#second .gam-svc').length") == 3 and len(HUB['calls']) == 1, len(HUB['calls']))
    pg.keyboard.press('Escape')

    # markup in the data stays text
    HUB['mode'] = 'evil'
    goto(pg, 'svc-evil', page(mount_js("name: '<img src=x onerror=\"window.__pwned=10\">Лёв <b>Авдошин</b>', email: '\"><script>window.__pwned=11<\\/script>@x.com', "
                                       "items: [{label: '<img src=x onerror=\"window.__pwned=12\">', href: 'javascript:window.__pwned=13'}, {label: 'data', href: 'data:text/html,x'}]")))
    open_services(pg)
    pg.wait_for_selector('#account .gam-svc')
    safe = pg.evaluate('''() => ({pwned: window.__pwned || 0, imgs: document.querySelectorAll('img').length, scripts: document.querySelectorAll('#account script').length,
      rows: [...document.querySelectorAll('#account .gam-svc')].map(a => [a.querySelector('.gam-name').textContent.slice(0, 40), a.getAttribute('href')]),
      head: document.querySelector('#account .gid-menu-head-tx').textContent, chipName: document.querySelector('#account .gid-chip-name').textContent,
      bold: document.querySelectorAll('#account b').length, hrefs: [...document.querySelectorAll('#account a')].map(a => a.getAttribute('href')),
      icons: [...document.querySelectorAll('#account .gam-tile svg')].map(s => s.children.length > 0)})''')
    check('safety', 'nothing from the data ran', safe['pwned'] == 0 and safe['imgs'] == 0 and safe['scripts'] == 0, safe)
    check('safety', 'name and e-mail with markup are shown as text', '<img src=x' in safe['head'] and '<script>' in safe['head'] and safe['chipName'] == '<img', safe['head'])
    check('safety', 'no element is made from a title: one <b> in the whole menu (the name line)', safe['bold'] == 1, safe['bold'])
    titles = [r[0] for r in safe['rows']]
    check('safety', 'javascript:, data:, plain http to a stranger, empty title, no url, duplicate key, non-objects are dropped; 4 rows are left (x1, x5, x8, x9)',
          len(titles) == 4 and titles[0].startswith('<img src=x') and 'Х' * 40 == titles[2], titles)
    check('safety', 'no javascript: or data: address anywhere in the menu', not [h for h in safe['hrefs'] if h and re.match(r'(javascript|data):', h, re.I)], safe['hrefs'])
    check('safety', 'an unknown or inherited icon name (a quote, constructor, __proto__) falls back to the default icon, which draws', all(safe['icons']), safe['icons'])
    check('safety', 'a very long title is cut to 120 characters', len(pg.evaluate("document.querySelectorAll('#account .gam-svc .gam-name')[2].textContent")) == 120)
    pg.keyboard.press('Escape')
    check('services', 'no page errors in the services runs', not errs, errs[:3])
    ctx.close()


# ---------------------------------------------------------------------------------------------------------------- phone

def phone(b, engine):
    svc = ORIGINS['svc']
    HUB['allowed'] = {svc}
    HUB['mode'], HUB['delay'] = 'many', 0
    kw = {'viewport': {'width': 390, 'height': 844}, 'device_scale_factor': 2}
    if engine != 'firefox':
        kw.update(has_touch=True, is_mobile=True)
    ctx = b.new_context(**kw)
    ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
    pg = ctx.new_page()
    goto(pg, 'ph', page(mount_js(ITEMS)))
    geo = pg.evaluate('''() => { const c = document.querySelector('#account .gid-chip'), r = c.getBoundingClientRect(), av = c.querySelector('.gid-avatar'), ar = av.getBoundingClientRect(),
      de = document.documentElement, cs = getComputedStyle(av);
      return {w: r.width, h: r.height, avatar: ar.width, text: av.textContent, bg: cs.backgroundImage, ink: cs.color, radius: getComputedStyle(c).borderRadius, scrollW: de.scrollWidth, clientW: de.clientWidth,
              name: getComputedStyle(c.querySelector('.gid-chip-name')).display, arrow: getComputedStyle(c.querySelector('svg')).display, right: r.right}; }''')
    check('phone', 'at 390 px the chip is the round 40 px initials (name and arrow are gone, as in AKB)', abs(geo['w'] - 40) < 1.1 and abs(geo['h'] - 40) < 1.1 and geo['name'] == 'none' and geo['arrow'] == 'none', geo)
    check('phone', 'the initials are ЛА navy on the light blue gradient circle (12.10: no dark fill)', geo['text'] == 'ЛА' and 'linear-gradient' in geo['bg'] and '232, 241, 250' in geo['bg'] and '214, 230, 245' in geo['bg']
          and geo['ink'] == 'rgb(19, 68, 93)' and abs(geo['avatar'] - 28) < 0.6, geo)
    check('phone', 'no horizontal scroll with the chip in the header', geo['scrollW'] <= geo['clientW'], geo)
    named = pg.evaluate('''() => { const c = document.querySelector('#account .gid-chip'), sr = c.querySelector('.gam-sr'), r = sr.getBoundingClientRect(), cs = getComputedStyle(sr);
      return {text: sr.textContent, display: cs.display, visibility: cs.visibility, w: r.width, h: r.height, pos: cs.position}; }''')
    check('phone', 'at 390 px the chip still has its name for screen readers (not display none, one pixel, out of the flow)',
          named['text'] == 'Аккаунт: Лёв Авдошин' and named['display'] != 'none' and named['visibility'] == 'visible' and named['w'] <= 1.01 and named['pos'] == 'absolute', named)
    if engine == 'firefox':
        pg.click(CHIP)
    else:
        box = pg.locator(CHIP).bounding_box()
        pg.touchscreen.tap(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    pg.wait_for_timeout(350)
    m = pg.evaluate('''() => { const r = document.querySelector('#account .gid-menu').getBoundingClientRect(), de = document.documentElement;
      return {left: r.left, right: r.right, w: r.width, open: !document.querySelector('#account .gid-menu').hidden, scrollW: de.scrollWidth, clientW: de.clientWidth,
              items: [...document.querySelectorAll('#account .gid-menu-item')].filter(e => e.getClientRects().length).map(e => e.getBoundingClientRect().height)}; }''')
    check('phone', 'the card is open, 300 px wide, inside the screen with a margin of at least 8 px, no horizontal scroll',
          m['open'] and abs(m['w'] - 300) < 1.5 and m['left'] >= 8 and m['right'] <= 382 and m['scrollW'] <= m['clientW'], m)
    check('phone', 'every row is at least 36 px high (a finger)', all(h >= 36 for h in m['items']), m['items'])
    pg.click(MENU + ' button[data-gam-id="services"]') if engine == 'firefox' else pg.locator(MENU + ' button[data-gam-id="services"]').tap()
    pg.wait_for_selector('#account .gam-svc')
    pg.wait_for_timeout(300)
    sub = pg.evaluate('''() => { const p = document.querySelector('#account .gam-sub'), r = p.getBoundingClientRect(), menu = document.querySelector('#account .gid-menu'), m = menu.getBoundingClientRect();
      return {rows: p.querySelectorAll('.gam-svc').length, inside: r.left >= m.left && r.right <= m.right, scroll: p.scrollHeight > p.clientHeight + 1, menuScroll: menu.scrollHeight > menu.clientHeight + 1,
              menuBottom: m.bottom, vh: innerHeight,
              names: [...p.querySelectorAll('.gam-name')].every(n => n.scrollWidth <= n.clientWidth + 1 || getComputedStyle(n).textOverflow === 'ellipsis')}; }''')
    check('phone', 'the services list inside the card at 390 px: 60 rows, no scroll of its own, the whole card scrolls and stays in the window, long names are cut with an ellipsis',
          sub['rows'] == 60 and sub['inside'] and not sub['scroll'] and sub['menuScroll'] and sub['menuBottom'] <= sub['vh'] and sub['names'], sub)
    pg.screenshot(path=os.path.join(OUT, 'phone-services.png'))
    # a tap outside closes (pointerdown, because iOS sends no click for taps on plain page areas)
    if engine == 'firefox':
        pg.mouse.click(20, 700)
    else:
        pg.touchscreen.tap(20, 700)
    pg.wait_for_timeout(150)
    check('phone', 'a tap outside the card closes it', not state(pg)['open'], state(pg))

    # what the hub gives its administrator (13 services) on the phone: the card stays inside the screen, the list has no box of its own, the whole card scrolls
    def press(sel):
        if engine == 'firefox':
            pg.click(sel)
        else:
            pg.locator(sel).tap()
    HUB['mode'] = 'thirteen'
    goto(pg, 'ph13', page(mount_js(ITEMS)))
    press(CHIP)
    pg.wait_for_timeout(350)
    press(MENU + ' button[data-gam-id="services"]')
    pg.wait_for_selector('#account .gam-svc')
    pg.wait_for_timeout(300)
    geo = pg.evaluate(CARD_GEO)
    check('phone', '13 services at 390 px: the card is 300 px wide, inside the screen (margin at least 8 px), no horizontal scroll; the list has no box of its own and the whole card scrolls',
          geo['rows'] == 13 and abs(geo['w'] - 300) < 1.5 and geo['left'] >= 8 and geo['right'] <= geo['vw'] - 8 and not geo['hscroll'] and geo['panelMax'] == 'none'
          and not geo['panelScroll'] and geo['cardScrolls'] and geo['bottom'] <= geo['vh'], geo)
    pg.screenshot(path=os.path.join(OUT, 'phone-services-13.png'))
    pg.evaluate(SCROLL_CARD_END)
    end = pg.evaluate(CARD_GEO)
    check('phone', '13 services at 390 px: scrolled to its end the card shows «Все сервисы» and «Выйти», still inside the screen', end['allSeen'] and end['logoutSeen'] and end['bottom'] <= end['vh']
          and end['left'] >= 8 and end['right'] <= end['vw'] - 8 and not end['hscroll'], end)
    if engine == 'firefox':
        pg.mouse.click(20, 700)
    else:
        pg.touchscreen.tap(20, 700)
    pg.wait_for_timeout(150)
    # a long name and a long address inside 300 px
    PAGES['ph2'] = page(f"GGAccountMenu.mount('#account', {{name: 'Александра Образцова-Константинопольская', email: 'aleksandra.obraztsova-konstantinopolskaya@global-generations.com', logoutUrl: '/logout', {MIN}}}).open();")
    pg.goto(f'{svc}/app.html?p=ph2')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    pg.wait_for_timeout(300)
    longs = pg.evaluate('''() => { const m = document.querySelector('#account .gid-menu'), mr = m.getBoundingClientRect(), de = document.documentElement;
      return {outside: [...m.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > mr.right + 1 || r.left < mr.left - 1); }).length, scrollW: de.scrollWidth, clientW: de.clientWidth}; }''')
    check('phone', 'a long name and a long e-mail wrap inside the card, nothing sticks out', longs['outside'] == 0 and longs['scrollW'] <= longs['clientW'], longs)
    pg.screenshot(path=os.path.join(OUT, 'phone-long.png'))
    ctx.close()


def narrow_edges(b):
    """The chip that is not at the edge of the screen: the card is moved back inside the window (left and right edge)."""
    ctx = b.new_context(viewport={'width': 390, 'height': 700})
    pg = ctx.new_page()
    PAGES['edge'] = page(f"document.getElementById('account').style.cssText = 'position:fixed;top:20px;left:6px'; GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', logoutUrl: '/logout', {MIN}}}).open();")
    pg.goto(f'{ORIGINS["svc"]}/app.html?p=edge')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    pg.wait_for_timeout(300)
    r = pg.evaluate("(() => { const q = document.querySelector('#account .gid-menu').getBoundingClientRect(); return [q.left, q.right, innerWidth]; })()")
    check('phone', 'a chip at the left edge of a phone: the card (opening to the left) is shifted back into the window', r[0] >= 7.5 and r[1] <= r[2] - 7.5, r)
    PAGES['edge2'] = page(f"document.getElementById('account').style.cssText = 'position:fixed;top:20px;left:6px'; GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', placement: 'start', logoutUrl: '/logout', {MIN}}}).open();")
    pg.goto(f'{ORIGINS["svc"]}/app.html?p=edge2')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    pg.wait_for_timeout(300)
    r = pg.evaluate("(() => { const q = document.querySelector('#account .gid-menu').getBoundingClientRect(); return [q.left, q.right, innerWidth]; })()")
    check('phone', 'placement start: the card opens to the right of the chip and stays inside the window', r[0] >= 7.5 and r[1] <= r[2] - 7.5, r)
    ctx.close()


def avatar_variant(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    PAGES['av'] = page(f"GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', variant: 'avatar', logoutUrl: '/logout', {MIN}}});")
    pg.goto(f'{ORIGINS["svc"]}/app.html?p=av')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    w = pg.evaluate("document.querySelector('#account .gid-chip').getBoundingClientRect().width")
    check('look', 'variant avatar: the round initials at any width (40 px)', abs(w - 40) < 1.1, w)
    PAGES['dk'] = page(f"GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', theme: 'dark', logoutUrl: '/logout', {MIN}}}).open();")
    pg.goto(f'{ORIGINS["svc"]}/app.html?p=dk')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    pg.wait_for_timeout(300)
    bg = pg.evaluate("getComputedStyle(document.querySelector('#account .gid-menu')).backgroundColor")
    check('look', 'theme dark: the card is the dark surface of the kit', bg == 'rgb(10, 31, 44)', bg)
    pg.screenshot(path=os.path.join(OUT, 'dark-desktop.png'), clip={'x': 1000, 'y': 0, 'width': 440, 'height': 480})
    ctx.close()


def focus_rings(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    PAGES['fr'] = page("GGAccountMenu.mount('#account', {name: 'Лёв Авдошин', hubOrigin: '__HUB__', wallet: false, servicesApi: false, logoutUrl: '/logout'});")
    pg.goto(f'{ORIGINS["svc"]}/app.html?p=fr')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    pg.focus('#after')
    pg.keyboard.press('Shift+Tab')
    if not pg.evaluate("document.activeElement.classList.contains('gid-chip')"):
        pg.focus(CHIP)        # Safari: Tab does not stop on buttons by default; the chip is focused by script, the ring is the same
    ring = pg.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [document.activeElement.className, s.outlineStyle, s.outlineWidth, s.outlineColor]; })()")
    check('keys', 'the chip shows a visible keyboard focus ring (2 px solid, the kit blue)', ring[1] == 'solid' and ring[2] == '2px' and ring[3] == 'rgb(0, 156, 220)', ring)
    pg.keyboard.press('Enter')
    pg.keyboard.press('ArrowDown')
    ring = pg.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [document.activeElement.textContent.trim(), s.outlineStyle, s.outlineWidth, s.outlineColor]; })()")
    check('keys', 'an item shows the same ring', ring[1] == 'solid' and ring[2] == '2px' and ring[3] == 'rgb(0, 156, 220)', ring)
    ctx.close()


# ---------------------------------------------------------------------------------------------------------------- the Apple Wallet badge

WALLET_PATH = '/api/auth/wallet/apple.pkpass'
CARD_PATH = '/api/auth/card'
UAS = {
    'iPhone Safari': ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1', True),
    'iPhone Chrome': ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.6478.153 Mobile/15E148 Safari/604.1', True),
    'iPad Safari': ('Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1', True),
    'Mac Safari': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15', True),
    'Mac Chrome': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36', False),
    'Mac Edge': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0', False),
    'Mac Firefox': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0', False),
    'Windows Chrome': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36', False),
    'Android Chrome': ('Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36', False),
}
BADGE = r'''() => {
  const m = document.querySelector('#account .gid-menu'), head = m.querySelector('.gid-menu-head'), b = head.querySelector('a.gam-wallet');
  if (!b) return null;
  const av = head.querySelector('.gid-avatar'), tx = head.querySelector('.gid-menu-head-tx'), mr = m.getBoundingClientRect(), hr = head.getBoundingClientRect(),
        r = b.getBoundingClientRect(), a = av.getBoundingClientRect(), t = tx.getBoundingClientRect(), cs = getComputedStyle(b), hcs = getComputedStyle(head);
  return {href: b.getAttribute('href'), role: b.getAttribute('role'), lang: b.getAttribute('lang'), label: b.getAttribute('aria-label'), title: b.getAttribute('title'),
          text: (b.textContent || '').replace(/\s+/g, ' ').trim(), last: head.lastElementChild === b, headClass: head.className, glyph: !!b.querySelector('svg path'),
          img: !!b.querySelector('img'), imgSrc: (b.querySelector('img') || {}).src || '', imgH: (b.querySelector('img') || {getBoundingClientRect: () => ({height: 0})}).getBoundingClientRect().height,
          left: r.left - a.left, gapText: r.top - Math.max(t.bottom, a.bottom), toHeadBottom: hr.bottom - r.bottom, w: r.width, h: r.height, rightRoom: hr.right - r.right,
          insideMenu: r.left >= mr.left && r.right <= mr.right && r.bottom <= mr.bottom,
          bg: cs.backgroundColor, color: cs.color, border: [cs.borderTopWidth, cs.borderTopStyle, cs.borderTopColor].join(' '), radius: cs.borderTopLeftRadius,
          shadow: cs.boxShadow, filter: cs.filter, opacity: cs.opacity, transition: cs.transitionDuration, animation: cs.animationName, headBorder: hcs.borderBottomWidth,
          order: [...head.children].map(e => e.className.split(' ')[0]), scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth};
}'''
FOCUS_RING = "(() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth, s.outlineColor, s.outlineOffset]; })()"
OPEN_BADGE = "() => { const a = document.querySelector('#account a.gam-wallet'); return a ? a.getAttribute('href') : null; }"


def wallet_badge(b):
    svc, hub = ORIGINS['svc'], ORIGINS['hub']
    HUB['allowed'] = {svc}
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
    errs = []
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
    base = 'servicesApi: false, servicesUrl: "/cabinet", profileUrl: "/profile"'

    # where it sits, what it is
    goto(pg, 'w-on', page(mount_js('wallet: true, ' + base)))
    pg.click(CHIP)
    pg.wait_for_timeout(300)
    info = pg.evaluate(BADGE)
    check('wallet', 'wallet true: the badge is drawn in the menu', info is not None)
    if info is None:
        ctx.close()
        return
    check('wallet', 'it is the last row of the header block (avatar, name and e-mail, badge) and the header is the grid of the badge',
          info['last'] and info['order'] == ['gid-avatar', 'gid-menu-head-tx', 'gam-wallet'] and 'gam-head--wallet' in info['headClass'], (info['order'], info['headClass']))
    check('wallet', 'it links to the pass of the hub: <hub>/api/auth/wallet/apple.pkpass', info['href'] == hub + WALLET_PATH, info['href'])
    check('wallet', 'a menu item (the arrows reach it), English: «Add to Apple Wallet», lang en, a title that says whose card it is',
          info['role'] == 'menuitem' and info['lang'] == 'en' and info['label'] == 'Add to Apple Wallet' and info['text'] == 'Add to Apple Wallet'
          and re.fullmatch(r'[A-Za-z ]+', info['text']) and 'Global Generation ID card' in (info['title'] or ''), info)
    check('wallet', 'the drawn badge: a wallet glyph and two lines of text, no picture', info['glyph'] and not info['img'], info)
    check('wallet', 'its left edge is the left edge of the avatar, 12 px under the name block, 36 px high, 100 to 180 px wide (the system font differs from machine to machine), inside the card with 10 px to spare on the right',
          abs(info['left']) < 0.6 and 11.4 <= info['gapText'] <= 12.6 and abs(info['h'] - 36) < 0.6 and 100 <= info['w'] <= 180 and info['rightRoom'] >= 10 and info['insideMenu'], info)
    check('wallet', 'the divider of the header stays under the badge (14 px padding and the 1 px line)', info['toHeadBottom'] >= 14 and info['headBorder'] == '1px', info)
    check('wallet', 'Apple look: black, white text, the thin grey outline (1 px #A6A6A6), no shadow, no filter, no dimming, no animation',
          info['bg'] == 'rgb(0, 0, 0)' and info['color'] == 'rgb(255, 255, 255)' and info['border'] == '1px solid rgb(166, 166, 166)' and info['shadow'] == 'none'
          and info['filter'] == 'none' and info['opacity'] == '1' and info['transition'] == '0s' and info['animation'] == 'none', info)
    before = {k: info[k] for k in ('bg', 'color', 'border', 'shadow', 'filter', 'opacity', 'radius')}
    pg.hover(MENU + ' a.gam-wallet')
    after = pg.evaluate(BADGE)
    check('wallet', 'hover changes nothing on the badge (Apple: no dimming, no effects)', {k: after[k] for k in before} == before, after)
    pg.screenshot(path=os.path.join(OUT, 'wallet-desktop.png'), clip={'x': 1040, 'y': 0, 'width': 400, 'height': 460})

    # keyboard: the first stop is the first real row, the badge is one arrow up
    goto(pg, 'w-key', page(mount_js('wallet: true, ' + base)))
    pg.focus(CHIP)
    pg.keyboard.press('Enter')
    s = state(pg)
    check('wallet', 'Enter on the chip: the first stop is «Мои сервисы», not the badge', s['open'] and s['labels'][s['focus']] == 'Мои сервисы', s)
    pg.keyboard.press('ArrowUp')
    s = state(pg)
    check('wallet', 'the arrow up from the first row reaches the badge, the first item in the order of the page', s['focus'] == 0 and s['labels'][0] == 'Add to Apple Wallet', s)
    ring = pg.evaluate(FOCUS_RING)
    check('wallet', 'the focused badge has the kit ring (2 px solid blue, 3 px away)', ring[0] == 'solid' and ring[1] == '2px' and ring[2] == 'rgb(0, 156, 220)' and ring[3] == '3px', ring)
    pg.keyboard.press('ArrowUp')
    s = state(pg)
    check('wallet', 'the arrow up from the badge wraps to the last row (Выйти)', s['labels'][s['focus']] == 'Выйти', s)
    pg.keyboard.press('Home')
    check('wallet', 'Home goes to the first item, the badge', state(pg)['labels'][state(pg)['focus']] == 'Add to Apple Wallet', state(pg))
    pg.keyboard.press('Escape')
    s = state(pg)
    check('wallet', 'Esc closes the menu from the badge and the focus returns to the chip', not s['open'] and s['focus'] == 'chip', s)
    pg.focus(CHIP)
    pg.keyboard.press('ArrowUp')
    s = state(pg)
    check('wallet', 'ArrowUp on the closed chip still opens on the last row (Выйти), not on the badge', s['open'] and s['labels'][s['focus']] == 'Выйти', s)
    pg.keyboard.press('Escape')

    # the click: the pass comes from the hub with the cookie, the page stays, the menu closes, the page hears about it
    pg.evaluate("window.__events = []; document.getElementById('account').addEventListener('gam:select', e => window.__events.push(e.detail));")
    HUB['wallet'].clear()
    pg.click(CHIP)
    with pg.expect_download() as dl:
        pg.click(MENU + ' a.gam-wallet')
    got = dl.value
    check('wallet', 'a click on the badge fetches the pass from the hub with the hub cookie (an attachment, gg-id.pkpass) and the page stays where it was',
          got.suggested_filename == 'gg-id.pkpass' and len(HUB['wallet']) == 1 and 'gg_portal_session=test-session' in HUB['wallet'][0]['cookie'] and pg.url.startswith(svc + '/app.html'),
          (got.suggested_filename, HUB['wallet'], pg.url))
    check('wallet', 'the menu closes after the click and the page gets gam:select with id wallet', not state(pg)['open'] and pg.evaluate('window.__events') == [{'id': 'wallet', 'label': 'Add to Apple Wallet'}], pg.evaluate('window.__events'))

    # the rule of the cabinet (wallet not said = auto): iPhone, iPad, Safari on a Mac; the rest does not see it
    cases = [(ua, 0, want) for ua, want in UAS.values()] + [(UAS['Mac Safari'][0], 5, True), (UAS['Mac Chrome'][0], 5, True), (UAS['Mac Chrome'][0], 1, False), ('', 0, False)]
    got_rule = pg.evaluate('cases => cases.map(c => GGAccountMenu.walletDevice({userAgent: c[0], maxTouchPoints: c[1]}))', [[c[0], c[1]] for c in cases])
    check('wallet', 'GGAccountMenu.walletDevice is the rule of the hub cabinet: iPhone, iPad (also as a Mac with a touch screen), Safari on a Mac yes; Chrome, Edge, Firefox on a Mac, Windows, Android no',
          got_rule == [c[2] for c in cases], [(c[0][:40], c[1], g) for c, g in zip(cases, got_rule) if g != c[2]])
    check('wallet', 'walletDevice without a navigator is false', pg.evaluate('GGAccountMenu.walletDevice() === false'))
    PAGES['w-ua'] = page("GGAccountMenu.mount('#account', {name: 'Лёв Авдошин', email: 'lev@global-generations.com', hubOrigin: '__HUB__', servicesApi: false, logoutUrl: '/logout'});")
    for label, (ua, want) in UAS.items():
        c2 = b.new_context(viewport={'width': 1024, 'height': 800}, user_agent=ua)
        p2 = c2.new_page()
        p2.goto(f'{svc}/app.html?p=w-ua')
        p2.wait_for_function('window.GGAccountMenu !== undefined')
        p2.click(CHIP)
        shown = p2.evaluate(OPEN_BADGE)
        check('wallet', f'default (wallet not said), {label}: the badge is {"there" if want else "not there"}', (shown == hub + WALLET_PATH) if want else shown is None, shown)
        c2.close()

    # the options
    def badge_href(pid, extra, hub_opt=True):
        html = page(mount_js(extra) if hub_opt else f"window.menu = GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', email: 'lev@global-generations.com', logoutUrl: '/logout', {extra}}});")
        goto(pg, pid, html)
        pg.click(CHIP)
        res = pg.evaluate(OPEN_BADGE)
        pg.keyboard.press('Escape')
        return res
    check('wallet', 'walletUrl: the address of the service replaces the hub one', badge_href('w-url', 'wallet: true, servicesApi: false, walletUrl: "__SVC__/pass"') == svc + '/pass')
    check('wallet', 'walletUrl false removes the badge, even with wallet true', badge_href('w-url-off', 'wallet: true, servicesApi: false, walletUrl: false') is None)
    check('wallet', 'wallet false removes the badge', badge_href('w-off', 'wallet: false, servicesApi: false') is None)
    check('wallet', 'no hub and no walletUrl: nothing to link to, no badge (even with wallet true)', badge_href('w-nohub', 'wallet: true, hubOrigin: false', hub_opt=False) is None)
    check('wallet', 'no hub, but walletUrl given: the badge links to it', badge_href('w-nohub-url', 'wallet: true, hubOrigin: false, walletUrl: "/pass"', hub_opt=False) == svc + '/pass')
    res = badge_href('w-evil', 'wallet: true, servicesApi: false, walletUrl: "javascript:window.__pwned=21"')
    check('wallet', 'javascript: as walletUrl is dropped (the hub address is used), nothing runs', res == hub + WALLET_PATH and not pg.evaluate('window.__pwned || 0'), res)
    res = badge_href('w-evil2', 'wallet: true, servicesApi: false, walletUrl: "data:text/html,x"')
    check('wallet', 'data: as walletUrl is dropped too', res == hub + WALLET_PATH, res)

    # the official artwork of Apple in place of the drawn badge
    goto(pg, 'w-art', page(mount_js('wallet: true, servicesApi: false, walletImage: "/gg-id/gg-id-icon.svg"')))
    pg.click(CHIP)
    pg.wait_for_timeout(350)       # the card scales in for 0.2 s: sizes are read when it stands
    art = pg.evaluate(BADGE)
    check('wallet', 'walletImage: the file of Apple is shown as it is (an image in the same link, 36 px high, no frame, no background of ours), the name stays «Add to Apple Wallet»',
          art and art['img'] and art['imgSrc'].endswith('/gg-id/gg-id-icon.svg') and not art['glyph'] and abs(art['imgH'] - 36) < 0.6 and art['bg'] == 'rgba(0, 0, 0, 0)'
          and art['border'].startswith('0px') and art['label'] == 'Add to Apple Wallet' and art['href'] == hub + WALLET_PATH, art)
    goto(pg, 'w-art-bad', page(mount_js('wallet: true, servicesApi: false, walletImage: "javascript:window.__pwned=22"')))
    pg.click(CHIP)
    art = pg.evaluate(BADGE)
    check('wallet', 'a walletImage that is not an address is dropped: the drawn badge', art and art['glyph'] and not art['img'], art)

    # attributes instead of a script
    goto(pg, 'w-data', page('', manual=False, body='<div id="auto" data-gg-account-menu data-name="Лёв Авдошин" data-hub-origin="__HUB__" data-services-api="false" data-wallet="true" '
                            'data-wallet-url="__SVC__/pass" data-logout-url="/logout"></div>'))
    got_attr = pg.evaluate("(() => { const a = document.querySelector('#auto a.gam-wallet'); return a && a.getAttribute('href'); })()")
    check('wallet', 'data-wallet="true" and data-wallet-url work without a script of the service', got_attr == svc + '/pass', got_attr)
    goto(pg, 'w-data2', page('', manual=False, body='<div id="auto" data-gg-account-menu data-name="Лёв Авдошин" data-hub-origin="__HUB__" data-services-api="false" data-wallet="true" data-wallet-url="false" '
                             'data-logout-url="/logout"></div>'))
    check('wallet', 'data-wallet-url="false" removes the badge', pg.evaluate("document.querySelector('#auto a.gam-wallet')") is None)

    # a long name, 390 px, dark
    ctx3 = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
    ctx3.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
    p3 = ctx3.new_page()
    goto(p3, 'w-phone', page(mount_js('wallet: true, ' + base) + 'menu.open();'))
    p3.wait_for_timeout(350)
    ph = p3.evaluate(BADGE)
    check('wallet', 'at 390 px the badge is inside the card (10 px to spare), 36 px high, and the page has no horizontal scroll',
          ph and ph['insideMenu'] and ph['rightRoom'] >= 10 and abs(ph['h'] - 36) < 0.6 and ph['scrollW'] <= ph['clientW'], ph)
    p3.screenshot(path=os.path.join(OUT, 'wallet-phone.png'))
    PAGES['w-long'] = page(mount_js("wallet: true, " + base + ", name: 'Александра Образцова-Константинопольская', email: 'aleksandra.obraztsova-konstantinopolskaya@global-generations.com'") + 'menu.open();')
    p3.goto(f'{svc}/app.html?p=w-long')
    p3.wait_for_function('window.GGAccountMenu !== undefined')
    p3.wait_for_timeout(350)
    longs = p3.evaluate(BADGE)
    outside = p3.evaluate('''() => { const m = document.querySelector('#account .gid-menu'), mr = m.getBoundingClientRect();
      return [...m.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > mr.right + 1 || r.left < mr.left - 1); }).length; }''')
    check('wallet', 'a very long name and e-mail with the badge: both wrap inside the card, the badge keeps its place under them, nothing sticks out',
          longs and outside == 0 and longs['last'] and abs(longs['left']) < 0.6 and 11.4 <= longs['gapText'] <= 12.6 and longs['scrollW'] <= longs['clientW'], (outside, longs))
    p3.screenshot(path=os.path.join(OUT, 'wallet-phone-long.png'))
    ctx3.close()
    PAGES['w-dark'] = page(mount_js("wallet: true, theme: 'dark', " + base) + 'menu.open();')
    pg.goto(f'{svc}/app.html?p=w-dark')
    pg.wait_for_function('window.GGAccountMenu !== undefined')
    pg.wait_for_timeout(350)
    dk = pg.evaluate(BADGE)
    check('wallet', 'in the dark theme the badge is the same black badge with the grey outline (Apple: on a very dark background it needs the outline)',
          dk and dk['bg'] == 'rgb(0, 0, 0)' and dk['color'] == 'rgb(255, 255, 255)' and dk['border'] == '1px solid rgb(166, 166, 166)', dk)
    pg.screenshot(path=os.path.join(OUT, 'wallet-dark.png'), clip={'x': 1040, 'y': 0, 'width': 400, 'height': 460})
    check('wallet', 'no page errors in the badge runs', not errs, errs[:3])
    ctx.close()


# ---------------------------------------------------------------------------------------------------------------- the kit defaults

def hub_defaults(b):
    """No hubOrigin = the production hub: every address of the menu is the canonical one. The real hub is never reached: the page answers for it."""
    svc, hub = ORIGINS['svc'], ORIGINS['hub']
    HUB['allowed'] = {svc}
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
    pg = ctx.new_page()
    seen = []

    def answer(route):
        seen.append({'url': route.request.url, 'method': route.request.method})
        route.fulfill(status=401, content_type='application/json', body='{"error":"unauthenticated"}',
                      headers={'Access-Control-Allow-Origin': svc, 'Access-Control-Allow-Credentials': 'true', 'Vary': 'Origin'})
    pg.route(re.compile(r'^https://id\.global-generations-edu\.com/'), answer)
    PAGES['d-def'] = page("window.menu = GGAccountMenu.mount('#account', {name: 'Лёв Авдошин', email: 'lev@global-generations.com', wallet: true, logoutUrl: '/logout'});")
    goto(pg, 'd-def', PAGES['d-def'])
    kit = pg.evaluate('GGAccountMenu.hub')
    check('defaults', 'GGAccountMenu.hub lists the canonical addresses: the origin id.global-generations-edu.com and the seven paths',
          kit == {'origin': HUB_URL, 'services': '/cabinet/', 'profile': '/cabinet/#profile', 'servicesApi': '/api/auth/service-links', 'wallet': WALLET_PATH,
                  'card': CARD_PATH, 'logout': '/api/auth/logout', 'login': '/login.html'}, kit)
    pg.click(CHIP)
    pg.wait_for_function('document.querySelector("#account a[data-gam-id=services]") && document.querySelector("#account a[data-gam-id=services]").getClientRects().length > 0', timeout=6000)
    links = pg.evaluate('''() => ({services: document.querySelector('#account a[data-gam-id="services"]').getAttribute('href'), profile: document.querySelector('#account a[data-gam-id="profile"]').getAttribute('href'),
      wallet: (document.querySelector('#account a.gam-wallet') || {getAttribute: () => null}).getAttribute('href'), title: document.querySelector('#account a[data-gam-id="profile"]').getAttribute('title')})''')
    check('defaults', 'no hubOrigin: «Мои сервисы» is <hub>/cabinet/, «Профиль GG ID» is <hub>/cabinet/#profile, the badge is <hub>/api/auth/wallet/apple.pkpass',
          links['services'] == HUB_URL + '/cabinet/' and links['profile'] == HUB_URL + '/cabinet/#profile' and links['wallet'] == HUB_URL + WALLET_PATH, links)
    check('defaults', 'the profile row says in its tooltip what is behind it: «Face ID / Touch ID (passkey)», with the slash', 'Face ID / Touch ID (passkey)' in (links['title'] or ''), links)
    check('defaults', 'the photo is asked once at the mount (the card) and the services list once on the first open, both at the canonical address, by GET, in that order',
          seen == [{'url': HUB_URL + CARD_PATH, 'method': 'GET'}, {'url': HUB_URL + '/api/auth/service-links', 'method': 'GET'}], seen)
    pg.keyboard.press('Escape')

    # an empty (an unset setting), null or unusable hubOrigin is the production hub too, not "no hub": a mistake in a setting must not take «Мои сервисы» away
    warns = []
    pg.on('console', lambda m: warns.append(m.text) if m.type == 'warning' else None)
    for pid, opt, warned in (('d-empty', "hubOrigin: ''", False), ('d-null', 'hubOrigin: null', False), ('d-bad', "hubOrigin: 'javascript:window.__pwned=31'", True),
                             ('d-text', "hubOrigin: 'not an address'", True), ('d-noscheme', "hubOrigin: 'id.global-generations-edu.com'", True), ('d-rel', "hubOrigin: '/cabinet'", True)):
        warns.clear()
        goto(pg, pid, page(f"window.menu = GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', {opt}, wallet: true, logoutUrl: '/logout'}});"))
        pg.click(CHIP)
        pg.wait_for_function('document.querySelector("#account a[data-gam-id=services]") && document.querySelector("#account a[data-gam-id=services]").getClientRects().length > 0', timeout=6000)
        hrefs = pg.evaluate("""() => [document.querySelector('#account a[data-gam-id="services"]').getAttribute('href'), (document.querySelector('#account a.gam-wallet') || {getAttribute: () => null}).getAttribute('href')]""")
        check('defaults', f'{opt}: the production hub (the cabinet and the pass at the canonical addresses), not "this very service", nothing runs',
              hrefs == [HUB_URL + '/cabinet/', HUB_URL + WALLET_PATH] and not pg.evaluate('window.__pwned || 0'), hrefs)
        check('defaults', f'{opt}: ' + ('a warning in the console says why' if warned else 'no warning (an unset setting is not a mistake)'),
              bool([w for w in warns if 'not an absolute address' in w]) == warned, warns)
        pg.keyboard.press('Escape')

    # hubOrigin false and the attribute "false": no hub addresses at all
    asked = len(seen)
    goto(pg, 'd-none', page('', manual=False, body='<div id="auto" data-gg-account-menu data-name="Лёв" data-hub-origin="false" data-logout-url="/logout"></div>'))
    pg.click('#auto .gid-chip')
    labels = pg.evaluate('[...document.querySelectorAll("#auto [role=menuitem]")].filter(e => e.getClientRects().length).map(e => e.textContent.trim())')
    check('defaults', 'data-hub-origin="false": no hub addresses, only «Выйти»', labels == ['Выйти'], labels)
    check('defaults', 'data-hub-origin="false": no request to the hub at all (no card either), initials only', len(seen) == asked and pg.evaluate("document.querySelectorAll('#auto .gam-photo').length") == 0, seen[asked:])

    # a page of a service signs out through its own sign-out; the hub is not asked to
    HUB['logouts'].clear()
    goto(pg, 'd-svc', page(mount_js('servicesApi: false', logout=False)))
    pg.click(CHIP)
    pg.click(MENU + ' [data-gam-id="logout"]')
    pg.wait_for_timeout(300)
    check('defaults', 'on a service page «Выйти» with no logoutUrl and no onLogout only tells the page (gam:select): the hub sign-out is never called from a foreign origin',
          not HUB['logouts'] and pg.url.startswith(svc + '/app.html'), (HUB['logouts'], pg.url))
    ctx.close()

    # a page of the hub itself: the sign-out of the hub, then its sign-in page (or logoutNext)
    ctx2 = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx2.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': hub + '/'}])
    hp = ctx2.new_page()
    errs = []
    hp.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
    for pid, extra, want in (('d-hub', '', '/login.html'), ('d-hub-next', ', logoutNext: "/after"', '/after')):
        ctx2.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': hub + '/'}])      # the hub clears it on the sign-out, as the real one does
        PAGES[pid] = page("window.menu = GGAccountMenu.mount('#account', {name: 'Лёв Авдошин', email: 'lev@global-generations.com', hubOrigin: '__HUB__', wallet: false, servicesApi: false" + extra + "});")
        HUB['logouts'].clear()
        hp.goto(f'{hub}/app.html?p={pid}')
        hp.wait_for_function('window.GGAccountMenu !== undefined')
        hp.click(CHIP)
        with hp.expect_navigation(url=hub + want):
            hp.click(MENU + ' [data-gam-id="logout"]')
        got = HUB['logouts'][0] if HUB['logouts'] else {}
        check('defaults', f'a page of the hub itself ({"logoutNext" if extra else "no options"}): «Выйти» POSTs /api/auth/logout with its own cookie and goes to {want}',
              len(HUB['logouts']) == 1 and 'gg_portal_session=test-session' in got.get('cookie', '') and got.get('origin') in (hub, None) and hp.url == hub + want, (HUB['logouts'], hp.url))
    check('defaults', 'no page errors on the hub pages', not errs, errs[:3])
    ctx2.close()


# ---------------------------------------------------------------------------------------------------------------- the photo of the person

AV_PATH = '/api/auth/avatars/f-1-long-black/face-256.png'        # a picture of GG ID as the hub names it: an own path of the hub
AV_PATH2 = '/api/auth/avatars/m-2-short-brown/face-256.png'
AV_HTTPS = HUB_URL + AV_PATH                                       # what the hub really puts into `photo`: a full https address
AV_MISSING = '/api/auth/avatars/missing-1/face-256.png'            # the server answers 404
AV_BROKEN = '/api/auth/avatars/broken-1/face-256.png'              # the server answers 200, but it is not a picture
DEMO_AVATAR = '/gg-id/account-menu/demo-avatar.svg'                # the picture of the demo page and of the screenshots

# the two circles of a menu (the chip and the head of the card): what is in them
AVS = """(root) => [...document.querySelectorAll(root + ' .gid-avatar')].map(a => { const i = a.querySelector('img.gam-photo'), cs = getComputedStyle(a);
  return {text: a.textContent, cls: a.className, hasImg: !!i, src: i ? i.getAttribute('src') : null, color: cs.color, w: a.offsetWidth, h: a.offsetHeight, after: getComputedStyle(a, '::after').content}; })"""
IMG_CSS = """() => [...document.querySelectorAll('#account img.gam-photo')].map(i => { const cs = getComputedStyle(i), p = i.parentNode.getBoundingClientRect(), r = i.getBoundingClientRect();
  return {fit: cs.objectFit, radius: cs.borderTopLeftRadius, pos: cs.position, filter: cs.filter, shadow: cs.boxShadow, opacity: cs.opacity, events: cs.pointerEvents, pw: p.width,
          dw: r.width - p.width, dh: r.height - p.height, dx: r.left - p.left, dy: r.top - p.top}; })"""
GEOM = """() => { const r = document.getElementById('account'), m = r.querySelector('.gid-menu'), n = v => Math.round(v * 100) / 100;
  const q = s => { const e = r.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [n(b.width), n(b.height)]; };
  const me = r.getBoundingClientRect();
  return {root: [n(me.width), n(me.height)], chip: q('.gid-chip'), chipAv: q('.gid-chip .gid-avatar'), chipName: q('.gid-chip-name'), head: q('.gid-menu-head'), headAv: q('.gid-menu-head .gid-avatar'),
          headTx: q('.gid-menu-head-tx'), menu: [m.offsetWidth, m.offsetHeight], scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth}; }"""
# a screenshot of a circle, read back through a canvas: how much of the round shape is the green of the generated picture (see make_png). g = where the circle lies in the shot, in device pixels.
# The thin ring of the avatar lies on the outer 1 px (out of 0.93 of the radius in the chip), so the band that must be picture all over ends at 0.9 of the radius.
PIXELS = """async ([b64, g]) => {
  const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const x = c.getContext('2d', {willReadFrequently: true}); x.drawImage(img, 0, 0);
  const w = img.width, h = img.height, R = g.R, cx = g.cx, cy = g.cy, d = x.getImageData(0, 0, w, h).data;
  const px = (i, j) => { const k = (Math.round(j) * w + Math.round(i)) * 4; return [d[k], d[k + 1], d[k + 2]]; };
  const green = p => Math.abs(p[0]) < 16 && Math.abs(p[1] - 170) < 16 && Math.abs(p[2] - 70) < 16;
  let inner = 0, innerBad = 0, band = 0, bandGreen = 0;
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const r = Math.hypot(i + .5 - cx, j + .5 - cy) / R;
    if (r < .8) { inner++; if (!green(px(i, j))) innerBad++; } else if (r < .9) { band++; if (green(px(i, j))) bandGreen++; }
  }
  const k = .98 * R, corners = [[cx - k, cy - k], [cx + k, cy - k], [cx - k, cy + k], [cx + k, cy + k]].filter(([i, j]) => i >= 0 && j >= 0 && i < w && j < h).map(([i, j]) => px(i, j));
  return {w, h, inner, innerBad, band, bandGreen, corners: corners.length, cornersGreen: corners.filter(green).length};
}"""
MOUNT_WITH = ("(o) => { if (window.menu) window.menu.destroy(); window.menu = GGAccountMenu.mount('#account', Object.assign({name: 'Лёв Авдошин', email: 'lev@global-generations.com', "
              "hubOrigin: '%s', servicesApi: false, wallet: false, logoutUrl: '/logout'}, o)); }")
# addresses that are no photos: the option and the answer of the hub are held to the same rule (the rule of the card of the sign-in pages)
BAD_PHOTOS = [
    ('data:', 'data:image/png;base64,iVBORw0KGgo='), ('javascript:', 'javascript:window.__pwned=41'), ('plain http to a stranger', 'http://example.com/a.png'),
    ('protocol-relative (//host)', '//evil.example/a.png'), ('backslash (/\\host)', '/\\evil.example/a.png'), ('a tab between the slashes', '/\t/evil.example/a.png'),
    ('a space', 'https://example.com/a b.png'), ('a double quote', 'https://example.com/a"b.png'), ('a single quote', "https://example.com/a'b.png"),
    ('a less-than sign', 'https://example.com/a<b.png'), ('a greater-than sign', 'https://example.com/a>b.png'), ('a backslash inside', 'https://example.com/a\\b.png'),
    ('a control character', 'https://example.com/a\x01b.png'), ('over 500 characters', 'https://example.com/' + 'a' * 500 + '.png'), ('a bare word', 'avatar.png'),
    ('a relative address', './a.png'), ('ftp', 'ftp://example.com/a.png'), ('blob', 'blob:https://example.com/0000'), ('https with nothing after it', 'https://'),
]


def circle_pixels(pg, sel, scale=2):
    """The shot of one round avatar and where its circle lies in it. The box of the avatar is fractional, so the shot is cut on whole pixels around it and the centre is worked out from the box
    (a shot of the element itself is rounded outwards and the circle would sit off its middle). `scale` is the device_scale_factor of the context."""
    box = pg.locator(sel).first.bounding_box()
    x0, y0 = math.floor(box['x']) - 2, math.floor(box['y']) - 2
    clip = {'x': x0, 'y': y0, 'width': math.ceil(box['width']) + 5, 'height': math.ceil(box['height']) + 5}
    geo = {'cx': (box['x'] + box['width'] / 2 - x0) * scale, 'cy': (box['y'] + box['height'] / 2 - y0) * scale, 'R': box['width'] / 2 * scale}
    return pg.evaluate(PIXELS, [base64.b64encode(pg.screenshot(clip=clip)).decode('ascii'), geo])


def round_ok(px):
    """The picture fills the whole round shape: nothing but the picture inside 80 percent of the radius (letters included), 97 percent of the band out to 90 percent, the corners of the box stay empty."""
    return px['inner'] > 100 and px['innerBad'] == 0 and px['band'] > 20 and px['bandGreen'] >= px['band'] * 0.97 and px['corners'] == 4 and px['cornersGreen'] == 0


def photo(b):
    """The photo of the person (option photo, kit 2026-10-15.3): the avatar chosen in GG ID goes over the initials in the chip and in the head of the card.
    An address in the option draws it and asks nothing; false draws the initials and asks nothing; not said asks the hub once per person (GET /api/auth/card, real CORS with the cookie)."""
    svc, hub = ORIGINS['svc'], ORIGINS['hub']
    svc_host, hub_host = urllib.parse.urlparse(svc).netloc, urllib.parse.urlparse(hub).netloc
    HUB['allowed'] = {svc}
    HUB['card_mode'], HUB['card_delay'], HUB['card_body'], HUB['card_photo'] = 'nophoto', 0, None, AV_PATH
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)
    ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
    errs, warns, reqs = [], [], []
    pg = ctx.new_page()
    # WebKit reports the answer the browser blocked on purpose (the run "without CORS headers") as a page error, other engines only log it
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}') if 'access control checks' not in str(e) else None)
    pg.on('console', lambda m: warns.append(m.text) if m.type == 'warning' else None)
    pg.on('request', lambda r: reqs.append(r.url))
    base = 'servicesApi: false'
    avs = lambda root='#account': pg.evaluate(AVS, root)

    def up(n=2, root='#account', timeout=8000):
        pg.wait_for_function(f"document.querySelectorAll('{root} .gid-avatar.gam-av--photo').length === {n}", timeout=timeout)

    def gone(root='#account', timeout=8000):
        pg.wait_for_function(f"document.querySelectorAll('{root} img.gam-photo').length === 0", timeout=timeout)

    # --- an address in the option: both circles, nothing is asked of the hub
    goto(pg, 'p-opt', page(mount_js(f"photo: '{AV_PATH}', {base}")))
    up()
    av = avs()
    check('photo', 'photo as an own path draws the picture in both circles, the chip and the head of the card; the path is a path of this page (the service names its own file)',
          len(av) == 2 and all(a['hasImg'] for a in av) and [a['src'] for a in av] == [svc + AV_PATH] * 2, av)
    check('photo', 'an address in the option asks nothing of the hub (no card request)', len(HUB['cards']) == 0, HUB['cards'])
    check('photo', 'the picture is requested from the page\'s own server, without a Referer (referrerpolicy no-referrer)',
          len(AVATARS) >= 1 and all(a['host'] == svc_host and a['referer'] is None for a in AVATARS), AVATARS)
    attrs = pg.evaluate("() => [...document.querySelectorAll('#account img.gam-photo')].map(i => [i.getAttribute('alt'), i.getAttribute('referrerpolicy'), i.getAttribute('decoding'), "
                        "i.parentNode.classList.contains('gid-avatar'), i.parentNode.querySelectorAll('img').length, i.hasAttribute('srcset'), i.hasAttribute('onerror')])")
    check('photo', 'the img is alt="" (the name is in the text next to it), referrerpolicy no-referrer, decoding async, one per circle, no srcset, no handler attribute',
          attrs == [['', 'no-referrer', 'async', True, 1, False, False]] * 2, attrs)
    check('photo', 'the initials stay in the DOM under the picture and turn transparent while it shows (the ring of the avatar is drawn over it)',
          [a['text'] for a in av] == ['ЛА', 'ЛА'] and all(a['color'] == 'rgba(0, 0, 0, 0)' and a['after'] in ('""', "''") for a in av), av)
    pg.click(CHIP)
    pg.wait_for_timeout(450)
    css = pg.evaluate(IMG_CSS)
    check('photo', 'the picture fills the circle and nothing more: absolute, the whole box, object-fit cover, round, no filter, no shadow, no mouse of its own',
          len(css) == 2 and all(c['fit'] == 'cover' and c['pos'] == 'absolute' and c['radius'] == '50%' and c['filter'] == 'none' and c['shadow'] == 'none' and c['opacity'] == '1'
                                and c['events'] == 'none' and c['pw'] > 20 and abs(c['dw']) < 0.01 and abs(c['dh']) < 0.01 and abs(c['dx']) < 0.01 and abs(c['dy']) < 0.01 for c in css), css)
    av = avs()
    check('photo', 'the two circles keep the sizes of the kit: 28 px in the chip, 44 px in the head of the card', [a['w'] for a in av] == [28, 44] and [a['h'] for a in av] == [28, 44], av)
    for tag, sel in (('the chip', '#account .gid-chip .gid-avatar'), ('the head of the card', '#account .gid-menu-head .gid-avatar')):
        px = circle_pixels(pg, sel)
        check('photo', f'{tag}, light: the picture fills the whole round shape (a wide picture is cut to its middle, not squeezed), no letter shows through, the corners stay empty', round_ok(px), px)
    pg.keyboard.press('Escape')
    # the dark theme, the same pixels
    goto(pg, 'p-opt-dark', page(mount_js(f"photo: '{AV_PATH}', theme: 'dark', {base}") + 'menu.open();'))
    up()
    pg.wait_for_timeout(450)
    for tag, sel in (('the chip', '#account .gid-chip .gid-avatar'), ('the head of the card', '#account .gid-menu-head .gid-avatar')):
        px = circle_pixels(pg, sel)
        check('photo', f'{tag}, dark: the same, the picture fills the round shape', round_ok(px), px)

    # --- the circle keeps its size: with a picture, without one, on a wide screen and on a phone
    def geom(pid, extra, width, wait_img):
        pg.set_viewport_size({'width': width, 'height': 900})
        goto(pg, pid, page(mount_js(extra) + 'menu.open();'))
        if wait_img:
            up()
        pg.wait_for_timeout(450)
        return pg.evaluate(GEOM)
    for width in (1440, 390):
        off = geom('p-g0', f'photo: false, wallet: true, {base}', width, False)
        on = geom('p-g1', f"photo: '{AV_PATH}', wallet: true, {base}", width, True)
        check('photo', f'{width} px: every size is the same with and without the picture (the chip, both circles, the name, the head of the card, the card itself) and the page has no sideways scroll',
              on == off and on['scrollW'] <= on['clientW'] and on['chipAv'] == [28, 28] and on['headAv'] == [44, 44], (off, on))
    pg.set_viewport_size({'width': 1440, 'height': 900})

    # --- false and the attribute: initials, no request
    HUB['card_mode'] = 'ok'
    goto(pg, 'p-false', page(mount_js(f'photo: false, {base}')))
    pg.wait_for_timeout(500)
    av = avs()
    check('photo', 'photo false: the initials only, and the hub is not asked even though it would give a picture', len(HUB['cards']) == 0 and not any(a['hasImg'] for a in av) and [a['text'] for a in av] == ['ЛА', 'ЛА'], (av, HUB['cards']))
    data_menu = ('<div id="auto" data-gg-account-menu data-name="Лёв Авдошин" data-email="lev@global-generations.com" data-hub-origin="__HUB__" data-services-api="false" '
                 'data-wallet="false" data-logout-url="/logout" %s></div>')
    goto(pg, 'p-data-false', page('', manual=False, body=data_menu % 'data-photo="false"'))
    pg.wait_for_timeout(500)
    av = avs('#auto')
    check('photo', 'data-photo="false" is the same: initials, no request (the string false is the boolean false, as in the other attributes)',
          len(HUB['cards']) == 0 and len(av) == 2 and not any(a['hasImg'] for a in av), (av, HUB['cards']))
    goto(pg, 'p-data-path', page('', manual=False, body=data_menu % f'data-photo="{AV_PATH}"'))
    up(root='#auto')
    av = avs('#auto')
    check('photo', 'data-photo="<path>" draws the picture without a line of script, and asks nothing', len(HUB['cards']) == 0 and [a['src'] for a in av] == [svc + AV_PATH] * 2, (av, HUB['cards']))

    # --- not said: the kit asks the hub once
    HUB['card_mode'], HUB['card_photo'] = 'ok', AV_PATH
    goto(pg, 'p-hub', page(mount_js(base)))
    up()
    cards = list(HUB['cards'])
    check('photo', 'photo not said: the kit asks the card of the hub once, at the mount (GET, cross-origin, the hub cookie goes along, JSON asked for)',
          len(cards) == 1 and cards[0]['origin'] == svc and 'gg_portal_session=test-session' in cards[0]['cookie'] and 'application/json' in (cards[0]['accept'] or ''), cards)
    av = avs()
    check('photo', 'the own path of the answer is completed with the hub address: the picture comes from the hub, without a Referer',
          [a['src'] for a in av] == [hub + AV_PATH] * 2 and len(AVATARS) >= 1 and all(a['host'] == hub_host and a['referer'] is None for a in AVATARS), (av, AVATARS))
    pg.evaluate("window.menu.update({}); window.menu.update({placement: 'start'}); window.menu.update({name: 'Лёв Авдошин', email: 'LEV.AVDOSHIN@global-generations.com'}); window.menu.update({theme: 'dark'}); window.menu.update({theme: 'light'});")
    pg.wait_for_timeout(600)
    up()
    check('photo', 'update() five times for the same person (the e-mail in another case, a theme, a placement) sends no second request, and the picture stays', len(HUB['cards']) == 1, HUB['cards'])
    # a second menu for the same person shares the answer, another person asks once more
    goto(pg, 'p-two', page(mount_js(base) + "document.getElementById('account').insertAdjacentElement('afterend', Object.assign(document.createElement('div'), {id: 'second'}));"
                           + f"GGAccountMenu.mount('#second', {opts_js(base)});"))
    pg.wait_for_function("document.querySelectorAll('img.gam-photo').length === 4")
    check('photo', 'two menus on a page for the same person make one request, both draw the picture', len(HUB['cards']) == 1, HUB['cards'])
    pg.evaluate("(() => { document.getElementById('second').insertAdjacentElement('afterend', Object.assign(document.createElement('div'), {id: 'third'})); "
                "GGAccountMenu.mount('#third', {name: 'Вера Петрова', email: 'vera.petrova@global-generations.com', hubOrigin: '" + hub + "', wallet: false, servicesApi: false, logoutUrl: '/logout'}); })()")
    pg.wait_for_function("document.querySelectorAll('img.gam-photo').length === 6")
    check('photo', 'a third menu for another person asks once more (two requests in all)', len(HUB['cards']) == 2, HUB['cards'])
    # another person in one menu: the old picture goes at once, never shown for someone else
    goto(pg, 'p-person', page(mount_js(base)))
    up()
    HUB['card_photo'] = AV_PATH2
    n = pg.evaluate("() => { window.menu.update({name: 'Вера Петрова', email: 'vera.petrova@global-generations.com'}); return document.querySelectorAll('#account img.gam-photo').length; }")
    check('photo', 'update() with another person: the picture of the one before is gone at once (initials), it is never shown for someone else', n == 0 and len(HUB['cards']) == 1, (n, HUB['cards']))
    pg.wait_for_function(f"document.querySelectorAll('#account img.gam-photo').length === 2 && document.querySelector('#account img.gam-photo').getAttribute('src').endsWith('{AV_PATH2}')")
    check('photo', 'then one request for the new person and her picture', len(HUB['cards']) == 2, HUB['cards'])
    pg.evaluate("window.menu.update({name: 'Лёв Авдошин', email: 'lev.avdoshin@global-generations.com'})")
    pg.wait_for_function(f"document.querySelector('#account img.gam-photo') && document.querySelector('#account img.gam-photo').getAttribute('src').endsWith('{AV_PATH}')")
    check('photo', 'back to the first person: the answer of the page is reused, no third request', len(HUB['cards']) == 2, HUB['cards'])
    r = pg.evaluate("() => { window.menu.update({photo: false}); return document.querySelectorAll('#account img.gam-photo').length; }")
    check('photo', 'update({photo: false}) takes the picture away at once and asks nothing', r == 0 and len(HUB['cards']) == 2, (r, HUB['cards']))
    pg.evaluate("window.menu.update({photo: null})")
    up()
    check('photo', 'update({photo: null}) is "not said" again: the picture comes back from the answer the page already has, no new request', len(HUB['cards']) == 2, HUB['cards'])
    pg.evaluate(f"window.menu.update({{photo: '{AV_PATH2}'}})")
    pg.wait_for_function(f"document.querySelector('#account img.gam-photo') && document.querySelector('#account img.gam-photo').getAttribute('src').endsWith('{AV_PATH2}')")
    check('photo', 'update({photo: "<path>"}) puts the service\'s own picture over the hub one', [a['src'] for a in avs()] == [svc + AV_PATH2] * 2 and len(HUB['cards']) == 2, avs())

    # --- no hub, no request
    PAGES['p-nohub'] = page(f"GGAccountMenu.mount('#account', {{name: 'Лёв Авдошин', logoutUrl: '/logout', {MIN}}});")
    goto(pg, 'p-nohub', PAGES['p-nohub'])
    pg.wait_for_timeout(500)
    check('photo', 'hubOrigin false and no photo: no request and no picture', len(HUB['cards']) == 0 and not any(a['hasImg'] for a in avs()), HUB['cards'])

    # --- every refusal of the hub is silent: the initials stay, one request, the menu works
    for mode, why in (('nologin', '401: no hub session'), ('forbidden', '403: no level'), ('notfound', '404: no card'), ('error', '503: the hub is down'),
                      ('broken', 'broken JSON'), ('array', 'an answer of another shape'), ('no_cors', 'an answer without CORS headers (the browser blocks it)'),
                      ('nophoto', 'a card with no `photo` key (the person has chosen no avatar)')):
        HUB['card_mode'] = mode
        goto(pg, 'p-' + mode, page(mount_js(base)))
        pg.wait_for_timeout(600)
        av = avs()
        pg.click(CHIP)
        s = state(pg)
        pg.keyboard.press('Escape')
        check('photo', f'{why}: silent, the initials stay, one request and no retry, the menu works',
              not any(a['hasImg'] for a in av) and [a['text'] for a in av] == ['ЛА', 'ЛА'] and len(HUB['cards']) == 1 and s['open'], (av, len(HUB['cards']), s))
    HUB['card_mode'] = 'custom'
    for value in (None, '', '   ', 7, True, {}, [], ['a'], {'src': AV_PATH}):
        HUB['card_body'] = {'photo': value}
        goto(pg, 'p-photo-kinds', page(mount_js(base)))
        pg.wait_for_timeout(350)
        check('photo', f'`photo` in the answer is {json.dumps(value)}: no picture, no error', not any(a['hasImg'] for a in avs()) and len(HUB['cards']) == 1, avs())
    # slower than 4 seconds is no answer: the request is cut off, the late picture never comes
    HUB['card_mode'], HUB['card_delay'] = 'ok', 6.0
    goto(pg, 'p-slow', page(mount_js(base)))
    pg.wait_for_timeout(6600)
    check('photo', 'an answer that takes longer than 4 seconds is dropped (the request is cut off at 4 s, the picture that would come at 6 s never shows), one request',
          not any(a['hasImg'] for a in avs()) and len(HUB['cards']) == 1, (avs(), HUB['cards']))
    HUB['card_delay'] = 0
    check('photo', 'no page error in all the refusals', not errs, errs[:3])

    # --- addresses that are no photos, in the option and in the answer of the hub: dropped, nothing runs, nothing leaves the machine
    goto(pg, 'p-bad', page(''))
    mount_with = MOUNT_WITH % hub
    problems_opt = []
    for label, value in BAD_PHOTOS:
        warns.clear()
        n = len(reqs)
        pg.evaluate(mount_with, {'photo': value})
        pg.evaluate('window.menu.update({}); window.menu.update({name: "Лёв Авдошин"})')
        pg.wait_for_timeout(250)
        ours = [w for w in warns if 'GGAccountMenu: photo' in w]
        foreign = [u for u in reqs[n:] if not u.startswith(('http://localhost:', 'data:', 'about:'))]
        imgs = pg.evaluate("document.querySelectorAll('#account img').length")
        if imgs or foreign or pg.evaluate('window.__pwned || 0') or len(ours) != 1 or len(HUB['cards']):
            problems_opt.append((label, imgs, foreign[:1], len(ours), len(HUB['cards'])))
    check('photo', f'the option: {len(BAD_PHOTOS)} kinds of address that are no photo (data:, javascript:, http:, //host, /\\host, a tab, a space, quotes, < >, a backslash, a control character, over 500 characters, a word, '
          'a relative address, ftp:, blob:) draw nothing, run nothing, request nothing, ask nothing of the hub, and say so once in the console', not problems_opt, problems_opt[:3])
    HUB['card_mode'] = 'custom'
    problems_ans = []
    for i, (label, value) in enumerate(BAD_PHOTOS):
        HUB['card_body'] = {'photo': value}
        n, cn = len(reqs), len(HUB['cards'])
        pg.evaluate(mount_with, {'email': f'bad{i}@global-generations.com'})
        pg.wait_for_timeout(250)
        foreign = [u for u in reqs[n:] if not u.startswith(('http://localhost:', 'data:', 'about:'))]
        imgs = pg.evaluate("document.querySelectorAll('#account img').length")
        if imgs or foreign or pg.evaluate('window.__pwned || 0') or len(HUB['cards']) != cn + 1:
            problems_ans.append((label, imgs, foreign[:1], len(HUB['cards']) - cn))
    check('photo', f'the answer of the hub: the same {len(BAD_PHOTOS)} kinds of address are dropped the same way (silent: the hub is not blamed in the console), the initials stay', not problems_ans, problems_ans[:3])
    HUB['card_mode'], HUB['card_body'] = 'ok', None
    cn = len(HUB['cards'])
    pg.evaluate(mount_with, {'photo': '   ', 'email': 'blank@global-generations.com'})
    up()
    check('photo', 'a blank string in the option is "not said" (an unset setting, as with hubOrigin): the hub is asked once and its picture is drawn', len(HUB['cards']) == cn + 1, (cn, len(HUB['cards'])))
    check('photo', 'no page error with the bad addresses', not errs, errs[:3])

    # --- a full https address (what the hub really sends) is drawn, with no Referer
    seen_h = []

    def serve(route):
        seen_h.append({'url': route.request.url, 'referer': route.request.headers.get('referer')})
        route.fulfill(status=200, content_type='image/png', body=PNG)
    pg.route(re.compile(r'^https://id\.global-generations-edu\.com/api/auth/avatars/'), serve)
    HUB['card_mode'] = 'ok'
    goto(pg, 'p-https', page(mount_js(f"photo: '{AV_HTTPS}', {base}")))
    up()
    check('photo', 'an https address in the option is drawn as it is, requested without a Referer', [a['src'] for a in avs()] == [AV_HTTPS] * 2 and seen_h and all(s['referer'] is None for s in seen_h) and not HUB['cards'], (avs(), seen_h))
    HUB['card_mode'], HUB['card_body'] = 'custom', {'photo': AV_HTTPS}
    goto(pg, 'p-https2', page(mount_js(base)))
    up()
    check('photo', 'an https address in the answer of the hub (what the hub really sends) is drawn as it is', [a['src'] for a in avs()] == [AV_HTTPS] * 2 and len(HUB['cards']) == 1, (avs(), HUB['cards']))
    pg.unroute(re.compile(r'^https://id\.global-generations-edu\.com/api/auth/avatars/'))

    # --- a picture that does not load gives the initials back, once, and is not tried again on every redraw
    for label, path in (('a missing file (404)', AV_MISSING), ('a file that is not a picture (200, text)', AV_BROKEN)):
        goto(pg, 'p-err', page(mount_js(f"photo: '{path}', {base}") + 'menu.open();'))
        gone()
        av = avs()
        check('photo', f'{label} in the option: the picture is taken out, the letters are back (navy, not transparent), no leftover class', not any(a['hasImg'] for a in av) and [a['text'] for a in av] == ['ЛА', 'ЛА']
              and all(a['color'] == 'rgb(19, 68, 93)' and 'gam-av--' not in a['cls'] and a['after'] in ('normal', 'none') for a in av), av)
        pg.wait_for_timeout(300)
        n = len(AVATARS)
        pg.evaluate("window.menu.update({}); window.menu.update({name: 'Лёв Авдошин'}); window.menu.update({theme: 'dark'}); window.menu.update({theme: 'light'});")
        pg.wait_for_timeout(500)
        check('photo', f'{label}: a redraw (update without a new photo) does not ask for the same picture again', len(AVATARS) == n and not any(a['hasImg'] for a in avs()), (n, len(AVATARS)))
        pg.evaluate(f"window.menu.update({{photo: '{path}'}})")
        pg.wait_for_timeout(600)
        check('photo', f'{label}: the service saying photo again is a new try (one more request), and it fails the same way back to the initials', len(AVATARS) > n and not any(a['hasImg'] for a in avs()), (n, len(AVATARS)))
    HUB['card_mode'], HUB['card_body'] = 'custom', {'photo': AV_MISSING}
    goto(pg, 'p-err2', page(mount_js(base)))
    gone()
    pg.wait_for_timeout(300)
    n = len(AVATARS)
    pg.evaluate("window.menu.update({}); window.menu.update({name: 'Лёв Авдошин'})")
    pg.wait_for_timeout(500)
    check('photo', 'a picture of the hub that is gone: initials, one card request, no second try on a redraw', len(HUB['cards']) == 1 and len(AVATARS) == n and not any(a['hasImg'] for a in avs()), (len(HUB['cards']), n, len(AVATARS)))

    # --- the picture arrives while the card is open: nothing jumps
    HUB['card_mode'], HUB['card_delay'], HUB['card_body'] = 'ok', 1.0, None
    goto(pg, 'p-late', page(mount_js(base)))
    pg.click(CHIP)
    pg.keyboard.press('ArrowDown')
    pg.evaluate("window.__item = document.querySelector('#account [role=menuitem]');")
    s0 = state(pg)
    up()
    s1 = state(pg)
    check('photo', 'the picture arrives after the card was opened: the card stays open, the focus does not move, the rows are not redrawn',
          s0['open'] and s1 == s0 and s1['focus'] == 0 and pg.evaluate("document.querySelector('#account [role=menuitem]') === window.__item"), (s0, s1))
    pg.keyboard.press('Escape')
    # a menu that is destroyed before the answer comes: the answer is dropped, nothing breaks
    HUB['card_delay'] = 0.8
    goto(pg, 'p-destroy', page(mount_js(base) + 'menu.destroy();'))
    pg.wait_for_timeout(1400)
    check('photo', 'destroy() before the answer: the late answer is dropped, nothing is drawn back, no error', pg.evaluate("document.getElementById('account').children.length") == 0 and not errs, errs[:3])
    HUB['card_delay'] = 0
    check('photo', 'no page error in the photo runs', not errs, errs[:3])
    ctx.close()

    # --- the screenshots: a picture and the initials back, 1440 and 390, light and dark
    dark_head = '<style>body{background:#06141d}header{background:#0a1f2c;border-color:#17384a;color:#fff}</style>'
    for width, height, clip in ((1440, 640, {'x': 1040, 'y': 0, 'width': 400, 'height': 620}), (390, 700, None)):
        for theme in ('light', 'dark'):
            for fallback in (False, True):
                ctx = b.new_context(viewport={'width': width, 'height': height}, device_scale_factor=2)
                ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
                p2 = ctx.new_page()
                src = AV_MISSING if fallback else DEMO_AVATAR
                goto(p2, 'p-shot', page(mount_js(f"photo: '{src}', theme: '{theme}', wallet: true, {base}") + 'menu.open();', head=dark_head if theme == 'dark' else ''))
                if fallback:
                    p2.wait_for_function("document.querySelectorAll('#account img.gam-photo').length === 0")
                else:
                    p2.wait_for_function("document.querySelectorAll('#account .gid-avatar.gam-av--photo').length === 2")
                p2.evaluate('document.fonts.ready.then(() => 1)')
                p2.mouse.move(2, 2)
                p2.wait_for_timeout(450)
                name = f'photo-{"fallback-" if fallback else ""}{"desktop" if width == 1440 else "390"}-{theme}.png'
                p2.screenshot(path=os.path.join(OUT, name), **({'clip': clip} if clip else {}))
                ctx.close()


# ---------------------------------------------------------------------------------------------------------------- the demo page

DEMO_ROWS = "document.querySelectorAll('#account .gam-svc').length"
DEMO_LINK = """() => { const a = document.querySelector('#account a[data-gam-id="services"]'), b = document.querySelector('#account button[data-gam-id="services"]');
  return {link: !!a && !a.hidden, btn: !!b && !b.hidden}; }"""


# ---------------------------------------------------------------------------------------------------------------- the bar of a sign-in on behalf

IMP_SETUP = """
window.__ev = []; window.__until = Date.now() + 47 * 60000;
window.__bar = function (opts) {
  var el = document.getElementById('imp');
  if (!el) {
    el = document.createElement('div'); el.id = 'imp';
    document.querySelector('header').insertAdjacentElement('afterend', el);
    el.addEventListener('gimp:end', function () { window.__ev.push('end'); });
    el.addEventListener('gimp:over', function () { window.__ev.push('over'); });
  }
  return GGAccountMenu.impBar(el, opts);
};
"""
HM = "(() => { const d = new Date(window.__until); return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); })()"
IMP_PROBE = """() => {
  const b = document.getElementById('imp'), r = b.getBoundingClientRect(), hd = document.querySelector('header').getBoundingClientRect(), cs = getComputedStyle(b);
  const btn = b.querySelector('.gimp-btn'), br = btn ? btn.getBoundingClientRect() : null, l1 = b.querySelector('.gimp-l1'), l2 = b.querySelector('.gimp-l2');
  const ok = ['div', 'b', 'span', 'a', 'button', 'form', 'input', 'svg', 'path', 'rect', 'circle', 'line'];
  const bad = [...b.querySelectorAll('*')].map(e => e.tagName.toLowerCase()).filter(t => ok.indexOf(t) < 0);
  const lum = c => { const f = x => { x /= 255; return x <= .03928 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); }; return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
  const rgb = v => { const m = v.match(/rgba?\\(([^)]+)\\)/); const p = m[1].split(',').map(Number); return p.length > 3 ? p : p.concat([1]); };
  const over = (t, bg) => [t[0] * t[3] + bg[0] * (1 - t[3]), t[1] * t[3] + bg[1] * (1 - t[3]), t[2] * t[3] + bg[2] * (1 - t[3])];
  const ratio = (a, c) => { const x = lum(a), y = lum(c); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const bg = rgb(cs.backgroundColor).slice(0, 3);
  return {cls: b.className, role: b.getAttribute('role'), label: b.getAttribute('aria-label'), state: b.getAttribute('data-gimp-state'),
    l1: l1 ? l1.textContent : null, l2: l2 ? l2.textContent : null, l2role: l2 ? l2.getAttribute('role') : null,
    btn: btn ? btn.textContent.trim() : null, tag: btn ? btn.tagName.toLowerCase() : null, href: btn ? btn.getAttribute('href') : null, form: !!b.querySelector('form'),
    left: Math.round(r.left), width: Math.round(r.width), vw: innerWidth, top: Math.round(r.top), headBottom: Math.round(hd.bottom), h: Math.round(r.height),
    bg: cs.backgroundColor, color: cs.color, padTop: cs.paddingTop, padLeft: cs.paddingLeft, mb: cs.marginBottom,
    btnW: br ? Math.round(br.width) : 0, btnH: br ? Math.round(br.height) : 0, btnRight: br ? Math.round(r.right - br.right) : 0,
    hscroll: document.documentElement.scrollWidth > document.documentElement.clientWidth, bad: bad, busy: btn ? btn.getAttribute('aria-busy') : null,
    disabled: btn ? !!btn.disabled : null, err: !!b.querySelector('.gimp-err'), errRole: (b.querySelector('.gimp-err') || {getAttribute: () => null}).getAttribute('role'),
    c1: l1 ? ratio(rgb(getComputedStyle(l1).color).slice(0, 3), bg) : 0,
    c2: l2 ? ratio(over(rgb(getComputedStyle(l2).color), bg), bg) : 0,
    cb: btn ? ratio(rgb(getComputedStyle(btn).color).slice(0, 3), rgb(getComputedStyle(btn).backgroundColor).slice(0, 3)) : 0,
    pwned: window.__pwned || 0};
}"""


def imp_bar(b):
    """The one bar of a sign-in on behalf of a person (GGAccountMenu.impBar): texts, the three ways back, busy and failed states, the end of the time, safety, looks."""
    svc = ORIGINS['svc']
    HUB['allowed'] = {svc}
    errs = []

    def new_page(width, height, scheme='light'):
        ctx = b.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme)
        ctx.add_cookies([{'name': 'gg_portal_session', 'value': 'test-session', 'url': svc + '/'}])
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        return ctx, pg

    ON = "window.bar = window.__bar({name: 'Иван Образцов', until: window.__until, endHref: '/logout'});"

    # --- a strip over the whole width right under the header, the words, the way back as a link
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-on', page(IMP_SETUP + mount_js() + ON))
    r = pg.evaluate(IMP_PROBE)
    hm = pg.evaluate(HM)
    check('imp', 'the bar says whose GG ID is open and until when: «Вы смотрите как <имя>» and «Только просмотр до ЧЧ:ММ. Изменения не сохраняются.»',
          r['l1'] == 'Вы смотрите как Иван Образцов' and r['l2'] == f'Только просмотр до {hm}. Изменения не сохраняются.', (r['l1'], r['l2'], hm))
    check('imp', 'the way back is one white button «Вернуться к себе» (a link for endHref)', r['btn'] == 'Вернуться к себе' and r['tag'] == 'a' and (r['href'] or '').endswith('/logout'), r)
    check('imp', 'a region with a name for the screen readers (Вход от имени)', r['role'] == 'region' and r['label'] == 'Вход от имени', r)
    check('imp', 'a strip over the whole width: from the left edge to the right edge of the window, its top at the bottom of the header (right under the menu)',
          r['left'] == 0 and r['width'] == r['vw'] and abs(r['top'] - r['headBottom']) <= 1, r)
    check('imp', 'navy 13445d with white words, padding 18 and 28 px, 20 px of air below it, the button at the right edge, no sideways scroll',
          r['bg'] == 'rgb(19, 68, 93)' and r['color'] == 'rgb(255, 255, 255)' and r['padTop'] == '18px' and r['padLeft'] == '28px' and r['mb'] == '20px'
          and r['btnRight'] == 28 and r['btnH'] >= 38 and not r['hscroll'], r)
    check('imp', 'contrast: the first line, the second line and the label of the button are at least 4.5 to 1', r['c1'] >= 4.5 and r['c2'] >= 4.5 and r['cb'] >= 4.5, (r['c1'], r['c2'], r['cb']))
    check('imp', 'nothing but the allowed tags in the bar', r['bad'] == [], r['bad'])
    pg.screenshot(path=os.path.join(OUT, 'imp-desktop-light.png'), clip={'x': 0, 'y': 0, 'width': 1440, 'height': 220})
    # the account menu opens above the bar, the strip does not cover the card
    pg.click(CHIP)
    pg.wait_for_selector(MENU + ':not([hidden])')
    ov = pg.evaluate("""(() => { const m = document.querySelector('#account .gid-menu').getBoundingClientRect(), b = document.getElementById('imp').getBoundingClientRect();
      const y = Math.max(m.top, b.top) + 10, x = m.left + m.width / 2, e = document.elementFromPoint(x, y); return {overlap: m.top < b.bottom && m.bottom > b.top, inMenu: !!(e && e.closest('.gid-menu'))}; })()""")
    check('imp', 'the account menu opens over the bar', ov['overlap'] and ov['inMenu'], ov)
    pg.keyboard.press('Escape')
    # the keyboard: from the chip one Tab reaches the button, with the ring of the kit (2 px)
    pg.focus(CHIP)
    pg.keyboard.press('Tab')
    ring = pg.evaluate("(() => { const a = document.activeElement, s = getComputedStyle(a); return {cls: a.className, outline: [s.outlineStyle, s.outlineWidth, s.outlineColor]}; })()")
    check('imp', 'one Tab from the chip reaches the button «Вернуться к себе»; it has a visible ring of 2 px', 'gimp-btn' in ring['cls'] and ring['outline'][0] == 'solid' and ring['outline'][1] == '2px', ring)
    # the link goes back to the own session
    pg.click('#imp .gimp-btn')
    pg.wait_for_url('**/logout')
    check('imp', 'the link leads to the address of the service (the own sign-out)', pg.url.endswith('/logout'), pg.url)
    ctx.close()

    # --- the phone, the dark theme: the same strip, the button on the whole width
    ctx, pg = new_page(390, 844, 'dark')
    goto(pg, 'imp-phone', page(IMP_SETUP + mount_js() + ON))
    r = pg.evaluate(IMP_PROBE)
    check('imp', '390 px, dark theme: the same navy strip over the whole width, the button on the whole width of the strip (16 px of padding), no sideways scroll',
          r['bg'] == 'rgb(19, 68, 93)' and r['left'] == 0 and r['width'] == 390 and r['btnW'] == 390 - 32 and r['padLeft'] == '16px' and not r['hscroll'], r)
    check('imp', '390 px: the strip sits right under the header', abs(r['top'] - r['headBottom']) <= 1, r)
    pg.screenshot(path=os.path.join(OUT, 'imp-phone-dark.png'), clip={'x': 0, 'y': 0, 'width': 390, 'height': 260})
    ctx.close()

    # --- the way back is the service's own call: busy, one call, false = it stayed, a failure is said in words, a silent one is not
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-fn', page(IMP_SETUP + mount_js() + """window.__calls = 0;
      window.bar = window.__bar({name: 'Иван Образцов', until: window.__until, onEnd: function () { window.__calls++; return new Promise(function (res, rej) { window.__settle = {res: res, rej: rej}; }); }});"""))
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'onEnd: the way back is a button', r['tag'] == 'button' and r['btn'] == 'Вернуться к себе' and not r['form'], r)
    pg.click('#imp .gimp-btn')
    r = pg.evaluate(IMP_PROBE)
    pg.evaluate("document.querySelector('#imp .gimp-btn').click()")
    check('imp', 'while the call runs: «Возвращаем…», aria-busy, the button is locked, a second click starts nothing',
          r['btn'] == 'Возвращаем…' and r['busy'] == 'true' and r['disabled'] and pg.evaluate('window.__calls') == 1, (r, pg.evaluate('window.__calls')))
    pg.evaluate('window.__settle.res(false)')
    pg.wait_for_function("document.querySelector('#imp .gimp-btn') && !document.querySelector('#imp .gimp-btn').disabled")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'false from the call = the service stayed: the button works again with its own words', r['btn'] == 'Вернуться к себе' and r['busy'] is None and not r['err'], r)
    pg.click('#imp .gimp-btn')
    pg.evaluate("window.__settle.rej(new Error('boom'))")
    pg.wait_for_selector('#imp .gimp-err')
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'a failed call says so in words and the button works again; the visible line has no live role of its own (the quiet alert region says it, see below)',
          r['l2'] == 'Не получилось вернуться к себе. Попробуйте ещё раз.' and r['errRole'] is None and not r['disabled'] and r['btn'] == 'Вернуться к себе', r)
    pg.click('#imp .gimp-btn')
    pg.evaluate("window.__settle.rej(Object.assign(new Error('x'), {silent: true}))")
    pg.wait_for_function("document.querySelector('#imp .gimp-btn') && !document.querySelector('#imp .gimp-btn').disabled")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'a silent failure (the service already said it) adds no line of its own', not r['err'] and (r['l2'] or '').startswith('Только просмотр'), r)
    check('imp', 'gimp:end is fired on every press (3), nothing else', pg.evaluate('window.__ev') == ['end', 'end', 'end'], pg.evaluate('window.__ev'))
    # destroy gives the element back as it was
    pg.evaluate('window.bar.destroy()')
    gone = pg.evaluate("(() => { const e = document.getElementById('imp'); return {html: e.innerHTML, cls: e.className, role: e.getAttribute('role')}; })()")
    check('imp', 'destroy() empties the element and takes its class and role away', gone == {'html': '', 'cls': '', 'role': None}, gone)
    pg.evaluate("window.bar.update({name: 'Мария'}); window.bar.notice('x', 100)")
    pg.wait_for_timeout(250)
    gone = pg.evaluate("(() => { const e = document.getElementById('imp'); return {html: e.innerHTML, cls: e.className, role: e.getAttribute('role')}; })()")
    check('imp', 'after destroy() update() and notice() do nothing (no bar comes back, no timer draws it)', gone == {'html': '', 'cls': '', 'role': None}, gone)
    ctx.close()

    # --- the keyboard, the screen reader, the page from the cache, the clock after sleep
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-robust', page(IMP_SETUP + mount_js() + """window.__calls = 0;
      window.bar = window.__bar({name: 'Иван Образцов', until: window.__until, onEnd: function () { window.__calls++; return new Promise(function (res, rej) { window.__settle = {res: res, rej: rej}; }); }});"""))
    regions = pg.evaluate("[...document.querySelectorAll('[data-gimp-live]')].map(n => [n.getAttribute('data-gimp-live'), n.getAttribute('role'), n.getAttribute('aria-live'), n.getAttribute('aria-atomic'), n.textContent])")
    check('imp', 'two quiet regions are born with the bar, empty: status (polite) and alert (assertive), so a screen reader hears a change and not a newborn',
          regions == [['polite', 'status', 'polite', 'true', ''], ['assertive', 'alert', 'assertive', 'true', '']], regions)
    pg.evaluate("""window.__said = [];
      new MutationObserver(function () { var t = document.querySelector('[data-gimp-live=assertive]').textContent; if (t) window.__said.push(t); })
        .observe(document.querySelector('[data-gimp-live=assertive]'), {childList: true, characterData: true, subtree: true});""")
    pg.focus('#imp .gimp-btn')
    pg.keyboard.press('Enter')
    pg.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'a page that comes back from the cache (pageshow, persisted) is not left on «Возвращаем…»: the button works again',
          r['btn'] == 'Вернуться к себе' and not r['disabled'] and r['busy'] is None, r)
    pg.focus('#imp .gimp-btn')
    pg.keyboard.press('Enter')
    check('imp', 'the second call started (the first one is still unsettled but the bar was reset): busy again', pg.evaluate(IMP_PROBE)['btn'] == 'Возвращаем…')
    pg.evaluate("window.__settle.rej(new Error('boom'))")
    pg.wait_for_selector('#imp .gimp-err')
    f = pg.evaluate("(() => { const a = document.activeElement; return {cls: a.className, inBar: !!a.closest('#imp')}; })()")
    check('imp', 'after a failed call the focus is back on the new «Вернуться к себе» (a keyboard user is not thrown to the top of the page)', 'gimp-btn' in f['cls'] and f['inBar'], f)
    pg.wait_for_function("window.__said.length === 1", timeout=3000)
    check('imp', 'the failure is said once through the quiet alert region, in words', pg.evaluate('window.__said') == ['Не получилось вернуться к себе. Попробуйте ещё раз.'], pg.evaluate('window.__said'))
    pg.keyboard.press('Enter')
    pg.evaluate("window.__settle.rej(new Error('boom again'))")
    pg.wait_for_function("window.__said.length === 2", timeout=3000)
    check('imp', 'the same failure twice is said twice (the region is emptied before it is filled again)', pg.evaluate('window.__said.length') == 2, pg.evaluate('window.__said'))
    ctx.close()

    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-wake', page(IMP_SETUP + mount_js() + ON))
    check('imp', 'a running bar is on', pg.evaluate(IMP_PROBE)['state'] == 'on')
    pg.evaluate("(() => { const real = Date.now.bind(Date); Date.now = () => real() + 3600000; })()")
    pg.wait_for_timeout(300)
    check('imp', 'a laptop that slept: the clock is an hour ahead but the timer has not fired, the bar still says «on» (that is the trap)', pg.evaluate(IMP_PROBE)['state'] == 'on')
    pg.evaluate("window.dispatchEvent(new Event('focus'))")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'the window gets the focus back: the bar reads the clock, says «Вход от имени закончился» and fires gimp:over once',
          r['state'] == 'over' and r['l1'] == 'Вход от имени закончился' and pg.evaluate('window.__ev') == ['over'], (r['state'], pg.evaluate('window.__ev')))
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    check('imp', 'visibilitychange afterwards changes nothing and fires nothing more', pg.evaluate('window.__ev') == ['over'], pg.evaluate('window.__ev'))
    pg.wait_for_function("document.querySelector('[data-gimp-live=polite]').textContent === 'Вход от имени закончился. Вернитесь к себе, чтобы продолжить.'", timeout=3000)
    check('imp', 'the end of the time is said through the quiet status region', True)
    ctx.close()

    # --- a real POST of the service's own sign-out
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-form', page(IMP_SETUP + mount_js() + "window.bar = window.__bar({name: 'Мария Петрова', until: window.__until, endForm: {action: '/logout', fields: {to: 'gg-id', csrf_token: 'a b&c'}}});"))
    POSTS.clear()
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'endForm: a form with a button; the fields are hidden inputs', r['form'] and r['tag'] == 'button' and r['btn'] == 'Вернуться к себе', r)
    pg.click('#imp .gimp-btn')
    pg.wait_for_url('**/logged-out')
    check('imp', 'endForm: the press sends a POST with the fields (encoded) and the cookie of the service',
          len(POSTS) == 1 and POSTS[0]['path'] == '/logout' and 'to=gg-id' in POSTS[0]['body'] and 'csrf_token=a+b%26c' in POSTS[0]['body'] and 'gg_portal_session=test-session' in POSTS[0]['cookie'], POSTS)
    ctx.close()

    # --- the end of the time: the bar changes by itself, says so once, keeps the button
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-over', page(IMP_SETUP + mount_js() + "window.bar = window.__bar({name: 'Иван Образцов', until: Date.now() + 1200, endHref: '/logout'});"))
    check('imp', 'before the end the bar is on', pg.evaluate(IMP_PROBE)['state'] == 'on')
    pg.wait_for_function("document.getElementById('imp').getAttribute('data-gimp-state') === 'over'", timeout=6000)
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'after the end: «Вход от имени закончился», «Вернитесь к себе, чтобы продолжить.», the button stays, isOver() is true',
          r['l1'] == 'Вход от имени закончился' and r['l2'] == 'Вернитесь к себе, чтобы продолжить.' and 'gimp--over' in r['cls'] and r['btn'] == 'Вернуться к себе'
          and pg.evaluate('window.bar.isOver()') is True, r)
    check('imp', 'gimp:over is fired once', pg.evaluate('window.__ev') == ['over'], pg.evaluate('window.__ev'))
    check('imp', 'the ended bar has the same navy strip and enough contrast', r['bg'] == 'rgb(19, 68, 93)' and r['c1'] >= 4.5 and r['c2'] >= 4.5, r)
    pg.screenshot(path=os.path.join(OUT, 'imp-over-desktop.png'), clip={'x': 0, 'y': 0, 'width': 1440, 'height': 220})
    ctx.close()
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-ended', page(IMP_SETUP + mount_js() + "window.bar = window.__bar({name: 'Иван Образцов', ended: true, endHref: '/logout'});"))
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'ended: true is the ended bar at once, no gimp:over for a bar that was never on', r['state'] == 'over' and r['l1'] == 'Вход от имени закончился' and pg.evaluate('window.__ev') == [], (r['state'], pg.evaluate('window.__ev')))
    pg.evaluate("window.bar.update({ended: false, until: Date.now() + 600000})")
    check('imp', 'update() puts a running time back: the bar is on again', pg.evaluate(IMP_PROBE)['state'] == 'on' and pg.evaluate('window.bar.isOver()') is False)
    ctx.close()

    # --- safety: the words go in as text, the addresses are checked, the notice is text and goes away
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-xss', page(IMP_SETUP + mount_js() + """window.bar = window.__bar({name: '<img src=x onerror="window.__pwned=11">Иван', until: window.__until, endHref: '/logout'});
      window.bar.notice('<b>x</b> wow', 800);"""))
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'a name with markup is shown as text; the notice is text too and replaces the second line',
          r['l1'] == 'Вы смотрите как <img src=x onerror="window.__pwned=11">Иван' and r['l2'] == '<b>x</b> wow' and r['l2role'] is None and r['bad'] == [] and r['pwned'] == 0, r)
    pg.wait_for_function("document.querySelector('[data-gimp-live=polite]').textContent === '<b>x</b> wow'", timeout=3000)
    check('imp', 'the notice is said through the quiet status region as text', pg.evaluate("document.querySelectorAll('[data-gimp-live=polite] b').length") == 0)
    pg.wait_for_function("(document.querySelector('#imp .gimp-l2') || {}).textContent.indexOf('Только просмотр') === 0", timeout=6000)
    check('imp', 'the notice goes away by itself and the usual line comes back', True)
    for what, upd in (('a javascript: address', "{endHref: 'javascript:window.__pwned=12'}"), ('a plain http address of a stranger', "{endHref: 'http://evil.example/x'}"),
                      ('a data: address', "{endHref: 'data:text/html,<script>window.__pwned=14</script>'}"),
                      ('a javascript: action of the form', "{endHref: '', endForm: {action: 'javascript:window.__pwned=13', fields: {}}}"),
                      ('a protocol-relative address of a stranger (//evil.example/x)', "{endHref: '//evil.example/x'}"),
                      ('a backslash address of a stranger (/\\evil.example/x)', "{endHref: '/\\\\evil.example/x'}"),
                      ('a tab between the slashes (/<tab>/evil.example/x)', "{endHref: '/\\t/evil.example/x'}"),
                      ('an https address of a stranger', "{endHref: 'https://evil.example/x'}"),
                      ('a protocol-relative action of the form', "{endHref: '', endForm: {action: '//evil.example/logout', fields: {}}}"),
                      ('an https action of a stranger in the form', "{endHref: '', endForm: {action: 'https://evil.example/logout', fields: {}}}")):
        pg.evaluate(f'window.bar.update({upd})')
        r = pg.evaluate(IMP_PROBE)
        check('imp', f'{what}: no way back is drawn, nothing runs', r['btn'] is None and r['pwned'] == 0, r)
    pg.evaluate("window.bar.update({endForm: null, endHref: 'https://id.global-generations-edu.com/cabinet/'})")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'the address of the hub (https) is a link', r['tag'] == 'a' and r['href'] == 'https://id.global-generations-edu.com/cabinet/', r)
    pg.evaluate(f"window.bar.update({{endHref: '{svc}/logout'}})")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'an absolute address of the page\'s own origin is a link', r['tag'] == 'a' and r['href'] == svc + '/logout', r)
    pg.evaluate("window.bar.update({endHref: 'https://id-staging.example/cabinet/'})")
    check('imp', 'another hub (staging) is a stranger until the page names it', pg.evaluate(IMP_PROBE)['btn'] is None)
    pg.evaluate("window.bar.update({hubOrigin: 'https://id-staging.example'})")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'hubOrigin names the staging hub: its address is a link', r['tag'] == 'a' and r['href'] == 'https://id-staging.example/cabinet/', r)
    pg.evaluate("window.bar.update({hubOrigin: 'javascript:window.__pwned=15', endHref: 'javascript:window.__pwned=16'})")
    r = pg.evaluate(IMP_PROBE)
    check('imp', 'a hubOrigin that is not an http(s) address names nobody', r['btn'] is None and r['pwned'] == 0, r)
    ctx.close()

    # --- the attributes alone are enough
    ctx, pg = new_page(1440, 900)
    until = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=47)).strftime('%Y-%m-%dT%H:%M:%SZ')
    goto(pg, 'imp-attr', page('', body=f'<div id="attrbar" data-gg-imp-bar data-name="Мария Петрова" data-until="{until}" data-end-href="/logout"></div>', manual=False))
    pg.wait_for_selector('#attrbar .gimp-btn')
    a = pg.evaluate("(() => { const e = document.getElementById('attrbar'); return [e.querySelector('.gimp-l1').textContent, e.querySelector('.gimp-btn').textContent.trim(), e.querySelector('.gimp-btn').tagName]; })()")
    check('imp', 'data-gg-imp-bar with data-name, data-until and data-end-href draws the bar without a line of script', a == ['Вы смотрите как Мария Петрова', 'Вернуться к себе', 'A'], a)
    ctx.close()
    # a bar that markup alone brings to a page must not lead out of it
    ctx, pg = new_page(1440, 900)
    goto(pg, 'imp-attr-evil', page('', body='<div id="attrbar" data-gg-imp-bar data-name="Мария Петрова" data-end-href="//evil.example/x"></div>'
                                           '<div id="attrform" data-gg-imp-bar data-name="Мария Петрова" data-end-form=\'{"action":"/\\t/evil.example/logout","fields":{"to":"gg-id"}}\'></div>', manual=False))
    pg.wait_for_selector('#attrbar .gimp-l1')
    pg.wait_for_selector('#attrform .gimp-l1')
    ev = pg.evaluate("[...document.querySelectorAll('#attrbar, #attrform')].map(e => [e.querySelector('.gimp-btn'), e.querySelector('form'), e.querySelector('a')].filter(Boolean).length)")
    check('imp', 'data-end-href="//evil.example/x" and a tab-broken data-end-form action draw no way back (only the words)', ev == [0, 0], ev)
    ctx.close()
    check('imp', 'no script errors on the pages', not errs, errs[:3])


def demo_page(b):
    svc = ORIGINS['svc']
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=2)
    pg = ctx.new_page()
    errs = []
    missing_ok = [False]      # the avatar mode "the picture does not load" asks for a file that is not there: the 404 line of the browser is the point of that state, not an error of the page
    pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type == 'error' and not (missing_ok[0] and m.text.startswith('Failed to load resource')) else None)
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
    for state in ('ok', 'slow', 'nologin', 'error', 'empty', 'offline'):
        pg.goto(f'{svc}/gg-id/account-menu/demo.html?state={state}')
        pg.wait_for_function("[...document.querySelectorAll('iframe')].every(f => f.contentDocument && f.contentDocument.querySelector('#account .gid-chip'))", timeout=15000)
        frames = {k: next(f for f in pg.frames if f'embed={k}' in f.url) for k in ('desktop', 'phone')}
        for k, fr in frames.items():
            fr.evaluate('document.fonts.ready.then(() => 1)')
            if state in ('ok', 'slow'):
                fr.click('#account button[data-gam-id="services"]')
                fr.wait_for_selector('#account .gam-svc', timeout=6000)
            else:       # the card is open from the start, the list fails, the expander turns into the link by itself
                fr.wait_for_function("document.querySelector('#account a[data-gam-id=services]') && !document.querySelector('#account a[data-gam-id=services]').hidden", timeout=6000)
            res = fr.evaluate(DEMO_LINK)
            rows = fr.evaluate(DEMO_ROWS)
            if state in ('ok', 'slow'):
                own = fr.evaluate("(() => { const p = document.querySelector('#account .gam-sub:not([hidden])'); return p.scrollHeight > p.clientHeight + 1; })()")
                check('demo', f'{state} / {k}: the list is drawn (13 services) whole, with no scroll of its own, the expander stays', rows == 13 and not own and res['btn'] and not res['link'], (rows, own, res))
            else:
                check('demo', f'{state} / {k}: a plain link to the cabinet, no list', rows == 0 and res['link'] and not res['btn'], (rows, res))
            check('demo', f'{state} / {k}: no bar of a sign-in on behalf without ?imp', fr.evaluate("document.querySelectorAll('#imp .gimp').length") == 0)
            bd = fr.evaluate("(() => { const a = document.querySelector('#account a.gam-wallet'); return a && [a.getAttribute('href'), a.getClientRects().length > 0]; })()")
            check('demo', f'{state} / {k}: the Wallet badge is in the card (the demo shows it on every device) and links to the pass of the hub', bd == [HUB_URL + WALLET_PATH, True], bd)
        phone_scroll = frames['phone'].evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth, innerWidth]')
        check('demo', f'{state}: the 390 px frame is 390 px wide and has no horizontal scroll', phone_scroll[2] == 390 and phone_scroll[0] <= phone_scroll[1], phone_scroll)
        if state == 'ok':
            pg.screenshot(path=os.path.join(OUT, 'demo-page.png'), full_page=True)
    # the bar of a sign-in on behalf: ?imp=on | over puts it in both frames, right under the header
    for mode in ('on', 'over'):
        pg.goto(f'{svc}/gg-id/account-menu/demo.html?state=ok&imp={mode}')
        pg.wait_for_function("[...document.querySelectorAll('iframe')].every(f => f.contentDocument && f.contentDocument.querySelector('#imp .gimp-btn'))", timeout=15000)
        for fr in [f for f in pg.frames if 'embed=' in f.url]:
            t = fr.evaluate("document.querySelector('#imp .gimp-l1').textContent")
            check('demo', f'imp={mode}: the bar is in the frame with the right words', t == ('Вы смотрите как Иван Образцов' if mode == 'on' else 'Вход от имени закончился'), t)
    check('demo', 'the second row of switches of the demo page has three links (own session, on, ended)', pg.evaluate("document.querySelectorAll('#imps a').length") == 3)
    # the third row (?avatar=photo | initials | broken): the demo names its own picture in the option photo, so it asks the hub for nothing (the stub of the page counts a card call)
    check('demo', 'the third row of switches of the demo page has three links (the photo, the initials, the picture that does not load)', pg.evaluate("document.querySelectorAll('#avatars a').length") == 3)
    HUB['cards'].clear()
    for mode in ('photo', 'initials', 'broken'):
        missing_ok[0] = mode == 'broken'
        pg.goto(f'{svc}/gg-id/account-menu/demo.html?state=ok&avatar={mode}')
        pg.wait_for_function("[...document.querySelectorAll('iframe')].every(f => f.contentDocument && f.contentDocument.querySelector('#account .gid-chip'))", timeout=15000)
        for k in ('desktop', 'phone'):
            fr = next(f for f in pg.frames if f'embed={k}' in f.url)
            if mode == 'photo':
                fr.wait_for_function("document.querySelectorAll('#account .gid-avatar.gam-av--photo').length === 2", timeout=8000)
            elif mode == 'broken':
                fr.wait_for_function("document.querySelectorAll('#account img.gam-photo').length === 0", timeout=8000)
            else:
                pg.wait_for_timeout(400)
            av = fr.evaluate(AVS, '#account')
            srcs = [a['src'] for a in av]
            if mode == 'photo':
                ok = len(av) == 2 and all(a['hasImg'] for a in av) and all(s and s.endswith('/gg-id/account-menu/demo-avatar.svg') for s in srcs) and all(a['color'] == 'rgba(0, 0, 0, 0)' for a in av)
            else:
                ok = len(av) == 2 and not any(a['hasImg'] for a in av) and all(a['color'] == 'rgb(19, 68, 93)' for a in av) and [a['text'] for a in av] == ['ЛА', 'ЛА']
            check('demo', f'avatar={mode} / {k}: ' + {'photo': 'the picture of the demo is in both circles', 'initials': 'the initials only', 'broken': 'the file is not there, the picture is taken out and the initials are back'}[mode],
                  ok and [round(a['w']) for a in av] == [28, 44], av)
            check('demo', f'avatar={mode} / {k}: the demo asks the hub for no card (the option photo is given)', fr.evaluate('window.__demoCardCalls || 0') == 0 and not HUB['cards'], (fr.evaluate('window.__demoCardCalls || 0'), HUB['cards']))
        if mode != 'photo':
            pg.wait_for_timeout(300)
            hrefs = pg.evaluate("[...document.querySelectorAll('#states a, #imps a')].map(a => a.getAttribute('href'))")
            check('demo', f'avatar={mode}: the other two rows of switches keep the avatar mode in their links', all(f'avatar={mode}' in h for h in hrefs), hrefs[:2])
        missing_ok[0] = False
    check('demo', 'the demo page and its frames print no console errors', not errs, errs[:3])
    ctx.close()


def pictures(b):
    """The pictures of the README: the demo frames, opened as a person sees them."""
    svc = ORIGINS['svc']
    desk = {'x': 1040, 'y': 0, 'width': 400, 'height': 600}
    # the last field is the avatar of the demo: the first six pictures keep the initials (they are about the list and the bar, and they stay as they were), the last three are about the photo
    shots = (('menu-desktop.png', 'desktop', 'ok', False, (1440, 640), desk, 'initials'),
             ('services-desktop.png', 'desktop', 'ok', True, (1440, 1160), {'x': 1040, 'y': 0, 'width': 400, 'height': 1140}, 'initials'),
             ('services-390.png', 'phone', 'ok', True, (390, 1160), None, 'initials'),
             ('services-fallback.png', 'phone', 'nologin', False, (390, 700), None, 'initials'),
             ('photo-desktop.png', 'desktop', 'ok', False, (1440, 640), desk, 'photo'),
             ('photo-390.png', 'phone', 'ok', False, (390, 700), None, 'photo'),
             ('photo-fallback.png', 'desktop', 'ok', False, (1440, 640), desk, 'broken'))
    for name, embed, state, expand, (w, h), clip, avatar in shots:
        ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2)
        pg = ctx.new_page()
        pg.goto(f'{svc}/gg-id/account-menu/demo.html?embed={embed}&state={state}&open=1&avatar={avatar}')
        pg.wait_for_function('window.GGAccountMenu !== undefined')
        pg.evaluate('document.fonts.ready.then(() => 1)')
        if avatar == 'photo':
            pg.wait_for_function("document.querySelectorAll('#account .gid-avatar.gam-av--photo').length === 2", timeout=8000)
        elif avatar == 'broken':
            pg.wait_for_function("document.querySelectorAll('#account img.gam-photo').length === 0", timeout=8000)
        if expand:
            pg.click('#account button[data-gam-id="services"]')
            pg.wait_for_selector('#account .gam-svc')
        elif state != 'ok':
            pg.wait_for_function("document.querySelector('#account a[data-gam-id=services]') && !document.querySelector('#account a[data-gam-id=services]').hidden", timeout=6000)
        pg.mouse.move(2, 2)
        pg.wait_for_timeout(450)
        pg.screenshot(path=os.path.join(OUT, 'picture-' + name), **({'clip': clip} if clip else {}))
        ctx.close()
    for name, embed, (w, h) in (('imp-desktop.png', 'desktop', (1440, 300)), ('imp-390.png', 'phone', (390, 330))):
        ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2)
        pg = ctx.new_page()
        pg.goto(f'{svc}/gg-id/account-menu/demo.html?embed={embed}&state=ok&imp=on&avatar=initials')
        pg.wait_for_function('window.GGAccountMenu !== undefined')
        pg.evaluate('document.fonts.ready.then(() => 1)')
        pg.wait_for_selector('#imp .gimp-btn')
        pg.mouse.move(2, 2)
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(OUT, 'picture-' + name))
        ctx.close()


# ---------------------------------------------------------------------------------------------------------------- run

def main():
    sources()
    svc, hub, evil = Server(site_handler()), Server(hub_handler()), Server(site_handler())
    ORIGINS.update(svc=f'http://localhost:{svc.port}', hub=f'http://localhost:{hub.port}', evil=f'http://localhost:{evil.port}')
    HUB['allowed'] = {ORIGINS['svc']}          # the hub knows the service page; a card request of a menu with no cookie, or of a foreign page, is a quiet 401 or 403
    # every page is also served by the "evil" server (same files): a page of a stranger that asks the hub
    try:
        with sync_playwright() as p:
            b = getattr(p, ENGINE).launch()
            _new = b.new_context

            def new_context(**kw):
                c = _new(**kw)
                c.set_default_timeout(60000)       # a shared Mac with dozens of agents: 30 seconds of Playwright is sometimes too little
                # the production hub is never reached from a check: a menu that has no hubOrigin asks the canonical address, the context refuses it
                # (a page that wants to answer for it, as hub_defaults does, has its own route, and a page route comes first)
                c.route(re.compile(r'^https://id\.global-generations-edu\.com/'), lambda route: route.abort())
                return c
            b.new_context = new_context
            for name, fn, args in (('look', look, ()), ('avatar_variant', avatar_variant, ()), ('behaviour', behaviour, ()), ('focus_rings', focus_rings, ()),
                                   ('wallet_badge', wallet_badge, ()), ('hub_defaults', hub_defaults, ()), ('photo', photo, ()),
                                   ('listing', listing, ()), ('imp_bar', imp_bar, ()), ('phone', phone, (ENGINE,)), ('narrow_edges', narrow_edges, ()), ('demo_page', demo_page, ()),
                                   ('pictures', pictures, ())):
                try:
                    fn(b, *args)
                except Exception as e:   # a step that cannot finish is a failure of the check, the others still run
                    problems.append(f'{name}: the run stopped: {type(e).__name__}: {str(e).splitlines()[0][:300]}')
                finally:
                    HUB['card_mode'], HUB['card_delay'], HUB['card_body'] = 'nophoto', 0, None     # the card answer of one group (a picture, a refusal) is never the answer of the next
            b.close()
    finally:
        for s in (svc, hub, evil):
            s.stop()
    summary = ', '.join(f'{v} {k}' for k, v in counts.items())
    if problems:
        print('GG ACCOUNT MENU CHECK FAILED', f'({ENGINE})', '|', summary)
        for x in problems:
            print(' -', x)
        sys.exit(1)
    print('ok:', summary, f'({ENGINE})', '| shots in', OUT)
    if '--preview' in sys.argv:
        pdir = os.path.join(DIR, 'preview')
        os.makedirs(pdir, exist_ok=True)
        import shutil
        for name in ('menu-desktop.png', 'services-desktop.png', 'services-390.png', 'services-fallback.png', 'imp-desktop.png', 'imp-390.png', 'photo-desktop.png', 'photo-390.png', 'photo-fallback.png'):
            shutil.copyfile(os.path.join(OUT, 'picture-' + name), os.path.join(pdir, name))
        print('preview pictures refreshed in', pdir)


if __name__ == '__main__':
    main()
