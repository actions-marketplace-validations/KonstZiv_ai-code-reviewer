# GitLab

Детальний гайд для інтеграції з GitLab CI.

---

## Токен доступу {#tokens}

### Project Access Token {#get-token}

Для роботи AI Reviewer потрібен **Project Access Token** з правами на створення коментарів.

!!! note "Потрібні права Maintainer"
    Для створення Project Access Token потрібна роль **Maintainer** або **Owner** у проєкті.

    :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

**Створення токена:**

1. Відкрийте проєкт → `Settings` → `Access Tokens`
2. Натисніть **Add new token**
3. Заповніть форму:

| Поле | Значення |
|------|----------|
| **Token name** | `ai-reviewer` |
| **Expiration date** | Оберіть дату (макс. 1 рік) |
| **Role** | `Developer` |
| **Scopes** | :white_check_mark: `api` |

4. Натисніть **Create project access token**
5. **Скопіюйте токен** — він показується лише один раз!

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # З CI/CD Variables
```

!!! warning "Збережіть токен"
    GitLab показує токен **лише один раз**. Збережіть його одразу.

:material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

---

## CI/CD Variables

### Додавання змінних

`Settings → CI/CD → Variables → Add variable`

| Змінна | Значення | Опції |
|--------|----------|-------|
| `GOOGLE_API_KEY` | Gemini API ключ | Masked |
| `GITLAB_TOKEN` | Project Access Token | Masked |

!!! tip "Masked"
    Завжди вмикайте **Masked** для секретів — вони не будуть показані в логах.

---

## Triggers

### Рекомендований trigger

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Це запускає job тільки для Merge Request pipelines.

### Альтернативний trigger (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — новіший синтаксис, рекомендований GitLab.

---

## Job приклади

### Мінімальний

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
```

### Повний (рекомендовано)

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
  interruptible: true
```

**Що робить:**

- `allow_failure: true` — MR не блокується якщо review failed
- `timeout: 10m` — максимум 10 хвилин
- `interruptible: true` — можна скасувати при новому коміті

### З кастомним stage

```yaml
stages:
  - test
  - review
  - deploy

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  needs: []  # Не чекати на попередні stages
```

---

## Self-hosted GitLab

### Конфігурація

```yaml
variables:
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
```

### Docker registry

Якщо ваш GitLab не має доступу до `ghcr.io`, створіть mirror:

```bash
# На машині з доступом
docker pull ghcr.io/konstziv/ai-code-reviewer:1
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
docker push gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

```yaml
ai-review:
  image: gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

---

## GitLab CI змінні

AI Code Reviewer автоматично використовує:

| Змінна | Опис |
|--------|------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | Номер MR |
| `CI_SERVER_URL` | URL GitLab |

Вам не потрібно передавати `--project` та `--mr-iid` — вони беруться з CI автоматично.

---

## Результат review

### Notes (коментарі)

AI Review публікує коментарі до MR як notes.

### Discussions (inline)

Для inline коментарів потрібен Project Access Token з scope `api`.

Inline коментарі з'являються безпосередньо біля рядків коду в diff view.

### Summary

В кінці review публікується Summary note з:

- Загальною статистикою
- Метриками
- Good practices

---

## Troubleshooting

### Review не постить коментарі

**Перевірте:**

1. `GOOGLE_API_KEY` змінна встановлена
2. `GITLAB_TOKEN` має достатньо прав (scope: `api`)
3. Pipeline запущено для MR (не для гілки)

### "401 Unauthorized"

**Причина:** Невалідний токен.

**Рішення:**

- Перевірте що токен не expired
- Перевірте scope (потрібен `api`)

### "403 Forbidden"

**Причина:** Недостатньо прав.

**Рішення:**

- Використовуйте Project Access Token з scope `api`
- Перевірте що токен має доступ до проєкту

### "404 Not Found"

**Причина:** MR не знайдено.

**Рішення:**

- Перевірте що pipeline запущено для MR
- Перевірте `CI_MERGE_REQUEST_IID`

### Rate limit (429)

**Причина:** Перевищено ліміт API.

**Рішення:**

- AI Code Reviewer автоматично retry з backoff
- Якщо постійно — зачекайте або збільште ліміти

---

## Best practices

### 1. Використовуйте PAT для повної функціональності

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Project Access Token
```

### 2. Додайте allow_failure

```yaml
allow_failure: true
```

MR не буде заблоковано якщо review failed.

### 3. Встановіть timeout

```yaml
timeout: 10m
```

### 4. Зробіть job interruptible

```yaml
interruptible: true
```

При новому коміті старий review буде скасовано.

### 5. Не чекайте на інші stages

```yaml
needs: []
```

Review запуститься одразу, не чекаючи на build/test.

---

## Наступний крок

- [GitHub інтеграція →](github.md)
- [CLI Reference →](api.md)
