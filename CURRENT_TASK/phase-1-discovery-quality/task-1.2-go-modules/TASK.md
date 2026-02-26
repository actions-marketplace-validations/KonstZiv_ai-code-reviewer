# Task 1.2: Go Modules Detection in CI Analyzer

## Тип: Enhancement | Пріоритет: MEDIUM | Estimate: 30min

## Опис (для борди)

`CIPipelineAnalyzer` не розпізнає Go modules як package manager.
Коли Go проєкт має `.gitlab-ci.yml` з `go test`, `go vet` — поле `package_manager` залишається `None`.

**Acceptance Criteria:**
- [ ] `go mod`, `go build`, `go test` → `package_manager = "go modules"`
- [ ] Fixture `go_gitlab/expected_profile.json` оновлений
- [ ] Existing tests pass

## Залежності: немає | Блокує: нічого критичного

---

# Implementation Guide

## Що змінити

### `discovery/ci_analyzer.py`

Додати Go-specific patterns до `_TOOL_PATTERNS` або додати detection в `_detect_package_manager()`.

```python
# Варіант 1: додати до _TOOL_PATTERNS (якщо go test ще не матчиться)
# Вже є: ("go\\s+test", "go test", ToolCategory.TESTING)
# Потрібно додати detection в package manager

# В функції _detect_package_manager або _detect_versions:
_GO_MODULE_PATTERNS = (
    r"go\s+mod\b",
    r"go\s+build\b",
    r"go\s+test\b",
    r"go\s+vet\b",
    r"go\s+install\b",
)

def _detect_go_package_manager(content: str) -> str | None:
    """Detect Go modules from CI commands."""
    for pattern in _GO_MODULE_PATTERNS:
        if re.search(pattern, content):
            return "go modules"
    return None
```

### `tests/fixtures/discovery/go_gitlab/expected_profile.json`

Оновити `package_manager: null` → `package_manager: "go modules"`.

## Checklist

- [ ] Додати Go modules detection в CI analyzer
- [ ] Оновити `go_gitlab` fixture
- [ ] `make check` passes
