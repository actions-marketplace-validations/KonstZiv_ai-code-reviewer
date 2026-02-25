"""Shared test helpers for building discovery models.

Provides factory functions used across unit, integration, and E2E tests
to construct ProjectProfile and related objects with sensible defaults.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_reviewer.discovery.models import (
    AutomatedChecks,
    CIInsights,
    PlatformData,
    ProjectProfile,
    ReviewGuidance,
)

if TYPE_CHECKING:
    from ai_reviewer.discovery.models import DetectedTool


def make_profile(**kw: object) -> ProjectProfile:
    """Build a ProjectProfile with sensible defaults, overridable via kwargs.

    Supports shorthand kwargs for common fields:
        - ``ci_tools``: tuple of DetectedTool (builds CIInsights automatically).
        - ``ci_provider``: CI provider name for AutomatedChecks.
        - ``ci_file_path``: CI config file path (default: ``.github/workflows/ci.yml``).
        - ``skip``, ``focus``: tuples for ReviewGuidance.
        - ``language``: primary language name (default: ``Python``).
        - ``file_tree``: file paths in the repository.
        - ``framework``, ``language_version``, ``package_manager``: stack details.
        - ``gaps``: tuple of Gap objects.

    Example::

        profile = make_profile(
            ci_tools=(DetectedTool(name="ruff", category=ToolCategory.LINTING),),
            gaps=(Gap(observation="No tests", default_assumption="None"),),
        )
    """
    ci_tools: tuple[DetectedTool, ...] = kw.pop("ci_tools", ())  # type: ignore[assignment]
    ci_provider: str | None = kw.pop("ci_provider", None)  # type: ignore[assignment]
    ci_file_path: str = kw.pop("ci_file_path", ".github/workflows/ci.yml")  # type: ignore[assignment]
    skip: tuple[str, ...] = kw.pop("skip", ())  # type: ignore[assignment]
    focus: tuple[str, ...] = kw.pop("focus", ())  # type: ignore[assignment]
    language: str = kw.pop("language", "Python")  # type: ignore[assignment]
    file_tree: tuple[str, ...] = kw.pop("file_tree", ("src/main.py",))  # type: ignore[assignment]

    ci = CIInsights(ci_file_path=ci_file_path, detected_tools=ci_tools) if ci_tools else None
    return ProjectProfile(
        platform_data=PlatformData(
            languages={language: 100.0},
            primary_language=language,
            file_tree=file_tree,
        ),
        ci_insights=ci,
        framework=kw.pop("framework", None),
        language_version=kw.pop("language_version", None),
        package_manager=kw.pop("package_manager", None),
        automated_checks=AutomatedChecks(ci_provider=ci_provider),
        guidance=ReviewGuidance(skip_in_review=skip, focus_in_review=focus),
        gaps=kw.pop("gaps", ()),
    )
