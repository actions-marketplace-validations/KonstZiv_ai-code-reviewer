# Epic: Review Integration

## 🔙 Контекст (після Phase 1)

Discovery Engine видає `DiscoveryResult` з:
- Три зони уваги (well / not / weakly covered)
- MR-specific data (diff languages, new deps)
- Кешовані або свіжі результати

Але ці дані ще **не впливають на review**. `## Project Context` у review prompt
все ще пасивний — просто перелік фактів.

## 🎯 Мета

Три зони **активно формують** review prompt:
- "DON'T comment on formatting — CI handles it"
- "MUST check SQL injection — not covered"
- "Verify test coverage — pytest exists but threshold low"

## Tasks

| Task | Опис | Estimate |
|------|------|----------|
| 2.1 Dynamic System Prompt | Три зони → review інструкції | 1.5-2h |
| 2.2 Discovery Comment | Verbose mode + візуалізація зон | 30min-1h |

## Вплив на користувача

**До:**
```
You are a code reviewer. Here is some context about the project:
## Project Context
Languages: Python
CI: GitHub Actions with ruff, pytest
```

**Після:**
```
You are a code reviewer. Follow these guidelines based on automated analysis:

## What to SKIP (well covered by CI):
- Code formatting (ruff --format enforced)
- Type errors (mypy --strict in CI)

## What to FOCUS on (not covered):
- SQL injection prevention
- Input validation
- Authentication patterns

## What to CHECK and recommend improvements:
- Test quality (pytest exists but no coverage threshold — recommend --cov-fail-under=80)

## MR-specific notes:
- This MR is primarily SQL migrations — focus on SQL security, not Python style
- New dependency added: sqlalchemy — verify necessity and security
```

## Review Gate

- [ ] Review prompt з трьома зонами генерується
- [ ] SKIP зони → LLM менше коментує style issues
- [ ] FOCUS зони → LLM більше коментує security
- [ ] Discovery comment показує зони для користувача
- [ ] `make check` passes
