# Task 3.3: Discovery Comment — Implementation Guide

## Актуальний стан коду (після Phase 2)

- `ProjectProfile` має всі потрібні поля: `platform_data`, `ci_insights`, `guidance`, `gaps`, `framework`, `language_version`, `package_manager`
- `ConversationProvider.post_question_comment()` вже використовується в orchestrator для gaps
- Discovery comment — це **окремий** коментар від question comment

## Формат

```markdown
## 🔍 AI ReviewBot: Project Analysis

**Stack:** Python 3.13 (Django 5.1), uv, src layout
**CI:** ✅ GitHub Actions — ruff, mypy --strict, pytest (coverage ≥ 80%)

**What I'll skip** (CI handles these):
- Code formatting and import ordering (ruff)
- Basic type errors (mypy strict)

**What I'll focus on:**
- Security (no SAST tool detected)
- Business logic correctness
- Error handling edge cases

---
💡 *Create `.reviewbot.md` in your repo root to customize.*
```

## Реалізація

### 1. format_discovery_comment()

```python
# discovery/comment.py (або в orchestrator чи окремий модуль)

def format_discovery_comment(profile: ProjectProfile) -> str:
    """Format a discovery summary comment for posting to MR."""
    parts = ["## 🔍 AI ReviewBot: Project Analysis\n"]

    # Stack line
    pd = profile.platform_data
    stack = f"**Stack:** {pd.primary_language}"
    if profile.framework:
        stack += f" ({profile.framework})"
    if profile.language_version:
        stack += f" {profile.language_version}"
    if profile.package_manager:
        stack += f", {profile.package_manager}"
    parts.append(stack)

    # CI status
    ci = profile.ci_insights
    if ci and ci.detected_tools:
        tool_names = ", ".join(t.name for t in ci.detected_tools)
        provider = profile.automated_checks.ci_provider or ci.ci_file_path
        parts.append(f"**CI:** ✅ {provider} — {tool_names}")
    else:
        parts.append("**CI:** ❌ No CI pipeline detected")

    # Skip / Focus from guidance
    g = profile.guidance
    if g.skip_in_review:
        parts.append("\n**What I'll skip** (CI handles these):")
        for item in g.skip_in_review:
            parts.append(f"- {item}")
    if g.focus_in_review:
        parts.append("\n**What I'll focus on:**")
        for item in g.focus_in_review:
            parts.append(f"- {item}")

    # Footer
    parts.append("\n---")
    parts.append("💡 *Create `.reviewbot.md` in your repo root to customize.*")

    return "\n".join(parts)
```

**Примітка:** `stats: dict` параметр прибрано — orchestrator не збирає метрики API calls/tokens. Якщо потрібно — додамо в Beta-1 разом з token tracking.

### 2. Коли постити

В `reviewer.py` після discovery:

```python
if profile and not profile.from_reviewbot_md:
    # Post discovery comment (first run or gaps exist)
    if profile.gaps or not _has_previous_discovery_comment(provider, repo_name, mr_id):
        comment = format_discovery_comment(profile)
        provider.post_comment(repo_name, mr_id, comment)
```

**Правила:**
- `.reviewbot.md` є → тихий режим (не постити)
- Є gaps/questions → завжди постити
- Все добре, нема питань, перший запуск → постити один раз
- Повторний запуск без змін → не постити (duplicate detection)

### 3. Визначення from_reviewbot_md

Додати поле в `ProjectProfile` або передавати окремим параметром:

```python
# Варіант: просто перевірити в reviewer.py
posted_reviewbot = profile.platform_data.file_tree and ".reviewbot.md" in profile.platform_data.file_tree
```

---

## Чеклист

- [ ] `format_discovery_comment()` — readable markdown
- [ ] Silent mode: `.reviewbot.md` → no comment
- [ ] Silent mode: no gaps + повторний запуск → no comment
- [ ] Duplicate detection (перевірка по заголовку `## 🔍 AI ReviewBot`)
- [ ] Тести на formatting
- [ ] `uv run pytest -x -q && uv run ruff check && uv run mypy`
