"""Prompt engineering for AI Code Reviewer.

This module handles the construction of prompts for the LLM, including:
- Formatting merge request data
- Formatting linked task data
- Formatting and truncating file diffs
- Constructing the final system and user prompts
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import FileChange, ReviewContext

# System prompt defining the AI's role and output format
SYSTEM_PROMPT = """You are an expert Senior Software Engineer and Security Researcher.
Your task is to review a Pull Request (Merge Request) and provide a structured assessment.

You must analyze the code changes for:
1. **Critical Security Vulnerabilities**: SQL injection, XSS, RCE, hardcoded secrets,
   auth bypass, etc.
   - Focus ONLY on high-confidence, critical or high severity issues.
   - Do not report nitpicks, style issues, or minor bugs unless they have security implications.

2. **Task Alignment**: Does the code implement what is described in the Linked Task?
   - Compare the code changes against the task title and description.
   - Determine if the changes are:
     - ALIGNED: Code implements the requirements.
     - MISALIGNED: Code contradicts requirements or misses key parts.
     - INSUFFICIENT_DATA: Task description is too vague or missing.

Output must be valid JSON matching the ReviewResult schema.
"""


def _format_file_change(change: FileChange, max_lines: int) -> str:
    """Format a single file change with truncation logic.

    Args:
        change: The file change object.
        max_lines: Maximum number of diff lines to include.

    Returns:
        Formatted string representation of the file change.
    """
    header = f"File: {change.filename} ({change.change_type.value})"

    if change.patch is None:
        return f"{header}\n[Binary or large file - content skipped]"

    lines = change.patch.splitlines()
    if len(lines) > max_lines:
        truncated_patch = "\n".join(lines[:max_lines])
        skipped = len(lines) - max_lines
        return f"{header}\n{truncated_patch}\n... [Diff truncated, {skipped} lines skipped]"

    return f"{header}\n{change.patch}"


def build_review_prompt(context: ReviewContext, settings: Settings) -> str:
    """Construct the full user prompt for the review.

    Args:
        context: The review context (MR, task, etc.).
        settings: Application settings for limits.

    Returns:
        The constructed prompt string.
    """
    parts = []

    # 1. Linked Task Context
    if context.task:
        parts.append("## Linked Task")
        parts.append(f"Title: {context.task.title}")
        parts.append(f"Description:\n{context.task.description}")
    else:
        parts.append("## Linked Task")
        parts.append("No linked task provided.")

    # 2. Merge Request Context
    parts.append("\n## Merge Request")
    parts.append(f"Title: {context.mr.title}")
    parts.append(f"Description:\n{context.mr.description}")

    # 3. Code Changes
    parts.append("\n## Code Changes")

    # Filter and limit files
    files_to_process = context.mr.changes[: settings.review_max_files]
    skipped_files_count = len(context.mr.changes) - len(files_to_process)

    for change in files_to_process:
        parts.append(_format_file_change(change, settings.review_max_diff_lines))
        parts.append("---")

    if skipped_files_count > 0:
        parts.append(f"\n... [Skipped {skipped_files_count} more files due to limit]")

    return "\n".join(parts)
