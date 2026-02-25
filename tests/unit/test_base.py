"""Unit tests for base abstractions."""

import pytest

from ai_reviewer.integrations.base import (
    GitProvider,
    LineComment,
    ReviewSubmission,
    parse_branch_issue_number,
    parse_diff_valid_lines,
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

            def get_linked_tasks(
                self, repo_name: str, mr_id: int, source_branch: str
            ) -> tuple[LinkedTask, ...]:
                return ()

            def post_comment(self, repo_name: str, mr_id: int, body: str) -> None:
                pass

            def submit_review(
                self, repo_name: str, mr_id: int, submission: ReviewSubmission
            ) -> None:
                pass

        provider = MockProvider()
        assert isinstance(provider, GitProvider)


class TestParseBranchIssueNumber:
    """Tests for parse_branch_issue_number helper."""

    def test_plain_number_prefix(self) -> None:
        """Test branch like '86-task-22-ci'."""
        assert parse_branch_issue_number("86-task-22-ci") == 86

    def test_feature_prefix(self) -> None:
        """Test branch like 'feature/123-login'."""
        assert parse_branch_issue_number("feature/123-login") == 123

    def test_gh_prefix(self) -> None:
        """Test branch like 'GH-789-refactor'."""
        assert parse_branch_issue_number("GH-789-refactor") == 789

    def test_underscore_separator(self) -> None:
        """Test branch like '42_fix_bug'."""
        assert parse_branch_issue_number("42_fix_bug") == 42

    def test_plain_branch_returns_none(self) -> None:
        """Test branch like 'main' returns None."""
        assert parse_branch_issue_number("main") is None

    def test_no_number_returns_none(self) -> None:
        """Test branch like 'no-number' returns None."""
        assert parse_branch_issue_number("no-number") is None

    def test_prefix_slash_number_only(self) -> None:
        """Test branch like 'fix/456' (number at end, no trailing separator)."""
        assert parse_branch_issue_number("fix/456") == 456

    def test_bare_number(self) -> None:
        """Test branch like '123' (just a number)."""
        assert parse_branch_issue_number("123") == 123

    def test_number_in_middle_returns_none(self) -> None:
        """Test branch like 'feature-add-42' (number not at start)."""
        assert parse_branch_issue_number("feature-add-42") is None


class TestParseDiffValidLines:
    """Tests for parse_diff_valid_lines helper."""

    def test_none_patch(self) -> None:
        """Test that None patch returns empty frozenset."""
        assert parse_diff_valid_lines(None) == frozenset()

    def test_empty_patch(self) -> None:
        """Test that empty string patch returns empty frozenset."""
        assert parse_diff_valid_lines("") == frozenset()

    def test_single_hunk(self) -> None:
        """Test parsing a single hunk with context, additions, and deletions."""
        patch = "@@ -10,3 +10,4 @@\n context\n-removed\n+added1\n+added2\n context2\n"
        result = parse_diff_valid_lines(patch)
        # new-side: 10 (context), 11 (added1), 12 (added2), 13 (context2)
        assert result == frozenset({10, 11, 12, 13})

    def test_multiple_hunks(self) -> None:
        """Test parsing multiple hunks."""
        patch = "@@ -1,2 +1,2 @@\n-old\n+new\n ctx\n@@ -20,2 +20,3 @@\n ctx\n+added\n ctx2\n"
        result = parse_diff_valid_lines(patch)
        # Hunk 1: 1 (new), 2 (ctx)
        # Hunk 2: 20 (ctx), 21 (added), 22 (ctx2)
        assert result == frozenset({1, 2, 20, 21, 22})

    def test_additions_only(self) -> None:
        """Test hunk with only additions."""
        patch = "@@ -5,0 +6,2 @@\n+line1\n+line2\n"
        result = parse_diff_valid_lines(patch)
        assert result == frozenset({6, 7})

    def test_deletions_excluded(self) -> None:
        """Test that deletion-only lines don't appear in result."""
        patch = "@@ -1,3 +1,1 @@\n-removed1\n-removed2\n ctx\n"
        result = parse_diff_valid_lines(patch)
        # Only context line gets new-side number 1
        assert result == frozenset({1})

    def test_no_newline_marker_ignored(self) -> None:
        r"""Test that '\\ No newline at end of file' is ignored."""
        patch = "@@ -1,2 +1,2 @@\n-old\n+new\n\\ No newline at end of file\n"
        result = parse_diff_valid_lines(patch)
        assert result == frozenset({1})
