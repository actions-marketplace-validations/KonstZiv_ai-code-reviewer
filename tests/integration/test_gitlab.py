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

        # Mock Notes
        mock_note = Mock()
        mock_note.system = False
        mock_note.author = {"username": "user1", "bot": False}
        mock_note.body = "LGTM"
        mock_note.position = None
        mock_note.created_at = "2024-01-01T00:00:00Z"
        mock_mr.notes.list.return_value = [mock_note]

        # Mock Diffs
        mock_diff = Mock()
        mock_diff.id = 1
        mock_mr.diffs.list.return_value = [mock_diff]

        mock_diff_detail = Mock()
        mock_diff_detail.diffs = [
            {
                "new_file": False,
                "deleted_file": False,
                "renamed_file": False,
                "new_path": "test.py",
                "old_path": "test.py",
                "diff": "@@ -1,1 +1,2 @@\n-old\n+new\n+added",
            }
        ]
        mock_mr.diffs.get.return_value = mock_diff_detail

        # Execute
        mr = client.get_merge_request("owner/repo", 1)

        # Verify
        assert isinstance(mr, MergeRequest)
        assert mr.number == 1
        assert mr.title == "Test MR"
        assert len(mr.comments) == 1
        assert mr.comments[0].type == CommentType.ISSUE
        assert mr.comments[0].author_type == CommentAuthorType.USER
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
        mock_mr.diffs.list.return_value = []

        # Mock bot note
        mock_note = Mock()
        mock_note.system = False
        mock_note.author = {"username": "review-bot", "bot": True}
        mock_note.body = "Auto review"
        mock_note.position = {"new_line": 10}  # Inline comment
        mock_note.created_at = "2024-01-01T00:00:00Z"
        mock_mr.notes.list.return_value = [mock_note]

        mr = client.get_merge_request("owner/repo", 1)

        assert len(mr.comments) == 1
        assert mr.comments[0].author_type == CommentAuthorType.BOT
        assert mr.comments[0].type == CommentType.REVIEW

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
        mock_mr.diffs.list.return_value = []

        # Mock system note
        mock_note = Mock()
        mock_note.system = True  # System note - should be skipped
        mock_note.author = {"username": "gitlab"}
        mock_note.body = "merged"
        mock_mr.notes.list.return_value = [mock_note]

        mr = client.get_merge_request("owner/repo", 1)

        assert len(mr.comments) == 0

    def test_get_linked_task_found(self, client: GitLabClient) -> None:
        """Test finding linked issue."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project

        # Mock Issue
        mock_issue = Mock()
        mock_issue.iid = 123
        mock_issue.title = "Task Title"
        mock_issue.description = "Task Body"
        mock_issue.web_url = "https://gitlab.com/issue/123"
        mock_project.issues.get.return_value = mock_issue

        # Mock MR
        mr = MagicMock(spec=MergeRequest)
        mr.description = "Closes #123"

        task = client.get_linked_task("owner/repo", mr)

        assert task is not None
        assert task.identifier == "123"
        assert task.title == "Task Title"
        mock_project.issues.get.assert_called_once_with(123)

    def test_get_linked_task_not_found(self, client: GitLabClient) -> None:
        """Test when no linked issue is found."""
        mr = MagicMock(spec=MergeRequest)
        mr.description = "No issue link here"

        task = client.get_linked_task("owner/repo", mr)

        assert task is None

    def test_get_linked_task_fixes_pattern(self, client: GitLabClient) -> None:
        """Test finding linked issue with 'Fixes' pattern."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project

        mock_issue = Mock()
        mock_issue.iid = 456
        mock_issue.title = "Bug"
        mock_issue.description = ""
        mock_issue.web_url = "url"
        mock_project.issues.get.return_value = mock_issue

        mr = MagicMock(spec=MergeRequest)
        mr.description = "Fixes #456"

        task = client.get_linked_task("owner/repo", mr)

        assert task is not None
        assert task.identifier == "456"

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

    def test_submit_review_inline_comment_failure_continues(self, client: GitLabClient) -> None:
        """Test that inline comment failures don't stop the review."""
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
        # Summary should still be posted
        mock_mr.notes.create.assert_called_once()

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
