# Task 1.4: Housekeeping — Implementation Guide

## 1. Залежності

### Поточний стан в pyproject.toml

```toml
dependencies = [
    "langchain>=1.2.6",            # НЕ використовується
    "langgraph>=1.0.6",            # НЕ використовується
    "langchain-anthropic>=1.3.1",  # НЕ використовується
    "langchain-openai>=1.1.7",     # НЕ використовується
    "langchain-google-genai>=4.2.0", # НЕ використовується
    "langchain-deepseek>=1.0.1",   # НЕ використовується
    "langchain-ollama>=1.0.1",     # НЕ використовується
    "anthropic>=0.76.0",           # НЕ використовується
    "openai>=2.15.0",              # НЕ використовується
    "google-genai>=1.59.0",        # ВИКОРИСТОВУЄТЬСЯ
    # ... інші
]
```

### Що зробити

```toml
dependencies = [
    "google-genai>=1.59.0",  # Gemini — основний LLM
    "PyGithub>=2.6.1",
    "python-gitlab>=5.6.0",
    "pydantic>=2.11.4",
    "pydantic-settings>=2.9.1",
    "typer>=0.15.3",
    "rich>=14.0.0",
    "tenacity>=9.1.2",
    "httpx>=0.28.1",
    "PyYAML>=6.0.2",
]

[project.optional-dependencies]
all-providers = [
    "langchain>=1.2.6",
    "langgraph>=1.0.6",
    "langchain-anthropic>=1.3.1",
    "langchain-openai>=1.1.7",
    "langchain-google-genai>=4.2.0",
    "langchain-deepseek>=1.0.1",
    "langchain-ollama>=1.0.1",
    "anthropic>=0.76.0",
    "openai>=2.15.0",
]
```

Оновити `uv.lock` після змін.

## 2. GitLab N+1

### Проблема

```python
# gitlab.py:213-215 — ЗАРАЗ
for diff in mr.diffs.list(iterator=True):       # N запитів
    diff_detail = mr.diffs.get(diff.id)          # ще N запитів
    for file_diff in diff_detail.diffs:
```

### Рішення

```python
# gitlab.py — ПІСЛЯ
changes = mr.changes()
for file_diff in changes["changes"]:
    # ...process file_diff
```

Один API-запит замість 2N.

## 3. GeminiClient ініціалізація

Після task 1.1 `integrations/gemini.py` використовує `GeminiProvider`.
Переконатись що provider створюється один раз у `reviewer.py` або `cli.py`.

---

## Чеклист

- [ ] pyproject.toml: невикористані deps → optional
- [ ] `uv.lock` оновлений
- [ ] GitLab diffs N+1 виправлено
- [ ] Docker build перевірений
- [ ] `make check` проходить
