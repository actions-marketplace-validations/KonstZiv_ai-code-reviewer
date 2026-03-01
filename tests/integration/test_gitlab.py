"""Integration tests for GitLab client."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from gitlab.exceptions import GitlabAuthenticationError, GitlabError

from ai_reviewer.core.models import (
    CommentAuthorType,
    CommentType,
    FileChangeType,
    MergeRequest,
)
from ai_reviewer.integrations.base import GitProvider, LineComment, ReviewSubmission
from ai_reviewer.integrations.gitlab import GitLabClient
from ai_reviewer.utils.retry import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)


def _make_discussion(
    discussion_id: str,
    notes: list[dict[str, object]],
) -> Mock:
    """Create a mock GitLab discussion object.

    Args:
        discussion_id: Discussion ID (hex string).
        notes: List of note dicts with keys: id, system, author, body, position, created_at.

    Returns:
        Mock discussion object with attributes["notes"].
    """
    discussion = Mock()
    discussion.id = discussion_id
    discussion.attributes = {"notes": notes}
    return discussion


class TestGitLabClient:
    """Tests for GitLabClient."""

    @pytest.fixture
    def mock_gitlab(self) -> MagicMock:
        """Mock python-gitlab instance."""
        with patch("ai_reviewer.integrations.gitlab.gitlab.Gitlab") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_gitlab: MagicMock) -> GitLabClient:
        """Create GitLabClient instance with mocked Gitlab."""
        return GitLabClient("test-token", "https://gitlab.example.com")

    def test_init(self, mock_gitlab: MagicMock) -> None:
        """Test client initialization."""
        GitLabClient("test-token", "https://gitlab.example.com")
        mock_gitlab.assert_called_once_with(
            url="https://gitlab.example.com", private_token="test-token"
        )

    def test_init_default_url(self, mock_gitlab: MagicMock) -> None:
        """Test client initialization with default URL."""
        GitLabClient("test-token")
        mock_gitlab.assert_called_once_with(url="https://gitlab.com", private_token="test-token")

    def test_implements_git_provider(self, client: GitLabClient) -> None:
        """Test that GitLabClient implements GitProvider interface."""
        assert isinstance(client, GitProvider)

    def test_get_merge_request_success(self, client: GitLabClient) -> None:
        """Test successful MR fetching with notes and diffs."""
        # Mock Project and MR
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        # Setup MR data
        mock_mr.iid = 1
        mock_mr.title = "Test MR"
        mock_mr.description = "Description"
        mock_mr.author = {"username": "author"}
        mock_mr.source_branch = "feature"
        mock_mr.target_branch = "main"
        mock_mr.web_url = "https://gitlab.com/owner/repo/-/merge_requests/1"
        mock_mr.created_at = "2024-01-01T00:00:00Z"
        mock_mr.updated_at = "2024-01-01T00:00:00Z"

        # Mock Discussions (replaces notes.list)
        discussion = _make_discussion(
            "disc1",
            [
                {
                    "id": 1,
                    "system": False,
                    "author": {"username": "user1", "bot": False},
                    "body": "LGTM",
                    "position": None,
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        )
        mock_mr.discussions.list.return_value = [discussion]

        # Mock changes (single API call instead of N+1 diffs)
        mock_mr.changes.return_value = {
            "changes": [
                {
                    "new_file": False,
                    "deleted_file": False,
                    "renamed_file": False,
                    "new_path": "test.py",
                    "old_path": "test.py",
                    "diff": "@@ -1,1 +1,2 @@\n-old\n+new\n+added",
                }
            ]
        }

        # Execute
        mr = client.get_merge_request("owner/repo", 1)

        # Verify
        assert isinstance(mr, MergeRequest)
        assert mr.number == 1
        assert mr.title == "Test MR"
        assert len(mr.comments) == 1
        assert mr.comments[0].type == CommentType.ISSUE
        assert mr.comments[0].author_type == CommentAuthorType.USER
        assert mr.comments[0].file_path is None
        assert mr.comments[0].line_number is None
        assert len(mr.changes) == 1
        assert mr.changes[0].filename == "test.py"
        assert mr.changes[0].change_type == FileChangeType.MODIFIED

    def test_get_merge_request_with_bot_note(self, client: GitLabClient) -> None:
        """Test MR fetching with bot note."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        # Setup minimal MR data
        mock_mr.iid = 1
        mock_mr.title = "Test"
        mock_mr.description = ""
        mock_mr.author = {"username": "author"}
        mock_mr.source_branch = "head"
        mock_mr.target_branch = "base"
        mock_mr.web_url = "url"
        mock_mr.created_at = "2024-01-01T00:00:00Z"
        mock_mr.updated_at = "2024-01-01T00:00:00Z"
        mock_mr.changes.return_value = {"changes": []}

        # Mock discussion with bot note
        discussion = _make_discussion(
            "disc2",
            [
                {
                    "id": 10,
                    "system": False,
                    "author": {"username": "review-bot", "bot": True},
                    "body": "Auto review",
                    "position": {"new_line": 10, "new_path": "src/main.py"},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        )
        mock_mr.discussions.list.return_value = [discussion]

        mr = client.get_merge_request("owner/repo", 1)

        assert len(mr.comments) == 1
        assert mr.comments[0].author_type == CommentAuthorType.BOT
        assert mr.comments[0].type == CommentType.REVIEW
        assert mr.comments[0].file_path == "src/main.py"
        assert mr.comments[0].line_number == 10

    def test_get_merge_request_skips_system_notes(self, client: GitLabClient) -> None:
        """Test that system notes are skipped."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        # Setup minimal MR data
        mock_mr.iid = 1
        mock_mr.title = "Test"
        mock_mr.description = ""
        mock_mr.author = {"username": "author"}
        mock_mr.source_branch = "head"
        mock_mr.target_branch = "base"
        mock_mr.web_url = "url"
        mock_mr.created_at = "2024-01-01T00:00:00Z"
        mock_mr.updated_at = "2024-01-01T00:00:00Z"
        mock_mr.changes.return_value = {"changes": []}

        # Mock discussion with system note
        discussion = _make_discussion(
            "disc3",
            [
                {
                    "id": 20,
                    "system": True,  # System note - should be skipped
                    "author": {"username": "gitlab"},
                    "body": "merged",
                    "position": None,
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        )
        mock_mr.discussions.list.return_value = [discussion]

        mr = client.get_merge_request("owner/repo", 1)

        assert len(mr.comments) == 0

    def test_get_merge_request_note_without_position(self, client: GitLabClient) -> None:
        """Test MR fetching when note has no position (general comment)."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        # Setup minimal MR data
        mock_mr.iid = 1
        mock_mr.title = "Test"
        mock_mr.description = ""
        mock_mr.author = {"username": "author"}
        mock_mr.source_branch = "head"
        mock_mr.target_branch = "base"
        mock_mr.web_url = "url"
        mock_mr.created_at = "2024-01-01T00:00:00Z"
        mock_mr.updated_at = "2024-01-01T00:00:00Z"
        mock_mr.changes.return_value = {"changes": []}

        # Discussion with note that has no position key
        discussion = _make_discussion(
            "disc4",
            [
                {
                    "id": 30,
                    "system": False,
                    "author": {"username": "user1"},
                    "body": "General comment",
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        )
        mock_mr.discussions.list.return_value = [discussion]

        mr = client.get_merge_request("owner/repo", 1)

        assert len(mr.comments) == 1
        assert mr.comments[0].type == CommentType.ISSUE
        assert mr.comments[0].body == "General comment"

    def test_get_merge_request_discussion_threading(self, client: GitLabClient) -> None:
        """Test that discussions provide proper threading fields."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        mock_mr.iid = 1
        mock_mr.title = "Test"
        mock_mr.description = ""
        mock_mr.author = {"username": "author"}
        mock_mr.source_branch = "head"
        mock_mr.target_branch = "base"
        mock_mr.web_url = "url"
        mock_mr.created_at = "2024-01-01T00:00:00Z"
        mock_mr.updated_at = "2024-01-01T00:00:00Z"
        mock_mr.changes.return_value = {"changes": []}

        # Discussion with 2 notes (root + reply)
        discussion = _make_discussion(
            "abc123",
            [
                {
                    "id": 1,
                    "system": False,
                    "author": {"username": "user1"},
                    "body": "Root comment",
                    "position": None,
                    "created_at": "2024-01-01T10:00:00Z",
                },
                {
                    "id": 2,
                    "system": False,
                    "author": {"username": "user2"},
                    "body": "Reply",
                    "position": None,
                    "created_at": "2024-01-01T11:00:00Z",
                },
            ],
        )
        mock_mr.discussions.list.return_value = [discussion]

        mr = client.get_merge_request("owner/repo", 1)

        assert len(mr.comments) == 2
        # Root
        assert mr.comments[0].thread_id == "abc123"
        assert mr.comments[0].comment_id == "1"
        assert mr.comments[0].parent_comment_id is None
        # Reply
        assert mr.comments[1].thread_id == "abc123"
        assert mr.comments[1].comment_id == "2"
        assert mr.comments[1].parent_comment_id == "1"

    def test_get_linked_tasks_closes_issues(self, client: GitLabClient) -> None:
        """Test finding linked tasks via closes_issues API."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.description = ""

        mock_issue = Mock()
        mock_issue.iid = 42
        mock_issue.title = "Bug"
        mock_issue.description = "desc"
        mock_issue.web_url = "https://gitlab.com/g/r/-/issues/42"
        mock_mr.closes_issues.return_value = [mock_issue]

        tasks = client.get_linked_tasks("owner/repo", 1, "feat")

        assert len(tasks) == 1
        assert tasks[0].identifier == "42"
        assert tasks[0].title == "Bug"

    def test_get_linked_tasks_regex_fallback(self, client: GitLabClient) -> None:
        """Test regex fallback when closes_issues returns nothing."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.description = "Fixes #99"
        mock_mr.closes_issues.return_value = []

        mock_issue = Mock()
        mock_issue.iid = 99
        mock_issue.title = "Feature"
        mock_issue.description = ""
        mock_issue.web_url = "url"
        mock_project.issues.get.return_value = mock_issue

        tasks = client.get_linked_tasks("owner/repo", 1, "feat")

        assert len(tasks) == 1
        assert tasks[0].identifier == "99"

    def test_get_linked_tasks_branch_name(self, client: GitLabClient) -> None:
        """Test finding linked tasks via branch name convention."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.description = ""
        mock_mr.closes_issues.return_value = []

        mock_issue = Mock()
        mock_issue.iid = 86
        mock_issue.title = "From Branch"
        mock_issue.description = ""
        mock_issue.web_url = "url"
        mock_project.issues.get.return_value = mock_issue

        tasks = client.get_linked_tasks("owner/repo", 1, "86-task-22-ci")

        assert len(tasks) == 1
        assert tasks[0].identifier == "86"

    def test_get_linked_tasks_deduplication(self, client: GitLabClient) -> None:
        """Test deduplication between API and regex results."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.description = "Fixes #42"

        mock_issue = Mock()
        mock_issue.iid = 42
        mock_issue.title = "Bug"
        mock_issue.description = ""
        mock_issue.web_url = "url"
        mock_mr.closes_issues.return_value = [mock_issue]

        tasks = client.get_linked_tasks("owner/repo", 1, "42-fix")

        assert len(tasks) == 1

    def test_get_linked_tasks_fail_open(self, client: GitLabClient) -> None:
        """Test graceful handling when closes_issues fails."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.description = "Fixes #10"
        mock_mr.closes_issues.side_effect = GitlabError("403")

        mock_issue = Mock()
        mock_issue.iid = 10
        mock_issue.title = "Task"
        mock_issue.description = ""
        mock_issue.web_url = "url"
        mock_project.issues.get.return_value = mock_issue

        tasks = client.get_linked_tasks("owner/repo", 1, "feat")

        assert len(tasks) == 1
        assert tasks[0].identifier == "10"

    def test_get_linked_tasks_empty(self, client: GitLabClient) -> None:
        """Test when no linked tasks found."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.description = "No links"
        mock_mr.closes_issues.return_value = []

        tasks = client.get_linked_tasks("owner/repo", 1, "main")

        assert tasks == ()

    def test_post_comment_success(self, client: GitLabClient) -> None:
        """Test successful comment posting."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        client.post_comment("owner/repo", 1, "Test comment")

        mock_mr.notes.create.assert_called_once_with({"body": "Test comment"})

    def test_submit_review_success(self, client: GitLabClient) -> None:
        """Test successful review submission with inline comments."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        mock_mr.diff_refs = {
            "base_sha": "abc",
            "start_sha": "def",
            "head_sha": "ghi",
        }

        # Create submission with inline comments
        submission = ReviewSubmission(
            summary="Please fix these issues",
            line_comments=(
                LineComment(path="src/main.py", line=10, body="Fix this"),
                LineComment(
                    path="src/utils.py",
                    line=5,
                    body="Use f-string",
                    suggestion='print(f"Hello {name}")',
                ),
            ),
            event="COMMENT",
        )

        client.submit_review("owner/repo", 1, submission)

        # Verify discussions were created
        assert mock_mr.discussions.create.call_count == 2

        # Verify summary note was created
        mock_mr.notes.create.assert_called_once_with({"body": "Please fix these issues"})

    def test_submit_review_no_diff_refs(self, client: GitLabClient) -> None:
        """Test review submission when diff_refs is not available."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        mock_mr.diff_refs = None

        submission = ReviewSubmission(summary="LGTM!")

        client.submit_review("owner/repo", 1, submission)

        # Should post summary only
        mock_mr.notes.create.assert_called_once_with({"body": "LGTM!"})
        mock_mr.discussions.create.assert_not_called()

    def test_submit_review_inline_comment_failure_demotes_to_summary(
        self, client: GitLabClient
    ) -> None:
        """Test that failed inline comments are demoted to summary."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        mock_mr.diff_refs = {
            "base_sha": "abc",
            "start_sha": "def",
            "head_sha": "ghi",
        }

        # First discussion fails, second succeeds
        mock_mr.discussions.create.side_effect = [
            GitlabError("Position not found"),
            None,
        ]

        submission = ReviewSubmission(
            summary="Review",
            line_comments=(
                LineComment(path="deleted.py", line=1, body="Comment 1"),
                LineComment(path="existing.py", line=1, body="Comment 2"),
            ),
        )

        # Should not raise, should continue
        client.submit_review("owner/repo", 1, submission)

        # Both should be attempted
        assert mock_mr.discussions.create.call_count == 2
        # Summary should include demoted comment
        mock_mr.notes.create.assert_called_once()
        posted_body = mock_mr.notes.create.call_args[0][0]["body"]
        assert "Review" in posted_body
        assert "**`deleted.py:1`**" in posted_body
        assert "Comment 1" in posted_body
        # Successful comment should NOT appear in summary
        assert "existing.py" not in posted_body

    def test_submit_review_all_inline_comments_fail(self, client: GitLabClient) -> None:
        """Test that all failed inline comments are demoted to summary."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        mock_mr.diff_refs = {
            "base_sha": "abc",
            "start_sha": "def",
            "head_sha": "ghi",
        }

        mock_mr.discussions.create.side_effect = GitlabError("Position not found")

        submission = ReviewSubmission(
            summary="Review",
            line_comments=(
                LineComment(path="a.py", line=10, body="Issue A"),
                LineComment(path="b.py", line=20, body="Issue B"),
            ),
        )

        client.submit_review("owner/repo", 1, submission)

        posted_body = mock_mr.notes.create.call_args[0][0]["body"]
        assert "**`a.py:10`**" in posted_body
        assert "Issue A" in posted_body
        assert "**`b.py:20`**" in posted_body
        assert "Issue B" in posted_body
        assert "could not be posted" in posted_body

    @patch("ai_reviewer.integrations.gitlab.with_retry", lambda f: f)  # Disable retry for test
    def test_rate_limit_raises_error(self, client: GitLabClient) -> None:
        """Test that rate limit (429) raises RateLimitError."""
        error = GitlabError("Too Many Requests")
        error.response_code = 429
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(RateLimitError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.gitlab.with_retry", lambda f: f)  # Disable retry for test
    def test_not_found_raises_error(self, client: GitLabClient) -> None:
        """Test that 404 raises NotFoundError."""
        error = GitlabError("Not Found")
        error.response_code = 404
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(NotFoundError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.gitlab.with_retry", lambda f: f)  # Disable retry for test
    def test_unauthorized_raises_error(self, client: GitLabClient) -> None:
        """Test that 401 raises AuthenticationError."""
        client.gitlab.projects.get.side_effect = GitlabAuthenticationError("Unauthorized")

        with pytest.raises(AuthenticationError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.gitlab.with_retry", lambda f: f)  # Disable retry for test
    def test_forbidden_raises_error(self, client: GitLabClient) -> None:
        """Test that 403 raises ForbiddenError."""
        error = GitlabError("Forbidden")
        error.response_code = 403
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(ForbiddenError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.gitlab.with_retry", lambda f: f)  # Disable retry for test
    def test_server_error_raises_error(self, client: GitLabClient) -> None:
        """Test that 5xx raises ServerError."""
        error = GitlabError("Internal Server Error")
        error.response_code = 500
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(ServerError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.gitlab.with_retry", lambda f: f)  # Disable retry for test
    def test_post_comment_rate_limit(self, client: GitLabClient) -> None:
        """Test rate limit handling in post_comment."""
        error = GitlabError("Too Many Requests")
        error.response_code = 429
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(RateLimitError):
            client.post_comment("owner/repo", 1, "Test")

    @patch("ai_reviewer.integrations.gitlab.with_retry", lambda f: f)  # Disable retry for test
    def test_submit_review_rate_limit(self, client: GitLabClient) -> None:
        """Test rate limit handling in submit_review."""
        error = GitlabError("Too Many Requests")
        error.response_code = 429
        client.gitlab.projects.get.side_effect = error

        submission = ReviewSubmission(summary="Test")

        with pytest.raises(RateLimitError):
            client.submit_review("owner/repo", 1, submission)


class TestExtractGitLabContext:
    """Tests for extract_gitlab_context function."""

    def test_extract_from_env(self) -> None:
        """Test extracting context from GitLab CI environment."""
        import os
        from unittest.mock import patch

        from ai_reviewer.cli import extract_gitlab_context

        env = {
            "CI_PROJECT_PATH": "owner/repo",
            "CI_MERGE_REQUEST_IID": "42",
        }
        with patch.dict(os.environ, env, clear=True):
            project, mr_iid = extract_gitlab_context()
            assert project == "owner/repo"
            assert mr_iid == 42

    def test_missing_project_raises_error(self) -> None:
        """Test that missing CI_PROJECT_PATH raises ValueError."""
        import os
        from unittest.mock import patch

        from ai_reviewer.cli import extract_gitlab_context

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="CI_PROJECT_PATH"):
                extract_gitlab_context()

    def test_missing_mr_iid_raises_error(self) -> None:
        """Test that missing CI_MERGE_REQUEST_IID raises ValueError."""
        import os
        from unittest.mock import patch

        from ai_reviewer.cli import extract_gitlab_context

        env = {"CI_PROJECT_PATH": "owner/repo"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="MR number"):
                extract_gitlab_context()
