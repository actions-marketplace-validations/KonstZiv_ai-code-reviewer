"""Unit tests for review formatter."""

from ai_reviewer.core.formatter import format_review_comment
from ai_reviewer.core.models import (
    ReviewResult,
    TaskAlignmentStatus,
    Vulnerability,
    VulnerabilitySeverity,
)


class TestFormatReviewComment:
    """Tests for format_review_comment function."""

    def test_format_clean_result(self) -> None:
        """Test formatting a result with no vulnerabilities."""
        result = ReviewResult(
            summary="Code looks good.",
            task_alignment=TaskAlignmentStatus.ALIGNED,
            task_alignment_reasoning="Matches requirements.",
        )

        comment = format_review_comment(result)

        assert "# AI Code Review Report" in comment
        assert "## Summary" in comment
        assert "Code looks good." in comment
        assert "## Security Analysis" in comment
        assert "✅ No critical vulnerabilities found." in comment
        assert "## Task Alignment" in comment
        assert "✅ Aligned" in comment
        assert "Matches requirements." in comment

    def test_format_vulnerabilities(self) -> None:
        """Test formatting a result with vulnerabilities."""
        vuln = Vulnerability(
            title="SQL Injection",
            description="Unsafe query",
            severity=VulnerabilitySeverity.CRITICAL,
            recommendation="Use params",
            file="db.py",
            line=10,
        )
        result = ReviewResult(
            summary="Found issues.",
            vulnerabilities=(vuln,),
            task_alignment=TaskAlignmentStatus.INSUFFICIENT_DATA,
        )

        comment = format_review_comment(result)

        assert "| Severity | Issue | Description | Recommendation |" in comment
        assert "🔴 **CRITICAL**" in comment
        assert "SQL Injection" in comment
        assert "Unsafe query" in comment
        assert "Use params" in comment
        assert "_File: db.py:10_" in comment
        assert "⚠️ Insufficient Data" in comment

    def test_format_misaligned_task(self) -> None:
        """Test formatting a misaligned task result."""
        result = ReviewResult(
            summary="Logic error.",
            task_alignment=TaskAlignmentStatus.MISALIGNED,
            task_alignment_reasoning="Does not implement feature X.",
        )

        comment = format_review_comment(result)

        assert "❌ Misaligned" in comment
        assert "Does not implement feature X." in comment

    def test_escape_pipes_in_table(self) -> None:
        """Test that pipes in content are escaped to preserve table structure."""
        vuln = Vulnerability(
            title="Issue | with pipe",
            description="Desc | pipe",
            severity=VulnerabilitySeverity.LOW,
            recommendation="Fix | pipe",
        )
        result = ReviewResult(vulnerabilities=(vuln,))

        comment = format_review_comment(result)

        assert "Issue \\| with pipe" in comment
        assert "Desc \\| pipe" in comment
        assert "Fix \\| pipe" in comment
