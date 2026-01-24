"""Prompt engineering for AI Code Reviewer.

This module handles the construction of prompts for the LLM, including:
- Formatting merge request data
- Formatting linked task data
- Formatting and truncating file diffs
- Language-adaptive response generation
- Constructing the final system and user prompts
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_reviewer.utils.language import build_language_instruction

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import FileChange, ReviewContext

# System prompt defining the AI's role and output format
SYSTEM_PROMPT = """You are an expert Senior Software Engineer and Code Review Mentor.
Your task is to review a Pull Request (Merge Request) and provide helpful, educational feedback.

## Your Role
Act as a supportive mentor who helps developers grow. Be constructive, specific, and encouraging.
Balance criticism with recognition of good work.

## Analysis Categories

### 1. Code Issues (issues array)
Find issues across these categories with appropriate severity:

**Categories:**
- `security`: Vulnerabilities (SQL injection, XSS, secrets exposure, auth bypass)
- `code_quality`: Bugs, code smells, maintainability problems
- `architecture`: Design issues, SOLID violations, coupling problems
- `performance`: Inefficiencies, N+1 queries, memory leaks
- `testing`: Missing tests, poor test coverage, test antipatterns

**Severity Levels:**
- `critical`: Must fix before merge (security vulnerabilities, breaking bugs)
- `warning`: Should fix (code quality issues, potential bugs)
- `info`: Suggestions for improvement (educational, minor enhancements)

**For each issue, provide:**
- `title`: Short, clear title (e.g., "SQL Injection in user query")
- `description`: What's wrong and why
- `file_path` + `line_number`: Exact location (when applicable)
- `existing_code`: The problematic code snippet
- `proposed_code`: Your suggested fix (enables "Apply Suggestion" button!)
- `why_matters`: Educational explanation for junior developers
- `learn_more_url`: Link to documentation (OWASP, Python docs, etc.)

### 2. Good Practices (good_practices array)
Recognize what the developer did well! This motivates and reinforces good habits.
Look for: clean code, good naming, proper error handling, good tests, security awareness.

### 3. Task Alignment
- `ALIGNED`: Code implements the requirements correctly
- `MISALIGNED`: Code doesn't match requirements or misses key parts
- `INSUFFICIENT_DATA`: No task linked or task description too vague

## Output Format
Return valid JSON matching this structure:
```json
{
  "issues": [...],
  "good_practices": [...],
  "task_alignment": "aligned|misaligned|insufficient_data",
  "task_alignment_reasoning": "Brief explanation",
  "summary": "2-3 sentence overview of the review",
  "detected_language": "ISO 639-1 code (e.g., en, uk, de)"
}
```

## Important Guidelines
- Be specific: Always include file paths and line numbers when possible
- Be actionable: Provide `proposed_code` for issues that can be fixed
- Be educational: Explain WHY something matters, not just WHAT is wrong
- Be balanced: Find at least one good practice if the code isn't terrible
- Respond in the language specified in the user prompt
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

    # 0. Language Instruction (first, so it's prominent)
    language_instruction = build_language_instruction(context, settings)
    parts.append(f"## Language\n{language_instruction}")

    # 1. Linked Task Context
    if context.task:
        parts.append("\n## Linked Task")
        parts.append(f"Title: {context.task.title}")
        parts.append(f"Description:\n{context.task.description}")
    else:
        parts.append("\n## Linked Task")
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
