"""Tests for discovery.models — Pydantic models for the Discovery pipeline."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

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

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def minimal_platform_data() -> PlatformData:
    """PlatformData with only required fields."""
    return PlatformData(languages={"Python": 100.0}, primary_language="Python")


@pytest.fixture
def full_platform_data() -> PlatformData:
    """PlatformData with all fields populated."""
    return PlatformData(
        languages={"Python": 85.3, "JavaScript": 14.7},
        primary_language="Python",
        topics=("ai", "code-review", "llm"),
        description="AI-powered code reviewer",
        license="Apache-2.0",
        default_branch="main",
        file_tree=("src/app.py", "tests/test_app.py", "pyproject.toml"),
        ci_config_paths=(".github/workflows/ci.yml",),
    )


@pytest.fixture
def sample_tool() -> DetectedTool:
    """A sample detected tool."""
    return DetectedTool(
        name="ruff",
        category=ToolCategory.LINTING,
        command="ruff check src/",
        config_file="pyproject.toml",
    )


@pytest.fixture
def sample_ci_insights(sample_tool: DetectedTool) -> CIInsights:
    """CIInsights with representative data."""
    return CIInsights(
        ci_file_path=".github/workflows/ci.yml",
        raw_yaml="name: CI\non: push",
        detected_tools=(
            sample_tool,
            DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING, command="mypy src/"),
            DetectedTool(name="pytest", category=ToolCategory.TESTING, command="pytest tests/"),
        ),
        python_version="3.13",
        package_manager="uv",
        services=("postgres",),
        deployment_targets=("pypi",),
        min_coverage=80,
    )


@pytest.fixture
def full_profile(
    full_platform_data: PlatformData,
    sample_ci_insights: CIInsights,
) -> ProjectProfile:
    """ProjectProfile with all fields populated."""
    return ProjectProfile(
        platform_data=full_platform_data,
        ci_insights=sample_ci_insights,
        framework="FastAPI",
        language_version="3.13",
        package_manager="uv",
        layout="src",
        automated_checks=AutomatedChecks(
            linting=("ruff",),
            formatting=("ruff format",),
            type_checking=("mypy",),
            testing=("pytest",),
            ci_provider="github_actions",
        ),
        guidance=ReviewGuidance(
            skip_in_review=("formatting", "import sorting"),
            focus_in_review=("error handling", "security"),
            conventions=("Google-style docstrings", "type hints required"),
        ),
        gaps=(
            Gap(
                observation="No security scanner detected",
                question="Do you use any security scanning tools?",
                default_assumption="No security scanning configured",
            ),
        ),
    )


# ── ToolCategory ─────────────────────────────────────────────────────


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_all_values(self) -> None:
        assert set(ToolCategory) == {
            ToolCategory.LINTING,
            ToolCategory.FORMATTING,
            ToolCategory.TYPE_CHECKING,
            ToolCategory.TESTING,
            ToolCategory.SECURITY,
            ToolCategory.DEPLOYMENT,
            ToolCategory.META,
        }

    def test_string_values(self) -> None:
        assert ToolCategory.LINTING == "linting"
        assert ToolCategory.META == "meta"

    def test_is_str_enum(self) -> None:
        assert isinstance(ToolCategory.LINTING, str)


# ── DetectedTool ─────────────────────────────────────────────────────


class TestDetectedTool:
    """Tests for DetectedTool model."""

    def test_minimal(self) -> None:
        tool = DetectedTool(name="ruff", category=ToolCategory.LINTING)
        assert tool.name == "ruff"
        assert tool.category == ToolCategory.LINTING
        assert tool.command == ""
        assert tool.config_file is None

    def test_full(self, sample_tool: DetectedTool) -> None:
        assert sample_tool.name == "ruff"
        assert sample_tool.command == "ruff check src/"
        assert sample_tool.config_file == "pyproject.toml"

    def test_frozen(self, sample_tool: DetectedTool) -> None:
        with pytest.raises(ValidationError):
            sample_tool.name = "eslint"  # type: ignore[misc]

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            DetectedTool(name="", category=ToolCategory.LINTING)

    def test_serialization_roundtrip(self, sample_tool: DetectedTool) -> None:
        data = sample_tool.model_dump()
        restored = DetectedTool.model_validate(data)
        assert restored == sample_tool


# ── CIInsights ───────────────────────────────────────────────────────


class TestCIInsights:
    """Tests for CIInsights model."""

    def test_minimal(self) -> None:
        ci = CIInsights(ci_file_path=".gitlab-ci.yml")
        assert ci.ci_file_path == ".gitlab-ci.yml"
        assert ci.detected_tools == ()
        assert ci.python_version is None
        assert ci.min_coverage is None

    def test_full(self, sample_ci_insights: CIInsights) -> None:
        assert len(sample_ci_insights.detected_tools) == 3
        assert sample_ci_insights.python_version == "3.13"
        assert sample_ci_insights.package_manager == "uv"
        assert sample_ci_insights.services == ("postgres",)
        assert sample_ci_insights.min_coverage == 80

    def test_frozen(self, sample_ci_insights: CIInsights) -> None:
        with pytest.raises(ValidationError):
            sample_ci_insights.python_version = "3.14"  # type: ignore[misc]

    def test_empty_path_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            CIInsights(ci_file_path="")

    def test_coverage_bounds(self) -> None:
        ci = CIInsights(ci_file_path="ci.yml", min_coverage=0)
        assert ci.min_coverage == 0

        ci = CIInsights(ci_file_path="ci.yml", min_coverage=100)
        assert ci.min_coverage == 100

        with pytest.raises(ValidationError):
            CIInsights(ci_file_path="ci.yml", min_coverage=-1)

        with pytest.raises(ValidationError):
            CIInsights(ci_file_path="ci.yml", min_coverage=101)

    def test_serialization_roundtrip(self, sample_ci_insights: CIInsights) -> None:
        data = sample_ci_insights.model_dump()
        restored = CIInsights.model_validate(data)
        assert restored == sample_ci_insights


# ── PlatformData ─────────────────────────────────────────────────────


class TestPlatformData:
    """Tests for PlatformData model."""

    def test_minimal(self, minimal_platform_data: PlatformData) -> None:
        assert minimal_platform_data.languages == {"Python": 100.0}
        assert minimal_platform_data.primary_language == "Python"
        assert minimal_platform_data.topics == ()
        assert minimal_platform_data.file_tree == ()

    def test_full(self, full_platform_data: PlatformData) -> None:
        assert len(full_platform_data.languages) == 2
        assert full_platform_data.topics == ("ai", "code-review", "llm")
        assert full_platform_data.license == "Apache-2.0"
        assert len(full_platform_data.file_tree) == 3

    def test_frozen(self, minimal_platform_data: PlatformData) -> None:
        with pytest.raises(ValidationError):
            minimal_platform_data.primary_language = "Go"  # type: ignore[misc]

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            PlatformData(languages={"Python": 100.0})  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            PlatformData(primary_language="Python")  # type: ignore[call-arg]

    def test_empty_primary_language_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            PlatformData(languages={}, primary_language="")

    def test_serialization_roundtrip(self, full_platform_data: PlatformData) -> None:
        data = full_platform_data.model_dump()
        restored = PlatformData.model_validate(data)
        assert restored == full_platform_data


# ── AutomatedChecks ──────────────────────────────────────────────────


class TestAutomatedChecks:
    """Tests for AutomatedChecks model."""

    def test_defaults(self) -> None:
        ac = AutomatedChecks()
        assert ac.linting == ()
        assert ac.formatting == ()
        assert ac.type_checking == ()
        assert ac.testing == ()
        assert ac.security == ()
        assert ac.ci_provider is None

    def test_with_tools(self) -> None:
        ac = AutomatedChecks(
            linting=("ruff", "pylint"),
            formatting=("ruff format",),
            type_checking=("mypy",),
            testing=("pytest",),
            security=("bandit",),
            ci_provider="github_actions",
        )
        assert len(ac.linting) == 2
        assert ac.ci_provider == "github_actions"

    def test_frozen(self) -> None:
        ac = AutomatedChecks()
        with pytest.raises(ValidationError):
            ac.ci_provider = "gitlab_ci"  # type: ignore[misc]


# ── Gap ──────────────────────────────────────────────────────────────


class TestGap:
    """Tests for Gap model."""

    def test_without_question(self) -> None:
        gap = Gap(observation="No test framework", default_assumption="No tests configured")
        assert gap.observation == "No test framework"
        assert gap.question is None
        assert gap.default_assumption == "No tests configured"

    def test_with_question(self) -> None:
        gap = Gap(
            observation="No test framework",
            question="What test framework do you use?",
            default_assumption="pytest",
        )
        assert gap.question == "What test framework do you use?"

    def test_frozen(self) -> None:
        gap = Gap(observation="obs", default_assumption="default")
        with pytest.raises(ValidationError):
            gap.observation = "new"  # type: ignore[misc]

    def test_empty_observation_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            Gap(observation="", default_assumption="default")

    def test_empty_default_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            Gap(observation="obs", default_assumption="")

    def test_serialization_roundtrip(self) -> None:
        gap = Gap(
            observation="No linter",
            question="Do you use a linter?",
            default_assumption="No linting",
        )
        data = gap.model_dump()
        restored = Gap.model_validate(data)
        assert restored == gap


# ── ReviewGuidance ───────────────────────────────────────────────────


class TestReviewGuidance:
    """Tests for ReviewGuidance model."""

    def test_defaults(self) -> None:
        rg = ReviewGuidance()
        assert rg.skip_in_review == ()
        assert rg.focus_in_review == ()
        assert rg.conventions == ()

    def test_with_data(self) -> None:
        rg = ReviewGuidance(
            skip_in_review=("formatting",),
            focus_in_review=("error handling",),
            conventions=("Google-style docstrings",),
        )
        assert len(rg.skip_in_review) == 1
        assert rg.conventions[0] == "Google-style docstrings"

    def test_frozen(self) -> None:
        rg = ReviewGuidance()
        with pytest.raises(ValidationError):
            rg.conventions = ("new",)  # type: ignore[misc]


# ── ProjectProfile ───────────────────────────────────────────────────


class TestProjectProfile:
    """Tests for ProjectProfile model."""

    def test_minimal(self, minimal_platform_data: PlatformData) -> None:
        profile = ProjectProfile(platform_data=minimal_platform_data)
        assert profile.platform_data.primary_language == "Python"
        assert profile.ci_insights is None
        assert profile.framework is None
        assert profile.automated_checks.linting == ()
        assert profile.guidance.skip_in_review == ()
        assert profile.gaps == ()

    def test_full(self, full_profile: ProjectProfile) -> None:
        assert full_profile.framework == "FastAPI"
        assert full_profile.language_version == "3.13"
        assert full_profile.package_manager == "uv"
        assert full_profile.layout == "src"
        assert full_profile.ci_insights is not None
        assert len(full_profile.ci_insights.detected_tools) == 3
        assert full_profile.automated_checks.linting == ("ruff",)
        assert len(full_profile.gaps) == 1

    def test_frozen(self, full_profile: ProjectProfile) -> None:
        with pytest.raises(ValidationError):
            full_profile.framework = "Django"  # type: ignore[misc]

    def test_missing_platform_data(self) -> None:
        with pytest.raises(ValidationError):
            ProjectProfile()  # type: ignore[call-arg]

    def test_serialization_roundtrip(self, full_profile: ProjectProfile) -> None:
        data = full_profile.model_dump()
        restored = ProjectProfile.model_validate(data)
        assert restored == full_profile


# ── to_prompt_context() ──────────────────────────────────────────────


class TestToPromptContext:
    """Tests for ProjectProfile.to_prompt_context()."""

    def test_minimal_output(self, minimal_platform_data: PlatformData) -> None:
        profile = ProjectProfile(platform_data=minimal_platform_data)
        result = profile.to_prompt_context()
        assert result == "Project: Python"

    def test_full_output(self, full_profile: ProjectProfile) -> None:
        result = full_profile.to_prompt_context()
        lines = result.split("\n")

        assert lines[0] == "Project: Python (FastAPI) 3.13, pkg: uv, layout: src"
        assert "Automated:" in lines[1]
        assert "ruff" in lines[1]
        assert "mypy" in lines[1]
        assert "pytest" in lines[1]
        assert any(line.startswith("Skip:") for line in lines)
        assert any(line.startswith("Focus:") for line in lines)
        assert any(line.startswith("Conventions:") for line in lines)

    def test_with_framework_only(self, minimal_platform_data: PlatformData) -> None:
        profile = ProjectProfile(
            platform_data=minimal_platform_data,
            framework="Django",
        )
        result = profile.to_prompt_context()
        assert result == "Project: Python (Django)"

    def test_with_automated_checks_only(self, minimal_platform_data: PlatformData) -> None:
        profile = ProjectProfile(
            platform_data=minimal_platform_data,
            automated_checks=AutomatedChecks(
                linting=("eslint",),
                testing=("jest",),
            ),
        )
        result = profile.to_prompt_context()
        lines = result.split("\n")
        assert len(lines) == 2
        assert "lint: eslint" in lines[1]
        assert "test: jest" in lines[1]

    def test_with_guidance_only(self, minimal_platform_data: PlatformData) -> None:
        profile = ProjectProfile(
            platform_data=minimal_platform_data,
            guidance=ReviewGuidance(
                skip_in_review=("formatting",),
                focus_in_review=("security",),
                conventions=("PEP 8",),
            ),
        )
        result = profile.to_prompt_context()
        lines = result.split("\n")
        assert len(lines) == 4
        assert "Skip: formatting" in result
        assert "Focus: security" in result
        assert "Conventions: PEP 8" in result

    def test_empty_checks_not_in_output(self, minimal_platform_data: PlatformData) -> None:
        profile = ProjectProfile(
            platform_data=minimal_platform_data,
            automated_checks=AutomatedChecks(),
        )
        result = profile.to_prompt_context()
        assert "Automated:" not in result

    def test_multiple_tools_formatting(self, minimal_platform_data: PlatformData) -> None:
        profile = ProjectProfile(
            platform_data=minimal_platform_data,
            automated_checks=AutomatedChecks(
                linting=("ruff", "pylint"),
                formatting=("ruff format", "isort"),
            ),
        )
        result = profile.to_prompt_context()
        assert "lint: ruff, pylint" in result
        assert "fmt: ruff format, isort" in result


# ── __init__.py re-exports ───────────────────────────────────────────


class TestReExports:
    """Test that discovery.__init__ re-exports all models."""

    def test_all_models_importable(self) -> None:
        from ai_reviewer.discovery import (
            AutomatedChecks,
            CIInsights,
            DetectedTool,
            Gap,
            PlatformData,
            ProjectProfile,
            ReviewGuidance,
            ToolCategory,
        )

        assert AutomatedChecks is not None
        assert CIInsights is not None
        assert DetectedTool is not None
        assert Gap is not None
        assert PlatformData is not None
        assert ProjectProfile is not None
        assert ReviewGuidance is not None
        assert ToolCategory is not None
