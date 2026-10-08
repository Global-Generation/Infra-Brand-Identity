<!-- gg-readme-header:start -->
<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/global-generation-white.svg">
    <img src=".github/assets/global-generation-navy.svg" alt="Global Generation" width="115">
  </picture>

  <h1>Infra Brand Identity</h1>

  <p>Айдентика внутренних сервисов Global Generation: логотип, цвета, шрифт, фавиконы и правила.</p>

  <p>
    <img src="https://img.shields.io/badge/HTML-%D1%81%D1%82%D0%B0%D1%82%D0%B8%D0%BA%D0%B0-E34F26?logo=html5&logoColor=white" alt="HTML статика">
    <img src="https://img.shields.io/badge/Python-%D1%81%D0%B1%D0%BE%D1%80%D0%BA%D0%B0-3776AB?logo=python&logoColor=white" alt="Python сборка">
    <img src="https://img.shields.io/badge/%D0%A8%D1%80%D0%B8%D1%84%D1%82-Montserrat-13445d" alt="Шрифт Montserrat">
  </p>

  <p>
    <a href="#правила-утверждены-лёвом-28092026">Правила (утверждены Лёвом 28.09.2026)</a> ·
    <a href="#контуры-и-цвета-плиток">Контуры и цвета плиток</a> ·
    <a href="#пересобрать">Пересобрать</a> ·
    <a href="#где-уже-применено">Где уже применено</a>
  </p>
</div>
<!-- gg-readme-header:end -->

---

- `index.html` - страница айдентики (формат как у aura-ecosystem.com/brand.html, палитра GG): логотип, цвета, шрифт, компоненты, голос, сетка, токены, правила. Открыть в браузере.
- `lockups.html` - 10 вариантов подписи «логотип | сервис». Утверждён **вариант 2 «Во всю высоту»** (28.09.2026).
- `favicons-variants.html` - 10 вариантов фавиконов вместо «градиент + lucide» (07.10.2026, история выбора).
- `favicons-v9-icons.html` - вариант 9 с иконками в 7 палитрах (история выбора).
- `favicons-client-site.html` - клиентские как версии фавикона сайта. Утверждён **вариант 1 «Знак меньше + метка» для всех фавиконов GG**, внутренние тоже (07.10.2026).
- `assets/` - готовые файлы: бери отсюда, не рисуй заново.

## Правила (утверждены Лёвом 28.09.2026)

1. **Логотип один**: `assets/logo/global-logo-navy.svg` (знак + GLOBAL GENERATION широким гротеском) **одним цветом**: navy `#13445d` на светлом, белый (`global-logo-white.svg`) на тёмном. Везде: экран входа, шапки сервисов, письма, счета, PDF. Своих вордмарков, локапов на Montserrat и двухцветного знака нет.
2. **Название сервиса** рядом с логотипом через тонкую вертикальную линию **во всю высоту логотипа** (1 px, navy 20% на светлом, белый 35% на тёмном), отступ 14 px, Montserrat 600 navy (на тёмном белым).
3. **Фавиконы** (с 07.10.2026, клиентские и внутренние одинаково): версия фавикона сайта global-generations.com. Navy-градиент `#3D6488 → #1F3053`, белый знак GG чуть меньше слева сверху, справа снизу белая метка с navy-иконкой сервиса (свои залитые пиктограммы, не lucide). Файлы: `assets/favicons/<сервис>.svg`, `png/<сервис>-{32,180,192,512}.png` (180 = apple-touch-icon), `ico/<сервис>.ico`, список в `manifest.json` (поле `family`: client или internal). Корень GG (сайт, вход, каталог, письма) - `root.svg` = фавикон сайта как есть. SAT и IELTS теперь Aura, не GG. Старые «градиент + lucide» (`src/legacy-favicons/`) не использовать.
   Подключение: `<link rel="icon" href="/favicon.svg" type="image/svg+xml">`, `<link rel="icon" href="/favicon.ico" sizes="any">`, `<link rel="apple-touch-icon" href="/apple-touch-icon.png">`.
4. **Экран входа без значка** (с 07.10.2026): над «Вход для команды» никакой иконки, ни замка, ни плашки. Сервис уже подписан у логотипа.
5. **Джи-джи не трогаем**: только маскот `assets/gigi/gigi-mascot.png` как есть (это и аватарка @GGenbot_bot). Без плиток, градиентов, перекраски и замены иконкой.
6. Цвета интерфейса: navy `#13445d` (главное действие, активная вкладка), один акцент голубой `#009CDC`, ссылки текстом `#0077a8`, фон страницы `#e7eff8 → #eef3f9`, карточки белые. Токены: `assets/tokens/gg-tokens.css`.
7. Шрифт Montserrat самохостом (`src/fonts.css`), никаких CDN шрифтов. Иконки интерфейса lucide инлайн SVG (фавиконы: правило 3).
8. Нельзя: эмодзи, длинное тире, фиолетовый/сиреневый, декоративные полосы слева или сверху, «больничные» пастели.
9. Копирайт: «ментор» (не «наставник»), «Джи-джи» (не «ИИ»); стаффу чётко и корпоративно, студенту тепло, как Duolingo.

## Контуры и цвета плиток

| Семья | Сервисы |
|---|---|
| Клиентские | Сайт GG (фавикон сайта), Студенческий портал, Анкета apply.*, Презентация клиенту /d/ (Маяк: свой маскот Джи-джи) |
| Внутренние | АКБ, Пульс, Кабинет ментора, Юротдел, Бухгалтерия, Репортер, Онбординг, levauth, Стратегия, LLM-расходы |

Фавиконы у обеих семей одной схемы: плитка сайта, белый знак, белая метка, иконка `#12284C`. Сервис различается иконкой. Цвета контуров (`--c-*`) остаются только для интерфейса.

## Пересобрать

```
python3 src/build.py          # index.html из src/template.html
python3 src/build_lockups.py  # lockups.html
python3 src/check.py          # Playwright: 1440/390 px, шрифты, тире, ошибки (нужен playwright)
uv run --with fonttools --with brotli python src/build_favicon_variants.py --apply-final  # assets/favicons/*.svg
uv run --with playwright python src/rasterize_favicons.py                                  # png/*-180.png, ico/*.ico
```

Правки дизайна - в `src/template.html`, потом сборка и `check.py`. Новый сервис: строка в `SERVICES` в `src/build_favicon_variants.py` (контур + пиктограмма в `pictogram()`), строка в `SERVICES` внутри `template.html` и в `manifest.json`, затем две команды фавиконов выше и `build.py`.

## Где уже применено

- АКБ (GG-Product-Mentorship-AKB): на дев-стенде https://hub-dev.global-generations-edu.com ветка `exp/brand-v2` (шапка с логотипом, фавикон, вход, фон). Прод АКБ пока с текстовым заголовком «АКБ Global Generation».
