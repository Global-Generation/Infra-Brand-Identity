"""Build GG ID (единый вход): gg-id/fonts/*.woff2, gg-id/screens/*.html and the showcase gg-id.html.

Sources: gg-id/gg-id.css + gg-id/gg-id.js (the kit, edited by hand), src/gg_id/screens.html (screens),
src/gg_id/showcase.html (showcase page), src/fonts.css, src/global-logo.svg, src/gg-icon.svg, assets/favicons/root.svg.

Run: python3 src/build_gg_id.py
"""
import base64
import html as htmlmod
import json
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIT = os.path.join(ROOT, 'gg-id')
ICON_DIR = os.path.join(HERE, 'lucide-icons')


def read(*p):
    return open(os.path.join(*p), encoding='utf-8').read()


def write_if_changed(path, data):
    mode = 'wb' if isinstance(data, bytes) else 'w'
    old = None
    if os.path.exists(path):
        old = open(path, 'rb' if mode == 'wb' else 'r', **({} if mode == 'wb' else {'encoding': 'utf-8'})).read()
    if old != data:
        with open(path, mode, **({} if mode == 'wb' else {'encoding': 'utf-8'})) as f:
            f.write(data)


# ---- fonts: the variable Montserrat, one file per subset (all weights share it) ----
fonts_css = read(HERE, 'fonts.css')
faces = re.findall(r'@font-face\s*{(.*?)}', fonts_css, flags=re.S)
woff = {}
for f in faces:
    rng = re.search(r'unicode-range:\s*([^;]+)', f).group(1)
    b64 = re.search(r'base64,([A-Za-z0-9+/=]+)', f).group(1)
    subset = 'cyrillic' if 'U+0400' in rng else 'latin'
    if subset in woff:
        assert woff[subset] == b64, f'{subset}: weights are expected to share one variable font file'
    woff[subset] = b64
assert set(woff) == {'cyrillic', 'latin'}, woff.keys()
os.makedirs(os.path.join(KIT, 'fonts'), exist_ok=True)
for subset, b64 in woff.items():
    write_if_changed(os.path.join(KIT, 'fonts', f'montserrat-{subset}.woff2'), base64.b64decode(b64))

kit_css = read(KIT, 'gg-id.css')
kit_js = read(KIT, 'gg-id.js')
for subset in woff:
    assert f'url(fonts/montserrat-{subset}.woff2)' in kit_css, f'gg-id.css must load fonts/montserrat-{subset}.woff2'
inline_css = kit_css
for subset, b64 in woff.items():
    inline_css = inline_css.replace(f'url(fonts/montserrat-{subset}.woff2)', f'url(data:font/woff2;base64,{b64})')

# ---- logo, mark, root favicon ----
logo_paths = re.findall(r'<path d="([^"]+)"', read(HERE, 'global-logo.svg'))
assert len(logo_paths) == 20, len(logo_paths)
LOGO = ''.join(f'<path d="{d}"/>' for d in logo_paths)
LETTERS = ''.join(f'<path d="{d}"/>' for d in logo_paths[:16])  # 0-15 = GLOBAL GENERATION, 16-19 = mark
mark = re.findall(r'<path d="([^"]+)"', read(HERE, 'gg-icon.svg'))
assert len(mark) == 4, len(mark)
ARC, RIGHT_TOP, MAIN, RIGHT_BOTTOM = mark
root_svg = read(ROOT, 'assets', 'favicons', 'root.svg').strip()
root_inner = re.sub(r'^<svg[^>]*>|</svg>$', '', root_svg).strip()
# unique ids so the tile can sit next to other inline SVGs on a service page
root_inner = root_inner.replace('id="ggr"', 'id="gid-tile-clip"').replace('url(#ggr)', 'url(#gid-tile-clip)')
root_inner = root_inner.replace('paint0_radial_184_3', 'gid-tile-grad')
FAVICON_URI = 'data:image/svg+xml,' + urllib.parse.quote(root_svg, safe='')

AURA = ('<circle cx="21" cy="21" r="19" fill="none" stroke="currentColor" stroke-width="2.4" opacity=".3"/>'
        '<circle cx="21" cy="21" r="12" fill="none" stroke="currentColor" stroke-width="2.6" opacity=".6"/>'
        '<circle cx="21" cy="21" r="6"/>')

LOCKUP = ('<div class="gid-lockup"><svg class="gid-logo" viewBox="0 0 777 196" role="img" aria-label="Global Generation">'
          '<use href="#gid-logo"/></svg><span class="gid-lockup-name">ID</span></div>')
LOADER = ('<div class="gid-ld" aria-hidden="true"><svg class="gid-ld-mark" viewBox="3.6 8.6 31.3 20.95">'
          f'<path class="gid-ld-arc" d="{ARC}"/><path class="gid-ld-right" d="{RIGHT_TOP} {RIGHT_BOTTOM}"/>'
          f'<path class="gid-ld-main" d="{MAIN}"/></svg><span class="gid-ld-word"><svg viewBox="336 89 444 110">{LETTERS}</svg></span></div>')

# services in the split panel marquee (GG only, Aura products are not GG ID)
SERVICES = ['АКБ', 'Пульс', 'Кабинет ментора', 'Студенческий портал', 'Юротдел', 'Бухгалтерия', 'Онбординг', 'Репортер',
            'Стратегия', 'Продакшн', 'Фабрика роликов', 'YouTube-трекер', 'Маяк', 'Notetaker', 'Консультации',
            'Структура команды', 'Инфра-косты', 'CRM-чаты', 'LLM-расходы', 'Анкета']


def mq_row(i):
    names = SERVICES[i * 4 % len(SERVICES):] + SERVICES[:i * 4 % len(SERVICES)]
    one = ''.join(f'<span>{n}</span>' for n in names)
    return f'<div class="gid-mq-row">{one}{one}</div>'


ASIDE = ('<aside class="gid-aside">' + LOCKUP +
         '<div class="gid-mq" aria-hidden="true">' + ''.join(mq_row(i) for i in range(5)) + '</div>'
         '<div class="gid-aside-copy"><p class="gid-aside-title">Один вход во все сервисы Global&nbsp;Generation</p>'
         '<p class="gid-aside-sub">АКБ, Пульс, Кабинет ментора, Юротдел, Продакшн и остальные сервисы команды открываются '
         'с одним GG ID. Без отдельного пароля в каждом.</p></div></aside>')
FOOT = '<footer class="gid-foot"><span><b>GG ID</b> · единый вход Global Generation</span></footer>'


def shell(layout, card_inner, key):
    return (f'<div class="gid" data-layout="{layout}"><div class="gid-frame">{ASIDE}'
            f'<main class="gid-main"><section class="gid-card" data-gid-screen="{key}">{card_inner}</section>{FOOT}</main>'
            '</div></div>')


# ---- screens ----
src = read(HERE, 'gg_id', 'screens.html')
SCREENS = []
for attrs, body in re.findall(r'<template ([^>]*)>(.*?)</template>', src, flags=re.S):
    a = dict(re.findall(r'(data-[a-z]+)="([^"]*)"', attrs))
    body = body.strip().replace('@LOADER@', LOADER)
    SCREENS.append({'key': a['data-key'], 'tab': a['data-tab'], 'title': a['data-title'],
                    'lockup': a.get('data-lockup') != 'off', 'body': body})
KEYS = [s['key'] for s in SCREENS]
assert len(KEYS) == len(set(KEYS)), KEYS
for s in SCREENS:
    for target in re.findall(r'data-go(?:-submit|-complete)?="([a-z]+)"', s['body']):
        assert target in KEYS, f'{s["key"]}: data-go to unknown screen {target}'

# when each screen shows and what it calls on the hub (levauth, Lambda gg-portal-auth)
INFO = {
    'login': ('Первый экран. Главная кнопка Face ID, если на устройстве есть ключ входа; если нет, сразу экран пароля. Aura только ссылкой и только когда сервер включил.',
              'GET /api/auth/capabilities, GGPasskey.enabled(), GGPasskey.login()'),
    'password': ('Почта и пароль. После входа без ключа на устройстве предлагаем подключить Face ID.', 'POST /api/auth/login'),
    'error': ('401: неверная почта или пароль, поля трясутся, пароль очищается. 429: «Слишком много попыток, подождите минуту». Сеть: «Сеть недоступна».',
              'POST /api/auth/login: 401, 429'),
    'passkey': ('Открыто системное окно Face ID. Кнопка занята, второй запрос не уходит. Отмена в системном окне возвращает на первый экран без ошибки.',
                'GGPasskey.login()'),
    'done': ('Вход выполнен, идёт переход в сервис. Фирменная сборка знака, как прелоудер бренда.', 'GET /api/auth/me, переход на next'),
    'continue': ('Сессия GG ID на устройстве уже есть, сервис просит подтвердить аккаунт.', 'GET /api/auth/authorize'),
    'enroll': ('После входа по паролю, если ключа на этом устройстве нет. Совет: после «Не сейчас» не спрашивать на этом устройстве неделю.',
               'GGPasskey.register()'),
    'forgot': ('Восстановление по рабочей почте.', 'POST /api/auth/forgot'),
    'sent': ('Ответ одинаковый, есть такая почта в GG ID или нет: так нельзя проверить, кто в команде.', 'POST /api/auth/forgot: 200'),
    'setpass': ('Ссылка из приглашения или восстановления (#token=). Приглашение: «Добро пожаловать в команду», восстановление: «Новый пароль». Правила как на сервере.',
                'POST /api/auth/set-password/check, POST /api/auth/set-password'),
    'saved': ('После сохранения пароля. Сессии нет, человек идёт ко входу, браузер сам подставит новый пароль.', 'POST /api/auth/set-password: 200'),
    'resetoff': ('capabilities.password_reset не true: восстановление по почте выключено, вместо формы эта плашка.', 'GET /api/auth/capabilities'),
    'expired': ('Токен из ссылки устарел или уже использован.', 'POST /api/auth/set-password/check: ошибка'),
    'noaccess': ('Человек вошёл, но роли в этом сервисе у него нет.', 'GET /api/auth/me (level), entitlements'),
    'pin': ('Переходный вход по коду для сервисов, которые ещё не на GG ID.', 'sso-gate: PIN-ворота'),
    'unavailable': ('GG ID не отвечает (5xx или таймаут). Страница сама пробует снова.', 'sso-gate: sso-unavailable'),
    'signedout': ('После «Выйти» в меню аккаунта.', 'POST /api/v1/sessions/revoke'),
}
assert set(INFO) == set(KEYS), set(INFO) ^ set(KEYS)

# ---- icon sprite ----
def icon_inner(name):
    s = read(ICON_DIR, name + '.svg')
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S).strip()
    body = s.split('>', 1)[1].rsplit('</svg>', 1)[0]
    return re.sub(r'\s+', ' ', body).replace(' />', '/>').strip()


def sprite(text):
    names = set(re.findall(r'#gi-([a-z0-9-]+)', text))
    if 'data-gid-passkey-icon' in text:  # gg-id.js swaps the passkey icon per device
        names |= {'scan-face', 'fingerprint', 'key-round'}
    names = sorted(names)
    parts = []
    for n in names:
        if n == 'aura':
            parts.append(f'<symbol id="gi-aura" viewBox="0 0 42 42">{AURA}</symbol>')
        else:
            parts.append(f'<symbol id="gi-{n}" viewBox="0 0 24 24">{icon_inner(n)}</symbol>')
    if '#gid-logo' in text:
        parts.append(f'<symbol id="gid-logo" viewBox="0 0 777 196">{LOGO}</symbol>')
    if '#gid-tile' in text:
        parts.append(f'<symbol id="gid-tile" viewBox="0 0 39 39">{root_inner}</symbol>')
    return '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + ''.join(parts) + '</svg>'


# ---- brand asserts (same list as build.py) ----
def brand_check(name, text):
    problems = []
    leftover = re.findall(r'@[A-Z_]+@|/\*@[A-Z_]+@\*/|<!--@[A-Z_]+@-->', text)
    if leftover:
        problems.append(f'unfilled placeholders: {leftover[:5]}')
    for bad, why in [('—', 'em-dash'), ('–', 'en-dash'), ('&mdash;', 'em-dash entity'), ('&ndash;', 'en-dash entity'),
                     ('&#8212;', 'em-dash entity'), ('&#x2014;', 'em-dash entity'),
                     ('fonts.googleapis', 'google fonts'), ('fonts.gstatic', 'google fonts'),
                     ('5b4be0', 'violet'), ('6d5cf0', 'violet'), ('9286f0', 'violet'), ('4a39c8', 'violet'),
                     ('c4b5fd', 'lilac'), ('196, 181, 253', 'lilac'), ('196,181,253', 'lilac'),
                     ('наставник', 'наставник'), ('Mulish', 'Mulish font')]:
        if bad.lower() in text.lower():
            problems.append(f'{why}: {text.lower().count(bad.lower())}')
    emoji = re.findall('[\U0001F000-\U0001FAFF☀-➿⬀-⯿️]', text)
    if emoji:
        problems.append(f'emoji-like chars: {emoji[:10]}')
    ext = [u for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', text) 
           if u != 'https://mail.google.com/' and not u.startswith('https://levauth.global-generations-edu.com/')]
    if ext:
        problems.append(f'external resources: {ext}')
    if problems:
        print('BRAND CHECK FAILED in', name)
        for p in problems:
            print(' -', p)
        sys.exit(1)


brand_check('gg-id.css', kit_css)
brand_check('gg-id.js', kit_js)

# ---- standalone screens: gg-id/screens/<key>.html (reference for the hub, demo navigation only) ----
DEMO_NAV = """<script>
/* Демо-навигация между эталонными экранами. В хабе её нет: там кнопки вызывают /api/auth/* (README.md, таблица экранов).
   Раскладку и тему можно посмотреть параметрами: ?layout=card|minimal|split&theme=light|dark */
(function () {
  var q = new URLSearchParams(location.search), g = document.querySelector('.gid');
  if (/^(card|minimal|split)$/.test(q.get('layout') || '')) g.setAttribute('data-layout', q.get('layout'));
  if (/^(light|dark)$/.test(q.get('theme') || '')) g.setAttribute('data-theme', q.get('theme'));
  var keep = location.search;
  function go(k) { location.href = k + '.html' + keep; }
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-go]');
    if (t && !t.disabled) { e.preventDefault(); go(t.getAttribute('data-go')); }
  });
  document.addEventListener('submit', function (e) { var f = e.target; if (f.dataset.goSubmit) { e.preventDefault(); go(f.dataset.goSubmit); } });
  document.addEventListener('gid:code', function (e) { var b = e.target.closest('[data-go-complete]'); if (b) setTimeout(function () { go(b.dataset.goComplete); }, 350); });
})();
</script>"""

os.makedirs(os.path.join(KIT, 'screens'), exist_ok=True)
for s in SCREENS:
    body = s['body']
    body = re.sub(r'<a class="([^"]+)" data-go="([a-z]+)"', lambda m: f'<a class="{m.group(1)}" href="{m.group(2)}.html" data-go="{m.group(2)}"', body)
    card = (LOCKUP if s['lockup'] else '') + body
    page_body = shell('split', card, s['key'])
    page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#13445d" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#081b26" media="(prefers-color-scheme: dark)">
<title>{htmlmod.escape(s['title'])} · GG ID</title>
<link rel="icon" href="../../assets/favicons/root.svg" type="image/svg+xml">
<link rel="icon" href="../../assets/favicons/ico/root.ico" sizes="any">
<link rel="stylesheet" href="../gg-id.css">
</head>
<body class="gid-body">
<!-- Эталон GG ID, экран «{s['tab']}». Генерируется src/build_gg_id.py из src/gg_id/screens.html, руками не править. -->
{page_body}
{sprite(page_body)}
<script src="../gg-id.js"></script>
{DEMO_NAV}
</body>
</html>
"""
    brand_check(f'screens/{s["key"]}.html', page)
    write_if_changed(os.path.join(KIT, 'screens', s['key'] + '.html'), page)

# full sprite for the hub: every symbol any screen or service component uses (<use href="/assets/gg-id/sprite.svg#gi-eye">)
all_text = ''.join(s['body'] for s in SCREENS) + LOCKUP + read(HERE, 'gg_id', 'showcase.html') + ' data-gid-passkey-icon '
full = sprite(all_text).replace('<svg width="0" height="0" style="position:absolute" aria-hidden="true">',
                                '<svg xmlns="http://www.w3.org/2000/svg">', 1)
full = '<!-- GG ID: logo, root favicon tile and kit icons. Generated by src/build_gg_id.py -->\n' + full + '\n'
brand_check('gg-id/sprite.svg', full)
write_if_changed(os.path.join(KIT, 'sprite.svg'), full)

# drop screens that no longer exist in the source
for fn in os.listdir(os.path.join(KIT, 'screens')):
    if fn.endswith('.html') and fn[:-5] not in KEYS:
        os.remove(os.path.join(KIT, 'screens', fn))

# ---- showcase: gg-id.html (one self-contained file) ----
tpl = read(HERE, 'gg_id', 'showcase.html')
templates = ['<template id="tpl-lockup">' + LOCKUP + '</template>',
             '<template id="tpl-shell">' + shell('split', '', '') + '</template>']
templates += [f'<template id="scr-{s["key"]}">{s["body"]}</template>' for s in SCREENS]
templates = '\n'.join(templates)
meta = [{'key': s['key'], 'tab': s['tab'], 'title': s['title'], 'lockup': s['lockup'],
         'when': INFO[s['key']][0], 'api': INFO[s['key']][1]} for s in SCREENS]
api_rows = ''.join(
    f'<tr><td><b>{htmlmod.escape(m["tab"])}</b><span>screens/{m["key"]}.html</span></td><td>{htmlmod.escape(m["when"])}</td>'
    f'<td><code>{htmlmod.escape(m["api"]).replace("/", "/<wbr>").replace(", ", ",<br>")}</code></td></tr>' for m in meta)
page = (tpl
        .replace('/*@GID_CSS@*/', inline_css)
        .replace('/*@GID_JS@*/', kit_js.replace('</script', '<\\/script'))
        .replace('/*@META@*/', json.dumps(meta, ensure_ascii=False).replace('</', '<\\/'))
        .replace('<!--@TEMPLATES@-->', templates)
        .replace('<!--@API_ROWS@-->', api_rows)
        .replace('@LOCKUP@', LOCKUP)
        .replace('@FAVICON_URI@', FAVICON_URI)
        .replace('@N_SCREENS@', str(len(SCREENS))))
page = page.replace('<!--@SPRITE@-->', sprite(page))
brand_check('gg-id.html', page)
write_if_changed(os.path.join(ROOT, 'gg-id.html'), page)

# ---- gg-id/README.md: the screens table between markers, from the same INFO ----
readme_path = os.path.join(KIT, 'README.md')
readme = read(readme_path)
table = ['## Экраны', '', '| Экран | Файл | Когда | Хаб |', '|---|---|---|---|']
table += [f'| {m["tab"]} | `screens/{m["key"]}.html` | {m["when"]} | `{m["api"]}` |' for m in meta]
readme = re.sub(r'<!-- screens:start -->.*?<!-- screens:end -->',
                lambda _: '<!-- screens:start -->\n' + '\n'.join(table) + '\n<!-- screens:end -->', readme, flags=re.S)
brand_check('gg-id/README.md', readme)
write_if_changed(readme_path, readme)
print('ok gg-id.html', f'{len(page) / 1024:.0f} KB', '| screens:', len(SCREENS), '| fonts:', ', '.join(sorted(woff)))
