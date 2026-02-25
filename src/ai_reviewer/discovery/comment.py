"""Discovery comment formatter for MR/PR posts.

Produces a human-readable Markdown summary of what the bot discovered
about the project, including stack, CI tools, skip/focus guidance,
and any open questions (gaps).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_reviewer.discovery.models import ProjectProfile

# ── Constants ────────────────────────────────────────────────────────

DISCOVERY_COMMENT_HEADING = "## \U0001f50d AI ReviewBot: Project Analysis"

_REVIEWBOT_MD_PATH = ".reviewbot.md"


# ── Helpers ──────────────────────────────────────────────────────────


def _format_gaps_section(profile: ProjectProfile) -> list[str]:
    """Render the Gaps / Questions section lines."""
    if not profile.gaps:
        return []
    lines: list[str] = ["\n**Questions / Gaps:**"]
    for gap in profile.gaps:
        lines.append(f"- {gap.observation}")
        if gap.question:
            lines.append(f"  *Question:* {gap.question}")
        if gap.default_assumption:
            lines.append(f"  *Assumption:* {gap.default_assumption}")
    return lines


# ── Public API ───────────────────────────────────────────────────────


def format_discovery_comment(profile: ProjectProfile) -> str:
    """Format a discovery summary comment for posting to MR.

    Args:
        profile: Populated project profile from the Discovery pipeline.

    Returns:
        Markdown-formatted comment string.
    """
    parts: list[str] = [f"{DISCOVERY_COMMENT_HEADING}\n"]

    # Stack line
    pd = profile.platform_data
    stack = f"**Stack:** {pd.primary_language}"
    if profile.framework:
        stack += f" ({profile.framework})"
    if profile.language_version:
        stack += f" {profile.language_version}"
    if profile.package_manager:
        stack += f", {profile.package_manager}"
    parts.append(stack)

    # CI status
    ci = profile.ci_insights
    if ci and ci.detected_tools:
        tool_names = ", ".join(t.name for t in ci.detected_tools)
        provider = profile.automated_checks.ci_provider or ci.ci_file_path
        parts.append(f"**CI:** \u2705 {provider} \u2014 {tool_names}")
    else:
        parts.append("**CI:** \u274c No CI pipeline detected")

    # Skip / Focus from guidance
    g = profile.guidance
    if g.skip_in_review:
        parts.append("\n**What I'll skip** (CI handles these):")
        for item in g.skip_in_review:
            parts.append(f"- {item}")
    if g.focus_in_review:
        parts.append("\n**What I'll focus on:**")
        for item in g.focus_in_review:
            parts.append(f"- {item}")

    # Gaps / Questions
    parts.extend(_format_gaps_section(profile))

    # Footer
    parts.append("\n---")
    parts.append(f"\U0001f4a1 *Create `{_REVIEWBOT_MD_PATH}` in your repo root to customize.*")

    return "\n".join(parts)


def should_post_discovery_comment(
    profile: ProjectProfile,
    existing_comments: tuple[str, ...] = (),
) -> bool:
    """Decide whether to post the discovery comment.

    Rules:
        - ``.reviewbot.md`` present in file tree -> silent (skip).
        - Profile has unresolved gaps -> always post.
        - A previous discovery comment already exists -> skip (duplicate).
        - First run with no gaps -> post once.

    Args:
        profile: Populated project profile.
        existing_comments: Bodies of existing bot comments on the MR.

    Returns:
        True if the comment should be posted.
    """
    # .reviewbot.md present -> silent mode
    if _REVIEWBOT_MD_PATH in profile.platform_data.file_tree:
        return False

    # Duplicate detection: check if heading already posted
    return all(DISCOVERY_COMMENT_HEADING not in body for body in existing_comments)


__all__ = [
    "DISCOVERY_COMMENT_HEADING",
    "format_discovery_comment",
    "should_post_discovery_comment",
]
