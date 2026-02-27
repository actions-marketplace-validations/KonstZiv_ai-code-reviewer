"""Root conftest — auto-apply markers based on test directory."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-apply 'integration' and 'e2e' markers based on file path."""
    for item in items:
        path = str(item.fspath)
        if "/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)
