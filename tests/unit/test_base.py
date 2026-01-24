"""Unit tests for base abstractions."""

import pytest

from ai_reviewer.integrations.base import (
    GitProvider,
    LineComment,
    ReviewSubmission,
)


class TestLineComment:
    """Tests for LineComment dataclass."""

    def test_create_simple_comment(self) -> None:
        """Test creating a simple line comment."""
        comment = LineComment(path="src/main.py", line=10, body="Fix this")

        assert comment.path == "src/main.py"
        assert comment.line == 10
        assert comment.body == "Fix this"
        assert comment.suggestion is None
        assert comment.side == "RIGHT"

    def test_create_comment_with_suggestion(self) -> None:
        """Test creating a comment with suggestion."""
        comment = LineComment(
            path="src/main.py",
            line=10,
            body="Consider using f-string",
            suggestion='print(f"Hello {name}")',
        )

        assert comment.suggestion == 'print(f"Hello {name}")'

    def test_create_comment_with_left_side(self) -> None:
        """Test creating a comment on deleted line (LEFT side)."""
        comment = LineComment(
            path="src/main.py",
            line=5,
            body="This was wrong",
            side="LEFT",
        )

        assert comment.side == "LEFT"

    def test_line_must_be_positive(self) -> None:
        """Test that line number must be positive."""
        with pytest.raises(ValueError, match="Line number must be positive"):
            LineComment(path="src/main.py", line=0, body="Test")

    def test_line_negative_raises(self) -> None:
        """Test that negative line number raises error."""
        with pytest.raises(ValueError, match="Line number must be positive"):
            LineComment(path="src/main.py", line=-1, body="Test")

    def test_path_cannot_be_empty(self) -> None:
        """Test that path cannot be empty."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            LineComment(path="", line=1, body="Test")

    def test_format_body_without_suggestion(self) -> None:
        """Test formatting body when no suggestion present."""
        comment = LineComment(path="src/main.py", line=10, body="Fix this")

        assert comment.format_body_with_suggestion() == "Fix this"

    def test_format_body_with_suggestion(self) -> None:
        """Test formatting body with GitHub suggestion block."""
        comment = LineComment(
            path="src/main.py",
            line=10,
            body="Use f-string instead",
            suggestion='print(f"Hello {name}")',
        )

        expected = 'Use f-string instead\n\n```suggestion\nprint(f"Hello {name}")\n```'
        assert comment.format_body_with_suggestion() == expected

    def test_format_body_multiline_suggestion(self) -> None:
        """Test formatting body with multiline suggestion."""
        comment = LineComment(
            path="src/main.py",
            line=10,
            body="Refactor this",
            suggestion="def foo():\n    return 42",
        )

        result = comment.format_body_with_suggestion()
        assert "```suggestion\ndef foo():\n    return 42\n```" in result

    def test_immutability(self) -> None:
        """Test that LineComment is immutable (frozen)."""
        comment = LineComment(path="src/main.py", line=10, body="Test")

        with pytest.raises(AttributeError):
            comment.line = 20  # type: ignore[misc]


class TestReviewSubmission:
    """Tests for ReviewSubmission dataclass."""

    def test_create_simple_submission(self) -> None:
        """Test creating a review with just summary."""
        submission = ReviewSubmission(summary="LGTM!")

        assert submission.summary == "LGTM!"
        assert submission.line_comments == ()
        assert submission.event == "COMMENT"

    def test_create_submission_with_comments(self) -> None:
        """Test creating a review with inline comments."""
        comments = (
            LineComment(path="src/a.py", line=1, body="Fix"),
            LineComment(path="src/b.py", line=2, body="Update"),
        )

        submission = ReviewSubmission(
            summary="Please address comments",
            line_comments=comments,
            event="REQUEST_CHANGES",
        )

        assert len(submission.line_comments) == 2
        assert submission.event == "REQUEST_CHANGES"

    def test_create_approval(self) -> None:
        """Test creating an approval review."""
        submission = ReviewSubmission(summary="Looks good!", event="APPROVE")

        assert submission.event == "APPROVE"

    def test_immutability(self) -> None:
        """Test that ReviewSubmission is immutable (frozen)."""
        submission = ReviewSubmission(summary="Test")

        with pytest.raises(AttributeError):
            submission.summary = "Changed"  # type: ignore[misc]


class TestGitProvider:
    """Tests for GitProvider ABC."""

    def test_cannot_instantiate_abstract(self) -> None:
        """Test that GitProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            GitProvider()  # type: ignore[abstract]

    def test_must_implement_all_methods(self) -> None:
        """Test that subclass must implement all abstract methods."""

        class IncompleteProvider(GitProvider):
            pass

        with pytest.raises(TypeError, match="abstract"):
            IncompleteProvider()  # type: ignore[abstract]

    def test_concrete_subclass_works(self) -> None:
        """Test that a complete implementation can be instantiated."""
        from ai_reviewer.core.models import LinkedTask, MergeRequest

        class MockProvider(GitProvider):
            def get_merge_request(self, repo_name: str, mr_id: int) -> MergeRequest | None:
                return None

            def get_linked_task(self, repo_name: str, mr: MergeRequest) -> LinkedTask | None:
                return None

            def post_comment(self, repo_name: str, mr_id: int, body: str) -> None:
                pass

            def submit_review(
                self, repo_name: str, mr_id: int, submission: ReviewSubmission
            ) -> None:
                pass

        provider = MockProvider()
        assert isinstance(provider, GitProvider)
