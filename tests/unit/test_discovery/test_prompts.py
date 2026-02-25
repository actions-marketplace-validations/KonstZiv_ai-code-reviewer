"""Tests for discovery.prompts — LLM interpretation prompts."""

from __future__ import annotations

from ai_reviewer.discovery.config_collector import ConfigContent
from ai_reviewer.discovery.models import (
    CIInsights,
    DetectedTool,
    Gap,
    PlatformData,
    ToolCategory,
)
from ai_reviewer.discovery.prompts import (
    DISCOVERY_SYSTEM_PROMPT,
    LLMDiscoveryResponse,
    build_interpretation_prompt,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _make_platform_data(
    *,
    languages: dict[str, float] | None = None,
    topics: tuple[str, ...] = (),
    description: str | None = None,
) -> PlatformData:
    return PlatformData(
        languages=languages or {"Python": 85.0, "Shell": 15.0},
        primary_language="Python",
        topics=topics,
        description=description,
    )


def _make_ci_insights(
    *,
    tools: tuple[DetectedTool, ...] = (),
    python_version: str | None = "3.13",
    package_manager: str | None = "uv",
    services: tuple[str, ...] = (),
    min_coverage: int | None = None,
) -> CIInsights:
    return CIInsights(
        ci_file_path=".github/workflows/ci.yml",
        detected_tools=tools,
        python_version=python_version,
        package_manager=package_manager,
        services=services,
        min_coverage=min_coverage,
    )


def _make_config(
    path: str = "pyproject.toml",
    content: str = "[tool.ruff]\nline-length = 88\n",
    *,
    truncated: bool = False,
) -> ConfigContent:
    return ConfigContent(
        path=path,
        content=content,
        size_chars=len(content),
        truncated=truncated,
    )


# ── TestLLMDiscoveryResponse ─────────────────────────────────────────


class TestLLMDiscoveryResponse:
    """Tests for the LLM response model."""

    def test_defaults(self) -> None:
        resp = LLMDiscoveryResponse()
        assert resp.framework is None
        assert resp.architecture_notes is None
        assert resp.skip_in_review == []
        assert resp.focus_in_review == []
        assert resp.conventions == []
        assert resp.gaps == []

    def test_full_response(self) -> None:
        resp = LLMDiscoveryResponse(
            framework="Django 5.1",
            architecture_notes="Monolith with REST API",
            skip_in_review=["formatting", "type errors"],
            focus_in_review=["security", "SQL queries"],
            conventions=["Google docstrings"],
            gaps=[Gap(observation="No SAST", default_assumption="No security scanning")],
        )
        assert resp.framework == "Django 5.1"
        assert len(resp.skip_in_review) == 2
        assert len(resp.gaps) == 1
        assert resp.gaps[0].observation == "No SAST"

    def test_json_roundtrip(self) -> None:
        resp = LLMDiscoveryResponse(
            framework="FastAPI",
            skip_in_review=["formatting"],
            conventions=["Conventional commits"],
        )
        data = resp.model_dump_json()
        parsed = LLMDiscoveryResponse.model_validate_json(data)
        assert parsed == resp


# ── TestDiscoverySystemPrompt ────────────────────────────────────────


class TestDiscoverySystemPrompt:
    """Tests for the system prompt constant."""

    def test_is_nonempty_string(self) -> None:
        assert isinstance(DISCOVERY_SYSTEM_PROMPT, str)
        assert len(DISCOVERY_SYSTEM_PROMPT) > 50

    def test_contains_key_instructions(self) -> None:
        assert "concise" in DISCOVERY_SYSTEM_PROMPT.lower()
        assert "confirm" in DISCOVERY_SYSTEM_PROMPT.lower()
        assert "json" in DISCOVERY_SYSTEM_PROMPT.lower()


# ── TestBuildInterpretationPrompt ────────────────────────────────────


class TestBuildInterpretationPrompt:
    """Tests for build_interpretation_prompt."""

    def test_minimal_prompt(self) -> None:
        pd = _make_platform_data()
        result = build_interpretation_prompt(pd, None, ())
        assert "# Project Setup Analysis" in result
        assert "Python" in result
        assert "## CI Tools" not in result
        assert "## Config Files" not in result

    def test_includes_language_distribution(self) -> None:
        pd = _make_platform_data(languages={"Python": 85.0, "Shell": 15.0})
        result = build_interpretation_prompt(pd, None, ())
        assert "Python (85%)" in result
        assert "Shell (15%)" in result

    def test_includes_topics(self) -> None:
        pd = _make_platform_data(topics=("code-review", "ai", "python"))
        result = build_interpretation_prompt(pd, None, ())
        assert "code-review" in result
        assert "ai" in result

    def test_includes_description(self) -> None:
        pd = _make_platform_data(description="AI code review bot")
        result = build_interpretation_prompt(pd, None, ())
        assert "AI code review bot" in result

    def test_includes_ci_insights(self) -> None:
        pd = _make_platform_data()
        ci = _make_ci_insights(
            tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING),
            ),
            services=("postgres", "redis"),
            min_coverage=80,
        )
        result = build_interpretation_prompt(pd, ci, ())
        assert "ruff" in result
        assert "mypy" in result
        assert "Python: 3.13" in result
        assert "uv" in result
        assert "postgres" in result
        assert "80%" in result

    def test_includes_node_and_go_versions(self) -> None:
        pd = _make_platform_data()
        ci = CIInsights(
            ci_file_path=".github/workflows/ci.yml",
            node_version="22.x",
            go_version="1.22",
            python_version=None,
            package_manager=None,
        )
        result = build_interpretation_prompt(pd, ci, ())
        assert "Node: 22.x" in result
        assert "Go: 1.22" in result

    def test_includes_config_files(self) -> None:
        pd = _make_platform_data()
        configs = (
            _make_config("pyproject.toml", "[tool.ruff]\nline-length = 88"),
            _make_config("tsconfig.json", '{"strict": true}'),
        )
        result = build_interpretation_prompt(pd, None, configs)
        assert "### pyproject.toml" in result
        assert "line-length = 88" in result
        assert "### tsconfig.json" in result

    def test_truncated_config_noted(self) -> None:
        pd = _make_platform_data()
        configs = (_make_config("big.toml", "x" * 100, truncated=True),)
        result = build_interpretation_prompt(pd, None, configs)
        assert "(truncated)" in result

    def test_includes_task_section(self) -> None:
        pd = _make_platform_data()
        result = build_interpretation_prompt(pd, None, ())
        assert "## Task" in result
        assert "Framework" in result
        assert "SKIP" in result
        assert "FOCUS" in result
        assert "conventions" in result.lower()

    def test_full_prompt_under_token_estimate(self) -> None:
        """Full prompt with typical data should stay compact."""
        pd = _make_platform_data(
            topics=("python", "code-review"),
            description="AI reviewer",
        )
        ci = _make_ci_insights(
            tools=(
                DetectedTool(name="ruff", category=ToolCategory.LINTING),
                DetectedTool(name="mypy", category=ToolCategory.TYPE_CHECKING),
                DetectedTool(name="pytest", category=ToolCategory.TESTING),
            ),
            min_coverage=80,
        )
        configs = (_make_config("pyproject.toml", "[tool.ruff]\nline-length = 88\n" * 5),)
        result = build_interpretation_prompt(pd, ci, configs)
        # Rough estimate: 1 token ~ 4 chars; should be well under 2000 tokens
        assert len(result) < 8000

    def test_no_ci_tools_says_none(self) -> None:
        pd = _make_platform_data()
        ci = _make_ci_insights(tools=())
        result = build_interpretation_prompt(pd, ci, ())
        assert "none detected" in result
