# Task 3.2: Reviewer Integration — Implementation Guide

## Оновити reviewer.py

```python
def review_pull_request(provider, repo_name, mr_id, settings):
    # NEW: Create LLM provider once
    llm = GeminiProvider(settings.google_api_key, settings.gemini_model)

    # NEW: Discovery step
    profile = None
    if settings.discovery_enabled:
        discovery = DiscoveryOrchestrator(
            repo_provider=provider,
            conversation=provider,
            llm=llm,
        )
        try:
            profile = discovery.discover(repo_name, mr_id)
            logger.info("Discovery complete: %s", profile.platform_data.primary_language)
        except Exception:
            logger.warning("Discovery failed, continuing without profile", exc_info=True)

    # Existing: fetch MR
    mr = provider.get_merge_request(repo_name, mr_id)
    if mr is None:
        return

    task = provider.get_linked_task(repo_name, mr)
    context = ReviewContext(
        mr=mr,
        task=task,
        repository=repo_name,
        project_profile=profile,  # NEW
    )

    # Review via LLM
    prompt = build_review_prompt(context, settings)
    response = llm.generate(
        prompt,
        system_prompt=SYSTEM_PROMPT,
        response_schema=ReviewResult,
    )
    result = response.content

    # ... rest: format, submit, post
```

## Нові settings

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

## Оновити action.yml

```yaml
inputs:
  # ... existing ...
  discovery_enabled:
    description: 'Enable project discovery before review'
    required: false
    default: 'true'
```

---

## Чеклист

- [ ] Discovery step в reviewer.py
- [ ] Fail-open: Discovery error → warning + continue
- [ ] `discovery_enabled` setting
- [ ] action.yml updated
- [ ] Existing e2e test still passes
- [ ] `make check` проходить
