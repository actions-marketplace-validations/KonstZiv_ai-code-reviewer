"""Pydantic models for the Discovery pipeline.

Defines the data structures used across all Discovery layers:
platform metadata, CI insights, detected tools, automated checks,
review guidance, knowledge gaps, and the central ``ProjectProfile``.

All models are frozen (immutable) and use tuples for collections
to maintain consistency with ``core.models``.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolCategory(str, Enum):
    """Category of a detected development tool.

    Attributes:
        LINTING: Static analysis / lint (ruff, eslint, pylint).
        FORMATTING: Code formatting (ruff format, prettier, black).
        TYPE_CHECKING: Type checkers (mypy, pyright, tsc).
        TESTING: Test frameworks (pytest, jest, go test).
        SECURITY: Security scanners (bandit, snyk, trivy).
        DEPLOYMENT: Deployment tools (docker, helm, terraform).
        META: Meta-tools (pre-commit, husky, lefthook).
    """

    LINTING = "linting"
    FORMATTING = "formatting"
    TYPE_CHECKING = "type_checking"
    TESTING = "testing"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    META = "meta"


class DetectedTool(BaseModel):
    """A tool detected from CI configuration or config files.

    Attributes:
        name: Tool name (e.g. ``ruff``, ``eslint``, ``pytest``).
        category: Functional category of the tool.
        command: Full command string from CI (e.g. ``ruff check src/``).
        config_file: Path to the tool's config file, if found.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Tool name: ruff, eslint, etc.")
    category: ToolCategory = Field(..., description="Functional category of the tool")
    command: str = Field(default="", description="Full command from CI")
    config_file: str | None = Field(default=None, description="Related config file path")


class CIInsights(BaseModel):
    """Insights extracted from CI pipeline configuration.

    Parsed from GitHub Actions workflows, GitLab CI YAML, or Makefiles.
    Contains detected tools, language versions, and infrastructure details.

    Attributes:
        ci_file_path: Path to the CI config file (e.g. ``.github/workflows/ci.yml``).
        raw_yaml: Raw content of the CI file for LLM interpretation.
        detected_tools: Tools found in CI commands.
        python_version: Python version specified in CI.
        node_version: Node.js version specified in CI.
        go_version: Go version specified in CI.
        package_manager: Package manager (e.g. ``uv``, ``npm``, ``pnpm``).
        services: CI service containers (e.g. ``postgres``, ``redis``).
        deployment_targets: Deployment destinations (e.g. ``pypi``, ``ghcr.io``).
        min_coverage: Minimum test coverage threshold from CI config.
    """

    model_config = ConfigDict(frozen=True)

    ci_file_path: str = Field(..., min_length=1, description="CI config file path")
    raw_yaml: str = Field(default="", description="Raw CI file content")
    detected_tools: tuple[DetectedTool, ...] = Field(default=(), description="Tools detected in CI")
    python_version: str | None = Field(default=None, description="Python version from CI")
    node_version: str | None = Field(default=None, description="Node.js version from CI")
    go_version: str | None = Field(default=None, description="Go version from CI")
    package_manager: str | None = Field(default=None, description="Package manager: uv, npm, etc.")
    services: tuple[str, ...] = Field(default=(), description="CI service containers")
    deployment_targets: tuple[str, ...] = Field(default=(), description="Deployment destinations")
    min_coverage: int | None = Field(default=None, ge=0, le=100, description="Min coverage %")


class PlatformData(BaseModel):
    """Repository data collected from the platform API (Layer 0).

    Zero-cost data: no LLM tokens required, only API calls to
    GitHub/GitLab via ``RepositoryProvider``.

    Attributes:
        languages: Mapping of language name to percentage (0-100).
        primary_language: The dominant language by percentage.
        topics: Repository topics / tags.
        description: Repository description text.
        license: SPDX license identifier.
        default_branch: Name of the default branch.
        file_tree: All file paths in the repository.
        ci_config_paths: Detected CI configuration file paths.
    """

    model_config = ConfigDict(frozen=True)

    languages: dict[str, float] = Field(..., description="Language name to percentage mapping")
    primary_language: str = Field(..., min_length=1, description="Dominant language")
    topics: tuple[str, ...] = Field(default=(), description="Repository topics")
    description: str | None = Field(default=None, description="Repository description")
    license: str | None = Field(default=None, description="SPDX license identifier")
    default_branch: str = Field(default="main", description="Default branch name")
    file_tree: tuple[str, ...] = Field(default=(), description="All file paths in repository")
    ci_config_paths: tuple[str, ...] = Field(
        default=(), description="Detected CI config file paths"
    )


class AutomatedChecks(BaseModel):
    """Summary of automated checks already configured in the project.

    Used by the reviewer to avoid duplicating feedback that CI already
    catches (e.g. don't flag formatting if ``ruff format`` runs in CI).

    Attributes:
        linting: Linting tools (e.g. ``ruff``, ``eslint``).
        formatting: Formatting tools (e.g. ``ruff format``, ``prettier``).
        type_checking: Type checkers (e.g. ``mypy``, ``pyright``).
        testing: Test frameworks (e.g. ``pytest``, ``jest``).
        security: Security scanners (e.g. ``bandit``, ``snyk``).
        ci_provider: CI provider name (e.g. ``github_actions``, ``gitlab_ci``).
    """

    model_config = ConfigDict(frozen=True)

    linting: tuple[str, ...] = Field(default=(), description="Linting tools")
    formatting: tuple[str, ...] = Field(default=(), description="Formatting tools")
    type_checking: tuple[str, ...] = Field(default=(), description="Type checking tools")
    testing: tuple[str, ...] = Field(default=(), description="Test frameworks")
    security: tuple[str, ...] = Field(default=(), description="Security scanners")
    ci_provider: str | None = Field(default=None, description="CI provider name")


class Gap(BaseModel):
    """A knowledge gap identified during discovery.

    When the Discovery pipeline cannot determine something with certainty,
    it records a Gap. If a ``question`` is provided, it may be posted to
    the merge request via ``ConversationProvider``.

    Attributes:
        observation: What was observed (e.g. "No test framework detected").
        question: Optional question to ask the developer.
        default_assumption: What the bot assumes if no answer is given.
    """

    model_config = ConfigDict(frozen=True)

    observation: str = Field(..., min_length=1, description="What was observed")
    question: str | None = Field(default=None, description="Question to ask the developer")
    default_assumption: str = Field(..., min_length=1, description="Assumption if no answer")


class ReviewGuidance(BaseModel):
    """Guidance for the review prompt based on discovered project context.

    Directs the LLM reviewer to skip areas covered by automation,
    focus on uncovered areas, and respect project conventions.

    Attributes:
        skip_in_review: Areas to skip (already covered by CI).
        focus_in_review: Areas to focus on (not covered by CI).
        conventions: Project-specific conventions to enforce.
    """

    model_config = ConfigDict(frozen=True)

    skip_in_review: tuple[str, ...] = Field(default=(), description="Areas to skip (covered by CI)")
    focus_in_review: tuple[str, ...] = Field(
        default=(), description="Areas to focus on (not covered by CI)"
    )
    conventions: tuple[str, ...] = Field(default=(), description="Project-specific conventions")


class AttentionZone(BaseModel):
    """One area of code quality with its automation coverage status.

    Attributes:
        area: Quality area name (e.g. ``formatting``, ``type checking``).
        status: Coverage status from CI/tooling analysis.
        tools: CI tools handling this area.
        reason: Why this status was assigned.
        recommendation: Suggested improvement, if any.
    """

    model_config = ConfigDict(frozen=True)

    area: str = Field(..., min_length=1, description="Quality area name")
    status: Literal["well_covered", "not_covered", "weakly_covered"] = Field(
        ..., description="Coverage status"
    )
    tools: tuple[str, ...] = Field(default=(), description="CI tools handling this area")
    reason: str = Field(default="", description="Why this status was assigned")
    recommendation: str = Field(default="", description="Suggested improvement")


class LLMDiscoveryResult(BaseModel):
    """Structured LLM response for project analysis.

    Replaces the simpler ``LLMDiscoveryResponse`` with richer output:
    three attention zones, framework detection with confidence, watch-files
    for caching, and security concerns.

    Attributes:
        attention_zones: Code quality areas classified by coverage status.
        framework: Detected framework (e.g. ``Django 5.1``, ``Next.js 14``).
        framework_confidence: Confidence score 0.0-1.0 for framework detection.
        stack_summary: One-line stack description.
        watch_files: Files to monitor for re-analysis triggers.
        watch_files_reason: Why these files matter.
        conventions_detected: Specific rules from config files.
        security_concerns: Missing security practices.
        gaps: Unresolved questions the LLM could not answer.
    """

    model_config = ConfigDict(frozen=True)

    attention_zones: tuple[AttentionZone, ...] = Field(
        default=(), description="Code quality areas by coverage status"
    )
    framework: str | None = Field(default=None, description="Detected framework")
    framework_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Framework detection confidence"
    )
    stack_summary: str = Field(default="", description="One-line stack description")
    watch_files: tuple[str, ...] = Field(default=(), description="Files to monitor for re-analysis")
    watch_files_reason: str = Field(default="", description="Why watch-files matter")
    conventions_detected: tuple[str, ...] = Field(
        default=(), description="Specific rules from config files"
    )
    security_concerns: tuple[str, ...] = Field(default=(), description="Missing security practices")
    gaps: tuple[Gap, ...] = Field(default_factory=tuple, description="Unresolved questions")


class RawProjectData(BaseModel):
    """All data collected deterministically (0 LLM tokens).

    This is the input for LLM analysis (task 1.2).
    Contains raw strings — LLM interprets them.
    """

    model_config = ConfigDict(frozen=True)

    languages: dict[str, float] = Field(
        default_factory=dict,
        description="Language → percentage from Platform API",
    )
    file_tree: tuple[str, ...] = Field(
        default=(),
        description="Flattened file paths",
    )
    file_tree_truncated: bool = Field(
        default=False,
        description="True if tree was cut at FILE_TREE_LIMIT",
    )
    ci_files: dict[str, str] = Field(
        default_factory=dict,
        description="Path → content of CI config files",
        repr=False,
    )
    dependency_files: dict[str, str] = Field(
        default_factory=dict,
        description="Path → content (pyproject.toml, package.json, go.mod, etc.)",
        repr=False,
    )
    config_files: dict[str, str] = Field(
        default_factory=dict,
        description="Path → content (ruff.toml, .eslintrc, tsconfig.json, etc.)",
        repr=False,
    )
    detected_package_managers: tuple[str, ...] = Field(
        default=(),
        description="Deterministically detected: uv, pip, npm, yarn, pnpm, go modules",
    )
    layout: str | None = Field(
        default=None,
        description="src | flat | monorepo — from file tree heuristic",
    )
    reviewbot_config: str | None = Field(
        default=None,
        description="Content of .reviewbot.md if exists",
        repr=False,
    )


class ProjectProfile(BaseModel):
    """Central Discovery output passed to the review prompt.

    Aggregates all layers of the Discovery pipeline into a single
    immutable object. The ``to_prompt_context()`` method produces a
    compact text representation (~200-400 tokens) for injection into
    the review system prompt.

    Attributes:
        platform_data: Data from platform API (Layer 0).
        ci_insights: Parsed CI configuration (Layer 1), if available.
        framework: Detected framework (e.g. ``Django``, ``FastAPI``, ``React``).
        language_version: Primary language version (e.g. ``3.13``, ``22``).
        package_manager: Package manager (e.g. ``uv``, ``npm``, ``pnpm``).
        layout: Project layout style (``src``, ``flat``, ``monorepo``).
        automated_checks: Summary of CI-automated checks.
        guidance: Review guidance derived from discovery.
        gaps: Unresolved knowledge gaps.
    """

    model_config = ConfigDict(frozen=True)

    platform_data: PlatformData = Field(..., description="Data from platform API")
    ci_insights: CIInsights | None = Field(default=None, description="Parsed CI config")
    framework: str | None = Field(default=None, description="Detected framework")
    language_version: str | None = Field(default=None, description="Primary language version")
    package_manager: str | None = Field(default=None, description="Package manager")
    layout: str | None = Field(default=None, description="Project layout: src, flat, monorepo")

    automated_checks: AutomatedChecks = Field(
        default_factory=AutomatedChecks, description="CI-automated checks"
    )
    guidance: ReviewGuidance = Field(default_factory=ReviewGuidance, description="Review guidance")
    gaps: tuple[Gap, ...] = Field(default=(), description="Unresolved knowledge gaps")
    attention_zones: tuple[AttentionZone, ...] = Field(
        default=(), description="LLM-detected attention zones with reasons"
    )

    def to_prompt_context(self) -> str:
        """Produce a structured text summary for the review prompt.

        When ``attention_zones`` are present, generates directive
        SKIP/FOCUS/CHECK sections with reasons and recommendations.
        Falls back to the compact format when no zones are available.

        Returns:
            Multi-line text summary of the project profile.
        """
        header = f"Project: {self.platform_data.primary_language}"
        if self.framework:
            header += f" ({self.framework})"
        if self.language_version:
            header += f" {self.language_version}"
        if self.package_manager:
            header += f", pkg: {self.package_manager}"
        if self.layout:
            header += f", layout: {self.layout}"

        parts = [header]

        ac = self.automated_checks
        auto_parts: list[str] = []
        for name, tools in [
            ("lint", ac.linting),
            ("fmt", ac.formatting),
            ("types", ac.type_checking),
            ("test", ac.testing),
            ("sec", ac.security),
        ]:
            if tools:
                auto_parts.append(f"{name}: {', '.join(tools)}")
        if auto_parts:
            parts.append(f"Automated: {'; '.join(auto_parts)}")

        g = self.guidance
        if self.attention_zones:
            parts.extend(self._render_zone_sections())
        else:
            if g.skip_in_review:
                parts.append(f"Skip: {'; '.join(g.skip_in_review)}")
            if g.focus_in_review:
                parts.append(f"Focus: {'; '.join(g.focus_in_review)}")

        if g.conventions:
            parts.append(f"Conventions: {'; '.join(g.conventions)}")

        return "\n".join(parts)

    def _render_zone_sections(self) -> list[str]:
        """Render SKIP / FOCUS / CHECK sections from attention zones."""
        skip_lines: list[str] = []
        focus_lines: list[str] = []
        check_lines: list[str] = []

        def _format_entry(zone: AttentionZone) -> str:
            tools_str = f" ({', '.join(zone.tools)})" if zone.tools else ""
            entry = f"- {zone.area}{tools_str}"
            if zone.reason:
                entry += f": {zone.reason}"
            return entry

        for zone in self.attention_zones:
            if zone.status == "well_covered":
                skip_lines.append(_format_entry(zone))
            elif zone.status == "not_covered":
                focus_lines.append(_format_entry(zone))
            elif zone.status == "weakly_covered":
                entry = _format_entry(zone)
                if zone.recommendation:
                    entry += f"\n  → Recommendation: {zone.recommendation}"
                check_lines.append(entry)

        parts: list[str] = []
        if skip_lines:
            parts.append("\n## SKIP in review (covered by CI):")
            parts.extend(skip_lines)
        if focus_lines:
            parts.append("\n## FOCUS in review (not covered):")
            parts.extend(focus_lines)
        if check_lines:
            parts.append("\n## CHECK and improve:")
            parts.extend(check_lines)
        return parts


__all__ = [
    "AttentionZone",
    "AutomatedChecks",
    "CIInsights",
    "DetectedTool",
    "Gap",
    "LLMDiscoveryResult",
    "PlatformData",
    "ProjectProfile",
    "RawProjectData",
    "ReviewGuidance",
    "ToolCategory",
]
