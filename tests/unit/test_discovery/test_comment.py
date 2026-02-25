"""Tests for discovery.comment — discovery comment formatting and posting logic."""

from __future__ import annotations

from ai_reviewer.discovery.comment import (
    DISCOVERY_COMMENT_HEADING,
    format_discovery_comment,
    should_post_discovery_comment,
)
from ai_reviewer.discovery.models import (
    DetectedTool,
    Gap,
    ToolCategory,
)
from tests.helpers import make_profile

# ── TestFormatDiscoveryComment ───────────────────────────────────────


class TestFormatDiscoveryComment:
    """Tests for format_discovery_comment."""

    def test_minimal_profile(self) -> None:
        profile = make_profile()
        result = format_discovery_comment(profile)
        assert DISCOVERY_COMMENT_HEADING in result
        assert "**Stack:** Python" in result
        assert "No CI pipeline detected" in result

    def test_full_stack_line(self) -> None:
        profile = make_profile(
            framework="Django 5.1",
            language_version="3.13",
            package_manager="uv",
        )
        result = format_discovery_comment(profile)
        assert "**Stack:** Python (Django 5.1) 3.13, uv" in result

    def test_ci_tools_listed(self) -> None:
        profile = make_profile(
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
        profile = make_profile(
            ci_tools=(DetectedTool(name="pytest", category=ToolCategory.TESTING),),
            ci_provider=None,
            ci_file_path=".github/workflows/test.yml",
        )
        result = format_discovery_comment(profile)
        assert ".github/workflows/test.yml" in result

    def test_skip_section(self) -> None:
        profile = make_profile(
            skip=("Code formatting (handled by CI)", "Basic type errors (mypy)"),
        )
        result = format_discovery_comment(profile)
        assert "**What I'll skip**" in result
        assert "- Code formatting (handled by CI)" in result
        assert "- Basic type errors (mypy)" in result

    def test_focus_section(self) -> None:
        profile = make_profile(
            focus=("Security vulnerabilities", "Test coverage"),
        )
        result = format_discovery_comment(profile)
        assert "**What I'll focus on:**" in result
        assert "- Security vulnerabilities" in result

    def test_no_skip_section_when_empty(self) -> None:
        profile = make_profile(skip=(), focus=("Security",))
        result = format_discovery_comment(profile)
        assert "I'll skip" not in result
        assert "I'll focus" in result

    def test_no_focus_section_when_empty(self) -> None:
        profile = make_profile(skip=("Formatting",), focus=())
        result = format_discovery_comment(profile)
        assert "I'll skip" in result
        assert "I'll focus" not in result

    def test_footer_contains_reviewbot_hint(self) -> None:
        profile = make_profile()
        result = format_discovery_comment(profile)
        assert ".reviewbot.md" in result
        assert "customize" in result

    def test_no_ci_shows_cross_mark(self) -> None:
        profile = make_profile(ci_tools=())
        result = format_discovery_comment(profile)
        assert "\u274c" in result

    def test_gaps_section_observation_and_assumption(self) -> None:
        profile = make_profile(
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
        profile = make_profile(
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
        profile = make_profile(gaps=())
        result = format_discovery_comment(profile)
        assert "Questions / Gaps" not in result

    def test_russian_disclaimer_added(self) -> None:
        profile = make_profile()
        result = format_discovery_comment(profile, language="ru")
        assert "россиянин" in result

    def test_no_russian_disclaimer_for_other_languages(self) -> None:
        profile = make_profile()
        result = format_discovery_comment(profile, language="uk")
        assert "россиянин" not in result

    def test_no_disclaimer_when_language_none(self) -> None:
        """Test that no disclaimer when language is None (default)."""
        profile = make_profile()
        result = format_discovery_comment(profile)
        assert "россиянин" not in result

    def test_russian_iso639_3_code(self) -> None:
        """Test that ISO 639-3 'rus' code also triggers Russian disclaimer."""
        profile = make_profile()
        result = format_discovery_comment(profile, language="rus")
        assert "россиянин" in result

    def test_gap_without_question(self) -> None:
        """Test gap rendering when question is None."""
        profile = make_profile(
            gaps=(Gap(observation="No security scanner", default_assumption="None"),),
        )
        result = format_discovery_comment(profile)
        assert "- No security scanner" in result
        assert "*Question:*" not in result
        assert "  *Assumption:* None" in result

    def test_multiple_mixed_gaps(self) -> None:
        """Test rendering of multiple gaps with and without questions."""
        profile = make_profile(
            gaps=(
                Gap(
                    observation="No test framework",
                    question="What test runner do you use?",
                    default_assumption="No tests",
                ),
                Gap(
                    observation="No SAST tool",
                    default_assumption="No security scanning",
                ),
            ),
        )
        result = format_discovery_comment(profile)
        assert "- No test framework" in result
        assert "  *Question:* What test runner do you use?" in result
        assert "- No SAST tool" in result
        # Second gap has no question
        lines = result.split("\n")
        sast_idx = next(i for i, line in enumerate(lines) if "No SAST tool" in line)
        # Next line should be assumption, not question
        assert "*Assumption:*" in lines[sast_idx + 1]

    def test_full_profile_all_sections(self) -> None:
        """Test that a full profile renders all sections in order."""
        profile = make_profile(
            framework="FastAPI",
            language_version="3.12",
            package_manager="uv",
            ci_tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="pytest", category=ToolCategory.TESTING),
            ),
            ci_provider="GitHub Actions",
            skip=("Code style (CI handles)",),
            focus=("Security vulnerabilities",),
            gaps=(Gap(observation="No security scanner", default_assumption="None"),),
        )
        result = format_discovery_comment(profile)

        # Verify ordering: heading → stack → CI → skip → focus → gaps → footer
        heading_pos = result.index(DISCOVERY_COMMENT_HEADING)
        stack_pos = result.index("**Stack:**")
        ci_pos = result.index("**CI:**")
        skip_pos = result.index("I'll skip")
        focus_pos = result.index("I'll focus")
        gaps_pos = result.index("Questions / Gaps")
        footer_pos = result.index(".reviewbot.md")

        assert heading_pos < stack_pos < ci_pos < skip_pos < focus_pos < gaps_pos < footer_pos


# ── TestShouldPostDiscoveryComment ───────────────────────────────────


class TestShouldPostDiscoveryComment:
    """Tests for should_post_discovery_comment."""

    def test_skip_when_no_gaps(self) -> None:
        profile = make_profile(gaps=())
        assert should_post_discovery_comment(profile) is False

    def test_skip_when_reviewbot_md_exists(self) -> None:
        profile = make_profile(file_tree=("src/main.py", ".reviewbot.md"))
        assert should_post_discovery_comment(profile) is False

    def test_skip_when_duplicate_exists(self) -> None:
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = (f"{DISCOVERY_COMMENT_HEADING}\n**Stack:** Python",)
        assert should_post_discovery_comment(profile, existing) is False

    def test_post_with_gaps_no_duplicate(self) -> None:
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = ("## AI Review\nSome review content",)
        assert should_post_discovery_comment(profile, existing) is True

    def test_post_with_gaps_first_run(self) -> None:
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        assert should_post_discovery_comment(profile) is True

    def test_skip_reviewbot_md_even_with_gaps(self) -> None:
        profile = make_profile(
            file_tree=("src/main.py", ".reviewbot.md"),
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        assert should_post_discovery_comment(profile) is False

    def test_multiple_existing_comments_none_duplicate(self) -> None:
        """Test posting when multiple existing comments but none is duplicate."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = (
            "## Review\nFirst review",
            "LGTM",
            "Please fix the tests",
        )
        assert should_post_discovery_comment(profile, existing) is True

    def test_duplicate_detected_among_many(self) -> None:
        """Test that duplicate is detected even among many comments."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = (
            "## Review\nFirst review",
            f"old stuff\n{DISCOVERY_COMMENT_HEADING}\nold discovery",
            "LGTM",
        )
        assert should_post_discovery_comment(profile, existing) is False

    def test_reviewbot_md_check_before_gaps_check(self) -> None:
        """Test that .reviewbot.md check takes priority over gaps check."""
        # Profile has gaps but also .reviewbot.md — should NOT post
        profile = make_profile(
            file_tree=(".reviewbot.md",),
            gaps=(Gap(observation="Gap", default_assumption="Assumption"),),
        )
        assert should_post_discovery_comment(profile) is False
