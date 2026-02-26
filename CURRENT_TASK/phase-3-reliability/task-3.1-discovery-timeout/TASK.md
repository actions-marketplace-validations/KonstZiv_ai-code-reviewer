# Task 3.1: Discovery Pipeline Timeout

## Тип: Reliability | Пріоритет: HIGH | Estimate: 1h

## Для борди

Discovery робить 5-15 API calls послідовно. Якщо GitHub/GitLab API повільний (5s/call × 15 calls = 75s), CI pipeline чекає без feedback.

**Acceptance Criteria:**
- [ ] Discovery pipeline має загальний timeout (default 30s, configurable)
- [ ] При timeout → fail-open з warning, review продовжується без profile
- [ ] Новий env var `AI_REVIEWER_DISCOVERY_TIMEOUT` в Settings

---

# Implementation Guide

## Підхід

**НЕ timeout кожного API call** (вже є через PyGithub/python-gitlab).
**Timeout на весь pipeline** через `threading.Timer` або простий time check.

### Рекомендація: простий time check (без threads)

```python
# orchestrator.py

import time

_DEFAULT_TIMEOUT_SECONDS = 30

class DiscoveryOrchestrator:
    def __init__(self, ..., timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS):
        # ...existing...
        self._timeout = timeout_seconds
        self._start_time: float = 0.0

    def _check_timeout(self, phase: str) -> None:
        """Raise TimeoutError if pipeline exceeded time budget."""
        elapsed = time.monotonic() - self._start_time
        if elapsed > self._timeout:
            msg = f"Discovery timeout after {elapsed:.1f}s (limit: {self._timeout}s) during {phase}"
            raise TimeoutError(msg)

    def discover(self, repo_name: str, mr_id: int | None = None) -> ProjectProfile:
        self._start_time = time.monotonic()

        # 0. Check .reviewbot.md
        existing = self._repo.get_file_content(repo_name, _REVIEWBOT_MD_PATH)
        if existing:
            return parse_reviewbot_md(existing)

        # 1. Previous answers
        threads = ...

        self._check_timeout("platform_data")
        # Layer 0
        platform_data = self._collect_platform_data(repo_name)

        self._check_timeout("ci_analysis")
        # Layer 1
        ci_insights = self._analyze_ci(platform_data, repo_name)

        self._check_timeout("config_collection")
        # Layer 2
        configs = self._collect_configs(...)

        self._check_timeout("profile_build")
        # Layer 3
        profile = ...
```

### Settings

```python
# core/config.py
discovery_timeout: int = Field(
    default=30,
    ge=5,
    le=120,
    validation_alias=AliasChoices("AI_REVIEWER_DISCOVERY_TIMEOUT", "DISCOVERY_TIMEOUT"),
    description="Discovery pipeline timeout in seconds",
)
```

### Reviewer integration

```python
# reviewer.py — _run_discovery()
discovery = DiscoveryOrchestrator(
    repo_provider=provider,
    conversation=provider,
    llm=llm,
    timeout_seconds=settings.discovery_timeout,
)
```

### Catch in reviewer

```python
# reviewer.py — _run_discovery() вже має try/except
# TimeoutError буде caught by existing except Exception
# Але варто додати explicit logging:
except TimeoutError:
    logger.warning("Discovery timed out after %ds", settings.discovery_timeout)
    return None
except Exception:
    logger.warning("Discovery failed", exc_info=True)
    return None
```

## Tests

```python
class TestDiscoveryTimeout:
    def test_timeout_triggers(self):
        """Discovery with slow provider raises TimeoutError."""
        slow_repo = SlowMockRepoProvider(delay_per_call=5.0)
        orchestrator = DiscoveryOrchestrator(
            repo_provider=slow_repo, ..., timeout_seconds=2,
        )
        # Should raise or return fallback profile
        with pytest.raises(TimeoutError):
            orchestrator.discover("owner/repo")
```

## Checklist

- [ ] `_check_timeout()` method в orchestrator
- [ ] `discovery_timeout` в Settings
- [ ] Передавати timeout з settings в orchestrator
- [ ] Explicit `except TimeoutError` в reviewer
- [ ] Unit test з slow mock
- [ ] `make check` passes
