"""Tests for discovery.prompts — LLM interpretation prompts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_reviewer.discovery.models import (
    AttentionZone,
    Gap,
    LLMDiscoveryResult,
    RawProjectData,
)
from ai_reviewer.discovery.prompts import (
    DISCOVERY_SYSTEM_PROMPT,
    format_discovery_prompt,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _make_raw_data(**overrides: object) -> RawProjectData:
    """Build RawProjectData with sensible defaults."""
    defaults: dict[str, object] = {
        "languages": {"Python": 85.0, "Shell": 15.0},
        "file_tree": ("src/main.py", "pyproject.toml"),
        "file_tree_truncated": False,
        "ci_files": {},
        "dependency_files": {},
        "config_files": {},
        "detected_package_managers": (),
        "layout": None,
    }
    defaults.update(overrides)
    return RawProjectData(**defaults)  # type: ignore[arg-type]


# ── TestAttentionZone ────────────────────────────────────────────────


class TestAttentionZone:
    """Tests for the AttentionZone model."""

    def test_minimal(self) -> None:
        zone = AttentionZone(area="formatting", status="well_covered")
        assert zone.area == "formatting"
        assert zone.status == "well_covered"
        assert zone.tools == ()
        assert zone.reason == ""
        assert zone.recommendation == ""

    def test_full(self) -> None:
        zone = AttentionZone(
            area="testing",
            status="weakly_covered",
            tools=("pytest",),
            reason="pytest runs but no coverage threshold",
            recommendation="Add --cov-fail-under=80",
        )
        assert zone.tools == ("pytest",)
        assert "coverage" in zone.reason

    def test_frozen(self) -> None:
        zone = AttentionZone(area="linting", status="well_covered")
        with pytest.raises(ValidationError):
            zone.area = "other"  # type: ignore[misc]


# ── TestLLMDiscoveryResult ───────────────────────────────────────────


class TestLLMDiscoveryResult:
    """Tests for the LLM result model."""

    def test_defaults(self) -> None:
        result = LLMDiscoveryResult()
        assert result.attention_zones == ()
        assert result.framework is None
        assert result.framework_confidence == 0.0
        assert result.stack_summary == ""
        assert result.watch_files == ()
        assert result.conventions_detected == ()
        assert result.security_concerns == ()
        assert result.gaps == ()

    def test_full_response(self) -> None:
        result = LLMDiscoveryResult(
            attention_zones=(
                AttentionZone(
                    area="formatting",
                    status="well_covered",
                    tools=("ruff",),
                    reason="ruff format enforced in CI",
                ),
                AttentionZone(
                    area="security",
                    status="not_covered",
                    reason="No SAST tool found",
                    recommendation="Add bandit or semgrep",
                ),
            ),
            framework="Django 5.1",
            framework_confidence=0.95,
            stack_summary="Python 3.13 + Django 5.1 + PostgreSQL",
            watch_files=(".github/workflows/ci.yml", "pyproject.toml"),
            conventions_detected=("ruff: line-length=120", "mypy: strict=true"),
            security_concerns=("No dependency scanning",),
            gaps=(Gap(observation="No SAST", default_assumption="No security scanning"),),
        )
        assert result.framework == "Django 5.1"
        assert len(result.attention_zones) == 2
        assert result.attention_zones[0].status == "well_covered"
        assert result.attention_zones[1].status == "not_covered"
        assert len(result.gaps) == 1

    def test_json_roundtrip(self) -> None:
        result = LLMDiscoveryResult(
            attention_zones=(
                AttentionZone(area="linting", status="well_covered", tools=("ruff",)),
            ),
            framework="FastAPI",
            conventions_detected=("Conventional commits",),
        )
        data = result.model_dump_json()
        parsed = LLMDiscoveryResult.model_validate_json(data)
        assert parsed == result

    def test_framework_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            LLMDiscoveryResult(framework_confidence=1.5)
        with pytest.raises(ValidationError):
            LLMDiscoveryResult(framework_confidence=-0.1)


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


# ── TestFormatDiscoveryPrompt ────────────────────────────────────────


class TestFormatDiscoveryPrompt:
    """Tests for format_discovery_prompt."""

    def test_minimal_prompt(self) -> None:
        raw = _make_raw_data()
        result = format_discovery_prompt(raw)
        assert "Languages:" in result
        assert "Python (85%)" in result
        assert "(none found)" in result

    def test_includes_languages(self) -> None:
        raw = _make_raw_data(languages={"Python": 85.0, "Shell": 15.0})
        result = format_discovery_prompt(raw)
        assert "Python (85%)" in result
        assert "Shell (15%)" in result

    def test_includes_package_managers(self) -> None:
        raw = _make_raw_data(detected_package_managers=("uv", "npm"))
        result = format_discovery_prompt(raw)
        assert "uv" in result
        assert "npm" in result

    def test_includes_layout(self) -> None:
        raw = _make_raw_data(layout="monorepo")
        result = format_discovery_prompt(raw)
        assert "monorepo" in result

    def test_includes_ci_files(self) -> None:
        raw = _make_raw_data(ci_files={".github/workflows/ci.yml": "name: CI\non: [push]"})
        result = format_discovery_prompt(raw)
        assert "### .github/workflows/ci.yml" in result
        assert "name: CI" in result

    def test_includes_dependency_files(self) -> None:
        raw = _make_raw_data(dependency_files={"pyproject.toml": "[project]\nname = 'test'"})
        result = format_discovery_prompt(raw)
        assert "### pyproject.toml" in result

    def test_includes_config_files(self) -> None:
        raw = _make_raw_data(config_files={"ruff.toml": "line-length = 120"})
        result = format_discovery_prompt(raw)
        assert "### ruff.toml" in result
        assert "line-length = 120" in result

    def test_includes_file_tree(self) -> None:
        raw = _make_raw_data(file_tree=("src/main.py", "tests/test_main.py"))
        result = format_discovery_prompt(raw)
        assert "src/main.py" in result
        assert "tests/test_main.py" in result

    def test_truncated_tree_noted(self) -> None:
        raw = _make_raw_data(
            file_tree=tuple(f"file_{i}.py" for i in range(200)),
            file_tree_truncated=True,
        )
        result = format_discovery_prompt(raw)
        assert "truncated" in result
        assert "200 total files" in result

    def test_includes_instructions(self) -> None:
        raw = _make_raw_data()
        result = format_discovery_prompt(raw)
        assert "attention_zones" in result
        assert "framework" in result
        assert "watch_files" in result
        assert "conventions_detected" in result
        assert "security_concerns" in result

    def test_empty_raw_data(self) -> None:
        raw = RawProjectData()
        result = format_discovery_prompt(raw)
        assert "unknown" in result  # languages unknown
        assert "(empty)" in result  # file tree empty

    def test_top_5_languages_only(self) -> None:
        langs = {f"Lang{i}": float(20 - i) for i in range(8)}
        raw = _make_raw_data(languages=langs)
        result = format_discovery_prompt(raw)
        # Only top 5 should appear
        assert "Lang0" in result
        assert "Lang4" in result
        assert "Lang5" not in result

    def test_full_prompt_under_token_estimate(self) -> None:
        """Full prompt with typical data should stay compact."""
        raw = _make_raw_data(
            ci_files={".github/workflows/ci.yml": "name: CI\nsteps:\n  - run: pytest"},
            dependency_files={"pyproject.toml": "[tool.ruff]\nline-length = 88\n" * 5},
            config_files={"ruff.toml": "line-length = 88"},
            detected_package_managers=("uv",),
            layout="src",
        )
        result = format_discovery_prompt(raw)
        # Rough estimate: 1 token ~ 4 chars; should be well under 2000 tokens
        assert len(result) < 8000
