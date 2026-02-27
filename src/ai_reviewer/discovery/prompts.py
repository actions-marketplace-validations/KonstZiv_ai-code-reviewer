"""LLM prompts for Discovery Layer 3 (interpretation).

Provides a single focused prompt that transforms ``RawProjectData``
into ``LLMDiscoveryResult`` — three attention zones, framework detection,
watch-files, conventions, and security concerns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_reviewer.discovery.models import RawProjectData

# ── Constants ────────────────────────────────────────────────────────

_TOP_LANGUAGES = 5
_FILE_TREE_PREVIEW = 100


# ── System prompt ────────────────────────────────────────────────────

DISCOVERY_SYSTEM_PROMPT = """\
You are a senior DevOps and code quality expert.
Analyze the project data and classify code quality coverage into three zones.

Rules:
- Be concise and specific.
- Only list what you can CONFIRM from the provided data.
- If uncertain, add a Gap with a question for the developer.
- Do NOT guess or hallucinate tools or frameworks.
- Return valid JSON matching the provided schema.\
"""


# ── Prompt builder ───────────────────────────────────────────────────


def format_discovery_prompt(raw_data: RawProjectData) -> str:
    """Build a compact user prompt from collected raw project data.

    Formats ``RawProjectData`` into a structured Markdown prompt for the
    LLM. Limits content to keep token usage low (~200-400 input tokens
    for a typical project).

    Args:
        raw_data: Deterministically collected project data.

    Returns:
        Formatted prompt string.
    """
    # Languages: top N only
    top_langs = sorted(
        raw_data.languages.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:_TOP_LANGUAGES]
    lang_str = ", ".join(f"{lang} ({pct:.0f}%)" for lang, pct in top_langs)

    # File tree: first N entries
    tree_str = "\n".join(raw_data.file_tree[:_FILE_TREE_PREVIEW])
    if raw_data.file_tree_truncated:
        tree_str += f"\n... (truncated, {len(raw_data.file_tree)} total files)"

    # CI files: full content (usually small, already sanitized)
    ci_str = "\n\n".join(
        f"### {path}\n```\n{content}\n```" for path, content in raw_data.ci_files.items()
    )

    # Dependency files: full content
    dep_str = "\n\n".join(
        f"### {path}\n```\n{content}\n```" for path, content in raw_data.dependency_files.items()
    )

    # Config files: full content
    cfg_str = "\n\n".join(
        f"### {path}\n```\n{content}\n```" for path, content in raw_data.config_files.items()
    )

    pkg_mgr = ", ".join(raw_data.detected_package_managers) or "unknown"

    return _DISCOVERY_USER_PROMPT.format(
        languages=lang_str or "unknown",
        package_managers=pkg_mgr,
        layout=raw_data.layout or "unknown",
        dependency_files=dep_str or "(none found)",
        ci_files=ci_str or "(none found)",
        config_files=cfg_str or "(none found)",
        file_tree=tree_str or "(empty)",
    )


_DISCOVERY_USER_PROMPT = """\
Analyze this project and classify what is well covered, not covered, \
and weakly covered by automated tools.

## Project Data

Languages: {languages}
Package managers: {package_managers}
Layout: {layout}

## Dependency files
{dependency_files}

## CI Configuration
{ci_files}

## Quality Config Files
{config_files}

## File Tree (first 100 entries)
{file_tree}

## Instructions

1. **attention_zones**: Classify these areas: formatting, linting, \
type checking, testing, security scanning, dependency auditing, \
documentation, code coverage. Add project-specific areas if relevant.

2. **framework**: Detect the primary framework from dependencies. \
Include version if visible.

3. **watch_files**: List files that, if changed, would affect your analysis. \
These are files I should monitor to know when to re-run this analysis.

4. **conventions_detected**: Extract specific rules from config files \
(e.g., "ruff: line-length=120").

5. **security_concerns**: Note any missing security practices.\
"""


__all__ = [
    "DISCOVERY_SYSTEM_PROMPT",
    "format_discovery_prompt",
]
