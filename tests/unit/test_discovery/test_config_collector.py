"""Tests for discovery.config_collector — config collection layer."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from ai_reviewer.discovery.config_collector import (
    MAX_CHARS_PER_FILE,
    MAX_CHARS_TOTAL,
    ConfigCollector,
    ConfigContent,
    SmartConfigSelector,
)
from ai_reviewer.discovery.models import CIInsights, DetectedTool, PlatformData, ToolCategory

# ── Helpers ──────────────────────────────────────────────────────────


def _make_platform_data(
    *,
    languages: dict[str, float] | None = None,
    file_tree: tuple[str, ...] = (),
) -> PlatformData:
    return PlatformData(
        languages=languages or {"Python": 90.0},
        primary_language="Python",
        file_tree=file_tree,
    )


def _make_ci_insights(
    *,
    tools: tuple[DetectedTool, ...] = (),
) -> CIInsights:
    return CIInsights(ci_file_path=".github/workflows/ci.yml", detected_tools=tools)


def _tool(name: str, category: ToolCategory = ToolCategory.LINTING) -> DetectedTool:
    return DetectedTool(name=name, category=category)


# ── TestConfigContent ────────────────────────────────────────────────


class TestConfigContent:
    """ConfigContent model tests."""

    def test_frozen(self) -> None:
        cfg = ConfigContent(path="a.toml", content="x", size_chars=1)
        with pytest.raises(ValidationError):
            cfg.path = "b.toml"  # type: ignore[misc]

    def test_defaults(self) -> None:
        cfg = ConfigContent(path="a.toml", content="x", size_chars=1)
        assert cfg.truncated is False

    def test_size_chars_non_negative(self) -> None:
        with pytest.raises(ValidationError, match="greater_than_equal"):
            ConfigContent(path="a.toml", content="x", size_chars=-1)


# ── TestSmartConfigSelector ──────────────────────────────────────────


class TestSmartConfigSelector:
    """SmartConfigSelector tests."""

    @pytest.fixture
    def selector(self) -> SmartConfigSelector:
        return SmartConfigSelector()

    def test_targeted_finds_tool_configs(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(
            file_tree=("pyproject.toml", "ruff.toml", "src/main.py"),
        )
        ci = _make_ci_insights(tools=(_tool("ruff"),))
        result = selector.select_targeted(pd, ci)
        assert "pyproject.toml" in result
        assert "ruff.toml" in result

    def test_targeted_ignores_missing_files(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(file_tree=("src/main.py",))
        ci = _make_ci_insights(tools=(_tool("ruff"),))
        result = selector.select_targeted(pd, ci)
        assert result == ()

    def test_targeted_deduplicates(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(
            file_tree=("pyproject.toml", "setup.cfg"),
        )
        ci = _make_ci_insights(
            tools=(
                _tool("ruff"),
                _tool("mypy", ToolCategory.TYPE_CHECKING),
            ),
        )
        result = selector.select_targeted(pd, ci)
        assert result.count("pyproject.toml") == 1

    def test_targeted_empty_tools(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(file_tree=("pyproject.toml",))
        ci = _make_ci_insights(tools=())
        assert selector.select_targeted(pd, ci) == ()

    def test_broad_finds_language_configs(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(
            languages={"Python": 90.0},
            file_tree=("pyproject.toml", "setup.cfg", "src/main.py"),
        )
        result = selector.select_broad(pd)
        assert "pyproject.toml" in result
        assert "setup.cfg" in result

    def test_broad_ignores_unknown_language(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(
            languages={"Haskell": 100.0},
            file_tree=("Main.hs",),
        )
        assert selector.select_broad(pd) == ()

    def test_broad_ignores_missing_files(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(
            languages={"Python": 90.0},
            file_tree=("src/main.py",),
        )
        assert selector.select_broad(pd) == ()

    def test_broad_empty_languages(self, selector: SmartConfigSelector) -> None:
        pd = PlatformData(
            languages={},
            primary_language="Unknown",
            file_tree=("pyproject.toml",),
        )
        assert selector.select_broad(pd) == ()

    def test_results_sorted(self, selector: SmartConfigSelector) -> None:
        pd = _make_platform_data(
            file_tree=("tox.ini", "pyproject.toml", "setup.cfg", "setup.py"),
        )
        ci = _make_ci_insights(
            tools=(
                _tool("ruff"),
                _tool("mypy", ToolCategory.TYPE_CHECKING),
                _tool("flake8"),
            ),
        )
        result = selector.select_targeted(pd, ci)
        assert list(result) == sorted(result)


# ── TestConfigCollector ──────────────────────────────────────────────


class TestConfigCollector:
    """ConfigCollector tests."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def collector(self, mock_repo: MagicMock) -> ConfigCollector:
        return ConfigCollector(mock_repo)

    def test_collect_reads_files(self, mock_repo: MagicMock, collector: ConfigCollector) -> None:
        mock_repo.get_file_content.return_value = "[tool.ruff]\nline-length = 88"
        result = collector.collect("owner/repo", ["pyproject.toml"])
        assert len(result) == 1
        assert result[0].path == "pyproject.toml"
        assert result[0].content == "[tool.ruff]\nline-length = 88"
        assert result[0].truncated is False
        mock_repo.get_file_content.assert_called_once_with("owner/repo", "pyproject.toml")

    def test_collect_skips_none(self, mock_repo: MagicMock, collector: ConfigCollector) -> None:
        mock_repo.get_file_content.return_value = None
        result = collector.collect("owner/repo", ["missing.toml"])
        assert result == ()

    def test_collect_truncates_large_file(
        self, mock_repo: MagicMock, collector: ConfigCollector
    ) -> None:
        big = "x" * (MAX_CHARS_PER_FILE + 500)
        mock_repo.get_file_content.return_value = big
        result = collector.collect("owner/repo", ["big.toml"])
        assert len(result) == 1
        assert result[0].truncated is True
        assert result[0].size_chars == MAX_CHARS_PER_FILE
        assert len(result[0].content) == MAX_CHARS_PER_FILE

    def test_collect_stops_at_total_limit(
        self, mock_repo: MagicMock, collector: ConfigCollector
    ) -> None:
        chunk = "x" * MAX_CHARS_PER_FILE
        mock_repo.get_file_content.return_value = chunk
        paths = [f"cfg{i}.toml" for i in range(6)]
        result = collector.collect("owner/repo", paths)
        # MAX_CHARS_TOTAL / MAX_CHARS_PER_FILE = 50000 / 10000 = 5
        assert len(result) == 5

    def test_collect_respects_remaining_budget(
        self, mock_repo: MagicMock, collector: ConfigCollector
    ) -> None:
        """Last file is truncated to remaining budget, not per-file limit."""
        # 4 files x 10K = 40K used, remaining = 10K -> 5th fits fully
        # 5 files x 10K = 50K used, remaining = 0 -> 6th skipped
        # But if 4 files x 10K = 40K, and 5th is 15K -> truncated to 10K (remaining)
        calls = []

        def side_effect(_repo: str, path: str) -> str:
            calls.append(path)
            if path == "cfg4.toml":
                return "y" * (MAX_CHARS_PER_FILE + 5000)
            return "x" * MAX_CHARS_PER_FILE

        mock_repo.get_file_content.side_effect = side_effect
        paths = [f"cfg{i}.toml" for i in range(6)]
        result = collector.collect("owner/repo", paths)
        assert len(result) == 5
        total = sum(c.size_chars for c in result)
        assert total <= MAX_CHARS_TOTAL

    def test_collect_total_never_exceeded(
        self, mock_repo: MagicMock, collector: ConfigCollector
    ) -> None:
        """Total chars never exceeds MAX_CHARS_TOTAL even with large files."""
        # 45K used after 4.5 files worth, next file should be capped
        small = "a" * 9000  # 9K each → 5 files = 45K, 6th gets 5K budget
        big = "b" * MAX_CHARS_PER_FILE  # 10K but only 5K budget remains

        def side_effect(_repo: str, path: str) -> str:
            if path == "cfg5.toml":
                return big
            return small

        mock_repo.get_file_content.side_effect = side_effect
        paths = [f"cfg{i}.toml" for i in range(7)]
        result = collector.collect("owner/repo", paths)
        total = sum(c.size_chars for c in result)
        assert total <= MAX_CHARS_TOTAL
        # cfg5 should be truncated to remaining budget (50000 - 45000 = 5000)
        cfg5 = next(c for c in result if c.path == "cfg5.toml")
        assert cfg5.truncated is True
        assert cfg5.size_chars == MAX_CHARS_TOTAL - 5 * 9000  # 5000

    def test_collect_empty_paths(self, collector: ConfigCollector) -> None:
        assert collector.collect("owner/repo", []) == ()

    def test_collect_size_chars_correct(
        self, mock_repo: MagicMock, collector: ConfigCollector
    ) -> None:
        content = "abc\ndef"
        mock_repo.get_file_content.return_value = content
        result = collector.collect("owner/repo", ["f.toml"])
        assert result[0].size_chars == len(content)
