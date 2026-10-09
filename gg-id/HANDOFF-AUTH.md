# Хэндов: дизайн GG ID → AUTH-агенту

Кому: агент, который ведёт вход GG (хаб GG ID `https://id.global-generations-edu.com`, старый адрес `levauth.global-generations-edu.com` пока алиас; Lambda `gg-portal-auth`, sso-gate, SSO сервисов).
От кого: агент дизайна GG ID (сессия «gg-id login block»), 08.10.2026.
Статус на 08.10 (вечер): всё из этого хэндова сделано. Кит смержен (Infra-Brand-Identity #21, #24-#27) и доведён QA-правкой «2026-10-08.2» (версия кита = `gg-id/VERSION`, она же `GGID.version` и `GGIDService.version`): видимое кольцо фокуса, «меньше движения» без бесконечных анимаций, карта на панели в низком окне и на телефоне, «Резервный вход», latin-ext шрифт (₽), письмо в стиле «Итог». Хаб на ките (Infra-Services-Portal #140, #145, #149): в хабе `assets/gg-id/VERSION` = полный sha коммита кита, обновлять только `scripts/sync-gg-id.sh <sha>`. 09.10: подписи входа по ключу больше не угадывают устройство по виду браузера (раздел 6.1, кит «2026-10-09.2»); страница входа хаба (Infra-Services-Portal #168) и страница подтверждения Face ID для админов (Infra-AWS #98) уже работают по этому правилу. Ниже исходный план, адреса обновлены на `id.*`.

---

## 0. Коротко

1. Есть готовый дизайн всех экранов входа: **17 экранов**, 3 раскладки, светлая и тёмная тема, компоненты для сервисов. Всё на бренде GG (один логотип, Montserrat самохостом, navy + один голубой акцент).
2. Кит = 4 файла без зависимостей и без сетевых вызовов: `gg-id.css`, `gg-id.js`, `fonts/`, `sprite.svg`. Логику входа (`/api/auth/*`, `GGPasskey`) **не трогаем и не переписываем**, меняем только разметку и вид.
3. В хабе кит кладётся в **`/assets/gg-id/`** (публичный путь). Путь `/gg-id/` уже занят твоими инструкциями (Infra-Services-Portal #128, #129), его не трогаем.
4. Порядок: PR хаба «кит в assets» → `login.html` → `forgot.html` + `set-password.html` + `no-access.html` → sso-gate (PIN, «нет доступа», «недоступен») → кнопка «Войти через GG ID» и аккаунт в сервисах → обновить свою инструкцию `kak-voyti.html` под новый вид.
5. Деплой хаба по-прежнему только после «деплой» от Лёва в его текущем сообщении; nginx и sso-gate выкатывает Лёв своей командой.

---

## 1. Где что лежит

### Репо дизайна: Global-Generation/Infra-Brand-Identity (PR #21)

| Путь | Что | Править руками? |
|---|---|---|
| `gg-id/gg-id.css` | токены (светлая и тёмная), раскладки `split` / `card` / `minimal`, все компоненты | да, источник |
| `gg-id/gg-id.js` | поведение: глаз пароля, только рабочая почта, правила пароля, ячейки кода, отсчёт, подписи входа по ключу по памяти браузера (раздел 6.1), `GGID.busy/error/shake` | да, источник |
| `gg-id/fonts/montserrat-{cyrillic,latin}.woff2` | переменный Montserrat 400-700 | нет, генерируется из `src/fonts.css` |
| `gg-id/sprite.svg` | все символы: логотип `gid-logo`, иконка GG ID `gid-id-icon` (`gid-tile` = её старое имя), иконки `gi-*` | нет, генерируется |
| `gg-id/gg-id-service.js` | поведение компонентов в сервисах: меню аккаунта, окно «Сессия истекла», перехват 401 (README, «Поведение в сервисе») | да, источник |
| `gg-id/screens/*.html` | 17 эталонных страниц, открываются как есть | нет, генерируются |
| `gg-id/README.md` | справочник кита: каркас, атрибуты, таблица экранов → API | да (таблица между маркерами генерируется) |
| `gg-id/HANDOFF-AUTH.md` | этот файл | да |
| `gg-id.html` | витрина: все экраны, переключатели, компоненты, правила | нет, генерируется |
| `src/gg_id/screens.html` | тексты и разметка экранов (источник для screens и витрины) | да |
| `src/gg_id/showcase.html` | шаблон витрины | да |
| `src/build_gg_id.py` | сборка + бренд-ассерты (тире, фиолетовый, CDN, эмодзи) | да |
| `src/check_gg_id.py` | Playwright: все экраны x 3 раскладки x 2 темы x 1440/390 px + витрина | да |
| `src/check_gg_id_passkey.py` | Playwright: подписи входа по ключу и память браузера (раздел 6.1), 7 устройств x 8 состояний x 3 экрана, настоящий WebAuthn Chromium; идёт и из `check_gg_id.py` | да |

Локальный клон: `~/Global-Generation/Infra-Brand-Identity`, мой worktree `.claude/worktrees/gg-id-auth`. Копия витрины: `~/Desktop/GG-ID-2026-10-08/gg-id.html` (в той же папке лежат твои `index.html`, `kak-eto-ustroeno.html`, `kak-voyti.html`, я их не трогал).

Ссылка на любое состояние витрины: `gg-id.html#s=<экран>&l=<split|card|minimal>&t=<light|dark>&d=<desktop|phone|all>`. Эталон в другой раскладке: `gg-id/screens/login.html?layout=card&theme=dark`.

### Пересобрать и проверить

```
cd ~/Global-Generation/Infra-Brand-Identity          # или worktree
python3 src/build_gg_id.py                           # gg-id.html, screens, fonts, sprite, таблица в README
uv run --with playwright python src/check_gg_id.py   # 17 x 3 x 2 x 2 = 204 рендера: прокрутка, вылезания, шрифт, консоль, тире
uv run --with playwright python src/check_gg_id_passkey.py   # только подписи входа по ключу (раздел 6.1), около 15 секунд; полный прогон его тоже включает
```

Последний прогон 08.10: всё зелёное, 204 рендера, витрина кликается (пароль → «Подключить Face ID» и т.д.).

---

## 2. Что я учёл в хабе (факты на main Infra-Services-Portal, 08.10)

- **Публично без входа** (`nginx/levauth.conf`, блок «Публично»): `/login.html` (no-cache), `/forgot.html` (no-cache), `/set-password.html` (`access_log off`, `no-store`, `Referrer-Policy: no-referrer`), `/no-access.html` (no-store, отдаётся как `error_page 403`), `/assets/` (`try_files $uri =404`). Значит `/assets/gg-id/*` сразу доступен экрану входа, правка nginx **не нужна**.
- **Заголовки**: только `X-Robots-Tag noindex`, `X-Frame-Options: DENY`, `nosniff`. **CSP нет**: встроенные `<script>`, `<style>` и `data:` в CSS (галочка правил пароля) работают. Если когда-нибудь появится CSP, киту нужно: `style-src 'self'`, `img-src 'self' data:`, `font-src 'self'`, `script-src 'self'` (кит не требует inline, если страница тоже без inline).
- **Шрифты**: `gg-id/fonts/*.woff2` **байт в байт** те же, что `/assets/montserrat-cyrillic.woff2` и `/assets/montserrat-latin.woff2` (md5 `45ea393f…`, `c154477b…`). Можно копировать кит как есть (проще синхронизировать), браузер скачает лишние 57 КБ один раз.
- **Passkey**: `/assets/passkey.js` → `window.GGPasskey = { supported, platformAvailable(), register(), login(), enabled(), list(), remove(id) }`, сервер `/api/auth/passkey/*`. Кит его не заменяет и не вызывает; `GGID.passkeyWatch()` только читает `authenticatorAttachment` из ответов браузера (раздел 6.1).
- **Твои открытые PR в хабе**: #128 (`/gg-id/` инструкции, только admin), #129 (`location /gg-id/` с SAMEORIGIN), #120 (sso-gate волна 2). Мой кит с ними не пересекается: другой путь (`/assets/gg-id/`), другие файлы.
- Название: у тебя «Global Generation ID», у меня подпись у логотипа «GLOBAL GENERATION | ID» и в текстах «GG ID». Читается одинаково, менять не нужно.

---

## 3. План интеграции по PR

### PR 1. Хаб: кит в `assets/gg-id/` (только файлы, страницы не меняются)

1. Скопировать из Infra-Brand-Identity (после мержа #21: с main, до мержа: с ветки `feat/gg-id-auth`) в Infra-Services-Portal:
   ```
   assets/gg-id/gg-id.css
   assets/gg-id/gg-id.js
   assets/gg-id/sprite.svg
   assets/gg-id/fonts/montserrat-cyrillic.woff2
   assets/gg-id/fonts/montserrat-latin.woff2
   assets/gg-id/VERSION          # одна строка: sha коммита Infra-Brand-Identity, с которого скопировано
   ```
2. Предлагаю скрипт `scripts/sync-gg-id.sh <sha>`: берёт 5 файлов через `gh api repos/Global-Generation/Infra-Brand-Identity/contents/gg-id/...?ref=<sha>`, пишет `VERSION`, показывает diff. Руками файлы кита в хабе не править: правка вида = PR в Infra-Brand-Identity → sync.
3. Тест (по образцу твоего `tests/test_gg_id_docs.py`): файлы на месте, `VERSION` = 40 hex, в CSS/JS нет длинного тире и внешних URL, `url(fonts/...)` указывает на существующие файлы, в `sprite.svg` есть `gid-logo` и все `gi-*`, на которые ссылаются страницы хаба.
4. `scripts/deploy.sh`: `assets/` уже в выкатке (проверь, что подпапки тоже едут), `deploy.yml` `paths` уже ловит `assets/**`? Если нет, добавить.
5. Риск нулевой: ни одна страница ещё не подключает кит.

### PR 2. Хаб: `login.html` на ките

Одна страница с видами (`data-view`), логика 1-в-1 из текущего `login.html`, меняется только разметка. Подробно в разделе 4.1, готовый эскиз кода там же.

### PR 3. Хаб: `forgot.html`, `set-password.html`, `no-access.html`

Разделы 4.2-4.4. Тот же каркас, свои виды.

### PR 4. sso-gate: PIN, «нет доступа», «выбор входа», «недоступен», ошибки

Раздел 4.5. Это другие хосты (не хаб GG ID), поэтому кит там встраивается иначе.

### PR 5+. Сервисы: кнопка «Войти через GG ID», аккаунт, «сессия истекла»

Раздел 5. По одному PR на сервис, начиная с тех, где SSO уже заведён и выключен флагом (АКБ #287, Кабинет ментора #20/#21, Консультации #100/#101, Production #34, Notetaker/Merch/Italy SSO).

### PR последний. Твоя инструкция `kak-voyti.html`

После выкатки нового входа перерисовать в ней скриншоты и тексты кнопок («Войти с Face ID», «Войти по паролю»), иначе инструкция будет показывать старый экран.

---

## 4. Страница за страницей

### Общий каркас страницы хаба

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#13445d" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#081b26" media="(prefers-color-scheme: dark)">
<title>Вход · GG ID</title>
<link rel="icon" href="/assets/favicons/gg-id.svg" type="image/svg+xml">   <!-- иконка GG ID: ключ на светлом градиенте (тот же, что levauth.svg) -->
<link rel="stylesheet" href="/assets/gg-id/gg-id.css">
</head>
<body class="gid-body">
<div class="gid" data-layout="split">          <!-- split | card | minimal, решение Лёва (раздел 8). Тема по системе, data-theme не ставить -->
  <div class="gid-frame">
    <aside class="gid-aside">...</aside>        <!-- только split: скопировать целиком из gg-id/screens/login.html -->
    <main class="gid-main">
      <section class="gid-card" id="card">
        <div class="gid-lockup">
          <svg class="gid-logo" viewBox="0 0 777 196" role="img" aria-label="Global Generation"><use href="/assets/gg-id/sprite.svg#gid-logo"/></svg>
          <span class="gid-lockup-name">ID</span>
        </div>
        <!-- виды экрана: <div data-view="..." hidden>...</div> -->
      </section>
      <footer class="gid-foot"><span><b>GG ID</b> · единый вход Global Generation</span></footer>
    </main>
  </div>
</div>
<script src="/assets/passkey.js"></script>
<script src="/assets/gg-id/gg-id.js"></script>
<script>/* логика страницы */</script>
</body>
</html>
```

- Иконки: `<svg class="gid-ic" aria-hidden="true"><use href="/assets/gg-id/sprite.svg#gi-eye"/></svg>`. Внешний спрайт работает только с того же origin, на хабе GG ID это так. Иконку GG ID (`gid-id-icon`, в ней градиент) в сервисах надёжнее вставлять инлайн: готовый SVG в README кита, раздел «Иконка GG ID».
- Разметку каждого вида брать из `gg-id/screens/<экран>.html` (внутри `<section class="gid-card">`), убрать `data-go` (это демо-переходы) и `href="<экран>.html"`.
- `gg-id.js` сам вызывает `GGID.init(document)` на загрузке. Если вид появляется позже или в нём меняется разметка, вызвать `GGID.init(узел)` ещё раз (повторно уже обработанные элементы не трогаются).
- Показ видов: атрибут `hidden` (кит его не переопределяет). Скрытые виды не фокусируются.

### 4.1 `login.html` (экраны `login`, `password`, `error`, `passkey`, `enroll`, `done`, опционально `continue`)

**Инварианты текущего login.html, которые обязаны сохраниться** (всё это уже работает на проде):

1. `next` из `?next=`, разбор через `new URL(r, location.origin)`, только тот же origin, не `/login.html*`, уходим на `pathname + search + hash`, иначе `/`.
2. `land(me)`: если `next === '/'` и `me.level === 'services'`, то `/cabinet/`, иначе `next`. `location.replace`, не `href`.
3. `go()` после успешного входа ждёт `/api/auth/me` и возвращает **незавершающийся** Promise: кнопки остаются занятыми, второй вход и второй Face ID не запускаются.
4. `mobile = next.indexOf('/m/') === 0` уходит в теле `POST /api/auth/login` (сессия 12 ч для `/m/`).
5. На загрузке: `GET /api/auth/me`, если жива кука, сразу `land(me)`.
6. `GET /api/auth/capabilities`: `password_reset === true` показывает «Забыли пароль?». Ссылки «Войти через Aura» на экранах GG ID нет (решение Лёва 08.10: Aura и GG раздельно), `aura_login` экраны входа не читают.
7. Face ID доступен, только если `GGPasskey.supported` и `platformAvailable()` и `enabled().enabled`.
8. `NotAllowedError` от `GGPasskey.login()` (человек закрыл системное окно) = тихо вернуть вид, **без** текста ошибки. Любая другая ошибка = «Face ID не сработал, войдите по паролю» и вид пароля.
9. Резервный вход (вход Лёва на крайний случай, прежний «супер-админ»): тот же `POST /api/auth/login` с `email: 'superadmin'`, поле почты скрыто. На публичной странице слова «супер-админ» нет: под формой пароля свёрнутый блок кита `details.gid-fb` с подписью «Резервный вход» (`summary.gid-link.gid-link--muted.gid-link--sm` и стрелка), раскрыт = резервный вход (`form.classList.toggle('sa')`, почту прятать, подзаголовок «Резервный вход. Введите пароль.»), свёрнут = обычный. Раскрывается мышью и с клавиатуры.
10. Ошибки: 401 = «Неверная почта или пароль. Проверьте раскладку и Caps Lock.» (для супер-админа «Неверный пароль»), 429 = «Слишком много попыток, подождите минуту», сеть = «Сеть недоступна», прочее = «Не получилось войти (ошибка N). Попробуйте ещё раз». Пароль очистить, фокус в пароль.

**Виды и что показывать первым**

| Условие | Вид |
|---|---|
| ждём ответ `platformAvailable` + `enabled` (обычно < 200 мс) | только подпись, заголовок и подзаголовок, кнопок нет (не мигать формой) |
| Face ID готов | `login`: главная кнопка Face ID, вторая «Войти по паролю» |
| Face ID не готов | сразу `password`, кнопка «Войти с Face ID» под «или» скрыта |
| нажали Face ID | `passkey`: та же кнопка `is-busy` + `.gid-scan` + текст `GGID.passkeyText('wait')`, подсказка `GGID.passkeyHint()`, ссылка «Отменить» |
| 401/429/сеть на пароле | `password` + `[data-gid-error]` (это экран `error` витрины, отдельный вид не нужен) |
| вошёл по паролю, устройство умеет passkey, ключа тут нет, не отказывался последние 7 дней | `enroll` |
| вошёл с телефона (`cross-platform`), устройство умеет свой ключ, своего ключа в этом браузере нет, не отказывался последние 7 дней | `enroll` с текстом «Добавить вход по Touch ID на этом устройстве?» (раздел 6.1) |
| вошёл | `done` (сборка знака, «Открываем <сервис>»), сразу `land()` |

**Разметка видов** (внутри `<section class="gid-card" id="card">` после подписи; тексты и классы из `gg-id/screens/{login,password,enroll,done}.html`, здесь только каркас и id, на которые опирается код ниже):

```html
<h1 class="gid-h">Вход в <span id="svc">хаб команды</span></h1>

<div data-view="login" hidden>
  <p class="gid-sub" id="pkSub">Один вход GG ID открывает все сервисы команды Global Generation.</p>
  <div class="gid-stack">
    <button class="gid-btn gid-btn--primary" type="button" id="pkBtn">
      <span id="pkScan"><svg class="gid-ic" aria-hidden="true" data-gid-passkey-icon><use href="/assets/gg-id/sprite.svg#gi-scan-face"/></svg></span>
      <span id="pkText" data-gid-passkey="login">Войти с Face ID</span>
    </button>
    <button class="gid-btn gid-btn--secondary" type="button" id="pwBtn"><svg class="gid-ic" aria-hidden="true"><use href="/assets/gg-id/sprite.svg#gi-key-round"/></svg><span>Войти по паролю</span></button>
  </div>
</div>

<div data-view="password">                       <!-- без hidden: если JS не загрузился, вход по паролю всё равно виден -->
  <p class="gid-sub">Рабочая почта и пароль GG ID.</p>
  <form class="gid-form" id="form" novalidate>
    <div class="gid-field">... <input class="gid-input" id="email" type="email" autocomplete="username" data-gid-domain="global-generations.com"> ...</div>
    <div class="gid-field">
      <div class="gid-label-row"><label class="gid-label" for="password">Пароль</label><a class="gid-link gid-link--sm" id="forgot" href="/forgot.html" hidden>Забыли пароль?</a></div>
      <div class="gid-input-wrap"><input class="gid-input" id="password" type="password" autocomplete="current-password"><button class="gid-eye" type="button" data-gid-eye ...>...</button></div>
    </div>
    <div class="gid-msg gid-msg--error" role="alert" data-gid-error hidden><svg class="gid-ic" ...><use href="/assets/gg-id/sprite.svg#gi-circle-alert"/></svg><span data-gid-error-text></span></div>
    <button class="gid-btn gid-btn--primary" type="submit" id="submit">Войти</button>
  </form>
  <div id="pkAltWrap"><div class="gid-or"><span>или</span></div>
    <button class="gid-btn gid-btn--secondary" type="button" id="pkAlt">...Войти с Face ID</button></div>
  <div class="gid-alt"><details class="gid-fb" id="saBox"><summary class="gid-link gid-link--muted gid-link--sm" id="saToggle"><span>Резервный вход</span><svg class="gid-ic" aria-hidden="true"><use href="/assets/gg-id/sprite.svg#gi-chevron-down"/></svg></summary></details></div>
</div>

<div data-view="enroll" hidden>... id="enrollBtn" (primary), id="enrollSkip" (gid-btn--quiet «Не сейчас») ...</div>
<div data-view="done" hidden>... разметка gg-id/screens/done.html (сборка знака), «Открываем <сервис>» ...</div>
```

**Эскиз логики** (проверить на месте, это перенос текущего кода на виды кита):

```js
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var card = $('card');
  GGID.passkeyWatch();                                                            // 6.1: читать, чем браузер подтвердил вход (свой ключ или телефон)
  // 1. next: тот же origin, не /login.html
  var raw = new URLSearchParams(location.search).get('next') || '/';
  var next = (function (r) {
    try { var u = new URL(r, location.origin);
      if (u.origin !== location.origin || u.pathname.indexOf('/login.html') === 0) return '/';
      return u.pathname + u.search + u.hash; } catch (e) { return '/'; }
  })(raw);
  var mobile = next.indexOf('/m/') === 0;
  function view(name) { card.querySelectorAll('[data-view]').forEach(function (v) { v.hidden = v.getAttribute('data-view') !== name; }); }
  function forever() { return new Promise(function () {}); }
  function land(me) { location.replace(next === '/' && me && me.level === 'services' ? '/cabinet/' : next); }
  function me() { return fetch('/api/auth/me', { credentials: 'same-origin', cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }); }
  function go() { view('done'); return me().then(function (m) { land(m); return forever(); }, function () { location.replace(next); return forever(); }); }

  me().then(function (m) { if (m) land(m); }).catch(function () {});           // 5. уже вошёл

  fetch('/api/auth/capabilities', { credentials: 'same-origin', cache: 'no-store' })   // 6
    .then(function (r) { return r.ok ? r.json() : {}; })
    .then(function (j) {
      $('forgot').hidden = !(j && j.password_reset === true);
    }).catch(function () {});

  var faceReady = false, canEnroll = false;                                       // 7
  var pk = window.GGPasskey && GGPasskey.supported
    ? GGPasskey.platformAvailable().then(function (ok) {
        canEnroll = !!ok;
        return ok ? GGPasskey.enabled().then(function (r) { return !!(r && r.enabled); }) : false;
      }).catch(function () { return false; })
    : Promise.resolve(false);
  pk.then(function (ready) { faceReady = ready; canEnroll = canEnroll && ready; $('pkAltWrap').hidden = !ready; view(ready ? 'login' : 'password'); });

  // Face ID
  function waiting(on) {                                                          // экран passkey = тот же вид login, меняется кнопка
    var b = $('pkBtn');
    b.classList.toggle('is-busy', on); b.disabled = on; b.setAttribute('aria-busy', on ? 'true' : 'false');
    $('pkScan').classList.toggle('gid-scan', on);
    $('pkText').textContent = GGID.passkeyText(on ? 'wait' : 'login');
    $('pkSub').textContent = on ? GGID.passkeyHint()                              // 6.1: слово про устройство только при подтверждённом ключе
                                : 'Один вход GG ID открывает все сервисы команды Global Generation.';
  }
  function face() {
    GGID.error(card, '');
    waiting(true);
    GGPasskey.login().then(function () { GGID.passkeyRemember(GGID.passkeySeen()); return go(); }, function (e) {   // 6.1, 8
      waiting(false);
      GGID.passkeyMissed(e);
      if (!(e && e.name === 'NotAllowedError')) { view('password'); GGID.error(card, 'Face ID не сработал, войдите по паролю'); }
    });
  }
  $('pkBtn').addEventListener('click', face);
  $('pkAlt').addEventListener('click', face);
  $('pwBtn').addEventListener('click', function () { view('password'); $('email').focus(); });
  $('saBox').addEventListener('toggle', function () {                            // 9: «Резервный вход» раскрыт = вход без почты
    var on = this.open;
    $('form').classList.toggle('sa', on);
    $('email').closest('.gid-field').hidden = on;
    GGID.error(card, '');
    (on ? $('password') : $('email')).focus();
  });

  // пароль
  var form = $('form'), email = $('email'), password = $('password'), submit = $('submit');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var sa = form.classList.contains('sa');
    GGID.error(card, '');
    GGID.busy(submit, true, 'Входим');
    fetch('/api/auth/login', {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: sa ? 'superadmin' : email.value.trim(), password: password.value, mobile: mobile })   // 4, 9
    }).then(function (r) {
      if (r.ok) return afterPassword();                                           // кнопка остаётся занятой (3)
      var t = r.status === 401 ? (sa ? 'Неверный пароль' : 'Неверная почта или пароль. Проверьте раскладку и Caps Lock.')
            : r.status === 429 ? 'Слишком много попыток, подождите минуту'
            : 'Не получилось войти (ошибка ' + r.status + '). Попробуйте ещё раз';   // 10
      GGID.busy(submit, false);
      GGID.error(card, t, sa ? [password] : [email, password]);
      password.value = ''; password.focus();
    }, function () { GGID.busy(submit, false); GGID.error(card, 'Сеть недоступна'); });
  });

  // предложить Face ID после входа по паролю (после входа с телефона то же предложение, раздел 6.1)
  function afterPassword() {
    var m = GGID.passkeyMemory();
    if (!canEnroll || m.local || m.snoozed) return go();
    view('enroll');
    return forever();
  }
  $('enrollBtn').addEventListener('click', function () {
    GGID.busy($('enrollBtn'), true, GGID.passkeyText('wait'));
    GGPasskey.register().then(function () { GGID.passkeyCreated(); }, function (e) {
      if (e && (e.name === 'InvalidStateError' || e.message === 'already_registered')) GGID.passkeySnooze();   // ключ человека уже стоит (телефон): про это устройство ничего не узнали
    }).then(go);
  });
  $('enrollSkip').addEventListener('click', function () { GGID.passkeySnooze(); go(); });
})();
```

Замечания к эскизу:
- Память про ключ (`localStorage`) ведёт кит, каждое обращение в нём в try/catch (приватный режим Safari может кидать). Своих флагов в странице не заводить: имя `gg-id-pk` из первой версии этого эскиза снято, оно ставилось после любого входа по ключу, в том числе с телефона, и по нему нельзя было отличить свой ключ от чужого.
- Предложение после пароля стоит показывать, только пока у человека нет ни одного рабочего ключа (`GGPasskey.list()`, ключи с `stale: true` не считаются): сервер разрешает первый ключ из сессии по паролю, а второй и дальше только из сессии по Face ID. Живой эталон целиком, с этим и с предложением после входа с телефона: Infra-Services-Portal, `scripts/gg-id-pages/templates/login.tpl.html` (PR #168).
- Экран `continue` («Продолжить как Лёв») нужен, только если `/api/auth/authorize` при живой сессии **не** уводит сразу обратно в сервис. Если уводит, экран не делать.
- На экранах входа только GG: ни шапки «Global Generation × Aura», ни логотипа Aura, ни ссылки «Войти через Aura» (решение Лёва 08.10: GG и Aura раздельно).

**Название сервиса в заголовке** («Вход в АКБ»): страница знает только `next`. Для своих страниц хаба писать «Вход в хаб команды». Для SSO (`next` = `/api/auth/authorize?client_id=...`) нужно человеческое имя клиента: предлагаю, чтобы `GET /api/auth/capabilities?client_id=<id>` возвращал `client_name` из реестра клиентов (или authorize сам добавлял `&client=<slug>`, а страница брала имя из захардкоженной карты). Имя вставлять только через `textContent`. Названия пишем так, чтобы не склонялись: «Вход в АКБ», «Вход в Кабинет ментора», «сервис «Пульс»».

### 4.2 `forgot.html` (экраны `forgot`, `sent`, `resetoff`)

Инварианты: `capabilities.password_reset !== true` → вид `resetoff` («Восстановление по почте пока не включено» + плашка «напишите Лёве»); проверка формата почты на клиенте; `POST /api/auth/forgot`; 429 = «Слишком много попыток, подождите минуту»; `>= 500` = «Сервис не отвечает, попробуйте через минуту»; всё остальное (в том числе 200) = вид `sent` с **одинаковым** текстом, есть почта в GG ID или нет.

- Поле: `data-gid-domain="global-generations.com"` + `[data-gid-domain-hint]` (подсказка «Ссылка приходит только на рабочую почту @global-generations.com»). Сервер всё равно проверяет сам, подсказка только экономит человеку время.
- В виде `sent` подставить введённую почту в `<b>` через `textContent`. «Открыть почту» = `https://mail.google.com/` (Google Workspace). «Отправить ещё раз» включается отсчётом `data-gid-countdown="42" data-gid-countdown-done="enable:#gid-resend"`, повторная отправка = тот же POST.

### 4.3 `set-password.html` (экраны `setpass`, `saved`, `expired`)

Инварианты (страница публичная, токен секретный):
1. Токен из `#token=` (или старого `?token=`), сразу `history.replaceState(null, '', location.pathname)`, в хранилище не класть, в логи не писать.
2. `invite=1` (в query или во фрагменте): заголовок «Добро пожаловать в команду», подзаголовок «Придумайте пароль GG ID. С ним вы входите во все сервисы Global Generation.». Без него: заголовок «Новый пароль», подзаголовок «Придумайте новый пароль GG ID.».
3. Нет токена → `expired`. `POST /api/auth/set-password/check` ответил `{valid:false}` → `expired`.
4. Клиентская проверка: 12-256 символов, пароли совпадают (кит подсвечивает повтор сам). Ошибки: «Нужно не меньше 12 символов», «Пароль слишком длинный: до 256 символов», «Пароли не совпадают».
5. `POST /api/auth/set-password`: ok → `saved`; 400 `weak_password` → «Пароль не подошёл: нужно от 12 до 256 символов»; 400 иное (`invalid_token`) → `expired`; 429 → «Слишком много попыток, подождите минуту»; прочее → «Не получилось сохранить (ошибка N). Попробуйте ещё раз»; сеть → «Сеть недоступна».
6. `saved` ведёт на `/login.html` (сессию set-password не создаёт). Предложение Face ID человек увидит уже после входа.

Разметка: `data-gid-newpass` на первом поле, `data-gid-repeat` на втором, `[data-gid-meter]` и `[data-gid-rules]` с `data-rule="len|mix|case"`. Правила и шкала в ките совпадают с текущей страницей (4-й уровень с 14 символов). Скрытое `<input type="email" autocomplete="username" hidden>` с почтой (если сервер отдаёт её в `check`), чтобы менеджер паролей сохранил пару правильно.

### 4.4 `no-access.html` (экран `noaccess`)

Отдаётся nginx как `error_page 403` (статус остаётся 403), значит страница не знает, какой раздел просили. Тексты: заголовок «Нет доступа», подзаголовок «Вы вошли в GG ID, но этот раздел открыт не для всех. Если он нужен для работы, напишите Лёве: он откроет доступ.».

- `GET /api/auth/me`: если есть имя и почта, показать блок `.gid-who` (инициалы, имя, почта, ссылка «Сменить» = выход и `/login.html`). Если `me` не отдаёт имя, блок не показывать.
- Кнопка: `level === 'services'` → «Открыть мои сервисы» → `/cabinet/`, иначе «Вернуться на главную» → `/` (как сейчас).

### 4.5 sso-gate (другие хосты: PIN и единый вход сервисов)

Сейчас страницы рисует `sso-gate/gate.py` (`render_page(title, body, buttons)`) и статика в `/var/www/gg-gate/`:

| Сейчас | Экран кита | Что сделать |
|---|---|---|
| `nginx/pin-gate.html` → `/var/www/gg-gate/index.html` (`/__gate/`) | `pin` | 4 ячейки `data-gid-code`, на `gid:code` ставить куку `gg_pin` как сейчас и `location.replace("https://" + location.hostname + next)`. Неверный код (вернулись на гейт с уже стоящей кукой): `.gid-code.is-error` + `GGID.shake(box)` + сообщение «Неверный код, попробуйте снова». `next` только путь своего хоста, не `/__gate`. Подзаголовок: «<сервис> пока входит по коду для команды.» |
| `denied_page(email)` (403) | `noaccess` | почта в `.gid-who`, главная кнопка «Выйти» → `/__sso/logout` (кнопка, а не ссылка, если выход требует same-origin клика) |
| `interstitial_page(target, idp)` (режим перехода) | `login` в упрощённом виде | главная «Войти через GG ID» (`/__sso/login?go=1...`), вторая «Войти по PIN» (`/__gate/?next=...`) |
| `unavailable_page(pin=True)` → `sso-unavailable-auth.html` | `unavailable` | + ссылка «Войти по PIN» |
| `unavailable_page(pin=False)` → `sso-unavailable-gate.html` | `unavailable` | без PIN (гейт лежит, PIN проверяет он же) |
| `error_page(title, body)` | общий: `gid-h` + `gid-sub` + главная «Войти заново» | заголовки и тексты оставить как в `gate.py` («Вход не подтверждён», «Вход не удался», «Сессия уже закончилась...») |

Особенность: это не хаб GG ID, `/assets/gg-id/` там не отдаётся, а шрифт с чужого origin браузер не загрузит без CORS. Два варианта:
- **А (проще, как сейчас с логотипом)**: `gate.py` встраивает CSS кита и шрифты `data:` прямо в страницу. Объём ~110 КБ на страницу, для редких страниц ошибок нормально. Лимит nginx 4096 байт касается только встраивания строкой в конфиг, а у тебя страницы отдаются файлами и из Python.
- **Б**: класть кит в `/var/www/gg-gate/gg-id/` тем же `sso-gate/deploy.sh --apply` и отдавать через существующий `location ^~ /__gate/` (проверить, что он отдаёт подпапку и не требует PIN для статики). Тогда страницы ссылаются на `/__gate/gg-id/gg-id.css`.

После правки шаблона перегенерировать статику командой из `sso-gate/README.md`, прогнать `tests/test_gate.py`, e2e `sso-gate/tests/e2e/run.sh`, `tests/test_nginx_output_directives.py`. Выкатка `--apply` = команда Лёва.

---

## 5. Компоненты для сервисов

Правило для всех сервисов GG: своей формы пароля и PIN нет. На экране сервиса одна кнопка, в шапке аккаунт, на 401 окно. Разметка целиком в витрине (раздел «Компоненты для сервисов») и в `gg-id/README.md`.

1. **Кнопка «Войти через GG ID»** (`.gid-sso`): ведёт на `https://id.global-generations-edu.com/api/auth/authorize?...` (параметры по твоему SSO-контракту). Стиль A: белая с тонкой рамкой `#c9d5e1`, без navy-заливки. Варианты: `--light` (на белом), `--on-dark` (на navy), `--sm` (в шапке), `--block` (во всю ширину). Прежний вход сервиса, пока он нужен, сворачивать под кнопку как «Резервный вход» (`details.gid-fb`). Значок = иконка GG ID: белый ключ на светлом градиенте `--grad-tile` (`gid-id-icon`, инлайн SVG из README кита: у сервиса свой origin, поэтому внешний спрайт хаба не подойдёт). Тёмную плитку корня GG не ставить (правило 4a).
2. **Аккаунт в шапке** (`.gid-acct` = `.gid-chip` + `.gid-menu`, поведение в `gg-id-service.js`): инициалы на navy-градиенте (без фото), имя; в меню имя и почта, «Мои сервисы» → `https://id.global-generations-edu.com/cabinet/`, «Аккаунт GG ID» (Face ID и пароль) → страница хаба для ключей (если её нет, пока убрать пункт), «Выйти» → выход сервиса + отзыв сессии (`/api/v1/sessions/revoke` по контракту), затем экран `signedout`.
3. **Сессия истекла** (`.gid-scrim` + `.gid-dialog`): на 401 от API сервиса вместо внезапного выброса на логин. Текст «Войдите снова, и мы вернём вас на эту же страницу.», кнопка GG ID с возвратом на текущий URL. Esc и клик по фону закрывают.

Подключение в сервисе: обёртка с классом `gid-kit` (даёт токены, тема по системе или `data-theme`), `gg-id.css` копией в статику сервиса (или только нужные блоки), Montserrat у сервисов GG и так самохостом из бренд-репо.

---

## 6. Тексты (копирайт)

Все тексты экранов в `src/gg_id/screens.html`. Правила, по которым они написаны:
- Команде чётко и спокойно, без кодов ошибок и без вины («Проверьте раскладку и Caps Lock», а не «Ошибка авторизации»).
- Без длинных и средних тире, без эмодзи. «Ментор», не «наставник». «Джи-джи», не «ИИ».
- Названия сервисов не склоняем: «Вход в АКБ», «сервис «Пульс»».
- Вход по ключу называем «Face ID». «Touch ID», «Windows Hello», «отпечаток» и «палец» только когда в этом браузере уже входили своим ключом (раздел 6.1): `GGID.passkeyText('login'|'enroll'|'wait')` сама выбирает слова, значок меняет кит (`data-gid-passkey-icon`).
- Если Лёв решит открыть GG ID студентам: тон теплее (как Duolingo), заголовок «С возвращением!» и т.п., вид тот же.

### 6.1 Подписи входа по ключу: устройство не угадываем (правило 09.10.2026)

Причина: ключ GG ID Лёва лежит только в iPhone, а Chrome на маке показывает один QR-код телефона; страница при этом писала «Приложите палец к Touch ID». Датчик на маке есть, ключа для сайта на нём нет, а вид устройства (`GGID.passkeyKind()`) этого не знает.

**Правило.** «Touch ID», «Windows Hello», «отпечаток» и «палец» говорим, только когда в ЭТОМ браузере подтверждён ключ самого устройства. Иначе то, что верно всегда: Face ID на телефоне (QR-код) или ключ на этом устройстве. Одно исключение: предложение завести ключ здесь (`enroll` и `enroll-lead`, начало его подзаголовка) называет способ устройства, потому что ключ создаётся на нём; показывать его только после `GGPasskey.platformAvailable()`.

**Память браузера** лежит в `localStorage` (каждое обращение в try/catch, без хранилища всё работает). Origin у страницы входа хаба (Infra-Services-Portal #168, эталон), страницы подтверждения Face ID для админов (Infra-AWS #98) и кита один, поэтому имена общие; переименовать можно только везде сразу.

| Имя | Значение | Когда |
|---|---|---|
| `gg-id-local-key` | `1`: ключ устройства работает здесь | ставится, когда подтверждение пришло с `authenticatorAttachment` `platform` или ключ создан здесь (`create()` сказал `platform` или промолчал); снимается, если попытка с ним кончилась `NotAllowedError`, а следующее подтверждение пришло с `cross-platform` |
| `gg-id-last-method` | `platform` или `cross-platform` (телефон по QR-коду, ключ безопасности) | после каждого принятого подтверждения |
| `gg-id-local-miss` | `1` | `NotAllowedError` при поставленном `gg-id-local-key`; снимает следующее принятое подтверждение |
| `gg-id-enroll-skip` | время в мс | «Не сейчас», `InvalidStateError`, `already_registered` (ключ человека уже стоит, например в телефоне): неделю ключ не предлагаем, про это устройство ничего не узнали |

Ключ, который браузер назвал `cross-platform` (телефон, выбранный в окне браузера), ключом устройства не считается.

| Что браузер видел | Подсказка, пока открыто окно браузера | Кнопка входа |
|---|---|---|
| последний способ `platform` и ключ устройства | «Подтвердите вход: Touch ID на этом устройстве.» (слово по устройству: Touch ID, Face ID, Windows Hello, отпечаток пальца, ключ доступа) | «Войти с Touch ID», на Windows «Войти с Windows Hello», на Android «Войти по отпечатку» |
| последний способ `cross-platform` | «Подтвердите вход с телефона: наведите камеру телефона на QR-код в окне браузера и подтвердите Face ID.» | «Войти с Face ID» |
| ничего (новый браузер, хранилище недоступно) | «Подтвердите вход в окне браузера: Face ID на телефоне (QR-код) или ключ на этом устройстве.» | «Войти с Face ID» |

На iPhone и iPad QR-кода нет, там подсказка «Подтвердите вход Face ID в системном окне. Это займёт секунду.», на Android «Подтвердите вход в системном окне. Это займёт секунду.» и кнопка «Войти по ключу доступа». Пока ждём, на кнопке «Ждём подтверждения».

**Как это делает кит.** `GGID.init` подписывает кнопки, значки и подсказку сам (`data-gid-passkey`, `data-gid-passkey-icon`, `data-gid-passkey-hint`). Чем закончился вход, сообщает страница: `GGID.passkeyWatch()` один раз при загрузке (читает `authenticatorAttachment` из ответов браузера, `GGPasskey` не трогаем), после входа `GGID.passkeyRemember(GGID.passkeySeen())`, после создания ключа `GGID.passkeyCreated()`, при ошибке входа `GGID.passkeyMissed(e)`, при «Не сейчас» и `InvalidStateError` `GGID.passkeySnooze()`. Эскиз в 4.1 уже на этом, справочник в `gg-id/README.md`, «Вход по ключу».

**Предложение ключа после входа с телефона.** Вошли с `cross-platform`, своего ключа в этом браузере нет (`!GGID.passkeyMemory().local`), `platformAvailable()` истинно, неделю не отказывались: показать `enroll` с заголовком «Добавить вход по Touch ID на этом устройстве?» (слово по устройству, текст собирает страница; эталон в #168). Второй ключ сервер разрешает из сессии по Face ID, а она у человека только что появилась.

Проверки: `src/check_gg_id_passkey.py` (идёт и в `src/check_gg_id.py`), сборка не пускает слова про способ устройства в разметку экранов.

---

## 7. Безопасность: что нельзя сломать при переносе

- `next` только тот же origin (иначе открытый редирект, уже чинили 07.10).
- Токен set-password: только из фрагмента, сразу стереть из адреса, никуда не сохранять. Заголовки страницы (`no-store`, `no-referrer`, `access_log off`) уже в nginx, их не трогать.
- «Забыли пароль» отвечает одинаково, есть почта или нет (иначе можно перебрать, кто в команде).
- В публичных файлах (`login.html`, `forgot.html`, `set-password.html`, `assets/`) ничего секретного: ни почт людей, ни имён переменных, ни токенов. Демо-значения из эталонов (`lev@global-generations.com`, `Mentor2026`, `mentor-ggid-2026`, «Мария Иванова») **не переносить**: поля пустые.
- `X-Frame-Options: DENY` на входе оставить (защита от кликджекинга).
- Только почты @global-generations.com (железное правило 07.10). Подсказка кита клиентская, проверка остаётся на сервере.
- `autocomplete`: `username`, `current-password`, `new-password`, `one-time-code`; поля 16 px (iPhone не приближает).
- В nginx не подставлять раскодированное (`$uri`, `$1`...), только `$request_uri` (CRLF, чинили 08.10). Для кита правка nginx не нужна.
- Лёв никогда не должен остаться без входа: break-glass и вход владельца не завязывать на новый вид (если JS упал, форма пароля должна работать: можно отрисовать вид `password` без `hidden` и прятать его скриптом, а не наоборот).

---

## 8. Решения Лёва (не решать за него)

1. **Раскладка**: по умолчанию «Сплит» (navy-панель с картой GG ID на ленте, с 08.10 «Итог»; на телефоне в низком окне бейдж карты в строке над формой). Альтернативы «Карточка» и «Минимал» переключаются одним атрибутом `data-layout`. Текст панели без списка внутренних сервисов (страницы публичные).
2. **Шапка «GG × Aura»** на входе хаба: решено 08.10, только GG, без логотипа и без ссылки Aura.
3. **Подпись у логотипа**: сейчас «ID» (= Global Generation ID). Если хочет буквально «GG ID», это одна строка в ките.
4. **Предложение Face ID** после входа по паролю: показывать (рекомендую) и как часто после «Не сейчас» (в эскизе 7 дней).
5. **Экран «Продолжить как»**: нужен ли вообще (зависит от поведения authorize).

---

## 9. Что не делать

- Не мержить и не деплоить хаб без «деплой» в текущем сообщении Лёва. `deploy-nginx.sh` и `sso-gate/deploy.sh --apply` запускает Лёв.
- Не класть кит в `/gg-id/` (там твои инструкции, другой `location` и уровень доступа admin).
- Не править файлы кита в хабе руками: только PR в Infra-Brand-Identity и sync с `VERSION`.
- Не рисовать логотип заново, не красить его в другие цвета (только navy и белый), не ставить никаких значков над заголовком входа (ни замка, ни плашки, правило 07.10).
- Не трогать `/assets/montserrat-*.woff2` и `/assets/gg-ui.css` хаба: на них живут другие страницы и `/m/`.
- Не трогать Aura-репо, хосты и секреты (вход Aura у Яна).

---

## 10. Проверка после каждого PR хаба

1. Тесты хаба: `python3 -m unittest discover -s tests -p 'test_*.py'`, `scripts/check-auth-registry.py`, `scripts/deploy.sh --check`.
2. Визуально без входа: Playwright по `/login.html`, `/forgot.html`, `/set-password.html#token=x` на 1440 и 390, светлая и тёмная (`color_scheme`), горизонтальной прокрутки нет, шрифт Montserrat, консоль чистая. Мой `src/check_gg_id.py` можно взять за основу.
3. С входом: кука из `scripts/mint-test-session.sh` (в чат и логи не выводить), `/no-access.html` и переход `done → land()`.
4. Вручную у Лёва (агент этого проверить не может, ключи привязаны к его устройствам): iPhone Face ID вход; Mac в Chrome, когда ключ только в iPhone: в окне браузера один QR-код, а на странице ни слова про Touch ID и палец (раздел 6.1); вход ключом самого мака, после него кнопка «Войти с Touch ID»; вход по паролю + «Подключить Face ID» + повторный вход по Face ID, «Забыли пароль» до письма, ссылка из письма, тёмная тема на телефоне.
5. Прод после деплоя: не «200», а проверка содержимого (`<title>` и заголовок «Вход в ...»), cache-busted.

---

## 11. Если что-то непонятно

- Витрина: `gg-id.html` в Infra-Brand-Identity (или `~/Desktop/GG-ID-2026-10-08/gg-id.html`), там у каждого экрана подпись «когда показываем» и «что вызывает в хабе».
- Справочник атрибутов и JS: `gg-id/README.md`.
- Нужен новый экран или вариант: правка `src/gg_id/screens.html` (+ подпись в `INFO` в `src/build_gg_id.py`), сборка, проверка, PR в Infra-Brand-Identity. Сессия дизайна: «gg-id login block» (`SendMessage`), если жива.
