# Task 2.1: Dynamic System Prompt

## 🎯 Мета

Замінити пасивний `## Project Context` на активні інструкції
які формуються з трьох зон уваги Discovery.

## Що робити

### 1. Prompt Builder

```python
class ReviewPromptBuilder:
    """Builds review system prompt from discovery results."""

    def build_system_prompt(
        self,
        base_prompt: str,
        discovery: DiscoveryResult,
    ) -> str:
        """Inject discovery-driven instructions into review prompt."""
        sections = [base_prompt]

        # Three zones → instructions
        if discovery.llm_analysis:
            zones = discovery.llm_analysis.attention_zones
            sections.append(self._build_zone_instructions(zones))

        # MR-specific adaptations
        if discovery.diff_languages and not discovery.diff_languages.matches_repo:
            sections.append(self._build_language_adaptation(discovery.diff_languages))

        # New dependencies warning
        if discovery.deps_changes and discovery.deps_changes.added:
            sections.append(self._build_deps_warning(discovery.deps_changes))

        return "\n\n".join(sections)

    def _build_zone_instructions(self, zones: list[AttentionZone]) -> str:
        well = [z for z in zones if z.status == "well_covered"]
        not_covered = [z for z in zones if z.status == "not_covered"]
        weak = [z for z in zones if z.status == "weakly_covered"]

        parts = []

        if well:
            items = "\n".join(f"- {z.area}: {z.reason}" for z in well)
            parts.append(
                f"## What to SKIP (well covered by automated tools):\n"
                f"Do NOT comment on these areas — CI/CD already handles them.\n{items}"
            )

        if not_covered:
            items = "\n".join(f"- {z.area}: {z.reason}" for z in not_covered)
            parts.append(
                f"## What to FOCUS on (not covered by automated tools):\n"
                f"Pay extra attention to these areas — no automated checks exist.\n{items}"
            )

        if weak:
            items = "\n".join(
                f"- {z.area}: {z.reason}"
                + (f"\n  💡 Recommendation: {z.recommendation}" if z.recommendation else "")
                for z in weak
            )
            parts.append(
                f"## What to CHECK and recommend improvements:\n"
                f"These areas have some coverage but could be better.\n{items}"
            )

        return "\n\n".join(parts)
```

### 2. Інтеграція в review flow

```python
# В review orchestrator (або де формується review prompt):

prompt_builder = ReviewPromptBuilder()
system_prompt = prompt_builder.build_system_prompt(
    base_prompt=DEFAULT_REVIEW_SYSTEM_PROMPT,
    discovery=discovery_result,
)

# system_prompt тепер містить zone instructions
review = await llm.generate(
    system_prompt=system_prompt,
    user_prompt=diff_content,
    ...
)
```

### 3. Замінити старий `to_prompt_context()`

```python
# Було (Beta-0):
class ProjectProfile:
    def to_prompt_context(self) -> str:
        """Passive context block."""
        return f"## Project Context\n- Languages: {self.languages}\n..."

# Стає: ReviewPromptBuilder.build_system_prompt()
# to_prompt_context() позначити deprecated
```

## Tests

- [ ] Well covered zones → "SKIP" section в prompt
- [ ] Not covered zones → "FOCUS" section
- [ ] Mixed zones → all three sections present
- [ ] No discovery result → fallback to base prompt only
- [ ] Language mismatch → adaptation note in prompt
- [ ] New deps → warning section

## Definition of Done

- [ ] `ReviewPromptBuilder` створений
- [ ] Три секції генеруються з зон
- [ ] MR-specific adaptations включені
- [ ] Старий `to_prompt_context()` deprecated
- [ ] `make check` passes

## Estimate: 1.5-2h
