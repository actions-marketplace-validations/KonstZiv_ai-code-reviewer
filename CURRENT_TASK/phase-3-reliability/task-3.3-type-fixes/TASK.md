# Task 3.3: Fix type: ignore in Orchestrator

## Тип: Code Quality | Пріоритет: LOW | Estimate: 30min

## Для борди

5 місць `# type: ignore[arg-type]` в `_merge_ci_insights()`. Причина: `_first_non_none()` повертає `str | int | None`, але caller очікує `str | None` або `int | None`.

## Implementation

### Рішення: typed overloads або окремі helper functions

**Варіант A (простий):** Два окремих helper замість одного generic:

```python
def _first_non_none_str(*values: str | None) -> str | None:
    for v in values:
        if v is not None:
            return v
    return None

def _first_non_none_int(*values: int | None) -> int | None:
    for v in values:
        if v is not None:
            return v
    return None
```

**Варіант B (generic з TypeVar):**

```python
from typing import TypeVar

_T = TypeVar("_T")

def _first_non_none(*values: _T | None) -> _T | None:
    for v in values:
        if v is not None:
            return v
    return None
```

Проблема варіанту B: mypy може не вивести T з generator expression.

**Рекомендація: Варіант A** — простий, explicit, zero mypy issues.

### Caller site fix:

```python
return CIInsights(
    # ...
    python_version=_first_non_none_str(*(r.python_version for r in results)),
    node_version=_first_non_none_str(*(r.node_version for r in results)),
    go_version=_first_non_none_str(*(r.go_version for r in results)),
    package_manager=_first_non_none_str(*(r.package_manager for r in results)),
    min_coverage=_first_non_none_int(*(r.min_coverage for r in results)),
)
```

## Checklist

- [ ] Замінити `_first_non_none` на typed variants
- [ ] Видалити всі `type: ignore[arg-type]`
- [ ] `mypy --strict` passes
- [ ] `make check` passes
