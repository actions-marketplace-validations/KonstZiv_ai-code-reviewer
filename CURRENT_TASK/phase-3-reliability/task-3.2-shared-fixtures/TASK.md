# Task 3.2: conftest.py with Shared Fixtures

## Тип: Testing | Пріоритет: MEDIUM | Estimate: 1-1.5h

## Для борди

Тести дублюють mock setup для providers і sample data. Створити `conftest.py` з shared pytest fixtures для всього test suite.

**Acceptance Criteria:**
- [ ] `tests/conftest.py` з базовими fixtures
- [ ] `tests/unit/test_discovery/conftest.py` з discovery-specific fixtures
- [ ] Мінімум 3 existing test files refactored щоб використовувати нові fixtures
- [ ] Немає дублювання mock PlatformData / CIInsights creation

---

# Implementation Guide

## `tests/conftest.py` — root-level fixtures

```python
"""Shared test fixtures for the entire test suite."""

import pytest
from unittest.mock import MagicMock

from ai_reviewer.core.config import Settings
from ai_reviewer.discovery.models import (
    CIInsights, DetectedTool, PlatformData, ToolCategory,
)
from ai_reviewer.integrations.repository import RepositoryMetadata


@pytest.fixture
def mock_settings() -> Settings:
    """Minimal settings for testing."""
    return Settings(
        google_api_key="AIza-test-key-minimum-length-32chars",
        github_token="ghp_test_token_minimum_length_32chars",
        discovery_enabled=True,
    )


@pytest.fixture
def sample_platform_data() -> PlatformData:
    """Python project platform data."""
    return PlatformData(
        languages={"Python": 85.0, "Shell": 10.0, "Dockerfile": 5.0},
        primary_language="Python",
        topics=("python", "code-review", "ai"),
        description="AI-powered code reviewer",
        default_branch="main",
        file_tree=(
            "src/app/__init__.py",
            "src/app/main.py",
            "tests/test_main.py",
            "pyproject.toml",
            ".github/workflows/ci.yml",
        ),
        ci_config_paths=(".github/workflows/ci.yml",),
    )


@pytest.fixture
def sample_ci_insights() -> CIInsights:
    """CI insights with ruff + mypy + pytest."""
    return CIInsights(
        ci_file_path=".github/workflows/ci.yml",
        detected_tools=(
            DetectedTool(name="ruff", category=ToolCategory.LINTING, command="ruff check src/"),
            DetectedTool(name="ruff", category=ToolCategory.FORMATTING, command="ruff format --check"),
            DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING, command="mypy src/"),
            DetectedTool(name="pytest", category=ToolCategory.TESTING, command="pytest"),
        ),
        python_version="3.13",
        package_manager="uv",
    )


@pytest.fixture
def sample_repository_metadata() -> RepositoryMetadata:
    """Basic repository metadata."""
    return RepositoryMetadata(
        name="owner/repo",
        description="Test repository",
        default_branch="main",
        topics=("python",),
        visibility="public",
    )
```

## `tests/unit/test_discovery/conftest.py` — discovery fixtures

```python
"""Shared fixtures for discovery tests."""

import pytest
from unittest.mock import MagicMock, PropertyMock

from ai_reviewer.discovery.config_collector import ConfigContent
from ai_reviewer.discovery.models import ProjectProfile, ReviewGuidance, AutomatedChecks
from ai_reviewer.integrations.conversation import BotQuestion, BotThread, ThreadStatus
from ai_reviewer.integrations.repository import RepositoryProvider
from ai_reviewer.integrations.conversation import ConversationProvider
from ai_reviewer.llm.base import LLMProvider, LLMResponse


@pytest.fixture
def mock_repo_provider(sample_platform_data) -> MagicMock:
    """Mock RepositoryProvider with standard responses."""
    provider = MagicMock(spec=RepositoryProvider)
    provider.get_languages.return_value = sample_platform_data.languages
    provider.get_metadata.return_value = RepositoryMetadata(
        name="owner/repo", default_branch="main", topics=("python",)
    )
    provider.get_file_tree.return_value = sample_platform_data.file_tree
    provider.get_file_content.return_value = None  # no .reviewbot.md by default
    return provider


@pytest.fixture
def mock_conversation_provider() -> MagicMock:
    """Mock ConversationProvider with no existing threads."""
    provider = MagicMock(spec=ConversationProvider)
    provider.get_bot_threads.return_value = ()
    provider.post_question_comment.return_value = "comment-123"
    return provider


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    """Mock LLMProvider that returns empty response."""
    provider = MagicMock(spec=LLMProvider)
    return provider


@pytest.fixture
def sample_pyproject_config() -> ConfigContent:
    """pyproject.toml with Django dependency."""
    return ConfigContent(
        path="pyproject.toml",
        content='[project]\nname = "myapp"\ndependencies = ["django>=4.2", "celery>=5.3"]',
        size_chars=70,
    )


@pytest.fixture
def sample_package_json_config() -> ConfigContent:
    """package.json with React."""
    return ConfigContent(
        path="package.json",
        content='{"dependencies": {"react": "^18.0", "next": "^14.0"}}',
        size_chars=55,
    )
```

## Refactor existing tests

Pick 3 test files that duplicate mock setup most and refactor:
- `tests/unit/test_discovery/test_orchestrator.py`
- `tests/unit/test_discovery/test_comment.py`
- `tests/unit/test_discovery/test_config_collector.py`

## Checklist

- [ ] `tests/conftest.py` створений
- [ ] `tests/unit/test_discovery/conftest.py` створений
- [ ] 3+ test files refactored
- [ ] `make check` passes
