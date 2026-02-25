"""LLM prompts for Discovery Layer 3 (interpretation).

Used **only** when deterministic layers (platform API, CI, configs) leave
gaps. The LLM receives a compact summary of what was already collected
and fills in framework detection, review guidance, and conventions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ai_reviewer.discovery.models import Gap  # noqa: TC001

if TYPE_CHECKING:
    from ai_reviewer.discovery.config_collector import ConfigContent
    from ai_reviewer.discovery.models import CIInsights, PlatformData

# ── Response model ───────────────────────────────────────────────────


class LLMDiscoveryResponse(BaseModel):
    """Structured response from the LLM interpretation step.

    Contains only fields that cannot be extracted deterministically
    from CI configuration or config files.

    Attributes:
        framework: Detected framework (e.g. ``Django``, ``FastAPI``, ``React``).
        architecture_notes: Brief notes on project architecture.
        skip_in_review: Areas a reviewer should skip (already automated).
        focus_in_review: Areas a reviewer should focus on (gaps in automation).
        conventions: Project-specific conventions detected from configs.
        gaps: Unresolved questions the LLM could not answer.
    """

    framework: str | None = Field(default=None, description="Detected framework")
    architecture_notes: str | None = Field(default=None, description="Brief architecture notes")
    skip_in_review: list[str] = Field(
        default_factory=list, description="Areas to skip (already automated)"
    )
    focus_in_review: list[str] = Field(default_factory=list, description="Areas to focus on (gaps)")
    conventions: list[str] = Field(default_factory=list, description="Project conventions")
    gaps: list[Gap] = Field(default_factory=list, description="Unresolved questions")


# ── System prompt ────────────────────────────────────────────────────

DISCOVERY_SYSTEM_PROMPT = """\
You are a project setup analyst.
Your task: interpret project configuration files and determine \
what a code reviewer should know about this project.

Rules:
- Be concise and specific.
- Only list what you can CONFIRM from the provided data.
- If uncertain, add a Gap with a question for the developer.
- Do NOT guess or hallucinate tools/frameworks.
- Return valid JSON matching the provided schema.\
"""


# ── Prompt builder ───────────────────────────────────────────────────


def build_interpretation_prompt(
    platform_data: PlatformData,
    ci_insights: CIInsights | None,
    configs: tuple[ConfigContent, ...],
) -> str:
    """Build a compact user prompt for LLM interpretation.

    Assembles platform data, CI insights, and config file contents
    into a structured Markdown prompt for the LLM.

    Args:
        platform_data: Repository metadata from platform API.
        ci_insights: Parsed CI configuration, if available.
        configs: Collected configuration file contents.

    Returns:
        Formatted prompt string.
    """
    parts: list[str] = ["# Project Setup Analysis\n"]

    # Languages & metadata
    parts.append(f"## Languages: {platform_data.primary_language}")
    if platform_data.languages:
        lang_list = ", ".join(
            f"{lang} ({pct:.0f}%)" for lang, pct in platform_data.languages.items()
        )
        parts.append(f"Distribution: {lang_list}")
    if platform_data.topics:
        parts.append(f"Topics: {', '.join(platform_data.topics)}")
    if platform_data.description:
        parts.append(f"Description: {platform_data.description}")

    # CI insights
    if ci_insights:
        tools = [t.name for t in ci_insights.detected_tools]
        parts.append(f"\n## CI Tools: {', '.join(tools) or 'none detected'}")
        if ci_insights.python_version:
            parts.append(f"Python: {ci_insights.python_version}")
        if ci_insights.node_version:
            parts.append(f"Node: {ci_insights.node_version}")
        if ci_insights.go_version:
            parts.append(f"Go: {ci_insights.go_version}")
        if ci_insights.package_manager:
            parts.append(f"Package manager: {ci_insights.package_manager}")
        if ci_insights.services:
            parts.append(f"Services: {', '.join(ci_insights.services)}")
        if ci_insights.min_coverage is not None:
            parts.append(f"Min coverage: {ci_insights.min_coverage}%")

    # Config files
    if configs:
        parts.append("\n## Config Files")
        for cfg in configs:
            truncation_note = " (truncated)" if cfg.truncated else ""
            parts.append(f"\n### {cfg.path}{truncation_note}")
            parts.append(f"```\n{cfg.content}\n```")

    # Task
    parts.append("\n## Task")
    parts.append("Based on the above, determine:")
    parts.append("1. Framework (if detectable from dependencies or config)")
    parts.append("2. What a reviewer should SKIP (already automated by CI)")
    parts.append("3. What a reviewer should FOCUS on (gaps in automation)")
    parts.append("4. Project conventions (from config files)")
    parts.append("5. Questions if anything is unclear (as Gaps)")

    return "\n".join(parts)


__all__ = [
    "DISCOVERY_SYSTEM_PROMPT",
    "LLMDiscoveryResponse",
    "build_interpretation_prompt",
]
