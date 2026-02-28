# Аналіз проєкту (Discovery)

AI ReviewBot має автоматичну систему **Project Discovery**, яка аналізує ваш репозиторій перед кожним code review. Discovery вивчає ваш стек, CI pipeline та конвенції, щоб рецензент давав розумніший і менш шумний зворотний зв'язок.

---

## Як це працює

Discovery запускає **4-рівневий pipeline** при першому PR/MR:

| Рівень | Джерело | Вартість |
|--------|---------|----------|
| **Рівень 0** — Platform API | Мови, дерево файлів, теги з GitHub/GitLab API | Безкоштовно (лише API) |
| **Рівень 1** — Аналіз CI | Парсинг GitHub Actions / GitLab CI / Makefile | Безкоштовно (локальний парсинг) |
| **Рівень 2** — Config файли | Читання `pyproject.toml`, `package.json`, конфігів лінтерів | Безкоштовно (читання файлів) |
| **Рівень 3** — LLM інтерпретація | AI інтерпретує неоднозначні дані (тільки коли рівнів 0-2 недостатньо) | ~50-200 токенів |

Кожен рівень деградує м'яко — якщо один зазнає невдачі, pipeline продовжує з тим, що має.

---

## Attention Zones

Discovery класифікує кожну область якості в одну з трьох **Attention Zones** на основі покриття вашим CI/інструментами:

| Зона | Емодзі | Значення | Поведінка рецензента |
|------|--------|----------|----------------------|
| **Well Covered** | ✅ | CI інструменти покривають цю область | Рецензент **пропускає** її |
| **Weakly Covered** | ⚠️ | Часткове покриття, є що покращити | Рецензент **звертає увагу** + пропонує покращення |
| **Not Covered** | ❌ | Автоматизацію не виявлено | Рецензент **фокусується** на цій області |

### Приклади зон

| Область | Статус | Причина |
|---------|--------|---------|
| Formatting | ✅ Well Covered | ruff format in CI |
| Type checking | ✅ Well Covered | mypy --strict in CI |
| Security scanning | ❌ Not Covered | No security scanner in CI |
| Test coverage | ⚠️ Weakly Covered | pytest runs but no coverage threshold |

---

## Що відбувається автоматично

1. **Discovery аналізує** ваш репозиторій (мови, CI інструменти, конфіг-файли).
2. **Attention Zones обчислюються** — кожна область якості класифікується як Well Covered, Weakly Covered або Not Covered.
3. **Промпт рецензії збагачується** зонно-орієнтованими інструкціями (~200-400 токенів).
4. **Рецензент пропускає** Well Covered області та **фокусується** на Not Covered.

### Коментар Discovery

Якщо Discovery знаходить **прогалини** або непокриті зони, він постить одноразовий підсумковий коментар у PR/MR:

> ## 🔍 AI ReviewBot: Project Analysis
>
> **Stack:** Python (FastAPI) 3.13, uv
>
> **CI:** ✅ .github/workflows/tests.yml — ruff, mypy, pytest
>
> ### Not Covered (focusing in review)
> - ❌ **Security scanning** — No security scanner detected in CI
>   💡 Consider adding bandit or safety to your pipeline
>
> ### Could Be Improved
> - ⚠️ **Test coverage** — pytest runs but no coverage threshold enforced
>   💡 Add `--cov-fail-under=80` to enforce minimum coverage
>
> **Questions / Gaps:**
> - No security scanner detected in CI
>   *Question:* Do you use any security scanning tools?
>   *Assumption:* Will check for common vulnerabilities manually
>
> ---
> 💡 *Create `.reviewbot.md` in your repo root to customize.*

У **verbose mode** (`discovery_verbose=true`) коментар також включає Well Covered зони:

> ### Well Covered (skipping in review)
> - ✅ **Formatting** — ruff format in CI
> - ✅ **Type checking** — mypy --strict in CI

---

## Watch-Files та кешування (Caching)

Discovery використовує **watch-files** щоб уникнути повторного запуску LLM аналізу, коли конфігурація проєкту не змінилась.

### Як це працює

1. **Перший запуск:** Discovery виконує повний pipeline, LLM повертає список `watch_files` (наприклад, `pyproject.toml`, `.github/workflows/tests.yml`).
2. **Наступні запуски:** Discovery хешує кожен watch-file і порівнює з кешованим snapshot.
3. **Якщо не змінилось:** використовується кешований результат — **0 LLM токенів**.
4. **Якщо змінилось:** LLM повторно аналізує проєкт.

Це означає, що повторні PR в одній гілці коштують **нуль додаткових токенів** для discovery, доки спостережувані конфігураційні файли не змінились.

!!! tip "Економія токенів"
    На типовому проєкті другий і наступні PR використовують 0 токенів для discovery. Лише зміни в CI конфігурації, `pyproject.toml`, `package.json` або подібних файлах тригерять новий LLM виклик.

---

## CLI команда `discover`

Ви можете запустити discovery окремо (без створення ревʼю) за допомогою команди `discover`:

```bash
ai-review discover owner/repo
```

### Опції

| Опція | Скорочено | Опис | Default |
|-------|-----------|------|---------|
| `--provider` | `-p` | Git провайдер | `github` |
| `--json` | | Вивід у JSON | `false` |
| `--verbose` | `-v` | Показати всі деталі (conventions, CI інструменти, watch-files) | `false` |

### Приклади

```bash
# Базовий discovery
ai-review discover owner/repo

# JSON вивід для скриптів
ai-review discover owner/repo --json

# Verbose з усіма деталями
ai-review discover owner/repo --verbose

# GitLab проєкт
ai-review discover group/project -p gitlab
```

!!! info "Зворотна сумісність"
    `ai-review` (без subcommand) все ще запускає ревʼю як раніше. Subcommand `discover` є новим.

---

## `.reviewbot.md`

Створіть файл `.reviewbot.md` у корені репозиторію, щоб надати явний контекст проєкту. Коли цей файл існує, Discovery **пропускає автоматичний pipeline** і використовує вашу конфігурацію напряму.

### Формат

```markdown
<!-- Auto-generated by AI ReviewBot. Feel free to edit. -->
# .reviewbot.md

## Stack
- **Language:** Python 3.13
- **Framework:** FastAPI
- **Package manager:** uv
- **Layout:** src

## Automated Checks
- **Linting:** ruff
- **Formatting:** ruff
- **Type checking:** mypy
- **Testing:** pytest
- **Security:** bandit
- **CI:** github_actions

## Review Guidance

### Skip (CI handles these)
- Import ordering (ruff handles isort rules)
- Code formatting and style (ruff format in CI)
- Type annotation completeness (mypy --strict in CI)

### Focus
- SQL injection and other OWASP Top 10 vulnerabilities
- API backward compatibility
- Business logic correctness

### Conventions
- All endpoints must return Pydantic response models
- Use dependency injection for database sessions
```

### Секції

| Секція | Призначення |
|--------|-------------|
| **Stack** | Основна мова, версія, фреймворк, менеджер пакетів, layout |
| **Automated Checks** | Інструменти, що вже працюють у CI (рецензент пропустить ці області) |
| **Review Guidance → Skip** | Конкретні області, які рецензент не повинен коментувати |
| **Review Guidance → Focus** | Області, на які ви хочете більше уваги |
| **Review Guidance → Conventions** | Специфічні правила проєкту, які рецензент має дотримувати |

!!! tip "Автогенерація"
    Ви можете дозволити Discovery запуститися один раз, потім скопіювати його результати у `.reviewbot.md` та скоригувати за потреби. Бот додає у footer посилання, що пропонує цей workflow.

---

## Конфігурація

| Змінна | За замовчуванням | Опис |
|--------|------------------|------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Увімкнути або вимкнути аналіз проєкту |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Завжди постити коментар discovery (default: тільки при прогалинах/непокритих зонах) |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Таймаут discovery pipeline у секундах (1-300) |

Встановіть `AI_REVIEWER_DISCOVERY_ENABLED` у `false`, щоб повністю пропустити discovery. Рецензент все одно працюватиме, але без контексту проєкту.

```yaml
# GitHub Actions — вимкнути discovery
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    discovery_enabled: 'false'
```

---

## Тихий режим (Silent Mode)

Коментар discovery **не поститься** коли:

1. **`.reviewbot.md` існує** у репозиторії — бот вважає, що ви вже налаштували його.
2. **Прогалин та непокритих зон не знайдено** — все Well Covered, немає питань.
3. **Виявлення дублікатів** — коментар discovery вже був запостений у цьому PR/MR.

У всіх трьох випадках discovery все одно працює і збагачує промпт рецензії — просто не постить видимий коментар.

---

## FAQ

### Чи можу я вимкнути discovery?

Так. Встановіть `AI_REVIEWER_DISCOVERY_ENABLED=false`. Рецензент працюватиме без контексту проєкту — так само, як до появи функції Discovery.

### Чи коштує discovery додаткові LLM токени?

При **першому запуску**: рівні 0-2 безкоштовні (API виклики та локальний парсинг). Рівень 3 (LLM інтерпретація) викликається лише коли перших трьох рівнів недостатньо — зазвичай 50-200 токенів, що мізерно порівняно із самим ревʼю (~1 500 токенів).

При **наступних запусках**: якщо ваші watch-files не змінились, discovery використовує **кешований результат** і коштує **0 токенів**.

### Чи можу я редагувати автоматично згенерований `.reviewbot.md`?

Так, безумовно. Файл розроблений для ручного редагування. Змінюйте що завгодно — парсер толерантний до додаткового контенту та відсутніх секцій.

### Чи запускається discovery на кожному PR?

Discovery збагачує промпт рецензії на кожному PR. **LLM виклик** кешується через watch-files (0 токенів, коли файли не змінились). **Коментар discovery** поститься лише один раз (виявлення дублікатів запобігає повторним постам).

### Як побачити всі зони, включаючи Well Covered?

Встановіть `AI_REVIEWER_DISCOVERY_VERBOSE=true`. Це змушує коментар discovery завжди поститися і включає всі зони (Well Covered, Weakly Covered, Not Covered).

### Що робити, якщо discovery працює надто довго?

Встановіть `AI_REVIEWER_DISCOVERY_TIMEOUT` на більше значення (default: 30 секунд, max: 300). Якщо discovery перевищує таймаут, ревʼю продовжується без контексту discovery.

---

## Наступний крок

- [Конфігурація →](configuration.md)
- [GitHub інтеграція →](github.md)
- [GitLab інтеграція →](gitlab.md)
