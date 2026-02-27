"""Tests for discovery.comment — discovery comment formatting and posting logic."""

from __future__ import annotations

from ai_reviewer.discovery.comment import (
    DISCOVERY_COMMENT_HEADING,
    format_discovery_comment,
    should_post_discovery_comment,
)
from ai_reviewer.discovery.models import (
    AttentionZone,
    DetectedTool,
    Gap,
    ToolCategory,
)
from tests.helpers import make_profile

# ── Helpers ──────────────────────────────────────────────────────────


def _zone(
    area: str,
    status: str,
    *,
    reason: str = "",
    recommendation: str = "",
    tools: tuple[str, ...] = (),
) -> AttentionZone:
    return AttentionZone(
        area=area,
        status=status,
        reason=reason,
        recommendation=recommendation,
        tools=tools,
    )


# ── TestFormatDiscoveryComment ───────────────────────────────────────


class TestFormatDiscoveryComment:
    """Tests for format_discovery_comment."""

    def test_minimal_profile_no_issues_returns_none(self) -> None:
        """Default mode: no zones, no gaps -> None."""
        profile = make_profile()
        assert format_discovery_comment(profile) is None

    def test_verbose_always_returns_comment(self) -> None:
        """Verbose mode: always returns a comment, even without issues."""
        profile = make_profile()
        result = format_discovery_comment(profile, verbose=True)
        assert result is not None
        assert DISCOVERY_COMMENT_HEADING in result
        assert "**Stack:** Python" in result

    def test_not_covered_zone_triggers_comment(self) -> None:
        """Default mode: not_covered zone -> comment generated."""
        profile = make_profile(
            attention_zones=(_zone("security", "not_covered", reason="no SAST in CI"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "Not Covered" in result
        assert "security" in result
        assert "no SAST in CI" in result

    def test_weakly_covered_zone_triggers_comment(self) -> None:
        """Default mode: weakly_covered zone -> comment generated."""
        profile = make_profile(
            attention_zones=(
                _zone(
                    "testing",
                    "weakly_covered",
                    reason="pytest exists but no coverage threshold",
                    recommendation="add --cov-fail-under=80",
                ),
            ),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "Could Be Improved" in result
        assert "testing" in result
        assert "--cov-fail-under=80" in result

    def test_gaps_trigger_comment(self) -> None:
        """Default mode: gaps present -> comment generated."""
        profile = make_profile(
            gaps=(Gap(observation="No test framework detected", default_assumption="No testing"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "Questions / Gaps" in result

    def test_well_covered_only_returns_none_default(self) -> None:
        """Default mode: only well_covered zones -> None (no noise)."""
        profile = make_profile(
            attention_zones=(_zone("linting", "well_covered", reason="ruff in CI"),),
        )
        assert format_discovery_comment(profile) is None

    def test_verbose_shows_well_covered(self) -> None:
        """Verbose mode: well_covered zones are displayed."""
        profile = make_profile(
            attention_zones=(
                _zone("linting", "well_covered", reason="ruff in CI"),
                _zone("formatting", "well_covered", reason="ruff format in CI"),
            ),
        )
        result = format_discovery_comment(profile, verbose=True)
        assert result is not None
        assert "Well Covered" in result
        assert "linting" in result
        assert "\u2705" in result  # checkmark

    def test_verbose_shows_all_zone_types(self) -> None:
        """Verbose mode: all three zone types rendered."""
        profile = make_profile(
            attention_zones=(
                _zone("linting", "well_covered", reason="ruff in CI"),
                _zone("security", "not_covered", reason="no SAST"),
                _zone("testing", "weakly_covered", reason="no coverage gate"),
            ),
        )
        result = format_discovery_comment(profile, verbose=True)
        assert result is not None
        assert "Well Covered" in result
        assert "Not Covered" in result
        assert "Could Be Improved" in result

    def test_full_stack_line(self) -> None:
        profile = make_profile(
            framework="Django 5.1",
            language_version="3.13",
            package_manager="uv",
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "**Stack:** Python (Django 5.1) 3.13, uv" in result

    def test_ci_tools_listed(self) -> None:
        profile = make_profile(
            ci_tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING),
            ),
            ci_provider="GitHub Actions",
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "GitHub Actions" in result
        assert "ruff" in result
        assert "mypy" in result

    def test_ci_falls_back_to_file_path(self) -> None:
        profile = make_profile(
            ci_tools=(DetectedTool(name="pytest", category=ToolCategory.TESTING),),
            ci_provider=None,
            ci_file_path=".github/workflows/test.yml",
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert ".github/workflows/test.yml" in result

    def test_no_ci_shows_cross_mark(self) -> None:
        profile = make_profile(
            ci_tools=(),
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "\u274c" in result

    def test_legacy_skip_focus_when_no_zones(self) -> None:
        """Fallback to guidance when no attention_zones but gaps present."""
        profile = make_profile(
            skip=("Code formatting (handled by CI)",),
            focus=("Security vulnerabilities",),
            gaps=(Gap(observation="No scanner", default_assumption="None"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "I'll skip" in result
        assert "I'll focus" in result

    def test_zones_replace_legacy_guidance(self) -> None:
        """When zones present, legacy skip/focus is NOT shown."""
        profile = make_profile(
            skip=("Should not appear",),
            focus=("Should not appear either",),
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "I'll skip" not in result
        assert "I'll focus" not in result
        assert "Not Covered" in result

    def test_footer_contains_reviewbot_hint(self) -> None:
        profile = make_profile(
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert ".reviewbot.md" in result
        assert "customize" in result

    def test_gaps_section_observation_and_assumption(self) -> None:
        profile = make_profile(
            gaps=(
                Gap(observation="No test framework detected", default_assumption="No testing"),
                Gap(observation="Hardcoded API key", default_assumption="Will be moved to env"),
            ),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "**Questions / Gaps:**" in result
        assert "- No test framework detected" in result
        assert "  *Assumption:* No testing" in result

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
        assert result is not None
        assert "  *Question:* Do you run security scans separately?" in result

    def test_russian_disclaimer_added(self) -> None:
        profile = make_profile(
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile, language="ru")
        assert result is not None
        assert "\u0440\u043e\u0441\u0441\u0438\u044f\u043d\u0438\u043d" in result

    def test_no_russian_disclaimer_for_other_languages(self) -> None:
        profile = make_profile(
            attention_zones=(_zone("security", "not_covered", reason="missing"),),
        )
        result = format_discovery_comment(profile, language="uk")
        assert result is not None
        assert "\u0440\u043e\u0441\u0441\u0438\u044f\u043d\u0438\u043d" not in result

    def test_recommendation_shown_in_weak_zone(self) -> None:
        """Recommendation text appears with lightbulb icon."""
        profile = make_profile(
            attention_zones=(
                _zone(
                    "testing",
                    "weakly_covered",
                    reason="no threshold",
                    recommendation="add --cov-fail-under=80",
                ),
            ),
        )
        result = format_discovery_comment(profile)
        assert result is not None
        assert "\U0001f4a1" in result
        assert "--cov-fail-under=80" in result


# ── TestShouldPostDiscoveryComment ───────────────────────────────────


class TestShouldPostDiscoveryComment:
    """Tests for should_post_discovery_comment."""

    def test_skip_when_no_issues(self) -> None:
        """No gaps, no uncovered zones -> False."""
        profile = make_profile(gaps=())
        assert should_post_discovery_comment(profile) is False

    def test_skip_when_only_well_covered(self) -> None:
        """Only well_covered zones -> False."""
        profile = make_profile(
            attention_zones=(_zone("linting", "well_covered", reason="ruff in CI"),),
        )
        assert should_post_discovery_comment(profile) is False

    def test_post_with_not_covered_zone(self) -> None:
        """not_covered zone -> True."""
        profile = make_profile(
            attention_zones=(_zone("security", "not_covered", reason="no SAST"),),
        )
        assert should_post_discovery_comment(profile) is True

    def test_post_with_weakly_covered_zone(self) -> None:
        """weakly_covered zone -> True."""
        profile = make_profile(
            attention_zones=(_zone("testing", "weakly_covered", reason="no gate"),),
        )
        assert should_post_discovery_comment(profile) is True

    def test_post_with_gaps(self) -> None:
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        assert should_post_discovery_comment(profile) is True

    def test_skip_when_reviewbot_md_exists(self) -> None:
        profile = make_profile(
            file_tree=("src/main.py", ".reviewbot.md"),
            attention_zones=(_zone("security", "not_covered", reason="no SAST"),),
        )
        assert should_post_discovery_comment(profile) is False

    def test_skip_when_reviewbot_md_even_verbose(self) -> None:
        """.reviewbot.md suppresses even verbose mode."""
        profile = make_profile(
            file_tree=("src/main.py", ".reviewbot.md"),
        )
        assert should_post_discovery_comment(profile, verbose=True) is False

    def test_skip_when_duplicate_exists(self) -> None:
        profile = make_profile(
            attention_zones=(_zone("security", "not_covered", reason="no SAST"),),
        )
        existing = (f"{DISCOVERY_COMMENT_HEADING}\n**Stack:** Python",)
        assert should_post_discovery_comment(profile, existing) is False

    def test_verbose_posts_without_gaps(self) -> None:
        """Verbose mode -> True even without gaps or uncovered zones."""
        profile = make_profile(gaps=())
        assert should_post_discovery_comment(profile, verbose=True) is True

    def test_verbose_skip_duplicate(self) -> None:
        """Verbose mode still skips duplicates."""
        profile = make_profile(gaps=())
        existing = (f"{DISCOVERY_COMMENT_HEADING}\nold content",)
        assert should_post_discovery_comment(profile, existing, verbose=True) is False

    def test_post_with_gaps_first_run(self) -> None:
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        assert should_post_discovery_comment(profile) is True

    def test_multiple_existing_comments_none_duplicate(self) -> None:
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = ("## Review\nFirst review", "LGTM", "Please fix the tests")
        assert should_post_discovery_comment(profile, existing) is True

    def test_duplicate_detected_among_many(self) -> None:
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        existing = (
            "## Review\nFirst review",
            f"old stuff\n{DISCOVERY_COMMENT_HEADING}\nold discovery",
            "LGTM",
        )
        assert should_post_discovery_comment(profile, existing) is False
