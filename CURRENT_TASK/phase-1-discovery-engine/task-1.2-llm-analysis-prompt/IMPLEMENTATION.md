# Implementation: LLM Analysis Prompt

## Файли для зміни

```
ai-code-reviewer/
├── discovery/
│   ├── models.py              # + AttentionZone, LLMDiscoveryResult
│   ├── prompts.py             # NEW: discovery prompts
│   ├── llm_analyzer.py        # NEW: LLM analysis logic
│   ├── orchestrator.py        # integrate _analyze_with_llm
│   └── ci_analyzer.py         # DEPRECATED (mark, don't delete yet)
└── tests/
    └── discovery/
        ├── test_llm_analyzer.py    # NEW
        └── fixtures/
            └── llm_responses/      # NEW: sample LLM outputs
```

## Послідовність

1. Додати моделі в `models.py`
2. Створити `prompts.py` з шаблонами
3. Створити `llm_analyzer.py` з логікою
4. Інтегрувати в `orchestrator.py`
5. Позначити `ci_analyzer.py` як deprecated

## Ключові рішення

### Промпт formatting

`RawProjectData` → prompt string. Важливо **не** передавати ВСЕ — обмежити:

```python
def _format_discovery_prompt(self, raw_data: RawProjectData) -> str:
    # Languages: top 5 only
    top_langs = sorted(
        raw_data.languages.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    # File tree: first 100 entries
    tree_str = "\n".join(raw_data.file_tree[:100])
    if raw_data.file_tree_truncated:
        tree_str += f"\n... (truncated, {len(raw_data.file_tree)} total files)"

    # CI files: full content (usually small)
    ci_str = "\n\n".join(
        f"### {path}\n```\n{content}\n```"
        for path, content in raw_data.ci_files.items()
    )

    # Dep files: full content
    dep_str = "\n\n".join(
        f"### {path}\n```\n{content}\n```"
        for path, content in raw_data.dependency_files.items()
    )

    # Config files: full content
    cfg_str = "\n\n".join(
        f"### {path}\n```\n{content}\n```"
        for path, content in raw_data.config_files.items()
    )

    return DISCOVERY_USER_PROMPT.format(
        languages=", ".join(f"{l} ({p:.0f}%)" for l, p in top_langs),
        package_managers=", ".join(raw_data.detected_package_managers) or "unknown",
        layout=raw_data.layout or "unknown",
        dependency_files=dep_str or "(none found)",
        ci_files=ci_str or "(none found)",
        config_files=cfg_str or "(none found)",
        file_tree=tree_str or "(empty)",
    )
```

### LLMProvider.generate() з response_schema

Переконатися що `LLMProvider` ABC підтримує:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        max_tokens: int = 2000,
    ) -> BaseModel | str:
        """Generate response, optionally parsed to schema."""
```

GeminiProvider реалізація:
- `response_schema` → Gemini `response_mime_type="application/json"` + `response_schema`
- Або: prompt + JSON parsing fallback

### Deprecation ci_analyzer.py

```python
# ci_analyzer.py - top of file
import warnings

warnings.warn(
    "ci_analyzer module is deprecated since Beta-0.5. "
    "Use llm_analyzer.py with LLM-driven discovery instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

НЕ видаляємо ще — може знадобитися як fallback reference.

## Mock для тестів

```python
# fixtures/llm_responses/python_django_project.json
{
    "attention_zones": [
        {
            "area": "formatting",
            "status": "well_covered",
            "tools": ["ruff"],
            "reason": "ruff format enforced in CI with --check flag",
            "recommendation": ""
        },
        {
            "area": "type_checking",
            "status": "well_covered",
            "tools": ["mypy"],
            "reason": "mypy --strict in CI pipeline",
            "recommendation": ""
        },
        {
            "area": "testing",
            "status": "weakly_covered",
            "tools": ["pytest"],
            "reason": "pytest runs in CI but no coverage threshold",
            "recommendation": "Add --cov-fail-under=80 to pytest configuration"
        },
        {
            "area": "security",
            "status": "not_covered",
            "tools": [],
            "reason": "No SAST tool (bandit, semgrep) or dependency scanner found",
            "recommendation": "Add bandit for Python security scanning, pip-audit for dependency vulnerabilities"
        }
    ],
    "framework": "Django 5.1",
    "framework_confidence": 0.95,
    "stack_summary": "Python 3.13 + Django 5.1 + PostgreSQL",
    "watch_files": [
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "ruff.toml"
    ],
    "conventions_detected": [
        "ruff: line-length=120",
        "mypy: strict=true",
        "ruff: target-version=py313"
    ],
    "security_concerns": [
        "No dependency vulnerability scanning",
        "No SAST tool configured"
    ]
}
```
