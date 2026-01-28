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
from ai_reviewer.integrations.base import GitProvider, LineComment, ReviewSubmission
from ai_reviewer.integrations.github import GitHubClient
from ai_reviewer.utils.retry import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
)


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

    def test_implements_git_provider(self, client: GitHubClient) -> None:
        """Test that GitHubClient implements GitProvider interface."""
        assert isinstance(client, GitProvider)

    def test_get_merge_request_success(self, client: GitHubClient) -> None:
        """Test successful MR fetching with comments and files."""
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
        mr = client.get_merge_request("owner/repo", 1)

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

    def test_get_merge_request_binary_file(self, client: GitHubClient) -> None:
        """Test fetching MR with binary file (no patch)."""
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

        mr = client.get_merge_request("owner/repo", 1)

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

    def test_post_comment_success(self, client: GitHubClient) -> None:
        """Test successful comment posting."""
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        client.post_comment("owner/repo", 1, "Test comment")

        mock_pr.create_issue_comment.assert_called_once_with("Test comment")

    def test_post_review_comment_backward_compat(self, client: GitHubClient) -> None:
        """Test backward compatibility alias for post_review_comment."""
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        # Use deprecated alias
        client.post_review_comment("owner/repo", 1, "Test comment")

        mock_pr.create_issue_comment.assert_called_once_with("Test comment")

    def test_submit_review_success(self, client: GitHubClient) -> None:
        """Test successful review submission with inline comments."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_commit = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit

        mock_pr.head.sha = "abc123"

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
            event="REQUEST_CHANGES",
        )

        client.submit_review("owner/repo", 1, submission)

        # Verify create_review was called
        mock_pr.create_review.assert_called_once()
        call_kwargs = mock_pr.create_review.call_args[1]

        assert call_kwargs["commit"] == mock_commit
        assert call_kwargs["body"] == "Please fix these issues"
        assert call_kwargs["event"] == "REQUEST_CHANGES"
        assert len(call_kwargs["comments"]) == 2

        # Verify comment formatting
        assert call_kwargs["comments"][0]["path"] == "src/main.py"
        assert call_kwargs["comments"][0]["line"] == 10
        assert call_kwargs["comments"][0]["body"] == "Fix this"
        assert call_kwargs["comments"][0]["side"] == "RIGHT"

        # Verify suggestion formatting
        assert "```suggestion" in call_kwargs["comments"][1]["body"]

    def test_submit_review_no_comments(self, client: GitHubClient) -> None:
        """Test review submission without inline comments."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_commit = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit

        mock_pr.head.sha = "abc123"

        submission = ReviewSubmission(summary="LGTM!", event="APPROVE")

        client.submit_review("owner/repo", 1, submission)

        call_kwargs = mock_pr.create_review.call_args[1]
        assert call_kwargs["comments"] is None

    @patch("ai_reviewer.integrations.github.with_retry", lambda f: f)  # Disable retry for test
    def test_rate_limit_raises_error(self, client: GitHubClient) -> None:
        """Test that RateLimitExceededException raises RateLimitError."""
        client.github.get_repo.side_effect = RateLimitExceededException(403, "Rate limit", {})

        # Now raises RateLimitError instead of returning None
        with pytest.raises(RateLimitError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.github.with_retry", lambda f: f)  # Disable retry for test
    def test_rate_limit_403_raises_error(self, client: GitHubClient) -> None:
        """Test that 403 with 'rate limit' text raises RateLimitError."""
        client.github.get_repo.side_effect = GithubException(403, "API rate limit exceeded", {})

        with pytest.raises(RateLimitError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.github.with_retry", lambda f: f)  # Disable retry for test
    def test_not_found_raises_error(self, client: GitHubClient) -> None:
        """Test that 404 raises NotFoundError."""
        client.github.get_repo.side_effect = GithubException(404, "Not Found", {})

        with pytest.raises(NotFoundError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.github.with_retry", lambda f: f)  # Disable retry for test
    def test_unauthorized_raises_error(self, client: GitHubClient) -> None:
        """Test that 401 raises AuthenticationError."""
        client.github.get_repo.side_effect = GithubException(401, "Unauthorized", {})

        with pytest.raises(AuthenticationError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.github.with_retry", lambda f: f)  # Disable retry for test
    def test_forbidden_raises_error(self, client: GitHubClient) -> None:
        """Test that 403 (non-rate-limit) raises ForbiddenError."""
        client.github.get_repo.side_effect = GithubException(403, "Permission denied", {})

        with pytest.raises(ForbiddenError):
            client.get_merge_request("owner/repo", 1)

    @patch("ai_reviewer.integrations.github.with_retry", lambda f: f)  # Disable retry for test
    def test_submit_review_rate_limit(self, client: GitHubClient) -> None:
        """Test rate limit handling in submit_review."""
        client.github.get_repo.side_effect = RateLimitExceededException(403, "Rate limit", {})

        submission = ReviewSubmission(summary="Test")

        with pytest.raises(RateLimitError):
            client.submit_review("owner/repo", 1, submission)

    @patch("ai_reviewer.integrations.github.with_retry", lambda f: f)  # Disable retry for test
    def test_post_comment_rate_limit(self, client: GitHubClient) -> None:
        """Test rate limit handling in post_comment."""
        client.github.get_repo.side_effect = RateLimitExceededException(403, "Rate limit", {})

        with pytest.raises(RateLimitError):
            client.post_comment("owner/repo", 1, "Test")
