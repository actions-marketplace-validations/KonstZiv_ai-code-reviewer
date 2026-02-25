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
from typing import TYPE_CHECKING, Any

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
from ai_reviewer.integrations.base import ISSUE_CLOSING_RE, GitProvider, parse_branch_issue_number
from ai_reviewer.integrations.conversation import (
    BOT_QUESTION_MARKER,
    BotThread,
    ConversationProvider,
    ThreadStatus,
    format_questions_markdown,
    parse_questions_from_markdown,
)
from ai_reviewer.integrations.repository import RepositoryMetadata, RepositoryProvider
from ai_reviewer.utils.retry import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    with_retry,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ai_reviewer.integrations.base import ReviewSubmission
    from ai_reviewer.integrations.conversation import BotQuestion


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


def _parse_discussion_notes(
    notes: list[dict[str, object]],
    discussion_id: str,
) -> list[Comment]:
    """Parse notes from a GitLab discussion into Comment objects.

    Args:
        notes: List of note dicts from discussion.attributes["notes"].
        discussion_id: The discussion ID for thread grouping.

    Returns:
        List of Comment objects with threading fields populated.
    """
    comments: list[Comment] = []
    first_note_id: str | None = None

    for note_data in notes:
        # Skip system notes (e.g., "merged", "assigned", etc.)
        if note_data.get("system", False):
            continue

        author_data: dict[str, object] = note_data.get("author", {})  # type: ignore[assignment]

        # Determine if it's a bot (use GitLab API "bot" field)
        author_type = CommentAuthorType.USER
        if author_data.get("bot", False):
            author_type = CommentAuthorType.BOT

        # Determine comment type from position
        position = note_data.get("position")
        comment_type = CommentType.REVIEW if position else CommentType.ISSUE

        # Extract file path and line number from position dict
        file_path: str | None = None
        line_number: int | None = None
        if position and isinstance(position, dict):
            file_path = position.get("new_path")
            raw_line = position.get("new_line")
            if raw_line is not None:
                line_number = int(raw_line)

        note_id = str(note_data.get("id", ""))

        # Threading: first note is root, subsequent reply to root
        parent_id: str | None = None
        if first_note_id is None:
            first_note_id = note_id
        else:
            parent_id = first_note_id

        comments.append(
            Comment(
                author=str(author_data.get("username", "unknown")),
                author_type=author_type,
                body=str(note_data.get("body", "")),
                type=comment_type,
                created_at=note_data.get("created_at"),  # type: ignore[arg-type]
                file_path=file_path,
                line_number=line_number,
                comment_id=note_id,
                parent_comment_id=parent_id,
                thread_id=discussion_id,
            )
        )

    return comments


class GitLabClient(GitProvider, RepositoryProvider, ConversationProvider):
    """Client for interacting with GitLab API.

    Implements GitProvider, RepositoryProvider, and ConversationProvider
    interfaces for GitLab-specific operations.

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

        # Fetch comments via discussions API (provides threading)
        comments: list[Comment] = []
        for discussion in mr.discussions.list(iterator=True):
            discussion_id = str(discussion.id)
            notes = discussion.attributes.get("notes", [])
            comments.extend(_parse_discussion_notes(notes, discussion_id))

        # Fetch file changes (single API call instead of N+1)
        changes: list[FileChange] = []
        mr_changes = mr.changes()
        for file_diff in mr_changes.get("changes", []):  # type: ignore[union-attr]
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

    @staticmethod
    def _issue_to_linked_task(issue: Any) -> LinkedTask:  # noqa: ANN401
        """Convert a python-gitlab Issue to LinkedTask.

        Args:
            issue: python-gitlab ProjectIssue object.

        Returns:
            LinkedTask model.
        """
        return LinkedTask(
            identifier=str(issue.iid),
            title=issue.title,
            description=issue.description or "",
            url=issue.web_url,
        )

    def get_linked_tasks(
        self,
        repo_name: str,
        mr_id: int,
        source_branch: str,
    ) -> tuple[LinkedTask, ...]:
        """Find linked tasks via closes_issues API, regex, and branch name.

        Combines three strategies (each fail-open):
        1. GitLab's ``closes_issues()`` API endpoint.
        2. Regex fallback for closing keywords in the MR description.
        3. Branch name convention (e.g. ``86-task-description``).

        Note: This method does NOT use ``@with_retry`` as linked tasks
        are optional. Failure should not block the review.

        Args:
            repo_name: Project path (e.g., 'owner/repo').
            mr_id: Merge request IID.
            source_branch: Source branch name.

        Returns:
            Tuple of LinkedTask objects (deduplicated by issue IID).
        """
        tasks: list[LinkedTask] = []
        seen_ids: set[int] = set()

        try:
            project = self.gitlab.projects.get(repo_name)
            mr = project.mergerequests.get(mr_id)

            # Strategy 1: GitLab closes_issues API
            try:
                for issue in mr.closes_issues():
                    iid = issue.iid
                    if iid not in seen_ids:
                        seen_ids.add(iid)
                        tasks.append(self._issue_to_linked_task(issue))
            except GitlabError:
                logger.debug("closes_issues() unavailable for MR !%s", mr_id)

            # Strategy 2: Regex fallback in description
            description = mr.description or ""
            for match in ISSUE_CLOSING_RE.finditer(description):
                issue_number = int(match.group(1))
                if issue_number in seen_ids:
                    continue
                seen_ids.add(issue_number)
                try:
                    issue = project.issues.get(issue_number)
                    tasks.append(self._issue_to_linked_task(issue))
                except GitlabError:
                    logger.warning("Failed to fetch issue #%s", issue_number)

            # Strategy 3: Branch name convention
            branch_issue = parse_branch_issue_number(source_branch)
            if branch_issue and branch_issue not in seen_ids:
                try:
                    issue = project.issues.get(branch_issue)
                    seen_ids.add(branch_issue)
                    tasks.append(self._issue_to_linked_task(issue))
                except GitlabError:
                    logger.debug("Branch issue #%s not found", branch_issue)

        except GitlabError as e:
            logger.warning("Failed task search for MR !%s: %s", mr_id, e)

        return tuple(tasks)

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

    # ── RepositoryProvider implementation ──────────────────────────────

    @with_retry
    def get_languages(self, repo_name: str) -> dict[str, float]:
        """Get repository languages as percentages.

        GitLab returns percentages natively.

        Args:
            repo_name: Project path (e.g. ``owner/repo``).

        Returns:
            Mapping of language name to percentage (0-100).
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            langs: dict[str, float] = dict(project.languages())  # type: ignore[arg-type]
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e
        else:
            return langs

    @with_retry
    def get_metadata(self, repo_name: str) -> RepositoryMetadata:
        """Get basic repository metadata from GitLab.

        Args:
            repo_name: Project path (e.g. ``owner/repo``).

        Returns:
            RepositoryMetadata populated from the GitLab API.
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            return RepositoryMetadata(
                name=project.path_with_namespace,
                description=project.description,
                default_branch=project.default_branch,
                topics=tuple(project.topics or []),
                license=None,  # GitLab: requires separate API call
                visibility=project.visibility,
                ci_config_path=getattr(project, "ci_config_path", None),
            )
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def get_file_tree(
        self,
        repo_name: str,
        *,
        ref: str | None = None,
    ) -> tuple[str, ...]:
        """Get file paths in the repository (blobs only).

        Uses GitLab's Repository Tree API with ``recursive=True``.

        Args:
            repo_name: Project path (e.g. ``owner/repo``).
            ref: Git ref. Defaults to the default branch.

        Returns:
            Tuple of file paths relative to the repository root.
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            kwargs: dict[str, str] = {"ref": ref} if ref else {}
            items = project.repository_tree(
                recursive=True,
                get_all=True,
                per_page=100,
                **kwargs,
            )
            return tuple(item["path"] for item in items if item["type"] == "blob")
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def get_file_content(
        self,
        repo_name: str,
        path: str,
        *,
        ref: str | None = None,
    ) -> str | None:
        """Get file content as text.

        Args:
            repo_name: Project path (e.g. ``owner/repo``).
            path: File path relative to the repository root.
            ref: Git ref. Defaults to the default branch.

        Returns:
            File content string, or ``None`` for binary files
            or if the file does not exist.
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            file_ref = ref or project.default_branch
            f = project.files.get(path, ref=file_ref)
            try:
                return f.decode().decode("utf-8")
            except UnicodeDecodeError:
                return None  # binary file
        except GitlabError as e:
            if getattr(e, "response_code", None) == HTTP_NOT_FOUND:
                return None
            raise _convert_gitlab_exception(e) from e

    # ── ConversationProvider implementation ──────────────────────────

    @with_retry
    def post_question_comment(
        self,
        repo_name: str,
        mr_id: int,
        questions: Sequence[BotQuestion],
        *,
        intro: str = "",
    ) -> str:
        """Post a discussion with structured bot questions.

        Creates a new discussion (not a plain note) so that GitLab's
        native threading is used for responses.

        Args:
            repo_name: Project path (e.g., 'owner/repo').
            mr_id: Merge request IID.
            questions: Questions to post.
            intro: Optional introductory text.

        Returns:
            The discussion ID as a string.
        """
        try:
            body = format_questions_markdown(questions, intro)
            project = self.gitlab.projects.get(repo_name)
            mr = project.mergerequests.get(mr_id)
            discussion = mr.discussions.create({"body": body})
            logger.info("Posted question discussion to MR !%s in %s", mr_id, repo_name)
            return str(discussion.id)
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def reply_in_thread(
        self,
        repo_name: str,
        mr_id: int,
        thread_id: str,
        body: str,
    ) -> str:
        """Reply in an existing GitLab discussion thread.

        Args:
            repo_name: Project path (e.g., 'owner/repo').
            mr_id: Merge request IID.
            thread_id: Discussion ID to reply in.
            body: Reply text (markdown supported).

        Returns:
            The new note ID as a string.
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            mr = project.mergerequests.get(mr_id)
            discussion = mr.discussions.get(thread_id)
            note = discussion.notes.create({"body": body})
            logger.info(
                "Posted reply to discussion %s on MR !%s in %s",
                thread_id,
                mr_id,
                repo_name,
            )
            return str(note["id"])  # type: ignore[index]
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def get_bot_threads(
        self,
        repo_name: str,
        mr_id: int,
    ) -> tuple[BotThread, ...]:
        """Find all bot-initiated question threads on the MR.

        Scans discussions for the bot question marker in the first note,
        then collects subsequent non-system notes as responses. Uses
        GitLab's native ``resolved`` status for thread resolution.

        Args:
            repo_name: Project path (e.g., 'owner/repo').
            mr_id: Merge request IID.

        Returns:
            Tuple of BotThread objects with questions and responses.
        """
        try:
            project = self.gitlab.projects.get(repo_name)
            mr = project.mergerequests.get(mr_id)
            threads: list[BotThread] = []

            for discussion in mr.discussions.list(iterator=True):
                notes = discussion.attributes.get("notes", [])
                if not notes:
                    continue

                first_note = notes[0]
                body = str(first_note.get("body", ""))
                if BOT_QUESTION_MARKER not in body:
                    continue

                questions = parse_questions_from_markdown(body)
                if not questions:
                    continue

                # Collect non-system responses from subsequent notes
                responses: list[Comment] = []
                for note_data in notes[1:]:
                    if note_data.get("system", False):
                        continue

                    author_data: dict[str, object] = note_data.get("author", {})
                    is_bot = bool(author_data.get("bot", False))

                    responses.append(
                        Comment(
                            author=str(author_data.get("username", "unknown")),
                            author_type=(
                                CommentAuthorType.BOT if is_bot else CommentAuthorType.USER
                            ),
                            body=str(note_data.get("body", "")),
                            type=CommentType.ISSUE,
                            created_at=note_data.get("created_at"),
                            comment_id=str(note_data.get("id", "")),
                            thread_id=str(discussion.id),
                        )
                    )

                # Determine status
                is_resolved = discussion.attributes.get("resolved", False)
                if is_resolved:
                    status = ThreadStatus.RESOLVED
                elif responses:
                    status = ThreadStatus.ANSWERED
                else:
                    status = ThreadStatus.PENDING

                discussion_id = str(discussion.id)
                threads.append(
                    BotThread(
                        thread_id=discussion_id,
                        platform_thread_id=discussion_id,
                        mr_id=mr_id,
                        questions=tuple(questions),
                        responses=tuple(responses),
                        status=status,
                    )
                )

            return tuple(threads)
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e
