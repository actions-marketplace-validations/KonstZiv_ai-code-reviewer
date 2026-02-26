# Task 2.5: Discovery Prompts — Implementation Guide

## LLMDiscoveryResponse

```python
class LLMDiscoveryResponse(BaseModel):
    """Тільки те, чого не можна витягнути детерміністично."""
    framework: str | None = None
    architecture_notes: str | None = None
    skip_in_review: list[str] = []
    focus_in_review: list[str] = []
    gaps: list[Gap] = []
    conventions: list[str] = []
```

## DISCOVERY_SYSTEM_PROMPT

```python
DISCOVERY_SYSTEM_PROMPT = """You are a project setup analyst.
Your task: interpret project configuration files and determine
what a code reviewer should know about this project.

Rules:
- Be concise and specific
- Only list what you can CONFIRM from the provided data
- If uncertain, add a Gap with a question
- Do NOT guess or hallucinate tools/frameworks
"""
```

## build_interpretation_prompt()

```python
def build_interpretation_prompt(
    platform_data: PlatformData,
    ci_insights: CIInsights | None,
    configs: tuple[ConfigContent, ...],
) -> str:
    parts = ["# Project Setup Analysis\n"]

    parts.append(f"## Languages: {platform_data.primary_language}")
    if platform_data.topics:
        parts.append(f"Topics: {', '.join(platform_data.topics)}")

    if ci_insights:
        tools = [t.name for t in ci_insights.detected_tools]
        parts.append(f"\n## CI Tools: {', '.join(tools)}")

    if configs:
        parts.append("\n## Config Files")
        for cfg in configs:
            parts.append(f"\n### {cfg.path}")
            parts.append(f"```\n{cfg.content}\n```")

    parts.append("\n## Task")
    parts.append("Based on the above, determine:")
    parts.append("1. Framework (if detectable)")
    parts.append("2. What a reviewer should SKIP (already automated)")
    parts.append("3. What a reviewer should FOCUS on (gaps)")
    parts.append("4. Project conventions")
    parts.append("5. Questions if anything is unclear")

    return "\n".join(parts)
```

---

## Чеклист

- [ ] `LLMDiscoveryResponse` model
- [ ] `DISCOVERY_SYSTEM_PROMPT`
- [ ] `build_interpretation_prompt()` — compact, informative
- [ ] Тести: prompt generation, token estimation (should be <2000 tokens)
- [ ] `make check` проходить
