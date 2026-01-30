# Швидкий старт

Запустіть AI Code Reviewer за 5 хвилин на GitHub або GitLab.

---

## Крок 1: Отримайте API ключ

Для роботи AI Reviewer потрібен ключ Google Gemini API.

1. Перейдіть на [Google AI Studio](https://aistudio.google.com/)
2. Увійдіть з Google акаунтом
3. Натисніть **"Get API key"** → **"Create API key"**
4. Скопіюйте ключ (він починається з `AIza...`)

!!! warning "Збережіть ключ"
    Ключ показується лише один раз. Збережіть його в безпечному місці.

!!! tip "Безкоштовний рівень"
    Gemini API має безкоштовний рівень: 15 запитів на хвилину, достатньо для більшості проєктів.

---

## Крок 2: Додайте ключ у середовище репозиторію

Ключ потрібно додати як секретну змінну у вашому репозиторії.

=== "GitHub"

    **Шлях:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    | Поле | Значення |
    |------|----------|
    | **Name** | `GOOGLE_API_KEY` |
    | **Secret** | Ваш ключ (`AIza...`) |

    Натисніть **"Add secret"**.

    ??? info "Детальна інструкція з скріншотами"
        1. Відкрийте ваш репозиторій на GitHub
        2. Натисніть **Settings** (шестерня у верхньому меню)
        3. У лівому меню знайдіть **Secrets and variables** → **Actions**
        4. Натисніть зелену кнопку **New repository secret**
        5. У полі **Name** введіть: `GOOGLE_API_KEY`
        6. У полі **Secret** вставте ваш ключ
        7. Натисніть **Add secret**

    :material-book-open-variant: [Офіційна документація GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Для GitLab потрібно створити **Project Access Token** та додати дві змінні.

    ### Крок 2a: Створіть Project Access Token

    !!! note "Потрібні права Maintainer"
        Для створення Project Access Token потрібна роль **Maintainer** або **Owner** у проєкті.

        :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

    **Шлях:** Project → `Settings` → `Access Tokens`

    | Поле | Значення |
    |------|----------|
    | **Token name** | `ai-reviewer` |
    | **Expiration date** | Оберіть дату (макс. 1 рік) |
    | **Role** | `Developer` |
    | **Scopes** | :white_check_mark: `api` |

    Натисніть **"Create project access token"** → **Скопіюйте токен** (показується лише раз!)

    :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Крок 2b: Додайте змінні в CI/CD

    **Шлях:** Project → `Settings` → `CI/CD` → `Variables`

    Додайте **дві** змінні:

    | Key | Value | Flags |
    |-----|-------|-------|
    | `GOOGLE_API_KEY` | Ваш Gemini ключ (`AIza...`) | :white_check_mark: Mask variable |
    | `GITLAB_TOKEN` | Токен з кроку 2a | :white_check_mark: Mask variable |

    ??? info "Детальна інструкція"
        1. Відкрийте ваш проєкт на GitLab
        2. Перейдіть **Settings** → **CI/CD**
        3. Розгорніть секцію **Variables**
        4. Натисніть **Add variable**
        5. Додайте `GOOGLE_API_KEY`:
            - Key: `GOOGLE_API_KEY`
            - Value: ваш Gemini API ключ
            - Flags: Mask variable ✓
        6. Натисніть **Add variable**
        7. Повторіть для `GITLAB_TOKEN`:
            - Key: `GITLAB_TOKEN`
            - Value: токен з кроку 2a
            - Flags: Mask variable ✓

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Крок 3: Додайте AI Review у CI {#ci-setup}

=== "GitHub"

    ### Варіант A: Новий workflow файл

    Якщо ви ще не використовуєте GitHub Actions, або хочете окремий файл для AI Review:

    1. Створіть папку `.github/workflows/` в корені репозиторію (якщо не існує)
    2. Створіть файл `ai-review.yml` в цій папці
    3. Скопіюйте цей код:

    ```yaml
    name: AI Code Review

    on:
      pull_request:
        types: [opened, synchronize, reopened]

    concurrency:
      group: ai-review-${{ github.event.pull_request.number }}
      cancel-in-progress: true

    jobs:
      review:
        runs-on: ubuntu-latest
        # Не запускати для fork PRs (немає доступу до secrets)
        if: github.event.pull_request.head.repo.full_name == github.repository
        permissions:
          contents: read
          pull-requests: write

        steps:
          - uses: KonstZiv/ai-code-reviewer@v1
            with:
              github_token: ${{ secrets.GITHUB_TOKEN }}
              google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    ```

    !!! info "Про `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` — це **автоматичний токен**, який GitHub створює для кожного workflow run. Його **не потрібно** додавати в secrets вручну — він вже доступний.

        Права токена визначаються секцією `permissions` у workflow файлі.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

    4. Закомітьте та запуште файл

    ### Варіант B: Додати до існуючого workflow

    Якщо ви вже маєте `.github/workflows/` з іншими jobs, додайте цей job до існуючого файлу:

    ```yaml
    # Додайте цей job до вашого існуючого workflow файлу
    ai-review:
      runs-on: ubuntu-latest
      if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository
      permissions:
        contents: read
        pull-requests: write
      steps:
        - uses: KonstZiv/ai-code-reviewer@v1
          with:
            github_token: ${{ secrets.GITHUB_TOKEN }}
            google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    ```

    !!! note "Перевірте triggers"
        Переконайтесь, що ваш workflow має `on: pull_request` серед тригерів.

=== "GitLab"

    ### Варіант A: Новий CI файл

    Якщо у вас ще немає `.gitlab-ci.yml`:

    1. Створіть файл `.gitlab-ci.yml` в корені репозиторію
    2. Скопіюйте цей код:

    ```yaml
    stages:
      - review

    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review
      script:
        - ai-review
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      allow_failure: true
      variables:
        GITLAB_TOKEN: $GITLAB_TOKEN
        GOOGLE_API_KEY: $GOOGLE_API_KEY
    ```

    3. Закомітьте та запуште файл

    ### Варіант B: Додати до існуючого CI

    Якщо у вас вже є `.gitlab-ci.yml`:

    1. Додайте `review` до списку `stages` (якщо потрібен окремий stage)
    2. Додайте цей job:

    ```yaml
    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review  # або test, або інший існуючий stage
      script:
        - ai-review
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      allow_failure: true
      variables:
        GITLAB_TOKEN: $GITLAB_TOKEN
        GOOGLE_API_KEY: $GOOGLE_API_KEY
    ```

---

## Крок 4: Перевірте результат

Тепер AI Review буде запускатись автоматично при:

| Платформа | Подія |
|-----------|-------|
| **GitHub** | Створення PR, нові коміти в PR, reopening PR |
| **GitLab** | Створення MR, нові коміти в MR |

### Що ви побачите

Після завершення CI job, в PR/MR з'являться:

- **Inline коментарі** — прив'язані до конкретних рядків коду
- **Кнопка "Apply suggestion"** — для швидкого застосування виправлень (GitHub)
- **Summary коментар** — загальний огляд з метриками

Кожен коментар містить:

- :red_circle: / :yellow_circle: / :blue_circle: Severity badge
- Опис проблеми
- Пропозицію виправлення
- Collapsible секцію "Чому це важливо?"

---

## Troubleshooting

### Review не з'являється?

Перевірте чеклист:

- [ ] `GOOGLE_API_KEY` доданий як секрет?
- [ ] `github_token` передано явно? (для GitHub)
- [ ] CI job завершився успішно? (перевірте логи)
- [ ] Для GitHub: є `permissions: pull-requests: write`?
- [ ] Для fork PRs: секрети недоступні — це очікувана поведінка

### В логах показує `--help`?

Це означає, що CLI не отримав необхідні параметри. Перевірте:

- Чи передано `github_token` / `GITLAB_TOKEN` явно
- Чи правильний формат YAML (відступи!)

### Rate limit?

Gemini free tier: 15 запитів на хвилину. Зачекайте хвилину та спробуйте знову.

:point_right: [Всі проблеми та рішення →](troubleshooting.md)

---

## Що далі?

| Задача | Документ |
|--------|----------|
| Налаштувати мову відповідей | [Конфігурація](configuration.md) |
| Розширені налаштування GitHub | [GitHub Guide](github.md) |
| Розширені налаштування GitLab | [GitLab Guide](gitlab.md) |
| Приклади workflows | [Приклади](examples/index.md) |
