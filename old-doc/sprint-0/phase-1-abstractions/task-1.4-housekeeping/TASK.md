# Task 1.4: Housekeeping

| Поле | Значення |
|------|----------|
| **Фаза** | 1 — Abstractions |
| **Оцінка** | 2-3 години |
| **Залежності** | 1.1 (GeminiProvider) |
| **Блокує** | — |
| **Файли** | `pyproject.toml`, `gitlab.py`, `integrations/gemini.py` |

---

## Що робимо

Технічний борг: прибрати невикористані залежності, виправити N+1 у GitLab,
прибрати повторне створення GeminiClient.

## Очікуваний результат

- pyproject.toml: langchain-*/anthropic/openai в `[project.optional-dependencies]`
- GitLab: `mr.changes()` замість `diffs.list()` + `diffs.get()`
- Docker image менший
- `pip install` швидший

## Як перевірити

```bash
make check
# Docker build time повинен зменшитись
```
