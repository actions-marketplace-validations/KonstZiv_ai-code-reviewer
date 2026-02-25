"""Tests for discovery.comment — discovery comment formatting and posting logic."""

from __future__ import annotations

from ai_reviewer.discovery.comment import (
    DISCOVERY_COMMENT_HEADING,
    format_discovery_comment,
    should_post_discovery_comment,
)
from ai_reviewer.discovery.models import (
    AutomatedChecks,
    CIInsights,
    DetectedTool,
    Gap,
    PlatformData,
    ProjectProfile,
    ReviewGuidance,
    ToolCategory,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _make_profile(**kw: object) -> ProjectProfile:
    """Build a ProjectProfile with sensible defaults, overridable via kwargs."""
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
        framework=kw.pop("framework", None),  # type: ignore[arg-type]
        language_version=kw.pop("language_version", None),  # type: ignore[arg-type]
        package_manager=kw.pop("package_manager", None),  # type: ignore[arg-type]
        automated_checks=AutomatedChecks(ci_provider=ci_provider),
        guidance=ReviewGuidance(skip_in_review=skip, focus_in_review=focus),
        gaps=kw.pop("gaps", ()),  # type: ignore[arg-type]
    )


# ── TestFormatDiscoveryComment ───────────────────────────────────────


class TestFormatDiscoveryComment:
    """Tests for format_discovery_comment."""

    def test_minimal_profile(self) -> None:
        profile = _make_profile()
        result = format_discovery_comment(profile)
        assert DISCOVERY_COMMENT_HEADING in result
        assert "**Stack:** Python" in result
        assert "No CI pipeline detected" in result

    def test_full_stack_line(self) -> None:
        profile = _make_profile(
            framework="Django 5.1",
            language_version="3.13",
            package_manager="uv",
        )
        result = format_discovery_comment(profile)
        assert "**Stack:** Python (Django 5.1) 3.13, uv" in result

    def test_ci_tools_listed(self) -> None:
        profile = _make_profile(
            ci_tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING),
            ),
            ci_provider="GitHub Actions",
        )
        result = format_discovery_comment(profile)
        assert "GitHub Actions" in result
        assert "ruff" in result
        assert "mypy" in result
        assert "\u2705" in result  # checkmark

    def test_ci_falls_back_to_file_path(self) -> None:
        profile = _make_profile(
            ci_tools=(DetectedTool(name="pytest", category=ToolCategory.TESTING),),
            ci_provider=None,
            ci_file_path=".github/workflows/test.yml",
        )
        result = format_discovery_comment(profile)
        assert ".github/workflows/test.yml" in result

    def test_skip_section(self) -> None:
        profile = _make_profile(
            skip=("Code formatting (handled by CI)", "Basic type errors (mypy)"),
        )
        result = format_discovery_comment(profile)
        assert "**What I'll skip**" in result
        assert "- Code formatting (handled by CI)" in result
        assert "- Basic type errors (mypy)" in result

    def test_focus_section(self) -> None:
        profile = _make_profile(
            focus=("Security vulnerabilities", "Test coverage"),
        )
        result = format_discovery_comment(profile)
        assert "**What I'll focus on:**" in result
        assert "- Security vulnerabilities" in result

    def test_no_skip_section_when_empty(self) -> None:
        profile = _make_profile(skip=(), focus=("Security",))
        result = format_discovery_comment(profile)
        assert "I'll skip" not in result
        assert "I'll focus" in result

    def test_no_focus_section_when_empty(self) -> None:
        profile = _make_profile(skip=("Formatting",), focus=())
        result = format_discovery_comment(profile)
        assert "I'll skip" in result
        assert "I'll focus" not in result

    def test_footer_contains_reviewbot_hint(self) -> None:
        profile = _make_profile()
        result = format_discovery_comment(profile)
        assert ".reviewbot.md" in result
        assert "customize" in result

    def test_no_ci_shows_cross_mark(self) -> None:
        profile = _make_profile(ci_tools=())
        result = format_discovery_comment(profile)
        assert "\u274c" in result

    def test_gaps_section_observation_and_assumption(self) -> None:
        profile = _make_profile(
            gaps=(
                Gap(observation="No test framework detected", default_assumption="No testing"),
                Gap(observation="Hardcoded API key", default_assumption="Will be moved to env"),
            ),
        )
        result = format_discovery_comment(profile)
        assert "**Questions / Gaps:**" in result
        assert "- No test framework detected" in result
        assert "  *Assumption:* No testing" in result
        assert "- Hardcoded API key" in result
        assert "  *Assumption:* Will be moved to env" in result

    def test_gaps_section_with_question(self) -> None:
        profile = _make_profile(
            gaps=(
                Gap(
                    observation="No SAST tool detected",
                    question="Do you run security scans separately?",
                    default_assumption="No security scanning",
                ),
            ),
        )
        result = format_discovery_comment(profile)
        assert "**Questions / Gaps:**" in result
        assert "- No SAST tool detected" in result
        assert "  *Question:* Do you run security scans separately?" in result
        assert "  *Assumption:* No security scanning" in result

    def test_no_gaps_section_when_empty(self) -> None:
        profile = _make_profile(gaps=())
        result = format_discovery_comment(profile)
        assert "Questions / Gaps" not in result

    def test_russian_disclaimer_added(self) -> None:
        profile = _make_profile()
        result = format_discovery_comment(profile, language="ru")
        assert "россиянин" in result

    def test_no_russian_disclaimer_for_other_languages(self) -> None:
        profile = _make_profile()
        result = format_discovery_comment(profile, language="uk")
        assert "россиянин" not in result


# ── TestShouldPostDiscoveryComment ───────────────────────────────────


class TestShouldPostDiscoveryComment:
    """Tests for should_post_discovery_comment."""

    def test_skip_when_no_gaps(self) -> None:
        profile = _make_profile(gaps=())
        assert should_post_discovery_comment(profile) is False

    def test_skip_when_reviewbot_md_exists(self) -> None:
        profile = _make_profile(file_tree=("src/main.py", ".reviewbot.md"))
        assert should_post_discovery_comment(profile) is False

    def test_skip_when_duplicate_exists(self) -> None:
        profile = _make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = (f"{DISCOVERY_COMMENT_HEADING}\n**Stack:** Python",)
        assert should_post_discovery_comment(profile, existing) is False

    def test_post_with_gaps_no_duplicate(self) -> None:
        profile = _make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = ("## AI Review\nSome review content",)
        assert should_post_discovery_comment(profile, existing) is True

    def test_post_with_gaps_first_run(self) -> None:
        profile = _make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        assert should_post_discovery_comment(profile) is True

    def test_skip_reviewbot_md_even_with_gaps(self) -> None:
        profile = _make_profile(
            file_tree=("src/main.py", ".reviewbot.md"),
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        assert should_post_discovery_comment(profile) is False
