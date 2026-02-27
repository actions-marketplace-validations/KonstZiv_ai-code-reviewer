"""Fixture-based integration tests for DiscoveryOrchestrator.discover().

Each fixture in ``tests/fixtures/discovery/`` represents a realistic project.
A mock ``RepositoryProvider`` serves files from the fixture directory.
A mock ``LLMProvider`` returns canned responses for the ``empty`` fixture
(where deterministic data is insufficient).

Tests compare the actual ``discover()`` output against ``expected_profile.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from ai_reviewer.discovery.models import LLMDiscoveryResult
from ai_reviewer.discovery.orchestrator import DiscoveryOrchestrator
from ai_reviewer.integrations.repository import RepositoryMetadata
from ai_reviewer.llm.base import LLMResponse

if TYPE_CHECKING:
    from ai_reviewer.discovery.models import ProjectProfile

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "discovery"

# ── Fixture catalog ──────────────────────────────────────────────────

FIXTURE_NAMES = [
    "modern_python",
    "legacy_python",
    "javascript",
    "go_gitlab",
    "empty",
    "with_reviewbot_md",
]


def _load_expected(fixture_name: str) -> dict[str, object]:
    path = FIXTURES_DIR / fixture_name / "expected_profile.json"
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _collect_fixture_files(fixture_dir: Path) -> tuple[str, ...]:
    """Walk fixture directory and return relative paths (simulates file tree)."""
    paths: list[str] = []
    for p in sorted(fixture_dir.rglob("*")):
        if p.is_file() and p.name != "expected_profile.json":
            paths.append(str(p.relative_to(fixture_dir)))
    return tuple(paths)


def _build_mock_repo(
    fixture_name: str,
    expected: dict[str, object],
) -> MagicMock:
    """Build a mock RepositoryProvider that serves files from fixture dir."""
    fixture_dir = FIXTURES_DIR / fixture_name
    file_tree = _collect_fixture_files(fixture_dir)

    languages: dict[str, float] = expected.get("languages", {"Python": 100.0})  # type: ignore[assignment]

    repo = MagicMock()
    repo.get_languages.return_value = languages
    repo.get_metadata.return_value = RepositoryMetadata(
        name="owner/test-repo",
        default_branch="main",
        description=f"Fixture: {fixture_name}",
    )
    repo.get_file_tree.return_value = file_tree

    def _get_file_content(_repo_name: str, path: str, **_kw: object) -> str | None:
        file_path = fixture_dir / path
        if file_path.is_file() and file_path.name != "expected_profile.json":
            return file_path.read_text()
        return None

    repo.get_file_content.side_effect = _get_file_content
    return repo


def _build_mock_llm(fixture_name: str) -> MagicMock:
    """Build a mock LLMProvider. Only the ``empty`` fixture needs LLM."""
    llm = MagicMock()
    if fixture_name == "empty":
        llm.generate.return_value = LLMResponse(
            content=LLMDiscoveryResult(),
        )
    else:
        # LLM should NOT be called for fixtures with sufficient CI data
        llm.generate.side_effect = AssertionError(
            f"LLM unexpectedly called for fixture '{fixture_name}'"
        )
    return llm


# ── Assertion helpers ────────────────────────────────────────────────


def _assert_sorted_eq(
    actual: tuple[str, ...] | list[str],
    expected: object,
    msg: str,
) -> None:
    """Compare two sequences after sorting."""
    exp_list: list[str] = list(expected) if isinstance(expected, (list, tuple)) else []
    assert sorted(actual) == sorted(exp_list), msg


def _assert_profile_matches(
    profile: ProjectProfile,
    expected: dict[str, object],
    fixture_name: str,
) -> None:
    """Compare a ProjectProfile against expected_profile.json values."""
    msg = f"[{fixture_name}]"

    # Platform data
    assert profile.platform_data.primary_language == expected["primary_language"], msg

    # Language version
    if expected.get("language_version") is not None:
        assert profile.language_version == expected["language_version"], msg
    else:
        assert profile.language_version is None, msg

    # Package manager
    assert profile.package_manager == expected.get("package_manager"), msg

    # Framework
    assert profile.framework == expected.get("framework"), msg

    # CI insights
    if expected.get("ci_file_path"):
        assert profile.ci_insights is not None, f"{msg} ci_insights should not be None"
        assert profile.ci_insights.ci_file_path == expected["ci_file_path"], msg

    # CI provider
    assert profile.automated_checks.ci_provider == expected.get("ci_provider"), msg

    # Tool categories
    ac = profile.automated_checks
    _assert_sorted_eq(ac.linting, expected.get("linting", []), f"{msg} linting")
    _assert_sorted_eq(ac.formatting, expected.get("formatting", []), f"{msg} formatting")
    _assert_sorted_eq(ac.type_checking, expected.get("type_checking", []), f"{msg} type_checking")
    _assert_sorted_eq(ac.testing, expected.get("testing", []), f"{msg} testing")
    _assert_sorted_eq(ac.security, expected.get("security", []), f"{msg} security")

    # Review guidance
    g = profile.guidance
    _assert_sorted_eq(g.skip_in_review, expected.get("skip_in_review", []), f"{msg} skip")
    _assert_sorted_eq(g.focus_in_review, expected.get("focus_in_review", []), f"{msg} focus")

    # Conventions (only for reviewbot_md fixtures)
    if "conventions" in expected:
        _assert_sorted_eq(g.conventions, expected["conventions"], f"{msg} conventions")

    # Gaps
    expected_gaps: list[dict[str, str]] = expected.get("gaps", [])  # type: ignore[assignment]
    assert len(profile.gaps) == len(expected_gaps), f"{msg} gaps count"
    for gap, exp_gap in zip(profile.gaps, expected_gaps, strict=True):
        assert gap.observation == exp_gap["observation"], f"{msg} gap observation"
        assert gap.default_assumption == exp_gap["default_assumption"], f"{msg} gap assumption"


# ── Parametrized tests ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "fixture_name",
    [f for f in FIXTURE_NAMES if f not in ("empty", "with_reviewbot_md")],
    ids=lambda f: f,
)
def test_discover_deterministic(fixture_name: str) -> None:
    """Deterministic fixtures: CI has >= 2 tools, no LLM needed."""
    expected = _load_expected(fixture_name)
    mock_repo = _build_mock_repo(fixture_name, expected)
    mock_conversation = MagicMock()
    mock_conversation.get_bot_threads.return_value = ()
    mock_llm = _build_mock_llm(fixture_name)

    orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
    profile = orch.discover("owner/test-repo")

    _assert_profile_matches(profile, expected, fixture_name)
    # Verify LLM was NOT called
    mock_llm.generate.assert_not_called()


def test_discover_empty_uses_llm() -> None:
    """Empty fixture: no CI, no configs -> LLM fallback."""
    expected = _load_expected("empty")
    mock_repo = _build_mock_repo("empty", expected)
    mock_conversation = MagicMock()
    mock_conversation.get_bot_threads.return_value = ()
    mock_llm = _build_mock_llm("empty")

    orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
    profile = orch.discover("owner/test-repo")

    _assert_profile_matches(profile, expected, "empty")
    # Verify LLM WAS called
    mock_llm.generate.assert_called_once()


def test_discover_reviewbot_md_shortcut() -> None:
    """Reviewbot.md fixture: pipeline skipped entirely, parsed from markdown."""
    expected = _load_expected("with_reviewbot_md")
    mock_repo = _build_mock_repo("with_reviewbot_md", expected)
    mock_conversation = MagicMock()
    mock_llm = MagicMock()

    orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
    profile = orch.discover("owner/test-repo")

    _assert_profile_matches(profile, expected, "with_reviewbot_md")
    # No platform API calls (pipeline skipped)
    mock_repo.get_languages.assert_not_called()
    mock_repo.get_file_tree.assert_not_called()
    mock_llm.generate.assert_not_called()
