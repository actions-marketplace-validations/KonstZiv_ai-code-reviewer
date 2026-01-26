# Встановлення

Три способи встановлення AI Code Reviewer.

---

## Docker (рекомендовано)

Найпростіший спосіб — використовуйте готовий Docker image:

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:latest
```

**Перевірка:**

```bash
docker run --rm ghcr.io/konstziv/ai-code-reviewer:latest --help
```

**Запуск:**

```bash
docker run --rm \
  -e GOOGLE_API_KEY=your_api_key \
  -e GITHUB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:latest \
  --repo owner/repo --pr-number 123
```

!!! tip "Docker images"
    - `ghcr.io/konstziv/ai-code-reviewer:latest` — GitHub Container Registry
    - `konstziv/ai-code-reviewer:latest` — DockerHub

---

## PyPI

Встановлення через pip:

```bash
pip install ai-code-reviewer
```

**Перевірка:**

```bash
ai-review --help
```

!!! note "Python версія"
    Потрібен Python **3.13+**

---

## Source (для розробників)

Клонування та встановлення з репозиторію:

```bash
# Клонувати репозиторій
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Встановити залежності (використовуємо uv)
uv sync

# Перевірити
uv run ai-review --help
```

!!! info "uv"
    Ми використовуємо [uv](https://github.com/astral-sh/uv) для керування залежностями.
    Встановити: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## Вимоги

### Системні

| Компонент | Вимога |
|-----------|--------|
| Python | 3.13+ |
| OS | Linux, macOS, Windows |
| RAM | 256MB+ |

### API ключі

Для роботи потрібен API ключ **Google Gemini**:

1. Перейдіть на [Google AI Studio](https://aistudio.google.com/)
2. Створіть API ключ
3. Збережіть як `GOOGLE_API_KEY`

!!! warning "Free tier"
    Google Gemini має безкоштовний tier з обмеженнями:

    - 15 RPM (requests per minute)
    - 1M tokens/day
    - 1500 requests/day

    Для більшості проєктів цього достатньо.

---

## Git провайдери

### GitHub

Для GitHub потрібен токен з правами `pull-requests: write`:

- В GitHub Actions: автоматичний `GITHUB_TOKEN`
- Локально: [створіть PAT](https://github.com/settings/tokens)

### GitLab

Для GitLab потрібен токен з правами `api`:

- В GitLab CI: автоматичний `CI_JOB_TOKEN`
- Локально: [створіть PAT](https://gitlab.com/-/profile/personal_access_tokens)

---

## Перевірка встановлення

Після встановлення перевірте:

```bash
# Версія
ai-review --version

# Допомога
ai-review --help

# Тестовий запуск (dry-run)
export GOOGLE_API_KEY=your_key
ai-review --help
```

---

## Наступний крок

:point_right: [Швидкий старт →](quick-start.md)
