"""Core data models for AI Code Reviewer.

This module defines Pydantic models for representing merge requests,
linked tasks, review context, and review results.

All datetime fields must be timezone-aware (have tzinfo set).
All models are frozen (immutable) to prevent accidental mutations.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - required at runtime for Pydantic
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_timezone_aware(v: datetime | None, field_name: str) -> datetime | None:
    """Validate that datetime is timezone-aware.

    Args:
        v: The datetime value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated datetime value.

    Raises:
        ValueError: If datetime is naive (no timezone info).
    """
    if v is not None and v.tzinfo is None:
        msg = f"{field_name} must be timezone-aware (e.g., use datetime.now(timezone.utc))"
        raise ValueError(msg)
    return v


class CommentAuthorType(str, Enum):
    """Type of comment author."""

    USER = "user"
    BOT = "bot"


class FileChangeType(str, Enum):
    """Type of file change in a merge request."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class Comment(BaseModel):
    """A comment on a merge request.

    Attributes:
        author: The username of the comment author.
        author_type: Whether the author is a user or bot.
        body: The content of the comment.
        created_at: When the comment was created (must be timezone-aware).
    """

    model_config = ConfigDict(frozen=True)

    author: str = Field(..., min_length=1, description="Username of the comment author")
    author_type: CommentAuthorType = Field(
        default=CommentAuthorType.USER, description="Type of author (user or bot)"
    )
    body: str = Field(..., description="Content of the comment")
    created_at: datetime | None = Field(default=None, description="When the comment was created")

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone(cls, v: datetime | None) -> datetime | None:
        """Ensure created_at is timezone-aware."""
        return _validate_timezone_aware(v, "created_at")


class FileChange(BaseModel):
    """A file change in a merge request.

    Attributes:
        filename: Path to the changed file.
        change_type: Type of change (added, modified, deleted, renamed).
        additions: Number of lines added.
        deletions: Number of lines deleted.
        patch: The diff patch content (may be None for binary files).
        previous_filename: Previous filename if renamed.
    """

    model_config = ConfigDict(frozen=True)

    filename: str = Field(..., min_length=1, description="Path to the changed file")
    change_type: FileChangeType = Field(..., description="Type of change")
    additions: int = Field(default=0, ge=0, description="Number of lines added")
    deletions: int = Field(default=0, ge=0, description="Number of lines deleted")
    patch: str | None = Field(default=None, description="Diff patch content")
    previous_filename: str | None = Field(default=None, description="Previous filename if renamed")

    @field_validator("previous_filename")
    @classmethod
    def validate_previous_filename(cls, v: str | None) -> str | None:
        """Validate that empty previous_filename is converted to None."""
        if v is not None and v.strip() == "":
            return None
        return v


class MergeRequest(BaseModel):
    """A merge request (pull request) to be reviewed.

    Attributes:
        number: The MR/PR number.
        title: Title of the merge request.
        description: Body/description of the merge request.
        author: Username of the MR author.
        source_branch: The branch being merged from.
        target_branch: The branch being merged into.
        comments: List of comments on the MR.
        changes: List of file changes in the MR.
        url: URL to the merge request.
        created_at: When the MR was created (must be timezone-aware).
        updated_at: When the MR was last updated (must be timezone-aware).
    """

    model_config = ConfigDict(frozen=True)

    number: int = Field(..., gt=0, description="MR/PR number")
    title: str = Field(..., min_length=1, description="Title of the merge request")
    description: str = Field(default="", description="Body/description of the merge request")
    author: str = Field(..., min_length=1, description="Username of the MR author")
    source_branch: str = Field(..., min_length=1, description="Branch being merged from")
    target_branch: str = Field(..., min_length=1, description="Branch being merged into")
    comments: tuple[Comment, ...] = Field(default=(), description="Comments on the MR")
    changes: tuple[FileChange, ...] = Field(default=(), description="File changes in the MR")
    url: str | None = Field(default=None, description="URL to the merge request")
    created_at: datetime | None = Field(default=None, description="When the MR was created")
    updated_at: datetime | None = Field(default=None, description="When the MR was last updated")

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_datetime_timezone(cls, v: datetime | None) -> datetime | None:
        """Ensure datetime fields are timezone-aware."""
        return _validate_timezone_aware(v, "created_at/updated_at")

    @property
    def total_additions(self) -> int:
        """Calculate total lines added across all file changes."""
        return sum(change.additions for change in self.changes)

    @property
    def total_deletions(self) -> int:
        """Calculate total lines deleted across all file changes."""
        return sum(change.deletions for change in self.changes)

    @property
    def files_changed(self) -> int:
        """Get the number of files changed."""
        return len(self.changes)


class LinkedTask(BaseModel):
    """A task/issue linked to a merge request.

    Attributes:
        identifier: The task identifier (e.g., issue number or external ID).
        title: Title of the task.
        description: Description/body of the task.
        url: URL to the task (optional).
    """

    model_config = ConfigDict(frozen=True)

    identifier: str = Field(..., min_length=1, description="Task identifier")
    title: str = Field(..., min_length=1, description="Title of the task")
    description: str = Field(default="", description="Description of the task")
    url: str | None = Field(default=None, description="URL to the task")


class ReviewContext(BaseModel):
    """Context for performing a code review.

    Combines the merge request data with an optional linked task
    to provide full context for the AI reviewer.

    Attributes:
        mr: The merge request to review.
        task: The linked task (if any).
        repository: Repository name in owner/repo format.
    """

    model_config = ConfigDict(frozen=True)

    mr: MergeRequest = Field(..., description="The merge request to review")
    task: LinkedTask | None = Field(default=None, description="Linked task if available")
    repository: str = Field(..., min_length=1, description="Repository name (owner/repo)")

    @field_validator("repository")
    @classmethod
    def validate_repository_format(cls, v: str) -> str:
        """Validate repository is in owner/repo format."""
        if v.count("/") != 1:
            msg = "Repository must be in 'owner/repo' format"
            raise ValueError(msg)
        owner, repo = v.split("/")
        if not owner or not repo:
            msg = "Repository must be in 'owner/repo' format"
            raise ValueError(msg)
        return v

    @property
    def has_linked_task(self) -> bool:
        """Check if a task is linked to this review context."""
        return self.task is not None


class VulnerabilitySeverity(str, Enum):
    """Severity level of a detected vulnerability."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Vulnerability(BaseModel):
    """A detected vulnerability in the code.

    Attributes:
        title: Short title of the vulnerability.
        description: Detailed description of the vulnerability.
        severity: Severity level.
        file: File where the vulnerability was found (optional).
        line: Line number where the vulnerability was found (optional).
        recommendation: Suggested fix for the vulnerability.
    """

    model_config = ConfigDict(frozen=True)

    title: str = Field(..., min_length=1, description="Short title of the vulnerability")
    description: str = Field(..., min_length=1, description="Detailed description")
    severity: VulnerabilitySeverity = Field(..., description="Severity level")
    file: str | None = Field(default=None, description="File where found")
    line: int | None = Field(default=None, gt=0, description="Line number")
    recommendation: str = Field(default="", description="Suggested fix")


class TaskAlignmentStatus(str, Enum):
    """Status of task alignment check."""

    ALIGNED = "aligned"
    MISALIGNED = "misaligned"
    INSUFFICIENT_DATA = "insufficient_data"


class ReviewResult(BaseModel):
    """Result of an AI code review.

    Attributes:
        vulnerabilities: List of detected vulnerabilities.
        task_alignment: Whether code changes align with the linked task.
        task_alignment_reasoning: Explanation of task alignment assessment.
        summary: Brief summary of the review.
        reviewed_at: When the review was performed (must be timezone-aware).
    """

    model_config = ConfigDict(frozen=True)

    vulnerabilities: tuple[Vulnerability, ...] = Field(
        default=(), description="Detected vulnerabilities"
    )
    task_alignment: TaskAlignmentStatus = Field(
        default=TaskAlignmentStatus.INSUFFICIENT_DATA,
        description="Task alignment status",
    )
    task_alignment_reasoning: str = Field(
        default="", description="Explanation of task alignment assessment"
    )
    summary: str = Field(default="", description="Brief summary of the review")
    reviewed_at: datetime | None = Field(default=None, description="When the review was performed")

    @field_validator("reviewed_at")
    @classmethod
    def validate_reviewed_at_timezone(cls, v: datetime | None) -> datetime | None:
        """Ensure reviewed_at is timezone-aware."""
        return _validate_timezone_aware(v, "reviewed_at")

    @property
    def has_critical_vulnerabilities(self) -> bool:
        """Check if any critical vulnerabilities were found."""
        return any(v.severity == VulnerabilitySeverity.CRITICAL for v in self.vulnerabilities)

    @property
    def has_high_or_critical_vulnerabilities(self) -> bool:
        """Check if any high or critical vulnerabilities were found."""
        return any(
            v.severity in (VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH)
            for v in self.vulnerabilities
        )

    @property
    def vulnerability_count(self) -> int:
        """Get total number of vulnerabilities."""
        return len(self.vulnerabilities)

    @property
    def matches_task(self) -> bool | None:
        """Check if code changes match the linked task.

        This is a tri-state property for task alignment assessment:

        Returns:
            True: Task and code changes are aligned.
            False: Code changes contradict or don't match the task.
            None: Insufficient context to determine alignment
                  (e.g., no linked task, unclear task description).
        """
        if self.task_alignment == TaskAlignmentStatus.ALIGNED:
            return True
        if self.task_alignment == TaskAlignmentStatus.MISALIGNED:
            return False
        return None


# Public API - explicitly define what should be imported from this module
__all__ = [
    "Comment",
    "CommentAuthorType",
    "FileChange",
    "FileChangeType",
    "LinkedTask",
    "MergeRequest",
    "ReviewContext",
    "ReviewResult",
    "TaskAlignmentStatus",
    "Vulnerability",
    "VulnerabilitySeverity",
]
