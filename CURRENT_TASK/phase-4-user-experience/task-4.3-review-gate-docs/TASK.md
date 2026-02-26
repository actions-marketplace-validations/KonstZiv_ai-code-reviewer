# Task 4.3: Review Gate + Documentation Sync

## Тип: Documentation / QA | Пріоритет: HIGH | Estimate: 30min-1h

## Для борди

Фінальна верифікація Sprint Beta-0.5: `make check`, documentation sync, README update.

**Acceptance Criteria:**
- [ ] `make check` passes — zero warnings
- [ ] `docs/en/discovery.md` відповідає новому коду
- [ ] `docs/en/configuration.md` містить нові settings
- [ ] README.md оновлений з `ai-review discover`
- [ ] `sprint-beta-0-after-review.md` оновлений
- [ ] SPRINT.md має фінальні результати

---

# Implementation Guide

## 1. `make check`

```bash
make check  # lint + test
# Якщо fails → fix before proceeding
```

## 2. Documentation sync

### `docs/en/configuration.md`

Додати нові settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Discovery pipeline timeout (seconds) |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Always post discovery comment |

### `docs/en/discovery.md`

Оновити:
- Configuration table з новими settings
- Додати секцію "CLI: Standalone Discovery"
- Оновити "Silent Mode" з verbose option

### `docs/en/api.md`

Додати Discovery models API якщо відсутнє:
- `ProjectProfile.to_prompt_context()`
- `DiscoveryOrchestrator.discover()`
- Config parser public functions

## 3. README.md

Додати в Quick Start або Features:

```markdown
### Standalone Discovery

Test what the bot learns about your project:

```bash
ai-review discover owner/repo
ai-review discover owner/repo --json
```
```

## 4. `sprint-beta-0-after-review.md`

Оновити:
- ✅ Go modules detection (виконано в 1.2)
- Додати нові items якщо з'явились під час спринту

## 5. Translations

Якщо є час — оновити хоча б `docs/uk/discovery.md` (рідна мова).
Інші мови (de, es, it, sr) — позначити як TODO для Beta-1.

## 6. Final verification

```bash
make check          # All tests pass
make docs           # Docs build without errors
# Manual: перевірити links в README
```

## Checklist

- [ ] `make check` passes
- [ ] `docs/en/configuration.md` з новими settings
- [ ] `docs/en/discovery.md` оновлений
- [ ] README.md з discover CLI
- [ ] `sprint-beta-0-after-review.md` оновлений
- [ ] `make docs` passes (якщо є mkdocs setup)
