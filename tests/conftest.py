"""Root conftest — auto-apply markers and shared fixtures."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tests.helpers import make_mock_settings


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-apply 'integration' and 'e2e' markers based on file path."""
    for item in items:
        path = str(item.fspath)
        if "/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock Settings with sensible defaults for all attributes."""
    return make_mock_settings()


@pytest.fixture
def mock_provider() -> MagicMock:
    """Mock GitProvider for unit tests."""
    from ai_reviewer.integrations.base import GitProvider

    return MagicMock(spec=GitProvider)
