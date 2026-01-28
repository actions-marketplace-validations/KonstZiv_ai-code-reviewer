"""GitLab integration for AI Code Reviewer.

This module provides a client for interacting with the GitLab API using python-gitlab.
It handles fetching merge requests, retrieving linked issues, and posting review comments
including inline comments through the Discussions API.

Reference:
    - python-gitlab docs: https://python-gitlab.readthedocs.io/
    - GitLab Discussions API: https://docs.gitlab.com/api/discussions/
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import gitlab
from gitlab.exceptions import GitlabAuthenticationError, GitlabError

from ai_reviewer.core.models import (
    Comment,
    CommentAuthorType,
    CommentType,
    FileChange,
    FileChangeType,
    LinkedTask,
    MergeRequest,
)
from ai_reviewer.integrations.base import GitProvider
from ai_reviewer.utils.retry import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    with_retry,
)

if TYPE_CHECKING:
    from ai_reviewer.integrations.base import ReviewSubmission


logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500


def _convert_gitlab_exception(e: GitlabError) -> Exception:
    """Convert python-gitlab exception to our exception hierarchy.

    Args:
        e: python-gitlab exception.

    Returns:
        Converted exception (RetryableError or APIClientError).
    """
    # GitlabAuthenticationError is a specific subclass
    if isinstance(e, GitlabAuthenticationError):
        return AuthenticationError(f"GitLab: {e}")

    # Check response_code attribute
    status = getattr(e, "response_code", None)
    message = f"GitLab: {e}"

    # Mapping of status codes to exception types
    status_map: dict[int, type[Exception]] = {
        HTTP_UNAUTHORIZED: AuthenticationError,
        HTTP_FORBIDDEN: ForbiddenError,
        HTTP_NOT_FOUND: NotFoundError,
        HTTP_TOO_MANY_REQUESTS: RateLimitError,
    }

    if status in status_map:
        return status_map[status](message)

    if status is not None and status >= HTTP_INTERNAL_SERVER_ERROR:
        return ServerError(message, status_code=status)

    # For other errors, return as-is (will not be retried)
    return e


class GitLabClient(GitProvider):
    """Client for interacting with GitLab API.

    Implements the GitProvider interface for GitLab-specific operations.

    Attributes:
        gitlab: The python-gitlab instance.
    """

    def __init__(self, token: str, url: str = "https://gitlab.com") -> None:
        """Initialize GitLab client.

        Args:
            token: GitLab personal access token.
            url: GitLab server URL (default: https://gitlab.com).
        """
        self.gitlab = gitlab.Gitlab(url=url, private_token=token)
        self._url = url
        logger.debug("GitLab client initialized for %s", url)

    @with_retry
    def get_merge_request(self, repo_name: str, mr_id: int) -> MergeRequest:
        """Fetch a merge request from GitLab and convert to MergeRequest model.

        Args:
            repo_name: Project path (e.g., 'owner/repo' or 'group/subgroup/repo').
            mr_id: Merge request IID (project-level ID).

        Returns:
            MergeRequest model populated with MR data.

        Raises:
            AuthenticationError: If token is invalid.
            NotFoundError: If MR or project doesn't exist.
            RateLimitError: If rate limit exceeded (will retry).
            ServerError: If GitLab server error (will retry).
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            mr = project.mergerequests.get(mr_id)
        except GitlabError as e:
            logger.warning("GitLab API error for MR !%s in %s: %s", mr_id, repo_name, e)
            raise _convert_gitlab_exception(e) from e

        # Fetch notes (comments)
        comments: list[Comment] = []

        # GitLab notes include both general and inline comments
        for note in mr.notes.list(iterator=True):
            # Skip system notes (e.g., "merged", "assigned", etc.)
            if note.system:
                continue

            # Determine if it's a bot
            author_type = CommentAuthorType.USER
            is_bot = (
                hasattr(note.author, "bot") and note.author.get("bot")
            ) or "bot" in note.author.get("username", "").lower()
            if is_bot:
                author_type = CommentAuthorType.BOT

            # Determine comment type (position indicates inline comment)
            comment_type = CommentType.REVIEW if note.position else CommentType.ISSUE

            comments.append(
                Comment(
                    author=note.author.get("username", "unknown"),
                    author_type=author_type,
                    body=note.body,
                    type=comment_type,
                    created_at=note.created_at,
                )
            )

        # Fetch file changes
        changes: list[FileChange] = []
        for diff in mr.diffs.list(iterator=True):
            diff_detail = mr.diffs.get(diff.id)
            for file_diff in diff_detail.diffs:
                # Determine change type
                if file_diff.get("new_file"):
                    change_type = FileChangeType.ADDED
                elif file_diff.get("deleted_file"):
                    change_type = FileChangeType.DELETED
                elif file_diff.get("renamed_file"):
                    change_type = FileChangeType.RENAMED
                else:
                    change_type = FileChangeType.MODIFIED

                # Count additions/deletions from diff
                diff_content = file_diff.get("diff", "")
                additions = sum(1 for line in diff_content.split("\n") if line.startswith("+"))
                deletions = sum(1 for line in diff_content.split("\n") if line.startswith("-"))

                changes.append(
                    FileChange(
                        filename=file_diff.get("new_path", file_diff.get("old_path", "")),
                        change_type=change_type,
                        additions=additions,
                        deletions=deletions,
                        patch=diff_content if diff_content else None,
                        previous_filename=file_diff.get("old_path")
                        if file_diff.get("renamed_file")
                        else None,
                    )
                )

        return MergeRequest(
            number=mr.iid,
            title=mr.title,
            description=mr.description or "",
            author=mr.author.get("username", "unknown"),
            source_branch=mr.source_branch,
            target_branch=mr.target_branch,
            comments=tuple(comments),
            changes=tuple(changes),
            url=mr.web_url,
            created_at=mr.created_at,
            updated_at=mr.updated_at,
        )

    def get_linked_task(self, repo_name: str, mr: MergeRequest) -> LinkedTask | None:
        """Attempt to find a linked issue for the MR.

        Looks for patterns like "Closes #123" or "Fixes #123" in the MR description.
        If found, fetches the issue details from GitLab.

        Note: This method does NOT use retry as linked task is optional.
        Failure to fetch linked task should not block the review.

        Args:
            repo_name: Project path (e.g., 'owner/repo').
            mr: The MergeRequest object to check.

        Returns:
            LinkedTask if found, None otherwise.
        """
        if not mr.description:
            return None

        # GitLab keywords for closing issues
        # https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically
        pattern = r"(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)"
        match = re.search(pattern, mr.description, re.IGNORECASE)

        if not match:
            return None

        issue_number = int(match.group(1))

        try:
            project = self.gitlab.projects.get(repo_name)
            issue = project.issues.get(issue_number)

            return LinkedTask(
                identifier=str(issue.iid),
                title=issue.title,
                description=issue.description or "",
                url=issue.web_url,
            )
        except GitlabError as e:
            logger.warning("Found issue link #%s but failed to fetch it: %s", issue_number, e)
            return None

    @with_retry
    def post_comment(self, repo_name: str, mr_id: int, body: str) -> None:
        """Post a general comment (note) to the merge request.

        Creates a note visible in the MR discussion thread.
        Use this for summary comments, error notifications, etc.

        Args:
            repo_name: Project path (e.g., 'owner/repo').
            mr_id: Merge request IID.
            body: The comment text to post.

        Raises:
            AuthenticationError: If token is invalid.
            ForbiddenError: If insufficient permissions.
            RateLimitError: If rate limit exceeded (will retry).
            ServerError: If GitLab server error (will retry).
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            mr = project.mergerequests.get(mr_id)
            mr.notes.create({"body": body})
            logger.info("Posted comment to MR !%s in %s", mr_id, repo_name)
        except GitlabError as e:
            logger.warning("Failed to post comment to MR !%s in %s: %s", mr_id, repo_name, e)
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def submit_review(
        self,
        repo_name: str,
        mr_id: int,
        submission: ReviewSubmission,
    ) -> None:
        """Submit a code review with inline comments.

        Uses GitLab's Discussions API to create inline comments attached
        to specific lines in the diff.

        Args:
            repo_name: Project path (e.g., 'owner/repo').
            mr_id: Merge request IID.
            submission: Review data including summary and line comments.

        Raises:
            AuthenticationError: If token is invalid.
            ForbiddenError: If insufficient permissions.
            RateLimitError: If rate limit exceeded (will retry).
            ServerError: If GitLab server error (will retry).
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            mr = project.mergerequests.get(mr_id)

            # Get diff refs for positioning
            diff_refs = mr.diff_refs
            if not diff_refs:
                logger.warning("No diff_refs available for MR !%s, posting summary only", mr_id)
                if submission.summary:
                    mr.notes.create({"body": submission.summary})
                return

            base_sha = diff_refs.get("base_sha")
            start_sha = diff_refs.get("start_sha")
            head_sha = diff_refs.get("head_sha")

            # Post inline comments as discussions
            for line_comment in submission.line_comments:
                # Build position for inline comment
                position = {
                    "base_sha": base_sha,
                    "start_sha": start_sha,
                    "head_sha": head_sha,
                    "position_type": "text",
                    "new_path": line_comment.path,
                    "old_path": line_comment.path,
                }

                # Set line based on side
                if line_comment.side == "LEFT":
                    position["old_line"] = line_comment.line
                else:
                    position["new_line"] = line_comment.line

                # Format body with suggestion if present
                body = line_comment.format_body_with_suggestion()

                try:
                    mr.discussions.create({"body": body, "position": position})
                except GitlabError as e:
                    # Log but continue with other comments
                    logger.warning(
                        "Failed to post inline comment at %s:%d: %s",
                        line_comment.path,
                        line_comment.line,
                        e,
                    )

            # Post summary as a regular note
            if submission.summary:
                mr.notes.create({"body": submission.summary})

            logger.info(
                "Submitted review to MR !%s in %s with %d inline comments",
                mr_id,
                repo_name,
                len(submission.line_comments),
            )

        except GitlabError as e:
            logger.warning("Failed to submit review to MR !%s in %s: %s", mr_id, repo_name, e)
            raise _convert_gitlab_exception(e) from e
