"""Edge-case tests for the Discovery pipeline (Task 4.2).

Covers:
- Monorepo with 3+ languages (primary detection, multi-language CI tools).
- INFO-level logging verification via caplog.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from ai_reviewer.discovery.models import LLMDiscoveryResult
from ai_reviewer.discovery.orchestrator import DiscoveryOrchestrator
from ai_reviewer.integrations.repository import RepositoryMetadata
from ai_reviewer.llm.base import LLMResponse

# ── Shared fixtures ──────────────────────────────────────────────────


@pytest.fixture
def mock_conversation() -> MagicMock:
    conv = MagicMock()
    conv.get_bot_threads.return_value = ()
    return conv


# ── Monorepo tests ───────────────────────────────────────────────────


_MONOREPO_CI_YAML = """\
name: CI
on: [push]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check backend/
      - run: mypy backend/
      - run: pytest backend/tests/
  frontend:
    runs-on: ubuntu-latest
    steps:
      - run: npx eslint frontend/
      - run: npx prettier --check frontend/
      - run: npx jest
  go-service:
    runs-on: ubuntu-latest
    steps:
      - run: go vet ./...
      - run: go test ./...
"""


class TestMonorepoMultipleLanguages:
    """Monorepo with Python + TypeScript + Go in a single CI file."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_languages.return_value = {
            "Python": 45.0,
            "TypeScript": 35.0,
            "Go": 20.0,
        }
        repo.get_metadata.return_value = RepositoryMetadata(
            name="org/monorepo",
            default_branch="main",
            topics=("monorepo",),
            description="Multi-language monorepo",
        )
        repo.get_file_tree.return_value = (
            "backend/src/main.py",
            "backend/pyproject.toml",
            "frontend/src/index.ts",
            "frontend/package.json",
            "services/api/main.go",
            "services/api/go.mod",
            ".github/workflows/ci.yml",
        )
        repo.get_file_content.side_effect = lambda _repo, path, **_kw: (
            _MONOREPO_CI_YAML if path == ".github/workflows/ci.yml" else None
        )
        return repo

    def test_primary_language_is_highest_percentage(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
    ) -> None:
        """Primary language = Python (45% > TypeScript 35% > Go 20%)."""
        mock_llm = MagicMock()
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        profile = orch.discover("org/monorepo")

        assert profile.platform_data.primary_language == "Python"
        assert profile.platform_data.languages == {
            "Python": 45.0,
            "TypeScript": 35.0,
            "Go": 20.0,
        }

    def test_tools_from_all_languages_detected(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
    ) -> None:
        """CI tools from Python, JS, and Go jobs are all detected."""
        mock_llm = MagicMock()
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        profile = orch.discover("org/monorepo")

        assert profile.ci_insights is not None
        tool_names = {t.name for t in profile.ci_insights.detected_tools}
        # Python tools
        assert "ruff" in tool_names
        assert "mypy" in tool_names
        assert "pytest" in tool_names
        # JS tools
        assert "eslint" in tool_names
        assert "prettier" in tool_names
        assert "jest" in tool_names
        # Go tools
        assert "go vet" in tool_names
        assert "go test" in tool_names

    def test_deterministic_path_no_llm(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
    ) -> None:
        """8 tools detected -> deterministic path, no LLM call."""
        mock_llm = MagicMock()
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        orch.discover("org/monorepo")

        mock_llm.generate.assert_not_called()

    def test_skip_and_focus_reflect_all_categories(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
    ) -> None:
        """Review guidance reflects coverage across all languages."""
        mock_llm = MagicMock()
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        profile = orch.discover("org/monorepo")

        # Linting + formatting + type checking covered -> should skip
        skip_lower = [s.lower() for s in profile.guidance.skip_in_review]
        for keyword in ("lint", "formatting", "type"):
            assert any(keyword in s for s in skip_lower), (
                f"'{keyword}' not found in skip_in_review: {profile.guidance.skip_in_review}"
            )
        # Security not covered -> should focus
        focus_lower = [f.lower() for f in profile.guidance.focus_in_review]
        assert any("security" in f for f in focus_lower), (
            f"'security' not found in focus_in_review: {profile.guidance.focus_in_review}"
        )


# ── Caplog logging tests ─────────────────────────────────────────────

_ORCHESTRATOR_LOGGER = "ai_reviewer.discovery.orchestrator"

_SIMPLE_CI_YAML = """\
name: CI
on: [push]
jobs:
  t:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check .
      - run: pytest
"""


class TestDiscoveryLogging:
    """Verify INFO-level log messages from the orchestrator."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_languages.return_value = {"Python": 100.0}
        repo.get_metadata.return_value = RepositoryMetadata(
            name="owner/repo",
            default_branch="main",
        )
        repo.get_file_tree.return_value = (
            "src/main.py",
            "pyproject.toml",
            ".github/workflows/ci.yml",
        )
        repo.get_file_content.return_value = None
        return repo

    def test_logs_file_tree_size(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Orchestrator logs how many files are in the tree."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResponse(
            content=LLMDiscoveryResult(),
        )
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)

        with caplog.at_level(logging.INFO, logger=_ORCHESTRATOR_LOGGER):
            orch.discover("owner/repo")

        assert any("3 files in tree" in msg for msg in caplog.messages)

    def test_logs_ci_files_found(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Orchestrator logs which CI files were detected."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResponse(
            content=LLMDiscoveryResult(),
        )
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)

        with caplog.at_level(logging.INFO, logger=_ORCHESTRATOR_LOGGER):
            orch.discover("owner/repo")

        assert any("ci.yml" in msg for msg in caplog.messages)

    def test_logs_no_ci_files(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When no CI files exist, logs '(none)'."""
        mock_repo.get_file_tree.return_value = ("src/main.py", "README.md")
        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResponse(
            content=LLMDiscoveryResult(),
        )
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)

        with caplog.at_level(logging.INFO, logger=_ORCHESTRATOR_LOGGER):
            orch.discover("owner/repo")

        assert any("(none)" in msg for msg in caplog.messages)

    def test_logs_ci_content_fetched(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Logs chars fetched when CI file content is retrieved."""
        ci_yaml = _SIMPLE_CI_YAML
        mock_repo.get_file_content.side_effect = lambda _r, path, **_kw: (
            ci_yaml if path == ".github/workflows/ci.yml" else None
        )
        mock_llm = MagicMock()
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)

        with caplog.at_level(logging.INFO, logger=_ORCHESTRATOR_LOGGER):
            orch.discover("owner/repo")

        assert any("chars fetched" in msg for msg in caplog.messages)

    def test_logs_ci_no_content(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Logs 'no content returned' when CI file is missing."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResponse(
            content=LLMDiscoveryResult(),
        )
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)

        with caplog.at_level(logging.INFO, logger=_ORCHESTRATOR_LOGGER):
            orch.discover("owner/repo")

        assert any("no content returned" in msg for msg in caplog.messages)

    def test_logs_tools_detected_count(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Logs how many tools were detected from each CI file."""
        ci_yaml = _SIMPLE_CI_YAML
        mock_repo.get_file_content.side_effect = lambda _r, path, **_kw: (
            ci_yaml if path == ".github/workflows/ci.yml" else None
        )
        mock_llm = MagicMock()
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)

        with caplog.at_level(logging.INFO, logger=_ORCHESTRATOR_LOGGER):
            orch.discover("owner/repo")

        assert any("tool(s) detected" in msg for msg in caplog.messages)

    def test_logs_reviewbot_md_shortcut(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Logs when .reviewbot.md is found and pipeline is skipped."""
        mock_repo.get_file_content.return_value = (
            "# .reviewbot.md\n\n## Stack\n- **Language:** Rust\n"
        )
        mock_llm = MagicMock()
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)

        with caplog.at_level(logging.INFO, logger=_ORCHESTRATOR_LOGGER):
            orch.discover("owner/repo")

        assert any(".reviewbot.md" in msg and "skipping" in msg for msg in caplog.messages)

    def test_logs_ci_analysis_failure_as_warning(
        self,
        mock_repo: MagicMock,
        mock_conversation: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """CI parse failures logged at WARNING level."""
        mock_repo.get_file_content.side_effect = lambda _r, path, **_kw: (
            _SIMPLE_CI_YAML if path == ".github/workflows/ci.yml" else None
        )
        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResponse(
            content=LLMDiscoveryResult(),
        )
        orch = DiscoveryOrchestrator(mock_repo, mock_conversation, mock_llm)
        # Force the CI analyzer to raise using patch.object
        with (
            patch.object(orch._ci_analyzer, "analyze", side_effect=ValueError("broken")),
            caplog.at_level(logging.WARNING, logger=_ORCHESTRATOR_LOGGER),
        ):
            orch.discover("owner/repo")

        assert any("Failed to analyze CI file" in msg for msg in caplog.messages)
