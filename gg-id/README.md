# GG ID: единый вход Global Generation

Кит экранов входа для хаба levauth (IdP = Lambda `gg-portal-auth`) и компонентов для сервисов. Один вход, один вид во всех сервисах GG. Aura-продукты сюда не входят: у Aura свой вход.

- Витрина: `../gg-id.html` (все экраны, 3 раскладки, светлая и тёмная тема, телефон и компьютер, компоненты, правила). Ссылка на состояние: `gg-id.html#s=error&l=card&t=dark&d=phone`.
- Эталонные страницы: `screens/<экран>.html`, открываются как есть. Раскладка и тема параметрами: `screens/login.html?layout=card&theme=dark`. Переходы между ними демо: в хабе их заменяют вызовы `/api/auth/*`.

## Файлы

| Файл | Что внутри |
|---|---|
| `gg-id.css` | токены (светлая и тёмная тема), раскладки `split`, `card`, `minimal`, все компоненты |
| `gg-id.js` | без зависимостей и без сети: глаз пароля, только рабочая почта, правила нового пароля, ячейки кода, обратный отсчёт, подписи Face ID / Touch ID / Windows Hello |
| `fonts/` | Montserrat (переменный, 400-700), кириллица и латиница, самохостом |
| `sprite.svg` | логотип `gid-logo`, плитка фавикона `gid-tile` и все иконки `gi-*` одним файлом: `<use href="/assets/gg-id/sprite.svg#gi-eye"/>` (тот же origin) |
| `screens/` | 17 эталонных экранов, генерируются, руками не править |

Хаб копирует `gg-id.css`, `gg-id.js`, `fonts/`, `sprite.svg` к себе (например в `/assets/gg-id/`). Пути к шрифтам в CSS относительные: `fonts/...` рядом с `gg-id.css`.

## Каркас страницы

```html
<body class="gid-body">
<div class="gid" data-layout="split">            <!-- split (рекомендую) | card | minimal; data-theme="dark" только чтобы зафиксировать тему, иначе по системе -->
  <div class="gid-frame">
    <aside class="gid-aside">...</aside>          <!-- только для split, разметку брать из screens/login.html -->
    <main class="gid-main">
      <section class="gid-card">
        <div class="gid-lockup"><svg class="gid-logo" viewBox="0 0 777 196" role="img" aria-label="Global Generation"><use href="#gid-logo"/></svg><span class="gid-lockup-name">ID</span></div>
        <h1 class="gid-h">Вход в АКБ</h1>         <!-- название сервиса из client_id -->
        <p class="gid-sub">...</p>
        ...
      </section>
      <footer class="gid-foot"><span><b>GG ID</b> · единый вход Global Generation</span></footer>
    </main>
  </div>
</div>
<!-- спрайт иконок и логотипа: скопировать из любого screens/*.html -->
<script src="/assets/gg-id/gg-id.js"></script>
</body>
```

Раскладки переключаются только атрибутом, разметка одна. Ширину кит меряет container queries, поэтому тот же экран правильно ложится и во всё окно, и в модальное окно сервиса.

## Разметка поведения

| Атрибут | Что делает |
|---|---|
| `data-gid-passkey="login\|enroll\|wait"` | текст кнопки по устройству: «Войти с Face ID», «Войти с Touch ID», «Войти с Windows Hello», «Войти по отпечатку», «Войти по ключу доступа» |
| `data-gid-passkey-icon` на `<svg>` | значок к ней: лицо, отпечаток или ключ |
| `data-gid-eye` | кнопка «показать пароль» в `.gid-input-wrap` |
| `data-gid-domain="global-generations.com"` + `[data-gid-domain-hint]` | подсказка «только рабочая почта» сразу после ввода, до сервера |
| `data-gid-newpass`, `data-gid-repeat`, `[data-gid-meter]`, `[data-gid-rules] [data-rule=len\|mix\|case]` | шкала и галочки нового пароля вживую (правила как на сервере: 12-256 символов, буквы и цифры, заглавные и строчные) |
| `data-gid-code` | ячейки кода: ввод, вставка целиком, стирание назад; готовый код = событие `gid:code` с `detail.code` |
| `data-gid-countdown="42"` + `data-gid-countdown-done="enable:#id\|reload"` | обратный отсчёт «через 0:42», по нулю включает кнопку или перезагружает страницу |
| `[data-gid-error]` + `[data-gid-error-text]` | блок ошибки над кнопкой |

JS: `GGID.busy(btn, true, 'Входим')` и `GGID.busy(btn, false)` (кнопка занята, второй запрос не уходит), `GGID.error(root, 'Неверная почта или пароль', [email, password])` (текст, подсветка, встряска), `GGID.shake(el)`, `GGID.passkeyKind()`, `GGID.passwordChecks(v)`. Если разметка появляется позже, вызвать `GGID.init(root)`.

## Как связать со входом хаба

Логика как в текущем `login.html` хаба, меняется только вид:

1. `GET /api/auth/capabilities`: `password_reset` показывает «Забыли пароль?», `aura_login` показывает ссылку «Войти через Aura» (`/api/auth/aura/start?next=...`).
2. `GGPasskey.platformAvailable()` и `GGPasskey.enabled()`: если ключ есть, первый экран `login` (Face ID главной кнопкой); если нет, сразу `password`.
3. Face ID: `GGID.busy(btn, true)` и состояние `passkey`, затем `GGPasskey.login()`. `NotAllowedError` (человек отменил) = тихо назад, без ошибки. Другая ошибка = «Face ID не сработал, войдите по паролю» и экран `password`.
4. Пароль: `POST /api/auth/login`. 401 = «Неверная почта или пароль. Проверьте раскладку и Caps Lock.», 429 = «Слишком много попыток, подождите минуту», сеть = «Сеть недоступна». Поле пароля очистить, фокус в него.
5. Успех: экран `done` (сборка знака) и `location.replace(next)`. После входа по паролю на устройстве без ключа сначала `enroll` (`GGPasskey.register()`), «Не сейчас» идёт дальше.
6. `next` проверять как сейчас: только тот же origin, не `/login.html`.

<!-- screens:start -->
## Экраны

| Экран | Файл | Когда | Хаб |
|---|---|---|---|
| Вход | `screens/login.html` | Первый экран. Главная кнопка Face ID, если на устройстве есть ключ входа; если нет, сразу экран пароля. Aura только ссылкой и только когда сервер включил. | `GET /api/auth/capabilities, GGPasskey.enabled(), GGPasskey.login()` |
| По паролю | `screens/password.html` | Почта и пароль. После входа без ключа на устройстве предлагаем подключить Face ID. | `POST /api/auth/login` |
| Ошибка | `screens/error.html` | 401: неверная почта или пароль, поля трясутся, пароль очищается. 429: «Слишком много попыток, подождите минуту». Сеть: «Сеть недоступна». | `POST /api/auth/login: 401, 429` |
| Face ID | `screens/passkey.html` | Открыто системное окно Face ID. Кнопка занята, второй запрос не уходит. Отмена в системном окне возвращает на первый экран без ошибки. | `GGPasskey.login()` |
| Готово | `screens/done.html` | Вход выполнен, идёт переход в сервис. Фирменная сборка знака, как прелоудер бренда. | `GET /api/auth/me, переход на next` |
| Продолжить как | `screens/continue.html` | Сессия GG ID на устройстве уже есть, сервис просит подтвердить аккаунт. | `GET /api/auth/authorize` |
| Подключить Face ID | `screens/enroll.html` | После входа по паролю, если ключа на этом устройстве нет. Совет: после «Не сейчас» не спрашивать на этом устройстве неделю. | `GGPasskey.register()` |
| Забыли пароль | `screens/forgot.html` | Восстановление по рабочей почте. | `POST /api/auth/forgot` |
| Письмо отправлено | `screens/sent.html` | Ответ одинаковый, есть такая почта в GG ID или нет: так нельзя проверить, кто в команде. | `POST /api/auth/forgot: 200` |
| Новый пароль | `screens/setpass.html` | Ссылка из приглашения или восстановления (#token=). Приглашение: «Добро пожаловать в команду», восстановление: «Новый пароль». Правила как на сервере. | `POST /api/auth/set-password/check, POST /api/auth/set-password` |
| Пароль сохранён | `screens/saved.html` | После сохранения пароля. Сессии нет, человек идёт ко входу, браузер сам подставит новый пароль. | `POST /api/auth/set-password: 200` |
| Восстановление выключено | `screens/resetoff.html` | capabilities.password_reset не true: восстановление по почте выключено, вместо формы эта плашка. | `GET /api/auth/capabilities` |
| Ссылка устарела | `screens/expired.html` | Токен из ссылки устарел или уже использован. | `POST /api/auth/set-password/check: ошибка` |
| Нет доступа | `screens/noaccess.html` | Человек вошёл, но роли в этом сервисе у него нет. | `GET /api/auth/me (level), entitlements` |
| Код доступа | `screens/pin.html` | Переходный вход по коду для сервисов, которые ещё не на GG ID. | `sso-gate: PIN-ворота` |
| Недоступен | `screens/unavailable.html` | GG ID не отвечает (5xx или таймаут). Страница сама пробует снова. | `sso-gate: sso-unavailable` |
| Вы вышли | `screens/signedout.html` | После «Выйти» в меню аккаунта. | `POST /api/v1/sessions/revoke` |
<!-- screens:end -->

## Компоненты для сервисов

Сервис не рисует свою форму пароля и PIN. Обёртка `class="gid-kit"` даёт токены (тема по системе или `data-theme`).

```html
<!-- единственная кнопка входа на экране сервиса: ведёт на /api/auth/authorize хаба (параметры по SSO-контракту хаба, как у sso-gate) -->
<a class="gid-sso" href="https://levauth.global-generations-edu.com/api/auth/authorize?...">
  <svg class="gid-sso-tile" viewBox="0 0 39 39" aria-hidden="true"><use href="#gid-tile"/></svg><span>Войти через GG ID</span>
</a>
<!-- варианты: gid-sso--light (на белом), gid-sso--on-dark (на navy), gid-sso--sm (в шапке), gid-sso--block (во всю ширину) -->

<!-- аккаунт в шапке -->
<button class="gid-chip" aria-expanded="false" aria-haspopup="menu"><span class="gid-avatar gid-avatar--xs">ЛА</span><span>Лёв</span><svg class="gid-ic"><use href="#gi-chevron-down"/></svg></button>
<div class="gid-menu" role="menu">  <!-- gid-menu-head, gid-menu-item, gid-menu-sep, gid-menu-meta -->

<!-- сессия истекла (сервис получил 401): окно поверх страницы, не выброс на логин -->
<div class="gid-scrim gid-kit"><div class="gid-dialog" role="dialog" aria-modal="true">...</div></div>
```

Разметку целиком брать из витрины (раздел «Компоненты для сервисов»). Значок кнопки = фавикон сайта как есть (`assets/favicons/root.svg`), символ `gid-tile` в спрайте.

## Правила

- Над заголовком ничего: ни замка, ни значка, ни плашки (правило 07.10). Заголовок называет сервис: «Вход в АКБ». Названия сервисов пишем так, чтобы не склонять («сервис «Пульс»»).
- Подпись «логотип | ID»: логотип один, одного цвета (navy на светлом, белый на тёмном), высота 28 px (ширина не меньше 110 px).
- Одно главное действие на экране. Aura только ссылкой и только если сервер включил.
- Только рабочая почта @global-generations.com. Восстановление отвечает одинаково, есть почта в GG ID или нет.
- Тексты: без длинных тире и эмодзи, «ментор», «Джи-джи». Команде чётко и спокойно, ошибки без кодов.
- Поля 16 px (iPhone не приближает), `autocomplete`: `username`, `current-password`, `new-password`, `one-time-code`.
- Цвет: navy главное действие, голубой `#009CDC` только фокус и прогресс, красный и зелёный только для смысла. Тёмная тема: главная кнопка белая.
- Движение только opacity и transform; «меньше движения» в системе выключает бегущие строки, пятна и сборку знака.

## Пересобрать и проверить

```
python3 src/build_gg_id.py                                  # gg-id.html, gg-id/screens/*.html, gg-id/fonts/*
uv run --with playwright python src/check_gg_id.py          # все экраны x 3 раскладки x 2 темы x 1440/390 px + витрина
```

Правки вида: `gg-id/gg-id.css`. Тексты и экраны: `src/gg_id/screens.html` (подписи «когда» и «API» в `INFO` внутри `src/build_gg_id.py`). Витрина: `src/gg_id/showcase.html`.
