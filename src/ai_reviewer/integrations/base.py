"""Base abstractions for Git provider integrations.

This module defines the abstract interface for Git providers (GitHub, GitLab, etc.)
and common data structures used across all providers.

The GitProvider ABC ensures consistent behavior across different platforms,
enabling the reviewer to work with any supported Git provider.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ai_reviewer.core.models import (  # noqa: TC001 — runtime for deprecated alias
    LinkedTask,
    MergeRequest,
)

_BRANCH_ISSUE_RE = re.compile(r"^(?:\w+/)?(?:GH-)?(\d+)(?:[-_]|$)")

ISSUE_CLOSING_RE = re.compile(
    r"(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)",
    re.IGNORECASE,
)

_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_branch_issue_number(branch: str) -> int | None:
    """Extract issue number from a branch name convention.

    Supports formats like:
    - ``86-task-description``
    - ``feature/123-login``
    - ``GH-789-refactor``

    Args:
        branch: Source branch name.

    Returns:
        Issue number if found, None otherwise.
    """
    m = _BRANCH_ISSUE_RE.match(branch)
    return int(m.group(1)) if m else None


def parse_diff_valid_lines(patch: str | None) -> frozenset[int]:
    """Extract valid new-side line numbers from a unified diff patch.

    Walks through each diff line to compute exact new-side line numbers.
    Lines starting with ``-`` (deletions) do not have a new-side number.
    Lines starting with ``+`` (additions) or `` `` (context) do.

    These are the only lines that GitHub's Review API accepts for inline
    comments; posting on other lines results in 422 "Line could not be
    resolved".

    Args:
        patch: Unified diff string (``FileChange.patch``).

    Returns:
        Frozenset of valid new-side line numbers.
    """
    if not patch:
        return frozenset()

    valid: set[int] = set()
    new_line = 0

    for raw_line in patch.splitlines():
        hunk_match = _HUNK_HEADER_RE.match(raw_line)
        if hunk_match:
            new_line = int(hunk_match.group(1))
            continue

        if not new_line:
            # Before first hunk header
            continue

        if raw_line.startswith("-"):
            # Deletion: only old side, no new-side line number
            continue

        if raw_line.startswith("\\"):
            # "No newline at end of file" marker
            continue

        # Addition (+) or context ( ) line: has a new-side line number
        valid.add(new_line)
        new_line += 1

    return frozenset(valid)


@dataclass(frozen=True, slots=True)
class LineComment:
    """A comment attached to a specific line in a file.

    Used for inline code review comments with optional suggestions.
    When a suggestion is provided, platforms like GitHub render an
    "Apply suggestion" button for one-click fixes.

    Attributes:
        path: File path relative to repository root.
        line: Line number in the file (1-indexed).
        body: The comment text (markdown supported).
        suggestion: Optional code suggestion to replace the line.
            When provided, renders as an actionable suggestion block.
        side: Which side of the diff to comment on ('LEFT' for deletions,
            'RIGHT' for additions). Defaults to 'RIGHT'.
    """

    path: str
    line: int
    body: str
    suggestion: str | None = None
    side: str = field(default="RIGHT")

    def __post_init__(self) -> None:
        """Validate LineComment fields after initialization."""
        if self.line < 1:
            msg = f"Line number must be positive, got {self.line}"
            raise ValueError(msg)
        if not self.path:
            msg = "File path cannot be empty"
            raise ValueError(msg)

    def format_body_with_suggestion(self) -> str:
        """Format comment body with suggestion block if present.

        Returns:
            Comment body with GitHub-style suggestion block appended.
        """
        if not self.suggestion:
            return self.body

        # GitHub suggestion syntax
        # https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/incorporating-feedback-in-your-pull-request
        return f"{self.body}\n\n```suggestion\n{self.suggestion}\n```"


@dataclass(frozen=True, slots=True)
class ReviewSubmission:
    """Data for submitting a complete review.

    Attributes:
        summary: Overall review summary (posted as main comment or review body).
        line_comments: List of inline comments with file/line references.
        event: Review event type ('COMMENT', 'APPROVE', 'REQUEST_CHANGES').
    """

    summary: str
    line_comments: tuple[LineComment, ...] = field(default_factory=tuple)
    event: str = field(default="COMMENT")


class GitProvider(ABC):
    """Abstract base class for Git provider integrations.

    This interface defines the contract that all Git providers must implement.
    It enables the reviewer to work with any supported platform (GitHub, GitLab, etc.)
    through a consistent API.

    Each method represents a distinct capability:
    - get_merge_request: Fetch PR/MR metadata and changes
    - get_linked_tasks: Find associated issues/tasks via multiple strategies
    - post_comment: Post general comments (Issue Comments on GitHub)
    - submit_review: Submit review with inline comments (PR Review API on GitHub)
    """

    @abstractmethod
    def get_merge_request(self, repo_name: str, mr_id: int) -> MergeRequest | None:
        """Fetch a merge/pull request from the provider.

        Args:
            repo_name: Repository identifier (e.g., 'owner/repo' for GitHub).
            mr_id: Merge/Pull request number.

        Returns:
            MergeRequest model with PR data, or None if rate limited.

        Raises:
            Exception: If the request fails for reasons other than rate limiting.
        """

    @abstractmethod
    def get_linked_tasks(
        self,
        repo_name: str,
        mr_id: int,
        source_branch: str,
    ) -> tuple[LinkedTask, ...]:
        """Find linked tasks/issues for the merge request.

        Combines multiple discovery strategies (regex, platform API,
        branch name convention) and returns deduplicated results.

        Each strategy is fail-open: if one fails, the others continue.

        Args:
            repo_name: Repository identifier.
            mr_id: Merge/Pull request number.
            source_branch: Source branch name for branch-name strategy.

        Returns:
            Tuple of LinkedTask objects (deduplicated).
        """

    @abstractmethod
    def post_comment(self, repo_name: str, mr_id: int, body: str) -> None:
        """Post a general comment to the merge request.

        This creates a top-level comment (Issue Comment on GitHub,
        Note on GitLab) visible in the conversation thread.

        Use this for:
        - Summary comments
        - Error notifications
        - General feedback

        Args:
            repo_name: Repository identifier.
            mr_id: Merge/Pull request number.
            body: Comment text (markdown supported).

        Raises:
            Exception: If posting fails.
        """

    @abstractmethod
    def submit_review(
        self,
        repo_name: str,
        mr_id: int,
        submission: ReviewSubmission,
    ) -> None:
        """Submit a code review with inline comments.

        This uses the platform's review API to create a proper code review
        with inline comments attached to specific lines. On GitHub, this
        enables the "Apply suggestion" button for suggestions.

        Use this for:
        - Inline code comments
        - Suggestions with one-click apply
        - Structured code reviews

        Args:
            repo_name: Repository identifier.
            mr_id: Merge/Pull request number.
            submission: Review data including summary and line comments.

        Raises:
            Exception: If submission fails.
        """

    # ── Backward compatibility alias ────────────────────────────────

    def get_linked_task(
        self,
        repo_name: str,
        mr: MergeRequest,
    ) -> LinkedTask | None:
        """Find a linked task for the merge request (deprecated).

        .. deprecated::
            Use :meth:`get_linked_tasks` instead. This alias returns
            only the first linked task found or ``None``.

        Args:
            repo_name: Repository identifier.
            mr: MergeRequest model.

        Returns:
            First LinkedTask or None.
        """
        tasks = self.get_linked_tasks(repo_name, mr.number, mr.source_branch)
        return tasks[0] if tasks else None


__all__ = [
    "ISSUE_CLOSING_RE",
    "GitProvider",
    "LineComment",
    "ReviewSubmission",
    "parse_branch_issue_number",
    "parse_diff_valid_lines",
]
