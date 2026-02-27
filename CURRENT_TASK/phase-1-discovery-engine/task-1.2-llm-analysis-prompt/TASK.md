# Task 1.2: LLM Analysis Prompt

## 🔙 Контекст

`RawProjectData` (task 1.1) містить все зібране детерміністично.
Тепер потрібен ОДИН фокусований LLM-запит який перетворить це на actionable insights.

## 🎯 Мета

Один промпт (~200 input tokens) → structured response з:
1. **Три зони уваги** (well / not / weakly covered)
2. **Watch-files list** (файли для кешування)
3. **Framework + stack detection** (Django, FastAPI, React, etc.)
4. **Recommendations** (покращення CI/CD)

## Чому LLM а не regex

| | Regex (Beta-0) | LLM (Beta-0.5) |
|---|---|---|
| Новий CI tool | Додати regex pattern | Працює з коробки |
| Якість coverage | Не розуміє | "pytest є, але coverage threshold відсутній" |
| Framework detection | Hardcoded mapping | Розуміє context |
| Cross-tool interaction | Не бачить | "ruff + mypy = type errors covered" |
| Maintenance | 457 рядків regex | 1 промпт |

## Що робити

### 1. Pydantic Response Schema

```python
class AttentionZone(BaseModel):
    """One area of code quality."""
    area: str                    # "formatting", "type checking", "security", etc.
    status: Literal["well_covered", "not_covered", "weakly_covered"]
    tools: list[str] = []        # CI tools handling this area
    reason: str                  # "ruff --format enforced in CI pre-commit hook"
    recommendation: str = ""     # "Add coverage threshold to pytest (currently no --cov-fail-under)"

class LLMDiscoveryResult(BaseModel):
    """Structured LLM response for project analysis."""

    # Three attention zones
    attention_zones: list[AttentionZone]

    # Framework & stack
    framework: str | None = None          # "Django 5.1", "FastAPI", "Next.js 14"
    framework_confidence: float = 0.0     # 0.0-1.0
    stack_summary: str = ""               # "Python 3.13 + Django + PostgreSQL + Redis"

    # Watch-files (for caching)
    watch_files: list[str] = []           # [".github/workflows/ci.yml", "pyproject.toml"]
    watch_files_reason: str = ""          # "Changes to these files may affect CI coverage"

    # Additional insights
    conventions_detected: list[str] = []  # ["ruff: line-length=120", "mypy: strict mode"]
    security_concerns: list[str] = []     # ["No dependency scanning", "No SAST tool"]
```

### 2. Промпт

```python
DISCOVERY_SYSTEM_PROMPT = """You are a senior DevOps/code quality expert.
Analyze the project data and classify code quality coverage into three zones.

Respond ONLY with valid JSON matching the provided schema. No markdown, no explanation."""

DISCOVERY_USER_PROMPT = """Analyze this project and classify what is well covered, not covered, and weakly covered by automated tools.

## Project Data

Languages: {languages}
Package managers: {package_managers}
Layout: {layout}

## Dependency files
{dependency_files}

## CI Configuration
{ci_files}

## Quality Config Files
{config_files}

## File Tree (first 100 entries)
{file_tree}

## Instructions

1. **attention_zones**: Classify these areas: formatting, linting, type checking, testing, security scanning, dependency auditing, documentation, code coverage. Add project-specific areas if relevant.

2. **framework**: Detect the primary framework from dependencies. Include version if visible.

3. **watch_files**: List files that, if changed, would affect your analysis. These are files I should monitor to know when to re-run this analysis.

4. **conventions_detected**: Extract specific rules from config files (e.g., "ruff: line-length=120").

5. **security_concerns**: Note any missing security practices."""
```

### 3. Інтеграція з LLMProvider

```python
async def _analyze_with_llm(
    self,
    raw_data: RawProjectData,
    llm: LLMProvider,
) -> LLMDiscoveryResult | None:
    """Send one focused prompt to LLM. Returns None on failure."""
    try:
        result = await llm.generate(
            system_prompt=DISCOVERY_SYSTEM_PROMPT,
            user_prompt=self._format_discovery_prompt(raw_data),
            response_schema=LLMDiscoveryResult,
            max_tokens=1000,
        )
        return result
    except Exception as e:
        logger.warning("LLM discovery failed: %s. Falling back to deterministic.", e)
        return None
```

### 4. Fallback (LLM недоступний)

```python
def _build_fallback_result(self, raw_data: RawProjectData) -> LLMDiscoveryResult:
    """Deterministic fallback when LLM unavailable.

    Less useful but still provides basic structure.
    """
    zones = []

    # Basic: if CI files exist → at least something is covered
    if raw_data.ci_files:
        zones.append(AttentionZone(
            area="CI/CD",
            status="weakly_covered",
            reason="CI configuration found but couldn't analyze quality (LLM unavailable)",
        ))
    else:
        zones.append(AttentionZone(
            area="CI/CD",
            status="not_covered",
            reason="No CI configuration found",
        ))

    return LLMDiscoveryResult(
        attention_zones=zones,
        watch_files=list(raw_data.ci_files.keys()) + list(raw_data.dependency_files.keys()),
    )
```

## Token Budget

| Компонент | Tokens (estimate) |
|-----------|-------------------|
| System prompt | ~50 |
| User prompt template | ~80 |
| Raw data (typical project) | ~100-300 |
| Response | ~200-400 |
| **Total per run** | **~400-800** |

З watch-files caching (task 1.3): наступні запуски = **0 tokens**.

## Tests

- [ ] `LLMDiscoveryResult` парситься з valid JSON
- [ ] Промпт форматується без помилок для різних `RawProjectData`
- [ ] Fallback повертає базовий результат
- [ ] Empty raw data → fallback, не crash
- [ ] LLM timeout → fallback + warning log
- [ ] Response з extra fields → ігноруються (Pydantic)

## Definition of Done

- [ ] `LLMDiscoveryResult` schema створена
- [ ] Промпт написаний і тестований на fixture data
- [ ] Fallback працює при LLM failure
- [ ] `LLMProvider.generate()` приймає `response_schema`
- [ ] Token usage логується
- [ ] `make check` passes

## Estimate: 2-3h

## ⚠️ Важливо

Цей task **deprecated** regex CI analyzer. Після завершення:
- `_analyze_ci_*` методи видаляються або позначаються deprecated
- `CIInsights.tools` більше не заповнюється regex — тільки LLM або fallback
