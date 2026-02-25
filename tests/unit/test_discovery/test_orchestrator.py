"""Tests for discovery.orchestrator — 4-layer Discovery pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai_reviewer.discovery.models import (
    CIInsights,
    DetectedTool,
    Gap,
    PlatformData,
    ProjectProfile,
    ToolCategory,
)
from ai_reviewer.discovery.orchestrator import (
    DiscoveryOrchestrator,
    _build_automated_checks,
    _build_review_guidance,
    _detect_gaps,
    _enrich_from_threads,
    _find_ci_files,
    _has_enough_data,
    _infer_ci_provider,
)
from ai_reviewer.discovery.prompts import LLMDiscoveryResponse
from ai_reviewer.integrations.conversation import (
    BotQuestion,
    BotThread,
    ThreadStatus,
)
from ai_reviewer.integrations.repository import RepositoryMetadata
from ai_reviewer.llm.base import LLMResponse

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_languages.return_value = {"Python": 90.0, "Shell": 10.0}
    repo.get_metadata.return_value = RepositoryMetadata(
        name="owner/repo",
        default_branch="main",
        topics=("python", "code-review"),
        description="Test repo",
    )
    repo.get_file_tree.return_value = (
        "src/main.py",
        "pyproject.toml",
        ".github/workflows/ci.yml",
    )
    repo.get_file_content.return_value = None
    return repo


@pytest.fixture
def mock_conversation() -> MagicMock:
    conv = MagicMock()
    conv.get_bot_threads.return_value = ()
    return conv


@pytest.fixture
def mock_llm() -> MagicMock:
    return MagicMock()


@pytest.fixture
def orchestrator(
    mock_repo: MagicMock,
    mock_conversation: MagicMock,
    mock_llm: MagicMock,
) -> DiscoveryOrchestrator:
    return DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)


# ── TestFindCiFiles ──────────────────────────────────────────────────


class TestFindCiFiles:
    """Tests for _find_ci_files."""

    def test_matches_github_workflow(self) -> None:
        tree = ("src/main.py", ".github/workflows/ci.yml", "README.md")
        assert _find_ci_files(tree) == (".github/workflows/ci.yml",)

    def test_matches_gitlab_ci(self) -> None:
        tree = (".gitlab-ci.yml", "src/app.py")
        assert _find_ci_files(tree) == (".gitlab-ci.yml",)

    def test_matches_makefile(self) -> None:
        tree = ("Makefile", "src/main.go")
        assert _find_ci_files(tree) == ("Makefile",)

    def test_no_ci_files(self) -> None:
        tree = ("src/main.py", "README.md")
        assert _find_ci_files(tree) == ()

    def test_multiple_matches(self) -> None:
        tree = (".github/workflows/ci.yml", ".github/workflows/deploy.yaml", "Makefile")
        result = _find_ci_files(tree)
        assert len(result) == 3


# ── TestHasEnoughData ────────────────────────────────────────────────


class TestHasEnoughData:
    """Tests for _has_enough_data."""

    def test_enough_with_two_tools(self) -> None:
        ci = CIInsights(
            ci_file_path="ci.yml",
            detected_tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="pytest", category=ToolCategory.TESTING),
            ),
        )
        assert _has_enough_data(ci) is True

    def test_not_enough_with_one_tool(self) -> None:
        ci = CIInsights(
            ci_file_path="ci.yml",
            detected_tools=(DetectedTool(name="ruff", category=ToolCategory.LINTING),),
        )
        assert _has_enough_data(ci) is False

    def test_not_enough_with_none(self) -> None:
        assert _has_enough_data(None) is False


# ── TestBuildAutomatedChecks ─────────────────────────────────────────


class TestBuildAutomatedChecks:
    """Tests for _build_automated_checks."""

    def test_maps_categories(self) -> None:
        ci = CIInsights(
            ci_file_path=".github/workflows/ci.yml",
            detected_tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="black", category=ToolCategory.FORMATTING),
                DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING),
                DetectedTool(name="pytest", category=ToolCategory.TESTING),
                DetectedTool(name="bandit", category=ToolCategory.SECURITY),
            ),
        )
        ac = _build_automated_checks(ci)
        assert ac.linting == ("ruff",)
        assert ac.formatting == ("black",)
        assert ac.type_checking == ("mypy",)
        assert ac.testing == ("pytest",)
        assert ac.security == ("bandit",)
        assert ac.ci_provider == "GitHub Actions"


# ── TestInferCiProvider ──────────────────────────────────────────────


class TestInferCiProvider:
    """Tests for _infer_ci_provider."""

    def test_github(self) -> None:
        assert _infer_ci_provider(".github/workflows/ci.yml") == "GitHub Actions"

    def test_gitlab(self) -> None:
        assert _infer_ci_provider(".gitlab-ci.yml") == "GitLab CI"

    def test_makefile(self) -> None:
        assert _infer_ci_provider("Makefile") == "Makefile"

    def test_unknown(self) -> None:
        assert _infer_ci_provider("some/other/ci.yml") is None


# ── TestBuildReviewGuidance ──────────────────────────────────────────


class TestBuildReviewGuidance:
    """Tests for _build_review_guidance."""

    def test_skip_when_tools_present(self) -> None:
        ci = CIInsights(
            ci_file_path="ci.yml",
            detected_tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="black", category=ToolCategory.FORMATTING),
                DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING),
            ),
        )
        g = _build_review_guidance(ci)
        assert len(g.skip_in_review) == 3
        assert any("lint" in s.lower() for s in g.skip_in_review)

    def test_focus_when_tools_missing(self) -> None:
        ci = CIInsights(ci_file_path="ci.yml", detected_tools=())
        g = _build_review_guidance(ci)
        assert any("security" in f.lower() for f in g.focus_in_review)
        assert any("test" in f.lower() for f in g.focus_in_review)


# ── TestDetectGaps ───────────────────────────────────────────────────


class TestDetectGaps:
    """Tests for _detect_gaps."""

    def test_no_gaps_when_all_covered(self) -> None:
        ci = CIInsights(
            ci_file_path="ci.yml",
            detected_tools=(
                DetectedTool(name="pytest", category=ToolCategory.TESTING),
                DetectedTool(name="bandit", category=ToolCategory.SECURITY),
            ),
        )
        assert _detect_gaps(ci) == ()

    def test_gaps_when_testing_missing(self) -> None:
        ci = CIInsights(
            ci_file_path="ci.yml",
            detected_tools=(DetectedTool(name="ruff", category=ToolCategory.LINTING),),
        )
        gaps = _detect_gaps(ci)
        assert any("test" in g.observation.lower() for g in gaps)


# ── TestEnrichFromThreads ────────────────────────────────────────────


class TestEnrichFromThreads:
    """Tests for _enrich_from_threads."""

    def test_removes_answered_gaps(self) -> None:
        profile = _make_profile(
            gaps=(
                Gap(
                    observation="No tests",
                    question="What test framework?",
                    default_assumption="None",
                ),
                Gap(
                    observation="No SAST",
                    default_assumption="No security scanning",
                ),
            ),
        )
        threads = (
            BotThread(
                thread_id="t1",
                platform_thread_id="p1",
                mr_id=1,
                questions=(
                    BotQuestion(
                        question_id="Q1",
                        text="What test framework?",
                        default_assumption="None",
                    ),
                ),
                status=ThreadStatus.ANSWERED,
            ),
        )
        result = _enrich_from_threads(profile, threads)
        assert len(result.gaps) == 1
        assert result.gaps[0].observation == "No SAST"

    def test_no_change_when_no_threads(self) -> None:
        profile = _make_profile(
            gaps=(Gap(observation="X", default_assumption="Y"),),
        )
        result = _enrich_from_threads(profile, ())
        assert result is profile

    def test_no_change_when_pending(self) -> None:
        profile = _make_profile(
            gaps=(
                Gap(
                    observation="No tests",
                    question="What test framework?",
                    default_assumption="None",
                ),
            ),
        )
        threads = (
            BotThread(
                thread_id="t1",
                platform_thread_id="p1",
                mr_id=1,
                questions=(
                    BotQuestion(
                        question_id="Q1",
                        text="What test framework?",
                        default_assumption="None",
                    ),
                ),
                status=ThreadStatus.PENDING,
            ),
        )
        result = _enrich_from_threads(profile, threads)
        assert len(result.gaps) == 1


# ── TestDiscoveryOrchestrator — Scenarios ────────────────────────────


class TestScenarioFullStack:
    """Scenario 1: CI + configs -> deterministic profile, 0 LLM calls."""

    def test_full_stack_no_llm(
        self,
        orchestrator: DiscoveryOrchestrator,
        mock_repo: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        # CI file returns valid YAML with enough tools
        ci_yaml = """
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check .
      - run: mypy src/
      - run: pytest
"""
        mock_repo.get_file_content.side_effect = lambda _repo, path, **_kw: (
            ci_yaml if path == ".github/workflows/ci.yml" else None
        )

        profile = orchestrator.discover("owner/repo")

        assert profile.platform_data.primary_language == "Python"
        assert profile.automated_checks.linting
        mock_llm.generate.assert_not_called()


class TestScenarioNoCI:
    """Scenario 2: No CI -> LLM interpretation needed."""

    def test_no_ci_uses_llm(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        # No CI files in tree
        mock_repo.get_file_tree.return_value = ("src/main.py", "pyproject.toml")
        mock_repo.get_file_content.return_value = None

        llm_response = LLMResponse(
            content=LLMDiscoveryResponse(
                framework="FastAPI",
                skip_in_review=["formatting"],
                focus_in_review=["security"],
                conventions=["Google docstrings"],
            ),
        )
        mock_llm.generate.return_value = llm_response

        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        profile = orch.discover("owner/repo")

        mock_llm.generate.assert_called_once()
        assert profile.framework == "FastAPI"
        assert "formatting" in profile.guidance.skip_in_review


class TestScenarioReviewbotMd:
    """Scenario: .reviewbot.md exists -> skip pipeline entirely."""

    def test_reviewbot_md_shortcut(
        self,
        orchestrator: DiscoveryOrchestrator,
        mock_repo: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        reviewbot_content = "# .reviewbot.md\n\n## Stack\n- **Language:** Rust 1.78\n"
        mock_repo.get_file_content.return_value = reviewbot_content

        profile = orchestrator.discover("owner/repo")

        assert profile.platform_data.primary_language == "Rust"
        # No further API calls needed
        mock_repo.get_languages.assert_not_called()
        mock_llm.generate.assert_not_called()


class TestScenarioWithAnswers:
    """Scenario 4: Previous threads answered -> gaps removed."""

    def test_answered_gaps_removed(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        # Setup: no CI, LLM returns gaps
        mock_repo.get_file_tree.return_value = ("src/main.py",)
        mock_repo.get_file_content.return_value = None

        llm_response = LLMResponse(
            content=LLMDiscoveryResponse(
                gaps=[
                    Gap(
                        observation="No test framework",
                        question="What test framework?",
                        default_assumption="No tests",
                    ),
                ],
            ),
        )
        mock_llm.generate.return_value = llm_response

        # Previous thread answered the question
        mock_conversation.get_bot_threads.return_value = (
            BotThread(
                thread_id="t1",
                platform_thread_id="p1",
                mr_id=42,
                questions=(
                    BotQuestion(
                        question_id="Q1",
                        text="What test framework?",
                        default_assumption="No tests",
                    ),
                ),
                status=ThreadStatus.ANSWERED,
            ),
        )

        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        profile = orch.discover("owner/repo", mr_id=42)

        # Gap should be removed since it was answered
        assert len(profile.gaps) == 0
        # No new questions posted
        mock_conversation.post_question_comment.assert_not_called()


class TestScenarioGracefulDegradation:
    """Error handling: each layer can fail -> continue."""

    def test_llm_failure_uses_fallback(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        mock_repo.get_file_tree.return_value = ("src/main.py",)
        mock_repo.get_file_content.return_value = None
        mock_llm.generate.side_effect = RuntimeError("LLM down")

        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        profile = orch.discover("owner/repo")

        # Should not crash, returns fallback profile
        assert profile.platform_data.primary_language == "Python"

    def test_conversation_failure_continues(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        mock_repo.get_file_tree.return_value = ("src/main.py",)
        mock_repo.get_file_content.return_value = None
        mock_conversation.get_bot_threads.side_effect = RuntimeError("API down")

        llm_response = LLMResponse(content=LLMDiscoveryResponse())
        mock_llm.generate.return_value = llm_response

        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        # Should not crash
        profile = orch.discover("owner/repo", mr_id=1)
        assert profile is not None


# ── Helpers ──────────────────────────────────────────────────────────


def _make_profile(
    *,
    gaps: tuple[Gap, ...] = (),
) -> ProjectProfile:
    return ProjectProfile(
        platform_data=PlatformData(
            languages={"Python": 100.0},
            primary_language="Python",
        ),
        gaps=gaps,
    )
