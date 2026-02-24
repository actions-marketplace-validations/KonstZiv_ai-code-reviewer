# Task 3.3: Discovery Comment — Implementation Guide

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

**Q1:** I see `make verify` in your Makefile — what does this target do?
> *Default: I'll assume it's a convenience alias for lint+test.*

---
💡 *Create `.reviewbot.md` in your repo root to customize.*
📊 *Discovery: 3 API calls, 0 LLM tokens*
```

## Реалізація

```python
def format_discovery_comment(profile: ProjectProfile, stats: dict) -> str:
    parts = ["## 🔍 AI ReviewBot: Project Analysis\n"]

    # Stack
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
        parts.append(f"**CI:** ✅ {ci.ci_file_path} — {tool_names}")
    else:
        parts.append("**CI:** ❌ No CI pipeline detected")

    # Skip / Focus
    g = profile.guidance
    if g.skip_in_review:
        parts.append("\n**What I'll skip** (CI handles these):")
        for item in g.skip_in_review:
            parts.append(f"- {item}")
    if g.focus_in_review:
        parts.append("\n**What I'll focus on:**")
        for item in g.focus_in_review:
            parts.append(f"- {item}")

    # Questions from gaps
    questions_with_q = [g for g in profile.gaps if g.question]
    if questions_with_q:
        parts.append("")
        for i, gap in enumerate(questions_with_q, 1):
            parts.append(f"**Q{i}:** {gap.question}")
            parts.append(f"> *Default: {gap.default_assumption}*")
            parts.append("")

    # Footer
    parts.append("---")
    parts.append("💡 *Create `.reviewbot.md` in your repo root to customize.*")
    api_calls = stats.get("api_calls", 0)
    llm_tokens = stats.get("llm_tokens", 0)
    parts.append(f"📊 *Discovery: {api_calls} API calls, {llm_tokens} LLM tokens*")

    return "\n".join(parts)
```

## Коли постити

- Перший запуск або `.reviewbot.md` відсутній → завжди
- Є gaps/questions → завжди
- Все добре, нема питань → тихий режим (не постити)

---

## Чеклист

- [ ] `format_discovery_comment()` — readable markdown
- [ ] Questions formatted з BotQuestion pattern (parseable)
- [ ] Stats footer (API calls, LLM tokens)
- [ ] Silent mode: no gaps → no comment
- [ ] Тест на formatting
- [ ] `make check` проходить
