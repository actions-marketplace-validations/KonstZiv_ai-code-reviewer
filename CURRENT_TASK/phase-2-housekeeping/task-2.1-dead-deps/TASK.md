# Task 2.1: Remove Dead Dependencies

## Тип: Cleanup | Пріоритет: HIGH | Estimate: 20min

## Для борди

Видалити `[project.optional-dependencies] all-providers` group і порожній `agents/` package.

## Implementation

### `pyproject.toml`

**Видалити повністю:**
```toml
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

**Перевірити mypy config:** якщо є `[[tool.mypy.overrides]]` для langchain/anthropic — теж видалити:
```toml
# Видалити якщо є:
[[tool.mypy.overrides]]
module = ["anthropic.*", "langchain.*", ...]
```

### `src/ai_reviewer/agents/__init__.py`

Видалити весь `agents/` package (порожній `__init__.py`).

### `uv.lock`

Після видалення optional deps: `uv lock` для оновлення lock file.

## Checklist

- [ ] Видалити `all-providers` з pyproject.toml
- [ ] Видалити mypy overrides для langchain/anthropic/openai
- [ ] Видалити `src/ai_reviewer/agents/` directory
- [ ] `uv lock` → оновити lock file
- [ ] `make check` passes
- [ ] `docker build -t test .` succeeds
