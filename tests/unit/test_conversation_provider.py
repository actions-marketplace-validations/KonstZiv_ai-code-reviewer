"""Unit tests for ConversationProvider ABC, models, and implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from github import RateLimitExceededException
from pydantic import ValidationError

from ai_reviewer.integrations.conversation import (
    BOT_QUESTION_MARKER,
    BotQuestion,
    BotThread,
    ConversationProvider,
    QuestionContext,
    ThreadStatus,
    format_questions_markdown,
    parse_questions_from_markdown,
)
from ai_reviewer.integrations.github import GitHubClient
from ai_reviewer.integrations.gitlab import GitLabClient
from ai_reviewer.utils.retry import RateLimitError

if TYPE_CHECKING:
    from unittest.mock import MagicMock


# ── Model tests ────────────────────────────────────────────────────


class TestBotQuestion:
    """Tests for the BotQuestion model."""

    def test_create_minimal(self) -> None:
        """Test creating with required fields only."""
        q = BotQuestion(question_id="Q1", text="How?", default_assumption="pytest")
        assert q.question_id == "Q1"
        assert q.text == "How?"
        assert q.default_assumption == "pytest"
        assert q.context == QuestionContext.DISCOVERY
        assert q.asked_at is None

    def test_frozen(self) -> None:
        """Test that BotQuestion is immutable."""
        q = BotQuestion(question_id="Q1", text="How?", default_assumption="pytest")
        with pytest.raises(ValidationError):
            q.text = "What?"  # type: ignore[misc]

    def test_empty_question_id_rejected(self) -> None:
        """Test that empty question_id is rejected."""
        with pytest.raises(ValidationError):
            BotQuestion(question_id="", text="How?", default_assumption="x")

    def test_empty_text_rejected(self) -> None:
        """Test that empty text is rejected."""
        with pytest.raises(ValidationError):
            BotQuestion(question_id="Q1", text="", default_assumption="x")


class TestBotThread:
    """Tests for the BotThread model."""

    def test_create_minimal(self) -> None:
        """Test creating with required fields only."""
        t = BotThread(thread_id="t1", platform_thread_id="p1", mr_id=1)
        assert t.thread_id == "t1"
        assert t.questions == ()
        assert t.responses == ()
        assert t.status == ThreadStatus.PENDING

    def test_frozen(self) -> None:
        """Test that BotThread is immutable."""
        t = BotThread(thread_id="t1", platform_thread_id="p1", mr_id=1)
        with pytest.raises(ValidationError):
            t.status = ThreadStatus.ANSWERED  # type: ignore[misc]

    def test_invalid_mr_id_rejected(self) -> None:
        """Test that mr_id < 1 is rejected."""
        with pytest.raises(ValidationError):
            BotThread(thread_id="t1", platform_thread_id="p1", mr_id=0)


class TestThreadStatus:
    """Tests for ThreadStatus enum."""

    def test_values(self) -> None:
        """Test all enum values exist."""
        assert ThreadStatus.PENDING == "pending"
        assert ThreadStatus.ANSWERED == "answered"
        assert ThreadStatus.EXPIRED == "expired"
        assert ThreadStatus.RESOLVED == "resolved"


class TestQuestionContext:
    """Tests for QuestionContext enum."""

    def test_values(self) -> None:
        """Test all enum values exist."""
        assert QuestionContext.DISCOVERY == "discovery"
        assert QuestionContext.REVIEW == "review"
        assert QuestionContext.FOLLOW_UP == "follow_up"


# ── Markdown format/parse tests ────────────────────────────────────


class TestFormatQuestions:
    """Tests for format_questions_markdown."""

    def test_basic_formatting(self) -> None:
        """Test basic question formatting."""
        questions = [
            BotQuestion(
                question_id="Q1", text="How do you run tests?", default_assumption="pytest"
            ),
            BotQuestion(question_id="Q2", text="CI system?", default_assumption="GitHub Actions"),
        ]
        result = format_questions_markdown(questions)

        assert BOT_QUESTION_MARKER in result
        assert "**Q1:** How do you run tests?" in result
        assert "> *Default: pytest*" in result
        assert "**Q2:** CI system?" in result
        assert "> *Default: GitHub Actions*" in result

    def test_with_intro(self) -> None:
        """Test formatting with intro text."""
        questions = [
            BotQuestion(question_id="Q1", text="Test?", default_assumption="yes"),
        ]
        result = format_questions_markdown(questions, intro="Hello!")

        assert "Hello!" in result
        assert BOT_QUESTION_MARKER in result

    def test_empty_questions(self) -> None:
        """Test formatting with no questions."""
        result = format_questions_markdown([])
        assert BOT_QUESTION_MARKER in result


class TestParseQuestions:
    """Tests for parse_questions_from_markdown."""

    def test_roundtrip(self) -> None:
        """Test format -> parse roundtrip preserves questions."""
        original = [
            BotQuestion(question_id="Q1", text="How?", default_assumption="pytest"),
            BotQuestion(question_id="Q2", text="What CI?", default_assumption="Actions"),
        ]
        markdown = format_questions_markdown(original)
        parsed = parse_questions_from_markdown(markdown)

        assert len(parsed) == 2
        assert parsed[0].question_id == "Q1"
        assert parsed[0].text == "How?"
        assert parsed[0].default_assumption == "pytest"
        assert parsed[1].question_id == "Q2"

    def test_no_questions_in_body(self) -> None:
        """Test parsing a body with no questions."""
        result = parse_questions_from_markdown("Just a normal comment")
        assert result == []

    def test_partial_match_ignored(self) -> None:
        """Test that malformed questions are ignored."""
        result = parse_questions_from_markdown("**Q1:** text without default")
        assert result == []


# ── ConversationProvider ABC tests ─────────────────────────────────


class TestConversationProviderABC:
    """Tests for the ConversationProvider abstract base class."""

    def test_cannot_instantiate(self) -> None:
        """Test that ConversationProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            ConversationProvider()  # type: ignore[abstract]

    def test_incomplete_subclass(self) -> None:
        """Test that a subclass missing methods cannot be instantiated."""

        class _Incomplete(ConversationProvider):
            def post_question_comment(self, *args, **kwargs) -> str:  # type: ignore[override]  # noqa: ANN002, ANN003
                return ""

        with pytest.raises(TypeError, match="abstract"):
            _Incomplete()  # type: ignore[abstract]

    def test_github_implements_interface(self) -> None:
        """Test that GitHubClient implements ConversationProvider."""
        with patch("ai_reviewer.integrations.github.Github"):
            client = GitHubClient("token")
        assert isinstance(client, ConversationProvider)

    def test_gitlab_implements_interface(self) -> None:
        """Test that GitLabClient implements ConversationProvider."""
        with patch("ai_reviewer.integrations.gitlab.gitlab.Gitlab"):
            client = GitLabClient("token")
        assert isinstance(client, ConversationProvider)


# ── GitHub ConversationProvider tests ──────────────────────────────


class TestGitHubConversationProvider:
    """Tests for GitHubClient ConversationProvider methods."""

    @pytest.fixture
    def mock_github(self) -> MagicMock:
        """Mock PyGithub instance."""
        with patch("ai_reviewer.integrations.github.Github") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_github: MagicMock) -> GitHubClient:
        """Create GitHubClient instance with mocked Github."""
        return GitHubClient("test-token")

    # ── post_question_comment ─────────────────────────────────────

    def test_post_question_comment(self, client: GitHubClient) -> None:
        """Test posting a question comment."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.id = 42
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.create_issue_comment.return_value = mock_comment

        questions = [
            BotQuestion(question_id="Q1", text="Test?", default_assumption="yes"),
        ]
        result = client.post_question_comment("owner/repo", 1, questions)

        assert result == "42"
        call_body = mock_pr.create_issue_comment.call_args[0][0]
        assert BOT_QUESTION_MARKER in call_body
        assert "**Q1:** Test?" in call_body

    def test_post_question_comment_with_intro(self, client: GitHubClient) -> None:
        """Test posting with intro text."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.id = 1
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.create_issue_comment.return_value = mock_comment

        questions = [
            BotQuestion(question_id="Q1", text="CI?", default_assumption="Actions"),
        ]
        client.post_question_comment("owner/repo", 1, questions, intro="Hello!")

        call_body = mock_pr.create_issue_comment.call_args[0][0]
        assert "Hello!" in call_body

    def test_post_question_comment_rate_limit(self, client: GitHubClient) -> None:
        """Test rate limit raises RateLimitError."""
        client.github.get_repo.side_effect = RateLimitExceededException(
            403, {"message": "rate limit"}, {}
        )

        with pytest.raises(RateLimitError):
            client.post_question_comment("o/r", 1, [])

    # ── reply_in_thread ───────────────────────────────────────────

    def test_reply_in_thread(self, client: GitHubClient) -> None:
        """Test replying in a thread."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.id = 99
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.create_issue_comment.return_value = mock_comment

        result = client.reply_in_thread("owner/repo", 1, "42", "Thanks!")

        assert result == "99"
        mock_pr.create_issue_comment.assert_called_once_with("Thanks!")

    # ── get_bot_threads ───────────────────────────────────────────

    def test_get_bot_threads_finds_questions(self, client: GitHubClient) -> None:
        """Test finding bot question threads with responses."""
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        # Bot question comment
        from datetime import UTC, datetime

        bot_comment = Mock()
        bot_comment.id = 100
        bot_comment.body = format_questions_markdown(
            [BotQuestion(question_id="Q1", text="How?", default_assumption="pytest")]
        )
        bot_comment.user.login = "ai-bot"
        bot_comment.user.type = "Bot"
        bot_comment.created_at = datetime(2024, 1, 1, tzinfo=UTC)

        # Human response
        human_comment = Mock()
        human_comment.id = 101
        human_comment.body = "We use pytest"
        human_comment.user.login = "dev"
        human_comment.user.type = "User"
        human_comment.created_at = datetime(2024, 1, 2, tzinfo=UTC)

        mock_pr.get_issue_comments.return_value = [bot_comment, human_comment]

        threads = client.get_bot_threads("owner/repo", 1)

        assert len(threads) == 1
        assert threads[0].thread_id == "100"
        assert len(threads[0].questions) == 1
        assert threads[0].questions[0].question_id == "Q1"
        assert len(threads[0].responses) == 1
        assert threads[0].responses[0].body == "We use pytest"
        assert threads[0].status == ThreadStatus.ANSWERED

    def test_get_bot_threads_no_responses(self, client: GitHubClient) -> None:
        """Test bot thread with no responses stays PENDING."""
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        from datetime import UTC, datetime

        bot_comment = Mock()
        bot_comment.id = 100
        bot_comment.body = format_questions_markdown(
            [BotQuestion(question_id="Q1", text="CI?", default_assumption="Actions")]
        )
        bot_comment.user.login = "ai-bot"
        bot_comment.created_at = datetime(2024, 1, 1, tzinfo=UTC)

        mock_pr.get_issue_comments.return_value = [bot_comment]

        threads = client.get_bot_threads("owner/repo", 1)

        assert len(threads) == 1
        assert threads[0].status == ThreadStatus.PENDING

    def test_get_bot_threads_empty(self, client: GitHubClient) -> None:
        """Test no bot threads found."""
        mock_repo = Mock()
        mock_pr = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_issue_comments.return_value = []

        threads = client.get_bot_threads("owner/repo", 1)

        assert threads == ()


# ── GitLab ConversationProvider tests ──────────────────────────────


class TestGitLabConversationProvider:
    """Tests for GitLabClient ConversationProvider methods."""

    @pytest.fixture
    def mock_gitlab(self) -> MagicMock:
        """Mock python-gitlab instance."""
        with patch("ai_reviewer.integrations.gitlab.gitlab.Gitlab") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_gitlab: MagicMock) -> GitLabClient:
        """Create GitLabClient instance with mocked Gitlab."""
        return GitLabClient("test-token", "https://gitlab.example.com")

    # ── post_question_comment ─────────────────────────────────────

    def test_post_question_comment(self, client: GitLabClient) -> None:
        """Test posting a question as a discussion."""
        mock_project = Mock()
        mock_mr = Mock()
        mock_discussion = Mock()
        mock_discussion.id = "abc123"
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.discussions.create.return_value = mock_discussion

        questions = [
            BotQuestion(question_id="Q1", text="Test?", default_assumption="yes"),
        ]
        result = client.post_question_comment("group/repo", 1, questions)

        assert result == "abc123"
        call_body = mock_mr.discussions.create.call_args[0][0]["body"]
        assert BOT_QUESTION_MARKER in call_body

    # ── reply_in_thread ───────────────────────────────────────────

    def test_reply_in_thread(self, client: GitLabClient) -> None:
        """Test replying in a GitLab discussion."""
        mock_project = Mock()
        mock_mr = Mock()
        mock_discussion = Mock()
        mock_note = {"id": 456}
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.discussions.get.return_value = mock_discussion
        mock_discussion.notes.create.return_value = mock_note

        result = client.reply_in_thread("group/repo", 1, "abc123", "Got it")

        assert result == "456"
        mock_discussion.notes.create.assert_called_once_with({"body": "Got it"})

    # ── get_bot_threads ───────────────────────────────────────────

    def test_get_bot_threads_finds_questions(self, client: GitLabClient) -> None:
        """Test finding bot question threads with responses."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        question_body = format_questions_markdown(
            [BotQuestion(question_id="Q1", text="How?", default_assumption="pytest")]
        )

        discussion = Mock()
        discussion.id = "disc1"
        discussion.attributes = {
            "notes": [
                {
                    "id": 1,
                    "body": question_body,
                    "system": False,
                    "author": {"username": "ai-bot", "bot": True},
                    "created_at": "2024-01-01T00:00:00Z",
                },
                {
                    "id": 2,
                    "body": "We use pytest",
                    "system": False,
                    "author": {"username": "dev", "bot": False},
                    "created_at": "2024-01-02T00:00:00Z",
                },
            ],
            "resolved": False,
        }

        mock_mr.discussions.list.return_value = [discussion]

        threads = client.get_bot_threads("group/repo", 1)

        assert len(threads) == 1
        assert threads[0].thread_id == "disc1"
        assert len(threads[0].questions) == 1
        assert threads[0].questions[0].question_id == "Q1"
        assert len(threads[0].responses) == 1
        assert threads[0].responses[0].body == "We use pytest"
        assert threads[0].status == ThreadStatus.ANSWERED

    def test_get_bot_threads_resolved(self, client: GitLabClient) -> None:
        """Test that GitLab resolved status is detected."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        question_body = format_questions_markdown(
            [BotQuestion(question_id="Q1", text="CI?", default_assumption="Actions")]
        )

        discussion = Mock()
        discussion.id = "disc2"
        discussion.attributes = {
            "notes": [
                {
                    "id": 1,
                    "body": question_body,
                    "system": False,
                    "author": {"username": "bot"},
                },
                {
                    "id": 2,
                    "body": "Done",
                    "system": False,
                    "author": {"username": "dev"},
                    "created_at": "2024-01-02T00:00:00Z",
                },
            ],
            "resolved": True,
        }

        mock_mr.discussions.list.return_value = [discussion]

        threads = client.get_bot_threads("group/repo", 1)

        assert len(threads) == 1
        assert threads[0].status == ThreadStatus.RESOLVED

    def test_get_bot_threads_skips_system_notes(self, client: GitLabClient) -> None:
        """Test that system notes are not counted as responses."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        question_body = format_questions_markdown(
            [BotQuestion(question_id="Q1", text="Test?", default_assumption="yes")]
        )

        discussion = Mock()
        discussion.id = "disc3"
        discussion.attributes = {
            "notes": [
                {
                    "id": 1,
                    "body": question_body,
                    "system": False,
                    "author": {"username": "bot"},
                },
                {
                    "id": 2,
                    "body": "resolved merge conflict",
                    "system": True,
                    "author": {"username": "system"},
                },
            ],
            "resolved": False,
        }

        mock_mr.discussions.list.return_value = [discussion]

        threads = client.get_bot_threads("group/repo", 1)

        assert len(threads) == 1
        assert threads[0].status == ThreadStatus.PENDING
        assert len(threads[0].responses) == 0

    def test_get_bot_threads_empty(self, client: GitLabClient) -> None:
        """Test no bot threads found."""
        mock_project = Mock()
        mock_mr = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr
        mock_mr.discussions.list.return_value = []

        threads = client.get_bot_threads("group/repo", 1)

        assert threads == ()
