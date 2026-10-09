"""GG ID: how the kit words a sign-in with a passkey (rule of 09.10.2026).

The rule: Touch ID, Windows Hello, «отпечаток» and «палец» are named only when THIS browser has a confirmed key of the device
(localStorage gg-id-local-key + gg-id-last-method = platform). Until then the kit says what is true everywhere: Face ID on the phone
(QR code) or a key on this device. The offer to create a key here (enroll) may name the method of the device: the key is made on this
device and the page shows the offer only after the browser said it can. The four localStorage names are shared with the sign-in page of
the hub and with the Face ID confirmation page of the admins (Infra-Services-Portal #168, Infra-AWS #98 and its port Infra-Auth #17): one
origin, one memory.

What is checked (Chromium):
  1. the sources: the four storage names, the sentences and the phrases word for word, no network calls, the docs carry the same; the guard
     against the words of a device (it also sees Touch&nbsp;ID, Touch U+00A0 ID, TouchID) and the same pattern in the build;
  2. every kind of device x every memory state x every phrase through the API (explicit kind);
  3. 7 devices x 8 memory states x 3 screens (login, passkey, enroll) loaded fresh with the memory already in localStorage: label, icon and
     hint; without a confirmed key no method of the device on the sign-in and the waiting screens at all, on any device (the case of Lev's Mac);
  4. the rules of the memory: what a confirmation by the device, by the phone, a miss, a cancelled attempt and «Не сейчас» change; nothing
     but the four names is ever written;
  5. storage that throws, a blocked localStorage getter and a browser without WebAuthn: nothing breaks, nothing is promised;
  6. demo mode of the showcase keeps the words of the markup; a page without passkey markup is not touched (no storage reads);
  7. the real WebAuthn of Chromium (virtual authenticators over CDP, navigator.credentials is not replaced): a key of the device says
     «platform», a USB key says «cross-platform», GGID.passkeyWatch() reads it and the next load words the screen accordingly.
Run alone: uv run --with playwright python src/check_gg_id_passkey.py   (it also runs inside src/check_gg_id.py)
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'gg-id')
SCREENS = os.path.join(KIT, 'screens')
ORIGIN = 'http://localhost'          # a secure context for WebAuthn without a certificate; the pages are served from the repo by a route

# shared with Infra-Services-Portal (login.tpl.html), Infra-AWS (portal-auth, step_up.py) and Infra-Auth (step_up.py): rename only in all four at once
KEYS = {'PK_LOCAL': 'gg-id-local-key', 'PK_LAST': 'gg-id-last-method', 'PK_MISS': 'gg-id-local-miss', 'PK_SKIP': 'gg-id-enroll-skip'}
L, S, M, Z = KEYS['PK_LOCAL'], KEYS['PK_LAST'], KEYS['PK_MISS'], KEYS['PK_SKIP']


class Banned:
    """The words that name a method of the device. Looked for in what a person reads: entities decoded (Touch&nbsp;ID), soft hyphens and zero-width
    characters dropped, any space (a non-breaking one too) between «Touch» and «ID», so a typographic variant does not slip through.
    The same pattern is DEVICE_WORDS in src/build_gg_id.py (the build refuses it in the markup of the screens); the check compares the two."""
    pattern = r'(?<![a-z])(?:Touch\s*ID|Windows\s*Hello)(?![a-z])|отпечат|палец|пальц'
    _re = re.compile(pattern, re.I)

    @staticmethod
    def plain(text):
        return re.sub('[\u00ad\u200b-\u200d\u2060\ufeff]', '', html.unescape('' if text is None else str(text)))

    def search(self, text):
        return self._re.search(self.plain(text))

    def findall(self, text):
        return self._re.findall(self.plain(text))


BANNED = Banned()

HINT_UNKNOWN = 'Подтвердите вход в окне браузера: Face ID на телефоне (QR-код) или ключ на этом устройстве.'
HINT_PHONE = 'Подтвердите вход с телефона: наведите камеру телефона на QR-код в окне браузера и подтвердите Face ID.'
HINT_OWN = 'Подтвердите вход: {} на этом устройстве.'
HINT_SYSTEM_IOS = 'Подтвердите вход Face ID в системном окне. Это займёт секунду.'
HINT_SYSTEM_ANDROID = 'Подтвердите вход в системном окне. Это займёт секунду.'
WAIT = 'Ждём подтверждения'

# device -> (user agent, navigator.platform, maxTouchPoints, navigator.userAgentData.platform or None, expected kind)
DEVICES = {
    'mac-safari': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15',
                   'MacIntel', 0, None, 'touchid'),
    'mac-chrome': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                   'MacIntel', 0, 'macOS', 'touchid'),
    'iphone': ('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
               'iPhone', 5, None, 'faceid'),
    'ipad': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15',
             'MacIntel', 5, None, 'faceid'),
    'windows': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Win32', 0, 'Windows', 'hello'),
    'android': ('Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
                'Linux armv81', 5, 'Android', 'finger'),
    'linux': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
              'Linux x86_64', 0, 'Linux', 'key'),
}
# the expected words, written out by hand (not derived from the kit): kind -> ...
OWN_WORD = {'touchid': 'Touch ID', 'faceid': 'Face ID', 'hello': 'Windows Hello', 'finger': 'отпечаток пальца', 'key': 'ключ доступа'}
OWN_LOGIN = {'touchid': 'Войти с Touch ID', 'faceid': 'Войти с Face ID', 'hello': 'Войти с Windows Hello',
             'finger': 'Войти по отпечатку', 'key': 'Войти по ключу доступа'}
ICON = {'touchid': 'fingerprint', 'faceid': 'scan-face', 'hello': 'scan-face', 'finger': 'fingerprint', 'key': 'key-round'}
ENROLL = {'touchid': 'Подключить Touch ID', 'faceid': 'Подключить Face ID', 'hello': 'Подключить Windows Hello',
          'finger': 'Подключить вход по отпечатку', 'key': 'Создать ключ доступа'}
LEAD = {'touchid': 'Подключите Touch ID', 'faceid': 'Подключите Face ID', 'hello': 'Подключите Windows Hello',     # start of the sub line of the offer
        'finger': 'Подключите отпечаток', 'key': 'Создайте ключ доступа'}


def safe_login(kind):      # what is true on every device: Face ID of the phone (Android has no Face ID: the general phrase)
    return 'Войти по ключу доступа' if kind == 'finger' else 'Войти с Face ID'


def safe_icon(kind):
    return 'key-round' if kind == 'finger' else 'scan-face'


def hint_for(kind, own, last):
    if own:
        return HINT_OWN.format(OWN_WORD[kind])
    if kind == 'faceid':
        return HINT_SYSTEM_IOS
    if kind == 'finger':
        return HINT_SYSTEM_ANDROID
    return HINT_PHONE if last == 'cross-platform' else HINT_UNKNOWN


# memory states: storage content -> does the browser have a confirmed key of the device (own), how was the last confirmation given
STATES = {
    'new browser': ({}, False, ''),
    'last: phone': ({S: 'cross-platform'}, False, 'cross-platform'),
    'key of the device, last: phone': ({L: '1', S: 'cross-platform'}, False, 'cross-platform'),
    'key flag only': ({L: '1'}, False, ''),
    'last: device, no key flag': ({S: 'platform'}, False, 'platform'),
    'junk values': ({L: 'yes', S: 'touchid'}, False, ''),
    'own key': ({L: '1', S: 'platform'}, True, 'platform'),
    'own key, one miss': ({L: '1', S: 'platform', M: '1'}, True, 'platform'),
}

DEVICE_JS = '''(d) => {
  const def = (o, k, v) => { try { Object.defineProperty(o, k, { get: () => v, configurable: true }); } catch (e) {} };
  def(navigator, 'platform', d.platform);
  def(navigator, 'maxTouchPoints', d.touch);
  def(navigator, 'userAgentData', d.uaData ? { platform: d.uaData } : undefined);
}'''
READ = '''() => {
  const q = (s) => document.querySelector(s);
  const label = q('.gid-btn [data-gid-passkey]'), icon = q('.gid-btn [data-gid-passkey-icon] use'), hint = q('[data-gid-passkey-hint]'),
    lead = q('[data-gid-passkey="enroll-lead"]');
  return { kind: GGID.passkeyKind(), phrase: label && label.getAttribute('data-gid-passkey'), text: label && label.textContent.trim(),
    icon: icon && icon.getAttribute('href'), hint: hint && hint.textContent.trim(), lead: lead && lead.textContent.trim(), page: document.body.innerText };
}'''
STORE = '''() => { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); o[k] = localStorage.getItem(k); } return o; }'''
SET_STORE = '''(m) => { localStorage.clear(); for (const k in m) localStorage.setItem(k, m[k]); }'''
CREATE = '''async (att) => (await navigator.credentials.create({ publicKey: { challenge: new Uint8Array([1, 2, 3, 4]), rp: { id: location.hostname, name: 'GG ID' },
  user: { id: new Uint8Array([9]), name: 'a', displayName: 'A' }, pubKeyCredParams: [{ type: 'public-key', alg: -7 }, { type: 'public-key', alg: -257 }],
  authenticatorSelection: { authenticatorAttachment: att, residentKey: 'required', userVerification: 'required' }, attestation: 'none' } })).authenticatorAttachment'''
GET = '''async () => (await navigator.credentials.get({ publicKey: { challenge: new Uint8Array([5, 6, 7, 8]), rpId: location.hostname,
  userVerification: 'required', allowCredentials: [] } })).authenticatorAttachment'''


def device_script(dev):
    _, platform, touch, ua_data, _ = DEVICES[dev]
    return '(' + DEVICE_JS + ')(' + json.dumps({'platform': platform, 'touch': touch, 'uaData': ua_data}) + ')'


def short(s, n=90):
    s = '' if s is None else str(s)
    return s if len(s) <= n else s[:n] + '...'


def run(b, problems, counts):
    """Runs every check on the Chromium `b`; appends to `problems`, counts into counts['passkey']. A section that crashes is one problem, not the end."""
    counts.setdefault('passkey', 0)

    def ok(name, cond, got=None):
        counts['passkey'] += 1
        if not cond:
            problems.append(f'passkey wording: {name}' + (f' (got {short(got, 220)})' if got is not None else ''))

    def eq(name, got, want):
        ok(name, got == want, f'{got!r}, expected {want!r}')

    def page_in(ctx, errs, file='login.html', query='?layout=split'):
        pg = ctx.new_page()
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        if file:
            pg.goto('file://' + os.path.join(SCREENS, file) + query)
        return pg

    def section(fn):
        try:
            fn()
        except Exception as e:     # a crash inside a section is a failure of that section, the others still run
            counts['passkey'] += 1
            problems.append(f'passkey wording: section "{fn.__name__}" crashed: {short(str(e).splitlines()[0] if str(e) else repr(e), 300)}')

    # ---- 1. the sources: names and sentences are the ones the hub and the Face ID page use ----
    def sources():
        js = open(os.path.join(KIT, 'gg-id.js'), encoding='utf-8').read()
        for const, name in KEYS.items():
            eq(f'source: {const} is {name}', re.findall(const + r"\s*=\s*'([^']+)'", js), [name])
        for sentence in (HINT_UNKNOWN, HINT_PHONE, HINT_SYSTEM_IOS, HINT_SYSTEM_ANDROID, WAIT, 'Подтвердите вход: '):
            ok(f'source: gg-id.js says «{short(sentence, 50)}»', sentence in js)
        ok('source: gg-id.js makes no network calls', not re.search(r'\b(fetch|XMLHttpRequest|sendBeacon|WebSocket)\b', js))
        ok('source: gg-id.js has the icon table the hub test reads (PASSKEY_ICON = {...})', re.search(r"PASSKEY_ICON\s*=\s*\{[^}]*\}", js) is not None)
        handoff = open(os.path.join(KIT, 'HANDOFF-AUTH.md'), encoding='utf-8').read()
        for name in KEYS.values():
            ok(f'docs: HANDOFF-AUTH.md names {name}', name in handoff)
        for sentence in (HINT_UNKNOWN, HINT_PHONE, HINT_OWN.format('Touch ID'), HINT_SYSTEM_IOS, HINT_SYSTEM_ANDROID, WAIT):
            ok(f'docs: HANDOFF-AUTH.md carries «{short(sentence, 50)}»', sentence in handoff)
        ok('docs: HANDOFF-AUTH.md no longer tells to set the old gg-id-pk flag', "setItem('gg-id-pk'" not in handoff and "getItem('gg-id-pk')" not in handoff)
        readme = open(os.path.join(KIT, 'README.md'), encoding='utf-8').read()
        for fn in ('passkeyText', 'passkeyIcon', 'passkeyHint', 'passkeyMemory', 'passkeyWatch', 'passkeySeen', 'passkeyRemember', 'passkeyCreated',
                   'passkeyMissed', 'passkeySnooze', 'data-gid-passkey-hint', 'enroll-lead'):
            ok(f'docs: README.md describes {fn}', fn in readme)
        for name in sorted(n for n in os.listdir(SCREENS) if n.endswith('.html')):
            text = open(os.path.join(SCREENS, name), encoding='utf-8').read()
            text = re.sub(r'<(script|style)\b.*?</\1>|<!--.*?-->', ' ', text, flags=re.S)
            ok(f'markup: screens/{name} names no method of the device', not BANNED.search(text), BANNED.findall(text))

    # ---- 1b. the guard itself: the words it looks for are found in the typographic variants this repo uses, and nothing true is taken for a method of the device ----
    def guard_words():
        for text in ('Войти с Touch ID', 'touch id', 'TOUCH ID', 'Touch&nbsp;ID', 'Touch&#160;ID', 'Touch\u00a0ID', 'Touch\u202fID', 'TouchID', 'Tou\u200bch ID',
                     'Windows Hello', 'Windows&nbsp;Hello', 'Windows\u00a0Hello', 'Войти по отпечатку', 'Приложите палец', 'пальцем'):
            ok(f'guard: {text!r} names a method of the device', bool(BANNED.search(text)), text)
        for text in ('Войти с Face ID', 'Face&nbsp;ID', 'Face\u00a0ID', 'Войти по ключу доступа', 'Ждём подтверждения', 'touch ideas', 'Windows Helloween',
                     'Подтвердите вход в окне браузера: Face ID на телефоне (QR-код) или ключ на этом устройстве.'):
            ok(f'guard: {text!r} is not one', not BANNED.search(text), BANNED.findall(text))
        build = open(os.path.join(ROOT, 'src', 'build_gg_id.py'), encoding='utf-8').read()
        ok('guard: the build refuses the same words as this check (DEVICE_WORDS = BANNED.pattern)', "DEVICE_WORDS = re.compile(r'" + BANNED.pattern + "', re.I)" in build)

    # ---- 2. explicit kind: every kind x every memory state x every phrase, in one page ----
    def explicit_kinds():
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        errs = []
        pg = page_in(ctx, errs, query='?layout=minimal')
        for sname, (mem, own, last) in STATES.items():
            pg.evaluate(SET_STORE, mem)
            got = pg.evaluate('() => GGID.passkeyMemory()')
            eq(f'memory [{sname}]: own', got['own'], own)
            eq(f'memory [{sname}]: last', got['last'], last)
            eq(f'memory [{sname}]: local flag', got['local'], mem.get(L) == '1')
            eq(f'memory [{sname}]: miss flag', got['miss'], mem.get(M) == '1')
            for kind in OWN_WORD:
                t = pg.evaluate('(k) => ({ login: GGID.passkeyText("login", k), enroll: GGID.passkeyText("enroll", k), wait: GGID.passkeyText("wait", k), '
                                'lead: GGID.passkeyText("enroll-lead", k), loginIcon: GGID.passkeyIcon("login", k), waitIcon: GGID.passkeyIcon("wait", k), enrollIcon: GGID.passkeyIcon("enroll", k), '
                                'hint: GGID.passkeyHint(k) })', kind)
                tag = f'[{sname}] [{kind}]'
                eq(f'login phrase {tag}', t['login'], OWN_LOGIN[kind] if own else safe_login(kind))
                eq(f'login icon {tag}', t['loginIcon'], ICON[kind] if own else safe_icon(kind))
                eq(f'wait phrase {tag}', t['wait'], WAIT)
                eq(f'wait icon {tag}', t['waitIcon'], ICON[kind] if own else safe_icon(kind))
                eq(f'enroll phrase {tag}', t['enroll'], ENROLL[kind])
                eq(f'enroll-lead phrase {tag}', t['lead'], LEAD[kind])
                eq(f'enroll icon {tag}', t['enrollIcon'], ICON[kind])
                eq(f'hint {tag}', t['hint'], hint_for(kind, own, last))
                if not own:
                    for k in ('login', 'wait', 'hint'):
                        ok(f'no method of the device without a confirmed key {tag} {k}', not BANNED.search(t[k]), t[k])
        pg.evaluate(SET_STORE, {})
        eq('unknown phrase falls back to the login phrase', pg.evaluate('() => GGID.passkeyText("nope", "key")'), 'Войти с Face ID')
        pg.evaluate(SET_STORE, STATES['own key'][0])
        eq('unknown kind falls back to the key phrase (own key)', pg.evaluate('() => GGID.passkeyText("login", "toaster")'), 'Войти по ключу доступа')
        eq('unknown kind falls back to the key word in the hint (own key)', pg.evaluate('() => GGID.passkeyHint("toaster")'), HINT_OWN.format('ключ доступа'))
        for args, want in ((['Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)', 'iPhone', 5], 'faceid'),
                           (['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'MacIntel', 0], 'touchid'),
                           (['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'MacIntel', 5], 'faceid'),
                           (['Mozilla/5.0 (Windows NT 10.0)', 'Win32', 0], 'hello'),
                           (['Mozilla/5.0 (Linux; Android 14)', 'Linux armv81', 5], 'finger'),
                           (['Mozilla/5.0 (X11; Linux x86_64)', 'Linux x86_64', 0], 'key')):
            eq(f'passkeyKind{tuple(args)}', pg.evaluate('(a) => GGID.passkeyKind(a[0], a[1], a[2])', args), want)
        ok('page: console and exceptions clean (explicit kinds)', not errs, errs[:3])
        ctx.close()

    # ---- 3. each device loads the three screens with the memory already in localStorage ----
    def devices():
        for dev, (ua, platform, touch, ua_data, kind) in DEVICES.items():
            ctx = b.new_context(user_agent=ua, viewport={'width': 1280, 'height': 800}, has_touch=touch > 0)
            ctx.add_init_script(device_script(dev))
            errs = []
            pg = page_in(ctx, errs, file=None)
            for sname, (mem, own, last) in STATES.items():
                shown = {}
                for screen in ('login', 'passkey', 'enroll'):
                    pg.goto('file://' + os.path.join(SCREENS, screen + '.html') + '?layout=split')
                    pg.evaluate(SET_STORE, mem)
                    pg.reload()
                    shown[screen] = pg.evaluate(READ)
                tag = f'{dev} [{sname}]'
                eq(f'device kind {dev}', shown['login']['kind'], kind)
                eq(f'login screen label {tag}', shown['login']['text'], OWN_LOGIN[kind] if own else safe_login(kind))
                eq(f'login screen icon {tag}', (shown['login']['icon'] or '').split('#')[-1], 'gi-' + (ICON[kind] if own else safe_icon(kind)))
                eq(f'waiting screen label {tag}', shown['passkey']['text'], WAIT)
                eq(f'waiting screen icon {tag}', (shown['passkey']['icon'] or '').split('#')[-1], 'gi-' + (ICON[kind] if own else safe_icon(kind)))
                eq(f'waiting screen hint {tag}', shown['passkey']['hint'], hint_for(kind, own, last))
                eq(f'enroll screen label {tag}', shown['enroll']['text'], ENROLL[kind])
                eq(f'enroll screen icon {tag}', (shown['enroll']['icon'] or '').split('#')[-1], 'gi-' + ICON[kind])
                eq(f'enroll screen lead {tag}', shown['enroll']['lead'], LEAD[kind])
                if not own:    # Lev's Mac: not a word about Touch ID, Windows Hello or a finger on the sign-in and the waiting screens
                    for screen in ('login', 'passkey'):
                        ok(f'no method of the device on the {screen} screen {tag}', not BANNED.search(shown[screen]['page']), BANNED.findall(shown[screen]['page']))
                    rest = shown['enroll']['page'].replace(shown['enroll']['text'] or '', '').replace(shown['enroll']['lead'] or '', '')
                    ok(f'enroll screen names the method only on its button and in the lead of its sub line {tag}', not BANNED.search(rest), BANNED.findall(rest))
            ok(f'page: console and exceptions clean on {dev}', not errs, errs[:3])
            ctx.close()

    # ---- 3b. a page with the sprite in a separate file (the hub): the path in the href of the icon stays, only the symbol changes ----
    def icon_path():
        ctx = b.new_context(user_agent=DEVICES['mac-safari'][0], viewport={'width': 1280, 'height': 800})
        ctx.add_init_script(device_script('mac-safari'))
        errs = []
        pg = ctx.new_page()        # no console listener: a file:// page refuses to load an external sprite, which is not the kit's concern
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        pg.goto('file://' + os.path.join(SCREENS, 'login.html') + '?layout=minimal')
        fixture = '''() => { const d = document.createElement('div');
          d.innerHTML = '<button><svg data-gid-passkey-icon><use href="/assets/gg-id/sprite.svg#gi-scan-face"/></svg><span data-gid-passkey="login">x</span></button>'
            + '<button><svg data-gid-passkey-icon><use href="https://id.example/assets/gg-id/sprite.svg#gi-scan-face"/></svg><span data-gid-passkey="enroll">x</span></button>'
            + '<button><svg data-gid-passkey-icon><use/></svg><span data-gid-passkey="wait">x</span></button>'
            + '<span><svg data-gid-passkey-icon><use href="sprite.svg#gi-key-round"/></svg></span>';
          document.body.appendChild(d); GGID.init(d);
          return [...d.querySelectorAll('use')].map(u => u.getAttribute('href')); }'''
        pg.evaluate(SET_STORE, STATES['new browser'][0])
        eq('icons on a Mac without a confirmed key: the sprite path stays, login and wait are the face, enroll is the device',
           pg.evaluate(fixture), ['/assets/gg-id/sprite.svg#gi-scan-face', 'https://id.example/assets/gg-id/sprite.svg#gi-fingerprint', '#gi-scan-face', 'sprite.svg#gi-scan-face'])
        pg.evaluate(SET_STORE, STATES['own key'][0])
        eq('icons on a Mac with its own key: the sprite path stays, the fingerprint everywhere',
           pg.evaluate(fixture), ['/assets/gg-id/sprite.svg#gi-fingerprint', 'https://id.example/assets/gg-id/sprite.svg#gi-fingerprint', '#gi-fingerprint', 'sprite.svg#gi-fingerprint'])
        pg.evaluate('''() => { const d = document.createElement('div');
          d.innerHTML = '<p data-gid-passkey-hint>x</p><button><span data-gid-passkey="login">x</span></button>'; document.body.appendChild(d); GGID.init(d); window.__fx = d; }''')
        eq('a hint and a label added later are painted by GGID.init(node)',
           pg.evaluate('() => [...window.__fx.querySelectorAll("p, span")].map(e => e.textContent)'), ['Подтвердите вход: Touch ID на этом устройстве.', 'Войти с Touch ID'])
        ok('page: console and exceptions clean (icons)', not errs, errs[:3])
        ctx.close()

    # ---- 4. the rules of the memory ----
    def memory_rules():
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        errs = []
        pg = page_in(ctx, errs, query='?layout=minimal')
        na = '{ name: "NotAllowedError" }'
        scenarios = [
            # (name, storage before, js, storage after)
            ('device confirmed: key flag and last method', {}, 'GGID.passkeyRemember("platform")', {L: '1', S: 'platform'}),
            ('phone confirmed: last method only, no key of the device', {}, 'GGID.passkeyRemember("cross-platform")', {S: 'cross-platform'}),
            ('the browser says nothing: nothing is learned', {}, 'GGID.passkeyRemember("")', {}),
            ('an unknown answer teaches nothing', {}, 'GGID.passkeyRemember("security-key")', {}),
            ('no argument teaches nothing', {}, 'GGID.passkeyRemember()', {}),
            ('device confirmed after a miss: the miss goes, the key stays', {L: '1', S: 'platform', M: '1'}, 'GGID.passkeyRemember("platform")', {L: '1', S: 'platform'}),
            ('phone confirmed after a miss: the key of the device is gone', {L: '1', S: 'platform', M: '1'}, 'GGID.passkeyRemember("cross-platform")', {S: 'cross-platform'}),
            ('phone confirmed without a miss: the key of the device stays', {L: '1', S: 'platform'}, 'GGID.passkeyRemember("cross-platform")', {L: '1', S: 'cross-platform'}),
            ('device confirmed after the phone: the key of the device is back', {S: 'cross-platform'}, 'GGID.passkeyRemember("platform")', {L: '1', S: 'platform'}),
            ('NotAllowedError with a key of the device: a miss', {L: '1', S: 'platform'}, f'GGID.passkeyMissed({na})', {L: '1', S: 'platform', M: '1'}),
            ('NotAllowedError with the key flag and the phone last: a miss', {L: '1', S: 'cross-platform'}, f'GGID.passkeyMissed({na})', {L: '1', S: 'cross-platform', M: '1'}),
            ('NotAllowedError without a key of the device: nothing', {}, f'GGID.passkeyMissed({na})', {}),
            ('NotAllowedError with only the last method: nothing', {S: 'platform'}, f'GGID.passkeyMissed({na})', {S: 'platform'}),
            ('AbortError with a key: nothing', {L: '1', S: 'platform'}, 'GGID.passkeyMissed({ name: "AbortError" })', {L: '1', S: 'platform'}),
            ('InvalidStateError with a key: nothing', {L: '1', S: 'platform'}, 'GGID.passkeyMissed({ name: "InvalidStateError" })', {L: '1', S: 'platform'}),
            ('InvalidStateError without a key: nothing, no key is claimed', {}, 'GGID.passkeyMissed({ name: "InvalidStateError" })', {}),
            ('no error object: nothing', {L: '1', S: 'platform'}, 'GGID.passkeyMissed()', {L: '1', S: 'platform'}),
            ('«Не сейчас»: the time is stored', {}, 'GGID.passkeySnooze()', {Z: 'NOW'}),
            ('«Не сейчас» does not touch the rest', {L: '1', S: 'platform'}, 'GGID.passkeySnooze()', {L: '1', S: 'platform', Z: 'NOW'}),
            ('«Не сейчас» keeps a miss', {L: '1', S: 'platform', M: '1'}, 'GGID.passkeySnooze()', {L: '1', S: 'platform', M: '1', Z: 'NOW'}),
        ]
        for name, before, code, after in scenarios:
            pg.evaluate(SET_STORE, before)
            pg.evaluate('() => { ' + code + '; }')
            got = pg.evaluate(STORE)
            if Z in after:
                ok(f'memory: {name}: the time is now', abs(int(got.get(Z, '0') or 0) - pg.evaluate('Date.now()')) < 60000, got.get(Z))
                got = {k: v for k, v in got.items() if k != Z}
                after = {k: v for k, v in after.items() if k != Z}
            eq(f'memory: {name}', got, after)
        # the week: «Не сейчас» an hour short of 7 days ago still holds, an hour past 7 days does not (so neither a shorter nor a longer pause passes);
        # garbage and zero are not a pause
        for hours, want in ((0, True), (144, True), (167, True), (169, False), (192, False)):
            pg.evaluate(SET_STORE, {Z: str(pg.evaluate('Date.now()') - hours * 3600000)})
            eq(f'snoozed {hours} hours after «Не сейчас»', pg.evaluate('() => GGID.passkeyMemory().snoozed'), want)
        for junk in ('', 'abc', '0', '1e21'):
            pg.evaluate(SET_STORE, {Z: junk})
            eq(f'snoozed with {junk!r} in the box', pg.evaluate('() => GGID.passkeyMemory().snoozed'), False)
        # a time from the future (junk in the box, a clock that was set ahead) is not a pause
        for ahead in (3600000, 6 * 86400000, 30 * 86400000, 400 * 86400000):
            pg.evaluate(SET_STORE, {Z: str(pg.evaluate('Date.now()') + ahead)})
            eq(f'snoozed when the stored time is {ahead // 3600000} hours ahead', pg.evaluate('() => GGID.passkeyMemory().snoozed'), False)
        pg.evaluate(SET_STORE, {})
        eq('snoozed in an empty browser', pg.evaluate('() => GGID.passkeyMemory().snoozed'), False)
        # a whole life of a browser: phone first, then the key of the device appears, fails once, and the phone answers
        pg.evaluate(SET_STORE, {})
        for code, label, store in (('GGID.passkeyRemember("cross-platform")', 'Войти с Face ID', {S: 'cross-platform'}),
                                   ('GGID.passkeyRemember("platform")', 'Войти с Touch ID', {L: '1', S: 'platform'}),
                                   ('GGID.passkeyMissed({ name: "NotAllowedError" })', 'Войти с Touch ID', {L: '1', S: 'platform', M: '1'}),
                                   ('GGID.passkeyRemember("cross-platform")', 'Войти с Face ID', {S: 'cross-platform'})):
            pg.evaluate('() => { ' + code + '; }')
            eq(f'life: {code} -> label', pg.evaluate('() => GGID.passkeyText("login", "touchid")'), label)
            eq(f'life: {code} -> storage', pg.evaluate(STORE), store)
        # nothing but the four names is ever written
        pg.evaluate(SET_STORE, {})
        pg.evaluate('() => { for (const h of ["platform", "cross-platform", "", "x"]) GGID.passkeyRemember(h); GGID.passkeyMissed({ name: "NotAllowedError" }); '
                    'GGID.passkeySnooze(); GGID.passkeyCreated(); GGID.init(document); GGID.passkeyText("login"); GGID.passkeyHint(); }')
        ok('memory: only the four shared names are ever written', set(pg.evaluate(STORE)) <= set(KEYS.values()), list(pg.evaluate(STORE)))
        ok('page: console and exceptions clean (memory)', not errs, errs[:3])
        ctx.close()

    # ---- 5. a browser that remembers nothing or has no WebAuthn: the kit still works and promises nothing ----
    def degraded():
        for how, script in (
                ('storage methods throw', '''(() => { const boom = () => { throw new DOMException('denied', 'SecurityError'); };
                    Storage.prototype.getItem = boom; Storage.prototype.setItem = boom; Storage.prototype.removeItem = boom; })()'''),
                ('localStorage getter throws', '''Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('denied', 'SecurityError'); } })'''),
                ('no PublicKeyCredential', '''(() => { try { delete window.PublicKeyCredential; } catch (e) { window.PublicKeyCredential = undefined; } })()''')):
            ctx = b.new_context(user_agent=DEVICES['mac-safari'][0], viewport={'width': 1280, 'height': 800})
            ctx.add_init_script(device_script('mac-safari'))
            errs = []
            pg = page_in(ctx, errs, file=None)
            pg.add_init_script(script)
            pg.goto('file://' + os.path.join(SCREENS, 'login.html') + '?layout=split')
            r = pg.evaluate(READ)
            eq(f'{how}: a Mac says Face ID, not Touch ID', r['text'], 'Войти с Face ID')
            ok(f'{how}: no method of the device on the screen', not BANNED.search(r['page']), BANNED.findall(r['page']))
            res = pg.evaluate('''() => { const out = {};
              for (const [n, f] of Object.entries({ remember: () => GGID.passkeyRemember('platform'), missed: () => GGID.passkeyMissed({ name: 'NotAllowedError' }),
                snooze: () => GGID.passkeySnooze(), created: () => GGID.passkeyCreated(), watch: () => GGID.passkeyWatch(), init: () => GGID.init(document) })) {
                try { f(); out[n] = 'ok'; } catch (e) { out[n] = String(e); } }
              out.memory = GGID.passkeyMemory(); out.hint = GGID.passkeyHint(); out.text = GGID.passkeyText('login'); return out; }''')
            for name in ('remember', 'missed', 'snooze', 'created', 'watch', 'init'):
                eq(f'{how}: GGID.{name} does not throw', res[name], 'ok')
            if how != 'no PublicKeyCredential':
                eq(f'{how}: nothing is remembered', [res['memory']['own'], res['memory']['last'], res['memory']['snoozed']], [False, '', False])
                eq(f'{how}: the hint stays the honest default', res['hint'], HINT_UNKNOWN)
                eq(f'{how}: the label stays Face ID', res['text'], 'Войти с Face ID')
            ok(f'{how}: console and exceptions clean', not errs, errs[:3])
            ctx.close()

    # ---- 6. demo mode (the showcase) keeps the words of the markup whatever the browser remembers ----
    def demo_mode():
        ctx = b.new_context(user_agent=DEVICES['mac-safari'][0], viewport={'width': 1280, 'height': 800})
        ctx.add_init_script(device_script('mac-safari'))
        errs = []
        pg = page_in(ctx, errs, file='passkey.html', query='?layout=minimal')
        pg.evaluate(SET_STORE, STATES['own key'][0])
        words = '() => [...document.querySelectorAll("[data-gid-passkey], [data-gid-passkey-hint]")].map(e => e.textContent)'
        before = pg.evaluate(words)
        pg.evaluate('() => GGID.init(document, { demo: true })')
        eq('demo mode leaves the words of the markup, even with an own key in the browser', pg.evaluate(words), before)
        pg.evaluate('() => GGID.init(document)')
        ok('real mode repaints the same markup', pg.evaluate(words) != before, pg.evaluate(words))
        ok('page: console and exceptions clean (demo)', not errs, errs[:3])
        ctx.close()

    # ---- 7. WebAuthn of Chromium, for real: virtual authenticators over CDP, navigator.credentials is not replaced ----
    def serve(route):
        path = route.request.url[len(ORIGIN):].split('?')[0].split('#')[0]
        local = os.path.join(ROOT, path.lstrip('/'))
        if os.path.isfile(local):
            return route.fulfill(path=local)
        return route.fulfill(status=404, body='')

    def secure_page(transports, errs):
        c = b.new_context(user_agent=DEVICES['mac-safari'][0], viewport={'width': 1280, 'height': 800})
        c.add_init_script(device_script('mac-safari'))
        p = c.new_page()
        p.route(ORIGIN + '/**', serve)
        p.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        p.on('pageerror', lambda x: errs.append(f'pageerror: {x}'))
        p.goto(ORIGIN + '/gg-id/screens/login.html?layout=split')
        cdp = c.new_cdp_session(p)
        cdp.send('WebAuthn.enable')
        for transport in transports:
            cdp.send('WebAuthn.addVirtualAuthenticator', {'options': {'protocol': 'ctap2', 'transport': transport, 'hasResidentKey': True,
                                                                         'hasUserVerification': True, 'isUserVerified': True, 'automaticPresenceSimulation': True}})
        return c, p

    def webauthn_device_key():
        errs = []
        ctx, pg = secure_page(['internal'], errs)
        eq('webauthn: the page is a secure context with navigator.credentials', pg.evaluate('() => typeof navigator.credentials.create'), 'function')
        pg.evaluate('() => { GGID.passkeyWatch(); window.__g = navigator.credentials.get; window.__c = navigator.credentials.create; GGID.passkeyWatch(); }')
        eq('webauthn: GGID.passkeyWatch is idempotent (the second call wraps nothing again)',
           pg.evaluate('() => [navigator.credentials.get === window.__g, navigator.credentials.create === window.__c]'), [True, True])
        eq('webauthn: the wrapper carries the mark of this copy of the kit', pg.evaluate('() => typeof navigator.credentials.get._gidWatch'), 'object')
        eq('webauthn: nothing seen before the first call', pg.evaluate('() => GGID.passkeySeen()'), '')
        eq('webauthn: a key made on the internal authenticator says platform', pg.evaluate(CREATE, 'platform'), 'platform')
        eq('webauthn: GGID.passkeySeen() read platform from the real answer', pg.evaluate('() => GGID.passkeySeen()'), 'platform')
        pg.evaluate('() => GGID.passkeyCreated()')
        eq('webauthn: created on the device -> key flag and platform', pg.evaluate(STORE), {L: '1', S: 'platform'})
        pg.reload()
        eq('webauthn: the next load of the screen names the device on a Mac', pg.evaluate(READ)['text'], 'Войти с Touch ID')
        pg.evaluate('() => GGID.passkeyWatch()')
        eq('webauthn: a real sign-in with the key of the device says platform', pg.evaluate(GET), 'platform')
        pg.evaluate('() => GGID.passkeyRemember(GGID.passkeySeen())')
        eq('webauthn: signed in by the device -> still platform, key flag kept', pg.evaluate(STORE), {L: '1', S: 'platform'})
        ok('webauthn: console and exceptions clean (internal)', not errs, errs[:3])
        ctx.close()

    def webauthn_phone_key():
        errs = []
        ctx, pg = secure_page(['usb'], errs)
        pg.evaluate('() => GGID.passkeyWatch()')
        eq('webauthn: a key made on a USB authenticator says cross-platform', pg.evaluate(CREATE, 'cross-platform'), 'cross-platform')
        pg.evaluate('() => GGID.passkeyCreated()')
        eq('webauthn: created elsewhere -> no key of the device is claimed', pg.evaluate(STORE), {S: 'cross-platform'})
        eq('webauthn: a real sign-in with the USB key says cross-platform', pg.evaluate(GET), 'cross-platform')
        pg.evaluate('() => GGID.passkeyRemember(GGID.passkeySeen())')
        eq('webauthn: signed in by the phone/USB key -> cross-platform, no key of the device', pg.evaluate(STORE), {S: 'cross-platform'})
        pg.reload()
        r = pg.evaluate(READ)
        eq('webauthn: after the phone, a Mac still says Face ID', r['text'], 'Войти с Face ID')
        ok('webauthn: after the phone, no method of the device on the screen', not BANNED.search(r['page']), BANNED.findall(r['page']))
        pg.goto(ORIGIN + '/gg-id/screens/passkey.html?layout=split')
        eq('webauthn: after the phone, the waiting hint tells to point the phone at the QR code', pg.evaluate(READ)['hint'], HINT_PHONE)
        # a refused call leaves nothing seen: the answer of the previous call is not taken for the next one
        pg.evaluate('() => GGID.passkeyWatch()')
        pg.evaluate(GET)
        eq('webauthn: seen after a working call', pg.evaluate('() => GGID.passkeySeen()'), 'cross-platform')
        failed = pg.evaluate('''async () => { try { await navigator.credentials.get({ publicKey: { challenge: new Uint8Array([1]), rpId: 'not-this-site.example',
          userVerification: 'required' } }); return 'resolved'; } catch (e) { return e.name + '|' + GGID.passkeySeen(); } }''')
        ok('webauthn: a refused call leaves nothing seen', failed.endswith('|'), failed)
        ok('webauthn: console and exceptions clean (usb)', not errs, errs[:3])
        ctx.close()

    def webauthn_stub():
        # a browser that answers without authenticatorAttachment: sign-in teaches nothing, a key it made for the device counts as the device's
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        errs = []
        pg = page_in(ctx, errs, query='?layout=minimal')
        pg.evaluate('''() => { const mk = (a) => ({ id: 'x', type: 'public-key', ...(a === undefined ? {} : { authenticatorAttachment: a }) });
          window.__answer = undefined; window.__calls = 0;
          Object.defineProperty(navigator, 'credentials', { configurable: true, value: {
            get() { window.__calls++; return Promise.resolve(mk(window.__answer)); }, create() { window.__calls++; return Promise.resolve(mk(window.__answer)); } } });
          GGID.passkeyWatch(); }''')
        pg.evaluate(SET_STORE, {})
        pg.evaluate('async () => { await navigator.credentials.get(); GGID.passkeyRemember(GGID.passkeySeen()); }')
        eq('stub: sign-in without authenticatorAttachment teaches nothing', pg.evaluate(STORE), {})
        pg.evaluate('async () => { await navigator.credentials.create(); GGID.passkeyCreated(); }')
        eq('stub: a key made for the device with no attachment in the answer counts as the key of the device', pg.evaluate(STORE), {L: '1', S: 'platform'})
        pg.evaluate(SET_STORE, {})
        pg.evaluate('async () => { window.__answer = "cross-platform"; await navigator.credentials.create(); GGID.passkeyCreated(); }')
        eq('stub: a key the browser says is cross-platform is not the key of the device', pg.evaluate(STORE), {S: 'cross-platform'})
        pg.evaluate(SET_STORE, {})
        pg.evaluate('async () => { window.__answer = "platform"; await navigator.credentials.get(); GGID.passkeyRemember(GGID.passkeySeen()); }')
        eq('stub: sign-in says platform -> the key of the device', pg.evaluate(STORE), {L: '1', S: 'platform'})
        eq('stub: the wrapper passes the call through (one call each)', pg.evaluate('() => window.__calls'), 4)
        # an attachment the specification does not know (junk, a future value) is not seen: it teaches nothing and is not handed on as an answer
        pg.evaluate(SET_STORE, {})
        pg.evaluate('async () => { window.__answer = "security-key"; await navigator.credentials.get(); GGID.passkeyRemember(GGID.passkeySeen()); }')
        eq('stub: an unknown authenticatorAttachment is not seen', pg.evaluate('() => GGID.passkeySeen()'), '')
        eq('stub: an unknown authenticatorAttachment teaches nothing', pg.evaluate(STORE), {})
        ok('stub: console and exceptions clean', not errs, errs[:3])
        ctx.close()

    def two_copies():
        # two copies of the kit on one page (say the hub's and a service's): each keeps its own `seen`, and a copy never takes the wrapper of another for its own
        errs = []
        ctx, pg = secure_page(['usb'], errs)
        src = open(os.path.join(KIT, 'gg-id.js'), encoding='utf-8').read()
        pg.evaluate('(src) => { const a = window.GGID; (0, eval)(src); window.GGID_B = window.GGID; window.GGID = a; }', src)
        ok('two copies: the second copy is a separate object', pg.evaluate('() => window.GGID_B && window.GGID_B !== window.GGID && !!GGID_B.passkeyWatch'))
        pg.evaluate('() => { GGID.passkeyWatch(); GGID_B.passkeyWatch(); }')
        eq('two copies: a key made on a USB authenticator says cross-platform', pg.evaluate(CREATE, 'cross-platform'), 'cross-platform')
        eq('two copies: both copies saw the answer', pg.evaluate('() => [GGID.passkeySeen(), GGID_B.passkeySeen()]'), ['cross-platform', 'cross-platform'])
        pg.evaluate(SET_STORE, {})
        pg.evaluate('() => GGID_B.passkeyCreated()')
        eq('two copies: the second copy does not claim a key of the device for a key made elsewhere', pg.evaluate(STORE), {S: 'cross-platform'})
        pg.evaluate(SET_STORE, {})
        pg.evaluate('() => GGID.passkeyCreated()')
        eq('two copies: nor does the first one', pg.evaluate(STORE), {S: 'cross-platform'})
        ok('two copies: console and exceptions clean', not errs, errs[:3])
        ctx.close()

    def partial_credentials():
        # a browser whose navigator.credentials has no create: the answer to a key made here cannot be seen, so the created key is not written down;
        # without get only the sign-in cannot be seen, and a created key (its answer is visible) still counts
        for missing, want in (('create', {}), ('get', {L: '1', S: 'platform'})):
            ctx = b.new_context(viewport={'width': 1280, 'height': 800})
            errs = []
            pg = page_in(ctx, errs, query='?layout=minimal')
            pg.evaluate("""(m) => { const c = { get() { return Promise.resolve({ authenticatorAttachment: 'platform' }); },
                create() { return Promise.resolve({ authenticatorAttachment: 'platform' }); } };
              delete c[m]; Object.defineProperty(navigator, 'credentials', { configurable: true, value: c }); GGID.passkeyWatch(); }""", missing)
            pg.evaluate(SET_STORE, {})
            pg.evaluate('async () => { if (navigator.credentials.create) await navigator.credentials.create(); GGID.passkeyCreated(); }')
            eq(f'navigator.credentials without {missing}: what a created key writes down', pg.evaluate(STORE), want)
            ok(f'navigator.credentials without {missing}: console and exceptions clean', not errs, errs[:3])
            ctx.close()
        # a create that cannot be wrapped (an accessor whose setter swallows the assignment): the answer to a key made here cannot be seen either
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        errs = []
        pg = page_in(ctx, errs, query='?layout=minimal')
        pg.evaluate("""() => { const f = () => Promise.resolve({ authenticatorAttachment: 'platform' }); const c = { get: f };
          Object.defineProperty(c, 'create', { get() { return f; }, set() {} });
          Object.defineProperty(navigator, 'credentials', { configurable: true, value: c }); GGID.passkeyWatch(); }""")
        pg.evaluate(SET_STORE, {})
        pg.evaluate('async () => { await navigator.credentials.create(); GGID.passkeyCreated(); }')
        eq('navigator.credentials.create that cannot be wrapped: a created key is not written down', pg.evaluate(STORE), {})
        ok('navigator.credentials.create that cannot be wrapped: console and exceptions clean', not errs, errs[:3])
        ctx.close()
        # passkeyWatch() again on a navigator.credentials that has lost create meanwhile: the earlier verdict does not stay, a created key is not written down
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        errs = []
        pg = page_in(ctx, errs, query='?layout=minimal')
        pg.evaluate("""() => { const mk = () => ({ get() { return Promise.resolve({ authenticatorAttachment: 'platform' }); },
            create() { return Promise.resolve({ authenticatorAttachment: 'platform' }); } });
          Object.defineProperty(navigator, 'credentials', { configurable: true, value: mk() }); GGID.passkeyWatch();
          const c = mk(); delete c.create; Object.defineProperty(navigator, 'credentials', { configurable: true, value: c }); GGID.passkeyWatch(); }""")
        pg.evaluate(SET_STORE, {})
        pg.evaluate('() => GGID.passkeyCreated()')
        eq('passkeyWatch() again without create: a created key is not written down', pg.evaluate(STORE), {})
        ok('passkeyWatch() again without create: console and exceptions clean', not errs, errs[:3])
        ctx.close()

    def no_markup_no_storage():
        # a page without passkey markup (the PIN gate pages of the hub inline the whole kit) is left alone: the kit does not even read the storage there
        for screen, reads in (('forgot.html', False), ('pin.html', False), ('login.html', True), ('enroll.html', True)):
            ctx = b.new_context(viewport={'width': 1280, 'height': 800})
            ctx.add_init_script("""(() => { window.__reads = 0; const g = Storage.prototype.getItem;
              Storage.prototype.getItem = function () { window.__reads++; return g.apply(this, arguments); }; })()""")
            errs = []
            pg = page_in(ctx, errs, file=screen, query='?layout=split')
            n = pg.evaluate('() => window.__reads')
            ok(f'{screen}: the kit reads the storage only where there is passkey markup ({n} reads)', (n > 0) == reads, n)
            ok(f'{screen}: console and exceptions clean', not errs, errs[:3])
            ctx.close()

    def no_watch():
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        errs = []
        pg = page_in(ctx, errs, query='?layout=minimal')
        pg.evaluate(SET_STORE, {})
        pg.evaluate('() => GGID.passkeyCreated()')
        eq('without GGID.passkeyWatch() a created key is not written down (the answer of the browser is not visible)', pg.evaluate(STORE), {})
        eq('without GGID.passkeyWatch() nothing is seen', pg.evaluate('() => GGID.passkeySeen()'), '')
        ok('page: console and exceptions clean (no watch)', not errs, errs[:3])
        ctx.close()

    for fn in (sources, guard_words, explicit_kinds, devices, icon_path, memory_rules, degraded, demo_mode, webauthn_device_key, webauthn_phone_key, two_copies,
               webauthn_stub, partial_credentials, no_markup_no_storage, no_watch):
        section(fn)


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    problems, counts = [], {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        _new_context = browser.new_context

        def new_context(**kw):
            c = _new_context(**kw)
            c.set_default_timeout(60000)
            c.set_default_navigation_timeout(60000)
            return c
        browser.new_context = new_context
        run(browser, problems, counts)
        browser.close()
    if problems:
        print('GG ID PASSKEY WORDING FAILED |', counts.get('passkey', 0), 'checks')
        for x in problems:
            print(' -', x)
        sys.exit(1)
    print('ok:', counts.get('passkey', 0), 'passkey wording checks')
