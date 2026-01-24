"""Base abstractions for Git provider integrations.

This module defines the abstract interface for Git providers (GitHub, GitLab, etc.)
and common data structures used across all providers.

The GitProvider ABC ensures consistent behavior across different platforms,
enabling the reviewer to work with any supported Git provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_reviewer.core.models import LinkedTask, MergeRequest


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
    - get_linked_task: Find associated issues/tasks
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
    def get_linked_task(self, repo_name: str, mr: MergeRequest) -> LinkedTask | None:
        """Find a linked task/issue for the merge request.

        Searches the MR description for issue references and fetches
        the linked issue details.

        Args:
            repo_name: Repository identifier.
            mr: The MergeRequest to search for linked tasks.

        Returns:
            LinkedTask if found, None otherwise.
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


__all__ = [
    "GitProvider",
    "LineComment",
    "ReviewSubmission",
]
