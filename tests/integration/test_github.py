"""Integration tests for GitHub client."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from github import GithubException, RateLimitExceededException

from ai_reviewer.core.models import (
    CommentAuthorType,
    CommentType,
    FileChangeType,
    MergeRequest,
)
from ai_reviewer.integrations.github import GitHubClient


class TestGitHubClient:
    """Tests for GitHubClient."""

    @pytest.fixture
    def mock_github(self) -> MagicMock:
        """Mock PyGithub instance."""
        with patch("ai_reviewer.integrations.github.Github") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_github: MagicMock) -> GitHubClient:
        """Create GitHubClient instance with mocked Github."""
        return GitHubClient("test-token")

    def test_init(self, mock_github: MagicMock) -> None:
        """Test client initialization."""
        GitHubClient("test-token")
        mock_github.assert_called_once()

    def test_get_pull_request_success(self, client: GitHubClient) -> None:
        """Test successful PR fetching with comments and files."""
        # Mock Repo and PR
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        # Setup PR data
        mock_pr.number = 1
        mock_pr.title = "Test PR"
        mock_pr.body = "Description"
        mock_pr.user.login = "author"
        mock_pr.head.ref = "feature"
        mock_pr.base.ref = "main"
        mock_pr.html_url = "http://github.com/owner/repo/pull/1"
        mock_pr.created_at = datetime.now(UTC)
        mock_pr.updated_at = datetime.now(UTC)

        # Mock Issue Comments
        mock_issue_comment = Mock()
        mock_issue_comment.user.login = "user1"
        mock_issue_comment.user.type = "User"
        mock_issue_comment.body = "LGTM"
        mock_issue_comment.created_at = datetime.now(UTC)
        mock_pr.get_issue_comments.return_value = [mock_issue_comment]

        # Mock Review Comments
        mock_review_comment = Mock()
        mock_review_comment.user.login = "bot"
        mock_review_comment.user.type = "Bot"
        mock_review_comment.body = "Fix this"
        mock_review_comment.created_at = datetime.now(UTC)
        mock_pr.get_review_comments.return_value = [mock_review_comment]

        # Mock Files
        mock_file = Mock()
        mock_file.filename = "test.py"
        mock_file.status = "modified"
        mock_file.additions = 10
        mock_file.deletions = 5
        mock_file.patch = "diff"
        mock_file.previous_filename = None
        mock_pr.get_files.return_value = [mock_file]

        # Execute
        mr = client.get_pull_request("owner/repo", 1)

        # Verify
        assert isinstance(mr, MergeRequest)
        assert mr.number == 1
        assert len(mr.comments) == 2
        assert mr.comments[0].type == CommentType.ISSUE
        assert mr.comments[0].author_type == CommentAuthorType.USER
        assert mr.comments[1].type == CommentType.REVIEW
        assert mr.comments[1].author_type == CommentAuthorType.BOT
        assert len(mr.changes) == 1
        assert mr.changes[0].filename == "test.py"
        assert mr.changes[0].change_type == FileChangeType.MODIFIED

    def test_get_pull_request_binary_file(self, client: GitHubClient) -> None:
        """Test fetching PR with binary file (no patch)."""
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        # Setup minimal PR data
        mock_pr.number = 1
        mock_pr.title = "Test"
        mock_pr.body = ""
        mock_pr.user.login = "author"
        mock_pr.head.ref = "head"
        mock_pr.base.ref = "base"
        mock_pr.html_url = "url"
        mock_pr.created_at = datetime.now(UTC)
        mock_pr.updated_at = datetime.now(UTC)
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []

        # Mock Binary File
        mock_file = Mock()
        mock_file.filename = "image.png"
        mock_file.status = "added"
        mock_file.additions = 0
        mock_file.deletions = 0
        mock_file.patch = None  # Binary file
        mock_file.previous_filename = None
        mock_pr.get_files.return_value = [mock_file]

        mr = client.get_pull_request("owner/repo", 1)

        assert len(mr.changes) == 1
        assert mr.changes[0].patch is None

    def test_get_linked_task_found(self, client: GitHubClient) -> None:
        """Test finding linked task."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo

        # Mock Issue
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Task Title"
        mock_issue.body = "Task Body"
        mock_issue.html_url = "http://issue/123"
        mock_repo.get_issue.return_value = mock_issue

        # Mock MR
        mr = MagicMock(spec=MergeRequest)
        mr.description = "Fixes #123"

        task = client.get_linked_task("owner/repo", mr)

        assert task is not None
        assert task.identifier == "123"
        assert task.title == "Task Title"
        mock_repo.get_issue.assert_called_once_with(123)

    def test_get_linked_task_not_found(self, client: GitHubClient) -> None:
        """Test when no linked task is found."""
        mr = MagicMock(spec=MergeRequest)
        mr.description = "No task link here"

        task = client.get_linked_task("owner/repo", mr)

        assert task is None

    def test_post_review_comment_success(self, client: GitHubClient) -> None:
        """Test successful comment posting."""
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        client.post_review_comment("owner/repo", 1, "Test comment")

        mock_pr.create_issue_comment.assert_called_once_with("Test comment")

    def test_rate_limit_handling(self, client: GitHubClient) -> None:
        """Test that RateLimitExceededException is handled."""
        client.github.get_repo.side_effect = RateLimitExceededException(403, "Rate limit", {})

        # Should return None instead of raising exception
        result = client.get_pull_request("owner/repo", 1)
        assert result is None

    def test_rate_limit_403_handling(self, client: GitHubClient) -> None:
        """Test that 403 with 'rate limit' text is handled."""
        client.github.get_repo.side_effect = GithubException(403, "API rate limit exceeded", {})

        result = client.get_pull_request("owner/repo", 1)
        assert result is None

    def test_other_github_exception_raised(self, client: GitHubClient) -> None:
        """Test that other GitHub exceptions are re-raised."""
        client.github.get_repo.side_effect = GithubException(404, "Not Found", {})

        with pytest.raises(GithubException):
            client.get_pull_request("owner/repo", 1)
