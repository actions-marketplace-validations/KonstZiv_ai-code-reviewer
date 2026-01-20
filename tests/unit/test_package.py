"""Smoke tests for package initialization."""

import ai_reviewer


def test_version_exists() -> None:
    """Test that package version is defined."""
    assert hasattr(ai_reviewer, "__version__")
    assert isinstance(ai_reviewer.__version__, str)


def test_version_format() -> None:
    """Test that version follows semantic versioning format."""
    version = ai_reviewer.__version__
    parts = version.split(".")
    assert len(parts) == 3, f"Version should have 3 parts: {version}"
    assert all(part.isdigit() for part in parts), f"Version parts should be digits: {version}"
