"""Unit tests for reviewer module."""

from ai_reviewer.core.models import (
    CodeIssue,
    GoodPractice,
    IssueCategory,
    IssueSeverity,
    ReviewResult,
    TaskAlignmentStatus,
)
from ai_reviewer.reviewer import _build_review_submission


class TestBuildReviewSubmission:
    """Tests for _build_review_submission."""

    def test_all_inline_issues(self) -> None:
        """Test that issues with file_path and line_number become inline comments."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="SQL Injection",
            description="Use parameterized query",
            file_path="db.py",
            line_number=10,
            proposed_code="safe_code()",
        )
        result = ReviewResult(issues=(issue,), summary="Found issues")

        submission = _build_review_submission(result, "en")

        assert len(submission.line_comments) == 1
        assert submission.line_comments[0].path == "db.py"
        assert submission.line_comments[0].line == 10
        assert submission.line_comments[0].suggestion == "safe_code()"
        assert "SQL Injection" in submission.line_comments[0].body

    def test_all_fallback_issues(self) -> None:
        """Test that issues without file/line are in summary only."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="General issue",
            description="Description here",
        )
        result = ReviewResult(issues=(issue,), summary="Found issues")

        submission = _build_review_submission(result, "en")

        assert len(submission.line_comments) == 0
        assert "General issue" in submission.summary

    def test_mixed_issues_partition(self) -> None:
        """Test that mixed issues are correctly partitioned."""
        inline = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Inline Issue",
            description="Desc",
            file_path="src/main.py",
            line_number=5,
        )
        fallback = CodeIssue(
            category=IssueCategory.ARCHITECTURE,
            severity=IssueSeverity.INFO,
            title="Fallback Issue",
            description="Desc",
        )
        result = ReviewResult(issues=(inline, fallback), summary="Review")

        submission = _build_review_submission(result, None)

        assert len(submission.line_comments) == 1
        assert submission.line_comments[0].path == "src/main.py"
        assert "Fallback Issue" in submission.summary
        assert "Inline Issue" not in submission.summary

    def test_empty_issues(self) -> None:
        """Test with no issues at all."""
        result = ReviewResult(summary="Clean code")

        submission = _build_review_submission(result, "en")

        assert len(submission.line_comments) == 0
        assert "Clean code" in submission.summary

    def test_issue_with_file_but_no_line_is_fallback(self) -> None:
        """Test that issue with file_path but no line_number is fallback."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="No line",
            description="Has file but no line",
            file_path="main.py",
            line_number=None,
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert len(submission.line_comments) == 0
        assert "No line" in submission.summary

    def test_issue_with_line_but_no_file_is_fallback(self) -> None:
        """Test that issue with line_number but no file_path is fallback."""
        # CodeIssue with line_number requires ge=1, and file_path=None
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="No file",
            description="Has line but no file",
            file_path=None,
            line_number=5,
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert len(submission.line_comments) == 0
        assert "No file" in submission.summary

    def test_suggestion_mapping(self) -> None:
        """Test that proposed_code maps to suggestion on LineComment."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Fix code",
            description="Desc",
            file_path="app.py",
            line_number=42,
            proposed_code="better_code()",
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert submission.line_comments[0].suggestion == "better_code()"

    def test_no_suggestion_when_absent(self) -> None:
        """Test that LineComment has no suggestion when proposed_code is None."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Fix code",
            description="Desc",
            file_path="app.py",
            line_number=42,
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert submission.line_comments[0].suggestion is None

    def test_summary_includes_good_practices(self) -> None:
        """Test that good practices appear in summary."""
        practice = GoodPractice(description="Nice type hints", file_path="models.py")
        result = ReviewResult(good_practices=(practice,), summary="Good")

        submission = _build_review_submission(result, None)

        assert "Nice type hints" in submission.summary

    def test_summary_includes_task_alignment(self) -> None:
        """Test that task alignment appears in summary."""
        result = ReviewResult(
            summary="Review",
            task_alignment=TaskAlignmentStatus.ALIGNED,
            task_alignment_reasoning="Matches task",
        )

        submission = _build_review_submission(result, None)

        assert "✅ Aligned" in submission.summary
        assert "Matches task" in submission.summary

    def test_event_defaults_to_comment(self) -> None:
        """Test that submission event defaults to COMMENT."""
        result = ReviewResult(summary="Test")

        submission = _build_review_submission(result, None)

        assert submission.event == "COMMENT"
