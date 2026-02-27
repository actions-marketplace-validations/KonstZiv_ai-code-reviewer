"""Discovery comment formatter for MR/PR posts.

Produces a human-readable Markdown summary of what the bot discovered
about the project, including stack, CI tools, attention zones (well-covered,
not-covered, weakly-covered), and any open questions (gaps).

Two modes:
- **Default:** comment only when gaps or not_covered/weakly_covered zones exist.
- **Verbose:** comment always (``discovery_verbose=True``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_reviewer.core.config import BOT_NAME
from ai_reviewer.core.formatter import RUSSIAN_DISCLAIMER, is_russian_language

if TYPE_CHECKING:
    from ai_reviewer.discovery.models import AttentionZone, ProjectProfile

# ── Constants ────────────────────────────────────────────────────────

DISCOVERY_COMMENT_HEADING = f"## \U0001f50d {BOT_NAME}: Project Analysis"

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


def _format_zone_item(zone: AttentionZone) -> str:
    """Format a single attention zone as a bullet line."""
    line = f"- **{zone.area}**"
    if zone.reason:
        line += f" \u2014 {zone.reason}"
    if zone.recommendation:
        line += f"\n  \U0001f4a1 {zone.recommendation}"
    return line


def _format_stack_and_ci(profile: ProjectProfile) -> list[str]:
    """Render the Stack and CI status lines."""
    parts: list[str] = []

    pd = profile.platform_data
    stack = f"**Stack:** {pd.primary_language}"
    if profile.framework:
        stack += f" ({profile.framework})"
    if profile.language_version:
        stack += f" {profile.language_version}"
    if profile.package_manager:
        stack += f", {profile.package_manager}"
    parts.append(stack)

    ci = profile.ci_insights
    if ci and ci.detected_tools:
        tool_names = ", ".join(t.name for t in ci.detected_tools)
        provider = profile.automated_checks.ci_provider or ci.ci_file_path
        parts.append(f"**CI:** \u2705 {provider} \u2014 {tool_names}")
    else:
        parts.append("**CI:** \u274c No CI pipeline detected")

    return parts


def _format_zones_sections(
    zones: tuple[AttentionZone, ...],
    *,
    verbose: bool,
) -> list[str]:
    """Build attention zone sections for the comment.

    In verbose mode all zones are shown. In default mode only
    not_covered and weakly_covered zones are rendered.
    """
    well = [z for z in zones if z.status == "well_covered"]
    not_covered = [z for z in zones if z.status == "not_covered"]
    weak = [z for z in zones if z.status == "weakly_covered"]

    parts: list[str] = []

    if verbose and well:
        items = "\n".join(f"- \u2705 **{z.area}** \u2014 {z.reason}" for z in well)
        parts.append(f"\n### Well Covered (skipping in review)\n{items}")

    if not_covered:
        items = "\n".join(f"- \u274c {_format_zone_item(z)[2:]}" for z in not_covered)
        parts.append(f"\n### Not Covered (focusing in review)\n{items}")

    if weak:
        items = "\n".join(f"- \u26a0\ufe0f {_format_zone_item(z)[2:]}" for z in weak)
        parts.append(f"\n### Could Be Improved\n{items}")

    return parts


# ── Public API ───────────────────────────────────────────────────────


def format_discovery_comment(
    profile: ProjectProfile,
    *,
    verbose: bool = False,
    language: str | None = None,
) -> str | None:
    """Format a discovery summary comment for posting to MR.

    Args:
        profile: Populated project profile from the Discovery pipeline.
        verbose: When True, always produce a comment with all zones.
        language: ISO 639 language code. If Russian, adds disclaimer.

    Returns:
        Markdown-formatted comment string, or ``None`` if nothing to report
        (default mode with no gaps/not_covered/weakly_covered).
    """
    zones = profile.attention_zones
    not_covered = [z for z in zones if z.status == "not_covered"]
    weak = [z for z in zones if z.status == "weakly_covered"]

    # Default mode: only post when there are gaps or uncovered zones
    if not verbose and not not_covered and not weak and not profile.gaps:
        return None

    parts: list[str] = [f"{DISCOVERY_COMMENT_HEADING}\n"]
    parts.extend(_format_stack_and_ci(profile))

    # Attention zones (zone-driven sections replace old Skip/Focus)
    if zones:
        parts.extend(_format_zones_sections(zones, verbose=verbose))
    else:
        # Fallback to legacy guidance when no zones available
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

    # Russian disclaimer
    if is_russian_language(language):
        parts.append(RUSSIAN_DISCLAIMER)

    # Footer
    parts.append("\n---")
    parts.append(f"\U0001f4a1 *Create `{_REVIEWBOT_MD_PATH}` in your repo root to customize.*")

    return "\n".join(parts)


def should_post_discovery_comment(
    profile: ProjectProfile,
    existing_comments: tuple[str, ...] = (),
    *,
    verbose: bool = False,
) -> bool:
    """Decide whether to post the discovery comment.

    Rules:
        - ``.reviewbot.md`` present in file tree -> silent (skip).
        - Verbose mode -> always post (unless duplicate or .reviewbot.md).
        - No gaps and no uncovered zones -> silent (avoid noise).
        - A previous discovery comment already exists -> skip (duplicate).

    Args:
        profile: Populated project profile.
        existing_comments: Bodies of existing bot comments on the MR.
        verbose: When True, always post (unless suppressed by .reviewbot.md
            or duplicate).

    Returns:
        True if the comment should be posted.
    """
    # .reviewbot.md present -> silent mode
    if _REVIEWBOT_MD_PATH in profile.platform_data.file_tree:
        return False

    # Duplicate detection: check if heading already posted
    if any(DISCOVERY_COMMENT_HEADING in body for body in existing_comments):
        return False

    # Verbose → always post
    if verbose:
        return True

    # Default: post only when there are gaps or uncovered/weak zones
    zones = profile.attention_zones
    return (
        bool(profile.gaps)
        or any(z.status == "not_covered" for z in zones)
        or any(z.status == "weakly_covered" for z in zones)
    )


__all__ = [
    "DISCOVERY_COMMENT_HEADING",
    "format_discovery_comment",
    "should_post_discovery_comment",
]
