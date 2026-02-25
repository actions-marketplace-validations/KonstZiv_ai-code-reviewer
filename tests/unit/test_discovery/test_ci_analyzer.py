"""Tests for discovery.ci_analyzer — deterministic CI pipeline parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_reviewer.discovery.ci_analyzer import CIPipelineAnalyzer
from ai_reviewer.discovery.models import ToolCategory

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "ci"


@pytest.fixture
def analyzer() -> CIPipelineAnalyzer:
    """Create a CIPipelineAnalyzer instance."""
    return CIPipelineAnalyzer()


def _load_fixture(name: str) -> str:
    """Load a CI fixture file by name."""
    return (FIXTURES_DIR / name).read_text()


def _tool_names(insights: object) -> set[str]:
    """Extract tool names from CIInsights as a set."""
    return {t.name for t in insights.detected_tools}  # type: ignore[union-attr]


def _tool_categories(insights: object) -> dict[str, str]:
    """Extract tool name → category mapping."""
    return {t.name: t.category for t in insights.detected_tools}  # type: ignore[union-attr]


# ── GitHub Actions: modern Python ────────────────────────────────────


class TestGitHubActionsPythonModern:
    """Tests for modern Python GitHub Actions workflow."""

    @pytest.fixture(autouse=True)
    def _setup(self, analyzer: CIPipelineAnalyzer) -> None:
        content = _load_fixture("github_actions_python_modern.yml")
        self.insights = analyzer.analyze(content, ".github/workflows/ci.yml")

    def test_ci_file_path(self) -> None:
        assert self.insights.ci_file_path == ".github/workflows/ci.yml"

    def test_raw_yaml_preserved(self) -> None:
        assert "ruff check" in self.insights.raw_yaml

    def test_detects_ruff(self) -> None:
        assert "ruff" in _tool_names(self.insights)

    def test_detects_ruff_format(self) -> None:
        assert "ruff format" in _tool_names(self.insights)

    def test_detects_mypy(self) -> None:
        assert "mypy" in _tool_names(self.insights)

    def test_detects_pytest(self) -> None:
        assert "pytest" in _tool_names(self.insights)

    def test_detects_bandit(self) -> None:
        assert "bandit" in _tool_names(self.insights)

    def test_tool_categories(self) -> None:
        cats = _tool_categories(self.insights)
        assert cats["ruff"] == ToolCategory.LINTING
        assert cats["ruff format"] == ToolCategory.FORMATTING
        assert cats["mypy"] == ToolCategory.TYPE_CHECKING
        assert cats["pytest"] == ToolCategory.TESTING
        assert cats["bandit"] == ToolCategory.SECURITY

    def test_python_version(self) -> None:
        assert self.insights.python_version == "3.13"

    def test_package_manager_uv(self) -> None:
        assert self.insights.package_manager == "uv"

    def test_services(self) -> None:
        assert "postgres" in self.insights.services
        assert "redis" in self.insights.services

    def test_coverage_threshold(self) -> None:
        assert self.insights.min_coverage == 80

    def test_deployment_targets(self) -> None:
        assert "pypi" in self.insights.deployment_targets

    def test_tool_command_preserved(self) -> None:
        ruff_tool = next(t for t in self.insights.detected_tools if t.name == "ruff")
        assert "ruff check" in ruff_tool.command


# ── GitHub Actions: legacy Python ────────────────────────────────────


class TestGitHubActionsPythonLegacy:
    """Tests for legacy Python GitHub Actions workflow."""

    @pytest.fixture(autouse=True)
    def _setup(self, analyzer: CIPipelineAnalyzer) -> None:
        content = _load_fixture("github_actions_python_legacy.yml")
        self.insights = analyzer.analyze(content, ".github/workflows/tests.yml")

    def test_detects_flake8(self) -> None:
        assert "flake8" in _tool_names(self.insights)

    def test_detects_black(self) -> None:
        assert "black" in _tool_names(self.insights)

    def test_detects_isort(self) -> None:
        assert "isort" in _tool_names(self.insights)

    def test_detects_pytest(self) -> None:
        assert "pytest" in _tool_names(self.insights)

    def test_python_version_from_matrix(self) -> None:
        # Should detect first version from matrix
        assert self.insights.python_version in ("3.9", "3.10", "3.11")

    def test_package_manager_pip(self) -> None:
        assert self.insights.package_manager == "pip"

    def test_no_coverage_threshold(self) -> None:
        assert self.insights.min_coverage is None

    def test_no_services(self) -> None:
        assert self.insights.services == ()


# ── GitHub Actions: JavaScript ───────────────────────────────────────


class TestGitHubActionsJavaScript:
    """Tests for JavaScript GitHub Actions workflow."""

    @pytest.fixture(autouse=True)
    def _setup(self, analyzer: CIPipelineAnalyzer) -> None:
        content = _load_fixture("github_actions_js.yml")
        self.insights = analyzer.analyze(content, ".github/workflows/node.yml")

    def test_detects_eslint(self) -> None:
        assert "eslint" in _tool_names(self.insights)

    def test_detects_prettier(self) -> None:
        assert "prettier" in _tool_names(self.insights)

    def test_detects_tsc(self) -> None:
        assert "tsc" in _tool_names(self.insights)

    def test_detects_jest(self) -> None:
        assert "jest" in _tool_names(self.insights)

    def test_detects_npm_audit(self) -> None:
        assert "npm audit" in _tool_names(self.insights)

    def test_node_version(self) -> None:
        assert self.insights.node_version == "20"

    def test_package_manager_npm(self) -> None:
        assert self.insights.package_manager == "npm"

    def test_coverage_threshold(self) -> None:
        assert self.insights.min_coverage == 75


# ── GitLab CI: Go ────────────────────────────────────────────────────


class TestGitLabCIGo:
    """Tests for Go GitLab CI configuration."""

    @pytest.fixture(autouse=True)
    def _setup(self, analyzer: CIPipelineAnalyzer) -> None:
        content = _load_fixture("gitlab_ci_go.yml")
        self.insights = analyzer.analyze(content, ".gitlab-ci.yml")

    def test_detects_go_vet(self) -> None:
        assert "go vet" in _tool_names(self.insights)

    def test_detects_golangci_lint(self) -> None:
        assert "golangci-lint" in _tool_names(self.insights)

    def test_detects_go_test(self) -> None:
        assert "go test" in _tool_names(self.insights)

    def test_detects_gofmt(self) -> None:
        assert "gofmt" in _tool_names(self.insights)

    def test_go_version(self) -> None:
        assert self.insights.go_version == "1.22"

    def test_services(self) -> None:
        assert "postgres" in self.insights.services

    def test_deployment_docker(self) -> None:
        assert "docker_registry" in self.insights.deployment_targets


# ── Makefile ─────────────────────────────────────────────────────────


class TestMakefile:
    """Tests for Makefile as CI proxy."""

    @pytest.fixture(autouse=True)
    def _setup(self, analyzer: CIPipelineAnalyzer) -> None:
        content = _load_fixture("makefile_only.txt")
        self.insights = analyzer.analyze_makefile(content)

    def test_ci_file_path(self) -> None:
        assert self.insights.ci_file_path == "Makefile"

    def test_detects_ruff(self) -> None:
        assert "ruff" in _tool_names(self.insights)

    def test_detects_ruff_format(self) -> None:
        assert "ruff format" in _tool_names(self.insights)

    def test_detects_mypy(self) -> None:
        assert "mypy" in _tool_names(self.insights)

    def test_detects_pytest(self) -> None:
        assert "pytest" in _tool_names(self.insights)

    def test_detects_pre_commit(self) -> None:
        assert "pre-commit" in _tool_names(self.insights)

    def test_package_manager_uv(self) -> None:
        assert self.insights.package_manager == "uv"

    def test_coverage_threshold(self) -> None:
        assert self.insights.min_coverage == 90

    def test_no_services_in_makefile(self) -> None:
        assert self.insights.services == ()


# ── Edge cases ───────────────────────────────────────────────────────


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_yaml(self, analyzer: CIPipelineAnalyzer) -> None:
        insights = analyzer.analyze("", "empty.yml")
        assert insights.ci_file_path == "empty.yml"
        assert insights.detected_tools == ()

    def test_invalid_yaml(self, analyzer: CIPipelineAnalyzer) -> None:
        insights = analyzer.analyze("not: [valid: yaml: !!!", "bad.yml")
        assert insights.ci_file_path == "bad.yml"
        assert insights.detected_tools == ()

    def test_yaml_with_only_scalars(self, analyzer: CIPipelineAnalyzer) -> None:
        insights = analyzer.analyze("name: CI\non: push", "minimal.yml")
        assert insights.detected_tools == ()

    def test_no_duplicate_tools(self, analyzer: CIPipelineAnalyzer) -> None:
        yaml_content = """
jobs:
  lint:
    steps:
      - run: ruff check src/
      - run: ruff check tests/
"""
        insights = analyzer.analyze(yaml_content)
        ruff_tools = [t for t in insights.detected_tools if t.name == "ruff"]
        assert len(ruff_tools) == 1

    def test_deeply_nested_commands(self, analyzer: CIPipelineAnalyzer) -> None:
        yaml_content = """
jobs:
  build:
    steps:
      - name: Lint
        run: |
          ruff check .
          mypy src/
"""
        insights = analyzer.analyze(yaml_content)
        names = _tool_names(insights)
        assert "ruff" in names
        assert "mypy" in names

    def test_multiline_run_command(self, analyzer: CIPipelineAnalyzer) -> None:
        yaml_content = """
jobs:
  test:
    steps:
      - run: pytest tests/ --cov --cov-fail-under=95
"""
        insights = analyzer.analyze(yaml_content)
        assert "pytest" in _tool_names(insights)
        assert insights.min_coverage == 95

    def test_gitlab_services_as_list(self, analyzer: CIPipelineAnalyzer) -> None:
        yaml_content = """
test:
  services:
    - postgres:15
    - redis:7-alpine
  script:
    - go test ./...
"""
        insights = analyzer.analyze(yaml_content)
        assert "postgres" in insights.services
        assert "redis" in insights.services

    def test_ruff_format_only_no_false_linting(self, analyzer: CIPipelineAnalyzer) -> None:
        yaml_content = """
jobs:
  fmt:
    steps:
      - run: ruff format src/
"""
        insights = analyzer.analyze(yaml_content)
        names = _tool_names(insights)
        assert "ruff format" in names
        assert "ruff" not in names

    def test_empty_makefile(self, analyzer: CIPipelineAnalyzer) -> None:
        insights = analyzer.analyze_makefile("")
        assert insights.detected_tools == ()
        assert insights.min_coverage is None

    def test_custom_ci_file_path_for_makefile(self, analyzer: CIPipelineAnalyzer) -> None:
        insights = analyzer.analyze_makefile("", ci_file_path="custom/Makefile")
        assert insights.ci_file_path == "custom/Makefile"

    def test_multiple_coverage_thresholds_returns_max(self, analyzer: CIPipelineAnalyzer) -> None:
        """When multiple coverage thresholds exist, return the highest."""
        yaml_content = """
jobs:
  test:
    steps:
      - run: pytest --cov-fail-under=80
      - run: pytest tests/critical/ --cov-fail-under=95
"""
        insights = analyzer.analyze(yaml_content)
        assert insights.min_coverage == 95

    def test_python_major_version_only(self, analyzer: CIPipelineAnalyzer) -> None:
        """Major-only version like python-version: '3' is detected."""
        yaml_content = """
jobs:
  test:
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3'
      - run: pytest tests/
"""
        insights = analyzer.analyze(yaml_content)
        assert insights.python_version == "3"

    def test_go_major_version_only(self, analyzer: CIPipelineAnalyzer) -> None:
        """Major-only version like go-version: '1' is detected."""
        yaml_content = """
jobs:
  test:
    steps:
      - uses: actions/setup-go@v5
        with:
          go-version: '1'
      - run: go test ./...
"""
        insights = analyzer.analyze(yaml_content)
        assert insights.go_version == "1"

    def test_node_semver_version(self, analyzer: CIPipelineAnalyzer) -> None:
        """Full SemVer like node-version: '20.11.1' is detected."""
        yaml_content = """
jobs:
  test:
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: '20.11.1'
      - run: npm test
"""
        insights = analyzer.analyze(yaml_content)
        assert insights.node_version == "20.11.1"

    def test_services_inside_list_structure(self, analyzer: CIPipelineAnalyzer) -> None:
        """Services nested inside a list are discovered via recursion."""
        yaml_content = """
jobs:
  test:
    strategy:
      matrix:
        include:
          - services:
              - postgres:16
              - redis:7
            run: pytest
"""
        insights = analyzer.analyze(yaml_content)
        assert "postgres" in insights.services
        assert "redis" in insights.services
