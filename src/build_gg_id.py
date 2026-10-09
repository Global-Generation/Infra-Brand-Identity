"""Build GG ID (единый вход): gg-id/fonts/*.woff2, gg-id/screens/*.html and the showcase gg-id.html.

Sources: gg-id/gg-id.css + gg-id/gg-id.js (the kit, edited by hand), src/gg_id/screens.html (screens),
src/gg_id/showcase.html (showcase page), src/fonts.css, src/global-logo.svg, src/gg-icon.svg, assets/favicons/gg-id.svg,
gg-id/email-card.html + gg-id/email/gg-id-lockup-2x.png (the e-mail card, checked here, PNG from src/rasterize_gg_id_email.py).

Run: python3 src/build_gg_id.py
"""
import base64
import hashlib
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
service_js = read(KIT, 'gg-id-service.js')   # поведение компонентов в сервисах: меню аккаунта, окно, 401
# версия кита: gg-id/VERSION, её же отдают GGID.version и GGIDService.version (сервис видит, какая копия у него). Поднимать при каждой правке кита
KIT_VERSION = read(KIT, 'VERSION').strip()
assert re.fullmatch(r'\d{4}-\d{2}-\d{2}(\.\d+)?', KIT_VERSION), f'gg-id/VERSION: дата релиза кита, например 2026-10-08.2, а не {KIT_VERSION!r}'
for _name, _src in (('gg-id.js', kit_js), ('gg-id-service.js', service_js)):
    _v = re.findall(r"version: '([^']+)'", _src)
    assert _v == [KIT_VERSION], f'{_name}: version {_v} должна быть равна gg-id/VERSION ({KIT_VERSION})'
for _name, _src in (('gg-id.js', kit_js), ('gg-id.css', kit_css)):   # и версия в шапке файла, её копируют руками
    assert f'версия {KIT_VERSION}' in _src.split('\n', 1)[0], f'{_name}: в первой строке должно быть «версия {KIT_VERSION}» (gg-id/VERSION)'
for subset in woff:
    assert f'url(fonts/montserrat-{subset}.woff2)' in kit_css, f'gg-id.css must load fonts/montserrat-{subset}.woff2'
# латиница с диакритикой и знаки валют (₽ U+20BD): подмножество latin-ext того же Montserrat v31 (Version 9.000, Google Fonts),
# что cyrillic и latin выше (они байт в байт равны v31). Файл лежит в ките как есть, sha256 закреплён: подменить его незаметно нельзя
LATIN_EXT = os.path.join(KIT, 'fonts', 'montserrat-latin-ext.woff2')
LATIN_EXT_SHA256 = '920711de9ae96c18970fa4faca73cd302b93ac5ed57ebeb6bfec2ddeff930082'
assert hashlib.sha256(open(LATIN_EXT, 'rb').read()).hexdigest() == LATIN_EXT_SHA256, 'gg-id/fonts/montserrat-latin-ext.woff2 changed'
assert 'url(fonts/montserrat-latin-ext.woff2)' in kit_css, 'gg-id.css must load fonts/montserrat-latin-ext.woff2'
inline_css = kit_css
for subset, b64 in woff.items():
    inline_css = inline_css.replace(f'url(fonts/montserrat-{subset}.woff2)', f'url(data:font/woff2;base64,{b64})')
# витрина лежит рядом с gg-id/: latin-ext грузится файлом, только если на странице есть такие знаки (как у хаба)
inline_css = inline_css.replace('url(fonts/montserrat-latin-ext.woff2)', 'url(gg-id/fonts/montserrat-latin-ext.woff2)')

# ---- logo, mark, root favicon ----
logo_paths = re.findall(r'<path d="([^"]+)"', read(HERE, 'global-logo.svg'))
assert len(logo_paths) == 20, len(logo_paths)
LOGO = ''.join(f'<path d="{d}"/>' for d in logo_paths)
LETTERS = ''.join(f'<path d="{d}"/>' for d in logo_paths[:16])  # 0-15 = GLOBAL GENERATION, 16-19 = mark
mark = re.findall(r'<path d="([^"]+)"', read(HERE, 'gg-icon.svg'))
assert len(mark) == 4, len(mark)
ARC, RIGHT_TOP, MAIN, RIGHT_BOTTOM = mark
# иконка GG ID (08.10.2026): белый ключ на светлом градиенте #8FBADD -> #4B8FD6 (--grad-tile), файл assets/favicons/gg-id.svg
# (копия levauth.svg). Значок кнопки «Войти через GG ID», окна «Сессия истекла» и фавикон всех экранов GG ID и витрины.
# Тёмная плитка корня GG (root.svg) в ките больше не стоит: правило 4a, тёмные градиентные плитки в интерфейсе запрещены.
ID_ICON_SVG = read(ROOT, 'assets', 'favicons', 'gg-id.svg').strip()
assert '#8FBADD' in ID_ICON_SVG and '#4B8FD6' in ID_ICON_SVG, 'gg-id.svg: the GG ID icon is the key on the light tile gradient'
_id_inner = re.sub(r'^<svg[^>]*>|</svg>$', '', ID_ICON_SVG).strip()


def id_icon_inner(prefix):
    """The icon body with ids unique per copy, so it can sit next to other inline SVGs (and next to its own alias)."""
    return _id_inner.replace('id="sg"', f'id="{prefix}-g"').replace('url(#sg)', f'url(#{prefix}-g)')


# inline variant for services (their own origin cannot <use> the hub sprite): one <svg>, no sprite needed
ID_ICON_INLINE = (f'<svg class="gid-sso-tile" viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
                  f'{id_icon_inner("gid-id-icon-inline")}</svg>')
FAVICON_URI = 'data:image/svg+xml,' + urllib.parse.quote(ID_ICON_SVG, safe='')

LOCKUP = ('<div class="gid-lockup"><svg class="gid-logo" viewBox="0 0 777 196" role="img" aria-label="Global Generation">'
          '<use href="#gid-logo"/></svg><span class="gid-lockup-name">ID</span></div>')
LOADER = ('<div class="gid-ld" aria-hidden="true"><svg class="gid-ld-mark" viewBox="3.6 8.6 31.3 20.95">'
          f'<path class="gid-ld-arc" d="{ARC}"/><path class="gid-ld-right" d="{RIGHT_TOP} {RIGHT_BOTTOM}"/>'
          f'<path class="gid-ld-main" d="{MAIN}"/></svg><span class="gid-ld-word"><svg viewBox="336 89 444 110">{LETTERS}</svg></span></div>')

# ---- карта GG ID (08.10, «Итог»): светлая, ключ GG ID в печати, без фото и плашки инициалов. Данные вымышленные ----
MONTHS_GEN = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
DEMO = {'name': 'Иван Образцов', 'positions': ['Ментор', 'Продажи'], 'email': 'ivan.obraztsov@global-generations.com',
        'id': 'GG 0042-7F3A', 'since': '2024-03', 'status': 'active', 'passkey': True}
LONG = {'name': 'Александра Образцова-Константинопольская',
        'positions': ['Ментор', 'Руководитель направления «Магистратура в Европе»', 'Ведущая роликов YouTube-канала'],
        'email': 'aleksandra.obraztsova-konstantinopolskaya@global-generations.com', 'id': 'GG 9031-55C0E7', 'since': '2025-09',
        'status': 'active', 'passkey': True}
TPL = {'name': 'Имя Фамилия', 'positions': ['Должность'], 'id': 'GG 0042-7F3A', 'sample': True}   # карта на экране входа до входа
VERIFY = 'https://id.global-generations-edu.com/v/'   # QR карты = адрес проверки: VERIFY + номер через дефис (как в варианте «Итог»)


def verify_url(card_id):
    return VERIFY + '-'.join(card_id.split())


ID_MAX = 14  # номер GG ID: строка до 14 символов, формат решает хаб


def initials(name):
    return ''.join(w[0] for w in name.split()[:2]).upper()


def since_text(v):
    y, m = v.split('-')[:2]
    return f'{MONTHS_GEN[int(m) - 1]} {y}'


KEY_SEAL = ('<span class="gid-idcard-seal" aria-hidden="true"><svg class="gid-idcard-key" viewBox="0 0 64 64" focusable="false">'
            '<use href="#gid-id-icon"/></svg></span>')
HOLO = '<span class="gid-idcard-holo" aria-hidden="true"></span>'


def idcard(d, indent=''):
    """The cabinet card, pretty, with data-gid-field hooks. Inline-sensitive spots (li, email, icon) stay on one line."""
    e = htmlmod.escape
    assert len(d['id']) <= ID_MAX and 0 <= len(d['positions']) <= 3 and d['email'].endswith('@global-generations.com'), d
    local, dom = d['email'].rsplit('@', 1)
    roles = ''.join(f'<li>{e(p)}</li>' for p in d['positions'])
    on = d['status'] == 'active'
    lines = [
        f'<article class="gid-idcard" aria-label="Global Generation ID: {e(d["name"])}">',
        '  ' + HOLO,
        '  <div class="gid-idcard-top">',
        '    ' + LOCKUP,
        '    ' + KEY_SEAL,
        '  </div>',
        '  <div class="gid-idcard-who">',
        f'    <p class="gid-idcard-name" data-gid-field="name">{e(d["name"])}</p>',
        f'    <ul class="gid-idcard-roles" data-gid-field="positions" aria-label="Должности"{"" if roles else " hidden"}>{roles}</ul>',
        f'    <p class="gid-idcard-mail" data-gid-field="email">{re.sub(r"([._-])", r"\1<wbr>", e(local))}<wbr><span>@{e(dom)}</span></p>',
        '    <p class="gid-idcard-meta">'
        f'<span class="gid-idcard-status" data-gid-field="status" data-status="{"active" if on else "disabled"}">{"Активен" if on else "Отключён"}</span>'
        '<span class="gid-idcard-passkey" data-gid-field="passkey"' + ('' if d['passkey'] else ' hidden') +
        '><svg class="gid-ic" aria-hidden="true"><use href="#gi-scan-face"/></svg>Face ID подключён</span></p>',
        '  </div>',
        '  <div class="gid-idcard-facts">',
        f'    <dl class="gid-idcard-fact"><dt>Номер GG ID</dt><dd class="gid-idcard-num" data-gid-field="id">{e(d["id"])}</dd></dl>',
        f'    <dl class="gid-idcard-fact"><dt>В команде с</dt><dd data-gid-field="since">{e(since_text(d["since"]))}</dd></dl>',
        '  </div>',
        '</article>']
    return '\n'.join(indent + ln for ln in lines)


def herocard(d, qr=None):
    """The sign-in hero card: big GG ID, name, position and number bottom left, QR bottom right (gg-id.js draws it).
    The sample card (before sign-in, public pages) encodes the sample number as plain text, no address of the hub;
    a known account («Продолжить как») encodes the verification address."""
    e = htmlmod.escape
    qr = qr or (d['id'] if d.get('sample') else verify_url(d['id']))
    roles = ''.join(f'<li>{e(p)}</li>' for p in d['positions'])
    return ('<article class="gid-idcard gid-idcard--hero">' + HOLO +
            f'<div class="gid-idcard-top">{LOCKUP}{KEY_SEAL}</div><p class="gid-idcard-big">GG ID</p>'
            '<div class="gid-idcard-bot"><div class="gid-idcard-who">'
            f'<p class="gid-idcard-name" data-gid-field="name">{e(d["name"])}</p>'
            f'<ul class="gid-idcard-roles" data-gid-field="positions">{roles}</ul>'
            f'<p class="gid-idcard-num" data-gid-field="id">{e(d["id"])}</p></div>'
            f'<svg class="gid-idcard-qr" data-gid-field="qr" data-gid-qr="{e(qr)}" viewBox="0 0 37 37" role="img" aria-label="QR-код GG ID">'
            '<path fill="#13445d" d=""/></svg></div></article>')


def hero(d=TPL):
    return ('<div class="gid-aside-hero"><div class="gid-hero" aria-hidden="true"><div class="gid-hero-hang">'
            '<div class="gid-hero-lan"><span class="gid-hero-strap"></span><svg class="gid-hero-clip" viewBox="0 0 30 36">'
            '<rect x="4" y="2" width="22" height="16" rx="6"/><rect class="bar" x="11.5" y="14" width="7" height="22" rx="2.5"/></svg></div>'
            f'<div class="gid-hero-holder"><span class="gid-hero-gloss"></span>{herocard(d)}</div></div></div></div>')


# Текст панели (правило 08.10): без списка внутренних сервисов, страницы входа публичные. «GG ID» и «Global Generation» не рвутся (&nbsp;)
ASIDE_COPY = ('<div class="gid-aside-copy"><p class="gid-aside-title">Один вход во все сервисы Global&nbsp;Generation</p>'
              '<p class="gid-aside-sub">Все рабочие сервисы команды открываются с одним GG&nbsp;ID, без отдельного пароля в каждом.</p></div>')
for _svc in ('АКБ', 'Пульс', 'Кабинет ментора', 'Юротдел', 'Продакшн', 'Бухгалтерия', 'Репортер', 'Онбординг'):
    assert _svc not in ASIDE_COPY, f'панель входа публичная: без списка внутренних сервисов ({_svc})'


def aside(d=TPL):
    return '<aside class="gid-aside">' + LOCKUP + hero(d) + ASIDE_COPY + '</aside>'


ASIDE = aside()
FOOT = '<footer class="gid-foot"><span><b>GG ID</b> · единый вход Global Generation</span></footer>'
# экран «Продолжить как»: аккаунт известен, на карте его имя, должности и номер
SIDE_FOR = {'continue': aside({'name': DEMO['name'], 'positions': DEMO['positions'], 'id': DEMO['id']})}


def shell(layout, card_inner, key, side=None):
    return (f'<div class="gid" data-layout="{layout}"><div class="gid-frame">{side or ASIDE}'
            f'<main class="gid-main"><section class="gid-card" data-gid-screen="{key}">{card_inner}</section>{FOOT}</main>'
            '</div></div>')


def idrow(d, status=True):
    """The compact row: initials, name, number (+ status). Same data-gid-field hooks as the card."""
    e = htmlmod.escape
    st = ('<span class="gid-idcard-status" data-gid-field="status" data-status="active">Активен</span>' if status else '')
    return (f'<div class="gid-idrow"><span class="gid-avatar gid-avatar--sm" data-gid-field="initials" aria-hidden="true">{e(initials(d["name"]))}</span>'
            f'<span class="gid-idrow-tx"><b data-gid-field="name">{e(d["name"])}</b>'
            f'<span class="gid-idrow-num" data-gid-field="id">{e(d["id"])}</span></span>{st}</div>')


IDCARD = idcard(DEMO)


# ---- screens ----
src = read(HERE, 'gg_id', 'screens.html')
SCREENS = []
for attrs, body in re.findall(r'<template ([^>]*)>(.*?)</template>', src, flags=re.S):
    a = dict(re.findall(r'(data-[a-z]+)="([^"]*)"', attrs))
    body = body.strip().replace('@LOADER@', LOADER).replace('@IDCARD@', idcard(DEMO, '  ').lstrip())
    SCREENS.append({'key': a['data-key'], 'tab': a['data-tab'], 'title': a['data-title'],
                    'lockup': a.get('data-lockup') != 'off', 'path': a.get('data-path', ''), 'body': body})
KEYS = [s['key'] for s in SCREENS]
assert len(KEYS) == len(set(KEYS)), KEYS
for s in SCREENS:
    for target in re.findall(r'data-go(?:-submit|-complete)?="([a-z]+)"', s['body']):
        assert target in KEYS, f'{s["key"]}: data-go to unknown screen {target}'

# when each screen shows and what it calls on the hub (levauth, Lambda gg-portal-auth)
INFO = {
    'login': ('Первый экран. Главная кнопка Face ID, если на устройстве есть ключ входа; если нет, сразу экран пароля. '
              'Touch ID, Windows Hello и «отпечаток» в подписи только после входа своим ключом в этом браузере.',
              'GET /api/auth/capabilities, GGPasskey.enabled(), GGPasskey.login()'),
    'password': ('Почта и пароль. После входа без ключа на устройстве предлагаем подключить Face ID.', 'POST /api/auth/login'),
    'error': ('401: неверная почта или пароль, поля трясутся, пароль очищается. 429: «Слишком много попыток, подождите минуту». Сеть: «Сеть недоступна».',
              'POST /api/auth/login: 401, 429'),
    'passkey': ('Открыто окно браузера (на телефоне системное). Кнопка занята, второй запрос не уходит, подсказка по тому, что браузер уже видел: '
                'свой ключ, телефон по QR-коду или ничего. Отмена в окне возвращает на первый экран без ошибки.',
                'GGPasskey.login()'),
    'done': ('Вход выполнен, идёт переход в сервис. Фирменная сборка знака, как прелоудер бренда.', 'GET /api/auth/me, переход на next'),
    'continue': ('Сессия GG ID на устройстве уже есть, сервис просит подтвердить аккаунт.', 'GET /api/auth/authorize'),
    'enroll': ('После входа по паролю, если ключа на этом устройстве нет, и после входа с телефона, если своего ключа в этом браузере нет. '
               'Показывать после GGPasskey.platformAvailable(): способ устройства здесь назван, потому что ключ создаётся на нём. '
               'Совет: после «Не сейчас» не спрашивать на этом устройстве неделю.',
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
    'card': ('Карточка сотрудника, как студенческий ID: вверху кабинета «Мои сервисы», на первом входе после приглашения '
             '(онбординг) и образцом в инструкции «Как войти». В письме-приглашении её копия gg-id/email-card.html.',
             'GET /api/auth/me: display_name, email (уже есть); positions, gg_id, since, status (добавить); GGPasskey.list()'),
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
        parts.append(f'<symbol id="gi-{n}" viewBox="0 0 24 24">{icon_inner(n)}</symbol>')
    if '#gid-logo' in text:
        parts.append(f'<symbol id="gid-logo" viewBox="0 0 777 196">{LOGO}</symbol>')
    if '#gid-id-icon' in text:
        parts.append(f'<symbol id="gid-id-icon" viewBox="0 0 64 64">{id_icon_inner("gid-id-icon")}</symbol>')
    if '#gid-tile' in text:   # старое имя: та же иконка GG ID, чтобы старая разметка <use href="#gid-tile"> показала ключ
        parts.append(f'<symbol id="gid-tile" viewBox="0 0 64 64">{id_icon_inner("gid-tile")}</symbol>')
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
    ext = [u for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', text)    # хаб GG ID (id.*, старый адрес levauth пока алиас)
           if u != 'https://mail.google.com/' and not u.startswith(('https://id.global-generations-edu.com/', 'https://levauth.global-generations-edu.com/'))]
    if ext:
        problems.append(f'external resources: {ext}')
    if problems:
        print('BRAND CHECK FAILED in', name)
        for p in problems:
            print(' -', p)
        sys.exit(1)


DARK_TILE = ('#1F3053', '#3D6488', 'paint0_radial_184_3', 'favicons/root.', 'ico/root.')


def kit_rules_check(name, text):
    """Rule 4a (08.10.2026): no dark gradient tiles in the kit UI; the GG ID icon (key on the light tile) wherever a tile stands."""
    problems = [f'dark tile of the GG root (rule 4a): {bad}' for bad in DARK_TILE if bad.lower() in text.lower()]
    if 'href="#gid-tile"' in text:
        problems.append('#gid-tile is the old name of the GG ID icon: use #gid-id-icon')
    for m in re.finditer(r'<a class="gid-sso[^"]*"[^>]*>(.*?)</a>', text, flags=re.S):
        if 'gid-id-icon' not in m.group(1):
            problems.append(f'.gid-sso without the GG ID icon: {m.group(0)[:90]}')
    if problems:
        print('KIT RULES FAILED in', name)
        for p in problems:
            print(' -', p)
        sys.exit(1)


# any space between the words (a plain one, &nbsp;, U+00A0) and TouchID count too; the same pattern lives in src/check_gg_id_passkey.py (BANNED), the check compares them
DEVICE_WORDS = re.compile(r'(?<![a-z])(?:Touch\s*ID|Windows\s*Hello)(?![a-z])|отпечат|палец|пальц', re.I)


def passkey_words_check(name, text):
    """Rule 09.10.2026 (HANDOFF-AUTH.md, 6.1): the markup of a screen never names the method of the device. gg-id.js words the buttons, icons and the hint
    from what this browser has seen work; in the markup stays Face ID, which is true on every device (the phone does it by QR code).
    The words are looked for in what a person reads: entities decoded (Touch&nbsp;ID), soft hyphens and zero-width characters dropped."""
    shown = re.sub(r'<(script|style)\b.*?</\1>|<!--.*?-->', ' ', text, flags=re.S)
    shown = re.sub('[\u00ad\u200b-\u200d\u2060\ufeff]', '', htmlmod.unescape(shown))
    found = sorted({re.sub(r'\s+', ' ', m).lower() for m in DEVICE_WORDS.findall(shown)})
    if found:
        print('PASSKEY WORDS FAILED in', name)
        print(' - the method of the device is named in the markup (Touch ID, Windows Hello, fingerprint) although it is guessed from the kind of device:', found)
        print('   write Face ID (data-gid-passkey) and let gg-id.js word it from the memory of the browser')
        sys.exit(1)


brand_check('gg-id.css', kit_css)
brand_check('gg-id.js', kit_js)
brand_check('gg-id-service.js', service_js)

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
    page_body = shell('split', card, s['key'], SIDE_FOR.get(s['key']))
    page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#13445d" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#081b26" media="(prefers-color-scheme: dark)">
<title>{htmlmod.escape(s['title'])} · GG ID</title>
<link rel="icon" href="../../assets/favicons/gg-id.svg" type="image/svg+xml">
<link rel="icon" href="../../assets/favicons/ico/gg-id.ico" sizes="any">
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
    kit_rules_check(f'screens/{s["key"]}.html', page)
    passkey_words_check(f'screens/{s["key"]}.html', page)
    write_if_changed(os.path.join(KIT, 'screens', s['key'] + '.html'), page)

# full sprite for the hub: every symbol any screen or service component uses (<use href="/assets/gg-id/sprite.svg#gi-eye">)
all_text = (''.join(s['body'] for s in SCREENS) + LOCKUP + IDCARD + idrow(DEMO) + read(HERE, 'gg_id', 'showcase.html') +
            ' data-gid-passkey-icon #gid-id-icon #gid-tile ')   # gid-tile = старое имя иконки GG ID, для старой разметки
full = sprite(all_text).replace('<svg width="0" height="0" style="position:absolute" aria-hidden="true">',
                                '<svg xmlns="http://www.w3.org/2000/svg">', 1)
full = '<!-- GG ID: logo, root favicon tile and kit icons. Generated by src/build_gg_id.py -->\n' + full + '\n'
brand_check('gg-id/sprite.svg', full)
kit_rules_check('gg-id/sprite.svg', full)
write_if_changed(os.path.join(KIT, 'sprite.svg'), full)
# иконка GG ID отдельным файлом в ките: хаб отдаёт её из /assets/gg-id/ (img, презентации), источник assets/favicons/gg-id.svg
write_if_changed(os.path.join(KIT, 'gg-id-icon.svg'), ID_ICON_SVG + '\n')

# drop screens that no longer exist in the source
for fn in os.listdir(os.path.join(KIT, 'screens')):
    if fn.endswith('.html') and fn[:-5] not in KEYS:
        os.remove(os.path.join(KIT, 'screens', fn))

# ---- карточка GG ID и кнопки письма: gg-id/email-card.html (правится руками, стиль «Итог», как письмо Infra-AWS #93) ----
# логотип письма: gg-id/email/gg-logo-navy-2x.png (src/rasterize_gg_id_email.py), хаб отдаёт его из /assets/gg-id/email/
EMAIL_PATH = os.path.join(KIT, 'email-card.html')
EMAIL_PNG = os.path.join(KIT, 'email', 'gg-logo-navy-2x.png')
EMAIL_PNG_URL = 'https://id.global-generations-edu.com/assets/gg-id/email/gg-logo-navy-2x.png'
EMAIL_FIELDS = ('name', 'positions', 'email', 'id')            # карта
EMAIL_ACTION_FIELDS = ('link', 'guide_url')                   # кнопка «Задать пароль» и ссылка «Инструкция: как войти»
GUIDE_URL = 'https://id.global-generations-edu.com/instructions/'
email_html = read(EMAIL_PATH)
brand_check('gg-id/email-card.html', email_html)


def email_problems(text):
    """What would break the card in mail clients (Gmail drops SVG, data: images, flex; Outlook drops rgba and variables)."""
    problems = []
    m = re.search(r'<!-- gg-id-card:start -->(.*?)<!-- gg-id-card:end -->', text, flags=re.S)
    a = re.search(r'<!-- gg-id-actions:start -->(.*?)<!-- gg-id-actions:end -->', text, flags=re.S)
    if not m or not a:
        return ['no <!-- gg-id-card:start/end --> or <!-- gg-id-actions:start/end --> block']
    block, actions = m.group(1), a.group(1)
    for part, want, label in ((block, EMAIL_FIELDS, 'card'), (actions, EMAIL_ACTION_FIELDS, 'actions')):
        found = set(re.findall(r'\{\{([a-z_]+)\}\}', part))
        if found != set(want):
            problems.append(f'{label}: placeholders {sorted(found)}, expected {sorted(want)}')
    for bad, why in [('<link', 'external stylesheet'), ('@import', '@import'), ('@font-face', 'web font'), ('<script', 'script'),
                     ('<svg', 'inline SVG (Gmail drops it)'), ('data:', 'data: URI (Gmail blocks it)'), ('display:flex', 'flex'),
                     ('display:grid', 'grid'), ('position:', 'position'), ('var(--', 'CSS variables'), ('class="gid-', 'kit classes')]:
        if bad in text:
            problems.append(f'{why}: {bad}')
    for part, label in ((block, 'card'), (actions, 'actions')):
        if 'rgba(' in part:
            problems.append(f'rgba() inside the {label} (Outlook): use solid colours')
        texts = re.findall(r'<(td|div|a)\b([^>]*)>([^<]+)<', part)
        bare = [t[2].strip() for t in texts if t[2].strip() and 'font-family:' not in t[1] and t[0] != 'a']
        if bare:
            problems.append(f'{label}: text without an inline font-family: {bare[:4]}')
    for img in re.findall(r'<img [^>]*>', block):
        if not re.search(r'src="https://[^"]+"', img) or not all(f'{x}="' in img for x in ('alt', 'width', 'height')):
            problems.append(f'img needs https src, alt, width, height: {img[:90]}')
    if EMAIL_PNG_URL not in block:
        problems.append(f'the logo image is not {EMAIL_PNG_URL}')
    for want in ('Задать пароль', 'Инструкция: как войти', 'Войти через GG&nbsp;ID', 'border:1px solid #c9d5e1'):
        if want not in actions:
            problems.append(f'actions: no {want!r} (white button with the thin border, text link, «Войти через GG ID»)')
    if 'Номер GG ID' not in block or 'Активен' not in block:
        problems.append('card: the number «Номер GG ID» and the status «Активен» are part of the card')
    png = open(EMAIL_PNG, 'rb').read()
    pw, ph = int.from_bytes(png[16:20], 'big'), int.from_bytes(png[20:24], 'big')
    tag = re.search(r'<img [^>]*' + re.escape(EMAIL_PNG_URL) + r'[^>]*>', block)
    if tag:
        w, h = int(re.search(r'width="(\d+)"', tag.group(0)).group(1)), int(re.search(r'height="(\d+)"', tag.group(0)).group(1))
        if pw < 2 * w or ph < 2 * h or abs(pw / ph - w / h) > 0.05:
            problems.append(f'logo PNG is {pw}x{ph}, the tag says {w}x{h} (expected at least 2x, same proportions)')
    return problems


bad_mail = email_problems(email_html)
if bad_mail:
    print('EMAIL CHECK FAILED in gg-id/email-card.html')
    for p in bad_mail:
        print(' -', p)
    sys.exit(1)


def email_filled(d, logo_src=EMAIL_PNG_URL):
    """The e-mail card and buttons with the values of d, every value HTML-escaped, the way the hub fills it."""
    vals = {'name': d['name'], 'positions': ' · '.join(d['positions']), 'email': d['email'], 'id': d['id'],
            'link': 'https://id.global-generations-edu.com/set-password.html#token=demo&invite=1', 'guide_url': GUIDE_URL}
    out = re.sub(r'\{\{([a-z_]+)\}\}', lambda mm: htmlmod.escape(vals[mm.group(1)], quote=True), email_html)
    return out.replace(EMAIL_PNG_URL, logo_src)


EMAIL_PNG_URI = 'data:image/png;base64,' + base64.b64encode(open(EMAIL_PNG, 'rb').read()).decode()

# ---- showcase: gg-id.html (one self-contained file) ----
tpl = read(HERE, 'gg_id', 'showcase.html')
templates = ['<template id="tpl-lockup">' + LOCKUP + '</template>',
             '<template id="tpl-shell">' + shell('split', '', '') + '</template>']
templates += [f'<template id="scr-{s["key"]}">{s["body"]}</template>' for s in SCREENS]
templates = '\n'.join(templates)
meta = [{'key': s['key'], 'tab': s['tab'], 'title': s['title'], 'lockup': s['lockup'], 'path': s['path'],
         'when': INFO[s['key']][0], 'api': INFO[s['key']][1]} for s in SCREENS]
api_rows = ''.join(
    f'<tr><td><b>{htmlmod.escape(m["tab"])}</b><span>screens/{m["key"]}.html</span></td><td>{htmlmod.escape(m["when"])}</td>'
    f'<td><code>{htmlmod.escape(m["api"]).replace("/", "/<wbr>").replace(", ", ",<br>")}</code></td></tr>' for m in meta)
page = (tpl
        .replace('/*@GID_CSS@*/', inline_css)
        .replace('/*@GID_JS@*/', kit_js.replace('</script', '<\\/script'))
        .replace('/*@GID_SERVICE_JS@*/', service_js.replace('</script', '<\\/script'))
        .replace('/*@META@*/', json.dumps(meta, ensure_ascii=False).replace('</', '<\\/'))
        .replace('/*@HERO_DEMO@*/', json.dumps({'name': DEMO['name'], 'positions': DEMO['positions'], 'id': DEMO['id'], 'qr': verify_url(DEMO['id'])}, ensure_ascii=False))
        .replace('<!--@TEMPLATES@-->', templates)
        .replace('<!--@API_ROWS@-->', api_rows)
        .replace('@LOCKUP@', LOCKUP)
        .replace('@FAVICON_URI@', FAVICON_URI)
        .replace('@IDCARD@', idcard(DEMO, '        '))
        .replace('@IDCARD_LONG@', idcard(LONG, '        '))
        .replace('@IDROW@', idrow(DEMO))
        .replace('@EMAIL_SRCDOC@', htmlmod.escape(email_filled(DEMO, EMAIL_PNG_URI), quote=True))
        .replace('@N_LOGIN@', str(len([s for s in SCREENS if s['key'] != 'card'])))
        .replace('@N_SCREENS@', str(len(SCREENS))))
page = page.replace('<!--@SPRITE@-->', sprite(page))
brand_check('gg-id.html', page)
kit_rules_check('gg-id.html', page)
write_if_changed(os.path.join(ROOT, 'gg-id.html'), page)

# ---- gg-id/README.md: the screens table between markers, from the same INFO ----
readme_path = os.path.join(KIT, 'README.md')
readme = read(readme_path)
table = ['## Экраны', '', '| Экран | Файл | Когда | Хаб |', '|---|---|---|---|']
table += [f'| {m["tab"]} | `screens/{m["key"]}.html` | {m["when"]} | `{m["api"]}` |' for m in meta]
readme = re.sub(r'<!-- screens:start -->.*?<!-- screens:end -->',
                lambda _: '<!-- screens:start -->\n' + '\n'.join(table) + '\n<!-- screens:end -->', readme, flags=re.S)
# the card markup in the README is the same string the screens and the showcase use
card_md = '```html\n' + IDCARD + '\n\n<!-- компактная строка -->\n' + idrow(DEMO) + '\n```'
assert '<!-- idcard:start -->' in readme, 'gg-id/README.md: add <!-- idcard:start --><!-- idcard:end --> markers'
icon_md = '```html\n<!-- кнопка в сервисе (свой origin): иконка инлайном, спрайт хаба не нужен -->\n' + \
    '<a class="gid-sso" href="https://id.global-generations-edu.com/api/auth/authorize?...">' + ID_ICON_INLINE + \
    '<span>Войти через GG&nbsp;ID</span></a>\n\n<!-- на хабе (тот же origin): символ спрайта -->\n' + \
    '<svg class="gid-sso-tile" viewBox="0 0 64 64" aria-hidden="true"><use href="/assets/gg-id/sprite.svg#gid-id-icon"/></svg>\n```'
assert '<!-- idicon:start -->' in readme, 'gg-id/README.md: add <!-- idicon:start --><!-- idicon:end --> markers'
readme = re.sub(r'<!-- idicon:start -->.*?<!-- idicon:end -->',
                lambda _: '<!-- idicon:start -->\n' + icon_md + '\n<!-- idicon:end -->', readme, flags=re.S)
readme = re.sub(r'<!-- idcard:start -->.*?<!-- idcard:end -->',
                lambda _: '<!-- idcard:start -->\n' + card_md + '\n<!-- idcard:end -->', readme, flags=re.S)
brand_check('gg-id/README.md', readme)
kit_rules_check('gg-id/README.md', readme)
write_if_changed(readme_path, readme)
print('ok gg-id.html', f'{len(page) / 1024:.0f} KB', '| screens:', len(SCREENS), '| fonts:', ', '.join(sorted(woff) + ['latin-ext']), '| version:', KIT_VERSION)
