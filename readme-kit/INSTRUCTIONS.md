# README в стиле GG: draft PR на каждый репо (без мержа)

Лёв (владелец, Global Generation) хочет, чтобы README всех репо орги `Global-Generation` были оформлены как у `Infra-Core` / `Infra-IaC`:
лого по центру, заголовок, строка-описание, бейджи стека и прода, навигация по разделам. Пилот, одобренный по дизайну:
- https://github.com/Global-Generation/GG-Product-SAT/blob/docs/readme-design/README.md (спека `spec-sat.json`)
- https://github.com/Global-Generation/Ops-Legal/blob/docs/readme-design/README.md (`spec-legal.json`)
- https://github.com/Global-Generation/Aura-LeadGen-CRM/blob/docs/readme-design/README.md (`spec-crm.json`, README написан с нуля)

Всё лежит в `~/Global-Generation/Infra-Brand-Identity/readme-kit/`. Генератор: `build_readme.py <spec.json> <worktree-dir>`.
Он сам ставит шапку (лого GG для всех, лого Aura для репо `Aura-*`, размеры уже правильные), навигацию по `##`-разделам,
кладёт лого в `.github/assets/`, убирает длинные тире и эмодзи из текста (код не трогает). Повторный запуск безопасен.

## Шаги на каждый репо из своего списка

1. `gh auth switch -u LevAvdoshin` (один раз). Клон: `~/Global-Generation/<Repo>`; если его нет: `repo Global-Generation/<Repo>`.
   Не трогай рабочую копию (там могут работать другие агенты): `git -C <clone> fetch -q origin` и
   `git -C <clone> worktree add -q -b docs/readme-design <clone>/.claude/worktrees/readme-design origin/<default-branch>`.
   Если ветка `docs/readme-design` уже есть на origin, остановись по этому репо и запиши в отчёт.
2. Разберись, что это за репо: README, `package.json` / `requirements.txt` / `pyproject.toml`, структура папок, `.github/workflows`,
   домены (ищи в README, workflows, коде; домены на `*.global-generations-edu.com`, `global-generations.com`, `aura-ecosystem.com`).
   НЕ выдумывай: домен, версии и хостинг пиши только если нашёл в репо. Нет уверенности: бейджа нет.
3. Напиши спеку `~/Global-Generation/Infra-Brand-Identity/readme-kit/specs/<Repo>.json`:
   - `title`: человеческое название продукта (как в текущем H1 или описании репо), не slug.
   - `tagline`: одна строка, что это и для кого. Язык = язык текущего README (у большинства русский); нет README: русский.
   - `badges`: 2-4 бейджа стека (например Next.js / NestJS / Python / FastAPI / PostgreSQL / Terraform / HTML; цвета и `logo` как в пилотных спеках,
     slug иконок с simpleicons.org), 1 бейдж хостинга если известен (AWS App Runner / EC2 / S3 / Lambda / GitHub Actions), и бейдж
     `{"label":"Prod","message":"<домен>","color":"13445d","href":"https://<домен>"}` только если прод-домен точно найден.
   - `body`: `"keep"`, когда README содержательный (текст сохраняется полностью, первый `#`-заголовок уходит в шапку).
     `"drop_lead_lines": 1`, только если первая строка после H1 дословно повторяет tagline.
   - `body`: `"replace"` + `body_md`, когда README нет, он пустой или это заготовка (create-next-app и т.п.). Тогда напиши README по коду,
     по-русски, разделы `##`: что внутри (разделы / модули), стек, интеграции, деплой (только найденное), локальный запуск, документация (ссылки на
     существующие файлы `docs/` и т.п.). Образец: `spec-crm.json`.
4. `python3 ~/Global-Generation/Infra-Brand-Identity/readme-kit/build_readme.py <spec> <worktree>`.
5. Проверки перед коммитом:
   - `git -C <wt> diff --stat` трогает только `README.md` и `.github/assets/*.svg`;
   - в новом тексте нет «—», эмодзи, паролей/токенов/PIN (существующий текст не переписывай, но новых секретов не добавляй);
   - все относительные ссылки в новом/переписанном тексте ведут на существующие файлы.
6. Коммит строго с `[skip ci]` в первой строке (иначе в части репо пуш запускает сборку/деплой):
   `git -C <wt> add -A README.md .github/assets` и
   `git -C <wt> commit -m "docs: README в стиле GG (лого, бейджи, навигация) [skip ci]" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"`,
   `git -C <wt> push -q -u origin docs/readme-design`.
7. Draft PR в дефолтную ветку: `gh pr create --repo Global-Generation/<Repo> --draft --head docs/readme-design --title "docs: README в стиле GG"`
   с телом: «Оформление README как в Infra-Core / Infra-IaC (лого, бейджи, навигация). Только README и `.github/assets/*.svg`, коммит с [skip ci]. Не мержить до ОК Лёва.» + пустая строка + `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
8. Проверь, что на ветке не запустилось ни одного workflow: `gh run list --repo Global-Generation/<Repo> --branch docs/readme-design --json name -q length` = 0. Если запустился, сразу отмени (`gh run cancel <id>`) и запиши в отчёт.
9. Worktree оставь (понадобится для правок), рабочую копию и main не трогай. НИКОГДА не мержи PR и не пушь в main.

## Отчёт

Допиши строку на каждый репо в `~/Global-Generation/Infra-Brand-Identity/readme-kit/results.tsv` (через `>>`, одной строкой):
`<Repo>\t<PR url или ->\t<keep|replace>\t<brand gg|aura>\t<runs>\t<заметка: что не нашёл / что смутило>`.
В конце верни таблицу своих репо и проблемы. Не больше 20 строк.

## Строка для карточек хаба

Карточки в levauth (хаб и личный борд) берут строку из спеки: сначала `card_tagline`, иначе `tagline`. `card_tagline` нужен, когда README на английском, а в карточке нужна русская строка: README от него не меняется.
