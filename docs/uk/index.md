# AI ReviewBot

**AI-асистент для автоматичного code review у вашому CI/CD pipeline.**

---

## Що це?

AI Code Reviewer — інструмент, який автоматично аналізує ваші Pull Requests (GitHub) та Merge Requests (GitLab), знаходить проблеми та пропонує виправлення з кнопкою **"Apply Suggestion"**.
Фактично Ви отримуєте незаангажований погляд senior developer на Ваш код і поради як його покращити.

Можлива інтеграція з широким набором існуючих LLM провайдерів (за замовчуванням  **Google Gemini**, модель **gemini-2.5-flash** (на момент виходу поточного релізу - безкоштовного варіанту використання - Free Tier - що обмежує кількість запитів за хвилину і за день - цілком достатньо для нормального робочого процесу команди 4-8 full time розробників)).


---

## Що ви отримуєте?


- :white_check_mark: **Code Comments** — загальна оцінка коду та рекомендації
- :white_check_mark: **Task Alignment** — відповідність PR/MR контексту завдання
- :white_check_mark: **Inline Comments** — коментарі прямо до рядків коду
- :white_check_mark: **Apply Suggestion** — одна кнопка для застосування виправлення
- :white_check_mark: **Менторські пояснення** — чому це важливо + посилання на ресурси
- :white_check_mark: **Мовна адаптивність** — визначає мову з контексту PR/MR
- :white_check_mark: **Метрики** — час виконання, токени
- :white_check_mark: **Стійкість** — retry logic для 429/5xx помилок

---

## Швидкий старт

Важливо: для реалізації подальших кроків Вам знадобиться Ваш особистий Google API key. Отримати його можна безкоштовно або в [Google AI Studio](https://aistudio.google.com/api-keys) або в [Google Cloud Console](https://console.cloud.google.com/).

*AI Code Reviewer може бути налаштований для використання різних LLM провайдерів і моделей, як безкоштовних у використанні, так і платних. В наступних прикладах використовується модель* **gemini-2.5-flash** *В інших розділах документації пояснюється як підключити інших провадерів і використовувати інші моделі. Нам цікава Ваша думка про різницю у використанні різних моделей - будем раді читати в коментарях про Ваш досвід.*


### GitHub


У Вашому репозиторії створіть:
- в розділі `settings` -> `Secrets and variables[Security]` -> `Actions` -> press `New repository sectet`:
    - створіть secret з назвою `GOOGLE_API_KEY` і значенням Вашого Google API key.
- в корені проєкту репозиторія:
    - створіть файл `.github/workflows/ai-review.yml` наступного вмісту:

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### GitLab

У Вашому репозиторії створіть:
- в розділі `settings` -> `CI/CD` -> `Variables` -> `CI/CD Variables` -> press `Add variable`:
    - `Type`: Variable (default)
    - `Visibility`: Masked (щоб не відображалась в логах)
    - `Key`: GOOGLE_API_KEY
    - `Value`: значенням Вашого Google API key
- в корені репозиторію проєкту:
    - створіть файл `.gitlab-ci.yml` наступного вмісту:

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-reviewbot:latest
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

:point_right: [Детальніше →](quick-start.md)


Створіть новий PR/MR - отрмайте ревью.

**Якість ревью напряму залежить від розуміння AI Code Reviewer Ваших намірів** (як і реального "живого" ревʼювера). Тому хорошою ідеєю буде супроводжувати процес розробки документуванням:
- створити issue з описом проблеми і бажаними результатами
- створити в issue повʼязану гілку/повʼязаний PR/MR, в якому описати детальніше проблему, шлях вирішення, обмеження, бажані результати, особливі випадки - будь що що додає розуміння контексту, інструментів, результатів
- якщо ви працюєте командою - то спілкуйтесь в issue, коментуйте PR/MR - все це додає контекст і підвищує якість ревʼю

---

## Підтримувані платформи

| Платформа | Статус | Інтеграція |
|-----------|--------|------------|
| **GitHub** | :white_check_mark: | GitHub Actions / GitHub Action |
| **GitLab** | :white_check_mark: | GitLab CI / Docker image |
| **Self-hosted** | :white_check_mark: | Docker / PyPI |

---

## Як це працює?

```mermaid
graph TD
    A[PR/MR створено] --> B[CI запускає AI Review]
    B --> C[Отримання diff + контексту]
    C --> D[Аналіз через Gemini]
    D --> E[Публікація Inline Comments]
    E --> F[Кнопка Apply Suggestion]
```

**Крок за кроком:**

1. Ви створюєте PR/MR
2. CI pipeline запускає AI Code Reviewer
3. Інструмент отримує diff, опис PR, linked task
4. Gemini аналізує код та генерує рекомендації
5. Результат публікується як inline comments з кнопкою "Apply"

---

## Приклад review

!!! danger "🔴 CRITICAL: Hardcoded Secret"
    **Файл:** `config.py:15`

    Знайдено захардкоджений API ключ у коді.

    ```suggestion
    API_KEY = os.getenv("API_KEY")
    ```

    ??? info "Чому це важливо?"
        Секрети в коді потрапляють у git історію і можуть бути викрадені.
        Використовуйте environment variables або secret managers.

        :link: [OWASP: Hardcoded Credentials](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password)

---

## Категорії проблем

| Категорія | Опис |
|-----------|------|
| :lock: **Security** | Вразливості, секрети в коді |
| :memo: **Code Quality** | Читабельність, naming, DRY |
| :building_construction: **Architecture** | SOLID, design patterns |
| :zap: **Performance** | N+1, неефективні алгоритми |
| :test_tube: **Testing** | Покриття, edge cases |

---

## Встановлення

=== "Docker (рекомендовано)"

    ```bash
    docker pull ghcr.io/konstziv/ai-reviewbot:latest
    ```

=== "PyPI"

    ```bash
    pip install ai-reviewbot
    ```

=== "Source"

    ```bash
    git clone https://github.com/KonstZiv/ai-code-reviewer.git
    cd ai-code-reviewer
    uv sync
    ```

:point_right: [Детальніше →](installation.md)

---

## Конфігурація

Мінімальна конфігурація — тільки API ключ:

```bash
export GOOGLE_API_KEY=your_api_key
```

Додаткові опції:

| Змінна | Опис | Default |
|--------|------|---------|
| `LANGUAGE` | Мова відповідей (ISO 639) | `en` |
| `LANGUAGE_MODE` | `adaptive` / `fixed` | `adaptive` |
| `GEMINI_MODEL` | Модель Gemini | `gemini-2.0-flash` |
| `LOG_LEVEL` | Рівень логування | `INFO` |

:point_right: [Всі опції →](configuration.md)

---

## Документація

<div class="grid cards" markdown>

-   :rocket: **[Швидкий старт](quick-start.md)**

    Copy-paste інструкції для GitHub та GitLab

-   :gear: **[Конфігурація](configuration.md)**

    Всі environment variables та опції

-   :octicons-mark-github-16: **[GitHub](github.md)**

    Permissions, secrets, workflow tips

-   :simple-gitlab: **[GitLab](gitlab.md)**

    Job tokens, MR triggers, self-hosted

-   :material-console: **[CLI Reference](api.md)**

    Команди та параметри

-   :material-lifebuoy: **[Troubleshooting](troubleshooting.md)**

    FAQ та вирішення проблем

</div>

---

## Вартість

AI Code Reviewer використовує **Google Gemini 2.5 Flash** — в режимі Free Tire. Обмеження (на дату релізу) 500 RPD. Цього цілком достатньо для обслуговування PR/MR команди з 4 - 8 full time розробників з врахуванням як ревʼю так і змістовних коментарів (без flood та off-top).
Якщо використовувати платний рівень використання (Pay-as-you-go), то вартість умовного ревʼю і необмежених бесід:

| Метрика | Вартість            |
|---------|---------------------|
| Input tokens | $0.30 / 1M          |
| Output tokens | $2.5 / 1M           |
| **Типовий review** | **~$0.003 - $0.01** |

:bulb: ~1000 reviews = ~$3 ... ~$10

---

## Ліцензія

Apache 2.0 — вільне використання, модифікація та розповсюдження.

---

## Підтримка

- :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — баги та пропозиції
- :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — питання та обговорення

---

**Готові покращити свої code reviews?** :point_right: [Почати →](quick-start.md)
