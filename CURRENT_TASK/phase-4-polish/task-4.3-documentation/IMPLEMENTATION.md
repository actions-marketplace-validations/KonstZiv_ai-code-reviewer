# Task 4.3: Documentation — Implementation Guide

## README update

Додати після "Quick Start":

```markdown
## 🔍 Project Discovery

AI ReviewBot automatically analyzes your repository before each review:

- **Languages & frameworks** detected from GitHub/GitLab API
- **CI pipeline** parsed to understand what's already automated
- **Config files** read to understand project rules

This means the bot won't comment on:
- Formatting issues if you have a formatter in CI
- Type errors if you run mypy/pyright in CI
- Style issues that your linter already catches

### Customize with .reviewbot.md

Create `.reviewbot.md` in your repo root to fine-tune:

```markdown
# .reviewbot.md

## Review Guidance

### Skip
- Import ordering (isort in CI)
- Docstring style (we don't enforce)

### Focus
- SQL injection vulnerabilities
- API backward compatibility
```

## Example .reviewbot.md

Create `examples/.reviewbot.md` — copy of task 2.4 format.

## ROADMAP update

```markdown
## Beta Roadmap

- [x] Beta-0: Project Discovery + Conversation Foundation
- [ ] Beta-1: Deep Context + Stability
- [ ] Beta-2: Multi-Step Review + Dialogue
- [ ] Beta-3: Interactive Mode
```

---

## Чеклист

- [ ] README.md updated
- [ ] examples/.reviewbot.md created
- [ ] ROADMAP.md updated
- [ ] CHANGELOG.md entry
- [ ] `make check` проходить (docs build if configured)
