# Task 4.1: Reliability

## Три підзадачі

### A) Discovery Timeout (30 min)

**Проблема:** Немає загального timeout на Discovery pipeline. CI може чекати 60+ сек.

```python
import asyncio

DISCOVERY_TIMEOUT = int(os.getenv("DISCOVERY_TIMEOUT", "30"))

async def discover(self, ...) -> DiscoveryResult:
    try:
        return await asyncio.wait_for(
            self._discover_impl(...),
            timeout=DISCOVERY_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Discovery timed out after %ds", DISCOVERY_TIMEOUT)
        return DiscoveryResult.empty()  # fail-open
```

### B) Type Fixes (15 min)

**Проблема:** 5x `type: ignore` в orchestrator, переважно в `_first_non_none` та `_merge_ci_insights`.

Переписати з proper typing:

```python
# Було:
result = self._first_non_none(a, b, c)  # type: ignore

# Стає:
T = TypeVar("T")

def _first_non_none(self, *values: T | None) -> T | None:
    return next((v for v in values if v is not None), None)
```

### C) conftest.py з shared fixtures (30 min)

**Проблема:** Mock setup дублюється в кожному test file.

```python
# tests/conftest.py

import pytest
from unittest.mock import AsyncMock
from ai_code_reviewer.discovery.models import RawProjectData, LLMDiscoveryResult

@pytest.fixture
def mock_llm_provider():
    """Mock LLMProvider that returns fixture data."""
    provider = AsyncMock()
    provider.generate.return_value = LLMDiscoveryResult(
        attention_zones=[...],
        framework="Django 5.1",
        watch_files=[".github/workflows/ci.yml"],
    )
    return provider

@pytest.fixture
def mock_repo_provider():
    """Mock RepositoryProvider with sample data."""
    provider = AsyncMock()
    provider.get_languages.return_value = {"Python": 95.0, "Shell": 5.0}
    provider.get_file_tree.return_value = ["src/", "tests/", "pyproject.toml"]
    return provider

@pytest.fixture
def sample_raw_data():
    """Typical Python project raw data."""
    return RawProjectData(
        languages={"Python": 95.0, "Shell": 5.0},
        file_tree=["src/app/", "tests/", "pyproject.toml", "uv.lock"],
        dependency_files={"pyproject.toml": "[project]\nname='test'"},
        detected_package_managers=["uv"],
        layout="src",
    )
```

## Tests

- [ ] Timeout → `DiscoveryResult.empty()`, не exception
- [ ] `_first_non_none` type-safe, mypy passes
- [ ] conftest fixtures import в існуючих тестах

## Estimate: 1h total
