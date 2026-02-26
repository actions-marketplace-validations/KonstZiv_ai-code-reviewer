# Task 3.2: Reviewer Integration — Implementation Guide

## Актуальний стан коду (після Phase 2)

- `reviewer.py` використовує `analyze_code_changes()` з `integrations/gemini.py`
- `analyze_code_changes()` сам створює `GeminiProvider`, будує prompt, робить fallback
- `provider` — triple inheritance (`GitProvider + RepositoryProvider + ConversationProvider`)
- `ReviewContext` має `tasks: tuple[LinkedTask, ...]` і буде мати `project_profile` (task 3.1)

## Стратегія інтеграції

Discovery крок додається **перед** `analyze_code_changes()`.
`analyze_code_changes()` не змінюється — вона вже отримує `ReviewContext`, який тепер матиме `project_profile`.

## 1. Оновити review_pull_request()

```python
# reviewer.py

from ai_reviewer.discovery import DiscoveryOrchestrator
from ai_reviewer.llm.gemini import GeminiProvider

def review_pull_request(provider, repo_name, mr_id, settings):
    try:
        logger.info("Starting review for MR #%s in %s", mr_id, repo_name)

        # NEW: Discovery step (fail-open)
        profile = None
        if settings.discovery_enabled:
            profile = _run_discovery(provider, repo_name, mr_id, settings)

        # 1. Fetch MR data (existing)
        mr = provider.get_merge_request(repo_name, mr_id)
        if not mr:
            logger.error("Could not fetch MR data. Aborting.")
            return

        # 2. Get linked tasks (existing)
        tasks = provider.get_linked_tasks(repo_name, mr.number, mr.source_branch)

        # 3. Build context (add project_profile)
        context = ReviewContext(
            mr=mr,
            tasks=tasks,
            repository=repo_name,
            project_profile=profile,  # NEW
        )

        # 4-6. Analyze, format, post (existing, unchanged)
        result = analyze_code_changes(context, settings)
        # ...
```

## 2. Додати _run_discovery() helper

```python
def _run_discovery(provider, repo_name, mr_id, settings):
    """Run discovery pipeline, fail-open on any error."""
    try:
        llm = GeminiProvider(
            api_key=settings.google_api_key.get_secret_value(),
            model_name=settings.gemini_model,
        )
        discovery = DiscoveryOrchestrator(
            repo_provider=provider,  # triple inheritance
            conversation=provider,
            llm=llm,
        )
        profile = discovery.discover(repo_name, mr_id)
        logger.info("Discovery: %s project, %d CI tools",
                     profile.platform_data.primary_language,
                     len(profile.ci_insights.detected_tools) if profile.ci_insights else 0)
        return profile
    except Exception:
        logger.warning("Discovery failed, continuing without profile", exc_info=True)
        return None
```

## 3. Нові settings

```python
# core/config.py

class Settings(BaseSettings):
    # ... existing ...
    discovery_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AI_REVIEWER_DISCOVERY_ENABLED", "DISCOVERY_ENABLED",
        ),
    )
```

## 4. Оновити action.yml

```yaml
inputs:
  # ... existing ...
  discovery_enabled:
    description: 'Enable project discovery before review'
    required: false
    default: 'true'
```

І в env mapping:

```yaml
env:
  AI_REVIEWER_DISCOVERY_ENABLED: ${{ inputs.discovery_enabled }}
```

---

## Чеклист

- [ ] `_run_discovery()` helper в reviewer.py
- [ ] Discovery step в `review_pull_request()` перед fetch MR
- [ ] Fail-open: Discovery error → warning + continue
- [ ] `discovery_enabled` setting в config.py
- [ ] action.yml updated
- [ ] Existing tests still pass
- [ ] `uv run pytest -x -q && uv run ruff check && uv run mypy`
