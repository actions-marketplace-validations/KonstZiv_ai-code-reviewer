# CLI Reference

Довідник команд AI Code Reviewer.

---

## Основна команда

```bash
ai-review [OPTIONS]
```

**Поведінка:**

- В CI (GitHub Actions / GitLab CI) — автоматично визначає контекст
- Вручну — потрібно вказати `--provider`, `--repo`, `--pr`

!!! info "Subcommands"
    `ai-review` (без subcommand) запускає ревʼю — зворотно сумісно. `ai-review discover` — standalone discovery.

---

## Опції

| Опція | Скорочено | Опис | Default |
|-------|-----------|------|---------|
| `--provider` | `-p` | CI провайдер | Auto-detect |
| `--repo` | `-r` | Репозиторій (owner/repo) | Auto-detect |
| `--pr` | | Номер PR/MR | Auto-detect |
| `--help` | | Показати допомогу | |
| `--version` | | Показати версію | |

---

## Провайдери

| Значення | Опис |
|----------|------|
| `github` | GitHub (GitHub Actions) |
| `gitlab` | GitLab (GitLab CI) |

---

## Приклади використання

### В CI (автоматично)

```bash
# GitHub Actions — все автоматично
ai-review

# GitLab CI — все автоматично
ai-review
```

### Вручну для GitHub

```bash
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token

ai-review --provider github --repo owner/repo --pr 123
```

<small>
**Де взяти значення:**

- `--repo` — з URL репозиторію: `github.com/owner/repo` → `owner/repo`
- `--pr` — номер з URL: `github.com/owner/repo/pull/123` → `123`
</small>

### Вручну для GitLab

```bash
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITLAB_TOKEN=your_token

ai-review --provider gitlab --repo owner/repo --pr 456
```

<small>
**Де взяти значення:**

- `--repo` — project path з URL: `gitlab.com/group/project` → `group/project`
- `--pr` — номер MR з URL: `gitlab.com/group/project/-/merge_requests/456` → `456`
</small>

### Скорочений синтаксис

```bash
ai-review -p github -r owner/repo --pr 123
```

---

## Environment Variables

CLI читає конфігурацію з environment variables:

### Обов'язкові

| Змінна | Опис |
|--------|------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API ключ |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub токен (для GitHub) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab токен (для GitLab) |

!!! tip "Fallback"
    Старі назви без префіксу (наприклад, `GOOGLE_API_KEY`) все ще працюють як fallback.

### Опціональні

| Змінна | Опис | Default |
|--------|------|---------|
| `AI_REVIEWER_LANGUAGE` | Мова відповідей | `en` |
| `AI_REVIEWER_LANGUAGE_MODE` | Режим мови | `adaptive` |
| `AI_REVIEWER_GEMINI_MODEL` | Модель Gemini | `gemini-2.5-flash` |
| `AI_REVIEWER_LOG_LEVEL` | Рівень логування | `INFO` |
| `AI_REVIEWER_GITLAB_URL` | URL GitLab | `https://gitlab.com` |

:point_right: [Повний список →](configuration.md)

---

## Auto-detection

### GitHub Actions

CLI автоматично використовує:

| Змінна | Опис |
|--------|------|
| `GITHUB_ACTIONS` | Визначення середовища |
| `GITHUB_REPOSITORY` | owner/repo |
| `GITHUB_EVENT_PATH` | JSON з деталями PR |
| `GITHUB_REF` | Fallback для PR номера |

### GitLab CI

CLI автоматично використовує:

| Змінна | Опис |
|--------|------|
| `GITLAB_CI` | Визначення середовища |
| `CI_PROJECT_PATH` | owner/repo |
| `CI_MERGE_REQUEST_IID` | Номер MR |
| `CI_SERVER_URL` | URL GitLab |

---

## Exit Codes

| Код | Опис |
|-----|------|
| `0` | Успіх |
| `1` | Помилка (конфігурація, API, тощо) |

---

## Логування

### Рівні

| Рівень | Опис |
|--------|------|
| `DEBUG` | Детальна інформація для debugging |
| `INFO` | Загальна інформація (default) |
| `WARNING` | Попередження |
| `ERROR` | Помилки |
| `CRITICAL` | Критичні помилки |

### Налаштування

```bash
export AI_REVIEWER_LOG_LEVEL=DEBUG
ai-review
```

### Вивід

CLI використовує [Rich](https://rich.readthedocs.io/) для форматованого виводу:

```
[12:34:56] INFO     Detected CI Provider: github
[12:34:56] INFO     Context extracted: owner/repo PR #123
[12:34:57] INFO     Fetching PR diff...
[12:34:58] INFO     Analyzing code with Gemini...
[12:35:02] INFO     Review completed successfully
```

---

## Помилки

### Configuration Error

```
Configuration Error: GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Причина:** Невалідна конфігурація.

**Рішення:** Перевірте environment variables.

### Context Error

```
Context Error: Could not determine PR number from GitHub Actions context.
```

**Причина:** Workflow не запущено для PR.

**Рішення:** Переконайтесь що workflow має `on: pull_request`.

### Provider not detected

```
Error: Could not detect CI environment.
Please specify --provider, --repo, and --pr manually.
```

**Причина:** Запуск поза CI.

**Рішення:** Вкажіть всі параметри вручну.

---

## Команда Discover

Запуск project discovery окремо (без створення ревʼю):

```bash
ai-review discover <REPO> [OPTIONS]
```

### Аргументи

| Аргумент | Опис |
|----------|------|
| `REPO` | Репозиторій (owner/repo) |

### Опції

| Опція | Скорочено | Опис | Default |
|-------|-----------|------|---------|
| `--provider` | `-p` | Git провайдер | `github` |
| `--json` | | Вивід у JSON | `false` |
| `--verbose` | `-v` | Показати всі деталі (conventions, CI інструменти, watch-files) | `false` |

### Приклади

```bash
# GitHub репозиторій
ai-review discover owner/repo

# JSON вивід
ai-review discover owner/repo --json

# Verbose режим
ai-review discover owner/repo -v

# GitLab проєкт
ai-review discover group/project -p gitlab
```

### Приклад виводу

```
🔍 Discovering project context...

Stack: Python (FastAPI) 3.13, uv
CI: ✅ .github/workflows/tests.yml — ruff, mypy, pytest

Attention Zones:
  ✅ Formatting — ruff format in CI
  ✅ Type checking — mypy --strict in CI
  ❌ Security scanning — No security scanner detected
  ⚠️ Test coverage — no coverage threshold
```

---

## Docker

Запуск через Docker:

```bash
docker run --rm \
  -e AI_REVIEWER_GOOGLE_API_KEY=your_key \
  -e AI_REVIEWER_GITHUB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --provider github \
  --repo owner/repo \
  --pr 123
```

---

## Версія

```bash
ai-review --version
```

```
AI Code Reviewer 0.1.0
```

---

## Допомога

```bash
ai-review --help
```

```
Usage: ai-review [OPTIONS]

  Run AI Code Reviewer.

  Automatically detects CI environment and reviews the current Pull Request.
  Can also be run manually by providing arguments.

Options:
  -p, --provider [github|gitlab]  CI provider (auto-detected if not provided)
  -r, --repo TEXT                 Repository name (e.g. owner/repo). Auto-detected in CI.
  --pr INTEGER                    Pull Request number. Auto-detected in CI.
  --help                          Show this message and exit.
```

---

## Наступний крок

- [Troubleshooting →](troubleshooting.md)
- [Приклади →](examples/index.md)
